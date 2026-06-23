"""Discord views and embeds for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import Any

import discord

from core.interaction_safety import safe_defer
from inventory.models import InventoryReportVisibility
from player_self_service import (
    account_service,
    dashboard_card,
    preference_service,
    reminder_service,
)
from player_self_service.account_service import AccountCentreState
from player_self_service.reminder_service import ReminderCentreState
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)
from ui.views.player_self_service_account_views import (
    AccountLookupModal,
    AccountSlotSelectView,
)
from ui.views.player_self_service_reminder_views import (
    ReminderSetupView,
    ReminderUnsubscribeConfirmView,
)

logger = logging.getLogger(__name__)

PlayerSelfServicePage = str
SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]

PAGE_DASHBOARD = "dashboard"
PAGE_ACCOUNTS = "accounts"
PAGE_REMINDERS = "reminders"
PAGE_PREFERENCES = "preferences"
PAGE_EXPORTS = "exports"

_QUICK_LAUNCH_COPY = {
    "kvk_stats": ("KVK stats", "Use `/kvk stats` for the modern KVK stats view."),
    "kvk_targets": ("KVK targets", "Use `/kvk targets` for your target guidance."),
    "kvk_history": ("KVK history", "Use `/kvk history` for personal KVK history."),
    "kvk_rankings": ("KVK rankings", "Use `/kvk rankings` for KVK, honor, and records."),
    "inventory": ("Inventory", "Use `/myinventory` for your latest inventory report."),
}


def _display_name(user: object) -> str:
    return (
        str(getattr(user, "display_name", "") or "").strip()
        or str(getattr(user, "name", "") or "").strip()
        or "player"
    )


def _field_value(lines: list[str]) -> str:
    return "\n".join(lines)[:1024]


def build_dashboard_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    embed = discord.Embed(
        title="K98 Personal Command Centre",
        description=f"Private setup dashboard for {display_name}",
        color=discord.Color.blurple(),
    )
    accounts = summary.accounts
    reminders = summary.reminders
    preferences = summary.preferences

    embed.add_field(
        name="Accounts",
        value=_field_value(
            [
                f"Main: {accounts.main_state}",
                f"Linked: {accounts.linked_label}",
                f"Next action: {accounts.next_action}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Reminders",
        value=_field_value(
            [
                f"KVK reminders: {reminders.state}",
                f"Times: {reminders.time_summary}",
                f"Next action: {reminders.next_action}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Preferences",
        value=_field_value(
            [
                f"Inventory visibility: {preferences.inventory_visibility}",
                f"Exports: {preferences.exports_summary}",
                f"Next action: {preferences.next_action}",
            ]
        ),
        inline=False,
    )
    embed.set_footer(text="Private player setup. Legacy commands remain available.")
    return embed


def build_accounts_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    accounts = summary.accounts
    embed = discord.Embed(
        title="Account Centre",
        description=f"Private account status for {display_name}",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Current Status",
        value=_field_value(
            [
                f"Main: {accounts.main_label}",
                f"Linked accounts: {accounts.linked_count}",
                f"State: {accounts.state}",
            ]
        ),
        inline=False,
    )
    names = ", ".join(accounts.account_names[:5]) if accounts.account_names else "none shown"
    embed.add_field(
        name="Next Step",
        value=_field_value(
            [
                f"Recommended action: {accounts.next_action}",
                f"Account names: {names}",
                "Use the controls below to look up, register, replace, or remove accounts.",
            ]
        ),
        inline=False,
    )
    return embed


def build_reminders_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    reminders = summary.reminders
    embed = discord.Embed(
        title="Reminder Centre",
        description=f"Private KVK reminder status for {display_name}",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="Current Status",
        value=_field_value(
            [
                f"KVK reminders: {reminders.state}",
                f"Events: {reminders.event_summary}",
                f"Times: {reminders.time_summary}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Next Step",
        value=_field_value(
            [
                f"Recommended action: {reminders.next_action}",
                "Use the controls below to manage event types and reminder times.",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="DM Check",
        value="A confirmation DM is sent after changes. If it does not arrive, check server DM settings.",
        inline=False,
    )
    return embed


def build_preferences_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    preferences = summary.preferences
    embed = discord.Embed(
        title="Preferences",
        description=f"Private preference status for {display_name}",
        color=discord.Color.teal(),
    )
    embed.add_field(
        name="Current Status",
        value=_field_value(
            [
                f"Inventory visibility: {preferences.inventory_visibility}",
                f"Exports: {preferences.exports_summary}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Next Step",
        value=_field_value(
            [
                f"Recommended action: {preferences.next_action}",
                "Use the controls below to update inventory report visibility.",
            ]
        ),
        inline=False,
    )
    return embed


def build_exports_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    exports = summary.exports
    embed = discord.Embed(
        title="Exports",
        description=f"Private export guidance for {display_name}",
        color=discord.Color.dark_teal(),
    )
    embed.add_field(
        name="Available Paths",
        value=_field_value(
            [
                f"Stats: {exports.stats_export}",
                f"Inventory: {exports.inventory_export}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Privacy",
        value=exports.privacy_note,
        inline=False,
    )
    return embed


def build_page_embed(
    page: PlayerSelfServicePage,
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    if page == PAGE_ACCOUNTS:
        return build_accounts_embed(summary, display_name=display_name)
    if page == PAGE_REMINDERS:
        return build_reminders_embed(summary, display_name=display_name)
    if page == PAGE_PREFERENCES:
        return build_preferences_embed(summary, display_name=display_name)
    if page == PAGE_EXPORTS:
        return build_exports_embed(summary, display_name=display_name)
    return build_dashboard_embed(summary, display_name=display_name)


def _reset_files(files: list[discord.File] | None) -> None:
    for file in files or []:
        try:
            file.reset(seek=True)
        except Exception:
            logger.debug("player_self_service_file_reset_failed", exc_info=True)


async def _build_page_response(
    page: PlayerSelfServicePage,
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> tuple[discord.Embed, list[discord.File]]:
    embed = build_page_embed(page, summary, display_name=display_name)
    if page != PAGE_DASHBOARD:
        return embed, []

    try:
        rendered = await asyncio.to_thread(
            dashboard_card.render_dashboard_card,
            summary,
            display_name=display_name,
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_dashboard_card_render_failed user_id=%s",
            summary.discord_user_id,
        )
        return embed, []

    file = discord.File(rendered.image_bytes, filename=rendered.filename)
    embed.set_image(url=f"attachment://{rendered.filename}")
    return embed, [file]


def _edit_kwargs(
    *,
    embed: discord.Embed,
    view: discord.ui.View,
    files: list[discord.File],
) -> dict[str, object]:
    kwargs: dict[str, object] = {"embed": embed, "view": view, "attachments": []}
    if files:
        kwargs["files"] = files
    return kwargs


async def _edit_original_with_image_fallback(
    target: Any,
    *,
    page: PlayerSelfServicePage,
    summary: PlayerSelfServiceSummary,
    display_name: str,
    view: discord.ui.View,
    embed: discord.Embed,
    files: list[discord.File],
) -> object:
    try:
        return await target.edit_original_response(
            **_edit_kwargs(embed=embed, view=view, files=files)
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        if not files:
            raise
        logger.exception(
            "player_self_service_dashboard_card_send_failed user_id=%s",
            summary.discord_user_id,
        )
        fallback_embed = build_page_embed(page, summary, display_name=display_name)
        return await target.edit_original_response(
            embed=fallback_embed,
            view=view,
            attachments=[],
        )


class PlayerSelfServiceView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        page: PlayerSelfServicePage = PAGE_DASHBOARD,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.page = page
        self.summary_loader = summary_loader
        self.message: discord.Message | None = None
        self._apply_page_state()

    def set_message_ref(self, message: discord.Message | None) -> None:
        self.message = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This private menu is not for you.", ephemeral=True)
        return False

    def _apply_page_state(self) -> None:
        if self.page == PAGE_DASHBOARD:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and child.custom_id == "me:dashboard":
                    self.remove_item(child)
        if self.page != PAGE_ACCOUNTS:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:account:"
                ):
                    self.remove_item(child)
        if self.page != PAGE_REMINDERS:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:reminder:"
                ):
                    self.remove_item(child)
        if self.page != PAGE_PREFERENCES:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:preference:"
                ):
                    self.remove_item(child)
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = child.custom_id == f"me:{self.page}"
        if self.page == PAGE_DASHBOARD and not any(
            isinstance(child, PlayerSelfServiceQuickLaunchSelect) for child in self.children
        ):
            self.add_item(PlayerSelfServiceQuickLaunchSelect())

    async def _show_page(
        self, interaction: discord.Interaction, page: PlayerSelfServicePage
    ) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                await interaction.response.defer()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug(
                    "player_self_service_navigation_defer_failed user_id=%s page=%s",
                    self.author_id,
                    page,
                    exc_info=True,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug(
                "player_self_service_navigation_defer_failed user_id=%s page=%s",
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
                "player_self_service_view_summary_failed user_id=%s page=%s",
                self.author_id,
                page,
            )
            try:
                await interaction.followup.send(
                    "Personal status is temporarily unavailable. Please try again in a moment.",
                    ephemeral=True,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("player_self_service_view_error_followup_failed", exc_info=True)
            return

        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=page,
            summary_loader=self.summary_loader,
            timeout=self.timeout or 180,
        )
        embed, files = await _build_page_response(page, summary, display_name=self.display_name)
        try:
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
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_edit_message_failed", exc_info=True)
            _reset_files(files)
            sent = await interaction.followup.send(
                embed=build_page_embed(page, summary, display_name=self.display_name),
                view=view,
                ephemeral=True,
            )
            view.set_message_ref(sent)

    @discord.ui.button(label="Accounts", style=discord.ButtonStyle.primary, custom_id="me:accounts")
    async def accounts_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_ACCOUNTS)

    @discord.ui.button(
        label="Reminders",
        style=discord.ButtonStyle.primary,
        custom_id="me:reminders",
    )
    async def reminders_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_REMINDERS)

    @discord.ui.button(
        label="Preferences",
        style=discord.ButtonStyle.primary,
        custom_id="me:preferences",
    )
    async def preferences_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_PREFERENCES)

    @discord.ui.button(
        label="Dashboard",
        style=discord.ButtonStyle.secondary,
        custom_id="me:dashboard",
        row=1,
    )
    async def dashboard_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_DASHBOARD)

    async def _load_account_state(
        self, interaction: discord.Interaction
    ) -> AccountCentreState | None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer()
            except Exception:
                logger.debug("player_self_service_account_action_defer_failed", exc_info=True)
        except Exception:
            logger.debug("player_self_service_account_action_defer_failed", exc_info=True)

        try:
            state = await account_service.build_account_centre_state(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_account_state_failed user_id=%s page=%s",
                self.author_id,
                self.page,
            )
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

    @discord.ui.button(
        label="Find ID",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:lookup",
        row=1,
    )
    async def account_lookup_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.send_modal(AccountLookupModal(author_id=self.author_id))

    @discord.ui.button(
        label="Register",
        style=discord.ButtonStyle.success,
        custom_id="me:account:register",
        row=1,
    )
    async def account_register_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_account_state(interaction)
        if state is None:
            return
        if not state.can_register:
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
                slots=state.free_slots,
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Replace",
        style=discord.ButtonStyle.primary,
        custom_id="me:account:replace",
        row=2,
    )
    async def account_replace_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_account_state(interaction)
        if state is None:
            return
        if not state.can_modify:
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
                slots=state.registered_slots,
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Remove",
        style=discord.ButtonStyle.danger,
        custom_id="me:account:remove",
        row=2,
    )
    async def account_remove_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_account_state(interaction)
        if state is None:
            return
        if not state.can_remove:
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
                slots=state.registered_slots,
            ),
            ephemeral=True,
        )

    async def _load_reminder_state(
        self, interaction: discord.Interaction
    ) -> ReminderCentreState | None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer()
            except Exception:
                logger.debug("player_self_service_reminder_action_defer_failed", exc_info=True)
        except Exception:
            logger.debug("player_self_service_reminder_action_defer_failed", exc_info=True)

        try:
            state = await reminder_service.build_reminder_centre_state(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_reminder_state_failed user_id=%s page=%s",
                self.author_id,
                self.page,
            )
            await interaction.followup.send(
                "Reminder data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None

        if not state.ok:
            await interaction.followup.send(
                "Reminder data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None
        return state

    @discord.ui.button(
        label="Manage",
        style=discord.ButtonStyle.success,
        custom_id="me:reminder:manage",
        row=1,
    )
    async def reminder_manage_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_reminder_state(interaction)
        if state is None:
            return
        if not state.can_manage:
            await interaction.followup.send(
                "Reminder data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            "Choose your KVK event types and reminder times.",
            view=ReminderSetupView(
                author_id=self.author_id,
                username=str(getattr(interaction, "user", "") or self.display_name),
                state=state,
                display_name=self.display_name,
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Unsubscribe",
        style=discord.ButtonStyle.danger,
        custom_id="me:reminder:unsubscribe",
        row=2,
    )
    async def reminder_unsubscribe_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_reminder_state(interaction)
        if state is None:
            return
        if not state.can_unsubscribe:
            await interaction.followup.send(
                "You are not currently subscribed to KVK event reminders.",
                ephemeral=True,
            )
            return
        confirmation, error = await reminder_service.prepare_unsubscribe_confirmation(
            self.author_id,
        )
        if error or confirmation is None:
            await interaction.followup.send(
                error or "Could not prepare unsubscribe confirmation.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            confirmation.body,
            view=ReminderUnsubscribeConfirmView(
                author_id=self.author_id,
                display_name=self.display_name,
                confirmation=confirmation,
            ),
            ephemeral=True,
        )

    async def _save_inventory_visibility(
        self,
        interaction: discord.Interaction,
        visibility: InventoryReportVisibility,
    ) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer()
            except Exception:
                logger.debug("player_self_service_preference_defer_failed", exc_info=True)
        except Exception:
            logger.debug("player_self_service_preference_defer_failed", exc_info=True)

        result = await preference_service.save_inventory_visibility(
            self.author_id,
            visibility,
        )
        await interaction.followup.send(result.message, ephemeral=True)
        if not result.ok:
            return

        try:
            summary = await self.summary_loader(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_preference_refresh_failed user_id=%s",
                self.author_id,
            )
            return

        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=PAGE_PREFERENCES,
            summary_loader=self.summary_loader,
            timeout=self.timeout or 180,
        )
        embed = build_preferences_embed(summary, display_name=self.display_name)
        try:
            edited = await interaction.edit_original_response(
                embed=embed,
                view=view,
                attachments=[],
            )
            view.set_message_ref(getattr(interaction, "message", None) or edited)
        except Exception:
            logger.debug("player_self_service_preference_refresh_edit_failed", exc_info=True)

    @discord.ui.button(
        label="Set Private",
        style=discord.ButtonStyle.primary,
        custom_id="me:preference:private",
        row=3,
    )
    async def preference_private_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._save_inventory_visibility(interaction, InventoryReportVisibility.ONLY_ME)

    @discord.ui.button(
        label="Set Public",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:public",
        row=3,
    )
    async def preference_public_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._save_inventory_visibility(interaction, InventoryReportVisibility.PUBLIC)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            logger.debug("player_self_service_timeout_edit_failed", exc_info=True)


class PlayerSelfServiceQuickLaunchSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="KVK stats", value="kvk_stats"),
            discord.SelectOption(label="KVK targets", value="kvk_targets"),
            discord.SelectOption(label="KVK history", value="kvk_history"),
            discord.SelectOption(label="KVK rankings", value="kvk_rankings"),
            discord.SelectOption(label="Inventory", value="inventory"),
            discord.SelectOption(label="Exports", value=PAGE_EXPORTS),
        ]
        super().__init__(
            placeholder="Quick launch",
            min_values=1,
            max_values=1,
            options=options,
            row=4,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, PlayerSelfServiceView):
            await interaction.response.send_message(
                "This launcher is temporarily unavailable.",
                ephemeral=True,
            )
            return

        value = self.values[0]
        if value == PAGE_EXPORTS:
            await view._show_page(interaction, PAGE_EXPORTS)
            return

        label, copy = _QUICK_LAUNCH_COPY[value]
        await interaction.response.send_message(
            f"{label}: {copy} Existing channel and visibility rules still apply.",
            ephemeral=True,
        )


async def send_player_self_service_page(
    ctx: discord.ApplicationContext,
    *,
    page: PlayerSelfServicePage = PAGE_DASHBOARD,
    summary_loader: SummaryLoader = build_player_self_service_summary,
) -> None:
    await safe_defer(ctx, ephemeral=True)
    display_name = _display_name(getattr(ctx, "user", None))
    try:
        summary = await summary_loader(int(ctx.user.id))
    except Exception:
        logger.exception(
            "player_self_service_initial_summary_failed user_id=%s page=%s",
            getattr(getattr(ctx, "user", None), "id", None),
            page,
        )
        try:
            await ctx.interaction.edit_original_response(
                content="Personal status is temporarily unavailable. Please try again in a moment.",
                embed=None,
                view=None,
            )
        except Exception:
            logger.debug("player_self_service_initial_error_edit_failed", exc_info=True)
            await ctx.followup.send(
                "Personal status is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
        return

    view = PlayerSelfServiceView(
        author_id=int(ctx.user.id),
        display_name=display_name,
        page=page,
        summary_loader=summary_loader,
    )
    embed, files = await _build_page_response(page, summary, display_name=display_name)
    message = await _edit_original_with_image_fallback(
        ctx.interaction,
        page=page,
        summary=summary,
        display_name=display_name,
        view=view,
        embed=embed,
        files=files,
    )
    view.set_message_ref(message)
