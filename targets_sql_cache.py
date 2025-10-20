# targets_sql_cache.py
from __future__ import annotations

import json
import logging
import os
from typing import Any

from constants import PLAYER_TARGETS_CACHE, _conn
from kvk_state import get_kvk_context_today
from utils import normalize_governor_id, utcnow

log = logging.getLogger(__name__)

VIEW_NAME = "dbo.v_TARGETS_FOR_UPLOAD"  # single source of truth


def _read_json(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.debug("[targets_sql_cache] Failed to read JSON %s: %s", path, exc)
        return {}


def _write_json(path: str, data: dict[str, Any]) -> None:
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        # If write fails, remove temp file if present and raise/log.
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        log.exception("[targets_sql_cache] Failed to write JSON cache to %s", path)
        raise


def _fetch_targets_from_view(cur) -> list[dict[str, Any]]:
    """
    Reads from dbo.v_TARGETS_FOR_UPLOAD and normalizes columns to:
      GovernorID, GovernorName, Power (bigint), DKP_Target, Kill_Target, Deads_Target, Min_Kill_Target

    Notes:
      - Uses COALESCE to support both [Dead Target] and [Deads Target].
      - Power may be NVARCHAR with thousands separators; coerced to bigint via replace.
    """
    # shared expression to coerce NVARCHAR '129,882,341' -> bigint 129882341
    POWER_EXPR = "TRY_CONVERT(bigint, REPLACE(REPLACE([Power], ',', ''), ' ', ''))"

    # Use COALESCE to handle either column name variant in a single query
    sql = f"""
        SELECT
            CAST([Gov_ID] AS bigint)                 AS GovernorID,
            CAST([Governor_Name] AS nvarchar(255))   AS GovernorName,
            {POWER_EXPR}                             AS Power,
            TRY_CONVERT(float, [DKP Target])         AS DKP_Target,
            TRY_CONVERT(float, [Kill Target])        AS Kill_Target,
            TRY_CONVERT(float, COALESCE([Dead Target], [Deads Target])) AS Deads_Target,
            TRY_CONVERT(float, [Minimum Kill Target]) AS Min_Kill_Target
        FROM {VIEW_NAME}
    """

    cur.execute(sql)
    rows = cur.fetchall()

    out: list[dict[str, Any]] = []
    for r in rows:
        # r is row-like; using positional indices keeps parity with previous code
        gov_raw = r[0]
        if gov_raw is None:
            # Skip rows without a valid GovernorID (log at debug to allow post-mortem)
            log.debug("[targets_sql_cache] Skipping row with missing GovernorID: %s", r)
            continue

        try:
            # Normalize GovernorID to canonical string form
            normalized_id = normalize_governor_id(gov_raw)
        except Exception:
            # Fallback to simple str cast if normalization fails
            normalized_id = str(int(gov_raw)) if isinstance(gov_raw, (int, float)) else str(gov_raw)

        out.append(
            {
                "GovernorID": normalized_id,
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
    Returns the new cache (or existing cache on failures).
    """
    existing = _read_json(PLAYER_TARGETS_CACHE)
    ctx = get_kvk_context_today()
    if not ctx:
        log.debug("[targets_sql_cache] No KVK context available; returning existing cache.")
        return existing

    data: dict[str, Any] = {
        "_meta": {
            # Use aware UTC helper for consistent timestamps
            "generated_at": utcnow().isoformat(),
            "kvk_no": ctx.get("kvk_no"),  # context value for reference
            "state": ctx.get("state"),  # e.g., ACTIVE / ENDED / DRAFT
        },
        "by_gov": {},
    }

    # Explicitly open/close connection and cursor for portability
    try:
        conn = _conn()
    except Exception:
        log.exception(
            "[targets_sql_cache] Failed to create DB connection; returning existing cache."
        )
        return existing

    try:
        cur = conn.cursor()
        try:
            try:
                rows = _fetch_targets_from_view(cur)
            except Exception:
                log.exception("[targets_sql_cache] Failed to read from %s", VIEW_NAME)
                return existing

            for t in rows:
                # Skip rows without a valid GovernorID (guard)
                gid = t.get("GovernorID")
                if not gid:
                    continue
                # Enrich with current context—useful for downstream logic/embeds
                t["TargetState"] = ctx.get("state")
                t["KVK_NO"] = ctx.get("kvk_no")
                # Ensure key is canonical string
                key = str(gid)
                data["by_gov"][key] = t
        finally:
            try:
                cur.close()
            except Exception:
                pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Persist the cache atomically
    try:
        _write_json(PLAYER_TARGETS_CACHE, data)
    except Exception:
        log.exception("[targets_sql_cache] Failed to persist cache to %s", PLAYER_TARGETS_CACHE)
        # Return newly built data even if write failed (so callers can still use in-memory result)
    return data


def get_targets_for_governor(governor_id: int) -> dict[str, Any] | None:
    cache = _read_json(PLAYER_TARGETS_CACHE)
    if not cache:
        cache = refresh_targets_cache()
    # Make sure lookup uses canonical id form
    try:
        key = normalize_governor_id(governor_id)
    except Exception:
        key = str(governor_id)
    return (cache.get("by_gov") or {}).get(str(key))
