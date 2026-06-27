# commands/subscriptions_cmds.py
from __future__ import annotations

from datetime import UTC, datetime
import io
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
from event_scheduler import dm_scheduled_tracker, dm_sent_tracker
from reminder_task_registry import active_task_count
from subscription_tracker import (
    get_all_subscribers,
    migrate_subscriptions,
)
from versioning import versioned

logger = logging.getLogger(__name__)


def register_subscriptions(bot: ext_commands.Bot) -> None:
    subscriptions_group = discord.SlashCommandGroup(
        "subscriptions",
        "Subscription admin controls",
        guild_ids=[GUILD_ID],
    )

    @bot.slash_command(
        name="subscribe",
        description="Subscribe to KVK event reminders via DM",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.11")
    @safe_command
    @track_usage()
    async def subscribe_command(ctx):
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/subscribe",
                new_path="/me reminders",
                detail="The reminder centre now manages KVK and calendar reminders in one private guided flow.",
            ),
            ephemeral=True,
        )
        return

    @bot.slash_command(
        name="modify_subscription",
        # architecture-check: allow
        description="Update your KVK event reminder preferences",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.09")
    @safe_command
    @track_usage()
    async def modify_subscribe_command(ctx):
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/modify_subscription",
                new_path="/me reminders",
                detail="The reminder centre now updates reminder types, timings, and remove-all settings in one private guided flow.",
            ),
            ephemeral=True,
        )
        return

    @bot.slash_command(
        name="unsubscribe", description="Stop receiving KVK event reminders", guild_ids=[GUILD_ID]
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def unsubscribe_command(ctx):
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/unsubscribe",
                new_path="/me reminders",
                detail="The reminder centre now handles remove-all/unsubscribe with confirmation in the private reminder flow.",
            ),
            ephemeral=True,
        )
        return

    @subscriptions_group.command(
        name="list",
        description="View all subscribed users (Admin only)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def list_subscribers(ctx):

        await safe_defer(ctx, ephemeral=True)

        try:
            subs = get_all_subscribers() or {}
        except Exception as e:
            logger.exception("[/list_subscribers] get_all_subscribers failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to fetch subscribers: `{type(e).__name__}: {e}`"
            )
            return

        if not subs:
            await ctx.interaction.edit_original_response(
                content="📭 No users are currently subscribed."
            )
            return

        # Normalize + sort by username (case-insensitive)
        items = []
        for uid, data in subs.items():
            username = str(data.get("username", "Unknown"))
            types = ", ".join(data.get("subscriptions", [])) or "None"
            times = ", ".join(data.get("reminder_times", [])) or "None"
            uid_str = str(uid)  # mention formatting

            # Live stats (best-effort)
            try:
                # Count scheduled deltas and sent deltas for this user across all events
                scheduled = sum(
                    len(per_user.get(uid_str, set())) for per_user in dm_scheduled_tracker.values()
                )
                sent = sum(len(per_user.get(uid_str, [])) for per_user in dm_sent_tracker.values())
                tasks = active_task_count(uid_str)
            except Exception:
                scheduled = sent = tasks = 0

            items.append((username, uid_str, types, times, scheduled, sent, tasks))
        items.sort(key=lambda t: t[0].lower())

        embed = discord.Embed(
            title="📋 Subscribed Users",
            description=f"{len(items)} user(s) currently subscribed to reminders.",
            color=discord.Color.blurple(),
        )

        MAX_FIELDS = 25  # Discord embed field limit
        shown = items[:MAX_FIELDS]
        for username, uid_str, types, times, scheduled, sent, tasks in shown:
            mention = f"<@{uid_str}>" if uid_str.isdigit() else uid_str
            embed.add_field(
                name=f"{username} • {mention}",
                value=(
                    f"**Types:** {types}\n"
                    f"**Times:** {times}\n"
                    f"**Queues:** {scheduled} scheduled • {tasks} task(s) • {sent} sent"
                ),
                inline=False,
            )

        attachments = []
        if len(items) > MAX_FIELDS:
            # Attach the full list as CSV (includes live stats)
            buf = io.StringIO()
            buf.write("username,user_id,types,times,scheduled_sent,history_sent,active_tasks\n")
            for username, uid_str, types, times, scheduled, sent, tasks in items:
                buf.write(f"{username},{uid_str},{types},{times},{scheduled},{sent},{tasks}\n")
            data = io.BytesIO(buf.getvalue().encode("utf-8", "replace"))
            data.seek(0)
            attachments = [discord.File(data, filename="subscribers_full.csv")]
            embed.set_footer(text=f"Showing first {MAX_FIELDS}. Full list attached.")

        await ctx.interaction.edit_original_response(embed=embed, attachments=attachments)

    def _send_report_text_or_file(interaction: discord.Interaction, title: str, summary: str):
        """
        Edits the original interaction with a short message and (if needed) a full report file.
        """
        MAX_DISCORD = 1900  # be safe under 2000 incl. code fences etc.
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        if len(summary) <= MAX_DISCORD:
            return interaction.edit_original_response(
                content=f"**{title}**\n```text\n{summary}\n```"
            )
        # attach as file
        buf = io.BytesIO(summary.encode("utf-8", "replace"))
        file = discord.File(buf, filename=f"subscription_migration_report_{ts}.txt")
        return interaction.edit_original_response(
            content=f"**{title}**\nReport was long; attached full details.", attachments=[file]
        )

    @subscriptions_group.command(
        name="migrate_dryrun",
        description="(Admin) Show what would change in the subscription file (no writes)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def migrate_subscriptions_dryrun(ctx):
        await ctx.defer(ephemeral=True)
        try:
            before, after, summary = migrate_subscriptions(dry_run=True)
            await _send_report_text_or_file(
                ctx.interaction, title=f"Dry Run: subscriptions {before} → {after}", summary=summary
            )
        except Exception as e:
            await ctx.interaction.edit_original_response(
                content=f"❌ Dry run failed: `{type(e).__name__}: {e}`"
            )

    @subscriptions_group.command(
        name="migrate_apply",
        description="(Admin) Apply the subscription migration (writes file; backup created)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def migrate_subscriptions_apply(ctx):
        await ctx.defer(ephemeral=True)
        try:
            before, after, summary = migrate_subscriptions(dry_run=False)
            await _send_report_text_or_file(
                ctx.interaction, title=f"Applied: subscriptions {before} → {after}", summary=summary
            )
        except Exception as e:
            await ctx.interaction.edit_original_response(
                content=f"❌ Migration failed: `{type(e).__name__}: {e}`"
            )

    bot.add_application_command(subscriptions_group)
