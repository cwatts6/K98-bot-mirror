import asyncio
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os

import discord
import psutil

from bot_config import DISCORD_BOT_TOKEN, NOTIFY_CHANNEL_ID
from constants import (
    EXIT_CODE_FILE,
    LAST_SHUTDOWN_INFO,
    SHUTDOWN_LOG_PATH,
    SHUTDOWN_MARKER_FILE,
)

# === Setup Logging ===
logger = logging.getLogger("shutdown_logger")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    SHUTDOWN_LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# === Step 1: Write shutdown markers and reason ===
def write_exit_code(reason="scheduled_shutdown"):
    with open(EXIT_CODE_FILE, "w") as f:
        f.write("0")
    with open(SHUTDOWN_MARKER_FILE, "w") as f:
        f.write(reason)
    with open(LAST_SHUTDOWN_INFO, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "reason": reason}, f)

    print(f"[SHUTDOWN] Wrote exit code and marker for reason: {reason}")


def flush_and_close_logger():
    for handler in logger.handlers:
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass


# === Step 2: Log shutdown to file ===
def log_shutdown(status, pid, cmdline, reason):
    short_cmdline = " ".join(cmdline)[:200] if cmdline else "N/A"
    msg = f"Status: {status} | PID: {pid or 'N/A'} | Cmd: {short_cmdline} | Reason: {reason}"
    logger.info(msg)


# === Step 3: Send embed notification ===
async def send_shutdown_embed():
    intents = discord.Intents.none()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            channel = await client.fetch_channel(NOTIFY_CHANNEL_ID)
            embed = discord.Embed(
                title="⏹️¸ Graceful Shutdown Initiated",
                description="The bot is shutting down cleanly in preparation for a server restart.",
                color=0xF1C40F,
                timestamp=datetime.utcnow(),
            )
            embed.add_field(name="Triggered By", value="shutdown bot", inline=False)
            embed.add_field(
                name="Time", value=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), inline=False
            )
            await channel.send(embed=embed)
            print("[SHUTDOWN] Embed sent successfully.", flush=True)
        except Exception as e:
            print(f"[SHUTDOWN] Failed during embed send: {e}")
        finally:
            await client.close()

    try:
        await client.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"[SHUTDOWN] Discord client failed: {e}")


# === Step 4: Kill all matching DL_bot.py processes ===
async def terminate_all_dl_bot(reason="scheduled_shutdown"):
    print("[DEBUG] Listing all Python-related processes:")
    found = False
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and any("DL_bot.py" in str(arg) for arg in cmdline):
                print(f"  PID {proc.pid}: {proc.info['name']} – {' '.join(cmdline)}")
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    found = True
                    log_shutdown("terminated", proc.pid, cmdline, reason)
                    print(f"[SHUTDOWN] Terminated PID {proc.pid}", flush=True)
                    await asyncio.sleep(0.5)  # âœ… Delay between kills
                except Exception as e:
                    print(f"[SHUTDOWN] Failed to terminate PID {proc.pid}: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not found:
        print("[SHUTDOWN] No running DL_bot.py processes found.")
        log_shutdown("no_match_found", None, None, reason)


# === Step 5: Main async flow ===
async def main():
    shutdown_reason = "scheduled_shutdown"
    write_exit_code(shutdown_reason)
    await send_shutdown_embed()
    await asyncio.sleep(2)
    await terminate_all_dl_bot(shutdown_reason)
    flush_and_close_logger()

    if os.getenv("INTERACTIVE", "1") == "1":
        input("\n[SHUTDOWN] Press Enter to exit this window...")


if __name__ == "__main__":
    asyncio.run(main())
