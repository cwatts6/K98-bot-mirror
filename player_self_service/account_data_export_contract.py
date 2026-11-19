"""Typed contracts and pure helpers for private Account Data downloads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from numbers import Number
from pathlib import Path
from typing import Any

import pandas as pd

from player_self_service.accounts_models import AccountsPortfolioPayload


class AccountDataOutputKind(StrEnum):
    FULL_WORKBOOK = "full_workbook"
    CURRENT_SNAPSHOT = "current_snapshot"
    RAW_HISTORY = "raw_history"


ALLOWED_HISTORY_DAYS = (30, 60, 90, 180, 360)
DEFAULT_HISTORY_DAYS = 90


@dataclass(frozen=True, slots=True)
class AuthorisedAccountDataContext:
    discord_user_id: int
    display_name: str
    portfolio: AccountsPortfolioPayload
    governor_ids: tuple[int, ...]
    generated_at_utc: datetime


@dataclass(frozen=True, slots=True)
class HistoryWindowResult:
    frame: pd.DataFrame
    requested_days: int
    window_start: date | None
    window_end: date | None
    written_start: date | None
    written_end: date | None
    invalid_date_rows: int

    @property
    def row_count(self) -> int:
        return int(len(self.frame.index))


@dataclass(frozen=True, slots=True)
class AccountDataExportMetadata:
    output_kind: AccountDataOutputKind
    generated_at_utc: datetime
    authorised_governor_count: int
    snapshot_row_count: int | None
    history_row_count: int | None
    requested_days: int | None
    window_start: date | None
    window_end: date | None
    written_start: date | None
    written_end: date | None
    stats_freshness: date | None
    governor_scan_freshness: datetime | None
    inventory_oldest: datetime | None
    inventory_latest: datetime | None
    inventory_reporting_count: int | None
    inventory_expected_count: int | None


@dataclass(frozen=True, slots=True)
class AccountDataExportFile:
    file_path: Path
    temp_dir: Path
    filename: str
    metadata: AccountDataExportMetadata


@dataclass(frozen=True, slots=True)
class AccountDataExportOutcome:
    status: str
    message: str | None = None
    export_file: AccountDataExportFile | None = None


def validate_output_kind(value: AccountDataOutputKind | str) -> AccountDataOutputKind:
    if isinstance(value, AccountDataOutputKind):
        return value
    try:
        return AccountDataOutputKind(str(value).strip())
    except ValueError as exc:
        raise ValueError("Unsupported Account Data output kind.") from exc


def validate_history_days(output_kind: AccountDataOutputKind, value: int | None) -> int | None:
    if output_kind is AccountDataOutputKind.CURRENT_SNAPSHOT:
        return None
    days = DEFAULT_HISTORY_DAYS if value is None else int(value)
    if days not in ALLOWED_HISTORY_DAYS:
        choices = ", ".join(str(item) for item in ALLOWED_HISTORY_DAYS)
        raise ValueError(f"History days must be one of: {choices}.")
    return days


def filter_history_window(frame: pd.DataFrame, days: int) -> HistoryWindowResult:
    """Return one exact inclusive window anchored to the latest valid source date."""
    if days not in ALLOWED_HISTORY_DAYS:
        raise ValueError("Unsupported history window.")
    if "AsOfDate" not in frame.columns:
        raise ValueError("Stats history is missing AsOfDate.")
    if "GovernorID" not in frame.columns:
        raise ValueError("Stats history is missing GovernorID.")

    working = frame.copy(deep=True)
    parsed = pd.to_datetime(working["AsOfDate"], errors="coerce")
    invalid_count = int(parsed.isna().sum())
    working = working.loc[parsed.notna()].copy()
    working["AsOfDate"] = parsed.loc[parsed.notna()].dt.normalize()

    if working.empty:
        return HistoryWindowResult(
            frame=working,
            requested_days=days,
            window_start=None,
            window_end=None,
            written_start=None,
            written_end=None,
            invalid_date_rows=invalid_count,
        )

    governor_ids = pd.to_numeric(working["GovernorID"], errors="coerce")
    if governor_ids.isna().any() or (governor_ids <= 0).any():
        raise ValueError("Stats history contains an invalid GovernorID.")
    working["GovernorID"] = governor_ids.astype("int64")

    duplicate_mask = working.duplicated(subset=["GovernorID", "AsOfDate"], keep=False)
    if duplicate_mask.any():
        raise ValueError("Stats history contains duplicate GovernorID/source-date rows.")

    latest_timestamp = pd.Timestamp(working["AsOfDate"].max()).normalize()
    start_timestamp = latest_timestamp - pd.Timedelta(days=days - 1)
    filtered = working.loc[
        working["AsOfDate"].between(start_timestamp, latest_timestamp, inclusive="both")
    ].copy()
    filtered = filtered.sort_values(
        ["GovernorID", "AsOfDate"], ascending=[True, False], kind="mergesort"
    ).reset_index(drop=True)

    written_start = pd.Timestamp(filtered["AsOfDate"].min()).date() if not filtered.empty else None
    written_end = pd.Timestamp(filtered["AsOfDate"].max()).date() if not filtered.empty else None
    return HistoryWindowResult(
        frame=filtered,
        requested_days=days,
        window_start=start_timestamp.date(),
        window_end=latest_timestamp.date(),
        written_start=written_start,
        written_end=written_end,
        invalid_date_rows=invalid_count,
    )


def spreadsheet_safe_text(value: Any) -> Any:
    """Protect spreadsheet text without converting numeric values to text."""
    if isinstance(value, Number) and not isinstance(value, bool):
        return value
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def safe_filename_part(value: str, *, fallback: str = "user", max_length: int = 80) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    cleaned = cleaned.strip("_")[:max_length]
    return cleaned or fallback


def ensure_child_path(parent: Path, child: Path) -> Path:
    resolved_parent = parent.resolve()
    resolved_child = child.resolve()
    if resolved_child.parent != resolved_parent:
        raise ValueError("Export path escaped its temporary directory.")
    return resolved_child


def normalise_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
