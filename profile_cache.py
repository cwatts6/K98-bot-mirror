# profile_cache.py (updated - PR 4 adjustments)
# - Uses centralized utils.json_default for JSON serialization
# - Passes json_default into atomic_write_json so atomic path and fallback behave the same
# - Keeps PR1 (connection handling), PR2 (locking/immutability), PR3 (generated_at normalization) changes
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


# Central constants (PLAYER_PROFILE_CACHE should be defined in constants.py)
from constants import DATA_DIR, PLAYER_PROFILE_CACHE as CONST_PLAYER_PROFILE_CACHE, _conn

# Optional fuzzy deps
try:
    from rapidfuzz import fuzz  # type: ignore

    HAVE_RAPIDFUZZ = True
except Exception:
    HAVE_RAPIDFUZZ = False
try:
    from unidecode import unidecode  # type: ignore
except Exception:

    def unidecode(s: str) -> str:  # graceful fallback
        return s


# Default to constants value (ensures consistent location)
PLAYER_PROFILE_CACHE = (
    CONST_PLAYER_PROFILE_CACHE
    if CONST_PLAYER_PROFILE_CACHE
    else os.path.join(DATA_DIR, "player_profile_cache.json")
)
CACHE_TTL_SECS = 15 * 60  # 15 min

_cache_lock = threading.Lock()
_cache: dict[str, Any] = {}
_cache_loaded_at: float = 0.0


# -------------------- Helpers --------------------
def _parse_generated_at(raw: Any) -> float:
    """
    Parse generated_at from disk into epoch seconds (float).
    Accepts:
    - float/int timestamps (seconds since epoch)
    - ISO 8601 string (UTC-aware or naive ISO produced by utcnow().isoformat())
    - None/unknown -> returns 0.0
    """
    if raw is None:
        return 0.0
    # numeric
    try:
        # cover strings that are numeric too
        return float(raw)
    except Exception:
        pass

    # try ISO parse via utils
    try:
        from utils import parse_isoformat_utc

        dt = parse_isoformat_utc(str(raw))
        return dt.timestamp()
    except Exception:
        # Last resort: return 0
        return 0.0


def get_cache_stats() -> dict[str, Any]:
    """
    Return lightweight, thread-safe stats about the in-memory cache.
    Useful for health checks and diagnostics. Does not expose internal objects.
    """
    with _cache_lock:
        count = len(_cache) if _cache else 0
        loaded_at = _cache_loaded_at
    # convert loaded_at to ISO if present
    try:
        if loaded_at:
            loaded_iso = datetime.utcfromtimestamp(loaded_at).isoformat() + "Z"
        else:
            loaded_iso = None
    except Exception:
        loaded_iso = None
    return {"count": count, "loaded_at_epoch": loaded_at, "loaded_at_iso": loaded_iso}


# -------------------- DB helpers --------------------
def _connect():
    """
    Return a pyodbc.Connection using our centralized retry helper when available.

    - Prefer file_utils.get_conn_with_retries if present; falls back to constants._conn().
    """
    try:
        # lazy import to avoid circulars
        from file_utils import get_conn_with_retries

        return get_conn_with_retries()
    except Exception:
        # fallback: use constants._conn (may raise)
        logger.debug(
            "file_utils.get_conn_with_retries not available; falling back to constants._conn()"
        )
        return _conn()


def _rowdicts(cursor, rows):
    """Convert pyodbc rows to list[dict] using cursor.description."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _to_int(v):
    try:
        return int(v) if v is not None else None
    except Exception:
        try:
            return int(float(v)) if v is not None else None
        except Exception:
            return None


def _to_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


# If you might have numpy types; leave import optional
try:
    import numpy as np  # type: ignore
except Exception:
    np = None


def _safe_utc(dt):
    """
    Defensive wrapper: if dt is a datetime, try to make it aware UTC using utils.ensure_aware_utc.
    If conversion fails or dt is falsy, return it unchanged (None or original).
    """
    if not dt:
        return dt
    try:
        # lazy import
        from utils import ensure_aware_utc

        if isinstance(dt, datetime):
            return ensure_aware_utc(dt)
    except Exception:
        # If utils can't be imported or conversion fails, return original
        pass
    return dt


def build_full_cache() -> dict[str, Any]:
    """
    Load v_PlayerProfile and (optionally) v_PlayerKVK_Last3; write JSON to disk.
    Returns the in-memory dict in the same shape.

    Note: Writes atomically using file_utils.atomic_write_json. Raises exceptions on DB errors
    so callers can decide whether to preserve an on-disk cache.
    """
    out: dict[str, Any] = {}

    start_ts = time.perf_counter()
    logger.info(
        "[CACHE] Starting DB build of player profile cache: writing to %s", PLAYER_PROFILE_CACHE
    )

    conn = None
    cur = None
    try:
        conn = _connect()
        # If the returned connection is a context-manager wrapper, prefer using it
        if hasattr(conn, "__enter__") and hasattr(conn, "__exit__"):
            # Use as context manager to allow wrappers to manage lifecycle
            with conn as c:
                cur = c.cursor()
                # v_PlayerProfile is the one-stop view we joined earlier
                cur.execute("SELECT * FROM dbo.v_PlayerProfile WITH (NOLOCK)")
                rows = cur.fetchall()
                for row in _rowdicts(cur, rows):
                    gid = _to_int(row.get("GovernorID"))
                    if gid is None:
                        continue

                    # Handle City Hall column naming (alias or with space)
                    ch_val = row.get("CityHallLevel", row.get("City Hall"))

                    # Defensive timestamp conversions
                    forts_updated = _safe_utc(row.get("FortsUpdated"))
                    location_updated = _safe_utc(row.get("LocationUpdated"))
                    status_updated = _safe_utc(row.get("StatusUpdated"))

                    out[str(gid)] = {
                        "GovernorID": gid,
                        "GovernorName": (row.get("Governor_Name") or "").strip(),
                        "Alliance": (row.get("Alliance") or "").strip(),
                        "CityHallLevel": _to_int(ch_val),
                        "Power": _to_int(row.get("Power")),
                        "Kills": _to_int(row.get("Kills")),
                        "Deads": _to_int(row.get("Deads")),
                        "RSS_Gathered": _to_int(row.get("RSS_Gathered")),
                        "Helps": _to_int(row.get("Helps")),
                        "X": _to_int(row.get("X")),
                        "Y": _to_int(row.get("Y")),
                        "Status": row.get("Status"),
                        "FortsRank": _to_int(row.get("FortsRank")),
                        "FortsStarted": _to_int(row.get("FortsStarted")),
                        "FortsJoined": _to_int(row.get("FortsJoined")),
                        "FortsTotal": _to_int(row.get("FortsTotal")),
                        # Timestamp fields
                        "FortsUpdated": forts_updated,
                        "LocationUpdated": location_updated,
                        "StatusUpdated": status_updated,
                        # NEW — pulled directly from v_PlayerProfile after your SQL change
                        "PowerRank": _to_int(row.get("PowerRank")),
                    }

                # --- NEW: enrich with first/last scan and offline >30d ---
                try:
                    cur.execute(
                        "SELECT GovernorID, FirstScanDate, LastScanDate, OfflineDaysOver30 FROM dbo.v_PlayerScanMeta WITH (NOLOCK)"
                    )
                    for r in _rowdicts(cur, cur.fetchall()):
                        gid = str(_to_int(r.get("GovernorID")))
                        if gid in out:
                            out_gid = out[gid]
                            out_gid["FirstScanDate"] = _safe_utc(r.get("FirstScanDate"))
                            out_gid["LastScanDate"] = _safe_utc(r.get("LastScanDate"))
                            out_gid["OfflineDaysOver30"] = _to_int(r.get("OfflineDaysOver30")) or 0
                except Exception:
                    # If the view isn’t present, we just skip; embed will omit the line gracefully
                    logger.debug(
                        "[CACHE] v_PlayerScanMeta not present or query failed; skipping enrichment",
                        exc_info=True,
                    )

                # Optional KVK view — skip gracefully if it doesn't exist
                try:
                    cur.execute(
                        "SELECT GovernorID, KVK_NUMBER, KVK_KILL_RANK, KillPercent FROM dbo.v_PlayerKVK_Last3 WITH (NOLOCK)"
                    )
                    kvkrows = cur.fetchall()
                    for rr in _rowdicts(cur, kvkrows):
                        gid = str(_to_int(rr.get("GovernorID")))
                        if gid == "None":
                            continue
                        out.setdefault(gid, {}).setdefault("KVK", []).append(
                            {
                                "KVK": _to_int(rr.get("KVK_NUMBER")),
                                "Rank": _to_int(rr.get("KVK_KILL_RANK")),
                                "Percent": _to_float(rr.get("KillPercent")),
                            }
                        )
                except Exception:
                    logger.debug(
                        "[CACHE] v_PlayerKVK_Last3 not present or query failed; skipping KVK enrichment",
                        exc_info=True,
                    )
        else:
            # Plain connection object: manage cursor and close the connection manually
            cur = conn.cursor()
            cur.execute("SELECT * FROM dbo.v_PlayerProfile WITH (NOLOCK)")
            rows = cur.fetchall()
            for row in _rowdicts(cur, rows):
                gid = _to_int(row.get("GovernorID"))
                if gid is None:
                    continue

                ch_val = row.get("CityHallLevel", row.get("City Hall"))
                forts_updated = _safe_utc(row.get("FortsUpdated"))
                location_updated = _safe_utc(row.get("LocationUpdated"))
                status_updated = _safe_utc(row.get("StatusUpdated"))

                out[str(gid)] = {
                    "GovernorID": gid,
                    "GovernorName": (row.get("Governor_Name") or "").strip(),
                    "Alliance": (row.get("Alliance") or "").strip(),
                    "CityHallLevel": _to_int(ch_val),
                    "Power": _to_int(row.get("Power")),
                    "Kills": _to_int(row.get("Kills")),
                    "Deads": _to_int(row.get("Deads")),
                    "RSS_Gathered": _to_int(row.get("RSS_Gathered")),
                    "Helps": _to_int(row.get("Helps")),
                    "X": _to_int(row.get("X")),
                    "Y": _to_int(row.get("Y")),
                    "Status": row.get("Status"),
                    "FortsRank": _to_int(row.get("FortsRank")),
                    "FortsStarted": _to_int(row.get("FortsStarted")),
                    "FortsJoined": _to_int(row.get("FortsJoined")),
                    "FortsTotal": _to_int(row.get("FortsTotal")),
                    # Timestamp fields
                    "FortsUpdated": forts_updated,
                    "LocationUpdated": location_updated,
                    "StatusUpdated": status_updated,
                    # NEW — pulled directly from v_PlayerProfile after your SQL change
                    "PowerRank": _to_int(row.get("PowerRank")),
                }

            # --- NEW: enrich with first/last scan and offline >30d ---
            try:
                cur.execute(
                    "SELECT GovernorID, FirstScanDate, LastScanDate, OfflineDaysOver30 FROM dbo.v_PlayerScanMeta WITH (NOLOCK)"
                )
                for r in _rowdicts(cur, cur.fetchall()):
                    gid = str(_to_int(r.get("GovernorID")))
                    if gid in out:
                        out_gid = out[gid]
                        out_gid["FirstScanDate"] = _safe_utc(r.get("FirstScanDate"))
                        out_gid["LastScanDate"] = _safe_utc(r.get("LastScanDate"))
                        out_gid["OfflineDaysOver30"] = _to_int(r.get("OfflineDaysOver30")) or 0
            except Exception:
                logger.debug(
                    "[CACHE] v_PlayerScanMeta not present or query failed; skipping enrichment",
                    exc_info=True,
                )

            # Optional KVK view — skip gracefully if it doesn't exist
            try:
                cur.execute(
                    "SELECT GovernorID, KVK_NUMBER, KVK_KILL_RANK, KillPercent FROM dbo.v_PlayerKVK_Last3 WITH (NOLOCK)"
                )
                kvkrows = cur.fetchall()
                for rr in _rowdicts(cur, kvkrows):
                    gid = str(_to_int(rr.get("GovernorID")))
                    if gid == "None":
                        continue
                    out.setdefault(gid, {}).setdefault("KVK", []).append(
                        {
                            "KVK": _to_int(rr.get("KVK_NUMBER")),
                            "Rank": _to_int(rr.get("KVK_KILL_RANK")),
                            "Percent": _to_float(rr.get("KillPercent")),
                        }
                    )
            except Exception:
                logger.debug(
                    "[CACHE] v_PlayerKVK_Last3 not present or query failed; skipping KVK enrichment",
                    exc_info=True,
                )

    finally:
        # Close cursor first if present
        try:
            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            pass
        # Then close connection (if it's a plain connection)
        try:
            if conn is not None and not (hasattr(conn, "__enter__") and hasattr(conn, "__exit__")):
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception:
            pass

    # Sort KVK slices by KVK desc for each player
    for v in out.values():
        if "KVK" in v and isinstance(v["KVK"], list):
            v["KVK"].sort(key=lambda x: x.get("KVK") or 0, reverse=True)

    # Persist to disk using atomic write and timezone-aware generated_at
    try:
        # lazy import to avoid circulars
        from file_utils import atomic_write_json
        from utils import json_default, utcnow

        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(PLAYER_PROFILE_CACHE) or ".", exist_ok=True)
        except Exception:
            pass

        payload = {"generated_at": utcnow().isoformat(), "players": out}
        # pass json_default so datetimes/Decimals etc. serialize in the atomic path too
        atomic_write_json(PLAYER_PROFILE_CACHE, payload, default=json_default)
    except Exception:
        # Best-effort fallback to non-atomic write if atomic helper isn't available;
        # but don't swallow exceptions raised by DB earlier (they were already raised).
        try:
            from utils import json_default, utcnow

            with open(PLAYER_PROFILE_CACHE, "w", encoding="utf-8") as f:
                json.dump(
                    {"generated_at": utcnow().isoformat(), "players": out},
                    f,
                    default=json_default,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.exception("Failed to persist player profile cache: %s", e)

    elapsed = time.perf_counter() - start_ts
    logger.info(
        "[CACHE] Finished DB build of player profile cache: %d players in %.2fs", len(out), elapsed
    )

    return out


def warm_cache(force: bool = False):
    """Load from disk if fresh, else rebuild from SQL. Preserves on-disk cache if DB build fails."""
    global _cache, _cache_loaded_at
    with _cache_lock:
        # Fast path: recent in-memory cache valid
        if not force and _cache and (time.time() - _cache_loaded_at) < CACHE_TTL_SECS:
            logger.debug(
                "[CACHE] In-memory cache fresh; skipping warm (age=%.1fs)",
                time.time() - _cache_loaded_at,
            )
            return

        # Try to load on-disk cache if present and still fresh
        try:
            p = Path(PLAYER_PROFILE_CACHE)
            if p.exists():
                with p.open(encoding="utf-8") as f:
                    data = json.load(f)
                cached_at_raw = data.get("generated_at", 0.0)
                cached_at = _parse_generated_at(cached_at_raw)
                players = data.get("players", {})
                age = time.time() - cached_at if cached_at else float("inf")
                logger.debug(
                    "[CACHE] Disk cache found: %s (age=%.1fs, players=%d)",
                    PLAYER_PROFILE_CACHE,
                    age,
                    len(players) if players else 0,
                )
                if cached_at and (time.time() - cached_at) < CACHE_TTL_SECS and players:
                    _cache = players
                    _cache_loaded_at = cached_at
                    logger.info(
                        "[CACHE] Loaded player profile cache from disk (age=%.1fs, count=%d)",
                        age,
                        len(players),
                    )
                    return
            else:
                logger.debug("[CACHE] No on-disk cache at %s", PLAYER_PROFILE_CACHE)
        except Exception:
            # Missing or invalid on-disk cache — we'll attempt to build
            logger.debug(
                "[CACHE] Failed to read disk cache (will attempt DB rebuild)", exc_info=True
            )

        # Build fresh from SQL, but be defensive: preserve on-disk cache if the build fails
        try:
            # Note: build_full_cache may raise; we let that propagate to the except block below.
            new_cache = build_full_cache()
            # mark loaded_at to now (use UTC epoch)
            try:
                from utils import utcnow

                _cache_loaded_at = utcnow().timestamp()
            except Exception:
                _cache_loaded_at = time.time()
            _cache = new_cache
            logger.info("[CACHE] In-memory cache rebuilt from DB (count=%d)", len(_cache))
        except Exception as e:
            logger.exception("Failed to build fresh player profile cache from DB: %s", e)
            # If we had an existing on-disk cache previously loaded above it would already be set.
            # If not, try to fall back to reading the on-disk cache now (best-effort).
            try:
                with open(PLAYER_PROFILE_CACHE, encoding="utf-8") as f:
                    data = json.load(f)
                players = data.get("players", {})
                if players:
                    _cache = players
                    # attempt to set _cache_loaded_at from generated_at similar to above
                    try:
                        _cache_loaded_at = _parse_generated_at(data.get("generated_at"))
                    except Exception:
                        _cache_loaded_at = time.time()
                    logger.warning(
                        "Using last-good on-disk player profile cache after DB failure (count=%d).",
                        len(_cache),
                    )
                    return
            except Exception:
                logger.error("No usable on-disk player profile cache found; cache is empty.")
                _cache = {}
                _cache_loaded_at = 0.0


def invalidate_one(governor_id: int):
    """Remove one entry so next warm will repopulate it (after you upsert SQL)."""
    # warm the cache first (warm_cache acquires the lock internally)
    warm_cache()
    key = str(governor_id)
    # mutate under lock to avoid races with readers/writers
    with _cache_lock:
        _cache.pop(key, None)


def get_profile_cached(governor_id: int) -> dict[str, Any] | None:
    """
    Return a deep copy of the cached profile or None.

    Note: callers MUST NOT attempt to mutate the returned dict and expect changes
    to be reflected in the global cache. To update data, write to the DB and call
    invalidate_one() or warm_cache() to refresh.
    """
    warm_cache()
    key = str(governor_id)
    with _cache_lock:
        val = _cache.get(key)
        return copy.deepcopy(val) if val is not None else None


# -------------------- Fuzzy search (cache-only) --------------------
def _normalize(s: str) -> str:
    # casefold + strip accents + trim + collapse spaces
    base = unidecode((s or "").strip().lower())
    return " ".join(base.split())


def _iter_name_entries():
    """
    Yield (display_name, gid, normalized_name) for all cached players.
    Preserves duplicates (multiple players sharing same display name).

    Implementation note: snapshot the cache under lock to avoid iterator races
    if another thread replaces or mutates the global cache.
    """
    warm_cache()
    with _cache_lock:
        snapshot = list(_cache.values())
    for v in snapshot:
        try:
            name = (v.get("GovernorName") or "").strip()
            gid_raw = v.get("GovernorID")
            # ensure governor id is an int (skip malformed entries)
            if name and gid_raw is not None:
                try:
                    gid = int(gid_raw)
                except Exception:
                    continue
                yield name, gid, _normalize(name)
        except Exception:
            # Skip malformed entries rather than propagating
            logger.debug(
                "[CACHE] Skipping malformed cache entry during name iteration", exc_info=True
            )


def search_by_governor_name(name_query: str, limit: int = 8):
    """
    Fuzzy search within the in-memory cache.
    Returns a list of (GovernorName, GovernorID, score) sorted best-first.
    Keeps duplicate names if they map to different IDs.
    """
    warm_cache()
    # Fast check: if cache empty, return quickly (guard under lock)
    with _cache_lock:
        if not _cache:
            return []

    if not name_query:
        return []

    q_norm = _normalize(name_query)

    # Quick path: numeric input treated as direct ID match preference
    try:
        q_as_id = int(name_query)
    except Exception:
        q_as_id = None

    entries = list(_iter_name_entries())
    if not entries:
        return []

    results = []

    if HAVE_RAPIDFUZZ:
        # token_sort_ratio handles swapped words; add simple prefix/substring boosts
        for disp, gid, nrm in entries:
            score = fuzz.token_sort_ratio(q_norm, nrm)
            if nrm.startswith(q_norm):
                score += 12
            elif q_norm in nrm:
                score += 6
            # Prefer exact ID if typed
            if q_as_id is not None and gid == q_as_id:
                score += 25
            results.append((disp, gid, score))
    else:
        # Fallback: substring with tiny extras
        for disp, gid, nrm in entries:
            score = 0
            if nrm.startswith(q_norm):
                score = 80
            elif q_norm in nrm:
                score = 60
            if q_as_id is not None and gid == q_as_id:
                score = max(score, 85)
            if score:
                results.append((disp, gid, score))

    # Sort and threshold
    results.sort(key=lambda t: t[2], reverse=True)
    filtered = [r for r in results if r[2] >= 50][:limit]
    return filtered  # (name, gid, score)


def autocomplete_choices(name_query: str, limit: int = 25):
    """
    Helper specifically for Discord autocomplete.
    Returns a list of (label, value) where value is **str(GovernorID)**.
    """
    matches = search_by_governor_name(name_query, limit=limit)
    out = []
    seen = set()
    for disp, gid, _score in matches:
        # Avoid returning the same (name, gid) twice if data had dupes
        key = (disp, gid)
        if key in seen:
            continue
        seen.add(key)
        out.append((f"{disp} ({gid})", str(gid)))  # label, value
    return out


# -------------------- CLI for on-demand testing --------------------
def _print_profile(d: dict[str, Any]):
    # Use fmt_short for large numbers if available (lazy import to avoid circular)
    try:
        from embed_utils import fmt_short as _fmt_short
    except Exception:

        def _fmt_short(n):
            try:
                return f"{int(n):,}"
            except Exception:
                return str(n)

    def fmt(n):
        return f"{n:,}" if isinstance(n, int) else ("—" if n in (None, "", []) else str(n))

    fields = [
        ("GovernorID", d.get("GovernorID")),
        ("GovernorName", d.get("GovernorName")),
        ("Alliance", d.get("Alliance")),
        ("CityHallLevel", d.get("CityHallLevel")),
        ("Power", _fmt_short(d.get("Power")) if d.get("Power") is not None else "—"),
        ("PowerRank", d.get("PowerRank")),  # NEW
        ("Kills", _fmt_short(d.get("Kills")) if d.get("Kills") is not None else "—"),
        ("Deads", _fmt_short(d.get("Deads")) if d.get("Deads") is not None else "—"),
        (
            "RSS_Gathered",
            _fmt_short(d.get("RSS_Gathered")) if d.get("RSS_Gathered") is not None else "—",
        ),
        ("Helps", d.get("Helps")),
        ("Location", f"X {fmt(d.get('X'))} • Y {fmt(d.get('Y'))}"),
        ("LocationUpdated", d.get("LocationUpdated")),
        ("Status", d.get("Status")),
        ("FortsRank", d.get("FortsRank")),
        ("FortsStarted", d.get("FortsStarted")),
        ("FortsJoined", d.get("FortsJoined")),
        ("FortsTotal", d.get("FortsTotal")),
        ("FirstScanDate", d.get("FirstScanDate")),  # NEW
        ("LastScanDate", d.get("LastScanDate")),  # NEW
        ("Offline>30d", d.get("OfflineDaysOver30")),  # NEW
    ]

    print("\n== Player Profile ==")
    for k, v in fields:
        print(f"{k:14}: {fmt(v) if isinstance(v, int) else (v if v not in (None, '') else '—')}")
    kvk = d.get("KVK") or []
    if kvk:
        print(
            "KVK last 3   : "
            + ", ".join(
                [f"KVK {s.get('KVK')} -> {s.get('Rank')} / {s.get('Percent')}%" for s in kvk]
            )
        )
    print()


def main():
    ap = argparse.ArgumentParser(description="Player profile JSON cache tools")
    ap.add_argument("--rebuild", action="store_true", help="Rebuild cache from SQL now")
    ap.add_argument("--id", type=int, help="Show a single governor profile by GovernorID")
    ap.add_argument("--name", type=str, help="Fuzzy search by governor name")
    ap.add_argument("--limit", type=int, default=8, help="Max results for name search")
    args = ap.parse_args()

    if args.rebuild:
        print("Rebuilding cache from SQL…")
        try:
            build_full_cache()
            print(f"Wrote: {PLAYER_PROFILE_CACHE}")
        except Exception as e:
            print(f"Failed to rebuild cache: {e}")

    warm_cache(force=bool(args.rebuild))

    if args.id:
        p = get_profile_cached(args.id)
        if not p:
            print(f"GovernorID {args.id} not found in cache.")
        else:
            _print_profile(p)

    if args.name:
        print(f"Search: {args.name!r}")
        matches = search_by_governor_name(args.name, limit=args.limit)
        if not matches:
            print("No matches.")
        else:
            for name, gid, score in matches:
                print(f"- {name} ({gid})  score={score}")


if __name__ == "__main__":
    main()
