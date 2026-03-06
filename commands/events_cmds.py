# commands/events_cmds.py
from __future__ import annotations

from datetime import UTC, datetime
import logging

from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, KVK_EVENT_CHANNEL_ID
from core.interaction_safety import safe_command, safe_defer
from daily_KVK_overview_embed import post_or_update_daily_KVK_overview
from decoraters import is_admin_and_notify_channel, track_usage
from embed_utils import format_event_embed, format_fight_embed
from event_cache import get_last_refreshed, is_cache_stale, refresh_event_cache
from event_embed_manager import update_live_event_embeds
from event_utils import serialize_event
from rehydrate_views import save_view_tracker_with_retries as save_view_tracker_async
from ui.views.events_views import NextEventView, NextFightView
from utils import get_next_events, get_next_fights, utcnow
from versioning import versioned

logger = logging.getLogger(__name__)
UTC = UTC


def register_events(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="nextfight",
        description="Shows the next fight or up to the next 3 fights!",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def nextfight(ctx):
        logger.info("[COMMAND] /nextfight used")
        await safe_defer(ctx, ephemeral=False)

        try:
            # Get up to 3 upcoming fight-worthy events in one shot.
            all_fights = get_next_fights(3) or []
            if not all_fights:
                await ctx.interaction.edit_original_response(
                    content="Fighting finished just chill now!"
                )
                return

            # Show just the next fight in the initial embed.
            initial_limit = 1
            embed = format_fight_embed(all_fights[:initial_limit])
            prefix = "nextfight"

            # Build the view. If your view can take the list/availability, pass it.
            # (These setters are optional; guarded with hasattr so it won't break older code.)
            view = NextFightView(initial_limit=initial_limit, prefix=prefix)
            # if hasattr(view, "set_available"):
            # view.set_available(len(all_fights))
            # if hasattr(view, "set_events"):
            # view.set_events(all_fights)

            # Send initial response
            await ctx.interaction.edit_original_response(embed=embed, view=view)

            # Bind the sent message back to the view (so it can safely edit itself later)
            try:
                sent_msg = await ctx.interaction.original_response()
                if hasattr(view, "message"):
                    view.message = sent_msg
            except Exception:
                sent_msg = None

            # Persist for rehydration (include a bit more context)
            try:
                await save_view_tracker_async(
                    "nextfight",
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
                logger.exception("[nextfight] save_view_tracker_async failed: %s", e)

        except Exception as e:
            logger.exception("[COMMAND] /nextfight failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Unable to build next fights: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )

    @bot.slash_command(
        name="nextevent", description="Show the next upcoming events", guild_ids=[GUILD_ID]
    )
    @versioned("v1.03")
    @safe_command
    @track_usage()
    async def nextevent(ctx):
        logger.info("[COMMAND] /nextevent used")
        await safe_defer(ctx, ephemeral=False)

        try:
            all_events = get_next_events(limit=5) or []
            if not all_events:
                await ctx.interaction.edit_original_response(content="No upcoming events found.")
                return

            initial_limit = 1
            embed = format_event_embed(all_events[:initial_limit])
            prefix = "nextevent"
            view = NextEventView(initial_limit=initial_limit, prefix=prefix, preloaded=all_events)

            await ctx.interaction.edit_original_response(embed=embed, view=view)

            # Bind message so the view can safely edit later
            try:
                sent_msg = await ctx.interaction.original_response()
                if hasattr(view, "message"):
                    view.message = sent_msg
            except Exception:
                sent_msg = None

            # Save for rehydration
            try:
                await save_view_tracker_async(
                    "nextevent",
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
                logger.exception("[nextevent] save_view_tracker_async failed: %s", e)

        except Exception as e:
            logger.exception("[COMMAND] /nextevent failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Unable to build events: `{type(e).__name__}: {e}`",
                embed=None,
                view=None,
            )

    @bot.slash_command(
        name="refresh_events",
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
            # Refresh cached events
            await refresh_event_cache()

            # Update any live countdown embeds
            await update_live_event_embeds(bot, KVK_EVENT_CHANNEL_ID)

            ts = get_last_refreshed()
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                ts_text = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                ts_text = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

            dur = (datetime.now(UTC) - started).total_seconds()
            await ctx.interaction.edit_original_response(
                content=f"✅ Event cache and countdown embeds refreshed.\n"
                f"🕒 Last refreshed: `{ts_text}` • ⏱ {dur:.1f}s"
            )

        except Exception as e:
            logger.exception("[COMMAND ERROR] /refresh_events failed.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh event cache or embeds:\n```{type(e).__name__}: {e}```"
            )

    @bot.slash_command(
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
            # 1) Refresh events if cache looks stale (keeps manual refresh honest)
            try:
                if is_cache_stale():
                    await refresh_event_cache()
            except Exception:
                logger.warning(
                    "[/refresh_kvk_overview] Cache refresh check failed; proceeding anyway.",
                    exc_info=True,
                )

            # 2) Post or update the overview
            await post_or_update_daily_KVK_overview(bot, KVK_EVENT_CHANNEL_ID)

            # 3) Build friendly admin message with cache timestamp + duration
            ts = get_last_refreshed()
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                ts_text = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                ts_text = utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

            dur = (utcnow() - started).total_seconds()
            await ctx.interaction.edit_original_response(
                content=(
                    f"✅ Daily KVK Overview refreshed in **{dur:.1f}s** and posted to <#{KVK_EVENT_CHANNEL_ID}>.\n"
                    f"🕒 Event cache last refreshed: `{ts_text}`"
                )
            )

        except Exception as e:
            logger.exception("[COMMAND ERROR] /refresh_kvk_overview failed.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to refresh KVK overview:\n```{type(e).__name__}: {e}```"
            )
