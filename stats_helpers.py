# NEW helper module: stats_helpers.py
# Provides small shared helpers used by stats modules: cursor -> dict mapping, CSV builder,
# integer normalization, and slice detection.
# Place this file at repository root.

from collections.abc import Sequence
from itertools import zip_longest
from typing import Any


def cursor_row_to_dict(cursor, row: Sequence[Any]) -> dict[str, Any]:
    """
    Robust mapping from DB cursor + row -> dict.
    - Uses cursor.description to determine column names.
    - Uses zip_longest so rows shorter than the number of columns get None for missing values.
    - Rows longer than the number of columns are tolerated: extra values are ignored.
    - Ensures no None keys (filters any zipped pair where the column name is None).
    - Returns {} if cursor.description is None.
    """
    if not getattr(cursor, "description", None):
        return {}
    cols = [d[0] for d in cursor.description]
    # zip_longest pairs (col, val); if row shorter, val==None; if row longer, col==None for extra vals
    pairs = zip_longest(cols, row, fillvalue=None)
    out: dict[str, Any] = {}
    for col, val in pairs:
        # only include pairs where we have a valid column name
        if col is None:
            # extra row values beyond columns -> ignore
            continue
        out[col] = val
    return out


def fetch_all_dicts(cur) -> list[dict[str, Any]]:
    """
    Read cur.description and cur.fetchall() and return list[dict] mapping column names -> values.
    Defensive: if cur.description is None, returns [].

    Behavior:
    - Only column names from cur.description are used as keys.
    - If a row has fewer values than the number of columns, missing values are filled with None.
    - If a row has more values than the number of columns, extra values are ignored.
    """
    if not getattr(cur, "description", None):
        return []
    rows = cur.fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(cursor_row_to_dict(cur, r))
    return out


def csv_from_ids(ids: list[int]) -> str:
    """Join a list of ints into a CSV string (no spaces)."""
    return ",".join(str(i) for i in ids)


def to_ints(maybe_ids: list[str | int]) -> list[int]:
    """Normalize a list of values that may be strings/ints into unique sorted ints."""
    out: list[int] = []
    for v in maybe_ids:
        try:
            out.append(int(str(v).strip()))
        except Exception:
            pass
    return sorted(set(out))


def is_single_day_slice(window_key: str) -> bool:
    """Treat certain slice keys as single-day-only."""
    return (window_key or "").lower() in {"yesterday"}
