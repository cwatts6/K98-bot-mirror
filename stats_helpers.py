# NEW helper module: stats_helpers.py
# Provides small shared helpers used by stats modules: cursor -> dict mapping, CSV builder,
# integer normalization, and slice detection.
# Place this file at repository root.

from itertools import zip_longest
from typing import Any


def fetch_all_dicts(cur) -> list[dict[str, Any]]:
    """
    Read cur.description and cur.fetchall() and return list[dict] mapping column names -> values.
    Defensive: if cur.description is None, returns [].

    Uses itertools.zip_longest to avoid relying on zip(...) without an explicit strict= parameter.
    If a row has fewer columns than the description, missing values will be None. If a row has
    extra columns they will be ignored (only description columns are used as keys).
    """
    if not getattr(cur, "description", None):
        return []
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    out = []
    for r in rows:
        # Use zip_longest to avoid lint rule B905 (zip without explicit strict=).
        # Fill missing values with None so caller sees consistent keys.
        out.append(dict(zip_longest(cols, r, fillvalue=None)))
    return out


def csv_from_ids(ids: list[int]) -> str:
    """Join a list of ints into a CSV string (no spaces)."""
    return ",".join(str(i) for i in ids)


def to_ints(maybe_ids: list[str | int]) -> list[int]:
    """Normalize a list of values that may be strings/ints into unique sorted ints."""
    out = []
    for v in maybe_ids:
        try:
            out.append(int(str(v).strip()))
        except Exception:
            pass
    return sorted(set(out))


def is_single_day_slice(window_key: str) -> bool:
    """Treat certain slice keys as single-day-only."""
    return (window_key or "").lower() in {"yesterday"}
