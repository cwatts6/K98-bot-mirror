# player_stats_cache.py
from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
import logging
import os
import random
import time
from typing import Any

import pyodbc

from constants import PLAYER_STATS_CACHE

logger = logging.getLogger(__name__)

# =========================
# Env standardization notes
# =========================
# This module now standardizes DB retry env vars to:
#   DB_CONN_RETRIES, DB_BACKOFF_BASE, DB_BACKOFF_MAX
# via file_utils.get_conn_with_retries().
#
# Legacy env vars (deprecated, no longer used here):
#   PLAYER_STATS_DB_RETRIES, PLAYER_STATS_DB_BACKOFF, PLAYER_STATS_DB_MAX_BACKOFF
#
# We warn once if legacy vars are present to help ops migration.
_WARNED_LEGACY_DB_ENVS = False

# NEW: cross-process lock timeout for cache writer (seconds)
_CACHE_LOCK_TIMEOUT = float(os.getenv("PLAYER_STATS_CACHE_LOCK_TIMEOUT", "5.0"))

# =========================
# SQL
# =========================
_SQL = "SELECT * FROM dbo.[STATS_FOR_UPLOAD]"  # spelled as provided


# =========================
# helpers
# =========================
def _utc_now_iso() -> str:
    # Project standard: always UTC-aware timestamps.
    return datetime.now(UTC).isoformat()


def _cache_lock_path() -> str:
    # Simple convention: sibling lock file next to the cache.
    return f"{PLAYER_STATS_CACHE}.lock"


def _last_kvk_cache_path() -> str:
    """
    Prefer explicit PLAYER_STATS_LAST_CACHE from constants if present.
    Otherwise derive a sibling file name from PLAYER_STATS_CACHE:
      e.g. player_stats_cache.json -> player_stats_cache.lastkvk.json
    """
    try:
        from constants import PLAYER_STATS_LAST_CACHE

        return PLAYER_STATS_LAST_CACHE
    except Exception:
        # Derive from PLAYER_STATS_CACHE
        p = PLAYER_STATS_CACHE
        base, ext = os.path.splitext(p)
        if ext:
            return f"{base}.lastkvk{ext}"
        return f"{p}.lastkvk"


def _last_kvk_lock_path() -> str:
    return f"{_last_kvk_cache_path()}.lock"


def _warn_legacy_db_envs_once() -> None:
    global _WARNED_LEGACY_DB_ENVS
    if _WARNED_LEGACY_DB_ENVS:
        return
    legacy = [
        "PLAYER_STATS_DB_RETRIES",
        "PLAYER_STATS_DB_BACKOFF",
        "PLAYER_STATS_DB_MAX_BACKOFF",
    ]
    if any(os.getenv(k) for k in legacy):
        logger.warning(
            "[CACHE] Deprecated env vars detected (%s). This module now uses DB_* (DB_CONN_RETRIES/DB_BACKOFF_BASE/DB_BACKOFF_MAX).",
            ", ".join([k for k in legacy if os.getenv(k)]),
        )
    _WARNED_LEGACY_DB_ENVS = True


def _atomic_write_json_with_retries(
    path: str,
    obj: Any,
    *,
    retries: int = 5,
    base_backoff: float = 0.05,
    max_backoff: float = 0.5,
) -> None:
    """
    Windows-safe wrapper around file_utils.atomic_write_json.

    atomic_write_json uses tmp + os.replace. On Windows, os.replace can raise PermissionError
    transiently (indexers/AV/process races). We retry a few times with jittered backoff.
    """
    from file_utils import atomic_write_json

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            atomic_write_json(path, obj)
            return
        except (PermissionError, OSError) as e:
            last_exc = e
            cap = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
            delay = random.uniform(0, cap) if cap > 0 else 0.0
            logger.warning(
                "[CACHE] atomic_write_json failed (attempt %d/%d) for %s: %s; retrying in %.3fs",
                attempt,
                retries,
                path,
                e,
                delay,
            )
            if attempt >= retries:
                break
            time.sleep(delay)

    assert last_exc is not None
    raise last_exc


def _to_int(v: Any, default: int = 0) -> int:
    try:
        if v is None or v == "":
            return default
        return int(float(v))
    except Exception:
        return default


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return str(v)


def _map_row(row: pyodbc.Row, cols: list[str]) -> dict[str, Any] | None:
    # Canonical normalizer from utils (keeps inclusion/exclusion consistent across builder+loader)
    from utils import normalize_governor_id

    d = {c: row[i] for i, c in enumerate(cols)}
    gov_id = normalize_governor_id(d.get("Governor ID", d.get("GovernorID", "")))

    # Preserve previous exclusion logic exactly
    if not gov_id or gov_id == "0":
        return None

    def gi(key: str) -> int:
        return _to_int(d.get(key, 0))

    def gf(key: str) -> float:
        return round(_to_float(d.get(key, 0.0)), 2)

    def gs(key: str) -> str:
        return _to_str(d.get(key, ""))

    return {
        "GovernorID": gov_id,
        "GovernorName": (gs("Governor_Name") or gs("Governor Name")).strip(),
        "Rank": gi("Rank"),
        "KVK_RANK": gi("KVK_RANK"),
        "Power": gi("Power"),
        "Power Delta": gi("Power Delta"),
        "T4_Kills": gi("T4_Kills"),
        "T5_Kills": gi("T5_Kills"),
        "T4&T5_Kills": gi("T4&T5_Kills"),
        "OFF_SEASON_KILLS": gi("OFF_SEASON_KILLS"),
        "Kill Target": gi("Kill Target"),
        "% of Kill target": gf("% of Kill target"),
        "Deads": gi("Deads"),
        "OFF_SEASON_DEADS": gi("OFF_SEASON_DEADS"),
        "T4_Deads": gi("T4_Deads"),
        "T5_Deads": gi("T5_Deads"),
        "Dead Target": gi("Dead Target"),
        "% of Dead Target": gf("% of Dead Target"),
        "Zeroed": gi("Zeroed"),
        "DKP Score": gf("DKP_SCORE"),
        "DKP Target": gi("DKP Target"),
        "% of DKP Target": gf("% of DKP Target"),
        "Helps": gi("Helps"),
        "RSS_Assist": gi("RSS_Assist"),
        "RSS_Gathered": gi("RSS_Gathered"),
        "Pass 4 Kills": gi("Pass 4 Kills"),
        "Pass 6 Kills": gi("Pass 6 Kills"),
        "Pass 7 Kills": gi("Pass 7 Kills"),
        "Pass 8 Kills": gi("Pass 8 Kills"),
        "Pass 4 Deads": gi("Pass 4 Deads"),
        "Pass 6 Deads": gi("Pass 6 Deads"),
        "Pass 7 Deads": gi("Pass 7 Deads"),
        "Pass 8 Deads": gi("Pass 8 Deads"),
        "KVK_NO": gi("KVK_NO"),
        "LAST_REFRESH": gs("LAST_REFRESH"),
        "STATUS": (gs("STATUS") or "INCLUDED"),
    }


def _map_excel_row(
    row: pyodbc.Row, cols: list[str], kvk_no: int | None = None
) -> dict[str, Any] | None:
    """
    Map rows from EXCEL_FOR_KVK_{N} tables into the same normalized shape used in the primary cache.
    Column names in those tables (example provided by you) include:
      Gov_ID, Governor_Name, Starting Power, Power_Delta, T4_KILLS, T5_KILLS, T4&T5_Kills, Kill Target, [% of Kill Target], ...
    This function attempts to map the common columns defensively.
    """
    from utils import normalize_governor_id

    d = {c: row[i] for i, c in enumerate(cols)}
    # Column names seen: 'Gov_ID' or 'Gov ID' etc.
    raw_gov = (
        d.get("Gov_ID")
        or d.get("Gov ID")
        or d.get("GovID")
        or d.get("Governor ID")
        or d.get("GovId")
        or d.get("GovId")
    )
    gov_id = normalize_governor_id(raw_gov or "")

    if not gov_id or gov_id == "0":
        return None

    def gi(key: str) -> int:
        return _to_int(d.get(key, 0))

    def gf(key: str) -> float:
        return round(_to_float(d.get(key, 0.0)), 2)

    def gs(key: str) -> str:
        return _to_str(d.get(key, ""))

    # Map column names from EXCEL table to canonical keys
    return {
        "GovernorID": gov_id,
        "GovernorName": (gs("Governor_Name") or gs("Governor Name") or gs("GovernorName")).strip(),
        "Rank": gi("Rank"),
        "KVK_RANK": gi("KVK_RANK"),
        "Power": gi("Starting Power") or gi("StartingPower") or gi("Power"),
        "Power Delta": gi("Power_Delta") or gi("Power Delta") or gi("PowerDelta"),
        "T4_Kills": gi("T4_KILLS") or gi("T4_Kills"),
        "T5_Kills": gi("T5_KILLS") or gi("T5_Kills"),
        "T4&T5_Kills": gi("T4&T5_Kills") or gi("T4&T5_Kills") or gi("T4&T5_Kills"),
        "OFF_SEASON_KILLS": gi("KILLS_OUTSIDE_KVK") or gi("KILLS_OUTSIDE"),
        "Kill Target": gi("Kill Target"),
        "% of Kill target": gf("% of Kill Target")
        or gf("[% of Kill Target]")
        or gf("% of Kill Target"),
        "Deads": gi("Deads"),
        "OFF_SEASON_DEADS": gi("DEADS_OUTSIDE_KVK") or gi("DEADS_OUTSIDE"),
        "T4_Deads": gi("T4_Deads"),
        "T5_Deads": gi("T5_Deads"),
        "Dead Target": gi("Dead_Target") or gi("Dead Target"),
        "% of Dead Target": gf("% of Dead Target") or gf("[% of Dead Target]"),
        "Zeroed": gi("Zeroed"),
        "DKP Score": gf("DKP_SCORE") or gf("DKP Score"),
        "DKP Target": gi("DKP Target"),
        "% of DKP Target": gf("% of DKP Target") or gf("[% of DKP Target]"),
        "Helps": gi("Helps"),
        "RSS_Assist": gi("RSS_Assist"),
        "RSS_Gathered": gi("RSS_Gathered"),
        "Pass 4 Kills": gi("Pass 4 Kills"),
        "Pass 6 Kills": gi("Pass 6 Kills"),
        "Pass 7 Kills": gi("Pass 7 Kills"),
        "Pass 8 Kills": gi("Pass 8 Kills"),
        "Pass 4 Deads": gi("Pass 4 Deads"),
        "Pass 6 Deads": gi("Pass 6 Deads"),
        "Pass 7 Deads": gi("Pass 7 Deads"),
        "Pass 8 Deads": gi("Pass 8 Deads"),
        "KVK_NO": kvk_no if kvk_no is not None else gi("KVK_NO"),
    }


def _build_cache_sync() -> dict[str, Any]:
    """
    Build in-memory dict for cache payload.
    Uses centralized DB connection retries via file_utils.get_conn_with_retries().
    """
    from file_utils import get_conn_with_retries
    from utils import score_player_stats_rec

    _warn_legacy_db_envs_once()

    output: dict[str, Any] = {}
    # Standardized DB_* env vars are honored inside get_conn_with_retries()
    with get_conn_with_retries(meta={"operation": "player_stats_cache"}) as cn:
        cur = cn.cursor()
        cur.execute(_SQL)
        cols = [c[0] for c in cur.description]

        while True:
            rows = cur.fetchmany(1000)
            if not rows:
                break
            for r in rows:
                mapped = _map_row(r, cols)
                if not mapped:
                    continue
                gid = mapped["GovernorID"]
                if gid in output:
                    existing = output[gid]
                    # Shared scoring helper (keeps builder+loader consistent)
                    if score_player_stats_rec(mapped) > score_player_stats_rec(existing):
                        output[gid] = mapped
                else:
                    output[gid] = mapped

    output["_meta"] = {
        "source": "SQL:dbo.STATS_FOR_UPLOAD",
        "generated_at": _utc_now_iso(),
        "count": len([k for k in output.keys() if k != "_meta"]),
    }
    return output


def _build_last_kvk_cache_sync() -> dict[str, Any] | None:
    """
    Build and persist a separate cache containing the last finished KVK snapshot.
    Naming assumption: per-KVK tables follow the pattern ROK_TRACKER.dbo.[EXCEL_FOR_KVK_{N}].
    We determine the last finished KVK as MAX(KVK_NO) - 1 (from STATS_FOR_UPLOAD), then read
    the corresponding EXCEL_FOR_KVK_{N} table if it exists.
    """
    from file_utils import get_conn_with_retries

    cache_path = _last_kvk_cache_path()

    try:
        with get_conn_with_retries(meta={"operation": "player_stats_last_kvk_cache"}) as cn:
            cur = cn.cursor()
            # get max KVK number from canonical stats table
            cur.execute("SELECT MAX(KVK_NO) FROM dbo.[STATS_FOR_UPLOAD]")
            row0 = cur.fetchone()
            if not row0:
                logger.info(
                    "[LAST_KVK] No KVK_NO rows in STATS_FOR_UPLOAD; skipping last-KVK build."
                )
                return None
            max_kvk = row0[0]
            try:
                max_kvk = int(max_kvk)
            except Exception:
                logger.warning("[LAST_KVK] MAX(KVK_NO) returned non-int (%s); skipping", max_kvk)
                return None

            last_kvk_no = max_kvk - 1
            if last_kvk_no < 0:
                logger.info("[LAST_KVK] Computed last_kvk_no < 0; skipping.")
                return None

            table_name = f"ROK_TRACKER.dbo.[EXCEL_FOR_KVK_{last_kvk_no}]"
            try:
                cur.execute(f"SELECT * FROM {table_name}")
            except Exception:
                # Table may not exist (e.g., no data saved for that KVK). Graceful skip.
                logger.warning(
                    "[LAST_KVK] Could not query %s; skipping last-KVK build.", table_name
                )
                return None

            cols = [c[0] for c in cur.description]
            last_kvk_map: dict[str, dict[str, Any]] = {}

            while True:
                rows = cur.fetchmany(1000)
                if not rows:
                    break
                for r in rows:
                    mapped = _map_excel_row(r, cols, kvk_no=last_kvk_no)
                    if not mapped:
                        continue
                    gid = mapped["GovernorID"]
                    # keep best row by same scoring used for primary cache
                    try:
                        from utils import score_player_stats_rec
                    except Exception:
                        score_player_stats_rec = None

                    if gid in last_kvk_map and score_player_stats_rec is not None:
                        existing = last_kvk_map[gid]
                        if score_player_stats_rec(mapped) > score_player_stats_rec(existing):
                            last_kvk_map[gid] = mapped
                    else:
                        last_kvk_map[gid] = mapped

            # persist last_kvk_map as a JSON file containing records keyed by GovernorID
            output = {
                "_meta": {
                    "kvk_no": last_kvk_no,
                    "generated_at": _utc_now_iso(),
                    "count": len(last_kvk_map),
                },
                **last_kvk_map,
            }
            # Use atomic write with retries
            _atomic_write_json_with_retries(cache_path, output)
            logger.info(
                "[LAST_KVK] Wrote last-KVK cache to %s (KVK %s) with %s entries.",
                cache_path,
                last_kvk_no,
                len(last_kvk_map),
            )
            return output

    except Exception:
        logger.exception("[LAST_KVK] Unexpected error building last-KVK cache; skipping.")
        return None


def _build_and_persist_cache_sync() -> dict[str, Any] | None:
    """
    Sync worker intended to run off the event loop.
    Builds cache from SQL and persists it atomically.

    Concurrency:
      - Uses file_utils.acquire_lock to avoid concurrent writers across processes.
    """
    from file_utils import acquire_lock, emit_telemetry_event  # local import to reduce coupling

    t0 = time.perf_counter()
    lock_path = _cache_lock_path()

    def _emit(status: str, *, output: dict[str, Any] | None = None, error: Exception | None = None):
        try:
            duration_ms = int((time.perf_counter() - t0) * 1000)
        except Exception:
            duration_ms = None
        try:
            count = (
                (output or {}).get("_meta", {}).get("count") if isinstance(output, dict) else None
            )
        except Exception:
            count = None

        payload: dict[str, Any] = {
            "event": "player_stats_cache.build",
            "status": status,
            "duration_ms": duration_ms,
            "count": count,
            "cache_path": PLAYER_STATS_CACHE,
            "lock_path": lock_path,
        }
        if error is not None:
            payload["error_type"] = type(error).__name__
            payload["error"] = str(error)
        emit_telemetry_event(payload)

    try:
        with acquire_lock(lock_path, timeout=_CACHE_LOCK_TIMEOUT):
            try:
                output = _build_cache_sync()

                # Enforce UTC meta timestamp even if _build_cache_sync gets changed later
                meta = output.get("_meta")
                if not isinstance(meta, dict):
                    meta = {}
                    output["_meta"] = meta
                meta.setdefault("source", "SQL:dbo.STATS_FOR_UPLOAD")
                meta["generated_at"] = _utc_now_iso()

            except Exception as e:
                logger.exception(
                    "build_player_stats_cache failed while building cache from SQL: %s", e
                )

                # Preserve existing cache if present (availability first)
                if os.path.exists(PLAYER_STATS_CACHE):
                    logger.info(
                        "Existing cache %s found; leaving it unchanged after SQL failure.",
                        PLAYER_STATS_CACHE,
                    )
                    _emit("preserved_existing", error=e)
                    return None

                err_output = {
                    "_meta": {
                        "source": "SQL:dbo.STATS_FOR_UPLOAD",
                        "generated_at": _utc_now_iso(),
                        "count": 0,
                        "error": "Failed to build cache from SQL server. See logs for details.",
                    }
                }
                _atomic_write_json_with_retries(PLAYER_STATS_CACHE, err_output)
                logger.info(
                    "Wrote fallback player_stats_cache.json with error metadata at %s",
                    PLAYER_STATS_CACHE,
                )
                _emit("fallback_written", output=err_output, error=e)
                return err_output

            _atomic_write_json_with_retries(PLAYER_STATS_CACHE, output)
            _emit("ok", output=output)

            # Build/persist last-KVK cache independently (non-fatal)
            try:
                # We don't need to hold the main cache lock while building last_kvk
                last_output = _build_last_kvk_cache_sync()
                if last_output:
                    # Emit telemetry for last-kvk build
                    emit_telemetry_event(
                        {
                            "event": "player_stats_last_kvk_cache.build",
                            "status": "ok",
                            "kvk_no": (last_output.get("_meta") or {}).get("kvk_no"),
                            "count": (last_output.get("_meta") or {}).get("count"),
                        }
                    )
            except Exception as e:
                logger.exception("[LAST_KVK] Non-fatal error building last-KVK cache: %s", e)

            return output

    except TimeoutError as e:
        logger.exception(
            "[CACHE] Timeout acquiring cache lock; build aborted. lock=%s cache=%s",
            lock_path,
            PLAYER_STATS_CACHE,
        )
        _emit("lock_timeout", error=e)
        return None
    except Exception as e:
        # Defensive: telemetry if something unexpected happens outside the lock.
        logger.exception("[CACHE] Unexpected failure in cache build/persist: %s", e)
        _emit("error", error=e)
        raise


async def build_player_stats_cache():
    from file_utils import run_blocking_in_thread

    output = await run_blocking_in_thread(
        _build_and_persist_cache_sync,
        name="build_player_stats_cache",
        meta={"cache_path": PLAYER_STATS_CACHE},
    )

    if output is None:
        return

    try:
        count = (output.get("_meta") or {}).get("count")
    except Exception:
        count = None

    logger.info("[CACHE] ✅ player_stats_cache.json written with %s entries.", count)


async def build_lastkvk_player_stats_cache():
    """Standalone builder for the last-KVK cache (can be scheduled independently)."""
    from file_utils import run_blocking_in_thread

    output = await run_blocking_in_thread(
        _build_last_kvk_cache_sync,
        name="build_lastkvk_player_stats_cache",
        meta={"cache_path": _last_kvk_cache_path()},
    )
    if output is None:
        return
    try:
        count = (output.get("_meta") or {}).get("count")
    except Exception:
        count = None
    logger.info("[LAST_KVK] ✅ last-kvk cache written with %s entries.", count)


if __name__ == "__main__":
    asyncio.run(build_player_stats_cache())
    asyncio.run(build_lastkvk_player_stats_cache())
