from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from player_self_service.reminders_summary import (
    CalendarEventCatalog,
    NextScheduledReminderAlert,
    ReminderCompleteness,
    ReminderConfigurationState,
    ReminderHeroKind,
    alert_time_label,
    build_reminders_summary_payload,
    calendar_event_label,
    format_absolute_utc,
    next_alert_hero,
    no_upcoming_hero,
    unavailable_hero,
)

NOW = datetime(2026, 7, 14, 15, 30, tzinfo=UTC)
CATALOG = CalendarEventCatalog(
    available=True,
    event_types=(
        "20gh",
        "ark",
        "armament_reveal",
        "ceroli",
        "dhalruk",
        "esmeralda",
    ),
)


def _payload(
    *,
    kvk: object = None,
    calendar: object = None,
    catalog: CalendarEventCatalog = CATALOG,
):
    return build_reminders_summary_payload(
        viewer_discord_id=42,
        display_name="Tester",
        kvk_config=kvk,
        calendar_prefs=calendar or {"enabled": False, "by_event_type": {}},
        calendar_catalog=catalog,
        generated_at_utc=NOW,
    )


def test_active_summary_uses_friendly_labels_order_counts_and_coverage() -> None:
    payload = _payload(
        kvk={"subscriptions": ["altars"], "reminder_times": ["now", "24h", "24h"]},
        calendar={
            "enabled": True,
            "by_event_type": {
                "armament_reveal": ["start", "7d"],
                "20gh": ["24h"],
                "ark": ["7d"],
            },
        },
    )

    assert payload.configuration_state is ReminderConfigurationState.ACTIVE
    assert payload.state_supporting_text == "2 of 2 systems enabled"
    assert payload.kvk.state_count_line == "ON • 1 event • 2 alert times"
    assert payload.kvk.event_summary == "Altars"
    assert payload.kvk.time_summary == "24h • At start"
    assert payload.kvk.coverage_label == "Coverage: 24h → start"
    assert payload.calendar.event_summary == "20 GH • Ark of Osiris • Armament Reveal"
    assert payload.calendar.time_summary == "7d • 24h • At start"
    assert payload.calendar.coverage_label == "Coverage: 7d → start"
    assert payload.hero.kind is ReminderHeroKind.COVERAGE
    assert payload.insight == "Both systems are active; coverage begins 7d before event start."


def test_review_states_cover_missing_events_times_and_both() -> None:
    missing_events = _payload(
        kvk={"subscriptions": [], "reminder_times": ["24h"]},
    )
    missing_times = _payload(
        kvk={"subscriptions": ["ruins"], "reminder_times": []},
    )
    missing_both = _payload(
        kvk={"subscriptions": [], "reminder_times": []},
    )

    assert missing_events.configuration_state is ReminderConfigurationState.REVIEW
    assert missing_events.kvk.completeness is ReminderCompleteness.MISSING_EVENTS
    assert missing_events.state_supporting_text == "KVK needs an event"
    assert missing_events.insight == (
        "KVK reminders are enabled, but no event types are selected."
    )
    assert missing_times.kvk.completeness is ReminderCompleteness.MISSING_TIMES
    assert missing_times.state_supporting_text == "KVK needs an alert time"
    assert missing_both.kvk.completeness is ReminderCompleteness.MISSING_BOTH
    assert missing_both.insight == "KVK reminders need an event and an alert time."


def test_both_systems_off_retain_saved_calendar_choices_honestly() -> None:
    payload = _payload(
        calendar={
            "enabled": False,
            "by_event_type": {"ark": ["7d", "start"]},
        },
    )

    assert payload.configuration_state is ReminderConfigurationState.OFF
    assert payload.state_supporting_text == "All reminder systems are off"
    assert payload.calendar.state_count_line == "OFF • 1 saved event • 2 saved alert times"
    assert payload.calendar.coverage_label == "Saved coverage: 7d → start"
    assert payload.insight == "All reminders are off; use Manage to choose what you want to receive."


def test_disabled_system_does_not_make_active_configuration_review() -> None:
    payload = _payload(
        kvk={"subscriptions": ["major"], "reminder_times": ["4h"]},
        calendar={
            "enabled": False,
            "by_event_type": {"retired_event": ["not_a_time"]},
        },
    )

    assert payload.configuration_state is ReminderConfigurationState.ACTIVE
    assert payload.calendar.unavailable_event_count == 1
    assert payload.calendar.event_summary == "Unavailable event"
    assert "retired_event" not in payload.calendar.event_summary
    assert "not_a_time" not in payload.calendar.time_summary
    assert payload.insight == "Calendar reminders are off; only KVK alerts will be sent."


def test_enabled_unknown_selections_are_review_without_raw_key_disclosure() -> None:
    payload = _payload(
        calendar={
            "enabled": True,
            "by_event_type": {
                "armament_reveal": ["7d"],
                "retired_event": ["not_a_time"],
            },
        },
    )

    assert payload.configuration_state is ReminderConfigurationState.REVIEW
    assert payload.calendar.completeness is ReminderCompleteness.UNAVAILABLE_SELECTION
    assert payload.calendar.unavailable_event_count == 1
    assert payload.calendar.unavailable_time_count == 1
    combined = " ".join(
        (
            payload.calendar.state_count_line,
            payload.calendar.event_summary,
            payload.calendar.time_summary,
            payload.insight,
        )
    )
    assert "retired_event" not in combined
    assert "not_a_time" not in combined
    assert "Unavailable event" in combined
    assert "Unavailable alert time" in combined


def test_calendar_event_overflow_is_deterministic() -> None:
    payload = _payload(
        calendar={
            "enabled": True,
            "by_event_type": {
                "esmeralda": ["24h"],
                "dhalruk": ["24h"],
                "ceroli": ["24h"],
                "armament_reveal": ["24h"],
                "ark": ["24h"],
            },
        },
    )

    assert payload.calendar.selected_event_count == 5
    assert payload.calendar.hidden_event_count == 2
    assert payload.calendar.event_summary == "Ark of Osiris • Armament Reveal • Ceroli • + 2 more"


def test_now_and_start_are_presentation_synonyms_only() -> None:
    assert alert_time_label("now") == "At start"
    assert alert_time_label("start") == "At start"
    assert calendar_event_label("armament_reveal") == "Armament Reveal"


def test_catalog_failure_does_not_make_saved_calendar_configuration_review() -> None:
    payload = _payload(
        calendar={
            "enabled": True,
            "by_event_type": {"armament_reveal": ["7d"]},
        },
        catalog=CalendarEventCatalog(available=False, event_types=()),
    )

    assert payload.configuration_state is ReminderConfigurationState.ACTIVE
    assert payload.calendar.event_summary == "Armament Reveal"
    assert "Calendar event catalogue unavailable" in payload.warnings


def test_temporary_settings_source_failure_degrades_without_hiding_healthy_system() -> None:
    payload = build_reminders_summary_payload(
        viewer_discord_id=42,
        display_name="Tester",
        kvk_config=None,
        calendar_prefs={"enabled": True, "by_event_type": {"ark": ["24h"]}},
        calendar_catalog=CATALOG,
        generated_at_utc=NOW,
        kvk_source_available=False,
    )

    assert payload.configuration_state is ReminderConfigurationState.ACTIVE
    assert payload.kvk.state_count_line == "REVIEW • Settings unavailable"
    assert payload.calendar.state_count_line == "ON • 1 event • 1 alert time"
    assert payload.insight == "KVK reminder settings are temporarily unavailable."
    assert "KVK settings unavailable" in payload.warnings


def test_contract_retains_internal_selected_keys_without_using_them_as_labels() -> None:
    payload = _payload(
        calendar={
            "enabled": True,
            "by_event_type": {"armament_reveal": ["start"]},
        },
    )

    assert payload.calendar.selected_event_keys == ("armament_reveal",)
    assert payload.calendar.selected_time_keys == ("start",)
    assert payload.calendar.event_labels == ("Armament Reveal",)
    assert payload.calendar.time_labels == ("At start",)


def test_insight_priority_prefers_configuration_then_disabled_then_coverage() -> None:
    review = _payload(
        kvk={"subscriptions": ["ruins"], "reminder_times": []},
        calendar={"enabled": False, "by_event_type": {}},
    )
    disabled = _payload(
        kvk={"subscriptions": ["ruins"], "reminder_times": ["24h"]},
    )
    neutral = _payload(
        kvk={"subscriptions": ["ruins"], "reminder_times": ["24h", "4h"]},
        calendar={"enabled": True, "by_event_type": {"ark": ["start"]}},
    )

    assert review.insight.startswith("KVK reminders are enabled")
    assert disabled.insight.startswith("Calendar reminders are off")
    assert neutral.insight == (
        "KVK coverage ends 4h before the event; no start-time alert is selected."
    )


def test_every_hero_variant_and_exact_utc_year_format() -> None:
    alert = NextScheduledReminderAlert(
        system_label="Calendar",
        event_label="Ark of Osiris",
        lead_time_label="24h",
        alert_at_utc=NOW + timedelta(days=2),
        event_start_at_utc=datetime(2027, 1, 2, 18, 0, tzinfo=UTC),
        occurrence_identity="ark-2027-01-02",
    )
    next_hero = next_alert_hero(alert, generated_at_utc=NOW)
    no_upcoming = no_upcoming_hero()
    passed = no_upcoming_hero(warning_windows_passed=True)
    unavailable = unavailable_hero()

    assert next_hero.kind is ReminderHeroKind.NEXT_ALERT
    assert "16 Jul 15:30 UTC" in next_hero.secondary_line
    assert "02 Jan 2027 18:00 UTC" in next_hero.secondary_line
    assert no_upcoming.kind is ReminderHeroKind.NO_UPCOMING
    assert "currently scheduled" in no_upcoming.primary_line
    assert "No alert remains" in passed.primary_line
    assert unavailable.kind is ReminderHeroKind.UNAVAILABLE
    assert format_absolute_utc(NOW, reference=replace(alert).alert_at_utc) == "14 Jul 15:30 UTC"
