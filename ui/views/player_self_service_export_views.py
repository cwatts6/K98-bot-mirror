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
    await interaction.followup.send(message, ephemeral=True)


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
) -> None:
    await _defer_private(interaction)
    export_file = None
    try:
        export_file = await inventory_export_service.build_inventory_export_file(
            discord_user_id=int(interaction.user.id),
            username=_user_display_name(interaction.user, display_name),
            export_format=export_format,
            view=InventoryReportView.ALL,
            governor_id=None,
            lookback_days=DEFAULT_INVENTORY_EXPORT_LOOKBACK_DAYS,
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
