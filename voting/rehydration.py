from __future__ import annotations

import logging
from typing import Any

from ui.views.vote_post_view import VotePostView
from voting import dal

logger = logging.getLogger(__name__)


async def rehydrate_vote_post_views(bot: Any) -> dict[str, int]:
    summary = {"rehydrated": 0, "failed": 0}
    snapshots = await dal.list_open_vote_posts()
    if not snapshots:
        logger.info("vote_view_rehydration_no_open_votes")
        return summary

    for snapshot in snapshots:
        if snapshot.message_id is None:
            continue
        try:
            bot.add_view(VotePostView(snapshot), message_id=int(snapshot.message_id))
            summary["rehydrated"] += 1
            logger.info(
                "vote_view_rehydrated vote_post_id=%s channel_id=%s message_id=%s",
                snapshot.vote_post_id,
                snapshot.channel_id,
                snapshot.message_id,
            )
        except Exception:
            summary["failed"] += 1
            logger.exception(
                "vote_view_rehydration_failed vote_post_id=%s channel_id=%s message_id=%s",
                snapshot.vote_post_id,
                snapshot.channel_id,
                snapshot.message_id,
            )
    logger.info(
        "vote_view_rehydration_complete rehydrated=%s failed=%s",
        summary["rehydrated"],
        summary["failed"],
    )
    return summary
