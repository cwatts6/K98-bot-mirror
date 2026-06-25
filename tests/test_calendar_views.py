from types import SimpleNamespace

import pytest

from event_calendar import reminder_config_service
from ui.views import calendar as cv
from ui.views.reminder_config import ReminderConfigView


def test_reminder_config_view_does_not_write_prefs_directly():
    from pathlib import Path

    source = Path("ui/views/reminder_config.py").read_text(encoding="utf-8")
    assert "from event_calendar.reminder_prefs_store import set_user_prefs" not in source
    assert "set_user_prefs(" not in source


@pytest.mark.asyncio
async def test_reminder_config_save_acknowledges_before_post_save_refresh(monkeypatch):
    calls = []

    def _save_preferences(*args, **kwargs):
        calls.append("save")
        return reminder_config_service.CalendarReminderMutationResult(
            ok=True,
            message="saved",
        )

    async def _on_saved(_interaction):
        calls.append("on_saved")

    class _Response:
        async def send_message(self, *args, **kwargs):
            calls.append("send")

        async def edit_message(self, *args, **kwargs):
            calls.append("edit")

    monkeypatch.setattr(
        reminder_config_service,
        "save_user_calendar_reminder_preferences",
        _save_preferences,
    )

    view = ReminderConfigView(
        owner_user_id=42,
        user_id=42,
        initial_prefs={
            "enabled": True,
            "by_event_type": {"raid": ["24h"]},
        },
        known_event_types=["raid"],
        on_saved=_on_saved,
    )
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        response=_Response(),
        message=SimpleNamespace(),
    )

    await view.save_button.callback(interaction)

    assert calls == ["save", "edit", "on_saved"]


def test_allowed_days_has_365_not_356():
    days = cv.allowed_days()
    assert 365 in days
    assert 356 not in days


def test_cache_footer_uses_payload_fields():
    s = {
        "cache_age_minutes": 5,
        "payload": {"generated_utc": "x", "horizon_days": 30, "source": "sql"},
    }
    out = cv.cache_footer(s)
    assert "generated_utc=x" in out
    assert "horizon_days=30" in out
    assert "source=sql" in out


def test_grouped_embed_build_smoke():
    events = [
        {
            "title": "A",
            "start_utc": "2026-03-10T00:00:00+00:00",
            "end_utc": "2026-03-10T01:00:00+00:00",
        },
        {
            "title": "B",
            "start_utc": "2026-03-10T02:00:00+00:00",
            "end_utc": "2026-03-10T03:00:00+00:00",
        },
    ]
    emb = cv.build_pinned_calendar_embed(events=events, footer="f")
    assert emb.fields
    assert emb.footer.text == "f"
