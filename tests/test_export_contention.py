"""Classified coordination retries cannot replay a producer or unknown commit."""

import json
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import UncertainCommit
from services import export_contention as module
from services.export_coordination_dal import _mutex


def refusal(result=-1):
    return module.CoordinationLockRefused(
        result=result,
        session=77,
        transaction_state=1,
        transaction_count=1,
        resource_hash="a" * 64,
    )


@pytest.mark.parametrize("result", [-1, -2, -3, -999])
def test_original_lock_result_preserved_without_driver_payload(result):
    cursor = Mock()
    cursor.execute.side_effect = Exception(
        "42000", f"K98_COORDINATION_LOCK result={result} session=77 xact=1 count=1 (51400) secret"
    )
    with pytest.raises(module.CoordinationLockRefused) as caught:
        _mutex(cursor, "account:sensitive")
    assert caught.value.result == result
    assert caught.value.__cause__ is cursor.execute.side_effect
    assert not caught.value.transaction_released
    assert "secret" not in str(caught.value)
    assert "sensitive" not in json.dumps(module.sql_error_facts(caught.value))


def test_legacy_51400_and_other_sql_errors_are_not_classified(caplog):
    cursor = Mock()
    original = Exception("42000", "Export admission busy (51400); PWD=secret")
    cursor.execute.side_effect = original
    with pytest.raises(Exception) as caught:
        _mutex(cursor, "account:sensitive")
    assert caught.value is original
    assert "secret" not in caplog.text and "sensitive" not in caplog.text


@pytest.mark.parametrize("failure", [None, "rollback", "close"])
def test_retry_proof_requires_rollback_and_connection_release(failure):
    connection = Mock(autocommit=False)
    if failure:
        getattr(connection, failure).side_effect = OSError(failure)
    error = refusal()
    with pytest.raises(OSError if failure else module.CoordinationLockRefused):
        with module.transaction(lambda: connection):
            raise error
    assert error.transaction_released is (failure is None)
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
    connection.commit.assert_not_called()


def clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(module.time, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    return now


def test_safe_retry_releases_connection_before_wait_and_recovers(monkeypatch, caplog):
    clock(monkeypatch)
    connections = []

    @module.retry_coordination
    def authorize():
        cn = Mock(autocommit=False)
        connections.append(cn)
        with module.transaction(lambda: cn):
            if len(connections) == 1:
                raise refusal()
        return "admitted"

    with caplog.at_level("INFO"):
        assert authorize() == "admitted"
    connections[0].rollback.assert_called_once()
    for cn in connections:
        cn.close.assert_called_once()
    assert len(caplog.records) == 1 and '"outcome": "recovered"' in caplog.text


@pytest.mark.parametrize("result", [-1, -2, -3, -999, None])
def test_existing_sql_worker_accepts_only_attributed_timeout(result):
    from tests.test_kvk_export_sql_integration import test_sql_two_workers_cannot_both_claim

    error = refusal(result) if result is not None else RuntimeError("Export admission busy")
    dal = Mock()
    dal.claim_next.side_effect = [object(), error]
    if result == -1:
        test_sql_two_workers_cannot_both_claim(dal)
        assert dal.claim_next.call_count == 2
    else:
        with pytest.raises(type(error)) as caught:
            test_sql_two_workers_cannot_both_claim(dal)
        assert caught.value is error


@pytest.mark.parametrize("result", [-2, -3, -999])
def test_non_timeout_refusal_never_retried(monkeypatch, result):
    clock(monkeypatch)
    error = refusal(result)
    error.transaction_released = True
    operation = Mock(side_effect=error)
    operation.__name__ = "authorize"
    with pytest.raises(module.CoordinationLockRefused):
        module.retry_coordination(operation)()
    operation.assert_called_once()


def test_exhaustion_has_one_deadline_and_one_summary(monkeypatch, caplog):
    now = clock(monkeypatch)
    error = refusal()
    error.transaction_released = True
    operation = Mock(side_effect=error)
    operation.__name__ = "authorize"
    with pytest.raises(module.CoordinationLockRefused):
        module.retry_coordination(operation)()
    assert now[0] <= module.LOCK_BUDGET_SECONDS
    assert 1 < operation.call_count <= module.MAX_ATTEMPTS
    assert len(caplog.records) == 1


@pytest.mark.parametrize(
    "error", [UncertainCommit("unknown"), OSError("connection lost"), KeyboardInterrupt()]
)
def test_unclassified_and_unknown_commit_never_retried(monkeypatch, error):
    clock(monkeypatch)
    operation = Mock(side_effect=error)
    operation.__name__ = "transition"
    with pytest.raises(type(error)):
        module.retry_coordination(operation)()
    operation.assert_called_once()


def test_external_transaction_never_retried_even_with_old_release_marker(monkeypatch):
    clock(monkeypatch)
    error = refusal()
    error.transaction_released = True
    operation = Mock(side_effect=error)
    operation.__name__ = "transition"
    with pytest.raises(module.CoordinationLockRefused):
        module.retry_coordination(operation)(external_cursor=object())
    operation.assert_called_once()


def test_unknown_commit_from_real_transaction_wrapper_is_not_retried(monkeypatch):
    clock(monkeypatch)
    connection = Mock(autocommit=False)
    connection.commit.side_effect = OSError("acknowledgement lost")
    connect = Mock(return_value=connection)

    @module.retry_coordination
    def checkpoint():
        with module.transaction(connect):
            pass

    with pytest.raises(UncertainCommit):
        checkpoint()
    connect.assert_called_once()
    connection.rollback.assert_not_called()


def test_writer_original_error_survives_failed_uncertainty_cleanup(tmp_path, caplog):
    from services.legacy_export_snapshot_service import admitted_writer, use_runtime
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    original = OSError("original-sensitive-payload")
    dal.uncertain.side_effect = OSError("cleanup-sensitive-payload")

    @admitted_writer("all_kvk")
    def producer():
        raise original

    with use_runtime(runtime), pytest.raises(OSError) as caught:
        producer()
    assert caught.value is original
    assert "original-sensitive" not in caplog.text
    assert "cleanup-sensitive" not in caplog.text
    assert '"stage": "uncertain_cleanup"' in caplog.text
    dal.connect.return_value.close.assert_called_once()


@pytest.mark.parametrize(
    "explicit,previously_authorized,released,expected_release",
    [
        (True, False, True, True),
        (False, False, True, False),
        (True, True, True, False),
        (True, False, False, False),
    ],
)
def test_only_explicit_first_pre_execution_refusal_releases_live_owner(
    tmp_path, explicit, previously_authorized, released, expected_release
):
    from services.legacy_export_snapshot_service import (
        admitted_writer,
        current_owner,
        use_runtime,
        verify_producer_cursor,
    )
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    error = refusal()
    error.transaction_released = released
    dal.verify_producer_cursor.side_effect = error
    producer = Mock()

    @admitted_writer("all_kvk")
    def operation():
        current_owner().producer_authorized = previously_authorized
        verify_producer_cursor(Mock(), before_side_effects=explicit)
        producer()

    with use_runtime(runtime), pytest.raises(module.CoordinationLockRefused):
        operation()
    producer.assert_not_called()
    assert dal.uncertain.called is (not expected_release)
    if expected_release:
        assert dal.transition.call_args.kwargs == dict(
            expected="writing", state="unavailable", release=True
        )
    dal.connect.return_value.close.assert_called_once()


def test_health_probe_does_not_retry_native_timeout(tmp_path, monkeypatch):
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    error = refusal()
    error.transaction_released = True
    dal.claim.side_effect = error
    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)
    assert runtime._claim_unstarted("ticket", wait_for_admission=False, stage="preflight") is None
    dal.claim.assert_called_once()
    sleep.assert_not_called()


@pytest.mark.parametrize("result", [-2, -3, -999])
@pytest.mark.parametrize("stage", ["preflight", "writing"])
def test_terminal_claim_rollback_withdraws_only_its_ticket(tmp_path, monkeypatch, result, stage):
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    admitted = dal.claim.return_value
    error = refusal(result)
    connection = Mock(autocommit=False)
    calls = []

    def claim(identifier, **kwargs):
        calls.append((identifier, kwargs["stage"]))
        if kwargs["stage"] != stage:
            return admitted
        # Exercise the real acknowledgement wrapper; do not manufacture its
        # transaction_released witness in the regression.
        with module.transaction(lambda: connection):
            raise error

    dal.claim.side_effect = claim
    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)
    with pytest.raises(module.CoordinationLockRefused) as caught:
        runtime.begin_writer("all_kvk")
    assert caught.value is error and error.transaction_released
    assert calls[-1] == (dal.request.return_value, stage)
    assert len(calls) == (1 if stage == "preflight" else 2)
    dal.request.assert_called_once()
    dal.withdraw_unstarted.assert_called_once_with(dal.request.return_value)
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
    sleep.assert_not_called()
    dal.connect.assert_not_called()
    dal.uncertain.assert_not_called()


@pytest.mark.parametrize("failure", ["rollback", "close"])
@pytest.mark.parametrize("result", [-2, -3, -999])
def test_terminal_claim_without_rollback_close_proof_keeps_ticket(tmp_path, failure, result):
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    error = refusal(result)
    connection = Mock(autocommit=False)
    getattr(connection, failure).side_effect = OSError("acknowledgement lost")

    def claim(*args, **kwargs):
        with module.transaction(lambda: connection):
            raise error

    dal.claim.side_effect = claim
    with pytest.raises(OSError):
        runtime.begin_writer("all_kvk")
    assert not error.transaction_released
    dal.withdraw_unstarted.assert_not_called()
    dal.claim.assert_called_once()
    dal.connect.assert_not_called()


def test_terminal_refusal_withdrawal_unknown_is_not_replayed(tmp_path, monkeypatch, caplog):
    import logging

    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(tmp_path)
    error = refusal(-2)
    error.transaction_released = True
    dal.claim.side_effect = error
    dal.withdraw_unstarted.side_effect = OSError("private acknowledgement detail")
    sleep = Mock()
    monkeypatch.setattr(module.time, "sleep", sleep)
    with caplog.at_level(logging.INFO), pytest.raises(OSError):
        runtime.begin_writer("all_kvk")
    dal.claim.assert_called_once()
    dal.withdraw_unstarted.assert_called_once_with(dal.request.return_value)
    sleep.assert_not_called()
    dal.connect.assert_not_called()
    assert '"outcome":"withdrawal_unknown"' in caplog.text
    assert "private acknowledgement detail" not in caplog.text


def test_configuration_terminal_refusal_withdraws_without_provider_entry(tmp_path):
    from tests.test_legacy_export_snapshot import producer_runtime

    runtime, dal = producer_runtime(
        tmp_path, configuration={"config": {"destinations": ["file-a"]}}
    )
    error = refusal(-3)
    error.transaction_released = True
    dal.claim.side_effect = error
    with pytest.raises(module.CoordinationLockRefused):
        with runtime.configuration_requests():
            pytest.fail("Terminal refusal must not start a provider operation")
    dal.withdraw_unstarted.assert_called_once_with(dal.request.return_value)
    dal.transition.assert_not_called()
    dal.uncertain.assert_not_called()
