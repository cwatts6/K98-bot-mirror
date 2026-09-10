from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ark.reminder_state import ArkReminderState, make_dm_key


def test_grace_window_send_within_10_minutes(tmp_path):
    state = ArkReminderState.load(tmp_path / "ark_reminder_state.json")
    now = datetime.now(UTC)
    scheduled = now - timedelta(minutes=10)

    key = make_dm_key(1, 2, "24h")
    assert state.should_send_with_grace(key, scheduled_for=scheduled, now=now) is True


def test_grace_window_skip_after_20_minutes(tmp_path):
    state = ArkReminderState.load(tmp_path / "ark_reminder_state.json")
    now = datetime.now(UTC)
    scheduled = now - timedelta(minutes=20)

    key = make_dm_key(1, 2, "24h")
    assert state.should_send_with_grace(key, scheduled_for=scheduled, now=now) is False
