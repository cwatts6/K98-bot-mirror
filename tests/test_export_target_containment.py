"""Authority reconstruction and lost-reply verification over temporary SQL."""

import json
import os
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, digest
from services.export_execution_dal import ExportExecutionDAL
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_runtime_composition import RuntimeRegistration
from services.export_target_containment import ExportTargetContainment
from services.export_target_containment_dal import ExportTargetContainmentDAL
from services.legacy_export_snapshot_service import configuration_digest
from tests import test_export_target_containment_sql as fixture_module
from tests.test_config_read_containment import private_store
from tests.test_export_runtime_composition import registration_fixture

contained_job = fixture_module.contained_job
pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit local temporary SQL opt-in"
)


@pytest.fixture
def recovery(contained_job):
    f = contained_job
    config = registration_fixture()
    config.update(account="test-account", storage_owner="disk")
    config["legacy_configuration"]["scan_data"]["destinations"] = ["old-file"]
    config["protected_file_ids"] = sorted(
        {
            file_id
            for scope in config["legacy_configuration"].values()
            for file_id in scope["destinations"]
        }
    )
    registration = RuntimeRegistration(config)
    f.sql.execute(
        "UPDATE #ExportExecutionStream SET RegistrationHash=CAST(? AS binary(32))",
        bytes.fromhex(configuration_digest(config["legacy_configuration"]["scan_data"])),
    )
    docs = {}
    service = ExportTargetContainment(
        dal=ExportTargetContainmentDAL(f.connect),
        discovery=ExportRecoveryDAL(f.connect, registration=registration),
        execution=ExportExecutionDAL(f.connect),
        store=private_store(docs),
        registration=registration,
    )
    return service, f, docs


def test_unknown_write_isolated_from_original_targets_without_claiming_delivery(recovery):
    service, f, docs = recovery
    report = service.inspect(f.job)
    assert report["targets"] == ["old-file"] and report["business_resolved"] is False
    actor = "recovery:" + str(uuid4())
    result = service.apply(f.job, token=report["token"], actor=actor, reason="Retire this output")
    assert result["outcome"] == "targets_isolated" and result["business_resolved"] is False
    assert len(docs) == 1
    audit = json.loads(next(iter(docs.values())))
    assert audit["child_termination_verified"] is False and audit["provider_success"] is False
    assert audit["before"] == report["snapshot"] and audit["seals"] == report["seals"]
    assert (
        service.apply(f.job, token=report["token"], actor=actor, reason="Retire this output")
        == result
    )
    with pytest.raises(SourceConflict, match="Another containment"):
        service.apply(
            f.job,
            token=report["token"],
            actor="recovery:" + str(uuid4()),
            reason="Retire this output",
        )


def test_lost_commit_acknowledgement_reads_original_receipt_without_repeat(recovery, monkeypatch):
    service, f, docs = recovery
    report = service.inspect(f.job)
    original = service.dal.settle
    calls = []

    def lost(*args, **kwargs):
        calls.append(kwargs)
        original(*args, **kwargs)
        raise UncertainCommit("Test lost acknowledgement after commit")

    monkeypatch.setattr(service.dal, "settle", lost)
    args = dict(token=report["token"], actor="recovery:" + str(uuid4()), reason="Retire output")
    with pytest.raises(UncertainCommit):
        service.apply(f.job, **args)
    assert service.apply(f.job, **args)["outcome"] == "targets_isolated"
    assert len(calls) == 1 and len(docs) == 1


def test_stale_confirmation_has_no_release_or_private_write(recovery):
    service, f, docs = recovery
    report = service.inspect(f.job)
    f.sql.execute("UPDATE #ExportExecutionStream SET Version=Version+1")
    f.sql.commit()
    with pytest.raises(SourceConflict, match="changed"):
        service.apply(
            f.job, token=report["token"], actor="recovery:" + str(uuid4()), reason="Retire output"
        )
    assert not docs
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 0


@pytest.mark.parametrize(
    "fault",
    [
        "request_target",
        "request_gap",
        "registration",
        "resource_owner",
        "stream_owner",
        "stream_scope",
        "missing_event",
        "foreign_principal",
    ],
)
def test_unsafe_or_incomplete_scope_cannot_be_isolated(recovery, fault):
    service, f, docs = recovery
    mutations = {
        "request_target": "UPDATE #ExportProviderRequest SET TargetID='foreign-file'",
        "request_gap": "UPDATE #ExportProviderRequest SET Sequence=2",
        "registration": "UPDATE #ExportExecutionStream SET RegistrationHash=HASHBYTES('SHA2_256','wrong')",
        "resource_owner": "UPDATE #ExportResource SET OwnerID=NEWID() WHERE ResourceKind='destination'",
        "stream_owner": "UPDATE #ExportExecutionStream SET OwnerID=NEWID()",
        "stream_scope": "UPDATE #ExportExecutionStream SET ScopeJson='{}'",
        "missing_event": "DELETE #ExportProviderRequestEvent WHERE EventSequence=1",
        "foreign_principal": "UPDATE #ExportExecutionSession SET AuthorityPrincipal='foreign'",
    }
    f.sql.execute(mutations[fault])
    with pytest.raises((SourceConflict, KeyError)):
        service.inspect(f.job)
    assert not docs
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainedTarget").fetchval() == 0


@pytest.mark.parametrize(
    "fault", ["target_deleted", "stream_changed", "job_changed", "private_missing"]
)
def test_verification_refuses_missing_or_changed_postconditions(recovery, fault):
    service, f, docs = recovery
    report = service.inspect(f.job)
    service.apply(
        f.job, token=report["token"], actor="recovery:" + str(uuid4()), reason="Retire output"
    )
    if fault == "private_missing":
        docs.clear()
    else:
        f.sql.execute(
            {
                "target_deleted": "DELETE #ExportContainedTarget",
                "stream_changed": "UPDATE #ExportExecutionStream SET Version=Version+1",
                "job_changed": "UPDATE #ExportJob SET Version=Version+1",
            }[fault]
        )
        f.sql.commit()
    with pytest.raises((SourceConflict, KeyError)):
        service.inspect(f.job)


def test_new_owner_after_release_is_preserved_during_lost_reply_verification(recovery):
    service, f, _ = recovery
    report = service.inspect(f.job)
    args = dict(token=report["token"], actor="recovery:" + str(uuid4()), reason="Retire output")
    service.apply(f.job, **args)
    owner = str(uuid4())
    f.sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=?,Fence=99,Version=99 WHERE ResourceKind='account'",
        str(uuid4()),
        owner,
    )
    f.sql.commit()
    assert service.apply(f.job, **args)["outcome"] == "targets_isolated"
    assert (
        str(
            f.sql.execute(
                "SELECT OwnerID FROM #ExportResource WHERE ResourceKind='account'"
            ).fetchval()
        ).lower()
        == owner
    )


@pytest.fixture
def pool_recovery(contained_job):
    f = contained_job
    pool_id, slots = fixture_module.pool_job(f)
    config = registration_fixture()
    config.update(account="test-account", storage_owner="disk")
    pool = config["pools"][0]
    pool.update(
        pool_id=pool_id,
        index_file_id="old-file",
        slot_file_ids=["old-slot-1", "old-slot-2"],
        owner_email="owner@example.test",
    )
    f.sql.execute(
        "UPDATE #SourceOutputPool SET RegistrationJson=?,RegistrationHash=CAST(? AS binary(32))",
        '{"pool":0}',
        digest(dict(pool=0)),
    )
    f.sql.execute(
        "UPDATE #ExportExecutionStream SET RegistrationHash=CAST(? AS binary(32))",
        digest(dict(pool=0)),
    )
    registration = RuntimeRegistration(config)
    docs = {}
    service = ExportTargetContainment(
        dal=ExportTargetContainmentDAL(f.connect),
        discovery=ExportRecoveryDAL(f.connect, registration=registration),
        execution=ExportExecutionDAL(f.connect),
        store=private_store(docs),
        registration=registration,
    )
    return service, f, docs, slots


def test_complete_registered_pool_isolated_and_lost_reply_verified(pool_recovery):
    service, f, docs, slots = pool_recovery
    report = service.inspect(f.job)
    assert report["targets"] == ["old-file", "old-slot-1", "old-slot-2"]
    args = dict(
        token=report["token"], actor="recovery:" + str(uuid4()), reason="Replace all pool files"
    )
    result = service.apply(f.job, **args)
    assert result["outcome"] == "targets_isolated" and result["business_resolved"] is False
    assert service.apply(f.job, **args) == result
    assert len(docs) == 1
    assert [
        tuple(r) for r in f.sql.execute("SELECT * FROM #SourceOutputSlot ORDER BY SlotNo")
    ] == slots


@pytest.mark.parametrize("fault", ["pool_version", "pool_identity", "pool_reason", "slot_history"])
def test_pool_containment_verification_preserves_exact_pool_and_slot_history(pool_recovery, fault):
    service, f, _, _ = pool_recovery
    report = service.inspect(f.job)
    service.apply(
        f.job, token=report["token"], actor="recovery:" + str(uuid4()), reason="Replace pool"
    )
    f.sql.execute(
        {
            "pool_version": "UPDATE #SourceOutputPool SET Version=Version+1",
            "pool_identity": "UPDATE #SourceOutputPool SET IndexFileID='changed-file'",
            "pool_reason": "UPDATE #SourceOutputPool SET BlockedReason='changed reason'",
            "slot_history": "UPDATE #SourceOutputSlot SET Version=Version+1",
        }[fault]
    )
    f.sql.commit()
    with pytest.raises(SourceConflict, match="history"):
        service.inspect(f.job)
