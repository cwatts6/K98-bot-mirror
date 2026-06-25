from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from PIL import Image

from player_self_service.page_cards import HEIGHT, WIDTH, _page_copy, render_page_card
from player_self_service.service import (
    AccountStatus,
    ExportStatus,
    PlayerSelfServiceSummary,
    PreferenceStatus,
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
        preferences=PreferenceStatus(
            inventory_visibility="private",
            exports_summary="available through private export tools",
            next_action="Review preferences",
            vip_summary="Main Gov - 19",
        ),
        exports=ExportStatus(
            stats_export="stats export available",
            inventory_export="inventory export available for approved records",
            privacy_note="file exports are delivered privately",
        ),
    )


def test_render_page_cards_output_pngs_for_remaining_me_pages() -> None:
    for page in ("dashboard", "accounts", "reminders", "preferences", "exports"):
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
        preferences=PreferenceStatus(
            inventory_visibility="unknown",
            exports_summary="available through private export tools",
            next_action="Try again",
        ),
        exports=ExportStatus(
            stats_export="stats export available",
            inventory_export="inventory export available for approved records",
            privacy_note="file exports are delivered privately",
        ),
    )

    assert _page_copy("accounts", summary)[2] == "Actions available: Manage"
    assert _page_copy("accounts", summary)[3] == (
        "Find ID by name, then add a governor to an available account slot."
    )
    assert _page_copy("reminders", summary)[2] == "Actions available: Manage"
    assert "Calendar Settings" in _page_copy("reminders", summary)[3]
    assert _page_copy("preferences", summary)[2] == ("Actions available: Set Private, Update VIP")


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
        preferences=PreferenceStatus(
            inventory_visibility="private",
            exports_summary="available through private export tools",
            next_action="Review preferences",
            vip_summary="Main - 19, Alt 1 - 15",
        ),
        exports=ExportStatus(
            stats_export="stats export available",
            inventory_export="inventory export available for approved records",
            privacy_note="file exports are delivered privately",
        ),
    )

    assert "Farm 2" in _page_copy("accounts", summary)[4][2]
    assert _page_copy("preferences", summary)[4][1] == "VIP levels: Main - 19, Alt 1 - 15"


def test_page_card_reminder_lines_include_calendar_status() -> None:
    lines = _page_copy("reminders", _summary())[4]

    assert "KVK reminders: on" in lines
    assert "Calendar reminders: off" in lines
    assert "Calendar lead times: not set" in lines
