"""Lost approval -> guided read discard/new proposal -> verified delivery."""

import hashlib
from uuid import UUID

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_evidence_recovery import EvidenceRecoveryAdapter
from services.export_evidence_storage import EvidenceCopies
from services.recovery_service import RecoveryService
from tests.test_export_evidence_supersession_sql import (
    contained_job as contained_job,
    guided as guided,
    proof_catalogue as proof_catalogue,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    rpc as rpc,
    store as store,
    verification as verification,
)
from tests.test_export_replacement_guided_sql import apply
from tests.test_guided_recovery import ACTOR


def lose_proposal(r, tmp_path, stage="none", damage="missing"):
    if stage != "none":
        if stage == "checking":
            r.runtime.failure = "drive.files.get"
        apply(r, "verify_replacements")
        if stage == "activated":
            apply(r, "activate_replacements")
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    for reference, raw in r.docs.items():
        (tmp_path / UUID(str(reference)).hex).write_bytes(raw[::-1])
        EvidenceCopies(private).repair(reference, hashlib.sha256(raw).digest())
    r.broker.authority.store = private
    r.service.proposals.store = private
    key, reference = r.f.sql.execute(
        "SELECT ReplacementID,ReceiptReference FROM #ExportReplacementPlan"
    ).fetchone()
    r.lost_proposal = str(key).lower()
    r.lost_reference = str(reference).lower()
    for name in (UUID(str(reference)).hex, "replica_" + UUID(str(reference)).hex):
        if damage == "missing":
            (tmp_path / name).unlink()
        else:
            (tmp_path / name).write_bytes(b"corrupt receipt")
    adapter = EvidenceRecoveryAdapter(r.rpc_runtime.client)
    r.recovery = RecoveryService(
        r.recovery.store,
        dict(r.recovery.adapters, private_evidence=adapter),
        admin_id=1,
        guild_id=2,
        channel_id=3,
    )
    return r.recovery.review_source(ACTOR, "private_evidence", r.lost_reference)


def new_proposal(r):
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    r.recovery.save_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        0,
        0,
        {"owner_email": "owner@example.com", "old-file": "fresh-file"},
    )
    preview = r.recovery.input_confirmation(ACTOR, row["IncidentID"], "choose_replacements")
    return r.recovery.execute_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        preview["draft_version"],
    )


@pytest.mark.parametrize("stage", ["none", "verified", "checking"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_lost_proposal_guides_new_approval_check_activation_and_publication(
    rpc, tmp_path, stage, damage
):
    r = rpc
    alert = lose_proposal(r, tmp_path, stage, damage)
    assert alert["evidence"]["outcome"] == "fresh_proposal_required"
    assert alert["evidence"]["evidence_recovery_job_id"] == r.f.job
    with pytest.raises(SourceConflict):
        r.service.proposals.inspect(r.lost_proposal)
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    if stage == "checking":
        assert row["evidence"]["outcome"] == "proposal_read_discard_required"
        assert set(row["evidence"]["actions"]) == {"discard_replacement_check"}
        row = apply(r, "discard_replacement_check")
        r.runtime.failure = None
    assert row["evidence"]["outcome"] == "replacement_proposal_required"
    assert set(row["evidence"]["actions"]) == {"choose_replacements"}
    # Reopening uses persisted SQL/evidence; no view-local approval survives.
    r.recovery = RecoveryService(
        r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
    )
    assert new_proposal(r)["evidence"]["outcome"] == "verification_required"
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert (
        r.recovery.review(ACTOR, alert["IncidentID"])["evidence"]["outcome"]
        == "superseded_proposal"
    )
    assert apply(r, "activate_replacements")["evidence"]["outcome"] == "publication_required"
    assert apply(r, "publish_replacement")["evidence"]["outcome"] == "replacement_queued"
    from tests.test_export_replacement_end_to_end import prepare_publication

    r.activated = r.broker.replacements.workflow(r.f.job)._state(r.f.job)["activation"]
    r.delivery = r.workflow.continuation
    prepare_publication(r)
    r.publish()
    assert r.recovery.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )


def test_activated_proposal_cannot_use_new_approval_shortcut(rpc, tmp_path):
    alert = lose_proposal(rpc, tmp_path, "activated")
    assert alert["evidence"]["outcome"] == "backup_required"
    assert "evidence_recovery_job_id" not in alert["evidence"]
    with pytest.raises(SourceConflict):
        rpc.broker.replacements.current()


def test_lost_proposal_and_read_receipt_both_resolve_through_new_verification(rpc, tmp_path):
    r = rpc
    alert = lose_proposal(r, tmp_path, "verified")
    reference = str(
        r.f.sql.execute("SELECT ReceiptReference FROM #ExportReplacementVerification").fetchval()
    ).lower()
    for name in (UUID(reference).hex, "replica_" + UUID(reference).hex):
        (tmp_path / name).unlink()
    read_alert = r.recovery.review_source(ACTOR, "private_evidence", reference)
    assert read_alert["evidence"]["outcome"] == "fresh_read_required"
    assert new_proposal(r)["evidence"]["outcome"] == "verification_required"
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert r.recovery.review(ACTOR, alert["IncidentID"])["State"] == "resolved"
    assert r.recovery.review(ACTOR, read_alert["IncidentID"])["State"] == "resolved"


@pytest.mark.parametrize("defect", ["mutation", "ownership", "mapping"])
def test_invalid_original_scope_cannot_release_or_replace(rpc, tmp_path, defect):
    r = rpc
    lose_proposal(r, tmp_path, "checking")
    if defect == "mutation":
        r.f.sql.execute(
            "UPDATE #ExportProviderRequest SET RequestKind='mutation',Operation='sheets.values.update'"
        )
    elif defect == "ownership":
        r.f.sql.execute(
            "UPDATE #ExportResource SET OwnerID=NEWID() WHERE ResourceKey='account:test-account'"
        )
    else:
        r.f.sql.execute("UPDATE #ExportReplacementPlan SET MappingJson='[]'")
    r.f.sql.commit()
    if defect == "mapping":
        with pytest.raises(SourceConflict):
            r.recovery.review(ACTOR, r.row["IncidentID"])
    else:
        apply(r, "discard_replacement_check")
    assert (
        r.f.sql.execute("SELECT State FROM #ExportReplacementVerification").fetchval() == "checking"
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementPlan").fetchval() == 1


def test_lost_discard_reply_and_stale_or_foreign_confirmation(rpc, tmp_path, monkeypatch):
    from services.export_execution_authority import ExecutionUncertain

    r = rpc
    lose_proposal(r, tmp_path, "checking")
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    args = (
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "discard_replacement_check",
        "Abandon read",
    )
    with pytest.raises(SourceConflict, match="configured admin"):
        r.recovery.execute(type(ACTOR)(999, 2, 3), *args)
    original, lost = r.broker.dispatch, []

    def dispatch(message):
        result = original(message)
        if (
            message.get("operation") == "execute"
            and message.get("step") == "discard_replacement_check"
            and not lost
        ):
            lost.append(True)
            raise ExecutionUncertain("Injected lost discard reply")
        return result

    monkeypatch.setattr(r.broker, "dispatch", dispatch)
    fixed = r.recovery.execute(ACTOR, *args)
    assert not fixed["pending_action"]
    assert fixed["evidence"]["outcome"] == "replacement_proposal_required"
    with pytest.raises(SourceConflict, match="evidence changed"):
        r.recovery.execute(ACTOR, *args)
    assert r.f.sql.execute("SELECT Version FROM #ExportReplacementVerification").fetchval() == 2


@pytest.mark.asyncio
async def test_proposal_alert_button_opens_the_guided_form(rpc, tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from ui.views import recovery_view

    r = rpc
    alert = lose_proposal(r, tmp_path)
    view = recovery_view.RecoveryIncidentView(alert)
    button = next(b for b in view.children if b.label == "Recover replacement")
    monkeypatch.setattr(recovery_view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(recovery_view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(r.recovery, method)(*args)

    monkeypatch.setattr(recovery_view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await button.callback(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"]
    assert "Re-enter replacement links" in [b.label for b in sent["view"].children]
