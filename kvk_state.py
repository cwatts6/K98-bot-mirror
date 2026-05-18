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
    matchmaking_scan: int | None
    pass4_start_scan: int | None
    kvk_end_scan: int | None
    max_scan_order: int | None
    state_reason: str


class KVKDetails(TypedDict):
    kvk_no: int
    kvk_name: str
    registration: dt.date | None
    start_date: dt.date | None
    end_date: dt.date | None
    matchmaking_scan: int | None
    kvk_end_scan: int | None
    matchmaking_start_date: dt.date | None
    fighting_start_date: dt.date | None
    pass4_start_scan: int | None
    next_kvk_no: int | None
    max_scan_order: int | None
    state: State
    state_reason: str


def _as_date(v) -> dt.date | None:
    if not v:
        return None
    if isinstance(v, dt.date):
        return v
    try:
        return dt.datetime.fromisoformat(str(v)).date()
    except Exception:
        return None


def _as_int(v) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def is_scan_within_open_window(
    start_scan: int | None,
    end_scan: int | None,
    max_scan_order: int | None,
) -> bool:
    if not isinstance(start_scan, int) or start_scan <= 0:
        return False
    if not isinstance(max_scan_order, int) or max_scan_order < start_scan:
        return False
    if end_scan is not None:
        if not isinstance(end_scan, int) or end_scan <= 0 or end_scan < start_scan:
            return False
        return max_scan_order <= end_scan
    return True


def resolve_kvk_scan_state(
    *,
    pass4_start_scan: int | None,
    kvk_end_scan: int | None,
    max_scan_order: int | None,
) -> tuple[State, str]:
    if not isinstance(pass4_start_scan, int) or pass4_start_scan <= 0:
        return "DRAFT", "invalid_pass4_start_scan"
    if not isinstance(max_scan_order, int):
        return "DRAFT", "missing_max_scan_order"
    if kvk_end_scan is not None:
        if not isinstance(kvk_end_scan, int) or kvk_end_scan <= 0:
            return "DRAFT", "invalid_kvk_end_scan"
        if kvk_end_scan < pass4_start_scan:
            return "DRAFT", "end_scan_before_pass4_start_scan"
        if max_scan_order > kvk_end_scan:
            return "ENDED", "max_scan_order_after_kvk_end_scan"
    if max_scan_order < pass4_start_scan:
        return "DRAFT", "max_scan_order_before_pass4_start_scan"
    return "ACTIVE", "max_scan_order_within_fighting_window"


def _get_max_scan_order() -> int | None:
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(ScanOrder) AS MaxScanOrder FROM ROK_TRACKER.dbo.kingdomscandata4"
            )
            row = fetch_one_dict(cur)
            if not row:
                return None
            return _as_int(row.get("MaxScanOrder", next(iter(row.values()), None)))
    except Exception as e:
        log.warning("[kvk_state] Could not read max ScanOrder: %s", e)
        return None


def get_latest_kvk_details(today: dt.date | None = None) -> KVKDetails | None:
    today = today or dt.date.today()
    try:
        with _conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT TOP 1
                    KVK_NO,
                    KVK_NAME,
                    KVK_REGISTRATION_DATE,
                    KVK_START_DATE,
                    KVK_END_DATE,
                    CAST(MATCHMAKING_START_DATE AS date) AS MATCHMAKING_START_DATE,
                    CAST(FIGHTING_START_DATE AS date) AS FIGHTING_START_DATE,
                    NEXT_KVK_NO,
                    MATCHMAKING_SCAN,
                    PASS4_START_SCAN,
                    KVK_END_SCAN
                FROM dbo.KVK_Details
                WHERE KVK_NO IS NOT NULL
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

    kvk_no = _as_int(by_name("KVK_NO", idx=0))
    if not kvk_no:
        log.warning("[kvk_state] Ignoring KVK_Details row with invalid KVK_NO=%r", kvk_no)
        return None
    name = (by_name("KVK_NAME", idx=1) or f"KVK {kvk_no}").strip()
    registration = _as_date(by_name("KVK_REGISTRATION_DATE", idx=2))
    start_d = _as_date(by_name("KVK_START_DATE", idx=3))
    end_d = _as_date(by_name("KVK_END_DATE", idx=4))
    mm_start = _as_date(by_name("MATCHMAKING_START_DATE", idx=5))
    fight_start = _as_date(by_name("FIGHTING_START_DATE", idx=6))
    next_no_raw = by_name("NEXT_KVK_NO", "NextKVKNo", idx=7)
    next_no = _as_int(next_no_raw)
    matchmaking_scan = _as_int(by_name("MATCHMAKING_SCAN", idx=8))
    pass4_start_scan = _as_int(by_name("PASS4_START_SCAN", idx=9))
    kvk_end_scan = _as_int(by_name("KVK_END_SCAN", idx=10))
    max_scan_order = _get_max_scan_order()

    if mm_start and today < mm_start:
        state: State = "DRAFT"
        reason = "today_before_matchmaking_start_date"
    else:
        state, reason = resolve_kvk_scan_state(
            pass4_start_scan=pass4_start_scan,
            kvk_end_scan=kvk_end_scan,
            max_scan_order=max_scan_order,
        )

    log.info(
        "[kvk_state] resolved KVK state kvk_no=%s matchmaking_scan=%r pass4_start_scan=%r "
        "kvk_end_scan=%r max_scan_order=%r resolved_state=%s reason=%s",
        kvk_no,
        matchmaking_scan,
        pass4_start_scan,
        kvk_end_scan,
        max_scan_order,
        state,
        reason,
    )

    return KVKDetails(
        kvk_no=kvk_no,
        kvk_name=name,
        registration=registration,
        start_date=start_d,
        end_date=end_d,
        matchmaking_scan=matchmaking_scan,
        kvk_end_scan=kvk_end_scan,
        matchmaking_start_date=mm_start,
        fighting_start_date=fight_start,
        pass4_start_scan=pass4_start_scan,
        next_kvk_no=next_no,
        max_scan_order=max_scan_order,
        state=state,
        state_reason=reason,
    )


def get_kvk_context_today(today: dt.date | None = None) -> KVKContext | None:
    details = get_latest_kvk_details(today=today)
    if not details:
        return None

    return KVKContext(
        kvk_no=details["kvk_no"],
        kvk_name=details["kvk_name"],
        start_date=details["matchmaking_start_date"],
        end_date=details["end_date"],
        state=details["state"],
        next_kvk_no=details["next_kvk_no"],
        matchmaking_scan=details["matchmaking_scan"],
        pass4_start_scan=details["pass4_start_scan"],
        kvk_end_scan=details["kvk_end_scan"],
        max_scan_order=details["max_scan_order"],
        state_reason=details["state_reason"],
    )
