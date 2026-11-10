"""Unowned-block previews are consistent observations, never release authority."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.recovery_sql_snapshot import RecoveryObservationCleanupUnknown
from kvk.dal.new_source_import_dal import SourceConflict
from services import unowned_sql_hold_dal as module


@pytest.fixture
def reader(monkeypatch):
    connection = Mock(autocommit=False, timeout=15)
    connect = Mock(return_value=connection)
    dal = module.UnownedSqlHoldDAL(
        SimpleNamespace(
            dal=SimpleNamespace(connect=connect),
            account="a",
            store=SimpleNamespace(storage_owner="local"),
        )
    )
    one = Mock(side_effect=[None, {"n": 0}, None])
    monkeypatch.setattr(module, "one", one)
    monkeypatch.setattr(module, "rows", lambda cursor: [])
    return SimpleNamespace(dal=dal, cn=connection, connect=connect, one=one)


@pytest.mark.parametrize("operation", ["pending", "snapshot", "action"])
def test_read_paths_own_snapshot_without_commit_or_writer_locks(reader, operation):
    r = reader
    if operation == "pending":
        assert r.dal.pending() == []
    elif operation == "action":
        assert r.dal.action(str(uuid4())) is None
    else:
        assert r.dal.snapshot(r.dal.source_id) == {
            "resource": None,
            "producers": [],
            "streams": 0,
            "disposition": None,
        }
    statements = [call.args[0].upper() for call in r.cn.cursor.return_value.execute.call_args_list]
    assert not any(
        "SP_GETAPPLOCK" in sql or "UPDLOCK" in sql or "HOLDLOCK" in sql for sql in statements
    )
    assert r.cn.timeout == 3
    assert [call.args for call in r.cn.set_attr.call_args_list] == [(1227, 0x20), (1227, 0x02)]
    assert r.cn.rollback.call_count == 2
    r.cn.close.assert_called_once()
    r.cn.commit.assert_not_called()


@pytest.mark.parametrize("close_fails", [False, True])
def test_failed_preview_never_retries_or_hides_cleanup_uncertainty(reader, close_fails):
    error = OSError("original read failure")
    reader.one.side_effect = error
    if close_fails:
        reader.cn.close.side_effect = OSError("private cleanup detail")
    with pytest.raises(RecoveryObservationCleanupUnknown if close_fails else OSError) as caught:
        reader.dal.snapshot(reader.dal.source_id)
    if close_fails:
        assert caught.value.__cause__ is error
        assert "private" not in str(caught.value)
    else:
        assert caught.value is error
    reader.connect.assert_called_once()
    reader.cn.close.assert_called_once()
    reader.cn.commit.assert_not_called()


def test_foreign_source_is_rejected_before_opening_connection(reader):
    with pytest.raises(SourceConflict):
        reader.dal.snapshot(str(uuid4()))
    reader.connect.assert_not_called()


def test_mutation_snapshot_retains_both_mutexes_and_all_row_locks(reader, monkeypatch):
    mutex = Mock()
    monkeypatch.setattr(module, "_mutex", mutex)
    cursor = reader.cn.cursor.return_value
    reader.dal._snapshot(cursor)
    assert [call.args[1] for call in mutex.call_args_list] == ["account:a", module.RESOURCE]
    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert "WITH(UPDLOCK,HOLDLOCK)" in statements[0]
    assert statements[1].count("WITH(UPDLOCK,HOLDLOCK)") == 2
    assert "WITH(HOLDLOCK)" in statements[1]
    assert "WITH(UPDLOCK,HOLDLOCK)" in statements[2]


def test_pending_snapshot_preserves_exact_account_source(reader):
    reader.one.side_effect = [{"BlockedReason": "retained"}]
    assert reader.dal.pending() == [reader.dal.source_id]
