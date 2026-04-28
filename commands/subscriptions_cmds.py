# commands/subscriptions_cmds.py
from __future__ import annotations

from datetime import UTC, datetime
import io
import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from constants import DEFAULT_REMINDER_TIMES, VALID_TYPES
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
from dm_tracker_utils import (
    purge_user_from_dm_scheduled_tracker,
    purge_user_from_dm_sent_tracker,
)
from event_scheduler import dm_scheduled_tracker, dm_sent_tracker
from reminder_task_registry import active_task_count, cancel_user_reminder_tasks
from subscription_tracker import (
    get_all_subscribers,
    get_user_config,
    migrate_subscriptions,
    remove_user,
    set_user_config,
)
from ui.views.subscription_views import SubscriptionView
from versioning import versioned

logger = logging.getLogger(__name__)


def register_subscriptions(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="subscribe",
        description="Subscribe to KVK event reminders via DM",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.11")
    @safe_command
    @track_usage()
    async def subscribe_command(ctx):
        user = ctx.user
        uid = user.id
        username = str(user)

        existing = get_user_config(uid)
        if existing:
            await ctx.respond(
                "❌ You're already subscribed. Use `/modify_subscription` to change your preferences.",
                ephemeral=True,
            )
            return

        async def _on_timeout_edit(view: SubscriptionView):
            try:
                msg = await ctx.interaction.original_response()
                await msg.edit(view=view)
            except Exception:
                pass

        async def _on_confirm(interaction: discord.Interaction, view: SubscriptionView):
            types = list(view.selected_types)
            times = list(view.selected_reminders)
            if not times:
                times = DEFAULT_REMINDER_TIMES
            if not types:
                await interaction.response.send_message(
                    "❌ Please select at least one event type.", ephemeral=True
                )
                return
            if not times:
                await interaction.response.send_message(
                    "❌ Please select at least one reminder time.", ephemeral=True
                )
                return

            valid_types = set(VALID_TYPES)
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                await interaction.response.send_message(
                    f"❌ Invalid event types: {', '.join(invalid_types)}", ephemeral=True
                )
                return
            valid_times = set(DEFAULT_REMINDER_TIMES)
            invalid_times = [t for t in times if t not in valid_times]
            if invalid_times:
                await interaction.response.send_message(
                    f"❌ Invalid reminder times: {', '.join(invalid_times)}", ephemeral=True
                )
                return

            original_types = types.copy()
            if "all" in types:
                types = ["all"]
            elif "fights" in types:
                types = [t for t in types if t not in ("altars", "major")]
            try:
                set_user_config(view.uid, view.username, types, times)
            except Exception as e:
                logger.exception("[subscribe] set_user_config failed")
                await interaction.response.send_message(
                    f"❌ Failed to save your subscription: `{type(e).__name__}: {e}`",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="👋 Subscribed to Event Reminders",
                description=f"Hi {view.user.mention}, you're now subscribed to event reminders!",
                color=0x2ECC71,
            )
            embed.add_field(name="Event Types", value=", ".join(types), inline=False)
            embed.add_field(name="Reminder Times", value=", ".join(times), inline=False)

            if set(types) != set(original_types):
                embed.add_field(
                    name="⚠️ Note",
                    value="Some selections were adjusted to avoid duplicate reminders (e.g., 'all' disables others).",
                    inline=False,
                )
            embed.set_footer(text="You can update these anytime with /modify_subscription")

            try:
                await view.user.send(embed=embed)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Could not send DM. Please enable DMs from this server and try again.",
                    ephemeral=True,
                )
                return

            for c in view.children:
                c.disabled = True
            await interaction.response.edit_message(
                content="✅ Subscribed successfully! A confirmation has been sent via DM.",
                view=view,
            )
            view.stop()

        await ctx.respond(
            "📝 Please complete your subscription below:",
            view=SubscriptionView(
                user=user,
                uid=uid,
                username=username,
                selected_types=[],
                selected_reminders=[],
                confirm_label="✅ Confirm",
                include_unsubscribe=False,
                reminder_min_values=1,
                cid_prefix="sub",
                on_confirm=_on_confirm,
                on_timeout_edit=_on_timeout_edit,
            ),
            ephemeral=True,
        )

    @bot.slash_command(
        name="modify_subscription",
        description="Update your KVK event reminder preferences",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.09")
    @safe_command
    @track_usage()
    async def modify_subscribe_command(ctx):

        user = ctx.user
        uid = user.id
        username = str(user)

        existing = get_user_config(uid)
        if not existing:
            await ctx.respond(
                "❌ You're not currently subscribed. Use `/subscribe` to set your preferences.",
                ephemeral=True,
            )
            return

        existing_types = list(existing.get("subscriptions", []))
        existing_times = list(existing.get("reminder_times", []))

        async def _on_timeout_edit(view: SubscriptionView):
            try:
                msg = await ctx.interaction.original_response()
                await msg.edit(view=view)
            except Exception:
                pass

        async def _on_unsubscribe(interaction: discord.Interaction, view: SubscriptionView):
            try:
                cancelled = cancel_user_reminder_tasks(uid)
                sched_removed = purge_user_from_dm_scheduled_tracker(uid)
                sent_removed = purge_user_from_dm_sent_tracker(uid)
                remove_user(uid)
                logger.info(
                    "[unsubscribe] uid=%s | tasks_cancelled=%s scheduled_removed=%s sent_removed=%s",
                    uid,
                    cancelled,
                    sched_removed,
                    sent_removed,
                )

            except Exception as e:
                logger.exception("[modify_subscription] unsubscribe failed")
                await interaction.response.send_message(
                    f"❌ Failed to unsubscribe: `{type(e).__name__}: {e}`", ephemeral=True
                )
                return

            for c in view.children:
                c.disabled = True
            await interaction.response.edit_message(
                content="✅ You’ve been unsubscribed.", view=view
            )
            try:
                await user.send(
                    embed=discord.Embed(
                        title="🔕 Unsubscribed",
                        description=f"Hi {user.mention}, you’ve been unsubscribed from all event reminders.",
                        color=0xE74C3C,
                    )
                )
            except discord.Forbidden:
                pass
            view.stop()

        async def _on_confirm(interaction: discord.Interaction, view: SubscriptionView):
            types = list(view.selected_types)
            times = list(view.selected_reminders)
            if not times:
                times = DEFAULT_REMINDER_TIMES

            if not types:
                await interaction.response.send_message(
                    "❌ Please select at least one event type.", ephemeral=True
                )
                return
            if not times:
                await interaction.response.send_message(
                    "❌ Please select at least one reminder time.", ephemeral=True
                )
                return

            invalid_types = [t for t in types if t not in VALID_TYPES]
            if invalid_types:
                await interaction.response.send_message(
                    f"❌ Invalid event types: {', '.join(invalid_types)}", ephemeral=True
                )
                return
            invalid_times = [t for t in times if t not in DEFAULT_REMINDER_TIMES]
            if invalid_times:
                await interaction.response.send_message(
                    f"❌ Invalid reminder times: {', '.join(invalid_times)}", ephemeral=True
                )
                return

            original_types = types.copy()
            if "all" in types:
                types = ["all"]
            elif "fights" in types:
                types = [t for t in types if t not in ("altars", "major")]

            try:
                set_user_config(view.uid, view.username, types, times)
            except Exception as e:
                logger.exception("[modify_subscription] set_user_config failed")
                await interaction.response.send_message(
                    f"❌ Failed to save your preferences: `{type(e).__name__}: {e}`",
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title="🔄 Preferences Updated",
                description=f"Hi {view.user.mention}, your event reminder preferences are now updated!",
                color=0xF1C40F,
            )
            embed.add_field(name="Event Types", value=", ".join(types), inline=False)
            embed.add_field(name="Reminder Times", value=", ".join(times), inline=False)

            if set(types) != set(original_types):
                embed.add_field(
                    name="⚠️ Note",
                    value="Some selections were adjusted to avoid duplicate reminders (e.g., 'all' disables others).",
                    inline=False,
                )
            embed.set_footer(text="You can update these anytime with /modify_subscription")

            try:
                await view.user.send(embed=embed)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Could not send DM. Please enable DMs from this server.", ephemeral=True
                )
                return

            for c in view.children:
                c.disabled = True
            await interaction.response.edit_message(
                content="✅ Preferences updated! A confirmation has been sent via DM.",
                view=view,
            )
            view.stop()

        await ctx.respond(
            "🛠️ Update your preferences below:",
            view=SubscriptionView(
                user=user,
                uid=uid,
                username=username,
                selected_types=existing_types,
                selected_reminders=existing_times,
                confirm_label="✅ Update Preferences",
                include_unsubscribe=True,
                reminder_min_values=0,
                cid_prefix="modsub",
                on_confirm=_on_confirm,
                on_unsubscribe=_on_unsubscribe,
                on_timeout_edit=_on_timeout_edit,
            ),
            ephemeral=True,
        )

    @bot.slash_command(
        name="unsubscribe", description="Stop receiving KVK event reminders", guild_ids=[GUILD_ID]
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def unsubscribe_command(ctx):

        await safe_defer(ctx, ephemeral=True)

        user = ctx.user
        uid = user.id

        # Look up existing config once
        existing = get_user_config(uid)
        if not existing:
            await ctx.interaction.edit_original_response(
                content="❌ You’re not currently subscribed to any reminders. Use `/subscribe` to get started."
            )
            return

        # Keep a copy for the DM summary
        prev_types = list(existing.get("subscriptions", []))
        prev_times = list(existing.get("reminder_times", []))

        # Remove from the store (cancel tasks, purge trackers, then remove config)
        try:
            cancelled = cancel_user_reminder_tasks(uid)  # no-op if none
            sched_removed = purge_user_from_dm_scheduled_tracker(uid)  # per-user, per-event buckets
            sent_removed = purge_user_from_dm_sent_tracker(uid)  # per-user, per-event buckets
            success = remove_user(uid)
            if success:
                logger.info(
                    "[UNSUBSCRIBE] uid=%s | success=1 tasks_cancelled=%s scheduled_removed=%s sent_removed=%s",
                    uid,
                    cancelled,
                    sched_removed,
                    sent_removed,
                )
            else:
                logger.info("[UNSUBSCRIBE] No subscription found for user %s (stale state)", uid)
        except Exception as e:
            logger.exception("[UNSUBSCRIBE] remove_user failed for %s", uid)
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to unsubscribe: `{type(e).__name__}: {e}`"
            )
            return

        # Build DM confirmation (include prior settings for the user's record)
        embed = discord.Embed(
            title="🔕 Unsubscribed",
            description=f"Hi {user.mention}, you’ve been unsubscribed from all event reminders.",
            color=0xE74C3C,
        )
        embed.add_field(
            name="Previous Event Types", value=", ".join(prev_types) or "None", inline=False
        )
        embed.add_field(
            name="Previous Reminder Times", value=", ".join(prev_times) or "None", inline=False
        )
        embed.set_footer(text="You can re-subscribe anytime with /subscribe")

        # Try sending DM first (doesn't affect the unsubscribe result)
        dm_sent = True
        try:
            await user.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            dm_sent = False

        # Confirm in the interaction (single-ack path)
        try:
            if dm_sent:
                await ctx.interaction.edit_original_response(
                    content="✅ You’ve been unsubscribed. A confirmation has been sent via DM."
                )
            else:
                await ctx.interaction.edit_original_response(
                    content="✅ You’ve been unsubscribed, but I couldn’t send you a DM. You’re all set!"
                )
        except discord.HTTPException:
            # If the original response was deleted or already acknowledged elsewhere, ignore.
            pass

    @bot.slash_command(
        name="list_subscribers",
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

    @bot.slash_command(
        name="migrate_subscriptions_dryrun",
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

    @bot.slash_command(
        name="migrate_subscriptions_apply",
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
