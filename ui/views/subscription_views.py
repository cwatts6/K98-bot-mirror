# ui/views/subscription_views.py
from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence

import discord
from discord.errors import HTTPException, NotFound

from constants import DEFAULT_REMINDER_TIMES, VALID_TYPES
from utils import make_cid


def _option_desc(key: str) -> str:
    return {
        "ruins": "Ruins events",
        "altars": "Altar fights",
        "major": "Major timeline events",
        "fights": "All fights (altars + major FIGHTs)",
        "all": "Every event type",
    }.get(key, "")


class DynamicEventSelect(discord.ui.Select):
    def __init__(self, *, selected: Sequence[str], custom_id: str, min_values: int = 0):
        options = [
            discord.SelectOption(
                label=typ,
                value=typ,
                description=_option_desc(typ),
                default=(typ in selected),
            )
            for typ in VALID_TYPES
        ]
        super().__init__(
            placeholder="Select event types...",
            min_values=min_values,
            max_values=len(options),
            options=options,
            custom_id=custom_id,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        view: SubscriptionView = self.view  # type: ignore[assignment]
        if not view.is_owner(interaction):
            await interaction.response.send_message("This selector isn't for you.", ephemeral=True)
            return
        view.selected_types = list(self.values)
        view.rebuild_items()
        await interaction.response.edit_message(view=view)


class ReminderSelect(discord.ui.Select):
    def __init__(self, *, selected: Sequence[str], custom_id: str, min_values: int = 0):
        options = [
            discord.SelectOption(
                label=t,
                value=t,
                description=f"{t.upper()} reminder",
                default=(t in selected),
            )
            for t in DEFAULT_REMINDER_TIMES
        ]
        super().__init__(
            placeholder="Select reminder times...",
            min_values=min_values,
            max_values=len(options),
            options=options,
            custom_id=custom_id,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        view: SubscriptionView = self.view  # type: ignore[assignment]
        if not view.is_owner(interaction):
            await interaction.response.send_message("This selector isn't for you.", ephemeral=True)
            return
        view.selected_reminders = list(self.values)
        await interaction.response.defer()


class ConfirmButton(discord.ui.Button):
    def __init__(self, *, label: str, custom_id: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.success,
            custom_id=custom_id,
            row=2,
        )
        self._clicked = False

    async def callback(self, interaction: discord.Interaction):
        view: SubscriptionView = self.view  # type: ignore[assignment]
        if not view.is_owner(interaction):
            await interaction.response.send_message("This button isn't for you.", ephemeral=True)
            return
        if self._clicked:
            await interaction.response.defer()
            return
        self._clicked = True
        await view.on_confirm(interaction)


class SubscriptionView(discord.ui.View):
    def __init__(
        self,
        *,
        user: discord.abc.User,
        uid: int,
        username: str,
        selected_types: Sequence[str] | None = None,
        selected_reminders: Sequence[str] | None = None,
        confirm_label: str = "✅ Confirm",
        include_unsubscribe: bool = False,
        reminder_min_values: int = 0,
        cid_prefix: str = "sub",
        timeout: int = 180,
        on_confirm: Callable[[discord.Interaction, SubscriptionView], Awaitable[None]],
        on_unsubscribe: (
            Callable[[discord.Interaction, SubscriptionView], Awaitable[None]] | None
        ) = None,
        on_timeout_edit: Callable[[SubscriptionView], Awaitable[None]] | None = None,
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.uid = uid
        self.username = username
        self.selected_types = list(selected_types or [])
        self.selected_reminders = list(selected_reminders or [])
        self.confirm_label = confirm_label
        self.include_unsubscribe = include_unsubscribe
        self.reminder_min_values = reminder_min_values
        self.on_confirm_cb = on_confirm
        self.on_unsubscribe_cb = on_unsubscribe
        self.on_timeout_edit_cb = on_timeout_edit

        self.event_select_id = make_cid(f"{cid_prefix}:event", uid)
        self.reminder_select_id = make_cid(f"{cid_prefix}:remind", uid)
        self.confirm_button_id = make_cid(f"{cid_prefix}:confirm", uid)
        self.unsubscribe_button_id = make_cid(f"{cid_prefix}:unsubscribe", uid)

        self.rebuild_items()

    def is_owner(self, interaction: discord.Interaction) -> bool:
        return bool(interaction.user and interaction.user.id == self.uid)

    def rebuild_items(self) -> None:
        self.clear_items()
        self.add_item(
            DynamicEventSelect(
                selected=self.selected_types, custom_id=self.event_select_id, min_values=0
            )
        )
        self.add_item(
            ReminderSelect(
                selected=self.selected_reminders,
                custom_id=self.reminder_select_id,
                min_values=self.reminder_min_values,
            )
        )
        self.add_item(ConfirmButton(label=self.confirm_label, custom_id=self.confirm_button_id))

        if self.include_unsubscribe and self.on_unsubscribe_cb:
            button = discord.ui.Button(
                label="🔕 Unsubscribe",
                style=discord.ButtonStyle.danger,
                custom_id=self.unsubscribe_button_id,
                row=3,
            )

            async def _unsub_cb(interaction: discord.Interaction):
                if not self.is_owner(interaction):
                    await interaction.response.send_message(
                        "This button isn't for you.", ephemeral=True
                    )
                    return
                await self.on_unsubscribe_cb(interaction, self)

            button.callback = _unsub_cb
            self.add_item(button)

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        if self.on_timeout_edit_cb is None:
            return
        try:
            await self.on_timeout_edit_cb(self)
        except (NotFound, HTTPException):
            return

    async def on_confirm(self, interaction: discord.Interaction):
        await self.on_confirm_cb(interaction, self)


__all__ = [
    "ConfirmButton",
    "DynamicEventSelect",
    "ReminderSelect",
    "SubscriptionView",
]
