from __future__ import annotations

from collections.abc import Iterable, Mapping
import logging
import re

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_or_leadership_only, track_usage
from ui.views.vote_admin_update_view import VoteAdminUpdateView
from ui.views.vote_post_view import VotePostView, disabled_vote_view
from versioning import versioned
from voting.discord_presentation import (
    build_close_embed,
    build_vote_embed,
    build_vote_file,
    configured_everyone_mentions,
    mention_content,
    no_broad_mentions,
)
from voting.export_service import build_vote_totals_export, build_vote_voter_audit_export
from voting.service import (
    CLOSE_DURATION_CHOICES,
    MAX_CLOSE_REASON_LEN,
    MAX_DESCRIPTION_LEN,
    MAX_OPTION_LABEL_LEN,
    MAX_TITLE_LEN,
    VoteValidationError,
    attach_vote_message,
    build_create_request,
    cancel_vote_launch_failure,
    close_vote,
    create_vote_record,
    get_vote_snapshot,
    search_closed_vote_choices,
    search_vote_choices,
)

logger = logging.getLogger(__name__)

_CLOSE_DURATION_LABELS = {
    "30m": "30 minutes",
    "1h": "1 hour",
    "2h": "2 hours",
    "4h": "4 hours",
    "8h": "8 hours",
    "12h": "12 hours",
    "1d": "1 day",
    "2d": "2 days",
    "3d": "3 days",
    "7d": "7 days",
}
_CLOSE_DURATION_CHOICES = [
    discord.OptionChoice(name=_CLOSE_DURATION_LABELS.get(value, value), value=value)
    for value in CLOSE_DURATION_CHOICES
]
_EXPORT_MODE_TOTALS = "totals"
_EXPORT_MODE_VOTER_AUDIT = "voter_audit"
_EXPORT_MODE_CHOICES = [
    discord.OptionChoice(name="Totals only", value=_EXPORT_MODE_TOTALS),
    discord.OptionChoice(name="Voter audit", value=_EXPORT_MODE_VOTER_AUDIT),
]


def _channel_permission_error(
    channel: discord.abc.GuildChannel,
    me: discord.Member,
    *,
    needs_mention_everyone: bool = False,
) -> str | None:
    perms = channel.permissions_for(me)
    missing = []
    if not perms.send_messages:
        missing.append("send messages")
    if not perms.attach_files:
        missing.append("attach files")
    if not perms.embed_links:
        missing.append("embed links")
    if not perms.read_message_history:
        missing.append("read message history")
    if needs_mention_everyone and not perms.mention_everyone:
        missing.append("mention everyone")
    if missing:
        return "Bot is missing target-channel permissions: " + ", ".join(missing) + "."
    return None


def _parse_vote_post_id(value: str | int) -> int:
    if isinstance(value, int):
        return int(value)
    text = str(value or "").strip()
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"#(\d+)", text)
    if match:
        return int(match.group(1))
    raise VoteValidationError("Choose a vote from autocomplete.")


async def _vote_post_autocomplete(ctx: discord.AutocompleteContext):
    query = str(getattr(ctx, "value", "") or "")
    try:
        choices = await search_vote_choices(query=query, limit=25)
    except Exception:
        logger.exception("vote_post_autocomplete_failed query=%r", query)
        return []
    output = []
    for choice in choices:
        closes = choice.closes_at_utc.strftime("%Y-%m-%d %H:%M UTC")
        label = f"#{choice.vote_post_id} {choice.title} | {choice.status} | {closes}"
        output.append(discord.OptionChoice(name=label[:100], value=str(choice.vote_post_id)))
    return output


async def _closed_vote_post_autocomplete(ctx: discord.AutocompleteContext):
    query = str(getattr(ctx, "value", "") or "")
    try:
        choices = await search_closed_vote_choices(query=query, limit=25)
    except Exception:
        logger.exception("closed_vote_post_autocomplete_failed query=%r", query)
        return []
    output = []
    for choice in choices:
        closed_at = choice.closed_at_utc or choice.closes_at_utc
        closed = closed_at.strftime("%Y-%m-%d %H:%M UTC")
        label = f"#{choice.vote_post_id} {choice.title} | Closed | {closed}"
        output.append(discord.OptionChoice(name=label[:100], value=str(choice.vote_post_id)))
    return output


def _build_vote_export_summary_embed(export) -> discord.Embed:
    snapshot = export.snapshot
    embed = discord.Embed(
        title=f"Vote #{snapshot.vote_post_id} totals export",
        description=export.outcome_summary,
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Total votes", value=str(snapshot.total_votes), inline=True)
    embed.add_field(name="Rows", value=str(export.row_count), inline=True)
    embed.add_field(
        name="Closed",
        value=(
            snapshot.closed_at_utc.strftime("%Y-%m-%d %H:%M UTC")
            if snapshot.closed_at_utc
            else "Unknown"
        ),
        inline=True,
    )
    if snapshot.closed_by_discord_user_id is not None:
        embed.add_field(
            name="Closed by",
            value=str(snapshot.closed_by_discord_user_id),
            inline=True,
        )
    if snapshot.closed_reason:
        embed.add_field(name="Close reason", value=snapshot.closed_reason[:1024], inline=False)
    if snapshot.message_id:
        embed.add_field(
            name="Message",
            value=f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}",
            inline=False,
        )
    embed.set_footer(text="Totals-only export.")
    return embed


def _discord_display_name(member) -> str:
    for attr in ("display_name", "global_name", "name"):
        value = str(getattr(member, attr, "") or "").strip()
        if value:
            return value
    return "Unknown"


async def _resolve_voter_discord_names(
    ctx: discord.ApplicationContext,
    discord_user_ids: Iterable[int],
) -> Mapping[int, str]:
    unique_ids = tuple(dict.fromkeys(int(user_id) for user_id in discord_user_ids))
    guild = getattr(ctx, "guild", None)
    if guild is None:
        bot = getattr(ctx, "bot", None)
        guild_id = getattr(ctx, "guild_id", None)
        if bot is not None and guild_id is not None and hasattr(bot, "get_guild"):
            guild = bot.get_guild(int(guild_id))

    names: dict[int, str] = {}
    for user_id in unique_ids:
        member = None
        if guild is not None and hasattr(guild, "get_member"):
            member = guild.get_member(int(user_id))
        if member is None and guild is not None and hasattr(guild, "fetch_member"):
            try:
                member = await guild.fetch_member(int(user_id))
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                logger.info("vote_voter_name_lookup_unavailable discord_user_id=%s", user_id)
            except Exception:
                logger.exception("vote_voter_name_lookup_failed discord_user_id=%s", user_id)
        names[user_id] = _discord_display_name(member) if member is not None else "Unknown"
    return names


def _build_vote_voter_audit_export_summary_embed(export) -> discord.Embed:
    snapshot = export.snapshot
    embed = discord.Embed(
        title=f"Vote #{snapshot.vote_post_id} voter audit export",
        description="Voter-level audit rows for one closed vote.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Total votes", value=str(snapshot.total_votes), inline=True)
    embed.add_field(name="Rows", value=str(export.row_count), inline=True)
    embed.add_field(
        name="Closed",
        value=(
            snapshot.closed_at_utc.strftime("%Y-%m-%d %H:%M UTC")
            if snapshot.closed_at_utc
            else "Unknown"
        ),
        inline=True,
    )
    embed.set_footer(text="Private voter-level export. Includes Discord user ID and name.")
    return embed


async def _send_vote_update_panel(ctx: discord.ApplicationContext, snapshot) -> None:
    # architecture-check: allow - Discord response copy, not embedded SQL.
    content = f"Choose what to update for Vote #{snapshot.vote_post_id}."
    view = VoteAdminUpdateView(snapshot, owner_user_id=int(ctx.user.id))
    followup = getattr(ctx, "followup", None)
    if followup is not None and hasattr(followup, "send"):
        try:
            await followup.send(content=content, view=view, ephemeral=True)
            await ctx.interaction.edit_original_response(
                # architecture-check: allow - Discord response copy, not embedded SQL.
                content=f"Update panel opened for Vote #{snapshot.vote_post_id}."
            )
            return
        except Exception:
            logger.exception(
                "vote_admin_update_followup_failed vote_post_id=%s", snapshot.vote_post_id
            )

    await ctx.interaction.edit_original_response(content=content, view=view)


def register_vote_admin(bot: ext_commands.Bot) -> None:
    group = discord.SlashCommandGroup(
        "vote_admin",
        "Live vote post admin controls",
        guild_ids=[GUILD_ID],
    )

    # architecture-check: allow - "create" is the public command verb, not embedded SQL.
    @group.command(name="create", description="Start a durable live vote post.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_create(
        ctx: discord.ApplicationContext,
        title: str = discord.Option(str, "Vote title", max_length=MAX_TITLE_LEN),
        target_channel: discord.TextChannel = discord.Option(
            discord.TextChannel, "Channel to post in"
        ),
        close_in: str = discord.Option(
            str,
            "When voting should close",
            choices=_CLOSE_DURATION_CHOICES,
        ),
        option_1: str = discord.Option(str, "Option 1", max_length=MAX_OPTION_LABEL_LEN),
        option_2: str = discord.Option(str, "Option 2", max_length=MAX_OPTION_LABEL_LEN),
        description: str = discord.Option(
            str,
            "Vote description",
            required=False,
            default="",
            max_length=MAX_DESCRIPTION_LEN,
        ),
        option_3: str = discord.Option(
            str, "Option 3", required=False, default="", max_length=MAX_OPTION_LABEL_LEN
        ),
        option_4: str = discord.Option(
            str, "Option 4", required=False, default="", max_length=MAX_OPTION_LABEL_LEN
        ),
        option_5: str = discord.Option(
            str, "Option 5", required=False, default="", max_length=MAX_OPTION_LABEL_LEN
        ),
        option_6: str = discord.Option(
            str, "Option 6", required=False, default="", max_length=MAX_OPTION_LABEL_LEN
        ),
        reminder_offsets_minutes: str = discord.Option(
            str,
            "Reminder offsets before close in minutes, comma-separated",
            required=False,
            default="60",
        ),
        launch_mention_everyone: bool = discord.Option(
            bool,
            "Mention @everyone on the launch post",
            required=False,
            default=False,
        ),
        reminder_mention_everyone: bool = discord.Option(
            bool,
            "Mention @everyone on reminder posts",
            required=False,
            default=False,
        ),
        close_mention_everyone: bool = discord.Option(
            bool,
            "Mention @everyone on closing post",
            required=False,
            default=False,
        ),
        allow_vote_changes: bool = discord.Option(
            bool,
            "Allow players to change vote before close",
            required=False,
            default=True,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            req = build_create_request(
                guild_id=int(ctx.guild_id or target_channel.guild.id),
                channel_id=int(target_channel.id),
                created_by_discord_user_id=int(ctx.user.id),
                title=title,
                description=description,
                option_labels=(option_1, option_2, option_3, option_4, option_5, option_6),
                close_time_utc=close_in,
                reminder_offsets=reminder_offsets_minutes,
                allow_vote_change=allow_vote_changes,
                launch_mention_everyone=launch_mention_everyone,
                reminder_mention_everyone=reminder_mention_everyone,
                close_mention_everyone=close_mention_everyone,
            )
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not created: {exc}")
            return
        me = target_channel.guild.me
        if me is not None:
            needs_mention_everyone = (
                req.launch_mention_everyone
                or req.reminder_mention_everyone
                or req.close_mention_everyone
            )
            permission_error = _channel_permission_error(
                target_channel,
                me,
                needs_mention_everyone=needs_mention_everyone,
            )
            if permission_error:
                await ctx.interaction.edit_original_response(content=permission_error)
                return

        message = None
        snapshot = await create_vote_record(req)
        try:
            view = VotePostView(snapshot)
            message = await target_channel.send(
                content=mention_content(snapshot.launch_mention_everyone, "New vote is open"),
                embed=build_vote_embed(snapshot),
                file=build_vote_file(snapshot),
                view=view,
                allowed_mentions=configured_everyone_mentions(snapshot.launch_mention_everyone),
            )
            snapshot = await attach_vote_message(
                snapshot,
                channel_id=int(target_channel.id),
                message_id=int(message.id),
            )
        except Exception:
            logger.exception("vote_launch_failed vote_post_id=%s", snapshot.vote_post_id)
            await cancel_vote_launch_failure(
                vote_post_id=snapshot.vote_post_id,
                actor_discord_user_id=int(ctx.user.id),
                reason="launch failed",
            )
            if message is not None:
                try:
                    cancelled = await get_vote_snapshot(snapshot.vote_post_id)
                    if cancelled is not None:
                        await message.edit(
                            embed=build_vote_embed(cancelled),
                            attachments=[],
                            files=[build_vote_file(cancelled)],
                            view=disabled_vote_view(cancelled),
                            allowed_mentions=no_broad_mentions(),
                        )
                except Exception:
                    logger.exception(
                        "vote_launch_failed_message_disable_failed vote_post_id=%s",
                        snapshot.vote_post_id,
                    )
            await ctx.interaction.edit_original_response(
                content=(
                    "Vote not created: the Discord vote post could not be sent, "
                    "and the SQL record was cancelled."
                )
            )
            return
        await ctx.interaction.edit_original_response(
            content=f"Vote #{snapshot.vote_post_id} created in {target_channel.mention}."
        )

    @group.command(name="close", description="Close a vote early and disable its buttons.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_close(
        ctx: discord.ApplicationContext,
        vote: str = discord.Option(
            str,
            "Vote to close",
            autocomplete=_vote_post_autocomplete,
        ),
        reason: str = discord.Option(
            str,
            "Close reason",
            required=False,
            default="closed early",
            max_length=MAX_CLOSE_REASON_LEN,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            vote_post_id = _parse_vote_post_id(vote)
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not closed: {exc}")
            return
        try:
            result, snapshot = await close_vote(
                vote_post_id=vote_post_id,
                actor_discord_user_id=int(ctx.user.id),
                reason=reason,
            )
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not closed: {exc}")
            return
        if snapshot is None:
            await ctx.interaction.edit_original_response(content=result.message)
            return
        if not result.closed:
            await ctx.interaction.edit_original_response(content=result.message)
            return
        channel = bot.get_channel(snapshot.channel_id) or await bot.fetch_channel(
            snapshot.channel_id
        )
        message = await channel.fetch_message(snapshot.message_id) if snapshot.message_id else None
        if message is not None:
            await message.edit(
                embed=build_vote_embed(snapshot),
                attachments=[],
                files=[build_vote_file(snapshot)],
                view=disabled_vote_view(snapshot),
                allowed_mentions=no_broad_mentions(),
            )
        await channel.send(
            content=mention_content(snapshot.close_mention_everyone, "Vote closed"),
            embed=build_close_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.close_mention_everyone),
        )
        await ctx.interaction.edit_original_response(content=f"Vote #{vote_post_id} closed.")

    # architecture-check: allow - "update" is the public command verb, not embedded SQL.
    @group.command(name="update", description="Change safe fields for an open vote.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_update(
        ctx: discord.ApplicationContext,
        vote: str = discord.Option(
            str,
            # architecture-check: allow - Discord option copy, not embedded SQL.
            "Vote to update",
            autocomplete=_vote_post_autocomplete,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            vote_post_id = _parse_vote_post_id(vote)
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not updated: {exc}")
            return
        snapshot = await get_vote_snapshot(vote_post_id)
        if snapshot is None:
            await ctx.interaction.edit_original_response(content="Vote not found.")
            return
        if snapshot.status != "Open":
            await ctx.interaction.edit_original_response(
                content="Vote not updated: vote is already closed."
            )
            return
        # architecture-check: allow - Discord response copy, not embedded SQL.
        await _send_vote_update_panel(ctx, snapshot)

    @group.command(name="status", description="Show vote status and reminder state.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_status(
        ctx: discord.ApplicationContext,
        vote: str = discord.Option(
            str,
            "Vote to inspect",
            autocomplete=_vote_post_autocomplete,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            vote_post_id = _parse_vote_post_id(vote)
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not found: {exc}")
            return
        snapshot = await get_vote_snapshot(vote_post_id)
        if snapshot is None:
            await ctx.interaction.edit_original_response(content="Vote not found.")
            return
        reminder_lines = [
            f"{r.offset_minutes_before_close}m: {'sent' if r.sent_at_utc else 'pending'}"
            for r in snapshot.reminders
        ] or ["No reminders configured"]
        embed = discord.Embed(
            title=f"Vote #{snapshot.vote_post_id}: {snapshot.title}",
            color=discord.Color.green() if snapshot.status == "Open" else discord.Color.red(),
        )
        embed.add_field(name="Status", value=snapshot.status, inline=True)
        embed.add_field(name="Total votes", value=str(snapshot.total_votes), inline=True)
        embed.add_field(
            name="Closes",
            value=snapshot.closes_at_utc.strftime("%Y-%m-%d %H:%M UTC"),
            inline=True,
        )
        embed.add_field(name="Reminders", value="\n".join(reminder_lines), inline=False)
        if snapshot.message_id:
            embed.add_field(
                name="Message",
                value=f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}",
                inline=False,
            )
        await ctx.interaction.edit_original_response(embed=embed)

    @group.command(name="export", description="Export final totals for a closed vote.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_export(
        ctx: discord.ApplicationContext,
        vote: str = discord.Option(
            str,
            "Closed vote to export",
            autocomplete=_closed_vote_post_autocomplete,
        ),
        mode: str = discord.Option(
            str,
            "Export type",
            choices=_EXPORT_MODE_CHOICES,
            required=False,
            default=_EXPORT_MODE_TOTALS,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            vote_post_id = _parse_vote_post_id(vote)
            export_mode = str(mode or _EXPORT_MODE_TOTALS).strip().casefold()
            if export_mode == _EXPORT_MODE_TOTALS:
                export = await build_vote_totals_export(
                    vote_post_id=vote_post_id,
                    requested_by_discord_user_id=int(ctx.user.id),
                )
                summary_embed = _build_vote_export_summary_embed(export)
                generated_message = (
                    f"Vote #{export.snapshot.vote_post_id} totals export generated."
                )
            elif export_mode == _EXPORT_MODE_VOTER_AUDIT:
                export = await build_vote_voter_audit_export(
                    vote_post_id=vote_post_id,
                    requested_by_discord_user_id=int(ctx.user.id),
                    discord_name_resolver=lambda ids: _resolve_voter_discord_names(ctx, ids),
                )
                summary_embed = _build_vote_voter_audit_export_summary_embed(export)
                generated_message = (
                    f"Vote #{export.snapshot.vote_post_id} voter audit export generated."
                )
            else:
                raise VoteValidationError("Choose a valid export type.")
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not exported: {exc}")
            return
        except Exception:
            logger.exception("vote_admin_export_failed vote=%r", vote)
            await ctx.interaction.edit_original_response(
                content="Vote export failed. Please try again."
            )
            return

        if export.is_oversized():
            await ctx.interaction.edit_original_response(
                content=(
                    "Vote export was built but is too large for Discord upload. "
                    "Ask an operator for a direct SQL export."
                )
            )
            return

        file = discord.File(export.csv_bytes, filename=export.filename)
        await ctx.followup.send(embed=summary_embed, file=file, ephemeral=True)
        await ctx.interaction.edit_original_response(content=generated_message)

    bot.add_application_command(group)
