"""Service orchestration for personal stats exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import os
import shutil
import tempfile

import pandas as pd

from services import stats_account_service
from stats.dal import stats_export_dal
from stats_exporter import build_user_stats_excel
from stats_exporter_csv import build_user_stats_csv

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StatsExportFile:
    file_path: str
    temp_dir: str
    filename: str
    format_name: str
    format_emoji: str
    description: str
    instructions: str
    governor_ids: list[int]
    row_count: int
    days: int
    telemetry: dict[str, object]


@dataclass(frozen=True, slots=True)
class StatsExportOutcome:
    status: str
    message: str | None = None
    export_file: StatsExportFile | None = None


def cleanup_export_file(export_file: StatsExportFile | None) -> None:
    if export_file is None:
        return
    if export_file.file_path and os.path.exists(export_file.file_path):
        try:
            os.unlink(export_file.file_path)
            logger.debug("stats_export_temp_file_cleaned path=%s", export_file.file_path)
        except Exception:
            logger.warning(
                "stats_export_temp_file_cleanup_failed path=%s",
                export_file.file_path,
                exc_info=True,
            )
    if export_file.temp_dir and os.path.exists(export_file.temp_dir):
        try:
            shutil.rmtree(export_file.temp_dir)
            logger.debug("stats_export_temp_dir_cleaned path=%s", export_file.temp_dir)
        except Exception:
            logger.warning(
                "stats_export_temp_dir_cleanup_failed path=%s",
                export_file.temp_dir,
                exc_info=True,
            )


async def build_personal_stats_export(
    *,
    discord_user_id: int,
    display_name: str,
    requested_format: str,
    days: int,
) -> StatsExportOutcome:
    account_summary = await stats_account_service.get_account_summary_for_user(discord_user_id)
    if not account_summary.ok:
        return StatsExportOutcome(
            status="registry_error",
            message=f"Registry is temporarily unavailable: `{account_summary.error}`",
        )
    if not account_summary.governor_ids:
        return StatsExportOutcome(
            status="no_accounts",
            message="You have no registered accounts. Use `/register_governor` first.",
        )

    df_daily = await _fetch_daily(account_summary.governor_ids)
    if df_daily.empty:
        return StatsExportOutcome(
            status="no_data",
            message="No stats data found for your accounts.",
        )

    export_format = _normalize_format(requested_format)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    safe_name = _safe_filename_part(display_name) or "user"
    temp_dir = tempfile.mkdtemp()
    filename, file_path = _build_export_target(
        export_format=export_format,
        safe_name=safe_name,
        timestamp=timestamp,
        temp_dir=temp_dir,
    )

    try:
        export_file = await _build_export_file(
            df_daily=df_daily,
            temp_dir=temp_dir,
            file_path=file_path,
            filename=filename,
            export_format=export_format,
            days=days,
            governor_ids=account_summary.governor_ids,
            discord_user_id=discord_user_id,
        )
    except Exception:
        cleanup_export_file(
            StatsExportFile(
                file_path=file_path,
                temp_dir=temp_dir,
                filename=filename,
                format_name=export_format,
                format_emoji="",
                description="",
                instructions="",
                governor_ids=account_summary.governor_ids,
                row_count=len(df_daily),
                days=days,
                telemetry={},
            )
        )
        raise

    logger.info(
        "stats_export_ready user_id=%s format=%s days=%s governors=%s rows=%s",
        discord_user_id,
        export_format,
        days,
        len(account_summary.governor_ids),
        len(df_daily),
    )
    return StatsExportOutcome(status="ok", export_file=export_file)


async def _fetch_daily(governor_ids: list[int]) -> pd.DataFrame:
    import asyncio

    return await asyncio.to_thread(stats_export_dal.fetch_daily_player_export, governor_ids)


async def _build_export_file(
    *,
    df_daily: pd.DataFrame,
    temp_dir: str,
    file_path: str,
    filename: str,
    export_format: str,
    days: int,
    governor_ids: list[int],
    discord_user_id: int,
) -> StatsExportFile:
    import asyncio

    if export_format == "CSV":
        await asyncio.to_thread(
            build_user_stats_csv,
            df_daily,
            None,
            out_path=file_path,
            days_for_daily_table=days,
        )
    else:
        await asyncio.to_thread(
            build_user_stats_excel,
            df_daily,
            None,
            out_path=file_path,
            days_for_daily_table=days,
        )

    meta = _format_metadata(export_format)
    telemetry = {
        "event": "my_stats_export",
        "user_id": discord_user_id,
        "format": export_format,
        "days": days,
        "num_governors": len(governor_ids),
        "num_rows": len(df_daily),
    }
    return StatsExportFile(
        file_path=file_path,
        temp_dir=temp_dir,
        filename=filename,
        format_name=meta["name"],
        format_emoji=meta["emoji"],
        description=meta["description"],
        instructions=meta["instructions"],
        governor_ids=list(governor_ids),
        row_count=len(df_daily),
        days=days,
        telemetry=telemetry,
    )


def _build_export_target(*, export_format: str, safe_name: str, timestamp: str, temp_dir: str) -> tuple[str, str]:
    """Build export target and return (filename, absolute_path)."""
    extension = ".csv" if export_format == "CSV" else ".xlsx"
    filename = f"stats_{safe_name}_{timestamp}{extension}"
    return filename, os.path.join(temp_dir, filename)


def _normalize_format(value: str) -> str:
    cleaned = (value or "Excel").strip()
    if cleaned in {"CSV", "GoogleSheets"}:
        return cleaned
    return "Excel"


def _safe_filename_part(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return cleaned.strip("_")[:80]


def _format_metadata(export_format: str) -> dict[str, str]:
    if export_format == "CSV":
        return {
            "emoji": "📄",
            "name": "CSV",
            "description": "**Lightweight text-based format**\nOpen with any spreadsheet app.",
            "instructions": (
                "**💻 Desktop:**\n"
                "1. Download the attached file\n"
                "2. Open with Excel, Google Sheets, or any spreadsheet app\n\n"
                "**📱 Mobile:**\n"
                "• **iPhone/iPad:** Tap attachment → Share → Save to Files → Open with Numbers or Google Sheets\n"
                "• **Android:** Tap attachment → Download → Open with Google Sheets or Excel"
            ),
        }
    if export_format == "GoogleSheets":
        return {
            "emoji": "📊",
            "name": "Google Sheets",
            "description": "**Google Sheets-compatible format**\nUpload to Google Drive to open in Sheets.",
            "instructions": (
                "**💻 Desktop:**\n"
                "1. Download the attached file\n"
                "2. Go to [drive.google.com](https://drive.google.com)\n"
                "3. Click **New** → **File upload**\n"
                "4. Upload this file → Double-click to open in Google Sheets\n\n"
                "**📱 Mobile:**\n"
                "• **iPhone/iPad:**\n"
                "  1. Tap attachment → Share → Save to Files\n"
                "  2. Open Google Drive app\n"
                "  3. Tap **+** → **Upload** → Select file from Files\n"
                "  4. Tap file in Drive to open in Sheets\n\n"
                "• **Android:**\n"
                "  1. Tap attachment → Download\n"
                "  2. Open Google Drive app\n"
                "  3. Tap **+** → **Upload** → Select downloaded file\n"
                "  4. Tap file in Drive to open in Sheets"
            ),
        }
    return {
        "emoji": "📘",
        "name": "Excel",
        "description": "**Full-featured Excel workbook**\nIncludes charts, formatting, and multiple sheets.",
        "instructions": (
            "**💻 Desktop:**\n"
            "1. Download the attached file\n"
            "2. Open with Microsoft Excel, LibreOffice, or Numbers\n\n"
            "**📱 Mobile:**\n"
            "• **iPhone/iPad:** Tap attachment → Share → Open in Excel or Numbers\n"
            "• **Android:** Tap attachment → Open with Excel or Google Sheets"
        ),
    }
