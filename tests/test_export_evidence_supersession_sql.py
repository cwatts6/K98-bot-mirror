"""Lost private read evidence -> guided fresh check -> verified publication.

SQL uses temporary objects; provider children and DPAPI encoding are simulated.
"""

import hashlib
from uuid import UUID

import pytest

from core.export_execution_host import PrivateEvidenceStore
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_evidence_catalog_dal import EvidenceCatalogDAL
from services.export_evidence_recovery import EvidenceRecoveryAdapter
from services.export_evidence_storage import EvidenceCopies
from services.export_execution_authority import ExecutionUncertain
from services.recovery_service import RecoveryService
from tests.test_export_evidence_recovery_sql import (
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


def lose_check(r, tmp_path, damage="missing", *, part="receipt", discarded=False, activated=False):
    if discarded:
        r.runtime.failure = "drive.files.get"
    row = apply(r, "verify_replacements")
    if discarded:
        assert row["evidence"]["outcome"] == "checking_replacements"
        apply(r, "discard_replacement_check")
        r.runtime.failure = None
    else:
        assert row["evidence"]["outcome"] == "activation_required"
    if activated:
        assert apply(r, "activate_replacements")["evidence"]["outcome"] == "publication_required"
    private = PrivateEvidenceStore(
        tmp_path, "disk", protect=lambda b: b[::-1], unprotect=lambda b: b[::-1]
    )
    for reference, raw in r.docs.items():
        (tmp_path / UUID(str(reference)).hex).write_bytes(raw[::-1])
        EvidenceCopies(private).repair(reference, hashlib.sha256(raw).digest())
    r.broker.authority.store = private
    r.service.proposals.store = private
    saved = r.f.sql.execute(
        "SELECT VerificationID,ReceiptReference FROM #ExportReplacementVerification"
    ).fetchone()
    check_id, reference = (str(value).lower() for value in saved)
    selectors = {
        "closure": "SELECT ClosureReference FROM #ExportExecutionStream WHERE PreparationID=?",
        "payload": "SELECT TOP (1) r.PayloadReference FROM #ExportProviderRequest r JOIN #ExportExecutionStream s ON s.StreamID=r.StreamID WHERE s.PreparationID=? ORDER BY r.Sequence",
        "event": "SELECT TOP (1) e.EvidenceReference FROM #ExportProviderRequestEvent e JOIN #ExportProviderRequest r ON r.RequestID=e.RequestID JOIN #ExportExecutionStream s ON s.StreamID=r.StreamID WHERE s.PreparationID=? AND e.EvidenceReference IS NOT NULL ORDER BY r.Sequence,e.EventSequence",
    }
    if part != "receipt":
        reference = str(r.f.sql.execute(selectors[part], check_id).fetchval()).lower()
    key = UUID(reference).hex
    for name in (key, "replica_" + key):
        if damage == "missing":
            (tmp_path / name).unlink()
        else:
            (tmp_path / name).write_bytes(b"wrong evidence")
    adapter = EvidenceRecoveryAdapter(r.rpc_runtime.client)
    r.recovery = RecoveryService(
        r.recovery.store,
        dict(r.recovery.adapters, private_evidence=adapter),
        admin_id=1,
        guild_id=2,
        channel_id=3,
    )
    r.private, r.lost_check_id, r.lost_reference = private, check_id, reference
    return r.recovery.review_source(ACTOR, adapter.kind, reference)


@pytest.mark.parametrize("part", ["closure", "payload", "event"])
def test_lost_private_journal_member_links_to_fresh_read(rpc, tmp_path, part):
    r = rpc
    alert = lose_check(r, tmp_path, part=part)
    assert alert["evidence"]["outcome"] == "fresh_read_required"
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert r.recovery.review(ACTOR, alert["IncidentID"])["evidence"]["outcome"] == "superseded_read"


def test_lost_discard_receipt_offers_fresh_verification_without_releasing_again(rpc, tmp_path):
    r = rpc
    alert = lose_check(r, tmp_path, discarded=True)
    assert alert["evidence"]["outcome"] == "fresh_read_required"
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert r.recovery.review(ACTOR, alert["IncidentID"])["State"] == "resolved"
    assert (
        r.f.sql.execute(
            "SELECT State FROM #ExportReplacementVerification WHERE VerificationID=?",
            r.lost_check_id,
        ).fetchval()
        == "discarded"
    )


@pytest.mark.parametrize("defect", ["mutation", "ownership", "membership", "resource_membership"])
def test_lost_receipt_does_not_hide_invalid_or_owned_read_history(rpc, tmp_path, defect):
    from services.export_replacement_check_recovery import inspect_read_check

    r = rpc
    lose_check(r, tmp_path)
    if defect == "mutation":
        r.f.sql.execute(
            "UPDATE r SET RequestKind='mutation',Operation='sheets.values.update' "
            "FROM #ExportProviderRequest r JOIN #ExportExecutionStream s ON s.StreamID=r.StreamID "
            "WHERE s.PreparationID=? AND r.Sequence=1",
            r.lost_check_id,
        )
    elif defect == "ownership":
        r.f.sql.execute(
            "UPDATE #ExportResource SET ActivePreparationID=?,OwnerID=? WHERE ResourceKey='account:test-account'",
            r.lost_check_id,
            r.lost_check_id,
        )
    elif defect == "membership":
        r.f.sql.execute(
            "DELETE r FROM #ExportProviderRequest r JOIN #ExportExecutionStream s ON s.StreamID=r.StreamID "
            "WHERE s.PreparationID=? AND r.Sequence=1",
            r.lost_check_id,
        )
    else:
        r.f.sql.execute(
            "DELETE FROM #ExportPreparationResource WHERE PreparationID=? AND ResourceKey LIKE 'destination:%'",
            r.lost_check_id,
        )
    r.f.sql.commit()
    workflow = r.broker.replacements.workflow(r.f.job)
    with pytest.raises(SourceConflict):
        inspect_read_check(workflow.verification, r.lost_check_id)
    assert len(r.runtime.sent) == 5


def test_evidence_already_used_for_activation_cannot_be_superseded_by_a_read_shortcut(
    rpc, tmp_path
):
    r = rpc
    row = lose_check(r, tmp_path, activated=True)
    assert row["evidence"]["outcome"] == "backup_required" and row["State"] == "open"
    assert not row["evidence"]["actions"] and "evidence_recovery_job_id" not in row["evidence"]
    with pytest.raises(SourceConflict):
        r.broker.replacements.current()


def test_stale_confirmation_and_wrong_admin_never_duplicate_the_fresh_read(rpc, tmp_path):
    r = rpc
    lose_check(r, tmp_path)
    row = r.recovery.review(ACTOR, r.row["IncidentID"])
    args = (
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "verify_replacements",
        "Fresh check",
    )
    with pytest.raises(SourceConflict, match="configured admin"):
        r.recovery.execute(type(ACTOR)(999, 2, 3), *args)
    assert len(r.runtime.sent) == 5
    assert r.recovery.execute(ACTOR, *args)["evidence"]["outcome"] == "activation_required"
    with pytest.raises(SourceConflict, match="evidence changed"):
        r.recovery.execute(ACTOR, *args)
    assert len(r.runtime.sent) == 10
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 2


def test_replacement_read_failure_after_evidence_loss_still_has_guided_discard_and_retry(
    rpc, tmp_path
):
    r = rpc
    lose_check(r, tmp_path)
    r.runtime.failure = "drive.files.get"
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "checking_replacements"
    assert "discard_replacement_check" in row["evidence"]["actions"]
    assert apply(r, "discard_replacement_check")["evidence"]["outcome"] == "verification_required"
    r.runtime.failure = None
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 3


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_lost_check_alert_guides_fresh_verification_and_complete_publication(rpc, tmp_path, damage):
    r = rpc
    alert = lose_check(r, tmp_path, damage)
    assert alert["State"] == "open" and alert["evidence"]["outcome"] == "fresh_read_required"
    assert alert["evidence"]["evidence_recovery_job_id"] == r.f.job
    assert not alert["evidence"]["actions"]  # Never offer fabricated byte restoration.
    with pytest.raises(SourceConflict):
        r.broker.replacements.workflow(r.f.job).verification.inspect(r.lost_check_id)
    with pytest.raises(SourceConflict):
        r.broker.replacements.workflow(r.f.job).activation.apply(
            r.plan.value()["replacement_id"],
            r.lost_check_id,
            token="0" * 64,
            actor="recovery:" + r.lost_check_id,
            reason="Cannot use lost result",
        )
    row = r.recovery.review_source(
        ACTOR, "export_job", alert["evidence"]["evidence_recovery_job_id"]
    )
    assert row["evidence"]["actions"]["verify_replacements"]["label"] == "Run fresh read check"
    assert "activate_replacements" not in row["evidence"]["actions"]
    r.recovery = RecoveryService(
        r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
    )
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert len(r.runtime.sent) == 10 and all(
        q.operation
        in {"drive.files.get", "drive.permissions.list", "sheets.get", "sheets.values.batchGet"}
        for q in r.runtime.sent
    )
    fixed = r.recovery.review(ACTOR, alert["IncidentID"])
    assert fixed["State"] == "resolved" and fixed["evidence"]["outcome"] == "superseded_read"
    assert fixed["evidence"]["successor_check_id"] != r.lost_check_id
    assert not (tmp_path / UUID(r.lost_reference).hex).exists() or damage == "corrupt"
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


def test_lost_fresh_check_acknowledgement_reconciles_without_duplicate_read(
    rpc, tmp_path, monkeypatch
):
    r = rpc
    lose_check(r, tmp_path)
    original = r.broker.dispatch
    lost = []

    def dispatch(message):
        result = original(message)
        if (
            message.get("operation") == "execute"
            and message.get("step") == "verify_replacements"
            and not lost
        ):
            lost.append(True)
            raise ExecutionUncertain("Injected lost fresh-check acknowledgement")
        return result

    monkeypatch.setattr(r.broker, "dispatch", dispatch)
    row = apply(r, "verify_replacements")
    assert not row["pending_action"] and row["evidence"]["outcome"] == "activation_required"
    assert len(r.runtime.sent) == 10
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementVerification").fetchval() == 2


@pytest.mark.asyncio
async def test_evidence_alert_button_opens_correct_guided_check(rpc, tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from ui.views import recovery_view

    r = rpc
    row = lose_check(r, tmp_path)
    view = recovery_view.RecoveryIncidentView(row)
    button = next(b for b in view.children if b.label == "Recover replacement check")
    monkeypatch.setattr(recovery_view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(recovery_view, "safe_defer", AsyncMock(return_value=True))

    async def call(method, *args):
        return getattr(r.recovery, method)(*args)

    monkeypatch.setattr(recovery_view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    await button.callback(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"]
    assert "Run fresh read check" in [b.label for b in sent["view"].children]
    with pytest.raises(SourceConflict, match="exact"):
        EvidenceCatalogDAL(r.f.connect, "another-account").replacement_check(r.lost_reference)
