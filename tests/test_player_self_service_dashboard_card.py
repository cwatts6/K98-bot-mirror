from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from PIL import Image

from player_self_service.dashboard_card import HEIGHT, WIDTH, render_dashboard_card
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
            stats_export="stats export available",
            inventory_export="inventory export available for approved records",
            privacy_note="file exports are delivered privately",
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
