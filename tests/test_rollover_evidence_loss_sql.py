"""Lost rollover evidence routes through guided fresh checks, never job recovery."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_evidence_catalog_dal import EvidenceCatalogDAL
from services.recovery_service import RecoveryService
from tests.test_export_evidence_recovery_sql import proof_catalogue as proof_catalogue
from tests.test_export_evidence_supersession_sql import lose_check
from tests.test_export_proposal_loss_sql import lose_proposal
from tests.test_export_replacement_guided_sql import apply
from tests.test_guided_recovery import ACTOR
from tests.test_rollover_replacement_guided_sql import (
    contained_job as contained_job,
    guided as guided,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    seed_choices,
    store as store,
    verification as verification,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("part", ["receipt", "closure", "payload", "event"])
async def test_lost_rollover_read_button_runs_fresh_check_then_activation_and_queue(
    guided, tmp_path, monkeypatch, part
):
    from ui.views import recovery_view

    r = guided
    r.rpc_runtime = r.rpc
    alert = lose_check(r, tmp_path, part=part)
    assert alert["evidence"]["outcome"] == "fresh_read_required"
    assert "evidence_recovery_job_id" not in alert["evidence"]
    assert alert["evidence"]["recovery_links"] == [
        dict(label="Recover replacement check", kind="export_rollover", source_id=r.f.operation)
    ]
    with pytest.raises(SourceConflict):
        EvidenceCatalogDAL(r.f.connect, "other-account").replacement_check(r.lost_reference)
    r.recovery = RecoveryService(
        r.recovery.store, r.recovery.adapters, admin_id=1, guild_id=2, channel_id=3
    )

    async def call(method, *args):
        return getattr(r.recovery, method)(*args)

    monkeypatch.setattr(recovery_view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(recovery_view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(recovery_view, "call", call)
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b
        for b in recovery_view.RecoveryIncidentView(alert).children
        if b.label == "Recover replacement check"
    )
    await button.callback(interaction)
    opened = interaction.followup.send.call_args.kwargs
    assert opened["ephemeral"]
    button = next(b for b in opened["view"].children if b.label == "Run fresh read check")
    await button.callback(interaction)
    confirm = interaction.followup.send.call_args.kwargs["view"]
    assert isinstance(confirm, recovery_view.RecoveryConfirmView)
    await confirm.confirm.callback(interaction)
    assert (
        interaction.followup.send.call_args.kwargs["view"].row["evidence"]["outcome"]
        == "activation_required"
    )
    assert r.recovery.review(ACTOR, alert["IncidentID"])["State"] == "resolved"
    row = apply(r, "activate_replacements")
    assert row["State"] == "open" and row["evidence"]["outcome"] == "rollover_continuation_required"
    activation = r.rpc.client.replacement_recovery(
        r.f.operation, "context", owner_kind="rollover", token=row["EvidenceHash"]
    )
    dal = seed_choices(r, activation)
    row = apply(r, "start_replacement_rollover")
    assert row["State"] == "open" and dal.read(r.f.operation, activation)["State"] == "closing"
    assert (
        r.f.sql.execute(
            "SELECT State FROM #SourceOutputOperation WHERE OperationID=?", r.f.operation
        ).fetchval()
        == "uncertain"
    )


@pytest.mark.parametrize("stage", ["none", "checking", "verified"])
def test_lost_rollover_proposal_has_guided_reentry_discard_and_new_verification(
    guided, tmp_path, stage
):
    r = guided
    r.rpc_runtime = r.rpc
    alert = lose_proposal(r, tmp_path, stage)
    assert alert["evidence"]["outcome"] == "fresh_proposal_required"
    assert alert["evidence"]["recovery_links"][0]["kind"] == "export_rollover"
    if stage == "checking":
        apply(r, "discard_replacement_check")
        r.runtime.failure = None
    incident = r.row["IncidentID"]
    first = r.recovery.input_page(ACTOR, incident, "choose_replacements")
    for number in range(first["pages"]):
        page = r.recovery.input_page(ACTOR, incident, "choose_replacements", number)
        row = page["row"]
        r.recovery.save_input(
            ACTOR,
            incident,
            row["Revision"],
            row["EvidenceHash"],
            "choose_replacements",
            number,
            page["draft_version"],
            {
                field["key"]: (
                    "owner@example.com"
                    if field["key"] == "owner_email"
                    else "refreshed-" + field["key"]
                )
                for field in page["fields"]
            },
        )
    preview = r.recovery.input_confirmation(ACTOR, incident, "choose_replacements")
    row = preview["row"]
    r.recovery.execute_input(
        ACTOR,
        incident,
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        preview["draft_version"],
    )
    assert apply(r, "verify_replacements")["evidence"]["outcome"] == "activation_required"
    assert (
        r.recovery.review(ACTOR, alert["IncidentID"])["evidence"]["outcome"]
        == "superseded_proposal"
    )
    assert (
        apply(r, "activate_replacements")["evidence"]["outcome"] == "rollover_continuation_required"
    )


@pytest.mark.parametrize(
    "row", [dict(JobID=None, OutputOperationID=None), dict(JobID="x", OutputOperationID="y")]
)
def test_ambiguous_owner_never_selects_a_recovery_workflow(row):
    with pytest.raises(SourceConflict, match="exact replacement owner"):
        EvidenceCatalogDAL._replacement_owner(row)
