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
    expected_paths = {
        (Path(LOG_DIR).parent / name / "Scripts" / "python.exe").resolve()
        for name in ("venv", ".venv")
    }
    actual = Path(sys.executable).resolve()
    if actual not in expected_paths:
        expected_display = ", ".join(str(p) for p in sorted(expected_paths))
        logger.critical(
            "❌ Wrong interpreter: %s (expected one of: %s). Exiting.",
            actual,
            expected_display,
        )
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
import json
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
    INVENTORY_UPLOAD_CHANNEL_ID,
    MGE_DATA_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
    PLAYER_LOCATION_CHANNEL_ID,
    PREKVK_CHANNEL_ID,
    PROKINGDOM_CHANNEL_ID,
)
from bot_helpers import channel_queues
from Commands import register_commands
from embed_utils import send_embed
from kvk_all_importer import _auto_export_kvk
from log_health import LogHeadroomError, preflight_from_env_sync
from upload_routes.fallback_queue_route import (
    FallbackQueueRouteDeps,
    handle_fallback_queue_upload,
)
from upload_routes.honor_route import HonorRouteDeps, handle_honor_upload
from upload_routes.inventory_route import InventoryRouteDeps, handle_inventory_upload
from upload_routes.kvk_all_route import KvkAllRouteDeps, handle_kvk_all_upload
from upload_routes.mge_results_route import MgeResultsRouteDeps, handle_mge_results_upload
from upload_routes.player_location_route import (
    PlayerLocationRouteDeps,
    handle_player_location_upload,
)
from upload_routes.prekvk_route import PreKvkRouteDeps, handle_prekvk_upload
from upload_routes.rally_forts_route import RallyFortsRouteDeps, handle_rally_forts_upload
from upload_routes.weekly_activity_route import (
    WeeklyActivityRouteDeps,
    handle_weekly_activity_upload,
)
from utils import live_queue, live_queue_lock, update_live_queue_embed, utcnow

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


# === Global Error Logging ===
@bot.event
async def on_error(event_method, *args, **kwargs):
    logger.exception("💥 Unhandled error in %s", event_method)


@bot.event
async def on_message(message: discord.Message):
    if not bot.user or message.author.id == bot.user.id:
        return

    # MGE Task G: route DM attachment messages to active MGE DM sessions
    if message.guild is None and not message.author.bot:
        try:
            from mge import mge_dm_followup

            handled = await mge_dm_followup.route_dm_message(message)
            if handled:
                return
        except Exception:
            logger.exception("mge_dm_followup_route_unexpected_failed")

    # === Fast-path: inventory image upload-first import ===
    if await handle_inventory_upload(
        message,
        InventoryRouteDeps(
            inventory_upload_channel_id=INVENTORY_UPLOAD_CHANNEL_ID,
            bot=bot,
        ),
    ):
        return

    # === Fast-path: Player Location CSV auto-import ===
    if await handle_player_location_upload(
        message,
        PlayerLocationRouteDeps(
            player_location_channel_id=PLAYER_LOCATION_CHANNEL_ID,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            trigger_log_backup_background=trigger_log_backup_background,
        ),
    ):
        return

    # === Fast-path: MGE results auto-import ===
    if await handle_mge_results_upload(
        message,
        MgeResultsRouteDeps(
            mge_data_channel_id=MGE_DATA_CHANNEL_ID,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            trigger_log_backup_background=trigger_log_backup_background,
        ),
    ):
        return

    # === Fast-path: Pre-KVK snapshot ingest (dynamic KVK lookup) ===
    if await handle_prekvk_upload(
        message,
        PreKvkRouteDeps(
            prekvk_channel_id=PREKVK_CHANNEL_ID,
            bot=bot,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            trigger_log_backup_background=trigger_log_backup_background,
        ),
    ):
        return

    # === Fast-path: KVK Honour ingest (full snapshots, multiple/day) ===
    if await handle_honor_upload(
        message,
        HonorRouteDeps(
            honor_channel_id=HONOR_CHANNEL_ID,
            bot=bot,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            trigger_log_backup_background=trigger_log_backup_background,
        ),
    ):
        return

    # --- Fast-path: Weekly activity ingest ---
    if await handle_weekly_activity_upload(
        message,
        WeeklyActivityRouteDeps(
            activity_upload_channel_id=ACTIVITY_UPLOAD_CHANNEL_ID,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            trigger_log_backup_background=trigger_log_backup_background,
            server=os.environ.get("SQL_SERVER"),
            database=os.environ.get("SQL_DATABASE"),
            username=os.environ.get("SQL_USERNAME"),
            password=os.environ.get("SQL_PASSWORD"),
        ),
    ):
        return

    # === Fast-path: Rally Forts XLSX auto-ingest (hardened) ===
    if await handle_rally_forts_upload(
        message,
        RallyFortsRouteDeps(
            fort_rally_channel_id=FORT_RALLY_CHANNEL_ID,
            log_dir=LOG_DIR,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            trigger_log_backup_background=trigger_log_backup_background,
        ),
    ):
        return

    # === KVK (all kingdoms) ingest ===
    if await handle_kvk_all_upload(
        message,
        KvkAllRouteDeps(
            prokingdom_channel_id=PROKINGDOM_CHANNEL_ID,
            bot=bot,
            get_notify_channel=_get_notify_channel,
            send_embed=send_embed,
            ensure_sql_headroom_or_notify=ensure_sql_headroom_or_notify,
            offload_callable=_offload_callable,
            auto_export_enabled=KVK_AUTO_EXPORT,
            auto_export_scheduler=_auto_export_kvk,
            get_sheet_id=lambda: (
                ALL_KVK_SHEET_ID
                or os.environ.get("KVK_SHEET_ID")
                or os.environ.get("ALL_KVK_SHEET_ID")
            ),
        ),
    ):
        return

    # === Main monitored channels: enqueue heavy imports for worker processes ===
    await handle_fallback_queue_upload(
        message,
        FallbackQueueRouteDeps(
            channel_ids=CHANNEL_IDS,
            channel_queues=channel_queues,
            live_queue=live_queue,
            live_queue_lock=live_queue_lock,
            bot=bot,
            notify_channel_id=NOTIFY_CHANNEL_ID,
            update_live_queue_embed=update_live_queue_embed,
            trigger_log_backup_background=trigger_log_backup_background,
            utcnow=utcnow,
        ),
    )
    await bot.process_commands(message)


#
# ===== Commit 2: Signal-safe async graceful shutdown (Windows-first) =====
#

# Idempotent guard + timeout
_closing = False
_closing_lock = threading.Lock()
_SHUTDOWN_TIMEOUT_SECONDS = 10


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
    Stop app-owned schedulers/registries before closing the Discord client.
    Must be safe/idempotent if called multiple times.
    """
    try:
        from bot_instance import run_graceful_teardown

        await run_graceful_teardown()
        return
    except Exception:
        logger.exception("[SHUTDOWN] bot_instance graceful teardown failed.")

    # Fallback only: keep the previous narrow cleanup if the bot teardown import/path fails.
    try:
        from reminder_task_registry import TaskRegistry

        await TaskRegistry.cancel_all(timeout=5)
    except Exception:
        logger.debug("[SHUTDOWN] TaskRegistry fallback cancel skipped or failed.", exc_info=True)
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
