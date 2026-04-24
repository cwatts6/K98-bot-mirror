# graceful_shutdown.py﻿
"""
Graceful shutdown helper script used to:
 - write shutdown markers and last-shutdown info
 - send an optional Discord embed notification
 - terminate running DL_bot.py processes (best-effort)

This variant adopts the centralized process helpers in `process_utils` for
liveness / information checks while keeping psutil usage local and optional.
"""

import asyncio
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys

import discord

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


# --- Helpers for time / UTC ---
def _now_iso() -> str:
    """
    Prefer the project's timezone-aware helper if available; fall back to naive UTC.
    Lazy import avoids heavy startup dependencies.
    """
    try:
        from utils import utcnow

        return utcnow().isoformat()
    except Exception:
        return datetime.utcnow().isoformat()


def _now_human() -> str:
    """Human-friendly UTC times used in embeds/logs."""
    try:
        from utils import utcnow

        return utcnow().strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


# === Step 1: Write shutdown markers and reason ===
def write_exit_code(reason="scheduled_shutdown"):
    try:
        Path(EXIT_CODE_FILE).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    try:
        with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
            f.write("0")
    except Exception:
        pass

    try:
        with open(SHUTDOWN_MARKER_FILE, "w", encoding="utf-8") as f:
            f.write(reason)
    except Exception:
        pass

    try:
        with open(LAST_SHUTDOWN_INFO, "w", encoding="utf-8") as f:
            json.dump({"timestamp": _now_iso(), "reason": reason}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(f"[SHUTDOWN] Wrote exit code and marker for reason: {reason}", flush=True)


def flush_and_close_logger():
    for h in list(logger.handlers):
        try:
            h.flush()
            h.close()
        except Exception:
            pass


# === Step 2: Log shutdown to file ===
def log_shutdown(status, pid, cmdline, reason, info: dict | None = None):
    """
    Log shutdown events with optional process metadata surfaced from process_utils.get_process_info.

    info (optional) may contain keys:
      - pid_exists
      - is_running
      - exe
      - create_time
      - alive (boolean from pid_alive check)
    """
    short_cmdline = " ".join(cmdline)[:200] if cmdline else "N/A"
    parts = [
        f"Status: {status}",
        f"PID: {pid or 'N/A'}",
        f"Cmd: {short_cmdline}",
        f"Reason: {reason}",
    ]

    if info:
        try:
            pid_exists = info.get("pid_exists")
            is_running = info.get("is_running")
            exe = info.get("exe")
            ct = info.get("create_time")
            alive_flag = info.get("alive")
            parts.append(f"pid_exists={pid_exists}")
            parts.append(f"is_running={is_running}")
            if alive_flag is not None:
                parts.append(f"alive={alive_flag}")
            if exe:
                parts.append(f"exe={exe}")
            if ct:
                parts.append(f"create_time={ct}")
        except Exception:
            # Best-effort: ignore any issues formatting info
            pass

    msg = " | ".join(parts)
    try:
        logger.info(msg)
    except Exception:
        print(msg, flush=True)


# === Step 3: Send embed notification ===
async def send_shutdown_embed():
    """
    Send a short embed to the configured notify channel.
    Uses a minimal discord.Client and closes it after send.
    """
    intents = discord.Intents.none()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            channel = await client.fetch_channel(NOTIFY_CHANNEL_ID)
            embed = discord.Embed(
                title="⏹️ Graceful Shutdown Initiated",
                description="The bot is shutting down cleanly in preparation for a server restart.",
                color=0xF1C40F,
                timestamp=datetime.utcnow(),
            )
            embed.add_field(name="Triggered By", value="shutdown bot", inline=False)
            embed.add_field(name="Time", value=_now_human(), inline=False)
            try:
                await channel.send(embed=embed)
                print("[SHUTDOWN] Embed sent successfully.", flush=True)
            except Exception as e:
                print(f"[SHUTDOWN] Failed to send embed: {e}", flush=True)
        except Exception as e:
            print(f"[SHUTDOWN] Failed during embed send: {e}", flush=True)
        finally:
            await client.close()

    try:
        await client.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"[SHUTDOWN] Discord client failed: {e}", flush=True)


# === Step 4: Kill all matching DL_bot.py processes ===
async def terminate_all_dl_bot(reason="scheduled_shutdown"):
    """
    Best-effort: iterate processes that look like DL_bot.py and terminate them.
    - psutil is optional; if absent, we skip termination (but markers are still written).
    - We use process_utils.get_process_info / pid_alive where helpful for logging and
      to centralize liveness heuristics.
    """
    print("[DEBUG] Attempting to locate running DL_bot.py processes...", flush=True)
    found = False

    # Try to import psutil lazily — do not require it at module import time
    try:
        import psutil  # type: ignore
    except Exception:
        psutil = None

    if psutil is None:
        print("[SHUTDOWN] psutil not available — skipping process termination step.", flush=True)
        log_shutdown("skipped_no_psutil", None, None, reason)
        return

    # Lazy import centralized helpers (optional)
    try:
        from process_utils import get_process_info, pid_alive  # type: ignore
    except Exception:
        get_process_info = None
        pid_alive = None

    # Iterate processes and look for occurrences of DL_bot.py in the cmdline
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if not cmdline:
                continue
            if any("DL_bot.py" in str(arg) for arg in cmdline):
                try:
                    pid = int(proc.pid)
                except Exception:
                    pid = getattr(proc, "pid", None)

                # Gather best-effort process metadata
                try:
                    info = get_process_info(pid) if get_process_info else None
                except Exception:
                    info = None

                # Confirm liveness via centralized helper if present (used only for logging here)
                try:
                    alive = bool(pid_alive(pid)) if pid_alive else True
                except Exception:
                    alive = True

                # Ensure info is a dict we can enrich
                if info is None:
                    info = {}
                info["alive"] = alive

                # Surface background info in logs before attempting termination
                try:
                    log_shutdown("found", pid, cmdline, reason, info=info)
                except Exception:
                    pass

                print(f"  PID {pid}: {proc.info.get('name')} – {' '.join(cmdline)}", flush=True)
                try:
                    # Attempt graceful terminate
                    proc.terminate()
                    try:
                        if psutil:
                            proc.wait(timeout=5)
                    except Exception:
                        # Timeout or other issues: escalate to kill
                        try:
                            proc.kill()
                        except Exception:
                            pass

                    found = True
                    # Refresh info after termination attempt (best-effort)
                    try:
                        post_info = get_process_info(pid) if get_process_info else None
                    except Exception:
                        post_info = None

                    # Enrich post_info with an alive probe result where possible
                    try:
                        if post_info is None:
                            post_info = {}
                        post_alive = bool(pid_alive(pid)) if pid_alive else False
                        post_info["alive"] = post_alive
                    except Exception:
                        pass

                    log_shutdown("terminated", pid, cmdline, reason, info=post_info)
                    print(f"[SHUTDOWN] Terminated PID {pid}", flush=True)
                    # small delay between kills to reduce system load
                    await asyncio.sleep(0.5)
                except Exception as e:
                    # Attempt to log with available info
                    try:
                        log_shutdown(
                            "terminate_failed", pid, cmdline, reason + f" -> {e}", info=info
                        )
                    except Exception:
                        pass
                    print(f"[SHUTDOWN] Failed to terminate PID {pid}: {e}", flush=True)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            # Defensive: never crash the shutdown helper
            print(f"[SHUTDOWN] Unexpected error while iterating processes: {e}", flush=True)
            continue

    if not found:
        print("[SHUTDOWN] No running DL_bot.py processes found.", flush=True)
        log_shutdown("no_match_found", None, None, reason)


# === Helper: remove shutdown marker (unless preserved) ===
def remove_shutdown_marker_if_allowed():
    preserve = os.getenv("PRESERVE_SHUTDOWN_MARKER", "0") == "1"
    if preserve:
        print("[SHUTDOWN] PRESERVE_SHUTDOWN_MARKER=1; leaving marker file in place.", flush=True)
        return

    try:
        if os.path.exists(SHUTDOWN_MARKER_FILE):
            os.remove(SHUTDOWN_MARKER_FILE)
            print(f"[SHUTDOWN] Removed shutdown marker file: {SHUTDOWN_MARKER_FILE}", flush=True)
    except Exception as e:
        print(f"[SHUTDOWN] Failed to remove shutdown marker file: {e}", flush=True)


# === Step 5: Main async flow ===
async def main():
    shutdown_reason = "scheduled_shutdown"
    write_exit_code(shutdown_reason)
    # Notify via Discord where possible (best-effort)
    try:
        await send_shutdown_embed()
    except Exception:
        # continue regardless of embed outcome
        pass

    # give a small pause before attempting termination to allow Discord send to complete
    await asyncio.sleep(2)

    await terminate_all_dl_bot(shutdown_reason)
    flush_and_close_logger()

    # Remove persistent marker unless preserved
    remove_shutdown_marker_if_allowed()

    # Interactive pause for local windows/operator convenience
    if os.getenv("INTERACTIVE", "1") == "1":
        try:
            input("\n[SHUTDOWN] Press Enter to exit this window...")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[SHUTDOWN] Interrupted by user.", flush=True)
        sys.exit(0)
