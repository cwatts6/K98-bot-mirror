from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging

import discord
from discord.ext import commands as ext_commands

from account_picker import safe_build_unique_gov_options
from bot_config import GUILD_ID, KVK_PLAYER_STATS_CHANNEL_ID, KVK_TARGET_CHANNEL_ID
from build_KVKrankings_embed import build_kvkrankings_embed
from commands.kvk_stats_card_posting import post_kvk_stats_output
from core.interaction_safety import safe_command, safe_defer
from decoraters import channel_only, track_usage
from honor_rankings_view import HonorRankingView, build_honor_rankings_embed
from kvk_ui import make_kvk_targets_view
from prekvk import report_service
from registry.account_slots import ACCOUNT_ORDER
from services import governor_account_service, kvk_history_service, kvk_personal_service
from stats_alerts.honors import get_latest_honor_top
from target_utils import run_target_lookup
from ui.views.kvk_history_view import KVKHistoryView
from ui.views.kvk_personal_views import MyKVKStatsSelectView
from ui.views.prekvk_report_views import send_prekvk_report
from ui.views.registry_views import GovNameModal, MyRegsActionView, RegisterStartView
from ui.views.stats_views import KVKRankingView
from utils import load_stat_cache, normalize_governor_id
from versioning import versioned

logger = logging.getLogger(__name__)


async def _open_registration_flow(interaction: discord.Interaction) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    except Exception:
        pass

    try:
        summary = await governor_account_service.get_account_summary_for_user(interaction.user.id)
        if not summary.ok:
            await interaction.followup.send(
                "Registry is temporarily unavailable. Please try again later.",
                ephemeral=True,
            )
            return
        free_slots = summary.free_slots()
        if not free_slots:
            await interaction.followup.send(
                "All account slots are already registered. Use **/my_registrations -> Modify Registration** to change one.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            "Pick an account slot to register:",
            view=RegisterStartView(author_id=interaction.user.id, free_slots=free_slots),
            ephemeral=True,
        )
    except Exception:
        logger.exception("[/kvk targets] registration flow failed")
        try:
            await interaction.followup.send(
                "Failed to open registration flow. Please try again later.",
                ephemeral=True,
            )
        except Exception:
            pass


async def _open_governor_lookup(interaction: discord.Interaction) -> None:
    try:
        await interaction.response.send_modal(GovNameModal(author_id=interaction.user.id))
    except Exception:
        try:
            message = "Use **/mygovernorid** and start typing your governor name to find your Governor ID."
            if not interaction.response.is_done():
                await interaction.response.send_message(message, ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)
        except Exception:
            pass


async def _send_personal_kvk_stats(ctx: discord.ApplicationContext) -> None:
    await safe_defer(ctx, ephemeral=True)

    account_summary = await governor_account_service.get_account_summary_for_user(ctx.user.id)
    if not account_summary.ok:
        await ctx.interaction.edit_original_response(
            content=f"Could not load registry: `{account_summary.error}`"
        )
        return

    if not account_summary.governor_ids:
        view = MyRegsActionView(author_id=ctx.user.id, has_regs=False)
        msg = await ctx.interaction.edit_original_response(
            content="You don't have any Governor accounts registered yet. Use the options below:",
            view=view,
        )
        view.set_message_ref(msg)
        return

    accounts = account_summary.ordered_accounts
    try:
        last_kvk_map = await kvk_personal_service.load_last_kvk_map()
        if not isinstance(last_kvk_map, dict):
            last_kvk_map = {}
    except Exception:
        logger.exception("[/kvk stats] load_last_kvk_map failed")
        last_kvk_map = {}

    if len(accounts) == 1:
        ((_, info),) = accounts.items()
        governor_id = normalize_governor_id(info.get("GovernorID"))
        if not governor_id:
            await ctx.interaction.edit_original_response(
                content="Your registration has no valid Governor ID."
            )
            return

        row = await kvk_personal_service.load_kvk_personal_stats(governor_id)
        if not row:
            await ctx.interaction.edit_original_response(
                content=f"Stats not found for Governor ID `{governor_id}`."
            )
            return

        try:
            last_kvk = last_kvk_map.get(str(governor_id))
            if last_kvk:
                row["last_kvk"] = last_kvk
        except Exception:
            logger.exception("[/kvk stats] failed attaching last_kvk for %s", governor_id)

        try:
            await post_kvk_stats_output(
                bot=getattr(ctx, "bot", None),
                ctx=ctx,
                row=row,
                user=ctx.user,
            )
        except Exception as exc:
            logger.exception("[/kvk stats] post_kvk_stats_output failed")
            await ctx.interaction.edit_original_response(
                content=f"Failed to build stats: `{type(exc).__name__}: {exc}`"
            )
            return

        try:
            await ctx.interaction.edit_original_response(content=" ", view=None)
        except Exception:
            pass
        return

    ordered_accounts = {slot: accounts[slot] for slot in ACCOUNT_ORDER if slot in accounts}
    for slot in sorted(accounts.keys()):
        if slot not in ordered_accounts:
            ordered_accounts[slot] = accounts[slot]

    try:
        view = MyKVKStatsSelectView(ctx=ctx, accounts=ordered_accounts, author_id=ctx.user.id)
        view._last_kvk_map = last_kvk_map
    except Exception as exc:
        logger.exception("[/kvk stats] MyKVKStatsSelectView init failed")
        await ctx.interaction.edit_original_response(
            content=f"Failed to build account selector: `{type(exc).__name__}: {exc}`"
        )
        return

    await ctx.interaction.edit_original_response(
        content="Select an account below to view your stats:",  # architecture-check: allow
        view=view,
    )


async def _send_personal_kvk_targets(
    ctx: discord.ApplicationContext, governor_id: str | None, only_me: bool
) -> None:
    await safe_defer(ctx, ephemeral=only_me)

    try:
        last_kvk_map = await kvk_personal_service.load_last_kvk_map()
        if not isinstance(last_kvk_map, dict):
            last_kvk_map = {}
    except Exception:
        logger.exception("[/kvk targets] load_last_kvk_map failed")
        last_kvk_map = {}

    if governor_id and governor_id.strip().isdigit():
        await run_target_lookup(ctx.interaction, governor_id.strip(), ephemeral=only_me)
        try:
            await ctx.interaction.edit_original_response(content=" ", view=None)
        except Exception:
            pass
        return

    try:
        account_summary = await governor_account_service.get_account_summary_for_user(ctx.user.id)
        if not account_summary.ok:
            raise RuntimeError(account_summary.error or "registry unavailable")
    except Exception:
        logger.exception("[/kvk targets] load_registry failed")
        await ctx.followup.send(
            "Couldn't load your registered accounts. Provide `governor_id` or try again later.",
            ephemeral=True,
        )
        return

    options = safe_build_unique_gov_options(account_summary)
    if options and len(options) == 1:
        await run_target_lookup(ctx.interaction, options[0].value, ephemeral=only_me)
        try:
            await ctx.interaction.edit_original_response(content=" ", view=None)
        except Exception:
            pass
        return

    async def _on_select(
        interaction: discord.Interaction, selected_governor_id: str, ephemeral: bool
    ) -> None:
        await run_target_lookup(interaction, selected_governor_id, ephemeral=ephemeral)

    if options:
        try:
            view = make_kvk_targets_view(
                ctx=ctx,
                options=options,
                on_select_governor=_on_select,
                show_register_btn=True,
                ephemeral=only_me,
                last_kvk_map=last_kvk_map,
                lookup_callback=_open_governor_lookup,
                register_callback=_open_registration_flow,
            )
            await ctx.followup.send(
                "Select an account to view its KVK targets:",  # architecture-check: allow
                view=view,
                ephemeral=only_me,
            )
        except Exception:
            logger.exception(
                "[/kvk targets] failed to create/send account selector view"  # architecture-check: allow
            )
            await ctx.followup.send(
                "Failed to show account selector. Try again later.", ephemeral=True
            )
        return

    hint = (
        "You don't have any linked governor accounts yet.\n"
        "- Use `/register_governor`, or\n"
        "- Re-run this command with the `governor_id` option."
    )
    try:
        view = make_kvk_targets_view(
            ctx=ctx,
            options=[],
            on_select_governor=_on_select,
            show_register_btn=True,
            ephemeral=only_me,
            last_kvk_map=last_kvk_map,
            lookup_callback=_open_governor_lookup,
            register_callback=_open_registration_flow,
        )
        await ctx.followup.send(hint, view=view, ephemeral=only_me)
    except Exception:
        logger.exception(
            "[/kvk targets] failed to create/send empty account picker view"  # architecture-check: allow
        )
        await ctx.followup.send(hint, ephemeral=only_me)


async def _send_kvk_history(
    ctx: discord.ApplicationContext, ephemeral: bool, governor_id: int | None
) -> None:
    await safe_defer(ctx, ephemeral=ephemeral)

    account_summary = await governor_account_service.get_account_summary_for_user(ctx.user.id)
    if not account_summary.ok and not governor_id:
        await ctx.followup.send(
            f"Registry is temporarily unavailable: `{account_summary.error}`",
            ephemeral=True,
        )
        return
    account_map = kvk_history_service.build_ordered_account_map(account_summary.ordered_accounts)

    if governor_id:
        try:
            from kvk_history_utils import fetch_history_for_governors

            df_lookup = await asyncio.to_thread(fetch_history_for_governors, [governor_id])
            governor_name = None
            for column in ("GovernorName", "Gov_Name", "Name"):
                if column in df_lookup.columns and not df_lookup[column].dropna().empty:
                    governor_name = str(df_lookup[column].dropna().iloc[0])
                    break
            governor_name = governor_name or str(governor_id)
        except Exception:
            governor_name = str(governor_id)
        account_map = {"Lookup": {"GovernorID": int(governor_id), "GovernorName": governor_name}}
    elif not account_map:
        await ctx.followup.send(
            "You haven't registered any accounts yet. Use `/register_governor` or pass a Governor ID here.",
            ephemeral=True,
        )
        return

    default_id = (
        str(governor_id)
        if governor_id
        else kvk_history_service.pick_default_governor_id(account_map)
    )
    if not default_id:
        await ctx.followup.send(
            "I couldn't find a valid Governor ID in your registered accounts.",
            ephemeral=True,
        )
        return

    view = KVKHistoryView(
        user=ctx.user,
        account_map=account_map,
        selected_ids=[default_id],
        allow_all=True,
        ephemeral=ephemeral,
    )
    await view.initial_send(ctx)


async def _send_kvk_rankings(ctx: discord.ApplicationContext) -> None:
    await safe_defer(ctx, ephemeral=False)

    cache = load_stat_cache()
    rows = [row for key, row in cache.items() if key != "_meta"]
    if not rows:
        await ctx.followup.send(
            "No stats cache available yet. Try again after the next scan/export.",
            ephemeral=False,
        )
        return

    view = KVKRankingView(cache, metric="power", limit=10, timeout=120.0)
    embed = build_kvkrankings_embed(rows, "power", 10, page=1)
    if not embed.footer or not embed.footer.text:
        last_ref = cache.get("_meta", {}).get("generated_at") or "unknown"
        embed.set_footer(text=f"Last refreshed: {last_ref}")

    response = await ctx.followup.send(embed=embed, view=view)
    try:
        view.message = await ctx.interaction.original_response()
    except Exception:
        try:
            view.message = await response.original_response()
        except Exception:
            view.message = None


async def _send_honor_rankings(ctx: discord.ApplicationContext) -> None:
    await safe_defer(ctx, ephemeral=False)
    try:
        rows = await get_latest_honor_top(10)
    except Exception:
        logger.exception("[/kvk rankings honor] get_latest_honor_top failed")
        rows = []

    if not rows:
        await ctx.followup.send("No honor data found for the latest KVK.", ephemeral=False)
        return

    embed = build_honor_rankings_embed(rows, limit=10)
    view = HonorRankingView()
    await ctx.followup.send(embed=embed, view=view, ephemeral=False)


async def _send_prekvk_rankings(ctx: discord.ApplicationContext) -> None:
    await safe_defer(ctx, ephemeral=True)
    await send_prekvk_report(
        ctx=ctx,
        kvk_no=None,
        sort_by=report_service.parse_report_sort("Overall"),
        limit=10,
    )


async def _run_tracked(
    ctx: discord.ApplicationContext,
    *,
    command_name: str,
    callback: Callable[[discord.ApplicationContext], Awaitable[None]],
) -> None:
    @track_usage(command_name)
    async def tracked(inner_ctx: discord.ApplicationContext) -> None:
        await callback(inner_ctx)

    await tracked(ctx)


async def _run_channel_guarded(
    ctx: discord.ApplicationContext,
    channel_id: int,
    *,
    admin_override: bool,
    command_name: str,
    callback: Callable[[discord.ApplicationContext], Awaitable[None]],
) -> None:
    @channel_only(channel_id, admin_override=admin_override)
    @track_usage(command_name)
    async def guarded(inner_ctx: discord.ApplicationContext) -> None:
        await callback(inner_ctx)

    await guarded(ctx)


def register_kvk(bot: ext_commands.Bot) -> None:
    kvk_group = discord.SlashCommandGroup(
        "kvk",
        "KVK player tools",
        guild_ids=[GUILD_ID],
    )

    @kvk_group.command(
        name="stats",
        description="View your personal KVK stats.",
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def kvk_stats(ctx: discord.ApplicationContext) -> None:
        await _send_personal_kvk_stats(ctx)

    @kvk_group.command(
        name="targets",
        description="View your DKP, kill, and deads targets.",
    )
    @channel_only(KVK_TARGET_CHANNEL_ID, admin_override=True)
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def kvk_targets(
        ctx: discord.ApplicationContext,
        governor_id: str | None = discord.Option(
            str,
            name="governor_id",
            description="Optional Governor ID if you prefer to type it",
            required=False,
            default=None,
        ),
        only_me: bool = discord.Option(
            bool,
            name="only_me",
            description="Show only to me",
            required=False,
            default=False,
        ),
    ) -> None:
        await _send_personal_kvk_targets(ctx, governor_id, only_me)

    @kvk_group.command(
        name="history",
        description="View your KVK-by-KVK history as a chart and table.",
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=False)
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def kvk_history(
        ctx: discord.ApplicationContext,
        ephemeral: bool = discord.Option(bool, "Only show to me", required=False, default=False),
        governor_id: int | None = discord.Option(
            int, "Governor ID (optional)", required=False, default=None
        ),
    ) -> None:
        await _send_kvk_history(ctx, ephemeral, governor_id)

    @kvk_group.command(
        name="rankings",
        description="Browse KVK, honor, or PreKvK rankings.",
    )
    @versioned("v1.00")
    @safe_command
    async def kvk_rankings(
        ctx: discord.ApplicationContext,
        ranking_type_option: str = discord.Option(
            str,
            name="type",
            description="Ranking type",
            required=True,
            choices=["kvk", "honor", "prekvk"],
        ),
    ) -> None:
        ranking_type = (ranking_type_option or "").strip().lower()
        if ranking_type == "kvk":
            await _run_channel_guarded(
                ctx,
                KVK_PLAYER_STATS_CHANNEL_ID,
                admin_override=True,
                command_name="kvk rankings",
                callback=_send_kvk_rankings,
            )
            return
        if ranking_type == "honor":
            await _run_channel_guarded(
                ctx,
                KVK_PLAYER_STATS_CHANNEL_ID,
                admin_override=False,
                command_name="kvk rankings",
                callback=_send_honor_rankings,
            )
            return
        if ranking_type == "prekvk":
            await _run_tracked(
                ctx=ctx,
                command_name="kvk rankings",
                callback=_send_prekvk_rankings,
            )
            return
        await ctx.respond("Unknown ranking type.", ephemeral=True)

    bot.add_application_command(kvk_group)
