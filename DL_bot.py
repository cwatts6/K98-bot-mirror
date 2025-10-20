# DL_bot.py
import logging_setup

logging_setup.clean_old_lock_files(logging_setup.LOG_DIR, age_seconds=7 * 24 * 3600)

import logging
import sys

for h in list(logging.getLogger().handlers):
    is_file = isinstance(h, (logging.FileHandler, logging.handlers.RotatingFileHandler))
    if isinstance(h, logging.StreamHandler) and not is_file:
        logging.getLogger().removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

from logging_setup import ORIG_STDOUT  # add this import near the top

root = logging.getLogger()
root.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_console = logging.StreamHandler(ORIG_STDOUT)  # ✅ use original, not sys.stdout
_console.setFormatter(_fmt)
_console.setLevel(logging.INFO)
root.addHandler(_console)

import os
from pathlib import Path

from constants import (
    ALL_KVK_SHEET_ID,
    BASE_DIR,
    DATABASE,
    DOWNLOAD_FOLDER,
    EXIT_CODE_FILE,
    LAST_SHUTDOWN_INFO,
    PASSWORD,
    SERVER,
    USERNAME,
)

logger = logging.getLogger(__name__)

# Keep Discord/asyncio noise down early
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
for noisy in ["discord", "discord.client"]:
    logging.getLogger(noisy).setLevel(logging.ERROR)
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Utilities we need *before* any early-exit
# ✅ Load .env BEFORE anything that might use env vars
from dotenv import load_dotenv

from logging_setup import flush_logs

load_dotenv()

from startup_utils import migrate_legacy_artifacts_once

try:
    migrate_legacy_artifacts_once()
except Exception:
    # Debug-level trace so startup is resilient but failures are visible in logs when debug is enabled
    logger.debug("Failed to migrate legacy artifacts (continuing startup)", exc_info=True)

if os.environ.get("WATCHDOG_RUN") != "1":
    logger.critical("❌ Not launched by watchdog (WATCHDOG_RUN missing). Exiting.")
    flush_logs()
    sys.exit(1)

logger.info("✅ Step 1: dotenv loaded")

# --- Diagnostics: child process (before taking lock) ---
logger.info(
    "[DIAG][child] exe=%s | pid=%s | ppid=%s | WATCHDOG_RUN=%s | WATCHDOG_PARENT_PID=%s",
    sys.executable,
    os.getpid(),
    getattr(os, "getppid", lambda: None)(),
    os.environ.get("WATCHDOG_RUN"),
    os.environ.get("WATCHDOG_PARENT_PID"),
)

# --- Hard fail if not running under the project venv interpreter
if os.name == "nt":
    expected = (Path(BASE_DIR) / "venv" / "Scripts" / "python.exe").resolve()
    actual = Path(sys.executable).resolve()
    if actual != expected:
        logger.critical("❌ Wrong interpreter: %s (expected %s). Exiting.", actual, expected)
        flush_logs()
        sys.exit(1)

# Only now bring in the singleton and take the CHILD lock
from constants import BOT_LOCK_PATH, KVK_AUTO_EXPORT
from singleton_lock import acquire_singleton_lock, release_singleton_lock

acquire_singleton_lock(BOT_LOCK_PATH)
logger.info("[LOCK] Child lock acquired at %s (PID %d)", BOT_LOCK_PATH, os.getpid())

# sys.path.append(os.path.expanduser(r"~\AppData\Roaming\Python\Python311\site-packages"))

import asyncio
from asyncio import QueueFull
import json
import re
import signal
import threading

import discord

from bot_config import (
    ACTIVITY_UPLOAD_CHANNEL_ID,
    CHANNEL_IDS,
    DISCORD_BOT_TOKEN as TOKEN,
    FORT_RALLY_CHANNEL_ID,
    HONOR_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
    PLAYER_LOCATION_CHANNEL_ID,
    PREKVK_CHANNEL_ID,
    PROKINGDOM_CHANNEL_ID,
)
from bot_helpers import channel_queues
from Commands import register_commands
from embed_utils import send_embed
from honor_importer import ingest_honor_snapshot, parse_honor_xlsx
from kvk_all_importer import _auto_export_kvk, ingest_kvk_all_excel
from location_importer import load_staging_and_replace, parse_output_csv
from prekvk_importer import import_prekvk_bytes
from utils import live_queue, update_live_queue_embed, utcnow
from weekly_activity_importer import ingest_weekly_activity_excel

# === Load environment variables ===
if not TOKEN:
    logger.critical("❌ DISCORD_BOT_TOKEN is not set in the environment. Exiting.")
    flush_logs()
    sys.exit(1)

if "idlelib" in sys.modules:
    logger.critical("❌ Detected IDLE environment. Must be run by the watchdog. Exiting.")
    flush_logs()
    try:
        release_singleton_lock(BOT_LOCK_PATH)
    except Exception:
        pass
    sys.exit(1)

BOT_PID_FILE = Path(BASE_DIR) / "bot_pid.txt"

# --- DEBUG guard: detect Button shadowing early ---
import inspect

if not inspect.isclass(discord.ui.Button):
    raise RuntimeError(
        f"discord.ui.Button is shadowed by {discord.ui.Button!r} (should be a class). "
        "Search for 'from discord.ui import Button' or 'Button =' assignments."
    )

# Atomic write so ops tools always see the current child PID
try:
    tmp = BOT_PID_FILE.with_suffix(".tmp")
    tmp.write_text(str(os.getpid()), encoding="utf-8")
    # os.replace is atomic on NTFS; Path.replace works too
    os.replace(tmp, BOT_PID_FILE)
    logger.info("[PID] bot_pid.txt updated -> %s (PID %d)", BOT_PID_FILE, os.getpid())
except Exception as e:
    # Keep startup resilient but capture full stack at DEBUG level for later debugging
    logger.debug("[PID] Failed to update %s (continuing): %s", BOT_PID_FILE, e, exc_info=True)

# --- Process-level exception fallbacks (non-async) — SAFE, non-logging ---
import io
import traceback

# Keep original std streams so we can bypass logging safely
_ORIG_STDERR = sys.stderr


def _safe_stderr_write(text: str):
    """Write to a safe stderr without using logging; avoid recursion."""
    try:
        stream = _ORIG_STDERR or sys.__stderr__ or sys.stderr
        if stream:
            stream.write(text)
            stream.flush()
            return
    except Exception:
        pass
    # Last resort: raw write to file descriptor 2
    try:
        os.write(2, text.encode("utf-8", "replace"))
    except Exception:
        pass


def _sys_excepthook(exc_type, exc, tb):
    try:
        buf = io.StringIO()
        buf.write("💥 Unhandled exception in main thread:\n")
        traceback.print_exception(exc_type, exc, tb, file=buf)
        _safe_stderr_write(buf.getvalue())
    except Exception:
        try:
            os.write(2, "💥 Unhandled exception (hook failed)\n".encode("utf-8", "replace"))
        except Exception:
            pass


def _threading_excepthook(args):
    try:
        buf = io.StringIO()
        buf.write(f"💥 Unhandled exception in thread {getattr(args, 'thread', None)}:\n")
        traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=buf)
        _safe_stderr_write(buf.getvalue())
    except Exception:
        try:
            os.write(2, "💥 Unhandled thread exception (hook failed)\n".encode("utf-8", "replace"))
        except Exception:
            pass


sys.excepthook = _sys_excepthook
try:
    import threading as _thr  # ensure name is present if import order changes

    _thr.excepthook = _threading_excepthook  # Py 3.8+
except Exception:
    pass

from bot_instance import bot

register_commands(bot)
# Keep an explicit reference to the bot loop. Use this for signal -> loop scheduling
# to avoid subtle get_event_loop() corner cases on different Python versions/environments.
MAIN_LOOP = getattr(bot, "loop", None)


async def _get_notify_channel():
    """Fetch the notification channel, with a safe fallback."""
    ch = bot.get_channel(NOTIFY_CHANNEL_ID)
    if ch is None:
        try:
            ch = await bot.fetch_channel(NOTIFY_CHANNEL_ID)
        except Exception:
            ch = None
    return ch


def is_rally_daily(fn: str) -> bool:
    return re.search(r"^Rally_data_\d{2}-\d{2}-\d{4}\.xlsx$", fn, re.I) is not None


def is_rally_alltime(fn: str) -> bool:
    return re.search(r"Rally[_\s]?data.*all[\s_]?time.*\.xlsx$", fn, re.I) is not None


# === Global Error Logging ===
@bot.event
async def on_error(event_method, *args, **kwargs):
    logger.exception("💥 Unhandled error in %s", event_method)


@bot.event
async def on_message(message: discord.Message):
    if not bot.user or message.author.id == bot.user.id:
        return

    # === Fast-path: Player Location CSV auto-import ===
    if message.channel.id == PLAYER_LOCATION_CHANNEL_ID and message.attachments:
        target = next((a for a in message.attachments if a.filename.lower() == "output.csv"), None)
        if target:
            # Resolve target channel first so it's always defined
            target_ch = message.channel
            try:
                notify_ch = await _get_notify_channel()
                if notify_ch:
                    target_ch = notify_ch
            except Exception:
                # keep fallback to message.channel
                pass

            try:
                csv_bytes = await target.read()
                rows = parse_output_csv(csv_bytes)

                if not rows:
                    await send_embed(
                        target_ch,
                        "Player Location Import",
                        {
                            "Status": "No valid rows found in CSV.",
                            "Source Channel": f"#{message.channel.name} ({message.channel.id})",
                            "Uploaded By": f"{message.author} ({message.author.id})",
                        },
                        0xE74C3C,
                    )
                    return

                # Run blocking DB work off the event loop
                staging_rows, total_tracked = await asyncio.to_thread(
                    load_staging_and_replace, rows
                )

                await send_embed(
                    target_ch,
                    "Player Location Import ✅",
                    {
                        "Imported Rows": str(staging_rows),
                        "Total Tracked": str(total_tracked),
                        "Source Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploaded By": f"{message.author} ({message.author.id})",
                    },
                    0x2ECC71,
                )

                # 1) Ensure the profile cache reflects the newly merged data
                try:
                    from profile_cache import warm_cache as warm_profile_cache

                    warm_profile_cache()
                except Exception:
                    pass

                # 2) Signal any waiting tasks that the refresh is complete
                try:
                    from Commands import (
                        signal_location_refresh_complete,  # import where the globals live
                    )

                    signal_location_refresh_complete()
                except Exception:
                    pass

            except Exception as e:
                await send_embed(
                    target_ch,
                    "Player Location Import ❌",
                    {
                        "Error": f"{type(e).__name__}: {e}",
                        "Source Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploaded By": f"{message.author} ({message.author.id})",
                    },
                    0xE74C3C,
                    mention=None,
                )
            finally:
                return  # don't enqueue into the heavy pipeline

    # === Fast-path: Pre-KVK snapshot ingest (KVK 13) ===
    if message.channel.id == PREKVK_CHANNEL_ID and message.attachments:
        notify_ch = await _get_notify_channel() or message.channel

        # Only accept the canonical filename
        target = next(
            (a for a in message.attachments if a.filename.lower().strip() == "1198_prekvk.xlsx"),
            None,
        )

        if not target:
            await send_embed(
                notify_ch,
                "Pre-KVK Import ⚠️",
                {
                    "Info": "No matching file found.",
                    "Expected": "1198_prekvk.xlsx",
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE67E22,
            )
            return

        try:
            file_bytes = await target.read()

            # Run the blocking work in a thread
            ok, note, rows = await asyncio.to_thread(
                import_prekvk_bytes,
                file_bytes,
                target.filename,
                kvk_no=13,
                server=SERVER,
                db=DATABASE,
                user=USERNAME,
                pwd=PASSWORD,
            )

            if ok:
                await send_embed(
                    notify_ch,
                    "Pre-KVK Snapshot Imported ✅",
                    {
                        "KVK": "13",
                        "Rows": str(rows),
                        "Filename": target.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                        "Note": note,
                    },
                    0x2ECC71,
                )

                # Optional: refresh your daily/pinned stats embed which includes the Pre-KVK panel.
                # Guarded so it never crashes this path if not available / signature differs.
                try:
                    from stats_alert_utils import send_stats_update_embed

                    sql_conn_str = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
                    )
                    ts = utcnow().strftime("%Y-%m-%d %H:%M UTC")

                    # ✅ IMPORTANT: is_kvk=True to trigger Pre-KVK path (before Pass 4)
                    await send_stats_update_embed(
                        bot,
                        ts,  # timestamp (str)
                        True,  # is_kvk -> True so Pre-KVK path is considered
                        sql_conn_str,
                        is_test=False,  # set True if you want to bypass daily send-guards during testing
                    )
                except Exception:
                    # Silent: embed refresh is a bonus; import success is what matters
                    pass
            else:
                await send_embed(
                    notify_ch,
                    (
                        "Pre-KVK Import (Skipped/Duplicate) ℹ️"
                        if "Duplicate" in (note or "")
                        else "Pre-KVK Import ❌"
                    ),
                    {
                        "Filename": target.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                        "Info" if "Duplicate" in (note or "") else "Error": note or "Unknown",
                    },
                    0xF1C40F if "Duplicate" in (note or "") else 0xE74C3C,
                )
        except Exception as e:
            await send_embed(
                notify_ch,
                "Pre-KVK Import ❌",
                {
                    "Error": f"{type(e).__name__}: {e}",
                    "Filename": target.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE74C3C,
            )
        finally:
            return  # do not fall through to other pipelines

    # === Fast-path: KVK Honour ingest (full snapshots, multiple/day) ===
    if message.channel.id == HONOR_CHANNEL_ID and message.attachments:
        notify_ch = await _get_notify_channel() or message.channel

        # Accept canonical + common variants (TEST_/DEMO_/SAMPLE_ prefix, extra words), .xlsx only
        honor_name_rx = re.compile(
            r"^(?:test_|demo_|sample_)?1198[_\s-]*honor.*\.xlsx$", re.IGNORECASE
        )

        target = next(
            (a for a in message.attachments if honor_name_rx.match(a.filename.strip())), None
        )

        if not target:
            await send_embed(
                notify_ch,
                "KVK Honor Import ⚠️",
                {
                    "Info": "No matching file found.",
                    "Expected": "1198_honor.xlsx  • also accepts *1198_honor*.xlsx with optional TEST_/DEMO_/SAMPLE_ prefix",
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE67E22,
            )
            return

        try:
            # Decide test-mode from message text or filename
            msg_text = (message.content or "").lower()
            is_test = ("[test]" in msg_text) or (" test " in f" {msg_text} ")
            is_test = is_test or target.filename.lower().startswith(("test_", "demo_", "sample_"))

            # Read bytes once
            file_bytes = await target.read()

            # Pre-parse for row count (used only for the status embed)
            try:
                pre_df = await asyncio.to_thread(parse_honor_xlsx, file_bytes)
                row_count = len(pre_df)
            except Exception:
                row_count = 0  # don't fail the import if pre-parse fails

            # Ingest (blocking DB work off-loop)
            kvk_no, scan_id = await asyncio.to_thread(
                ingest_honor_snapshot,
                file_bytes,
                source_filename=target.filename,
                scan_ts_utc=message.created_at,  # aware UTC from Discord
            )

            # Success embed
            await send_embed(
                notify_ch,
                "KVK Honor Import ✅" + (" (TEST)" if is_test else ""),
                {
                    "KVK": str(kvk_no),
                    "ScanID": str(scan_id),
                    "Rows": str(row_count),
                    "Filename": target.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0x2ECC71,
            )

            # Optional: refresh stats embed so Honour Top-3 appears/refreshes.
            # Respect test-mode so it won't ping or claim daily limits.
            try:
                from stats_alert_utils import send_stats_update_embed

                sql_conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
                )
                ts = utcnow().strftime("%Y-%m-%d %H:%M UTC")
                await send_stats_update_embed(
                    bot,
                    ts,
                    True,  # is_kvk=True (season path)
                    sql_conn_str,
                    is_test=is_test,  # <- critical
                )
            except Exception:
                # Non-blocking nicety; ignore failures
                pass

        except Exception as e:
            await send_embed(
                notify_ch,
                "KVK Honor Import ❌",
                {
                    "Error": f"{type(e).__name__}: {e}",
                    "Filename": target.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE74C3C,
            )
        finally:
            return  # don't fall through to other pipelines

    # --- Fast-path: Weekly activity ingest ---
    if message.channel.id == ACTIVITY_UPLOAD_CHANNEL_ID and message.attachments:
        target = next(
            (
                a
                for a in message.attachments
                if a.filename.lower().endswith("1198_alliance_activity.xlsx")
            ),
            None,
        )
        if target:
            target_ch = message.channel
            try:
                notify = await _get_notify_channel()
                if notify:
                    target_ch = notify
            except Exception:
                pass

            try:
                file_bytes = await target.read()
                snap_id, row_count = await asyncio.to_thread(
                    ingest_weekly_activity_excel,
                    content=file_bytes,
                    snapshot_ts_utc=message.created_at,  # aware UTC from Discord
                    message_id=message.id,
                    channel_id=message.channel.id,
                    server=SERVER,
                    database=DATABASE,
                    username=USERNAME,
                    password=PASSWORD,
                    source_filename=target.filename,
                )
                if snap_id == 0:
                    await send_embed(
                        target_ch,
                        "Alliance Activity Import",
                        {"Status": "Duplicate detected for this week. Skipped."},
                        0xF1C40F,
                    )
                else:
                    await send_embed(
                        target_ch,
                        "Alliance Activity Import ✅",
                        {
                            "SnapshotId": str(snap_id),
                            "Rows": str(row_count),
                            "Filename": target.filename,
                            "Channel": f"#{message.channel.name} ({message.channel.id})",
                            "Uploader": f"{message.author} ({message.author.id})",
                        },
                        0x2ECC71,
                    )
            except Exception as e:
                await send_embed(
                    target_ch,
                    "Alliance Activity Import ❌",
                    {
                        "Error": f"{type(e).__name__}: {e}",
                        "Filename": target.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                    },
                    0xE74C3C,
                    mention=None,
                )
            finally:
                # do not fall through to other pipeline logic
                return

    # === Fast-path: Rally Forts XLSX auto-ingest (hardened) ===
    if message.channel.id == FORT_RALLY_CHANNEL_ID and message.attachments:
        notify_ch = await _get_notify_channel() or message.channel

        if not FORT_RALLY_CHANNEL_ID:
            # channel id missing from env/config – surface it loudly
            await send_embed(
                notify_ch,
                "Rally Forts Import ❌",
                {"Error": "FORT_RALLY_CHANNEL_ID is 0 (unset). Check .env/bot_config."},
                0xE74C3C,
            )
            return

        # Lazy import so missing deps don't crash startup
        try:
            from forts_ingest import import_rally_alltime_xlsx, import_rally_daily_xlsx
        except Exception as e:
            await send_embed(
                notify_ch,
                "Rally Forts Import ❌",
                {
                    "Error": f"Import failure: {type(e).__name__}: {e}",
                    "Hint": "Ensure forts_ingest.py and its dependencies (pandas, pyodbc) are installed in the venv.",
                },
                0xE74C3C,
            )
            return

        try:
            os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        except Exception:
            pass

        results = []
        matched_any = False
        for att in message.attachments:
            if not att.filename.lower().endswith(".xlsx"):
                continue

            local_path = os.path.join(DOWNLOAD_FOLDER, att.filename)
            try:
                await att.save(local_path)
                fn = att.filename
                logger.info("[RALLY] Saved %s to %s", fn, local_path)

                if is_rally_alltime(fn):
                    matched_any = True
                    logger.info("[RALLY] Detected ALL-TIME file: %s", fn)
                    res = await asyncio.to_thread(import_rally_alltime_xlsx, local_path)
                    results.append(("ok", fn, res))
                elif is_rally_daily(fn):
                    matched_any = True
                    logger.info("[RALLY] Detected DAILY file: %s", fn)
                    res = await asyncio.to_thread(import_rally_daily_xlsx, local_path)
                    results.append(("ok", fn, res))
                else:
                    results.append(("skip", fn, "Unrecognized rally filename"))
            except Exception as e:
                logger.exception("[RALLY] Error processing attachment %s", att.filename)
                results.append(("err", att.filename, f"{type(e).__name__}: {e}"))

        # If nothing matched (e.g., wrong filenames or no .xlsx), surface that
        if not matched_any and not results:
            await send_embed(
                notify_ch,
                "Rally Forts Import ⚠️",
                {
                    "Info": "No rally .xlsx attachments matched expected patterns.",
                    "Expected Daily": "Rally_data_DD-MM-YYYY.xlsx",
                    "Expected All-Time": "Rally_data_All_Time*.xlsx",
                },
                0xE67E22,
            )
            return

        fields = {
            "Source Channel": f"#{message.channel.name} ({message.channel.id})",
            "Uploaded By": f"{message.author} ({message.author.id})",
        }
        oks = [r for r in results if r[0] == "ok"]
        errs = [r for r in results if r[0] == "err"]
        skips = [r for r in results if r[0] == "skip"]

        for _, fn, res in oks[:5]:
            if isinstance(res, dict):
                rows = res.get("rows")
                asof = res.get("as_of")
                extra = f"rows={rows}" + (f"; as_of={asof}" if asof else "")
            else:
                extra = str(res)
            fields[f"✅ {fn}"] = extra or "ok"

        for _, fn, why in skips[:5]:
            fields[f"⏭️ {fn}"] = why

        for _, fn, err in errs[:5]:
            fields[f"❌ {fn}"] = err

        color = 0x2ECC71 if oks and not errs else (0xE67E22 if oks and errs else 0xE74C3C)
        title = "Rally Forts Import" + (
            " ✅" if oks and not errs else " ⚠️" if oks and errs else " ❌"
        )

        try:
            await send_embed(notify_ch, title, fields, color)
        except Exception:
            logger.exception("Failed to send Rally Forts import embed")

        return  # don't enqueue into heavy stats pipeline

    # === Fast-path: KVK (all kingdoms) ingest — robust & verbose ===
    if message.channel.id == PROKINGDOM_CHANNEL_ID and message.attachments:
        notify_ch = await _get_notify_channel() or message.channel

        # Log what Discord actually gave us
        try:
            logger.info(
                "[KVK] msg=%s attachments=%s", message.id, [a.filename for a in message.attachments]
            )
        except Exception:
            pass

        # Find ALL excel/csv attachments (process each)
        excel_attachments = [
            a
            for a in message.attachments
            if a.filename.lower().strip().endswith((".xlsx", ".xls", ".csv"))
        ]

        if not excel_attachments:
            await send_embed(
                notify_ch,
                "KVK All-Kingdom Import ⚠️",
                {
                    "Info": "No .xlsx/.xls/.csv attachment found.",
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE67E22,
            )
            return

        # Process each matching attachment independently
        for att in excel_attachments:
            try:
                logger.info("[KVK] Reading attachment: %s (%s bytes)", att.filename, att.size)
                file_bytes = await att.read()

                # Kick the blocking work to a thread
                result = await asyncio.to_thread(
                    ingest_kvk_all_excel,
                    content=file_bytes,
                    source_filename=att.filename,
                    uploader_id=message.author.id,
                    scan_ts_utc=message.created_at,  # aware UTC from Discord
                    server=SERVER,
                    database=DATABASE,
                    username=USERNAME,
                    password=PASSWORD,
                )

                kvk_no = int(result["kvk_no"])
                scan_id = int(result["scan_id"])
                rows = int(result["row_count"])
                neg = int(result["negatives"])
                dur_s = float(result["duration_s"])
                staged = int(
                    result.get("staged_rows", rows)
                )  # fallback to final rows if not provided
                proc_ms = float(result.get("proc_ms", max(0.0, dur_s * 1000.0)))
                io_ms = max(0.0, dur_s * 1000.0 - proc_ms)

                # Tiny badge + color flip if negatives > 0
                neg_badge = "0" if neg == 0 else f"{neg} ⚠️"
                color = 0x2ECC71 if neg == 0 else 0xE67E22  # green vs orange
                title = "KVK All-Kingdom Import ✅" if neg == 0 else "KVK All-Kingdom Import ⚠️"

                # Optional recompute timing (returned by new importer)
                recompute_ms = float(result.get("recompute_ms", 0.0))

                fields = {
                    "KVK": str(kvk_no),
                    "ScanID": str(scan_id),
                    "Rows": str(rows),
                    "Staged": str(staged),  # ← NEW
                    "Negative Corrections": neg_badge,
                    "Duration": f"{dur_s:.2f}s",
                    # Health line: proc / I/O (+ recompute if available)
                    "Health": (
                        f"proc `{proc_ms:.0f}ms` • I/O `{io_ms:.0f}ms`"
                        + (f" • recompute `{recompute_ms:.0f}ms`" if recompute_ms > 0 else "")
                    ),
                    "File": att.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                }
                embed = discord.Embed(title=title, color=color)
                for k, v in fields.items():
                    embed.add_field(name=k, value=str(v), inline=True)

                # Optional: keep your bot’s branding thumbnail for consistency
                try:
                    from constants import CUSTOM_AVATAR_URL

                    if CUSTOM_AVATAR_URL:
                        embed.set_thumbnail(url=CUSTOM_AVATAR_URL)
                except Exception:
                    pass

                # Add a link button to the stats sheet (graceful no-op if ID missing)
                view = None
                try:
                    sheet_id = ALL_KVK_SHEET_ID
                    if sheet_id:
                        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
                        view = discord.ui.View()
                        view.add_item(
                            discord.ui.Button(
                                label="📄 Open KVK_ALLPLAYER_OUTPUT",
                                url=url,
                                style=discord.ButtonStyle.link,
                            )
                        )
                except Exception:
                    view = None  # never block on UI bits

                await notify_ch.send(embed=embed, view=view)

                # Auto-export to Google Sheets (non-blocking) — keep your existing logic
                if KVK_AUTO_EXPORT:
                    logger.info(
                        "[KVK_EXPORT] Scheduling auto-export for KVK %s (Scan %s)", kvk_no, scan_id
                    )
                    asyncio.create_task(_auto_export_kvk(kvk_no, notify_ch, bot.loop))

            except Exception as e:
                # Log + surface any error per-attachment
                logger.exception("[KVK] Import failed for %s: %s", att.filename, e)
                await send_embed(
                    notify_ch,
                    "KVK All-Kingdom Import ❌",
                    {
                        "Error": f"{type(e).__name__}: {e}",
                        "File": att.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                    },
                    0xE74C3C,
                )
        return  # don't enqueue into other pipelines

    if message.channel.id in CHANNEL_IDS:
        logger.info("✅ Channel %s is monitored.", message.channel.id)

        for attachment in message.attachments:
            logger.info("📎 Attachment: %s", attachment.filename)
            if attachment.filename.lower().endswith((".xlsx", ".xls", ".csv")):
                logger.info("📥 Enqueuing message %s for worker", message.id)
                queue = channel_queues.get(message.channel.id)
                if not queue:
                    logger.warning(
                        "No queue configured for channel %s; message %s not enqueued",
                        message.channel.id,
                        message.id,
                    )
                    continue
                try:
                    queue.put_nowait(message)
                except QueueFull:
                    logger.warning(
                        "⚠️ Queue full for channel %s; dropping message %s",
                        message.channel.id,
                        message.id,
                    )
                else:
                    # Protect the in-memory live_queue mutation with a lock to reduce risks
                    # if any other threads or off-loop tasks access live_queue.
                    try:
                        with LIVE_QUEUE_LOCK:
                            live_queue["jobs"].append(
                                {
                                    "filename": attachment.filename,
                                    "user": str(message.author),
                                    "channel": message.channel.name,
                                    "uploaded": utcnow().isoformat(),
                                    "status": "🕐 Queued",
                                }
                            )
                    except Exception:
                        # Never crash on queue bookkeeping; log debug info for investigation.
                        logger.debug("Failed to append to live_queue (continuing)", exc_info=True)
                    try:
                        await update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)
                    except Exception:
                        logger.exception("Failed to update live queue embed")

    await bot.process_commands(message)


#
# ===== Commit 2: Signal-safe async graceful shutdown (Windows-first) =====
#

# Idempotent guard + timeout
_closing = False
_closing_lock = threading.Lock()
_SHUTDOWN_TIMEOUT_SECONDS = 10

# Lock to guard in-memory live_queue mutations across threads if needed.
# In normal operation the event-loop mutates this, but some helper threads or future changes
# might touch it; this lock reduces risk of race conditions.
LIVE_QUEUE_LOCK = threading.Lock()


async def _write_shutdown_markers(exit_code: int = 0, reason: str = "signal"):
    """
    Write minimal shutdown markers off the signal thread.
    Uses EXIT_CODE_FILE and LAST_SHUTDOWN_INFO from constants.
    """
    data = {"timestamp": utcnow().isoformat(), "exit_code": exit_code, "reason": reason}

    def _do_write():
        try:
            with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
                f.write(str(exit_code))
        except Exception:
            pass
        try:
            with open(LAST_SHUTDOWN_INFO, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    await asyncio.to_thread(_do_write)


async def _quiesce_background_tasks():
    """
    Stop schedulers/registries before closing the Discord client.
    Must be safe/idempotent if called multiple times.
    """
    # 1) Cancel registry/scheduler loops if present
    try:
        from reminder_task_registry import TaskRegistry

        await TaskRegistry.cancel_all(timeout=5)
    except Exception:
        logger.debug("[SHUTDOWN] TaskRegistry cancel skipped or failed.", exc_info=True)
    # 2) Quiesce any per-module loops (no hard fails)
    try:
        from bot_instance import quiesce_logging

        quiesce_logging()
    except Exception:
        logger.debug("[SHUTDOWN] quiesce_logging skipped or failed.", exc_info=True)


async def _close_http_clients_if_any():
    """
    Close any shared aiohttp sessions or other clients managed globally.
    No-op if none exist.
    """
    try:
        # Example:
        # from http_clients import session
        # if session and not session.closed:
        #     await session.close()
        pass
    except Exception:
        logger.debug("[SHUTDOWN] HTTP client close failed.", exc_info=True)


async def _graceful_shutdown(exit_code: int = 0, reason: str = "signal"):
    """
    1) write markers
    2) quiesce background tasks/schedulers
    3) bot.close() with timeout
    4) close HTTP clients
    5) flush + shutdown logging (last)
    """
    try:
        await _write_shutdown_markers(exit_code=exit_code, reason=reason)
        await _quiesce_background_tasks()
        try:
            await asyncio.wait_for(bot.close(), timeout=_SHUTDOWN_TIMEOUT_SECONDS)
        except TimeoutError:
            logger.warning("[SHUTDOWN] bot.close() timed out after %ss", _SHUTDOWN_TIMEOUT_SECONDS)
        except Exception:
            logger.exception("[SHUTDOWN] bot.close() raised")
        await _close_http_clients_if_any()
    finally:
        try:
            flush_logs()
        finally:
            # Close the queue listener & file handles (Commit 1)
            from logging_setup import shutdown_logging as _shutdown_logging

            _shutdown_logging()


def _begin_shutdown_from_signal(signum_name: str = "UNKNOWN", exit_code: int = 0):
    """
    Fast, idempotent signal entry. Schedules async shutdown on the loop thread.
    """
    global _closing
    with _closing_lock:
        if _closing:
            return
        _closing = True
    logger.warning("[SIGNAL] Received %s — scheduling graceful shutdown...", signum_name)
    # Prefer MAIN_LOOP (explicit) but fall back to the running event loop if needed.
    try:
        if MAIN_LOOP:
            loop = MAIN_LOOP
        else:
            loop = asyncio.get_event_loop()
    except Exception:
        # If get_event_loop() fails for whatever reason, try to schedule via asyncio's default
        # thread-safe mechanism by creating a new task on the current loop as a last resort.
        try:
            asyncio.get_running_loop().call_soon_threadsafe(
                lambda: asyncio.create_task(
                    _graceful_shutdown(exit_code=exit_code, reason=signum_name)
                )
            )
            return
        except Exception:
            # Last resort: log and return (shutdown will be attempted elsewhere)
            logger.exception("[SIGNAL] Failed to obtain event loop to schedule graceful shutdown")
            return

    loop.call_soon_threadsafe(
        lambda: asyncio.create_task(_graceful_shutdown(exit_code=exit_code, reason=signum_name))
    )


def _sigint_handler(signum, frame):
    _begin_shutdown_from_signal("SIGINT", exit_code=0)


def _sigbreak_handler(signum, frame):
    _begin_shutdown_from_signal("SIGBREAK", exit_code=0)


def _sigterm_handler(signum, frame):
    _begin_shutdown_from_signal("SIGTERM", exit_code=0)


# Register signal/console control handlers (Windows-first, cross-platform safe)
try:
    signal.signal(signal.SIGINT, _sigint_handler)  # Ctrl-C
except Exception:
    pass
try:
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _sigbreak_handler)  # Ctrl-Break (Windows)
except Exception:
    pass
try:
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _sigterm_handler)  # POSIX/services
except Exception:
    pass

# === Run Bot ===
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except SystemExit:
        logger.info("[EXIT] Bot exited via loop stop")
        flush_logs()
        sys.exit(0)
    except Exception as e:
        logger.exception("[CRASH] Unhandled exception during bot.run: %s", e)
        # Mark a crash exit code so the watchdog can distinguish
        try:
            with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
                f.write("1")
        except Exception:
            pass
        flush_logs()
        sys.exit(1)
    finally:
        # ensure lock release on any path
        try:
            # Only clear the PID file if it still points to *this* process
            try:
                if BOT_PID_FILE.exists() and BOT_PID_FILE.read_text(
                    encoding="utf-8"
                ).strip() == str(os.getpid()):
                    BOT_PID_FILE.unlink(missing_ok=True)
            except Exception:
                pass
            release_singleton_lock(BOT_LOCK_PATH)
        except Exception:
            pass
