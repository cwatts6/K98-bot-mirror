"""First failure, unknown commit and physical SQL custody are separate facts."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.recovery_sql_snapshot import recovery_snapshot
from kvk.dal.new_source_import_dal import UncertainCommit, transaction
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL


@pytest.mark.parametrize("failure", [OSError("body"), KeyboardInterrupt()])
@pytest.mark.parametrize("cleanup", ["rollback", "close", "both"])
def test_source_cleanup_keeps_first_cause_and_fences_failed_rollback(failure, cleanup):
    cn = Mock(autocommit=False)
    if cleanup in {"rollback", "both"}:
        cn.rollback.side_effect = OSError("rollback")
    if cleanup in {"close", "both"}:
        cn.close.side_effect = OSError("close")
    with pytest.raises(Exception) as caught:
        with transaction(lambda: cn):
            raise failure
    assert caught.value.__cause__ is failure
    cn.rollback.assert_called_once()
    if cleanup in {"rollback", "both"}:
        from core import sql_connection_custody as custody

        cn.close.assert_not_called()
        held = next(iter(custody._holds.values())).retained_connection
        assert held.resource is cn.cursor.return_value
    else:
        cn.close.assert_called_once()
    cn.commit.assert_not_called()


def test_commit_uncertainty_survives_failed_close():
    cn = Mock(autocommit=False)
    first = OSError("commit acknowledgement")
    cn.commit.side_effect = first
    cn.close.side_effect = OSError("close")
    with pytest.raises(UncertainCommit) as caught:
        with transaction(lambda: cn):
            pass
    assert caught.value.__cause__ is first
    cn.rollback.assert_not_called()
    cn.close.assert_called_once()


def test_cancellation_during_commit_is_unknown_not_replayable():
    cn = Mock(autocommit=False)
    first = KeyboardInterrupt()
    cn.commit.side_effect = first
    with pytest.raises(BaseException) as caught:
        with transaction(lambda: cn):
            pass
    assert isinstance(caught.value, UncertainCommit)
    assert caught.value.__cause__ is first
    cn.close.assert_called_once()


@pytest.mark.parametrize("entry", ["source", "snapshot", "capture"])
def test_unclosed_connection_is_retained_and_new_admission_refused(entry, monkeypatch):
    from core import sql_connection_custody as custody

    cn = Mock(autocommit=False)
    cn.close.side_effect = OSError("close not acknowledged")
    connect = Mock(return_value=cn)
    if entry == "capture":
        monkeypatch.setattr(
            "services.import_capture_recovery_dal.one",
            lambda _: {"LockResult": 0, "Mode": "NoLock"},
        )
        context = lambda: ImportCaptureRecoveryDAL(SimpleNamespace(connect=connect)).session(
            str(uuid4())
        )
    else:
        context = lambda: (transaction if entry == "source" else recovery_snapshot)(connect)
    with pytest.raises(RuntimeError):
        with context():
            pass
    assert custody.custody_snapshot()["unconfirmed"] == 1
    assert custody.connection_retained(cn)
    with pytest.raises(custody.SqlCleanupUnknown):
        with context():
            pytest.fail("Unconfirmed physical cleanup must not admit another operation")
    connect.assert_called_once()
    assert "close not acknowledged" not in str(custody.custody_snapshot())


@pytest.mark.parametrize("release_failure", [0, 1])
def test_capture_stops_at_unknown_guard_release_and_preserves_body_failure(
    monkeypatch, release_failure
):
    cn = Mock()
    cursor = cn.cursor.return_value
    monkeypatch.setattr(
        "services.import_capture_recovery_dal.one", lambda _: {"LockResult": 0, "Mode": "NoLock"}
    )
    releases = []

    def execute(sql, *args):
        if "sp_releaseapplock" in sql:
            releases.append(args[0])
            if len(releases) == release_failure + 1:
                raise OSError("release failed")

    cursor.execute.side_effect = execute
    first = ValueError("body failure")
    with pytest.raises(Exception) as caught:
        with ImportCaptureRecoveryDAL(SimpleNamespace(connect=lambda: cn)).session(str(uuid4())):
            raise first
    assert caught.value.__cause__ is first
    assert len(releases) == release_failure + 1
    cursor.close.assert_not_called()
    cn.close.assert_not_called()


def test_capture_lost_grant_ack_attempts_release_before_close(monkeypatch):
    cn = Mock()
    cursor = cn.cursor.return_value
    first = OSError("grant reply lost")
    monkeypatch.setattr("services.import_capture_recovery_dal.one", lambda _: {"Mode": "NoLock"})

    def execute(sql, *args):
        if "sp_getapplock" in sql:
            raise first

    cursor.execute.side_effect = execute
    with pytest.raises(OSError) as caught:
        with ImportCaptureRecoveryDAL(SimpleNamespace(connect=lambda: cn)).session(str(uuid4())):
            pytest.fail("Unknown grant must not enter capture")
    assert caught.value is first
    assert sum("sp_releaseapplock" in c.args[0] for c in cursor.execute.call_args_list) >= 1
    cn.close.assert_called_once()


@pytest.mark.parametrize("phase", ["body", "commit"])
def test_capture_transaction_keeps_original_failure_when_rollback_and_cursor_close_fail(phase):
    from core.sql_connection_custody import SqlCleanupUnknown
    from services.import_capture_recovery_dal import capture_transaction

    cn = Mock()
    cursor = cn.cursor.return_value
    first = OSError("first failure")

    def execute(sql):
        if sql.startswith("IF @@TRANCOUNT"):
            raise OSError("rollback failure")
        if sql == "COMMIT TRANSACTION" and phase == "commit":
            raise first

    cursor.execute.side_effect = execute
    cursor.close.side_effect = OSError("cursor cleanup")
    with pytest.raises(UncertainCommit if phase == "commit" else SqlCleanupUnknown) as caught:
        with capture_transaction(cn):
            if phase == "body":
                raise first
    error = caught.value
    while error.__cause__ is not None:
        error = error.__cause__
    assert error is first
    cursor.close.assert_not_called()


def test_borrowed_transaction_cannot_prove_physical_release():
    from kvk.dal.new_source_admin_dal import _BorrowedConnection
    from services import export_contention
    from tests.test_export_contention import refusal

    cursor = Mock()
    error = refusal()
    with pytest.raises(export_contention.CoordinationLockRefused):
        with export_contention.transaction(lambda: _BorrowedConnection(cursor)):
            raise error
    assert error.transaction_released is False
    cursor.close.assert_not_called()


@pytest.mark.parametrize("setup", ["cursor", "statement"])
def test_setup_failure_rolls_back_and_closes_without_masking(setup):
    cn = Mock(autocommit=False)
    first = OSError("setup")
    if setup == "cursor":
        cn.cursor.side_effect = first
    else:
        cn.cursor.return_value.execute.side_effect = first
    with pytest.raises(OSError) as caught:
        with transaction(lambda: cn):
            pytest.fail("Setup failure must not enter the transaction")
    assert caught.value is first
    cn.rollback.assert_called_once()
    cn.close.assert_called_once()


def test_committed_effect_survives_unknown_close():
    from core import sql_connection_custody as custody

    cn = Mock(autocommit=False)
    cn.close.side_effect = OSError("close")
    with pytest.raises(custody.SqlCleanupUnknown):
        with transaction(lambda: cn):
            pass
    assert next(iter(custody._holds.values())).effect == "committed"
    cn.rollback.assert_not_called()


def test_busy_with_unconfirmed_close_is_not_retryable_observation():
    from core.sql_connection_custody import SqlCleanupUnknown
    from core.sql_observation import observation
    from tests.test_export_contention import refusal

    cn = Mock(autocommit=False)
    first = refusal()
    cn.close.side_effect = OSError("close")
    with observation(), pytest.raises(SqlCleanupUnknown) as caught:
        with transaction(lambda: cn):
            raise first
    assert caught.value.__cause__ is first
