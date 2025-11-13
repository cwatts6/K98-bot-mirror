# profile_cache.py (updated)
# - Uses centralized constants.PLAYER_PROFILE_CACHE (moved to DATA_DIR)
# - Uses file_utils.get_conn_with_retries for DB connection retry/backoff
# - Uses file_utils.atomic_write_json for atomic persistence
# - Uses utils.utcnow() for generated_at and ensure_aware_utc for converting DB timestamps
# - warm_cache is defensive: if DB build fails, it preserves last-good on-disk cache
from __future__ import annotations

import argparse
from datetime import date, datetime
from decimal import Decimal
import json
import logging
import os
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


# Central file utilities and timezone helpers (lazy import when needed)
# We'll import helpers where they are used to avoid circular imports and startup cost.

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


def _json_default(o):
    # Datetimes/dates -> ISO 8601
    if isinstance(o, (datetime, date)):
        # Use ISO 8601 string; utils.ensure_aware_utc will be used earlier where needed
        return o.isoformat()

    # Decimal -> float (or int if exact)
    if isinstance(o, Decimal):
        try:
            i = int(o)
            if Decimal(i) == o:
                return i
        except Exception:
            pass
        return float(o)

    # Sets/Tuples -> list
    if isinstance(o, (set, tuple)):
        return list(o)

    # Numpy scalars -> Python scalars
    if np is not None and isinstance(
        o, (np.integer, np.floating, np.bool_)  # type: ignore[attr-defined]
    ):
        return o.item()

    # As a last resort, stringify unknown objects
    return str(o)


# -------------------- Cache build / warm --------------------
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

    # Use our centralized connect (with retries) — will raise if ultimately fails
    with _connect() as c:
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
            pass

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
            # View missing — totally fine for now
            pass

    # Sort KVK slices by KVK desc for each player
    for v in out.values():
        if "KVK" in v and isinstance(v["KVK"], list):
            v["KVK"].sort(key=lambda x: x.get("KVK") or 0, reverse=True)

    # Persist to disk using atomic write and timezone-aware generated_at
    try:
        # lazy import to avoid circulars
        from file_utils import atomic_write_json
        from utils import utcnow

        payload = {"generated_at": utcnow().isoformat(), "players": out}
        atomic_write_json(PLAYER_PROFILE_CACHE, payload)
    except Exception:
        # Best-effort fallback to non-atomic write if atomic helper isn't available;
        # but don't swallow exceptions raised by DB earlier (they were already raised).
        try:
            with open(PLAYER_PROFILE_CACHE, "w", encoding="utf-8") as f:
                json.dump(
                    {"generated_at": time.time(), "players": out},
                    f,
                    default=_json_default,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.exception("Failed to persist player profile cache: %s", e)

    return out


def warm_cache(force: bool = False):
    """Load from disk if fresh, else rebuild from SQL. Preserves on-disk cache if DB build fails."""
    global _cache, _cache_loaded_at
    with _cache_lock:
        # Fast path: recent in-memory cache valid
        if not force and _cache and (time.time() - _cache_loaded_at) < CACHE_TTL_SECS:
            return
        # Try to load on-disk cache if present and still fresh
        try:
            with open(PLAYER_PROFILE_CACHE, encoding="utf-8") as f:
                data = json.load(f)
            cached_at_raw = data.get("generated_at", 0.0)
            # Accept either float timestamp or ISO string
            try:
                cached_at = float(cached_at_raw)
            except Exception:
                # try ISO parse -> timestamp
                try:
                    from utils import parse_isoformat_utc

                    cached_at = parse_isoformat_utc(cached_at_raw).timestamp()
                except Exception:
                    cached_at = 0.0
            players = data.get("players", {})
            if (time.time() - cached_at) < CACHE_TTL_SECS and players:
                _cache = players
                _cache_loaded_at = cached_at
                return
        except Exception:
            # Missing or invalid on-disk cache — we'll attempt to build
            pass

        # Build fresh from SQL, but be defensive: preserve on-disk cache if the build fails
        try:
            _cache = build_full_cache()
            # mark loaded_at to now (use monotonic wall clock)
            try:
                from utils import utcnow

                _cache_loaded_at = utcnow().timestamp()
            except Exception:
                _cache_loaded_at = time.time()
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
                        from utils import parse_isoformat_utc

                        _cache_loaded_at = parse_isoformat_utc(data.get("generated_at")).timestamp()
                    except Exception:
                        _cache_loaded_at = time.time()
                    logger.warning("Using last-good on-disk player profile cache after DB failure.")
                    return
            except Exception:
                logger.error("No usable on-disk player profile cache found; cache is empty.")
                _cache = {}
                _cache_loaded_at = 0.0


def invalidate_one(governor_id: int):
    """Remove one entry so next warm will repopulate it (after you upsert SQL)."""
    warm_cache()
    _cache.pop(str(governor_id), None)


def get_profile_cached(governor_id: int) -> dict[str, Any] | None:
    warm_cache()
    return _cache.get(str(governor_id))


# -------------------- Fuzzy search (cache-only) --------------------
def _normalize(s: str) -> str:
    # casefold + strip accents + trim + collapse spaces
    base = unidecode((s or "").strip().lower())
    return " ".join(base.split())


def _iter_name_entries():
    """
    Yield (display_name, gid, normalized_name) for all cached players.
    Preserves duplicates (multiple players sharing same display name).
    """
    warm_cache()
    for v in _cache.values():
        name = (v.get("GovernorName") or "").strip()
        gid = v.get("GovernorID")
        if name and gid:
            yield name, int(gid), _normalize(name)


def search_by_governor_name(name_query: str, limit: int = 8):
    """
    Fuzzy search within the in-memory cache.
    Returns a list of (GovernorName, GovernorID, score) sorted best-first.
    Keeps duplicate names if they map to different IDs.
    """
    warm_cache()
    if not name_query or not _cache:
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
