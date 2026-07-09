"""Read-only DAL for future governor dashboard payload assembly."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from file_utils import fetch_one_dict, get_conn_with_retries
from player_self_service.governor_dashboard_models import GovernorDashboardDataRow


def _clean_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, Decimal):
            return int(value)
        text = str(value).strip()
        if not text:
            return None
        return int(Decimal(text))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return None


def _row_to_dashboard_data(
    row: dict[str, Any] | None, governor_id: int
) -> GovernorDashboardDataRow:
    if not row:
        return GovernorDashboardDataRow(governor_id=int(governor_id))
    return GovernorDashboardDataRow(
        governor_id=int(row.get("GovernorID") or governor_id),
        governor_name=_clean_text(row.get("GovernorName")),
        alliance=_clean_text(row.get("Alliance")),
        power=_to_int(row.get("Power")),
        kill_points=_to_int(row.get("KillPoints")),
        dead=_to_int(row.get("Dead")),
        helps=_to_int(row.get("Helps")),
        healed=_to_int(row.get("Healed")),
        highest_acclaim=_to_int(row.get("HighestAcclaim")),
        ark_joined=_to_int(row.get("AOOJoined")),
        ark_won=_to_int(row.get("AOOWon")),
        times_named_autarch=_to_int(row.get("AutarchTimes")),
        conduct=_to_float(row.get("Conduct")),
        civilization=_clean_text(row.get("Civilization")),
        updated_at_utc=row.get("UpdatedAtUtc"),
        scan_order=_to_int(row.get("ScanOrder")),
    )


def fetch_governor_dashboard_data(governor_id: int) -> GovernorDashboardDataRow:
    """Fetch the approved Phase 2 dashboard fields for a selected governor."""
    gid = int(governor_id)
    sql = """
        WITH Requested AS (
            SELECT CAST(? AS BIGINT) AS GovernorID
        ),
        LatestScan AS (
            SELECT TOP (1)
                CAST(s.GovernorID AS BIGINT) AS GovernorID,
                LTRIM(RTRIM(s.GovernorName)) AS GovernorName,
                LTRIM(RTRIM(s.Alliance)) AS Alliance,
                CAST(s.Power AS BIGINT) AS Power,
                CAST(s.KillPoints AS BIGINT) AS KillPoints,
                CAST(s.Deads AS BIGINT) AS Dead,
                CAST(s.Helps AS BIGINT) AS Helps,
                CAST(s.HealedTroops AS BIGINT) AS Healed,
                s.Conduct,
                LTRIM(RTRIM(s.Civilization)) AS Civilization,
                s.ScanDate AS UpdatedAtUtc,
                CAST(s.SCANORDER AS BIGINT) AS ScanOrder
            FROM dbo.KingdomScanData4 AS s WITH (NOLOCK)
            WHERE TRY_CONVERT(BIGINT, s.GovernorID) = ?
            ORDER BY s.SCANORDER DESC, s.ScanDate DESC
        ),
        DashboardAgg AS (
            SELECT
                CAST(d.[Gov_ID] AS BIGINT) AS GovernorID,
                MAX(TRY_CONVERT(BIGINT, d.[HighestAcclaim])) AS HighestAcclaim,
                MAX(TRY_CONVERT(BIGINT, d.[AOOJoined])) AS AOOJoined,
                MAX(TRY_CONVERT(INT, d.[AOOWon])) AS AOOWon,
                MAX(TRY_CONVERT(BIGINT, d.[AutarchTimes])) AS AutarchTimes
            FROM dbo.ALL_STATS_FOR_DASHBOARD AS d WITH (NOLOCK)
            WHERE d.[Gov_ID] = ?
            GROUP BY d.[Gov_ID]
        ),
        LatestDashboard AS (
            SELECT TOP (1)
                CAST(d.[Gov_ID] AS BIGINT) AS GovernorID,
                LTRIM(RTRIM(d.[Governor_Name])) AS GovernorName,
                LTRIM(RTRIM(d.[Civilization])) AS Civilization,
                d.[Conduct]
            FROM dbo.ALL_STATS_FOR_DASHBOARD AS d WITH (NOLOCK)
            WHERE d.[Gov_ID] = ?
            ORDER BY d.[KVK_NO] DESC
        )
        SELECT
            r.GovernorID,
            COALESCE(NULLIF(ls.GovernorName, ''), NULLIF(ld.GovernorName, '')) AS GovernorName,
            NULLIF(ls.Alliance, '') AS Alliance,
            ls.Power,
            ls.KillPoints,
            ls.Dead,
            ls.Helps,
            ls.Healed,
            da.HighestAcclaim,
            da.AOOJoined,
            da.AOOWon,
            da.AutarchTimes,
            COALESCE(ls.Conduct, ld.Conduct) AS Conduct,
            COALESCE(NULLIF(ls.Civilization, ''), NULLIF(ld.Civilization, '')) AS Civilization,
            ls.UpdatedAtUtc,
            ls.ScanOrder
        FROM Requested AS r
        LEFT JOIN LatestScan AS ls ON ls.GovernorID = r.GovernorID
        LEFT JOIN DashboardAgg AS da ON da.GovernorID = r.GovernorID
        LEFT JOIN LatestDashboard AS ld ON ld.GovernorID = r.GovernorID;
    """
    conn = get_conn_with_retries()
    try:
        cur = conn.cursor()
        cur.execute(sql, (gid, gid, gid, gid))
        return _row_to_dashboard_data(fetch_one_dict(cur), gid)
    finally:
        conn.close()
