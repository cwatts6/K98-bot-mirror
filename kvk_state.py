# kvk_state.py
from __future__ import annotations

import datetime as dt
import logging
from typing import Literal, TypedDict

from kvk.dal import kvk_lifecycle_dal

log = logging.getLogger(__name__)

KvkFightingState = Literal["DRAFT", "ACTIVE", "ENDED"]

# Compatibility alias for callers that imported the original generic name.
State = KvkFightingState


class KvkFightingContext(TypedDict):
    kvk_no: int
    kvk_name: str
    start_date: dt.date | None
    end_date: dt.date | None
    fighting_state: KvkFightingState
    next_kvk_no: int | None
    matchmaking_scan: int | None
    pass4_start_scan: int | None
    kvk_end_scan: int | None
    max_scan_order: int | None
    fighting_state_reason: str


class KVKContext(TypedDict):
    kvk_no: int
    kvk_name: str
    start_date: dt.date | None
    end_date: dt.date | None
    state: KvkFightingState
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
    state: KvkFightingState
    state_reason: str


class KVKWindow(TypedDict):
    kvk_no: int
    matchmaking_scan: int | None
    kvk_end_scan: int | None
    pass4_start_scan: int | None
    max_scan_order: int | None
    source: str


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


def resolve_kvk_fighting_state(
    *,
    pass4_start_scan: int | None,
    kvk_end_scan: int | None,
    max_scan_order: int | None,
) -> tuple[KvkFightingState, str]:
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


def resolve_kvk_scan_state(
    *,
    pass4_start_scan: int | None,
    kvk_end_scan: int | None,
    max_scan_order: int | None,
) -> tuple[State, str]:
    """Compatibility adapter for the explicit fighting-lifecycle resolver."""
    return resolve_kvk_fighting_state(
        pass4_start_scan=pass4_start_scan,
        kvk_end_scan=kvk_end_scan,
        max_scan_order=max_scan_order,
    )


def _get_max_scan_order() -> int | None:
    try:
        return kvk_lifecycle_dal.fetch_max_scan_order()
    except Exception as e:
        log.warning("[kvk_state] Could not read max ScanOrder: %s", e)
        return None


def get_latest_kvk_details(today: dt.date | None = None) -> KVKDetails | None:
    today = today or dt.date.today()
    try:
        row = kvk_lifecycle_dal.fetch_latest_kvk_details_record()
        if not row:
            return None
    except Exception as e:
        log.warning("[kvk_state] Could not read dbo.KVK_Details: %s", e)
        return None

    kvk_no = row.kvk_no
    if not kvk_no:
        log.warning("[kvk_state] Ignoring KVK_Details row with invalid KVK_NO=%r", kvk_no)
        return None
    name = (row.kvk_name or f"KVK {kvk_no}").strip()
    registration = row.registration
    start_d = row.start_date
    end_d = row.end_date
    mm_start = row.matchmaking_start_date
    fight_start = row.fighting_start_date
    next_no = row.next_kvk_no
    matchmaking_scan = row.matchmaking_scan
    pass4_start_scan = row.pass4_start_scan
    kvk_end_scan = row.kvk_end_scan
    max_scan_order = _get_max_scan_order()

    if mm_start and today < mm_start:
        state: KvkFightingState = "DRAFT"
        reason = "today_before_matchmaking_start_date"
    else:
        state, reason = resolve_kvk_fighting_state(
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


def _is_valid_kvk_window(matchmaking_scan: int | None, kvk_end_scan: int | None) -> bool:
    if not isinstance(matchmaking_scan, int) or matchmaking_scan <= 0:
        return False
    if kvk_end_scan is None:
        return True
    return isinstance(kvk_end_scan, int) and kvk_end_scan > 0 and kvk_end_scan >= matchmaking_scan


def _get_proc_config_window(max_scan_order: int | None) -> KVKWindow | None:
    try:
        row = kvk_lifecycle_dal.fetch_proc_config_window_record()
        current_kvk = row.current_kvk
        if not current_kvk:
            log.warning("[kvk_state] No CURRENTKVK3 found in ProcConfig.")
            return None

        matchmaking_scan = row.matchmaking_scan
        kvk_end_scan = row.kvk_end_scan
        if not _is_valid_kvk_window(matchmaking_scan, kvk_end_scan):
            log.warning(
                "[kvk_state] Invalid ProcConfig KVK window. kvk_no=%s matchmaking_scan=%r kvk_end_scan=%r",
                current_kvk,
                matchmaking_scan,
                kvk_end_scan,
            )
            return None
        return KVKWindow(
            kvk_no=current_kvk,
            matchmaking_scan=matchmaking_scan,
            kvk_end_scan=kvk_end_scan,
            pass4_start_scan=None,
            max_scan_order=max_scan_order,
            source="ProcConfig",
        )
    except Exception as e:
        log.warning("[kvk_state] Could not read ProcConfig KVK window: %s", e)
        return None


def get_kvk_window_with_fallback() -> KVKWindow | None:
    details = get_latest_kvk_details()
    max_scan_order = details["max_scan_order"] if details else _get_max_scan_order()
    if details and _is_valid_kvk_window(details["matchmaking_scan"], details["kvk_end_scan"]):
        return KVKWindow(
            kvk_no=details["kvk_no"],
            matchmaking_scan=details["matchmaking_scan"],
            kvk_end_scan=details["kvk_end_scan"],
            pass4_start_scan=details["pass4_start_scan"],
            max_scan_order=max_scan_order,
            source="KVK_Details",
        )

    fallback = _get_proc_config_window(max_scan_order)
    if fallback:
        log.info(
            "[kvk_state] Using ProcConfig KVK window fallback. kvk_no=%s matchmaking_scan=%r "
            "kvk_end_scan=%r max_scan_order=%r",
            fallback["kvk_no"],
            fallback["matchmaking_scan"],
            fallback["kvk_end_scan"],
            fallback["max_scan_order"],
        )
    return fallback


def get_kvk_fighting_context_today(today: dt.date | None = None) -> KvkFightingContext | None:
    details = get_latest_kvk_details(today=today)
    if not details:
        return None

    return KvkFightingContext(
        kvk_no=details["kvk_no"],
        kvk_name=details["kvk_name"],
        start_date=details["matchmaking_start_date"],
        end_date=details["end_date"],
        fighting_state=details["state"],
        next_kvk_no=details["next_kvk_no"],
        matchmaking_scan=details["matchmaking_scan"],
        pass4_start_scan=details["pass4_start_scan"],
        kvk_end_scan=details["kvk_end_scan"],
        max_scan_order=details["max_scan_order"],
        fighting_state_reason=details["state_reason"],
    )


def get_kvk_context_today(today: dt.date | None = None) -> KVKContext | None:
    """Compatibility adapter returning the original generic state keys."""
    context = get_kvk_fighting_context_today(today=today)
    if not context:
        return None
    return KVKContext(
        kvk_no=context["kvk_no"],
        kvk_name=context["kvk_name"],
        start_date=context["start_date"],
        end_date=context["end_date"],
        state=context["fighting_state"],
        next_kvk_no=context["next_kvk_no"],
        matchmaking_scan=context["matchmaking_scan"],
        pass4_start_scan=context["pass4_start_scan"],
        kvk_end_scan=context["kvk_end_scan"],
        max_scan_order=context["max_scan_order"],
        state_reason=context["fighting_state_reason"],
    )
