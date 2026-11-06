"""Real independent SQL sessions and complete receipt-to-card recovery.

Only namespaced disposable tables/locks in localhost K98DEV are used.
"""

from datetime import UTC, datetime
import json
import os
from uuid import uuid4

import pytest

from core.sql_observation import ObservationBusy, observe_call
from services.configuration_attempt_recovery import (
    AttemptJournal,
    ConfigurationAttemptRecovery,
    attempt_resolver,
)
from tests.test_configuration_continuation_sql import commit_child, run
from tests.test_configuration_read_continuation_sql import setup
from tests.test_guided_recovery import ACTOR
from tests.test_import_capture_recovery_sql import recovery as recovery
from tests.test_recovery_sql import store as store

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable local SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


@pytest.mark.parametrize("lost_commit_reply", [False, True])
def test_original_failure_through_publication_capture_disposition_and_restart_card(
    recovery, store, tmp_path, lost_commit_reply
):
    from ui.views.recovery_view import incident_embed

    r = recovery
    generation = json.loads(r.outcomes.inspect(r.source)["preparation"]["GenerationJson"])
    calls = []

    def runner():
        calls.append("producer")
        return commit_child(r, generation, lost_reply=lost_commit_reply)

    source, continuation, service = setup(r, runner)
    service.store = store
    operation = continuation.dal.review_context(continuation.dal.original(source))[
        "failure_context"
    ]["operation_id"]
    journal = AttemptJournal(tmp_path / "attempts")
    attempt_id = str(uuid4())
    journal.save(
        dict(
            schema="configuration-attempt/1",
            attempt_id=attempt_id,
            operation_id=operation,
            phase="before_inputs",
            outcome="failed_before_inputs",
            started_utc=datetime.now(UTC).isoformat(),
            finished_utc=datetime.now(UTC).isoformat(),
        )
    )
    original = journal.path(attempt_id).read_bytes()
    adapter = ConfigurationAttemptRecovery(journal, attempt_resolver(r.runtime, service.adapters))
    service.adapters[adapter.kind] = adapter
    failed = service.review_source(ACTOR, adapter.kind, attempt_id)
    assert failed["State"] == "open"
    assert incident_embed(failed).title == "ProcConfig import attempt"
    review = service.review_source(ACTOR, continuation.kind, source)
    run(service, review, "retry_configuration")
    child = continuation.dal.snapshot(source)["child"]["PreparationID"]
    evidence, token, _ = continuation.producer.inspect(child)
    continuation.producer.execute(
        child, "resume_capture", token, "recovery:" + str(uuid4()), "Capture once"
    )
    evidence, token, _ = continuation.producer.inspect(child)
    continuation.producer.execute(
        child,
        "complete_configuration_only",
        token,
        "recovery:" + str(uuid4()),
        "Verify disposition",
    )
    # Recreate the attempt adapter: closure is derived from exact SQL linkage,
    # not an in-memory successful return or a later unrelated attempt.
    service.adapters[adapter.kind] = ConfigurationAttemptRecovery(
        AttemptJournal(journal.root), attempt_resolver(r.runtime, service.adapters)
    )
    closed = service.refresh(failed["IncidentID"])
    assert closed["State"] == "resolved"
    assert closed["evidence"]["original_outcome"] == "failed_before_inputs"
    assert "report/cache" not in closed["evidence"]["explanation"]
    assert incident_embed(closed).title == "ProcConfig import attempt"
    assert calls == ["producer"]
    assert journal.path(attempt_id).read_bytes() == original
    assert service.refresh(failed["IncidentID"])["State"] == "resolved"
    assert calls == ["producer"]


def test_monitor_row_lock_defers_then_reads_without_releasing_writer(recovery):
    from kvk.dal.new_source_import_dal import transaction

    r = recovery
    holder = r.connect()
    holder.cursor().execute(
        "SELECT Version FROM dbo.ExportPreparation WITH(UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
        r.source,
    ).fetchone()

    def connection():
        cn = r.connect()
        cn.cursor().execute("SET LOCK_TIMEOUT 50")
        return cn

    def inspect():
        with transaction(connection) as cursor:
            cursor.execute(
                "SELECT Version FROM dbo.ExportPreparation WITH(UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
                r.source,
            )
            return cursor.fetchone()[0]

    try:
        with pytest.raises(ObservationBusy):
            observe_call(inspect)
        assert holder.cursor().execute("SELECT @@TRANCOUNT").fetchone()[0] == 1
    finally:
        holder.rollback()
        holder.close()
    assert observe_call(inspect) > 0


def test_report_configuration_and_observer_overlap_without_abandoning_output(recovery):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from kvk.dal.new_source_import_dal import transaction
    from services.producer_recovery_intent import atomic_producer_intent

    r = recovery
    entered, release, configuration_queued = Event(), Event(), Event()
    calls = []

    @atomic_producer_intent("player_stats_report")
    def report():
        with transaction(r.connect) as cursor:
            cursor.execute(
                "UPDATE dbo.ExportPreparation SET Version=Version+1 WHERE PreparationID=?", r.source
            )
            calls.append("report_started")
            entered.set()
            assert release.wait(5)
        calls.append("report_committed")

    @atomic_producer_intent("configuration_import")
    def configuration():
        with transaction(r.connect) as cursor:
            cursor.execute(
                "SELECT Version FROM dbo.ExportPreparation WHERE PreparationID=?", r.source
            )
            assert cursor.fetchone()[0] > 1
        calls.append("configuration_read")

    def queued():
        configuration_queued.set()
        configuration()

    def read_busy():
        with transaction(r.connect) as cursor:
            cursor.execute("SET LOCK_TIMEOUT 50")
            cursor.execute(
                "SELECT Version FROM dbo.ExportPreparation WHERE PreparationID=?", r.source
            )
            return cursor.fetchone()[0]

    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(report)
        try:
            assert entered.wait(5)
            second = pool.submit(queued)
            assert configuration_queued.wait(5)
            with pytest.raises(ObservationBusy):
                observe_call(read_busy)
            assert calls == ["report_started"]
        finally:
            release.set()
        first.result(5)
        second.result(5)
    assert calls == ["report_started", "report_committed", "configuration_read"]
    assert observe_call(read_busy) > 1
