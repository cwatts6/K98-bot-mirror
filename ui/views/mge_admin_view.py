from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import discord

from core.interaction_safety import send_ephemeral
from mge.mge_event_service import SwitchToOpenResult, switch_event_to_open


@dataclass(slots=True)
class MGEAdminViewDeps:
    refresh_embed: Callable[[int], None]
    is_admin: Callable[[discord.Interaction], bool]


class ConfirmSwitchOpenView(discord.ui.View):
    def __init__(self, event_id: int, deps: MGEAdminViewDeps, timeout: float = 120) -> None:
        super().__init__(timeout=timeout)
        self.event_id = event_id
        self.deps = deps

    @discord.ui.button(
        label="Confirm Switch to Open",
        style=discord.ButtonStyle.danger,
        custom_id="mge_confirm_switch_open",
    )
    async def confirm_switch(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        if not self.deps.is_admin(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return

        actor_id = int(interaction.user.id)
        result: SwitchToOpenResult = switch_event_to_open(
            event_id=self.event_id,
            actor_discord_id=actor_id,
        )

        if not result.success:
            await send_ephemeral(interaction, f"❌ {result.message}")
            return

        self.deps.refresh_embed(self.event_id)
        await send_ephemeral(
            interaction,
            f"✅ Event switched to open mode. Deleted {result.deleted_signup_count} signups.",
        )
        self.stop()

    @discord.ui.button(
        label="Cancel", style=discord.ButtonStyle.secondary, custom_id="mge_cancel_switch_open"
    )
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        await send_ephemeral(interaction, "Cancelled.")
        self.stop()
