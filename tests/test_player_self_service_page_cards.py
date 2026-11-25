from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from PIL import Image, ImageDraw
import pytest

from player_self_service.page_cards import (
    HEIGHT,
    WIDTH,
    _dashboard_rows,
    _font,
    _page_copy,
    _reminder_rows,
    _summarize_items_for_width,
    _text_width,
    render_page_card,
)
from player_self_service.service import (
    AccountStatus,
    CalendarReminderStatus,
    PlayerSelfServiceSummary,
    ReminderStatus,
)


def _summary() -> PlayerSelfServiceSummary:
    return PlayerSelfServiceSummary(
        discord_user_id=42,
        accounts=AccountStatus(
            state="single",
            linked_count=1,
            linked_label="1 linked",
            main_state="set",
            main_label="Main Gov (111)",
            next_action="Manage",
            account_names=("Main Gov",),
        ),
        reminders=ReminderStatus(
            state="on",
            event_summary="all KVK events",
            time_summary="24h, 4h, 1h",
            next_action="Manage",
        ),
    )


def test_render_page_cards_output_pngs_for_remaining_me_pages() -> None:
    for page in ("dashboard", "accounts", "reminders"):
        rendered = render_page_card(
            page,
            _summary(),
            display_name="Tester",
            generated_at_utc=datetime(2026, 6, 24, 8, 0, tzinfo=UTC),
        )

        assert rendered.filename == f"me_{page}_42.png"
        assert rendered.image_bytes.getbuffer().nbytes > 8_000

        image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
        assert image.format == "PNG"
        assert image.size == (WIDTH, HEIGHT)


def test_page_card_action_copy_uses_available_action_copy() -> None:
    summary = PlayerSelfServiceSummary(
        discord_user_id=42,
        accounts=AccountStatus(
            state="none",
            linked_count=0,
            linked_label="0 linked",
            main_state="not set",
            main_label="not set",
            next_action="Register",
        ),
        reminders=ReminderStatus(
            state="off",
            event_summary="not subscribed",
            time_summary="not set",
            next_action="Set up",
        ),
    )

    assert _page_copy("accounts", summary)[2] == "Actions available: Manage"
    assert _page_copy("accounts", summary)[3] == (
        "Find ID by name, then add a governor to an available account slot."
    )
    assert _page_copy("reminders", summary)[2] == "Actions available: Manage"
    assert "manage calendar reminders" in _page_copy("reminders", summary)[3]
    with pytest.raises(ValueError, match="Unsupported /me page card: preferences"):
        _page_copy("preferences", summary)
    assert _page_copy("dashboard", summary)[2] == (
        "Actions available: Accounts, Reminders, Preferences"
    )


def test_page_card_reminder_copy_treats_incomplete_as_setup() -> None:
    summary = PlayerSelfServiceSummary(
        discord_user_id=42,
        accounts=AccountStatus(
            state="single",
            linked_count=1,
            linked_label="1 linked",
            main_state="set",
            main_label="Main Gov (111)",
            next_action="Manage",
        ),
        reminders=ReminderStatus(
            state="off",
            event_summary="not subscribed",
            time_summary="not set",
            next_action="Set up",
            calendar=CalendarReminderStatus(
                state="incomplete",
                event_summary="raid",
                time_summary="not set",
                next_action="Finish setup",
            ),
        ),
    )

    assert _page_copy("reminders", summary)[1] == "incomplete"
    assert "Choose KVK reminders" in _page_copy("reminders", summary)[3]


def test_page_card_account_and_vip_lines_show_full_summary() -> None:
    summary = PlayerSelfServiceSummary(
        discord_user_id=42,
        accounts=AccountStatus(
            state="multiple",
            linked_count=5,
            linked_label="multiple linked",
            main_state="set",
            main_label="Main Gov (111)",
            next_action="Manage",
            account_names=("Main", "Alt 1", "Alt 2", "Farm 1", "Farm 2"),
        ),
        reminders=ReminderStatus(
            state="off",
            event_summary="not subscribed",
            time_summary="not set",
            next_action="Set up",
        ),
    )

    assert "Farm 2" in _page_copy("accounts", summary)[4][2]
    with pytest.raises(ValueError, match="Unsupported /me page card: preferences"):
        _page_copy("preferences", summary)


def test_page_card_reminder_lines_include_calendar_status() -> None:
    lines = _page_copy("reminders", _summary())[4]

    assert "KVK reminders: on" in lines
    assert "Calendar reminders: off" in lines
    assert "Calendar lead times: not set" in lines


def test_dashboard_card_rows_group_status_by_user_workflow() -> None:
    summary = _summary()
    rows = _dashboard_rows(summary)

    assert rows[0][0].value == "Main Gov (111)"
    assert rows[0][0].label == ""
    assert rows[0][0].detail == ""
    assert rows[0][1].value == "Accounts Linked: 1"
    assert rows[1][0].value == "KVK Reminders: ON"
    assert rows[1][0].detail == "All"
    assert rows[1][1].value == "Calendar Reminders: OFF"
    assert len(rows) == 2


def test_reminder_card_rows_split_kvk_and_calendar() -> None:
    rows = _reminder_rows(_summary())

    assert [cell.label for cell in rows[0]] == ["KVK Reminders", "KVK Events", "KVK Time"]
    assert [cell.label for cell in rows[1]] == [
        "Calendar Reminders",
        "Calendar Events",
        "Calendar Times",
    ]
    assert rows[0][0].value == "ON"
    assert rows[1][0].value == "OFF"


def test_calendar_event_summary_compacts_to_two_rows_with_remaining_count() -> None:
    image = Image.new("RGB", (420, 180))
    draw = ImageDraw.Draw(image)
    value = "20gh, ark, armament_reveal, ceroli, dhalruk, esmeralda, hammer, olympia"
    font = _font(34, bold=True)
    width = (
        max(
            _text_width(draw, "plus 8 more events", font),
            *(_text_width(draw, item, font) for item in value.split(", ")),
        )
        + 20
    )

    lines = _summarize_items_for_width(
        draw,
        value,
        width=width,
        font=font,
        max_lines=2,
    )

    assert len(lines) <= 2
    assert "plus" in " ".join(lines)
    assert "more events" in " ".join(lines)
