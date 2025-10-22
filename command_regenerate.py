from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

from commands import NextEventView, NextFightView
from constants import VIEW_TRACKING_FILE
from embed_utils import format_event_embed, format_fight_embed
from rehydrate_views import serialize_event


async def regenerate_embed(key: str, channel) -> dict | None:
    try:
        with open(VIEW_TRACKING_FILE, encoding="utf-8") as f:
            views = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    data = views.get(key)
    if not data or "events" not in data:
        return None

    events = data["events"]

    if key == "nextevent":
        embed = format_event_embed(events)
        view = NextEventView(initial_limit=1, prefix="nextevent")
        log_label = "/nextevent"

    elif key == "nextfight":
        embed = format_fight_embed(events)
        view = NextFightView(initial_limit=1, prefix="nextfight")
        log_label = "/nextfight"

    else:
        logger.warning(f"[REGEN] Unknown key in regenerate_embed: {key}")
        return None

    try:
        message = await channel.send(embed=embed, view=view)
        logger.info(f"[REGEN] {log_label} – restored view with {len(events)} event(s)")
        return {
            "message_id": message.id,
            "channel_id": channel.id,
            "created_at": datetime.utcnow().isoformat(),
            "prefix": key,
            "events": [serialize_event(e) for e in events],
        }
    except Exception as e:
        logger.error(f"[REGEN] Failed to post {log_label} embed: {e}")
        return None
