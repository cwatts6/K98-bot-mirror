"""Reminder-centre Discord components for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import Any

import discord

from constants import DEFAULT_REMINDER_TIMES, VALID_TYPES
from event_calendar import reminder_config_service
from event_calendar.reminder_prefs_store import get_user_prefs
from event_calendar.reminder_types import REMINDER_OFFSETS_ORDERED
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


def _normalize_calendar_types(selected: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(sorted({str(value).strip().lower() for value in selected if str(value).strip()}))
    if "all" in values:
        return ("all",)
    return values


def _calendar_event_options(
    *,
    known_event_types: tuple[str, ...],
    selected: tuple[str, ...],
) -> list[discord.SelectOption]:
    selected_set = set(selected)
    event_types = ("all", *tuple(sorted(set(known_event_types) | (selected_set - {"all"}))))
    return [
        discord.SelectOption(
            label=event_type,
            value=event_type,
            description=(
                "Every calendar event"
                if event_type == "all"
                else f"{event_type.title()} calendar events"
            ),
            default=event_type in selected_set,
        )
        for event_type in event_types[:25]
    ]


def _calendar_time_options(selected: tuple[str, ...]) -> list[discord.SelectOption]:
    selected_set = set(selected)
    return [
        discord.SelectOption(
            label=offset,
            value=offset,
            description=f"{offset.upper()} lead time",
            default=offset in selected_set,
        )
        for offset in REMINDER_OFFSETS_ORDERED
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


class CalendarReminderEventSelect(discord.ui.Select):
    def __init__(
        self,
        *,
        known_event_types: tuple[str, ...],
        selected: tuple[str, ...],
    ) -> None:
        options = _calendar_event_options(
            known_event_types=known_event_types,
            selected=selected,
        )
        super().__init__(
            placeholder="Choose calendar event types",
            min_values=1,
            max_values=len(options),
            options=options,
            row=0,
        )
        self.known_event_types = tuple(known_event_types)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, CalendarReminderSetupView):
            await interaction.response.send_message(
                "This calendar reminder selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        selected_types = _normalize_calendar_types(tuple(self.values))
        view.selected_types = list(selected_types)
        self.options = _calendar_event_options(
            known_event_types=tuple(view.known_event_types),
            selected=selected_types,
        )
        await view.autosave_selection(interaction)


class CalendarReminderTimeSelect(discord.ui.Select):
    def __init__(self, *, selected: tuple[str, ...]) -> None:
        super().__init__(
            placeholder="Choose calendar lead times",
            min_values=1,
            max_values=len(REMINDER_OFFSETS_ORDERED),
            options=_calendar_time_options(selected),
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, CalendarReminderSetupView):
            await interaction.response.send_message(
                "This calendar reminder selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        view.selected_offsets = [str(value).strip().lower() for value in self.values]
        await view.autosave_selection(interaction)


class CalendarReminderSetupView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        username: str,
        display_name: str,
        state: reminder_config_service.CalendarReminderConfigState,
        known_event_types: tuple[str, ...],
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 180,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.username = username
        self.display_name = display_name
        self.host_message = host_message
        self.summary_loader = summary_loader
        self.known_event_types = tuple(sorted({t for t in known_event_types if t}))
        self.selected_types = list(state.selected_types)
        self.selected_offsets = list(state.selected_offsets or REMINDER_OFFSETS_ORDERED)
        self._message_ref: Any | None = None
        self._saving = False
        self.add_item(
            CalendarReminderEventSelect(
                known_event_types=self.known_event_types,
                selected=tuple(self.selected_types),
            )
        )
        self.add_item(CalendarReminderTimeSelect(selected=tuple(self.selected_offsets)))

    def set_message_ref(self, message: Any | None) -> None:
        self._message_ref = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private calendar reminder menu is not for you.",
            ephemeral=True,
        )
        return False

    async def on_timeout(self) -> None:
        await super().on_timeout()
        try:
            if self._message_ref is not None:
                await self._message_ref.edit(
                    content="This private calendar reminder menu has expired. Run `/me reminders` again.",
                    view=self,
                )
        except Exception:
            logger.debug("player_self_service_calendar_reminder_timeout_edit_failed", exc_info=True)

    async def autosave_selection(self, interaction: discord.Interaction) -> None:
        if self._saving:
            await interaction.response.defer()
            return
        self._saving = True
        await _defer_private(interaction)

        result = reminder_config_service.save_user_calendar_reminder_preferences(
            self.author_id,
            enabled=True,
            selected_types=self.selected_types,
            selected_offsets=self.selected_offsets,
            known_event_types=self.known_event_types,
        )
        if not result.ok:
            self._saving = False
            await interaction.followup.send(result.message, ephemeral=True)
            return

        if result.state is not None:
            self.selected_types = list(result.state.selected_types)
            self.selected_offsets = list(result.state.selected_offsets)
        for child in self.children:
            if isinstance(child, CalendarReminderEventSelect):
                child.options = _calendar_event_options(
                    known_event_types=self.known_event_types,
                    selected=tuple(self.selected_types),
                )
            if isinstance(child, CalendarReminderTimeSelect):
                child.options = _calendar_time_options(tuple(self.selected_offsets))

        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        self._saving = False
        content = "Calendar reminders saved automatically."
        try:
            await interaction.edit_original_response(content=content, embed=None, view=self)
        except Exception:
            logger.debug(
                "player_self_service_calendar_reminder_autosave_edit_failed", exc_info=True
            )
            await interaction.followup.send(content, view=self, ephemeral=True)

    @discord.ui.button(
        label="Manage KVK Reminders",
        style=discord.ButtonStyle.secondary,
        custom_id="me:reminder:manage_kvk",
        row=2,
    )
    async def manage_kvk_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await _defer_private(interaction)
        try:
            state = await reminder_service.build_reminder_centre_state(self.author_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "player_self_service_calendar_to_kvk_state_failed user_id=%s",
                self.author_id,
            )
            await interaction.followup.send(
                "KVK reminder preferences are temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return

        view = ReminderSetupView(
            author_id=self.author_id,
            username=self.username,
            state=state,
            display_name=self.display_name,
            host_message=self.host_message,
            summary_loader=self.summary_loader,
        )
        try:
            await interaction.edit_original_response(
                content="Choose KVK event types and reminder times.",
                embed=None,
                view=view,
            )
            view.set_message_ref(getattr(interaction, "message", None))
        except Exception:
            logger.debug("player_self_service_calendar_to_kvk_edit_failed", exc_info=True)
            sent = await interaction.followup.send(
                "Choose KVK event types and reminder times.",
                view=view,
                ephemeral=True,
            )
            view.set_message_ref(sent)

    @discord.ui.button(
        label="Remove All",
        style=discord.ButtonStyle.danger,
        custom_id="me:reminder:calendar_remove_all",
        row=2,
    )
    async def remove_all_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await _defer_private(interaction)
        result = reminder_config_service.clear_user_calendar_reminder_preferences(self.author_id)
        if not result.ok:
            await interaction.followup.send(result.message, ephemeral=True)
            return

        self.selected_types = []
        self.selected_offsets = list(REMINDER_OFFSETS_ORDERED)
        for child in self.children:
            if isinstance(child, CalendarReminderEventSelect):
                child.options = _calendar_event_options(
                    known_event_types=self.known_event_types,
                    selected=tuple(),
                )
            if isinstance(child, CalendarReminderTimeSelect):
                child.options = _calendar_time_options(tuple(self.selected_offsets))
        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        try:
            await interaction.edit_original_response(
                content="Calendar reminders removed.",
                embed=None,
                view=self,
            )
        except Exception:
            logger.debug("player_self_service_calendar_remove_all_edit_failed", exc_info=True)
            await interaction.followup.send(
                "Calendar reminders removed.", view=self, ephemeral=True
            )


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
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.username = username
        self.display_name = display_name
        self.host_message = host_message
        self._message_ref: Any | None = None
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

    def set_message_ref(self, message: Any | None) -> None:
        self._message_ref = message
        if message is not None and hasattr(message, "flags") and hasattr(message, "channel"):
            try:
                self._message = message
            except Exception:
                logger.debug(
                    "player_self_service_reminder_internal_message_ref_failed",
                    exc_info=True,
                )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private reminder menu is not for you.",
            ephemeral=True,
        )
        return False

    async def on_timeout(self) -> None:
        await super().on_timeout()
        try:
            if self._message_ref is not None:
                await self._message_ref.edit(
                    content="This private reminder menu has expired. Run `/me reminders` again.",
                    view=self,
                )
        except Exception:
            logger.debug("player_self_service_reminder_timeout_edit_failed", exc_info=True)

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
        label="Manage Calendar Reminders",
        style=discord.ButtonStyle.secondary,
        custom_id="me:reminder:manage_calendar",
        row=2,
    )
    async def manage_calendar_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await _defer_private(interaction)
        known_types = list(reminder_config_service.known_calendar_event_types())
        if not known_types:
            known_types = ["all"]
        try:
            prefs = get_user_prefs(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_calendar_reminder_prefs_load_failed user_id=%s",
                self.author_id,
            )
            await interaction.followup.send(
                "Calendar reminder preferences are temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return

        calendar_state = reminder_config_service.state_from_prefs(prefs)
        config_view = CalendarReminderSetupView(
            author_id=self.author_id,
            username=self.username,
            display_name=self.display_name,
            state=calendar_state,
            known_event_types=tuple(
                event_type for event_type in known_types if event_type != "all"
            ),
            host_message=self.host_message,
            summary_loader=self.summary_loader,
        )
        try:
            await interaction.edit_original_response(
                content="Choose calendar reminder event types and lead times.",
                embed=None,
                view=config_view,
            )
            config_view.set_message_ref(getattr(interaction, "message", None))
        except Exception:
            logger.debug("player_self_service_reminder_calendar_switch_failed", exc_info=True)
            sent = await interaction.followup.send(
                "Choose calendar reminder event types and lead times.",
                view=config_view,
                ephemeral=True,
            )
            config_view.set_message_ref(sent)

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
        from ui.views.player_self_service_views import (
            show_player_self_service_page_for_interaction,
        )

        await show_player_self_service_page_for_interaction(
            interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            page=page,
            summary_loader=self.summary_loader,
            timeout=self.timeout or 120,
        )

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
