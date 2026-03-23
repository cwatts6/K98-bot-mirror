from __future__ import annotations

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_or_leadership_interaction
from ui.views.mge_admin_add_signup_view import MgeAdminAddLookupModal
from ui.views.mge_signup_view import MGESignupView


class MGESimplifiedSignupView(MGESignupView):
    """Simplified public-facing MGE signup view for player/data channel use."""

    def __init__(self, event_id: int, admin_deps, timeout: float | None = None):
        super().__init__(event_id=event_id, admin_deps=admin_deps, timeout=timeout)
        for item in list(self.children):
            if getattr(item, "custom_id", "") in {
                "mge_switch_open",
                "mge_switch_fixed",
                "mge_edit_rules",
                "mge_refresh_embed",
                "mge_open_leadership_board",
                "mge_admin_completion_controls",
            }:
                self.remove_item(item)

        edit_button = next(
            (child for child in self.children if getattr(child, "custom_id", "") == "mge_edit"),
            None,
        )
        if edit_button is not None:
            edit_button.label = "Edit Sign Up"

        admin_add_button = discord.ui.Button(
            label="Admin Add Signup",
            style=discord.ButtonStyle.secondary,
            custom_id="mge_admin_add_signup",
        )
        admin_add_button.callback = self.admin_add_signup
        self.add_item(admin_add_button)

    async def admin_add_signup(self, interaction: discord.Interaction) -> None:
        """Open the admin/leadership add-signup lookup flow."""
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        if await self._block_if_locked(interaction):
            return

        await interaction.response.send_modal(
            MgeAdminAddLookupModal(
                author_id=int(interaction.user.id),
                on_governor_selected=self._open_admin_signup_modal,
            )
        )

    async def _open_admin_signup_modal(
        self,
        interaction: discord.Interaction,
        governor_id: int,
        governor_name: str,
    ) -> None:
        """Continue admin-add flow into the normal MGE signup form."""
        await self._open_signup_modal(
            interaction,
            governor_id=int(governor_id),
            governor_name=str(governor_name),
        )
