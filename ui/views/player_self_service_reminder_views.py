"""Reminder-centre Discord components for the /me player command centre."""

from __future__ import annotations

import asyncio
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


def _time_options(selected: tuple[str, ...]) -> list[discord.SelectOption]:
    return [
        discord.SelectOption(
            label=reminder_time,
            value=reminder_time,
            description=f"{reminder_time.upper()} reminder",
            default=reminder_time in selected,
        )
        for reminder_time in DEFAULT_REMINDER_TIMES
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
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_reminder_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_reminder_defer_failed", exc_info=True)


async def _refresh_host_page(
    *,
    host_message: object | None,
    interaction: discord.Interaction | None = None,
    author_id: int,
    display_name: str,
    summary_loader: SummaryLoader,
) -> None:
    if host_message is None:
        return
    try:
        summary = await summary_loader(int(author_id))
        from ui.views.player_self_service_views import (
            PAGE_REMINDERS,
            PlayerSelfServiceView,
            _build_page_response,
            _edit_original_with_image_fallback,
        )

        view = PlayerSelfServiceView(
            author_id=int(author_id),
            display_name=display_name,
            page=PAGE_REMINDERS,
            summary=summary,
            summary_loader=summary_loader,
        )
        embed, files = await _build_page_response(
            PAGE_REMINDERS,
            summary,
            display_name=display_name,
        )

        class _MessageTarget:
            async def edit_original_response(self, **kwargs):
                if interaction is not None and hasattr(interaction.followup, "edit_message"):
                    return await interaction.followup.edit_message(host_message.id, **kwargs)
                if not hasattr(host_message, "edit"):
                    return None
                return await host_message.edit(**kwargs)

        edited = await _edit_original_with_image_fallback(
            _MessageTarget(),
            page=PAGE_REMINDERS,
            summary=summary,
            display_name=display_name,
            view=view,
            embed=embed,
            files=files,
        )
        view.set_message_ref(edited or host_message)
    except discord.NotFound:
        logger.debug(
            "player_self_service_reminder_host_refresh_message_missing user_id=%s",
            author_id,
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_reminder_host_refresh_failed", exc_info=True)


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
        await view.autosave_selection(interaction, adjusted=adjusted)


class ReminderTimeSelect(discord.ui.Select):
    def __init__(self, *, selected: tuple[str, ...]) -> None:
        super().__init__(
            placeholder="Choose reminder times",
            min_values=1,
            max_values=len(DEFAULT_REMINDER_TIMES),
            options=_time_options(selected),
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
        await view.autosave_selection(interaction)


class ReminderSetupView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        username: str,
        state: ReminderCentreState,
        display_name: str,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.username = username
        self.display_name = display_name
        self.host_message = host_message
        self.summary_loader = summary_loader
        self.selected_types = list(state.event_types)
        self.selected_reminders = list(state.reminder_times or tuple(DEFAULT_REMINDER_TIMES))
        self.can_unsubscribe = state.can_unsubscribe
        self._saving = False
        self.add_item(ReminderEventSelect(selected=tuple(self.selected_types)))
        self.add_item(ReminderTimeSelect(selected=tuple(self.selected_reminders)))
        for child in list(self.children):
            if getattr(child, "custom_id", None) == "me:reminder:save":
                self.remove_item(child)
        for child in self.children:
            if getattr(child, "custom_id", None) == "me:reminder:remove_all":
                child.disabled = not self.can_unsubscribe

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private reminder menu is not for you.",
            ephemeral=True,
        )
        return False

    async def autosave_selection(
        self,
        interaction: discord.Interaction,
        *,
        adjusted: bool = False,
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
        content = f"{result.message} Saved automatically."
        if dm_sent:
            content += " A confirmation DM was sent."
        elif result.dm_message is not None:
            content += " I could not send a confirmation DM. Check your server DM settings."
        self.selected_types = list(result.event_types)
        self.selected_reminders = list(result.reminder_times)
        for child in self.children:
            if isinstance(child, ReminderEventSelect):
                child.options = _event_options(tuple(self.selected_types))
            if isinstance(child, ReminderTimeSelect):
                child.options = _time_options(tuple(self.selected_reminders))
        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        self.can_unsubscribe = True
        self._saving = False
        for child in self.children:
            if getattr(child, "custom_id", None) == "me:reminder:remove_all":
                child.disabled = False
        try:
            await interaction.edit_original_response(content=content, embed=None, view=self)
        except Exception:
            logger.debug(
                "player_self_service_reminder_autosave_edit_failed adjusted=%s",
                adjusted,
                exc_info=True,
            )
            await interaction.followup.send(content, view=self, ephemeral=True)

    @discord.ui.button(
        label="Remove All",
        style=discord.ButtonStyle.danger,
        custom_id="me:reminder:remove_all",
        row=2,
    )
    async def remove_all_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        if not self.can_unsubscribe:
            await interaction.response.send_message(
                "You are not currently subscribed to KVK event reminders.",
                ephemeral=True,
            )
            return
        await _defer_private(interaction)
        confirmation, error = await reminder_service.prepare_unsubscribe_confirmation(
            self.author_id,
        )
        if error or confirmation is None:
            await interaction.followup.send(
                error or "Could not prepare unsubscribe confirmation.",
                ephemeral=True,
            )
            return
        try:
            await interaction.edit_original_response(
                content=confirmation.body,
                embed=None,
                view=ReminderUnsubscribeConfirmView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    confirmation=confirmation,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                ),
            )
        except Exception:
            logger.debug("player_self_service_reminder_remove_all_edit_failed", exc_info=True)
            await interaction.followup.send(
                confirmation.body,
                view=ReminderUnsubscribeConfirmView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    confirmation=confirmation,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                ),
                ephemeral=True,
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


class ReminderUnsubscribeConfirmView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        confirmation: ReminderUnsubscribeConfirmation,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.confirmation = confirmation
        self.host_message = host_message
        self.summary_loader = summary_loader
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
        await _refresh_host_page(
            host_message=self.host_message,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        view = ReminderCompletionView(
            author_id=self.author_id,
            display_name=self.display_name,
            message=content,
            summary_loader=self.summary_loader,
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
        except asyncio.CancelledError:
            raise
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
            _build_page_response,
            _edit_original_with_image_fallback,
        )

        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=page,
            summary=summary,
            summary_loader=self.summary_loader,
        )
        embed, files = await _build_page_response(page, summary, display_name=self.display_name)
        edited = await _edit_original_with_image_fallback(
            interaction,
            page=page,
            summary=summary,
            display_name=self.display_name,
            view=view,
            embed=embed,
            files=files,
        )
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
