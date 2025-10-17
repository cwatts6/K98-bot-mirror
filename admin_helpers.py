# admin_helpers

import asyncio
from datetime import datetime, timezone
import logging
import os
from typing import Optional, Tuple

import discord

from bot_config import ADMIN_USER_ID, ADMIN_USER_MENTION, NOTIFY_CHANNEL_ID
from constants import DATABASE, DOWNLOAD_FOLDER, FAILED_LOG, INPUT_LOG, PASSWORD, SERVER, USERNAME
from embed_utils import send_embed
from file_utils import append_csv_line
from input_helpers import wait_with_reminder
from stats_alert_utils import is_currently_kvk, send_stats_update_embed
from utils import load_cached_input, save_cached_input

logger = logging.getLogger(__name__)


async def prompt_admin_inputs(bot, user: discord.User, admin_id: int) -> Tuple[str, str]:
    """
    Prompt admin for kingdom rank and seed inputs.
    
    Checks cache first; if today's inputs exist, returns cached values.
    Otherwise, prompts the admin and stores values in bot.k98_state instead
    of os.environ for safer runtime state management.
    
    Args:
        bot: Discord bot instance
        user: Discord user object (admin)
        admin_id: Admin user ID for targeting prompts
        
    Returns:
        Tuple[str, str]: (rank, seed) - defaults to ("default", "default") on error
    """
    today_str: str = datetime.now(timezone.utc).date().isoformat()
    cache = load_cached_input()

    if cache and cache.get("date") == today_str:
        rank: str = cache.get("rank", "default")
        seed: str = cache.get("seed", "default")
        if rank != "default" and seed != "default":
            logger.info("[INPUT] Using cached Kingdom Rank and Seed.")
            return rank, seed
        else:
            logger.info("[INPUT] Cached values were 'default' – skipping cache.")

    try:
        rank = await wait_with_reminder(bot, "📊 Enter new **Kingdom Rank**", admin_id)
        rank = rank or "default"
        logger.info(f"[INPUT] Collected Kingdom Rank: {rank}")

        await asyncio.sleep(1)

        seed = await wait_with_reminder(bot, "🌱 Enter new **Kingdom Seed**", admin_id)
        seed = seed or "default"
        logger.info(f"[INPUT] Collected Kingdom Seed: {seed}")

        # Store in bot state instead of os.environ to avoid modifying process environment
        # This keeps runtime state isolated and safer for concurrent operations
        if not hasattr(bot, 'k98_state'):
            bot.k98_state = {}
        bot.k98_state['KINGDOM_RANK'] = rank
        bot.k98_state['KINGDOM_SEED'] = seed

        save_cached_input(today_str, rank, seed)
        return rank, seed
    except Exception as e:
        logger.exception("[INPUT] Failed to collect admin inputs")
        return "default", "default"


async def log_processing_result(
    bot,
    notify_channel_id: int,
    user: discord.User,
    message: Optional[discord.Message],
    filename: str,
    rank: str,
    seed: str,
    success_excel: Optional[bool],
    success_archive: Optional[bool],
    success_sql: Optional[bool],
    success_export: Optional[bool],
    success_proc_import: Optional[bool],
    combined_log: str,
    start_time: datetime,
    summary_log_path: str,
) -> None:
    """
    Log processing results to CSV files and send notification embed.
    
    Logs input data, full processing results, and failure details. Sends
    a status embed to the configured notify channel (with fallback to DM).
    If all steps succeed, also triggers stats update embed.
    
    Args:
        bot: Discord bot instance
        notify_channel_id: Primary notification channel ID
        user: Discord user who initiated processing
        message: Discord message object (may be None for slash commands)
        filename: Name of processed file
        rank: Kingdom rank input
        seed: Kingdom seed input
        success_excel: Excel step success (None if not attempted)
        success_archive: Archive step success (None if not attempted)
        success_sql: SQL step success (None if not attempted)
        success_export: Export step success (None if not attempted)
        success_proc_import: ProcConfig import step success (None if not attempted)
        combined_log: Combined log content (unused but kept for signature compatibility)
        start_time: Processing start timestamp (timezone-aware)
        summary_log_path: Path to summary log CSV
        
    Returns:
        None
    """
    end_time: datetime = datetime.now(timezone.utc)
    duration: float = (end_time - start_time).total_seconds()
    notify_channel: Optional[discord.TextChannel] = bot.get_channel(notify_channel_id)
    
    # Fallback channel resolution: try NOTIFY_CHANNEL_ID, then DM admin
    if notify_channel is None:
        logger.warning(
            f"[NOTIFY] Primary channel {notify_channel_id} not found, "
            f"trying configured NOTIFY_CHANNEL_ID={NOTIFY_CHANNEL_ID}"
        )
        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
        
        if notify_channel is None:
            logger.warning(
                f"[NOTIFY] Configured NOTIFY_CHANNEL_ID={NOTIFY_CHANNEL_ID} not found, "
                f"attempting DM to admin {ADMIN_USER_ID}"
            )
            try:
                admin_user = await bot.fetch_user(ADMIN_USER_ID)
                notify_channel = await admin_user.create_dm()
                logger.info(f"[NOTIFY] Successfully created DM channel with admin {ADMIN_USER_ID}")
            except Exception as e:
                logger.warning(
                    f"[NOTIFY] Failed to DM admin {ADMIN_USER_ID}: {e}. "
                    "Processing results will not be sent."
                )
                notify_channel = None

    # Log rank/seed input with error handling
    try:
        await append_csv_line(
            INPUT_LOG, [end_time.strftime("%Y-%m-%d %H:%M:%S"), str(user), rank, seed]
        )
    except Exception as e:
        logger.exception(f"[LOG] Failed to write to INPUT_LOG: {INPUT_LOG}")

    # Fallbacks for slash commands (no message object)
    channel_name: str = message.channel.name if message else "slash"
    author_name: str = message.author.name if message else str(user)

    # Log full processing result with error handling
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
    except Exception as e:
        logger.exception(f"[LOG] Failed to write to summary log: {summary_log_path}")

    # Determine embed metadata
    attempted = {
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
        f"[DEBUG] Step Success – Excel: {success_excel}, Archive: {success_archive}, "
        f"SQL: {success_sql}, Export: {success_export}, ProcConfig: {success_proc_import}"
    )

    # Final embed - only send if we have a valid channel
    if notify_channel is not None:
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
    else:
        logger.warning("[NOTIFY] No valid channel found, skipping embed notification")

    # Log failure separately with error handling
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
        except Exception as e:
            logger.exception(f"[LOG] Failed to write to FAILED_LOG: {FAILED_LOG}")

    # Post stats update embed if all steps succeeded
    if all([success_excel, success_archive, success_sql, success_export, success_proc_import]):
        sql_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
        )
        is_kvk = is_currently_kvk()
        try:
            await send_stats_update_embed(
                bot,
                timestamp=end_time.strftime("%Y-%m-%d %H:%M UTC"),
                is_kvk=is_kvk,
                sql_conn_str=sql_conn_str,
            )
            logger.info("[STATS EMBED] Stats update embed sent successfully.")
        except Exception as e:
            logger.exception("[STATS EMBED] Failed to send embed")
