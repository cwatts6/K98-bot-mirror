from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from PIL import Image

from player_self_service.dashboard_card import (
    HEIGHT,
    WIDTH,
    _account_lines,
    _linked_display,
    _preference_lines,
    _reminder_lines,
    _status_label,
    render_dashboard_card,
)
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
            next_action="Review",
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
        ),
        exports=ExportStatus(
            stats_export="Excel / CSV",
            inventory_export="Excel / CSV",
            privacy_note="Private",
        ),
    )


def test_render_dashboard_card_outputs_png_with_expected_size() -> None:
    rendered = render_dashboard_card(
        _summary(),
        display_name="ãƒ… Laki à¹›",
        generated_at_utc=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
    )

    assert rendered.filename == "me_dashboard_42.png"
    assert rendered.image_bytes.getbuffer().nbytes > 8_000

    image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
    assert image.format == "PNG"
    assert image.size == (WIDTH, HEIGHT)


def test_dashboard_card_status_labels_are_semantic() -> None:
    assert _status_label("set") == "READY"
    assert _status_label("multiple") == "READY"
    assert _status_label("on") == "ON"
    assert _status_label("private") == "PRIVATE"
    assert _status_label("not subscribed") == "OFF"
    assert _status_label("unknown") == "CHECK"


def test_dashboard_card_linked_display_removes_duplicate_wording() -> None:
    assert _linked_display("0 linked") == "0"
    assert _linked_display("1 linked") == "1"
    assert _linked_display("multiple linked") == "multiple"
    assert _linked_display("unknown") == "unknown"


def test_dashboard_card_lines_are_mobile_embed_friendly() -> None:
    summary = _summary()

    assert _account_lines(summary) == (
        "Main: Main Gov (111)",
        "Linked: 1",
        "Accounts: 1",
    )
    assert _reminder_lines(summary) == (
        "KVK: all KVK events",
        "Calendar: not configured",
        "Times: 24h, 4h, 1h",
        "Lead times: not set",
    )
    assert _preference_lines(summary) == (
        "Inventory: private",
        "Exports: private",
    )
