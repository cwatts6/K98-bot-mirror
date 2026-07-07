from __future__ import annotations

from collections.abc import Iterable, Mapping
import logging
import re

import discord
from discord.ext import commands as ext_commands

from bot_config import GUILD_ID
from core.interaction_safety import safe_command, safe_defer, send_ephemeral
from decoraters import is_admin_or_leadership_only, track_usage
from ui.views.survey_admin_update_view import SurveyAdminUpdateView
from ui.views.survey_post_view import SurveyBuilderView, SurveyPostView, disabled_survey_view
from ui.views.vote_admin_dashboard_view import VoteAdminDashboardView
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
from voting.option_emojis import option_display_label
from voting.reporting_service import build_admin_leadership_dashboard_report
from voting.result_visibility import (
    RESULT_VISIBILITY_PUBLIC_LIVE,
    result_visibility_label,
)
from voting.service import (
    CLOSE_DURATION_CHOICES,
    MAX_CLOSE_REASON_LEN,
    MAX_DESCRIPTION_LEN,
    MAX_OPTION_LABEL_LEN,
    MAX_TITLE_LEN,
    RESULT_VISIBILITY_CHOICES,
    VOTE_MODE_CHOICES,
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
from voting.survey_export_service import (
    build_survey_report_bundle_export,
    build_survey_response_detail_export,
    build_survey_totals_export,
)
from voting.survey_models import (
    SURVEY_QUESTION_RANKING,
    SURVEY_QUESTION_RATING,
    SURVEY_QUESTION_TEXT,
    ranking_count_for_value,
    rating_distribution_text,
    rating_scale_text,
)
from voting.survey_presentation import (
    build_survey_close_embed,
    build_survey_embed,
    build_survey_file,
)
from voting.survey_service import (
    attach_survey_message,
    build_create_request as build_survey_create_request,
    cancel_survey_launch_failure,
    close_survey,
    create_survey_record,
    get_survey_snapshot,
    search_closed_survey_choices,
    search_survey_choices,
)
from voting.vote_modes import VOTE_MODE_ONE_CHOICE, normalize_vote_mode, vote_mode_label

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
_RESULT_VISIBILITY_CHOICES = [
    discord.OptionChoice(name=label, value=value)
    for value, label in RESULT_VISIBILITY_CHOICES.items()
]
_VOTE_MODE_CHOICES = [
    discord.OptionChoice(name=label, value=value) for value, label in VOTE_MODE_CHOICES.items()
]
_SURVEY_EXPORT_MODE_TOTALS = "totals"
_SURVEY_EXPORT_MODE_RESPONSE_DETAIL = "response_detail"
_SURVEY_EXPORT_MODE_REPORT_BUNDLE = "report_bundle"
_SURVEY_EXPORT_MODE_CHOICES = [
    discord.OptionChoice(name="Totals only", value=_SURVEY_EXPORT_MODE_TOTALS),
    discord.OptionChoice(name="Response detail", value=_SURVEY_EXPORT_MODE_RESPONSE_DETAIL),
    discord.OptionChoice(name="Report bundle", value=_SURVEY_EXPORT_MODE_REPORT_BUNDLE),
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


def _parse_survey_id(value: str | int) -> int:
    if isinstance(value, int):
        return int(value)
    text = str(value or "").strip()
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"#(\d+)", text)
    if match:
        return int(match.group(1))
    raise VoteValidationError("Choose a survey from autocomplete.")


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


async def _survey_autocomplete(ctx: discord.AutocompleteContext):
    query = str(getattr(ctx, "value", "") or "")
    try:
        choices = await search_survey_choices(query=query, limit=25)
    except Exception:
        logger.exception("survey_autocomplete_failed query=%r", query)
        return []
    output = []
    for choice in choices:
        closes = choice.closes_at_utc.strftime("%Y-%m-%d %H:%M UTC")
        label = f"#{choice.survey_id} {choice.title} | {choice.status} | {closes}"
        output.append(discord.OptionChoice(name=label[:100], value=str(choice.survey_id)))
    return output


async def _closed_survey_autocomplete(ctx: discord.AutocompleteContext):
    query = str(getattr(ctx, "value", "") or "")
    try:
        choices = await search_closed_survey_choices(query=query, limit=25)
    except Exception:
        logger.exception("closed_survey_autocomplete_failed query=%r", query)
        return []
    output = []
    for choice in choices:
        closed_at = choice.closed_at_utc or choice.closes_at_utc
        closed = closed_at.strftime("%Y-%m-%d %H:%M UTC")
        label = f"#{choice.survey_id} {choice.title} | Closed | {closed}"
        output.append(discord.OptionChoice(name=label[:100], value=str(choice.survey_id)))
    return output


def _build_vote_export_summary_embed(export) -> discord.Embed:
    snapshot = export.snapshot
    embed = discord.Embed(
        title=f"Vote #{snapshot.vote_post_id} totals export",
        description=export.outcome_summary,
        color=discord.Color.blurple(),
    )
    is_multi_select = normalize_vote_mode(snapshot.vote_mode) != VOTE_MODE_ONE_CHOICE
    embed.add_field(
        name="Total voters" if is_multi_select else "Total votes",
        value=str(snapshot.total_votes),
        inline=True,
    )
    if is_multi_select:
        embed.add_field(name="Total selections", value=str(snapshot.total_selections), inline=True)
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
    is_multi_select = normalize_vote_mode(snapshot.vote_mode) != VOTE_MODE_ONE_CHOICE
    embed.add_field(
        name="Total voters" if is_multi_select else "Total votes",
        value=str(snapshot.total_votes),
        inline=True,
    )
    if is_multi_select:
        embed.add_field(name="Total selections", value=str(snapshot.total_selections), inline=True)
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


def _build_survey_totals_export_summary_embed(export) -> discord.Embed:
    snapshot = export.snapshot
    embed = discord.Embed(
        title=f"Survey #{snapshot.survey_id} totals export",
        description="Per-question option totals for one closed survey.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Responses", value=str(snapshot.total_responses), inline=True)
    embed.add_field(name="Questions", value=str(len(snapshot.questions)), inline=True)
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
    if snapshot.message_id:
        embed.add_field(
            name="Message",
            value=f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}",
            inline=False,
        )
    embed.set_footer(text="Totals-only survey export.")
    return embed


def _build_survey_response_detail_export_summary_embed(export) -> discord.Embed:
    snapshot = export.snapshot
    embed = discord.Embed(
        title=f"Survey #{snapshot.survey_id} response detail export",
        description="Response-level detail rows for one closed survey.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Responses", value=str(snapshot.total_responses), inline=True)
    embed.add_field(name="Questions", value=str(len(snapshot.questions)), inline=True)
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
    embed.set_footer(text="Private response-detail export. Includes Discord user ID and name.")
    return embed


def _build_survey_report_bundle_export_summary_embed(export) -> discord.Embed:
    snapshot = export.snapshot
    embed = discord.Embed(
        title=f"Survey #{snapshot.survey_id} report bundle",
        description=(
            "Private reporting CSV bundle for one closed survey. Aggregate files exclude raw "
            "answers; response detail includes Discord user ID and name."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Responses", value=str(snapshot.total_responses), inline=True)
    embed.add_field(name="Questions", value=str(len(snapshot.questions)), inline=True)
    embed.add_field(name="Files", value=str(len(export.files)), inline=True)
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
    embed.add_field(
        name="Profiles",
        value="\n".join(f"{file.filename}: {file.row_count} row(s)" for file in export.files)[
            :1024
        ],
        inline=False,
    )
    embed.set_footer(text="Private admin/leadership report bundle.")
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


async def _send_survey_update_panel(ctx: discord.ApplicationContext, snapshot) -> None:
    # architecture-check: allow - Discord response copy, not embedded SQL.
    content = f"Choose what to update for Survey #{snapshot.survey_id}."
    view = SurveyAdminUpdateView(snapshot, owner_user_id=int(ctx.user.id))
    followup = getattr(ctx, "followup", None)
    if followup is not None and hasattr(followup, "send"):
        try:
            await followup.send(content=content, view=view, ephemeral=True)
            # architecture-check: allow - Discord response copy, not embedded SQL.
            await ctx.interaction.edit_original_response(
                # architecture-check: allow - Discord response copy, not embedded SQL.
                content=f"Update panel opened for Survey #{snapshot.survey_id}."
            )
            return
        except Exception:
            logger.exception("survey_admin_update_followup_failed survey_id=%s", snapshot.survey_id)

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
        result_visibility: str = discord.Option(
            str,
            "Show live results publicly or hide them until close",
            choices=_RESULT_VISIBILITY_CHOICES,
            required=False,
            default=RESULT_VISIBILITY_PUBLIC_LIVE,
        ),
        vote_mode: str = discord.Option(
            str,
            "Whether players choose one option or multiple options",
            choices=_VOTE_MODE_CHOICES,
            required=False,
            default=VOTE_MODE_ONE_CHOICE,
        ),
        min_selections: int = discord.Option(
            int,
            # architecture-check: allow - Discord option copy, not embedded SQL.
            "Minimum options for multi-select votes",
            required=False,
            default=1,
            min_value=1,
            max_value=6,
        ),
        max_selections: int = discord.Option(
            int,
            # architecture-check: allow - Discord option copy, not embedded SQL.
            "Maximum options for multi-select votes",
            required=False,
            default=1,
            min_value=1,
            max_value=6,
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
                result_visibility=result_visibility,
                vote_mode=vote_mode,
                min_selections=min_selections,
                max_selections=max_selections,
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
        is_multi_select = normalize_vote_mode(snapshot.vote_mode) != VOTE_MODE_ONE_CHOICE
        embed.add_field(
            name="Total voters" if is_multi_select else "Total votes",
            value=str(snapshot.total_votes),
            inline=True,
        )
        if is_multi_select:
            embed.add_field(
                name="Total selections",
                value=str(snapshot.total_selections),
                inline=True,
            )
        embed.add_field(
            name="Result visibility",
            value=result_visibility_label(snapshot.result_visibility),
            inline=True,
        )
        embed.add_field(
            name="Vote mode",
            value=(
                f"{vote_mode_label(snapshot.vote_mode)} "
                f"({snapshot.min_selections}-{snapshot.max_selections} selections)"
            ),
            inline=True,
        )
        embed.add_field(
            name="Closes",
            value=snapshot.closes_at_utc.strftime("%Y-%m-%d %H:%M UTC"),
            inline=True,
        )
        option_label = "selections" if is_multi_select else "votes"
        option_lines = [
            f"{option_display_label(option.label, option.emoji)}: {option.vote_count} {option_label}"
            for option in snapshot.options
        ] or ["No options configured"]
        embed.add_field(
            name="Option totals",
            value="\n".join(option_lines)[:1024],
            inline=False,
        )
        embed.add_field(name="Reminders", value="\n".join(reminder_lines), inline=False)
        if snapshot.message_id:
            embed.add_field(
                name="Message",
                value=f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}",
                inline=False,
            )
        await ctx.interaction.edit_original_response(embed=embed)

    @group.command(
        name="dashboard",
        description="Open a private aggregate vote and survey dashboard.",
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def vote_dashboard(ctx: discord.ApplicationContext) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            contract = await build_admin_leadership_dashboard_report()
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Dashboard not opened: {exc}")
            return
        except Exception:
            logger.exception("vote_admin_dashboard_failed")
            await ctx.interaction.edit_original_response(
                content="Dashboard could not be opened. Please try again."
            )
            return

        view = VoteAdminDashboardView(contract, owner_user_id=int(ctx.user.id))
        await ctx.interaction.edit_original_response(embed=view.current_embed(), view=view)

    @group.command(name="export", description="Export closed vote totals or voter audit.")
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
                generated_message = f"Vote #{export.snapshot.vote_post_id} totals export generated."
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

    @group.command(
        name="survey_create", description="Build and start a durable multi-question survey."
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def survey_create(
        ctx: discord.ApplicationContext,
        title: str = discord.Option(str, "Survey title", max_length=MAX_TITLE_LEN),
        target_channel: discord.TextChannel = discord.Option(
            discord.TextChannel, "Channel to post in"
        ),
        close_in: str = discord.Option(
            str,
            "When the survey should close",
            choices=_CLOSE_DURATION_CHOICES,
        ),
        description: str = discord.Option(
            str,
            "Survey description",
            required=False,
            default="",
            max_length=MAX_DESCRIPTION_LEN,
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
        allow_response_changes: bool = discord.Option(
            bool,
            "Allow players to change responses before close",
            required=False,
            default=True,
        ),
        result_visibility: str = discord.Option(
            str,
            "Show live results publicly or hide them until close",
            choices=_RESULT_VISIBILITY_CHOICES,
            required=False,
            default=RESULT_VISIBILITY_PUBLIC_LIVE,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        me = target_channel.guild.me
        if me is not None:
            needs_mention_everyone = (
                launch_mention_everyone or reminder_mention_everyone or close_mention_everyone
            )
            permission_error = _channel_permission_error(
                target_channel,
                me,
                needs_mention_everyone=needs_mention_everyone,
            )
            if permission_error:
                await ctx.interaction.edit_original_response(content=permission_error)
                return

        async def _publish_survey(interaction, questions) -> bool:
            try:
                req = build_survey_create_request(
                    guild_id=int(ctx.guild_id or target_channel.guild.id),
                    channel_id=int(target_channel.id),
                    created_by_discord_user_id=int(ctx.user.id),
                    title=title,
                    description=description,
                    questions=questions,
                    close_time_utc=close_in,
                    reminder_offsets=reminder_offsets_minutes,
                    allow_response_change=allow_response_changes,
                    launch_mention_everyone=launch_mention_everyone,
                    reminder_mention_everyone=reminder_mention_everyone,
                    close_mention_everyone=close_mention_everyone,
                    result_visibility=result_visibility,
                )
            except VoteValidationError as exc:
                await send_ephemeral(interaction, f"Survey not created: {exc}")
                return False

            message = None
            try:
                snapshot = await create_survey_record(req)
            except VoteValidationError as exc:
                await send_ephemeral(interaction, f"Survey not created: {exc}")
                return False
            try:
                message = await target_channel.send(
                    content=mention_content(snapshot.launch_mention_everyone, "New survey is open"),
                    embed=build_survey_embed(snapshot),
                    file=build_survey_file(snapshot),
                    view=SurveyPostView(snapshot),
                    allowed_mentions=configured_everyone_mentions(snapshot.launch_mention_everyone),
                )
                snapshot = await attach_survey_message(
                    snapshot,
                    channel_id=int(target_channel.id),
                    message_id=int(message.id),
                )
            except Exception:
                logger.exception("survey_launch_failed survey_id=%s", snapshot.survey_id)
                await cancel_survey_launch_failure(
                    survey_id=snapshot.survey_id,
                    actor_discord_user_id=int(ctx.user.id),
                    reason="launch failed",
                )
                if message is not None:
                    try:
                        cancelled = await get_survey_snapshot(snapshot.survey_id)
                        if cancelled is not None:
                            await message.edit(
                                embed=build_survey_embed(cancelled),
                                attachments=[],
                                files=[build_survey_file(cancelled)],
                                view=disabled_survey_view(cancelled),
                                allowed_mentions=no_broad_mentions(),
                            )
                    except Exception:
                        logger.exception(
                            "survey_launch_failed_message_disable_failed survey_id=%s",
                            snapshot.survey_id,
                        )
                await send_ephemeral(
                    interaction,
                    "Survey not created: the Discord survey post could not be sent, "
                    "and the SQL record was cancelled.",
                )
                return False
            await send_ephemeral(
                interaction,
                f"Survey #{snapshot.survey_id} created in {target_channel.mention}.",
            )
            return True

        async def _expire_survey_builder(expired_view: SurveyBuilderView) -> None:
            await ctx.interaction.edit_original_response(
                content=expired_view.expired_content(),
                view=expired_view,
            )

        view = SurveyBuilderView(
            owner_user_id=int(ctx.user.id),
            publish_callback=_publish_survey,
            timeout_edit_callback=_expire_survey_builder,
        )
        await ctx.interaction.edit_original_response(
            content=f"Survey builder opened.\n\n{view.summary()}",
            view=view,
        )

    # architecture-check: allow - "update" is the public command verb, not embedded SQL.
    @group.command(name="survey_update", description="Change safe fields for an open survey.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def survey_update(
        ctx: discord.ApplicationContext,
        survey: str = discord.Option(
            str,
            # architecture-check: allow - Discord option copy, not embedded SQL.
            "Survey to update",
            autocomplete=_survey_autocomplete,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            survey_id = _parse_survey_id(survey)
        except ValueError:
            await ctx.interaction.edit_original_response(content="Choose a valid survey.")
            return
        snapshot = await get_survey_snapshot(survey_id)
        if snapshot is None:
            await ctx.interaction.edit_original_response(content="Survey was not found.")
            return
        if snapshot.status != "Open":
            await ctx.interaction.edit_original_response(
                content="Survey not updated: survey is already closed."
            )
            return
        await _send_survey_update_panel(ctx, snapshot)

    @group.command(name="survey_close", description="Close a survey early and disable its button.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def survey_close(
        ctx: discord.ApplicationContext,
        survey: str = discord.Option(
            str,
            "Survey to close",
            autocomplete=_survey_autocomplete,
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
            survey_id = _parse_survey_id(survey)
            result, snapshot = await close_survey(
                survey_id=survey_id,
                actor_discord_user_id=int(ctx.user.id),
                reason=reason,
            )
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Survey not closed: {exc}")
            return
        if snapshot is None or not result.closed:
            await ctx.interaction.edit_original_response(content=result.message)
            return
        channel = bot.get_channel(snapshot.channel_id) or await bot.fetch_channel(
            snapshot.channel_id
        )
        message = await channel.fetch_message(snapshot.message_id) if snapshot.message_id else None
        if message is not None:
            await message.edit(
                embed=build_survey_embed(snapshot),
                attachments=[],
                files=[build_survey_file(snapshot)],
                view=disabled_survey_view(snapshot),
                allowed_mentions=no_broad_mentions(),
            )
        await channel.send(
            content=mention_content(snapshot.close_mention_everyone, "Survey closed"),
            embed=build_survey_close_embed(snapshot),
            allowed_mentions=configured_everyone_mentions(snapshot.close_mention_everyone),
        )
        await ctx.interaction.edit_original_response(content=f"Survey #{survey_id} closed.")

    @group.command(name="survey_status", description="Show survey status and private live totals.")
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def survey_status(
        ctx: discord.ApplicationContext,
        survey: str = discord.Option(
            str,
            "Survey to inspect",
            autocomplete=_survey_autocomplete,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            survey_id = _parse_survey_id(survey)
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Survey not found: {exc}")
            return
        snapshot = await get_survey_snapshot(survey_id)
        if snapshot is None:
            await ctx.interaction.edit_original_response(content="Survey not found.")
            return
        reminder_lines = [
            f"{r.offset_minutes_before_close}m: {'sent' if r.sent_at_utc else 'pending'}"
            for r in snapshot.reminders
        ] or ["No reminders configured"]
        question_lines = []
        for question in snapshot.questions:
            total_responses = int(snapshot.total_responses)
            raw_answered = (
                int(question.answered_response_count)
                if question.answered_response_count is not None
                else total_responses
            )
            answered = max(0, min(raw_answered, total_responses))
            skipped = max(0, total_responses - answered)
            requirement = "required" if question.is_required else "optional"
            if question.question_type == SURVEY_QUESTION_TEXT:
                question_lines.append(
                    f"Q{question.sort_order}: private text responses ({answered} answered, {skipped} skipped, {requirement})"
                )
                continue
            if question.question_type == SURVEY_QUESTION_RATING:
                if answered and question.rating_average is not None:
                    rating_summary = (
                        f"avg {question.rating_average:.1f} on {rating_scale_text(question)}, "
                        f"min {question.rating_min or '-'}, max {question.rating_max or '-'}, "
                        f"{rating_distribution_text(question)}"
                    )
                else:
                    rating_summary = "no ratings"
                question_lines.append(
                    f"Q{question.sort_order}: {rating_summary} ({answered} answered, {skipped} skipped, {requirement})"
                )
                continue
            if question.question_type == SURVEY_QUESTION_RANKING:
                ranked_options = [
                    option for option in question.options if option.ranking_average is not None
                ]
                if answered and ranked_options:
                    best_average = min(
                        float(option.ranking_average or 99) for option in ranked_options
                    )
                    average_leaders = [
                        option_display_label(option.label, option.emoji)
                        for option in ranked_options
                        if option.ranking_average is not None
                        and abs(float(option.ranking_average) - best_average) < 0.0001
                    ]
                    first_place_top = max(
                        int(option.ranking_first_place_count or 0) for option in ranked_options
                    )
                    first_place_leaders = [
                        option_display_label(option.label, option.emoji)
                        for option in ranked_options
                        if int(option.ranking_first_place_count or 0) == first_place_top
                    ]
                    distribution = "; ".join(
                        f"{option_display_label(option.label, option.emoji)}: "
                        f"avg {option.ranking_average:.1f}, first "
                        f"{option.ranking_first_place_count}, "
                        + " ".join(
                            f"{rank}:{ranking_count_for_value(option, rank)}"
                            for rank in range(1, len(question.options) + 1)
                        )
                        for option in ranked_options[:3]
                    )
                    ranking_summary = (
                        f"best avg {', '.join(average_leaders[:2])} ({best_average:.1f}); "
                        f"most first-place {', '.join(first_place_leaders[:2])} ({first_place_top}); "
                        f"{distribution}"
                    )
                else:
                    ranking_summary = "no rankings"
                question_lines.append(
                    f"Q{question.sort_order}: {ranking_summary} ({answered} answered, {skipped} skipped, {requirement})"
                )
                continue
            top = max((option.response_count for option in question.options), default=0)
            leaders = [
                option_display_label(option.label, option.emoji)
                for option in question.options
                if option.response_count == top
            ]
            question_lines.append(
                f"Q{question.sort_order}: {', '.join(leaders[:2]) if top else 'no responses'} ({top}; {answered} answered, {skipped} skipped, {requirement})"
            )
        embed = discord.Embed(
            title=f"Survey #{snapshot.survey_id}: {snapshot.title}",
            color=discord.Color.green() if snapshot.status == "Open" else discord.Color.red(),
        )
        embed.add_field(name="Status", value=snapshot.status, inline=True)
        embed.add_field(name="Responses", value=str(snapshot.total_responses), inline=True)
        embed.add_field(name="Questions", value=str(len(snapshot.questions)), inline=True)
        embed.add_field(
            name="Result visibility",
            value=result_visibility_label(snapshot.result_visibility),
            inline=True,
        )
        embed.add_field(
            name="Closes",
            value=snapshot.closes_at_utc.strftime("%Y-%m-%d %H:%M UTC"),
            inline=True,
        )
        embed.add_field(
            name="Private live totals", value="\n".join(question_lines)[:1024], inline=False
        )
        embed.add_field(name="Reminders", value="\n".join(reminder_lines), inline=False)
        if snapshot.message_id:
            embed.add_field(
                name="Message",
                value=f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}",
                inline=False,
            )
        await ctx.interaction.edit_original_response(embed=embed)

    @group.command(
        name="survey_export", description="Export closed survey totals or response detail."
    )
    @versioned("v1.00")
    @safe_command
    @is_admin_or_leadership_only()
    @track_usage()
    async def survey_export(
        ctx: discord.ApplicationContext,
        survey: str = discord.Option(
            str,
            "Closed survey to export",
            autocomplete=_closed_survey_autocomplete,
        ),
        mode: str = discord.Option(
            str,
            "Export type",
            choices=_SURVEY_EXPORT_MODE_CHOICES,
            required=False,
            default=_SURVEY_EXPORT_MODE_TOTALS,
        ),
    ) -> None:
        await safe_defer(ctx, ephemeral=True)
        try:
            survey_id = _parse_survey_id(survey)
            export_mode = str(mode or _SURVEY_EXPORT_MODE_TOTALS).strip().casefold()
            if export_mode == _SURVEY_EXPORT_MODE_TOTALS:
                export = await build_survey_totals_export(
                    survey_id=survey_id,
                    requested_by_discord_user_id=int(ctx.user.id),
                )
                summary_embed = _build_survey_totals_export_summary_embed(export)
                generated_message = f"Survey #{export.snapshot.survey_id} totals export generated."
            elif export_mode == _SURVEY_EXPORT_MODE_RESPONSE_DETAIL:
                export = await build_survey_response_detail_export(
                    survey_id=survey_id,
                    requested_by_discord_user_id=int(ctx.user.id),
                    discord_name_resolver=lambda ids: _resolve_voter_discord_names(ctx, ids),
                )
                summary_embed = _build_survey_response_detail_export_summary_embed(export)
                generated_message = (
                    f"Survey #{export.snapshot.survey_id} response detail export generated."
                )
            elif export_mode == _SURVEY_EXPORT_MODE_REPORT_BUNDLE:
                export = await build_survey_report_bundle_export(
                    survey_id=survey_id,
                    requested_by_discord_user_id=int(ctx.user.id),
                    discord_name_resolver=lambda ids: _resolve_voter_discord_names(ctx, ids),
                )
                summary_embed = _build_survey_report_bundle_export_summary_embed(export)
                generated_message = f"Survey #{export.snapshot.survey_id} report bundle generated."
            else:
                raise VoteValidationError("Choose a valid export type.")
        except VoteValidationError as exc:
            await ctx.interaction.edit_original_response(content=f"Survey not exported: {exc}")
            return
        except Exception:
            logger.exception("survey_admin_export_failed survey=%r", survey)
            await ctx.interaction.edit_original_response(
                content="Survey export failed. Please try again."
            )
            return

        if export.is_oversized():
            oversized_files = getattr(export, "oversized_filenames", lambda: ())()
            file_detail = (
                " Oversized file(s): " + ", ".join(oversized_files) + "." if oversized_files else ""
            )
            await ctx.interaction.edit_original_response(
                content=(
                    "Survey export was built but is too large for Discord upload. "
                    "Ask an operator for a direct SQL export."
                    f"{file_detail}"
                )
            )
            return

        if export_mode == _SURVEY_EXPORT_MODE_REPORT_BUNDLE:
            files = [discord.File(file.csv_bytes, filename=file.filename) for file in export.files]
            await ctx.followup.send(embed=summary_embed, files=files, ephemeral=True)
        else:
            file = discord.File(export.csv_bytes, filename=export.filename)
            await ctx.followup.send(embed=summary_embed, file=file, ephemeral=True)
        await ctx.interaction.edit_original_response(content=generated_message)

    bot.add_application_command(group)
