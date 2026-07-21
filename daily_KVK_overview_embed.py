# daily_KVK_overview_embed.py

from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

import os

import discord

from constants import DAILY_KVK_OVERVIEW_TRACKER
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
                    view=LocalTimeToggleView(events=upcoming, prefix=prefix, timeout=None),
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
            embed=embed, view=LocalTimeToggleView(events=upcoming, prefix=prefix, timeout=None)
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
    logger.info("[INFO] Building daily KVK overview embed...")

    TYPE_MAP = {
        "ruins": "ruins",
        "next ruins": "ruins",
        "altar": "altars",  # loader emits 'altar'
        "altars": "altars",
        "next altar fight": "altars",
        "chronicle": "chronicle",
        "major": "major",
    }

    grouped = {"ruins": [], "altars": [], "chronicle": [], "major": []}

    for e in events:
        raw_type = (e.get("type") or "").lower()
        normalized_type = TYPE_MAP.get(raw_type)
        if normalized_type in grouped:
            grouped[normalized_type].append(e)
        else:
            logger.warning(f"[DAILY_KVK_OVERVIEW] Skipping unknown event type: {e}")

    logger.info(f"[INFO] Grouped results: {[ (k, len(v)) for k,v in grouped.items() ]}")

    # ----- Window description helpers -----
    def _fmt_day(d: datetime) -> str:
        return d.strftime("%a %d %b")

    # Compute the window shown in this overview (now → now+4d)
    now = utcnow()
    window_start = now
    window_end = now + timedelta(days=4)

    # You can also derive from the passed events if you prefer the *actual* min/max:
    # if events:
    #     window_start = min(e["start_time"] for e in events)
    #     window_end   = max(e["start_time"] for e in events)

    # Total events shown across all types within the window
    total_in_window = len(events)

    window_str = f"**{_fmt_day(window_start)} → {_fmt_day(window_end)} (UTC)**"
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

    # Helper to format a date header like "Wed 01 Oct"
    def _date_hdr(dt):
        return dt.strftime("%a %d %b")

    # Build each field with date headers and a cap of 6 entries per type
    CAP_PER_TYPE = 6
    for event_type, entries in grouped.items():
        if not entries:
            continue

        entries.sort(key=lambda x: x["start_time"])
        field_name = f"{event_type.capitalize()} • {len(entries)}"

        # Group by calendar date (UTC)
        by_date = {}
        for e in entries:
            dkey = e["start_time"].date()
            by_date.setdefault(dkey, []).append(e)

        # Compose lines with date headers, respecting the cap
        lines = []
        added = 0
        remaining = max(0, len(entries) - CAP_PER_TYPE)

        for dkey in sorted(by_date.keys()):
            if added >= CAP_PER_TYPE:
                break
            day_block = by_date[dkey]
            day_block.sort(key=lambda x: x["start_time"])

            # How many we can still add from this day
            can_take = CAP_PER_TYPE - added
            to_show = day_block[:can_take]

            # Date header
            lines.append(f"**{_date_hdr(to_show[0]['start_time'])}**")

            for e in to_show:
                start_time_str = format_event_time(e["start_time"])
                title = e.get("title") or e.get("name", "(Unnamed Event)")
                lines.append(f"• **{title}**\n{start_time_str}")
                added += 1
                if added >= CAP_PER_TYPE:
                    break

        if remaining > 0:
            lines.append(f"… +{remaining} more in next 4 days")

        value = "\n".join(lines)

        # Discord hard cap safety (1024 chars per field)
        if len(value) > 1024:
            trimmed = []
            total = 0
            for line in lines:
                ln = len(line) + 1
                if total + ln > 1010:
                    break
                trimmed.append(line)
                total += ln
            value = "\n".join(trimmed) + "\n…"

        embed.add_field(name=field_name, value=value, inline=False)

    # Legend footer
    embed.set_footer(
        text="K98 Bot – Daily Schedule • Times shown in UTC — tap ‘Show in my local time’ to convert.",
        icon_url=None,
    )

    logger.info("[INFO] Finished building embed successfully.")
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
