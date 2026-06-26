from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from PIL import Image, ImageDraw

from player_self_service.page_cards import (
    HEIGHT,
    WIDTH,
    _dashboard_rows,
    _font,
    _inventory_rows,
    _page_copy,
    _reminder_rows,
    _summarize_items_for_width,
    _text_width,
    render_page_card,
)
from player_self_service.service import (
    AccountStatus,
    CalendarReminderStatus,
    ExportStatus,
    InventoryCategoryStatus,
    InventoryStatus,
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
            stats_export="Excel / CSV / Google Sheets",
            inventory_export="Excel / CSV / Google Sheets",
            privacy_note="Private",
        ),
        inventory=InventoryStatus(
            state="available",
            account_summary="1 registered governor(s) with complete approved inventory data.",
            resources=InventoryCategoryStatus(
                state="available",
                value="1.2B RSS",
                detail="1/1 governors | latest 2026-06-25",
                governor_count=1,
                latest_scan_label="2026-06-25",
            ),
            speedups=InventoryCategoryStatus(
                state="available",
                value="365d total",
                detail="1/1 governors | latest 2026-06-25",
                governor_count=1,
                latest_scan_label="2026-06-25",
            ),
            materials=InventoryCategoryStatus(
                state="available",
                value="42 legendary",
                detail="1/1 governors | latest 2026-06-25",
                governor_count=1,
                latest_scan_label="2026-06-25",
            ),
            upload_guidance="Use `/inventory import` in the inventory upload channel.",
        ),
    )


def test_render_page_cards_output_pngs_for_remaining_me_pages() -> None:
    for page in ("dashboard", "accounts", "reminders", "preferences", "inventory", "exports"):
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
            stats_export="Excel / CSV / Google Sheets",
            inventory_export="Excel / CSV / Google Sheets",
            privacy_note="Private",
        ),
    )

    assert _page_copy("accounts", summary)[2] == "Actions available: Manage"
    assert _page_copy("accounts", summary)[3] == (
        "Find ID by name, then add a governor to an available account slot."
    )
    assert _page_copy("reminders", summary)[2] == "Actions available: Manage"
    assert "manage calendar reminders" in _page_copy("reminders", summary)[3]
    assert _page_copy("preferences", summary)[2] == ("Actions available: Set Private, Update VIP")
    assert _page_copy("inventory", summary)[0] == "Inventory"
    assert _page_copy("exports", summary)[1] == "private"
    assert _page_copy("dashboard", summary)[2] == (
        "Actions available: Accounts, Reminders, Preferences, Inventory, Exports"
    )
    assert _page_copy("exports", summary)[2] == "Actions: Export Stats, Export Inventory"
    assert _page_copy("exports", summary)[3] == ""
    assert _page_copy("exports", summary)[4] == (
        "Stats: Excel / CSV / Google Sheets",
        "Inventory: Excel / CSV / Google Sheets",
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
        preferences=PreferenceStatus(
            inventory_visibility="private",
            exports_summary="available through private export tools",
            next_action="Review preferences",
        ),
        exports=ExportStatus(
            stats_export="Excel / CSV / Google Sheets",
            inventory_export="Excel / CSV / Google Sheets",
            privacy_note="Private",
        ),
    )

    assert _page_copy("reminders", summary)[1] == "incomplete"
    assert "Choose KVK reminders" in _page_copy("reminders", summary)[3]


def test_page_card_export_copy_handles_unavailable_state() -> None:
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
            inventory_visibility="private",
            exports_summary="available through private export tools",
            next_action="Review preferences",
        ),
        exports=ExportStatus(
            stats_export="Unavailable",
            inventory_export="Unavailable",
            privacy_note="Private",
            action_state="unavailable",
            action_summary="Register an account first.",
        ),
    )

    assert _page_copy("exports", summary)[1] == "unavailable"
    assert _page_copy("exports", summary)[2] == "Actions unavailable"
    assert _page_copy("exports", summary)[3] == "Register an account first."
    assert _page_copy("exports", summary)[4] == (
        "Stats: Unavailable",
        "Inventory: Unavailable",
        "Register an account first.",
    )


def test_page_card_export_copy_handles_guidance_state() -> None:
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
        ),
        preferences=PreferenceStatus(
            inventory_visibility="private",
            exports_summary="available through private export tools",
            next_action="Review preferences",
        ),
        exports=ExportStatus(
            stats_export="Legacy",
            inventory_export="Legacy",
            privacy_note="Private",
            action_state="guidance",
            action_summary="Use legacy commands.",
        ),
    )

    assert _page_copy("exports", summary)[1] == "private"
    assert _page_copy("exports", summary)[2] == "Guidance only"
    assert _page_copy("exports", summary)[3] == "Use legacy commands."
    assert _page_copy("exports", summary)[4] == (
        "Stats: Legacy",
        "Inventory: Legacy",
    )


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
            stats_export="Excel / CSV / Google Sheets",
            inventory_export="Excel / CSV / Google Sheets",
            privacy_note="Private",
        ),
    )

    assert "Farm 2" in _page_copy("accounts", summary)[4][2]
    assert _page_copy("preferences", summary)[4][1] == "VIP levels: Main - 19, Alt 1 - 15"


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
    assert rows[2][0].value == "Import: Private"
    assert rows[2][0].detail == "Inventory Visibility"
    assert rows[2][1].value == "Export: Private"
    assert rows[2][1].detail == "Export Visibility"


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


def test_inventory_card_rows_show_approved_data_categories() -> None:
    rows = _inventory_rows(_summary())

    assert [row[0].label for row in rows] == ["Resources", "Speedups", "Materials"]
    assert rows[0][0].value == "1.2B RSS"
    assert rows[1][0].value == "365d total"
    assert rows[2][0].value == "42 legendary"


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
