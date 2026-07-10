"""Discord views and embeds for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from types import SimpleNamespace
from typing import Any

import discord

from core.interaction_safety import safe_defer
from inventory import reporting_service
from inventory.models import InventoryReportVisibility
from player_self_service import (
    account_service,
    dashboard_card,
    page_cards,
    preference_service,
    profile_preference_service,
    reminder_service,
)
from player_self_service.account_service import AccountCentreState
from player_self_service.reminder_service import ReminderCentreState
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)
from ui.views import player_self_service_export_views as export_views
from ui.views.inventory_report_views import (
    send_inventory_preference_prompt,
    send_inventory_vip_preference_prompt,
    start_myinventory_command,
)
from ui.views.player_self_service_account_views import AccountManageView
from ui.views.player_self_service_preference_views import ProfilePreferenceManageView
from ui.views.player_self_service_reminder_views import (
    ReminderSetupView,
)

logger = logging.getLogger(__name__)

PlayerSelfServicePage = str
SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]

PAGE_DASHBOARD = "dashboard"
PAGE_ACCOUNTS = "accounts"
PAGE_REMINDERS = "reminders"
PAGE_PREFERENCES = "preferences"
PAGE_EXPORTS = "exports"
PAGE_INVENTORY = "inventory"


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
                f"Calendar reminders: {reminders.calendar.state}",
                f"KVK times: {reminders.time_summary}",
                f"Calendar lead times: {reminders.calendar.time_summary}",
                f"Next action: {reminders.combined_next_action}",
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


def build_dashboard_card_embed(filename: str) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.blurple())
    embed.set_image(url=f"attachment://{filename}")
    return embed


def build_card_embed(filename: str) -> discord.Embed:
    return build_dashboard_card_embed(filename)


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
        name="Available Actions",
        value=_field_value(
            [
                f"Account names: {names}",
                "Use Manage to look up IDs, add governors to open slots, replace, or remove accounts.",
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
                f"Calendar reminders: {reminders.calendar.state}",
                f"Calendar events: {reminders.calendar.event_summary}",
                f"Calendar lead times: {reminders.calendar.time_summary}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Available Actions",
        value=_field_value(
            [
                "Manage auto-saves KVK event type and reminder time changes.",
                "Manage Calendar Reminders switches to calendar event types and lead times.",
                "Remove All unsubscribes from KVK event reminders.",
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
                f"VIP levels: {preferences.vip_summary}",
                f"Timezone: {preferences.timezone}",
                f"Location: {preferences.location_country}",
                f"Language: {preferences.preferred_language}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Available Actions",
        value=_field_value(
            [
                "Use the visibility toggle to choose how inventory reports are posted.",
                "Use Update VIP to keep inventory capacity assumptions accurate.",
                "Use Manage Profile to save timezone, country, and language.",
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
        description=f"Private exports for {display_name}",
        color=discord.Color.dark_teal(),
    )
    embed.add_field(
        name="Status",
        value=_field_value(
            [
                f"Stats: {exports.stats_export}",
                f"Inventory: {exports.inventory_export}",
                f"Delivery: {exports.privacy_note}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Actions",
        value=_field_value(
            ["Export Stats", "Export Inventory"]
            if exports.action_state.strip().lower() == "actionable"
            else [exports.action_summary]
        ),
        inline=False,
    )
    return embed


def build_inventory_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    inventory = summary.inventory
    embed = discord.Embed(
        title="Inventory",
        description=f"Private inventory summary for {display_name}",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Latest Approved Data",
        value=_field_value(
            [
                f"Resources: {inventory.resources.value} ({inventory.resources.detail})",
                f"Speedups: {inventory.speedups.value} ({inventory.speedups.detail})",
                f"Materials: {inventory.materials.value} ({inventory.materials.detail})",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Status",
        value=_field_value([inventory.account_summary, inventory.upload_guidance]),
        inline=False,
    )
    embed.add_field(
        name="Actions",
        value="Open Report shows the report picker with ranges and export buttons.",
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
    if page == PAGE_INVENTORY:
        return build_inventory_embed(summary, display_name=display_name)
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
    fallback_embed = build_page_embed(page, summary, display_name=display_name)
    try:
        if page == PAGE_DASHBOARD:
            rendered = await asyncio.to_thread(
                dashboard_card.render_dashboard_card,
                summary,
                display_name=display_name,
            )
        else:
            rendered = await asyncio.to_thread(
                page_cards.render_page_card,
                page,
                summary,
                display_name=display_name,
            )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_card_render_failed user_id=%s page=%s",
            summary.discord_user_id,
            page,
        )
        return fallback_embed, []

    file = discord.File(rendered.image_bytes, filename=rendered.filename)
    embed = (
        build_dashboard_card_embed(rendered.filename)
        if page == PAGE_DASHBOARD
        else build_card_embed(rendered.filename)
    )
    return embed, [file]


def _edit_kwargs(
    *,
    embed: discord.Embed,
    view: discord.ui.View,
    files: list[discord.File],
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "content": None,
        "embed": embed,
        "view": view,
        "attachments": [],
    }
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
    except discord.NotFound:
        raise
    except asyncio.CancelledError:
        raise
    except Exception:
        if not files:
            raise
        logger.exception(
            "player_self_service_card_send_failed user_id=%s page=%s",
            summary.discord_user_id,
            page,
        )
        fallback_embed = build_page_embed(page, summary, display_name=display_name)
        return await target.edit_original_response(
            content=None,
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
        summary: PlayerSelfServiceSummary | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.page = page
        self.summary = summary
        self.summary_loader = summary_loader
        self._message_ref: discord.Message | None = None
        self._expired = False
        self._apply_page_state()

    def set_message_ref(self, message: discord.Message | None) -> None:
        self._message_ref = message
        if message is not None and hasattr(message, "flags") and hasattr(message, "channel"):
            try:
                self._message = message
            except Exception:
                logger.debug("player_self_service_internal_message_ref_failed", exc_info=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._expired:
            await interaction.response.send_message(
                "This private menu has expired. Run `/me dashboard` again.",
                ephemeral=True,
            )
            return False
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This private menu is not for you.", ephemeral=True)
        return False

    def _apply_page_state(self) -> None:
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
        if self.page != PAGE_EXPORTS:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:export:"
                ):
                    self.remove_item(child)
        if self.page != PAGE_INVENTORY:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:inventory:"
                ):
                    self.remove_item(child)
        if self.page == PAGE_PREFERENCES:
            self._apply_preference_toggle_state()
        if self.page == PAGE_EXPORTS:
            self._apply_export_button_state()
        self._apply_visible_action_rows()
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if str(child.custom_id or "").startswith("me:export:"):
                    continue
                child.disabled = child.custom_id == f"me:{self.page}"

    def _apply_visible_action_rows(self) -> None:
        action_prefixes = (
            "me:account:",
            "me:reminder:",
            "me:preference:",
            "me:export:",
            "me:inventory:",
        )
        for child in self.children:
            if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                action_prefixes
            ):
                child.row = 2

    def _apply_preference_toggle_state(self) -> None:
        visibility = ""
        if self.summary is not None:
            visibility = self.summary.preferences.inventory_visibility.strip().lower()
        for child in self.children:
            if (
                isinstance(child, discord.ui.Button)
                and child.custom_id == "me:preference:visibility"
            ):
                if visibility == "private":
                    child.label = "Set Public"
                    child.style = discord.ButtonStyle.success
                elif visibility == "public":
                    child.label = "Set Private"
                    child.style = discord.ButtonStyle.success
                elif visibility == "unknown":
                    child.label = "Set Visibility"
                    child.style = discord.ButtonStyle.success
                    child.disabled = True
                else:
                    child.label = "Set Private"
                    child.style = discord.ButtonStyle.success

    def _apply_export_button_state(self) -> None:
        action_state = ""
        if self.summary is not None:
            action_state = self.summary.exports.action_state.strip().lower()
        disabled = action_state != "actionable"
        for child in self.children:
            if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                "me:export:"
            ):
                child.disabled = disabled

    async def _show_page(
        self,
        interaction: discord.Interaction,
        page: PlayerSelfServicePage,
        *,
        can_edit: Callable[[], bool] | None = None,
    ) -> bool:
        if page == PAGE_DASHBOARD:
            from ui.views.player_self_service_governor_dashboard_views import (
                show_governor_dashboard_for_interaction,
            )

            await show_governor_dashboard_for_interaction(
                interaction,
                author_id=self.author_id,
                display_name=self.display_name,
                summary_loader=self.summary_loader,
                timeout=self.timeout or 180,
            )
            return True
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
            return False

        if can_edit is not None and not can_edit():
            logger.info(
                "player_self_service_stale_navigation_suppressed user_id=%s page=%s",
                self.author_id,
                page,
            )
            return False

        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=page,
            summary=summary,
            summary_loader=self.summary_loader,
            timeout=self.timeout or 180,
        )
        embed, files = await _build_page_response(page, summary, display_name=self.display_name)
        if can_edit is not None and not can_edit():
            logger.info(
                "player_self_service_stale_navigation_render_suppressed user_id=%s page=%s",
                self.author_id,
                page,
            )
            return False
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
            return True
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_edit_message_failed", exc_info=True)
            if can_edit is not None and not can_edit():
                return False
            _reset_files(files)
            sent = await interaction.followup.send(
                embed=build_page_embed(page, summary, display_name=self.display_name),
                view=view,
                ephemeral=True,
            )
            view.set_message_ref(sent)
            return True

    @discord.ui.button(
        label="Accounts",
        style=discord.ButtonStyle.primary,
        custom_id="me:accounts",
        row=0,
    )
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
        row=0,
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
        row=0,
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

    @discord.ui.button(
        label="Inventory",
        style=discord.ButtonStyle.secondary,
        custom_id="me:inventory",
        row=1,
    )
    async def dashboard_inventory_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_INVENTORY)

    @discord.ui.button(
        label="Exports",
        style=discord.ButtonStyle.secondary,
        custom_id="me:exports",
        row=1,
    )
    async def dashboard_exports_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_EXPORTS)

    @discord.ui.button(
        label="Export Stats",
        style=discord.ButtonStyle.success,
        custom_id="me:export:stats",
        row=2,
    )
    async def export_stats_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await export_views.send_stats_export_options(
            interaction,
            display_name=self.display_name,
        )

    @discord.ui.button(
        label="Export Inventory",
        style=discord.ButtonStyle.success,
        custom_id="me:export:inventory",
        row=2,
    )
    async def export_inventory_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await export_views.send_inventory_export_options(
            interaction,
            display_name=self.display_name,
        )

    @discord.ui.button(
        label="Open Report",
        style=discord.ButtonStyle.success,
        custom_id="me:inventory:report",
        row=2,
    )
    async def inventory_report_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_inventory_report_options(interaction)

    async def _show_inventory_report_options(self, interaction: discord.Interaction) -> None:
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
                logger.debug("player_self_service_inventory_defer_failed", exc_info=True)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_inventory_defer_failed", exc_info=True)

        ctx_adapter: Any = SimpleNamespace(user=interaction.user, followup=interaction.followup)
        try:
            visibility = await reporting_service.get_visibility_preference_or_none(self.author_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "player_self_service_inventory_visibility_failed user_id=%s",
                self.author_id,
            )
            await interaction.followup.send(
                "Inventory reporting preferences are not available yet. Please contact an admin.",
                ephemeral=True,
            )
            return

        if visibility is None:
            await send_inventory_preference_prompt(ctx_adapter)
            return

        try:
            await start_myinventory_command(ctx=ctx_adapter, visibility=visibility)
        except PermissionError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
        except ValueError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "player_self_service_inventory_report_failed user_id=%s",
                self.author_id,
            )
            await interaction.followup.send(
                "Inventory report generation failed. Please try again or contact an admin.",
                ephemeral=True,
            )

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
        label="Manage",
        style=discord.ButtonStyle.success,
        custom_id="me:account:manage",
        row=3,
    )
    async def account_manage_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_account_state(interaction)
        if state is None:
            return
        await interaction.followup.send(
            "Choose what you want to manage.",
            view=AccountManageView(
                author_id=self.author_id,
                display_name=self.display_name,
                state=state,
                host_message=getattr(interaction, "message", None),
                summary_loader=self.summary_loader,
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
        row=3,
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
        setup_view = ReminderSetupView(
            author_id=self.author_id,
            username=str(getattr(interaction, "user", "") or self.display_name),
            state=state,
            display_name=self.display_name,
            host_message=getattr(interaction, "message", None),
            summary_loader=self.summary_loader,
        )
        sent = await interaction.followup.send(
            "Choose KVK event types and times, or switch to calendar reminder management.",
            view=setup_view,
            ephemeral=True,
        )
        setup_view.set_message_ref(sent)

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
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("player_self_service_preference_defer_failed", exc_info=True)
        except asyncio.CancelledError:
            raise
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
        except asyncio.CancelledError:
            raise
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
            summary=summary,
            summary_loader=self.summary_loader,
            timeout=self.timeout or 180,
        )
        embed, files = await _build_page_response(
            PAGE_PREFERENCES,
            summary,
            display_name=self.display_name,
        )
        try:
            edited = await _edit_original_with_image_fallback(
                interaction,
                page=PAGE_PREFERENCES,
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
            logger.debug("player_self_service_preference_refresh_edit_failed", exc_info=True)

    @discord.ui.button(
        label="Set Visibility",
        style=discord.ButtonStyle.success,
        custom_id="me:preference:visibility",
        row=4,
    )
    async def preference_visibility_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        visibility = ""
        if self.summary is not None:
            visibility = self.summary.preferences.inventory_visibility.strip().lower()
        target = (
            InventoryReportVisibility.PUBLIC
            if visibility == "private"
            else InventoryReportVisibility.ONLY_ME
        )
        await self._save_inventory_visibility(interaction, target)

    @discord.ui.button(
        label="Update VIP",
        style=discord.ButtonStyle.success,
        custom_id="me:preference:vip",
        row=4,
    )
    async def preference_vip_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
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
                logger.debug("player_self_service_preference_vip_defer_failed", exc_info=True)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_preference_vip_defer_failed", exc_info=True)

        await send_inventory_vip_preference_prompt(
            interaction=interaction,
            requester_id=self.author_id,
        )

    @discord.ui.button(
        label="Manage Profile",
        style=discord.ButtonStyle.success,
        custom_id="me:preference:profile",
        row=4,
    )
    async def preference_profile_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
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
                logger.debug("player_self_service_preference_profile_defer_failed", exc_info=True)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_preference_profile_defer_failed", exc_info=True)

        result = await profile_preference_service.read_user_profile_preference(self.author_id)
        if not result.ok:
            await interaction.followup.send(
                "Profile preferences are temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            "\n".join(result.profile.summary_lines),
            view=ProfilePreferenceManageView(
                author_id=self.author_id,
                display_name=self.display_name,
                profile=result.profile,
                host_message=getattr(interaction, "message", None),
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )

    async def on_timeout(self) -> None:
        self._expired = True
        for child in self.children:
            child.disabled = True
        message = self._message_ref or getattr(self, "message", None)
        try:
            if message:
                await message.edit(
                    content="This private /me menu has expired. Run `/me dashboard` again.",
                    view=self,
                )
        except Exception:
            logger.debug("player_self_service_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


async def show_player_self_service_page_for_interaction(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    page: PlayerSelfServicePage,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    timeout: float = 180,
    can_edit: Callable[[], bool] | None = None,
) -> bool:
    """Open an existing Discord-user-level ``/me`` page in the current message."""
    router = PlayerSelfServiceView(
        author_id=author_id,
        display_name=display_name,
        page=page,
        summary_loader=summary_loader,
        timeout=timeout,
    )
    return await router._show_page(interaction, page, can_edit=can_edit)


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
        summary=summary,
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
