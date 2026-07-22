"""Pure validation and UTC classification helpers for leadership Last Active."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise

from leadership_player_review.models import LastActive, LastActiveState

ELIGIBLE_SOURCE_CODES = frozenset(
    {
        "POWER",
        "HEALED",
        "RSS_GATHERED",
        "RSS_ASSISTED",
        "HELPS",
        "TECH_DONATIONS",
        "BUILDING_MINUTES",
        "FORT_RALLIES",
    }
)
_COUNTER_SOURCE_ORDER = (
    "POWER",
    "HEALED",
    "RSS_GATHERED",
    "RSS_ASSISTED",
    "HELPS",
    "TECH_DONATIONS",
    "BUILDING_MINUTES",
)


@dataclass(frozen=True, slots=True)
class LastActiveObservation:
    """One selected target-present complete kingdom scan cutoff."""

    scan_order: int
    scan_date: date
    values: tuple[tuple[str, Decimal | None], ...]
    positive_interval_sources: frozenset[str] = frozenset()


def derive_last_active(
    observations: tuple[LastActiveObservation, ...],
) -> tuple[date, str, int] | None:
    """Reference implementation for deterministic SQL/Python parity fixtures."""
    ordered = sorted(observations, key=lambda item: (item.scan_date, item.scan_order))
    if len({item.scan_order for item in ordered}) != len(ordered):
        raise ValueError("Last Active observations require unique selected scan orders")
    for previous, current in reversed(tuple(pairwise(ordered))):
        previous_values = dict(previous.values)
        current_values = dict(current.values)
        for source_code in _COUNTER_SOURCE_ORDER:
            before = previous_values.get(source_code)
            after = current_values.get(source_code)
            if before is not None and after is not None and after > before:
                return current.scan_date, source_code, current.scan_order
        if "FORT_RALLIES" in current.positive_interval_sources:
            return current.scan_date, "FORT_RALLIES", current.scan_order
    return None


def classify_last_active(
    last_active_date: date | None, effective_utc_date: date
) -> LastActiveState:
    """Classify using UTC calendar dates; exactly 30 days remains active."""
    if last_active_date is None:
        return "NOT_RECORDED"
    return "INACTIVE" if last_active_date < effective_utc_date - timedelta(days=30) else "ACTIVE"


def validate_last_active(record: LastActive) -> LastActive:
    """Fail closed when the additive SQL result contradicts its published contract."""
    if not 1 <= record.history_days <= 720:
        raise ValueError("Last Active history is outside the 1 through 720 day bound")
    if record.history_start_date > record.history_end_date:
        raise ValueError("Last Active history dates are inverted")
    if record.effective_utc_date != record.history_end_date:
        raise ValueError("Last Active history must end on effective UTC today")
    if record.last_active_date is not None and not (
        record.history_start_date <= record.last_active_date <= record.history_end_date
    ):
        raise ValueError("Last Active date falls outside the bounded history")
    if record.compared_complete_scans < 0:
        raise ValueError("Last Active comparison count cannot be negative")
    expected_state = classify_last_active(record.last_active_date, record.effective_utc_date)
    if record.activity_state != expected_state:
        raise ValueError("Last Active SQL/Python activity classification mismatch")
    if record.last_active_date is None:
        if record.qualifying_source_code is not None or record.qualifying_scan_order is not None:
            raise ValueError("Not-recorded Last Active cannot contain qualifying evidence")
    elif (
        record.qualifying_source_code not in ELIGIBLE_SOURCE_CODES
        or record.qualifying_scan_order is None
    ):
        raise ValueError("Recorded Last Active requires approved qualifying evidence")
    return record
