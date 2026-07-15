from __future__ import annotations

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command
from decoraters import track_usage
from inventory.models import InventoryReportView
from ui.views.player_self_service_governor_dashboard_views import send_governor_dashboard
from ui.views.player_self_service_inventory_report_views import send_player_inventory_report
from ui.views.player_self_service_views import (
    PAGE_ACCOUNTS,
    PAGE_EXPORTS,
    PAGE_INVENTORY,
    PAGE_PREFERENCES,
    PAGE_REMINDERS,
    send_player_self_service_page,
)
from versioning import versioned


def register_me(bot: ext_commands.Bot) -> None:
    me_group = discord.SlashCommandGroup(
        "me",
        "Private player self-service tools",
        guild_ids=[GUILD_ID],
    )

    @me_group.command(
        name="dashboard",
        description="Open your private K98 personal command centre",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @track_usage()
    async def me_dashboard(ctx: discord.ApplicationContext) -> None:
        await send_governor_dashboard(ctx)

    @me_group.command(
        name="accounts",
        description="Open your private account centre",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def me_accounts(ctx: discord.ApplicationContext) -> None:
        await send_player_self_service_page(ctx, page=PAGE_ACCOUNTS)

    @me_group.command(
        name="reminders",
        description="Review your private KVK and calendar reminders",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def me_reminders(ctx: discord.ApplicationContext) -> None:
        await send_player_self_service_page(ctx, page=PAGE_REMINDERS)

    @me_group.command(
        name="preferences",
        description="Review your private inventory preferences",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def me_preferences(ctx: discord.ApplicationContext) -> None:
        await send_player_self_service_page(ctx, page=PAGE_PREFERENCES)

    @me_group.command(
        name="inventory",
        description="Review your private inventory summary",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def me_inventory(ctx: discord.ApplicationContext) -> None:
        await send_player_self_service_page(ctx, page=PAGE_INVENTORY)

    @me_group.command(
        name="resources",
        description="Open your private selected-governor Resources report",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def me_resources(ctx: discord.ApplicationContext) -> None:
        await send_player_inventory_report(ctx, report_view=InventoryReportView.RESOURCES)

    @me_group.command(
        name="materials",
        description="Open your private selected-governor Materials report",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def me_materials(ctx: discord.ApplicationContext) -> None:
        await send_player_inventory_report(ctx, report_view=InventoryReportView.MATERIALS)

    @me_group.command(
        name="speedups",
        description="Open your private selected-governor Speedups report",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def me_speedups(ctx: discord.ApplicationContext) -> None:
        await send_player_inventory_report(ctx, report_view=InventoryReportView.SPEEDUPS)

    @me_group.command(
        name="exports",
        description="Review private personal export options",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def me_exports(ctx: discord.ApplicationContext) -> None:
        await send_player_self_service_page(ctx, page=PAGE_EXPORTS)

    bot.add_application_command(me_group)
