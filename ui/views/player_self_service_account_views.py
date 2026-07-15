"""Account-centre Discord components for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import Literal

import discord

from core.interaction_safety import send_or_followup
from player_self_service import account_service, accounts_service
from player_self_service.account_service import (
    AccountAction,
    AccountCentreState,
    AccountConfirmation,
    AccountSlot,
)
from player_self_service.accounts_models import AccountsPortfolioPayload
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)

logger = logging.getLogger(__name__)

SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]
AccountsLoader = Callable[[int], Awaitable[AccountsPortfolioPayload]]


def _account_option_label(slot: str | AccountSlot) -> str:
    if isinstance(slot, AccountSlot):
        return slot.label[:100]
    return str(slot)[:100]


def _account_option_description(slot: str | AccountSlot) -> str:
    if isinstance(slot, AccountSlot):
        return slot.description[:100]
    return "Available account slot"


def _lookup_match_label(match: dict[str, str]) -> str:
    name = str(match.get("GovernorName") or "Unknown").strip() or "Unknown"
    return name[:100]


def _lookup_match_description(match: dict[str, str]) -> str:
    governor_id = str(match.get("GovernorID") or "").strip()
    return f"Governor ID {governor_id}"[:100]


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
        governor_query: str | None = None,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.action = action
        self.governor_query = (governor_query or "").strip() or None
        self.host_message = host_message
        self.summary_loader = summary_loader
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
            if self.governor_query:
                await _prepare_account_confirmation(
                    interaction,
                    author_id=self.author_id,
                    display_name=self.display_name,
                    action=self.action,
                    account_type=account_type,
                    governor_query=self.governor_query,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                )
                return
            await interaction.response.send_modal(
                AccountGovernorInputModal(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    action=self.action,
                    account_type=account_type,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
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
                host_message=self.host_message,
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )


class AccountManageActionSelect(discord.ui.Select):
    def __init__(self, state: AccountCentreState) -> None:
        options: list[discord.SelectOption] = [
            discord.SelectOption(
                label="Find Governor ID",
                value="lookup",
                description="Search by full or partial governor name",
            )
        ]
        if state.can_register:
            options.append(
                discord.SelectOption(
                    label="Register account",
                    value="register",
                    description="Add a governor to an empty account slot",
                )
            )
        if state.can_modify:
            options.append(
                discord.SelectOption(
                    label="Replace account",
                    value="replace",
                    description="Choose an existing slot and a new Governor ID",
                )
            )
            options.append(
                discord.SelectOption(
                    label="Remove account",
                    value="remove",
                    description="Choose an existing slot to remove",
                )
            )
        super().__init__(
            placeholder="Choose account task",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AccountManageView):
            await send_or_followup(
                interaction,
                "This account menu is temporarily unavailable.",
                ephemeral=True,
            )
            return
        await view.handle_action(interaction, self.values[0])


class AccountManageView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        state: AccountCentreState,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.state = state
        self.host_message = host_message
        self.summary_loader = summary_loader
        self.add_item(AccountManageActionSelect(state))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private account menu is not for you.",
            ephemeral=True,
        )
        return False

    async def handle_action(self, interaction: discord.Interaction, action: str) -> None:
        if action == "lookup":
            await interaction.response.send_modal(
                AccountLookupModal(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                )
            )
            return
        await _defer_private(interaction)
        if action == "register":
            if not self.state.can_register:
                await interaction.followup.send(
                    "All account slots are already in use.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Choose the slot for the new account.",
                view=AccountSlotSelectView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    action="register",
                    slots=self.state.free_slots,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                ),
                ephemeral=True,
            )
            return
        if action == "replace":
            if not self.state.can_modify:
                await interaction.followup.send(
                    "You do not have any registered accounts to replace yet.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Choose the account slot to replace.",
                view=AccountSlotSelectView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    action="replace",
                    slots=self.state.registered_slots,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                ),
                ephemeral=True,
            )
            return
        if action == "remove":
            if not self.state.can_remove:
                await interaction.followup.send(
                    "You do not have any registered accounts to remove.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "Choose the account slot to remove.",
                view=AccountSlotSelectView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    action="remove",
                    slots=self.state.registered_slots,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                ),
                ephemeral=True,
            )
            return
        await interaction.followup.send("Unknown account task.", ephemeral=True)


class AccountLookupMatchSelect(discord.ui.Select):
    def __init__(self, matches: tuple[dict[str, str], ...]) -> None:
        options = [
            discord.SelectOption(
                label=_lookup_match_label(match),
                value=str(match.get("GovernorID") or ""),
                description=_lookup_match_description(match),
            )
            for match in matches[:25]
            if str(match.get("GovernorID") or "").strip()
        ]
        super().__init__(
            placeholder="Choose a lookup result",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.matches_by_id = {
            str(match.get("GovernorID") or "").strip(): str(match.get("GovernorName") or "Unknown")
            for match in matches[:25]
        }

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AccountLookupMatchesView):
            await send_or_followup(
                interaction,
                "This lookup result selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        governor_id = self.values[0]
        governor_name = self.matches_by_id.get(governor_id, "Governor")
        await interaction.response.edit_message(
            content=f"Selected {governor_name} (`{governor_id}`).",
            view=AccountLookupResultActionView(
                author_id=view.author_id,
                display_name=view.display_name,
                governor_id=governor_id,
                governor_name=governor_name,
                host_message=view.host_message,
                summary_loader=view.summary_loader,
            ),
        )


class AccountLookupMatchesView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        matches: tuple[dict[str, str], ...],
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.host_message = host_message
        self.summary_loader = summary_loader
        self.add_item(AccountLookupMatchSelect(matches))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This lookup is not for you.", ephemeral=True)
        return False


class AccountLookupResultActionView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        governor_id: str,
        governor_name: str | None,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.governor_id = str(governor_id)
        self.governor_name = governor_name or "Governor"
        self.host_message = host_message
        self.summary_loader = summary_loader

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This lookup is not for you.", ephemeral=True)
        return False

    async def _load_state(self, interaction: discord.Interaction) -> AccountCentreState | None:
        await _defer_private(interaction)
        try:
            state = await account_service.build_account_centre_state(self.author_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("player_self_service_lookup_state_failed user_id=%s", self.author_id)
            await interaction.followup.send(
                "Account data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None
        if not state.ok:
            await interaction.followup.send(
                "Account data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None
        return state

    async def _precheck_lookup_action(
        self,
        interaction: discord.Interaction,
        *,
        action: Literal["register", "replace"],
        account_type: str,
    ) -> bool:
        if action == "register":
            confirmation, error = await account_service.prepare_register_confirmation(
                self.author_id,
                account_type,
                self.governor_id,
            )
        else:
            confirmation, error = await account_service.prepare_replace_confirmation(
                self.author_id,
                account_type,
                self.governor_id,
            )
        if error or confirmation is None:
            await interaction.followup.send(
                error or "Could not prepare account action.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(
        label="Register",
        style=discord.ButtonStyle.success,
        custom_id="me:account:lookup:register",
    )
    async def register_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_state(interaction)
        if state is None:
            return
        if not state.can_register:
            await interaction.followup.send(
                "All account slots are already in use.",
                ephemeral=True,
            )
            return
        if not await self._precheck_lookup_action(
            interaction,
            action="register",
            account_type=str(state.free_slots[0]),
        ):
            return
        await interaction.followup.send(
            f"Choose where to register {self.governor_name} (`{self.governor_id}`).",
            view=AccountSlotSelectView(
                author_id=self.author_id,
                display_name=self.display_name,
                action="register",
                slots=state.free_slots,
                governor_query=self.governor_id,
                host_message=self.host_message,
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Replace",
        style=discord.ButtonStyle.primary,
        custom_id="me:account:lookup:replace",
    )
    async def replace_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_state(interaction)
        if state is None:
            return
        if not state.can_modify:
            await interaction.followup.send(
                "You do not have any registered accounts to replace yet.",
                ephemeral=True,
            )
            return
        if not await self._precheck_lookup_action(
            interaction,
            action="replace",
            account_type=state.registered_slots[0].slot,
        ):
            return
        await interaction.followup.send(
            f"Choose which slot to replace with {self.governor_name} (`{self.governor_id}`).",
            view=AccountSlotSelectView(
                author_id=self.author_id,
                display_name=self.display_name,
                action="replace",
                slots=state.registered_slots,
                governor_query=self.governor_id,
                host_message=self.host_message,
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )


class AccountLookupModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
    ) -> None:
        super().__init__(title="Find Governor ID")
        self.author_id = int(author_id)
        self.display_name = display_name
        self.host_message = host_message
        self.summary_loader = summary_loader
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
            result_view = None
            if outcome.governor_id:
                result_view = AccountLookupResultActionView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    governor_id=str(outcome.governor_id),
                    governor_name=outcome.governor_name,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                )
            await interaction.followup.send(
                f"{outcome.governor_name or 'Governor'}: Governor ID `{outcome.governor_id}`",
                view=result_view,
                ephemeral=True,
            )
            return
        if outcome.status == "matches":
            matches_with_ids = tuple(
                match for match in outcome.matches if str(match.get("GovernorID") or "").strip()
            )
            lines = [
                f"- {match.get('GovernorName') or 'Unknown'}: `{match.get('GovernorID')}`"
                for match in outcome.matches[:8]
            ]
            result_view = None
            if matches_with_ids:
                result_view = AccountLookupMatchesView(
                    author_id=self.author_id,
                    display_name=self.display_name,
                    matches=matches_with_ids,
                    host_message=self.host_message,
                    summary_loader=self.summary_loader,
                )
            await interaction.followup.send(
                "Possible matches:\n" + "\n".join(lines),
                view=result_view,
                ephemeral=True,
            )
            return
        await interaction.followup.send(outcome.message, ephemeral=True)


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
            logger.debug("player_self_service_account_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_account_defer_failed", exc_info=True)


async def _prepare_account_confirmation(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    action: Literal["register", "replace"],
    account_type: str,
    governor_query: str,
    host_message: object | None = None,
    summary_loader: SummaryLoader = build_player_self_service_summary,
) -> None:
    await _defer_private(interaction)
    if action == "register":
        confirmation, error = await account_service.prepare_register_confirmation(
            author_id,
            account_type,
            governor_query,
        )
    else:
        confirmation, error = await account_service.prepare_replace_confirmation(
            author_id,
            account_type,
            governor_query,
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
            author_id=author_id,
            display_name=display_name,
            confirmation=confirmation,
            host_message=host_message,
            summary_loader=summary_loader,
        ),
        ephemeral=True,
    )


async def _refresh_host_page(
    *,
    host_message: object | None,
    author_id: int,
    display_name: str,
    summary_loader: SummaryLoader,
    page: str,
    user: object | None = None,
) -> None:
    if host_message is None or not hasattr(host_message, "edit"):
        return
    from player_self_service.accounts_service import build_accounts_portfolio
    from ui.views.player_self_service_views import (
        PlayerSelfServiceView,
        _build_page_response,
        _close_files,
        _edit_original_with_image_fallback,
        _read_avatar_bytes,
    )

    files = []
    try:
        accounts_payload = await build_accounts_portfolio(int(author_id))
        avatar_bytes = await _read_avatar_bytes(user, expected_user_id=int(author_id))

        view = PlayerSelfServiceView(
            author_id=int(author_id),
            display_name=display_name,
            page=page,
            summary_loader=summary_loader,
            accounts_payload=accounts_payload,
            avatar_bytes=avatar_bytes,
        )
        embed, files = await _build_page_response(
            page,
            None,
            display_name=display_name,
            accounts_payload=accounts_payload,
            avatar_bytes=avatar_bytes,
        )

        class _MessageTarget:
            async def edit_original_response(self, **kwargs):
                return await host_message.edit(**kwargs)

        edited = await _edit_original_with_image_fallback(
            _MessageTarget(),
            page=page,
            summary=None,
            accounts_payload=accounts_payload,
            display_name=display_name,
            view=view,
            embed=embed,
            files=files,
        )
        view.set_message_ref(edited or host_message)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_account_host_refresh_failed", exc_info=True)
    finally:
        _close_files(files)


class AccountGovernorInputModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        action: Literal["register", "replace"],
        account_type: str,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
    ) -> None:
        title = "Register account" if action == "register" else "Replace account"
        super().__init__(title=title)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.action = action
        self.account_type = account_type
        self.host_message = host_message
        self.summary_loader = summary_loader
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

        await _prepare_account_confirmation(
            interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            action=self.action,
            account_type=self.account_type,
            governor_query=str(self.governor_query.value),
            host_message=self.host_message,
            summary_loader=self.summary_loader,
        )


class AccountConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        confirmation: AccountConfirmation,
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

        if result.ok:
            from ui.views.player_self_service_views import PAGE_ACCOUNTS

            await _refresh_host_page(
                host_message=self.host_message,
                author_id=self.author_id,
                display_name=self.display_name,
                summary_loader=self.summary_loader,
                page=PAGE_ACCOUNTS,
                user=getattr(interaction, "user", None),
            )

        view = AccountCompletionView(
            author_id=self.author_id,
            display_name=self.display_name,
            message=result.message,
            summary_loader=self.summary_loader,
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
        accounts_loader: AccountsLoader = accounts_service.build_accounts_portfolio,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.message = message
        self.summary_loader = summary_loader
        self.accounts_loader = accounts_loader

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
            accounts_loader=self.accounts_loader,
            timeout=self.timeout or 120,
        )

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
