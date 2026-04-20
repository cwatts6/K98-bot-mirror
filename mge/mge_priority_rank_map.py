"""
Priority-Rank mapping for the simplified MGE signup flow.

Maps user-visible combined options to (RequestPriority, PreferredRankBand) pairs
used by the service layer and order/sort logic.

Tie-break rules (used in ordering):
  1. sort_weight ascending (High=1, Medium=2, Low=3, No preference=4)
  2. kvk_rank ascending (lower rank number = better performance)
  3. SignupId ascending (stable insertion-order tie-break)

Legacy signups that do not match any option key resolve to sort_weight=99,
placing them at the bottom of the queue.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityRankOption:
    """A single selectable option in the combined Priority (Rank) dropdown."""

    label: str           # Shown to the player
    value: str           # Internal key stored in view state
    request_priority: str      # Maps to RequestPriority DB column
    preferred_rank_band: str   # Maps to PreferredRankBand DB column
    sort_weight: int     # Lower = higher priority in ordering


PRIORITY_RANK_OPTIONS: list[PriorityRankOption] = [
    PriorityRankOption(
        label="High (Rank 1\u20135)",
        value="high_1_5",
        request_priority="High",
        preferred_rank_band="1-5",
        sort_weight=1,
    ),
    PriorityRankOption(
        label="Medium (Rank 6\u201310)",
        value="medium_6_10",
        request_priority="Medium",
        preferred_rank_band="6-10",
        sort_weight=2,
    ),
    PriorityRankOption(
        label="Low (Rank 11\u201315)",
        value="low_11_15",
        request_priority="Low",
        preferred_rank_band="11-15",
        sort_weight=3,
    ),
    PriorityRankOption(
        label="No preference",
        value="no_preference",
        request_priority="Low",
        preferred_rank_band="no_preference",
        sort_weight=4,
    ),
]

_BY_VALUE: dict[str, PriorityRankOption] = {o.value: o for o in PRIORITY_RANK_OPTIONS}
_BY_PRIORITY_RANK: dict[tuple[str, str], PriorityRankOption] = {
    (o.request_priority.lower(), o.preferred_rank_band.lower()): o
    for o in PRIORITY_RANK_OPTIONS
}


def get_option_by_value(value: str) -> PriorityRankOption | None:
    """Return the PriorityRankOption matching the given internal value key, or None."""
    return _BY_VALUE.get(value)


def get_option_by_priority_rank(
    request_priority: str, preferred_rank_band: str | None
) -> PriorityRankOption | None:
    """
    Resolve a combined option from existing priority + rank_band values.

    Used when prefilling the combined dropdown for edit flows (e.g. legacy signups
    created before the simplified flow existed).  Falls back to 'no_preference'
    if no exact match is found, so legacy signups can still be edited gracefully.
    """
    key = (
        (request_priority or "").strip().lower(),
        (preferred_rank_band or "no_preference").strip().lower(),
    )
    return _BY_PRIORITY_RANK.get(key) or _BY_VALUE.get("no_preference")


def get_sort_weight(request_priority: str, preferred_rank_band: str | None) -> int:
    """
    Return the sort_weight for a given priority+rank_band pair.

    Returns 99 for unrecognised combinations (legacy rows that predate the mapping).
    This places them at the bottom of auto-sort order.
    """
    key = (
        (request_priority or "").strip().lower(),
        (preferred_rank_band or "no_preference").strip().lower(),
    )
    option = _BY_PRIORITY_RANK.get(key)
    return option.sort_weight if option is not None else 99
