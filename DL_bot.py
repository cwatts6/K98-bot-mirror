# DL_bot.py
# Note: minimal edit to use centralized logging_setup (UTC timestamps, rotation, console handling).
import ast
import io
import os
from pathlib import Path
import sys

# Centralized logging setup
from logging_setup import LOG_DIR, ORIG_STDOUT, clean_old_lock_files, flush_logs, setup_logging

# Prepare default logfile for child process and initialize logging
# CHILD_LOG = os.path.join(LOG_DIR, "dl_bot.log")
LEGACY_FULL_LOG = os.path.join(LOG_DIR, "log.txt")
# Use ORIG_STDOUT so child process console output goes to the original stream
setup_logging(logfile=LEGACY_FULL_LOG, console_stream=ORIG_STDOUT)

# preserve original behaviour: remove old lock files on startup (same semantics as previous code)
clean_old_lock_files(LOG_DIR, age_seconds=7 * 24 * 3600)

import logging
import traceback

from log_backup import trigger_log_backup_sync

# After centralized setup, get the module logger
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
    expected = (Path(LOG_DIR).parent / "venv" / "Scripts" / "python.exe").resolve()
    actual = Path(sys.executable).resolve()
    if actual != expected:
        logger.critical("❌ Wrong interpreter: %s (expected %s). Exiting.", actual, expected)
        flush_logs()
        sys.exit(1)

# Only now bring in the singleton and take the CHILD lock
from constants import (
    ALL_KVK_SHEET_ID,
    BOT_LOCK_PATH,
    EXIT_CODE_FILE,
    KVK_AUTO_EXPORT,
    LAST_SHUTDOWN_INFO,
    SQL_DATABASE,
    SQL_PASSWORD,
    SQL_SERVER,
    SQL_USERNAME,
)
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

# Programmatic DB trigger helper requires pyodbc; fail gracefully if missing
try:
    import pyodbc
except Exception:
    pyodbc = None

# NEW: import log health helpers and other modules (kept as in the repo)
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
from log_health import LogHeadroomError, preflight_from_env_sync
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

BOT_PID_FILE = (
    Path(LOG_DIR).parent / "bot_pid.txt"
)  # keep path consistent with LOG_DIR/BASE_DIR layout

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


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on", "y"}


def _collect_declared_slash_commands(module_relpath: str) -> set[str]:
    """Collect decorator-declared slash/app command names from a module file."""
    module_path = Path(__file__).parent / module_relpath
    names: set[str] = set()
    try:
        source = module_path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(module_path))
    except Exception as exc:
        logger.warning("[COMMAND AUDIT] Failed parsing %s: %s", module_relpath, exc)
        return names

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                continue
            attr = deco.func.attr
            is_slash = attr == "slash_command"
            is_app = (
                attr == "command"
                and isinstance(deco.func.value, ast.Name)
                and deco.func.value.id == "app_commands"
            )
            if not (is_slash or is_app):
                continue

            for kw in deco.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and kw.value.value:
                    names.add(str(kw.value.value))
                    break
    return names


def audit_command_registration_paths() -> tuple[dict[str, set[str]], dict[str, list[str]]]:
    """Return registration map and duplicate command-name map across known paths."""
    paths = {
        "Commands.py (authoritative)": _collect_declared_slash_commands("Commands.py"),
        "cogs/commands.py (secondary)": _collect_declared_slash_commands("cogs/commands.py"),
        "subscribe.py (secondary)": _collect_declared_slash_commands("subscribe.py"),
    }

    owners: dict[str, list[str]] = {}
    for source, command_names in paths.items():
        for cmd_name in command_names:
            owners.setdefault(cmd_name, []).append(source)

    duplicates = {name: sorted(srcs) for name, srcs in owners.items() if len(srcs) > 1}
    return paths, duplicates


def _log_registration_audit() -> dict[str, list[str]]:
    paths, duplicates = audit_command_registration_paths()
    logger.info(
        "[COMMAND AUDIT] registration summary: primary=%d secondary_cogs=%d secondary_subscribe=%d total_unique=%d",
        len(paths["Commands.py (authoritative)"]),
        len(paths["cogs/commands.py (secondary)"]),
        len(paths["subscribe.py (secondary)"]),
        len(set().union(*paths.values())),
    )
    if duplicates:
        logger.warning(
            "[COMMAND AUDIT] Duplicate slash command names detected across registration paths:"
        )
        for name in sorted(duplicates):
            logger.warning("[COMMAND AUDIT] - /%s -> %s", name, ", ".join(duplicates[name]))
    else:
        logger.info("[COMMAND AUDIT] No duplicate slash command names detected across paths.")
    return duplicates


ENABLE_SECONDARY_COGS = _env_bool("ENABLE_SECONDARY_COGS", default=False)

register_commands(bot)
_duplicates = _log_registration_audit()
if ENABLE_SECONDARY_COGS:
    logger.warning(
        "[COMMAND AUDIT] ENABLE_SECONDARY_COGS=true requested; startup currently keeps Commands.py as authoritative-only to avoid duplicate registrations."
    )
else:
    logger.info(
        "[COMMAND AUDIT] ENABLE_SECONDARY_COGS=false (default); secondary command paths are disabled."
    )
if _duplicates:
    logger.warning(
        "[COMMAND AUDIT] Duplicate names were detected in source definitions; authoritative registration path remains Commands.py only."
    )

# Keep an explicit reference to the bot loop. Use this for signal -> loop scheduling
# to avoid subtle get_event_loop() corner cases on different Python versions/environments.
MAIN_LOOP = getattr(bot, "loop", None)


# Centralized offload helper used throughout DL_bot to prefer process isolation,
# then callable offload, then thread, then asyncio.to_thread. This keeps call-sites
# concise and ensures consistent telemetry/meta usage.
async def _offload_callable(
    fn,
    *args,
    name: str | None = None,
    meta: dict | None = None,
    prefer_process: bool = True,
    **kwargs,
):
    """
    Attempt to run `fn(*args, **kwargs)` in (in order):
      - run_maintenance_with_isolation(..., prefer_process=prefer_process)
      - start_callable_offload(..., prefer_process=prefer_process)
      - run_blocking_in_thread(...)
      - asyncio.to_thread(...)

    Returns the callable result (or raises).
    """
    # Local imports & resolution
    try:
        from file_utils import run_maintenance_with_isolation  # type: ignore
    except Exception:
        run_maintenance_with_isolation = None  # type: ignore

    try:
        from file_utils import start_callable_offload  # type: ignore
    except Exception:
        start_callable_offload = None  # type: ignore

    try:
        from file_utils import run_blocking_in_thread  # type: ignore
    except Exception:
        run_blocking_in_thread = None  # type: ignore

    meta = meta or {}
    # Try maintenance isolation (preferred for DB/long-running)
    if run_maintenance_with_isolation is not None:
        try:
            res = await run_maintenance_with_isolation(
                fn,
                *args,
                **kwargs,
                name=name or getattr(fn, "__name__", None),
                prefer_process=prefer_process,
                meta=meta,
            )
            # Support helpers that may return (value, meta)
            if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
                return res[0]
            return res
        except Exception:
            # fallback to next option
            pass

    # Try callable offload (lighter-weight process/thread spawn)
    if start_callable_offload is not None:
        try:
            res = await start_callable_offload(
                fn,
                *args,
                **kwargs,
                name=name or getattr(fn, "__name__", None),
                prefer_process=prefer_process,
                meta=meta,
            )
            if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
                return res[0]
            return res
        except Exception:
            pass

    # Try thread helper
    if run_blocking_in_thread is not None:
        try:
            return await run_blocking_in_thread(
                fn, *args, **kwargs, name=name or getattr(fn, "__name__", None), meta=meta
            )
        except Exception:
            pass

    # Last resort: asyncio.to_thread
    return await asyncio.to_thread(fn, *args, **kwargs)


# NEW: helper to run preflight using environment credentials in a thread and notify user if it fails
async def ensure_sql_headroom_or_notify(notify_ch) -> bool:
    """
    Returns True if it's OK to proceed, False if the import should be skipped because of log headroom.
    This runs the blocking pyodbc check in an isolated process if helper available.
    """
    server = SQL_SERVER
    database = SQL_DATABASE
    username = SQL_USERNAME
    password = SQL_PASSWORD
    # If any credential is missing, skip the check (legacy behavior) and allow the import.
    if not (server and database and username and password):
        logger.debug("SQL env credentials incomplete; skipping log headroom check.")
        return True

    try:
        # Offload to isolated process when possible
        await _offload_callable(
            preflight_from_env_sync,
            server,
            database,
            username,
            password,
            name="preflight_from_env_sync",
            prefer_process=True,
            meta={"channel": getattr(notify_ch, "id", None)},
        )
        return True
    except LogHeadroomError as e:
        # User-visible notification: abort the import with an embed
        try:
            await send_embed(
                notify_ch,
                "Import Aborted ❌",
                {
                    "Reason": "SQL log headroom insufficient",
                    "Details": str(e),
                    "Advice": "Run FULL+LOG backups or resolve LOG_BACKUP reuse wait before retrying.",
                },
                0xE74C3C,
            )
        except Exception:
            logger.exception("Failed to send log-headroom alert embed")
        return False
    except Exception as e:
        # Non-deterministic failure checking SQL headroom; log and allow the import to avoid blocking
        logger.exception("Unexpected failure running SQL log headroom check: %s", e)
        return True


async def trigger_log_backup_background():
    """Schedule the synchronous trigger in an isolated process when possible, else a thread."""
    try:
        res = await _offload_callable(
            trigger_log_backup_sync, name="trigger_log_backup", prefer_process=True
        )
        # res may be bool-like or dict; handle both
        try:
            ok = res.get("ok") if isinstance(res, dict) else bool(res)
        except Exception:
            ok = bool(res)
        if ok:
            # log the richer info if present
            if isinstance(res, dict):
                logger.info(
                    "Background log backup trigger succeeded (method=%s last_log=%s reuse=%s log_pct=%s).",
                    res.get("used_method"),
                    res.get("last_log_backup"),
                    res.get("log_reuse_wait_desc"),
                    res.get("log_space_used_pct"),
                )
            else:
                logger.info("Background log backup trigger succeeded.")
        else:
            # include diagnostics when possible
            if isinstance(res, dict):
                logger.warning(
                    "Background log backup trigger failed: %s (method_try=%s last_log=%s reuse=%s log_pct=%s).",
                    res.get("error"),
                    res.get("method_tried"),
                    res.get("last_log_backup"),
                    res.get("log_reuse_wait_desc"),
                    res.get("log_space_used_pct"),
                )
            else:
                logger.warning("Background log backup trigger failed.")
    except Exception:
        logger.exception("Unexpected error running log backup trigger in background.")


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

                # NEW: preflight check before heavy DB work
                ok = await ensure_sql_headroom_or_notify(target_ch)
                if not ok:
                    return

                # Run blocking DB work off the event loop via offload helper
                staging_rows, total_tracked = await _offload_callable(
                    load_staging_and_replace,
                    rows,
                    name="load_staging_and_replace",
                    prefer_process=True,
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

                # schedule a background log-backup trigger (best-effort)
                try:
                    asyncio.create_task(trigger_log_backup_background())
                except Exception:
                    logger.exception("Failed to schedule background log-backup trigger")

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

    # === Fast-path: Pre-KVK snapshot ingest (dynamic KVK lookup) ===
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

            # NEW: preflight check
            ok = await ensure_sql_headroom_or_notify(notify_ch)
            if not ok:
                return

            # Resolve current KVK number dynamically (offload when available)
            try:
                from file_utils import run_blocking_in_thread
            except Exception:
                run_blocking_in_thread = None

            meta = None
            try:
                import stats_alerts.kvk_meta as kvk_meta

                if run_blocking_in_thread is not None:
                    meta = await run_blocking_in_thread(
                        kvk_meta.get_latest_kvk_metadata_sql,
                        name="get_latest_kvk_metadata_sql_dlbot",
                    )
                else:
                    # fallback to asyncio.to_thread
                    meta = await asyncio.to_thread(kvk_meta.get_latest_kvk_metadata_sql)
            except Exception:
                logger.exception("[DL_BOT] Failed to determine current KVK metadata")

            # Hard-fail if we cannot determine a valid kvk_no
            detected_kvk_no = None
            try:
                if meta and meta.get("kvk_no") is not None:
                    detected_kvk_no = int(meta.get("kvk_no"))
            except Exception:
                detected_kvk_no = None

            if detected_kvk_no is None:
                logger.error(
                    "[DL_BOT] Could not determine current KVK number; aborting Pre-KVK import"
                )
                await send_embed(
                    notify_ch,
                    "Pre-KVK Import ❌",
                    {
                        "Error": "Could not determine current KVK number (kvk_no). Import aborted.",
                        "Filename": target.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                    },
                    0xE74C3C,
                )
                return

            # Run importer offload (prefer process) with detected kvk_no
            ok, note, rows = await _offload_callable(
                import_prekvk_bytes,
                file_bytes,
                target.filename,
                kvk_no=detected_kvk_no,
                name="import_prekvk_bytes",
                prefer_process=True,
                meta={"filename": target.filename, "kvk_no": detected_kvk_no},
            )

            if ok:
                await send_embed(
                    notify_ch,
                    "Pre-KVK Snapshot Imported ✅",
                    {
                        "KVK": str(detected_kvk_no),
                        "Rows": str(rows),
                        "Filename": target.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                        "Note": note,
                    },
                    0x2ECC71,
                )

                # schedule a background log-backup trigger (best-effort)
                try:
                    asyncio.create_task(trigger_log_backup_background())
                except Exception:
                    logger.exception("Failed to schedule background log-backup trigger")

                # Optional: refresh your daily/pinned stats embed which includes the Pre-KVK panel.
                # Guarded so it never crashes this path if debug is enabled
                try:
                    from stats_alerts.interface import send_stats_update_embed

                    ts = utcnow().strftime("%Y-%m-%d %H:%M UTC")

                    # ✅ IMPORTANT: is_kvk=True to trigger Pre-KVK path (before Pass 4)
                    await send_stats_update_embed(bot, ts, True, is_test=False)
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

            # NEW: pre-parse for row count (used only for the status embed)
            try:
                pre_df = await _offload_callable(
                    parse_honor_xlsx,
                    file_bytes,
                    name="parse_honor_xlsx",
                    prefer_process=True,
                    meta={"filename": target.filename},
                )
                row_count = len(pre_df)
            except Exception:
                row_count = 0  # don't fail the import if pre-parse fails

            # NEW: preflight check
            ok = await ensure_sql_headroom_or_notify(notify_ch)
            if not ok:
                return

            # Ingest (blocking DB work off-loop) via offload helper
            kvk_no, scan_id = await _offload_callable(
                ingest_honor_snapshot,
                file_bytes,
                source_filename=target.filename,
                scan_ts_utc=message.created_at,  # aware UTC from Discord
                name="ingest_honor_snapshot",
                prefer_process=True,
                meta={"filename": target.filename},
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

            # schedule a background log-backup trigger (best-effort)
            try:
                asyncio.create_task(trigger_log_backup_background())
            except Exception:
                logger.exception("Failed to schedule background log-backup trigger")

            # Optional: refresh stats embed so Honour Top-3 appears/refreshes.
            # Respect test-mode so it won't ping or claim daily limits.
            try:
                from stats_alerts.interface import send_stats_update_embed

                sql_conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={os.environ.get('SQL_SERVER')};DATABASE={os.environ.get('SQL_DATABASE')};UID={os.environ.get('SQL_USERNAME')};PWD={os.environ.get('SQL_PASSWORD')};"
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
            return  # do not fall through to other pipelines

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
                # NEW: preflight check
                ok = await ensure_sql_headroom_or_notify(target_ch)
                if not ok:
                    return

                snap_id, row_count = await _offload_callable(
                    ingest_weekly_activity_excel,
                    content=file_bytes,
                    snapshot_ts_utc=message.created_at,
                    message_id=message.id,
                    channel_id=message.channel.id,
                    server=os.environ.get("SQL_SERVER"),
                    database=os.environ.get("SQL_DATABASE"),
                    username=os.environ.get("SQL_USERNAME"),
                    password=os.environ.get("SQL_PASSWORD"),
                    source_filename=target.filename,
                    name="ingest_weekly_activity_excel",
                    prefer_process=True,
                    meta={"filename": target.filename},
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
                            "Note": "",
                        },
                        0x2ECC71,
                    )

                    # schedule a background log-backup trigger (best-effort)
                    try:
                        asyncio.create_task(trigger_log_backup_background())
                    except Exception:
                        logger.exception("Failed to schedule background log-backup trigger")

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
            os.makedirs(os.path.join(LOG_DIR, "downloads"), exist_ok=True)
        except Exception:
            pass

        results = []
        matched_any = False
        for att in message.attachments:
            if not att.filename.lower().endswith(".xlsx"):
                continue

            local_path = os.path.join(LOG_DIR, "downloads", att.filename)
            try:
                await att.save(local_path)
                fn = att.filename
                logger.info("[RALLY] Saved %s to %s", fn, local_path)

                if is_rally_alltime(fn):
                    matched_any = True
                    logger.info("[RALLY] Detected ALL-TIME file: %s", fn)
                    # NEW: preflight check per-file
                    ok = await ensure_sql_headroom_or_notify(notify_ch)
                    if not ok:
                        results.append(("err", fn, "Aborted: SQL log headroom insufficient"))
                        continue

                    res = await _offload_callable(
                        import_rally_alltime_xlsx,
                        local_path,
                        name="import_rally_alltime_xlsx",
                        prefer_process=True,
                        meta={"path": local_path},
                    )
                    results.append(("ok", fn, res))

                    # schedule a background log-backup trigger (best-effort) for each successful file
                    try:
                        asyncio.create_task(trigger_log_backup_background())
                    except Exception:
                        logger.exception("Failed to schedule background log-backup trigger")
                elif is_rally_daily(fn):
                    matched_any = True
                    logger.info("[RALLY] Detected DAILY file: %s", fn)
                    ok = await ensure_sql_headroom_or_notify(notify_ch)
                    if not ok:
                        results.append(("err", fn, "Aborted: SQL log headroom insufficient"))
                        continue

                    res = await _offload_callable(
                        import_rally_daily_xlsx,
                        local_path,
                        name="import_rally_daily_xlsx",
                        prefer_process=True,
                        meta={"path": local_path},
                    )
                    results.append(("ok", fn, res))

                    # schedule a background log-backup trigger (best-effort) for each successful file
                    try:
                        asyncio.create_task(trigger_log_backup_background())
                    except Exception:
                        logger.exception("Failed to schedule background log-backup trigger")
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

        return  # don't enqueue into the heavy stats pipeline

    # === KVK (all kingdoms) ingest ===
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

                # NEW: preflight check
                ok = await ensure_sql_headroom_or_notify(notify_ch)
                if not ok:
                    await send_embed(
                        notify_ch,
                        "KVK All-Kingdom Import Aborted ❌",
                        {"File": att.filename, "Reason": "SQL log headroom insufficient"},
                        0xE74C3C,
                    )
                    continue

                # Offload heavy importer to an isolated process when available
                result = await _offload_callable(
                    ingest_kvk_all_excel,
                    content=file_bytes,
                    source_filename=att.filename,
                    uploader_id=message.author.id,
                    scan_ts_utc=message.created_at,
                    server=os.environ.get("SQL_SERVER"),
                    database=os.environ.get("SQL_DATABASE"),
                    username=os.environ.get("SQL_USERNAME"),
                    password=os.environ.get("SQL_PASSWORD"),
                    name="ingest_kvk_all_excel",
                    prefer_process=True,
                    meta={"filename": att.filename},
                )

                # Handle structured importer failures (no traceback)
                if isinstance(result, dict) and not result.get("success", True):
                    # concise log (no stacktrace) and user-facing embed
                    logger.info("[KVK] Import failed for %s: %s", att.filename, result.get("error"))
                    await send_embed(
                        notify_ch,
                        "KVK All-Kingdom Import ❌",
                        {
                            "Filename": att.filename,
                            "Channel": f"#{message.channel.name} ({message.channel.id})",
                            "Uploader": f"{message.author} ({message.author.id})",
                            "Error": result.get("error"),
                            "Sheet": result.get("sheet", "unknown"),
                        },
                        0xE74C3C,
                    )
                    continue  # move on to next attachment

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

                sheet_used = result.get("sheet", "unknown")

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
                    "Sheet": sheet_used,
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
                    sheet_id = (
                        ALL_KVK_SHEET_ID
                        or os.environ.get("KVK_SHEET_ID")
                        or os.environ.get("ALL_KVK_SHEET_ID")
                    )
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
                    logger.info("[KVK EXPORT] ALL KVK SHEET ID INVALID")
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

    # === Main monitored channels: enqueue heavy imports for worker processes ===
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

                    # NEW: schedule a background log-backup trigger (best-effort) for main imports
                    # This reduces the window where transaction log bursts between scheduled backups can cause aborts.
                    try:
                        asyncio.create_task(trigger_log_backup_background())
                    except Exception:
                        logger.exception(
                            "Failed to schedule background log-backup trigger for queued import"
                        )

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

    await _offload_callable(_do_write, name="write_shutdown_markers", prefer_process=False)


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
