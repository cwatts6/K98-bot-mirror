"""Discord views and embeds for the /me player command centre."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

from core.interaction_safety import safe_defer
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
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
                "Detailed register, modify, and remove flows stay in the existing account tools for this phase.",
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
                "Subscribe, update, and unsubscribe actions remain in the existing reminder tools for this phase.",
            ]
        ),
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
                "Preference writes stay in existing service-backed tools for this phase.",
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
        except Exception:
            logger.debug(
                "player_self_service_navigation_defer_failed user_id=%s page=%s",
                self.author_id,
                page,
                exc_info=True,
            )

        try:
            summary = await self.summary_loader(self.author_id)
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
        embed = build_page_embed(page, summary, display_name=self.display_name)
        try:
            edited = await interaction.edit_original_response(embed=embed, view=view)
            view.set_message_ref(getattr(interaction, "message", None) or edited)
        except Exception:
            logger.debug("player_self_service_edit_message_failed", exc_info=True)
            sent = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
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
            row=2,
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
    embed = build_page_embed(page, summary, display_name=display_name)
    message = await ctx.interaction.edit_original_response(embed=embed, view=view)
    view.set_message_ref(message)
