from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from core.interaction_safety import safe_command, safe_defer
from decoraters import track_usage
from event_calendar.runtime_cache import (
    load_runtime_cache,
    stale_banner,
)
from ui.views.calendar import (
    CalendarLocalTimeToggleView,
    CalendarPaginationView,
    allowed_days,
    build_next_event_embed,
    cache_footer,
    calendar_importance_autocomplete,
    calendar_type_autocomplete,
    get_next_event,
    paginate,
    query_calendar,
)
from versioning import versioned

logger = logging.getLogger(__name__)

_ALLOWED_DAYS = allowed_days()


def register_calendar(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="calendar",
        description="Browse upcoming calendar events (cache-only).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.06")
    @safe_command
    @track_usage()
    async def calendar(
        ctx: discord.ApplicationContext,
        days: str = discord.Option(
            default="30",
            choices=["1", "3", "7", "30", "90", "180", "365"],
            required=True,
            description="Upcoming window in days",
        ),
        type: str = discord.Option(
            default="all",
            required=False,
            autocomplete=calendar_type_autocomplete,
            description="Event type",
        ),
        importance: str = discord.Option(
            default="all",
            required=False,
            autocomplete=calendar_importance_autocomplete,
            description="Importance",
        ),
        page: int = discord.Option(default=1, required=False, description="Page number"),
    ):
        await safe_defer(ctx, ephemeral=True)

        try:
            days_int = int(days)
        except Exception:
            await ctx.interaction.edit_original_response(content="Invalid days choice.")
            return

        if days_int not in _ALLOWED_DAYS:
            await ctx.interaction.edit_original_response(content="Invalid days choice.")
            return

        cache_state, filtered = query_calendar(
            days=days_int, event_type=type, importance=importance
        )
        banner = stale_banner(cache_state)

        if not cache_state.get("ok"):
            await ctx.interaction.edit_original_response(
                content=banner or "Calendar cache unavailable."
            )
            return

        if not filtered:
            text = "No matching upcoming events found."
            if banner:
                text = f"{banner}\n\n{text}"
            await ctx.interaction.edit_original_response(content=text)
            return

        page_items, p, total = paginate(filtered, page)
        footer = cache_footer(cache_state)
        summary_text = f"days={days_int}"

        view = CalendarPaginationView(
            title="📅 Calendar",
            items=filtered,
            cache_footer_text=footer,
            owner_user_id=getattr(ctx.author, "id", None),
            summary_field_name="Filter",
            summary_field_value=summary_text,
            color=discord.Color.blurple(),
            timeout=180.0,
            local_time_events=page_items,
            local_time_prefix="calendar_command",
        )
        view._page = p
        embed = view._build_current_embed()

        msg = await ctx.interaction.edit_original_response(
            content=banner or None,
            embed=embed,
            view=view,
        )
        view.message = msg

    @bot.slash_command(
        name="calendar_next_event",
        description="Show the next upcoming calendar event (cache-only).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.05")
    @safe_command
    @track_usage()
    async def calendar_next_event(
        ctx: discord.ApplicationContext,
        type: str = discord.Option(
            default="all",
            required=False,
            autocomplete=calendar_type_autocomplete,
            description="Event type",
        ),
    ):
        await safe_defer(ctx, ephemeral=True)

        cache_state = load_runtime_cache()
        banner = stale_banner(cache_state)
        if not cache_state.get("ok"):
            await ctx.interaction.edit_original_response(
                content=banner or "Calendar cache unavailable."
            )
            return

        e = get_next_event(cache_state, event_type=type)
        if not e:
            text = f"No upcoming events found for type `{(type or 'all').strip().lower()}`."
            if banner:
                text = f"{banner}\n\n{text}"
            await ctx.interaction.edit_original_response(content=text)
            return

        footer = cache_footer(cache_state)
        embed = build_next_event_embed(event=e, footer=footer)
        view = CalendarLocalTimeToggleView(events=[e], prefix="calendar_next_event", timeout=180.0)

        await ctx.interaction.edit_original_response(content=banner or None, embed=embed, view=view)

    @bot.slash_command(
        name="calendar_reminder_config",
        # architecture-check: allow
        description="Interactive reminder configuration panel (multi-select).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def calendar_reminder_config(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/calendar_reminder_config",
                new_path="/me reminders",
                detail="Calendar reminder preferences now live beside KVK reminders in the private reminder centre.",
            ),
            ephemeral=True,
        )
        return
