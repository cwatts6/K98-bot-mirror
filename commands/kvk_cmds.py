from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging

import discord
from discord.ext import commands as ext_commands

from account_picker import AccountPickerView, safe_build_unique_gov_options
from bot_config import GUILD_ID, KVK_PLAYER_STATS_CHANNEL_ID, KVK_TARGET_CHANNEL_ID
from commands.kvk_history_card_posting import post_kvk_history_output
from commands.kvk_stats_card_posting import post_kvk_stats_output
from commands.kvk_targets_card_posting import post_kvk_targets_output
from core.interaction_safety import safe_command, safe_defer
from decoraters import channel_only, track_usage
from kvk.models.kvk_rankings import HallOfFameMetric
from kvk.rendering.kvk_rankings_card_renderer import (
    can_render_current_rankings_top10_card,
    can_render_hall_of_fame_top10_card,
    render_current_rankings_top10_card,
    render_hall_of_fame_top10_card,
)
from kvk.rendering.kvk_rankings_embed import (
    build_current_rankings_embed,
    build_hall_of_fame_embed,
)
from kvk.services import kvk_rankings_service
from kvk_ui import make_kvk_targets_view
from registry.account_slots import ACCOUNT_ORDER
from services import governor_account_service, kvk_history_service, kvk_personal_service
from target_utils import run_target_lookup
from ui.views.kvk_personal_views import MyKVKStatsSelectView
from ui.views.kvk_rankings_views import (
    CurrentRankingsBrowserView,
    HallOfFameRecordsView,
)
from ui.views.registry_views import GovNameModal, MyRegsActionView, RegisterStartView
from utils import normalize_governor_id
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
            posted, channel_used = await post_kvk_stats_output(
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

        if not posted:
            logger.warning(
                "[/kvk stats] post_kvk_stats_output returned false channel_used=%s governor_id=%s",
                channel_used,
                governor_id,
            )
            await ctx.interaction.edit_original_response(
                content=(
                    "Could not post your KVK stats publicly. "
                    "Please check bot/channel permissions or try again later."
                ),
                view=None,
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
        view = MyKVKStatsSelectView(
            ctx=ctx,
            accounts=ordered_accounts,
            author_id=ctx.user.id,
            use_visual_card=True,
        )
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
        try:
            await post_kvk_targets_output(ctx.interaction, governor_id.strip(), ephemeral=only_me)
        except Exception:
            logger.exception("[/kvk targets] modern target output failed; falling back")
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
        try:
            await post_kvk_targets_output(ctx.interaction, options[0].value, ephemeral=only_me)
        except Exception:
            logger.exception("[/kvk targets] modern target output failed; falling back")
            await run_target_lookup(ctx.interaction, options[0].value, ephemeral=only_me)
        try:
            await ctx.interaction.edit_original_response(content=" ", view=None)
        except Exception:
            pass
        return

    async def _on_select(
        interaction: discord.Interaction, selected_governor_id: str, ephemeral: bool
    ) -> None:
        try:
            await post_kvk_targets_output(interaction, selected_governor_id, ephemeral=ephemeral)
        except Exception:
            logger.exception("[/kvk targets] selected modern target output failed; falling back")
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


async def _send_kvk_history(ctx: discord.ApplicationContext, governor_id: int | None) -> None:
    if governor_id:
        await safe_defer(ctx, ephemeral=False)
        await _post_kvk_history_view(
            ctx,
            user=ctx.user,
            default_id=str(governor_id),
            ephemeral=False,
        )
        return

    account_summary = await governor_account_service.get_account_summary_for_user(ctx.user.id)
    if not account_summary.ok:
        await safe_defer(ctx, ephemeral=True)
        await ctx.followup.send(
            f"Registry is temporarily unavailable: `{account_summary.error}`",
            ephemeral=True,
        )
        return
    account_map = kvk_history_service.build_ordered_account_map(account_summary.ordered_accounts)

    if not account_map:
        await safe_defer(ctx, ephemeral=True)

        async def _on_select_empty(
            interaction: discord.Interaction, selected_governor_id: str, _selected_ephemeral: bool
        ) -> None:
            await _post_kvk_history_view(
                interaction,
                user=interaction.user,
                default_id=selected_governor_id,
                ephemeral=False,
            )

        view = AccountPickerView(
            ctx=ctx,
            options=[],
            on_select_governor=_on_select_empty,
            heading="Select an account to view its KVK history:",  # architecture-check: allow
            show_register_btn=True,
            ephemeral=True,
            lookup_callback=_open_governor_lookup,
            register_callback=_open_registration_flow,
        )
        await ctx.followup.send(
            content="You haven't registered any accounts yet. Use the options below or pass a Governor ID.",
            view=view,
            ephemeral=True,
        )
        return

    options = safe_build_unique_gov_options(account_summary if account_summary.ok else account_map)

    async def _on_select_history(
        interaction: discord.Interaction, selected_governor_id: str, _selected_ephemeral: bool
    ) -> None:
        await _post_kvk_history_view(
            interaction,
            user=interaction.user,
            default_id=selected_governor_id,
            ephemeral=False,
        )

    default_id = (
        str(governor_id)
        if governor_id
        else kvk_history_service.pick_default_governor_id(account_map)
    )
    if not default_id:
        await safe_defer(ctx, ephemeral=True)
        await ctx.followup.send(
            "I couldn't find a valid Governor ID in your registered accounts.",
            ephemeral=True,
        )
        return

    if len(options) > 1:
        await safe_defer(ctx, ephemeral=True)
        view = AccountPickerView(
            ctx=ctx,
            options=options,
            on_select_governor=_on_select_history,
            heading="Select an account to view its KVK history:",  # architecture-check: allow
            show_register_btn=True,
            ephemeral=True,
            lookup_callback=_open_governor_lookup,
            register_callback=_open_registration_flow,
        )
        await ctx.followup.send(
            content="Select an account to view its KVK history:",  # architecture-check: allow
            view=view,
            ephemeral=True,
        )
        return

    await safe_defer(ctx, ephemeral=False)
    await _post_kvk_history_view(
        ctx,
        user=ctx.user,
        default_id=default_id,
        ephemeral=False,
    )


async def _post_kvk_history_view(
    target: discord.ApplicationContext | discord.Interaction,
    *,
    user: discord.User | discord.Member,
    default_id: str,
    ephemeral: bool,
) -> None:
    await post_kvk_history_output(
        target,
        user=user,
        governor_id=default_id,
        ephemeral=ephemeral,
    )


async def _send_current_rankings(ctx: discord.ApplicationContext, *, mode: str) -> None:
    await safe_defer(ctx, ephemeral=False)

    try:
        payload = await kvk_rankings_service.build_current_rankings_payload(
            mode=mode,
            metric=None,
            limit=10,
        )
    except Exception:
        logger.exception("[/kvk rankings %s] build_current_rankings_payload failed", mode)
        await ctx.followup.send(
            "Rankings are temporarily unavailable. Please try again later.",
            ephemeral=False,
        )
        return

    view = CurrentRankingsBrowserView(
        mode=payload.mode,
        metric=payload.metric,
        limit=payload.limit,
    )
    rendered = None
    if can_render_current_rankings_top10_card(payload):
        try:
            rendered = await asyncio.to_thread(render_current_rankings_top10_card, payload)
        except Exception:
            logger.exception(
                "[/kvk rankings %s] render_current_rankings_top10_card failed", payload.mode
            )

    if rendered is not None:
        rendered.image_bytes.seek(0)
        file = discord.File(rendered.image_bytes, filename=rendered.filename)
        try:
            view.message = await ctx.followup.send(file=file, view=view, ephemeral=False)
            return
        except Exception:
            logger.exception(
                "[/kvk rankings %s] card send failed; falling back to embed", payload.mode
            )

    embed = build_current_rankings_embed(payload)
    view.message = await ctx.followup.send(embed=embed, view=view, ephemeral=False)


async def _send_kvk_rankings(ctx: discord.ApplicationContext) -> None:
    await _send_current_rankings(ctx, mode="kvk")


async def _send_honor_rankings(ctx: discord.ApplicationContext) -> None:
    await _send_current_rankings(ctx, mode="honor")


async def _send_hall_of_fame_rankings(ctx: discord.ApplicationContext) -> None:
    await safe_defer(ctx, ephemeral=False)
    metric = HallOfFameMetric.KILLS
    try:
        payload = await kvk_rankings_service.build_hall_of_fame_payload(metric=metric, limit=10)
    except Exception:
        logger.exception("[/kvk rankings records] build_hall_of_fame_payload failed")
        await ctx.followup.send(
            "Hall of Fame rankings are temporarily unavailable. Please try again later.",
            ephemeral=False,
        )
        return
    view = HallOfFameRecordsView(metric=metric, limit=payload.limit)
    rendered = None
    if can_render_hall_of_fame_top10_card(payload):
        try:
            rendered = await asyncio.to_thread(render_hall_of_fame_top10_card, payload)
        except Exception:
            logger.exception("[/kvk rankings records] render_hall_of_fame_top10_card failed")

    if rendered is not None:
        rendered.image_bytes.seek(0)
        file = discord.File(rendered.image_bytes, filename=rendered.filename)
        try:
            view.message = await ctx.followup.send(file=file, view=view, ephemeral=False)
            return
        except Exception:
            logger.exception("[/kvk rankings records] card send failed; falling back to embed")

    embed = build_hall_of_fame_embed(payload)
    view.message = await ctx.followup.send(embed=embed, view=view, ephemeral=False)


async def _send_prekvk_rankings(ctx: discord.ApplicationContext) -> None:
    await _send_current_rankings(ctx, mode="prekvk")


async def _run_channel_guarded(
    ctx: discord.ApplicationContext,
    channel_id: int,
    *,
    admin_override: bool,
    _command_name: str,
    callback: Callable[[discord.ApplicationContext], Awaitable[None]],
) -> None:
    @channel_only(channel_id, admin_override=admin_override)
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
        description="View your modern KVK history cards.",
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def kvk_history(
        ctx: discord.ApplicationContext,
        governor_id: int | None = discord.Option(
            int, "Governor ID (optional)", required=False, default=None
        ),
    ) -> None:
        await _send_kvk_history(ctx, governor_id)

    @kvk_group.command(
        name="rankings",
        description="Browse KVK, honor, PreKvK, or records rankings.",
    )
    @channel_only(KVK_PLAYER_STATS_CHANNEL_ID, admin_override=True)
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def kvk_rankings(
        ctx: discord.ApplicationContext,
        ranking_type_option: str = discord.Option(
            str,
            name="type",
            description="Ranking type",
            required=True,
            choices=["kvk", "honor", "prekvk", "records"],
        ),
    ) -> None:
        ranking_type = (ranking_type_option or "").strip().lower()
        if ranking_type == "kvk":
            await _run_channel_guarded(
                ctx,
                KVK_PLAYER_STATS_CHANNEL_ID,
                admin_override=True,
                _command_name="kvk rankings",
                callback=_send_kvk_rankings,
            )
            return
        if ranking_type == "honor":
            await _run_channel_guarded(
                ctx,
                KVK_PLAYER_STATS_CHANNEL_ID,
                admin_override=False,
                _command_name="kvk rankings",
                callback=_send_honor_rankings,
            )
            return
        if ranking_type == "prekvk":
            await _send_prekvk_rankings(ctx)
            return
        if ranking_type == "records":
            await _run_channel_guarded(
                ctx,
                KVK_PLAYER_STATS_CHANNEL_ID,
                admin_override=True,
                _command_name="kvk rankings",
                callback=_send_hall_of_fame_rankings,
            )
            return
        await ctx.respond("Unknown ranking type.", ephemeral=True)

    bot.add_application_command(kvk_group)
