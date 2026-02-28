from __future__ import annotations

import logging
from typing import Any

import discord

from ark.dal.ark_dal import (
    get_match,
    get_roster,
    insert_audit_log,
    mark_checked_in,
    mark_emergency_withdraw,
    update_match_confirmation_message,
)
from ark.embeds import build_ark_confirmation_embed_from_match, resolve_ark_match_datetime
from ark.registration_flow import ArkRegistrationController
from ark.registration_messages import upsert_confirmation_message
from ark.state.ark_state import ArkJsonState, ArkMessageState
from ui.views.ark_views import ArkConfirmationView, ArkGovernorSelectView
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)


def _response_is_done(interaction: discord.Interaction) -> bool:
    try:
        return interaction.response.is_done()
    except Exception:
        return False


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
        embed = build_ark_confirmation_embed_from_match(
            match,
            players_cap=int(self.config["PlayersCap"]),
            subs_cap=int(self.config["SubsCap"]),
            roster=roster,
            updates=updates,
        )
        view = ArkConfirmationView(
            match_id=int(match["MatchId"]),
            match_name=f"Ark Match — {(match.get('Alliance') or '').strip()}",
            match_datetime_utc=match_dt,
            on_check_in=self.check_in,
            on_emergency_withdraw=self.emergency_withdraw,
            show_check_in=show_check_in,
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
        embed, view = await self.build_payload(
            match,
            roster=roster,
            updates=updates,
            show_check_in=show_check_in,
        )
        state = ArkJsonState()
        await state.load_async()
        moved, changed = await upsert_confirmation_message(
            client=client,
            state=state,
            match_id=self.match_id,
            embed=embed,
            view=view,
            target_channel_id=target_channel_id,
        )
        if changed:
            msg_state = state.messages.get(self.match_id)
            if msg_state and msg_state.confirmation:
                await update_match_confirmation_message(
                    self.match_id,
                    msg_state.confirmation.channel_id,
                    msg_state.confirmation.message_id,
                )
            await state.save_async()
        return changed

    async def check_in(self, interaction: discord.Interaction) -> None:
        match = await get_match(self.match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
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

    async def emergency_withdraw(self, interaction: discord.Interaction) -> None:
        match = await get_match(self.match_id)
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
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

        # Refresh roster for promotion
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
