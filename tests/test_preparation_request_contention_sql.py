"""Request admission retries use isolated SQL tables and never call a producer."""

from concurrent.futures import ThreadPoolExecutor
import os
from threading import Event
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import UncertainCommit
from services.export_contention import CoordinationLockRefused
from services.export_coordination_dal import _mutex
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Local disposable SQL opt-in"
    ),
    pytest.mark.parametrize("recovery", ["scan_data"], indirect=True),
]


def arguments():
    return dict(
        account="a",
        consumer="config",
        kvk_no=None,
        request={"read_configuration": str(uuid4())},
        storage_owner="disk-a",
        actor="system:configuration",
        reason="Read immutable configuration inputs",
    )


def test_configuration_request_waits_for_rolled_back_contention_then_saves_once(
    recovery, monkeypatch
):
    from services import legacy_export_snapshot_dal as module

    holder = recovery.connect()
    _mutex(holder.cursor(), "account:a")
    refused = Event()
    original = module._mutex

    def observe(cursor, key):
        try:
            return original(cursor, key)
        except CoordinationLockRefused:
            refused.set()
            raise

    monkeypatch.setattr(module, "_mutex", observe)
    args = arguments()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(recovery.runtime.dal.request, **args)
            assert refused.wait(3)
            holder.rollback()
            identifier = pending.result(timeout=4)
        assert recovery.runtime.dal.request(**args) == identifier
        row = recovery.owner.execute(
            recovery.rewrite(
                "SELECT State,OwnerID FROM dbo.ExportPreparation WHERE PreparationID=?"
            ),
            identifier,
        ).fetchone()
        assert tuple(row) == ("pending", None)
        assert (
            recovery.owner.execute(
                recovery.rewrite(
                    "SELECT COUNT(*) FROM dbo.ExportPreparation WHERE Actor='system:configuration'"
                )
            ).fetchval()
            == 1
        )
    finally:
        holder.rollback()
        holder.close()


def test_configuration_request_permanent_contention_saves_nothing(recovery):
    holder = recovery.connect()
    _mutex(holder.cursor(), "account:a")
    try:
        with pytest.raises(CoordinationLockRefused) as caught:
            recovery.runtime.dal.request(**arguments())
        assert caught.value.result == -1 and caught.value.transaction_released
        assert (
            recovery.owner.execute(
                recovery.rewrite(
                    "SELECT COUNT(*) FROM dbo.ExportPreparation WHERE Actor='system:configuration'"
                )
            ).fetchval()
            == 0
        )
    finally:
        holder.rollback()
        holder.close()


def test_configuration_request_unknown_commit_is_not_replayed(recovery):
    connections = []

    class LostReply:
        def __init__(self):
            self.inner = recovery.connect()
            connections.append(self)

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def commit(self):
            self.inner.commit()
            raise OSError("synthetic lost commit reply")

    with pytest.raises(UncertainCommit):
        LegacySnapshotDAL(LostReply).request(**arguments())
    assert len(connections) == 1
    assert (
        recovery.owner.execute(
            recovery.rewrite(
                "SELECT COUNT(*) FROM dbo.ExportPreparation WHERE Actor='system:configuration'"
            )
        ).fetchval()
        == 1
    )
