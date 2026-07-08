from __future__ import annotations

from collections.abc import Awaitable, Callable
from collections import Counter
import logging

import discord

from bot_config import LEADERSHIP_ROLE_IDS, LEADERSHIP_ROLE_NAMES
from core.interaction_safety import send_ephemeral
from voting import dashboard_presentation, reporting_service
from voting.reporting_models import (
    DashboardReportingContract,
    EngagementEligibleUser,
    EngagementReportingContract,
)

logger = logging.getLogger(__name__)

DashboardReportLoader = Callable[[], Awaitable[DashboardReportingContract]]
EngagementReportLoader = Callable[..., Awaitable[EngagementReportingContract]]

_ROLE_FILTER_EXPECTED = reporting_service.ENGAGEMENT_ROLE_FILTER_EXPECTED
_ROLE_FILTER_ALL = reporting_service.ENGAGEMENT_ROLE_FILTER_ALL


class _DashboardFilterSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminDashboardView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Filter dashboard",
            min_values=1,
            max_values=1,
            row=1,
            options=dashboard_presentation.dashboard_filter_options(parent_view.filter_value),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.filter_value = dashboard_presentation.normalize_dashboard_filter(
            self.values[0] if self.values else None
        )
        self.parent_view.page_index = 0
        self.parent_view.rebuild_pages()
        await self.parent_view.edit_current(interaction)


class _DashboardModeSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminDashboardView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Dashboard mode",
            min_values=1,
            max_values=1,
            row=0,
            options=dashboard_presentation.dashboard_mode_options(parent_view.mode_value),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.mode_value = dashboard_presentation.normalize_dashboard_mode(
            self.values[0] if self.values else None
        )
        self.parent_view.page_index = 0
        if self.parent_view.mode_value == dashboard_presentation.DASHBOARD_MODE_ENGAGEMENT:
            if not await self.parent_view.ensure_engagement_contract(interaction):
                return
        self.parent_view.rebuild_pages()
        await self.parent_view.edit_current(interaction)


class _EngagementWindowSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminDashboardView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Engagement window",
            min_values=1,
            max_values=1,
            row=2,
            options=_engagement_window_options(parent_view.window_value),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.window_value = reporting_service.normalize_engagement_window(
            self.values[0] if self.values else None
        )
        self.parent_view.engagement_contract = None
        self.parent_view.page_index = 0
        if not await self.parent_view.ensure_engagement_contract(interaction):
            return
        self.parent_view.rebuild_pages()
        await self.parent_view.edit_current(interaction)


class _EngagementRoleSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminDashboardView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Engagement role",
            min_values=1,
            max_values=1,
            row=3,
            options=_engagement_role_options(
                parent_view.eligible_users,
                parent_view.role_filter_value,
            ),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.role_filter_value = reporting_service.normalize_engagement_role_filter(
            self.values[0] if self.values else None
        )
        self.parent_view.engagement_contract = None
        self.parent_view.page_index = 0
        if not await self.parent_view.ensure_engagement_contract(interaction):
            return
        self.parent_view.rebuild_pages()
        await self.parent_view.edit_current(interaction)


class VoteAdminDashboardView(discord.ui.View):
    def __init__(
        self,
        contract: DashboardReportingContract,
        *,
        owner_user_id: int,
        report_loader: DashboardReportLoader | None = None,
        engagement_report_loader: EngagementReportLoader | None = None,
        eligible_users: tuple[EngagementEligibleUser, ...] | None = None,
        filter_value: str | None = None,
        mode_value: str | None = None,
        window_value: str | None = None,
        role_filter_value: str | None = None,
    ) -> None:
        super().__init__(timeout=600)
        self.contract = contract
        self.engagement_contract: EngagementReportingContract | None = None
        self.owner_user_id = int(owner_user_id)
        self.report_loader = (
            report_loader or reporting_service.build_admin_leadership_dashboard_report
        )
        self.engagement_report_loader = (
            engagement_report_loader or reporting_service.build_admin_leadership_engagement_report
        )
        self.eligible_users = tuple(eligible_users or ())
        self.filter_value = dashboard_presentation.normalize_dashboard_filter(filter_value)
        self.mode_value = dashboard_presentation.normalize_dashboard_mode(mode_value)
        self.window_value = reporting_service.normalize_engagement_window(window_value)
        self.role_filter_value = reporting_service.normalize_engagement_role_filter(
            role_filter_value
        )
        self.page_index = 0
        self.pages: tuple[discord.Embed, ...] = ()

        self.mode_select = _DashboardModeSelect(self)
        self.filter_select = _DashboardFilterSelect(self)
        self.window_select = _EngagementWindowSelect(self)
        self.role_select = _EngagementRoleSelect(self)
        self.prev_btn = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=4,
        )
        self.next_btn = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            row=4,
        )
        self.refresh_btn = discord.ui.Button(
            label="Refresh",
            style=discord.ButtonStyle.primary,
            row=4,
        )
        self.close_btn = discord.ui.Button(
            label="Close",
            style=discord.ButtonStyle.secondary,
            row=4,
        )

        self.prev_btn.callback = self._on_prev
        self.next_btn.callback = self._on_next
        self.refresh_btn.callback = self._on_refresh
        self.close_btn.callback = self._on_close

        self.add_item(self.mode_select)
        self.add_item(self.filter_select)
        self.add_item(self.window_select)
        self.add_item(self.role_select)
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
        if self.mode_value == dashboard_presentation.DASHBOARD_MODE_ENGAGEMENT:
            if self.engagement_contract is None:
                self.pages = (_engagement_not_loaded_embed(),)
            else:
                self.pages = dashboard_presentation.build_engagement_dashboard_embeds(
                    self.engagement_contract
                )
        else:
            self.pages = dashboard_presentation.build_dashboard_embeds(
                self.contract,
                filter_value=self.filter_value,
            )
        if not self.pages:
            self.page_index = 0
        else:
            self.page_index = max(0, min(self.page_index, len(self.pages) - 1))
        self.mode_select.options = dashboard_presentation.dashboard_mode_options(self.mode_value)
        self.filter_select.options = dashboard_presentation.dashboard_filter_options(
            self.filter_value
        )
        self.window_select.options = _engagement_window_options(self.window_value)
        self.role_select.options = _engagement_role_options(
            self.eligible_users,
            self.role_filter_value,
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
        engagement_mode = self.mode_value == dashboard_presentation.DASHBOARD_MODE_ENGAGEMENT
        self.filter_select.disabled = engagement_mode
        self.window_select.disabled = not engagement_mode
        self.role_select.disabled = not engagement_mode
        self.prev_btn.disabled = self.page_index <= 0
        self.next_btn.disabled = total_pages <= 1 or self.page_index >= total_pages - 1

    async def ensure_engagement_contract(self, interaction: discord.Interaction) -> bool:
        if self.engagement_contract is not None:
            return True
        self._refresh_eligible_users_from_interaction(interaction)
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            logger.debug("vote_admin_dashboard_engagement_defer_failed", exc_info=True)
        try:
            self.engagement_contract = await self.engagement_report_loader(
                eligible_users=self.eligible_users,
                window_key=self.window_value,
                role_filter_value=self.role_filter_value,
            )
        except Exception:
            logger.exception("vote_admin_dashboard_engagement_load_failed")
            await send_ephemeral(
                interaction,
                "Engagement summary could not be loaded. Please try again.",
            )
            return False
        return True

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
            if self.mode_value == dashboard_presentation.DASHBOARD_MODE_ENGAGEMENT:
                self._refresh_eligible_users_from_interaction(interaction)
                self.engagement_contract = await self.engagement_report_loader(
                    eligible_users=self.eligible_users,
                    window_key=self.window_value,
                    role_filter_value=self.role_filter_value,
                )
            else:
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

    def _refresh_eligible_users_from_interaction(self, interaction: discord.Interaction) -> None:
        guild = getattr(interaction, "guild", None)
        if guild is None:
            return
        users = eligible_users_from_guild(guild)
        if users:
            self.eligible_users = users


def eligible_users_from_guild(guild) -> tuple[EngagementEligibleUser, ...]:
    users: list[EngagementEligibleUser] = []
    for member in tuple(getattr(guild, "members", ()) or ()):
        if bool(getattr(member, "bot", False)):
            continue
        roles = [
            role
            for role in tuple(getattr(member, "roles", ()) or ())
            if str(getattr(role, "name", "") or "") != "@everyone"
        ]
        users.append(
            EngagementEligibleUser(
                discord_user_id=int(getattr(member, "id")),
                display_name=_discord_display_name(member),
                role_ids=tuple(int(getattr(role, "id")) for role in roles),
                role_names=tuple(str(getattr(role, "name", "") or "") for role in roles),
            )
        )
    return tuple(users)


def _discord_display_name(member) -> str:
    for attr in ("display_name", "global_name", "name"):
        value = str(getattr(member, attr, "") or "").strip()
        if value:
            return value
    return str(getattr(member, "id", "Unknown"))


def _engagement_window_options(selected: str | None) -> list[discord.SelectOption]:
    normalized = reporting_service.normalize_engagement_window(selected)
    values = (
        reporting_service.ENGAGEMENT_WINDOW_LAST_MONTH,
        reporting_service.ENGAGEMENT_WINDOW_LAST_3_MONTHS,
        reporting_service.ENGAGEMENT_WINDOW_LAST_6_MONTHS,
    )
    return [
        discord.SelectOption(
            label=reporting_service.engagement_window_label(value),
            value=value,
            default=value == normalized,
        )
        for value in values
    ]


def _engagement_role_options(
    users: tuple[EngagementEligibleUser, ...],
    selected: str | None,
) -> list[discord.SelectOption]:
    normalized = reporting_service.normalize_engagement_role_filter(selected)
    options = [
        discord.SelectOption(
            label="Expected roles",
            value=_ROLE_FILTER_EXPECTED,
            default=normalized == _ROLE_FILTER_EXPECTED,
        ),
        discord.SelectOption(
            label="All non-bot members",
            value=_ROLE_FILTER_ALL,
            default=normalized == _ROLE_FILTER_ALL,
        ),
    ]
    role_counts: Counter[tuple[int, str]] = Counter()
    configured_role_ids = {int(role_id) for role_id in (LEADERSHIP_ROLE_IDS or ())}
    configured_role_names = {str(name) for name in (LEADERSHIP_ROLE_NAMES or ())}
    for user in users:
        for index, role_id in enumerate(user.role_ids):
            name = user.role_names[index] if index < len(user.role_names) else f"Role {role_id}"
            role_counts[(int(role_id), name)] += 1

    def sort_key(item: tuple[tuple[int, str], int]) -> tuple[int, int, str]:
        (role_id, name), count = item
        priority = 0 if role_id in configured_role_ids or name in configured_role_names else 1
        return (priority, -count, name.casefold())

    sorted_roles = sorted(role_counts.items(), key=sort_key)
    selected_role = None
    if normalized.startswith("role:"):
        selected_role_id = int(normalized.split(":", 1)[1])
        selected_role = next(
            (item for item in sorted_roles if int(item[0][0]) == selected_role_id),
            None,
        )
    displayed_roles = sorted_roles[:23]
    if selected_role is not None and selected_role not in displayed_roles:
        displayed_roles = sorted_roles[:22] + [selected_role]

    for (role_id, name), count in displayed_roles:
        value = f"role:{role_id}"
        options.append(
            discord.SelectOption(
                label=name[:100],
                value=value,
                description=f"{count} eligible member(s)"[:100],
                default=value == normalized,
            )
        )
    if normalized.startswith("role:") and all(option.value != normalized for option in options):
        options.append(
            discord.SelectOption(
                label=f"Role {normalized.split(':', 1)[1]}"[:100],
                value=normalized,
                default=True,
            )
        )
    return options[:25]


def _engagement_not_loaded_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Voting engagement",
        description="Choose an engagement window or refresh to load the private summary.",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Private leadership engagement. Discord names included when loaded.")
    return embed


__all__ = [
    "DashboardReportLoader",
    "EngagementReportLoader",
    "VoteAdminDashboardView",
    "eligible_users_from_guild",
]
