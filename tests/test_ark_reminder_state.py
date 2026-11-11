from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from ark.reminder_state import (
    ArkReminderState,
    make_channel_daily_key,
    make_channel_key,
    make_dm_key,
)


def test_channel_daily_key_format():
    assert (
        make_channel_daily_key(2, 1095, "daily", date(2026, 2, 28))
        == "2|channel:1095|daily|2026-02-28"
    )


def test_dm_and_channel_key_format():
    assert make_dm_key(7, 99, "24h") == "7|99|24h"
    assert make_channel_key(7, 111, "daily") == "7|channel:111|daily"


def test_should_send_with_grace_and_dedupe(tmp_path):
    state = ArkReminderState.load(tmp_path / "ark_reminder_state.json")
    key = make_dm_key(1, 2, "24h")
    now = datetime(2026, 3, 7, 12, 0, tzinfo=UTC)
    scheduled = now - timedelta(minutes=5)

    assert state.should_send_with_grace(key, scheduled_for=scheduled, now=now) is True

    state.mark_sent(key, sent_at=now)
    assert state.should_send_with_grace(key, scheduled_for=scheduled, now=now) is False


def test_should_not_send_outside_grace(tmp_path):
    state = ArkReminderState.load(tmp_path / "ark_reminder_state.json")
    key = make_dm_key(1, 2, "24h")
    now = datetime(2026, 3, 7, 12, 0, tzinfo=UTC)
    scheduled = now - timedelta(minutes=16)

    assert state.should_send_with_grace(key, scheduled_for=scheduled, now=now) is False


def test_channel_message_ref_roundtrip(tmp_path):
    path = tmp_path / "ark_reminder_state.json"
    state = ArkReminderState.load(path)
    state.set_channel_message_ref(7, "daily", 1001, 2002)
    state.save()

    reloaded = ArkReminderState.load(path)
    ref = reloaded.get_channel_message_ref(7, "daily")
    assert ref is not None
    assert ref["channel_id"] == 1001
    assert ref["message_id"] == 2002
