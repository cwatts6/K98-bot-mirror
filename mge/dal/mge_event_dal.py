"""DAL for MGE event/calendar scheduler operations."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query

logger = logging.getLogger(__name__)

SQL_SELECT_CANDIDATE_CALENDAR_EVENTS = """
SELECT InstanceID, SourceKind, SourceID, StartUTC, EndUTC, Title, EventType, Variant, IsCancelled
FROM dbo.EventInstances
WHERE IsCancelled = 0
  AND StartUTC >= ?
  AND StartUTC < ?
  AND Variant IS NOT NULL;
"""

SQL_SELECT_ACTIVE_VARIANTS = """
SELECT VariantId, VariantName
FROM dbo.MGE_Variants
WHERE IsActive = 1;
"""

SQL_SELECT_EVENT_BY_STABLE_KEY = """
SELECT TOP (1)
    e.EventId,
    e.CalendarEventSourceId,
    e.CalendarSourceKind,
    e.CalendarSourceID
FROM dbo.MGE_Events e
WHERE e.VariantId = ?
  AND e.StartUtc = ?
  AND e.EndUtc = ?
  AND e.CalendarSourceID = ?
ORDER BY e.EventId DESC;
"""

SQL_UPDATE_EVENT_CALENDAR_SOURCE = """
UPDATE dbo.MGE_Events
SET CalendarEventSourceId = ?,
    CalendarSourceKind = ?,
    CalendarSourceID = ?,
    UpdatedUtc = ?
WHERE EventId = ?;
"""


SQL_SELECT_FIXED_RULE_TEMPLATE = """
SELECT TOP (1) RuleText
FROM dbo.MGE_DefaultRules
WHERE RuleKey = 'fixed_mge_rules'
  AND RuleMode = 'fixed'
  AND IsActive = 1
ORDER BY UpdatedUtc DESC;
"""

SQL_SELECT_EVENT_BY_SOURCE = """
SELECT TOP (1) EventId, RulesText
FROM dbo.MGE_Events
WHERE CalendarEventSourceId = ?
ORDER BY EventId DESC;
"""

SQL_SELECT_EVENT_FOR_EMBED = """
SELECT
    e.EventId,
    e.EventName,
    e.StartUtc,
    e.EndUtc,
    e.SignupCloseUtc,
    e.EventMode,
    e.Status,
    e.RuleMode,
    e.RulesText,
    e.SignupEmbedMessageId,
    e.SignupEmbedChannelId,
    e.LeadershipEmbedMessageId,
    e.LeadershipEmbedChannelId,
    e.AwardEmbedMessageId,
    e.AwardEmbedChannelId,
    v.VariantName
FROM dbo.MGE_Events e
JOIN dbo.MGE_Variants v ON e.VariantId = v.VariantId
WHERE e.EventId = ?;
"""

SQL_INSERT_MGE_EVENT = """
INSERT INTO dbo.MGE_Events
(
    VariantId, EventName, StartUtc, EndUtc, SignupCloseUtc,
    EventMode, Status, RuleMode, RulesText,
    PublishVersion, LastPublishedUtc,
    SignupEmbedMessageId, SignupEmbedChannelId,
    CalendarEventSourceId, CalendarSourceKind, CalendarSourceID, CreatedByDiscordId,
    CompletedAtUtc, CompletedByDiscordId, ReopenedAtUtc, ReopenedByDiscordId,
    CreatedUtc, UpdatedUtc
)
OUTPUT INSERTED.EventId
VALUES
(
    ?, ?, ?, ?, ?,
    'controlled', 'signup_open', 'fixed', ?,
    0, NULL,
    NULL, NULL,
    ?, ?, ?, NULL,
    NULL, NULL, NULL, NULL,
    ?, ?
);
"""

SQL_UPDATE_EMBED_IDS = """
UPDATE dbo.MGE_Events
SET SignupEmbedMessageId = ?, SignupEmbedChannelId = ?, UpdatedUtc = ?
WHERE EventId = ?;
"""

SQL_UPDATE_LEADERSHIP_EMBED_IDS = """
UPDATE dbo.MGE_Events
SET LeadershipEmbedMessageId = ?, LeadershipEmbedChannelId = ?, UpdatedUtc = ?
WHERE EventId = ?;
"""

SQL_TOUCH_UPDATED_UTC = """
UPDATE dbo.MGE_Events
SET UpdatedUtc = ?
WHERE EventId = ?;
"""

SQL_SELECT_EVENT_SWITCH_CONTEXT = """
SELECT EventId, Status, RuleMode, RulesText
FROM dbo.MGE_Events
WHERE EventId = ?;
"""

SQL_SELECT_OPEN_RULE_TEMPLATE = """
SELECT TOP (1) RuleText
FROM dbo.MGE_DefaultRules
WHERE RuleKey = 'open_mge_rules'
  AND RuleMode = 'open'
  AND IsActive = 1
ORDER BY UpdatedUtc DESC;
"""

SQL_SELECT_PUBLIC_SIGNUP_NAMES = """
SELECT GovernorNameSnapshot
FROM dbo.MGE_Signups
WHERE EventId = ?
  AND IsActive = 1
ORDER BY CreatedUtc ASC;
"""


def _naive_utc(dt: datetime) -> datetime:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


def fetch_calendar_candidates(window_start: datetime, window_end: datetime) -> list[dict[str, Any]]:
    try:
        return run_query(
            SQL_SELECT_CANDIDATE_CALENDAR_EVENTS, (_naive_utc(window_start), _naive_utc(window_end))
        )
    except Exception:
        logger.exception("mge_event_dal_fetch_calendar_candidates_failed")
        return []


def fetch_mge_event_by_stable_key(
    *,
    variant_id: int,
    start_utc: datetime,
    end_utc: datetime,
    calendar_source_id: str,
) -> dict[str, Any] | None:
    try:
        rows = run_query(
            SQL_SELECT_EVENT_BY_STABLE_KEY,
            (
                int(variant_id),
                _naive_utc(start_utc),
                _naive_utc(end_utc),
                str(calendar_source_id),
            ),
        )
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_event_dal_fetch_mge_event_by_stable_key_failed")
        return None


def update_event_calendar_source(
    *,
    event_id: int,
    calendar_event_source_id: int,
    calendar_source_kind: str | None,
    calendar_source_id: str | None,
    now_utc: datetime,
) -> bool:
    try:

        def _callback(cur):
            cur.execute(
                SQL_UPDATE_EVENT_CALENDAR_SOURCE,
                (
                    int(calendar_event_source_id),
                    calendar_source_kind,
                    calendar_source_id,
                    _naive_utc(now_utc),
                    int(event_id),
                ),
            )
            return int(cur.rowcount or 0)

        affected = exec_with_cursor(_callback)
        return bool(affected and affected > 0)
    except Exception:
        logger.exception("mge_event_dal_update_event_calendar_source_failed event_id=%s", event_id)
        return False


def fetch_active_variants() -> list[dict[str, Any]]:
    try:
        return run_query(SQL_SELECT_ACTIVE_VARIANTS)
    except Exception:
        logger.exception("mge_event_dal_fetch_active_variants_failed")
        return []


def fetch_fixed_rule_template() -> str | None:
    try:
        rows = run_query(SQL_SELECT_FIXED_RULE_TEMPLATE)
        if not rows:
            return None
        value = rows[0].get("RuleText")
        return str(value) if value is not None else None
    except Exception:
        logger.exception("mge_event_dal_fetch_fixed_rule_template_failed")
        return None


def fetch_mge_event_by_source(calendar_event_source_id: int) -> dict[str, Any] | None:
    try:
        sid = int(calendar_event_source_id)
        rows = run_query(SQL_SELECT_EVENT_BY_SOURCE, (sid,))
        if not rows:
            logger.info(
                "mge_event_dal_fetch_by_source_miss source_instance_id=%s",
                sid,
            )
            return None
        row = rows[0]
        logger.info(
            "mge_event_dal_fetch_by_source_hit source_instance_id=%s event_id=%s",
            sid,
            row.get("EventId"),
        )
        return row
    except Exception:
        logger.exception(
            "mge_event_dal_fetch_mge_event_by_source_failed source_instance_id=%s",
            calendar_event_source_id,
        )
        return None


def fetch_event_for_embed(event_id: int) -> dict[str, Any] | None:
    try:
        rows = run_query(SQL_SELECT_EVENT_FOR_EMBED, (event_id,))
        return rows[0] if rows else None
    except Exception:
        logger.exception("mge_event_dal_fetch_event_for_embed_failed event_id=%s", event_id)
        return None


def insert_mge_event(
    *,
    variant_id: int,
    event_name: str,
    start_utc: datetime,
    end_utc: datetime,
    signup_close_utc: datetime,
    rules_text: str,
    calendar_event_source_id: int,
    calendar_source_kind: str | None,
    calendar_source_id: str | None,
    now_utc: datetime,
) -> int | None:
    try:

        def _callback(cur):
            cur.execute(
                SQL_INSERT_MGE_EVENT,
                (
                    variant_id,
                    event_name,
                    _naive_utc(start_utc),
                    _naive_utc(end_utc),
                    _naive_utc(signup_close_utc),
                    rules_text,
                    int(calendar_event_source_id),
                    calendar_source_kind,
                    calendar_source_id,
                    _naive_utc(now_utc),
                    _naive_utc(now_utc),
                ),
            )
            row = cur.fetchone()
            return int(row[0]) if row else None

        event_id = exec_with_cursor(_callback)
        return int(event_id) if event_id is not None else None
    except Exception:
        logger.exception(
            "mge_event_dal_insert_mge_event_failed source=%s", calendar_event_source_id
        )
        return None


def update_event_embed_ids(
    *, event_id: int, message_id: int, channel_id: int, now_utc: datetime
) -> bool:
    try:

        def _callback(cur):
            cur.execute(
                SQL_UPDATE_EMBED_IDS,
                (message_id, channel_id, _naive_utc(now_utc), event_id),
            )
            return int(cur.rowcount or 0)

        affected = exec_with_cursor(_callback)
        return bool(affected and affected > 0)
    except Exception:
        logger.exception("mge_event_dal_update_event_embed_ids_failed event_id=%s", event_id)
        return False


def update_event_leadership_embed_ids(
    *, event_id: int, message_id: int, channel_id: int, now_utc: datetime
) -> bool:
    """Persist leadership embed message/channel ids on dbo.MGE_Events."""
    try:

        def _callback(cur):
            cur.execute(
                SQL_UPDATE_LEADERSHIP_EMBED_IDS,
                (message_id, channel_id, _naive_utc(now_utc), event_id),
            )
            return int(cur.rowcount or 0)

        affected = exec_with_cursor(_callback)
        return bool(affected and affected > 0)
    except Exception:
        logger.exception(
            "mge_event_dal_update_event_leadership_embed_ids_failed event_id=%s", event_id
        )
        return False


def touch_event_updated_utc(*, event_id: int, now_utc: datetime) -> bool:
    try:

        def _callback(cur):
            cur.execute(SQL_TOUCH_UPDATED_UTC, (_naive_utc(now_utc), event_id))
            return int(cur.rowcount or 0)

        affected = exec_with_cursor(_callback)
        return bool(affected and affected > 0)
    except Exception:
        logger.exception("mge_event_dal_touch_event_updated_utc_failed event_id=%s", event_id)
        return False


def fetch_event_switch_context(event_id: int) -> dict[str, Any] | None:
    rows = run_query(SQL_SELECT_EVENT_SWITCH_CONTEXT, (event_id,))
    return rows[0] if rows else None


def fetch_open_rule_template() -> str | None:
    rows = run_query(SQL_SELECT_OPEN_RULE_TEMPLATE)
    if not rows:
        return None
    value = rows[0].get("RuleText")
    return str(value) if value is not None else None


def fetch_public_signup_names(event_id: int) -> list[str]:
    rows = run_query(SQL_SELECT_PUBLIC_SIGNUP_NAMES, (event_id,))
    names: list[str] = []
    for row in rows:
        v = row.get("GovernorNameSnapshot")
        if v is None:
            continue
        names.append(str(v))
    return names


def apply_open_mode_switch_atomic(
    *,
    event_id: int,
    actor_discord_id: int,
    old_rule_mode: str | None,
    old_rules_text: str | None,
    new_rules_text: str,
) -> int:
    """
    Atomically:
      - hard delete signups
      - switch event mode/rule mode/rules text
      - write MGE_RuleAudit
      - write MGE_SignupAudit (bulk_delete_open_switch)
    Returns deleted row count.
    """

    def _callback(cur):
        cur.execute(
            """
            DELETE FROM dbo.MGE_Signups
            WHERE EventId = ?;
            """,
            (event_id,),
        )
        deleted_count = int(cur.rowcount or 0)

        cur.execute(
            """
            UPDATE dbo.MGE_Events
            SET EventMode = 'open',
                RuleMode = 'open',
                RulesText = ?,
                UpdatedUtc = SYSUTCDATETIME()
            WHERE EventId = ?;
            """,
            (new_rules_text, event_id),
        )

        cur.execute(
            """
            INSERT INTO dbo.MGE_RuleAudit
                (EventId, ActorDiscordId, ActionType, OldRuleMode, NewRuleMode, OldRulesText, NewRulesText, CreatedUtc)
            VALUES
                (?, ?, 'mode_switch', ?, 'open', ?, ?, SYSUTCDATETIME());
            """,
            (event_id, actor_discord_id, old_rule_mode, old_rules_text, new_rules_text),
        )

        details_json = json.dumps(
            {
                "action": "bulk_delete_open_switch",
                "deleted_signup_count": deleted_count,
            },
            ensure_ascii=False,
        )

        cur.execute(
            """
            INSERT INTO dbo.MGE_SignupAudit
                (SignupId, EventId, GovernorId, ActionType, ActorDiscordId, DetailsJson, CreatedUtc)
            VALUES
                (0, ?, 0, 'bulk_delete_open_switch', ?, ?, SYSUTCDATETIME());
            """,
            (event_id, actor_discord_id, details_json),
        )
        return deleted_count

    result = exec_with_cursor(_callback)
    if result is None:
        raise RuntimeError("apply_open_mode_switch_atomic_failed")
    return int(result)


def apply_fixed_mode_switch_atomic(
    *,
    event_id: int,
    actor_discord_id: int,
    old_rule_mode: str | None,
    old_rules_text: str | None,
    new_rules_text: str,
) -> int:
    """
    Atomically switch an event back to controlled/fixed mode without deleting signups.
    Returns the number of affected rows on the event update.
    """

    def _callback(cur):
        cur.execute(
            """
            UPDATE dbo.MGE_Events
            SET EventMode = 'controlled',
                RuleMode = 'fixed',
                RulesText = ?,
                UpdatedUtc = SYSUTCDATETIME()
            WHERE EventId = ?;
            """,
            (new_rules_text, event_id),
        )
        affected = int(cur.rowcount or 0)

        if affected > 0:
            cur.execute(
                """
                INSERT INTO dbo.MGE_RuleAudit
                    (EventId, ActorDiscordId, ActionType, OldRuleMode, NewRuleMode, OldRulesText, NewRulesText, CreatedUtc)
                VALUES
                    (?, ?, 'mode_switch_back', ?, 'fixed', ?, ?, SYSUTCDATETIME());
                """,
                (event_id, actor_discord_id, old_rule_mode, old_rules_text, new_rules_text),
            )

        return affected

    result = exec_with_cursor(_callback)
    if result is None:
        raise RuntimeError("apply_fixed_mode_switch_atomic_failed")
    return int(result)
