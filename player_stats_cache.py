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

# NEW: Stored procedure execution timeout (seconds)
_SP_EXECUTION_TIMEOUT = int(os.getenv("PLAYER_STATS_SP_TIMEOUT", "300"))

# NEW: Enable/disable stored procedure execution before cache build
_REFRESH_BEFORE_BUILD = os.getenv("PLAYER_STATS_REFRESH_BEFORE_BUILD", "true").lower() == "true"

# =========================
# SQL
# =========================
_SQL_EXEC_SP = "EXEC dbo.SP_Stats_for_Upload;"
_SQL_SELECT = "SELECT * FROM dbo.[STATS_FOR_UPLOAD]"

# =========================
# Canonical mapping
# =========================
# Map canonical cache keys to possible source column name variants.
# Normalization (see _norm_name) will be applied to both incoming column
# names and candidate names to perform tolerant matching.
#
# The STATS_FOR_UPLOAD table structure has changed. The canonical candidates
# below are aligned with the exact column names from the provided extract so
# every source column is mapped into the cache payload.
_CANONICAL_FIELD_CANDIDATES: dict[str, list[str]] = {
    # identifiers / names
    "GovernorID": ["Gov_ID", "Gov ID", "GovID", "GovId", "GovernorID", "Governor ID"],
    "GovernorName": ["Governor_Name", "Governor Name", "GovernorName", "Governor_Name"],
    # basic stats
    "Rank": ["Rank"],
    "KVK_RANK": ["KVK_RANK", "KVK RANK", "KVK Rank"],
    # power
    "Starting Power": ["Starting Power", "StartingPower", "Power", "Power_Value"],
    "Power_Delta": ["Power_Delta", "Power Delta", "PowerDelta"],
    # civ / kvk meta
    "Civilization": ["Civilization"],
    "KvKPlayed": ["KvKPlayed", "KvK Played", "KvK_Played"],
    "KVK_NO": ["KVK_NO", "KVK NO", "KVK_No"],
    # most kvk fields
    "MostKvKKill": ["MostKvKKill", "MostKvK_Kill", "Most KvK Kill"],
    "MostKvKDead": ["MostKvKDead", "MostKvK_Dead", "Most KvK Dead"],
    "MostKvKHeal": ["MostKvKHeal", "MostKvK_Heal", "Most KvK Heal"],
    # acclaim / aoo
    "Acclaim": ["Acclaim"],
    "HighestAcclaim": ["HighestAcclaim", "Highest Acclaim"],
    "AOOJoined": ["AOOJoined", "AOO Joined", "AOO_Joined"],
    "AOOWon": ["AOOWon", "AOO Won", "AOOWon"],
    "AOOAvgKill": ["AOOAvgKill", "AOO Avg Kill", "AOOAvgKill"],
    "AOOAvgDead": ["AOOAvgDead", "AOO Avg Dead", "AOOAvgDead"],
    "AOOAvgHeal": ["AOOAvgHeal", "AOO Avg Heal", "AOOAvgHeal"],
    # t4/t5 kills
    "Starting_T4&T5_KILLS": [
        "Starting_T4&T5_KILLS",
        "Starting T4&T5_KILLS",
        "Starting T4&T5 Kills",
        "StartingT4&T5_KILLS",
    ],
    "T4_KILLS": ["T4_KILLS", "T4_Kills", "T4_Kills", "T4 KILLS", "T4 Kills"],
    "T5_KILLS": ["T5_KILLS", "T5_Kills", "T5_Kills", "T5 KILLS", "T5 Kills"],
    "T4&T5_Kills": ["T4&T5_Kills", "T4&T5_Kills", "T4&T5 Kills"],
    "KILLS_OUTSIDE_KVK": ["KILLS_OUTSIDE_KVK", "KILLS_OUTSIDE", "KILLS_OUTSIDE_KVK"],
    # kill targets / percents
    "Kill Target": ["Kill Target", "Kill_Target", "KillTarget"],
    "% of Kill Target": ["% of Kill Target", "% of Kill target", "[% of Kill Target]"],
    # deads / deads deltas
    "Starting_Deads": ["Starting_Deads", "Starting Deads", "StartingDeads"],
    "Deads_Delta": ["Deads_Delta", "Deads Delta", "DeadsDelta", "Deads_Delta"],
    "DEADS_OUTSIDE_KVK": ["DEADS_OUTSIDE_KVK", "DEADS_OUTSIDE", "DEADS_OUTSIDE_KVK"],
    "T4_Deads": ["T4_Deads", "T4 Deads"],
    "T5_Deads": ["T5_Deads", "T5 Deads"],
    "Dead_Target": ["Dead_Target", "Dead Target"],
    "% of Dead Target": ["% of Dead Target", "[% of Dead Target]"],
    # zero / dkp
    "Zeroed": ["Zeroed"],
    "DKP_SCORE": ["DKP_SCORE", "DKP Score"],
    "DKP_Target": ["DKP Target", "DKP_Target"],
    "% of DKP Target": ["% of DKP Target", "[% of DKP Target]"],
    # helps / rss (deltas present in new schema)
    "HelpsDelta": ["HelpsDelta", "Helps_Delta", "Helps Delta"],
    "RSS_Assist_Delta": ["RSS_Assist_Delta", "RSS Assist Delta", "RSS_Assist Delta"],
    "RSS_Gathered_Delta": ["RSS_Gathered_Delta", "RSS Gathered Delta", "RSS_Gathered Delta"],
    # passes (kills & deads)
    "Pass 4 Kills": ["Pass 4 Kills", "Pass4 Kills"],
    "Pass 6 Kills": ["Pass 6 Kills"],
    "Pass 7 Kills": ["Pass 7 Kills"],
    "Pass 8 Kills": ["Pass 8 Kills"],
    "Pass 4 Deads": ["Pass 4 Deads"],
    "Pass 6 Deads": ["Pass 6 Deads"],
    "Pass 7 Deads": ["Pass 7 Deads"],
    "Pass 8 Deads": ["Pass 8 Deads"],
    # healed troops / kill points / ranged
    "Starting_HealedTroops": [
        "Starting_HealedTroops",
        "Starting HealedTroops",
        "Starting_Healed_Troops",
    ],
    "HealedTroopsDelta": ["HealedTroopsDelta", "Healed Troops Delta", "Healed_Troops_Delta"],
    "Starting_KillPoints": ["Starting_KillPoints", "Starting KillPoints", "Starting Kill Points"],
    "KillPointsDelta": ["KillPointsDelta", "Kill Points Delta", "KillPoints_Delta"],
    "RangedPoints": ["RangedPoints", "Ranged Points", "Ranged_Points"],
    "RangedPointsDelta": ["RangedPointsDelta", "Ranged Points Delta", "Ranged_Points_Delta"],
    "AutarchTimes": ["AutarchTimes", "Autarch Times", "Autarch_Times"],
    # pre-kvk / honor fields
    "Max_PreKvk_Points": ["Max_PreKvk_Points", "Max PreKvk Points"],
    "Max_HonorPoints": ["Max_HonorPoints", "Max Honor Points"],
    "PreKvk_Rank": ["PreKvk_Rank", "PreKvk Rank"],
    "Honor_Rank": ["Honor_Rank", "Honor Rank"],
    # standard metadata
    "LAST_REFRESH": ["LAST_REFRESH", "LAST REFRESH"],
    "STATUS": ["STATUS", "INCLUDED", "EXCLUDED"],
}

# Keys that should be coerced to int
_INT_KEYS = {
    "Rank",
    "KVK_RANK",
    "T4_KILLS",
    "T5_KILLS",
    "Starting_T4&T5_KILLS",
    "T4&T5_Kills",
    "KILLS_OUTSIDE_KVK",
    "Kill Target",
    "Starting_Deads",
    "Deads_Delta",
    "DEADS_OUTSIDE_KVK",
    "T4_Deads",
    "T5_Deads",
    "Dead_Target",
    "Zeroed",
    "DKP_Target",
    "HelpsDelta",
    "RSS_Assist_Delta",
    "RSS_Gathered_Delta",
    "Pass 4 Kills",
    "Pass 6 Kills",
    "Pass 7 Kills",
    "Pass 8 Kills",
    "Pass 4 Deads",
    "Pass 6 Deads",
    "Pass 7 Deads",
    "Pass 8 Deads",
    "KVK_NO",
    "Starting_HealedTroops",
    "HealedTroopsDelta",
    "Starting_KillPoints",
    "KillPointsDelta",
    "RangedPoints",
    "RangedPointsDelta",
    "AutarchTimes",
    "KvKPlayed",
    "MostKvKKill",
    "MostKvKDead",
    "MostKvKHeal",
    "Acclaim",
    "HighestAcclaim",
    "AOOJoined",
    "AOOWon",
    "AOOAvgKill",
    "AOOAvgDead",
    "AOOAvgHeal",
    "Max_PreKvk_Points",
    "Max_HonorPoints",
    "PreKvk_Rank",
    "Honor_Rank",
    "DKP_SCORE",
    "Power_Delta",
}

# Keys that should be coerced to float
_FLOAT_KEYS = {
    "% of Kill Target",
    "% of Dead Target",
    "% of DKP Target",
}

# Keys that should be coerced to str
_STR_KEYS = {
    "GovernorName",
    "LAST_REFRESH",
    "STATUS",
    "Civilization",
}


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


def _norm_name(s: Any) -> str:
    """Normalize a column name for tolerant matching: keep only alphanumeric (lowercased)."""
    if s is None:
        return ""
    s = str(s)
    return "".join(ch.lower() for ch in s if ch.isalnum())


def _build_lookup_from_cols(cols: list[str]) -> dict[str, str]:
    """
    Return a mapping from normalized source-column-name -> actual column name.
    Later lookups will search using normalized candidate names.
    """
    lookup: dict[str, str] = {}
    for c in cols:
        key = _norm_name(c)
        # keep first occurrence if duplicates normalize to same key
        if key not in lookup:
            lookup[key] = c
    return lookup


def _find_first_col(lookup: dict[str, str], candidates: list[str]) -> str | None:
    """
    Given the normalized lookup and a list of candidate names, return the
    first matching actual column name or None.
    """
    for cand in candidates:
        k = _norm_name(cand)
        if k in lookup:
            return lookup[k]
    return None


def _execute_sp_with_retries(
    cn: pyodbc.Connection,
    *,
    retries: int = 3,
    base_backoff: float = 2.0,
    max_backoff: float = 10.0,
) -> None:
    """
    Execute SP_Stats_for_Upload with retry logic and explicit transaction management.

    Args:
        cn: Active database connection
        retries: Number of retry attempts
        base_backoff: Base delay in seconds for exponential backoff
        max_backoff: Maximum delay in seconds
    """
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            logger.info(
                "[CACHE] Executing SP_Stats_for_Upload (attempt %d/%d) with timeout=%ds...",
                attempt,
                retries,
                _SP_EXECUTION_TIMEOUT,
            )

            sp_start = time.perf_counter()
            cur = cn.cursor()

            # Set query timeout
            cur.execute(f"SET LOCK_TIMEOUT {_SP_EXECUTION_TIMEOUT * 1000};")  # milliseconds

            # Execute stored procedure
            cur.execute(_SQL_EXEC_SP)

            # Explicitly commit the transaction
            cn.commit()

            sp_duration = time.perf_counter() - sp_start
            logger.info(
                "[CACHE] ✅ SP_Stats_for_Upload completed successfully in %.2fs",
                sp_duration,
            )

            # Close cursor
            cur.close()

            return

        except pyodbc.Error as e:
            last_exc = e
            sqlstate = getattr(e, "args", [None])[0] if e.args else None

            logger.warning(
                "[CACHE] SP_Stats_for_Upload failed (attempt %d/%d): SQLSTATE=%s, Error=%s",
                attempt,
                retries,
                sqlstate,
                e,
            )

            # Rollback on error
            try:
                cn.rollback()
            except Exception as rollback_err:
                logger.warning("[CACHE] Rollback failed: %s", rollback_err)

            if attempt >= retries:
                break

            # Exponential backoff with jitter
            cap = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
            delay = random.uniform(cap * 0.5, cap)
            logger.info("[CACHE] Retrying SP execution in %.2fs...", delay)
            time.sleep(delay)

        except Exception as e:
            last_exc = e
            logger.exception("[CACHE] Unexpected error executing SP_Stats_for_Upload: %s", e)

            try:
                cn.rollback()
            except Exception:
                pass

            if attempt >= retries:
                break

            cap = min(max_backoff, base_backoff * (2 ** (attempt - 1)))
            delay = random.uniform(cap * 0.5, cap)
            time.sleep(delay)

    # If we get here, all retries failed
    assert last_exc is not None
    logger.error("[CACHE] ❌ SP_Stats_for_Upload failed after %d attempts", retries)
    raise last_exc


# =========================
# Mapping functions
# =========================
def _map_row(row: pyodbc.Row, cols: list[str]) -> dict[str, Any] | None:
    # Canonical normalizer from utils (keeps inclusion/exclusion consistent across builder+loader)
    from utils import normalize_governor_id

    # preserve previous direct-access pattern but use the lookup helpers
    d = {c: row[i] for i, c in enumerate(cols)}
    lookup = _build_lookup_from_cols(cols)

    # determine governor id from common variants
    gov_col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get("GovernorID", []))
    raw_gov = d.get(gov_col) if gov_col else None
    gov_id = normalize_governor_id(raw_gov or "")

    # Preserve previous exclusion logic exactly
    if not gov_id or gov_id == "0":
        return None

    def gi(canonical: str) -> int:
        col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get(canonical, []))
        return _to_int(d.get(col, 0)) if col else 0

    def gf(canonical: str) -> float:
        col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get(canonical, []))
        return round(_to_float(d.get(col, 0.0)), 2) if col else 0.0

    def gs(canonical: str) -> str:
        col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get(canonical, []))
        return _to_str(d.get(col, "")) if col else ""

    # Build canonical mapped payload: include every source column from the provided extract.
    # Keys use the source-like column names (underscores where source uses them) so the cache
    # precisely reflects the STATS_FOR_UPLOAD columns.
    mapped = {
        "GovernorID": gov_id,
        "GovernorName": (gs("GovernorName") or gs("Governor_Name") or "").strip(),
        "Rank": gi("Rank"),
        "KVK_RANK": gi("KVK_RANK"),
        "Starting Power": gi("Starting Power"),
        "Power_Delta": gi("Power_Delta"),
        "Civilization": gs("Civilization"),
        "KvKPlayed": gi("KvKPlayed"),
        "MostKvKKill": gi("MostKvKKill"),
        "MostKvKDead": gi("MostKvKDead"),
        "MostKvKHeal": gi("MostKvKHeal"),
        "Acclaim": gi("Acclaim"),
        "HighestAcclaim": gi("HighestAcclaim"),
        "AOOJoined": gi("AOOJoined"),
        "AOOWon": gi("AOOWon"),
        "AOOAvgKill": gi("AOOAvgKill"),
        "AOOAvgDead": gi("AOOAvgDead"),
        "AOOAvgHeal": gi("AOOAvgHeal"),
        "Starting_T4&T5_KILLS": gi("Starting_T4&T5_KILLS"),
        "T4_KILLS": gi("T4_KILLS"),
        "T5_KILLS": gi("T5_KILLS"),
        "T4&T5_Kills": gi("T4&T5_Kills"),
        "KILLS_OUTSIDE_KVK": gi("KILLS_OUTSIDE_KVK"),
        "Kill Target": gi("Kill Target"),
        "% of Kill Target": gf("% of Kill Target"),
        "Starting_Deads": gi("Starting_Deads"),
        "Deads_Delta": gi("Deads_Delta"),
        "DEADS_OUTSIDE_KVK": gi("DEADS_OUTSIDE_KVK"),
        "T4_Deads": gi("T4_Deads"),
        "T5_Deads": gi("T5_Deads"),
        "Dead_Target": gi("Dead_Target"),
        "% of Dead Target": gf("% of Dead Target"),
        "Zeroed": gi("Zeroed"),
        "DKP_SCORE": gi("DKP_SCORE"),
        "DKP_Target": gi("DKP_Target"),
        "% of DKP Target": gf("% of DKP Target"),
        "HelpsDelta": gi("HelpsDelta"),
        "RSS_Assist_Delta": gi("RSS_Assist_Delta"),
        "RSS_Gathered_Delta": gi("RSS_Gathered_Delta"),
        "Pass 4 Kills": gi("Pass 4 Kills"),
        "Pass 6 Kills": gi("Pass 6 Kills"),
        "Pass 7 Kills": gi("Pass 7 Kills"),
        "Pass 8 Kills": gi("Pass 8 Kills"),
        "Pass 4 Deads": gi("Pass 4 Deads"),
        "Pass 6 Deads": gi("Pass 6 Deads"),
        "Pass 7 Deads": gi("Pass 7 Deads"),
        "Pass 8 Deads": gi("Pass 8 Deads"),
        "Starting_HealedTroops": gi("Starting_HealedTroops"),
        "HealedTroopsDelta": gi("HealedTroopsDelta"),
        "Starting_KillPoints": gi("Starting_KillPoints"),
        "KillPointsDelta": gi("KillPointsDelta"),
        "RangedPoints": gi("RangedPoints"),
        "RangedPointsDelta": gi("RangedPointsDelta"),
        "AutarchTimes": gi("AutarchTimes"),
        "Max_PreKvk_Points": gi("Max_PreKvk_Points"),
        "Max_HonorPoints": gi("Max_HonorPoints"),
        "PreKvk_Rank": gi("PreKvk_Rank"),
        "Honor_Rank": gi("Honor_Rank"),
        "KVK_NO": gi("KVK_NO"),
        "LAST_REFRESH": gs("LAST_REFRESH"),
        "STATUS": (gs("STATUS") or "INCLUDED"),
    }

    return mapped


def _map_excel_row(
    row: pyodbc.Row, cols: list[str], kvk_no: int | None = None
) -> dict[str, Any] | None:
    """
    Map rows from EXCEL_FOR_KVK_{N} tables into the same normalized shape used in the primary cache.
    This mirrors _map_row but prefers the explicit kvk_no when provided.
    """
    from utils import normalize_governor_id

    d = {c: row[i] for i, c in enumerate(cols)}
    lookup = _build_lookup_from_cols(cols)

    gov_col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get("GovernorID", []))
    raw_gov = d.get(gov_col) if gov_col else None
    gov_id = normalize_governor_id(raw_gov or "")

    if not gov_id or gov_id == "0":
        return None

    def gi(canonical: str) -> int:
        col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get(canonical, []))
        return _to_int(d.get(col, 0)) if col else 0

    def gf(canonical: str) -> float:
        col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get(canonical, []))
        return round(_to_float(d.get(col, 0.0)), 2) if col else 0.0

    def gs(canonical: str) -> str:
        col = _find_first_col(lookup, _CANONICAL_FIELD_CANDIDATES.get(canonical, []))
        return _to_str(d.get(col, "")) if col else ""

    mapped = {
        "GovernorID": gov_id,
        "GovernorName": (gs("GovernorName") or gs("Governor_Name") or "").strip(),
        "Rank": gi("Rank"),
        "KVK_RANK": gi("KVK_RANK"),
        "Starting Power": gi("Starting Power"),
        "Power_Delta": gi("Power_Delta"),
        "Civilization": gs("Civilization"),
        "KvKPlayed": gi("KvKPlayed"),
        "MostKvKKill": gi("MostKvKKill"),
        "MostKvKDead": gi("MostKvKDead"),
        "MostKvKHeal": gi("MostKvKHeal"),
        "Acclaim": gi("Acclaim"),
        "HighestAcclaim": gi("HighestAcclaim"),
        "AOOJoined": gi("AOOJoined"),
        "AOOWon": gi("AOOWon"),
        "AOOAvgKill": gi("AOOAvgKill"),
        "AOOAvgDead": gi("AOOAvgDead"),
        "AOOAvgHeal": gi("AOOAvgHeal"),
        "Starting_T4&T5_KILLS": gi("Starting_T4&T5_KILLS"),
        "T4_KILLS": gi("T4_KILLS"),
        "T5_KILLS": gi("T5_KILLS"),
        "T4&T5_Kills": gi("T4&T5_Kills"),
        "KILLS_OUTSIDE_KVK": gi("KILLS_OUTSIDE_KVK"),
        "Kill Target": gi("Kill Target"),
        "% of Kill Target": gf("% of Kill Target"),
        "Starting_Deads": gi("Starting_Deads"),
        "Deads_Delta": gi("Deads_Delta"),
        "DEADS_OUTSIDE_KVK": gi("DEADS_OUTSIDE_KVK"),
        "T4_Deads": gi("T4_Deads"),
        "T5_Deads": gi("T5_Deads"),
        "Dead_Target": gi("Dead_Target"),
        "% of Dead Target": gf("% of Dead Target"),
        "Zeroed": gi("Zeroed"),
        "DKP_SCORE": gi("DKP_SCORE"),
        "DKP_Target": gi("DKP_Target"),
        "% of DKP Target": gf("% of DKP Target"),
        "HelpsDelta": gi("HelpsDelta"),
        "RSS_Assist_Delta": gi("RSS_Assist_Delta"),
        "RSS_Gathered_Delta": gi("RSS_Gathered_Delta"),
        "Pass 4 Kills": gi("Pass 4 Kills"),
        "Pass 6 Kills": gi("Pass 6 Kills"),
        "Pass 7 Kills": gi("Pass 7 Kills"),
        "Pass 8 Kills": gi("Pass 8 Kills"),
        "Pass 4 Deads": gi("Pass 4 Deads"),
        "Pass 6 Deads": gi("Pass 6 Deads"),
        "Pass 7 Deads": gi("Pass 7 Deads"),
        "Pass 8 Deads": gi("Pass 8 Deads"),
        "Starting_HealedTroops": gi("Starting_HealedTroops"),
        "HealedTroopsDelta": gi("HealedTroopsDelta"),
        "Starting_KillPoints": gi("Starting_KillPoints"),
        "KillPointsDelta": gi("KillPointsDelta"),
        "RangedPoints": gi("RangedPoints"),
        "RangedPointsDelta": gi("RangedPointsDelta"),
        "AutarchTimes": gi("AutarchTimes"),
        "Max_PreKvk_Points": gi("Max_PreKvk_Points"),
        "Max_HonorPoints": gi("Max_HonorPoints"),
        "PreKvk_Rank": gi("PreKvk_Rank"),
        "Honor_Rank": gi("Honor_Rank"),
        "KVK_NO": kvk_no if kvk_no is not None else gi("KVK_NO"),
        "LAST_REFRESH": gs("LAST_REFRESH"),
        "STATUS": (gs("STATUS") or "INCLUDED"),
    }

    return mapped


def _build_cache_sync() -> dict[str, Any]:
    """
    Build in-memory dict for cache payload.
    Uses centralized DB connection retries via file_utils.get_conn_with_retries().

    NEW: Executes SP_Stats_for_Upload BEFORE reading to ensure fresh data.
    """
    from file_utils import get_conn_with_retries
    from utils import score_player_stats_rec

    _warn_legacy_db_envs_once()

    output: dict[str, Any] = {}

    # Standardized DB_* env vars are honored inside get_conn_with_retries()
    with get_conn_with_retries(meta={"operation": "player_stats_cache"}) as cn:
        # NEW: Execute stored procedure to refresh STATS_FOR_UPLOAD table
        if _REFRESH_BEFORE_BUILD:
            try:
                _execute_sp_with_retries(cn)
            except Exception as e:
                logger.error(
                    "[CACHE] Failed to execute SP_Stats_for_Upload: %s. Proceeding with existing data.",
                    e,
                )
                # Don't fail the entire cache build if SP fails - use existing data
        else:
            logger.info("[CACHE] Skipping SP execution (PLAYER_STATS_REFRESH_BEFORE_BUILD=false)")

        # Read from STATS_FOR_UPLOAD table
        logger.info("[CACHE] Reading from STATS_FOR_UPLOAD table...")
        read_start = time.perf_counter()

        cur = cn.cursor()
        cur.execute(_SQL_SELECT)
        cols = [c[0] for c in cur.description]

        row_count = 0
        batch_count = 0

        while True:
            rows = cur.fetchmany(1000)
            if not rows:
                break

            batch_count += 1
            for r in rows:
                row_count += 1
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

        read_duration = time.perf_counter() - read_start
        logger.info(
            "[CACHE] Read %d rows in %d batches (%.2fs, %.0f rows/sec)",
            row_count,
            batch_count,
            read_duration,
            row_count / read_duration if read_duration > 0 else 0,
        )

    output["_meta"] = {
        "source": "SQL:dbo.STATS_FOR_UPLOAD",
        "generated_at": _utc_now_iso(),
        "count": len([k for k in output.keys() if k != "_meta"]),
        "sp_executed": _REFRESH_BEFORE_BUILD,
    }

    return output


def _build_last_kvk_cache_sync() -> dict[str, Any] | None:
    """
    Build and persist a separate cache containing the last finished KVK snapshot.
    Naming assumption: per-KVK tables follow the pattern ROK_TRACKER.dbo.[EXCEL_FOR_KVK_{N}].
    We determine the last finished KVK as MAX(KVK_NO) - 1 (from STATS_FOR_UPLOAD), then read
    the corresponding EXCEL_FOR_KVK_{N} table if it exists.

    The resulting last-KVK cache will contain the same keys as the main cache but with
    KVK_NO set to the last_kvk_no and values populated from the per-KVK EXCEL table.
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
    from file_utils import acquire_lock, emit_telemetry_event

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
            "sp_executed": _REFRESH_BEFORE_BUILD,
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
