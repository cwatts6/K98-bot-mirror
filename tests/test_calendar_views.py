from types import SimpleNamespace

import pytest

from core.discord_embed_limits import validate_embed_payload
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


def test_pinned_embed_has_exact_marker_and_only_complete_pathological_events():
    events = [
        {
            "title": f"{index}-" + ("T" * 2000),
            "variant": "V" * 500,
            "start_utc": "2026-03-10T00:00:00+00:00",
            "end_utc": "2026-03-10T01:00:00+00:00",
            "link_url": "https://example.invalid/" + ("a" * 476),
        }
        for index in range(20)
    ]
    embed = cv.build_pinned_calendar_embed(events=events, footer="f")
    values = "\n".join(field.value for field in embed.fields)
    shown = values.count("starts:")

    assert f"{len(events) - shown} additional calendar events omitted" in values
    assert values.count("[link](") == shown
    assert not validate_embed_payload(embed)


def test_calendar_link_is_never_truncated_into_a_broken_url():
    event = {
        "title": "Event",
        "start_utc": "2026-03-10T00:00:00+00:00",
        "end_utc": "2026-03-10T01:00:00+00:00",
        "link_url": "https://example.invalid/" + ("a" * 477),
    }
    line = cv.event_line(event)
    assert "link omitted: source URL exceeds the supported length" in line
    assert "[link](" not in line


def test_pinned_field_slot_exhaustion_reserves_exact_marker():
    events = [
        {
            "title": f"Event {index}",
            "start_utc": f"2026-03-{index + 1:02d}T00:00:00+00:00",
            "end_utc": f"2026-03-{index + 1:02d}T01:00:00+00:00",
        }
        for index in range(30)
    ]
    embed = cv.build_pinned_calendar_embed(events=events, footer="f")
    values = "\n".join(field.value for field in embed.fields)
    shown = values.count("starts:")

    assert len(embed.fields) == 25
    assert f"{30 - shown} additional calendar events omitted" in values
    assert not validate_embed_payload(embed)


def test_pinned_embed_reserves_aggregate_budget_for_omission_marker():
    events = [
        {
            "title": "Pathological event",
            "start_utc": "2026-03-10T00:00:00+00:00",
            "end_utc": "2026-03-10T01:00:00+00:00",
        }
    ]

    embed = cv.build_pinned_calendar_embed(
        events=events,
        description="d" * 4096,
        footer="f" * 2048,
    )

    assert not validate_embed_payload(embed)
    assert len(embed.footer.text) < 2048
    assert len(embed.description) == 4096
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "… More calendar events"
    assert (
        embed.fields[0].value
        == "1 additional calendar event omitted to fit Discord limits — use /calendar."
    )
