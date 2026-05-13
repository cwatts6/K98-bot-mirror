from datetime import UTC, datetime

import pytest

from commands.activity_cmds import _render_activity_top
from server_activity.activity_models import ActivityTopResult, ActivityUserSummary


def test_render_activity_top_empty():
    result = ActivityTopResult(
        window="24h",
        since_utc=datetime(2026, 4, 28, tzinfo=UTC),
        rows=[],
    )

    assert _render_activity_top(result) == "No tracked activity found for the last 24h."


def test_render_activity_top_breakdown():
    result = ActivityTopResult(
        window="7d",
        since_utc=datetime(2026, 4, 21, tzinfo=UTC),
        rows=[
            ActivityUserSummary(
                user_id=123,
                score=5,
                messages=2,
                reactions=1,
                voice_events=2,
            )
        ],
    )

    rendered = _render_activity_top(result)
    assert "Top active users - last 7d" in rendered
    assert "<@123> - 5 (messages 2, reactions 1, voice 2)" in rendered


@pytest.mark.asyncio
async def test_activity_command_registration_handoff(monkeypatch):
    import commands.activity_cmds as activity_cmds

    registered = {}

    class FakeBot:
        def slash_command(self, **kwargs):
            def _decorator(fn):
                registered[kwargs["name"]] = fn
                return fn

            return _decorator

    monkeypatch.setattr(activity_cmds, "GUILD_ID", 1)
    activity_cmds.register_activity(FakeBot())

    assert "activity_top" in registered
