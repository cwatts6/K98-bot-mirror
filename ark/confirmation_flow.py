from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import discord

from ark.ark_draft_service import (
    ArkDraftPreconditionError,
    generate_draft_for_match,
)
from ark.dal.ark_dal import (
    get_match,
    get_roster,
    insert_audit_log,
    list_match_team_rows,
    mark_checked_in,
    mark_emergency_withdraw,
    mark_no_show,
    set_match_result,
    update_match_confirmation_message,
)
from ark.embeds import (
    build_ark_cancelled_embed_from_match,
    build_ark_confirmation_embed_from_match,
    build_ark_match_complete_embed_from_match,
    resolve_ark_match_datetime,
)
from ark.registration_flow import ArkRegistrationController
from ark.registration_messages import upsert_confirmation_message
from ark.state.ark_state import ArkJsonState, ArkMessageState
from decoraters import _has_leadership_role, _is_admin
from ui.views.ark_views import (
    ArkConfirmationView,
    ArkGovernorSelectView,
    ArkMatchResultModal,
)
from ui.views.team_builder_views import ArkTeamBuilderView
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)


def _response_is_done(interaction: discord.Interaction) -> bool:
    try:
        return interaction.response.is_done()
    except Exception:
        return False


def _is_admin_or_leadership(interaction: discord.Interaction) -> bool:
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    guild = getattr(interaction, "guild", None)
    if not member and guild:
        try:
            member = guild.get_member(interaction.user.id)
        except Exception:
            member = None
    return bool(_is_admin(interaction.user) or _has_leadership_role(member))


def _post_start_at(match_dt: datetime) -> datetime:
    return ensure_aware_utc(match_dt + timedelta(minutes=30))


def _complete_at(match_dt: datetime) -> datetime:
    return ensure_aware_utc(match_dt + timedelta(hours=1))


class ArkConfirmationController:
    def __init__(self, *, match_id: int, config: dict[str, Any]) -> None:
        self.match_id = match_id
        self.config = config

    async def build_payload(
        self,
        match: dict[str, Any],
        *,
        roster: list[dict[str, Any]] | None = None,
        updates: list[str] | None = None,
        show_check_in: bool = False,
    ):
        match_dt = resolve_ark_match_datetime(
            match["ArkWeekendDate"],
            match["MatchDay"],
            match["MatchTimeUtc"],
        )
        now = ensure_aware_utc(utcnow())
        status = (match.get("Status") or "").lower()
        post_start_at = _post_start_at(match_dt)
        complete_at = _complete_at(match_dt)

        if status == "cancelled":
            embed = build_ark_cancelled_embed_from_match(
                match,
                players_cap=int(self.config["PlayersCap"]),
                subs_cap=int(self.config["SubsCap"]),
                roster=roster,
            )
            return embed, None

        if status == "completed" and now >= complete_at:
            embed = build_ark_match_complete_embed_from_match(
                match,
                players_cap=int(self.config["PlayersCap"]),
                subs_cap=int(self.config["SubsCap"]),
                roster=roster,
                updates=updates,
            )
            return embed, None

        checkin_offset_hours = int(self.config.get("CheckInActivationOffsetHours") or 12)
        checkin_at = ensure_aware_utc(match_dt - timedelta(hours=checkin_offset_hours))

        is_locked = status == "locked"
        before_post_start = now < post_start_at
        before_complete = now < complete_at

        allow_emergency = is_locked and before_complete
        checkin_window_open = now >= checkin_at and before_post_start
        allow_check_in = bool(show_check_in) and is_locked and checkin_window_open

        show_admin_actions = status != "cancelled"
        show_result_actions = (
            now >= post_start_at or status == "completed"
        ) and status != "cancelled"

        # Team assignment buttons are only relevant before the match starts (+30 min buffer).
        # After post_start_at they are hidden — no point assigning teams mid-match.
        show_team_actions = show_admin_actions and before_post_start

        # Check whether final team rows exist — only needed when team actions are shown.
        teams_published = False
        if show_team_actions:
            try:
                all_rows = await list_match_team_rows(
                    match_id=int(match["MatchId"]), draft_only=False
                )
                teams_published = any(int(r.get("IsFinal") or 0) == 1 for r in (all_rows or []))
            except Exception:
                logger.exception(
                    "[ARK_CONFIRM] build_payload failed checking final team rows match_id=%s",
                    match["MatchId"],
                )

        embed = build_ark_confirmation_embed_from_match(
            match,
            players_cap=int(self.config["PlayersCap"]),
            subs_cap=int(self.config["SubsCap"]),
            roster=roster,
            updates=updates,
        )

        # Team assignment help text — only shown when team actions are visible.
        if show_team_actions:
            if teams_published:
                team_help = (
                    "✅ Teams are published. "
                    "Click **Reconfirm Teams** to review or edit assignments."
                )
            else:
                team_help = "Click **Confirm Teams** to assign and publish match teams."
            embed.add_field(name="Team Assignment", value=team_help, inline=False)

        view = ArkConfirmationView(
            match_id=int(match["MatchId"]),
            match_name=f"Ark Match — {(match.get('Alliance') or '').strip()}",
            match_datetime_utc=match_dt,
            on_check_in=self.check_in,
            on_emergency_withdraw=self.emergency_withdraw,
            on_record_result=self.record_result,
            on_no_show=self.no_show,
            on_create_teams=self.create_teams,
            on_reconfirm_teams=self.reconfirm_teams,
            show_check_in=allow_check_in,
            allow_emergency=allow_emergency,
            show_admin_actions=show_team_actions,  # ← drives Confirm/Reconfirm Teams visibility
            show_result_actions=show_result_actions,
            teams_published=teams_published,
            timeout=None,
        )
        return embed, view

    async def refresh_confirmation_message(
        self,
        *,
        client,
        target_channel_id: int | None = None,
        updates: list[str] | None = None,
        show_check_in: bool = False,
    ) -> bool:
        match = await get_match(self.match_id)
        if not match:
            return False
        roster = await get_roster(self.match_id)

        # Load ArkJsonState early so we can merge persisted confirmation_updates
        # with any caller-supplied updates before building the embed.
        state = ArkJsonState()
        await state.load_async()
        msg_state = state.messages.get(self.match_id)
        persisted_updates = (msg_state.confirmation_updates if msg_state else None) or []

        # Merge: caller-supplied updates take precedence; persisted fill in when
        # the caller doesn't provide any (e.g. scheduler-driven refreshes).
        if updates is not None:
            merged_updates = updates
        elif persisted_updates:
            merged_updates = persisted_updates
        else:
            merged_updates = None

        embed, view = await self.build_payload(
            match,
            roster=roster,
            updates=merged_updates,
            show_check_in=show_check_in,
        )

        logger.info(
            "[ARK_CONFIRM] refresh start match_id=%s show_check_in_arg=%s status=%s updates=%s",
            self.match_id,
            bool(show_check_in),
            str(match.get("Status")),
            len(merged_updates) if merged_updates else 0,
        )

        delivered, state_changed = await upsert_confirmation_message(
            client=client,
            state=state,
            match_id=self.match_id,
            embed=embed,
            view=view,
            target_channel_id=target_channel_id,
        )

        logger.info(
            "[ARK_CONFIRM] refresh result match_id=%s delivered=%s state_changed=%s",
            self.match_id,
            delivered,
            state_changed,
        )

        if state_changed:
            msg_state = state.messages.get(self.match_id)
            if msg_state and msg_state.confirmation:
                await update_match_confirmation_message(
                    self.match_id,
                    msg_state.confirmation.channel_id,
                    msg_state.confirmation.message_id,
                )
            await state.save_async()

        return bool(delivered)

    async def check_in(self, interaction: discord.Interaction) -> None:
        match = await get_match(self.match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        match_dt = resolve_ark_match_datetime(
            match["ArkWeekendDate"], match["MatchDay"], match["MatchTimeUtc"]
        )
        if ensure_aware_utc(utcnow()) >= _post_start_at(match_dt):
            await interaction.response.send_message("❌ Check-in is closed.", ephemeral=True)
            return

        roster = await get_roster(self.match_id)
        user_entries = [
            r for r in roster if int(r.get("DiscordUserId") or 0) == int(interaction.user.id)
        ]
        if not user_entries:
            await interaction.response.send_message(
                "❌ You are not signed up for this match.", ephemeral=True
            )
            return

        if len(user_entries) == 1:
            await self._apply_check_in(interaction, match, roster, user_entries[0])
            return

        options = [
            discord.SelectOption(
                label=str(r.get("GovernorNameSnapshot") or "Unknown")[:100],
                value=str(r.get("GovernorId") or r.get("GovernorID") or ""),
            )
            for r in user_entries
        ]

        async def _apply(inter: discord.Interaction, governor_id: str):
            target = next(
                (r for r in user_entries if str(r.get("GovernorId") or "") == governor_id), None
            )
            if not target:
                await inter.response.send_message("❌ Governor not found.", ephemeral=True)
                return
            await self._apply_check_in(inter, match, roster, target)

        view = ArkGovernorSelectView(
            author_id=interaction.user.id, options=options, on_select=_apply, timeout=120.0
        )
        await interaction.response.send_message(
            "Select which governor to check in:", view=view, ephemeral=True
        )

    async def emergency_withdraw(self, interaction: discord.Interaction) -> None:
        match = await get_match(self.match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        match_dt = resolve_ark_match_datetime(
            match["ArkWeekendDate"], match["MatchDay"], match["MatchTimeUtc"]
        )
        if ensure_aware_utc(utcnow()) >= _complete_at(match_dt):
            await interaction.response.send_message(
                "❌ Emergency withdrawals are closed.", ephemeral=True
            )
            return

        roster = await get_roster(self.match_id)
        user_entries = [
            r for r in roster if int(r.get("DiscordUserId") or 0) == int(interaction.user.id)
        ]
        if not user_entries:
            await interaction.response.send_message(
                "❌ You are not signed up for this match.", ephemeral=True
            )
            return

        if len(user_entries) == 1:
            await self._apply_emergency_withdraw(interaction, match, user_entries[0])
            return

        options = [
            discord.SelectOption(
                label=str(r.get("GovernorNameSnapshot") or "Unknown")[:100],
                value=str(r.get("GovernorId") or r.get("GovernorID") or ""),
            )
            for r in user_entries
        ]

        async def _apply(inter: discord.Interaction, governor_id: str):
            target = next(
                (r for r in user_entries if str(r.get("GovernorId") or "") == governor_id), None
            )
            if not target:
                await inter.response.send_message("❌ Governor not found.", ephemeral=True)
                return
            await self._apply_emergency_withdraw(inter, match, target)

        view = ArkGovernorSelectView(
            author_id=interaction.user.id, options=options, on_select=_apply, timeout=120.0
        )
        await interaction.response.send_message(
            "Select which governor to withdraw:", view=view, ephemeral=True
        )

    async def create_teams(self, interaction: discord.Interaction) -> None:
        if not _is_admin_or_leadership(interaction):
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)
            return

        logger.info(
            "[ARK_CONFIRM] create_teams_start match_id=%s actor_discord_id=%s",
            self.match_id,
            interaction.user.id,
        )
        try:
            roster = await get_roster(self.match_id)
            logger.info(
                "[ARK_CONFIRM] create_teams_roster match_id=%s actor_discord_id=%s roster_rows=%s",
                self.match_id,
                interaction.user.id,
                len(roster or []),
            )
            result = await generate_draft_for_match(
                self.match_id,
                actor_discord_id=interaction.user.id,
                source="confirmation_create_teams",
                roster_rows=roster,
            )
            logger.info(
                "[ARK_CONFIRM] create_teams draft_generated match_id=%s actor_discord_id=%s team1=%s team2=%s",
                self.match_id,
                interaction.user.id,
                len(result.team1_ids),
                len(result.team2_ids),
            )
        except ArkDraftPreconditionError as exc:
            logger.info(
                "[ARK_CONFIRM] create_teams draft_skipped match_id=%s actor_discord_id=%s reason=%s",
                self.match_id,
                interaction.user.id,
                str(exc),
            )
        except Exception:
            logger.exception(
                "[ARK_CONFIRM] create_teams draft_generation_failed match_id=%s actor_discord_id=%s",
                self.match_id,
                interaction.user.id,
            )

        await self._open_team_builder(interaction)

    async def reconfirm_teams(self, interaction: discord.Interaction) -> None:
        """
        Open the team builder for a match that already has published (final) teams.

        Does not unpublish or clear final rows — the admin can do that from within
        the team builder using the Unpublish Teams button.
        """
        if not _is_admin_or_leadership(interaction):
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)
            return

        logger.info(
            "[ARK_CONFIRM] reconfirm_teams_start match_id=%s actor_discord_id=%s",
            self.match_id,
            interaction.user.id,
        )

        await self._open_team_builder(interaction)

    async def _open_team_builder(self, interaction: discord.Interaction) -> None:
        """Open (or refresh) the team builder ephemeral message for this match."""
        try:
            logger.info(
                "[ARK_CONFIRM] open_team_builder match_id=%s actor_discord_id=%s",
                self.match_id,
                interaction.user.id,
            )
            await ArkTeamBuilderView.open(
                match_id=self.match_id,
                actor_discord_id=interaction.user.id,
                interaction=interaction,
            )
            logger.info(
                "[ARK_CONFIRM] review_opened match_id=%s actor_discord_id=%s",
                self.match_id,
                interaction.user.id,
            )
        except Exception:
            logger.exception(
                "[ARK_CONFIRM] open_team_builder_failed match_id=%s actor_discord_id=%s",
                self.match_id,
                interaction.user.id,
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Opening the review panel failed. Check logs.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "❌ Opening the review panel failed. Check logs.",
                    ephemeral=True,
                )

    async def record_result(self, interaction: discord.Interaction) -> None:
        if not _is_admin_or_leadership(interaction):
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)
            return

        match = await get_match(self.match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        if (match.get("Status") or "").lower() == "cancelled":
            await interaction.response.send_message("❌ Match is cancelled.", ephemeral=True)
            return

        async def _apply(inter: discord.Interaction, result_value: str, notes: str | None):
            result = (result_value or "").strip().title()
            notes = (notes or "").strip() or None
            if result not in {"Win", "Loss"}:
                await inter.response.send_message("❌ Result must be Win or Loss.", ephemeral=True)
                return

            ok = await set_match_result(
                match_id=self.match_id,
                result=result,
                notes=notes,
                actor_discord_id=inter.user.id,
            )
            if not ok:
                await inter.response.send_message("❌ Failed to set result.", ephemeral=True)
                return

            await insert_audit_log(
                action_type="match_result",
                actor_discord_id=inter.user.id,
                match_id=self.match_id,
                governor_id=None,
                details_json={"result": result, "notes": notes},
            )

            await self.refresh_confirmation_message(
                client=inter.client,
                show_check_in=False,
            )

            await inter.response.send_message("✅ Result recorded.", ephemeral=True)

        modal = ArkMatchResultModal(
            author_id=interaction.user.id,
            current_result=(match.get("Result") or ""),
            current_notes=(match.get("ResultNotes") or ""),
            result_label="Result (Win/Loss) — record No Shows first",
            on_submit=_apply,
        )
        await interaction.response.send_modal(modal)

    async def no_show(self, interaction: discord.Interaction) -> None:
        if not _is_admin_or_leadership(interaction):
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)
            return

        match = await get_match(self.match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        if (match.get("Status") or "").lower() == "cancelled":
            await interaction.response.send_message("❌ Match is cancelled.", ephemeral=True)
            return

        roster = await get_roster(self.match_id)
        eligible = [r for r in roster if not r.get("NoShow")]
        if not eligible:
            await interaction.response.send_message(
                "ℹ️ No eligible players for no-show.", ephemeral=True
            )
            return

        options = [
            discord.SelectOption(
                label=f"{r.get('GovernorNameSnapshot')} • {r.get('GovernorId')}"[:100],
                value=str(r.get("GovernorId")),
            )
            for r in eligible[:25]
        ]

        async def _apply(inter: discord.Interaction, governor_id: str):
            entry = next(
                (r for r in eligible if str(r.get("GovernorId")) == str(governor_id)), None
            )
            if not entry:
                await inter.response.send_message("❌ Governor not found.", ephemeral=True)
                return

            ok = await mark_no_show(
                match_id=self.match_id,
                governor_id=int(governor_id),
                actor_discord_id=inter.user.id,
            )
            if not ok:
                await inter.response.send_message("❌ Failed to mark no-show.", ephemeral=True)
                return

            await insert_audit_log(
                action_type="signup_no_show",
                actor_discord_id=inter.user.id,
                match_id=self.match_id,
                governor_id=int(governor_id),
                details_json={"source": "Admin"},
            )

            update_line = (
                f"No Show: {entry.get('GovernorNameSnapshot')} ({entry.get('GovernorId')})"
            )

            state = ArkJsonState()
            await state.load_async()
            msg_state = state.messages.get(self.match_id)
            if msg_state:
                msg_state.confirmation_updates.append(update_line)
            else:
                msg_state = ArkMessageState(confirmation_updates=[update_line])
                state.messages[self.match_id] = msg_state
            await state.save_async()

            await self.refresh_confirmation_message(
                client=inter.client,
                show_check_in=False,
                updates=msg_state.confirmation_updates,
            )

            await inter.response.send_message("✅ No-show recorded.", ephemeral=True)

        view = ArkGovernorSelectView(
            author_id=interaction.user.id, options=options, on_select=_apply, timeout=120.0
        )
        await interaction.response.send_message(
            "Select a governor to mark as No Show:", view=view, ephemeral=True
        )

    async def _apply_check_in(
        self,
        interaction: discord.Interaction,
        match: dict[str, Any],
        roster: list[dict[str, Any]],
        entry: dict[str, Any],
    ) -> None:
        if entry.get("CheckedIn") or entry.get("CheckedInAtUtc"):
            await interaction.response.send_message(
                "✅ You are already checked in.", ephemeral=True
            )
            return

        ok = await mark_checked_in(
            match_id=self.match_id,
            governor_id=int(entry["GovernorId"]),
            checked_in_at_utc=ensure_aware_utc(utcnow()),
        )
        if not ok:
            await interaction.response.send_message("❌ Failed to check in.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="check_in",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(entry["GovernorId"]),
            details_json={"source": "Self"},
        )

        await self.refresh_confirmation_message(
            client=interaction.client,
            show_check_in=True,
        )

        if _response_is_done(interaction):
            await interaction.followup.send("✅ Check-in recorded.", ephemeral=True)
        else:
            await interaction.response.send_message("✅ Check-in recorded.", ephemeral=True)

    async def _apply_emergency_withdraw(
        self, interaction: discord.Interaction, match: dict[str, Any], entry: dict[str, Any]
    ) -> None:
        ok = await mark_emergency_withdraw(
            match_id=self.match_id,
            governor_id=int(entry["GovernorId"]),
            actor_discord_id=interaction.user.id,
        )
        if not ok:
            await interaction.response.send_message("❌ Failed to withdraw.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="emergency_withdraw",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(entry["GovernorId"]),
            details_json={"source": "Self"},
        )

        roster = await get_roster(self.match_id)
        promoter = ArkRegistrationController(match_id=self.match_id, config=self.config)
        await promoter._maybe_promote_sub(interaction, match, roster)

        update_line = (
            f"Emergency withdraw: {entry.get('GovernorNameSnapshot')} "
            f"({entry.get('GovernorId')})"
        )

        state = ArkJsonState()
        await state.load_async()
        msg_state = state.messages.get(self.match_id)
        if msg_state:
            msg_state.confirmation_updates.append(update_line)
        else:
            msg_state = ArkMessageState(confirmation_updates=[update_line])
            state.messages[self.match_id] = msg_state
        await state.save_async()

        await self.refresh_confirmation_message(
            client=interaction.client,
            show_check_in=True,
            updates=msg_state.confirmation_updates,
        )

        if _response_is_done(interaction):
            await interaction.followup.send("✅ Withdrawal recorded.", ephemeral=True)
        else:
            await interaction.response.send_message("✅ Withdrawal recorded.", ephemeral=True)
