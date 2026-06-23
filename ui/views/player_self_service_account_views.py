"""Account-centre Discord components for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import Literal

import discord

from core.interaction_safety import send_or_followup
from player_self_service import account_service
from player_self_service.account_service import (
    AccountAction,
    AccountConfirmation,
    AccountSlot,
)
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)

logger = logging.getLogger(__name__)

SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]


def _account_option_label(slot: str | AccountSlot) -> str:
    if isinstance(slot, AccountSlot):
        return slot.label[:100]
    return str(slot)[:100]


def _account_option_description(slot: str | AccountSlot) -> str:
    if isinstance(slot, AccountSlot):
        return slot.description[:100]
    return "Available account slot"


class AccountSlotSelect(discord.ui.Select):
    def __init__(
        self,
        *,
        action: AccountAction,
        slots: tuple[str, ...] | tuple[AccountSlot, ...],
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> None:
        options = [
            discord.SelectOption(
                label=_account_option_label(slot),
                value=slot.slot if isinstance(slot, AccountSlot) else str(slot),
                description=_account_option_description(slot),
            )
            for slot in slots
        ]
        base_placeholder = {
            "register": "Choose an empty slot",
            "replace": "Choose a slot to replace",
            "remove": "Choose a slot to remove",
        }[action]
        placeholder = (
            f"{base_placeholder} ({chunk_index + 1}/{total_chunks})"
            if total_chunks > 1
            else base_placeholder
        )
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AccountSlotSelectView):
            await send_or_followup(
                interaction,
                "This account selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        await view.handle_slot(interaction, self.values[0])


class AccountSlotSelectView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        action: AccountAction,
        slots: tuple[str, ...] | tuple[AccountSlot, ...],
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.action = action
        slot_chunks = tuple(slots[index : index + 25] for index in range(0, len(slots), 25))
        total_chunks = len(slot_chunks)
        for index, chunk in enumerate(slot_chunks):
            self.add_item(
                AccountSlotSelect(
                    action=action,
                    slots=chunk,
                    chunk_index=index,
                    total_chunks=total_chunks,
                )
            )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private account menu is not for you.",
            ephemeral=True,
        )
        return False

    async def handle_slot(self, interaction: discord.Interaction, account_type: str) -> None:
        if self.action in {"register", "replace"}:
            await interaction.response.send_modal(
                AccountGovernorInputModal(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    action=self.action,
                    account_type=account_type,
                )
            )
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("player_self_service_remove_prepare_defer_failed", exc_info=True)
        confirmation, error = await account_service.prepare_remove_confirmation(
            self.author_id,
            account_type,
        )
        if error or confirmation is None:
            await interaction.followup.send(error or "Could not prepare removal.", ephemeral=True)
            return
        await interaction.followup.send(
            confirmation.body,
            view=AccountConfirmationView(
                author_id=self.author_id,
                display_name=self.display_name,
                confirmation=confirmation,
            ),
            ephemeral=True,
        )


class AccountLookupModal(discord.ui.Modal):
    def __init__(self, *, author_id: int) -> None:
        super().__init__(title="Find Governor ID")
        self.author_id = int(author_id)
        self.query = discord.ui.InputText(
            label="Governor name or partial ID",
            placeholder="Start typing the governor name",
            required=True,
            max_length=100,
        )
        self.add_item(self.query)

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user and int(interaction.user.id) != self.author_id:
            await interaction.response.send_message("This lookup is not for you.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        outcome = await account_service.lookup_governor(str(self.query.value))
        if outcome.status == "found":
            await interaction.followup.send(
                f"{outcome.governor_name or 'Governor'}: Governor ID `{outcome.governor_id}`",
                ephemeral=True,
            )
            return
        if outcome.status == "matches":
            lines = [
                f"- {match.get('GovernorName') or 'Unknown'}: `{match.get('GovernorID')}`"
                for match in outcome.matches[:8]
            ]
            await interaction.followup.send(
                "Possible matches:\n" + "\n".join(lines),
                ephemeral=True,
            )
            return
        await interaction.followup.send(outcome.message, ephemeral=True)


class AccountGovernorInputModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        action: Literal["register", "replace"],
        account_type: str,
    ) -> None:
        title = "Register account" if action == "register" else "Replace account"
        super().__init__(title=title)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.action = action
        self.account_type = account_type
        self.governor_query = discord.ui.InputText(
            label="Governor ID",
            placeholder="Enter the exact Governor ID",
            required=True,
            max_length=30,
        )
        self.add_item(self.governor_query)

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.user and int(interaction.user.id) != self.author_id:
            await interaction.response.send_message(
                "This account action is not for you.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        if self.action == "register":
            confirmation, error = await account_service.prepare_register_confirmation(
                self.author_id,
                self.account_type,
                str(self.governor_query.value),
            )
        else:
            confirmation, error = await account_service.prepare_replace_confirmation(
                self.author_id,
                self.account_type,
                str(self.governor_query.value),
            )
        if error or confirmation is None:
            await interaction.followup.send(
                error or "Could not prepare account action.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            confirmation.body,
            view=AccountConfirmationView(
                author_id=self.author_id,
                display_name=self.display_name,
                confirmation=confirmation,
            ),
            ephemeral=True,
        )


class AccountConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        confirmation: AccountConfirmation,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.confirmation = confirmation

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
        return False

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.danger,
        custom_id="me:account:confirm",
    )
    async def confirm_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("player_self_service_account_confirm_defer_failed", exc_info=True)
        discord_name = str(getattr(interaction, "user", "") or self.display_name)
        if self.confirmation.action == "register":
            result = await account_service.confirm_register(
                self.author_id,
                discord_name,
                self.confirmation,
            )
        elif self.confirmation.action == "replace":
            result = await account_service.confirm_replace(
                self.author_id,
                discord_name,
                self.confirmation,
            )
        else:
            result = await account_service.confirm_remove(self.author_id, self.confirmation)

        view = AccountCompletionView(
            author_id=self.author_id,
            display_name=self.display_name,
            message=result.message,
        )
        try:
            await interaction.edit_original_response(content=result.message, embed=None, view=view)
        except Exception:
            logger.debug("player_self_service_account_confirm_edit_failed", exc_info=True)
            await interaction.followup.send(result.message, view=view, ephemeral=True)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:cancel",
    )
    async def cancel_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.edit_message(
            content="Account action cancelled.",
            embed=None,
            view=AccountCompletionView(
                author_id=self.author_id,
                display_name=self.display_name,
                message="Account action cancelled.",
            ),
        )


class AccountCompletionView(discord.ui.View):
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
        try:
            await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                await interaction.response.defer()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug(
                    "player_self_service_account_completion_defer_failed user_id=%s page=%s",
                    self.author_id,
                    page,
                    exc_info=True,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug(
                "player_self_service_account_completion_defer_failed user_id=%s page=%s",
                self.author_id,
                page,
                exc_info=True,
            )
        try:
            summary = await self.summary_loader(self.author_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "player_self_service_account_completion_summary_failed user_id=%s page=%s",
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

    @discord.ui.button(label="Account Centre", style=discord.ButtonStyle.primary)
    async def accounts_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        from ui.views.player_self_service_views import PAGE_ACCOUNTS

        await self._show_page(interaction, PAGE_ACCOUNTS)

    @discord.ui.button(label="Dashboard", style=discord.ButtonStyle.secondary)
    async def dashboard_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        from ui.views.player_self_service_views import PAGE_DASHBOARD

        await self._show_page(interaction, PAGE_DASHBOARD)
