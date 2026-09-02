# daily_KVK_overview_embed.py

from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

import os

import discord

from constants import DAILY_KVK_OVERVIEW_TRACKER
from core.discord_embed_limits import (
    MAX_FIELD_VALUE_CHARACTERS,
    require_valid_embed_payload,
    truncate_text,
    validate_embed_payload,
)
from embed_utils import LocalTimeToggleView, format_event_time
from event_cache import get_all_upcoming_events
from event_utils import serialize_event

# Use the safer, centralized retrying save helper (delegates to file_utils.run_with_retries)
from rehydrate_views import save_view_tracker_with_retries
from stats_alerts.kvk_meta import is_currently_kvk
from utils import utcnow  # tz-aware UTC


async def post_or_update_daily_KVK_overview(bot, event_channel_id):
    if not is_currently_kvk():
        logger.info("[DAILY_KVK_OVERVIEW] Kingdom is not in KVK. Skipping daily KVK overview.")
        await remove_daily_KVK_overview_embed(bot, event_channel_id)
        return

    try:
        now = utcnow()
        next_days = now + timedelta(days=4)
        # Use future-only list (already sorted) from in-memory cache
        events = get_all_upcoming_events()
        upcoming = [e for e in events if e["start_time"] <= next_days]

        if not upcoming:
            logger.info(
                "[DAILY_KVK_OVERVIEW] No upcoming KVK events in next 4 days. Skipping update."
            )
            return

        embed = build_daily_KVK_overview_embed(upcoming)
        if not isinstance(embed, discord.Embed):
            logger.error("[DAILY_KVK_OVERVIEW] Embed builder returned None or invalid type!")
            return
        channel = await bot.fetch_channel(event_channel_id)
        msg_id = load_existing_daily_KVK_overview_id()

        if msg_id:
            try:
                msg = await channel.fetch_message(msg_id)
                prefix = "daily_kvk_overview"
                await msg.edit(
                    embed=embed,
                    view=LocalTimeToggleView(
                        events=upcoming,
                        prefix=prefix,
                        timeout=None,
                        complete_event_packing=True,
                    ),
                )

                # Save view for rehydration (use centralized retrying helper)
                await save_view_tracker_with_retries(
                    "daily_kvk_overview",
                    {
                        "message_id": msg.id,
                        "channel_id": channel.id,
                        "created_at": utcnow().isoformat(),
                        "events": [serialize_event(e) for e in upcoming],
                        "prefix": prefix,
                    },
                )

                logger.info("[DAILY_KVK_OVERVIEW] Updated existing daily KVK overview embed.")
                return
            except discord.NotFound:
                logger.warning(
                    "[DAILY_KVK_OVERVIEW] Previous KVK overview message not found. Reposting."
                )

        # Create new message if not found
        prefix = "daily_kvk_overview"
        new_msg = await channel.send(
            embed=embed,
            view=LocalTimeToggleView(
                events=upcoming,
                prefix=prefix,
                timeout=None,
                complete_event_packing=True,
            ),
        )
        await new_msg.pin()
        save_daily_KVK_overview_id(new_msg.id)

        # Save view for rehydration (use centralized retrying helper)
        await save_view_tracker_with_retries(
            "daily_kvk_overview",
            {
                "message_id": new_msg.id,
                "channel_id": channel.id,
                "created_at": utcnow().isoformat(),
                "events": [serialize_event(e) for e in upcoming],
                "prefix": prefix,
            },
        )

        logger.info("[DAILY_KVK_OVERVIEW] Posted new daily KVK overview embed.")

    except Exception:
        logger.exception("[DAILY_KVK_OVERVIEW] Failed to post or update embed")


async def remove_daily_KVK_overview_embed(bot, event_channel_id):
    msg_id = load_existing_daily_KVK_overview_id()
    if not msg_id:
        return
    try:
        channel = await bot.fetch_channel(event_channel_id)
        msg = await channel.fetch_message(msg_id)
        await msg.unpin()
        await msg.delete()
        logger.info("[DAILY_KVK_OVERVIEW] Unpinned and deleted outdated KVK overview embed.")
    except discord.Forbidden:
        logger.warning("[DAILY_OVERVIEW] Missing permissions to unpin/delete daily overview.")
    except discord.NotFound:
        logger.warning("[DAILY_OVERVIEW] Message already gone when attempting to remove.")
    except Exception:
        logger.exception("[DAILY_OVERVIEW] Failed to remove embed")
    finally:
        try:
            os.remove(DAILY_KVK_OVERVIEW_TRACKER)
        except Exception:
            pass


# ---- Embed Generator ----
def build_daily_KVK_overview_embed(events):
    type_map = {
        "ruins": "ruins",
        "next ruins": "ruins",
        "altar": "altars",
        "altars": "altars",
        "next altar fight": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }
    grouped = {"ruins": [], "altars": [], "chronicle": [], "major": []}
    for event in events:
        raw_type = (event.get("type") or "").lower()
        normalized_type = type_map.get(raw_type)
        if normalized_type in grouped:
            grouped[normalized_type].append(event)
        else:
            logger.warning("[DAILY_KVK_OVERVIEW] Skipping unknown event type")

    now = utcnow()
    window_end = now + timedelta(days=4)
    total_in_window = len(events)
    window_str = f"**{now.strftime('%a %d %b')} → {window_end.strftime('%a %d %b')} (UTC)**"
    desc = (
        f"{window_str}\n"
        f"{total_in_window} upcoming event{'s' if total_in_window != 1 else ''} in the next 4 days.\n\n"
        f"Use the toggle below to view times in your local timezone."
    )

    embed = discord.Embed(
        title="📊 KVK Event Overview – Next 4 Days",
        description=desc,
        color=discord.Color.teal(),
        timestamp=utcnow(),
    )
    embed.set_footer(
        text="K98 Bot – Daily Schedule • Times shown in UTC — tap ‘Show in my local time’ to convert.",
        icon_url=None,
    )

    for entries in grouped.values():
        entries.sort(key=lambda item: item["start_time"])
    shown = {key: min(6, len(entries)) for key, entries in grouped.items()}

    def event_block(event):
        start_text = format_event_time(event["start_time"])
        date_header = event["start_time"].strftime("%a %d %b")
        raw_title = " ".join(
            str(event.get("title") or event.get("name") or "(Unnamed Event)").split()
        )
        fixed_length = len(f"**{date_header}**\n• ****\n{start_text}")
        title = truncate_text(raw_title, MAX_FIELD_VALUE_CHARACTERS - fixed_length)
        return f"**{date_header}**\n• **{title}**\n{start_text}"

    def event_was_compacted(event):
        start_text = format_event_time(event["start_time"])
        date_header = event["start_time"].strftime("%a %d %b")
        raw_title = " ".join(
            str(event.get("title") or event.get("name") or "(Unnamed Event)").split()
        )
        fixed_length = len(f"**{date_header}**\n• ****\n{start_text}")
        return len(raw_title) > MAX_FIELD_VALUE_CHARACTERS - fixed_length

    def build_fields():
        fields = []
        for event_type, entries in grouped.items():
            if not entries:
                continue
            base_name = f"{event_type.capitalize()} • {len(entries)}"
            type_fields = []
            for event in entries[: shown[event_type]]:
                block = event_block(event)
                if (
                    type_fields
                    and len(f"{type_fields[-1][1]}\n\n{block}") <= MAX_FIELD_VALUE_CHARACTERS
                ):
                    name, value = type_fields[-1]
                    type_fields[-1] = (name, f"{value}\n\n{block}")
                else:
                    suffix = " (continued)" if type_fields else ""
                    type_fields.append((f"{base_name}{suffix}", block))

            omitted = len(entries) - shown[event_type]
            if omitted:
                marker = f"… {omitted} more {event_type} events in the next 4 days — use Local Time"
                if (
                    type_fields
                    and len(f"{type_fields[-1][1]}\n{marker}") <= MAX_FIELD_VALUE_CHARACTERS
                ):
                    name, value = type_fields[-1]
                    type_fields[-1] = (name, f"{value}\n{marker}")
                else:
                    type_fields.append((f"{base_name} (continued)", marker))
            fields.extend(type_fields)
        return fields

    fields = build_fields()
    while validate_embed_payload(
        {
            **embed.to_dict(),
            "fields": [{"name": name, "value": value, "inline": False} for name, value in fields],
        }
    ):
        removable = next((key for key in reversed(tuple(grouped)) if shown[key] > 0), None)
        if removable is None:
            break
        shown[removable] -= 1
        fields = build_fields()

    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)

    usage = require_valid_embed_payload(embed)
    compacted = sum(
        event_was_compacted(event)
        for key, entries in grouped.items()
        for event in entries[: shown[key]]
    )
    omitted = sum(len(entries) - shown[key] for key, entries in grouped.items())
    logger.info(
        "[EMBED_PAYLOAD] renderer=daily_kvk fields=%d chars=%d max_field_value=%d compacted_events=%d omitted_events=%d",
        usage.field_counts[0],
        usage.total_characters,
        max((len(field.value or "") for field in embed.fields), default=0),
        compacted,
        omitted,
    )
    return embed


# ---- Tracker for pin/update ----
def load_existing_daily_KVK_overview_id():
    if os.path.exists(DAILY_KVK_OVERVIEW_TRACKER):
        try:
            with open(DAILY_KVK_OVERVIEW_TRACKER) as f:
                return json.load(f).get("message_id")
        except Exception:
            pass
    return None


def save_daily_KVK_overview_id(msg_id):
    with open(DAILY_KVK_OVERVIEW_TRACKER, "w") as f:
        json.dump({"message_id": msg_id}, f)
