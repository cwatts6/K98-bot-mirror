from __future__ import annotations

from datetime import datetime
import logging
import math
from typing import Any

import discord

from account_picker import build_unique_gov_options
from ark.ark_constants import ARK_MATCH_STATUS_CANCELLED, ARK_MATCH_STATUS_COMPLETED
from ark.dal.ark_dal import (
    add_signup,
    find_active_signup_for_weekend,
    get_match,
    get_roster,
    get_signup,
    insert_audit_log,
    move_signup_slot,
    reactivate_signup,
    remove_signup,
    switch_signup_governor,
)
from ark.embeds import build_ark_registration_embed_from_match, resolve_ark_match_datetime
from ark.registration_messages import upsert_registration_message
from ark.state.ark_state import ArkJsonState
from decoraters import _has_leadership_role, _is_admin
from governor_registry import load_registry
from profile_cache import get_profile_cached
from target_utils import _name_cache, lookup_governor_id
from ui.views.ark_views import (
    ArkAdminAddNameModal,
    ArkAdminSlotSelectView,
    ArkGovernorSelectView,
    ArkRegistrationView,
)
from utils import ensure_aware_utc, utcnow

logger = logging.getLogger(__name__)

_SIGNUP_CLOSED_MESSAGE = "❌ Signups are closed. Contact leadership for changes."


def _is_missing(val: Any) -> bool:
    if val is None:
        return True
    try:
        return math.isnan(float(val))
    except Exception:
        return False


def _get_city_hall_level(governor_id: str) -> float | None:
    rows = (_name_cache or {}).get("rows", []) if isinstance(_name_cache, dict) else []
    for row in rows:
        if str(row.get("GovernorID", "")).strip() == str(governor_id).strip():
            ch = row.get("CityHallLevel")
            if _is_missing(ch):
                return None
            try:
                return float(ch)
            except Exception:
                return None
    return None


def _get_user_accounts(user_id: int) -> dict[str, dict]:
    registry = load_registry() or {}
    user_block = registry.get(str(user_id)) or registry.get(user_id) or {}
    return user_block.get("accounts") or {}


def _get_governor_name(accounts: dict[str, dict], governor_id: str) -> str:
    gid = str(governor_id).strip()
    for info in (accounts or {}).values():
        if str(info.get("GovernorID", "")).strip() == gid:
            return str(info.get("GovernorName") or "Unknown")
    return "Unknown"


def _find_user_signup(roster: list[dict], user_id: int) -> dict[str, Any] | None:
    for entry in roster:
        if int(entry.get("DiscordUserId") or 0) == int(user_id):
            return entry
    return None


def _is_signup_closed(match: dict[str, Any]) -> bool:
    close_dt = ensure_aware_utc(match["SignupCloseUtc"])
    return utcnow() > close_dt


def build_registration_view(
    match_id: int, match_name: str, match_dt: datetime, *, config: dict[str, Any]
) -> ArkRegistrationView:
    controller = ArkRegistrationController(match_id=match_id, config=config)
    return ArkRegistrationView(
        match_id=match_id,
        match_name=match_name,
        match_datetime_utc=match_dt,
        on_join_player=controller.join_player,
        on_join_sub=controller.join_sub,
        on_leave=controller.leave,
        on_switch=controller.switch,
        on_admin_add=controller.admin_add,
        on_admin_remove=controller.admin_remove,
        on_admin_move=controller.admin_move,
        timeout=None,
    )


class ArkRegistrationController:
    def __init__(self, *, match_id: int, config: dict[str, Any]) -> None:
        self.match_id = int(match_id)
        self.config = config

    @staticmethod
    def _response_is_done(interaction: discord.Interaction) -> bool:
        responder = getattr(interaction, "response", None)
        try:
            return bool(responder and hasattr(responder, "is_done") and responder.is_done())
        except Exception:
            return False

    async def build_payload(
        self, match: dict[str, Any], roster: list[dict[str, Any]]
    ) -> tuple[discord.Embed, ArkRegistrationView]:
        match_dt = resolve_ark_match_datetime(
            match["ArkWeekendDate"],
            match["MatchDay"],
            match["MatchTimeUtc"],
        )
        embed = build_ark_registration_embed_from_match(
            match,
            players_cap=int(self.config["PlayersCap"]),
            subs_cap=int(self.config["SubsCap"]),
            roster=roster,
        )
        view = ArkRegistrationView(
            match_id=self.match_id,
            match_name=f"Ark Match — {match.get('Alliance')}",
            match_datetime_utc=match_dt,
            on_join_player=self.join_player,
            on_join_sub=self.join_sub,
            on_leave=self.leave,
            on_switch=self.switch,
            on_admin_add=self.admin_add,
            on_admin_remove=self.admin_remove,
            on_admin_move=self.admin_move,
            timeout=None,
        )
        return embed, view

    async def refresh_registration_message(self, client) -> None:
        match = await get_match(self.match_id)
        if not match:
            return
        roster = await get_roster(self.match_id)
        embed, view = await self.build_payload(match, roster)

        state = ArkJsonState()
        await state.load_async()
        _, state_changed = await upsert_registration_message(
            client=client,
            state=state,
            match_id=self.match_id,
            embed=embed,
            view=view,
            target_channel_id=None,
            delete_old=False,
        )
        if state_changed:
            await state.save_async()

    async def _prompt_governor_selection(
        self,
        interaction: discord.Interaction,
        *,
        accounts: dict[str, dict],
        on_select,
        heading: str,
        only_governor_ids: set[str] | None = None,
    ) -> None:
        options = build_unique_gov_options(accounts)

        if only_governor_ids is not None:
            options = [o for o in options if str(o.value) in only_governor_ids]

        if not options:
            if self._response_is_done(interaction):
                await interaction.followup.send(
                    "❌ You don’t have any registered governors. Use `/register_governor` first.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ You don’t have any registered governors. Use `/register_governor` first.",
                    ephemeral=True,
                )
            return

        if len(options) == 1:
            await on_select(interaction, options[0].value)
            return

        view = ArkGovernorSelectView(
            author_id=interaction.user.id,
            options=options,
            on_select=on_select,
        )

        if self._response_is_done(interaction):
            await interaction.followup.send(heading, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(heading, view=view, ephemeral=True)

    async def _validate_governor(
        self,
        interaction: discord.Interaction,
        governor_id: str,
    ) -> bool:
        # TODO(Phase 8): ban checks (discord/governor)
        gov = get_profile_cached(governor_id)
        if not gov:
            if self._response_is_done(interaction):
                await interaction.followup.send(
                    "❌ Governor not found in registry.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ Governor not found in registry.",
                    ephemeral=True,
                )
            return False

        ch_level = (gov or {}).get("CityHallLevel") or 0
        if int(ch_level) < 16:
            if self._response_is_done(interaction):
                await interaction.followup.send(
                    "❌ Governor must be CH16 or higher to sign up.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ Governor must be CH16 or higher to sign up.",
                    ephemeral=True,
                )
            return False

        return True

    async def _ensure_open_match(self, interaction: discord.Interaction) -> dict[str, Any] | None:
        match = await get_match(self.match_id)
        if not match:
            await interaction.followup.send("❌ Match not found.", ephemeral=True)
            return None
        if match.get("Status") in {ARK_MATCH_STATUS_CANCELLED, ARK_MATCH_STATUS_COMPLETED}:
            await interaction.followup.send("❌ This match is no longer open.", ephemeral=True)
            return None
        if _is_signup_closed(match):
            await interaction.followup.send(_SIGNUP_CLOSED_MESSAGE, ephemeral=True)
            return None
        return match

    async def join_player(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        match = await self._ensure_open_match(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        players = [r for r in roster if (r.get("SlotType") or "").lower() == "player"]

        if len(players) >= int(self.config["PlayersCap"]):
            await interaction.followup.send("❌ Player slots are full.", ephemeral=True)
            return

        # NOTE: Removed user-level block. Governor-level duplicate check happens in _apply_join.

        accounts = _get_user_accounts(interaction.user.id)

        async def _apply(inter: discord.Interaction, governor_id: str) -> None:
            await self._apply_join(inter, match, roster, accounts, governor_id, slot_type="Player")

        await self._prompt_governor_selection(
            interaction,
            accounts=accounts,
            on_select=_apply,
            heading="Select a governor to join as **Player**:",
        )

    async def join_sub(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        match = await self._ensure_open_match(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        players = [r for r in roster if (r.get("SlotType") or "").lower() == "player"]
        subs = [r for r in roster if (r.get("SlotType") or "").lower() == "sub"]

        if len(players) < int(self.config["PlayersCap"]):
            await interaction.followup.send(
                "❌ Sub slots are only available once player slots are full.",
                ephemeral=True,
            )
            return

        if len(subs) >= int(self.config["SubsCap"]):
            await interaction.followup.send("❌ Sub slots are full.", ephemeral=True)
            return

        accounts = _get_user_accounts(interaction.user.id)

        async def _apply(inter: discord.Interaction, governor_id: str) -> None:
            await self._apply_join(inter, match, roster, accounts, governor_id, slot_type="Sub")

        await self._prompt_governor_selection(
            interaction,
            accounts=accounts,
            on_select=_apply,
            heading="Select a governor to join as **Sub**:",
        )

    async def _apply_join(
        self,
        interaction: discord.Interaction,
        match: dict[str, Any],
        roster: list[dict[str, Any]],
        accounts: dict[str, dict],
        governor_id: str,
        *,
        slot_type: str,
    ) -> None:

        async def _send_ephemeral(message: str) -> None:
            if self._response_is_done(interaction):
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)

        if any(str(r.get("GovernorId")) == str(governor_id) for r in roster):
            await _send_ephemeral("❌ That governor is already signed up for this match.")
            return

        conflict = await find_active_signup_for_weekend(
            int(governor_id),
            match["ArkWeekendDate"],
            exclude_match_id=self.match_id,
        )
        if conflict:
            await _send_ephemeral(
                "❌ That governor is already signed up for another match this Ark weekend."
            )
            return

        if not await self._validate_governor(interaction, governor_id):
            return

        gov_name = _get_governor_name(accounts, governor_id)
        existing = await get_signup(self.match_id, int(governor_id))
        if existing and (existing.get("Status") or "").lower() != "active":
            ok = await reactivate_signup(
                match_id=self.match_id,
                governor_id=int(governor_id),
                governor_name=gov_name,
                discord_user_id=interaction.user.id,
                slot_type=slot_type,
                source="Self",
            )
            if not ok:
                await _send_ephemeral("❌ Failed to re-activate signup.")
                return
            signup_id = int(existing.get("SignupId") or 0)
        else:
            signup_id = await add_signup(
                match_id=self.match_id,
                governor_id=int(governor_id),
                governor_name=gov_name,
                discord_user_id=interaction.user.id,
                slot_type=slot_type,
                source="Self",
                actor_discord_id=interaction.user.id,
            )
            if not signup_id:
                await _send_ephemeral("❌ Failed to add signup.")
                return

        await insert_audit_log(
            action_type="signup_add",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(governor_id),
            details_json={
                "slot_type": slot_type,
                "source": "Self",
            },
        )

        await self.refresh_registration_message(interaction.client)
        # Success response: replace the selector message and remove the view
        if self._response_is_done(interaction):
            await interaction.edit_original_response(
                content="✅ You’re signed up!",
                view=None,
            )
        else:
            await interaction.response.edit_message(
                content="✅ You’re signed up!",
                view=None,
            )

    async def leave(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        match = await self._ensure_open_match(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        accounts = _get_user_accounts(interaction.user.id)

        account_gov_ids = {
            str(info.get("GovernorID")).strip()
            for info in (accounts or {}).values()
            if info.get("GovernorID") is not None
        }

        # Filter roster to governors linked to this Discord user
        roster_govs = [r for r in roster if str(r.get("GovernorId")).strip() in account_gov_ids]

        if not roster_govs:
            await interaction.followup.send("❌ You are not signed up.", ephemeral=True)
            return

        async def _apply(inter: discord.Interaction, governor_id: str) -> None:
            ok = await remove_signup(
                match_id=self.match_id,
                governor_id=int(governor_id),
                status="Withdrawn",
                actor_discord_id=interaction.user.id,
            )
            if not ok:
                if inter.response.is_done():
                    await inter.followup.send("❌ Failed to withdraw signup.", ephemeral=True)
                else:
                    await inter.response.send_message(
                        "❌ Failed to withdraw signup.", ephemeral=True
                    )
                return

            await insert_audit_log(
                action_type="signup_withdraw",
                actor_discord_id=interaction.user.id,
                match_id=self.match_id,
                governor_id=int(governor_id),
                details_json={"source": "Self"},
            )

            await self.refresh_registration_message(interaction.client)

            if inter.response.is_done():
                await inter.edit_original_response(
                    content="✅ You’ve left the match.",
                    view=None,
                )
            else:
                await inter.response.edit_message(
                    content="✅ You’ve left the match.",
                    view=None,
                )

        await self._prompt_governor_selection(
            interaction,
            accounts=accounts,
            on_select=_apply,
            heading="Select a governor to **leave**:",
            # Only show governors from roster
            only_governor_ids={str(r.get("GovernorId")) for r in roster_govs},
        )

    async def switch(self, interaction: discord.Interaction) -> None:
        async def _close_menu(inter: discord.Interaction, message: str) -> None:
            if inter.response.is_done():
                await inter.edit_original_response(content=message, view=None)
            else:
                await inter.response.edit_message(content=message, view=None)

        await interaction.response.defer(ephemeral=True)
        match = await self._ensure_open_match(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        accounts = _get_user_accounts(interaction.user.id)

        # Governor IDs linked to this Discord user
        account_gov_ids = {
            str(info.get("GovernorID")).strip()
            for info in (accounts or {}).values()
            if info.get("GovernorID") is not None
        }

        # Active signups in this match that belong to this user
        active_govs = {
            str(r.get("GovernorId")).strip()
            for r in roster
            if str(r.get("GovernorId")).strip() in account_gov_ids
        }

        if not active_govs:
            if self._response_is_done(interaction):
                await interaction.followup.send(
                    "❌ You are not signed up yet. Use **Join** first.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "❌ You are not signed up yet. Use **Join** first.",
                    ephemeral=True,
                )
            return

        async def _select_new(inter: discord.Interaction, current_governor_id: str) -> None:
            # Governors eligible to switch *to* (linked to user, not already active)
            eligible_targets = account_gov_ids - {str(current_governor_id).strip()}
            eligible_targets = eligible_targets - active_govs

            if not eligible_targets:
                await _close_menu(
                    inter,
                    "❌ All your linked governors are already active in this match.",
                )
                return

            await _close_menu(
                inter, "✅ Current governor selected. Choose an inactive governor below."
            )

            # Auto-select if only one inactive governor is available
            if len(eligible_targets) == 1:
                only_id = next(iter(eligible_targets))
                await self._apply_switch(
                    inter, match, roster, accounts, current_governor_id, only_id
                )
                return

            async def _apply(inter2: discord.Interaction, new_governor_id: str) -> None:
                await self._apply_switch(
                    inter2, match, roster, accounts, current_governor_id, new_governor_id
                )

            await self._prompt_governor_selection(
                inter,
                accounts=accounts,
                on_select=_apply,
                heading="Select an **inactive** governor to switch to:",
                only_governor_ids=eligible_targets,
            )

        await self._prompt_governor_selection(
            interaction,
            accounts=accounts,
            on_select=_select_new,
            heading="Select the **current** governor to switch off:",
            only_governor_ids=active_govs,
        )

    async def _apply_switch(
        self,
        interaction: discord.Interaction,
        match: dict[str, Any],
        roster: list[dict[str, Any]],
        accounts: dict[str, dict],
        current_governor_id: str,
        governor_id: str,
    ) -> None:
        async def _send_ephemeral(message: str) -> None:
            if self._response_is_done(interaction):
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)

        if str(current_governor_id) == str(governor_id):
            await _send_ephemeral("❌ You’re already signed up with that governor.")
            return

        if any(str(r.get("GovernorId")) == str(governor_id) for r in roster):
            await _send_ephemeral(
                "❌ That governor is already active in this match. Choose a different one."
            )
            return

        conflict = await find_active_signup_for_weekend(
            int(governor_id),
            match["ArkWeekendDate"],
            exclude_match_id=self.match_id,
        )
        if conflict:
            await _send_ephemeral(
                "❌ That governor is already signed up for another match this Ark weekend."
            )
            return

        if not await self._validate_governor(interaction, governor_id):
            return

        gov_name = _get_governor_name(accounts, governor_id)

        current_entry = next(
            (r for r in roster if str(r.get("GovernorId")) == str(current_governor_id)),
            None,
        )
        current_slot_type = (current_entry or {}).get("SlotType") or "Player"

        existing = await get_signup(self.match_id, int(governor_id))
        if existing and (existing.get("Status") or "").lower() != "active":
            ok = await reactivate_signup(
                match_id=self.match_id,
                governor_id=int(governor_id),
                governor_name=gov_name,
                discord_user_id=interaction.user.id,
                slot_type=current_slot_type,
                source="Self",
            )
            if ok:
                await remove_signup(
                    match_id=self.match_id,
                    governor_id=int(current_governor_id),
                    status="Withdrawn",
                    actor_discord_id=interaction.user.id,
                )
        else:
            ok = await switch_signup_governor(
                match_id=self.match_id,
                old_governor_id=int(current_governor_id),
                new_governor_id=int(governor_id),
                new_governor_name=gov_name,
                discord_user_id=interaction.user.id,
            )

        if not ok:
            await _send_ephemeral("❌ Failed to switch governor.")
            return

        await insert_audit_log(
            action_type="signup_switch",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(governor_id),
            details_json={"source": "Self"},
        )

        await self.refresh_registration_message(interaction.client)

        # Close selector
        if self._response_is_done(interaction):
            await interaction.edit_original_response(content="✅ Governor switched.", view=None)
        else:
            await interaction.response.edit_message(content="✅ Governor switched.", view=None)

    def _admin_override_sub_rule(self) -> bool:
        raw = self.config.get("AdminOverrideSubRule", 0) if self.config else 0
        try:
            return bool(int(raw))
        except Exception:
            return bool(raw)

    def _is_admin_or_leadership(self, interaction: discord.Interaction) -> bool:
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        guild = getattr(interaction, "guild", None)
        if not member and guild:
            try:
                member = guild.get_member(interaction.user.id)
            except Exception:
                member = None
        return bool(_is_admin(interaction.user) or _has_leadership_role(member))

    async def _deny_admin_only(self, interaction: discord.Interaction) -> None:
        responder = getattr(interaction, "response", None)
        is_done = False
        try:
            if responder and hasattr(responder, "is_done"):
                is_done = bool(responder.is_done())
        except Exception:
            is_done = False

        if is_done:
            await interaction.followup.send("❌ Admin/Leadership only.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)

    async def _get_match_for_admin(self, interaction: discord.Interaction) -> dict[str, Any] | None:
        match = await get_match(self.match_id)
        if not match:
            await interaction.followup.send("❌ Match not found.", ephemeral=True)
            return None
        if match.get("Status") in {ARK_MATCH_STATUS_CANCELLED, ARK_MATCH_STATUS_COMPLETED}:
            await interaction.followup.send("❌ This match is no longer open.", ephemeral=True)
            return None
        return match

    async def admin_add(self, interaction: discord.Interaction) -> None:
        if not self._is_admin_or_leadership(interaction):
            await self._deny_admin_only(interaction)
            return
        await interaction.response.send_modal(
            ArkAdminAddNameModal(
                author_id=interaction.user.id, on_submit=self._handle_admin_add_name
            )
        )

    async def _handle_admin_add_name(self, interaction: discord.Interaction, raw_name: str) -> None:
        name = (raw_name or "").strip()
        if not name:
            await interaction.response.send_message("❌ Name is required.", ephemeral=True)
            return

        result = await lookup_governor_id(name)
        status = (result or {}).get("status")

        if status == "found":
            data = result.get("data") or {}
            await self._prompt_admin_slot_selection(
                interaction,
                governor_id=str(data.get("GovernorID")),
                governor_name=str(data.get("GovernorName") or "Unknown"),
            )
            return

        if status == "fuzzy_matches":
            matches = result.get("matches") or []
            if not matches:
                await interaction.response.send_message("No matches found.", ephemeral=True)
                return

            id_to_name = {str(m.get("GovernorID")): str(m.get("GovernorName")) for m in matches}
            options = [
                discord.SelectOption(
                    label=f"{m.get('GovernorName')} • {m.get('GovernorID')}"[:100],
                    value=str(m.get("GovernorID")),
                )
                for m in matches[:25]
            ]

            async def _apply(inter: discord.Interaction, governor_id: str) -> None:
                await self._prompt_admin_slot_selection(
                    inter,
                    governor_id=governor_id,
                    governor_name=id_to_name.get(str(governor_id), "Unknown"),
                )

            view = ArkGovernorSelectView(
                author_id=interaction.user.id,
                options=options,
                on_select=_apply,
            )
            if self._response_is_done(interaction):
                await interaction.followup.send(
                    "Multiple matches — pick one:", view=view, ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Multiple matches — pick one:", view=view, ephemeral=True
                )
            return

        await interaction.response.send_message(
            (result or {}).get("message", "No matches found."),
            ephemeral=True,
        )

    async def _prompt_admin_slot_selection(
        self,
        interaction: discord.Interaction,
        *,
        governor_id: str,
        governor_name: str,
    ) -> None:
        async def _apply(inter: discord.Interaction, slot_type: str) -> None:
            await self._apply_admin_add(inter, governor_id, governor_name, slot_type=slot_type)

        view = ArkAdminSlotSelectView(
            author_id=interaction.user.id,
            on_select=_apply,
            player_label="Add as Player",
            sub_label="Add as Sub",
        )
        msg = f"Select slot type for **{governor_name}** (`{governor_id}`):"
        if self._response_is_done(interaction):
            await interaction.followup.send(msg, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(msg, view=view, ephemeral=True)

    async def _apply_admin_add(
        self,
        interaction: discord.Interaction,
        governor_id: str,
        governor_name: str,
        *,
        slot_type: str,
    ) -> None:
        if not self._is_admin_or_leadership(interaction):
            await self._deny_admin_only(interaction)
            return

        match = await self._get_match_for_admin(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        players = [r for r in roster if (r.get("SlotType") or "").lower() == "player"]
        subs = [r for r in roster if (r.get("SlotType") or "").lower() == "sub"]

        if slot_type == "Player" and len(players) >= int(self.config["PlayersCap"]):
            await interaction.response.send_message("❌ Player slots are full.", ephemeral=True)
            return

        if slot_type == "Sub":
            if len(subs) >= int(self.config["SubsCap"]):
                await interaction.response.send_message("❌ Sub slots are full.", ephemeral=True)
                return
            if (
                len(players) < int(self.config["PlayersCap"])
                and not self._admin_override_sub_rule()
            ):
                await interaction.response.send_message(
                    "❌ Sub slots are only available once player slots are full.",
                    ephemeral=True,
                )
                return

        if any(str(r.get("GovernorId")) == str(governor_id) for r in roster):
            await interaction.response.send_message(
                "❌ That governor is already signed up for this match.", ephemeral=True
            )
            return

        conflict = await find_active_signup_for_weekend(
            int(governor_id),
            match["ArkWeekendDate"],
            exclude_match_id=self.match_id,
        )
        if conflict:
            await interaction.response.send_message(
                "❌ That governor is already signed up for another match this Ark weekend.",
                ephemeral=True,
            )
            return

        if not await self._validate_governor(interaction, governor_id):
            return

        existing = await get_signup(self.match_id, int(governor_id))
        if existing and (existing.get("Status") or "").lower() != "active":
            ok = await reactivate_signup(
                match_id=self.match_id,
                governor_id=int(governor_id),
                governor_name=governor_name,
                discord_user_id=existing.get("DiscordUserId"),
                slot_type=slot_type,
                source="Admin",
            )
        else:
            ok = bool(
                await add_signup(
                    match_id=self.match_id,
                    governor_id=int(governor_id),
                    governor_name=governor_name,
                    discord_user_id=None,
                    slot_type=slot_type,
                    source="Admin",
                    actor_discord_id=interaction.user.id,
                )
            )

        if not ok:
            await interaction.response.send_message("❌ Failed to add signup.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="signup_add",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(governor_id),
            details_json={"slot_type": slot_type, "source": "Admin"},
        )

        await self.refresh_registration_message(interaction.client)
        await interaction.response.edit_message(
            content=f"✅ Added **{governor_name}** (`{governor_id}`) as **{slot_type}**.",
            view=None,
        )

    async def admin_remove(self, interaction: discord.Interaction) -> None:
        if not self._is_admin_or_leadership(interaction):
            await self._deny_admin_only(interaction)
            return

        roster = await get_roster(self.match_id)
        if not roster:
            await interaction.response.send_message("❌ No signups to remove.", ephemeral=True)
            return

        options = [
            discord.SelectOption(
                label=f"{r.get('GovernorNameSnapshot')} • {r.get('GovernorId')}"[:100],
                value=str(r.get("GovernorId")),
            )
            for r in roster[:25]
        ]

        async def _apply(inter: discord.Interaction, governor_id: str) -> None:
            await self._apply_admin_remove(inter, governor_id)

        view = ArkGovernorSelectView(
            author_id=interaction.user.id,
            options=options,
            on_select=_apply,
        )
        await interaction.response.send_message(
            "Select a governor to remove:", view=view, ephemeral=True
        )

    async def _apply_admin_remove(self, interaction: discord.Interaction, governor_id: str) -> None:
        match = await self._get_match_for_admin(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        entry = next((r for r in roster if str(r.get("GovernorId")) == str(governor_id)), None)
        if not entry:
            await interaction.response.send_message("❌ Signup not found.", ephemeral=True)
            return

        ok = await remove_signup(
            match_id=self.match_id,
            governor_id=int(governor_id),
            status="Removed",
            actor_discord_id=interaction.user.id,
        )
        if not ok:
            await interaction.response.send_message("❌ Failed to remove signup.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="signup_remove",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(governor_id),
            details_json={"source": "Admin"},
        )

        roster_after = await get_roster(self.match_id)
        if (entry.get("SlotType") or "").lower() == "player":
            await self._maybe_promote_sub(interaction, match, roster_after)

        await self.refresh_registration_message(interaction.client)
        await interaction.response.edit_message(
            content=f"✅ Removed **{entry.get('GovernorNameSnapshot')}** (`{governor_id}`).",
            view=None,
        )

    async def admin_move(self, interaction: discord.Interaction) -> None:
        if not self._is_admin_or_leadership(interaction):
            await self._deny_admin_only(interaction)
            return

        roster = await get_roster(self.match_id)
        if not roster:
            await interaction.response.send_message("❌ No signups to move.", ephemeral=True)
            return

        options = [
            discord.SelectOption(
                label=f"{r.get('GovernorNameSnapshot')} • {r.get('GovernorId')}"[:100],
                value=str(r.get("GovernorId")),
            )
            for r in roster[:25]
        ]

        async def _apply(inter: discord.Interaction, governor_id: str) -> None:
            await self._prompt_admin_move_slot(inter, governor_id)

        view = ArkGovernorSelectView(
            author_id=interaction.user.id,
            options=options,
            on_select=_apply,
        )
        await interaction.response.send_message(
            "Select a governor to move:", view=view, ephemeral=True
        )

    async def _prompt_admin_move_slot(
        self, interaction: discord.Interaction, governor_id: str
    ) -> None:
        async def _apply(inter: discord.Interaction, slot_type: str) -> None:
            await self._apply_admin_move(inter, governor_id, slot_type=slot_type)

        view = ArkAdminSlotSelectView(
            author_id=interaction.user.id,
            on_select=_apply,
            player_label="Move to Player",
            sub_label="Move to Sub",
        )
        await interaction.response.send_message("Select new slot type:", view=view, ephemeral=True)

    async def _apply_admin_move(
        self, interaction: discord.Interaction, governor_id: str, slot_type: str
    ) -> None:
        match = await self._get_match_for_admin(interaction)
        if not match:
            return

        roster = await get_roster(self.match_id)
        entry = next((r for r in roster if str(r.get("GovernorId")) == str(governor_id)), None)
        if not entry:
            await interaction.response.send_message("❌ Governor not found.", ephemeral=True)
            return

        current_slot = entry.get("SlotType")
        if current_slot == slot_type:
            await interaction.response.send_message(
                "❌ Governor is already in that slot.", ephemeral=True
            )
            return

        # Exclude the governor being moved from counts
        filtered = [r for r in roster if str(r.get("GovernorId")) != str(governor_id)]
        players = [r for r in filtered if (r.get("SlotType") or "").lower() == "player"]
        subs = [r for r in filtered if (r.get("SlotType") or "").lower() == "sub"]

        if slot_type == "Player" and len(players) >= int(self.config["PlayersCap"]):
            await interaction.response.send_message("❌ Player slots are full.", ephemeral=True)
            return

        if slot_type == "Sub":
            if len(subs) >= int(self.config["SubsCap"]):
                await interaction.response.send_message("❌ Sub slots are full.", ephemeral=True)
                return
            if (
                len(players) < int(self.config["PlayersCap"])
                and not self._admin_override_sub_rule()
            ):
                await interaction.response.send_message(
                    "❌ Sub slots are only available once player slots are full.",
                    ephemeral=True,
                )
                return

        ok = await move_signup_slot(
            match_id=self.match_id,
            governor_id=int(governor_id),
            slot_type=slot_type,
            actor_discord_id=interaction.user.id,
        )
        if not ok:
            await interaction.response.send_message("❌ Failed to move signup.", ephemeral=True)
            return

        await insert_audit_log(
            action_type="signup_move",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(governor_id),
            details_json={"from": current_slot, "to": slot_type, "source": "Admin"},
        )

        await self.refresh_registration_message(interaction.client)
        await interaction.response.edit_message(
            content=f"✅ Moved **{entry.get('GovernorNameSnapshot')}** to **{slot_type}**.",
            view=None,
        )

    async def _maybe_promote_sub(
        self, interaction: discord.Interaction, match: dict[str, Any], roster: list[dict[str, Any]]
    ) -> None:
        players = [r for r in roster if (r.get("SlotType") or "").lower() == "player"]
        subs = [r for r in roster if (r.get("SlotType") or "").lower() == "sub"]

        if len(players) >= int(self.config["PlayersCap"]) or not subs:
            return

        promoted = subs[0]
        ok = await move_signup_slot(
            match_id=self.match_id,
            governor_id=int(promoted["GovernorId"]),
            slot_type="Player",
            actor_discord_id=interaction.user.id,
        )
        if not ok:
            return

        await insert_audit_log(
            action_type="signup_promote",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=int(promoted["GovernorId"]),
            details_json={"from": "Sub", "to": "Player", "source": "AutoPromotion"},
        )

        await self._send_promotion_dm(interaction, match, promoted)

    async def _send_promotion_dm(
        self, interaction: discord.Interaction, match: dict[str, Any], promoted: dict[str, Any]
    ) -> None:
        user_id = promoted.get("DiscordUserId")
        if not user_id:
            return

        match_dt = resolve_ark_match_datetime(
            match["ArkWeekendDate"],
            match["MatchDay"],
            match["MatchTimeUtc"],
        )
        msg = (
            f"✅ You have been promoted to **Player** for **{match.get('Alliance')}**.\n"
            f"Match time: `{match_dt.strftime('%Y-%m-%d %H:%M UTC')}`"
        )
        try:
            user = interaction.client.get_user(int(user_id))
            if not user:
                user = await interaction.client.fetch_user(int(user_id))
            if user:
                await user.send(msg)
        except Exception:
            logger.exception("[ARK] Failed to DM promoted user %s", user_id)
