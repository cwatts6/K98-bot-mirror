from __future__ import annotations

import discord

from ark.dal.ark_dal import get_reminder_prefs, upsert_reminder_prefs
from ark.reminder_prefs import merge_with_defaults


class ArkReminderPrefsView(discord.ui.View):
    def __init__(self, *, author_id: int):
        super().__init__(timeout=180)
        self.author_id = author_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This preferences panel is not for you.", ephemeral=True
            )
            return False
        return True

    async def _toggle(self, interaction: discord.Interaction, field: str) -> None:
        row = await get_reminder_prefs(interaction.user.id)
        prefs = merge_with_defaults(row)
        current = int(prefs.get(field, 0))
        prefs[field] = 0 if current == 1 else 1

        await upsert_reminder_prefs(
            interaction.user.id,
            opt_out_all=int(prefs["OptOutAll"]),
            opt_out_24h=int(prefs["OptOut24h"]),
            opt_out_4h=int(prefs["OptOut4h"]),
            opt_out_1h=int(prefs["OptOut1h"]),
            opt_out_start=int(prefs["OptOutStart"]),
            opt_out_checkin_12h=int(prefs["OptOutCheckIn12h"]),
        )
        await interaction.response.edit_message(
            content=self._render_text(prefs),
            view=self,
        )

    @staticmethod
    def _render_text(prefs: dict) -> str:
        def yn(v: int) -> str:
            return "Opted Out" if int(v) == 1 else "Enabled"

        return (
            "**Ark Reminder Preferences**\n"
            f"- All reminders: **{yn(prefs.get('OptOutAll', 0))}**\n"
            f"- 24h DM: **{yn(prefs.get('OptOut24h', 0))}**\n"
            f"- 4h DM: **{yn(prefs.get('OptOut4h', 0))}**\n"
            f"- 1h DM: **{yn(prefs.get('OptOut1h', 0))}**\n"
            f"- Start DM: **{yn(prefs.get('OptOutStart', 0))}**\n"
            f"- Check-in (12h) DM: **{yn(prefs.get('OptOutCheckIn12h', 0))}**\n"
        )

    @discord.ui.button(label="Toggle All", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_all(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await self._toggle(interaction, "OptOutAll")

    @discord.ui.button(label="Toggle 24h", style=discord.ButtonStyle.primary, row=1)
    async def toggle_24h(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await self._toggle(interaction, "OptOut24h")

    @discord.ui.button(label="Toggle 4h", style=discord.ButtonStyle.primary, row=1)
    async def toggle_4h(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await self._toggle(interaction, "OptOut4h")

    @discord.ui.button(label="Toggle 1h", style=discord.ButtonStyle.primary, row=1)
    async def toggle_1h(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await self._toggle(interaction, "OptOut1h")

    @discord.ui.button(label="Toggle Start", style=discord.ButtonStyle.success, row=2)
    async def toggle_start(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await self._toggle(interaction, "OptOutStart")

    @discord.ui.button(label="Toggle Check-in 12h", style=discord.ButtonStyle.success, row=2)
    async def toggle_checkin(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await self._toggle(interaction, "OptOutCheckIn12h")


__all__ = ["ArkReminderPrefsView"]
