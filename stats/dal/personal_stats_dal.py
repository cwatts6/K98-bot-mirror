"""Set-based read-only SQL access for private personal period performance."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from file_utils import get_conn_with_retries
from player_self_service.stats_models import (
    PersonalStatsDailyRow,
    PersonalStatsDataSet,
    PersonalStatsHeader,
)

_MAX_GOVERNORS = 26
_QUERY_TIMEOUT_SECONDS = 9
_VALUE_ROWS = ", ".join("(?)" for _ in range(_MAX_GOVERNORS))
PERSONAL_STATS_SQL = f"""
SET NOCOUNT ON;

DECLARE @GovernorIDs dbo.IntList;
INSERT INTO @GovernorIDs (ID)
SELECT DISTINCT GovernorID
FROM (VALUES {_VALUE_ROWS}) AS Requested(GovernorID)
WHERE GovernorID IS NOT NULL;

EXEC dbo.usp_GetPersonalStatsDaily
    @GovernorIDs = @GovernorIDs,
    @HistoryDays = ?;
"""


def _to_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(Decimal(str(value).strip()))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _to_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    return value if isinstance(value, date) else None


def _to_utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _rows_to_dicts(cursor: Any) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    columns = [str(item[0]) for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def _next_rows(cursor: Any, *, advance: bool, missing_message: str) -> list[dict[str, Any]]:
    """Return the next row-bearing result set, skipping statement-count results."""
    if advance and not cursor.nextset():
        raise ValueError(missing_message)
    while cursor.description is None:
        if not cursor.nextset():
            raise ValueError(missing_message)
    return _rows_to_dicts(cursor)


def _map_header(row: dict[str, Any], *, expected_count: int) -> PersonalStatsHeader:
    count = _to_int(row.get("RequestedGovernorCount"))
    if count != expected_count:
        raise ValueError("Personal stats SQL returned a mismatched governor count")
    anchor = _to_date(row.get("StatsAnchorDate"))
    source_refreshed_at = _to_utc_datetime(row.get("StatsSourceRefreshedAtUtc"))
    if (anchor is None) != (source_refreshed_at is None):
        raise ValueError("Personal stats SQL returned an invalid source refresh timestamp")
    if anchor is not None and source_refreshed_at is not None:
        if source_refreshed_at.date() != anchor:
            raise ValueError("Personal stats SQL returned a source refresh outside its anchor date")
    return PersonalStatsHeader(
        stats_anchor_date=anchor,
        stats_source_refreshed_at_utc=source_refreshed_at,
        window_start_date=_to_date(row.get("WindowStartDate")),
        window_end_date=_to_date(row.get("WindowEndDate")),
        requested_governor_count=count,
    )


def _map_daily_row(row: dict[str, Any], *, allowed_ids: frozenset[int]) -> PersonalStatsDailyRow:
    governor_id = _to_int(row.get("GovernorID"))
    as_of_date = _to_date(row.get("AsOfDate"))
    if governor_id is None or governor_id not in allowed_ids or as_of_date is None:
        raise ValueError("Personal stats SQL returned an invalid source row identity")
    return PersonalStatsDailyRow(
        governor_id=governor_id,
        as_of_date=as_of_date,
        has_stats=bool(row.get("HasStats")),
        previous_stats_date=_to_date(row.get("PreviousStatsDate")),
        power_value=_to_int(row.get("PowerValue")),
        troop_power_value=_to_int(row.get("TroopPowerValue")),
        power_delta=_to_int(row.get("PowerDelta")),
        troop_power_delta=_to_int(row.get("TroopPowerDelta")),
        kill_points_delta=_to_int(row.get("KillPointsDelta")),
        rss_gathered_delta=_to_int(row.get("RSSGatheredDelta")),
        rss_assist_delta=_to_int(row.get("RSSAssistDelta")),
        helps_delta=_to_int(row.get("HelpsDelta")),
        t4_kills_delta=_to_int(row.get("T4KillsDelta")),
        t5_kills_delta=_to_int(row.get("T5KillsDelta")),
        deads_delta=_to_int(row.get("DeadsDelta")),
        healed_troops_delta=_to_int(row.get("HealedTroopsDelta")),
        has_alliance_activity=bool(row.get("HasAllianceActivity")),
        previous_activity_date=_to_date(row.get("PreviousActivityDate")),
        build_activity_delta=_to_int(row.get("BuildActivityDelta")),
        tech_donations_delta=_to_int(row.get("TechDonationsDelta")),
        has_forts=bool(row.get("HasForts")),
        forts_total=_to_int(row.get("FortsTotal")),
        forts_launched=_to_int(row.get("FortsLaunched")),
        forts_joined=_to_int(row.get("FortsJoined")),
    )


def fetch_personal_stats_daily(
    governor_ids: Iterable[int],
    *,
    history_days: int = 180,
) -> PersonalStatsDataSet:
    """Load one bounded daily dataset for at most 26 distinct Governor IDs."""
    ids = tuple(dict.fromkeys(int(value) for value in governor_ids if int(value) > 0))
    if not 1 <= len(ids) <= _MAX_GOVERNORS:
        raise ValueError("Personal stats requires between 1 and 26 governor IDs")
    if not 1 <= int(history_days) <= 180:
        raise ValueError("Personal stats history days must be between 1 and 180")

    params: tuple[Any, ...] = (
        *ids,
        *(None for _ in range(_MAX_GOVERNORS - len(ids))),
        history_days,
    )
    conn = get_conn_with_retries()
    cursor = None
    try:
        cursor = conn.cursor()
        if hasattr(cursor, "timeout"):
            cursor.timeout = _QUERY_TIMEOUT_SECONDS
        cursor.execute(PERSONAL_STATS_SQL, params)
        header_rows = _next_rows(
            cursor,
            advance=False,
            missing_message="Personal stats SQL did not return its header result set",
        )
        if len(header_rows) != 1:
            raise ValueError("Personal stats SQL did not return exactly one header row")
        header = _map_header(header_rows[0], expected_count=len(ids))
        if header.stats_anchor_date is not None:
            expected_start = header.stats_anchor_date - timedelta(days=history_days - 1)
            if (
                header.window_start_date != expected_start
                or header.window_end_date != header.stats_anchor_date
            ):
                raise ValueError("Personal stats SQL returned an invalid history window")
        allowed_ids = frozenset(ids)
        daily_rows = _next_rows(
            cursor,
            advance=True,
            missing_message="Personal stats SQL did not return its daily result set",
        )
        rows = tuple(_map_daily_row(row, allowed_ids=allowed_ids) for row in daily_rows)
        if header.window_start_date is not None and header.window_end_date is not None:
            if any(
                not header.window_start_date <= row.as_of_date <= header.window_end_date
                for row in rows
            ):
                raise ValueError("Personal stats SQL returned an out-of-window source row")
        return PersonalStatsDataSet(header=header, rows=rows)
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()
