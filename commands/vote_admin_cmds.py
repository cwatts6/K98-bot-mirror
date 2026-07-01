from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_or_leadership_only, track_usage
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
from voting.service import (
    VoteValidationError,
    attach_vote_message,
    build_create_request,
    close_vote,
    create_vote_record,
    get_vote_snapshot,
    update_vote,
)

logger = logging.getLogger(__name__)


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


def _optional_bool_choice(value: str | None) -> bool | None:
    normalized = (value or "unchanged").strip().casefold()
    if normalized == "yes":
        return True
    if normalized == "no":
        return False
    return None


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
        title: str = discord.Option(str, "Vote title"),
        description: str = discord.Option(str, "Vote description"),
        options: str = discord.Option(str, "Options separated by |, from 2 to 5 options"),
        target_channel: discord.TextChannel = discord.Option(discord.TextChannel, "Channel to post in"),
        closes_at_utc: str = discord.Option(str, "UTC close time, e.g. 2026-07-01 20:30"),
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
                raw_options=options,
                close_time_utc=closes_at_utc,
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

        snapshot = await create_vote_record(req)
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
        vote_post_id: int = discord.Option(int, "Vote ID to close"),
        reason: str = discord.Option(str, "Close reason", required=False, default="closed early"),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        result, snapshot = await close_vote(
            vote_post_id=vote_post_id,
            actor_discord_user_id=int(ctx.user.id),
            reason=reason,
        )
        if snapshot is None:
            await ctx.interaction.edit_original_response(content=result.message)
            return
        channel = bot.get_channel(snapshot.channel_id) or await bot.fetch_channel(snapshot.channel_id)
        message = await channel.fetch_message(snapshot.message_id) if snapshot.message_id else None
        if message is not None:
            await message.edit(
                embed=build_vote_embed(snapshot),
                attachments=[build_vote_file(snapshot)],
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
        vote_post_id: int = discord.Option(int, "Vote number to change"),
        title: str = discord.Option(str, "New title", required=False, default=None),
        description: str = discord.Option(str, "New description", required=False, default=None),
        closes_at_utc: str = discord.Option(
            str,
            "New UTC close time, e.g. 2026-07-01 20:30",
            required=False,
            default=None,
        ),
        reminder_offsets_minutes: str = discord.Option(
            str,
            "Replace unsent reminder offsets, comma-separated minutes",
            required=False,
            default=None,
        ),
        reminder_mention_everyone: str = discord.Option(
            str,
            "Mention @everyone on future reminders",
            required=False,
            default="unchanged",
            choices=["unchanged", "yes", "no"],
        ),
        close_mention_everyone: str = discord.Option(
            str,
            "Mention @everyone on close",
            required=False,
            default="unchanged",
            choices=["unchanged", "yes", "no"],
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            snapshot = await update_vote(
                vote_post_id=vote_post_id,
                actor_discord_user_id=int(ctx.user.id),
                title=title,
                description=description,
                close_time_utc=closes_at_utc,
                reminder_offsets=reminder_offsets_minutes,
                reminder_mention_everyone=_optional_bool_choice(reminder_mention_everyone),
                close_mention_everyone=_optional_bool_choice(close_mention_everyone),
            )
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Vote not updated: {exc}")
            return
        if snapshot.message_id:
            channel = bot.get_channel(snapshot.channel_id) or await bot.fetch_channel(snapshot.channel_id)
            message = await channel.fetch_message(snapshot.message_id)
            await message.edit(
                embed=build_vote_embed(snapshot),
                attachments=[build_vote_file(snapshot)],
                view=VotePostView(snapshot),
                allowed_mentions=no_broad_mentions(),
            )
        await ctx.interaction.edit_original_response(content=f"Vote #{vote_post_id} updated.")

    @group.command(name="status", description="Show vote status and reminder state.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_status(
        ctx: discord.ApplicationContext,
        vote_post_id: int = discord.Option(int, "Vote ID to inspect"),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
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

    bot.add_application_command(group)
