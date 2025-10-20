# rehydrate_views.py

from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

import os

from constants import VIEW_TRACKING_FILE
from embed_utils import LocalTimeToggleView


def load_view_tracker():
    if os.path.exists(VIEW_TRACKING_FILE):
        try:
            with open(VIEW_TRACKING_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[VIEW] Failed to load view tracker: {e}")
    return {}


async def rehydrate_tracked_views(bot):
    view_data = load_view_tracker()
    if not view_data:
        logger.info("[VIEW] No tracked views to rehydrate.")
        return

    for key, entry in view_data.items():
        try:
            channel = await bot.fetch_channel(entry["channel_id"])
            _message = await channel.fetch_message(entry["message_id"])

            # Rebuild event dicts
            events = []
            for e in entry["events"]:
                events.append(
                    {
                        "name": e["name"],
                        "type": e["type"],
                        "start_time": datetime.fromisoformat(e["start_time"]),
                        "description": e.get("description", ""),
                    }
                )

            bot.add_view(LocalTimeToggleView(events, prefix=key, timeout=None))
            logger.info(f"[VIEW] Rehydrated view for: {key}")

        except Exception as e:
            logger.warning(f"[VIEW] Failed to rehydrate view {key}: {e}")


def save_view_tracker(key: str, entry: dict):
    """
    Saves a view tracking entry under a unique key (e.g. 'nextevent', 'nextfight').
    Replaces any existing entry with the same key.
    """
    tracker = {}

    if os.path.exists(VIEW_TRACKING_FILE):
        try:
            with open(VIEW_TRACKING_FILE) as f:
                tracker = json.load(f)
        except Exception:
            tracker = {}

    tracker[key] = entry

    os.makedirs(os.path.dirname(VIEW_TRACKING_FILE), exist_ok=True)
    with open(VIEW_TRACKING_FILE, "w") as f:
        json.dump(tracker, f, indent=2, default=str)


def serialize_event(event):
    return {
        "name": event["name"],
        "type": event["type"],
        "start_time": event["start_time"].isoformat(),
        "description": event.get("description", ""),
    }
