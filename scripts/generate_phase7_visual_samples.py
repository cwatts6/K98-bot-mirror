# pyright: reportMissingImports=false
"""Generate deterministic Phase 7 /me visual samples without Discord, SQL, or network I/O."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw

from inventory.models import (
    InventoryMaterialPoint,
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
    InventoryResourcePoint,
    InventorySpeedupPoint,
)
from inventory.report_image_renderer import render_inventory_reports
from player_self_service import accounts_renderer, accounts_service
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
)
from player_self_service.governor_dashboard_models import (
    GovernorDashboardAccessDecision,
    GovernorDashboardActivityHonours,
    GovernorDashboardContext,
    GovernorDashboardFreshness,
    GovernorDashboardHistoricalHighlights,
    GovernorDashboardIdentity,
    GovernorDashboardInventoryHighlights,
    GovernorDashboardLatestMetrics,
    GovernorDashboardPayload,
    GovernorDashboardProfileStatus,
    GovernorDashboardSelfView,
)
from player_self_service.governor_dashboard_renderer import render_governor_dashboard
from player_self_service.preferences_renderer import render_preferences_card
from player_self_service.preferences_summary import (
    PreferencesSummaryPayload,
    PreferenceValueSummary,
    RegionalProfileSummary,
    TimeReferenceSummary,
)
from player_self_service.reminders_renderer import render_reminders_card
from player_self_service.reminders_summary import (
    CalendarEventCatalog,
    build_reminders_summary_payload,
)
from player_self_service.stats_models import (
    PersonalStatsMetrics,
    PersonalStatsPayload,
    StatsCoverage,
    StatsDailyPoint,
    StatsGovernorOption,
    StatsMetricSummary,
    StatsMode,
    StatsPeriod,
    StatsResultState,
    StatsScopeType,
    StatsWindow,
)
from player_self_service.stats_renderer import render_personal_stats_card

NOW = datetime(2026, 7, 18, 14, 5, tzinfo=UTC)
SCENARIOS = (
    "full",
    "sparse",
    "no_data",
    "unavailable",
    "long_latin",
    "cjk",
    "emoji",
    "avatar_absent",
    "maximum",
    "zero",
    "long_support",
)
NAMES = {
    "full": "Invoking Player",
    "sparse": "P",
    "no_data": "No Data Player",
    "unavailable": "Unavailable Player",
    "long_latin": "Alexandria-Montgomery-Winterbourne the Third of Kingdom Ninety-Eight",
    "cjk": "義Vìper義 長い表示名 王國一一九八",
    "emoji": "Fox🦊 👩🏽‍🚀🏳️‍🌈",
    "avatar_absent": "Avatar Fallback",
    "maximum": "Maximum Values",
    "zero": "Zero Values",
    "long_support": "Supporting Copy Stress",
}


def _avatar() -> bytes:
    image = Image.new("RGB", (256, 256), (16, 35, 70))
    draw = ImageDraw.Draw(image)
    draw.ellipse((18, 18, 238, 238), fill=(91, 190, 255), outline=(255, 206, 92), width=10)
    draw.ellipse((82, 54, 174, 146), fill=(248, 251, 255))
    draw.rounded_rectangle((58, 142, 198, 232), radius=38, fill=(248, 251, 255))
    stream = BytesIO()
    image.save(stream, format="PNG")
    image.close()
    return stream.getvalue()


def _value(scenario: str, normal: int) -> int | None:
    if scenario in {"sparse", "no_data", "unavailable"}:
        return None
    if scenario == "zero":
        return 0
    if scenario == "maximum":
        return 987_654_321_098
    return normal


def _dashboard_payload(scenario: str) -> GovernorDashboardPayload:
    name = NAMES[scenario]
    context = GovernorDashboardContext(
        viewer_discord_id=42,
        viewer_mode="self",
        selected_governor_id=123456789,
        selected_governor_name=name,
        is_linked_to_viewer=True,
        account_type_for_self_view="Main",
        access_decision=GovernorDashboardAccessDecision(True, "linked"),
        privacy_profile="self_view",
    )
    value = lambda normal: _value(scenario, normal)
    return GovernorDashboardPayload(
        context=context,
        identity=GovernorDashboardIdentity(
            name, 123456789, "KD98", "France", 321 if scenario != "sparse" else None, 654
        ),
        latest_metrics=GovernorDashboardLatestMetrics(
            value(123_850_000),
            value(8_520_000_000),
            value(26_220_000),
            value(189_260),
            value(357_160_000),
        ),
        historical_highlights=GovernorDashboardHistoricalHighlights(
            value(10_010_000), value(3), value(11)
        ),
        activity_honours=GovernorDashboardActivityHonours(
            value(75),
            value(28),
            0.3733 if scenario not in {"sparse", "no_data", "unavailable"} else None,
            "37.33%" if scenario not in {"sparse", "no_data", "unavailable"} else "N/A",
        ),
        profile_status=GovernorDashboardProfileStatus(value(100)),
        freshness=GovernorDashboardFreshness(None if scenario == "unavailable" else NOW),
        inventory=GovernorDashboardInventoryHighlights(
            value(100_700_000_000), value(4_372), value(177)
        ),
        available_actions=("accounts",),
        missing_fields=(),
        self_view=GovernorDashboardSelfView("Main", "VIP 19"),
    )


def _accounts_payload(scenario: str) -> AccountsPortfolioPayload:
    count = 0 if scenario in {"no_data", "unavailable"} else 1 if scenario == "sparse" else 9
    rows = tuple(
        AccountPortfolioRow(
            slot="Main" if index == 0 else f"Farm {index}",
            role="Main" if index == 0 else "Farm",
            registered_name=NAMES[scenario],
            current_governor_name=f"{NAMES[scenario]} {index}",
            governor_id=100_000 + index,
            civilisation="Rome",
            city_hall=_value(scenario, 25),
            vip_level="VIP 18",
            power=_value(scenario, 1_000_000_000 + index),
            troop_power=_value(scenario, 500_000_000),
            kill_points=_value(scenario, 2_000_000),
            t4_kills=_value(scenario, 300_000),
            t5_kills=_value(scenario, 200_000),
            t4_t5_kills=_value(scenario, 500_000),
            deads=_value(scenario, 50_000),
            healed_troops=_value(scenario, 75_000),
            highest_acclaim=_value(scenario, 1_500),
            helps=_value(scenario, 10_000),
            rss_gathered=_value(scenario, 3_000_000),
            rss_assistance=_value(scenario, 2_000_000),
            rss_total=_value(scenario, 4_000_000),
            conduct=98.5,
            location_x=123,
            location_y=456,
            data_state="STALE" if scenario == "sparse" else "CURRENT",
            last_governor_scan=NOW,
            inventory_as_of=NOW,
        )
        for index in range(count)
    )
    metric_value = sum((row.power or 0) for row in rows) if rows else None
    metric = AccountMetricTotal(metric_value, len(rows), max(1, len(rows)))
    state = "SETUP" if not rows else "REVIEW" if scenario == "sparse" else "READY"
    insight = (
        "This deliberately long supporting sentence verifies that insight copy remains readable "
        "without forcing tiny text or crossing the approved panel boundary."
        if scenario == "long_support"
        else "All linked governors are on the latest approved scan."
    )
    return AccountsPortfolioPayload(
        discord_user_id=42,
        state=state,
        rows=rows,
        linked_count=len(rows),
        main_row=rows[0] if rows else None,
        role_counts=(("Main", 1), ("Farm", max(0, len(rows) - 1))) if rows else (),
        power=metric,
        troop_power=metric,
        t4_t5_kills=metric,
        rss_total=metric,
        insight=insight,
        refreshed_at_utc=NOW,
        latest_scan_date=NOW if rows else None,
    )


def _preferences_payload(scenario: str) -> PreferencesSummaryPayload:
    available = scenario not in {"sparse", "no_data", "unavailable"}
    mode = "UTC" if scenario in {"sparse", "unavailable"} else "LOCAL"
    missing = PreferenceValueSummary(False, False, "Not recorded", None, None)
    regional = RegionalProfileSummary(
        timezone=(
            PreferenceValueSummary(True, True, "United Kingdom", "Europe/London", "Europe/London")
            if available
            else missing
        ),
        location=(
            PreferenceValueSummary(True, True, "United Kingdom (GB)", "GB", "GB")
            if available
            else missing
        ),
        preferred_language=(
            PreferenceValueSummary(True, True, "English (en-GB)", "en-GB", "en-GB")
            if available
            else missing
        ),
    )
    return PreferencesSummaryPayload(
        discord_user_id=42,
        display_name=NAMES[scenario],
        kingdom_id=1198,
        generated_at_utc=NOW,
        regional_profile=regional,
        time_reference=TimeReferenceSummary(
            mode=mode,
            heading="LOCAL TIME REFERENCE" if mode == "LOCAL" else "UTC REFERENCE",
            display_time="15:05" if mode == "LOCAL" else "14:05",
            timezone_label="United Kingdom" if mode == "LOCAL" else None,
            utc_offset_label="UTC+1" if mode == "LOCAL" else "UTC",
            supporting_line=(
                "United Kingdom • UTC+1"
                if mode == "LOCAL"
                else "Set a timezone to show local time."
            ),
            regional_context="United Kingdom (GB) • English (en-GB)",
        ),
        profile_details_set=3 if available else 0,
        profile_details_total=3,
        profile_supporting_text=(
            "3 of 3 profile details set" if available else "0 of 3 profile details set"
        ),
        settings_insight=(
            "This deliberately long supporting sentence verifies Regional Profile text fitting at Discord desktop and mobile scales."
            if scenario == "long_support"
            else (
                "All three regional profile details are available."
                if available
                else "Regional profile details are not recorded."
            )
        ),
    )


def _reminders_payload(scenario: str):
    enabled = scenario not in {"no_data", "unavailable"}
    return build_reminders_summary_payload(
        viewer_discord_id=42,
        display_name=NAMES[scenario],
        kvk_config=(
            {"subscriptions": ["ruins", "altars"], "reminder_times": ["24h", "1h"]}
            if enabled
            else None
        ),
        calendar_prefs={"enabled": enabled, "by_event_type": {"ark": ["24h"]} if enabled else {}},
        calendar_catalog=CalendarEventCatalog(
            available=scenario != "unavailable", event_types=("ark",) if enabled else ()
        ),
        generated_at_utc=NOW,
    )


def _stats_payload(scenario: str) -> PersonalStatsPayload:
    state = {
        "sparse": StatsResultState.PARTIAL,
        "no_data": StatsResultState.NO_DATA,
        "unavailable": StatsResultState.UNAVAILABLE,
    }.get(scenario, StatsResultState.READY)
    total = _value(scenario, 75)
    daily = (
        ()
        if total is None
        else (StatsDailyPoint(date(2026, 7, 17), total), StatsDailyPoint(date(2026, 7, 18), -total))
    )
    metric = StatsMetricSummary(
        total=total, reporting_days=len(daily), expected_days=2, daily=daily
    )
    metrics = PersonalStatsMetrics(
        **{
            name: metric
            for name in PersonalStatsMetrics.__dataclass_fields__
            if name not in {"period_end_power", "period_end_troop_power", "period_end_date"}
        },
        period_end_power=_value(scenario, 123_456_789),
        period_end_troop_power=_value(scenario, 98_765_432),
        period_end_date=date(2026, 7, 18),
    )
    return PersonalStatsPayload(
        discord_user_id=42,
        period=StatsPeriod.THIS_WEEK,
        window=StatsWindow(date(2026, 7, 14), date(2026, 7, 18)),
        stats_anchor_date=date(2026, 7, 18),
        scope_type=StatsScopeType.SELECTED,
        scope_governor_ids=(111,),
        scope_label=NAMES[scenario],
        governor_options=(StatsGovernorOption(111, NAMES[scenario], "Main", True),),
        duplicate_id_warning=False,
        registry_fingerprint=(("Main", 111),),
        coverage=StatsCoverage(5, 1, 5, 5, 5, 5, 5, 5),
        state=state,
        metrics=metrics,
        data_refreshed_at_utc=NOW - timedelta(minutes=5),
        generated_at_utc=NOW,
    )


def _inventory_payload(scenario: str, view: InventoryReportView) -> InventoryReportPayload:
    empty = scenario in {"no_data", "unavailable"}
    count = 1 if scenario == "sparse" else 2
    value = int(_value(scenario, 1_000_000_000) or 0)
    dates = tuple(NOW - timedelta(days=7 * (count - index - 1)) for index in range(count))
    resources = (
        tuple(
            InventoryResourcePoint(
                stamp, value + index * 100_000_000, value * 2, value * 3, value * 4
            )
            for index, stamp in enumerate(dates)
        )
        if view == InventoryReportView.RESOURCES and not empty
        else ()
    )
    speedups = (
        tuple(
            InventorySpeedupPoint(stamp, 1, 2, 20 + index, 30 + index, 10 + index)
            for index, stamp in enumerate(dates)
        )
        if view == InventoryReportView.SPEEDUPS and not empty
        else ()
    )
    materials = (
        tuple(
            InventoryMaterialPoint(
                stamp, 10 + index, 20 + index, 30 + index, 40 + index, 50 + index
            )
            for index, stamp in enumerate(dates)
        )
        if view == InventoryReportView.MATERIALS and not empty
        else ()
    )
    return InventoryReportPayload(
        111,
        NAMES[scenario],
        view,
        InventoryReportRange.ONE_MONTH,
        resources=resources,
        speedups=speedups,
        materials=materials,
        generated_at_utc=NOW,
    )


def _render_scenario(scenario: str) -> list[tuple[str, bytes]]:
    avatar = None if scenario == "avatar_absent" else _avatar()
    cards: list[tuple[str, bytes]] = []
    dashboard = render_governor_dashboard(_dashboard_payload(scenario), avatar_bytes=avatar)
    cards.append(("dashboard", dashboard.image_bytes))
    accounts_payload = _accounts_payload(scenario)
    accounts = accounts_renderer.render_accounts_card(
        accounts_payload, display_name=NAMES[scenario], avatar_bytes=avatar
    )
    cards.append(("accounts", accounts.image_bytes))
    for section in ("overview", "combat", "economy"):
        page = accounts_service.build_account_summary_page(
            accounts_payload, section=section, page=1
        )
        card = accounts_renderer.render_account_summary_card(
            page, display_name=NAMES[scenario], avatar_bytes=avatar
        )
        cards.append((f"account-summary-{section}", card.image_bytes))
    reminders = render_reminders_card(_reminders_payload(scenario), avatar_bytes=avatar)
    try:
        cards.append(("reminders", reminders.image_bytes.getvalue()))
    finally:
        reminders.image_bytes.close()
    preferences = render_preferences_card(_preferences_payload(scenario), avatar_bytes=avatar)
    cards.append(("preferences", preferences.image_bytes))
    stats_payload = _stats_payload(scenario)
    for mode in StatsMode:
        card = render_personal_stats_card(
            stats_payload, mode=mode, display_name=NAMES[scenario], avatar_bytes=avatar
        )
        cards.append((f"stats-{mode.value}", card.image_bytes))
    for view in InventoryReportView:
        rendered = render_inventory_reports(
            _inventory_payload(scenario, view), avatar_bytes=avatar
        )[0]
        try:
            cards.append((f"inventory-{view.value}", rendered.image_bytes.getvalue()))
        finally:
            rendered.image_bytes.close()
    return cards


def _save_variants(output: Path, scenario: str, cards: list[tuple[str, bytes]]) -> None:
    previews: dict[str, list[tuple[str, Image.Image]]] = {
        "original": [],
        "desktop": [],
        "mobile": [],
    }
    for label, raw in cards:
        with Image.open(BytesIO(raw)) as source:
            image = source.convert("RGB")
        target_dir = output / scenario / label
        target_dir.mkdir(parents=True, exist_ok=True)
        for scale, width in (("original", image.width), ("desktop", 960), ("mobile", 430)):
            height = round(width * image.height / image.width)
            preview = (
                image
                if width == image.width
                else image.resize((width, height), Image.Resampling.LANCZOS)
            )
            preview.save(target_dir / f"{scale}.png", format="PNG", optimize=True)
            sheet_preview = preview.copy()
            previews[scale].append((label, sheet_preview))
            if preview is not image:
                preview.close()
        image.close()

    for scale, images in previews.items():
        thumb_width = 420
        thumb_height = 285
        columns = 3
        rows = (len(images) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + 34)), (4, 11, 24))
        draw = ImageDraw.Draw(sheet)
        for index, (label, image) in enumerate(images):
            image.thumbnail((thumb_width - 12, thumb_height - 12), Image.Resampling.LANCZOS)
            x = (index % columns) * thumb_width + 6
            y = (index // columns) * (thumb_height + 34) + 28
            sheet.paste(image, (x, y))
            draw.text((x, y - 22), label, fill=(248, 251, 255))
            image.close()
        sheet.save(output / f"contact-sheet-{scenario}-{scale}.jpg", quality=88)
        sheet.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=("all", *SCENARIOS), default="all")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    selected = SCENARIOS if args.scenario == "all" else (args.scenario,)
    for scenario in selected:
        _save_variants(args.output, scenario, _render_scenario(scenario))
    print(f"Generated {len(selected) * 13} source renders in {args.output}")


if __name__ == "__main__":
    main()
