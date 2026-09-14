from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from stats_alerts.db import exec_with_cursor, run_query

logger = logging.getLogger(__name__)


def fetch_event_rules_context(event_id: int) -> dict[str, Any] | None:
    """Return current event rule context for editing/audit."""
    sql = """
    SELECT TOP 1
        EventId,
        EventName,
        EventMode,
        RuleMode,
        RulesText,
        SignupEmbedChannelId
    FROM dbo.MGE_Events
    WHERE EventId = ?
    """
    rows = run_query(sql, [int(event_id)])
    return rows[0] if rows else None


def fetch_default_rules_text(rule_mode: str) -> str | None:
    """Return active default rule text for a given mode ('fixed' or 'open')."""
    mode = str(rule_mode or "").strip().lower()
    if mode not in {"fixed", "open"}:
        return None

    sql = """
    SELECT TOP 1 RuleText
    FROM dbo.MGE_DefaultRules
    WHERE RuleMode = ?
      AND IsActive = 1
    ORDER BY RuleKey
    """
    rows = run_query(sql, [mode])
    if not rows:
        return None
    return str(rows[0].get("RuleText") or "").strip() or None


def update_event_rules_text_with_audit(
    *,
    event_id: int,
    actor_discord_id: int | None,
    old_rule_mode: str | None,
    old_rules_text: str | None,
    new_rule_mode: str | None,
    new_rules_text: str | None,
    action_type: str,
    now_utc: datetime | None = None,
) -> bool:
    """
    Update MGE_Events rules fields and append audit row atomically.

    Note: Task K manual edits should preserve RuleMode; caller controls new_rule_mode.
    """
    ts = (now_utc or datetime.now(UTC)).astimezone(UTC)
    details_json = json.dumps(
        {"source": "mge_rules_service", "action": action_type},
        separators=(",", ":"),
    )

    sql_update_with_output = """
    UPDATE dbo.MGE_Events
    SET RulesText = ?,
        RuleMode = ?,
        UpdatedUtc = ?
    OUTPUT INSERTED.EventId
    WHERE EventId = ?
    """

    sql_audit = """
    INSERT INTO dbo.MGE_RuleAudit
    (
        EventId,
        ActorDiscordId,
        ActionType,
        OldRuleMode,
        NewRuleMode,
        OldRulesText,
        NewRulesText,
        CreatedUtc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    def _op(cursor: Any) -> bool:
        cursor.execute(
            sql_update_with_output,
            (
                (str(new_rules_text) if new_rules_text is not None else None),
                (str(new_rule_mode) if new_rule_mode is not None else None),
                ts,
                int(event_id),
            ),
        )
        updated_row = cursor.fetchone()
        if not updated_row:
            # No target event row updated => no audit write.
            return False

        cursor.execute(
            sql_audit,
            (
                int(event_id),
                int(actor_discord_id) if actor_discord_id is not None else None,
                str(action_type),
                (str(old_rule_mode) if old_rule_mode is not None else None),
                (str(new_rule_mode) if new_rule_mode is not None else None),
                (str(old_rules_text) if old_rules_text is not None else None),
                (str(new_rules_text) if new_rules_text is not None else None),
                ts,
            ),
        )
        return True

    try:
        result = exec_with_cursor(callback=_op)
        return bool(result)
    except Exception:
        logger.exception(
            "mge_rules_update_with_audit_failed event_id=%s actor_discord_id=%s action_type=%s details=%s",
            event_id,
            actor_discord_id,
            action_type,
            details_json,
        )
        return False
