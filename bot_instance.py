# bot_instance.py
import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
import csv
from datetime import datetime, timedelta
from functools import partial
import json
import logging
import logging.handlers
import os
import platform
import random
import sys
import tempfile
import traceback
from typing import Any

import discord
from discord.ext import tasks

from ark.ark_scheduler import schedule_ark_lifecycle
from boot_safety import apply_boot_safety
from bot_config import (
    ACTIVITY_UPLOAD_CHANNEL_ID,
    ADMIN_USER_ID,
    CHANNEL_IDS,
    KVK_EVENT_CHANNEL_ID,
    KVK_NOTIFICATION_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
    STATUS_CHANNEL_ID,
)
from bot_helpers import (
    commands_changed,
    connection_watchdog,
    get_command_signature,
    load_command_signatures,
    prune_restart_log,
    queue_cleanup_loop,
    queue_worker,
    save_command_signatures,
)
from bot_loader import bot
from bot_startup_gate import claim_startup_once
from constants import (
    COMMAND_CACHE_FILE,
    CREDENTIALS_FILE,
    CSV_LOG,
    DATABASE,
    FAILED_LOG,
    INPUT_LOG,
    KVK_SHEET_ID,
    LAST_RESTART_INFO,
    LAST_SHUTDOWN_INFO,
    PASSWORD,
    REMINDER_TRACKING_FILE,
    RESTART_LOG_FILE,
    SERVER,
    STATS_SHEET_ID,
    SUMMARY_LOG,
    USERNAME,
)
from crystaltech_di import init_crystaltech_service
from daily_KVK_overview_embed import post_or_update_daily_KVK_overview
from embed_utils import expire_old_event_embeds, send_summary_embed
from event_cache import (
    get_all_upcoming_events,
    is_cache_stale,
    load_event_cache,
    refresh_event_cache,
)
from event_embed_manager import rehydrate_live_event_views, update_live_event_embeds
from event_scheduler import (
    cleanup_orphaned_reminders,
    load_active_reminders,
    load_dm_scheduled_tracker,
    load_dm_sent_tracker,
    refresh_reminder_format,
    reminder_cleanup_loop,
    schedule_event_reminders,
)

# added emit_telemetry_event import
from file_utils import append_csv_line, emit_telemetry_event, fetch_one_dict, run_blocking_in_thread
from gsheet_module import check_basic_gsheets_access  # <-- add
from logging_setup import (
    LOG_DIR,
    clean_old_lock_files,
)
from player_stats_cache import (  # optional, see note
    build_lastkvk_player_stats_cache,
    build_player_stats_cache,
)
from proc_config_import import run_proc_config_import, run_proc_config_import_offload
from profile_cache import get_cache_stats, warm_cache as warm_profile_cache
from rehydrate_views import rehydrate_tracked_views
from subscription_tracker import load_subscriptions
from target_utils import warm_name_cache
from utils import ensure_aware_utc, load_live_queue, update_live_queue_embed, utcnow

# offload monitor integration
try:
    from offload_monitor_lib import monitor_loop_coro  # scheduled via task_monitor
except Exception:
    monitor_loop_coro = None

# ensure asyncio is imported at top of file if not already

apply_boot_safety()

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

# Usage tracker (for component + autocomplete logging)
from decoraters import usage_tracker  # lazy singleton; safe to import here


def _aware(dt: datetime) -> datetime:
    """Ensure dt is timezone-aware in UTC."""
    return ensure_aware_utc(dt)


START_TIME = _aware(utcnow())


async def _with_timeout(coro, seconds: float, label: str):
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except TimeoutError:
        logger.warning("[BOOT] %s timed out after %.1fs; deferring.", label, seconds)
        # Emit telemetry so operators can track boot-time timeouts
        try:
            emit_telemetry_event(
                {
                    "event": "boot_step_timeout",
                    "label": label,
                    "status": "timeout",
                    "timeout_seconds": seconds,
                    "orphaned_offload_possible": False,
                }
            )
        except Exception:
            logger.debug("[TELEMETRY] Failed to emit boot_step_timeout telemetry", exc_info=True)
        return None
    except Exception as e:
        logger.exception("[BOOT] %s failed: %s", label, e)
        try:
            emit_telemetry_event(
                {
                    "event": "boot_step_failed",
                    "label": label,
                    "status": "failed",
                    "error": str(e),
                    "orphaned_offload_possible": False,
                }
            )
        except Exception:
            logger.debug("[TELEMETRY] Failed to emit boot_step_failed telemetry", exc_info=True)
        return None


async def _jittered(min_s=0.4, max_s=1.2):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def wait_for_events(timeout_seconds: int = 10) -> bool:
    """Return True as soon as we have at least 1 upcoming event, else False after timeout."""
    checks = int(max(1, timeout_seconds) * 10)
    for _ in range(checks):
        try:
            if get_all_upcoming_events():  # non-empty list means ready
                return True
        except Exception:
            pass
        await asyncio.sleep(0.1)
    return False


def schedule_bg(name: str, timeout: float, coro_factory: Callable[[], Awaitable[Any]]):
    async def _runner():
        await _jittered()
        await _with_timeout(coro_factory(), timeout, name)

    task_monitor.create(name, _runner)


async def _start_event_dependent_tasks():
    """Start tasks that require a ready event cache."""
    # Live embeds
    task_monitor.create("periodic_live_embed_update", periodic_live_embed_update)
    logger.info("[BOOT] Live event embed updater scheduled")

    # Daily KVK overview
    try:
        task_monitor.create("daily_kvk_overview", schedule_daily_KVK_overview)
        logger.info("[BOOT] Daily KVK overview embed updater scheduled")
    except Exception as e:
        logger.error(f"[BOOT] Failed to start Daily KVK overview embed updater: {e}")

    # Reminders
    try:
        task_monitor.create(
            "schedule_event_reminders",
            lambda: schedule_event_reminders(bot, KVK_NOTIFICATION_CHANNEL_ID, test_mode=False),
        )
        logger.info("[BOOT] Event reminder scheduler started")
    except Exception as e:
        logger.error(f"[BOOT] Failed to start schedule_event_reminders: {e}")

    # Refresh reminder formatting
    try:
        await _with_timeout(
            refresh_reminder_format(bot, KVK_NOTIFICATION_CHANNEL_ID),
            8.0,
            "refresh_reminder_format",
        )
        logger.info("Reminders refreshed")
    except Exception as e:
        logger.error(f"[BOOT] Failed to start refresh_reminder_format: {e}")

    # Rehydrate views that depend on events
    try:
        await _with_timeout(
            rehydrate_live_event_views(bot, KVK_EVENT_CHANNEL_ID),
            10.0,
            "rehydrate_live_event_views",
        )
        logger.info("[BOOT] rehydrate_live_event_views complete")
    except Exception:
        logger.error("[BOOT] Failed to start rehydrate_live_event_views: {e}")

    # Scheduled expiry
    try:
        task_monitor.create("event_embed_expiry", schedule_event_embed_expiry)
        logger.info("[BOOT] Event embed expiry task scheduled for 08:00 UTC daily")
    except Exception as e:
        logger.error(f"[BOOT] Failed to start event_embed_expiry task: {e}")


async def _start_event_tasks_when_ready(max_wait_seconds: int = 300):
    """
    Block until the event cache has at least one upcoming event (or timeout),
    then start all event-dependent background tasks exactly once.
    """
    try:
        ready = await wait_for_events(timeout_seconds=max_wait_seconds)
        if not ready:
            logger.warning(
                "[BOOT] Event cache still not ready after %ss; "
                "skipping event-dependent task start for now.",
                max_wait_seconds,
            )
            return
        await _start_event_dependent_tasks()
    except Exception as e:
        logger.exception("[BOOT] _start_event_tasks_when_ready failed: %s", e)


# wrap blockers
async def run_blocking(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


# --- Global asyncio loop exception handler (install once per process) ---
def global_asyncio_exception_handler(loop, context):
    try:
        msg = context.get("message")
        exc = context.get("exception")
        where = context.get("future") or context.get("handle") or context.get("task")
        where_info = f" where={where!r}" if where else ""

        if exc is not None:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            logger.error("[LOOP EXC]%s %s\n%s", where_info, (msg or ""), tb)
        else:
            logger.error("[LOOP EXC]%s %s | context=%r", where_info, (msg or ""), context)
    except Exception:
        # Last-ditch: logging subsystem might be broken; write plain text to stderr
        try:
            sys.__stderr__.write("[LOOP EXC] (fallback) Unhandled loop exception\n")
        except Exception:
            pass


def quiesce_logging():
    """
    Remove/disable any console-like stream handlers to avoid blocking writes
    during teardown. Keep the QueueHandler (non-blocking) in place so logs
    continue to flow to the QueueListener-owned file handlers until final shutdown.
    """
    root = logging.getLogger()
    for h in list(root.handlers):
        try:
            # Remove only console-ish stream handlers (stdout/stderr),
            # but keep FileHandler/RotatingFileHandler and QueueHandler.
            from logging.handlers import QueueHandler

            is_file = isinstance(h, (logging.FileHandler, logging.handlers.RotatingFileHandler))
            is_queue = isinstance(h, QueueHandler)
            is_console_like = isinstance(h, logging.StreamHandler) and not is_file
            if is_console_like and not is_queue:
                root.removeHandler(h)
                try:
                    h.close()
                except Exception:
                    pass
        except Exception:
            pass


def _drop_console_handlers_once():
    """Defensive: remove any console StreamHandlers a lib might have added."""
    root = logging.getLogger()
    for h in list(root.handlers):
        try:
            is_file = isinstance(h, (logging.FileHandler, logging.handlers.RotatingFileHandler))
            is_console_like = isinstance(h, logging.StreamHandler) and not is_file
            if is_console_like:
                root.removeHandler(h)
                try:
                    h.close()
                except Exception:
                    pass
        except Exception:
            pass


# ---------------- Usage logging helpers for interactions -------------------
def _clip(s: str | None, n: int) -> str | None:
    if s is None:
        return None
    s = str(s)
    return s if len(s) <= n else s[:n]


def _interaction_app_context(ir: discord.Interaction) -> str:
    """
    Map interaction types to our compact app_context values.
    """
    try:
        # py-cord / discord.py expose Interaction.type as an enum; also expose .data for components
        tname = (
            getattr(getattr(ir, "type", None), "name", None) or str(getattr(ir, "type", "")).lower()
        )
        if "autocomplete" in (tname or "").lower():
            return "autocomplete"
        if "component" in (tname or "").lower():
            # Distinguish button vs. select via component_type (2=button, 3/5/6/7/8=select variants)
            data = ir.data or {}
            ctype = data.get("component_type")
            if ctype == 2:
                return "button"
            return "select"
        if "application_command" in (tname or "").lower():
            return "slash"
        return (tname or "component").lower()
    except Exception:
        return "component"


async def _log_interaction_usage(ir: discord.Interaction):
    """
    Best-effort, non-blocking log of buttons/selects/autocomplete.
    We DO NOT log values the user typed; just the command/custom_id.
    """
    try:
        app_ctx = _interaction_app_context(ir)
        if app_ctx == "slash":
            return  # slash commands are handled by @track_usage on handlers

        # Derive a short name:
        # - For autocomplete: "autocomplete:<command_name>"
        # - For components:   custom_id (from your UI)
        cmd_name: str | None = None
        if app_ctx == "autocomplete":
            data = ir.data or {}
            # 'name' is the command the option belongs to; keep it short & neutral
            cmd_name = f"autocomplete:{data.get('name','unknown')}"
        else:
            # component (button/select): prefer custom_id
            data = ir.data or {}
            cmd_name = data.get("custom_id") or "component"

        # Enforce DB widths to avoid ODBC truncation errors
        cmd_name = _clip(cmd_name, 64)
        app_ctx_c = _clip(app_ctx, 16)
        user_disp = _clip(getattr(ir.user, "display_name", None), 128)

        evt = {
            "executed_at_utc": _aware(utcnow()).isoformat(),
            "command_name": cmd_name,
            "version": None,
            "app_context": app_ctx_c,
            "user_id": getattr(ir.user, "id", None),
            "user_display": user_disp,
            "guild_id": (
                getattr(getattr(ir, "guild", None), "id", None) if hasattr(ir, "guild") else None
            ),
            "channel_id": (
                getattr(getattr(ir, "channel", None), "id", None)
                if hasattr(ir, "channel")
                else None
            ),
            "success": True,  # passive click/usage log; failures are captured by handlers
            "error_code": None,
            "latency_ms": None,
            "args_shape": None,
        }
        # Fire-and-forget into the async tracker (which writes JSONL and batches to SQL)
        asyncio.create_task(usage_tracker().log(evt))
    except Exception:
        # Absolutely do not break interaction handling due to logging
        return


# --- Heartbeat + Task Monitor ------------------------------------------------
def _atomic_json_write(path: str, data: dict | list, *, mode="w", encoding="utf-8"):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".hb.", suffix=".tmp")
    try:
        with os.fdopen(fd, mode, encoding=encoding) as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


class TaskMonitor:
    """Supervise background tasks; auto-restart on crash with capped backoff."""

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}
        self._restarts: dict[str, int] = {}
        self._last_error: dict[str, str | None] = {}
        self._backoff: dict[str, float] = {}
        self._factories: dict[str, Callable[[], Awaitable[Any]]] = {}
        self._active = True

    def is_running(self, name: str) -> bool:
        t = self._tasks.get(name)
        return bool(t and not t.done())

    def create(self, name: str, coro_factory, *, replace: bool = False):
        """
        Register and start a background task from a coroutine FACTORY.
        Pass the function (no parentheses). If the task is already running
        and replace==False, this is a no-op and does not instantiate the coroutine.
        """
        if self.is_running(name) and not replace:
            logger.warning("[MONITOR] Task %s already running; not creating a duplicate.", name)
            return self._tasks[name]

        # Store/overwrite the factory so restarts use the same one
        self._factories[name] = coro_factory

        # Build coroutine *only when we intend to schedule it*
        coro = coro_factory()
        t = asyncio.create_task(coro, name=name)
        self._tasks[name] = t
        self._last_error.setdefault(name, None)
        self._restarts.setdefault(name, 0)
        self._backoff.setdefault(name, 1.0)
        t.add_done_callback(lambda fut, n=name: asyncio.create_task(self._on_done(n, fut)))
        logger.info("[MONITOR] Task started: %s", name)
        return t

    async def _on_done(self, name: str, fut: asyncio.Task):
        if not self._active:
            return
        try:
            exc = fut.exception()
        except asyncio.CancelledError:
            exc = None
        except Exception as e:
            exc = e

        if exc:
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            self._last_error[name] = f"{type(exc).__name__}: {exc}\n{tb}"
            self._restarts[name] += 1

            delay = min(60.0, self._backoff.get(name, 1.0))
            self._backoff[name] = min(60.0, max(1.0, delay * 2))
            logger.error("[MONITOR] Task %s crashed; restarting in %.1fs\n%s", name, delay, tb)
            await asyncio.sleep(delay)

            # Restart via the stored factory if available
            factory = self._factories.get(name)
            if factory:
                self.create(name, factory)
            else:
                logger.error("[MONITOR] No factory stored for %s; cannot restart.", name)
        else:
            self._backoff[name] = 1.0
            self._last_error[name] = None
            logger.info("[MONITOR] Task %s completed.", name)

    def list(self):
        out = []
        for name, task in self._tasks.items():
            out.append(
                {
                    "name": name,
                    "done": task.done(),
                    "cancelled": task.cancelled(),
                    "restarts": self._restarts.get(name, 0),
                    "last_error": self._last_error.get(name),
                }
            )
        return out

    # In TaskMonitor
    async def stop(self):
        self._active = False
        tasks = [t for t in self._tasks.values() if not t.done()]
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()  # optional
        logger.info("[MONITOR] Stop requested; tasks cancelled where applicable.")


task_monitor = TaskMonitor()


async def heartbeat_loop():
    """Write periodic health snapshot to LOG_DIR/heartbeat.json."""
    hb_path = os.path.join(LOG_DIR, "heartbeat.json")
    pid = os.getpid()
    while True:
        try:
            # Collect metrics
            now = _aware(utcnow())
            uptime = (now - START_TIME).total_seconds()
            latency = getattr(bot, "latency", None)
            try:
                guild_count = len(bot.guilds)
            except Exception:
                guild_count = None
            try:
                cmd_count = len(bot.application_commands)
            except Exception:
                cmd_count = None

            # Optional memory stats via psutil if present
            mem_info = None
            try:
                import psutil  # optional

                p = psutil.Process(pid)
                mem = p.memory_info()
                mem_info = {"rss": mem.rss, "vms": mem.vms}
            except Exception:
                mem_info = None

            data = {
                "ts": now.isoformat(),
                "pid": pid,
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "uptime_sec": int(uptime),
                "latency_sec": float(latency) if latency is not None else None,
                "guilds": guild_count,
                "commands": cmd_count,
                "tasks": task_monitor.list(),
            }
            if mem_info:
                data["memory"] = mem_info

            _atomic_json_write(hb_path, data)

        except Exception as e:
            logger.error("[HEARTBEAT] Failed to write heartbeat: %s", e)

        await asyncio.sleep(30)


# === Health dashboard (Phase 1) =============================================
HEALTH_MSG_ID_PATH = os.path.join(LOG_DIR, "health_msg_id.json")
ERROR_SPIKE_THRESHOLD = 5  # DM admin if >= this many ERROR lines in last 60m
STALENESS_THRESHOLD_MIN = 15  # DM admin if health embed wasn't updated within N minutes (rare)
HEALTH_REFRESH_MINUTES = 5  # embed update cadence

# state for alerts/debounce
_last_health_alert_ts: datetime | None = None
_last_health_embed_update_ts: datetime | None = None

# record of last discord session state (for the card)
LAST_DISCONNECT_UTC: datetime | None = None
LAST_RESUME_UTC: datetime | None = None


def _safe_error_log_path() -> str:
    try:
        from logging_setup import ERROR_LOG_PATH

        if ERROR_LOG_PATH and os.path.exists(ERROR_LOG_PATH):
            return ERROR_LOG_PATH
    except Exception:
        pass
    # common fallbacks
    for name in ("error_log.txt", "error.log"):
        candidate = os.path.join(LOG_DIR, name)
        if os.path.exists(candidate):
            return candidate
    # last resort
    return os.path.join(LOG_DIR, "error_log.txt")


async def _count_errors_last_minutes(
    minutes: int = 60, level: str = "ERROR", cap: int = 50000
) -> int:
    """
    Count only real [LEVEL] lines within the last N minutes.
    Expected prefix: 'YYYY-MM-DD HH:MM:SS,fff ' (23 chars) before the level token.
    """
    path = _safe_error_log_path()
    if not os.path.exists(path) or minutes <= 0:
        return 0

    cutoff = _aware(utcnow()) - timedelta(minutes=minutes)
    ts_len = 23  # len('YYYY-MM-DD HH:MM:SS,%f')
    pat = f"[{(level or 'ERROR').upper()}]"

    try:
        # Read and keep only the last `cap` lines (cap<=0 means keep all)
        if cap and cap > 0:
            buf = deque(maxlen=cap)
            with open(path, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    buf.append(ln)
            lines = buf
        else:
            with open(path, encoding="utf-8", errors="replace", newline="") as f:
                lines = f.readlines()

        count = 0
        for ln in lines:
            if pat not in ln:
                continue
            # parse timestamp prefix if present
            ts_str = ln[:ts_len]
            try:
                ts = _aware(datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f"))
            except Exception:
                # skip lines with no/invalid timestamp
                continue
            if ts >= cutoff:
                count += 1

        return count

    except Exception:
        return 0


async def _check_sql_health(timeout_sec: float = 3.0) -> tuple[bool, str | None]:
    """
    Probe SQL health.

    Strategy:
    1) If pyodbc isn't installed, skip the probe (treat as OK).
    2) Prefer using the shared constants._conn() helper (single source of truth).
       If that succeeds, we're healthy.
    3) If constants._conn() is unavailable or fails, fall back to attempting configured
       driver names. Only try drivers that appear installed via pyodbc.drivers() when possible.
    4) Keep per-driver failures at DEBUG to avoid log noise; emit a single WARNING only
       if all attempts fail.
    """
    try:
        import pyodbc
    except Exception:
        # Can't probe without pyodbc — avoid noisy warnings on hosts that don't have DB deps.
        logger.debug("pyodbc not available; skipping SQL health probe")
        return True, None

    # Prefer the project's canonical connector if available
    try:
        from constants import _conn as _default_conn  # lazy import
    except Exception:
        _default_conn = None

    last_err: str | None = None

    if _default_conn is not None:
        try:
            conn = _default_conn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                _ = fetch_one_dict(cur)  # value not used, use helper for consistency
            conn.close()
            return True, None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            logger.warning("[HEALTH][SQL] Probe via constants._conn failed: %s", last_err)
            # fall through to driver-based fallback

    # Fallback: try known driver names, but only those actually installed when possible
    dsn_list = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    ]

    installed_drivers: list[str] = []
    try:
        installed_drivers = [d for d in pyodbc.drivers() if d]
    except Exception:
        # enumeration failed — we'll try the configured dsn_list as a best-effort
        logger.debug("pyodbc.drivers() failed or unavailable; attempting configured driver names")

    if installed_drivers:
        to_try = [d for d in dsn_list if d in installed_drivers]
        if not to_try:
            # No matching drivers installed; skip probe to avoid repeated IM002 noise.
            logger.info(
                "No matching ODBC drivers installed (expected: %s, installed: %s); skipping SQL probe",
                dsn_list,
                installed_drivers,
            )
            return True, None
    else:
        to_try = dsn_list

    int_timeout = int(timeout_sec)

    for driver in to_try:
        try:
            conn = pyodbc.connect(
                f"DRIVER={{{driver}}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};"
                "Encrypt=yes;TrustServerCertificate=Yes;",
                timeout=int_timeout,
                autocommit=True,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                _ = fetch_one_dict(cur)
            conn.close()
            return True, None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            # Keep per-driver failures at DEBUG to reduce noise
            logger.debug("[HEALTH][SQL] Probe failed via '%s': %s", driver, last_err)

    # All attempts failed — emit single warning with final error
    logger.warning(
        "[HEALTH][SQL] All SQL driver probes failed: %s", last_err or "Unknown SQL error"
    )
    return False, last_err or "Unknown SQL error"


def _pick_health_sheet_id() -> str | None:
    """
    Choose a representative Sheet to probe for health.
    Prefer KVK_SHEET_ID; fall back to STATS_SHEET_ID.
    """
    try:
        if KVK_SHEET_ID:
            return KVK_SHEET_ID
    except Exception:
        pass
    try:
        if STATS_SHEET_ID:
            return STATS_SHEET_ID
    except Exception:
        pass
    return None


async def _check_gsheets_health(timeout_sec: float = 5.0):
    """
    Run the synchronous GSheets health check off the event loop with a timeout.
    Returns (success: bool, message: str)
    """
    sheet_id = _pick_health_sheet_id()
    if not sheet_id:
        # No configured sheet to probe; don't fail health for this
        return True, "No sheet configured for probe"

    try:
        # Run the blocking function in a thread and bound the total wait time
        success, message = await asyncio.wait_for(
            run_blocking_in_thread(
                check_basic_gsheets_access,
                CREDENTIALS_FILE,
                sheet_id,
                name="check_basic_gsheets_access",
                meta={"sheet_id": sheet_id},
            ),
            timeout=timeout_sec,
        )
        return success, message
    except asyncio.CancelledError:
        # Preserve cancellation so shutdown isn't swallowed; log then re-raise
        logger.warning("[HEALTH][GS] _check_gsheets_health cancelled")
        raise
    except TimeoutError:
        # Fast fail if the GSheets call times out — don't block the event loop
        logger.warning("[HEALTH][GS] GSheets check timed out after %.1fs", timeout_sec)
        try:
            emit_telemetry_event(
                {
                    "event": "gsheets_health_check",
                    "status": "timeout",
                    "timeout_seconds": timeout_sec,
                    "orphaned_offload_possible": True,
                }
            )
        except Exception:
            logger.debug(
                "[TELEMETRY] Failed to emit gsheets_health_check timeout telemetry", exc_info=True
            )
        return False, f"GSheets check timed out after {timeout_sec}s"
    except Exception as exc:
        # Log full exception with stack for diagnostics and return failure
        logger.exception("[HEALTH][GS] GSheets check raised exception: %s", exc)
        try:
            emit_telemetry_event(
                {
                    "event": "gsheets_health_check",
                    "status": "failed",
                    "error": str(exc),
                    "orphaned_offload_possible": False,
                }
            )
        except Exception:
            logger.debug(
                "[TELEMETRY] Failed to emit gsheets_health_check failed telemetry", exc_info=True
            )
        return False, f"GSheets check raised exception: {exc}"


def _uptime_hms() -> tuple[int, int, int, int]:
    """Return uptime as (days, hours, minutes, seconds)."""
    now = _aware(utcnow())
    sec = int((now - START_TIME).total_seconds())
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return d, h, m, s


def _get_queue_depth_safe() -> int:
    """Hook point for your real in-memory queue depth if exposed; fallback to 0."""
    try:
        # if you expose a global or helper returning the count, call it here
        from utils import get_live_queue_depth  # if you made one

        return int(get_live_queue_depth())
    except Exception:
        return 0


def _summarize_tasks() -> str:
    """Short status for TaskMonitor tasks: running count + crashed count + restarts."""
    entries = task_monitor.list()
    if not entries:
        return "none"
    running = sum(1 for e in entries if not e["done"] and not e["cancelled"])
    crashed = sum(1 for e in entries if e["done"] and e.get("last_error"))
    restarts = sum(int(e.get("restarts", 0) or 0) for e in entries)
    return f"running {running} • crashed {crashed} • restarts {restarts}"


class HealthView(discord.ui.View):
    def __init__(self, *, timeout: float = 30):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.primary, emoji="🔄")
    async def do_refresh(self, _button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # build latest embed exactly as you do in _update_health_embed()
            d, h, m, s = _uptime_hms()
            sql_ok, sql_reason = await _check_sql_health(timeout_sec=5)
            gs_ok, gs_message = await _check_gsheets_health(timeout_sec=5)
            err_10m = await _count_errors_last_minutes(10)
            err_60m = await _count_errors_last_minutes(60)
            queue_depth = _get_queue_depth_safe()
            latency = getattr(bot, "latency", None)
            latency_ms = int(latency * 1000) if latency is not None else None

            # Profile cache stats (best-effort)
            try:
                pc_stats = get_cache_stats()
                pc_count = pc_stats.get("count", 0)
                pc_loaded = pc_stats.get("loaded_at_iso")
                profile_line = f"\n**Profiles:** {pc_count} cached" + (
                    f" • as_of {pc_loaded}" if pc_loaded else ""
                )
            except Exception:
                profile_line = "\n**Profiles:** n/a"

            sess = "🟢 connected"
            if LAST_DISCONNECT_UTC and (
                not LAST_RESUME_UTC or LAST_RESUME_UTC < LAST_DISCONNECT_UTC
            ):
                sess = "🟠 disconnected"
            elif LAST_RESUME_UTC and LAST_DISCONNECT_UTC and LAST_RESUME_UTC > LAST_DISCONNECT_UTC:
                sess = "🟡 resumed"

            desc = (
                f"**Uptime:** {d}d {h}h {m}m {s}s\n"
                f"**Discord:** {sess}"
                + (f" • ping ~{latency_ms} ms" if latency_ms is not None else "")
                + "\n"
                f"**Database:** {'🟢 OK' if sql_ok else '🔴 Error'}"
                + (f" — `{(sql_reason or '')[:120]}`" if not sql_ok else "")
                + "\n"
                f"**GSheets:** {'🟢 ' if gs_ok else '🔴 '}{gs_message}\n"
                f"**Errors:** 10m **{err_10m}** • 60m **{err_60m}**\n"
                f"**Queue depth:** {queue_depth}\n"
                f"{profile_line}\n"
                f"**Tasks:** {_summarize_tasks()}\n"
            )
            if sql_ok and gs_ok and sess == "🟢 connected" and err_10m == 0 and err_60m == 0:
                color = 0x2ECC71
            elif err_10m > 0 and sql_ok and gs_ok:
                color = 0xF39C12
            else:
                color = (
                    0xE74C3C
                    if (
                        not sql_ok
                        or not gs_ok
                        or err_60m >= ERROR_SPIKE_THRESHOLD
                        or sess != "🟢 connected"
                    )
                    else 0xF39C12
                )

            embed = discord.Embed(title="🤖 Bot Health", description=desc, color=color)
            embed.set_footer(text="Auto-updates every 5 minutes • Use /logs for details")
            embed.timestamp = _aware(utcnow())

            # This both ACKs the interaction and edits the message in one go.
            await interaction.response.edit_message(embed=embed, view=HealthView())

        except discord.errors.InteractionResponded:
            # Fallback: if somehow already acked, edit the message object
            await interaction.message.edit(embed=embed, view=HealthView())
        except Exception as e:
            # As a last resort, send an ephemeral error (ensures no 'interaction failed')
            msg = f"Refresh failed: `{type(e).__name__}: {e}`"
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            logger.warning(f"[HEALTH] refresh failed: {e}")

    @discord.ui.button(label="Show last 20 errors", style=discord.ButtonStyle.secondary, emoji="📜")
    async def show_last_errors(self, _button: discord.ui.Button, interaction: discord.Interaction):
        try:
            path = _safe_error_log_path()
            if not os.path.exists(path):
                content = "No error log file found."
            else:
                lines = []
                with open(path, encoding="utf-8", errors="replace", newline="") as f:
                    for ln in f:
                        if "[ERROR]" in ln:
                            lines.append(ln.rstrip("\n"))

                # newest first, up to 20
                lines = list(reversed(lines))[:20]

                if not lines:
                    content = "(no [ERROR] lines found in log)"
                else:
                    body = "\n".join(lines).replace("```", "`\u200b``")

                    # Tip shown after code block
                    tip = "\nTip: use `/logs source:error level:ERROR page_size:50` for paging."
                    # Strict budget: 2000 total, minus fences (6 chars) and tip
                    BUDGET = 2000 - len(tip) - 6
                    if BUDGET < 0:
                        BUDGET = 0
                    if len(body) > BUDGET:
                        # leave room for truncation marker
                        body = body[: max(0, BUDGET - 14)] + "\n…(truncated)"

                    content = f"```{body}```{tip}"

            if not interaction.response.is_done():
                await interaction.response.send_message(content, ephemeral=True)
            else:
                await interaction.followup.send(content, ephemeral=True)

        except Exception as e:
            msg = f"❌ Failed to load last errors: `{type(e).__name__}: {e}`"
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)


async def _ensure_pinned_health_message(channel: discord.TextChannel) -> int:
    """Create or fetch the pinned health message; returns message ID."""
    msg_id = None
    try:
        if os.path.exists(HEALTH_MSG_ID_PATH):
            msg_id = json.load(open(HEALTH_MSG_ID_PATH, encoding="utf-8")).get("id")
    except Exception:
        msg_id = None

    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            return msg.id
        except Exception:
            msg_id = None

    # Create a placeholder message and pin it
    m = await channel.send(
        embed=discord.Embed(title="🤖 Bot Health", description="Initializing…", color=0x95A5A6),
        view=HealthView(),
    )
    try:
        await m.pin()
    except Exception:
        pass
    try:
        json.dump({"id": m.id}, open(HEALTH_MSG_ID_PATH, "w", encoding="utf-8"))
    except Exception:
        pass
    return m.id


async def _update_health_embed():
    """Build and push the latest health card, optionally DM admin on alerts."""
    global _last_health_embed_update_ts, _last_health_alert_ts

    ch = bot.get_channel(STATUS_CHANNEL_ID)
    if not isinstance(ch, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
        logger.warning("[HEALTH] status channel not found or invalid")
        return

    msg_id = await _ensure_pinned_health_message(ch)

    # Collect metrics
    d, h, m, s = _uptime_hms()
    sql_ok, sql_reason = await _check_sql_health(timeout_sec=5.0)
    gs_ok, gs_message = await _check_gsheets_health(timeout_sec=5.0)
    err_60m = await _count_errors_last_minutes(60)
    err_10m = await _count_errors_last_minutes(10)
    queue_depth = _get_queue_depth_safe()

    latency = getattr(bot, "latency", None)
    latency_ms = int(latency * 1000) if latency is not None else None

    # Profile cache stats (best-effort)
    try:
        pc_stats = get_cache_stats()
        pc_count = pc_stats.get("count", 0)
        pc_loaded = pc_stats.get("loaded_at_iso")
        profile_line = f"\n**Profiles:** {pc_count} cached" + (
            f" • as_of {pc_loaded}" if pc_loaded else ""
        )
    except Exception:
        profile_line = "\n**Profiles:** n/a"

    # Discord session state
    sess = "🟢 connected"
    if LAST_DISCONNECT_UTC and (not LAST_RESUME_UTC or LAST_RESUME_UTC < LAST_DISCONNECT_UTC):
        sess = "🟠 disconnected"
    elif LAST_RESUME_UTC and LAST_DISCONNECT_UTC and LAST_RESUME_UTC > LAST_DISCONNECT_UTC:
        sess = "🟡 resumed"

    # Description
    desc = (
        f"**Uptime:** {d}d {h}h {m}m {s}s\n"
        f"**Discord:** {sess}"
        + (f" • ping ~{latency_ms} ms" if latency_ms is not None else "")
        + "\n"
        f"**Database:** {'🟢 OK' if sql_ok else '🔴 Error'}"
        + (f" — `{(sql_reason or '')[:120]}`" if not sql_ok else "")
        + "\n"
        f"**GSheets:** {'🟢 ' if gs_ok else '🔴 '}{gs_message}\n"  # <-- add this line
        f"**Errors:** 10m **{err_10m}** • 60m **{err_60m}**\n"
        f"**Queue depth:** {queue_depth}\n"
        f"{profile_line}\n"
        f"**Tasks:** {_summarize_tasks()}\n"
    )

    # Green = all good, no recent errors
    if sql_ok and gs_ok and sess == "🟢 connected" and err_10m == 0 and err_60m == 0:
        color = 0x2ECC71
    # Amber = there are recent errors (last 10m) but no major outages
    elif err_10m > 0 and sql_ok and gs_ok:
        color = 0xF39C12
    # Red = major (DB/Sheets down) OR large spike in last 60m OR disconnected
    else:
        color = (
            0xE74C3C
            if (
                not sql_ok
                or not gs_ok
                or err_60m >= ERROR_SPIKE_THRESHOLD
                or sess != "🟢 connected"
            )
            else 0xF39C12
        )

    embed = discord.Embed(title="🤖 Bot Health", description=desc, color=color)
    embed.set_footer(text="Auto-updates every 5 minutes • Use /logs for details")
    embed.timestamp = _aware(utcnow())

    try:
        msg = await ch.fetch_message(int(msg_id))
        await msg.edit(embed=embed, view=HealthView(), attachments=[])
        _last_health_embed_update_ts = _aware(utcnow())
    except Exception as e:
        logger.warning(f"[HEALTH] edit failed: {e}")

    # Alerting (debounced)
    try:
        need_alert = False
        reasons = []

        if not sql_ok:
            need_alert = True
            reasons.append("DB check failed" + (f": {sql_reason}" if sql_reason else ""))

        if not gs_ok:
            need_alert = True
            reasons.append("GSheets check failed" + (f": {gs_message}" if gs_message else ""))
            logger.warning("[HEALTH][GS] Probe failed: %s", gs_message)

        if err_60m >= ERROR_SPIKE_THRESHOLD:
            need_alert = True
            reasons.append(f"error spike ({err_60m} in 60m)")

        if err_10m > 0:
            reasons.append(f"errors in last 10m ({err_10m})")

        if _last_health_embed_update_ts:
            age_min = (_aware(utcnow()) - _last_health_embed_update_ts).total_seconds() / 60.0
            if age_min >= STALENESS_THRESHOLD_MIN:
                need_alert = True
                reasons.append(f"health stale {int(age_min)}m")

        # Debounce: only once per 30 minutes
        if need_alert:
            now = _aware(utcnow())
            if not _last_health_alert_ts or (now - _last_health_alert_ts).total_seconds() >= 1800:
                _last_health_alert_ts = now
                try:
                    owner = await bot.fetch_user(ADMIN_USER_ID)
                    text = "⚠️ **Bot Health Alert**\n" + "\n".join(f"- {r}" for r in reasons)
                    await owner.send(text)
                    logger.warning("[HEALTH] Admin DM sent: %s", ", ".join(reasons))
                except Exception as e:
                    logger.warning(f"[HEALTH] Failed to DM admin: {e}")
    except Exception as e:
        logger.warning(f"[HEALTH] alert block error: {e}")


@tasks.loop(minutes=HEALTH_REFRESH_MINUTES)
async def health_dashboard_task():
    try:
        await _update_health_embed()
    except Exception as e:
        logger.warning(f"[HEALTH] loop error: {e}")


@health_dashboard_task.before_loop
async def _wait_ready_health():
    await bot.wait_until_ready()


# Daily summary send gate state
_daily_summary_last_sent_date = None  # UTC date() of last send


@tasks.loop(minutes=1)
async def daily_summary():
    from utils import async_log_csv

    global _daily_summary_last_sent_date
    now = _aware(utcnow())
    # Send once per UTC day at/around 21:00. The once-per-day guard avoids dupes.
    if now.hour == 21 and now.minute in (0, 1) and (_daily_summary_last_sent_date != now.date()):
        try:
            channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            if not channel:
                logger.warning("❌ daily_summary could not find NOTIFY_CHANNEL_ID")
                return

            await send_summary_embed(channel, days=1)
            _daily_summary_last_sent_date = now.date()
            logger.info(
                "[SCHEDULED] Daily summary sent to %s at %s",
                channel.name,
                now.strftime("%Y-%m-%d %H:%M UTC"),
            )

            await async_log_csv(
                CSV_LOG,
                {
                    "timestamp": now.isoformat(),
                    "event": "daily_summary",
                    "filename": "",
                    "user": "BOT",
                    "status": "Success",
                },
            )

        except Exception as e:
            logger.exception("[ERROR] Failed to send daily summary")
            await async_log_csv(
                CSV_LOG,
                {
                    "timestamp": now.isoformat(),
                    "event": "daily_summary",
                    "filename": "",
                    "user": "BOT",
                    "status": f"Failure: {e!s}",
                },
            )


@daily_summary.before_loop
async def _before_daily_summary():
    # Ensure client is ready before the loop runs
    await bot.wait_until_ready()
    logger.info("[TASK] daily_summary loop armed (minute cadence; 21:00 UTC gate).")


@tasks.loop(hours=6)
async def refresh_event_cache_task():
    try:
        logger.info("[TASK] Starting event cache refresh...")
        await refresh_event_cache()
    except Exception as e:
        logger.warning(f"[TASK] Event cache refresh failed: {e}")


@refresh_event_cache_task.before_loop
async def before_refresh_cache():
    await bot.wait_until_ready()
    now = _aware(utcnow())
    # Align the first run to 03:00 or 15:00 UTC, otherwise next day 03:00
    if now.hour < 3:
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
    elif now.hour < 15:
        target = now.replace(hour=15, minute=0, second=0, microsecond=0)
    else:
        target = (now + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
    delay = max(0, (target - now).total_seconds())
    logger.info(f"[TASK] Waiting {int(delay)}s to start 6-hour event cache refresh task.")
    await asyncio.sleep(delay)


async def periodic_live_embed_update():
    await asyncio.sleep(random.uniform(0, 3))  # jitter
    while True:
        try:
            await update_live_event_embeds(bot, event_channel_id=KVK_EVENT_CHANNEL_ID)
        except Exception:
            logger.exception("[ERROR] Failed to update live embeds")
        await asyncio.sleep(600 + random.uniform(0, 3))


async def schedule_daily_KVK_overview():
    while True:
        now = _aware(utcnow())
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        delay = (target - now).total_seconds()
        await asyncio.sleep(delay)
        try:
            await post_or_update_daily_KVK_overview(bot, event_channel_id=KVK_EVENT_CHANNEL_ID)
            logger.info("[SCHEDULE] Daily KVK overview posted/updated.")
        except Exception:
            logger.exception("[SCHEDULE] Failed to post/update Daily KVK overview")


async def schedule_event_embed_expiry():
    while True:
        now = _aware(utcnow())
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        delay = (target - now).total_seconds()

        await asyncio.sleep(delay)

        try:
            await expire_old_event_embeds(bot)
            logger.info("[SCHEDULE] Expired old /nextevent and /nextfight embeds.")
        except Exception as e:
            logger.error(f"[SCHEDULE] Failed to expire event embeds: {e}")


# --- Graceful teardown ------------------
_shutdown_once = asyncio.Event()


async def _graceful_teardown():
    if _shutdown_once.is_set():
        return
    _shutdown_once.set()
    logger.info("[SHUTDOWN] Graceful teardown initiated.")

    # Stop task loops...
    try:
        if daily_summary.is_running():
            daily_summary.stop()
            logger.info("[SHUTDOWN] Stopped daily_summary loop.")
    except Exception:
        logger.exception("[SHUTDOWN] Failed stopping daily_summary.")

    try:
        if refresh_event_cache_task.is_running():
            refresh_event_cache_task.stop()
            logger.info("[SHUTDOWN] Stopped refresh_event_cache_task loop.")
    except Exception:
        logger.exception("[SHUTDOWN] Failed stopping refresh_event_cache_task.")

    # Cancel supervised tasks
    try:
        await task_monitor.stop()
    except Exception:
        logger.exception("[SHUTDOWN] TaskMonitor stop failed.")

    # Ensure reminder_task_registry tasks are cancelled and awaited (best-effort).
    # This ensures user DM reminder tasks are cancelled while logging and bot resources are still available.
    try:
        import reminder_task_registry as _rtr

        try:
            cancelled = await _rtr.cancel_all_and_wait(timeout=5.0)
            logger.info(
                "[SHUTDOWN] reminder_task_registry: requested cancellation of %d tasks (best-effort).",
                cancelled,
            )
        except AttributeError:
            # Back-compat path if only TaskRegistry exists
            try:
                from reminder_task_registry import TaskRegistry

                cancelled = await TaskRegistry.cancel_all(timeout=5.0)
                logger.info(
                    "[SHUTDOWN] reminder_task_registry.TaskRegistry: requested cancellation of %d tasks.",
                    cancelled,
                )
            except Exception:
                logger.exception(
                    "[SHUTDOWN] Failed to cancel tasks via reminder_task_registry.TaskRegistry."
                )
        except Exception:
            logger.exception("[SHUTDOWN] Failed to cancel reminder_task_registry tasks.")
    except Exception:
        # Non-fatal: continue shutdown even if registry import/cancel fails
        logger.debug(
            "[SHUTDOWN] reminder_task_registry not available or failed to import.", exc_info=True
        )

    # Heartbeat marker
    try:
        _atomic_json_write(
            os.path.join(LOG_DIR, "shutdown_heartbeat.json"),
            {
                "ts": _aware(utcnow()).isoformat(),
                "reason": "graceful_shutdown",
                "tasks": task_monitor.list(),
            },
        )
    except Exception:
        logger.exception("[SHUTDOWN] Failed writing shutdown heartbeat.")

    # Ensure usage tracker flushes any queued events
    try:
        await usage_tracker().stop()
        logger.info("[SHUTDOWN] Usage tracker stopped.")
    except Exception:
        logger.exception("[SHUTDOWN] Failed stopping usage tracker.")

    # **NEW**: drop webhook/HTTP/stream handlers but keep file handlers alive
    try:
        quiesce_logging()
    except Exception:
        pass


@bot.event
async def on_graceful_shutdown():
    try:
        await _graceful_teardown()
    except Exception:
        logger.exception("[SHUTDOWN] on_graceful_shutdown failed.")


@bot.event
async def on_ready():
    # Gate: only the first on_ready() does startup work
    if not await claim_startup_once():
        logger.info("[STARTUP] on_ready called again — startup already completed; skipping.")
        return

    # Install the global asyncio loop exception handler once the loop exists
    try:
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(global_asyncio_exception_handler)
        logger.info("[BOOT] Global asyncio exception handler installed on running loop.")
    except Exception as e:
        logger.warning(f"[BOOT] Failed to set global loop exception handler: {e}")

    # Defensive: ensure no console handlers linger (QueueHandler only).
    try:
        _drop_console_handlers_once()
    except Exception:
        pass

    # Start heartbeat now that the loop is running

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        task_monitor.create("heartbeat", heartbeat_loop)
        logger.info("[BOOT] Heartbeat loop started; writing to %s/heartbeat.json", LOG_DIR)
    except Exception:
        logger.exception("[BOOT] Failed to start heartbeat loop")

    try:
        if not health_dashboard_task.is_running():
            health_dashboard_task.start()
            logger.info("[BOOT] Health dashboard task started")
    except Exception:
        logger.error("[BOOT] Failed to start health_dashboard_task: {e}")

    # Start offload monitor as a supervised TaskMonitor task if available
    try:
        if monitor_loop_coro is not None:
            # avoid duplicate creation if already scheduled
            if not task_monitor.is_running("offload_monitor"):
                # run with reasonable defaults; adjust via env or later config if needed
                task_monitor.create(
                    "offload_monitor",
                    lambda: monitor_loop_coro(
                        interval_seconds=int(os.getenv("OFFLOAD_MONITOR_INTERVAL", "300")),
                        rotate_days=int(os.getenv("OFFLOAD_MONITOR_ROTATE_DAYS", "30")),
                        max_entries=int(os.getenv("OFFLOAD_MONITOR_MAX_ENTRIES", "2000")),
                    ),
                )
                logger.info("[BOOT] Offload monitor scheduled via TaskMonitor")
            else:
                logger.info("[BOOT] Offload monitor already running; skipping schedule")
    except Exception:
        logger.exception("[BOOT] Failed to schedule offload monitor")

    # 🔒 Prevent accidental Image.show() calls that invoke tkinter
    try:
        from PIL import Image

        def disabled_show(*args, **kwargs):
            import warnings

            warnings.warn("⚠️ Image.show() disabled to prevent tkinter-based crashes.")

        Image.show = disabled_show
        logger.info("[BOOT] PIL.Image.show() disabled at startup.")
    except Exception as e:
        logger.warning(f"[BOOT] Failed to patch Image.show(): {e}")

    try:
        clean_old_lock_files(LOG_DIR)
        logger.info("[LOCK_FILES] Cleared old LOCK Files on Startup")
    except Exception as e:
        logger.warning(f"[LOCK_FILES] Failed to clean lock files: {e}")

    # Make sure usage tracker is alive (idempotent)
    try:
        usage_tracker().start()
        logger.info("[BOOT] Usage tracker started.")
    except Exception:
        logger.exception("[BOOT] Failed to start usage tracker.")

    try:
        if not daily_summary.is_running():
            daily_summary.start()
            logger.info("[BOOT] daily_summary loop started")
    except Exception:
        logger.exception("[BOOT] Failed to start daily_summary loop")

    try:
        logger.info(f"✅ Bot is ready – logged in as {bot.user} (ID: {bot.user.id})")

        commands = list(bot.application_commands)
        current_signatures = [
            sig for cmd in commands if (sig := get_command_signature(cmd)) is not None
        ]

        logger.info("🧪 Reading command cache file...")
        saved_signatures = load_command_signatures(filepath=COMMAND_CACHE_FILE)
        logger.info("✅ Command cache loaded")

        try:
            result = commands_changed(current_signatures, saved_signatures)
            logger.info(f"✅ commands_changed result: {result}")
        except Exception:
            logger.exception("💥 Exception in commands_changed")
            result = False

        if bool(result):
            logger.info(
                f"[DEBUG] Slash commands changed — syncing to GUILD_ID={os.getenv('GUILD_ID')}"
            )
            gid_env = os.getenv("GUILD_ID")
            try:
                if gid_env:
                    gid = int(gid_env)
                    try:
                        await asyncio.wait_for(bot.sync_commands(guild_ids=[gid]), timeout=10.0)
                        logger.info("[DEBUG] Commands synced successfully")
                    except TimeoutError:
                        logger.warning("[WARN] Command sync timed out — skipping for now.")
                        try:
                            emit_telemetry_event(
                                {
                                    "event": "command_sync",
                                    "status": "timeout",
                                    "guild_id": gid,
                                    "orphaned_offload_possible": False,
                                }
                            )
                        except Exception:
                            logger.debug(
                                "[TELEMETRY] Failed to emit command_sync timeout telemetry",
                                exc_info=True,
                            )
                    except Exception as e:
                        logger.warning(f"[WARN] Command sync failed: {e}")
                else:
                    logger.warning("[WARN] GUILD_ID not set; skipping scoped sync.")
            except ValueError:
                logger.warning("[WARN] GUILD_ID is not an integer; skipping scoped sync.")
            except Exception as e:
                logger.warning(f"[WARN] Command sync failed: {e}")

            save_command_signatures(current_signatures, filepath=COMMAND_CACHE_FILE)
            logger.warning("🔁 Slash commands changed — updated cache")
        else:
            logger.warning("⏩ Slash commands unchanged — skipping sync and update.")

        logger.warning("📋 Loaded slash commands:")
        for cmd in commands:
            logger.warning(f" - /{cmd.name} – {cmd.description}")

        logger.info(f"[REMINDER_CACHE] Attempting to load from {REMINDER_TRACKING_FILE}")
        loaded_ids = await load_active_reminders(bot)

        try:
            load_event_cache()
            logger.info("[EVENT_CACHE] Loaded cache from disk")
            if is_cache_stale() or not get_all_upcoming_events():
                logger.info("[EVENT_CACHE] Cache was stale or empty — refreshing from GSheet")
                await refresh_event_cache()

            # Log a definitive post-refresh count so we can see what the bot is working with
            try:
                count = len(get_all_upcoming_events() or [])
                logger.info(f"[EVENT_CACHE] Ready with {count} upcoming events.")
            except Exception:
                logger.info("[EVENT_CACHE] Ready; but could not count events.")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to load or refresh event cache: {e}")

        schedule_bg("refresh_event_cache_once", 10.0, lambda: refresh_event_cache())

        ready = await wait_for_events(10)
        if ready:
            await _start_event_dependent_tasks()
        else:
            logger.warning(
                "[BOOT] Event cache not ready; will wait in background and start event-dependent tasks when populated."
            )
            task_monitor.create(
                "event_tasks_when_ready",
                lambda: _start_event_tasks_when_ready(max_wait_seconds=300),
            )

        try:
            schedule_bg("warm_name_cache", 8.0, lambda: warm_name_cache())
            logger.info("[CACHE] Governor name cache warm scheduled")
        except Exception as e:
            logger.warning(f"[CACHE] Failed to load Governor name cache (will retry later): {e}")

        # NEW: warm the player profile cache on startup
        try:
            schedule_bg("warm_profile_cache", 12.0, lambda: run_blocking(warm_profile_cache))
            logger.info("[CACHE] Player profile cache warm scheduled")
        except Exception as e:
            logger.warning(f"[CACHE] Failed to warm player profile cache: {e} — will retry later")

        # OPTIONAL: ensure stats cache (KVK) is populated too
        try:
            schedule_bg("build_player_stats_cache", 20.0, lambda: build_player_stats_cache())
            logger.info("[CACHE] Player stats (KVK) cache build scheduled")
        except Exception as e:
            logger.warning(f"[CACHE] Failed to build stats cache (will retry on next cycle): {e}")

        # OPTIONAL: schedule last-KVK cache build shortly after main stats cache is scheduled.
        try:
            schedule_bg(
                "build_lastkvk_player_stats_cache", 25.0, lambda: build_lastkvk_player_stats_cache()
            )
            logger.info("[CACHE] Last-KVK player stats cache build scheduled")
        except Exception as e:
            logger.warning(f"[CACHE] Failed to schedule last-KVK cache build: {e}")

        await cleanup_orphaned_reminders(loaded_ids)

        try:
            load_dm_sent_tracker()
            logger.info("[DM_SENT_TRACKER] loaded successfully.")
            load_dm_scheduled_tracker()
            logger.info("[DM_SCHEDULED_TRACKER] loaded successfully.")
        except Exception as e:
            logger.error(f"[DM_TRACKERS] Failed to load at startup: {e}")

        # Ensure subscription cache is loaded
        try:
            load_subscriptions()
            logger.info("[SUBSCRIPTIONS] Subscription file loaded successfully.")
        except Exception:
            logger.error("[SUBSCRIPTIONS] Failed to load at startup: {e}")

        try:
            if not refresh_event_cache_task.is_running():
                refresh_event_cache_task.start()
            else:
                logger.info("[BOOT] refresh_event_cache_task already running; skipping start.")
        except Exception:
            logger.error("[BOOT] Failed to start refresh_event_cache_task: {e}")

        try:
            schedule_bg("rehydrate_tracked_views", 10.0, lambda: rehydrate_tracked_views(bot))
            logger.info("[BOOT] View tracker rehydration scheduled")
        except Exception:
            logger.error("[BOOT] Failed to start rehydrate_tracked_views: {e}")

        try:
            task_monitor.create("ark_scheduler", lambda: schedule_ark_lifecycle(bot))
            logger.info("[BOOT] Ark scheduler started")
        except Exception as e:
            logger.error(f"[BOOT] Failed to start Ark scheduler: {e}")

        logger.info("[DEBUG] Calling full_startup_sequence...")
        try:
            await full_startup_sequence()
        except Exception:
            logger.exception("[STARTUP] ❌ full_startup_sequence failed")
        try:
            task_monitor.create("reminder_cleanup", reminder_cleanup_loop)
            logger.info("[BOOT] Reminder cleanup task started")
        except Exception:
            logger.error("[BOOT] Failed to start reminder_cleanup_loop: {e}")

    except Exception as e:
        logger.exception(f"[CRITICAL] Exception during on_ready: {e}")


@bot.event
async def on_disconnect():
    global LAST_DISCONNECT_UTC
    LAST_DISCONNECT_UTC = _aware(utcnow())
    logger.warning("⚠️ Bot disconnected from Discord")


@bot.event
async def on_resumed():
    global LAST_RESUME_UTC
    LAST_RESUME_UTC = _aware(utcnow())
    logger.info("🔄 Bot session resumed")


@bot.listen("on_interaction")
async def _usage_on_interaction(interaction: discord.Interaction):
    """
    Passive listener to log button/select/autocomplete usage.
    Using @bot.listen avoids overriding default routing.
    """
    try:
        await _log_interaction_usage(interaction)
    except Exception:
        # Never disrupt Discord's interaction flow
        pass


async def full_startup_sequence():
    logger.info("[BOOT] Entered full_startup_sequence()")
    for attempt in range(3):
        try:
            logger.warning(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")
            logger.warning("✅ Bot is ready.")

            notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            if not notify_channel:
                logger.error(f"❌ Could not find notify channel ID {NOTIFY_CHANNEL_ID}")
                return

            if os.path.exists(LAST_RESTART_INFO):
                try:
                    with open(LAST_RESTART_INFO, encoding="utf-8") as f:
                        data = json.load(f)
                        restart_time = _aware(datetime.fromisoformat(data.get("timestamp", "")))
                        user_id = data.get("user_id", "SYSTEM")
                        reason = data.get("reason", "manual")

                    uptime_seconds = (_aware(utcnow()) - restart_time).total_seconds()
                    uptime_str = str(timedelta(seconds=int(uptime_seconds)))

                    embed = discord.Embed(
                        title="✅ Bot Restarted Successfully",
                        description=f"The bot is back online after **{uptime_str}** of downtime.",
                        color=0x2ECC71,
                    )
                    embed.add_field(name="Triggered By", value=f"<@{user_id}>", inline=False)
                    embed.add_field(name="Reason", value=reason, inline=False)
                    embed.add_field(name="Uptime", value=uptime_str, inline=False)
                    embed.timestamp = _aware(utcnow())
                    await notify_channel.send(embed=embed)

                    await append_csv_line(
                        RESTART_LOG_FILE,
                        [_aware(utcnow()).isoformat(), reason, user_id, "success", "", reason, ""],
                    )
                    prune_restart_log()
                except Exception as e:
                    logger.warning(f"[RESTART] Failed to process last_restart.json: {e}")
                finally:
                    try:
                        os.remove(LAST_RESTART_INFO)
                    except Exception as e:
                        logger.warning(f"[RESTART] Failed to remove last_restart.json: {e}")

            elif os.path.exists(LAST_SHUTDOWN_INFO):
                try:
                    with open(LAST_SHUTDOWN_INFO, encoding="utf-8") as f:
                        data = json.load(f)
                    shutdown_time = _aware(datetime.fromisoformat(data.get("timestamp", "")))
                    reason = data.get("reason", "graceful shutdown")

                    uptime_seconds = (_aware(utcnow()) - shutdown_time).total_seconds()
                    uptime_str = str(timedelta(seconds=int(uptime_seconds)))

                    embed = discord.Embed(
                        title="💤 Graceful Server Restart Detected",
                        description=f"The bot was cleanly shut down and restarted after **{uptime_str}** of downtime.",
                        color=0x3498DB,
                    )
                    embed.add_field(name="Triggered By", value="shutdown bot", inline=False)
                    embed.add_field(
                        name="Reason", value="graceful shutdown before server restart", inline=False
                    )
                    embed.add_field(name="Uptime", value=uptime_str, inline=False)
                    embed.timestamp = _aware(utcnow())
                    await notify_channel.send(embed=embed)

                    logger.info(f"[BOOT] Reported graceful restart after shutdown: {data}")
                    os.remove(LAST_SHUTDOWN_INFO)

                except Exception as e:
                    logger.warning(f"[RESTART] Could not process LAST_SHUTDOWN_INFO: {e}")

            else:
                uptime_seconds = (_aware(utcnow()) - START_TIME).total_seconds()
                uptime_str = str(timedelta(seconds=int(uptime_seconds)))
                logger.warning(
                    "[BOOT] No restart or shutdown marker found — assuming crash recovery"
                )
                embed = discord.Embed(
                    title="⚠️ Crash Recovery Detected",
                    description="The bot has restarted after an unexpected crash.",
                    color=0xE67E22,
                )
                embed.add_field(name="Uptime Since Start", value=uptime_str, inline=False)
                embed.timestamp = _aware(utcnow())
                await notify_channel.send(embed=embed)

            try:
                if os.path.exists(".last_disconnect_reason"):
                    os.remove(".last_disconnect_reason")
            except Exception as e:
                logger.warning(f"[RESTART] Could not remove .last_disconnect_reason: {e}")

            # --- ProcConfig import: schedule in background with explicit start/finish logs ---
            try:
                logger.warning("Scheduling ProcConfig import in background.")

                # Wrap the import to get robust start/end logging inside the background task
                async def _proc_import_wrapper():
                    logger.warning("[PROC_IMPORT] Background import START")
                    try:
                        # Prefer the async offload wrapper if available (runs in isolated worker when possible)
                        if callable(globals().get("run_proc_config_import_offload")):
                            try:
                                ok, report = await run_proc_config_import_offload(
                                    dry_run=False, prefer_process=True, meta={"trigger": "startup"}
                                )
                                logger.warning(
                                    "[PROC_IMPORT] Background import END (success=%s) report_keys=%s",
                                    ok,
                                    list(report.keys())[:10] if isinstance(report, dict) else None,
                                )
                                return ok
                            except Exception:
                                logger.exception(
                                    "[PROC_IMPORT] run_proc_config_import_offload crashed"
                                )
                                raise

                        # Fallback: run the legacy blocking import in a thread/executor
                        try:
                            res = await run_blocking(run_proc_config_import)
                            # res may be (bool, report) or similar
                            if isinstance(res, tuple):
                                ok = res[0]
                                report = res[1] if len(res) > 1 else None
                            else:
                                ok = bool(res)
                                report = None
                            logger.warning(
                                "[PROC_IMPORT] Background import END (success=%s) (fallback path)",
                                ok,
                            )
                            return ok
                        except Exception:
                            logger.exception("[PROC_IMPORT] Blocking fallback import crashed")
                            raise

                    except Exception as e:
                        logger.exception("[PROC_IMPORT] Background import crashed: %s", e)
                        raise

                # Give it a generous envelope (e.g., 180s) to cover Sheets/SQL work
                schedule_bg("proc_config_import", 180.0, _proc_import_wrapper)
            except Exception as e:
                logger.error("[BOOT] Failed to schedule ProcConfig import: %s", e)

            for log_file, headers in [
                (CSV_LOG, ["Timestamp", "Channel", "Filename", "Author", "SavedPath"]),
                (INPUT_LOG, ["Timestamp", "User", "Kingdom Rank", "Kingdom Seed"]),
                (
                    RESTART_LOG_FILE,
                    [
                        "Timestamp",
                        "Reason",
                        "UserID",
                        "Status",
                        "WS_Code",
                        "WS_Description",
                        "WS_Timestamp",
                    ],
                ),
                (
                    SUMMARY_LOG,
                    [
                        "Timestamp",
                        "Channel",
                        "Filename",
                        "Author",
                        "SavedPath",
                        "Excel Success",
                        "Archive Success",
                        "SQL Success",
                        "Export Success",
                        "Duration (sec)",
                    ],
                ),
                (
                    FAILED_LOG,
                    [
                        "Timestamp",
                        "Filename",
                        "User",
                        "Rank",
                        "Seed",
                        "Excel Success",
                        "Archive Success",
                        "SQL Success",
                        "Export Success",
                        "Duration (sec)",
                    ],
                ),
            ]:
                if not os.path.exists(log_file):
                    needs_header = True
                else:
                    try:
                        with open(log_file, encoding="utf-8") as fh:
                            first = fh.readline().strip().split(",")
                        needs_header = first != headers
                    except Exception as e:
                        logger.warning(f"[LOG INIT] Could not read {log_file}: {e}")
                        needs_header = True

                if needs_header:
                    with open(log_file, "w", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow(headers)
                        logger.info(f"[LOG INIT] Initialized headers for {log_file}")

            for cid in CHANNEL_IDS:
                task_monitor.create(f"queue_worker:{cid}", lambda cid=cid: queue_worker(cid))

            load_live_queue()
            try:
                await update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)
            except Exception as e:
                logger.error(f"💥 Failed to update queue embed: {e}")

            task_monitor.create("queue_cleanup", queue_cleanup_loop)
            task_monitor.create("connection_watchdog", lambda: connection_watchdog(bot))

            # --- CrystalTech config load & validate at startup ---
            try:
                report = await init_crystaltech_service(fail_on_warn=False)
                logger.info("[CRYSTALTECH] %s", report.summary())
                # Optional: if you want to halt the feature when invalid:
                if not report.ok:
                    logger.error(
                        "[CRYSTALTECH] Validation failed. Feature will remain loaded but flagged until fixed."
                    )
            except Exception as e:
                logger.exception("[CRYSTALTECH] Failed to initialize CrystalTechService: %s", e)

            try:
                owner = await bot.fetch_user(ADMIN_USER_ID)
                await owner.send("✅ DL Bot has started and is now online.")
                logger.warning("📬 Startup DM sent to owner.")
                logger.info(
                    f"👀 Monitoring channels: {CHANNEL_IDS}, ACT ID: {ACTIVITY_UPLOAD_CHANNEL_ID}"
                )
            except Exception as e:
                logger.warning(f"❌ Failed to send startup DM: {e}")

            break
        except Exception as e:
            logger.error(f"[BOOT] on_ready attempt {attempt+1} failed: {e}")
            await asyncio.sleep(5)
    logger.info("[BOOT] full_startup_sequence completed successfully")
