"""Private /me exports interaction helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from file_utils import emit_telemetry_event
from services import stats_export_service

logger = logging.getLogger(__name__)

DEFAULT_STATS_EXPORT_DAYS = 90
STATS_EXPORT_DAY_OPTIONS = (30, 60, 90, 180, 360)


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
) -> object | None:
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(message, view=view, ephemeral=True)
            try:
                return await interaction.original_response()
            except asyncio.CancelledError:
                raise
            except Exception:
                return None
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_export_initial_message_failed", exc_info=True)
    try:
        return await interaction.followup.send(message, view=view, ephemeral=True, wait=True)
    except TypeError:
        return await interaction.followup.send(message, view=view, ephemeral=True)


class _ExportOptionsView(discord.ui.View):
    expired_message = "This private export window has expired. Open `/me exports` again."

    def __init__(self, *, author_id: int, display_name: str) -> None:
        super().__init__(timeout=300, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.display_name = display_name
        self._message_ref: object | None = None
        self._expired = False

    def set_message_ref(self, message: object | None) -> None:
        self._message_ref = message
        if message is not None and hasattr(message, "flags") and hasattr(message, "channel"):
            try:
                self.message = message
            except Exception:
                logger.debug("player_self_service_export_message_ref_failed", exc_info=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._expired:
            await interaction.response.send_message(self.expired_message, ephemeral=True)
            return False
        if int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This export window is not for you.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        self._expired = True
        for child in self.children:
            child.disabled = True
        message = self._message_ref or getattr(self, "message", None)
        try:
            if message is not None and hasattr(message, "edit"):
                await message.edit(content=self.expired_message, view=self)
        except Exception:
            logger.debug("player_self_service_export_options_timeout_edit_failed", exc_info=True)


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


class StatsExportOptionsView(_ExportOptionsView):
    def __init__(self, *, author_id: int, display_name: str) -> None:
        super().__init__(author_id=author_id, display_name=display_name)
        self.selected_format = "Excel"
        self.selected_days = DEFAULT_STATS_EXPORT_DAYS
        self.add_item(StatsExportFormatSelect(self))
        self.add_item(StatsExportDaysSelect(self))

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


async def send_stats_export_options(
    interaction: discord.Interaction,
    *,
    display_name: str,
) -> None:
    view = StatsExportOptionsView(
        author_id=int(interaction.user.id),
        display_name=display_name,
    )
    message = await _send_private_message(
        interaction,
        (
            "Choose your stats export options.\n"
            "Export type: Excel, CSV, or Google Sheets.\n"
            f"Timeframe: last {DEFAULT_STATS_EXPORT_DAYS} days by default."
        ),
        view=view,
    )
    view.set_message_ref(message)
