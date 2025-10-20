# processing_pipeline.py
import asyncio
import inspect
import logging

logger = logging.getLogger(__name__)

import os
import traceback

import discord

from admin_helpers import log_processing_result, prompt_admin_inputs
from bot_config import ADMIN_USER_ID, DELETE_AFTER_DOWNLOAD_CHANNEL_ID, NOTIFY_CHANNEL_ID
from bot_loader import bot
from constants import CREDENTIALS_FILE, DATABASE, PASSWORD, SERVER, SUMMARY_LOG, USERNAME
from embed_utils import send_embed
from gsheet_module import run_all_exports
from player_stats_cache import build_player_stats_cache
from proc_config_import import run_proc_config_import
from stats_module import run_stats_copy_archive
from target_utils import warm_name_cache, warm_target_cache
from utils import live_queue, load_cached_input, update_live_queue_embed, utcnow


async def run_step(func, *args, offload_sync_to_thread: bool = False, **kwargs):
    """
    Run a step that might be sync or async.
    - If it's a coroutine function, await it.
    - If `offload_sync_to_thread=True`, run sync call in a thread.
    - If the result is awaitable (rare), await that too.
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    if offload_sync_to_thread:
        return await asyncio.to_thread(func, *args, **kwargs)

    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


async def execute_processing_pipeline(rank, seed, user, filename, channel_id, save_path=None):
    # Resolve source file (used for Excel processing)
    source_file = None
    if channel_id == 1346952247224828045:
        # Prefer the exact saved path if it exists
        if save_path and os.path.isfile(save_path):
            source_file = save_path
        else:
            # Fall back to DOWNLOAD_FOLDER/filename if that happens to exist
            try:
                from constants import DOWNLOAD_FOLDER

                candidate = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(candidate):
                    source_file = candidate
            except Exception:
                # Avoid hard failure if constants import fails in tests
                pass

    if source_file:
        logger.info(f"[EXCEL] Using source file: {source_file}")
    else:
        logger.warning("[EXCEL] Skipping Excel step — no source file path resolved.")

    # 1) Excel copy + archive + SQL
    _, out_archive, steps = await run_stats_copy_archive(
        rank,
        seed,
        source_filename=source_file,  # absolute path or None
        send_step_embed=lambda title, msg: send_embed(user, title, {"Status": msg}, 0x3498DB),
    )

    success_excel = steps.get("excel")
    success_archive = steps.get("archive")
    success_sql = steps.get("sql")

    await send_embed(
        user,
        "✅ Stats Copy Archive",
        {
            "Excel File": "✅" if success_excel else "❌",
            "Secondary Archive": "✅" if success_archive else "❌",
            "SQL Procedure": "✅" if success_sql else "❌",
            "Log": out_archive,
        },
        0x2ECC71 if all([success_excel, success_archive, success_sql]) else 0xE74C3C,
    )

    # 1b) Rebuild player_stats_cache.json as soon as SQL is updated
    #     (Cache is now SQL-sourced; it does NOT depend on Google Sheets)
    if success_sql:
        try:
            import json
            import time

            t0 = time.perf_counter()
            await build_player_stats_cache()  # async; internally offloads blocking bits
            # quick sanity log
            from constants import PLAYER_STATS_CACHE

            with open(PLAYER_STATS_CACHE, encoding="utf-8") as f:
                data = json.load(f)
            count = (data.get("_meta") or {}).get("count", "unknown")
            logger.info(
                "[CACHE] player_stats_cache rebuilt early: %s players in %.2fs",
                count,
                time.perf_counter() - t0,
            )
        except Exception:
            logger.exception("[CACHE] Early build_player_stats_cache failed")

    # 2) ProcConfig import — offload to a thread so we don't block the event loop
    success_proc_import = None
    if success_excel:
        logger.info("🛠️ Running ProcConfig import after successful Excel export")
        try:
            success_proc_import = await run_step(
                run_proc_config_import, offload_sync_to_thread=True
            )
        except Exception:
            logger.exception("[PROC_IMPORT] Unhandled error during run_proc_config_import")
            success_proc_import = False

        await send_embed(
            user,
            "🛠️ ProcConfig Import",
            {"Status": "Completed" if success_proc_import else "Failed"},
            0x2ECC71 if success_proc_import else 0xE74C3C,
        )

    # 3) Google Sheets exports — offload to thread
    await send_embed(user, "📤 Export to Google Sheets", {"Status": "Running"}, 0xF1C40F)

    notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    try:
        success_export, out_export = await run_step(
            run_all_exports,
            SERVER,
            DATABASE,
            USERNAME,
            PASSWORD,
            CREDENTIALS_FILE,
            notify_channel=notify_channel,
            bot_loop=bot.loop,
            offload_sync_to_thread=True,
        )
    except Exception:
        logger.exception("[EXPORT] Unhandled error during run_all_exports")
        success_export, out_export = False, "Export crashed (see logs)."

    # 4) Warm caches after an export so commands/autocomplete feel snappy
    try:
        await warm_name_cache()
    except Exception:
        logger.exception("[CACHE] warm_name_cache failed")

    try:
        await warm_target_cache()
    except Exception:
        logger.exception("[CACHE] warm_target_cache failed")

    await send_embed(
        user,
        "📊 Google Sheets Export",
        {
            "Status": "Success" if success_export else "Failure",
            "Log": out_export,
        },
        0x2ECC71 if success_export else 0xE74C3C,
    )

    # Defensive concatenation: keep things strings even if a future change returns None
    out_archive = out_archive or ""
    out_export = out_export or ""

    combined_log = f"{out_archive}\n\n{out_export}"
    return (
        success_excel,
        success_archive,
        success_sql,
        success_export,
        success_proc_import,
        combined_log,
    )


async def handle_file_processing(user, message, filename, save_path):
    # Use site-wide timezone-aware now
    start_time = utcnow()
    channel_id = message.channel.id

    notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    await send_embed(
        notify_channel,
        "📥 File Processing Started",
        {
            "Filename": filename,
            "User": str(message.author),
            "Status": "Starting",
        },
        0x3498DB,
    )

    rank, seed = await prompt_admin_inputs(bot, user, ADMIN_USER_ID)

    try:
        cache = load_cached_input()
    except Exception as e:
        logger.error(f"[HANDLE_FILE] Failed to call load_cached_input(): {e}")
        logger.error(traceback.format_exc())
        raise

    today_str = utcnow().date().isoformat()
    source = "🧠 Cached" if cache and cache.get("date") == today_str else "📬 Fresh Prompt"

    await send_embed(
        user,
        "🔄 Starting Script",
        {
            "Stage": "stats_copy_archive.py",
            "Rank": rank,
            "Seed": seed,
            "Source": source,
        },
        0x3498DB,
    )

    # Update live queue (keep only last 5 entries)
    for job in live_queue["jobs"]:
        if job["filename"] == filename and job["user"] == str(message.author):
            job["status"] = "⚙️ Processing..."
            break
    await update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)

    (
        success_excel,
        success_archive,
        success_sql,
        success_export,
        success_proc_import,
        combined_log,
    ) = await execute_processing_pipeline(
        rank, user=user, seed=seed, filename=filename, channel_id=channel_id, save_path=save_path
    )

    logger.info(
        "[SUMMARY] Excel=%s, Archive=%s, SQL=%s, Export=%s, ProcImport=%s",
        success_excel,
        success_archive,
        success_sql,
        success_export,
        success_proc_import,
    )
    logger.info("[SUMMARY LOG]\n%s", combined_log)

    # NOTE: source_file logging moved inside execute_processing_pipeline()

    await log_processing_result(
        bot,
        NOTIFY_CHANNEL_ID,
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
        SUMMARY_LOG,
    )

    # Status icon based on archive/export results
    if success_archive and success_export:
        status_icon = "🟢"
    elif success_archive or success_export:
        status_icon = "🟠"
    else:
        status_icon = "🔴"
    timestamp = utcnow().strftime("%Y-%m-%d %H:%M UTC")

    for job in live_queue["jobs"]:
        if job["filename"] == filename and job["user"] == str(message.author):
            job["status"] = f"{status_icon} {timestamp}"
            break

    live_queue["jobs"] = live_queue["jobs"][-5:]
    await update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)

    # Auto-delete in admin-only channel
    if (
        message.channel.id == DELETE_AFTER_DOWNLOAD_CHANNEL_ID
        and message.author.id == ADMIN_USER_ID
    ):
        try:
            await message.delete()
        except discord.NotFound:
            logger.warning(f"Message {message.id} already deleted.")
        except Exception:
            logger.exception("Unexpected error during message deletion")

    logger.info("[🟢 DONE] All steps completed. ✅ Monitoring for next file...")
