"""Private /me exports interaction helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from file_utils import emit_telemetry_event
from inventory import export_service as inventory_export_service
from inventory.models import InventoryExportFormat, InventoryReportView
from services import stats_export_service

logger = logging.getLogger(__name__)

DEFAULT_STATS_EXPORT_DAYS = 90
DEFAULT_INVENTORY_EXPORT_LOOKBACK_DAYS = 366
STATS_EXPORT_DAY_OPTIONS = (30, 60, 90, 180, 360)
INVENTORY_EXPORT_DAY_OPTIONS = (30, 60, 90, 180, 360, DEFAULT_INVENTORY_EXPORT_LOOKBACK_DAYS)


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
            logger.debug("player_self_service_export_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_export_defer_failed", exc_info=True)


def _user_display_name(user: Any, fallback: str) -> str:
    return (
        str(getattr(user, "display_name", "") or "").strip()
        or str(getattr(user, "name", "") or "").strip()
        or str(fallback or "").strip()
        or "player"
    )


async def _send_private_error(
    interaction: discord.Interaction,
    message: str,
) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
            return
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_export_initial_error_send_failed", exc_info=True)
    await interaction.followup.send(message, ephemeral=True)


async def _send_private_message(
    interaction: discord.Interaction,
    message: str,
    *,
    view: discord.ui.View | None = None,
) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(message, view=view, ephemeral=True)
            return
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_export_initial_message_failed", exc_info=True)
    await interaction.followup.send(message, view=view, ephemeral=True)


def _stats_export_embed(export_file: stats_export_service.StatsExportFile) -> discord.Embed:
    embed = discord.Embed(
        title=f"Stats Export ({export_file.format_name})",
        description=export_file.description,
        color=discord.Color.dark_teal(),
    )
    embed.add_field(
        name="Export Scope",
        value=(
            f"Governors: {len(export_file.governor_ids)}\n"
            f"Rows: {export_file.row_count}\n"
            f"Daily window: {export_file.days} days"
        ),
        inline=False,
    )
    embed.add_field(name="Open File", value=export_file.instructions, inline=False)
    embed.set_footer(text="Private export. Legacy /my_stats_export remains available.")
    return embed


async def send_stats_export(
    interaction: discord.Interaction,
    *,
    display_name: str,
    requested_format: str,
    days: int = DEFAULT_STATS_EXPORT_DAYS,
) -> None:
    await _defer_private(interaction)
    export_file: stats_export_service.StatsExportFile | None = None
    try:
        outcome = await stats_export_service.build_personal_stats_export(
            discord_user_id=int(interaction.user.id),
            display_name=_user_display_name(interaction.user, display_name),
            requested_format=requested_format,
            days=int(days),
        )
        if outcome.status != "ok" or outcome.export_file is None:
            await _send_private_error(
                interaction,
                f"Stats export unavailable: {outcome.message or 'Please try again later.'}",
            )
            return

        export_file = outcome.export_file
        file = discord.File(export_file.file_path, filename=export_file.filename)
        await interaction.followup.send(
            embed=_stats_export_embed(export_file),
            file=file,
            ephemeral=True,
        )
        try:
            emit_telemetry_event(export_file.telemetry)
        except Exception:
            logger.debug("player_self_service_stats_export_telemetry_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_stats_export_failed user_id=%s format=%s",
            getattr(getattr(interaction, "user", None), "id", None),
            requested_format,
        )
        await _send_private_error(
            interaction,
            "Stats export is temporarily unavailable. Please try again in a moment.",
        )
    finally:
        stats_export_service.cleanup_export_file(export_file)


def _inventory_export_content(export_file: Any) -> str:
    return (
        "Inventory export ready. "
        f"`{export_file.row_count}` raw approved row(s), "
        f"`{len(export_file.governor_ids)}` governor(s)."
    )


async def send_inventory_export(
    interaction: discord.Interaction,
    *,
    display_name: str,
    export_format: InventoryExportFormat,
    view: InventoryReportView = InventoryReportView.ALL,
    governor_id: int | None = None,
    lookback_days: int = DEFAULT_INVENTORY_EXPORT_LOOKBACK_DAYS,
) -> None:
    await _defer_private(interaction)
    export_file = None
    try:
        export_file = await inventory_export_service.build_inventory_export_file(
            discord_user_id=int(interaction.user.id),
            username=_user_display_name(interaction.user, display_name),
            export_format=export_format,
            view=view,
            governor_id=governor_id,
            lookback_days=int(lookback_days),
            is_admin=False,
            discord_user=interaction.user,
        )
        file = discord.File(str(export_file.path), filename=export_file.filename)
        await interaction.followup.send(
            _inventory_export_content(export_file),
            file=file,
            ephemeral=True,
        )
    except (PermissionError, ValueError) as exc:
        await _send_private_error(interaction, str(exc))
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_inventory_export_failed user_id=%s format=%s",
            getattr(getattr(interaction, "user", None), "id", None),
            export_format.value,
        )
        await _send_private_error(
            interaction,
            "Inventory export is temporarily unavailable. Please try again in a moment.",
        )
    finally:
        inventory_export_service.cleanup_export_file(export_file)


class StatsExportOptionsView(discord.ui.View):
    def __init__(self, *, author_id: int, display_name: str) -> None:
        super().__init__(timeout=300)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.selected_format = "Excel"
        self.selected_days = DEFAULT_STATS_EXPORT_DAYS
        self.add_item(StatsExportFormatSelect(self))
        self.add_item(StatsExportDaysSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This export window is not for you.", ephemeral=True
        )
        return False

    @discord.ui.button(
        label="Download",
        style=discord.ButtonStyle.success,
        custom_id="me:export:stats_options_download",
        row=2,
    )
    async def download_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await send_stats_export(
            interaction,
            display_name=self.display_name,
            requested_format=self.selected_format,
            days=self.selected_days,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="me:export:stats_options_cancel",
        row=2,
    )
    async def cancel_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.edit_message(content="Stats export cancelled.", view=None)


class StatsExportFormatSelect(discord.ui.Select):
    def __init__(self, parent_view: StatsExportOptionsView) -> None:
        options = [
            discord.SelectOption(label="Excel", value="Excel", default=True),
            discord.SelectOption(label="CSV", value="CSV"),
            discord.SelectOption(label="Google Sheets", value="GoogleSheets"),
        ]
        super().__init__(
            placeholder="Format",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:export:stats_options_format",
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_format = self.values[0]
        await interaction.response.defer(ephemeral=True)


class StatsExportDaysSelect(discord.ui.Select):
    def __init__(self, parent_view: StatsExportOptionsView) -> None:
        options = [
            discord.SelectOption(
                label=str(days),
                value=str(days),
                default=(days == DEFAULT_STATS_EXPORT_DAYS),
            )
            for days in STATS_EXPORT_DAY_OPTIONS
        ]
        super().__init__(
            placeholder="Days",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:export:stats_options_days",
            row=1,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_days = int(self.values[0])
        await interaction.response.defer(ephemeral=True)


class InventoryExportOptionsView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        governors: list,
    ) -> None:
        super().__init__(timeout=300)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.governors = governors
        self.selected_format = InventoryExportFormat.EXCEL
        self.selected_view = InventoryReportView.ALL
        self.selected_governor_id: int | None = None
        self.selected_days = DEFAULT_INVENTORY_EXPORT_LOOKBACK_DAYS
        self.add_item(InventoryExportFormatSelect(self))
        self.add_item(InventoryExportViewSelect(self))
        self.add_item(InventoryExportGovernorSelect(self))
        self.add_item(InventoryExportDaysSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This export window is not for you.", ephemeral=True
        )
        return False

    @discord.ui.button(
        label="Download",
        style=discord.ButtonStyle.success,
        custom_id="me:export:inventory_options_download",
        row=4,
    )
    async def download_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await send_inventory_export(
            interaction,
            display_name=self.display_name,
            export_format=self.selected_format,
            view=self.selected_view,
            governor_id=self.selected_governor_id,
            lookback_days=self.selected_days,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="me:export:inventory_options_cancel",
        row=4,
    )
    async def cancel_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await interaction.response.edit_message(content="Inventory export cancelled.", view=None)


class InventoryExportFormatSelect(discord.ui.Select):
    def __init__(self, parent_view: InventoryExportOptionsView) -> None:
        options = [
            discord.SelectOption(
                label="Excel", value=InventoryExportFormat.EXCEL.value, default=True
            ),
            discord.SelectOption(label="CSV", value=InventoryExportFormat.CSV.value),
            discord.SelectOption(
                label="Google Sheets",
                value=InventoryExportFormat.GOOGLE_SHEETS.value,
            ),
        ]
        super().__init__(
            placeholder="Format",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:export:inventory_options_format",
            row=0,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_format = InventoryExportFormat(self.values[0])
        await interaction.response.defer(ephemeral=True)


class InventoryExportViewSelect(discord.ui.Select):
    def __init__(self, parent_view: InventoryExportOptionsView) -> None:
        options = [
            discord.SelectOption(label="All", value=InventoryReportView.ALL.value, default=True),
            discord.SelectOption(label="Resources", value=InventoryReportView.RESOURCES.value),
            discord.SelectOption(label="Speedups", value=InventoryReportView.SPEEDUPS.value),
            discord.SelectOption(label="Materials", value=InventoryReportView.MATERIALS.value),
        ]
        super().__init__(
            placeholder="View",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:export:inventory_options_view",
            row=1,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_view = InventoryReportView(self.values[0])
        await interaction.response.defer(ephemeral=True)


class InventoryExportGovernorSelect(discord.ui.Select):
    def __init__(self, parent_view: InventoryExportOptionsView) -> None:
        governor_options = [
            discord.SelectOption(
                label=str(getattr(governor, "governor_name", "") or governor.governor_id)[:100],
                value=str(governor.governor_id),
                description=str(getattr(governor, "account_type", "") or "Governor")[:100],
            )
            for governor in parent_view.governors[:24]
        ]
        options = [
            discord.SelectOption(label="All registered governors", value="all", default=True),
            *governor_options,
        ]
        super().__init__(
            placeholder="Governor",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:export:inventory_options_governor",
            row=2,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        value = self.values[0]
        self.parent_view.selected_governor_id = None if value == "all" else int(value)
        await interaction.response.defer(ephemeral=True)


class InventoryExportDaysSelect(discord.ui.Select):
    def __init__(self, parent_view: InventoryExportOptionsView) -> None:
        options = [
            discord.SelectOption(
                label=str(days),
                value=str(days),
                default=(days == DEFAULT_INVENTORY_EXPORT_LOOKBACK_DAYS),
            )
            for days in INVENTORY_EXPORT_DAY_OPTIONS
        ]
        super().__init__(
            placeholder="Days",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="me:export:inventory_options_days",
            row=3,
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction) -> None:
        self.parent_view.selected_days = int(self.values[0])
        await interaction.response.defer(ephemeral=True)


async def send_stats_export_options(
    interaction: discord.Interaction,
    *,
    display_name: str,
) -> None:
    await _send_private_message(
        interaction,
        "Choose your stats export options.",
        view=StatsExportOptionsView(
            author_id=int(interaction.user.id),
            display_name=display_name,
        ),
    )


async def send_inventory_export_options(
    interaction: discord.Interaction,
    *,
    display_name: str,
) -> None:
    await _defer_private(interaction)
    try:
        governors = await inventory_export_service.get_registered_governors_for_user(
            int(interaction.user.id)
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_inventory_export_governors_failed user_id=%s",
            getattr(getattr(interaction, "user", None), "id", None),
        )
        await _send_private_error(
            interaction,
            "Inventory export options are temporarily unavailable. Please try again in a moment.",
        )
        return
    if not governors:
        await _send_private_error(
            interaction,
            "You have no registered governors. Use `/me accounts` first.",
        )
        return
    await _send_private_message(
        interaction,
        "Choose your inventory export options.",
        view=InventoryExportOptionsView(
            author_id=int(interaction.user.id),
            display_name=display_name,
            governors=list(governors),
        ),
    )
