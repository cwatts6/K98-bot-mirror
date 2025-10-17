# admin_helpers

import asyncio
from datetime import datetime
import logging
import os

import discord

from bot_config import ADMIN_USER_MENTION
from constants import DATABASE, DOWNLOAD_FOLDER, INPUT_LOG, PASSWORD, SERVER, USERNAME
from embed_utils import send_embed
from file_utils import append_csv_line
from input_helpers import wait_with_reminder
from stats_alert_utils import is_currently_kvk, send_stats_update_embed
from utils import load_cached_input, save_cached_input

logger = logging.getLogger(__name__)


async def prompt_admin_inputs(bot, user: discord.User, admin_id: int):
    today_str = datetime.utcnow().date().isoformat()
    cache = load_cached_input()

    if cache and cache.get("date") == today_str:
        rank = cache.get("rank", "default")
        seed = cache.get("seed", "default")
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

        os.environ["KINGDOM_RANK"] = rank
        os.environ["KINGDOM_SEED"] = seed

        save_cached_input(today_str, rank, seed)
        return rank, seed
    except Exception as e:
        logger.error(f"[INPUT] Failed to collect admin inputs: {e}")
        return "default", "default"


async def log_processing_result(
    bot,
    notify_channel_id,
    user,
    message,
    filename,
    rank,
    seed,
    success_excel,
    success_archive,
    success_sql,
    success_export,
    success_proc_import,
    combined_log,
    start_time,
    summary_log_path,
):
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    notify_channel = bot.get_channel(notify_channel_id)

    # Log rank/seed input
    await append_csv_line(
        INPUT_LOG, [end_time.strftime("%Y-%m-%d %H:%M:%S"), str(user), rank, seed]
    )

    # Fallbacks for slash commands (no message object)
    channel_name = message.channel.name if message else "slash"
    author_name = message.author.name if message else str(user)

    # Log full processing result
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

    print(
        f"[DEBUG] Step Success – Excel: {success_excel}, Archive: {success_archive}, SQL: {success_sql}, Export: {success_export}, ProcConfig: {success_proc_import}"
    )

    # Final embed
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

    # Log failure separately
    if not all(v for v in attempted.values()):
        await append_csv_line(
            "failed_log.csv",
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

        # ✅ Post stats update embed if all steps succeeded
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
            logger.error(f"[STATS EMBED] Failed to send embed: {e}")
