from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, time, timedelta
import json
import logging

import discord
from discord.ext import commands as ext_commands

from ark.ark_constants import (
    ARK_MATCH_STATUS_CANCELLED,
    ARK_MATCH_STATUS_COMPLETED,
    ARK_MATCH_STATUSES_OPEN,
)
from ark.ban_utils import (
    compute_ark_end_weekend_date,
    compute_next_ark_weekend_date,
)
from ark.confirmation_flow import ArkConfirmationController
from ark.dal.ark_dal import (
    ArkMatchCreateRequest,
    add_ban,
    amend_match,
    cancel_match,
    clear_match_signups,
    create_match,
    get_alliance,
    get_config,
    get_match,
    get_match_by_alliance_weekend,
    get_reminder_prefs,  # NEW
    get_roster,
    insert_audit_log,
    list_alliances,
    list_bans,
    list_open_matches,
    list_player_report_rows,
    reopen_cancelled_match,
    revoke_ban,
    set_match_result,
    upsert_reminder_prefs,
)
from ark.embeds import (
    build_ark_cancelled_embed_from_match,
    resolve_ark_match_datetime,
)
from ark.registration_flow import ArkRegistrationController
from ark.registration_messages import disable_registration_message
from ark.reminder_prefs import merge_with_defaults  # NEW
from ark.reminders import cancel_match_reminders, reschedule_match_reminders
from ark.state.ark_state import ArkJsonState, ArkMessageRef, ArkMessageState
from bot_config import ARK_SETUP_CHANNEL_ID, GUILD_ID
from core.interaction_safety import safe_command, safe_defer
from decoraters import channel_only, is_admin_or_leadership_only, track_usage
from ui.views.ark_reminder_prefs_view import ArkReminderPrefsView  # NEW
from ui.views.ark_report_view import ArkReportPlayersView
from ui.views.ark_views import AmendArkMatchView, CancelArkMatchView, CreateArkMatchView
from utils import ensure_aware_utc
from versioning import versioned

logger = logging.getLogger(__name__)

_DAY_TO_SHORT = {"Saturday": "Sat", "Sunday": "Sun"}


def _parse_time(val: str) -> time:
    return datetime.strptime(val, "%H:%M").time()


def _compute_weekend_dates(
    anchor_date: date, frequency_weekends: int, count: int = 8
) -> list[date]:
    step = timedelta(days=frequency_weekends * 7)
    today = datetime.now(UTC).date()
    cur = anchor_date
    while cur < today:
        cur += step
    out: list[date] = []
    for _ in range(count):
        out.append(cur)
        cur += step
    return out


def _compute_signup_close(ark_weekend_date: date, close_day: str, close_time_utc: time) -> datetime:
    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    close_idx = day_map.get(close_day.lower())
    if close_idx is None:
        raise ValueError(f"Invalid close day: {close_day}")
    weekend_idx = ark_weekend_date.weekday()
    diff = (weekend_idx - close_idx) % 7
    close_date = ark_weekend_date - timedelta(days=diff)
    return ensure_aware_utc(datetime.combine(close_date, close_time_utc))


def register_ark(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="ark_create_match",
        description="Create an Ark of Osiris match (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_create_match(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)

        config = await get_config()
        if not config:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig is missing or invalid. Contact an admin."
            )
            return

        try:
            allowed_days = json.loads(config.get("AllowedDaysJson") or "[]")
            time_slots = json.loads(config.get("AllowedTimeSlotsJson") or "[]")
        except Exception:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig contains invalid JSON. Contact an admin."
            )
            return

        allowed_times_by_day = {row.get("day"): list(row.get("times") or []) for row in time_slots}
        if not allowed_times_by_day:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig has no allowed time slots configured."
            )
            return

        alliances = await list_alliances(active_only=True)
        alliance_names = [a["Alliance"].strip() for a in alliances if a.get("Alliance")]
        if not alliance_names:
            await ctx.interaction.edit_original_response(
                content="❌ No active alliances configured in ArkAlliances."
            )
            return

        weekend_dates = _compute_weekend_dates(
            anchor_date=config["AnchorWeekendDate"],
            frequency_weekends=int(config["FrequencyWeekends"]),
            count=8,
        )

        async def _on_confirm(interaction: discord.Interaction, sel):
            # Re-validate config + selection
            if (
                not sel.alliance
                or not sel.ark_weekend_date
                or not sel.match_day
                or not sel.match_time_utc
            ):
                await interaction.response.send_message(
                    "❌ Missing selection fields.", ephemeral=True
                )
                return

            alliance_row = await get_alliance(sel.alliance)
            if not alliance_row:
                await interaction.response.send_message(
                    f"❌ Alliance `{sel.alliance}` not found.", ephemeral=True
                )
                return

            reg_channel_id = alliance_row.get("RegistrationChannelId")
            conf_channel_id = alliance_row.get("ConfirmationChannelId")
            if not reg_channel_id or not conf_channel_id:
                await interaction.response.send_message(
                    f"❌ `{sel.alliance}` has no registration or confirmation channel configured.",
                    ephemeral=True,
                )
                return

            # Validate allowed slot
            times_for_day = allowed_times_by_day.get(sel.match_day) or []
            if sel.match_time_utc not in times_for_day:
                await interaction.response.send_message(
                    f"❌ `{sel.match_time_utc}` is not an allowed time for {sel.match_day}.",
                    ephemeral=True,
                )
                return

            # Build datetime values
            match_day_short = _DAY_TO_SHORT.get(sel.match_day, sel.match_day[:3])
            match_time = _parse_time(sel.match_time_utc)

            signup_close = _compute_signup_close(
                sel.ark_weekend_date,
                config["SignupCloseDay"],
                config["SignupCloseTimeUtc"],
            )

            existing_match = await get_match_by_alliance_weekend(
                sel.alliance,
                sel.ark_weekend_date,
            )

            match_id = 0
            reused_cancelled = False
            if existing_match:
                if (existing_match.get("Status") or "").lower() == "cancelled":
                    reopened = await reopen_cancelled_match(
                        match_id=int(existing_match["MatchId"]),
                        match_day=match_day_short,
                        match_time_utc=match_time,
                        signup_close_utc=signup_close,
                        notes=None,
                    )
                    if not reopened:
                        await interaction.response.send_message(
                            "❌ Failed to reopen cancelled match in SQL.",
                            ephemeral=True,
                        )
                        return
                    match_id = int(existing_match["MatchId"])
                    reused_cancelled = True
                else:
                    await interaction.response.send_message(
                        f"❌ A match already exists for `{sel.alliance}` on `{sel.ark_weekend_date}`.",
                        ephemeral=True,
                    )
                    return
            else:
                req = ArkMatchCreateRequest(
                    alliance=sel.alliance,
                    ark_weekend_date=sel.ark_weekend_date,
                    match_day=match_day_short,
                    match_time_utc=match_time,
                    signup_close_utc=signup_close,
                    notes=None,
                    actor_discord_id=interaction.user.id,
                )
                match_id = await create_match(req)
                if not match_id:
                    await interaction.response.send_message(
                        "❌ Failed to create match in SQL.", ephemeral=True
                    )
                    return

            reg_channel = interaction.client.get_channel(int(reg_channel_id))
            if not reg_channel:
                await interaction.response.send_message(
                    f"❌ Cannot access registration channel <#{reg_channel_id}>.",
                    ephemeral=True,
                )
                return

            match_payload = {
                "MatchId": match_id,
                "Alliance": sel.alliance,
                "ArkWeekendDate": sel.ark_weekend_date,
                "MatchDay": match_day_short,
                "MatchTimeUtc": match_time,
                "SignupCloseUtc": signup_close,
                "Notes": None,
            }
            controller = ArkRegistrationController(match_id=match_id, config=config)
            embed, view = await controller.build_payload(match_payload, roster=[])

            msg = await reg_channel.send(embed=embed, view=view)

            from rehydrate_views import save_view_tracker_async, serialize_event

            match_dt = resolve_ark_match_datetime(
                sel.ark_weekend_date,
                sel.match_day,
                match_time,
            )

            await save_view_tracker_async(
                f"arkmatch_{match_id}",
                {
                    "channel_id": msg.channel.id,
                    "message_id": msg.id,
                    "prefix": f"arkmatch_{match_id}",
                    "events": [
                        serialize_event(
                            {
                                "name": f"Ark Match — {sel.alliance}",
                                "start_time": match_dt,
                            }
                        )
                    ],
                    "match_id": match_id,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

            # Persist message ID to JSON state
            state = ArkJsonState()
            await state.load_async()
            state.messages[match_id] = ArkMessageState(
                registration=ArkMessageRef(channel_id=msg.channel.id, message_id=msg.id)
            )
            await state.save_async()

            await insert_audit_log(
                action_type="match_create",
                actor_discord_id=interaction.user.id,
                match_id=match_id,
                governor_id=None,
                details_json={
                    "alliance": sel.alliance,
                    "ark_weekend_date": sel.ark_weekend_date.isoformat(),
                    "match_day": sel.match_day,
                    "match_time_utc": sel.match_time_utc,
                    "signup_close_utc": signup_close.isoformat(),
                    "reused_cancelled": reused_cancelled,
                },
            )

            status_note = " (reopened cancelled match)" if reused_cancelled else ""
            await interaction.response.edit_message(
                content=f"✅ Match created{status_note}: {msg.jump_url}", view=None
            )

        async def _on_cancel(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Cancelled.", view=None)

        view = CreateArkMatchView(
            author_id=ctx.user.id,
            alliances=alliance_names,
            ark_weekend_dates=weekend_dates,
            allowed_days=allowed_days,
            allowed_times_by_day=allowed_times_by_day,
            on_confirm=_on_confirm,
            on_cancel=_on_cancel,
        )

        await ctx.interaction.edit_original_response(
            content=view._selection_summary(),
            view=view,
        )

    @bot.slash_command(
        name="ark_amend_match",
        description="Amend an Ark of Osiris match (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_amend_match(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)

        config = await get_config()
        if not config:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig is missing or invalid. Contact an admin."
            )
            return

        try:
            allowed_days = json.loads(config.get("AllowedDaysJson") or "[]")
            time_slots = json.loads(config.get("AllowedTimeSlotsJson") or "[]")
        except Exception:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig contains invalid JSON. Contact an admin."
            )
            return

        allowed_times_by_day = {row.get("day"): list(row.get("times") or []) for row in time_slots}
        if not allowed_times_by_day:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig has no allowed time slots configured."
            )
            return

        matches = await list_open_matches()
        if not matches:
            await ctx.interaction.edit_original_response(
                content="❌ No open Ark matches found to amend."
            )
            return

        alliances = await list_alliances(active_only=True)
        alliance_names = [a["Alliance"].strip() for a in alliances if a.get("Alliance")]

        roster_tasks = [get_roster(int(m["MatchId"])) for m in matches]
        roster_results = await asyncio.gather(*roster_tasks)
        match_alliance_change_allowed = {
            int(m["MatchId"]): len(roster_results[i]) == 0 for i, m in enumerate(matches)
        }

        notes_templates = None
        try:
            templates_raw = config.get("NotesTemplatesJson")
            if templates_raw:
                notes_templates = json.loads(templates_raw)
        except Exception:
            notes_templates = None

        async def _on_confirm(interaction: discord.Interaction, sel):
            if not sel.match_id or not sel.match_day or not sel.match_time_utc:
                await interaction.response.send_message(
                    "❌ Missing selection fields.", ephemeral=True
                )
                return

            match = await get_match(sel.match_id)
            if not match:
                await interaction.response.send_message("❌ Match not found.", ephemeral=True)
                return

            status = match.get("Status")
            if status in {ARK_MATCH_STATUS_CANCELLED, ARK_MATCH_STATUS_COMPLETED}:
                await interaction.response.send_message(
                    "❌ Match is cancelled or completed and cannot be amended.",
                    ephemeral=True,
                )
                return
            if status not in ARK_MATCH_STATUSES_OPEN:
                await interaction.response.send_message(
                    "❌ Match is not amendable in its current state.",
                    ephemeral=True,
                )
                return

            existing_alliance = (match.get("Alliance") or "").strip()
            new_alliance = (sel.alliance or existing_alliance).strip()

            if new_alliance != existing_alliance:
                roster = await get_roster(sel.match_id)
                if roster:
                    await interaction.response.send_message(
                        "❌ Alliance cannot be changed because signups already exist.",
                        ephemeral=True,
                    )
                    return

            times_for_day = allowed_times_by_day.get(sel.match_day) or []
            if sel.match_time_utc not in times_for_day:
                await interaction.response.send_message(
                    f"❌ `{sel.match_time_utc}` is not an allowed time slot for `{sel.match_day}`.",
                    ephemeral=True,
                )
                return

            match_day_short = _DAY_TO_SHORT.get(sel.match_day, sel.match_day[:3])
            match_time = _parse_time(sel.match_time_utc)

            signup_close = _compute_signup_close(
                match["ArkWeekendDate"],
                config["SignupCloseDay"],
                config["SignupCloseTimeUtc"],
            )

            notes = sel.notes
            if notes is None:
                notes = match.get("Notes")

            updated = await amend_match(
                match_id=sel.match_id,
                alliance=new_alliance,
                match_day=match_day_short,
                match_time_utc=match_time,
                signup_close_utc=signup_close,
                notes=notes,
                actor_discord_id=interaction.user.id,
            )
            if not updated:
                await interaction.response.send_message(
                    "❌ Failed to amend match in SQL.",
                    ephemeral=True,
                )
                return

            match_dt = resolve_ark_match_datetime(
                match["ArkWeekendDate"], sel.match_day, match_time
            )

            updated_match = {
                "Alliance": new_alliance,
                "ArkWeekendDate": match["ArkWeekendDate"],
                "MatchDay": match_day_short,
                "MatchTimeUtc": match_time,
                "SignupCloseUtc": signup_close,
                "Notes": notes,
            }

            roster = await get_roster(sel.match_id)
            updated_match = {
                "MatchId": sel.match_id,
                "Alliance": new_alliance,
                "ArkWeekendDate": match["ArkWeekendDate"],
                "MatchDay": match_day_short,
                "MatchTimeUtc": match_time,
                "SignupCloseUtc": signup_close,
                "Notes": notes,
            }

            controller = ArkRegistrationController(match_id=sel.match_id, config=config)
            embed, view = await controller.build_payload(updated_match, roster=roster)

            state = ArkJsonState()
            await state.load_async()
            msg_state = state.messages.get(sel.match_id)

            if msg_state and msg_state.registration:
                reg_channel = interaction.client.get_channel(msg_state.registration.channel_id)
                if reg_channel:
                    try:
                        msg = await reg_channel.fetch_message(msg_state.registration.message_id)
                        await msg.edit(embed=embed, view=view)
                    except Exception:
                        logger.exception("[ARK] Failed to edit registration embed.")
                else:
                    logger.warning(
                        "[ARK] Registration channel not found for match %s.", sel.match_id
                    )

            await reschedule_match_reminders(
                match_id=sel.match_id,
                match_datetime_utc=match_dt,
                signup_close_utc=signup_close,
            )

            await insert_audit_log(
                action_type="match_amend",
                actor_discord_id=interaction.user.id,
                match_id=sel.match_id,
                governor_id=None,
                details_json={
                    "old": {
                        "alliance": existing_alliance,
                        "match_day": match.get("MatchDay"),
                        "match_time_utc": str(match.get("MatchTimeUtc")),
                        "signup_close_utc": (
                            match.get("SignupCloseUtc").isoformat()
                            if match.get("SignupCloseUtc")
                            else None
                        ),
                        "notes": match.get("Notes"),
                    },
                    "new": {
                        "alliance": new_alliance,
                        "match_day": match_day_short,
                        "match_time_utc": sel.match_time_utc,
                        "signup_close_utc": signup_close.isoformat(),
                        "notes": notes,
                    },
                },
            )

            await interaction.response.edit_message(
                content="✅ Match amended successfully.", view=None
            )

        async def _on_cancel(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Cancelled.", view=None)

        view = AmendArkMatchView(
            author_id=ctx.user.id,
            matches=matches,
            alliances=alliance_names,
            allowed_days=allowed_days,
            allowed_times_by_day=allowed_times_by_day,
            match_alliance_change_allowed=match_alliance_change_allowed,
            notes_templates=notes_templates,
            on_confirm=_on_confirm,
            on_cancel=_on_cancel,
        )

        await ctx.interaction.edit_original_response(
            content="Select a match and the fields to amend:",
            view=view,
        )

    @bot.slash_command(
        name="ark_cancel_match",
        description="Cancel an Ark of Osiris match (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_cancel_match(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)

        config = await get_config()
        if not config:
            await ctx.interaction.edit_original_response(
                content="❌ ArkConfig is missing or invalid. Contact an admin."
            )
            return

        matches = await list_open_matches()
        if not matches:
            await ctx.interaction.edit_original_response(
                content="❌ No open Ark matches found to cancel."
            )
            return

        async def _on_confirm(interaction: discord.Interaction, sel):
            if not sel.match_id:
                await interaction.response.send_message("❌ No match selected.", ephemeral=True)
                return

            match = await get_match(sel.match_id)
            if not match:
                await interaction.response.send_message("❌ Match not found.", ephemeral=True)
                return

            status = match.get("Status")
            if status == ARK_MATCH_STATUS_COMPLETED:
                await interaction.response.send_message(
                    "❌ Match already completed and cannot be cancelled.",
                    ephemeral=True,
                )
                return

            updated = await cancel_match(sel.match_id, interaction.user.id)
            if not updated:
                await interaction.response.send_message(
                    "❌ Failed to cancel match in SQL.",
                    ephemeral=True,
                )
                return

            roster = await get_roster(sel.match_id)

            # TODO: when notify_players is enabled, send notifications here
            # if sel.notify_players:
            #     await notify_cancelled_players(roster, match)

            cleared = await clear_match_signups(sel.match_id, status="Removed")

            cancelled_embed = build_ark_cancelled_embed_from_match(
                match,
                players_cap=int(config["PlayersCap"]),
                subs_cap=int(config["SubsCap"]),
                roster=roster,
            )

            state = ArkJsonState()
            await state.load_async()

            await disable_registration_message(
                client=interaction.client,
                state=state,
                match_id=sel.match_id,
                embed=cancelled_embed,
            )

            await cancel_match_reminders(sel.match_id)

            await insert_audit_log(
                action_type="match_cancel",
                actor_discord_id=interaction.user.id,
                match_id=sel.match_id,
                governor_id=None,
                details_json={
                    "alliance": (match.get("Alliance") or "").strip(),
                    "ark_weekend_date": (
                        match.get("ArkWeekendDate").isoformat()
                        if match.get("ArkWeekendDate")
                        else None
                    ),
                    "notify_players": sel.notify_players,
                    "cleared_signups": cleared,
                },
            )

            await interaction.response.edit_message(
                content="✅ Match cancelled successfully.", view=None
            )

        async def _on_cancel(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Cancelled.", view=None)

        view = CancelArkMatchView(
            author_id=ctx.user.id,
            matches=matches,
            on_confirm=_on_confirm,
            on_cancel=_on_cancel,
            notify_toggle_enabled=False,
        )

        await ctx.interaction.edit_original_response(
            content="Select a match to cancel:",
            view=view,
        )

    @bot.slash_command(
        name="ark_reminder_prefs",
        description="Configure your Ark reminder DM preferences",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.02")
    @safe_command
    @track_usage()
    async def ark_reminder_prefs(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=True)

        row = await get_reminder_prefs(ctx.user.id)
        prefs = merge_with_defaults(row)

        # ensure row exists (defaults enabled)
        await upsert_reminder_prefs(
            ctx.user.id,
            opt_out_all=int(prefs["OptOutAll"]),
            opt_out_24h=int(prefs["OptOut24h"]),
            opt_out_4h=int(prefs["OptOut4h"]),
            opt_out_1h=int(prefs["OptOut1h"]),
            opt_out_start=int(prefs["OptOutStart"]),
            opt_out_checkin_12h=int(prefs["OptOutCheckIn12h"]),
        )

        view = ArkReminderPrefsView(author_id=ctx.user.id)
        content = view._render_text(prefs)
        await ctx.interaction.edit_original_response(content=content, view=view)

    @bot.slash_command(
        name="ark_ban_add",
        description="Add an Ark ban for next N Ark weekends (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_ban_add(
        ctx: discord.ApplicationContext,
        banned_ark_weekends: int = discord.Option(
            int, "Number of Ark weekends to ban", min_value=1, max_value=52
        ),
        discord_user_id: str = discord.Option(
            str, "Discord user id (optional)", required=False, default=""
        ),
        governor_id: str = discord.Option(
            str, "Governor id (optional)", required=False, default=""
        ),
        reason: str = discord.Option(str, "Reason", required=False, default=""),
    ):
        await safe_defer(ctx, ephemeral=True)

        duid = int(discord_user_id) if str(discord_user_id).strip().isdigit() else None
        gid = int(governor_id) if str(governor_id).strip().isdigit() else None
        if not duid and not gid:
            await ctx.followup.send(
                "❌ Provide at least one target: discord_user_id or governor_id.", ephemeral=True
            )
            return

        config = await get_config()
        if not config:
            await ctx.followup.send("❌ ArkConfig missing.", ephemeral=True)
            return

        start_weekend = compute_next_ark_weekend_date(
            anchor_weekend_date=config["AnchorWeekendDate"],
            frequency_weekends=int(config.get("FrequencyWeekends") or 2),
        )
        end_weekend = compute_ark_end_weekend_date(
            start_weekend_date=start_weekend,
            banned_ark_weekends=banned_ark_weekends,
            frequency_weekends=int(config.get("FrequencyWeekends") or 2),
        )

        ban_id = await add_ban(
            discord_user_id=duid,
            governor_id=gid,
            reason=(reason or "").strip() or None,
            banned_ark_weekends=banned_ark_weekends,
            start_ark_weekend_date=start_weekend,
            actor_discord_id=ctx.user.id,  # was created_by_discord_id
        )

        await insert_audit_log(
            action_type="ban_add",
            actor_discord_id=ctx.user.id,
            match_id=None,
            governor_id=gid,
            details_json={
                "ban_id": ban_id,
                "discord_user_id": duid,
                "governor_id": gid,
                "banned_ark_weekends": banned_ark_weekends,
                "start_ark_weekend_date": str(start_weekend),
                "end_ark_weekend_date": str(end_weekend),
                "reason": (reason or "").strip(),
            },
        )

        await ctx.followup.send(
            f"✅ Ban added: applies for the next {banned_ark_weekends} Ark weekend(s), "
            f"starting {start_weekend} (through {end_weekend}).",
            ephemeral=True,
        )

    @bot.slash_command(
        name="ark_ban_revoke",
        description="Revoke an Ark ban by BanId (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_ban_revoke(
        ctx: discord.ApplicationContext,
        ban_id: int = discord.Option(int, "BanId to revoke", min_value=1),
    ):
        await safe_defer(ctx, ephemeral=True)

        ok = await revoke_ban(
            ban_id=ban_id,
            actor_discord_id=ctx.user.id,  # was revoked_by_discord_id
        )
        if not ok:
            await ctx.followup.send("❌ Ban not found or already revoked.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="ban_revoke",
            actor_discord_id=ctx.user.id,
            match_id=None,
            governor_id=None,
            details_json={"ban_id": ban_id},
        )
        await ctx.followup.send(
            "✅ Ban revoked. It will no longer block future signups.", ephemeral=True
        )

    @bot.slash_command(
        name="ark_ban_list",
        description="List Ark bans (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_ban_list(
        ctx: discord.ApplicationContext,
        active_only: bool = discord.Option(bool, "Only active bans", required=False, default=True),
    ):
        await safe_defer(ctx, ephemeral=True)

        rows = await list_bans(active_only=active_only)
        if not rows:
            await ctx.followup.send(
                "ℹ️ No active Ark bans found." if active_only else "ℹ️ No Ark bans found.",
                ephemeral=True,
            )
            return

        lines = []
        for r in rows[:25]:
            lines.append(
                f"BanId `{r.get('BanId')}` | DU `{r.get('DiscordUserId')}` | GOV `{r.get('GovernorId')}` | "
                f"{r.get('StartArkWeekendDate')} → {r.get('EndArkWeekendDate')} | "
                f"N={r.get('BannedArkWeekends')} | Revoked={bool(r.get('RevokedAtUtc'))}"
            )
        await ctx.followup.send("\n".join(lines), ephemeral=True)

    @bot.slash_command(
        name="ark_set_result",
        description="Record Win/Loss for an Ark match (leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership_only()
    @channel_only(ARK_SETUP_CHANNEL_ID, admin_override=True)
    @track_usage()
    async def ark_set_result(
        ctx: discord.ApplicationContext,
        match_id: int = discord.Option(int, "MatchId", min_value=1),
        result: str = discord.Option(str, "Result", choices=["Win", "Loss"]),
        notes: str = discord.Option(str, "Notes (optional)", required=False, default=""),
    ):
        await safe_defer(ctx, ephemeral=True)

        config = await get_config()
        if not config:
            await ctx.followup.send("❌ ArkConfig missing.", ephemeral=True)
            return

        match = await get_match(match_id)
        if not match:
            await ctx.followup.send("❌ Match not found.", ephemeral=True)
            return

        normalized = (result or "").strip().title()
        if normalized not in {"Win", "Loss"}:
            await ctx.followup.send("❌ Result must be Win or Loss.", ephemeral=True)
            return

        ok = await set_match_result(
            match_id=match_id,
            result=normalized,
            notes=(notes or "").strip() or None,
            actor_discord_id=ctx.user.id,
        )
        if not ok:
            await ctx.followup.send("❌ Failed to set result.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="match_result",
            actor_discord_id=ctx.user.id,
            match_id=match_id,
            governor_id=None,
            details_json={"result": normalized, "notes": (notes or "").strip() or None},
        )

        controller = ArkConfirmationController(match_id=match_id, config=config)
        await controller.refresh_confirmation_message(
            client=ctx.interaction.client,
            show_check_in=False,
        )

        await ctx.followup.send("✅ Result recorded.", ephemeral=True)

    @bot.slash_command(
        name="ark_report_players",
        description="Show Ark player report (public)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def ark_report_players(ctx: discord.ApplicationContext):
        await safe_defer(ctx, ephemeral=False)

        rows = await list_player_report_rows()
        if not rows:
            await ctx.followup.send("ℹ️ No report data available.")
            return

        def _format_row(idx: int, row: dict) -> str:
            win_pct = float(row.get("WinPct") or 0) * 100.0
            return (
                f"`{idx:>2}.` {row.get('GovernorName')} (`{row.get('GovernorId')}`) "
                f"• Played: {row.get('MatchesPlayed', 0)} "
                f"• Win%: {win_pct:.1f}% "
                f"• Emergency: {row.get('EmergencyWithdraws', 0)} "
                f"• No Show: {row.get('NoShows', 0)}"
            )

        page_size = 25
        pages: list[discord.Embed] = []

        for page_idx in range(0, len(rows), page_size):
            chunk = rows[page_idx : page_idx + page_size]
            lines = [_format_row(i + 1 + page_idx, row) for i, row in enumerate(chunk)]
            embed = discord.Embed(
                title="Ark Player Report",
                description="\n".join(lines),
                color=discord.Color.blurple(),
            )
            total_pages = (len(rows) + page_size - 1) // page_size
            embed.set_footer(text=f"Page {page_idx // page_size + 1} of {total_pages}")
            pages.append(embed)

        view = ArkReportPlayersView(author_id=ctx.user.id, pages=pages)
        await ctx.interaction.edit_original_response(embed=pages[0], view=view)
