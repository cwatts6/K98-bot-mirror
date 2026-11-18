"""Standalone previews own one consistent read; mutation helpers stay separate."""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from core.recovery_sql_snapshot import RecoveryObservationCleanupUnknown
from kvk.dal import source_output_pool_dal as pools
from services import export_recovery_dal as recovery

KEY = str(uuid4())


@pytest.fixture
def reader(monkeypatch):
    cn = Mock(autocommit=False, timeout=15)
    connect = Mock(return_value=cn)
    config = dict(
        account="a",
        storage_owner="fixture",
        pools=[dict(pool_id=KEY, index_file_id="index", slot_file_ids=["slot"])],
    )
    registration = SimpleNamespace(value=lambda: config)
    for module in (pools, recovery):
        monkeypatch.setattr(module, "rows", lambda _: [])
        monkeypatch.setattr(module, "one", lambda _: dict(SourceKey="snapshot_report_v1"))
    return SimpleNamespace(
        cn=cn,
        connect=connect,
        recovery=recovery.ExportRecoveryDAL(connect, registration=registration),
        pools=pools.SourceOutputPoolDAL(connect),
    )


@pytest.mark.parametrize(
    "method,args",
    [
        ("pending_jobs", ()),
        ("pending_rollovers", ()),
        ("published_outputs", ()),
    ],
)
def test_recovery_discovery_owns_snapshot(reader, method, args):
    getattr(reader.recovery, method)(*args)
    assert reader.cn.timeout == 3
    reader.cn.commit.assert_not_called()
    reader.cn.close.assert_called_once()


@pytest.mark.parametrize(
    "method,args",
    [
        ("choice", (16,)),
        ("is_index", ("index",)),
        ("pending", ("a",)),
        ("completed_setup", (KEY,)),
        ("files", (KEY,)),
    ],
)
def test_pool_discovery_owns_snapshot(reader, method, args):
    getattr(reader.pools, method)(*args)
    assert reader.cn.timeout == 3
    reader.cn.commit.assert_not_called()
    reader.cn.close.assert_called_once()


def test_pool_resolve_failure_closes_snapshot(reader):
    with pytest.raises(pools.SourceConflict):
        reader.pools.resolve(16)
    reader.cn.commit.assert_not_called()
    reader.cn.close.assert_called_once()
    assert reader.cn.timeout == 3


@pytest.mark.parametrize(
    "method", ["snapshot", "export_context", "operation_snapshot", "drain_snapshot"]
)
def test_nested_pool_reads_share_one_cursor(reader, monkeypatch, method):
    seen = []

    def snapshot(cursor, key):
        seen.append(cursor)
        return dict(pool=dict(ActiveKVK=16, SourceKey="snapshot_report_v1", ChoiceID=KEY))

    def operation(cursor, key):
        seen.append(cursor)
        return dict(PoolID=KEY)

    monkeypatch.setattr(reader.pools, "_snapshot", snapshot)
    monkeypatch.setattr(reader.pools, "_operation", operation)
    getattr(reader.pools, method)(KEY)
    reader.connect.assert_called_once()
    assert len({id(c) for c in seen}) == 1
    reader.cn.commit.assert_not_called()
    reader.cn.close.assert_called_once()


@pytest.mark.parametrize("method", ["published_outputs", "repairs"])
def test_recovery_nested_reads_do_not_open_another_connection(reader, monkeypatch, method):
    seen = []

    def job(cursor, key):
        seen.append(cursor)
        return dict(job=dict(CreatedUTC="2026-11-09", DestinationSetHash="00" * 32))

    monkeypatch.setattr(reader.recovery, "_job", job)
    if method == "published_outputs":
        reader.recovery.published_outputs(after=KEY)
    else:
        monkeypatch.setattr(recovery, "rows", lambda _: [dict(JobID=KEY)])
        reader.recovery.repairs(KEY)
    reader.connect.assert_called_once()
    assert len({id(c) for c in seen}) == 1
    reader.cn.commit.assert_not_called()


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_nested_failure_preserved_and_connection_closed(reader, monkeypatch, cleanup_fails):
    original = OSError("first read failure")
    monkeypatch.setattr(reader.pools, "_snapshot", Mock(side_effect=original))
    if cleanup_fails:
        reader.cn.close.side_effect = OSError("cleanup failure")
    with pytest.raises(RecoveryObservationCleanupUnknown if cleanup_fails else OSError) as caught:
        reader.pools.snapshot(KEY)
    assert (caught.value.__cause__ if cleanup_fails else caught.value) is original
    reader.cn.close.assert_called_once()
