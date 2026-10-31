"""Compatibility facade for owned profile refresh and copy-on-read access."""

from __future__ import annotations

import argparse
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# Central constants (PLAYER_PROFILE_CACHE should be defined in constants.py)
from constants import DATA_DIR, PLAYER_PROFILE_CACHE as CONST_PLAYER_PROFILE_CACHE

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

from services.profile_cache_service import ProfileCacheService

_service = ProfileCacheService()


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
    return _service.stats()


def _save(path, payload):
    from file_utils import atomic_json_write
    from utils import json_default

    atomic_json_write(path, payload, default=json_default)


def refresh_result(*, force=False, fresh=False, origin="legacy"):
    from stats.profile_cache_repository import read_profiles

    return _service.refresh(
        path=PLAYER_PROFILE_CACHE,
        ttl=CACHE_TTL_SECS,
        parse_time=_parse_generated_at,
        build=read_profiles,
        save=_save,
        force=force,
        fresh=fresh,
        origin=origin,
    )


async def refresh_async(*, force=False, fresh=False, origin="async"):
    from services.legacy_export_snapshot_service import drain_thread

    return await drain_thread(refresh_result, force=force, fresh=fresh, origin=origin)


def build_full_cache() -> dict[str, Any]:
    result = refresh_result(fresh=True, origin="build_full_cache")
    if result.execution != "succeeded" or result.persistence != "saved":
        raise RuntimeError("profile_build_not_durable")
    return _service.snapshot()


def warm_cache(force: bool = False):
    refresh_result(force=force)


def invalidate_one(governor_id: int):
    _service.invalidate(governor_id)


async def invalidate_async(governor_id: int):
    from services.legacy_export_snapshot_service import drain_thread

    await drain_thread(invalidate_one, governor_id)


def get_profile_cached(governor_id: int) -> dict[str, Any] | None:
    warm_cache()
    return _service.profile(governor_id)


async def get_profile_async(governor_id: int):
    from services.legacy_export_snapshot_service import drain_thread

    return await drain_thread(get_profile_cached, governor_id)


# -------------------- Fuzzy search (cache-only) --------------------
def _normalize(s: str) -> str:
    # casefold + strip accents + trim + collapse spaces
    base = unidecode((s or "").strip().lower())
    return " ".join(base.split())


def _iter_name_entries():
    """
    Yield (display_name, gid, normalized_name) for all cached players.
    Preserves duplicates (multiple players sharing same display name).

    Project only name/ID fields from one published snapshot. Nested profile
    payloads are not copied for autocomplete or name lookup.
    """
    warm_cache()
    for display_name, gid_raw in _service.name_entries():
        try:
            name = (display_name or "").strip()
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
    if not get_cache_stats()["count"]:
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
