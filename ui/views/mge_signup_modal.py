from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

import discord

from core.interaction_safety import member_role_ids, private_operation, send_ephemeral
from core.operation_outcome import MutationOutcome
from core.owned_work import drain_thread
from mge import mge_dm_followup, mge_signup_service

logger = logging.getLogger(__name__)


def _clamp(value: str | None, max_len: int) -> str:
    s = (value or "").strip()
    return s[:max_len] if len(s) > max_len else s


@dataclass(slots=True)
class MgeSignupModalPayload:
    event_id: int
    governor_id: int
    governor_name: str
    actor_role_ids: set[int]
    admin_role_ids: set[int]
    signup_id: int | None = None
    on_success_refresh: Callable[[int], None] | None = None
    expected_signup: dict | None = None
    owner_discord_id: int | None = None


class MgeSignupFinalModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        payload: MgeSignupModalPayload,
        selected_priority: str,
        selected_rank_band: str | None,
        selected_commander_id: int,
        initial_current_heads: int | None = None,
        initial_kingdom_role: str | None = None,
        initial_gear_text: str | None = None,
        initial_armament_text: str | None = None,
        title: str = "MGE Signup",
    ) -> None:
        super().__init__(title=title, timeout=300)
        self.payload = payload
        self.selected_priority = selected_priority
        self.selected_rank_band = selected_rank_band
        self.selected_commander_id = int(selected_commander_id)

        self.current_heads = discord.ui.InputText(
            # RETIRED_FLOW: current_heads — collected by the old player flow.
            # Retained for admin-add path and legacy signups.  Not used by the
            # simplified v2 player flow (MgeSimplifiedSignupFormView).
            label="Current Heads (0-680)",
            required=True,
            max_length=4,
            value=_clamp(
                str(initial_current_heads) if initial_current_heads is not None else "", 4
            ),
            placeholder="0",
        )

        self.kingdom_role = discord.ui.InputText(
            # RETIRED_FLOW: kingdom_role — retired from live player flow; retained
            # for admin-add path.
            label="Kingdom Role (optional)",
            required=False,
            max_length=100,
            value=_clamp(initial_kingdom_role, 100),
        )

        self.gear_text = discord.ui.InputText(
            # RETIRED_FLOW: gear_text — retired from live player flow; retained
            # for admin-add path.
            label="Gear Text (optional)",
            required=False,
            max_length=1000,
            style=discord.InputTextStyle.long,
            value=_clamp(initial_gear_text, 1000),
        )

        self.armament_text = discord.ui.InputText(
            # RETIRED_FLOW: armament_text — retired from live player flow; retained
            # for admin-add path.
            label="Armament Text (optional)",
            required=False,
            max_length=1000,
            style=discord.InputTextStyle.long,
            value=_clamp(initial_armament_text, 1000),
        )

        self.add_item(self.current_heads)
        self.add_item(self.kingdom_role)
        self.add_item(self.gear_text)
        self.add_item(self.armament_text)

    @private_operation
    async def callback(self, interaction: discord.Interaction) -> None:
        if (
            self.payload.owner_discord_id is not None
            and self.payload.owner_discord_id != interaction.user.id
        ):
            await send_ephemeral(interaction, "This form belongs to another user.")
            return
        if getattr(self, "_submitted", False):
            await send_ephemeral(
                interaction, "This form has already been submitted. Refresh to view its outcome."
            )
            return
        result = None
        try:
            try:
                heads = int(str(self.current_heads.value).strip())
            except ValueError:
                await send_ephemeral(
                    interaction,
                    "❌ Current heads must be a valid integer.",
                    ephemeral=True,
                )
                return

            kingdom_role = str(self.kingdom_role.value or "").strip() or None
            gear_text = str(self.gear_text.value or "").strip() or None
            armament_text = str(self.armament_text.value or "").strip() or None

            if self.payload.signup_id is None:
                result = await drain_thread(
                    mge_signup_service.create_signup,
                    event_id=self.payload.event_id,
                    actor_discord_id=interaction.user.id,
                    actor_role_ids=member_role_ids(interaction),
                    operation_id=str(interaction.id),
                    expected_signup=self.payload.expected_signup,
                    admin_role_ids=self.payload.admin_role_ids,
                    governor_id=self.payload.governor_id,
                    governor_name_snapshot=self.payload.governor_name,
                    request_priority=self.selected_priority,
                    preferred_rank_band=self.selected_rank_band,
                    requested_commander_id=self.selected_commander_id,
                    current_heads=heads,
                    kingdom_role=kingdom_role,
                    gear_text=gear_text,
                    armament_text=armament_text,
                )
            else:
                result = await drain_thread(
                    mge_signup_service.edit_signup,
                    signup_id=self.payload.signup_id,
                    event_id=self.payload.event_id,
                    actor_discord_id=interaction.user.id,
                    actor_role_ids=member_role_ids(interaction),
                    operation_id=str(interaction.id),
                    expected_signup=self.payload.expected_signup,
                    admin_role_ids=self.payload.admin_role_ids,
                    existing_governor_id=self.payload.governor_id,
                    request_priority=self.selected_priority,
                    preferred_rank_band=self.selected_rank_band,
                    requested_commander_id=self.selected_commander_id,
                    current_heads=heads,
                    kingdom_role=kingdom_role,
                    gear_text=gear_text,
                    armament_text=armament_text,
                )

            self._submitted = result.success or result.outcome == MutationOutcome.UNKNOWN
            await send_ephemeral(
                interaction,
                "✅ " + result.message if result.success else "❌ " + result.message,
                ephemeral=True,
            )

            if result.success and self.payload.on_success_refresh is not None:
                try:
                    self.payload.on_success_refresh(int(self.payload.event_id))
                except Exception:
                    logger.exception(
                        "mge_signup_refresh_callback_failed event_id=%s", self.payload.event_id
                    )

            if result.success and result.signup_id is not None:
                event = (
                    await drain_thread(mge_signup_service.get_event_context, self.payload.event_id)
                    or {}
                )
                event_name = str(event.get("EventName") or f"MGE Event {self.payload.event_id}")
                ok, dm_msg = await mge_dm_followup.open_dm_followup(
                    user=interaction.user,
                    event_id=self.payload.event_id,
                    signup_id=int(result.signup_id),
                    event_name=event_name,
                )
                await interaction.followup.send(dm_msg, ephemeral=True)
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

        except Exception:
            if result is None:
                self._submitted = True
            logger.exception(
                "mge_signup_final_modal_submit_failed event_id=%s", self.payload.event_id
            )
            await send_ephemeral(
                interaction,
                (
                    "Your signup was saved, but a follow-up step failed."
                    if result and result.success
                    else "The signup outcome could not be confirmed. Do not submit again until it has been checked."
                ),
            )
