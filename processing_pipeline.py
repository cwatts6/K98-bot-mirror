# processing_pipeline.py
import asyncio
import inspect
import logging
import os
import time
import traceback

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

import discord

from admin_helpers import log_processing_result, prompt_admin_inputs
from bot_config import (
    ADMIN_USER_ID,
    DELETE_AFTER_DOWNLOAD_CHANNEL_ID,
    EXCEL_SOURCE_CHANNEL_ID,
    NOTIFY_CHANNEL_ID,
)
from bot_loader import bot
from channel_helpers import get_channel_safe
from constants import (
    CREDENTIALS_FILE,
    DATABASE,
    DOWNLOAD_FOLDER,
    PASSWORD,
    SERVER,
    SUMMARY_LOG,
    USERNAME,
)
from embed_utils import (
    _DEFAULT_MAX_LOG_EMBED_CHARS,
    build_context_field,
    send_embed_safe,
    send_status_embed,
)
from file_utils import (
    emit_telemetry_event,
    find_offload_by_meta,
    read_json_safe,
    run_blocking_in_thread,  # still available for other modules; we favor run_step here
    run_maintenance_with_isolation,
)
from gsheet_module import run_all_exports

# NEW: log headroom helpers (bounded wait + auto-trigger on LOG_BACKUP)
from log_health import LogHeadroomError, preflight_from_env_sync
from player_stats_cache import build_lastkvk_player_stats_cache, build_player_stats_cache
from stats_module import run_stats_copy_archive
from target_utils import warm_name_cache, warm_target_cache
from utils import live_queue, live_queue_lock, load_cached_input, update_live_queue_embed, utcnow

# NEW: lightweight post-import stats maintenance (moved to file_utils.run_post_import_stats_update)
try:
    import pyodbc
except Exception:
    pyodbc = None

# Timeouts (seconds) — configurable via environment
EXPORT_TIMEOUT = int(os.getenv("EXPORT_TIMEOUT", "900"))  # default 15 minutes
POST_MAINT_TIMEOUT = int(os.getenv("POST_MAINT_TIMEOUT", "300"))  # default 5 minutes
# Separate proc import timeout (can be tuned)
PROC_IMPORT_TIMEOUT = int(os.getenv("PROC_IMPORT_TIMEOUT", str(POST_MAINT_TIMEOUT)))

# Maintenance worker mode: "thread" (legacy) or "process" (recommended)
MAINT_WORKER_MODE = os.getenv("MAINT_WORKER_MODE", "thread").lower()

# Optional timeout for build_player_stats_cache (seconds). None disables the wrapper.
BUILD_CACHE_TIMEOUT = float(os.getenv("BUILD_CACHE_TIMEOUT", "60.0"))

# Default trimming used when sending logs into embeds (kept small to avoid embed size issues)
_EMBED_LOG_TRIM = int(os.getenv("EMBED_LOG_TRIM", str(_DEFAULT_MAX_LOG_EMBED_CHARS)))


def _safe_trim(obj, n: int) -> str:
    """
    Safely convert `obj` to a string and return at most n characters.
    Protects logging and telemetry code from non-string types (bool, list, dict,
    objects with weird __getitem__ semantics that may raise on slicing).
    """
    try:
        if obj is None:
            return ""
        if isinstance(obj, str):
            return obj[:n]
        # bytes -> decode to str representation
        if isinstance(obj, (bytes, bytearray)):
            try:
                return obj.decode("utf-8", errors="replace")[:n]
            except Exception:
                return str(obj)[:n]
        # For other types, coerce to string (safe) then slice
        return str(obj)[:n]
    except Exception:
        # Last-resort fallback
        try:
            return repr(obj)[:n]
        except Exception:
            return "<unrepresentable>"


async def _local_send_step_embed(user, title, msg):
    """Async helper used by run_stats_copy_archive to send a step embed.

    The stats module expects `send_step_embed` to be awaited; making this async
    ensures we return an awaitable (coroutine) when invoked. Accepts `user`
    as first parameter so callers that only pass (title, msg) via a lambda can
    forward `user` in their closure.
    """
    try:
        fallback = get_channel_safe(bot, NOTIFY_CHANNEL_ID)
        if fallback is None:
            logger.info(
                "[EMBED_CALLBACK] notify channel not available; step embeds will attempt followup/DM fallback for user=%s",
                getattr(user, "id", "<unknown>"),
            )
        await send_embed_safe(
            user,
            title,
            {"Status": msg},
            0x3498DB,
            bot=bot,
            fallback_channel=fallback,
        )
    except Exception:
        logger.exception("[EMBED_CALLBACK] Failed to send step embed")


async def run_step(
    func,
    *args,
    offload_sync_to_thread: bool = False,
    name: str | None = None,
    meta: dict | None = None,
    **kwargs,
):
    """
    Run a step that might be sync or async.
    - If it's a coroutine function, await it.
    - If `offload_sync_to_thread=True`, run sync call in a thread via run_blocking_in_thread
      so telemetry (name/meta) is recorded and behavior is consistent.
    - If the result is awaitable (rare), await that too.

    Note: offloaded threads cannot be cancelled by asyncio.wait_for. Callers should
    be aware that awaiting run_step inside asyncio.wait_for and hitting a timeout
    will not stop the background thread — telemetry will be emitted to help operators.
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    if offload_sync_to_thread:
        run_name = name or getattr(func, "__name__", "run_blocking")
        # delegate to centralized helper so telemetry, naming and meta are consistent
        return await run_blocking_in_thread(func, *args, name=run_name, meta=meta, **kwargs)

    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


async def execute_processing_pipeline(
    rank: int, *, seed: int, user, filename: str, channel_id: int, save_path: str | None = None
) -> tuple[bool, bool, bool, bool, bool | None, str]:
    """
    Orchestrates the file -> SQL -> Sheets processing pipeline.

    Returns a tuple:
      (success_excel, success_archive, success_sql, success_export, success_proc_import, combined_log)

    This function is async; blocking operations are offloaded via run_blocking_in_thread
    for long-running blocking work so telemetry is recorded and code is consistent.
    """
    start_ts = utcnow()

    # Cache notify/fallback channel for the duration of this pipeline run to avoid
    # repeated lookups and small inconsistencies if the bot cache changes mid-run.
    notify_channel = get_channel_safe(bot, NOTIFY_CHANNEL_ID)
    if notify_channel is None:
        logger.info(
            "[PIPELINE] notify channel not available; using followup/DM fallback for this run"
        )

    # Resolve source file (used for Excel processing)
    source_file = None
    # Use configured constant instead of magic literal
    if channel_id == EXCEL_SOURCE_CHANNEL_ID:
        # Prefer the exact saved path if it exists
        if save_path and os.path.isfile(save_path):
            source_file = save_path
        else:
            # Fall back to DOWNLOAD_FOLDER/filename if exists
            try:
                candidate = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(candidate):
                    source_file = candidate
            except Exception:
                # Avoid hard failure if constants import fails in tests
                logger.debug("[EXCEL] DOWNLOAD_FOLDER check failed", exc_info=True)

    if source_file:
        logger.info(f"[EXCEL] Using source file: {source_file}")
    else:
        logger.info("[EXCEL] No source file path resolved (skipping Excel-specific step)")

    # 1) Excel copy + archive + SQL
    # Provide meta for telemetry so downstream run_block events include filename/rank/seed
    step_meta = {"filename": filename, "rank": rank, "seed": seed}

    # Some versions of run_stats_copy_archive may not accept a 'meta' kwarg.
    # Only include it when the callee supports it to avoid TypeError.
    rs_kwargs: dict = {}
    try:
        sig = inspect.signature(run_stats_copy_archive)
        if "meta" in sig.parameters:
            rs_kwargs["meta"] = step_meta
    except Exception:
        # If introspection fails, avoid passing meta to be safe.
        rs_kwargs = {}

    # Call run_stats_copy_archive via run_step so we tolerate both sync and async variants
    try:
        res = await run_step(
            run_stats_copy_archive,
            rank,
            seed,
            source_filename=source_file,  # absolute path or None
            send_step_embed=lambda title, msg: _local_send_step_embed(user, title, msg),
            offload_sync_to_thread=True,
            name="run_stats_copy_archive",
            meta=step_meta,
            **rs_kwargs,
        )
    except asyncio.CancelledError:
        # propagate cancellation
        raise
    except Exception:
        logger.exception("[STATS_COPY] run_stats_copy_archive raised an unexpected exception")
        emit_telemetry_event(
            {"event": "run_stats_copy_archive", "status": "exception", "filename": filename}
        )
        res = None

    # Expect canonical return contract from stats_module.run_stats_copy_archive:
    # (success: bool, combined_log: str, steps: dict[str, bool])
    try:
        _, out_archive, steps = res
    except Exception:
        # Minimal defensive fallback: log and coerce to failure. We intentionally removed
        # the previous extensive normalization in favor of a single stable contract.
        logger.exception(
            "[STATS_COPY] run_stats_copy_archive returned unexpected shape; coercing to failure"
        )
        emit_telemetry_event(
            {
                "event": "run_stats_copy_archive_unexpected_return",
                "type": str(type(res)),
                "filename": filename,
            }
        )
        out_archive = str(res or "")
        steps = {}

    # Defensive ensure steps is a dict
    if not isinstance(steps, dict):
        try:
            # attempt conversion if possible (e.g., list of pairs)
            steps = dict(steps)
        except Exception:
            logger.warning(
                "[STATS_COPY] 'steps' value is not a mapping (type=%s); coercing to empty dict",
                type(steps),
            )
            steps = {}

    success_excel = bool(steps.get("excel"))
    success_archive = bool(steps.get("archive"))
    success_sql = bool(steps.get("sql"))

    # Prepare a compact context field to include in embeds so humans can correlate
    context_field = build_context_field(filename=filename, rank=rank, seed=seed)

    if notify_channel is None:
        logger.info(
            "[STATS_COPY] notify channel not available; sending status embed with fallback=None"
        )

    # Use shared helper from embed_utils to emit telemetry and prepare embed fields.
    # The helper emits telemetry; we still call send_embed_safe to actually deliver the embed.
    await send_status_embed(
        "✅ Stats Copy Archive",
        {
            "Excel File": "✅" if success_excel else "❌",
            "Secondary Archive": "✅" if success_archive else "❌",
            "SQL Procedure": "✅" if success_sql else "❌",
            "Log": out_archive,
        },
        all([success_excel, success_archive, success_sql]),
        user,
        notify_channel,
        context_field=context_field,
    )
    # Now actually send the embed to channel/user
    try:
        await send_embed_safe(
            user,
            "✅ Stats Copy Archive",
            {
                "Excel File": "✅" if success_excel else "❌",
                "Secondary Archive": "✅" if success_archive else "❌",
                "SQL Procedure": "✅" if success_sql else "❌",
                "Log": out_archive,
            },
            0x2ECC71 if all([success_excel, success_archive, success_sql]) else 0xE74C3C,
            bot=bot,
            fallback_channel=notify_channel,
        )
    except Exception:
        logger.exception("[STATUS_EMBED] failed to send Stats Copy Archive embed")

    # 1b) Rebuild player_stats_cache.json as soon as SQL is updated
    #     (Cache is SQL-sourced; does NOT depend on Google Sheets)
    if success_sql:
        try:
            t0 = time.perf_counter()

            # Offload build_player_stats_cache to a thread and optionally bound it by BUILD_CACHE_TIMEOUT.
            try:
                # Use run_step with offload_sync_to_thread so sync/async variants are supported.
                build_task = run_step(
                    build_player_stats_cache,
                    offload_sync_to_thread=True,
                    name="build_player_stats_cache",
                    meta=step_meta,
                )
                if BUILD_CACHE_TIMEOUT and BUILD_CACHE_TIMEOUT > 0:
                    # Bound the wait so shutdown remains responsive and long hangs are documented.
                    await asyncio.wait_for(build_task, timeout=BUILD_CACHE_TIMEOUT)
                else:
                    await build_task
            except TimeoutError:
                # The background thread/process may still be running; record telemetry and continue.
                logger.exception("[CACHE] build_player_stats_cache timed out (continuing)")
                emit_telemetry_event({"event": "cache_build_timeout", "filename": filename})
            except asyncio.CancelledError:
                # Propagate cancellation cleanly
                raise
            except Exception as exc:
                logger.exception(
                    "[CACHE] build_player_stats_cache raised an exception (continuing)"
                )
                emit_telemetry_event(
                    {
                        "event": "cache_build_failed",
                        "filename": filename,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

                # Kick off last-KVK cache build in the same manner as the main cache rebuild.
                # Offload to a thread (non-fatal). Bound by BUILD_CACHE_TIMEOUT in the caller if desired.
                try:
                    last_task = run_step(
                        build_lastkvk_player_stats_cache,
                        offload_sync_to_thread=True,
                        name="build_lastkvk_player_stats_cache",
                        meta=step_meta,
                    )
                    if BUILD_CACHE_TIMEOUT and BUILD_CACHE_TIMEOUT > 0:
                        await asyncio.wait_for(last_task, timeout=BUILD_CACHE_TIMEOUT)
                    else:
                        await last_task
                except TimeoutError:
                    logger.warning(
                        "[CACHE] build_lastkvk_player_stats_cache timed out (continuing)"
                    )
                    emit_telemetry_event(
                        {"event": "lastkvk_cache_build_timeout", "filename": filename}
                    )
                except Exception:
                    logger.exception("[CACHE] build_lastkvk_player_stats_cache failed (continuing)")
                    emit_telemetry_event(
                        {"event": "lastkvk_cache_build_failed", "filename": filename}
                    )

            # quick sanity log: read PLAYER_STATS_CACHE off the loop
            from constants import PLAYER_STATS_CACHE

            try:
                data = await run_step(
                    read_json_safe,
                    PLAYER_STATS_CACHE,
                    offload_sync_to_thread=True,
                    name="read_json_safe",
                    meta=step_meta,
                )
            except asyncio.CancelledError:
                # Propagate cancellation cleanly
                raise
            except Exception as exc:
                logger.exception("[CACHE] Failed to read PLAYER_STATS_CACHE using read_json_safe")
                emit_telemetry_event(
                    {
                        "event": "cache_read_failed",
                        "filename": filename,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                data = {}

            count = (data.get("_meta") or {}).get("count", "unknown")
            logger.info(
                "[CACHE] player_stats_cache rebuilt early: %s players in %.2fs",
                count,
                time.perf_counter() - t0,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[CACHE] Early build_player_stats_cache failed")
            emit_telemetry_event({"event": "cache_build_failed", "filename": filename})

        # Keep a single stats refresh after the heavy UPDATE_ALL2 step
        try:
            ok, out = await run_maintenance_with_isolation(
                "post_stats",
                kwargs={
                    "server": SERVER,
                    "database": DATABASE,
                    "username": USERNAME,
                    "password": PASSWORD,
                },
                timeout=POST_MAINT_TIMEOUT,
                name="run_post_import_stats_update",
                meta=step_meta,
                prefer_process=(MAINT_WORKER_MODE == "process"),
            )
            if not ok:
                out_text = _safe_trim(out, 4000)
                logger.exception(
                    "[MAINT] post-import stats update failed or timed out: %s", out_text
                )
                emit_telemetry_event(
                    {
                        "event": "post_import_stats",
                        "status": "failed_or_timed_out",
                        "filename": filename,
                        "orphaned_offload_possible": False,
                        "detail": out_text,
                    }
                )
            else:
                logger.info("[MAINT] post-import stats update completed")
        except TimeoutError:
            # Offloaded post_stats may still run to completion — record telemetry for operational visibility.
            logger.exception("[MAINT] post-import stats update timed out (continuing)")

            # Attempt to find offload record to surface to operators
            try:
                off = find_offload_by_meta(step_meta)
                off_id = off.get("offload_id") if off else None
                off_pid = off.get("pid") if off else None
            except Exception:
                off_id = None
                off_pid = None

            emit_telemetry_event(
                {
                    "event": "post_import_stats",
                    "status": "timeout",
                    "filename": filename,
                    "orphaned_offload_possible": True,
                    "offload_id": off_id,
                    "pid": off_pid,
                }
            )

            # Include offload info in status embed for admins
            details = {"Status": "Skipped (preflight timeout)"}
            # Better messaging: clarify this was a post-import stats timeout
            details = {
                "Status": "Timed out waiting for post-import stats; offload may still be running."
            }
            if off_id or off_pid:
                details["Offload"] = f"id={off_id or 'unknown'} pid={off_pid or 'unknown'}"

            await send_status_embed(
                "🛠️ ProcConfig Import",
                details,
                False,
                user,
                notify_channel,
                context_field=context_field,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            tb = traceback.format_exc()
            logger.exception("[MAINT] post-import stats update failed (continuing)")
            emit_telemetry_event(
                {
                    "event": "post_import_stats",
                    "status": "failed",
                    "filename": filename,
                    "orphaned_offload_possible": False,
                    "error_type": type(exc).__name__,
                    "traceback": tb[:2000],
                }
            )

    # 2) ProcConfig import — insert a bounded headroom wait between steps
    success_proc_import: bool | None = None
    if success_excel:
        logger.info("🛠️ Running ProcConfig import after successful Excel export")

        # Only do the headroom wait if the SQL step actually ran (major writes)
        if success_sql:
            try:
                # Ensure log headroom (auto-trigger + bounded wait if LOG_BACKUP)
                # Use run_step to offload sync preflight to a thread for consistent telemetry
                await asyncio.wait_for(
                    run_step(
                        preflight_from_env_sync,
                        server=os.environ.get("SQL_SERVER") or SERVER,
                        database=os.environ.get("SQL_DATABASE") or DATABASE,
                        username=os.environ.get("SQL_USERNAME") or USERNAME,
                        password=os.environ.get("SQL_PASSWORD") or PASSWORD,
                        warn_threshold=85.0,
                        abort_threshold=95.0,
                        wait_on_log_backup=True,
                        max_wait_seconds=150,
                        poll_interval_seconds=5.0,
                        offload_sync_to_thread=True,
                        name="preflight_from_env_sync",
                        meta=step_meta,
                    ),
                    timeout=180.0,
                )
            except LogHeadroomError as e:
                logger.warning("[PROC_IMPORT] Skipping ProcConfig import: %s", e)
                success_proc_import = False
                await send_status_embed(
                    "🛠️ ProcConfig Import",
                    {"Status": "Skipped (SQL log not ready)", "Details": str(e)},
                    False,
                    user,
                    notify_channel,
                    context_field=context_field,
                )
            except TimeoutError:
                # Offloaded preflight thread may still run; mark telemetry so ops can inspect.
                logger.exception("[PROC_IMPORT] preflight timed out; skipping ProcConfig import")
                emit_telemetry_event(
                    {"event": "proc_import_preflight", "status": "timeout", "filename": filename}
                )
                success_proc_import = False
                await send_status_embed(
                    "🛠️ ProcConfig Import",
                    {"Status": "Skipped (preflight timeout)"},
                    False,
                    user,
                    notify_channel,
                    context_field=context_field,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("[PROC_IMPORT] preflight_from_env_sync failed (treating as skip)")
                emit_telemetry_event(
                    {
                        "event": "proc_import_preflight",
                        "status": "failed",
                        "filename": filename,
                        "error_type": type(exc).__name__,
                        "traceback": traceback.format_exc()[:2000],
                    }
                )
                success_proc_import = False
                await send_status_embed(
                    "🛠️ ProcConfig Import",
                    {"Status": "Skipped (preflight error)"},
                    False,
                    user,
                    notify_channel,
                    context_field=context_field,
                )
            else:
                try:
                    ok, out = await run_maintenance_with_isolation(
                        "proc_import",
                        args=[],
                        timeout=PROC_IMPORT_TIMEOUT,
                        name="proc_import",
                        meta=step_meta,
                        prefer_process=(MAINT_WORKER_MODE == "process"),
                    )
                    success_proc_import = bool(ok)
                    if not ok:
                        out_text = _safe_trim(out, 4000)
                        logger.exception("[PROC_IMPORT] proc_import failed: %s", out_text)

                        # Detect possible orphaned offload (subprocess timeout) by inspecting output
                        orphan_possible = False
                        try:
                            if isinstance(out, str) and (
                                "timed out" in out.lower() or "timeout" in out.lower()
                            ):
                                orphan_possible = True
                        except Exception:
                            orphan_possible = False

                        telemetry_payload = {
                            "event": "proc_import",
                            "status": "failed",
                            "filename": filename,
                            "detail": _safe_trim(out, 2000),
                        }
                        if orphan_possible:
                            # Attempt to find offload by meta to provide offload id/pid to operators
                            try:
                                off = find_offload_by_meta(step_meta)
                                telemetry_payload["orphaned_offload_possible"] = True
                                telemetry_payload["offload_id"] = (
                                    off.get("offload_id") if off else None
                                )
                                telemetry_payload["pid"] = off.get("pid") if off else None
                            except Exception:
                                telemetry_payload["orphaned_offload_possible"] = True
                                telemetry_payload["offload_id"] = None
                                telemetry_payload["pid"] = None
                        else:
                            telemetry_payload["orphaned_offload_possible"] = False

                        emit_telemetry_event(telemetry_payload)

                        # If orphan suspected, include in status embed for admins
                        if telemetry_payload.get("orphaned_offload_possible"):
                            off_text = f"id={telemetry_payload.get('offload_id') or 'unknown'} pid={telemetry_payload.get('pid') or 'unknown'}"
                            await send_status_embed(
                                "🛠️ ProcConfig Import",
                                {
                                    "Status": "Failed (offload may be orphaned)",
                                    "Offload": off_text,
                                    "Log": _safe_trim(out, _EMBED_LOG_TRIM),
                                },
                                False,
                                user,
                                notify_channel,
                                context_field=context_field,
                            )
                        else:
                            emit_telemetry_event(
                                {
                                    "event": "proc_import",
                                    "status": "failed",
                                    "filename": filename,
                                    "detail": _safe_trim(out, 2000),
                                }
                            )
                    else:
                        logger.info("[PROC_IMPORT] proc_import completed")
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.exception("[PROC_IMPORT] Unhandled error during run_proc_config_import")
                    emit_telemetry_event(
                        {
                            "event": "proc_import",
                            "status": "failed",
                            "filename": filename,
                            "error_type": type(exc).__name__,
                            "traceback": traceback.format_exc()[:2000],
                        }
                    )
                    success_proc_import = False

                await send_status_embed(
                    "🛠️ ProcConfig Import",
                    {"Status": "Completed" if success_proc_import else "Failed"},
                    success_proc_import is True,
                    user,
                    notify_channel,
                    context_field=context_field,
                )
        else:
            # SQL step didn’t run; run ProcConfig normally (no headroom wait needed)
            try:
                ok, out = await run_maintenance_with_isolation(
                    "proc_import",
                    args=[],
                    timeout=PROC_IMPORT_TIMEOUT,
                    name="proc_import",
                    meta=step_meta,
                    prefer_process=(MAINT_WORKER_MODE == "process"),
                )
                success_proc_import = bool(ok)
                if not ok:
                    out_text = _safe_trim(out, 4000)
                    logger.exception("[PROC_IMPORT] proc_import failed: %s", out_text)

                    orphan_possible = False
                    try:
                        if isinstance(out, str) and (
                            "timed out" in out.lower() or "timeout" in out.lower()
                        ):
                            orphan_possible = True
                    except Exception:
                        orphan_possible = False

                    telemetry_payload = {
                        "event": "proc_import",
                        "status": "failed",
                        "filename": filename,
                        "detail": _safe_trim(out, 2000),
                    }
                    if orphan_possible:
                        try:
                            off = find_offload_by_meta(step_meta)
                            telemetry_payload["orphaned_offload_possible"] = True
                            telemetry_payload["offload_id"] = off.get("offload_id") if off else None
                            telemetry_payload["pid"] = off.get("pid") if off else None
                        except Exception:
                            telemetry_payload["orphaned_offload_possible"] = True
                            telemetry_payload["offload_id"] = None
                            telemetry_payload["pid"] = None
                    else:
                        telemetry_payload["orphaned_offload_possible"] = False

                    emit_telemetry_event(telemetry_payload)

                    if telemetry_payload.get("orphaned_offload_possible"):
                        off_text = f"id={telemetry_payload.get('offload_id') or 'unknown'} pid={telemetry_payload.get('pid') or 'unknown'}"
                        await send_status_embed(
                            "🛠️ ProcConfig Import",
                            {
                                "Status": "Failed (offload may be orphaned)",
                                "Offload": off_text,
                                "Log": _safe_trim(out, _EMBED_LOG_TRIM),
                            },
                            False,
                            user,
                            notify_channel,
                            context_field=context_field,
                        )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("[PROC_IMPORT] Unhandled error during run_proc_config_import")
                emit_telemetry_event(
                    {
                        "event": "proc_import",
                        "status": "failed",
                        "filename": filename,
                        "error_type": type(exc).__name__,
                        "traceback": traceback.format_exc()[:2000],
                    }
                )
                success_proc_import = False

            await send_status_embed(
                "🛠️ ProcConfig Import",
                {"Status": "Completed" if success_proc_import else "Failed"},
                success_proc_import is True,
                user,
                notify_channel,
                context_field=context_field,
            )

    # 3) Google Sheets exports — offload to thread, but bounded by EXPORT_TIMEOUT
    await send_status_embed(
        "📤 Export to Google Sheets",
        {"Status": "Running"},
        None,
        user,
        notify_channel,
        context_field=context_field,
    )

    notify_channel_local = notify_channel
    if notify_channel_local is None:
        logger.warning(
            "[EXPORT] notify channel unavailable; run_all_exports will run without channel notifications"
        )

    try:
        try:
            success_export, out_export = await asyncio.wait_for(
                run_step(
                    run_all_exports,
                    SERVER,
                    DATABASE,
                    USERNAME,
                    PASSWORD,
                    CREDENTIALS_FILE,
                    notify_channel=notify_channel_local,
                    bot_loop=bot.loop,
                    offload_sync_to_thread=True,
                    name="run_all_exports",
                    meta=step_meta,
                ),
                timeout=EXPORT_TIMEOUT,
            )
        except TimeoutError:
            logger.exception("[EXPORT] run_all_exports timed out")
            emit_telemetry_event(
                {"event": "run_all_exports", "status": "timeout", "filename": filename}
            )
            success_export, out_export = False, "Export timed out (see logs)."
    except asyncio.CancelledError:
        # Propagate cancellation so shutdown is responsive
        raise
    except Exception as exc:
        logger.exception("[EXPORT] Unhandled error during run_all_exports")
        tb = traceback.format_exc()
        emit_telemetry_event(
            {
                "event": "run_all_exports",
                "status": "failed",
                "filename": filename,
                "error_type": type(exc).__name__,
                "traceback": tb[:2000],
            }
        )
        success_export, out_export = False, "Export crashed (see logs)."

    # 4) Warm caches after an export so commands/autocomplete feel snappy
    try:
        await warm_name_cache()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("[CACHE] warm_name_cache failed")

    try:
        await warm_target_cache()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("[CACHE] warm_target_cache failed")

    await send_status_embed(
        "📊 Google Sheets Export",
        {"Status": "Success" if success_export else "Failure", "Log": out_export},
        bool(success_export),
        user,
        notify_channel,
        context_field=context_field,
    )

    # Defensive concatenation: keep things strings even if a future change returns None
    out_archive = out_archive or ""
    out_export = out_export or ""

    combined_log = f"{out_archive}\n\n{out_export}"

    # Emit telemetry summary
    try:
        emit_telemetry_event(
            {
                "event": "processing_pipeline_summary",
                "excel": success_excel,
                "archive": success_archive,
                "sql": success_sql,
                "export": success_export,
                "proc_import": bool(success_proc_import),
                "duration_seconds": (utcnow() - start_ts).total_seconds(),
                "filename": filename,
            }
        )
    except Exception:
        logger.exception("[TELEMETRY] Failed to emit processing summary telemetry")

    return (
        success_excel,
        success_archive,
        success_sql,
        success_export,
        success_proc_import,
        combined_log,
    )


async def handle_file_processing(user, message, filename: str, save_path: str | None):
    """
    Entrypoint to process a downloaded file (called by queue worker).

    Steps:
      - Notify start
      - Prompt admin inputs
      - Run the execute_processing_pipeline orchestration
      - Log results and update the live queue embed
    """
    start_time = utcnow()
    channel_id = message.channel.id

    # Cache notify channel for consistent fallback behavior in this processing run
    notify_channel = get_channel_safe(bot, NOTIFY_CHANNEL_ID)
    if notify_channel is None:
        logger.warning(
            "[HANDLE_FILE] NOTIFY_CHANNEL_ID not resolvable; initial notify embed will rely on followup/DM fallback."
        )
    await send_embed_safe(
        notify_channel,
        "📥 File Processing Started",
        {
            "Filename": filename,
            "User": str(message.author),
            "Status": "Starting",
            **build_context_field(filename, None, None),
        },
        0x3498DB,
        bot=bot,
        fallback_channel=notify_channel,
    )

    rank, seed = await prompt_admin_inputs(bot, user, ADMIN_USER_ID)

    try:
        # Offload load_cached_input to avoid blocking the event loop if INPUT_CACHE_FILE is large or slow FS
        cache = await run_step(
            load_cached_input,
            offload_sync_to_thread=True,
            name="load_cached_input",
            meta={"filename": filename},
        )
    except asyncio.CancelledError:
        # allow cancellation to propagate during shutdown
        raise
    except Exception:
        logger.exception("[HANDLE_FILE] Failed to call load_cached_input()")
        raise

    today_str = utcnow().date().isoformat()
    source = "🧠 Cached" if cache and cache.get("date") == today_str else "📬 Fresh Prompt"

    # Add context for easier correlation in embeds
    context_field = build_context_field(filename=filename, rank=rank, seed=seed)

    await send_embed_safe(
        user,
        "🔄 Starting Script",
        {
            "Stage": "stats_copy_archive.py",
            "Rank": rank,
            "Seed": seed,
            "Source": source,
            **context_field,
        },
        0x3498DB,
        bot=bot,
        fallback_channel=notify_channel,
    )

    # Update live queue (keep only last 5 entries) — guarded by live_queue_lock
    async with live_queue_lock:
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

    async with live_queue_lock:
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
