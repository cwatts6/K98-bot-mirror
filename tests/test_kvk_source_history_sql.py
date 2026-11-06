"""Opt-in real SQL tests on separately approved disposable S8B prerequisites.

This suite never installs schema, creates databases or changes approval flags.
Install the reviewed Stage 2 migration separately before authorising this suite.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
from threading import Event

import pytest

from kvk.dal.new_source_history_dal import capture_history, iter_history
from kvk.dal.new_source_import_dal import one, transaction
from kvk.dal.new_source_report_context_dal import iter_player_powers, load_report_context
from tests import test_kvk_source_sql_integration as source_sql
from tests.test_kvk_source_sql_integration import (
    database as source_database,  # noqa: F401
    sealed_fixture,
)

GUILD = "900000000000000016"


@pytest.fixture
def database(request, monkeypatch):
    if os.getenv("KVK_EXPORT_HISTORY_SQL_ENABLE") != "1":
        pytest.skip("Stage 2 requires separately approved disposable SQL execution.")
    target = os.getenv("KVK_S8B_SQL_SERVER", "") + "|" + os.getenv("KVK_S8B_SQL_DATABASE", "")
    if os.getenv("KVK_EXPORT_HISTORY_SQL_APPROVED_TARGET") != target or not os.getenv(
        "KVK_S8B_SQL_DATABASE", ""
    ).startswith("K98_S8B_Disposable_ExportHistory_"):
        pytest.fail("Stage 2 exact disposable target approval is missing.")
    original_admission = source_sql.admission
    monkeypatch.setattr(
        source_sql,
        "admission",
        lambda *args, **kwargs: replace(original_admission(*args, **kwargs), guild_id=GUILD),
    )
    return request.getfixturevalue("source_database")


def selected(database):
    service, update = sealed_fixture(database)
    return service.publish(update["UpdateID"])


def capture(database, result, connect=None):
    factory, season, _ = database
    return capture_history(
        connect=connect or factory,
        intent_id=result.intent_id,
        kvk_no=season,
        guild_id=GUILD,
        batch_size=1,
    )


def test_engine_capture_restart_counts_context_and_duplicate_workers(database):
    connect, season, _ = database
    result = selected(database)
    with ThreadPoolExecutor(max_workers=2) as pool:
        snapshots = list(pool.map(lambda _: capture(database, result), range(2)))
    assert snapshots[0] == snapshots[1]
    first = list(iter_history(connect=connect, snapshot=snapshots[0], batch_size=1))
    assert len(first) == 3
    assert sum(r["player_records"] or 0 for r in first) == 4
    aggregate = next(r for r in first if r["aggregate_revision_id"])
    assert (aggregate["kingdom_records"], aggregate["camp_records"]) == (2, 2)
    # An accepted status may change after capture; restart must not refresh it.
    with transaction(connect) as cursor:
        cursor.execute(
            "UPDATE KVK.SourceImportAttempt SET Status='duplicate' WHERE AttemptID=?",
            first[0]["attempt_id"],
        )
    assert capture(database, result) == snapshots[0]
    assert list(iter_history(connect=connect, snapshot=snapshots[0])) == first
    context = load_report_context(
        connect=connect, publication_id=result.publication_id, kvk_no=season
    )
    powers = list(iter_player_powers(connect=connect, context=context, batch_size=1))
    assert len(powers) == 2 and all(r["BaselinePower"] is not None for r in powers)


@pytest.mark.parametrize("aggregate", [False, True])
@pytest.mark.parametrize("cancelled", [False, True])
def test_engine_retains_accepted_receipt_during_followup(database, aggregate, cancelled):
    connect, season, _ = database
    result = selected(database)
    column = "AggregateRevisionID" if aggregate else "ObservationRevisionID"
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT TOP (1) AttemptID,ObservationRevisionID,AggregateRevisionID "
            "FROM KVK.SourceImportAttempt WHERE SourceKey=? AND KVK_NO=? AND GuildID=? "
            "AND " + column + " IS NOT NULL ORDER BY ReceivedUTC,AttemptID",
            source_sql.SOURCE_KEY,
            season,
            GUILD,
        )
        selected_attempt = one(cursor)
        attempt_id = selected_attempt["AttemptID"]
        player_id = selected_attempt["ObservationRevisionID"]
        aggregate_id = selected_attempt["AggregateRevisionID"]
        payload = dict(
            version=2,
            cancelled=cancelled,
            proposal={"action": "correct"},
            history=[
                dict(
                    status="accepted",
                    proposal={"action": "accept"},
                    outcome=dict(
                        observation_revision_id=player_id,
                        aggregate_revision_id=aggregate_id,
                        private_diagnostic="DO_NOT_EXPORT",
                    ),
                )
            ],
        )
        # This is the durable transition made by SourceAdminDAL.prepare/cancel.
        cursor.execute(
            "UPDATE KVK.SourceImportAttempt SET Status='validated',ActionKey='s5a_draft',"
            "ObservationRevisionID=NULL,AggregateRevisionID=NULL,ProvenanceJson=? "
            "WHERE AttemptID=?",
            json.dumps(payload),
            attempt_id,
        )
    frozen = capture(database, result)
    facts = list(iter_history(connect=connect, snapshot=frozen))
    fact = next(r for r in facts if r["attempt_id"] == attempt_id)
    assert fact["observation_revision_id"] == player_id
    assert fact["aggregate_revision_id"] == aggregate_id
    assert fact["import_status"] == "Validated"
    assert fact["data_time_utc"] and fact["revision_number"] == 1
    assert fact["kingdom_records"] == 2 if aggregate else fact["player_records"] == 2
    if not aggregate:
        assert fact["scan"] is not None
    assert "DO_NOT_EXPORT" not in json.dumps(facts)
    assert "Earlier accepted input" in " ".join(fact["notes"])
    with transaction(connect) as cursor:
        cursor.execute(
            "UPDATE KVK.SourceImportAttempt SET ProvenanceJson='{}' WHERE AttemptID=?", attempt_id
        )
    assert capture(database, result) == frozen
    assert list(iter_history(connect=connect, snapshot=frozen)) == facts


def test_engine_capture_blocks_status_mutation_until_commit(database):
    connect, _, _ = database
    result = selected(database)
    copied, release, writer_started = Event(), Event(), Event()

    class PausedCursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def execute(self, sql, *args):
            self.cursor.execute(sql, *args)
            if "INSERT #ReportHistoryAttempts" in sql:
                copied.set()
                if not release.wait(10):
                    raise TimeoutError("Test capture was not released")
            return self

        def __getattr__(self, name):
            return getattr(self.cursor, name)

    class PausedConnection:
        def __init__(self):
            self.connection = connect()

        def cursor(self):
            return PausedCursor(self.connection.cursor())

        def __getattr__(self, name):
            return getattr(self.connection, name)

    def mutate():
        with transaction(connect) as cursor:
            cursor.execute("SET LOCK_TIMEOUT 1000")
            writer_started.set()
            with pytest.raises(Exception) as exc:
                cursor.execute(
                    "UPDATE KVK.SourceImportAttempt SET Status='duplicate' "
                    "WHERE KVK_NO=? AND GuildID=? AND Status='accepted'",
                    database[1],
                    GUILD,
                )
            assert "1222" in str(exc.value), "Expected a real SQL lock timeout"

    with ThreadPoolExecutor(max_workers=2) as pool:
        capturing = pool.submit(capture, database, result, PausedConnection)
        try:
            assert copied.wait(10)
            changing = pool.submit(mutate)
            assert writer_started.wait(5)
            changing.result(timeout=5)
        finally:
            release.set()
        snapshot = capturing.result(timeout=10)
    assert all(
        r["import_status"] == "Accepted" for r in iter_history(connect=connect, snapshot=snapshot)
    )


def test_engine_partial_capture_rolls_back_and_retry_recovers(database):
    connect, _, _ = database
    result = selected(database)

    class InterruptedCursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def execute(self, sql, *args):
            self.cursor.execute(sql, *args)
            if sql.startswith("INSERT KVK.SourceExportHistoryRow"):
                raise RuntimeError("Injected interruption after persisted row")
            return self

        def __getattr__(self, name):
            return getattr(self.cursor, name)

    class InterruptedConnection:
        def __init__(self):
            self.connection = connect()

        def cursor(self):
            return InterruptedCursor(self.connection.cursor())

        def __getattr__(self, name):
            return getattr(self.connection, name)

    with pytest.raises(RuntimeError, match="Injected interruption"):
        capture(database, result, InterruptedConnection)
    with transaction(connect) as cursor:
        for table in ("SourceExportHistory", "SourceExportHistoryRow"):
            cursor.execute(
                f"SELECT COUNT(*) FROM KVK.{table} WHERE IntentID=? AND GuildID=?",
                result.intent_id,
                GUILD,
            )
            assert cursor.fetchone()[0] == 0
    snapshot = capture(database, result)
    assert len(list(iter_history(connect=connect, snapshot=snapshot, batch_size=1))) == 3


@pytest.mark.parametrize(
    "statement,parameters,error_code",
    [
        ("UPDATE KVK.SourceExportHistory SET AttemptCount=-1 WHERE IntentID=?", (), "547"),
        ("UPDATE KVK.SourceExportHistory SET KVK_NO=KVK_NO+1 WHERE IntentID=?", (), "547"),
        ("UPDATE KVK.SourceExportHistoryRow SET Ordinal=0 WHERE IntentID=?", (), "547"),
        (
            "UPDATE KVK.SourceExportHistoryRow SET PayloadJson=? WHERE IntentID=?",
            ("not json",),
            "547",
        ),
        (
            "UPDATE KVK.SourceExportHistoryRow SET PayloadJson=? WHERE IntentID=?",
            ('{"value":"' + "x" * 8192 + '"}',),
            "547",
        ),
        (
            "DELETE KVK.SourceExportHistory WHERE IntentID=?",
            (),
            "547",
        ),
        (
            "INSERT KVK.SourceExportHistoryRow SELECT IntentID,GuildID,HistoryVersion,"
            "Ordinal+100,AttemptID,PayloadJson,RowHash FROM KVK.SourceExportHistoryRow "
            "WHERE IntentID=?",
            (),
            "2627",
        ),
    ],
)
def test_engine_history_constraints_reject_invalid_changes(
    database, statement, parameters, error_code
):
    connect, _, _ = database
    result = selected(database)
    snapshot = capture(database, result)
    first = list(iter_history(connect=connect, snapshot=snapshot))
    with pytest.raises(Exception) as exc:
        with transaction(connect) as cursor:
            cursor.execute(statement, *parameters, result.intent_id)
    assert error_code in str(exc.value)
    assert list(iter_history(connect=connect, snapshot=snapshot)) == first
