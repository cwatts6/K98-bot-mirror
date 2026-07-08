from __future__ import annotations

from collections import Counter
from collections.abc import Awaitable, Callable
import logging

import discord

from bot_config import ADMIN_USER_ID, LEADERSHIP_ROLE_IDS, LEADERSHIP_ROLE_NAMES
from core.interaction_safety import send_ephemeral
from voting import dashboard_presentation, reporting_service
from voting.engagement_export_service import EngagementCsvExport, build_engagement_csv_export
from voting.reporting_models import EngagementEligibleUser, EngagementReportingContract

logger = logging.getLogger(__name__)

EngagementReportLoader = Callable[..., Awaitable[EngagementReportingContract]]

_ROLE_FILTER_EXPECTED = reporting_service.ENGAGEMENT_ROLE_FILTER_EXPECTED
_ROLE_FILTER_ALL = reporting_service.ENGAGEMENT_ROLE_FILTER_ALL


class _EngagementWindowSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminEngagementView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Engagement window",
            min_values=1,
            max_values=1,
            row=0,
            options=_engagement_window_options(parent_view.window_value),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.window_value = reporting_service.normalize_engagement_window(
            self.values[0] if self.values else None
        )
        self.parent_view.contract = None
        if not await self.parent_view.ensure_contract(interaction):
            return
        self.parent_view.rebuild_controls()
        await self.parent_view.edit_current(interaction)


class _EngagementRoleSelect(discord.ui.Select):
    def __init__(self, parent_view: VoteAdminEngagementView) -> None:
        self.parent_view = parent_view
        super().__init__(
            placeholder="Engagement audience",
            min_values=1,
            max_values=1,
            row=1,
            options=_engagement_role_options(
                parent_view.eligible_users,
                parent_view.role_filter_value,
            ),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.role_filter_value = reporting_service.normalize_engagement_role_filter(
            self.values[0] if self.values else None
        )
        self.parent_view.contract = None
        if not await self.parent_view.ensure_contract(interaction):
            return
        self.parent_view.rebuild_controls()
        await self.parent_view.edit_current(interaction)


class VoteAdminEngagementView(discord.ui.View):
    def __init__(
        self,
        *,
        owner_user_id: int,
        eligible_users: tuple[EngagementEligibleUser, ...],
        contract: EngagementReportingContract | None = None,
        report_loader: EngagementReportLoader | None = None,
        window_value: str | None = None,
        role_filter_value: str | None = None,
    ) -> None:
        super().__init__(timeout=600)
        self.owner_user_id = int(owner_user_id)
        self.eligible_users = tuple(eligible_users)
        self.contract = contract
        self.report_loader = report_loader or reporting_service.build_admin_leadership_engagement_report
        self.window_value = reporting_service.normalize_engagement_window(
            window_value or (contract.window_key if contract else None)
        )
        self.role_filter_value = reporting_service.normalize_engagement_role_filter(
            role_filter_value or (contract.role_filter_value if contract else None)
        )

        self.window_select = _EngagementWindowSelect(self)
        self.role_select = _EngagementRoleSelect(self)
        self.export_btn = discord.ui.Button(
            label="Export CSV",
            style=discord.ButtonStyle.primary,
            row=2,
        )
        self.refresh_btn = discord.ui.Button(
            label="Refresh",
            style=discord.ButtonStyle.secondary,
            row=2,
        )
        self.close_btn = discord.ui.Button(
            label="Close",
            style=discord.ButtonStyle.secondary,
            row=2,
        )
        self.export_btn.callback = self._on_export
        self.refresh_btn.callback = self._on_refresh
        self.close_btn.callback = self._on_close

        self.add_item(self.window_select)
        self.add_item(self.role_select)
        self.add_item(self.export_btn)
        self.add_item(self.refresh_btn)
        self.add_item(self.close_btn)
        self.rebuild_controls()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(getattr(interaction.user, "id", 0)) != self.owner_user_id:
            await send_ephemeral(interaction, "This engagement export belongs to another admin.")
            return False
        if not _is_admin_or_leadership_user(interaction.user):
            await send_ephemeral(
                interaction,
                "You no longer have permission to use this engagement export.",
            )
            return False
        return True

    def rebuild_controls(self) -> None:
        self.window_select.options = _engagement_window_options(self.window_value)
        self.role_select.options = _engagement_role_options(
            self.eligible_users,
            self.role_filter_value,
        )

    def current_embed(self) -> discord.Embed:
        if self.contract is None:
            return _engagement_not_loaded_embed()
        return dashboard_presentation.build_engagement_dashboard_embeds(self.contract)[0]

    async def ensure_contract(self, interaction: discord.Interaction) -> bool:
        if self.contract is not None:
            return True
        self._refresh_eligible_users_from_interaction(interaction)
        await _defer_engagement_interaction(interaction)
        try:
            self.contract = await self.report_loader(
                eligible_users=self.eligible_users,
                window_key=self.window_value,
                role_filter_value=self.role_filter_value,
            )
        except Exception:
            logger.exception("vote_admin_engagement_load_failed")
            await send_ephemeral(
                interaction,
                "Engagement export data could not be loaded. Please try again.",
            )
            return False
        return True

    async def edit_current(self, interaction: discord.Interaction) -> None:
        embed = self.current_embed()
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            logger.warning("vote_admin_engagement_edit_failed", exc_info=True)
            await send_ephemeral(
                interaction,
                "Engagement controls took too long for Discord to accept. Please press Refresh.",
            )

    async def _on_export(self, interaction: discord.Interaction) -> None:
        if not await self.ensure_contract(interaction):
            return
        await _defer_engagement_interaction(interaction)
        assert self.contract is not None
        export = build_engagement_csv_export(
            self.contract,
            requested_by_discord_user_id=int(getattr(interaction.user, "id", 0)),
        )
        if export.is_oversized():
            await send_ephemeral(
                interaction,
                "Engagement export was built but is too large for Discord upload. "
                "Ask an operator for a direct SQL-assisted export.",
            )
            return
        file = discord.File(export.csv_bytes, filename=export.filename)
        await interaction.followup.send(
            embed=_export_summary_embed(export),
            file=file,
            ephemeral=True,
        )

    async def _on_refresh(self, interaction: discord.Interaction) -> None:
        self.contract = None
        if not await self.ensure_contract(interaction):
            return
        self.rebuild_controls()
        await self.edit_current(interaction)

    async def _on_close(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            child.disabled = True
        if interaction.response.is_done():
            await interaction.edit_original_response(content="Engagement export controls closed.", view=self)
        else:
            await interaction.response.edit_message(
                content="Engagement export controls closed.",
                view=self,
            )
        self.stop()

    def _refresh_eligible_users_from_interaction(self, interaction: discord.Interaction) -> None:
        guild = getattr(interaction, "guild", None)
        if guild is None:
            return
        users = eligible_users_from_guild(guild)
        if users:
            self.eligible_users = users


async def _defer_engagement_interaction(interaction: discord.Interaction) -> bool:
    if interaction.response.is_done():
        return True
    try:
        await interaction.response.defer()
        return True
    except TypeError:
        try:
            await interaction.response.defer(ephemeral=True)
            return True
        except Exception:
            logger.debug("vote_admin_engagement_defer_failed", exc_info=True)
            return False
    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
        logger.warning("vote_admin_engagement_defer_rejected", exc_info=True)
        return False
    except Exception:
        logger.debug("vote_admin_engagement_defer_failed", exc_info=True)
        return False


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
                discord_user_id=int(member.id),
                display_name=_discord_display_name(member),
                role_ids=tuple(int(role.id) for role in roles),
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


def _is_admin_or_leadership_user(user) -> bool:
    try:
        if int(getattr(user, "id", 0)) == int(ADMIN_USER_ID):
            return True
    except Exception:
        return False

    configured_role_ids = {int(role_id) for role_id in (LEADERSHIP_ROLE_IDS or ())}
    configured_role_names = {str(name) for name in (LEADERSHIP_ROLE_NAMES or ())}
    roles = tuple(getattr(user, "roles", ()) or ())
    role_ids = {int(getattr(role, "id", 0)) for role in roles if getattr(role, "id", None)}
    role_names = {str(getattr(role, "name", "") or "") for role in roles}
    return bool(configured_role_ids & role_ids or configured_role_names & role_names)


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


def _export_summary_embed(export: EngagementCsvExport) -> discord.Embed:
    contract = export.contract
    embed = discord.Embed(
        title="Voting engagement export",
        description=f"{contract.window_label} | {contract.role_filter_label}",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Rows", value=str(export.row_count), inline=True)
    embed.add_field(name="Users", value=str(contract.eligible_user_count), inline=True)
    embed.add_field(
        name="Participation",
        value=f"{contract.actual_participations}/{contract.possible_participations}",
        inline=True,
    )
    embed.set_footer(text="Private CSV includes Discord identity. Raw answers not included.")
    return embed


def _engagement_not_loaded_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Voting engagement export",
        description="Choose a window and audience, then export the private CSV.",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Private leadership engagement. Discord names included in CSV.")
    return embed


__all__ = [
    "EngagementReportLoader",
    "VoteAdminEngagementView",
    "eligible_users_from_guild",
]
