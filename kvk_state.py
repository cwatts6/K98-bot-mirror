# kvk_state.py
from __future__ import annotations

import datetime as dt
import logging
from typing import Literal, TypedDict

from constants import _conn

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
            cur.execute(
                """
                SELECT TOP 1
                    KVK_NO, KVK_NAME, CAST(MATCHMAKING_START_DATE AS date), CAST(KVK_END_DATE AS date),
                    NEXT_KVK_NO
                FROM dbo.KVK_Details
                ORDER BY KVK_NO DESC
            """
            )
            row = cur.fetchone()
            if not row:
                return None
    except Exception as e:
        log.warning("[kvk_state] Could not read dbo.KVK_Details: %s", e)
        return None

    kvk_no = int(row[0])
    name = (row[1] or f"KVK {kvk_no}").strip()
    start_d = _as_date(row[2])
    end_d = _as_date(row[3])
    next_no = int(row[4]) if row[4] is not None else None

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
