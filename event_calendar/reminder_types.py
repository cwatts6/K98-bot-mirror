from __future__ import annotations

from datetime import timedelta

REMINDER_7D = "7d"
REMINDER_3D = "3d"
REMINDER_24H = "24h"
REMINDER_1H = "1h"
REMINDER_START = "start"
REMINDER_ALL = "all"

REMINDER_OFFSETS_ORDERED: tuple[str, ...] = (
    REMINDER_7D,
    REMINDER_3D,
    REMINDER_24H,
    REMINDER_1H,
    REMINDER_START,
)

REMINDER_OFFSET_TO_DELTA: dict[str, timedelta] = {
    REMINDER_7D: timedelta(days=7),
    REMINDER_3D: timedelta(days=3),
    REMINDER_24H: timedelta(hours=24),
    REMINDER_1H: timedelta(hours=1),
    REMINDER_START: timedelta(seconds=0),
}


def normalize_offset_token(value: str) -> str:
    return (value or "").strip().lower().replace("at_start", "start")


def is_valid_offset(value: str) -> bool:
    v = normalize_offset_token(value)
    return v in set(REMINDER_OFFSETS_ORDERED) | {REMINDER_ALL}


def expand_offsets(values: list[str] | tuple[str, ...] | set[str] | None) -> set[str]:
    if not values:
        return set()

    out: set[str] = set()
    for raw in values:
        v = normalize_offset_token(str(raw))
        if not v:
            continue
        if v == REMINDER_ALL:
            out.update(REMINDER_OFFSETS_ORDERED)
            continue
        if v in REMINDER_OFFSETS_ORDERED:
            out.add(v)
    return out
