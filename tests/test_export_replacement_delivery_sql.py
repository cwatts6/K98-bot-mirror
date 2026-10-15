from copy import deepcopy
import hashlib
import os
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, digest
from services.export_coordination_dal import ExportCoordinationDAL
from services.export_replacement_delivery import ReplacementDelivery
from services.export_replacement_delivery_dal import ReplacementDeliveryDAL
from services.export_snapshot_store import SnapshotReceipt
from tests import (
    test_export_target_containment as authority_fixture,
    test_export_target_containment_sql as fixture_module,
)
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_snapshot import fixture
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    verification as verification,
)

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


@pytest.fixture
def recovery(contained_job, request):
    service, f, docs = authority_fixture.recovery.__wrapped__(contained_job)
    if getattr(request, "param", None) == "mixed":
        from services.export_recovery_dal import ExportRecoveryDAL
        from services.export_runtime_composition import RuntimeRegistration
        from services.legacy_export_snapshot_service import configuration_digest

        config = service.registration.value()
        config["legacy_configuration"]["scan_data"]["destinations"].append("unchanged-file")
        config["legacy_configuration"]["scan_data"]["grid_ids"] = {"unchanged-file": {"Report": 17}}
        config["protected_file_ids"] = sorted([*config["protected_file_ids"], "unchanged-file"])
        service.registration = RuntimeRegistration(config)
        service.discovery = ExportRecoveryDAL(f.connect, registration=service.registration)
        f.sql.execute(
            "UPDATE #ExportExecutionStream SET RegistrationHash=CAST(? AS binary(32))",
            bytes.fromhex(configuration_digest(config["legacy_configuration"]["scan_data"])),
        )
    original, _, _ = fixture()
    f.sql.execute(
        "UPDATE #ExportJob SET InputHash=CAST(? AS binary(32)),SpoolBytes=?",
        hashlib.sha256(original.payload).digest(),
        len(original.payload),
    )
    f.original_payload = original.payload
    return service, f, docs


@pytest.fixture
def delivery(monkeypatch, request):
    rewrite = fixture_module.local_sql
    monkeypatch.setattr(
        fixture_module,
        "local_sql",
        lambda text: rewrite(text).replace("=ExportJob.", "=#ExportJob."),
    )
    monkeypatch.setattr(
        fixture_module, "TABLES", (*fixture_module.TABLES, "dbo.ExportReplacementDelivery")
    )
    r = request.getfixturevalue("activation")
    r.activated = r.apply()
    spools = {"retained-input": r.f.original_payload}

    def put(raw):
        key = uuid4().hex
        spools[key] = raw
        return SnapshotReceipt(key, len(raw), hashlib.sha256(raw).hexdigest(), "disk")

    def read(receipt):
        raw = spools[receipt.key]
        assert receipt.sha256 == hashlib.sha256(raw).hexdigest() and receipt.byte_count == len(raw)
        return raw

    coordinator = ExportCoordinationDAL(
        r.f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    r.delivery = ReplacementDelivery(
        dal=ReplacementDeliveryDAL(r.f.connect, coordinator),
        discovery=r.service.proposals.containment.discovery,
        verify_delivery=Mock(),
        store=SimpleNamespace(read=read, put=put),
    )
    r.queue_args = dict(actor="recovery:" + str(uuid4()), reason="Publish the retained original")
    r.spools = spools
    return r


def test_queue_one_replacement_preserves_original_and_never_claims_delivery(delivery):
    r = delivery
    before = r.delivery.inspect(r.f.job, r.activated)
    assert before["stage"] == "publication_required" and not before["resolved"]
    r.delivery.execute(r.f.job, r.activated, "publish_replacement", **r.queue_args)
    after = r.delivery.inspect(r.f.job, r.activated)
    assert after["stage"] == "replacement_queued" and not after["resolved"]
    assert after["job_id"] != r.f.job
    r.delivery.execute(r.f.job, r.activated, "publish_replacement", **r.queue_args)
    assert len(r.spools) == 2
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportJob").fetchval() == 2
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    r.delivery.verify_delivery.assert_not_called()


def test_queue_commit_reply_loss_reconciles_original_decision(delivery, monkeypatch):
    r = delivery
    original = r.delivery.dal.enqueue

    def lose(**kwargs):
        original(**kwargs)
        raise UncertainCommit("Injected reply loss")

    monkeypatch.setattr(r.delivery.dal, "enqueue", lose)
    with pytest.raises(UncertainCommit):
        r.delivery.execute(r.f.job, r.activated, "publish_replacement", **r.queue_args)
    action = dict(
        ActionKind="publish_replacement",
        ActionID=r.queue_args["actor"].removeprefix("recovery:"),
        Reason=r.queue_args["reason"],
    )
    assert r.delivery.reconcile(r.f.job, r.activated, action) == "verified"
    r.delivery.execute(r.f.job, r.activated, "publish_replacement", **r.queue_args)
    assert len(r.spools) == 2
    assert not r.delivery.inspect(r.f.job, r.activated)["resolved"]


def test_changed_input_cannot_publish_from_original_receipt(delivery):
    r = delivery
    r.f.sql.execute(
        "UPDATE #ExportJob SET InputHash=CAST(? AS binary(32)) WHERE JobID=?", b"x" * 32, r.f.job
    )
    with pytest.raises((SourceConflict, AssertionError)):
        r.delivery.execute(r.f.job, r.activated, "publish_replacement", **r.queue_args)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 0


def waiting_job(r, *, mixed=False):
    retained, _, _ = fixture()
    if mixed:
        from services.legacy_export_snapshot_service import LegacySnapshot, configuration_digest

        meta = retained.metadata()
        config = deepcopy(meta["config"])
        extra = deepcopy(config["outputs"][0])
        extra.update(file_id="unchanged-file", grid_id=17, format_requests=[])
        config["outputs"].append(extra)
        config["destinations"].append("unchanged-file")
        retained = LegacySnapshot.capture(
            consumer=meta["consumer"],
            preparation_id=meta["preparation_id"],
            config=config,
            generation=meta["generation"] | dict(config_sha256=configuration_digest(config)),
            provenance=meta["provenance"],
            sections=retained.sections(),
        )
    follower_id = str(uuid4())
    cursor = r.f.sql.execute("SELECT * FROM #ExportJob WHERE JobID=?", r.f.job)
    job = dict(zip((c[0] for c in cursor.description), cursor.fetchone(), strict=True))
    job.update(
        JobID=follower_id,
        State="ready",
        OwnerID=None,
        Fence=0,
        Version=1,
        EnqueueSequence=99,
        InputHash=hashlib.sha256(retained.payload).digest(),
        SpoolKey="waiting-input",
        SpoolBytes=len(retained.payload),
        ProvenanceJson="{}",
        DestinationSetHash=digest(sorted(retained.metadata()["config"]["destinations"])),
    )
    r.f.insert("ExportJob", job)
    r.f.sql.execute(
        "INSERT #ExportJobResource SELECT ?,ResourceKey FROM #ExportJobResource WHERE JobID=?",
        follower_id,
        r.f.job,
    )
    r.spools["waiting-input"] = retained.payload
    if mixed:
        cursor = r.f.sql.execute(
            "SELECT * FROM #ExportResource WHERE ResourceKey='destination:old-file'"
        )
        resource = dict(zip((c[0] for c in cursor.description), cursor.fetchone(), strict=True))
        resource["ResourceKey"] = "destination:unchanged-file"
        r.f.insert("ExportResource", resource)
        r.f.sql.execute(
            "INSERT #ExportJobResource VALUES(?,'destination:unchanged-file')", follower_id
        )
    return follower_id


def test_waiting_export_links_blocker_then_queues_its_own_retained_input(delivery):
    from services.export_replacement_waiting import WaitingReplacementWorkflow

    r = delivery
    follower_id = waiting_job(r)
    blocker = dict(activation=r.activated, delivery=dict(resolved=False))
    workflow = WaitingReplacementWorkflow(
        discovery=r.delivery.discovery,
        continuation=r.delivery,
        blocking_jobs=r.delivery.dal.blocking_jobs,
        original_workflow=lambda key: SimpleNamespace(_state=lambda _: blocker),
    )

    evidence, _, resolved = workflow.inspect(follower_id)
    assert not resolved and evidence["blocking_job_ids"] == [r.f.job]
    assert evidence["outcome"] == "waiting_for_output_replacement" and not evidence["actions"]
    blocker["delivery"]["resolved"] = True
    evidence, token, resolved = workflow.inspect(follower_id)
    assert not resolved and "publish_replacement" in evidence["actions"]
    workflow.execute(follower_id, "publish_replacement", token, **r.queue_args)
    evidence, _, resolved = workflow.inspect(follower_id)
    assert not resolved and evidence["outcome"] == "replacement_queued"
    queued = r.delivery.discovery.job(evidence["delivery"]["job_id"])["job"]
    assert queued["JobID"] not in {r.f.job, follower_id}
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportExecutionStream WHERE JobID=?", follower_id
        ).fetchval()
        == 0
    )


@pytest.mark.parametrize("recovery", ["mixed"], indirect=True)
def test_waiting_export_keeps_unaffected_output_and_rechecks_projection(delivery, recovery):
    from services.export_replacement_projection import continuation_activation
    from services.export_replacement_waiting import WaitingReplacementWorkflow
    from services.legacy_export_snapshot_service import LegacySnapshot

    r = delivery
    follower_id = waiting_job(r, mixed=True)
    projection = continuation_activation(
        [r.activated], targets=["old-file", "unchanged-file"], consumer="scan_data"
    )
    workflow = WaitingReplacementWorkflow(
        discovery=r.delivery.discovery,
        continuation=r.delivery,
        blocking_jobs=r.delivery.dal.blocking_jobs,
        original_workflow=lambda _: SimpleNamespace(
            _state=lambda _: dict(activation=r.activated, delivery=dict(resolved=True))
        ),
        project_activation=lambda _: projection,
    )
    evidence, token, resolved = workflow.inspect(follower_id)
    assert not resolved and "publish_replacement" in evidence["actions"]
    workflow.execute(follower_id, "publish_replacement", token, **r.queue_args)
    receipt = r.delivery.dal.read(follower_id, projection["activation_id"], "test-account")
    queued = r.delivery.discovery.job(receipt["ReplacementJobID"])["job"]
    rebound = LegacySnapshot.load(r.spools[queued["SpoolKey"]])
    assert rebound.metadata()["config"]["destinations"] == ["fresh-file", "unchanged-file"]
    extra = next(
        o for o in rebound.metadata()["config"]["outputs"] if o["file_id"] == "unchanged-file"
    )
    assert extra["grid_id"] == 17
    assert (
        r.delivery.dal.continuation_anchor(follower_id, "test-account")
        == projection["activation_id"]
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
