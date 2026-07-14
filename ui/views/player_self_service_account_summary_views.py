"""Private paginated Account Summary controls for the /me Accounts centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from io import BytesIO
import logging

import discord

from player_self_service import accounts_export, accounts_renderer, accounts_service
from player_self_service.accounts_models import (
    AccountsPortfolioPayload,
    AccountSummaryPage,
    AccountSummarySection,
)
from player_self_service.service import PlayerSelfServiceSummary, build_player_self_service_summary

logger = logging.getLogger(__name__)

AccountsLoader = Callable[[int], Awaitable[AccountsPortfolioPayload]]
SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]


def build_account_summary_fallback(page: AccountSummaryPage) -> discord.Embed:
    """Build a concise same-payload fallback for the currently selected private page."""
    labels = {
        "overview": "Overview",
        "combat": "Combat & Participation",
        "economy": "Economy & Activity",
    }
    embed = discord.Embed(
        title=f"Account Summary • {labels[page.section]}",
        description=f"Private portfolio page {page.page}/{page.page_count}",
        color=discord.Color.blurple(),
    )
    for row in page.rows:
        if page.section == "combat":
            value = (
                f"KP {row.kill_points if row.kill_points is not None else '—'} • "
                f"T4+T5 {row.t4_t5_kills if row.t4_t5_kills is not None else '—'} • "
                f"Deads {row.deads if row.deads is not None else '—'} • "
                f"Helps {row.helps if row.helps is not None else '—'}"
            )
        elif page.section == "economy":
            value = (
                f"Gathered {row.rss_gathered if row.rss_gathered is not None else '—'} • "
                f"Assistance {row.rss_assistance if row.rss_assistance is not None else '—'} • "
                f"Current {row.rss_total if row.rss_total is not None else '—'} • "
                f"{row.data_state}"
            )
        else:
            location = (
                f"{row.location_x}:{row.location_y}"
                if row.location_x is not None and row.location_y is not None
                else "—"
            )
            value = (
                f"ID {row.governor_id or '—'} • {row.civilisation or '—'} • "
                f"CH {row.city_hall if row.city_hall is not None else '—'} • "
                f"Power {row.power if row.power is not None else '—'} • "
                f"Location {location} • {row.data_state}"
            )
        embed.add_field(name=f"{row.slot} • {row.display_name}", value=value[:1024], inline=False)
    if not page.rows:
        embed.description += "\nNo linked governors to show."
    embed.set_footer(text=f"Refreshed {page.payload.refreshed_at_utc:%H:%M UTC}")
    return embed


def _close_file(file: discord.File | None) -> None:
    if file is None:
        return
    try:
        file.close()
    except Exception:
        logger.debug("account_summary_file_close_failed", exc_info=True)
    stream = getattr(file, "fp", None)
    try:
        if stream is not None and not getattr(stream, "closed", False):
            stream.close()
    except Exception:
        logger.debug("account_summary_stream_close_failed", exc_info=True)


async def _render_summary(page: AccountSummaryPage, display_name: str) -> discord.File:
    rendered = await asyncio.to_thread(
        accounts_renderer.render_account_summary_card,
        page,
        display_name=display_name,
    )
    return discord.File(BytesIO(rendered.image_bytes), filename=rendered.filename)


class AccountSummaryView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        payload: AccountsPortfolioPayload,
        section: AccountSummarySection = "overview",
        page: int = 1,
        accounts_loader: AccountsLoader = accounts_service.build_accounts_portfolio,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        dashboard_governor_id: int | None = None,
        timeout: float = 180,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.payload = payload
        self.summary_page = accounts_service.build_account_summary_page(
            payload,
            section=section,
            page=page,
        )
        self.accounts_loader = accounts_loader
        self.summary_loader = summary_loader
        self.dashboard_governor_id = dashboard_governor_id
        self._apply_state()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private report is not for you.", ephemeral=True
        )
        return False

    def _apply_state(self) -> None:
        for child in self.children:
            custom_id = str(getattr(child, "custom_id", "") or "")
            if custom_id == f"me:account-summary:{self.summary_page.section}":
                child.disabled = True
            elif custom_id == "me:account-summary:previous":
                child.disabled = self.summary_page.page <= 1
            elif custom_id == "me:account-summary:next":
                child.disabled = self.summary_page.page >= self.summary_page.page_count
            elif custom_id == "me:account-summary:csv":
                child.disabled = not self.payload.rows

    async def _defer(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except TypeError:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

    async def _replace(
        self,
        interaction: discord.Interaction,
        *,
        section: AccountSummarySection,
        page: int,
    ) -> None:
        await self._defer(interaction)
        summary_page = accounts_service.build_account_summary_page(
            self.payload,
            section=section,
            page=page,
        )
        view = AccountSummaryView(
            author_id=self.author_id,
            display_name=self.display_name,
            payload=self.payload,
            section=summary_page.section,
            page=summary_page.page,
            accounts_loader=self.accounts_loader,
            summary_loader=self.summary_loader,
            dashboard_governor_id=self.dashboard_governor_id,
            timeout=self.timeout or 180,
        )
        file: discord.File | None = None
        try:
            try:
                file = await _render_summary(summary_page, self.display_name)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "account_summary_render_failed user_id=%s section=%s page=%s",
                    self.author_id,
                    section,
                    page,
                )
                await interaction.edit_original_response(
                    content=None,
                    embed=build_account_summary_fallback(summary_page),
                    view=view,
                    attachments=[],
                )
                return
            try:
                await interaction.edit_original_response(
                    content=None,
                    embed=None,
                    view=view,
                    attachments=[],
                    files=[file],
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "account_summary_delivery_failed user_id=%s section=%s page=%s",
                    self.author_id,
                    section,
                    page,
                )
                await interaction.edit_original_response(
                    content=None,
                    embed=build_account_summary_fallback(summary_page),
                    view=view,
                    attachments=[],
                )
        finally:
            _close_file(file)

    async def _navigate(self, interaction: discord.Interaction, target_page: str) -> None:
        from ui.views.player_self_service_views import show_player_self_service_page_for_interaction

        await show_player_self_service_page_for_interaction(
            interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            page=target_page,
            summary_loader=self.summary_loader,
            accounts_loader=self.accounts_loader,
            dashboard_governor_id=self.dashboard_governor_id,
            timeout=self.timeout or 180,
        )

    @discord.ui.button(label="Accounts", style=discord.ButtonStyle.primary, disabled=True, row=0)
    async def accounts_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        return None

    @discord.ui.button(label="Reminders", style=discord.ButtonStyle.primary, row=0)
    async def reminders_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        from ui.views.player_self_service_views import PAGE_REMINDERS

        await self._navigate(interaction, PAGE_REMINDERS)

    @discord.ui.button(label="Preferences", style=discord.ButtonStyle.primary, row=0)
    async def preferences_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        from ui.views.player_self_service_views import PAGE_PREFERENCES

        await self._navigate(interaction, PAGE_PREFERENCES)

    @discord.ui.button(label="Dashboard", style=discord.ButtonStyle.secondary, row=1)
    async def dashboard_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        from ui.views.player_self_service_views import PAGE_DASHBOARD

        await self._navigate(interaction, PAGE_DASHBOARD)

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.secondary, row=1)
    async def inventory_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        from ui.views.player_self_service_views import PAGE_INVENTORY

        await self._navigate(interaction, PAGE_INVENTORY)

    @discord.ui.button(label="Exports", style=discord.ButtonStyle.secondary, row=1)
    async def exports_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        from ui.views.player_self_service_views import PAGE_EXPORTS

        await self._navigate(interaction, PAGE_EXPORTS)

    @discord.ui.button(label="Overview", custom_id="me:account-summary:overview", row=2)
    async def overview_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._replace(interaction, section="overview", page=1)

    @discord.ui.button(label="Combat", custom_id="me:account-summary:combat", row=2)
    async def combat_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._replace(interaction, section="combat", page=1)

    @discord.ui.button(label="Economy", custom_id="me:account-summary:economy", row=2)
    async def economy_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._replace(interaction, section="economy", page=1)

    @discord.ui.button(label="Previous", custom_id="me:account-summary:previous", row=3)
    async def previous_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._replace(
            interaction,
            section=self.summary_page.section,
            page=self.summary_page.page - 1,
        )

    @discord.ui.button(label="Next", custom_id="me:account-summary:next", row=3)
    async def next_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        await self._replace(
            interaction,
            section=self.summary_page.section,
            page=self.summary_page.page + 1,
        )

    @discord.ui.button(label="Download CSV", custom_id="me:account-summary:csv", row=3)
    async def csv_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            if not interaction.response.is_done():
                await interaction.response.defer()
        export = await asyncio.to_thread(accounts_export.build_accounts_csv, self.payload)
        file: discord.File | None = discord.File(BytesIO(export.data), filename=export.filename)
        try:
            await interaction.followup.send(
                "Complete Account Summary CSV.",
                file=file,
                ephemeral=True,
            )
        finally:
            _close_file(file)

    @discord.ui.button(label="Back to Accounts", custom_id="me:account-summary:back", row=3)
    async def back_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        from ui.views.player_self_service_views import (
            PAGE_ACCOUNTS,
            PlayerSelfServiceView,
            _build_page_response,
            _close_files,
        )

        await self._defer(interaction)
        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=PAGE_ACCOUNTS,
            accounts_payload=self.payload,
            accounts_loader=self.accounts_loader,
            summary_loader=self.summary_loader,
            dashboard_governor_id=self.dashboard_governor_id,
            timeout=self.timeout or 180,
        )
        embed, files = await _build_page_response(
            PAGE_ACCOUNTS,
            None,
            display_name=self.display_name,
            accounts_payload=self.payload,
        )
        try:
            await interaction.edit_original_response(
                content=None,
                embed=embed,
                view=view,
                attachments=[],
                files=files,
            )
        except Exception:
            from ui.views.player_self_service_views import build_accounts_portfolio_fallback

            await interaction.edit_original_response(
                content=None,
                embed=build_accounts_portfolio_fallback(
                    self.payload,
                    display_name=self.display_name,
                ),
                view=view,
                attachments=[],
            )
        finally:
            _close_files(files)


async def show_account_summary_for_interaction(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    accounts_loader: AccountsLoader = accounts_service.build_accounts_portfolio,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    dashboard_governor_id: int | None = None,
    timeout: float = 180,
) -> None:
    """Re-resolve the registry once on entry, then keep one payload across report controls."""
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except TypeError:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    try:
        payload = await accounts_loader(int(author_id))
    except Exception:
        logger.exception("account_summary_load_failed user_id=%s", author_id)
        await interaction.followup.send(
            "Account Summary is temporarily unavailable. Please try again in a moment.",
            ephemeral=True,
        )
        return
    page = accounts_service.build_account_summary_page(payload, section="overview", page=1)
    view = AccountSummaryView(
        author_id=author_id,
        display_name=display_name,
        payload=payload,
        accounts_loader=accounts_loader,
        summary_loader=summary_loader,
        dashboard_governor_id=dashboard_governor_id,
        timeout=timeout,
    )
    file: discord.File | None = None
    try:
        try:
            file = await _render_summary(page, display_name)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("account_summary_initial_render_failed user_id=%s", author_id)
            await interaction.edit_original_response(
                content=None,
                embed=build_account_summary_fallback(page),
                view=view,
                attachments=[],
            )
            return
        try:
            await interaction.edit_original_response(
                content=None,
                embed=None,
                view=view,
                attachments=[],
                files=[file],
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("account_summary_initial_delivery_failed user_id=%s", author_id)
            await interaction.edit_original_response(
                content=None,
                embed=build_account_summary_fallback(page),
                view=view,
                attachments=[],
            )
    finally:
        _close_file(file)
