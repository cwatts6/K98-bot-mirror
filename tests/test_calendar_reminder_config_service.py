from __future__ import annotations

from event_calendar import reminder_config_service as service
from event_calendar.reminder_prefs import default_prefs, set_enabled, set_offsets_for_event_type


def test_state_from_prefs_summarizes_enabled_all_offsets() -> None:
    prefs = set_enabled(default_prefs(), True)
    prefs = set_offsets_for_event_type(
        prefs,
        event_type="all",
        offsets=["all"],
        known_event_types={"raid", "war"},
    )

    state = service.state_from_prefs(prefs)

    assert state.enabled is True
    assert state.selected_types == ("all",)
    assert state.selected_offsets == ("7d", "3d", "24h", "1h", "start")


def test_compose_prefs_payload_keeps_all_exclusive() -> None:
    payload = service.compose_prefs_payload(
        enabled=True,
        selected_types={"raid", "all"},
        selected_offsets={"24h", "start"},
        known_event_types={"raid", "war"},
    )

    assert payload == {
        "enabled": True,
        "by_event_type": {"all": ["24h", "start"]},
    }


def test_compose_prefs_payload_preserves_saved_types_when_known_types_unavailable() -> None:
    payload = service.compose_prefs_payload(
        enabled=False,
        selected_types={"raid"},
        selected_offsets={"24h"},
        known_event_types=set(),
    )

    assert payload == {
        "enabled": False,
        "by_event_type": {"raid": ["24h"]},
    }


def test_save_user_calendar_reminder_preferences_uses_writer() -> None:
    calls = []

    result = service.save_user_calendar_reminder_preferences(
        42,
        enabled=True,
        selected_types={"raid"},
        selected_offsets={"24h"},
        known_event_types={"raid"},
        writer=lambda user_id, payload: calls.append((user_id, payload)),
    )

    assert result.ok is True
    assert result.state is not None
    assert result.state.enabled is True
    assert calls == [(42, {"enabled": True, "by_event_type": {"raid": ["24h"]}})]


def test_save_user_calendar_reminder_preferences_rejects_unknown_type() -> None:
    calls = []

    result = service.save_user_calendar_reminder_preferences(
        42,
        enabled=True,
        selected_types={"unknown"},
        selected_offsets={"24h"},
        known_event_types={"raid"},
        writer=lambda user_id, payload: calls.append((user_id, payload)),
    )

    assert result.ok is False
    assert "Unknown calendar event type" in result.message
    assert calls == []
