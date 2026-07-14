"""Set-based read-only DAL for the private Accounts portfolio."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from file_utils import get_conn_with_retries
from player_self_service.accounts_models import AccountsScanRow

_BULK_CHUNK_SIZE = 500


def _to_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(Decimal(str(value).strip()))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _clean(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _rows_to_dicts(cursor: Any) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    columns = [str(item[0]) for item in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def _chunks(values: tuple[int, ...]) -> Iterable[tuple[int, ...]]:
    for start in range(0, len(values), _BULK_CHUNK_SIZE):
        yield values[start : start + _BULK_CHUNK_SIZE]


def _map_row(row: dict[str, Any]) -> AccountsScanRow:
    gid = _to_int(row.get("RequestedGovernorID"))
    if gid is None:
        raise ValueError("Accounts scan query returned an invalid requested Governor ID")
    return AccountsScanRow(
        governor_id=gid,
        governor_name=_clean(row.get("GovernorName")),
        civilisation=_clean(row.get("Civilisation")),
        city_hall=_to_int(row.get("CityHall")),
        power=_to_int(row.get("Power")),
        troop_power=_to_int(row.get("TroopPower")),
        kill_points=_to_int(row.get("KillPoints")),
        t4_kills=_to_int(row.get("T4Kills")),
        t5_kills=_to_int(row.get("T5Kills")),
        deads=_to_int(row.get("Deads")),
        healed_troops=_to_int(row.get("HealedTroops")),
        highest_acclaim=_to_int(row.get("HighestAcclaim")),
        helps=_to_int(row.get("Helps")),
        rss_gathered=_to_int(row.get("RSSGathered")),
        rss_assistance=_to_int(row.get("RSSAssistance")),
        conduct=row.get("Conduct"),
        location_x=_to_int(row.get("LocationX")),
        location_y=_to_int(row.get("LocationY")),
        scan_date=row.get("ScanDate") if isinstance(row.get("ScanDate"), datetime) else None,
        latest_scan_date=(
            row.get("LatestScanDate")
            if isinstance(row.get("LatestScanDate"), datetime)
            else None
        ),
    )


def fetch_latest_accounts_scan_rows(governor_ids: Iterable[int]) -> tuple[AccountsScanRow, ...]:
    """Fetch one latest Kingdom 1198 scan row per distinct requested Governor ID."""
    ids = tuple(dict.fromkeys(int(value) for value in governor_ids if int(value) > 0))
    if not ids:
        return ()

    output: list[AccountsScanRow] = []
    conn = get_conn_with_retries()
    try:
        for chunk in _chunks(ids):
            values_sql = ", ".join("(?)" for _ in chunk)
            sql = f"""
                WITH Requested(GovernorID) AS (
                    SELECT CAST(v.GovernorID AS BIGINT)
                    FROM (VALUES {values_sql}) AS v(GovernorID)
                ),
                GlobalLatest AS (
                    SELECT MAX(s.ScanDate) AS LatestScanDate
                    FROM dbo.KingdomScanData4 AS s WITH (NOLOCK)
                ),
                Ranked AS (
                    SELECT
                        TRY_CONVERT(BIGINT, s.GovernorID) AS GovernorID,
                        NULLIF(LTRIM(RTRIM(s.GovernorName)), '') AS GovernorName,
                        NULLIF(LTRIM(RTRIM(s.Civilization)), '') AS RawCivilisation,
                        TRY_CONVERT(INT, s.[City Hall]) AS CityHall,
                        TRY_CONVERT(BIGINT, s.Power) AS Power,
                        TRY_CONVERT(BIGINT, s.[Troops Power]) AS TroopPower,
                        TRY_CONVERT(BIGINT, s.KillPoints) AS KillPoints,
                        TRY_CONVERT(BIGINT, s.T4_Kills) AS T4Kills,
                        TRY_CONVERT(BIGINT, s.T5_Kills) AS T5Kills,
                        TRY_CONVERT(BIGINT, s.Deads) AS Deads,
                        TRY_CONVERT(BIGINT, s.HealedTroops) AS HealedTroops,
                        TRY_CONVERT(BIGINT, s.HighestAcclaim) AS HighestAcclaim,
                        TRY_CONVERT(BIGINT, s.Helps) AS Helps,
                        TRY_CONVERT(BIGINT, s.RSS_Gathered) AS RSSGathered,
                        TRY_CONVERT(BIGINT, s.RSSAssistance) AS RSSAssistance,
                        s.Conduct,
                        s.ScanDate,
                        ROW_NUMBER() OVER (
                            PARTITION BY TRY_CONVERT(BIGINT, s.GovernorID)
                            ORDER BY s.ScanDate DESC, s.SCANORDER DESC, s.AsOfDate DESC
                        ) AS rn
                    FROM dbo.KingdomScanData4 AS s WITH (NOLOCK)
                    INNER JOIN Requested AS r
                        ON r.GovernorID = TRY_CONVERT(BIGINT, s.GovernorID)
                )
                SELECT
                    r.GovernorID AS RequestedGovernorID,
                    ranked.GovernorName,
                    COALESCE(NULLIF(cm.Civilization_Name, ''), ranked.RawCivilisation)
                        AS Civilisation,
                    ranked.CityHall,
                    ranked.Power,
                    ranked.TroopPower,
                    ranked.KillPoints,
                    ranked.T4Kills,
                    ranked.T5Kills,
                    ranked.Deads,
                    ranked.HealedTroops,
                    ranked.HighestAcclaim,
                    ranked.Helps,
                    ranked.RSSGathered,
                    ranked.RSSAssistance,
                    ranked.Conduct,
                    pl.X AS LocationX,
                    pl.Y AS LocationY,
                    ranked.ScanDate,
                    global_scan.LatestScanDate
                FROM Requested AS r
                CROSS JOIN GlobalLatest AS global_scan
                LEFT JOIN Ranked AS ranked
                    ON ranked.GovernorID = r.GovernorID AND ranked.rn = 1
                LEFT JOIN dbo.Civilization_Mapping AS cm WITH (NOLOCK)
                    ON cm.Civilization = TRY_CONVERT(INT, NULLIF(ranked.RawCivilisation, ''))
                LEFT JOIN dbo.PlayerLocation AS pl WITH (NOLOCK)
                    ON pl.GovernorID = r.GovernorID
                ORDER BY r.GovernorID;
            """
            cursor = conn.cursor()
            cursor.execute(sql, tuple(chunk))
            output.extend(_map_row(row) for row in _rows_to_dicts(cursor))
    finally:
        conn.close()
    return tuple(output)
