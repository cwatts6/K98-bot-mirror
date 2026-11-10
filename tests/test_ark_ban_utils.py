from datetime import UTC, date, datetime

from ark.ban_utils import (
    admin_override_ban_rule,
    compute_ark_end_weekend_date,
    compute_next_ark_weekend_date,
    format_ban_block_message,
    is_weekend_date_in_ban_window,
)


def test_compute_next_ark_weekend_date_on_or_after_now():
    anchor = date(2026, 3, 7)
    now = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    assert compute_next_ark_weekend_date(
        anchor_weekend_date=anchor,
        frequency_weekends=2,
        now_utc=now,
    ) == date(2026, 3, 7)


def test_ban_end_weekend_math():
    start = date(2026, 3, 7)
    end = compute_ark_end_weekend_date(
        start_weekend_date=start,
        banned_ark_weekends=3,
        frequency_weekends=2,
    )
    assert end == date(2026, 4, 4)


def test_is_weekend_in_ban_window_true_exact_cycle():
    assert (
        is_weekend_date_in_ban_window(
            target_weekend_date=date(2026, 3, 21),
            start_weekend_date=date(2026, 3, 7),
            banned_ark_weekends=2,
            frequency_weekends=2,
        )
        is True
    )


def test_is_weekend_in_ban_window_false_non_cycle_day():
    assert (
        is_weekend_date_in_ban_window(
            target_weekend_date=date(2026, 3, 28),  # off-cycle for freq=2 from 3/7
            start_weekend_date=date(2026, 3, 7),
            banned_ark_weekends=3,
            frequency_weekends=2,
        )
        is False
    )


def test_messages_and_override_flag():
    msg_self = format_ban_block_message(admin_context=False)
    msg_admin = format_ban_block_message(admin_context=True, include_reason=True, reason="toxicity")
    assert "cannot sign up" in msg_self.lower()
    assert "cannot add this governor" in msg_admin.lower()
    assert "toxicity" in msg_admin.lower()

    assert admin_override_ban_rule({"AdminOverrideBanRule": 1}) is True
    assert admin_override_ban_rule({"AdminOverrideBanRule": 0}) is False
