"""Complete private Account Summary CSV export from an authorised portfolio payload."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from typing import Any

from player_self_service.accounts_models import AccountPortfolioRow, AccountsPortfolioPayload

CSV_COLUMNS = (
    "Slot",
    "Role",
    "Registered Name",
    "Current Governor Name",
    "Governor ID",
    "Civilisation",
    "City Hall",
    "Power",
    "Troop Power",
    "Kill Points",
    "T4 Kills",
    "T5 Kills",
    "T4+T5 Kills",
    "Deads",
    "Healed Troops",
    "Highest Acclaim",
    "Helps",
    "RSS Gathered",
    "RSS Assistance",
    "RSS Total",
    "Conduct",
    "Location X",
    "Location Y",
    "Data State",
    "Last Governor Scan",
    "Inventory As Of",
)


@dataclass(frozen=True, slots=True)
class AccountsCsvExport:
    filename: str
    data: bytes


def _safe_text(value: Any) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _date(value: datetime | None) -> str:
    if value is None:
        return ""
    stamp = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return stamp.isoformat(timespec="seconds")


def _row_values(row: AccountPortfolioRow) -> tuple[Any, ...]:
    return (
        _safe_text(row.slot),
        _safe_text(row.role),
        _safe_text(row.registered_name),
        _safe_text(row.current_governor_name),
        row.governor_id if row.governor_id is not None else "",
        _safe_text(row.civilisation),
        row.city_hall if row.city_hall is not None else "",
        row.power if row.power is not None else "",
        row.troop_power if row.troop_power is not None else "",
        row.kill_points if row.kill_points is not None else "",
        row.t4_kills if row.t4_kills is not None else "",
        row.t5_kills if row.t5_kills is not None else "",
        row.t4_t5_kills if row.t4_t5_kills is not None else "",
        row.deads if row.deads is not None else "",
        row.healed_troops if row.healed_troops is not None else "",
        row.highest_acclaim if row.highest_acclaim is not None else "",
        row.helps if row.helps is not None else "",
        row.rss_gathered if row.rss_gathered is not None else "",
        row.rss_assistance if row.rss_assistance is not None else "",
        row.rss_total if row.rss_total is not None else "",
        row.conduct if row.conduct is not None else "",
        row.location_x if row.location_x is not None else "",
        row.location_y if row.location_y is not None else "",
        _safe_text(row.data_state),
        _date(row.last_governor_scan),
        _date(row.inventory_as_of),
    )


def build_accounts_csv(payload: AccountsPortfolioPayload) -> AccountsCsvExport:
    stream = StringIO(newline="")
    try:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for row in payload.rows:
            writer.writerow(_row_values(row))
        data = stream.getvalue().encode("utf-8-sig")
    finally:
        stream.close()
    timestamp = payload.refreshed_at_utc.astimezone(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"me_account_summary_{int(payload.discord_user_id)}_{timestamp}.csv"
    return AccountsCsvExport(filename=filename, data=data)
