# kvk_state.py
from __future__ import annotations

import datetime as dt
import logging
from typing import Literal, TypedDict

from constants import _conn
from file_utils import fetch_one_dict

log = logging.getLogger(__name__)

State = Literal["DRAFT", "ACTIVE", "ENDED"]


class KVKContext(TypedDict):
    kvk_no: int
    kvk_name: str
    start_date: dt.date | None
    end_date: dt.date | None
    state: State
    next_kvk_no: int | None


def _as_date(v) -> dt.date | None:
    if not v:
        return None
    if isinstance(v, dt.date):
        return v
    try:
        return dt.datetime.fromisoformat(str(v)).date()
    except Exception:
        return None


def get_kvk_context_today(today: dt.date | None = None) -> KVKContext | None:
    today = today or dt.date.today()
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT TOP 1
                    KVK_NO, KVK_NAME, CAST(MATCHMAKING_START_DATE AS date), CAST(KVK_END_DATE AS date),
                    NEXT_KVK_NO
                FROM dbo.KVK_Details
                ORDER BY KVK_NO DESC
            """)
            row = fetch_one_dict(cur)
            if not row:
                return None
    except Exception as e:
        log.warning("[kvk_state] Could not read dbo.KVK_Details: %s", e)
        return None

    # Prefer named columns where available, fall back to positional ordering of returned values.
    vals = list(row.values())

    def by_name(*names, idx):
        for n in names:
            if n in row:
                return row[n]
        # positional fallback
        return vals[idx] if idx < len(vals) else None

    kvk_no = int(by_name("KVK_NO", idx=0))
    name = (by_name("KVK_NAME", idx=1) or f"KVK {kvk_no}").strip()
    start_d = _as_date(by_name("MATCHMAKING_START_DATE", "KVK_START_DATE", idx=2))
    end_d = _as_date(by_name("KVK_END_DATE", "MATCHMAKING_END_DATE", idx=3))
    next_no_raw = by_name("NEXT_KVK_NO", "NextKVKNo", idx=4)
    next_no = int(next_no_raw) if next_no_raw is not None else None

    if start_d and today < start_d:
        state: State = "DRAFT"
    elif start_d and end_d and start_d <= today <= end_d:
        state = "ACTIVE"
    elif end_d and today > end_d:
        state = "ENDED"
    else:
        state = "DRAFT"

    return KVKContext(
        kvk_no=kvk_no,
        kvk_name=name,
        start_date=start_d,
        end_date=end_d,
        state=state,
        next_kvk_no=next_no,
    )
