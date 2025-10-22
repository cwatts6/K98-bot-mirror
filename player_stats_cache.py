# player_stats_cache.py
from __future__ import annotations

import asyncio
from datetime import date, datetime
import json
import logging
import os
import time
from typing import Any

import pyodbc

from constants import PLAYER_STATS_CACHE, _conn

logger = logging.getLogger(__name__)

# =========================
# Configurable retry params (via env)
# =========================
_DB_RETRIES = int(os.getenv("PLAYER_STATS_DB_RETRIES", "5"))
_DB_BACKOFF_BASE = float(os.getenv("PLAYER_STATS_DB_BACKOFF", "1.0"))

# =========================
# SQL
# =========================
_SQL = "SELECT * FROM dbo.[STATS_FOR_UPLOAD]"  # spelled as provided


# =========================
# helpers
# =========================
def _get_conn_with_retries():
    """
    Get a DB connection with retry logic and exponential backoff.
    Retries on pyodbc.OperationalError with configurable attempts and backoff.
    """
    attempt = 0
    backoff = _DB_BACKOFF_BASE
    last_exc = None
    while attempt < _DB_RETRIES:
        attempt += 1
        try:
            logger.debug("Attempting DB connection (attempt %d/%d)", attempt, _DB_RETRIES)
            return _conn()
        except pyodbc.OperationalError as e:
            last_exc = e
            logger.warning(
                "DB connection attempt %d/%d failed: %s. Retrying in %.1fs",
                attempt,
                _DB_RETRIES,
                e,
                backoff,
            )
            if attempt >= _DB_RETRIES:
                break
            time.sleep(backoff)
            backoff *= 2
        except Exception as e:
            # Non-operational error — log and re-raise
            logger.exception("Unexpected exception while connecting to DB: %s", e)
            raise

    logger.error("All %d DB connection attempts failed. Last exception: %s", _DB_RETRIES, last_exc)
    if last_exc:
        raise last_exc
    raise pyodbc.OperationalError("Unknown DB connection failure")


# =========================
# Coercion + ID normalization
# =========================
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


def _normalize_governor_id(v: Any) -> str:
    """
    Canonical, integer-like string ID with no decimals/whitespace.
    Handles '856126', '856126.0', 856126, 856126.0, etc.
    """
    s = _to_str(v).strip()
    if not s or s.lower() == "nan":
        return ""
    try:
        return str(int(float(s)))
    except Exception:
        return s  # if it was some non-numeric key already


# =========================
# Row → dict mapper
# (Keep keys EXACTLY as the JSON schema your embeds use)
# =========================
def _map_row(row: pyodbc.Row, cols: list[str]) -> dict[str, Any] | None:
    # make a name→value dict for convenience
    d = {c: row[i] for i, c in enumerate(cols)}

    # Accept either "Governor ID" or "GovernorID" from SQL/view
    gov_id = _normalize_governor_id(d.get("Governor ID", d.get("GovernorID", "")))
    if not gov_id or gov_id == "0":
        return None

    # helpers
    def gi(key: str) -> int:
        return _to_int(d.get(key, 0))

    def gf(key: str) -> float:
        return round(_to_float(d.get(key, 0.0)), 2)

    def gs(key: str) -> str:
        return _to_str(d.get(key, ""))

    # Build the output with the SAME keys your bot expects
    return {
        "GovernorID": gov_id,
        # Accept either "Governor_Name" or "Governor Name" as source
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
        # FIX: correct source key includes the space
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


# =========================
# Core builder
# =========================
def _build_cache_sync() -> dict[str, Any]:
    output: dict[str, Any] = {}
    with _get_conn_with_retries() as cn:
        cur = cn.cursor()
        cur.execute(_SQL)
        cols = [c[0] for c in cur.description]

        # Stream rows to keep memory modest
        while True:
            rows = cur.fetchmany(1000)
            if not rows:
                break
            for r in rows:
                mapped = _map_row(r, cols)
                if not mapped:
                    continue
                gid = mapped["GovernorID"]
                # If there are duplicates, prefer INCLUDED or later LAST_REFRESH
                if gid in output:
                    existing = output[gid]

                    def score(rec: dict[str, Any]):
                        inc = 1 if rec.get("STATUS") == "INCLUDED" else 0
                        date = str(rec.get("LAST_REFRESH") or "")
                        return (inc, date)

                    if score(mapped) > score(existing):
                        output[gid] = mapped
                else:
                    output[gid] = mapped

    # Add a metadata block (non-breaking)
    output["_meta"] = {
        "source": "SQL:dbo.STATS_FOR_UPLOAD",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len([k for k in output.keys() if k != "_meta"]),
    }
    return output


async def build_player_stats_cache():
    """
    Async wrapper that runs the blocking SQL read & JSON write off the event loop.
    Includes exception handling and fallback logic to preserve existing cache on failure.
    """
    try:
        output = await asyncio.to_thread(_build_cache_sync)

        os.makedirs(os.path.dirname(PLAYER_STATS_CACHE) or ".", exist_ok=True)
        # Pretty JSON for diffs; switch to separators=(",", ":") for smaller file
        with open(PLAYER_STATS_CACHE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"[CACHE] ✅ player_stats_cache.json written with {output['_meta']['count']} entries.")
    except Exception as e:
        logger.error("Failed to build player stats cache: %s", e, exc_info=True)
        
        # If cache exists, preserve it
        if os.path.exists(PLAYER_STATS_CACHE):
            logger.warning(
                "Preserving existing cache file at %s due to SQL failure",
                PLAYER_STATS_CACHE
            )
            print(f"[CACHE] ⚠️  Preserved existing cache due to error: {e}")
        else:
            # Write minimal error-indicating JSON
            os.makedirs(os.path.dirname(PLAYER_STATS_CACHE) or ".", exist_ok=True)
            error_cache = {
                "_meta": {
                    "source": "SQL:dbo.STATS_FOR_UPLOAD",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "count": 0,
                    "error": f"SQL connection failed: {str(e)}",
                }
            }
            with open(PLAYER_STATS_CACHE, "w", encoding="utf-8") as f:
                json.dump(error_cache, f, indent=2, ensure_ascii=False)
            logger.warning("Wrote minimal error cache to %s", PLAYER_STATS_CACHE)
            print(f"[CACHE] ⚠️  Wrote error cache: {e}")


# Optional: run manually: `python player_stats_cache.py`
if __name__ == "__main__":
    asyncio.run(build_player_stats_cache())
