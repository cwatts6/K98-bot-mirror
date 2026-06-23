"""Reminder-centre Discord components for the /me player command centre."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

from constants import DEFAULT_REMINDER_TIMES, VALID_TYPES
from player_self_service import reminder_service
from player_self_service.reminder_service import (
    ReminderCentreState,
    ReminderMessage,
    ReminderUnsubscribeConfirmation,
)
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)

logger = logging.getLogger(__name__)

SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]


def _option_desc(key: str) -> str:
    return {
        "ruins": "Ruins events",
        "altars": "Altar fights",
        "major": "Major timeline events",
        "fights": "Altars plus major events marked FIGHT",
        "all": "Every KVK event type",
    }.get(key, "")


def _event_options(selected: tuple[str, ...]) -> list[discord.SelectOption]:
    return [
        discord.SelectOption(
            label=event_type,
            value=event_type,
            description=_option_desc(event_type),
            default=event_type in selected,
        )
        for event_type in VALID_TYPES
    ]


def _dm_embed(message: ReminderMessage) -> discord.Embed:
    embed = discord.Embed(
        title=message.title,
        description=message.description,
        color=message.color,
    )
    for name, value in message.fields:
        embed.add_field(name=name, value=value, inline=False)
    embed.set_footer(text=message.footer)
    return embed


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    except TypeError:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            logger.debug("player_self_service_reminder_defer_failed", exc_info=True)
    except Exception:
        logger.debug("player_self_service_reminder_defer_failed", exc_info=True)


class ReminderEventSelect(discord.ui.Select):
    def __init__(self, *, selected: tuple[str, ...]) -> None:
        options = _event_options(selected)
        super().__init__(
            placeholder="Choose event types",
            min_values=1,
            max_values=len(options),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, ReminderSetupView):
            await interaction.response.send_message(
                "This reminder selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        selected_types, adjusted = reminder_service.normalize_event_types(tuple(self.values))
        view.selected_types = list(selected_types)
        self.options = _event_options(selected_types)
        if adjusted:
            await interaction.response.edit_message(view=view)
            return
        await interaction.response.defer()


class ReminderTimeSelect(discord.ui.Select):
    def __init__(self, *, selected: tuple[str, ...]) -> None:
        options = [
            discord.SelectOption(
                label=reminder_time,
                value=reminder_time,
                description=f"{reminder_time.upper()} reminder",
                default=reminder_time in selected,
            )
            for reminder_time in DEFAULT_REMINDER_TIMES
        ]
        super().__init__(
            placeholder="Choose reminder times",
            min_values=1,
            max_values=len(options),
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, ReminderSetupView):
            await interaction.response.send_message(
                "This reminder selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        view.selected_reminders = list(self.values)
        await interaction.response.defer()


class ReminderSetupView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        username: str,
        state: ReminderCentreState,
        display_name: str,
        timeout: float = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.username = username
        self.display_name = display_name
        self.selected_types = list(state.event_types)
        self.selected_reminders = list(state.reminder_times or tuple(DEFAULT_REMINDER_TIMES))
        self._saving = False
        self.add_item(ReminderEventSelect(selected=tuple(self.selected_types)))
        self.add_item(ReminderTimeSelect(selected=tuple(self.selected_reminders)))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private reminder menu is not for you.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(
        label="Save",
        style=discord.ButtonStyle.success,
        custom_id="me:reminder:save",
        row=2,
    )
    async def save_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        if self._saving:
            await interaction.response.defer()
            return
        self._saving = True
        await _defer_private(interaction)

        result = await reminder_service.save_reminder_preferences(
            self.author_id,
            self.username,
            self.selected_types,
            self.selected_reminders,
        )
        if not result.ok:
            self._saving = False
            await interaction.followup.send(result.message, ephemeral=True)
            return

        dm_sent = await self._send_dm(interaction, result.dm_message)
        content = result.message
        if dm_sent:
            content += " A confirmation DM was sent."
        else:
            content += (
                " Saved, but I could not send a confirmation DM. Check your server DM settings."
            )
        view = ReminderCompletionView(
            author_id=self.author_id,
            display_name=self.display_name,
            message=content,
        )
        try:
            await interaction.edit_original_response(content=content, embed=None, view=view)
        except Exception:
            logger.debug("player_self_service_reminder_save_edit_failed", exc_info=True)
            await interaction.followup.send(content, view=view, ephemeral=True)
        self.stop()

    async def _send_dm(
        self,
        interaction: discord.Interaction,
        message: ReminderMessage | None,
    ) -> bool:
        if message is None:
            return False
        try:
            await interaction.user.send(embed=_dm_embed(message))
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False


class ReminderUnsubscribeConfirmView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        confirmation: ReminderUnsubscribeConfirmation,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.confirmation = confirmation
        self._confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private reminder confirmation is not for you.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.danger,
        custom_id="me:reminder:unsubscribe:confirm",
    )
    async def confirm_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        if self._confirmed:
            await interaction.response.defer()
            return
        self._confirmed = True
        await _defer_private(interaction)
        result = await reminder_service.confirm_unsubscribe(self.author_id, self.confirmation)
        if not result.ok:
            self._confirmed = False
            await interaction.followup.send(result.message, ephemeral=True)
            return

        dm_sent = await self._send_dm(interaction, result.dm_message)
        content = result.message
        if dm_sent:
            content += " A confirmation DM was sent."
        else:
            content += " I could not send a confirmation DM, but you are unsubscribed."
        view = ReminderCompletionView(
            author_id=self.author_id,
            display_name=self.display_name,
            message=content,
        )
        try:
            await interaction.edit_original_response(content=content, embed=None, view=view)
        except Exception:
            logger.debug(
                "player_self_service_reminder_unsubscribe_edit_failed",
                exc_info=True,
            )
            await interaction.followup.send(content, view=view, ephemeral=True)
        self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="me:reminder:unsubscribe:cancel",
    )
    async def cancel_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.edit_message(
            content="Reminder unsubscribe cancelled.",
            embed=None,
            view=ReminderCompletionView(
                author_id=self.author_id,
                display_name=self.display_name,
                message="Reminder unsubscribe cancelled.",
            ),
        )

    async def _send_dm(
        self,
        interaction: discord.Interaction,
        message: ReminderMessage | None,
    ) -> bool:
        if message is None:
            return False
        try:
            await interaction.user.send(embed=_dm_embed(message))
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False


class ReminderCompletionView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        message: str,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.message = message
        self.summary_loader = summary_loader

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This private menu is not for you.", ephemeral=True)
        return False

    async def _show_page(self, interaction: discord.Interaction, page: str) -> None:
        await _defer_private(interaction)
        try:
            summary = await self.summary_loader(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_reminder_completion_summary_failed user_id=%s page=%s",
                self.author_id,
                page,
            )
            await interaction.followup.send(
                "Personal status is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return

        from ui.views.player_self_service_views import (
            PlayerSelfServiceView,
            build_page_embed,
        )

        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=page,
            summary_loader=self.summary_loader,
        )
        embed = build_page_embed(page, summary, display_name=self.display_name)
        edited = await interaction.edit_original_response(content=None, embed=embed, view=view)
        view.set_message_ref(getattr(interaction, "message", None) or edited)

    @discord.ui.button(label="Reminder Centre", style=discord.ButtonStyle.primary)
    async def reminders_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        from ui.views.player_self_service_views import PAGE_REMINDERS

        await self._show_page(interaction, PAGE_REMINDERS)

    @discord.ui.button(label="Dashboard", style=discord.ButtonStyle.secondary)
    async def dashboard_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        from ui.views.player_self_service_views import PAGE_DASHBOARD

        await self._show_page(interaction, PAGE_DASHBOARD)
