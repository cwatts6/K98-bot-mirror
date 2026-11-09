"""Configuration previews own short reads; settlement still owns locked state."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.recovery_sql_snapshot import RecoveryObservationCleanupUnknown
from kvk.dal.new_source_import_dal import SourceConflict
from services import config_preparation_recovery_dal as module


@pytest.fixture
def reader(monkeypatch):
    cn = Mock(autocommit=False, timeout=15)
    connect = Mock(return_value=cn)
    target = SimpleNamespace(
        server="fixture",
        database="test",
        preparation_id=str(uuid4()),
        account="a",
        resources=(("account:a", 1),),
    )
    one = Mock(side_effect=[{"server": "fixture", "database": "test"}, None, {"n": 0}, {"n": 0}])
    monkeypatch.setattr(module, "one", one)
    monkeypatch.setattr(module, "rows", lambda cursor: [])
    return SimpleNamespace(
        cn=cn,
        connect=connect,
        target=target,
        one=one,
        dal=module.ConfigPreparationRecoveryDAL(connect),
    )


@pytest.mark.parametrize("operation", ["identity", "pending_recovery", "target_data", "snapshot"])
def test_all_read_routes_own_snapshot_without_writer_locks(reader, operation):
    r = reader
    if operation == "identity":
        r.dal.identity()
    elif operation == "pending_recovery":
        assert r.dal.pending_recovery(account="a", storage_owner="local") == []
    elif operation == "target_data":
        r.dal.target_data(r.target.preparation_id, account="a", storage_owner="local")
    else:
        r.dal.snapshot(r.target)
    sql = " ".join(call.args[0].upper() for call in r.cn.cursor.return_value.execute.call_args_list)
    assert all(term not in sql for term in ("SP_GETAPPLOCK", "UPDLOCK", "HOLDLOCK"))
    assert r.cn.timeout == 3
    assert [call.args for call in r.cn.set_attr.call_args_list] == [(1227, 0x20), (1227, 0x02)]
    assert r.cn.rollback.call_count == 2
    r.cn.close.assert_called_once()
    r.cn.commit.assert_not_called()


@pytest.mark.parametrize("close_fails", [False, True])
def test_failure_is_not_retried_and_cleanup_uncertainty_is_explicit(reader, close_fails):
    error = OSError("first read failure")
    reader.one.side_effect = error
    if close_fails:
        reader.cn.close.side_effect = OSError("private close detail")
    with pytest.raises(RecoveryObservationCleanupUnknown if close_fails else OSError) as caught:
        reader.dal.snapshot(reader.target)
    assert (caught.value.__cause__ if close_fails else caught.value) is error
    reader.connect.assert_called_once()
    reader.cn.close.assert_called_once()
    reader.cn.commit.assert_not_called()


def test_foreign_target_data_is_refused_and_closed(reader):
    reader.one.side_effect = [None]
    with pytest.raises(SourceConflict, match="outside"):
        reader.dal.target_data(
            reader.target.preparation_id, account="foreign", storage_owner="local"
        )
    reader.cn.close.assert_called_once()
    reader.cn.commit.assert_not_called()


def test_mutation_snapshot_defaults_to_original_locks(reader, monkeypatch):
    mutex = Mock()
    monkeypatch.setattr(module, "_mutex", mutex)
    cursor = reader.cn.cursor.return_value
    reader.dal._snapshot(cursor, reader.target)
    assert [call.args[1] for call in mutex.call_args_list] == ["account:a", "account:a"]
    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert sum(sql.count("UPDLOCK,HOLDLOCK") for sql in statements) == 7


def test_settlement_rejects_stale_preview_before_any_write(reader, monkeypatch):
    mutex = Mock()
    monkeypatch.setattr(module, "_mutex", mutex)
    with pytest.raises(SourceConflict, match="raced"):
        reader.dal.settle(reader.target, {}, {"actor": "test", "reason": "test"})
    assert mutex.call_count == 2
    statements = [
        call.args[0].upper() for call in reader.cn.cursor.return_value.execute.call_args_list
    ]
    assert not any(sql.startswith(("UPDATE", "EXEC DBO.USP_")) for sql in statements)
    reader.cn.commit.assert_not_called()
