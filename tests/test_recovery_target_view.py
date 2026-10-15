"""Admin link pages refresh evidence and keep every click permission checked."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.recovery_service import SourceConflict
from tests.test_guided_recovery import ACTOR, setup
from ui.views import recovery_target_view as view
from ui.views.recovery_view import RecoveryIncidentView


@pytest.fixture
def interaction(monkeypatch):
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock())
    monkeypatch.setattr(view, "report_error", AsyncMock())
    return SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))


def row():
    _, _, _, current = setup()
    current["evidence"].update(
        targets=["old-file-" + str(i) for i in range(7)],
        replacements={"old-file-" + str(i): "new-file-" + str(i) for i in range(7)},
        delivery=dict(job_id="replacement-job"),
    )
    return current


@pytest.mark.asyncio
async def test_pages_are_bounded_and_refresh_links_after_reopening(interaction):
    current = row()
    view.call.return_value = current
    await view.show_target_page(interaction, current["IncidentID"], 0)
    sent = interaction.followup.send.call_args.kwargs
    assert sent["ephemeral"] and len(sent["embed"].fields) == 5
    assert sent["view"].previous.disabled and not sent["view"].next.disabled
    newer = deepcopy(current)
    newer["Revision"] += 1
    newer["evidence"]["replacements"]["old-file-5"] = "refreshed-file"
    view.call.return_value = newer
    await sent["view"].next.callback(interaction)
    sent = interaction.followup.send.call_args.kwargs
    assert len(sent["embed"].fields) == 2 and sent["view"].next.disabled
    assert "/refreshed-file/edit" in sent["embed"].fields[0].value
    assert view.call.await_count == 2


@pytest.mark.asyncio
async def test_revoked_admin_cannot_read_link_page(interaction, monkeypatch):
    def denied(_):
        raise SourceConflict("Admin access revoked")

    monkeypatch.setattr(view, "actor_for", denied)
    await view.show_target_page(interaction, row()["IncidentID"], 0)
    view.call.assert_not_called()
    view.report_error.assert_awaited_once()
    interaction.followup.send.assert_not_called()


@pytest.mark.asyncio
async def test_final_incident_keeps_output_links_and_removes_repair_link():
    current = row()
    current["State"] = "resolved"
    current["evidence"]["actions"] = {}
    labels = {button.label for button in RecoveryIncidentView(current).children}
    assert "Review output links" in labels
    assert "Review replacement export" not in labels
