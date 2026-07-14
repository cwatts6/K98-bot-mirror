"""Authorised portfolio assembly for the private Accounts command centre."""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime
import logging
from typing import Any

from inventory import reporting_service
from player_self_service import accounts_dal
from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
    AccountsScanRow,
    AccountSummaryPage,
    AccountSummarySection,
)
from services import governor_account_service

logger = logging.getLogger(__name__)

SUMMARY_ROWS_PER_PAGE = 8


def _positive_governor_id(value: Any) -> int | None:
    try:
        governor_id = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return governor_id if governor_id > 0 else None


def _registered_name(info: dict[str, Any]) -> str:
    return str(info.get("GovernorName") or info.get("governor_name") or "").strip() or "Unknown"


def _role(slot: str) -> str:
    lowered = slot.casefold()
    if lowered == "main":
        return "Main"
    if lowered.startswith("alt"):
        return "Alt"
    if lowered.startswith("farm"):
        return "Farm"
    return "Other"


def _same_scan(left: datetime | None, right: datetime | None) -> bool:
    if left is None or right is None:
        return False
    return left == right


def _metric(rows: tuple[AccountPortfolioRow, ...], field: str) -> AccountMetricTotal:
    seen: set[int] = set()
    values: list[int] = []
    for row in rows:
        if row.governor_id is None or row.governor_id in seen:
            continue
        seen.add(row.governor_id)
        value = getattr(row, field)
        if value is not None:
            values.append(int(value))
    return AccountMetricTotal(
        value=sum(values) if values else None,
        reporting_count=len(values),
        expected_count=len(rows),
    )


def _top_row(
    rows: tuple[AccountPortfolioRow, ...], field: str
) -> tuple[AccountPortfolioRow, int] | None:
    candidates = [
        (row, int(value))
        for row in rows
        if (value := getattr(row, field)) is not None and int(value) > 0
    ]
    if not candidates:
        return None
    # Python's stable max preserves canonical Main/slot order for ties.
    return max(candidates, key=lambda item: item[1])


def _insight(
    rows: tuple[AccountPortfolioRow, ...],
    *,
    power: AccountMetricTotal,
    t4_t5_kills: AccountMetricTotal,
    rss_total: AccountMetricTotal,
) -> str:
    count = len(rows)
    if not rows:
        return "Add a Main governor to begin building your account portfolio."

    if any(row.duplicate_governor_id for row in rows):
        return "Duplicate Governor IDs need review; portfolio totals count each ID once."
    problem_count = sum(row.data_state != "CURRENT" for row in rows)
    if problem_count:
        return (
            f"{problem_count} of {count} governors need scan review; "
            f"current RSS reports for {rss_total.reporting_count}/{rss_total.expected_count}."
        )
    if rss_total.reporting_count != rss_total.expected_count:
        return (
            f"Governor scans are current; current RSS reports for "
            f"{rss_total.reporting_count}/{rss_total.expected_count}."
        )

    mismatch = next(
        (
            row
            for row in rows
            if row.current_governor_name
            and row.registered_name.casefold() != row.current_governor_name.casefold()
        ),
        None,
    )
    if mismatch is not None:
        return (
            f"{mismatch.slot} now scans as {mismatch.current_governor_name}; "
            f"the registered name is {mismatch.registered_name}."
        )

    rss_leader = _top_row(rows, "rss_total")
    if rss_leader and rss_total.value and rss_total.reporting_count > 1:
        row, value = rss_leader
        share = round(value * 100 / rss_total.value)
        return f"{row.display_name} holds {share}% of current portfolio RSS."

    power_leader = _top_row(rows, "power")
    if power_leader and power.value and power.reporting_count > 1:
        row, value = power_leader
        share = round(value * 100 / power.value)
        return f"{row.display_name} contributes {share}% of portfolio power."
    kill_leader = _top_row(rows, "t4_t5_kills")
    if kill_leader and t4_t5_kills.value and t4_t5_kills.reporting_count > 1:
        row, value = kill_leader
        share = round(value * 100 / t4_t5_kills.value)
        return f"{row.display_name} contributes {share}% of portfolio T4+T5 kills."

    for field, label in (("rss_assistance", "RSS assistance"), ("helps", "helps")):
        leader = _top_row(rows, field)
        if leader:
            row, _value = leader
            return f"{row.display_name} leads the portfolio for {label}."
    return "All linked governors are on the latest Kingdom 1198 scan."


async def build_accounts_portfolio(discord_user_id: int) -> AccountsPortfolioPayload:
    """Build one immutable, all-linked-governor payload for rendering and CSV export."""
    user_id = int(discord_user_id)
    resolution = await governor_account_service.get_account_summary_for_user(user_id)
    entries: list[tuple[str, dict[str, Any], int | None]] = []
    for slot, raw in resolution.ordered_accounts.items():
        info = dict(raw or {})
        entries.append(
            (
                str(slot),
                info,
                _positive_governor_id(
                    info.get("GovernorID") or info.get("GovernorId") or info.get("governor_id")
                ),
            )
        )
    distinct_ids = tuple(dict.fromkeys(gid for _slot, _info, gid in entries if gid is not None))

    scan_failed = False
    inventory_failed = False
    scan_rows: tuple[AccountsScanRow, ...] = ()
    inventory_points: dict[int, Any] = {}
    if distinct_ids:
        scan_result, inventory_result = await asyncio.gather(
            asyncio.to_thread(accounts_dal.fetch_latest_accounts_scan_rows, distinct_ids),
            reporting_service.build_latest_resource_points_by_governor(distinct_ids),
            return_exceptions=True,
        )
        if isinstance(scan_result, asyncio.CancelledError):
            raise scan_result
        if isinstance(inventory_result, asyncio.CancelledError):
            raise inventory_result
        if isinstance(scan_result, BaseException):
            scan_failed = True
            logger.error(
                "accounts_portfolio_scan_read_failed user_id=%s",
                user_id,
                exc_info=(type(scan_result), scan_result, scan_result.__traceback__),
            )
        else:
            scan_rows = tuple(scan_result)
        if isinstance(inventory_result, BaseException):
            inventory_failed = True
            logger.error(
                "accounts_portfolio_inventory_read_failed user_id=%s",
                user_id,
                exc_info=(type(inventory_result), inventory_result, inventory_result.__traceback__),
            )
        else:
            inventory_points = dict(inventory_result)

    scan_by_id = {row.governor_id: row for row in scan_rows}
    counts = Counter(gid for _slot, _info, gid in entries if gid is not None)
    rows: list[AccountPortfolioRow] = []
    for slot, info, governor_id in entries:
        scan = scan_by_id.get(governor_id) if governor_id is not None else None
        inventory = inventory_points.get(governor_id) if governor_id is not None else None
        if governor_id is None or scan_failed:
            data_state = "UNRESOLVED"
        elif scan is None or scan.scan_date is None:
            data_state = "NO DATA"
        elif _same_scan(scan.scan_date, scan.latest_scan_date):
            data_state = "CURRENT"
        else:
            data_state = "STALE"
        rows.append(
            AccountPortfolioRow(
                slot=slot,
                role=_role(slot),
                registered_name=_registered_name(info),
                governor_id=governor_id,
                current_governor_name=scan.governor_name if scan else None,
                civilisation=scan.civilisation if scan else None,
                city_hall=scan.city_hall if scan else None,
                power=scan.power if scan else None,
                troop_power=scan.troop_power if scan else None,
                kill_points=scan.kill_points if scan else None,
                t4_kills=scan.t4_kills if scan else None,
                t5_kills=scan.t5_kills if scan else None,
                t4_t5_kills=scan.t4_t5_kills if scan else None,
                deads=scan.deads if scan else None,
                healed_troops=scan.healed_troops if scan else None,
                highest_acclaim=scan.highest_acclaim if scan else None,
                helps=scan.helps if scan else None,
                rss_gathered=scan.rss_gathered if scan else None,
                rss_assistance=scan.rss_assistance if scan else None,
                rss_total=int(inventory.total) if inventory is not None else None,
                conduct=scan.conduct if scan else None,
                location_x=scan.location_x if scan else None,
                location_y=scan.location_y if scan else None,
                data_state=data_state,
                last_governor_scan=scan.scan_date if scan else None,
                inventory_as_of=inventory.scan_utc if inventory is not None else None,
                duplicate_governor_id=governor_id is not None and counts[governor_id] > 1,
            )
        )
    row_tuple = tuple(rows)
    main_row = next((row for row in row_tuple if row.slot == "Main"), None)
    duplicate = any(row.duplicate_governor_id for row in row_tuple)
    all_current = bool(row_tuple) and all(row.data_state == "CURRENT" for row in row_tuple)
    if not resolution.ok:
        state = "REVIEW"
    elif not row_tuple or main_row is None:
        state = "SETUP"
    elif resolution.ok and not duplicate and all_current:
        state = "READY"
    else:
        state = "REVIEW"

    power = _metric(row_tuple, "power")
    troop_power = _metric(row_tuple, "troop_power")
    t4_t5_kills = _metric(row_tuple, "t4_t5_kills")
    rss_total = _metric(row_tuple, "rss_total")
    role_counts = Counter(row.role for row in row_tuple)
    warnings: list[str] = []
    if not resolution.ok:
        warnings.append("Registry data is temporarily unavailable.")
    if scan_failed:
        warnings.append("Governor scan data is temporarily unavailable.")
    if inventory_failed:
        warnings.append("Inventory coverage is temporarily unavailable.")

    latest_scan = next((row.latest_scan_date for row in scan_rows if row.latest_scan_date), None)
    insight = _insight(
        row_tuple,
        power=power,
        t4_t5_kills=t4_t5_kills,
        rss_total=rss_total,
    )
    if not resolution.ok:
        insight = "Account registry data is temporarily unavailable; try again before managing links."
    return AccountsPortfolioPayload(
        discord_user_id=user_id,
        state=state,
        rows=row_tuple,
        linked_count=len(row_tuple),
        main_row=main_row,
        role_counts=tuple((role, role_counts.get(role, 0)) for role in ("Main", "Alt", "Farm")),
        power=power,
        troop_power=troop_power,
        t4_t5_kills=t4_t5_kills,
        rss_total=rss_total,
        insight=insight,
        refreshed_at_utc=datetime.now(UTC),
        latest_scan_date=latest_scan,
        warnings=tuple(warnings),
    )


def build_account_summary_page(
    payload: AccountsPortfolioPayload,
    *,
    section: AccountSummarySection,
    page: int,
) -> AccountSummaryPage:
    page_count = max(1, (len(payload.rows) + SUMMARY_ROWS_PER_PAGE - 1) // SUMMARY_ROWS_PER_PAGE)
    selected_page = min(max(1, int(page)), page_count)
    start = (selected_page - 1) * SUMMARY_ROWS_PER_PAGE
    return AccountSummaryPage(
        payload=payload,
        section=section,
        page=selected_page,
        page_count=page_count,
        rows=payload.rows[start : start + SUMMARY_ROWS_PER_PAGE],
    )
