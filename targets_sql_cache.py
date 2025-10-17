# targets_sql_cache.py
from __future__ import annotations

from datetime import datetime
import json
import logging
import os
from typing import Any

import pyodbc

from constants import PLAYER_TARGETS_CACHE, _conn
from kvk_state import get_kvk_context_today

log = logging.getLogger(__name__)

VIEW_NAME = "dbo.v_TARGETS_FOR_UPLOAD"  # single source of truth


def _read_json(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, data: dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _fetch_targets_from_view(cur) -> list[dict[str, Any]]:
    """
    Reads from dbo.v_TARGETS_FOR_UPLOAD and normalizes columns to:
      GovernorID, GovernorName, Power (bigint), DKP_Target, Kill_Target, Deads_Target, Min_Kill_Target

    Note:
      - Power is NVARCHAR in export (e.g. '129,882,341'); coerced to bigint.
      - Some exports use [Dead Target] vs [Deads Target]; we try both.
    """
    # shared expression to coerce NVARCHAR '129,882,341' -> bigint 129882341
    POWER_EXPR = "TRY_CONVERT(bigint, REPLACE(REPLACE([Power], ',', ''), ' ', ''))"

    sql_a = f"""
        SELECT
            CAST([Gov_ID] AS bigint)                 AS GovernorID,
            CAST([Governor_Name] AS nvarchar(255))   AS GovernorName,
            {POWER_EXPR}                             AS Power,
            TRY_CONVERT(float, [DKP Target])         AS DKP_Target,
            TRY_CONVERT(float, [Kill Target])        AS Kill_Target,
            TRY_CONVERT(float, [Dead Target])        AS Deads_Target,
            TRY_CONVERT(float, [Minimum Kill Target]) AS Min_Kill_Target
        FROM {VIEW_NAME}
    """
    sql_b = f"""
        SELECT
            CAST([Gov_ID] AS bigint)                 AS GovernorID,
            CAST([Governor_Name] AS nvarchar(255))   AS GovernorName,
            {POWER_EXPR}                             AS Power,
            TRY_CONVERT(float, [DKP Target])         AS DKP_Target,
            TRY_CONVERT(float, [Kill Target])        AS Kill_Target,
            TRY_CONVERT(float, [Deads Target])       AS Deads_Target,
            TRY_CONVERT(float, [Minimum Kill Target]) AS Min_Kill_Target
        FROM {VIEW_NAME}
    """

    try:
        cur.execute(sql_a)
        rows = cur.fetchall()
    except pyodbc.ProgrammingError:
        # Fall back to "[Deads Target]"
        cur.execute(sql_b)
        rows = cur.fetchall()

    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "GovernorID": int(r[0]) if r[0] is not None else None,
                "GovernorName": (r[1] or "").strip(),
                "Power": int(r[2]) if r[2] is not None else None,
                "DKP_Target": r[3],
                "Kill_Target": r[4],
                "Deads_Target": r[5],
                "Min_Kill_Target": r[6],
            }
        )
    return out


def refresh_targets_cache() -> dict[str, Any]:
    """
    Builds the cache from dbo.v_TARGETS_FOR_UPLOAD.
    Metadata (kvk_no/state) comes from get_kvk_context_today(), but all row data
    comes from the single view which always points at the latest KVK export.
    """
    existing = _read_json(PLAYER_TARGETS_CACHE)
    ctx = get_kvk_context_today()
    if not ctx:
        return existing

    data: dict[str, Any] = {
        "_meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "kvk_no": ctx.get("kvk_no"),  # context value for reference
            "state": ctx.get("state"),  # e.g., ACTIVE / ENDED / DRAFT
        },
        "by_gov": {},
    }

    with _conn() as conn, conn.cursor() as cur:
        try:
            rows = _fetch_targets_from_view(cur)
        except Exception:
            log.exception("[targets_sql_cache] Failed to read from %s", VIEW_NAME)
            return existing

        for t in rows:
            # Enrich with current context—useful for downstream logic/embeds
            t["TargetState"] = ctx.get("state")
            t["KVK_NO"] = ctx.get("kvk_no")
            data["by_gov"][str(t["GovernorID"])] = t

    _write_json(PLAYER_TARGETS_CACHE, data)
    return data


def get_targets_for_governor(governor_id: int) -> dict[str, Any] | None:
    cache = _read_json(PLAYER_TARGETS_CACHE)
    if not cache:
        cache = refresh_targets_cache()
    return (cache.get("by_gov") or {}).get(str(governor_id))
