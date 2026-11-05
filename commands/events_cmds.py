# commands/events_cmds.py
from __future__ import annotations

from datetime import UTC, datetime
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, KVK_EVENT_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from daily_KVK_overview_embed import post_or_update_daily_KVK_overview
from decoraters import is_admin_and_notify_channel, track_usage
from embed_utils import format_event_embed, format_fight_embed
from event_cache import (
    get_upcoming_event_cache_snapshot,
    is_cache_stale,
    refresh_event_cache_result,
)
from event_embed_manager import update_live_event_embeds
from event_utils import serialize_event
from rehydrate_views import save_view_tracker_with_retries as save_view_tracker_async
from services.event_cache_service import refresh_message
from ui.views.events_views import NextEventView, NextFightView
from utils import get_next_events, get_next_fights, utcnow
from versioning import versioned

logger = logging.getLogger(__name__)
UTC = UTC


def register_events(bot: ext_commands.Bot) -> None:
    events_group = discord.SlashCommandGroup(
        "events",
        "Event admin controls",
        guild_ids=[GUILD_ID],
    )

    @bot.slash_command(
        name="next_kvk_fight",
        description="Shows the next KVK fight or up to the next 3 fights!",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @track_usage()
    async def next_kvk_fight(ctx):
        logger.info("[COMMAND] /next_kvk_fight used")
        await safe_defer(ctx, ephemeral=False)

        try:
            all_fights = get_next_fights(3) or []
            if not all_fights:
                await ctx.interaction.edit_original_response(
                    content="Fighting finished just chill now!"
                )
                return

            initial_limit = 1
            embed = format_fight_embed(all_fights[:initial_limit])
            prefix = "next_kvk_fight"
            view = NextFightView(initial_limit=initial_limit, prefix=prefix)

            await ctx.interaction.edit_original_response(embed=embed, view=view)

            try:
                sent_msg = await ctx.interaction.original_response()
                if hasattr(view, "message"):
                    view.message = sent_msg
            except Exception:
                sent_msg = None

            try:
                await save_view_tracker_async(
                    "next_kvk_fight",
                    {
                        "message_id": getattr(sent_msg, "id", None),
                        "channel_id": getattr(
                            getattr(sent_msg, "channel", None),
                            "id",
                            ctx.channel.id if ctx.channel else None,
                        ),
                        "prefix": prefix,
                        "created_at": utcnow().isoformat(),
                        "initial_limit": initial_limit,
                        "available": len(all_fights),
                        "events": [
                            serialize_event(e)
                            for e in (getattr(view, "fights", None) or all_fights)
                        ],
                    },
                )
            except Exception as e:
                logger.exception("[next_kvk_fight] save_view_tracker_async failed: %s", e)

        except Exception as e:
            logger.exception("[COMMAND] /next_kvk_fight failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Unable to build next fights: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )

    @bot.slash_command(
        name="next_kvk_event",
        description="Show the next upcoming KVK events",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def next_kvk_event(ctx):
        logger.info("[COMMAND] /next_kvk_event used")
        await safe_defer(ctx, ephemeral=False)

        try:
            all_events = get_next_events(limit=5) or []
            if not all_events:
                await ctx.interaction.edit_original_response(content="No upcoming events found.")
                return

            initial_limit = 1
            embed = format_event_embed(all_events[:initial_limit])
            prefix = "next_kvk_event"
            view = NextEventView(initial_limit=initial_limit, prefix=prefix, preloaded=all_events)

            await ctx.interaction.edit_original_response(embed=embed, view=view)

            try:
                sent_msg = await ctx.interaction.original_response()
                if hasattr(view, "message"):
                    view.message = sent_msg
            except Exception:
                sent_msg = None

            try:
                await save_view_tracker_async(
                    "next_kvk_event",
                    {
                        "message_id": getattr(sent_msg, "id", None),
                        "channel_id": getattr(
                            getattr(sent_msg, "channel", None),
                            "id",
                            ctx.channel.id if ctx.channel else None,
                        ),
                        "prefix": prefix,
                        "created_at": utcnow().isoformat(),
                        "initial_limit": initial_limit,
                        "available": len(all_events),
                        "events": [serialize_event(e) for e in (view.events or all_events)],
                    },
                )
            except Exception as e:
                logger.exception("[next_kvk_event] save_view_tracker_async failed: %s", e)

        except Exception as e:
            logger.exception("[COMMAND] /next_kvk_event failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Unable to build events: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )

    @events_group.command(
        name="refresh",
        description="Manually refresh the event cache and countdowns",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_events(ctx):
        await safe_defer(ctx, ephemeral=True)
        logger.info("[COMMAND] /refresh_events used by %s", ctx.author)

        started = datetime.now(UTC)
        try:
            result = await refresh_event_cache_result(observation_seconds=10.0)
            publication = "Countdown publication was not attempted."
            if (
                result.status not in {"pending", "closed", "cancelled"}
                and get_upcoming_event_cache_snapshot().ok
            ):
                await update_live_event_embeds(bot, KVK_EVENT_CHANNEL_ID)
                publication = (
                    "Countdown publication attempted; delivery is not independently verified."
                )
            ts_text = (
                result.last_refreshed.strftime("%Y-%m-%d %H:%M:%S UTC")
                if result.last_refreshed
                else "unavailable"
            )
            dur = (datetime.now(UTC) - started).total_seconds()
            await ctx.interaction.edit_original_response(
                content=f"{refresh_message(result)}\n{publication}\n"
                f"Cache timestamp: `{ts_text}` | {dur:.1f}s"
            )

        except Exception as e:
            logger.exception("[COMMAND ERROR] /refresh_events failed.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh event cache or embeds:\n```{type(e).__name__}: {e}```"
            )

    @events_group.command(
        name="refresh_kvk_overview",
        description="📅 Refresh the Daily KVK Overview embed manually",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def refresh_kvk_overview(ctx):
        await safe_defer(ctx, ephemeral=True)
        logger.info("[COMMAND] /refresh_kvk_overview used by %s", ctx.author)

        started = utcnow()
        try:
            result = None
            if is_cache_stale():
                result = await refresh_event_cache_result(observation_seconds=10.0)
            snapshot = get_upcoming_event_cache_snapshot()
            cache_text = (
                refresh_message(result) if result else "Using the previously loaded event cache."
            )
            publication = "Overview publication was not attempted."
            if snapshot.ok and (
                result is None or result.status not in {"pending", "closed", "cancelled"}
            ):
                disposition = await post_or_update_daily_KVK_overview(
                    bot, event_channel_id=KVK_EVENT_CHANNEL_ID
                )
                publication = (
                    f"Overview disposition: {disposition}. Live visual acceptance is separate."
                )
            ts_text = (
                snapshot.last_refreshed.strftime("%Y-%m-%d %H:%M:%S UTC")
                if snapshot.last_refreshed
                else "unavailable"
            )
            dur = (utcnow() - started).total_seconds()
            await ctx.interaction.edit_original_response(
                content=f"{cache_text}\n{publication}\nCache timestamp: `{ts_text}` | {dur:.1f}s"
            )

        except Exception as e:
            logger.exception("[COMMAND ERROR] /refresh_kvk_overview failed.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh KVK overview:\n```{type(e).__name__}: {e}```"
            )

    bot.add_application_command(events_group)
