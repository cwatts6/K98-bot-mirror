# stats_helpers.py (compat shim)
# This module is kept for backwards compatibility. DB-row helpers were moved to file_utils.
# General helpers remain here; csv_from_ids/to_ints now live in utils.py and are re-exported.

from __future__ import annotations

from typing import Any

# Re-export DB helpers from file_utils for backwards compatibility.
try:
    from file_utils import cursor_row_to_dict, fetch_all_dicts, fetch_one_dict  # type: ignore
except Exception:
    # If import fails (e.g., during unit tests or odd import order), provide simple fallbacks.
    from itertools import zip_longest

    def cursor_row_to_dict(cursor, row) -> dict[str, Any]:
        """
        Fallback implementation that mirrors file_utils.cursor_row_to_dict behavior.

        Uses cursor.description to obtain column names and pairs them with the row
        values. Uses zip_longest so rows shorter than the number of columns get None,
        and rows longer than the number of columns are tolerated (extra values ignored).
        """
        if not getattr(cursor, "description", None):
            return {}
        cols = [d[0] for d in cursor.description]
        pairs = zip_longest(cols, row, fillvalue=None)
        out: dict[str, Any] = {}
        for col, val in pairs:
            if col is None:
                # extra row values beyond columns -> ignore
                continue
            out[col] = val
        return out

    def fetch_all_dicts(cur) -> list[dict[str, Any]]:
        if not getattr(cur, "description", None):
            return []
        rows = cur.fetchall() or []
        return [cursor_row_to_dict(cur, r) for r in rows]

    def fetch_one_dict(cur) -> dict[str, Any] | None:
        if not getattr(cur, "description", None):
            return None
        row = cur.fetchone()
        if row is None:
            return None
        return cursor_row_to_dict(cur, row)


# Re-export csv_from_ids / to_ints from utils for compatibility
try:
    from utils import csv_from_ids, to_ints  # type: ignore
except Exception:

    def csv_from_ids(ids: list[int]) -> str:
        """
        Serialize a list of ints to a comma-separated string.
        Keeps behavior simple and defensive.
        """
        if not ids:
            return ""
        return ",".join(str(int(i)) for i in ids)

    def to_ints(s: str) -> list[int]:
        """
        Parse a comma-separated string of ints into a list of ints.
        Ignores empty items and non-integers (skips them).
        """
        if not s:
            return []
        out: list[int] = []
        for part in str(s).split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except Exception:
                # Skip invalid entries rather than raising to keep compatibility
                continue
        return out


def is_single_day_slice(window_key: str) -> bool:
    """Treat certain slice keys as single-day-only."""
    return (window_key or "").lower() in {"yesterday"}


__all__ = [
    "csv_from_ids",
    "cursor_row_to_dict",
    "fetch_all_dicts",
    "fetch_one_dict",
    "is_single_day_slice",
    "to_ints",
]
