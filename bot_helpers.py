# bot_helpers.py
import asyncio
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
import os
import sys
import traceback

import discord

from bot_config import ADMIN_USER_ID, ADMIN_USER_MENTION, CHANNEL_IDS, NOTIFY_CHANNEL_ID
from bot_loader import bot  # ✅ safe to do now
from constants import COMMAND_CACHE_FILE, CSV_LOG, DOWNLOAD_FOLDER, RESTART_FLAG_PATH
from embed_utils import send_embed
from file_utils import append_csv_line
from logging_setup import flush_logs
from processing_pipeline import handle_file_processing
from utils import (
    download_attachment,
    ensure_aware_utc,
    live_queue,
    live_queue_lock,
    update_live_queue_embed,
    utcnow,
)


def safe_json(obj):
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception as e:
        return f"<Unserializable: {e}>"


def prune_restart_log(log_file="restart_log.csv", max_entries=100):
    try:
        if not os.path.exists(log_file):
            return

        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) <= max_entries + 1:
            return

        header = lines[0]
        entries = lines[1:][-max_entries:]

        with open(log_file, "w", encoding="utf-8", newline="") as f:
            f.writelines([header] + entries)

        logger.info(f"[LOG] Pruned {log_file} to last {max_entries} entries.")
    except Exception as e:
        logger.warning(f"[LOG] Failed to prune {log_file}: {e}")


def get_command_signature(command):
    if command is None:
        logger.warning("[SIGNATURE] Skipping null command object.")
        return None
    try:
        return {
            "name": command.name,
            "description": command.description,
            "version": getattr(command.callback, "__version__", "v1.0"),
        }
    except Exception as e:
        logger.warning(f"[SIGNATURE] Failed to extract signature from {command}: {e}")
        return None


def save_command_signatures(signatures, filepath=COMMAND_CACHE_FILE):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(signatures, f, indent=2)


def load_command_signatures(filepath: str) -> list:
    if not os.path.exists(filepath):
        logger.warning(f"[COMMAND_CACHE] File not found: {filepath}")
        return []
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[COMMAND_CACHE] Failed to load command cache: {e}")
        return []


def commands_changed(current, previous):
    current_sorted = sorted(current, key=lambda x: x["name"])
    previous_sorted = sorted(previous, key=lambda x: x["name"])

    if current_sorted != previous_sorted:
        logger.warning("[COMMAND DIFF] Slash command definitions have changed.")

        current_names = {
            cmd.get("name", f"unnamed_{i}"): cmd for i, cmd in enumerate(current_sorted)
        }
        previous_names = {
            cmd.get("name", f"unnamed_{i}"): cmd for i, cmd in enumerate(previous_sorted)
        }

        all_keys = sorted(set(current_names) | set(previous_names))
        for name in all_keys:
            c = current_names.get(name)
            p = previous_names.get(name)

            if c != p:
                logger.warning(f"↪️  Difference for /{name}:")
                try:
                    logger.warning(f"  🟢 New: {json.dumps(c, indent=2)}")
                except Exception as e:
                    logger.warning(f"  🟢 New (unserializable): {c} | Error: {e}")
                try:
                    logger.warning(f"  🔴 Old: {json.dumps(p, indent=2)}")
                except Exception as e:
                    logger.warning(f"  🔴 Old (unserializable): {p} | Error: {e}")

        return True

    return False


async def connection_watchdog(bot, interval=60, failure_threshold=3, alert_cooldown=600):
    failure_count = 0
    last_alert_time = None
    sent_disconnected_alert = False

    while True:
        try:
            now = utcnow()
            is_disconnected = bot.is_closed() or not bot.is_ready()

            if is_disconnected:
                failure_count += 1
                logger.warning(f"🕓 Bot connection issue (failure count: {failure_count})")

                if failure_count >= failure_threshold:
                    should_alert = (
                        last_alert_time is None
                        or (now - last_alert_time).total_seconds() >= alert_cooldown
                    )
                    if should_alert:
                        last_alert_time = now

                        embed = discord.Embed(
                            title="🚨 Bot Connection Issue",
                            description="Bot has been disconnected or not ready for several consecutive checks.",
                            color=0xE74C3C,
                        )
                        embed.add_field(name="Status", value="Disconnected or not ready")
                        embed.timestamp = utcnow()

                        try:
                            channel = bot.get_channel(NOTIFY_CHANNEL_ID)
                            if channel:
                                await channel.send(embed=embed)
                                logger.warning(
                                    "🚨 Disconnection alert sent to notification channel."
                                )
                        except Exception as e:
                            logger.error(f"❌ Failed to send alert to channel: {e}")

                        try:
                            owner = await bot.fetch_user(ADMIN_USER_ID)
                            await owner.send(embed=embed)
                            logger.warning("📩 Disconnection alert DM sent to admin.")
                        except Exception as e:
                            logger.error(f"❌ Failed to send DM to admin: {e}")

                        # Create restart flag
                        try:
                            with open(RESTART_FLAG_PATH, "w", encoding="utf-8") as f:
                                json.dump(
                                    {
                                        "timestamp": utcnow().isoformat(),
                                        "reason": "watchdog_disconnection",
                                        "user_id": "WATCHDOG",
                                    },
                                    f,
                                )
                            logger.info("[WATCHDOG] Restart flag created. Initiating shutdown.")
                            await bot.close()
                            flush_logs()
                            return
                        except Exception as e:
                            logger.error(
                                f"[WATCHDOG] Failed to create restart flag or shutdown bot: {e}"
                            )

                        sent_disconnected_alert = True

            else:
                if sent_disconnected_alert:
                    embed = discord.Embed(
                        title="✅ Bot Reconnected",
                        description="The bot has recovered and is now back online.",
                        color=0x2ECC71,
                    )
                    embed.timestamp = utcnow()

                    try:
                        channel = bot.get_channel(NOTIFY_CHANNEL_ID)
                        if channel:
                            await channel.send(embed=embed)
                            logger.info("✅ Reconnection alert sent to notification channel.")
                    except Exception as e:
                        logger.error(f"❌ Failed to send reconnection alert to channel: {e}")

                    try:
                        owner = await bot.fetch_user(ADMIN_USER_ID)
                        await owner.send(embed=embed)
                        logger.info("📩 Reconnection alert DM sent to admin.")
                    except Exception as e:
                        logger.error(f"❌ Failed to send reconnection DM to admin: {e}")

                    sent_disconnected_alert = False

                failure_count = 0
                logger.debug("✅ Bot is connected and ready.")

        except Exception as e:
            logger.error(f"💥 Watchdog internal error: {e}")

        await asyncio.sleep(interval)


# === Periodic Cleanup Task ===
async def queue_cleanup_loop():
    while not bot.is_closed():
        await clean_expired_jobs(days=7)  # now awaited
        await update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)
        await asyncio.sleep(6 * 3600)  # Every 6 hours


async def clean_expired_jobs(days=7):
    cutoff = utcnow().timestamp() - days * 86400

    async with live_queue_lock:
        before = len(live_queue["jobs"])
        live_queue["jobs"] = [
            job
            for job in live_queue["jobs"]
            if not (
                job["status"].startswith(("🟢", "🟠", "🔴"))
                and "uploaded" in job
                and (
                    # parse safely and normalise to UTC-aware before comparing
                    ensure_aware_utc(datetime.fromisoformat(job["uploaded"])).timestamp()
                    < cutoff
                )
            )
        ]
        removed = before - len(live_queue["jobs"])

    if removed > 0:
        logger.info(f"[QUEUE] Removed {removed} expired job(s).")


def should_use_exit_restart():
    # Detect if the bot is likely running inside a managed environment
    parent = os.path.basename(sys.argv[0])
    running_in_virtualenv = sys.prefix != sys.base_prefix
    env_indicators = [
        os.getenv("PM2_HOME"),  # pm2
        os.getenv("INVOCATION_ID"),  # systemd
        os.getenv("DOCKER"),  # Docker
        os.getenv("USE_EXIT_RESTART", "").lower() == "true",  # Manual override
    ]
    return any(env_indicators) or not parent.endswith(".py") or running_in_virtualenv


# === QUEUE PER CHANNEL ===
channel_queues = {cid: asyncio.Queue() for cid in CHANNEL_IDS}

# Global lock to prevent overlap between file processes
processing_lock = asyncio.Lock()

# active_jobs set protected by an explicit asyncio.Lock to avoid check-then-act races
active_jobs = set()  # Set of (channel_id, filename)
active_jobs_lock = asyncio.Lock()  # NEW: protect active_jobs mutations


async def queue_worker(channel_id):
    queue = channel_queues[channel_id]
    while True:
        try:
            message = await queue.get()
            try:
                for attachment in message.attachments:
                    # Sanitize filename to avoid path traversal or directory components
                    raw_filename = getattr(attachment, "filename", "unknown")
                    filename = os.path.basename(raw_filename)
                    save_path = os.path.join(DOWNLOAD_FOLDER, filename)
                    success = await download_attachment(
                        attachment,
                        save_path,
                        channel_name=message.channel.name,
                        user=message.author,
                    )

                    user = await bot.fetch_user(ADMIN_USER_ID)

                    if success:
                        await append_csv_line(
                            CSV_LOG,
                            [
                                utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                message.channel.name,
                                filename,
                                str(message.author),
                                save_path,
                            ],
                        )

                        job_id = (channel_id, filename)
                        # Use lock to make check-and-add atomic
                        async with active_jobs_lock:
                            if job_id in active_jobs:
                                logger.warning(f"Duplicate job skipped: {job_id}")
                                continue
                            active_jobs.add(job_id)

                        try:
                            async with processing_lock:
                                await handle_file_processing(user, message, filename, save_path)
                        finally:
                            # Remove under lock to avoid races
                            async with active_jobs_lock:
                                active_jobs.discard(job_id)
                    else:
                        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
                        await send_embed(
                            notify_channel,
                            "❌ Download Failed",
                            {
                                "File": filename,
                                "User": str(message.author),
                                "Channel": f"#{message.channel.name}",
                                "Status": "Failed after 3 attempts",
                            },
                            0xE74C3C,
                            ADMIN_USER_MENTION,
                        )

            finally:
                queue.task_done()  # ✅ Only after successful .get()

        except asyncio.CancelledError:
            logger.warning(f"[QUEUE_WORKER] Queue worker for channel {channel_id} cancelled.")
            break

        except Exception:
            logger.error(f"[QUEUE_WORKER] Unhandled error:\n{traceback.format_exc()}")
