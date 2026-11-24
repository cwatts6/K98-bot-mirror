"""Conditional MGE board identity writes against the qualified lifecycle snapshot."""

from datetime import UTC, datetime
import logging

from stats_alerts.db import exec_with_cursor

logger = logging.getLogger(__name__)
_FIELDS = {
    "signup": ("SignupEmbedChannelId", "SignupEmbedMessageId"),
    "leadership": ("LeadershipEmbedChannelId", "LeadershipEmbedMessageId"),
    "awards": ("AwardEmbedChannelId", "AwardEmbedMessageId"),
}


def _utc(value):
    return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value


def persist_identity(*, kind, event_id, channel_id, message_id, expected, now_utc):
    channel_column, message_column = _FIELDS[kind]
    required = (
        "EventId",
        "Status",
        "RuleMode",
        "PublishVersion",
        "UpdatedUtc",
        "UpdatedUtcToken",
        channel_column,
        message_column,
    )
    if any(field not in expected for field in required) or expected["EventId"] != event_id:
        return False
    if not isinstance(expected["UpdatedUtc"], datetime) or channel_id <= 0 or message_id <= 0:
        return False

    def write(cur):
        # Identifiers come exclusively from the fixed domain allowlist above.
        cur.execute(
            f"UPDATE dbo.MGE_Events SET {channel_column} = ?, {message_column} = ?, UpdatedUtc = ? "
            f"WHERE EventId = ? AND Status = ? AND RuleMode = ? AND PublishVersion = ? AND UpdatedUtc = CONVERT(datetime2(7), ?, 126) "
            f"AND ({channel_column} = ? OR ({channel_column} IS NULL AND ? IS NULL)) "
            f"AND ({message_column} = ? OR ({message_column} IS NULL AND ? IS NULL));",
            (
                channel_id,
                message_id,
                _utc(now_utc),
                event_id,
                expected["Status"],
                expected["RuleMode"],
                expected["PublishVersion"],
                expected["UpdatedUtcToken"],
                expected[channel_column],
                expected[channel_column],
                expected[message_column],
                expected[message_column],
            ),
        )
        return int(cur.rowcount)

    affected = exec_with_cursor(write)
    if affected != 1:
        logger.warning(
            "mge_board_identity_unconfirmed event_id=%s kind=%s outcome=%s",
            event_id,
            kind,
            "conflict" if affected == 0 else "unknown",
        )
        return False
    return True
