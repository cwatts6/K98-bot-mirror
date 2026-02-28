# event_embed_manager.py
import asyncio
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

import os

import discord

from constants import EMBED_TRACKING_FILE
from embed_utils import LocalTimeToggleView, format_event_time, sanitize_view_prefix
from event_cache import get_all_upcoming_events

# Use centralized event helpers
from event_utils import serialize_event
from file_utils import atomic_write_json, run_blocking_in_thread
from utils import ensure_aware_utc, utcnow

embed_tracker = {}  # {event_id: {"message_id": int, "prefix": str}}
event_expiry_buffer = timedelta(hours=12)


def load_embed_tracker():
    global embed_tracker
    if os.path.exists(EMBED_TRACKING_FILE):
        try:
            with open(EMBED_TRACKING_FILE, encoding="utf-8") as f:
                loaded_data = json.load(f)
                # Force all keys to str
                embed_tracker = {str(k): v for k, v in loaded_data.items()}
        except Exception as e:
            logger.warning("[EMBED_TRACKER] Failed to load tracker: %s", e)
            embed_tracker = {}


async def rehydrate_live_event_views(bot, event_channel_id):
    # Ensure tracker is loaded before using it
    load_embed_tracker()
    try:
        channel = await bot.fetch_channel(event_channel_id)
    except Exception as e:
        logger.warning("[REHYDRATE] Cannot fetch event channel %s: %s", event_channel_id, e)
        return

    now = utcnow()
    upcoming = get_all_upcoming_events()
    events_48h = [
        e
        for e in upcoming
        if now - timedelta(hours=1)
        <= ensure_aware_utc(e["start_time"])
        <= now + timedelta(hours=48)
    ]

    for event in events_48h:
        event_id = make_event_id(event)
        entry = embed_tracker.get(event_id)
        if not entry:
            continue

        # Legacy format fallback
        if isinstance(entry, int):
            msg_id = entry
            prefix = f"countdown_{event['name'].lower().replace(' ', '_')}"
        else:
            msg_id = entry["message_id"]
            prefix = entry.get("prefix", f"countdown_{event['name'].lower().replace(' ', '_')}")

        # Sanitize prefix consistently using shared helper
        safe_prefix = sanitize_view_prefix(prefix, max_len=64)

        try:
            _msg = await channel.fetch_message(msg_id)
            bot.add_view(LocalTimeToggleView([event], prefix=safe_prefix, timeout=None))
            logger.info(
                "[REHYDRATE] Re-registered view for event_id=%s with prefix=%s",
                event_id,
                safe_prefix,
            )
        except Exception as e:
            logger.warning("[REHYDRATE] Failed to rehydrate view for %s: %s", event_id, e)
        # micro-yield to keep loop responsive
        await asyncio.sleep(0)


def save_embed_tracker():
    """Atomically persist the embed tracker (UTF-8) to avoid partial writes."""
    try:
        payload = {str(k): v for k, v in embed_tracker.items()}
        atomic_write_json(EMBED_TRACKING_FILE, payload, ensure_parent_dir=True)
    except Exception as e:
        logger.warning("[EMBED_TRACKER] Failed to save tracker: %s", e)


async def save_embed_tracker_async():
    if run_blocking_in_thread:
        await run_blocking_in_thread(save_embed_tracker, name="save_embed_tracker")
        return

    await asyncio.to_thread(save_embed_tracker)


def get_event_thumbnail(event_type: str) -> str:
    raw = (event_type or "").lower()
    typ = {
        "next ruins": "ruins",
        "ruins": "ruins",
        "next altar fight": "altars",
        "altar": "altars",
        "altars": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }.get(raw, raw)
    thumbs = {
        "ruins": "https://i.ibb.co/CsK1GNVv/Ruins.jpg",
        "altars": "https://i.ibb.co/cKxCkTpW/altar.jpg",
        "major": "https://i.ibb.co/ksjMLzPN/rise-of-kingdoms-best-leonidas-builds.jpg",
        "chronicle": "https://i.ibb.co/CK0Lr5vL/chronicle-event.png",
    }
    return thumbs.get(typ, "https://i.ibb.co/0jM8R7GW/kvk-mistakes.jpg")


def make_event_id(event):
    raw_type = (event.get("type") or "").lower()
    typ = {
        "next ruins": "ruins",
        "ruins": "ruins",
        "next altar fight": "altars",
        "altar": "altars",
        "altars": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }.get(raw_type, raw_type)

    name_tok = (
        str(event.get("name") or event.get("title") or "").strip().lower().replace(" ", "_")[:64]
    )

    # Use centralized serializer to obtain a canonical ISO8601 UTC timestamp string
    try:
        serialized = serialize_event(event)
        ts = serialized.get("start_time")
    except Exception:
        # Fallback: ensure aware datetime then isoformat
        try:
            ts = ensure_aware_utc(event["start_time"]).isoformat()
        except Exception:
            ts = str(event.get("start_time"))

    return f"{typ}:{name_tok}:{ts}"


async def update_live_event_embeds(bot, event_channel_id):
    load_embed_tracker()
    now = utcnow()
    try:
        upcoming = get_all_upcoming_events()
    except Exception as e:
        logger.error("[EMBED] Failed to load upcoming events: %s", e)
        return

    # Filter to 48h window
    events_48h = [
        e
        for e in upcoming
        if now - timedelta(hours=1)
        <= ensure_aware_utc(e["start_time"])
        <= now + timedelta(hours=48)
    ]
    if not events_48h:
        logger.info("[EMBED] No events in the next 48h — skipping embed update.")
        return

    still_valid_ids = set()

    try:
        channel = await bot.fetch_channel(event_channel_id)
    except Exception as e:
        logger.warning("[EMBED] Cannot fetch event channel %s: %s", event_channel_id, e)
        return

    # Filter to 48h window
    for event in events_48h:
        event_id = make_event_id(event)
        still_valid_ids.add(event_id)

        try:
            entry = embed_tracker.get(event_id)
            msg_id = entry["message_id"] if isinstance(entry, dict) else entry
            prefix = (
                entry["prefix"]
                if isinstance(entry, dict)
                else f"countdown_{event['name'].lower().replace(' ', '_')}"
            )

            # Sanitize prefix consistently
            safe_prefix = sanitize_view_prefix(prefix, max_len=64)

            embed = build_event_embed(event)

            if msg_id:
                try:
                    msg = await channel.fetch_message(msg_id)
                    current_embed = msg.embeds[0] if msg.embeds else None

                    def extract_embed_contents(e):
                        return {
                            "title": e.title or "",
                            "description": e.description or "",
                            "fields": [(f.name, f.value) for f in e.fields],
                            "color": e.color.value if e.color else 0,
                            "thumbnail": e.thumbnail.url if e.thumbnail else "",
                        }

                    if current_embed and extract_embed_contents(
                        current_embed
                    ) == extract_embed_contents(embed):
                        logger.debug("[EMBED] Embed unchanged, refreshing view.")
                        await msg.edit(
                            embed=embed,
                            view=LocalTimeToggleView([event], prefix=safe_prefix, timeout=None),
                        )
                        await asyncio.sleep(0)
                        continue

                    logger.info(
                        "[EMBED] Updating embed for event_id=%s, msg_id=%s", event_id, msg_id
                    )
                    await msg.edit(
                        embed=embed,
                        view=LocalTimeToggleView([event], prefix=safe_prefix, timeout=None),
                    )
                    logger.info(
                        "[EMBED] Updated embed for event: %s",
                        event.get("title") or event.get("name", "Unnamed"),
                    )

                except discord.NotFound:
                    logger.warning(
                        "[EMBED] Previously pinned message for %s not found. Recreating.", event_id
                    )
                    msg = await channel.send(
                        embed=embed,
                        view=LocalTimeToggleView([event], prefix=safe_prefix, timeout=None),
                    )
                    embed_tracker[event_id] = msg.id

            else:
                msg = await channel.send(
                    embed=embed, view=LocalTimeToggleView([event], prefix=safe_prefix, timeout=None)
                )
                embed_tracker[event_id] = msg.id

        except Exception as e:
            logger.error("[EMBED] Failed to process event %s: %s", event_id, e)
        # yield inside the loop
        await asyncio.sleep(0)

    # 🔻 Clean up expired events with safe unpin/delete
    expired_ids = set(embed_tracker.keys()) - still_valid_ids
    logger.info("[CLEANUP] Expired event IDs: %s", expired_ids)
    for old_event_id in expired_ids:
        msg_id = embed_tracker.get(old_event_id)
        try:
            old_msg = await channel.fetch_message(msg_id)
            logger.debug(
                "[CLEANUP] Attempting to delete message_id=%s for expired event_id=%s",
                msg_id,
                old_event_id,
            )

            try:
                await old_msg.delete()
                logger.info("[CLEANUP] Deleted expired event embed: %s", old_event_id)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(
                    "[CLEANUP] Failed to delete message for expired event %s: %s", old_event_id, e
                )

        except discord.NotFound:
            logger.warning(
                "[CLEANUP] Could not clean up expired event %s: Message already deleted.",
                old_event_id,
            )
        except Exception as e:
            logger.warning(
                "[CLEANUP] Failed to delete message for expired event %s: %s", old_event_id, e
            )
        finally:
            embed_tracker.pop(old_event_id, None)

        # yield inside cleanup loop
        await asyncio.sleep(0)

    logger.info("[SAVE] Writing embed_tracker with %d items...", len(embed_tracker))
    await save_embed_tracker_async()
    logger.info("[EMBED] Live event countdown embed update completed.")


def build_event_embed(event):
    timestamp = int(ensure_aware_utc(event["start_time"]).timestamp())
    now = utcnow()
    time_remaining = ensure_aware_utc(event["start_time"]) - now

    # Determine embed color based on how close the event is
    if time_remaining > timedelta(hours=12):
        color = 0x3498DB  # Blue
    elif time_remaining > timedelta(hours=4):
        color = 0x2ECC71  # Green
    elif time_remaining > timedelta(hours=1):
        color = 0xE67E22  # Orange
    else:
        color = 0xE74C3C  # Red

    # Build event timing strings
    utc_text = format_event_time(event["start_time"])
    extra_description = (
        f"\ud83d\udcd6 {event.get('description')}\n\n" if event.get("description") else ""
    )

    # Description with invisible character to force visual update
    description = f"{extra_description}" f"**Starts <t:{timestamp}:R>**\n" f"On: {utc_text}\n\u200b"

    title = f"\ud83d\udcc5 {event.get('name') or event.get('title') or 'Unnamed Event'}"
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_thumbnail(url=get_event_thumbnail(event["type"]))
    embed.set_footer(text="This event will automatically update and expire")
    return embed
