# dm_tracker_utils.py
from __future__ import annotations

import logging

from event_scheduler import (
    dm_scheduled_tracker,
    dm_sent_tracker,
    save_dm_scheduled_tracker,
    save_dm_sent_tracker,
)

logger = logging.getLogger(__name__)


def purge_user_from_dm_sent_tracker(user_id) -> int:
    uid = str(user_id)
    removed = 0
    for event_id, per_user in list(dm_sent_tracker.items()):
        if uid in per_user:
            removed += len(per_user.get(uid) or [])
            per_user.pop(uid, None)
            if not per_user:
                dm_sent_tracker.pop(event_id, None)
    save_dm_sent_tracker()
    logger.info(f"[DM_PURGE] Removed {removed} sent entries for user {uid}")
    return removed


def purge_user_from_dm_scheduled_tracker(user_id) -> int:
    uid = str(user_id)
    removed = 0
    for event_id, per_user in list(dm_scheduled_tracker.items()):
        if uid in per_user:
            removed += len(per_user.get(uid) or set())
            per_user.pop(uid, None)
            if not per_user:
                dm_scheduled_tracker.pop(event_id, None)
    save_dm_scheduled_tracker()
    logger.info(f"[DM_PURGE] Removed {removed} scheduled entries for user {uid}")
    return removed


def purge_user_from_all_dm_trackers(user_id) -> tuple[int, int]:
    """
    Convenience wrapper used by /unsubscribe and Unsubscribe button.
    Returns (sent_removed, scheduled_removed).
    """
    sent_removed = purge_user_from_dm_sent_tracker(user_id)
    sched_removed = purge_user_from_dm_scheduled_tracker(user_id)
    logger.info(
        f"[DM_PURGE] Completed purge for user {user_id} | sent={sent_removed}, scheduled={sched_removed}"
    )
    return sent_removed, sched_removed
