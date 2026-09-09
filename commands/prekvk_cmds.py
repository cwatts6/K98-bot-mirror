from __future__ import annotations

import logging

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID, KVK_PLAYER_STATS_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID
from commands.deprecation_helpers import CommandRedirect, send_deprecated_command_redirect
from core.interaction_safety import safe_command, safe_defer
from decoraters import is_admin_and_notify_channel, track_usage
from utils import utcnow
from versioning import versioned

from .prekvk_admin_cmds import attach_prekvk_import_history

logger = logging.getLogger(__name__)


def register_prekvk(bot: ext_commands.Bot) -> None:
    group = discord.SlashCommandGroup(
        "prekvk",
        "PreKvK reports and diagnostics",
        guild_ids=[GUILD_ID],
    )

    @group.command(
        name="report",
        description="View the current PreKvK rankings report",
    )
    @versioned("v1.00")
    @safe_command
    @track_usage()
    async def prekvk_report(
        ctx: discord.ApplicationContext,
        kvk_no: int | None = discord.Option(
            int,
            "Optional KVK number; defaults to the current KVK",
            required=False,
            default=None,
            min_value=1,
        ),
        sort_by: str = discord.Option(
            str,
            "Initial report ordering",
            choices=["Overall", "Stage 1", "Stage 2", "Stage 3"],
            required=False,
            default="Overall",
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        await send_deprecated_command_redirect(
            ctx,
            CommandRedirect(
                old_path="/prekvk report",
                new_path="/kvk rankings type:prekvk",
                detail=(
                    "PreKvK rankings now live in the unified KVK rankings browser. "
                    f"Run it in <#{KVK_PLAYER_STATS_CHANNEL_ID}>."
                ),
            ),
            ephemeral=True,
        )
        return

    @group.command(
        name="dispatch_test",
        description="Inspect or run an isolated, mention-neutral Pre-KVK diagnostic",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def prekvk_dispatch_test(
        ctx,
        destination: discord.TextChannel = discord.Option(
            discord.TextChannel, "Explicit diagnostic text destination"
        ),
        action: str = discord.Option(
            str, "Run or inspect an existing session", choices=["run", "status"], default="run"
        ),
        session: str | None = discord.Option(
            str, "Issued session token; optional for a new session", required=False, default=None
        ),
    ):
        from bot_config import STATS_ALERT_CHANNEL_ID
        from core.interaction_safety import send_ephemeral
        from stats_alerts.diagnostics import runner, validate_destination
        from stats_alerts.embeds.prekvk import send_prekvk_embed
        from ui.views.prekvk_dispatch_diagnostic_view import PreKvkDispatchDiagnosticView

        def check_destination():
            requester = destination.permissions_for(ctx.user)
            publisher = destination.permissions_for(ctx.guild.me)
            validate_destination(
                guild_id=ctx.guild.id,
                expected_guild_id=int(GUILD_ID),
                channel_guild_id=destination.guild.id,
                channel_id=destination.id,
                forbidden_channels={STATS_ALERT_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID},
                is_text=isinstance(destination, discord.TextChannel)
                and destination.type == discord.ChannelType.text,
                requester_can_send=requester.view_channel and requester.send_messages,
                bot_can_publish=(
                    publisher.view_channel
                    and publisher.send_messages
                    and publisher.embed_links
                    and publisher.read_message_history
                ),
            )

        async def publish(opened, receipt):
            check_destination()
            return await send_prekvk_embed(
                bot,
                destination,
                utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                diagnostic_store=opened.store,
                diagnostic_check_destination=check_destination,
                diagnostic_view_factory=lambda events: PreKvkDispatchDiagnosticView(events, opened),
                on_diagnostic_receipt=lambda message_id: setattr(receipt, "message_id", message_id),
            )

        try:
            check_destination()
            if not await safe_defer(ctx, ephemeral=True):
                return
            result = await runner.execute(
                guild_id=ctx.guild.id,
                channel_id=destination.id,
                owner_id=ctx.user.id,
                token=session,
                action=action,
                publish=publish,
            )
            snapshot = result.snapshot or {}
            attempt = snapshot.get("attempt") or {}
            message_id = result.receipt or snapshot.get("message_id")
            lines = [
                "**Pre-KVK isolated diagnostic — outside calendar routing**",
                f"Outcome: **{result.outcome}** — {result.detail}",
                f"Session: `{result.session}`",
                f"Destination: `{destination.id}`",
                f"UTC: `{utcnow().isoformat()}`",
                f"Durable phase: `{attempt.get('phase', 'none')}`",
                f"Attempt: `{attempt.get('token', 'none')}`",
                f"Fresh admission blocked (observation): `{snapshot.get('guarded', 'unknown')}`",
            ]
            if message_id:
                lines.append(
                    f"Message: https://discord.com/channels/{ctx.guild.id}/{destination.id}/{message_id}"
                )
            await send_ephemeral(
                ctx.interaction, "\n".join(lines), allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception:
            logger.exception("[PREKVK DIAGNOSTIC] Command rejected or failed")
            await send_ephemeral(
                ctx.interaction,
                "Diagnostic unavailable. Check destination, session ownership and logs. No automatic retry.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

    attach_prekvk_import_history(group)
    bot.add_application_command(group)
