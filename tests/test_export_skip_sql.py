"""Real temporary SQL verifies skip receipts, stale workers and resumed eligibility."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import Claim, ExportCoordinationDAL
from services.export_recovery_service import ExportRecoveryAdapter, job_token
from tests import test_export_recovery_sql as fixtures

scoped_jobs = fixtures.scoped_jobs
pytestmark = pytest.mark.skipif(
    os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Explicit temporary SQL opt-in"
)


def setup(scoped_jobs, *, consumer="scan_data", state="failed"):
    discovery, ids, sql = scoped_jobs
    job_id = ids["legacy"]
    sql.execute(
        "UPDATE #ExportJob SET ConsumerKind=?,KVK_NO=?,State=? WHERE JobID=?",
        consumer,
        7 if consumer == "all_kvk" else None,
        state,
        job_id,
    )
    sql.commit()
    coordinator = ExportCoordinationDAL(discovery.connect)
    return ExportRecoveryAdapter(discovery, coordinator, None), job_id, sql, ids


@pytest.mark.parametrize("consumer", ["scan_data", "all_kvk"])
def test_lost_ack_preserves_input_and_cannot_retry(scoped_jobs, consumer):
    adapter, job_id, sql, _ = setup(scoped_jobs, consumer=consumer)
    before = adapter.discovery.job(job_id)
    evidence, token, resolved = adapter.inspect(job_id)
    assert not resolved and "skip_unstarted" in evidence["actions"]
    action_id = str(uuid4())
    action = dict(
        ActionID=action_id,
        ActionKind="skip_unstarted",
        EvidenceHash=token,
        Reason="Skip this export",
    )
    adapter.execute(job_id, "skip_unstarted", token, "recovery:" + action_id, action["Reason"])
    # Simulate losing the acknowledgement, then reconstruct the adapter.
    restarted = ExportRecoveryAdapter(adapter.discovery, adapter.coordinator, None)
    assert restarted.reconcile(job_id, action) == "verified"
    after = adapter.discovery.job(job_id)
    for key in (
        "JobID",
        "InputHash",
        "SpoolKey",
        "SpoolBytes",
        "OwnerID",
        "Fence",
        "DestinationSetHash",
    ):
        assert before["job"][key] == after["job"][key]
    assert after["job"]["Version"] == before["job"]["Version"] + 1
    assert restarted.inspect(job_id)[2]
    assert restarted.inspect(job_id)[0]["outcome"] == "export_skipped"
    with pytest.raises(SourceConflict, match="skipped"):
        adapter.coordinator.request_safe_retry(
            job_id,
            "account",
            expected_version=after["job"]["Version"],
            expected_epoch=None,
            actor="admin",
            reason="retry",
        )
    # A later owner of the shared account resource is not part of this repair.
    assert sql.execute("SELECT COUNT(*) FROM #ExportJob").fetchval() == 5


@pytest.mark.parametrize("state", ["running", "uncertain"])
def test_release_fences_old_worker_and_later_job_can_claim(scoped_jobs, state):
    adapter, job_id, sql, ids = setup(scoped_jobs, state=state)
    before = adapter.discovery.job(job_id)["job"]
    sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=?,Fence=1,Version=2 "
        "WHERE ResourceKey IN (SELECT ResourceKey FROM #ExportJobResource WHERE JobID=?)",
        job_id,
        before["OwnerID"],
        job_id,
    )
    sql.commit()
    snapshot = adapter.discovery.job(job_id)
    old = Claim(
        job_id,
        "account",
        before["OwnerID"],
        1,
        before["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in snapshot["resources"]),
    )
    adapter.execute(
        job_id, "skip_unstarted", job_token(snapshot), "recovery:" + str(uuid4()), "Skip"
    )
    assert all(r["ActiveJobID"] is None for r in adapter.discovery.job(job_id)["resources"])
    with pytest.raises(SourceConflict):
        adapter.coordinator.authorize(old)
    with pytest.raises(SourceConflict):
        adapter.coordinator.begin_attempt(old, {}, [])
    # Another retained job in the same account/storage becomes eligible normally.
    sql.execute(
        "UPDATE #ExportJob SET StorageOwner='disk',State='ready',OwnerID=NULL,Fence=0 WHERE JobID=?",
        ids["foreign-disk"],
    )
    sql.commit()
    claim = adapter.coordinator.claim_next("account", storage_owner="disk")
    assert claim.job_id == ids["foreign-disk"] and claim.fence > old.fence
    assert adapter.coordinator.authorize(claim)["State"] == "running"


@pytest.mark.parametrize("bad", ["stale", "foreign", "attempt", "stream", "ownership"])
def test_skip_refuses_conflicting_evidence(scoped_jobs, bad):
    adapter, job_id, sql, ids = setup(scoped_jobs)
    snapshot = adapter.discovery.job(job_id)
    token = job_token(snapshot)
    job = snapshot["job"]
    if bad == "stale":
        sql.execute("UPDATE #ExportJob SET Version=Version+1 WHERE JobID=?", job_id)
    elif bad == "foreign":
        job_id = ids["foreign-disk"]
    elif bad == "attempt":
        sql.execute(
            "INSERT #ExportAttempt (AttemptID,JobID,ConsumerKind,AttemptNo,OwnerID,Fence,Phase,RemoteSequence,Version,CreatedUTC,UpdatedUTC,ManifestHash,ManifestJson,PartCount) "
            "VALUES (?,?,'scan_data',1,?,1,'private_started',1,1,SYSUTCDATETIME(),SYSUTCDATETIME(),CONVERT(binary(32),0),'{}',1)",
            str(uuid4()),
            job_id,
            job["OwnerID"],
        )
    elif bad == "stream":
        sql.execute(
            "INSERT #ExportExecutionStream(StreamID,SessionID,AccountKey,ActiveAccountKey,JobID,OwnerID,Fence,ClaimVersion,RegistrationHash,SnapshotHash,ScopeJson,Purpose,State,Version,LastSequence,ChildIdentity,CreatedUTC) "
            "VALUES (?,?,'account','account',?,?,1,1,CONVERT(binary(32),0),CONVERT(binary(32),0),'{}','probe','open',1,0,?,SYSUTCDATETIME())",
            str(uuid4()),
            str(uuid4()),
            job_id,
            job["OwnerID"],
            str(uuid4()),
        )
    else:
        sql.execute(
            "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=?,Fence=2 WHERE ResourceKey='account:account'",
            job_id,
            str(uuid4()),
        )
    sql.commit()
    # DAL repeats the absence check even when the UI evidence token omitted stream membership.
    with pytest.raises(SourceConflict):
        adapter.execute(job_id, "skip_unstarted", token, "recovery:" + str(uuid4()), "Skip")
    current = adapter.discovery.job(ids["legacy"])
    assert "export_skipped" not in json.loads(current["job"]["ProvenanceJson"])


def test_other_owner_and_its_block_remain_intact(scoped_jobs):
    adapter, job_id, sql, ids = setup(scoped_jobs)
    sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=?,Fence=8,BlockedReason='Other unresolved work' WHERE ResourceKey='account:account'",
        ids["foreign-disk"],
        str(uuid4()),
    )
    sql.commit()
    before = adapter.discovery.job(job_id)
    adapter.execute(job_id, "skip_unstarted", job_token(before), "recovery:" + str(uuid4()), "Skip")
    after = adapter.discovery.job(job_id)
    assert before["resources"] == after["resources"]
    assert adapter.inspect(job_id)[2]


@pytest.mark.parametrize("state", ["ready", "waiting"])
def test_unowned_queue_cancellation_preserves_zero_fence(scoped_jobs, state):
    adapter, job_id, sql, _ = setup(scoped_jobs)
    sql.execute("UPDATE #ExportJob SET State=?,OwnerID=NULL,Fence=0 WHERE JobID=?", state, job_id)
    sql.commit()
    token = job_token(adapter.discovery.job(job_id))
    adapter.execute(job_id, "skip_unstarted", token, "recovery:" + str(uuid4()), "Skip")
    job = adapter.discovery.job(job_id)["job"]
    assert (job["State"], job["OwnerID"], job["Fence"]) == ("cancelled", None, 0)
    assert adapter.inspect(job_id)[2]


def test_new_source_cannot_use_legacy_skip_capability(scoped_jobs):
    adapter, _, _, ids = setup(scoped_jobs)
    with pytest.raises(SourceConflict):
        adapter.coordinator.skip_unstarted(
            ids["registered"],
            "account",
            storage_owner=None,
            expected_version=1,
            actor="admin",
            reason="Skip",
        )
