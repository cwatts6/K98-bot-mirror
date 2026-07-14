from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO

from PIL import Image
import pytest

from player_self_service import reminders_renderer
from player_self_service.reminders_summary import (
    CalendarEventCatalog,
    NextScheduledReminderAlert,
    build_reminders_summary_payload,
    next_alert_hero,
    no_upcoming_hero,
    unavailable_hero,
)

NOW = datetime(2026, 7, 14, 15, 30, tzinfo=UTC)


def _payload():
    return build_reminders_summary_payload(
        viewer_discord_id=42,
        display_name="Tést Player 長い表示名 " * 4,
        kvk_config={
            "subscriptions": ["ruins", "altars", "major", "fights", "all"],
            "reminder_times": ["24h", "12h", "4h", "1h", "now"],
        },
        calendar_prefs={
            "enabled": True,
            "by_event_type": {
                "20gh": ["7d", "24h", "start"],
                "ark": ["7d"],
                "armament_reveal": ["24h"],
                "ceroli": ["24h"],
                "dhalruk": ["24h"],
            },
        },
        calendar_catalog=CalendarEventCatalog(
            available=True,
            event_types=("20gh", "ark", "armament_reveal", "ceroli", "dhalruk"),
        ),
        generated_at_utc=NOW,
    )


def test_renderer_uses_locked_dimensions_stable_filename_and_does_not_mutate_backdrop() -> None:
    before = reminders_renderer.BACKDROP_PATH.read_bytes()

    rendered = reminders_renderer.render_reminders_card(_payload())

    assert rendered.filename == "me_reminders_42.png"
    with Image.open(BytesIO(rendered.image_bytes.getvalue())) as image:
        assert image.size == (1702, 924)
        assert image.mode == "RGB"
    assert reminders_renderer.BACKDROP_PATH.read_bytes() == before


def test_renderer_supports_every_approved_hero_variant() -> None:
    payload = _payload()
    alert = NextScheduledReminderAlert(
        system_label="Calendar",
        event_label="Ark of Osiris",
        lead_time_label="24h",
        alert_at_utc=NOW + timedelta(hours=24),
        event_start_at_utc=NOW + timedelta(hours=48),
        occurrence_identity="ark-2026-07-16",
    )
    heroes = (
        next_alert_hero(alert, generated_at_utc=NOW),
        no_upcoming_hero(),
        payload.hero,
        unavailable_hero(),
    )

    for hero in heroes:
        rendered = reminders_renderer.render_reminders_card(replace(payload, hero=hero))
        with Image.open(BytesIO(rendered.image_bytes.getvalue())) as image:
            assert image.size == (1702, 924)


def test_renderer_rejects_wrong_sized_or_translucent_backdrop(tmp_path, monkeypatch) -> None:
    wrong_size = tmp_path / "wrong.png"
    Image.new("RGB", (100, 100), "black").save(wrong_size)
    monkeypatch.setattr(reminders_renderer, "BACKDROP_PATH", wrong_size)
    with pytest.raises(ValueError, match="must be 1702x924"):
        reminders_renderer.render_reminders_card(_payload())

    translucent = tmp_path / "translucent.png"
    Image.new("RGBA", (1702, 924), (0, 0, 0, 200)).save(translucent)
    monkeypatch.setattr(reminders_renderer, "BACKDROP_PATH", translucent)
    with pytest.raises(ValueError, match="fully opaque"):
        reminders_renderer.render_reminders_card(_payload())
