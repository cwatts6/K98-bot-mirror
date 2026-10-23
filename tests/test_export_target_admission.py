"""Retired queued work cannot reacquire ownership or stall unrelated admission."""

from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import digest
from services.export_coordination_dal import ExportCoordinationDAL
from services.export_execution_dal import ExportExecutionDAL
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_recovery_service import ExportRecoveryAdapter
from services.export_runtime_composition import RuntimeRegistration
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_runtime_composition import registration_fixture

contained_job = fixture_module.contained_job
pytestmark = fixture_module.pytestmark


def enqueue(f, *, file_id, ticket, state="ready", account="test-account"):
    job = str(uuid4())
    f.sql.execute(
        "INSERT #ExportJob (JobID,ConsumerKind,AccountKey,DestinationSetHash,InputHash,"
        "SpoolKey,SpoolBytes,StorageOwner,EnqueueSequence,State,OwnerID,Fence,Version,CreatedUTC,"
        "UpdatedUTC,Actor,Reason,ProvenanceJson) SELECT ?,'scan_data',?,CAST(? AS binary(32)),"
        "CAST(? AS binary(32)),SpoolKey,SpoolBytes,StorageOwner,?,?,?,?,1,CreatedUTC,UpdatedUTC,"
        "Actor,Reason,? FROM #ExportJob WHERE JobID=?",
        job,
        account,
        digest([file_id]),
        digest(job),
        ticket,
        state,
        str(uuid4()) if state == "failed" else None,
        1 if state == "failed" else 0,
        '{"safe_retry":{"requested":true}}' if state == "failed" else "{}",
        f.job,
    )
    for key in ("account:" + account, "destination:" + file_id):
        f.sql.execute(
            "IF NOT EXISTS (SELECT 1 FROM #ExportResource WHERE ResourceKey=?) "
            "INSERT #ExportResource (ResourceKey,ResourceKind,Fence,Version) VALUES (?,?,0,1)",
            key,
            key,
            key.split(":", 1)[0],
        )
        f.insert("ExportJobResource", dict(JobID=job, ResourceKey=key))
    f.sql.commit()
    return job


@pytest.mark.parametrize("consumer", ["scan_data", "all_kvk", "new_source"])
def test_released_target_is_available_only_to_normal_legacy_jobs(contained_job, consumer):
    from services.export_target_admission_dal import AVAILABLE_JOB_TARGETS_SQL, contained_resources

    f = contained_job
    f.apply()
    action = str(uuid4())
    f.sql.execute(
        "INSERT #ExportLegacyCloseout SELECT ?,JobID,ContainmentID,AccountKey,1,?,?,?,?,'fixture closeout',SYSUTCDATETIME() FROM #ExportTargetContainment",
        action,
        b"s" * 32,
        b"h" * 32,
        str(uuid4()),
        "recovery:" + action,
    )
    job = enqueue(f, file_id="old-file", ticket=2)
    if consumer == "all_kvk":
        f.sql.execute("UPDATE #ExportJob SET ConsumerKind='all_kvk',KVK_NO=16 WHERE JobID=?", job)
    elif consumer == "new_source":
        f.sql.execute(
            "UPDATE #ExportJob SET ConsumerKind='new_source',SourceKey='snapshot_report_v1',IntentID=?,KVK_NO=16,PoolEpoch=1 WHERE JobID=?",
            str(uuid4()),
            job,
        )
    cursor = f.connect().cursor()
    available = cursor.execute(
        "SELECT JobID FROM dbo.ExportJob WHERE JobID=?" + AVAILABLE_JOB_TARGETS_SQL, job
    ).fetchval()
    assert (available is not None) == (consumer != "new_source")
    assert bool(contained_resources(cursor, ["destination:old-file"], consumer=consumer)) == (
        consumer == "new_source"
    )
    # Non-job callers, including rollover, retain the permanent fence by default.
    assert contained_resources(cursor, ["destination:old-file"])


@pytest.mark.parametrize("state", ["ready", "failed"])
@pytest.mark.parametrize("account", ["test-account", "other-account"])
def test_retired_queue_preserved_while_unrelated_job_can_claim(contained_job, state, account):
    f = contained_job
    f.apply()
    retired = enqueue(f, file_id="old-file", ticket=2, state=state, account=account)
    healthy = enqueue(f, file_id="healthy-file", ticket=3, account=account)
    original = tuple(f.sql.execute("SELECT * FROM #ExportJob WHERE JobID=?", retired).fetchone())
    dal = ExportCoordinationDAL(
        f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    claim = dal.claim_next(account, storage_owner="disk")
    assert claim.job_id == healthy
    assert (
        tuple(f.sql.execute("SELECT * FROM #ExportJob WHERE JobID=?", retired).fetchone())
        == original
    )
    assert (
        f.sql.execute(
            "SELECT ActiveJobID FROM #ExportResource WHERE ResourceKey='destination:old-file'"
        ).fetchval()
        is None
    )


def test_retired_ready_job_does_not_block_next_legacy_writer(contained_job):
    f = contained_job
    f.apply()
    enqueue(f, file_id="old-file", ticket=2)
    dal = LegacySnapshotDAL(f.connect, output_operations=True)
    # Fixture compiles the authoritative SQL into temporary objects; protected
    # installation attestation is separately tested, not performed against master.
    dal.execution_evidence = True
    preparation = dal.request(
        account="test-account",
        consumer="scan_data",
        kvk_no=None,
        request={
            "operation": str(uuid4()),
            "kind": "scan_data",
            "config": {"consumer": "scan_data", "kvk_no": None, "destinations": ["healthy-file"]},
        },
        storage_owner="disk",
        actor="test",
        reason="temporary admission test",
    )
    claim = dal.claim(
        preparation,
        account="test-account",
        storage_owner="disk",
        stage="preflight",
        resource_keys=("account:test-account",),
    )
    assert claim is not None and claim.preparation_id == preparation


def test_history_for_isolated_files_does_not_enter_unrelated_publication_catalogue(contained_job):
    f = contained_job
    f.apply()
    evidence = ExportExecutionDAL(f.connect)
    assert list(evidence.read_catalogue("test-account", ["healthy-file"])) == []
    retained = list(evidence.read_catalogue("test-account", ["old-file"]))
    assert len(retained) == 1
    assert str(retained[0]["StreamID"]).lower() == f.stream
    assert retained[0]["State"] == "target_contained"


def test_fresh_retired_queue_is_discovered_without_waiting_for_next_failure(contained_job):
    from unittest.mock import Mock

    f = contained_job
    f.apply()
    retired = enqueue(f, file_id="old-file", ticket=2)
    f.sql.execute("UPDATE #ExportJob SET UpdatedUTC=SYSUTCDATETIME() WHERE JobID=?", retired)
    f.sql.commit()
    config = registration_fixture()
    config.update(account="test-account", storage_owner="disk")
    discovery = ExportRecoveryDAL(f.connect, registration=RuntimeRegistration(config))
    assert retired in discovery.pending_jobs()
    adapter = ExportRecoveryAdapter(discovery, Mock(), Mock())
    evidence, _, resolved = adapter.inspect(retired)
    assert not resolved and evidence["outcome"] == "replacement_required"
    assert set(evidence["actions"]) == {"skip_unstarted"}


def test_locked_check_refuses_retired_job_even_with_stale_candidate_list(
    contained_job, monkeypatch
):
    import services.export_coordination_dal as coordination

    f = contained_job
    f.apply()
    retired = enqueue(f, file_id="old-file", ticket=2)
    original_rows = coordination.rows
    first = True

    def stale_candidates(cursor):
        nonlocal first
        actual = original_rows(cursor)
        if first:
            first = False
            return [{"JobID": retired}]
        return actual

    monkeypatch.setattr(coordination, "rows", stale_candidates)
    dal = ExportCoordinationDAL(
        f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    assert dal.claim_next("test-account", storage_owner="disk") is None
    assert f.sql.execute("SELECT OwnerID FROM #ExportJob WHERE JobID=?", retired).fetchval() is None
    assert (
        f.sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 0
    )


def test_healthy_older_job_still_preserves_queue_order(contained_job):
    f = contained_job
    f.apply()
    enqueue(f, file_id="healthy-file", ticket=2)
    dal = LegacySnapshotDAL(f.connect, output_operations=True)
    dal.execution_evidence = True
    preparation = dal.request(
        account="test-account",
        consumer="scan_data",
        kvk_no=None,
        request={"operation": str(uuid4())},
        storage_owner="disk",
        actor="test",
        reason="test",
    )
    assert (
        dal.claim(
            preparation,
            account="test-account",
            storage_owner="disk",
            stage="preflight",
            resource_keys=("account:test-account",),
        )
        is None
    )
