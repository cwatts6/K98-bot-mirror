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
                TRY_CONVERT(BIGINT, s.HighestAcclaim) AS HighestAcclaim,
                TRY_CONVERT(BIGINT, s.AOOJoined) AS AOOJoined,
                TRY_CONVERT(INT, s.AOOWon) AS AOOWon,
                TRY_CONVERT(BIGINT, s.AutarchTimes) AS AutarchTimes,
                s.Conduct,
                LTRIM(RTRIM(s.Civilization)) AS Civilization,
                s.ScanDate AS UpdatedAtUtc,
                CAST(s.SCANORDER AS BIGINT) AS ScanOrder
            FROM dbo.KingdomScanData4 AS s WITH (NOLOCK)
            WHERE TRY_CONVERT(BIGINT, s.GovernorID) = ?
            ORDER BY s.SCANORDER DESC, s.ScanDate DESC
        )
        SELECT
            r.GovernorID,
            NULLIF(ls.GovernorName, '') AS GovernorName,
            NULLIF(ls.Alliance, '') AS Alliance,
            ls.Power,
            ls.KillPoints,
            ls.Dead,
            ls.Helps,
            ls.Healed,
            ls.HighestAcclaim,
            ls.AOOJoined,
            ls.AOOWon,
            ls.AutarchTimes,
            ls.Conduct,
            COALESCE(NULLIF(cm.Civilization_Name, ''), NULLIF(ls.Civilization, ''))
                AS Civilization,
            ls.UpdatedAtUtc,
            ls.ScanOrder
        FROM Requested AS r
        LEFT JOIN LatestScan AS ls ON ls.GovernorID = r.GovernorID
        LEFT JOIN dbo.Civilization_Mapping AS cm WITH (NOLOCK)
            ON cm.Civilization = TRY_CONVERT(INT, NULLIF(ls.Civilization, ''));
    """
    conn = get_conn_with_retries()
    try:
        cur = conn.cursor()
        cur.execute(sql, (gid, gid))
        return _row_to_dashboard_data(fetch_one_dict(cur), gid)
    finally:
        conn.close()
