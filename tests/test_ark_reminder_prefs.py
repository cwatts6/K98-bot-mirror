from __future__ import annotations

from ark.reminder_prefs import is_dm_allowed
from ark.reminder_types import (
    REMINDER_1H,
    REMINDER_4H,
    REMINDER_24H,
    REMINDER_CHECKIN_12H,
    REMINDER_START,
)


def test_default_allows_everything():
    assert is_dm_allowed(REMINDER_24H, None) is True
    assert is_dm_allowed(REMINDER_4H, None) is True
    assert is_dm_allowed(REMINDER_1H, None) is True
    assert is_dm_allowed(REMINDER_START, None) is True
    assert is_dm_allowed(REMINDER_CHECKIN_12H, None) is True


def test_opt_out_all_blocks_everything():
    row = {"OptOutAll": 1}
    assert is_dm_allowed(REMINDER_24H, row) is False
    assert is_dm_allowed(REMINDER_4H, row) is False
    assert is_dm_allowed(REMINDER_1H, row) is False
    assert is_dm_allowed(REMINDER_START, row) is False
    assert is_dm_allowed(REMINDER_CHECKIN_12H, row) is False


def test_per_interval_opt_out():
    row = {
        "OptOutAll": 0,
        "OptOut24h": 1,
        "OptOut4h": 0,
        "OptOut1h": 1,
        "OptOutStart": 0,
        "OptOutCheckIn12h": 1,
    }
    assert is_dm_allowed(REMINDER_24H, row) is False
    assert is_dm_allowed(REMINDER_4H, row) is True
    assert is_dm_allowed(REMINDER_1H, row) is False
    assert is_dm_allowed(REMINDER_START, row) is True
    assert is_dm_allowed(REMINDER_CHECKIN_12H, row) is False
