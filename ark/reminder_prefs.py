from __future__ import annotations

from ark.reminder_types import (
    REMINDER_1H,
    REMINDER_4H,
    REMINDER_24H,
    REMINDER_CHECKIN_12H,
    REMINDER_START,
)

DEFAULT_PREFS = {
    "OptOutAll": 0,
    "OptOut24h": 0,
    "OptOut4h": 0,
    "OptOut1h": 0,
    "OptOutStart": 0,
    "OptOutCheckIn12h": 0,
}


def merge_with_defaults(row: dict | None) -> dict:
    if not row:
        return dict(DEFAULT_PREFS)
    merged = dict(DEFAULT_PREFS)
    merged.update(row)
    return merged


def is_dm_allowed(reminder_type: str, row: dict | None) -> bool:
    prefs = merge_with_defaults(row)
    if int(prefs.get("OptOutAll", 0)) == 1:
        return False

    if reminder_type == REMINDER_24H:
        return int(prefs.get("OptOut24h", 0)) == 0
    if reminder_type == REMINDER_4H:
        return int(prefs.get("OptOut4h", 0)) == 0
    if reminder_type == REMINDER_1H:
        return int(prefs.get("OptOut1h", 0)) == 0
    if reminder_type == REMINDER_START:
        return int(prefs.get("OptOutStart", 0)) == 0
    if reminder_type == REMINDER_CHECKIN_12H:
        return int(prefs.get("OptOutCheckIn12h", 0)) == 0

    # unknown reminder type defaults to allowed
    return True
