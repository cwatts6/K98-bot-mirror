from __future__ import annotations

from datetime import date, datetime, time

import pytest

from commands import ark_cmds
from ui.views.ark_views import CreateArkMatchView


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return cls(2026, 3, 1, 12, 0, 0, tzinfo=tz)


class LaterDatetime(datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return cls(2026, 3, 20, 12, 0, 0, tzinfo=tz)


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


def test_parse_time():
    result = ark_cmds._parse_time("14:30")
    assert result == time(14, 30)


def test_compute_signup_close_friday():
    ark_weekend = date(2026, 3, 7)  # Saturday
    close_time = time(23, 0)

    close_dt = ark_cmds._compute_signup_close(ark_weekend, "Friday", close_time)

    assert close_dt.date() == date(2026, 3, 6)
    assert close_dt.time() == close_time
    assert close_dt.tzinfo is not None


def test_compute_signup_close_invalid_day():
    ark_weekend = date(2026, 3, 7)
    close_time = time(23, 0)

    with pytest.raises(ValueError, match="Invalid close day"):
        ark_cmds._compute_signup_close(ark_weekend, "Funday", close_time)


def test_compute_weekend_dates_from_anchor(monkeypatch):
    monkeypatch.setattr(ark_cmds, "datetime", FixedDatetime)

    anchor = date(2026, 3, 7)
    out = ark_cmds._compute_weekend_dates(anchor, frequency_weekends=2, count=2)

    assert out == [date(2026, 3, 7), date(2026, 3, 21)]


def test_compute_weekend_dates_after_anchor(monkeypatch):
    monkeypatch.setattr(ark_cmds, "datetime", LaterDatetime)

    anchor = date(2026, 3, 7)
    out = ark_cmds._compute_weekend_dates(anchor, frequency_weekends=2, count=2)

    assert out == [date(2026, 3, 21), date(2026, 4, 4)]


@pytest.mark.asyncio
async def test_create_match_view_confirm_state_and_time_options():
    view = CreateArkMatchView(
        author_id=123,
        alliances=["A1"],
        ark_weekend_dates=[date(2026, 3, 7)],
        allowed_days=["Saturday", "Sunday"],
        allowed_times_by_day={"Saturday": ["11:00", "13:00"]},
        on_confirm=lambda *_: None,
        on_cancel=None,
    )

    assert view.confirm_btn.disabled is True

    view.selection.alliance = "A1"
    view.selection.ark_weekend_date = date(2026, 3, 7)
    view.selection.match_day = "Saturday"
    view._refresh_time_options()
    view.selection.match_time_utc = "11:00"
    view._refresh_confirm_state()

    assert view.time_select.disabled is False
    assert [o.value for o in view.time_select.options] == ["11:00", "13:00"]
    assert view.confirm_btn.disabled is False


@pytest.mark.asyncio
async def test_create_match_view_interaction_check_rejects_other_user():
    view = CreateArkMatchView(
        author_id=555,
        alliances=["A1"],
        ark_weekend_dates=[date(2026, 3, 7)],
        allowed_days=["Saturday"],
        allowed_times_by_day={"Saturday": ["11:00"]},
        on_confirm=lambda *_: None,
        on_cancel=None,
    )

    interaction = DummyInteraction(user_id=111)
    ok = await view.interaction_check(interaction)

    assert ok is False
    assert interaction.response.sent
    assert "isn’t for you" in interaction.response.sent[0]["content"]
