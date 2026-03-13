"""MGE signup modal flow (2-step UX, Discord max 5 inputs compliant)."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import discord

from core.interaction_safety import send_ephemeral
from mge import mge_dm_followup, mge_signup_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MgeSignupModalPayload:
    event_id: int
    governor_id: int
    governor_name: str
    actor_role_ids: set[int]
    admin_role_ids: set[int]
    signup_id: int | None = None


@dataclass(slots=True)
class _PrimaryFormData:
    request_priority: str
    preferred_rank_band: str | None
    requested_commander_id: int
    current_heads: int


class MgeSignupPrimaryModal(discord.ui.Modal):
    """Step 1 modal: required and core fields."""

    def __init__(
        self,
        *,
        payload: MgeSignupModalPayload,
        commander_options: dict[int, str],
        title: str = "MGE Signup — Step 1/2",
    ) -> None:
        super().__init__(title=title, timeout=300)
        self.payload = payload
        self.commander_options = commander_options

        self.priority = discord.ui.InputText(
            label="Priority (High/Medium/Low)",
            placeholder="High",
            required=True,
            max_length=10,
        )
        self.rank_band = discord.ui.InputText(
            label="Preferred Rank Band (optional)",
            placeholder="1-5 / 6-10 / 11-15 / no_preference",
            required=False,
            max_length=20,
        )
        self.commander_id = discord.ui.InputText(
            label="Requested Commander ID",
            placeholder="Enter commander ID from list",
            required=True,
            max_length=10,
        )
        self.current_heads = discord.ui.InputText(
            label="Current Heads (0-680)",
            placeholder="0",
            required=True,
            max_length=4,
        )

        self.add_item(self.priority)
        self.add_item(self.rank_band)
        self.add_item(self.commander_id)
        self.add_item(self.current_heads)

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            try:
                requested_commander_id = int(str(self.commander_id.value).strip())
            except ValueError:
                await interaction.response.send_message(
                    "❌ Commander ID must be a valid integer from the allowed list.",
                    ephemeral=True,
                )
                return

            if requested_commander_id not in self.commander_options:
                await interaction.response.send_message(
                    "❌ Commander ID is not valid for this event variant.",
                    ephemeral=True,
                )
                return

            try:
                heads = int(str(self.current_heads.value).strip())
            except ValueError:
                await interaction.response.send_message(
                    "❌ Current heads must be a valid integer.",
                    ephemeral=True,
                )
                return

            primary = _PrimaryFormData(
                request_priority=str(self.priority.value),
                preferred_rank_band=str(self.rank_band.value or "").strip() or None,
                requested_commander_id=requested_commander_id,
                current_heads=heads,
            )

            # Present step-2 optional modal for best UX.
            await interaction.response.send_modal(
                MgeSignupOptionalModal(
                    payload=self.payload,
                    commander_options=self.commander_options,
                    primary=primary,
                    title="MGE Signup — Step 2/2 (Optional Details)",
                )
            )
        except Exception:
            logger.exception(
                "mge_signup_primary_modal_submit_failed event_id=%s", self.payload.event_id
            )
            await interaction.response.send_message(
                "❌ Failed to process signup step 1.",
                ephemeral=True,
            )


class MgeSignupOptionalModal(discord.ui.Modal):
    """Step 2 modal: optional fields only."""

    def __init__(
        self,
        *,
        payload: MgeSignupModalPayload,
        commander_options: dict[int, str],
        primary: _PrimaryFormData,
        title: str = "MGE Signup — Step 2/2",
    ) -> None:
        super().__init__(title=title, timeout=300)
        self.payload = payload
        self.commander_options = commander_options
        self.primary = primary

        self.kingdom_role = discord.ui.InputText(
            label="Kingdom Role (optional)",
            required=False,
            max_length=100,
        )
        self.gear_text = discord.ui.InputText(
            label="Gear Text (optional)",
            required=False,
            max_length=1000,
            style=discord.InputTextStyle.long,
        )
        self.armament_text = discord.ui.InputText(
            label="Armament Text (optional)",
            required=False,
            max_length=1000,
            style=discord.InputTextStyle.long,
        )

        self.add_item(self.kingdom_role)
        self.add_item(self.gear_text)
        self.add_item(self.armament_text)

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            kingdom_role = str(self.kingdom_role.value or "").strip() or None
            gear_text = str(self.gear_text.value or "").strip() or None
            armament_text = str(self.armament_text.value or "").strip() or None

            if self.payload.signup_id is None:
                result = mge_signup_service.create_signup(
                    event_id=self.payload.event_id,
                    actor_discord_id=interaction.user.id,
                    actor_role_ids=self.payload.actor_role_ids,
                    admin_role_ids=self.payload.admin_role_ids,
                    governor_id=self.payload.governor_id,
                    governor_name_snapshot=self.payload.governor_name,
                    request_priority=self.primary.request_priority,
                    preferred_rank_band=self.primary.preferred_rank_band,
                    requested_commander_id=self.primary.requested_commander_id,
                    current_heads=self.primary.current_heads,
                    kingdom_role=kingdom_role,
                    gear_text=gear_text,
                    armament_text=armament_text,
                )
            else:
                result = mge_signup_service.edit_signup(
                    signup_id=self.payload.signup_id,
                    event_id=self.payload.event_id,
                    actor_discord_id=interaction.user.id,
                    actor_role_ids=self.payload.actor_role_ids,
                    admin_role_ids=self.payload.admin_role_ids,
                    existing_governor_id=self.payload.governor_id,
                    request_priority=self.primary.request_priority,
                    preferred_rank_band=self.primary.preferred_rank_band,
                    requested_commander_id=self.primary.requested_commander_id,
                    current_heads=self.primary.current_heads,
                    kingdom_role=kingdom_role,
                    gear_text=gear_text,
                    armament_text=armament_text,
                )

            await interaction.response.send_message(
                "✅ " + result.message if result.success else "❌ " + result.message,
                ephemeral=True,
            )

            if result.success and result.signup_id is not None:
                event = mge_signup_service.get_event_context(self.payload.event_id) or {}
                event_name = str(event.get("EventName") or f"MGE Event {self.payload.event_id}")
                ok, dm_msg = await mge_dm_followup.open_dm_followup(
                    user=interaction.user,
                    event_id=self.payload.event_id,
                    signup_id=int(result.signup_id),
                    event_name=event_name,
                )

                if ok:
                    logger.info(
                        "mge_dm_followup_open_result success=%s event_id=%s signup_id=%s actor_discord_id=%s",
                        ok,
                        self.payload.event_id,
                        int(result.signup_id),
                        interaction.user.id,
                    )
                else:
                    logger.warning(
                        "mge_dm_followup_open_result success=%s event_id=%s signup_id=%s actor_discord_id=%s",
                        ok,
                        self.payload.event_id,
                        int(result.signup_id),
                        interaction.user.id,
                    )
                # send as followup because response already used above
                await interaction.followup.send(dm_msg, ephemeral=True)

        except Exception:
            logger.exception(
                "mge_signup_optional_modal_submit_failed event_id=%s", self.payload.event_id
            )
            await send_ephemeral(
                interaction,
                "❌ Failed to process signup step 2.",
            )


# Backward-compatible alias so existing imports keep working.
MgeSignupModal = MgeSignupPrimaryModal
