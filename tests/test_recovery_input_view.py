from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.test_guided_recovery import ACTOR, setup
from ui.views import recovery_input_view as view


def page():
    _, _, _, row = setup()
    row["evidence"]["actions"] = {
        "choose_replacements": dict(
            label="Enter replacement links",
            check="Use fresh files",
            effect="Verify before using",
            input=True,
        )
    }
    return dict(
        row=row,
        action="choose_replacements",
        page=0,
        pages=2,
        completed=5,
        total=6,
        draft_version=1,
        fields=[
            dict(
                key=str(i),
                label=f"Role {i}",
                value="fresh-file-" + str(i),
                help="Required owner and access policy",
                max_length=512,
            )
            for i in range(5)
        ],
    )


@pytest.fixture
def interaction(monkeypatch):
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock())
    monkeypatch.setattr(view, "report_error", AsyncMock())
    return SimpleNamespace(
        response=SimpleNamespace(send_modal=AsyncMock()), followup=SimpleNamespace(send=AsyncMock())
    )


@pytest.mark.asyncio
async def test_open_modal_is_immediate_and_page_state_is_bounded(interaction):
    current = page()
    controls = view.RecoveryInputView(current)
    assert controls.previous.disabled and controls.review.disabled
    await controls.edit.callback(interaction)
    modal = interaction.response.send_modal.call_args.args[0]
    assert len(modal.children) == 5
    assert all(item.required and item.max_length == 512 for item in modal.children)
    view.call.assert_not_called()


@pytest.mark.asyncio
async def test_modal_submits_exact_saved_revision_and_version(interaction):
    current = page()
    view.call.return_value = current
    modal = view.RecoveryInputModal(current)
    await modal.callback(interaction)
    row = current["row"]
    view.call.assert_awaited_once_with(
        "save_input",
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        0,
        1,
        {str(i): "fresh-file-" + str(i) for i in range(5)},
    )
    assert interaction.followup.send.call_args.kwargs["ephemeral"]


@pytest.mark.asyncio
async def test_review_does_not_execute_and_confirmation_binds_draft(interaction):
    current = page()
    current["completed"] = current["total"]
    proposal = dict(
        row=current["row"],
        action=current["action"],
        draft_version=8,
        preview="Six exact files under the registered owner.",
    )
    view.call.return_value = proposal
    controls = view.RecoveryInputView(current, return_to="original-rollover-incident")
    await controls.review.callback(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert isinstance(sent["view"], view.RecoveryInputConfirmView)
    assert sent["view"].return_to == "original-rollover-incident"
    assert sent["embed"].description == proposal["preview"]
    view.call.assert_awaited_once_with(
        "input_confirmation", ACTOR, current["row"]["IncidentID"], current["action"]
    )
    view.call.reset_mock()
    view.call.return_value = current["row"]
    await sent["view"].confirm.callback(interaction)
    assert (
        interaction.followup.send.call_args.kwargs["view"].return_to == "original-rollover-incident"
    )
    row = current["row"]
    view.call.assert_awaited_once_with(
        "execute_input",
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        current["action"],
        8,
    )


@pytest.mark.asyncio
async def test_unauthorized_form_submit_never_calls_service(interaction, monkeypatch):
    from kvk.dal.new_source_import_dal import SourceConflict

    def denied(_):
        raise SourceConflict("Wrong admin or channel")

    monkeypatch.setattr(view, "actor_for", denied)
    await view.RecoveryInputModal(page()).callback(interaction)
    view.call.assert_not_called()
    view.report_error.assert_awaited_once()


@pytest.mark.asyncio
async def test_expired_form_acknowledgement_does_not_submit(interaction):
    view.safe_defer.return_value = False
    await view.RecoveryInputModal(page()).callback(interaction)
    view.call.assert_not_called()
