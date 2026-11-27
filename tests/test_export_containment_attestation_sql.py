"""Lost history remains lost; independently sealed current fences permit recovery."""

import os
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from scripts.run_export_authority import AuthorityBroker
from services import export_containment_attestation as attestation
from services.export_evidence_recovery import EvidenceRecoveryAdapter
from services.export_runtime_composition import LocalAuthorityClient
from services.recovery_release_policy import p0a_presentation
from services.recovery_service import RecoveryActor, RecoveryService
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_verification_sql import (
    proposal_service as proposal_service,
    verification as verification,
)
from tests.test_export_target_containment import recovery as recovery
from tests.test_export_target_containment_sql import contained_job as contained_job
from tests.test_guided_recovery import ACTOR, Store

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Local SQL opt-in"
)


def lost_receipt(recovery):
    service, fixture, documents = recovery
    state = service.inspect(fixture.job)
    service.apply(
        fixture.job,
        token=state["token"],
        actor="recovery:" + str(uuid4()),
        reason="Retire uncertain output",
    )
    original = service.dal.snapshot(fixture.job, account="test-account")["receipt"]
    documents.clear()
    return service, fixture, documents, original


def test_new_attestation_verifies_present_fences_without_recreating_original_or_releasing_work(
    recovery,
):
    service, f, docs, original = lost_receipt(recovery)
    snapshot = service.dal.snapshot(f.job, account="test-account")
    proof, token, _ = attestation.inspect(service, snapshot)
    actor = "recovery:" + str(uuid4())
    before = snapshot.copy()
    result = attestation.apply(
        service, snapshot, token=token, actor=actor, reason="Independently check present isolation"
    )
    assert result["outcome"] == "targets_isolated"
    assert result["original_receipt_verified"] is False and result["business_resolved"] is False
    assert proof["provider_success"] is False and proof["child_termination_verified"] is False
    assert service.dal.snapshot(f.job, account="test-account") == before
    assert len(docs) == 1
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainmentAttestation").fetchval() == 1
    assert (
        attestation.apply(
            service,
            snapshot,
            token=token,
            actor=actor,
            reason="Independently check present isolation",
        )
        == result
    )
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainmentAttestation").fetchval() == 1
    # The original remains absent; the new witness is a different identity/hash.
    assert str(UUID(original["ReceiptReference"])) not in docs
    assert service.inspect(f.job)["attestation_id"] == actor.removeprefix("recovery:")


@pytest.mark.parametrize(
    "mutation",
    [
        "DELETE #ExportContainedTarget",
        "UPDATE #ExportContainedStream SET LastSequence=LastSequence+1",
        "UPDATE #ExportJob SET Fence=Fence+1",
        "UPDATE #ExportExecutionStream SET Version=Version+1",
        "UPDATE #ExportExecutionSession SET AuthorityPrincipal='foreign'",
        "UPDATE #ExportResource SET ActiveJobID=(SELECT JobID FROM #ExportJob),OwnerID=NEWID() WHERE ResourceKind='account'",
    ],
)
def test_incomplete_changed_or_reacquired_ownership_is_not_attested(recovery, mutation):
    service, f, docs, _ = lost_receipt(recovery)
    snapshot = service.dal.snapshot(f.job, account="test-account")
    _, token, _ = attestation.inspect(service, snapshot)
    f.sql.execute(mutation)
    f.sql.commit()
    changed = service.dal.snapshot(f.job, account="test-account")
    with pytest.raises(SourceConflict):
        attestation.apply(
            service, changed, token=token, actor="recovery:" + str(uuid4()), reason="Stale review"
        )
    assert not docs
    assert f.sql.execute("SELECT COUNT(*) FROM #ExportContainmentAttestation").fetchval() == 0


def test_lost_attestation_commit_reply_reuses_the_saved_new_identity(recovery, monkeypatch):
    service, f, docs, _ = lost_receipt(recovery)
    snapshot = service.dal.snapshot(f.job, account="test-account")
    _, token, _ = attestation.inspect(service, snapshot)
    original = attestation.ContainmentAttestationDAL.save
    calls = []

    def lost(*args, **kwargs):
        original(*args, **kwargs)
        calls.append(1)
        raise TimeoutError("Lost attestation acknowledgement")

    monkeypatch.setattr(attestation.ContainmentAttestationDAL, "save", lost)
    args = dict(token=token, actor="recovery:" + str(uuid4()), reason="Confirm independent witness")
    with pytest.raises(TimeoutError):
        attestation.apply(service, snapshot, **args)
    assert attestation.apply(service, snapshot, **args)["attestation_id"] == args["actor"][9:]
    assert calls == [1] and len(docs) == 1


@pytest.fixture
def guided(recovery, tmp_path, monkeypatch):
    service, f, _ = recovery
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    service.store = private
    state = service.inspect(f.job)
    service.apply(
        f.job,
        token=state["token"],
        actor="recovery:" + str(uuid4()),
        reason="Retire uncertain output",
    )
    receipt = service.dal.snapshot(f.job, account="test-account")["receipt"]
    reference = str(UUID(receipt["ReceiptReference"]))
    for path in tmp_path.iterdir():
        path.unlink()
    # This fixture contains only one historical containment. The production
    # catalogue union and replacement history have separate SQL contract tests.
    binding = dict(
        reference=reference,
        sha256=receipt["ReceiptHash"],
        kinds=["target isolation", "stream closure"],
    )
    monkeypatch.setattr(
        "services.export_evidence_recovery.EvidenceCatalogDAL",
        lambda *_: SimpleNamespace(get=lambda key: binding),
    )
    authority = SimpleNamespace(
        dal=service.execution, store=private, _lock=RLock(), enrollment_plan=None
    )
    broker = AuthorityBroker(
        authority,
        service.registration,
        boundary=SimpleNamespace(fingerprint="a" * 64, recheck=Mock()),
    )
    broker.replacements = SimpleNamespace(activation_dal=SimpleNamespace(chain=lambda account: []))
    client = LocalAuthorityClient(broker)
    journal = Store()

    def restart():
        return RecoveryService(
            journal,
            {"private_evidence": EvidenceRecoveryAdapter(client)},
            admin_id=1,
            guild_id=2,
            channel_id=3,
            presentation_policy=p0a_presentation,
        )

    guided_service = restart()
    return SimpleNamespace(**locals())


def confirm(r, row, actor=ACTOR):
    return r.guided_service.execute(
        actor,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "attest_containment",
        "Verify present permanent isolation",
    )


@pytest.mark.parametrize("damage", ["hash", "decrypt"])
def test_corrupt_private_receipt_uses_independent_attestation(guided, monkeypatch, damage):
    r = guided
    corrupt = b"damaged encrypted containment"
    path = r.tmp_path / UUID(r.reference).hex
    path.write_bytes(corrupt)
    if damage == "decrypt":
        original = r.private._unprotect

        def decrypt(raw):
            if raw == corrupt:
                raise RuntimeError("Native decryption failed")
            return original(raw)

        monkeypatch.setattr(r.private, "_unprotect", decrypt)
    before = r.service.dal.snapshot(r.f.job, account="test-account")
    row = r.guided_service.review_source(ACTOR, "private_evidence", r.reference)
    assert set(row["evidence"]["actions"]) == {"attest_containment"}
    result = confirm(r, row)
    assert result["State"] == "resolved"
    assert result["evidence"]["original_receipt_verified"] is False
    assert r.service.inspect(r.f.job)["business_resolved"] is False
    assert r.service.dal.snapshot(r.f.job, account="test-account") == before
    assert path.read_bytes() == corrupt


def test_guided_current_isolation_requires_admin_and_survives_lost_reply_restart(
    guided, monkeypatch
):
    r = guided
    row = r.guided_service.review_source(ACTOR, "private_evidence", r.reference)
    assert set(row["evidence"]["actions"]) == {"attest_containment"}
    assert "required_evidence" not in row["evidence"]
    with pytest.raises(SourceConflict, match="configured admin"):
        confirm(r, row, RecoveryActor(9, 2, 3))
    assert not r.journal.actions
    dispatch = r.client.evidence_recovery
    calls = []

    def lost(operation, **values):
        result = dispatch(operation, **values)
        if operation == "attest":
            calls.append(operation)
            raise TimeoutError("Lost reply after SQL attestation commit")
        return result

    monkeypatch.setattr(r.client, "evidence_recovery", lost)
    result = confirm(r, row)
    assert result["State"] == "resolved"
    r.guided_service = r.restart()
    assert confirm(r, row)["State"] == "resolved"
    assert calls == ["attest"] and len(r.journal.actions) == 1
    assert r.journal.actions[0]["State"] == "verified"
    assert result["evidence"]["original_receipt_verified"] is False
    assert result["evidence"]["recovery_links"][0]["source_id"].lower() == r.f.job.lower()
    assert r.f.sql.execute("SELECT State FROM #ExportJob").fetchval() == "uncertain"
    assert not (r.tmp_path / UUID(r.reference).hex).exists()


def test_guided_stale_review_refuses_changed_owner_without_attesting(guided):
    r = guided
    row = r.guided_service.review_source(ACTOR, "private_evidence", r.reference)
    r.f.sql.execute("UPDATE #ExportJob SET Fence=Fence+1")
    with pytest.raises(SourceConflict, match="changed"):
        confirm(r, row)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportContainmentAttestation").fetchval() == 0


@pytest.mark.asyncio
async def test_containment_attestation_real_admin_confirmation(guided, monkeypatch):
    from tests.p0_attestation_ui_harness import confirm_through_view
    from ui.views.recovery_view import RecoveryIncidentView

    row = guided.guided_service.review_source(ACTOR, "private_evidence", guided.reference)
    current = await confirm_through_view(
        monkeypatch, guided.guided_service, row, "attest_containment"
    )
    assert current["evidence"]["original_receipt_verified"] is False
    assert any(
        b.label == "Continue original recovery" for b in RecoveryIncidentView(current).children
    )


def test_new_foreign_reservation_is_preserved_by_the_guided_attestation(guided):
    r = guided
    foreign = str(uuid4())
    r.f.sql.execute(
        "UPDATE #ExportResource SET ActiveJobID=?,OwnerID=NEWID() WHERE ResourceKind='account'",
        foreign,
    )
    before = r.f.sql.execute("SELECT * FROM #ExportResource ORDER BY ResourceKey").fetchall()
    row = r.guided_service.review_source(ACTOR, "private_evidence", r.reference)
    assert confirm(r, row)["State"] == "resolved"
    assert (
        r.f.sql.execute("SELECT * FROM #ExportResource ORDER BY ResourceKey").fetchall() == before
    )


@pytest.mark.parametrize("already_activated", [False, True])
def test_replacement_verifies_from_new_isolation_attestation_without_replaying_reads(
    activation, already_activated
):
    r = activation
    if already_activated:
        r.apply()
    containment = r.service.proposals.containment
    before = containment.dal.snapshot(r.f.job, account="test-account")
    reference = str(UUID(before["receipt"]["ReceiptReference"]))
    del r.docs[reference]
    _, token, _ = attestation.inspect(containment, before)
    attestation.apply(
        containment,
        before,
        token=token,
        actor="recovery:" + str(uuid4()),
        reason="Independently verify current isolation",
    )
    request_count = len(r.runtime.sent)
    result = r.apply()
    assert result["registration"]["legacy_configuration"]["scan_data"]["destinations"] == [
        "fresh-file"
    ]
    assert result["business_resolved"] is False
    assert len(r.runtime.sent) == request_count
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 1
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
