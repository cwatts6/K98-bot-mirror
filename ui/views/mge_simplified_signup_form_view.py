"""
Simplified MGE player signup form view (v2 — no modal, no DM).

Flow:
  1. Player selects combined "Priority (Rank)" option.
  2. Player selects Requested Commander.
  3. Player clicks "Sign Up" — service is called immediately; no modal is shown
     and no DM follow-up is sent.

This view is controlled by MGE_SIGNUP_FLOW_CONFIG.  When send_dm_followup is
False (the live default) the DM attachment flow is intentionally suppressed.

For edit flows the combined dropdown is pre-filled using
get_option_by_priority_rank() which resolves legacy signups gracefully.
When an existing signup is edited through this simplified view, current_heads,
kingdom_role, gear_text, and armament_text are written as None / 0 because the
simplified flow does not re-collect those fields.  This is intentional.
"""

from __future__ import annotations

import logging

import discord

from core.interaction_safety import send_ephemeral
from mge import mge_signup_service
from mge.mge_priority_rank_map import (
    PRIORITY_RANK_OPTIONS,
    get_option_by_priority_rank,
    get_option_by_value,
)
from mge.mge_validation import validate_priority_rank_value
from ui.views.mge_signup_modal import MgeSignupModalPayload

logger = logging.getLogger(__name__)


class MgeSimplifiedSignupFormView(discord.ui.View):
    """
    Simplified player signup form.

    Renders two dropdowns — combined Priority (Rank) and Commander — and a
    "Sign Up" button that submits directly without opening a modal or a DM.
    """

    def __init__(
        self,
        *,
        payload: MgeSignupModalPayload,
        commander_options: dict[int, str],
        is_edit: bool = False,
        initial_priority_rank_value: str | None = None,
        initial_commander_id: int | None = None,
        timeout: float = 300,
    ) -> None:
        super().__init__(timeout=timeout)
        self.payload = payload
        self.commander_options = commander_options
        self.is_edit = is_edit

        self.selected_priority_rank_value: str | None = initial_priority_rank_value
        self.selected_commander_id: int | None = initial_commander_id

        self.add_item(_PriorityRankSelect(self))
        self.add_item(_CommanderSelect(self))

    @discord.ui.button(
        label="Sign Up",
        style=discord.ButtonStyle.primary,
        custom_id="mge_simplified_signup_submit",
        row=2,
    )
    async def submit_btn(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button

        # --- Validate selections ---
        if not self.selected_priority_rank_value:
            await send_ephemeral(interaction, "❌ Please select a Priority (Rank) first.")
            return

        priority_rank_check = validate_priority_rank_value(self.selected_priority_rank_value)
        if not priority_rank_check.valid:
            await send_ephemeral(interaction, f"❌ {priority_rank_check.message}")
            return

        if self.selected_commander_id is None:
            await send_ephemeral(interaction, "❌ Please select a Requested Commander first.")
            return

        option = get_option_by_value(self.selected_priority_rank_value)
        if option is None:
            await send_ephemeral(interaction, "❌ Invalid Priority (Rank) selection.")
            return

        resolved_priority = option.request_priority
        resolved_rank_band = option.preferred_rank_band

        # --- Call service ---
        try:
            if self.payload.signup_id is None:
                result = mge_signup_service.create_signup(
                    event_id=self.payload.event_id,
                    actor_discord_id=interaction.user.id,
                    actor_role_ids=self.payload.actor_role_ids,
                    admin_role_ids=self.payload.admin_role_ids,
                    governor_id=self.payload.governor_id,
                    governor_name_snapshot=self.payload.governor_name,
                    request_priority=resolved_priority,
                    preferred_rank_band=resolved_rank_band,
                    requested_commander_id=self.selected_commander_id,
                    # Simplified flow does not collect these fields; defaults are safe
                    # given the nullable DB schema.
                    current_heads=0,
                    kingdom_role=None,
                    gear_text=None,
                    armament_text=None,
                )
            else:
                result = mge_signup_service.edit_signup(
                    signup_id=self.payload.signup_id,
                    event_id=self.payload.event_id,
                    actor_discord_id=interaction.user.id,
                    actor_role_ids=self.payload.actor_role_ids,
                    admin_role_ids=self.payload.admin_role_ids,
                    existing_governor_id=self.payload.governor_id,
                    request_priority=resolved_priority,
                    preferred_rank_band=resolved_rank_band,
                    requested_commander_id=self.selected_commander_id,
                    # When editing through the simplified view, these legacy fields are
                    # reset to defaults.  The original values remain in the DB audit log.
                    current_heads=0,
                    kingdom_role=None,
                    gear_text=None,
                    armament_text=None,
                )
        except Exception:
            logger.exception(
                "mge_simplified_signup_submit_exception event_id=%s actor_discord_id=%s",
                self.payload.event_id,
                interaction.user.id,
            )
            await send_ephemeral(interaction, "❌ Failed to submit signup.")
            return

        # --- Respond ---
        await interaction.response.send_message(
            ("✅ " if result.success else "❌ ") + result.message,
            ephemeral=True,
        )

        # --- Logging ---
        logger.info(
            "mge_simplified_signup_submitted",
            extra={
                "flow_config": "simplified_v2",
                "event_id": self.payload.event_id,
                "priority_rank_value": self.selected_priority_rank_value,
                "priority": resolved_priority,
                "rank_band": resolved_rank_band,
                "commander_id": self.selected_commander_id,
                "actor_discord_id": interaction.user.id,
                "outcome": "success" if result.success else "failure",
            },
        )

        # --- Refresh embed if success ---
        if result.success and self.payload.on_success_refresh is not None:
            try:
                self.payload.on_success_refresh(int(self.payload.event_id))
            except Exception:
                logger.exception(
                    "mge_simplified_signup_refresh_callback_failed event_id=%s",
                    self.payload.event_id,
                )

        # DM follow-up is intentionally suppressed in the simplified flow.
        # MGE_SIGNUP_FLOW_CONFIG.send_dm_followup == False is the live default.
        # The DM flow remains active for the admin path via MgeSignupFinalModal.


def build_simplified_signup_form_view(
    *,
    payload: MgeSignupModalPayload,
    commander_options: dict[int, str],
    is_edit: bool = False,
    existing_signup_row: dict | None = None,
    timeout: float = 300,
) -> MgeSimplifiedSignupFormView:
    """
    Construct a MgeSimplifiedSignupFormView, pre-filling dropdowns from an
    existing signup row when editing a legacy signup.

    For legacy signups that have separate RequestPriority + PreferredRankBand,
    get_option_by_priority_rank() resolves the nearest combined option.
    """
    initial_priority_rank_value: str | None = None
    initial_commander_id: int | None = None

    if existing_signup_row is not None:
        raw_priority = str(existing_signup_row.get("RequestPriority") or "").strip()
        raw_rank_band = str(existing_signup_row.get("PreferredRankBand") or "").strip() or None
        option = get_option_by_priority_rank(raw_priority, raw_rank_band)
        if option is not None:
            initial_priority_rank_value = option.value
        try:
            initial_commander_id = int(existing_signup_row.get("RequestedCommanderId"))
        except Exception:
            initial_commander_id = None

    return MgeSimplifiedSignupFormView(
        payload=payload,
        commander_options=commander_options,
        is_edit=is_edit,
        initial_priority_rank_value=initial_priority_rank_value,
        initial_commander_id=initial_commander_id,
        timeout=timeout,
    )


class _PriorityRankSelect(discord.ui.Select):
    """Combined Priority (Rank) dropdown for the simplified signup flow."""

    def __init__(self, parent: MgeSimplifiedSignupFormView) -> None:
        self.parent_view = parent
        selected = parent.selected_priority_rank_value or ""
        options: list[discord.SelectOption] = [
            discord.SelectOption(
                label=opt.label,
                value=opt.value,
                default=(opt.value == selected),
            )
            for opt in PRIORITY_RANK_OPTIONS
        ]
        super().__init__(
            placeholder="Select Priority (Rank)",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="mge_simplified_priority_rank_select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_priority_rank_value = str(self.values[0])
        await interaction.response.defer()


class _CommanderSelect(discord.ui.Select):
    """Commander dropdown for the simplified signup form."""

    def __init__(self, parent: MgeSimplifiedSignupFormView) -> None:
        self.parent_view = parent
        items = sorted(parent.commander_options.items(), key=lambda kv: kv[1].lower())[:25]
        # Discord API limits Select options to 25 items maximum.
        selected = parent.selected_commander_id
        options = [
            discord.SelectOption(
                label=name[:100],
                value=str(cid),
                default=(selected is not None and int(selected) == int(cid)),
            )
            for cid, name in items
        ]
        super().__init__(
            placeholder="Select requested commander",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="mge_simplified_commander_select",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_commander_id = int(self.values[0])
        await interaction.response.defer()
