from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import discord

from event_calendar.reminder_prefs import normalize_prefs
from event_calendar.reminder_prefs_store import set_user_prefs
from event_calendar.reminder_types import (
    REMINDER_1H,
    REMINDER_3D,
    REMINDER_7D,
    REMINDER_24H,
    REMINDER_START,
)

logger = logging.getLogger(__name__)

_OFFSET_CHOICES = [REMINDER_7D, REMINDER_3D, REMINDER_24H, REMINDER_1H, REMINDER_START]


@dataclass
class ReminderConfigState:
    enabled: bool
    selected_types: set[str]
    selected_offsets: set[str]


def _normalize_type_selection(selected: list[str]) -> set[str]:
    vals = {str(x).strip().lower() for x in selected if str(x).strip()}
    if "all" in vals:
        return {"all"}
    return vals


def _render_summary(state: ReminderConfigState) -> str:
    types_str = ", ".join(sorted(state.selected_types)) if state.selected_types else "(none)"
    offsets_str = ", ".join(sorted(state.selected_offsets)) if state.selected_offsets else "(none)"
    return (
        f"**Enabled:** `{state.enabled}`\n"
        f"**Selected Types:** `{types_str}`\n"
        f"**Selected Offsets:** `{offsets_str}`\n\n"
        "Pick types + offsets, then click **Save**."
    )


def build_reminder_config_embed(state: ReminderConfigState) -> discord.Embed:
    embed = discord.Embed(
        title="📬 Calendar Reminder Configuration",
        description=_render_summary(state),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Selections are staged until you click Save.")
    return embed


class ReminderTypeSelect(discord.ui.Select):
    def __init__(self, parent_view: ReminderConfigView, options: list[str]):
        select_options = [
            discord.SelectOption(label=t, value=t, default=(t in parent_view.state.selected_types))
            for t in options[:25]
        ]
        super().__init__(
            placeholder="Select event types",
            min_values=0,
            max_values=max(1, min(len(select_options), 25)),
            options=select_options,
            custom_id="calendar_reminder_cfg_types",
        )
        self._parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if not self._parent_view.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return

        new_state = ReminderConfigState(
            enabled=self._parent_view.state.enabled,
            selected_types=_normalize_type_selection(list(self.values)),
            selected_offsets=set(self._parent_view.state.selected_offsets),
        )
        new_view = self._parent_view.clone_with_state(new_state)
        embed = build_reminder_config_embed(new_view.state)
        await interaction.response.edit_message(embed=embed, view=new_view)
        new_view.message = interaction.message


class ReminderOffsetSelect(discord.ui.Select):
    def __init__(self, parent_view: ReminderConfigView):
        select_options = [
            discord.SelectOption(
                label=o, value=o, default=(o in parent_view.state.selected_offsets)
            )
            for o in _OFFSET_CHOICES
        ]
        super().__init__(
            placeholder="Select reminder offsets",
            min_values=0,
            max_values=len(select_options),
            options=select_options,
            custom_id="calendar_reminder_cfg_offsets",
        )
        self._parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if not self._parent_view.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return

        new_state = ReminderConfigState(
            enabled=self._parent_view.state.enabled,
            selected_types=set(self._parent_view.state.selected_types),
            selected_offsets={str(v).strip().lower() for v in self.values if str(v).strip()},
        )
        new_view = self._parent_view.clone_with_state(new_state)
        embed = build_reminder_config_embed(new_view.state)
        await interaction.response.edit_message(embed=embed, view=new_view)
        new_view.message = interaction.message


class ReminderConfigView(discord.ui.View):
    def __init__(
        self,
        *,
        owner_user_id: int,
        user_id: int,
        initial_prefs: dict[str, Any],
        known_event_types: list[str],
        timeout: float = 300.0,
        _state_override: ReminderConfigState | None = None,
    ):
        super().__init__(timeout=timeout)
        self.owner_user_id = int(owner_user_id)
        self.user_id = int(user_id)
        self.known_event_types = ["all", *sorted({t for t in known_event_types if t})]

        if _state_override is not None:
            self.state = _state_override
        else:
            p = normalize_prefs(initial_prefs)
            by_type = p.get("by_event_type", {}) or {}
            selected_types = set(by_type.keys())
            selected_offsets = set()
            for vals in by_type.values():
                selected_offsets.update(str(x).strip().lower() for x in vals if str(x).strip())

            self.state = ReminderConfigState(
                enabled=bool(p.get("enabled", False)),
                selected_types=selected_types,
                selected_offsets=selected_offsets,
            )

        self.add_item(ReminderTypeSelect(self, self.known_event_types))
        self.add_item(ReminderOffsetSelect(self))

    def clone_with_state(self, state: ReminderConfigState) -> ReminderConfigView:
        return ReminderConfigView(
            owner_user_id=self.owner_user_id,
            user_id=self.user_id,
            initial_prefs={},  # ignored due to override
            known_event_types=[t for t in self.known_event_types if t != "all"],
            timeout=self.timeout if self.timeout is not None else 300.0,
            _state_override=state,
        )

    def is_owner(self, interaction: discord.Interaction) -> bool:
        return bool(interaction.user and interaction.user.id == self.owner_user_id)

    def _compose_prefs_payload(self) -> dict[str, Any]:
        by_event_type: dict[str, list[str]] = {}
        offsets = sorted(self.state.selected_offsets)
        for t in sorted(self.state.selected_types):
            by_event_type[t] = offsets
        return {
            "enabled": self.state.enabled,
            "by_event_type": by_event_type,
        }

    @discord.ui.button(label="Enable", style=discord.ButtonStyle.success, custom_id="cfg_enable")
    async def enable_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return
        new_state = ReminderConfigState(
            enabled=True,
            selected_types=set(self.state.selected_types),
            selected_offsets=set(self.state.selected_offsets),
        )
        new_view = self.clone_with_state(new_state)
        await interaction.response.edit_message(
            embed=build_reminder_config_embed(new_view.state), view=new_view
        )
        new_view.message = interaction.message

    @discord.ui.button(
        label="Disable", style=discord.ButtonStyle.secondary, custom_id="cfg_disable"
    )
    async def disable_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return
        new_state = ReminderConfigState(
            enabled=False,
            selected_types=set(self.state.selected_types),
            selected_offsets=set(self.state.selected_offsets),
        )
        new_view = self.clone_with_state(new_state)
        await interaction.response.edit_message(
            embed=build_reminder_config_embed(new_view.state), view=new_view
        )
        new_view.message = interaction.message

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.secondary, custom_id="cfg_reset")
    async def reset_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return
        new_state = ReminderConfigState(
            enabled=False,
            selected_types=set(),
            selected_offsets=set(),
        )
        new_view = self.clone_with_state(new_state)
        await interaction.response.edit_message(
            embed=build_reminder_config_embed(new_view.state), view=new_view
        )
        new_view.message = interaction.message

    @discord.ui.button(label="Save", style=discord.ButtonStyle.primary, custom_id="cfg_save")
    async def save_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return

        if not self.state.selected_types:
            await interaction.response.send_message(
                "Select at least one event type before saving.", ephemeral=True
            )
            return
        if not self.state.selected_offsets:
            await interaction.response.send_message(
                "Select at least one reminder offset before saving.", ephemeral=True
            )
            return

        payload = self._compose_prefs_payload()
        set_user_prefs(self.user_id, payload)
        logger.info(
            "[CALENDAR][REMINDER_CFG] saved user_id=%s enabled=%s types=%s offsets=%s",
            self.user_id,
            self.state.enabled,
            sorted(self.state.selected_types),
            sorted(self.state.selected_offsets),
        )

        # terminal locked view
        locked = self.clone_with_state(self.state)
        for child in locked.children:
            child.disabled = True

        embed = build_reminder_config_embed(self.state)
        embed.color = discord.Color.green()
        embed.set_footer(text="✅ Saved. Run /calendar_reminder_config to edit again.")

        await interaction.response.edit_message(
            content="✅ Reminder preferences saved.",
            embed=embed,
            view=locked,
        )
        locked.message = interaction.message

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="cfg_cancel")
    async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "Only the command invoker can use this panel.", ephemeral=True
            )
            return
        locked = self.clone_with_state(self.state)
        for child in locked.children:
            child.disabled = True
        await interaction.response.edit_message(content="Cancelled.", embed=None, view=locked)
        locked.message = interaction.message

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            if getattr(self, "message", None):
                await self.message.edit(view=self)
        except Exception:
            logger.debug("[CALENDAR][REMINDER_CFG] timeout edit failed", exc_info=True)
