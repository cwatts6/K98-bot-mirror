"""DAL helpers for persistent MGE leadership-board embed state."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from mge.dal.mge_event_dal import fetch_event_for_embed, update_event_leadership_embed_ids

logger = logging.getLogger(__name__)


def _naive_utc(dt: datetime) -> datetime:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


def fetch_leadership_embed_state(event_id: int) -> dict[str, Any]:
    """Return persisted leadership embed message/channel ids for an event."""
    try:
        row = fetch_event_for_embed(event_id)
        if not row:
            return {"message_id": 0, "channel_id": 0}
        return {
            "message_id": int(row.get("LeadershipEmbedMessageId") or 0),
            "channel_id": int(row.get("LeadershipEmbedChannelId") or 0),
        }
    except Exception:
        logger.exception(
            "mge_leadership_dal_fetch_embed_state_failed event_id=%s",
            event_id,
        )
        return {"message_id": 0, "channel_id": 0}


def update_leadership_embed_state(
    *,
    event_id: int,
    message_id: int,
    channel_id: int,
    now_utc: datetime,
) -> bool:
    """Persist leadership embed message/channel ids on dbo.MGE_Events."""
    try:
        ok = update_event_leadership_embed_ids(
            event_id=event_id,
            message_id=message_id,
            channel_id=channel_id,
            now_utc=now_utc,
        )
        if not ok:
            logger.error(
                "mge_leadership_dal_update_embed_state_failed event_id=%s message_id=%s channel_id=%s",
                event_id,
                message_id,
                channel_id,
            )
            return False
        logger.info(
            "mge_leadership_dal_update_embed_state_success event_id=%s message_id=%s channel_id=%s ts_utc=%s",
            event_id,
            message_id,
            channel_id,
            _naive_utc(now_utc).isoformat(),
        )
        return True
    except Exception:
        logger.exception(
            "mge_leadership_dal_update_embed_state_exception event_id=%s",
            event_id,
        )
        return False
