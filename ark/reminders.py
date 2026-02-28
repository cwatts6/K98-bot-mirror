from __future__ import annotations

from datetime import datetime
import logging

from ark.state.ark_state import ArkJsonState

logger = logging.getLogger(__name__)


async def reschedule_match_reminders(
    *,
    match_id: int,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
) -> None:
    """
    Ark reminder reschedule hook (Phase 3B stub).

    This will later integrate Ark reminder logic (Phase 7).
    For now, it logs and provides a consistent call site.
    """
    logger.info(
        "[ARK_REMINDERS] Reschedule requested for match_id=%s match_datetime_utc=%s signup_close_utc=%s",
        match_id,
        match_datetime_utc.isoformat(),
        signup_close_utc.isoformat(),
    )


async def cancel_match_reminders(match_id: int) -> bool:
    """
    Remove reminder state for a match so reminders don't re-send after cancel.

    Returns True if any reminder entries were removed.
    """
    state = ArkJsonState()
    await state.load_async()
    prefix = f"{match_id}|"
    before = len(state.reminders)
    state.reminders = {
        key: val for key, val in (state.reminders or {}).items() if not key.startswith(prefix)
    }
    changed = len(state.reminders) != before
    if changed:
        await state.save_async()
        logger.info("[ARK_REMINDERS] Cleared reminder state for match_id=%s", match_id)
    return changed
