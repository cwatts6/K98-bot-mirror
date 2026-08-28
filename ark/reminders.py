from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import discord

from ark.reminder_state import ArkReminderState
from ark.reminder_types import ALL_DM_REMINDER_TYPES

logger = logging.getLogger(__name__)


def _is_time_relative_key(key: str, match_id: int) -> bool:
    """Return True if *key* is a time-relative reminder key for the given match_id.

    Handles both DM and channel key formats:
      DM key:      "{match_id}|{user_id}|{reminder_type}"
      Channel key: "{match_id}|channel:{channel_id}|{reminder_type}"

    Daily/final-day keys include a fourth segment (date suffix) and use reminder
    types not in ALL_DM_REMINDER_TYPES, so they are naturally excluded.
    """
    prefix = f"{match_id}|"
    if not key.startswith(prefix):
        return False
    parts = key.split("|")
    # reminder_type is always the third segment (index 2) for both DM and channel keys
    return len(parts) >= 3 and parts[2] in ALL_DM_REMINDER_TYPES


async def reschedule_match_reminders(
    *,
    match_id: int,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
) -> None:
    """Clear time-relative reminder state for a match so reminders re-fire after a reschedule.

    Removes all DM and channel reminder deduplication keys for the five time-relative
    reminder types (24h, 4h, 1h, start, checkin_12h). Daily repost keys and keys for
    other match IDs are left untouched.

    The ``match_datetime_utc`` and ``signup_close_utc`` parameters are retained for
    future use when reminder scheduling becomes proactive; they are not used beyond
    logging in this implementation.
    """
    state = ArkReminderState.load()

    keys_to_remove = [key for key in state.reminders if _is_time_relative_key(key, match_id)]
    cleared = len(keys_to_remove)

    if cleared:
        for key in keys_to_remove:
            del state.reminders[key]
        state.save()
        logger.info(
            "[ARK_REMINDERS] reschedule match_id=%s cleared_keys=%s "
            "new_match_dt=%s new_close_dt=%s",
            match_id,
            cleared,
            match_datetime_utc.isoformat(),
            signup_close_utc.isoformat(),
        )
    else:
        logger.debug(
            "[ARK_REMINDERS] reschedule match_id=%s cleared_keys=0 "
            "new_match_dt=%s new_close_dt=%s",
            match_id,
            match_datetime_utc.isoformat(),
            signup_close_utc.isoformat(),
        )


def cancel_match_reminders(match_id: int) -> bool:
    """Remove reminder state for a match so reminders don't re-send after cancel.

    CR1: preserve cancelled-DM dedupe keys ({match_id}|{user_id}|cancelled) so
    a same-match cancellation DM cannot be re-sent if cancel_match_reminders is
    called again after dispatch_cancel_dms has already run.

    Returns True if any non-cancelled reminder entries were removed.
    Uses ArkReminderState (the scheduler's authoritative reminder store).
    Synchronous — ArkReminderState.load() and .save() are synchronous.
    """
    state = ArkReminderState.load()
    prefix = f"{match_id}|"
    before = len(state.reminders)
    # CR1: keep keys that start with the match prefix AND end with |cancelled
    state.reminders = {
        key: val
        for key, val in state.reminders.items()
        if not key.startswith(prefix) or key.endswith("|cancelled")
    }
    changed = len(state.reminders) != before
    if changed:
        state.save()
        logger.info("[ARK_REMINDERS] Cleared reminder state for match_id=%s", match_id)
    return changed


async def dispatch_cancel_dms(
    *,
    client,
    match_id: int,
    match: dict[str, Any],
    roster: list[dict[str, Any]],
) -> dict[str, int]:
    """Send a cancellation DM to every active signed-up player for a match.

    CR2: saves ArkReminderState after each successful send so dedupe keys are
    persisted immediately — safe across bot restarts mid-dispatch.

    CR9: Attempt client.get_user before fetch_user to avoid unnecessary API
    calls for members already cached.

    Sends an embed DM. A discord.Forbidden exception (user has DMs disabled)
    marks the dedupe key so the user is not retried on subsequent runs.

    Deduplication is per-user via ArkReminderState keys — safe across bot
    restarts. No opt-out: cancellation DMs are always sent.

    Returns counters: {"attempted": n, "sent": n, "skipped_dedupe": n, "failed": n}
    """
    counters: dict[str, int] = {
        "attempted": 0,
        "sent": 0,
        "skipped_dedupe": 0,
        "failed": 0,
    }

    reminder_state = ArkReminderState.load()
    alliance = str(match.get("Alliance") or "Unknown")

    for row in roster:
        if (row.get("Status") or "").lower() != "active":
            continue

        uid = row.get("DiscordUserId")
        if not uid:
            logger.debug(
                "[ARK_CANCEL_DM] skipped_missing_discord_id match_id=%s governor=%s",
                match_id,
                row.get("GovernorNameSnapshot"),
            )
            continue

        user_id = int(uid)
        dkey = f"{match_id}|{user_id}|cancelled"

        if reminder_state.was_sent(dkey):
            counters["skipped_dedupe"] += 1
            logger.debug(
                "[ARK_CANCEL_DM] skipped_dedupe match_id=%s user_id=%s",
                match_id,
                user_id,
            )
            continue

        counters["attempted"] += 1

        # CR9: prefer cached lookup before HTTP fetch
        user = client.get_user(user_id)
        if user is None:
            try:
                user = await client.fetch_user(user_id)
            except Exception:
                logger.exception(
                    "[ARK_CANCEL_DM] failed to resolve user match_id=%s user_id=%s",
                    match_id,
                    user_id,
                )
                counters["failed"] += 1
                continue

        match_dt_str = str(match.get("MatchTimeUtc") or "")
        weekend_date = str(match.get("ArkWeekendDate") or "")
        embed = discord.Embed(
            title=f"Ark Match Cancelled — {alliance}",
            description=(
                f"The Ark match scheduled for **{weekend_date}** ({match_dt_str} UTC) "
                f"has been cancelled."
            ),
            color=discord.Color.red(),
        )

        try:
            await user.send(embed=embed)
            counters["sent"] += 1

            # CR2: save state after each successful send
            reminder_state.mark_sent(dkey)
            reminder_state.save()

            logger.info(
                "[ARK_CANCEL_DM] sent match_id=%s user_id=%s",
                match_id,
                user_id,
            )
        except discord.Forbidden:
            # User has DMs disabled — mark as sent to prevent retry spam
            reminder_state.mark_sent(dkey)
            reminder_state.save()
            counters["failed"] += 1
            logger.info(
                "[ARK_CANCEL_DM] dm_blocked match_id=%s user_id=%s",
                match_id,
                user_id,
            )
        except Exception:
            counters["failed"] += 1
            logger.exception(
                "[ARK_CANCEL_DM] failed match_id=%s user_id=%s",
                match_id,
                user_id,
            )

    logger.info(
        "[ARK_CANCEL_DM] dispatch_complete match_id=%s %s",
        match_id,
        counters,
    )
    return counters
