from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from PIL import Image

from player_self_service import accounts_renderer, accounts_service
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
)


def _payload(row_count: int = 10) -> AccountsPortfolioPayload:
    now = datetime(2026, 7, 14, 8, 30, tzinfo=UTC)
    rows = tuple(
        AccountPortfolioRow(
            slot="Main" if index == 0 else f"Farm {index}",
            role="Main" if index == 0 else "Farm",
            registered_name=f"Governor {index}",
            current_governor_name=f"Current Governor {index}",
            governor_id=100_000 + index,
            civilisation="Rome",
            city_hall=25,
            vip_level="VIP 18",
            power=1_000_000_000 + index,
            troop_power=500_000_000,
            kill_points=2_000_000,
            t4_kills=300_000,
            t5_kills=200_000,
            t4_t5_kills=500_000,
            deads=50_000,
            healed_troops=75_000,
            highest_acclaim=1_500,
            helps=10_000,
            rss_gathered=3_000_000,
            rss_assistance=2_000_000,
            rss_total=4_000_000,
            conduct=98.5,
            location_x=123,
            location_y=456,
            data_state="CURRENT",
            last_governor_scan=now,
            inventory_as_of=now,
        )
        for index in range(row_count)
    )
    metric = AccountMetricTotal(10_000_000, row_count, row_count)
    return AccountsPortfolioPayload(
        discord_user_id=42,
        state="READY",
        rows=rows,
        linked_count=row_count,
        main_row=rows[0],
        role_counts=(("Main", 1), ("Alt", 0), ("Farm", row_count - 1)),
        power=metric,
        troop_power=metric,
        t4_t5_kills=metric,
        rss_total=metric,
        insight="All linked governors are on the latest Kingdom 1198 scan.",
        refreshed_at_utc=now,
        latest_scan_date=now,
    )


def test_main_accounts_renderer_uses_locked_dimensions_and_stable_filename() -> None:
    rendered = accounts_renderer.render_accounts_card(_payload(), display_name="Tést Player")

    assert rendered.filename == "me_accounts_42.png"
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.size == (1702, 924)
        assert image.mode == "RGB"


def test_main_accounts_renderer_draws_avatar_and_deduplicates_kingdom_suffix() -> None:
    avatar = BytesIO()
    Image.new("RGB", (256, 256), (220, 20, 60)).save(avatar, format="PNG")

    rendered = accounts_renderer.render_accounts_card(
        _payload(),
        display_name="Test Player (1198)",
        avatar_bytes=avatar.getvalue(),
    )

    assert accounts_renderer._discord_heading("Test Player (1198)") == "Test Player (1198)"
    assert accounts_renderer._discord_heading("Test Player") == "Test Player (1198)"
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        red, green, blue = image.getpixel((109, 83))
        assert red > 180
        assert green < 60
        assert blue < 90


def test_governor_count_label_uses_singular_and_plural_grammar() -> None:
    assert accounts_renderer.format_governor_count(0) == "0 governors"
    assert accounts_renderer.format_governor_count(1) == "1 governor"
    assert accounts_renderer.format_governor_count(2) == "2 governors"


def test_linked_governor_tiles_preserve_order_and_overflow_contract() -> None:
    entries = accounts_renderer._linked_governor_entries(_payload(10))

    assert len(entries) == 8
    assert entries[0][:2] == ("Main", "Current Governor 0")
    assert entries[1][:2] == ("Farm 1", "Current Governor 1")
    assert entries[-1] == ("", "+ 3 more — open Account Summary", "", "", "")


def test_account_summary_renderer_supports_all_three_sections() -> None:
    payload = _payload(9)
    for section in ("overview", "combat", "economy"):
        page = accounts_service.build_account_summary_page(payload, section=section, page=2)
        rendered = accounts_renderer.render_account_summary_card(page, display_name="Player")
        assert rendered.filename == "me_account_summary_42.png"
        with Image.open(BytesIO(rendered.image_bytes)) as image:
            assert image.size == (1702, 924)


def test_summary_columns_and_values_follow_smoke_contract() -> None:
    payload = _payload(1)
    row = payload.rows[0]

    overview = accounts_service.build_account_summary_page(payload, section="overview", page=1)
    overview_labels = [label for label, _width in accounts_renderer._summary_columns(overview)]
    overview_values = accounts_renderer._summary_values(overview, row)
    assert "GOVERNOR ID" not in overview_labels
    assert "DATA" not in overview_labels
    assert "VIP" in overview_labels
    assert "VIP 18" in overview_values
    assert "1B" in overview_values
    assert "500M" in overview_values
    assert "14 Jul 2026 08:30 UTC" in overview_values

    combat = accounts_service.build_account_summary_page(payload, section="combat", page=1)
    combat_labels = [label for label, _width in accounts_renderer._summary_columns(combat)]
    combat_values = accounts_renderer._summary_values(combat, row)
    assert "HELPS" not in combat_labels
    assert "KP LOSS" in combat_labels
    assert "TANKING" in combat_labels
    assert "CONDUCT" not in combat_labels
    assert "1.5M" in combat_values
    assert combat_values[-1] == "129%"
    assert accounts_renderer._summary_section_label("combat") == "COMBAT"
    assert accounts_renderer._summary_footer_label("combat") == (
        "Combat all linked governors (Tanking: Higher = Better)"
    )

    economy = accounts_service.build_account_summary_page(payload, section="economy", page=1)
    economy_labels = [label for label, _width in accounts_renderer._summary_columns(economy)]
    economy_values = accounts_renderer._summary_values(economy, row)
    assert "HELPS" in economy_labels
    assert "CONDUCT" in economy_labels
    assert "DATA" not in economy_labels
    assert "10K" in economy_values
    assert "99" in economy_values
    assert accounts_renderer._compact_detail(8_515_574_404) == "8.52B"
