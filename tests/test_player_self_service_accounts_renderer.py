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


def test_account_summary_renderer_supports_all_three_sections() -> None:
    payload = _payload(9)
    for section in ("overview", "combat", "economy"):
        page = accounts_service.build_account_summary_page(payload, section=section, page=2)
        rendered = accounts_renderer.render_account_summary_card(page, display_name="Player")
        assert rendered.filename == "me_account_summary_42.png"
        with Image.open(BytesIO(rendered.image_bytes)) as image:
            assert image.size == (1702, 924)
