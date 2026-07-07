from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging

import discord

from core.interaction_safety import send_ephemeral
from voting import dashboard_presentation, reporting_service
from voting.reporting_models import DashboardReportingContract

logger = logging.getLogger(__name__)

DashboardReportLoader = Callable[[], Awaitable[DashboardReportingContract]]


class _DashboardFilterSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminDashboardView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Filter dashboard",
            min_values=1,
            max_values=1,
            options=dashboard_presentation.dashboard_filter_options(parent_view.filter_value),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.filter_value = dashboard_presentation.normalize_dashboard_filter(
            self.values[0] if self.values else None
        )
        self.parent_view.page_index = 0
        self.parent_view.rebuild_pages()
        await self.parent_view.edit_current(interaction)


class VoteAdminDashboardView(discord.ui.View):
    def __init__(
        self,
        contract: DashboardReportingContract,
        *,
        owner_user_id: int,
        report_loader: DashboardReportLoader | None = None,
        filter_value: str | None = None,
    ) -> None:
        super().__init__(timeout=600)
        self.contract = contract
        self.owner_user_id = int(owner_user_id)
        self.report_loader = (
            report_loader or reporting_service.build_admin_leadership_dashboard_report
        )
        self.filter_value = dashboard_presentation.normalize_dashboard_filter(filter_value)
        self.page_index = 0
        self.pages: tuple[discord.Embed, ...] = ()

        self.filter_select = _DashboardFilterSelect(self)
        self.prev_btn = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            disabled=True,
        )
        self.next_btn = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
        )
        self.refresh_btn = discord.ui.Button(
            label="Refresh",
            style=discord.ButtonStyle.primary,
        )
        self.close_btn = discord.ui.Button(
            label="Close",
            style=discord.ButtonStyle.secondary,
        )

        self.prev_btn.callback = self._on_prev
        self.next_btn.callback = self._on_next
        self.refresh_btn.callback = self._on_refresh
        self.close_btn.callback = self._on_close

        self.add_item(self.filter_select)
        self.add_item(self.prev_btn)
        self.add_item(self.next_btn)
        self.add_item(self.refresh_btn)
        self.add_item(self.close_btn)
        self.rebuild_pages()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(getattr(interaction.user, "id", 0)) != self.owner_user_id:
            await send_ephemeral(interaction, "This dashboard belongs to another admin.")
            return False
        return True

    def rebuild_pages(self) -> None:
        self.pages = dashboard_presentation.build_dashboard_embeds(
            self.contract,
            filter_value=self.filter_value,
        )
        if not self.pages:
            self.page_index = 0
        else:
            self.page_index = max(0, min(self.page_index, len(self.pages) - 1))
        self.filter_select.options = dashboard_presentation.dashboard_filter_options(
            self.filter_value
        )
        self._update_buttons()

    def current_embed(self) -> discord.Embed:
        if not self.pages:
            self.rebuild_pages()
        return self.pages[self.page_index]

    async def edit_current(self, interaction: discord.Interaction) -> None:
        embed = self.current_embed()
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    def _update_buttons(self) -> None:
        total_pages = len(self.pages)
        self.prev_btn.disabled = self.page_index <= 0
        self.next_btn.disabled = total_pages <= 1 or self.page_index >= total_pages - 1

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self.page_index = max(0, self.page_index - 1)
        self._update_buttons()
        await self.edit_current(interaction)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self.page_index = min(len(self.pages) - 1, self.page_index + 1)
        self._update_buttons()
        await self.edit_current(interaction)

    async def _on_refresh(self, interaction: discord.Interaction) -> None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("vote_admin_dashboard_refresh_defer_failed", exc_info=True)
        try:
            self.contract = await self.report_loader()
        except Exception:
            logger.exception("vote_admin_dashboard_refresh_failed")
            await send_ephemeral(interaction, "Dashboard could not be refreshed. Please try again.")
            return
        self.rebuild_pages()
        await self.edit_current(interaction)

    async def _on_close(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            child.disabled = True
        if interaction.response.is_done():
            await interaction.edit_original_response(content="Dashboard closed.", view=self)
        else:
            await interaction.response.edit_message(content="Dashboard closed.", view=self)
        self.stop()


__all__ = ["DashboardReportLoader", "VoteAdminDashboardView"]
