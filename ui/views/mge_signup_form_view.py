from __future__ import annotations

import logging

import discord

from core.interaction_safety import send_ephemeral
from ui.views.mge_signup_modal import MgeSignupFinalModal, MgeSignupModalPayload

logger = logging.getLogger(__name__)

PRIORITY_OPTIONS = ["High", "Medium", "Low"]
RANK_OPTIONS = ["1-5", "6-10", "11-15", "no_preference"]


class MgeSignupFormView(discord.ui.View):
    def __init__(
        self,
        *,
        payload: MgeSignupModalPayload,
        commander_options: dict[int, str],
        is_edit: bool = False,
        initial_priority: str | None = None,
        initial_rank_band: str | None = None,
        initial_commander_id: int | None = None,
        initial_current_heads: int | None = None,
        initial_kingdom_role: str | None = None,
        initial_gear_text: str | None = None,
        initial_armament_text: str | None = None,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)
        self.payload = payload
        self.commander_options = commander_options
        self.is_edit = is_edit

        self.selected_priority: str | None = initial_priority
        self.selected_rank_band: str | None = initial_rank_band
        self.selected_commander_id: int | None = initial_commander_id

        self.initial_current_heads = initial_current_heads
        self.initial_kingdom_role = initial_kingdom_role
        self.initial_gear_text = initial_gear_text
        self.initial_armament_text = initial_armament_text

        self.add_item(_PrioritySelect(self))
        self.add_item(_RankBandSelect(self))
        self.add_item(_CommanderSelect(self))

    @discord.ui.button(
        label="Continue",
        style=discord.ButtonStyle.primary,
        custom_id="mge_signup_continue",
    )
    async def continue_btn(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not self.selected_priority or self.selected_commander_id is None:
            await send_ephemeral(interaction, "Please select Priority and Commander first.")
            return

        logger.info(
            "mge_signup_modal_prefill_lengths heads=%s role=%s gear=%s armament=%s",
            len(str(self.initial_current_heads)) if self.initial_current_heads is not None else 0,
            len(self.initial_kingdom_role or ""),
            len(self.initial_gear_text or ""),
            len(self.initial_armament_text or ""),
        )

        await interaction.response.send_modal(
            MgeSignupFinalModal(
                payload=self.payload,
                selected_priority=self.selected_priority,
                selected_rank_band=self.selected_rank_band,
                selected_commander_id=self.selected_commander_id,
                initial_current_heads=self.initial_current_heads,
                initial_kingdom_role=self.initial_kingdom_role,
                initial_gear_text=self.initial_gear_text,
                initial_armament_text=self.initial_armament_text,
                title="Edit MGE Signup" if self.is_edit else "Create MGE Signup",
            )
        )


class _PrioritySelect(discord.ui.Select):
    def __init__(self, parent: MgeSignupFormView):
        self.parent_view = parent
        options: list[discord.SelectOption] = []
        selected = (parent.selected_priority or "").strip().lower()
        for v in PRIORITY_OPTIONS:
            options.append(
                discord.SelectOption(
                    label=v,
                    value=v,
                    default=(v.lower() == selected),
                )
            )
        super().__init__(
            placeholder="Select priority",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="mge_signup_priority_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_priority = str(self.values[0])
        await interaction.response.defer()


class _RankBandSelect(discord.ui.Select):
    # RETIRED_FLOW: Separate rank band selector — used only by the old player flow
    # (MgeSignupFormView / admin path).  Retained for admin-add and legacy edit
    # compatibility.  The simplified v2 player flow uses _PriorityRankSelect in
    # mge_simplified_signup_form_view.py instead.
    def __init__(self, parent: MgeSignupFormView):
        self.parent_view = parent
        options: list[discord.SelectOption] = []
        selected = (parent.selected_rank_band or "").strip().lower()
        for v in RANK_OPTIONS:
            options.append(
                discord.SelectOption(
                    label=v,
                    value=v,
                    default=(v.lower() == selected),
                )
            )
        super().__init__(
            placeholder="Select preferred rank band (optional)",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="mge_signup_rank_band_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_rank_band = str(self.values[0])
        await interaction.response.defer()


class _CommanderSelect(discord.ui.Select):
    def __init__(self, parent: MgeSignupFormView):
        self.parent_view = parent
        items = sorted(parent.commander_options.items(), key=lambda kv: kv[1].lower())[:25]
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
            custom_id="mge_signup_commander_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_commander_id = int(self.values[0])
        await interaction.response.defer()
