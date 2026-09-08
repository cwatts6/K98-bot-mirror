# admin_helpers

import asyncio
from datetime import datetime
import logging
import os
from typing import Any

import discord

from bot_config import ADMIN_USER_ID, ADMIN_USER_MENTION, NOTIFY_CHANNEL_ID
from constants import (
    DOWNLOAD_FOLDER,
    FAILED_LOG,
    INPUT_LOG,
)
from embed_utils import send_embed
from file_utils import append_csv_line
from input_helpers import wait_with_reminder
from stats_alerts.interface import send_stats_update_embed
from stats_alerts.kvk_meta import is_currently_kvk
from utils import ensure_aware_utc, load_cached_input, save_cached_input, utcnow

logger = logging.getLogger(__name__)


def _get_cached_value(cache: dict[str, str] | None, key: str) -> str | None:
    if not cache:
        return None
    value = cache.get(key)
    if not value or value == "default":
        return None
    return value


async def prompt_admin_inputs(bot: Any, user: discord.User, admin_id: int) -> tuple[str, str]:
    """Prompt an admin for Kingdom Rank and Seed, with daily caching.

    Returns:
        tuple[str, str]: (rank, seed) — strings, using cached values on timeout or 'default' as a last resort.

    Notes:
        - Uses a cached value (via utils.load_cached_input/save_cached_input) if present for today.
        - Instead of writing to os.environ, stores values on bot.k98_state (a namespaced dict)
          to avoid global process-wide environment side effects.
    """
    today_str = utcnow().date().isoformat()
    cache = load_cached_input()

    if cache and cache.get("date") == today_str:
        rank = _get_cached_value(cache, "rank")
        seed = _get_cached_value(cache, "seed")
        if rank and seed:
            logger.info("[INPUT] Using cached Kingdom Rank and Seed.")
            return rank, seed
        else:
            logger.info("[INPUT] Cached values were 'default' – skipping cache.")

    try:
        rank = await wait_with_reminder(bot, "📊 Enter new **Kingdom Rank**", admin_id)
        if not rank:
            cached_rank = _get_cached_value(cache, "rank")
            if cached_rank:
                rank = cached_rank
                logger.info("[INPUT] Kingdom Rank timed out; using cached value.")
            else:
                rank = "default"
                logger.warning("[INPUT] Kingdom Rank timed out with no cache; using default.")
        else:
            logger.info(f"[INPUT] Collected Kingdom Rank: {rank}")

        await asyncio.sleep(1)

        seed = await wait_with_reminder(bot, "🌱 Enter new **Kingdom Seed**", admin_id)
        if not seed:
            cached_seed = _get_cached_value(cache, "seed")
            if cached_seed:
                seed = cached_seed
                logger.info("[INPUT] Kingdom Seed timed out; using cached value.")
            else:
                seed = "default"
                logger.warning("[INPUT] Kingdom Seed timed out with no cache; using default.")
        else:
            logger.info(f"[INPUT] Collected Kingdom Seed: {seed}")

        # Safer runtime state: store rank/seed on the bot instance rather than process env.
        # This avoids global environment race conditions and is local to this bot instance.
        bot.k98_state = getattr(bot, "k98_state", {})  # type: ignore[attr-defined]
        bot.k98_state["KINGDOM_RANK"] = rank  # type: ignore[index]
        bot.k98_state["KINGDOM_SEED"] = seed  # type: ignore[index]

        save_cached_input(today_str, rank, seed)
        return rank, seed
    except Exception:
        # Preserve full traceback to logs for easier debugging
        logger.exception("[INPUT] Failed to collect admin inputs")
        return "default", "default"


async def log_processing_result(
    bot: Any,
    notify_channel_id: int,
    user: discord.User,
    message: discord.Message | None,
    filename: str,
    rank: str,
    seed: str,
    success_excel: bool | None,
    success_archive: bool | None,
    success_sql: bool | None,
    success_export: bool | None,
    success_proc_import: bool | None,
    combined_log: str,
    start_time: datetime,
    summary_log_path: str,
) -> None:
    """Log processing results, send status embed, and optionally post a stats update.

    Parameters:
        bot: Bot or client instance (any Discord bot object).
        notify_channel_id: Primary channel id to notify (int).
        user: The user who initiated the processing.
        message: The discord.Message object if available (None for slash commands).
        filename: Name of processed file.
        rank, seed: Admin inputs.
        success_*: Booleans or None for each processing step. None = step not attempted.
        combined_log: Path or content summary (not modified here).
        start_time: datetime when processing started (naive or aware; used as-is).
        summary_log_path: CSV path to append the summary row.

    Behavior:
        - Writes to INPUT_LOG and summary_log_path (uses append_csv_line).
        - Uses FAILED_LOG from constants for failed entries.
        - Attempts to send a rich embed to a notify channel; falls back to configured NOTIFY_CHANNEL_ID
          or DM to ADMIN_USER_ID if original channel is not available.
        - If all steps succeeded, calls send_stats_update_embed (unchanged behavior).
    """
    # Ensure start_time is an aware UTC datetime
    try:
        start_time = ensure_aware_utc(start_time)
    except Exception:
        logger.exception("[TIME] Failed to normalise start_time; proceeding with original value")

    end_time = utcnow()
    duration = (end_time - start_time).total_seconds()

    # Resolve notify channel with fallbacks
    notify_channel = bot.get_channel(notify_channel_id)
    if notify_channel is None:
        # try configured global notify channel from bot_config
        try:
            logger.debug("Primary notify channel not found; trying configured NOTIFY_CHANNEL_ID.")
            notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
        except Exception:
            # get_channel shouldn't raise, but guard defensively
            notify_channel = None

    if notify_channel is None:
        # As a last resort, attempt to DM the admin user
        try:
            logger.debug("Configured notify channel not available; attempting to DM admin.")
            admin_user = await bot.fetch_user(ADMIN_USER_ID)
            dm_channel = await admin_user.create_dm()
            notify_channel = dm_channel
        except Exception:
            logger.exception(
                "[NOTIFY] Failed to find notify channel and could not DM admin; continuing without embed."
            )
            notify_channel = None

    # Log rank/seed input (defensive I/O)
    try:
        await append_csv_line(
            INPUT_LOG, [end_time.strftime("%Y-%m-%d %H:%M:%S"), str(user), rank, seed]
        )
    except Exception:
        logger.exception("[LOG] Failed to append to INPUT_LOG")

    # Fallbacks for slash commands (no message object)
    channel_name = message.channel.name if message else "slash"
    author_name = message.author.name if message else str(user)

    # Log full processing result (defensive I/O)
    try:
        await append_csv_line(
            summary_log_path,
            [
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                channel_name,
                filename,
                author_name,
                os.path.join(DOWNLOAD_FOLDER, filename),
                str(success_excel),
                str(success_archive),
                str(success_sql),
                str(success_export),
                str(success_proc_import),
                f"{duration:.1f}",
            ],
        )
    except Exception:
        logger.exception("[LOG] Failed to append to summary log")

    # Determine embed metadata
    attempted: dict[str, bool | None] = {
        "Excel": success_excel,
        "Archive": success_archive,
        "SQL": success_sql,
        "Export": success_export,
        "ProcConfig": success_proc_import,
    }
    attempted = {k: v for k, v in attempted.items() if v is not None}

    if not attempted:
        title = "⚠️ No Steps Run"
        color = 0x95A5A6
        mention = ADMIN_USER_MENTION
    elif all(attempted.values()):
        title = "✅ Processing Completed"
        color = 0x2ECC71
        mention = None
    elif any(attempted.values()):
        title = "🟡 Processing Completed (Partial)"
        color = 0xF1C40F
        mention = None
    else:
        title = "❌ Processing Failed"
        color = 0xE74C3C
        mention = ADMIN_USER_MENTION

    logger.debug(
        "Step Success – Excel: %r, Archive: %r, SQL: %r, Export: %r, ProcConfig: %r",
        success_excel,
        success_archive,
        success_sql,
        success_export,
        success_proc_import,
    )

    # Only send embed when we have a valid channel object
    if notify_channel is not None:
        try:
            await send_embed(
                notify_channel,
                title,
                {
                    "Filename": filename,
                    "User": author_name,
                    "Rank": rank,
                    "Seed": seed,
                    "Excel Success": str(success_excel),
                    "Archive Success": str(success_archive),
                    "SQL Success": str(success_sql),
                    "Export Success": str(success_export),
                    "ProcConfig Import": str(success_proc_import),
                    "Duration": f"{duration:.1f} sec",
                },
                color,
                mention=mention,
            )
        except Exception:
            logger.exception("[EMBED] Failed to send processing result embed")
    else:
        logger.warning(
            "[NOTIFY] No available channel to send processing embed; skipping embed send."
        )

    # Log failure separately (defensive I/O)
    if not all(v for v in attempted.values()):
        try:
            await append_csv_line(
                FAILED_LOG,
                [
                    end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    filename,
                    author_name,
                    rank,
                    seed,
                    str(success_excel),
                    str(success_archive),
                    str(success_sql),
                    str(success_export),
                    str(success_proc_import),
                    f"{duration:.1f} sec",
                ],
            )
        except Exception:
            logger.exception("[LOG] Failed to append to FAILED_LOG")

    # Post stats update embed if all steps succeeded (unchanged behavior)
    if all([success_excel, success_archive, success_sql, success_export, success_proc_import]):
        is_kvk = is_currently_kvk()
        try:
            await send_stats_update_embed(
                bot, timestamp=end_time.strftime("%Y-%m-%d %H:%M UTC"), is_kvk=is_kvk
            )
            logger.info("[STATS EMBED] Stats update embed sent successfully.")
        except Exception:
            logger.exception("[STATS EMBED] Failed to send embed")
