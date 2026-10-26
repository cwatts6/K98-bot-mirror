"""Cross-stage waiting, receipt closure and no-replay lifecycle regressions."""

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from datetime import UTC, datetime
from threading import Event
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from core.sql_observation import ObservationBusy, observation
from kvk.dal.new_source_import_dal import SourceBusy, SourceConflict, UncertainCommit, transaction
from services import export_contention as contention
from services.configuration_attempt_recovery import AttemptJournal, ConfigurationAttemptRecovery
from services.producer_admission import producer_turn
from services.recovery_execution_guard import operation_key, recovery_execution


class SqlTimeout(Exception):
    pass


@pytest.mark.parametrize("cleanup", [None, "rollback", "close"])
def test_observation_wait_requires_rollback_and_close(cleanup):
    connection = Mock(autocommit=False)
    if cleanup:
        getattr(connection, cleanup).side_effect = OSError("cleanup unavailable")
    error = SqlTimeout("42000", "private query data (1222)")
    with observation(), pytest.raises(OSError if cleanup else ObservationBusy) as caught:
        with transaction(lambda: connection):
            raise error
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
    connection.commit.assert_not_called()
    assert "private query" not in str(caught.value)


def test_write_timeout_and_unknown_commit_are_not_observer_waits():
    connection = Mock(autocommit=False)
    error = SqlTimeout("42000", "(1222)")
    with pytest.raises(SqlTimeout):
        with transaction(lambda: connection):
            raise error
    connection.commit.side_effect = error
    with observation(), pytest.raises(UncertainCommit):
        with transaction(lambda: connection):
            pass


@pytest.mark.parametrize("result", [-1, -2, -3, -999])
def test_only_exact_released_observation_refusal_is_waiting(result):
    connection = Mock(autocommit=False)
    error = contention.CoordinationLockRefused(
        result=result, session=1, transaction_state=1, transaction_count=1, resource_hash="a" * 64
    )
    with (
        observation(),
        pytest.raises(ObservationBusy if result == -1 else contention.CoordinationLockRefused),
    ):
        with transaction(lambda: connection):
            raise error


@pytest.mark.parametrize("stage", ["request", "authorize", "transition", "uncertain", "captured"])
def test_connection_time_does_not_remove_later_stage_retry(monkeypatch, stage):
    clock = [0.0]
    monkeypatch.setattr(contention.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        contention.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds)
    )
    connections = []

    def connect():
        clock[0] += 1.3
        connection = Mock(autocommit=False)
        connections.append(connection)
        return connection

    calls = []

    def operation():
        calls.append(stage)
        with contention.transaction(connect):
            if len(calls) == 1:
                raise contention.CoordinationLockRefused(
                    result=-1,
                    session=1,
                    transaction_state=1,
                    transaction_count=1,
                    resource_hash="a" * 64,
                )
        return "saved-once"

    assert contention.retry_coordination(operation)() == "saved-once"
    assert len(calls) == 2
    connections[0].rollback.assert_called_once()
    connections[0].commit.assert_not_called()
    connections[1].commit.assert_called_once()


def test_inherited_deadline_is_not_extended_by_connection_credit(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(contention.time, "monotonic", lambda: clock[0])
    error = contention.CoordinationLockRefused(
        result=-1, session=1, transaction_state=1, transaction_count=1, resource_hash="a" * 64
    )
    error.transaction_released = True
    error.phase_timings_ms = {"connect": 1300}
    calls = []

    @contention.retry_coordination
    def attempt():
        calls.append(1)
        clock[0] += 1.3
        raise error

    with contention.contention_budget(0.5), pytest.raises(contention.CoordinationLockRefused):
        attempt()
    assert len(calls) == 1


def test_local_producers_wait_through_settlement_and_nested_helpers():
    entered, finish, queued = Event(), Event(), Event()
    order = []

    def first():
        with producer_turn():
            order.append("report")
            with producer_turn():
                order.append("nested")
            entered.set()
            assert finish.wait(5)
            order.append("settlement")

    def second():
        queued.set()
        with producer_turn():
            order.append("configuration")

    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(first)
        assert entered.wait(5)
        b = pool.submit(second)
        assert queued.wait(5)
        assert not b.done()
        finish.set()
        a.result(5)
        b.result(5)
    assert order == ["report", "nested", "settlement", "configuration"]


def test_stale_or_parallel_inherited_producer_turn_cannot_enter():
    with producer_turn():
        context = copy_context()
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(context.run, lambda: producer_turn().__enter__())
            with pytest.raises(SourceConflict):
                future.result(5)
    with pytest.raises(SourceConflict):
        context.run(lambda: producer_turn().__enter__())


def test_wait_timeout_never_enters_or_blocks_next_producer():
    with producer_turn():
        with ThreadPoolExecutor(1) as pool:

            def try_other():
                with producer_turn(timeout=0):
                    pytest.fail("entered active producer")

            with pytest.raises(SourceBusy):
                pool.submit(try_other).result(5)
    with producer_turn(timeout=0):
        pass


def test_different_incident_cards_share_exact_scoped_operation_guard():
    key = operation_key(("account", "store"), "source")
    with recovery_execution("card-a", operation=key) as first:
        assert first
        with recovery_execution("card-b", operation=key) as second:
            assert not second
        with recovery_execution(
            "card-c", operation=operation_key(("other", "store"), "source")
        ) as other:
            assert other


def attempt(journal, outcome):
    value = dict(
        schema="configuration-attempt/1",
        attempt_id=str(uuid4()),
        operation_id=str(uuid4()),
        started_utc=datetime.now(UTC).isoformat(),
        finished_utc=datetime.now(UTC).isoformat(),
        phase="before_inputs",
        outcome=outcome,
    )
    journal.save(value)
    return value


@pytest.mark.parametrize("outcome", ["failed_before_inputs", "reported_success", "unconfirmed"])
def test_attempt_receipt_reaches_real_card_renderer(tmp_path, outcome):
    from ui.views.recovery_view import incident_embed

    journal = AttemptJournal(tmp_path)
    value = attempt(journal, outcome)
    evidence, _, resolved = ConfigurationAttemptRecovery(journal).inspect(value["attempt_id"])
    embed = incident_embed(
        dict(
            evidence=evidence,
            State="resolved" if resolved else "open",
            SourceKind="configuration_attempt",
            LastSeenUTC="now",
            IncidentID="id",
        )
    )
    assert any(f.name == "Failure details" and f.value for f in embed.fields)


def test_verified_link_closes_incident_without_rewriting_attempt(tmp_path):
    journal = AttemptJournal(tmp_path)
    value = attempt(journal, "failed_before_inputs")
    original = journal.path(value["attempt_id"]).read_bytes()
    resolver = Mock(
        return_value=dict(
            resolved=True,
            outcome="configuration_only_completed",
            token="verified",
            links=[
                dict(kind="configuration_read_continuation", source_id="original", label="Review")
            ],
        )
    )
    evidence, token, resolved = ConfigurationAttemptRecovery(journal, resolver).inspect(
        value["attempt_id"]
    )
    assert resolved and evidence["outcome"] == "verified_recovery"
    assert evidence["original_outcome"] == "failed_before_inputs"
    resolver.assert_called_once_with(value["operation_id"], "before_inputs")
    assert journal.path(value["attempt_id"]).read_bytes() == original
    # Restart uses the same durable linked receipts, never the latest attempt.
    assert ConfigurationAttemptRecovery(AttemptJournal(tmp_path), resolver).inspect(
        value["attempt_id"]
    )[2]


def test_later_unrelated_success_or_unknown_link_cannot_close_failure(tmp_path):
    journal = AttemptJournal(tmp_path)
    failed = attempt(journal, "failed_before_inputs")
    attempt(journal, "reported_success")
    for result in (
        None,
        dict(resolved=False, outcome="checking_attempt", token="pending", links=[]),
    ):
        assert not ConfigurationAttemptRecovery(journal, Mock(return_value=result)).inspect(
            failed["attempt_id"]
        )[2]


@pytest.mark.parametrize("close_failure", [False, True])
def test_writer_guard_failure_closes_only_proven_nonentry(tmp_path, close_failure):
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    connection = dal.connect.return_value
    dal.session.return_value = MagicMock()
    dal.session.return_value.__enter__.side_effect = RuntimeError("guard refused")
    if close_failure:
        connection.close.side_effect = OSError("close unconfirmed")
    with pytest.raises(RuntimeError, match="guard refused"):
        runtime.begin_writer("all_kvk")
    connection.close.assert_called_once()
    releases = [c for c in dal.transition.call_args_list if c.kwargs.get("state") == "unavailable"]
    assert bool(releases) != close_failure
    dal.uncertain.assert_not_called()
