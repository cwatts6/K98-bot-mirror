"""A completed SQL step returns admins to current overall report/cache status."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.recovery_service import SourceConflict
from tests.test_guided_recovery import ACTOR, setup
from ui.views import recovery_view as view


@pytest.mark.asyncio
@pytest.mark.parametrize("denied", [False, True])
async def test_resolved_report_return_rechecks_access_and_loads_current_parent(monkeypatch, denied):
    _, _, _, child = setup()
    child["State"] = "resolved"
    child["SourceKind"] = "player_report"
    child["evidence"]["actions"] = {}
    child["evidence"]["recovery_links"] = [
        dict(
            label="Return to report and cache",
            kind="player_report_continuation",
            source_id="retained-parent",
        )
    ]
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))

    def actor(_):
        if denied:
            raise SourceConflict("Admin access revoked")
        return ACTOR

    monkeypatch.setattr(view, "actor_for", actor)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=child))
    monkeypatch.setattr(view, "report_error", AsyncMock())
    button = next(
        b
        for b in view.RecoveryIncidentView(child).children
        if b.label == "Return to report and cache"
    )
    await button.callback(interaction)
    if denied:
        view.call.assert_not_called()
        interaction.followup.send.assert_not_called()
        view.report_error.assert_awaited_once()
    else:
        view.call.assert_awaited_once_with(
            "review_source", ACTOR, "player_report_continuation", "retained-parent"
        )
        sent = interaction.followup.send.call_args.kwargs
        assert sent["ephemeral"] and not sent["allowed_mentions"].everyone


@pytest.mark.asyncio
async def test_unrelated_resolved_links_are_not_enabled():
    _, _, _, row = setup()
    row["State"] = "resolved"
    row["evidence"]["actions"] = {}
    row["evidence"]["recovery_links"] = [
        dict(label="Review old import", kind="stats_import", source_id="old")
    ]
    assert "Review old import" not in [b.label for b in view.RecoveryIncidentView(row).children]
