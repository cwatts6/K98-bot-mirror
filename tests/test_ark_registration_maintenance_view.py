from __future__ import annotations

from datetime import date, time

import discord
import pytest

from ui.views.ark_views import ArkGovernorSelectView, ArkRegistrationMaintenanceView


class DummyResponse:
    def __init__(self) -> None:
        self.sent = []
        self.edits = []
        self._done = False

    async def send_message(self, content=None, **kwargs):
        self.sent.append({"content": content, **kwargs})
        self._done = True

    async def edit_message(self, content=None, view=None):
        self.edits.append({"content": content, "view": view})
        self._done = True

    def is_done(self) -> bool:
        return self._done


class DummyFollowup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, content=None, **kwargs):
        self.sent.append({"content": content, **kwargs})


class DummyUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class DummyInteraction:
    def __init__(self, user_id: int = 123) -> None:
        self.user = DummyUser(user_id)
        self.response = DummyResponse()
        self.followup = DummyFollowup()


class DummyMessage:
    def __init__(self) -> None:
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


@pytest.mark.asyncio
async def test_governor_select_timeout_disables_menu_and_runs_repair_callback():
    called = {"repair": 0}

    async def _repair():
        called["repair"] += 1

    view = ArkGovernorSelectView(
        author_id=123,
        options=[discord.SelectOption(label="Gov", value="1")],
        on_select=lambda *_: None,
        on_timeout_callback=_repair,
    )
    message = DummyMessage()
    view.message = message

    await view.on_timeout()

    assert called["repair"] == 1
    assert message.edits
    assert all(item.disabled for item in view.children)


@pytest.mark.asyncio
async def test_governor_select_timeout_accepts_sync_repair_callback():
    called = {"repair": 0}

    def _repair():
        called["repair"] += 1

    view = ArkGovernorSelectView(
        author_id=123,
        options=[discord.SelectOption(label="Gov", value="1")],
        on_select=lambda *_: None,
        on_timeout_callback=_repair,
    )

    await view.on_timeout()

    assert called["repair"] == 1


@pytest.mark.asyncio
async def test_registration_maintenance_view_select_enables_actions_and_calls_refresh():
    captured = {}
    matches = [
        {
            "MatchId": 44,
            "Alliance": "k98A",
            "ArkWeekendDate": date(2026, 5, 30),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(20, 0),
        }
    ]

    async def _refresh(_interaction, selection):
        captured["refresh"] = selection.match_id

    async def _force(_interaction, selection):
        captured["force"] = selection.match_id

    view = ArkRegistrationMaintenanceView(
        author_id=123,
        matches=matches,
        on_refresh=_refresh,
        on_force_announce=_force,
    )
    interaction = DummyInteraction()

    view._apply_match_selection(44)
    await view._on_refresh(interaction)

    assert view.refresh_btn.disabled is False
    assert view.force_btn.disabled is False
    assert captured == {"refresh": 44}


@pytest.mark.asyncio
async def test_registration_maintenance_view_reports_refresh_callback_failure():
    matches = [
        {
            "MatchId": 44,
            "Alliance": "k98A",
            "ArkWeekendDate": date(2026, 5, 30),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(20, 0),
        }
    ]

    async def _refresh(_interaction, _selection):
        raise RuntimeError("boom")

    view = ArkRegistrationMaintenanceView(
        author_id=123,
        matches=matches,
        on_refresh=_refresh,
        on_force_announce=lambda *_: None,
    )
    interaction = DummyInteraction()

    view._apply_match_selection(44)
    await view._on_refresh(interaction)

    assert interaction.response.sent
    assert "Failed to refresh" in interaction.response.sent[-1]["content"]


@pytest.mark.asyncio
async def test_registration_maintenance_view_reports_force_callback_failure():
    matches = [
        {
            "MatchId": 44,
            "Alliance": "k98A",
            "ArkWeekendDate": date(2026, 5, 30),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(20, 0),
        }
    ]

    async def _force(_interaction, _selection):
        raise RuntimeError("boom")

    view = ArkRegistrationMaintenanceView(
        author_id=123,
        matches=matches,
        on_refresh=lambda *_: None,
        on_force_announce=_force,
    )
    interaction = DummyInteraction()

    view._apply_match_selection(44)
    await view._on_force_announce(interaction)

    assert interaction.response.sent
    assert "Failed to repost" in interaction.response.sent[-1]["content"]
