from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any

import discord

from constants import DATA_DIR
from event_calendar.runtime_cache import filter_events, load_runtime_cache, stale_banner
from file_utils import emit_telemetry_event
from ui.views.calendar import (
    CalendarLocalTimeToggleView,
    build_pinned_calendar_embed,
    cache_footer,
)

logger = logging.getLogger(__name__)

_TRACKER_PATH = Path(DATA_DIR) / "calendar_pinned_tracker.json"


def _load_tracker() -> dict[str, Any]:
    try:
        if _TRACKER_PATH.exists():
            return json.loads(_TRACKER_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("[CALENDAR][PINNED] tracker load failed")
    return {}


def now_utc() -> datetime:
    return datetime.now(UTC)


def _save_tracker(data: dict[str, Any]) -> None:
    try:
        _TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TRACKER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("[CALENDAR][PINNED] tracker save failed")


def _build_view(cache_state: dict[str, Any]) -> CalendarLocalTimeToggleView:
    events = filter_events(
        cache_state.get("events", []),
        now=now_utc(),
        days=30,
        event_type="all",
        importance="all",
    )
    return CalendarLocalTimeToggleView(
        events=events,
        prefix="calendar_pinned",
        timeout=None,
    )


async def update_calendar_embed(
    bot: discord.Client,
    channel_id: int,
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Create or edit one pinned calendar message in-place.
    Returns structured status dict.
    """
    cache_state = load_runtime_cache()
    banner = stale_banner(cache_state)

    if not cache_state.get("ok"):
        logger.warning("[CALENDAR][PINNED] cache unavailable; preserving existing message")
        return {
            "ok": False,
            "status": "cache_unavailable_preserved",
            "details": banner or "cache unavailable",
        }

    events = filter_events(
        cache_state.get("events", []),
        now=now_utc(),
        days=30,
        event_type="all",
        importance="all",
    )
    footer = cache_footer(cache_state)
    embed = build_pinned_calendar_embed(events=events, footer=footer)
    if banner:
        embed.description = banner

    view = _build_view(cache_state)
    tracker = _load_tracker()

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception as e:
            logger.exception("[CALENDAR][PINNED] channel fetch failed")
            return {"ok": False, "status": "channel_not_found", "details": str(e)}

    message_id = tracker.get("message_id")
    msg = None

    if message_id and not force_refresh:
        try:
            msg = await channel.fetch_message(int(message_id))
            await msg.edit(embed=embed, view=view)
            _save_tracker(
                {
                    "channel_id": int(channel_id),
                    "message_id": int(msg.id),
                    "updated_at_utc": now_utc().isoformat(),
                }
            )
            if not getattr(msg, "pinned", False):
                try:
                    await msg.pin(reason="Pinned calendar embed")
                except Exception:
                    logger.debug("[CALENDAR][PINNED] repin failed", exc_info=True)
            emit_telemetry_event(
                {"event": "calendar_pinned_embed_update", "status": "edited", "ok": True}
            )
            return {"ok": True, "status": "edited", "message_id": msg.id, "events": len(events)}
        except Exception:
            logger.warning("[CALENDAR][PINNED] tracked message missing; recreating", exc_info=True)

    try:
        msg = await channel.send(embed=embed, view=view)
        try:
            await msg.pin(reason="Pinned calendar embed")
        except Exception:
            logger.debug("[CALENDAR][PINNED] initial pin failed", exc_info=True)

        tracker["channel_id"] = channel_id
        tracker["message_id"] = msg.id
        _save_tracker(tracker)

        emit_telemetry_event(
            {"event": "calendar_pinned_embed_update", "status": "created", "ok": True}
        )
        return {"ok": True, "status": "created", "message_id": msg.id, "events": len(events)}
    except Exception as e:
        logger.exception("[CALENDAR][PINNED] send failed")
        emit_telemetry_event(
            {"event": "calendar_pinned_embed_update", "status": "failed_send", "ok": False}
        )
        return {"ok": False, "status": "failed_send", "details": str(e)}


async def rehydrate_pinned_calendar_view(bot: discord.Client) -> dict[str, Any]:
    tracker = _load_tracker()
    channel_id = tracker.get("channel_id")
    message_id = tracker.get("message_id")
    if not channel_id or not message_id:
        return {"ok": False, "status": "missing_tracker"}

    try:
        channel = bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
        msg = await channel.fetch_message(int(message_id))
    except Exception:
        logger.warning(
            "[CALENDAR][PINNED] rehydrate target missing; clearing tracker", exc_info=True
        )
        _save_tracker({})
        return {"ok": False, "status": "message_or_channel_missing"}

    cache_state = load_runtime_cache()
    if not cache_state.get("ok"):
        return {"ok": False, "status": "cache_unavailable"}

    view = _build_view(cache_state)
    try:
        await msg.edit(view=view)
        return {"ok": True, "status": "rehydrated"}
    except Exception as e:
        logger.exception("[CALENDAR][PINNED] rehydrate edit failed")
        return {"ok": False, "status": "rehydrate_failed", "details": str(e)}
