from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from mge.dal import mge_rules_dal

logger = logging.getLogger(__name__)

RULES_EMBED_FIELD_LIMIT = 1024
RULES_STORAGE_LIMIT = 4000


@dataclass(slots=True)
class RulesServiceResult:
    success: bool
    message: str
    event_id: int | None = None
    signup_channel_id: int | None = None


def get_event_rules_context(event_id: int) -> dict[str, Any] | None:
    """Load current rule context for an event."""
    return mge_rules_dal.fetch_event_rules_context(int(event_id))


def update_event_rules_text(
    *,
    event_id: int,
    new_rules_text: str,
    actor_discord_id: int | None,
) -> RulesServiceResult:
    """
    Update per-event rule text and audit the change.

    Manual edit preserves current RuleMode (Task K confirmed behavior).
    """
    ctx = mge_rules_dal.fetch_event_rules_context(int(event_id))
    if not ctx:
        return RulesServiceResult(False, "Event not found.", event_id=int(event_id))

    text = str(new_rules_text or "").strip()
    text_len = len(text)
    if not text:
        return RulesServiceResult(False, "Rules text cannot be empty.", event_id=int(event_id))
    if text_len > RULES_EMBED_FIELD_LIMIT:
        over_by = text_len - RULES_EMBED_FIELD_LIMIT
        return RulesServiceResult(
            False,
            (
                "Rules text is too long for the signup embed Rules field "
                f"(actual: {text_len}, allowed: {RULES_EMBED_FIELD_LIMIT}, over by: {over_by})."
            ),
            event_id=int(event_id),
        )
    if text_len > RULES_STORAGE_LIMIT:
        return RulesServiceResult(
            False,
            ("Rules text is too long " f"(actual: {text_len}, allowed: {RULES_STORAGE_LIMIT})."),
            event_id=int(event_id),
        )

    old_mode = str(ctx.get("RuleMode") or "").strip() or None
    old_text = str(ctx.get("RulesText")) if ctx.get("RulesText") is not None else None
    new_mode = old_mode  # preserve mode on manual edit

    ok = mge_rules_dal.update_event_rules_text_with_audit(
        event_id=int(event_id),
        actor_discord_id=actor_discord_id,
        old_rule_mode=old_mode,
        old_rules_text=old_text,
        new_rule_mode=new_mode,
        new_rules_text=text,
        action_type="edit",
    )
    if not ok:
        return RulesServiceResult(
            False,
            "Failed to update rules. Please try again.",
            event_id=int(event_id),
        )

    logger.info(
        "mge_rules_edit_success event_id=%s actor_discord_id=%s",
        event_id,
        actor_discord_id,
    )
    return RulesServiceResult(
        True,
        "Rules updated.",
        event_id=int(event_id),
        signup_channel_id=(
            int(ctx["SignupEmbedChannelId"])
            if ctx.get("SignupEmbedChannelId") is not None
            else None
        ),
    )


def reset_event_rules_to_mode_default(
    *,
    event_id: int,
    actor_discord_id: int | None,
) -> RulesServiceResult:
    """
    Reset event rules text to active default for current RuleMode and audit.
    """
    ctx = mge_rules_dal.fetch_event_rules_context(int(event_id))
    if not ctx:
        return RulesServiceResult(False, "Event not found.", event_id=int(event_id))

    mode = str(ctx.get("RuleMode") or "").strip().lower()
    if mode not in {"fixed", "open"}:
        return RulesServiceResult(
            False,
            f"Invalid event rule mode: {mode or 'unknown'}.",
            event_id=int(event_id),
        )

    default_text = mge_rules_dal.fetch_default_rules_text(mode)
    if not default_text:
        return RulesServiceResult(
            False,
            f"No active default rules found for mode '{mode}'.",
            event_id=int(event_id),
        )

    old_mode = str(ctx.get("RuleMode") or "").strip() or None
    old_text = str(ctx.get("RulesText")) if ctx.get("RulesText") is not None else None

    ok = mge_rules_dal.update_event_rules_text_with_audit(
        event_id=int(event_id),
        actor_discord_id=actor_discord_id,
        old_rule_mode=old_mode,
        old_rules_text=old_text,
        new_rule_mode=old_mode,  # mode preserved
        new_rules_text=default_text,
        action_type="reset_to_mode_default",
    )
    if not ok:
        return RulesServiceResult(
            False,
            "Failed to reset rules. Please try again.",
            event_id=int(event_id),
        )

    logger.info(
        "mge_rules_reset_success event_id=%s actor_discord_id=%s mode=%s",
        event_id,
        actor_discord_id,
        mode,
    )
    return RulesServiceResult(
        True,
        f"Rules reset to active '{mode}' default.",
        event_id=int(event_id),
        signup_channel_id=(
            int(ctx["SignupEmbedChannelId"])
            if ctx.get("SignupEmbedChannelId") is not None
            else None
        ),
    )
