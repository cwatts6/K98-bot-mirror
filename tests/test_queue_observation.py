"""Queue discovery and operator previews are not admission or settlement."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.recovery_sql_snapshot import RecoveryObservationCleanupUnknown
from services import export_coordination_dal as module


@pytest.fixture
def reader(monkeypatch):
    cn = Mock(autocommit=False, timeout=15)
    connect = Mock(return_value=cn)
    dal = module.ExportCoordinationDAL(connect, preparations=True, output_operations=True)
    monkeypatch.setattr(module, "rows", lambda cursor: [])
    return SimpleNamespace(cn=cn, connect=connect, dal=dal)


@pytest.mark.parametrize(
    "method,args",
    [
        ("pending_intents", ()),
        ("accounts", ()),
        ("pending_source_jobs", ("a",)),
        ("repair_receipt", (str(uuid4()),)),
    ],
)
def test_discovery_owns_snapshot_without_commit(reader, method, args):
    getattr(reader.dal, method)(*args)
    assert reader.cn.timeout == 3
    assert reader.cn.rollback.call_count == 2
    reader.cn.commit.assert_not_called()
    reader.cn.close.assert_called_once()


def test_operator_snapshot_passes_passive_only_inside_owned_context(reader, monkeypatch):
    snapshot = Mock(return_value={"job": "preview"})
    monkeypatch.setattr(reader.dal, "_operator_snapshot", snapshot)
    key = str(uuid4())
    assert reader.dal.operator_snapshot(key) == {"job": "preview"}
    assert snapshot.call_args.kwargs == {"passive": True}
    reader.cn.commit.assert_not_called()
    reader.cn.close.assert_called_once()


@pytest.mark.parametrize("passive", [False, True])
def test_job_lock_choice_defaults_to_authoritative_state(passive, monkeypatch):
    cursor = Mock()
    monkeypatch.setattr(module, "one", lambda _: None)
    module._job(cursor, str(uuid4()), **({"passive": True} if passive else {}))
    assert ("UPDLOCK,HOLDLOCK" in cursor.execute.call_args.args[0]) is not passive


@pytest.mark.parametrize("close_fails", [False, True])
def test_failed_operator_read_retains_first_error_and_cleanup(reader, monkeypatch, close_fails):
    original = OSError("first read failure")
    monkeypatch.setattr(reader.dal, "_operator_snapshot", Mock(side_effect=original))
    if close_fails:
        reader.cn.close.side_effect = OSError("private close failure")
    with pytest.raises(RecoveryObservationCleanupUnknown if close_fails else OSError) as caught:
        reader.dal.operator_snapshot(str(uuid4()))
    assert (caught.value.__cause__ if close_fails else caught.value) is original
    reader.connect.assert_called_once()
    reader.cn.commit.assert_not_called()
