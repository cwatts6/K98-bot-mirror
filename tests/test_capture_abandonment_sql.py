"""Guided missing-output decisions against real temporary SQL ownership rows."""

from copy import deepcopy
import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.all_kvk_capture_recovery_service import (
    AllKvkCaptureRecovery,
    AllKvkCaptureRecoveryAdapter,
)
from services.import_recovery_service import ImportRecoveryAdapter
from services.legacy_export_snapshot_service import SnapshotUnavailable
from services.recovery_service import RecoveryService
from tests import test_import_capture_recovery_sql as capture_fixtures
from tests.test_guided_recovery import ACTOR, Store

recovery = capture_fixtures.recovery

pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1",
    reason="Explicit local temp-table SQL opt-in required",
)


def adapter_for(r):
    kind = (
        AllKvkCaptureRecoveryAdapter
        if isinstance(r.service, AllKvkCaptureRecovery)
        else ImportRecoveryAdapter
    )
    return kind(r.outcomes, r.service)


def test_failed_capture_exposes_confirmed_skip_and_preserves_sql(recovery, monkeypatch):
    r = recovery
    original = deepcopy(r.outcomes.inspect(r.source))
    monkeypatch.setattr(
        r.runtime,
        "capture",
        lambda *_: (_ for _ in ()).throw(SnapshotUnavailable("missing output")),
    )
    adapter, store = adapter_for(r), Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, r.source)
    failed = service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "resume_capture",
        "Continue committed output",
    )
    assert failed["State"] == "open" and failed["pending_action"] is None
    assert set(failed["evidence"]["actions"]) == {"abandon_capture"}
    assert store.actions[0]["State"] == "not_applied"
    # A previously dispatched callback cannot resume after the failure checkpoint.
    with pytest.raises(SourceConflict, match="admin decision"):
        r.service.run(
            r.source, store.actions[0]["EvidenceHash"], "recovery:" + store.actions[0]["ActionID"]
        )
    resolved = service.execute(
        ACTOR,
        failed["IncidentID"],
        failed["Revision"],
        failed["EvidenceHash"],
        "abandon_capture",
        "Accept no spreadsheet export",
    )
    assert resolved["State"] == "resolved"
    assert resolved["evidence"]["outcome"] == "export_skipped"
    assert "not claim the spreadsheet" in resolved["evidence"]["explanation"]
    assert len(store.actions) == 2 and store.actions[1]["State"] == "verified"
    final = r.outcomes.inspect(r.source)
    assert not final["resources"] and final["preparation"]["State"] == "unavailable"
    assert final["preparation"]["JobID"] is None
    assert final["execution"] == original["execution"]
    assert final["preparation"]["RequestJson"] == original["preparation"]["RequestJson"]
    # Later work sees an unowned resource, rather than discovering the old block.
    resource = r.owner.execute(
        r.rewrite("SELECT ActivePreparationID,OwnerID,BlockedReason FROM dbo.ExportResource")
    ).fetchone()
    assert tuple(resource) == (None, None, None)


def test_unknown_abandon_ack_reconciles_same_receipt_once(recovery, monkeypatch):
    r = recovery
    adapter, store = adapter_for(r), Store()
    service = RecoveryService(store, {adapter.kind: adapter}, admin_id=1, guild_id=2, channel_id=3)
    row = service.review_source(ACTOR, adapter.kind, r.source)
    original = r.service.abandon

    def lose_ack(*args):
        original(*args)
        raise TimeoutError("lost commit acknowledgement")

    monkeypatch.setattr(r.service, "abandon", lose_ack)
    done = service.execute(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "abandon_capture",
        "Accept no export",
    )
    assert done["State"] == "resolved" and store.actions[0]["State"] == "verified"
    before = r.outcomes.inspect(r.source)["token"]
    assert service.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert r.outcomes.inspect(r.source)["token"] == before


@pytest.mark.parametrize("obstacle", ["active", "stale", "queued", "provider", "foreign"])
def test_abandonment_rejects_unproven_or_foreign_release(recovery, obstacle):
    r = recovery
    token = r.outcomes.inspect(r.source)["token"]
    held = None
    if obstacle == "active":
        held = r.parameter("k98-legacy-output-snapshot")
        r.owner.execute(
            "EXEC sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0",
            held,
        )
    elif obstacle == "stale":
        token = "0" * 64
    elif obstacle == "queued":
        r.service.run(r.source, token, "recovery:queue")
        token = r.outcomes.inspect(r.source)["token"]
    elif obstacle == "foreign":
        r.owner.execute(
            r.rewrite(
                "UPDATE dbo.ExportPreparation SET StorageOwner='foreign' WHERE PreparationID=?"
            ),
            r.source,
        )
    else:
        p = r.outcomes.inspect(r.source)["preparation"]
        r.owner.execute(
            r.rewrite("""INSERT dbo.ExportExecutionStream
            (StreamID,SessionID,AccountKey,ActiveAccountKey,PreparationID,OwnerID,Fence,ClaimVersion,
             RegistrationHash,SnapshotHash,ScopeJson,Purpose,State,Version,LastSequence,ChildIdentity,CreatedUTC)
            VALUES (NEWID(),NEWID(),?,?,?, ?,?,?,0x01,0x02,N'{}','probe','open',1,0,NEWID(),SYSUTCDATETIME())"""),
            p["AccountKey"],
            p["AccountKey"],
            r.source,
            p["OwnerID"],
            p["Fence"],
            p["Version"],
        )
    try:
        with pytest.raises(SourceConflict):
            r.service.abandon(r.source, token, "recovery:test", "Accept no export")
    finally:
        if held:
            r.owner.execute("EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", held)
    state = r.owner.execute(
        r.rewrite("SELECT State,GenerationJson FROM dbo.ExportPreparation WHERE PreparationID=?"),
        r.source,
    ).fetchone()
    assert state[0] != "unavailable" and "capture_abandoned" not in json.loads(state[1] or "{}")


def test_missing_spool_can_be_skipped_without_deleting_evidence(recovery, monkeypatch):
    r = recovery
    token = r.outcomes.inspect(r.source)["token"]
    enqueue = r.runtime.enqueue_snapshot
    monkeypatch.setattr(
        r.runtime, "enqueue_snapshot", lambda *_: (_ for _ in ()).throw(TimeoutError())
    )
    with pytest.raises(TimeoutError):
        r.service.run(r.source, token, "recovery:original")
    monkeypatch.setattr(r.runtime, "enqueue_snapshot", enqueue)
    before = r.outcomes.inspect(r.source)
    monkeypatch.setattr(
        r.runtime, "verified_snapshot", lambda *_: (_ for _ in ()).throw(FileNotFoundError())
    )
    monkeypatch.setattr(r.runtime, "enqueue_snapshot", r.runtime.verified_snapshot)
    action = dict(ActionKind="queue_capture", ActionID=str(uuid4()), EvidenceHash=before["token"])
    assert adapter_for(r).reconcile(r.source, action) == "not_applied"
    row = r.outcomes.inspect(r.source)
    # Even a caller that read the old spool before the failure cannot enqueue it:
    # the coordinator repeats the fence under its account/preparation row locks.
    from services.export_coordination_dal import ExportCoordinationDAL, JobSpec

    prep = row["preparation"]
    coordinator = ExportCoordinationDAL(r.outcomes.connect, preparations=True)
    with pytest.raises(SourceConflict, match="immutable job inputs"):
        coordinator.enqueue(
            JobSpec(
                account=prep["AccountKey"],
                consumer=prep["ConsumerKind"],
                kvk_no=prep["KVK_NO"],
                input_hash=bytes(prep["SpoolHash"]),
                destinations=("registered",),
                actor="test",
                reason="old queued caller",
                spool_key=prep["SpoolKey"],
                spool_bytes=prep["SpoolBytes"],
                storage_owner=prep["StorageOwner"],
            ),
            preparation_id=r.source,
        )
    r.service.abandon(r.source, row["token"], "recovery:skip", "Accept no export")
    final = r.outcomes.inspect(r.source)
    assert final["preparation"]["SpoolKey"] == before["preparation"]["SpoolKey"]
    assert final["preparation"]["SpoolHash"] == before["preparation"]["SpoolHash"]
    assert final["execution"] == before["execution"]
    assert adapter_for(r).inspect(r.source)[2]
