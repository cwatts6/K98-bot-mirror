from __future__ import annotations

from datetime import date, time

import pytest

from ui.views.ark_views import CancelArkMatchView


class DummyResponse:
    def __init__(self) -> None:
        self.sent = []
        self.edits = []

    async def send_message(self, content: str, ephemeral: bool = False):
        self.sent.append({"content": content, "ephemeral": ephemeral})

    async def edit_message(self, content: str | None = None, view=None):
        self.edits.append({"content": content, "view": view})


class DummyUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class DummyInteraction:
    def __init__(self, user_id: int) -> None:
        self.user = DummyUser(user_id)
        self.response = DummyResponse()


def _make_view():
    matches = [
        {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": date(2026, 3, 7),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(11, 0),
        }
    ]
    return CancelArkMatchView(
        author_id=999,
        matches=matches,
        on_confirm=lambda *_: None,
        on_cancel=None,
        notify_toggle_enabled=False,
    )


@pytest.mark.asyncio
async def test_cancel_view_interaction_check_rejects_other_user():
    view = _make_view()
    interaction = DummyInteraction(user_id=111)

    ok = await view.interaction_check(interaction)

    assert ok is False
    assert interaction.response.sent
    assert "isn’t for you" in interaction.response.sent[0]["content"]


@pytest.mark.asyncio
async def test_cancel_view_notify_toggle_disabled():
    view = _make_view()
    interaction = DummyInteraction(user_id=999)

    await view._on_notify_toggle(interaction)

    assert interaction.response.sent
    assert "not enabled yet" in interaction.response.sent[0]["content"]
    assert view.selection.notify_players is False


@pytest.mark.asyncio
async def test_cancel_view_confirm_enables_on_match_select():
    view = _make_view()

    assert view.confirm_btn.disabled is True
    view._apply_match_selection(1)

    assert view.confirm_btn.disabled is False


@pytest.mark.asyncio
async def test_cancel_view_confirm_calls_callback_with_selection():
    captured = {}

    def _on_confirm(_interaction, selection):
        captured["selection"] = selection

    matches = [
        {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": date(2026, 3, 7),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(11, 0),
        }
    ]
    view = CancelArkMatchView(
        author_id=999,
        matches=matches,
        on_confirm=_on_confirm,
        on_cancel=None,
        notify_toggle_enabled=False,
    )

    interaction = DummyInteraction(user_id=999)

    view._apply_match_selection(1)
    await view._on_confirm(interaction)

    assert "selection" in captured
    assert captured["selection"].match_id == 1


@pytest.mark.asyncio
async def test_cancel_view_confirm_not_called_without_match_id():
    called = {"flag": False}

    def _on_confirm(_interaction, _selection):
        called["flag"] = True

    matches = [
        {
            "MatchId": 1,
            "Alliance": "K98",
            "ArkWeekendDate": date(2026, 3, 7),
            "MatchDay": "Sat",
            "MatchTimeUtc": time(11, 0),
        }
    ]
    view = CancelArkMatchView(
        author_id=999,
        matches=matches,
        on_confirm=_on_confirm,
        on_cancel=None,
        notify_toggle_enabled=False,
    )

    interaction = DummyInteraction(user_id=999)

    await view._on_confirm(interaction)

    assert called["flag"] is False
    assert interaction.response.sent
    assert "No match selected" in interaction.response.sent[0]["content"]
