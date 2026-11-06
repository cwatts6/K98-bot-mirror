"""A contended checkpoint waits before execution; unknown commits never replay."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from services.export_coordination_dal import _mutex
from services.export_execution_dal import EvidenceCommitUnknown, ExportExecutionDAL
from services.export_execution_lock import execution_account_lock


class Cursor:
    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail
        self.description = None
        self.current = None
        self.closed = False

    def execute(self, sql, *args):
        self.calls.append((sql, args))
        self.current = (
            "release"
            if "sp_releaseapplock" in sql
            else "lock" if "sp_getapplock" in sql else "procedure"
        )
        if self.fail == self.current:
            raise OSError("synthetic missing acknowledgment")
        self.description = (("LockResult",),) if self.current == "release" else (("Version",),)
        return self

    def fetchone(self):
        return (0,) if self.current == "release" else (9,)

    def fetchall(self):
        return []

    def nextset(self):
        if self.fail == "commit" and self.current == "procedure":
            raise OSError("synthetic commit reply lost after SELECT")
        return None

    def close(self):
        self.closed = True


@pytest.mark.parametrize("kind", ["event", "stream"])
def test_checkpoint_runs_once_under_same_session_admission_and_releases_before_return(kind):
    cursor = Cursor()
    connection = SimpleNamespace(autocommit=False, cursor=lambda: cursor, close=Mock())
    result = ExportExecutionDAL(lambda: connection).transition(
        kind, AccountKey="synthetic", StreamID=str(uuid4())
    )
    assert result == {"Version": 9}
    assert connection.autocommit
    assert ["sp_getapplock" in sql for sql, _ in cursor.calls] == [True, False, False]
    assert "@LockOwner='Session',@LockTimeout=1000" in cursor.calls[0][0]
    assert "sp_releaseapplock" in cursor.calls[-1][0]
    assert cursor.calls[0][1] == cursor.calls[-1][1]
    assert cursor.closed
    connection.close.assert_called_once()


@pytest.mark.parametrize("failure", ["lock", "procedure", "commit", "release"])
def test_no_checkpoint_replay_or_success_on_unknown_admission_commit_or_release(failure):
    cursor = Cursor(failure)
    connection = SimpleNamespace(autocommit=False, cursor=lambda: cursor, close=Mock())
    connect = Mock(return_value=connection)
    with pytest.raises(EvidenceCommitUnknown):
        ExportExecutionDAL(connect).transition(
            "event", AccountKey="synthetic", StreamID=str(uuid4())
        )
    connect.assert_called_once()
    assert sum(sql.startswith("EXEC dbo.") for sql, _ in cursor.calls) == (
        0 if failure == "lock" else 1
    )
    assert cursor.closed
    connection.close.assert_called_once()


@pytest.mark.parametrize("account", [None, "", " trailing ", "é", "a" * 129])
def test_invalid_account_cannot_take_different_sql_lock(account):
    cursor = Cursor()
    with pytest.raises(ValueError):
        with execution_account_lock(cursor, account):
            pytest.fail("Invalid account admitted")
    assert not cursor.calls


@pytest.mark.parametrize("kwargs", [{"wait_ms": 1001}, {"wait_ms": True}, {"owner": "Other"}])
def test_lock_options_are_bounded_and_never_sql_input(kwargs):
    cursor = Cursor()
    with pytest.raises(ValueError):
        _mutex(cursor, "account:synthetic", **kwargs)
    assert not cursor.calls
