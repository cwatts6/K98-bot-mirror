"""Real recovery buttons retain authorization and evidence-bound confirmation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.test_guided_recovery import ACTOR, setup


@pytest.mark.asyncio
async def test_refused_stage_link_opens_exact_blocking_read(monkeypatch):
    from ui.views import recovery_view as view

    _, _, _, row = setup()
    row["evidence"].update(
        actions={},
        recovery_links=[
            dict(label="Review blocking stage", kind="configuration_read", source_id="read-id")
        ],
    )
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Review blocking stage"
    )
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review_source", ACTOR, "configuration_read", "read-id")
    assert interaction.followup.send.call_args.kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_blocker_link_does_not_bypass_admin_check(monkeypatch):
    import bot_config
    from ui.views import recovery_view as view

    for key, value in (("ADMIN_USER_ID", 1), ("GUILD_ID", 2), ("NOTIFY_CHANNEL_ID", 3)):
        monkeypatch.setattr(bot_config, key, value)
    _, _, _, row = setup()
    row["evidence"].update(
        actions={},
        recovery_links=[
            dict(label="Review blocking stage", kind="stats_import", source_id="receipt-id")
        ],
    )
    monkeypatch.setattr(view, "call", AsyncMock())
    monkeypatch.setattr(view, "report_error", AsyncMock())
    interaction = SimpleNamespace(user=SimpleNamespace(id=99), guild_id=2, channel_id=3)
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Review blocking stage"
    )
    await button.callback(interaction)
    view.call.assert_not_called()
    view.report_error.assert_awaited_once()


@pytest.mark.asyncio
async def test_resume_preview_explains_no_excel_or_archive_replay(monkeypatch):
    from ui.views import recovery_view as view

    _, _, _, row = setup()
    row["evidence"]["actions"] = {
        "resume_sql_stage": dict(
            label="Resume saved SQL stage",
            check="Confirm the retained scan; Excel conversion and archive will not run again.",
            effect="Use exact retained inputs and verify the receipt.",
        )
    }
    monkeypatch.setattr(view, "actor_for", lambda _: ACTOR)
    monkeypatch.setattr(view, "safe_defer", AsyncMock(return_value=True))
    monkeypatch.setattr(view, "call", AsyncMock(return_value=row))
    interaction = SimpleNamespace(followup=SimpleNamespace(send=AsyncMock()))
    button = next(
        b for b in view.RecoveryIncidentView(row).children if b.label == "Resume saved SQL stage"
    )
    await button.callback(interaction)
    view.call.assert_awaited_once_with("review", ACTOR, row["IncidentID"])
    message = interaction.followup.send.call_args.kwargs
    assert isinstance(message["view"], view.RecoveryConfirmView)
    assert message["view"].action == "resume_sql_stage"
    assert "archive will not run again" in message["embed"].fields[0].value
