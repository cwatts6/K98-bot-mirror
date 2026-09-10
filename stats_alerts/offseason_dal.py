"""SQL ownership for off-season stats-alert data loading."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from file_utils import fetch_one_dict

_ACTIVITY_COLUMNS = {
    "BuildingDelta": "BuildDonations",
    "TechDonationDelta": "TechDonations",
}
_DAILY_VIEW_CONTRACTS = {
    ("dbo.vDaily_Helps", "HelpsDelta", "GovernorName", "AsOfDate"),
    ("dbo.vDaily_RSSGathered", "RSSGatheredDelta", "GovernorName", "AsOfDate"),
    ("dbo.vDaily_RSSAssisted", "RSSAssistedDelta", "GovernorName", "AsOfDate"),
    ("dbo.v_RallyDaily_Latest", "TotalRallies", "GovernorName", None),
}
_WEEKLY_VIEW_CONTRACTS = {
    "building": ("dbo.vAllianceActivity_WeeklyDelta", "BuildingDeltaWeek"),
    "tech": ("dbo.vAllianceActivity_WeeklyDelta", "TechDonationDeltaWeek"),
    "helps": ("dbo.vWTD_Helps", "WTD_HELPS"),
    "rss_gathered": ("dbo.vWTD_RSSGathered", "WTD_RssGathered"),
    "rss_assisted": ("dbo.vWTD_RSSAssisted", "[WTD_RSSAssisted]"),
    "forts": ("dbo.vFortsCompleted_WeekToDate", "TotalRallies"),
}


def _bounded_limit(limit: int, *, maximum: int = 100) -> int:
    value = int(limit)
    if value < 1 or value > maximum:
        raise ValueError(f"Leaderboard limit must be between 1 and {maximum}")
    return value


def _fetchone(cur: Any, sql: str, *params: Any) -> tuple | None:
    cur.execute(sql, *params)
    row = fetch_one_dict(cur)
    return tuple(row.values()) if row is not None else None


def _fetchall(cur: Any, sql: str, *params: Any) -> list[tuple]:
    cur.execute(sql, *params)
    return cur.fetchall()


def pick_daily_snapshot_date(cur: Any) -> date:
    row = _fetchone(
        cur,
        """
        DECLARE @today date = CONVERT(date, SYSUTCDATETIME());
        DECLARE @yesterday date = DATEADD(day, -1, @today);
        SELECT TOP (1) AsOfDate
        FROM dbo.AllianceActivityDaily
        WHERE AsOfDate IN (@today, @yesterday)
        GROUP BY AsOfDate
        ORDER BY AsOfDate DESC;
        """,
    )
    if row and row[0]:
        return row[0]
    row = _fetchone(cur, "SELECT MAX(AsOfDate) FROM dbo.AllianceActivityDaily;")
    return row[0] if row and row[0] else datetime.now(UTC).date()


def get_kingdom_summary(cur: Any) -> dict[str, int]:
    row = _fetchone(
        cur,
        """
        ;WITH last AS (SELECT MAX(SCANORDER) AS cur_order FROM dbo.KingdomScanData4)
        SELECT
            (SELECT cur_order FROM last) AS cur_order,
            (SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4
             WHERE SCANORDER < (SELECT cur_order FROM last)) AS prev_order;
        """,
    )
    cur_order, prev_order = row or (None, None)
    if cur_order is None:
        return {"total_power_top300": 0, "total_players": 0, "power_delta_top300": 0}
    player_row = _fetchone(
        cur,
        "SELECT COUNT(*) FROM dbo.KingdomScanData4 WHERE SCANORDER = ?",
        cur_order,
    )
    total_players = player_row[0] if player_row else 0

    def top300_at(scan_order: int | None) -> int:
        if scan_order is None:
            return 0
        value = _fetchone(
            cur,
            """
            SELECT SUM(Power)
            FROM (
                SELECT TOP (300) Power
                FROM dbo.KingdomScanData4
                WHERE SCANORDER = ?
                ORDER BY Power DESC
            ) AS ranked_power;
            """,
            scan_order,
        )
        return int(value[0] or 0) if value else 0

    current_power = top300_at(cur_order)
    previous_power = top300_at(prev_order)
    return {
        "total_power_top300": current_power,
        "total_players": int(total_players or 0),
        "power_delta_top300": current_power - previous_power,
    }


def get_kingdom_summary_weekly(cur: Any) -> dict[str, int]:
    latest_row = _fetchone(
        cur,
        "SELECT CAST(MAX(ScanDate) AS date) FROM dbo.KingdomScanData4;",
    )
    latest_date = latest_row[0] if latest_row else None
    row = _fetchone(
        cur,
        """
        DECLARE @latest date = ?;
        DECLARE @dow int = (DATEPART(WEEKDAY, @latest) + 5) % 7;
        DECLARE @start_this_week date = DATEADD(day, -@dow, @latest);
        DECLARE @start_prev_week date = DATEADD(day, -7, @start_this_week);
        SELECT
            (SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4
             WHERE ScanDate < @start_prev_week) AS so_start,
            (SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4
             WHERE ScanDate < @start_this_week) AS so_end;
        """,
        latest_date,
    )
    start_order, end_order = row or (None, None)
    if start_order is None:
        first = _fetchone(cur, "SELECT MIN(SCANORDER) FROM dbo.KingdomScanData4;")
        start_order = first[0] if first else None
    if end_order is None:
        last = _fetchone(
            cur,
            "SELECT MAX(SCANORDER) FROM dbo.KingdomScanData4 WHERE ScanDate < ?",
            latest_date,
        )
        end_order = last[0] if last else None

    def top300_at(scan_order: int | None) -> int:
        if scan_order is None:
            return 0
        value = _fetchone(
            cur,
            """
            SELECT SUM(Power)
            FROM (SELECT TOP (300) Power
                  FROM dbo.KingdomScanData4
                  WHERE SCANORDER = ?
                  ORDER BY Power DESC) AS ranked_power;
            """,
            scan_order,
        )
        return int(value[0] or 0) if value else 0

    start_value = top300_at(start_order)
    end_value = top300_at(end_order)
    return {
        "top300_start": start_value,
        "top300_end": end_value,
        "weekly_delta": end_value - start_value,
    }


def _top_names_for_day(cur: Any, metric_sql_col: str, limit: int, snap_date: date):
    if metric_sql_col not in _ACTIVITY_COLUMNS.values():
        raise ValueError("Unsupported daily activity metric")
    safe_limit = _bounded_limit(limit)
    rows = _fetchall(
        cur,
        f"""
        WITH daily AS (
            SELECT GovernorID, SUM({metric_sql_col}) AS MetricValue
            FROM dbo.AllianceActivityDaily
            WHERE AsOfDate = ?
            GROUP BY GovernorID
        )
        SELECT TOP ({safe_limit})
               COALESCE(names.GovernorName,
                        CONCAT('#', CAST(daily.GovernorID AS varchar(20)))) AS GovernorName,
               daily.MetricValue
        FROM daily
        OUTER APPLY (
            SELECT TOP (1) rows.GovernorName
            FROM dbo.AllianceActivitySnapshotRow AS rows
            JOIN dbo.AllianceActivitySnapshotHeader AS headers
              ON headers.SnapshotId = rows.SnapshotId
            WHERE rows.GovernorID = daily.GovernorID
            ORDER BY headers.SnapshotTsUtc DESC
        ) AS names
        ORDER BY daily.MetricValue DESC, GovernorName ASC;
        """,
        snap_date,
    )
    return [(row[0], int(row[1] or 0)) for row in rows]


def get_activity_top_daily(cur: Any, metric_col: str, limit: int, snap_date: date):
    try:
        sql_column = _ACTIVITY_COLUMNS[metric_col]
    except KeyError as exc:
        raise ValueError("Unsupported daily activity metric") from exc
    return _top_names_for_day(cur, sql_column, limit, snap_date)


def get_daily_top(
    cur: Any,
    view_name: str,
    value_col: str,
    snap_date: date,
    label_col: str = "GovernorName",
    limit: int = 5,
    date_col: str | None = None,
):
    contract = (view_name, value_col, label_col, date_col)
    if contract not in _DAILY_VIEW_CONTRACTS:
        raise ValueError("Unsupported daily leaderboard contract")
    safe_limit = _bounded_limit(limit)
    if date_col:
        rows = _fetchall(
            cur,
            f"""
            SELECT TOP ({safe_limit}) {label_col}, {value_col}
            FROM {view_name}
            WHERE CAST({date_col} AS date) = ?
            ORDER BY {value_col} DESC, {label_col} ASC;
            """,
            snap_date,
        )
    else:
        rows = _fetchall(
            cur,
            f"""
            SELECT TOP ({safe_limit}) {label_col}, {value_col}
            FROM {view_name}
            ORDER BY {value_col} DESC, {label_col} ASC;
            """,
        )
    return [(row[0], int(row[1] or 0)) for row in rows]


def get_activity_top_week(cur: Any, metric_col: str, limit: int = 10):
    try:
        sql_column = _ACTIVITY_COLUMNS[metric_col]
    except KeyError as exc:
        raise ValueError("Unsupported weekly activity metric") from exc
    safe_limit = _bounded_limit(limit)
    rows = _fetchall(
        cur,
        f"""
        DECLARE @latest date = (SELECT MAX(AsOfDate) FROM dbo.AllianceActivityDaily);
        IF @latest IS NULL
        BEGIN
            SELECT TOP (0) CAST(NULL AS nvarchar(1)) AS GovernorName,
                           CAST(0 AS int) AS MetricValue;
            RETURN;
        END;
        DECLARE @dow int = (DATEPART(WEEKDAY, @latest) + 5) % 7;
        DECLARE @start_this_week date = DATEADD(day, -@dow, @latest);
        DECLARE @start_prev_week date = DATEADD(day, -7, @start_this_week);
        WITH weekly AS (
            SELECT GovernorID, SUM({sql_column}) AS MetricValue
            FROM dbo.AllianceActivityDaily
            WHERE AsOfDate >= @start_prev_week AND AsOfDate < @start_this_week
            GROUP BY GovernorID
        )
        SELECT TOP ({safe_limit})
               COALESCE(names.GovernorName,
                        CONCAT('#', CAST(weekly.GovernorID AS varchar(20)))) AS GovernorName,
               weekly.MetricValue
        FROM weekly
        OUTER APPLY (
            SELECT TOP (1) rows.GovernorName
            FROM dbo.AllianceActivitySnapshotRow AS rows
            JOIN dbo.AllianceActivitySnapshotHeader AS headers
              ON headers.SnapshotId = rows.SnapshotId
            WHERE rows.GovernorID = weekly.GovernorID
            ORDER BY headers.SnapshotTsUtc DESC
        ) AS names
        ORDER BY weekly.MetricValue DESC, GovernorName ASC;
        """,
    )
    return [(row[0], int(row[1] or 0)) for row in rows]


def load_all_daily(cur: Any) -> dict[str, list[tuple[str, int]]]:
    snap_date = pick_daily_snapshot_date(cur)
    return {
        "building": get_activity_top_daily(cur, "BuildingDelta", 5, snap_date),
        "tech": get_activity_top_daily(cur, "TechDonationDelta", 5, snap_date),
        "helps": get_daily_top(
            cur, "dbo.vDaily_Helps", "HelpsDelta", snap_date, date_col="AsOfDate"
        ),
        "rss_gathered": get_daily_top(
            cur,
            "dbo.vDaily_RSSGathered",
            "RSSGatheredDelta",
            snap_date,
            date_col="AsOfDate",
        ),
        "rss_assisted": get_daily_top(
            cur,
            "dbo.vDaily_RSSAssisted",
            "RSSAssistedDelta",
            snap_date,
            date_col="AsOfDate",
        ),
        "forts": get_daily_top(
            cur, "dbo.v_RallyDaily_Latest", "TotalRallies", snap_date, date_col=None
        ),
    }


def get_weekly_top(cur: Any, contract_name: str, limit: int = 10):
    try:
        view_name, value_col = _WEEKLY_VIEW_CONTRACTS[contract_name]
    except KeyError as exc:
        raise ValueError("Unsupported weekly leaderboard contract") from exc
    safe_limit = _bounded_limit(limit)
    rows = _fetchall(
        cur,
        f"""
        SELECT TOP ({safe_limit}) GovernorName, {value_col} AS MetricValue
        FROM {view_name}
        ORDER BY {value_col} DESC, GovernorName ASC;
        """,
    )
    return [(row[0], int(row[1] or 0)) for row in rows]


def load_all_weekly(cur: Any) -> dict[str, list[tuple[str, int]]]:
    return {name: get_weekly_top(cur, name) for name in _WEEKLY_VIEW_CONTRACTS}
