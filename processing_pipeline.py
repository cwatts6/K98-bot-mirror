# processing_pipeline.py
import asyncio
import inspect
import logging
import os
import traceback
from typing import Literal

from services.legacy_export_snapshot_service import bound_runtime, collect_producer_captures

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
    run_blocking_in_thread,  # still available for other modules; we favor run_step here
    run_maintenance_with_isolation,
)
from gsheet_module import run_all_exports

# NEW: log headroom helpers (bounded wait + auto-trigger on LOG_BACKUP)
from log_health import LogHeadroomError, preflight_from_env_sync
from player_stats_cache import build_player_stats_cache
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


async def _notification_intervention(user, notify_channel, run_id):
    await send_embed_safe(
        user,
        "Processing notification needs attention",
        {
            "Processing run": run_id,
            "Reason": "A required notification update could not be saved.",
            "Admin action": (
                "Preserve the journal and repair disk, locking or permissions. Inspect this exact "
                "run with processing_notifications.py status and correlated logs; reconcile or "
                "close its notifications after inspection. Do not repeat the import or export."
            ),
        },
        color=0xF1C40F,
        fallback_channel=notify_channel,
    )


async def _run_proc_config_step(step_meta):
    from services.legacy_export_snapshot_service import _writer_runtime

    if _writer_runtime() is not None:
        from proc_config_import import run_proc_config_import_offload

        return await run_proc_config_import_offload(prefer_process=False, meta=step_meta)
    return await run_maintenance_with_isolation(
        "proc_import",
        args=[],
        timeout=PROC_IMPORT_TIMEOUT,
        name="proc_import",
        meta=step_meta,
        prefer_process=(MAINT_WORKER_MODE == "process"),
    )


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


@bound_runtime
@collect_producer_captures
async def execute_processing_pipeline(
    rank: int,
    *,
    seed: int,
    user,
    filename: str,
    channel_id: int,
    save_path: str | None = None,
    notification_run_id: str | None = None,
) -> tuple[bool, bool, bool, bool | Literal["pending"] | None, bool | None, str]:
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

    def finish(excel, archive, sql, export, proc_import, log):
        try:
            emit_telemetry_event(
                {
                    "event": "processing_pipeline_summary",
                    "excel": excel,
                    "archive": archive,
                    "sql": sql,
                    "export": export,
                    "proc_import": proc_import,
                    "duration_seconds": (utcnow() - start_ts).total_seconds(),
                    "filename": filename,
                }
            )
        except Exception:
            logger.exception("[TELEMETRY] Failed to emit processing summary telemetry")
        return excel, archive, sql, export, proc_import, log

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

    if success_sql is not True:
        logger.warning(
            "processing_pipeline_stopped stage=sql outcome=failed_or_unproven "
            "dependent_stages=cache,maintenance,proc_config,export action=inspect_import_outcome "
            "excel=%s archive=%s sql=%s",
            success_excel,
            success_archive,
            success_sql,
        )
        await send_status_embed(
            "⏸️ Dependent Steps Skipped",
            {
                "Reason": "SQL import did not confirm success. Cache refresh, ProcConfig and export were not started.",
                "Next action": "Inspect the import error. If a preparation is held, use /ops import_resolution with its preparation ID.",
            },
            False,
            user,
            notify_channel,
            context_field=context_field,
        )
        return finish(
            success_excel, success_archive, success_sql, None, None, str(out_archive or "")
        )

    # SQL/cache readiness is independent of Google configuration and delivery.
    cache_output = None
    try:
        build_task = run_step(
            build_player_stats_cache,
            offload_sync_to_thread=True,
            name="build_player_stats_cache",
            meta=step_meta,
        )
        cache_output = (
            await asyncio.wait_for(build_task, timeout=BUILD_CACHE_TIMEOUT)
            if BUILD_CACHE_TIMEOUT and BUILD_CACHE_TIMEOUT > 0
            else await build_task
        )
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        logger.exception("[CACHE] Fresh stats cache build timed out")
        emit_telemetry_event({"event": "cache_build_timeout", "filename": filename})
    except Exception as exc:
        logger.exception("[CACHE] Fresh stats readiness not confirmed")
        emit_telemetry_event(
            {"event": "cache_build_failed", "filename": filename, "error_type": type(exc).__name__}
        )
    for warmer in (warm_name_cache, warm_target_cache):
        try:
            await warmer()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[CACHE] Auxiliary cache refresh failed")
    if notification_run_id:
        from services.processing_notification_service import NotificationTransitionFailed
        from stats_alerts.processing_notifications import bot_data_ready

        try:
            await bot_data_ready(bot, notification_run_id, cache_output)
        except NotificationTransitionFailed:
            await _notification_intervention(user, notify_channel, notification_run_id)
            raise

    if success_sql:
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
    if success_sql:
        logger.info("🛠️ Running ProcConfig import after confirmed SQL import")

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
                ok, out = await _run_proc_config_step(step_meta)
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
                            telemetry_payload["offload_id"] = off.get("offload_id") if off else None
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
    if success_proc_import is not True:
        logger.warning(
            "processing_pipeline_stopped stage=proc_config outcome=failed_or_unproven "
            "dependent_stages=export action=inspect_proc_config_error import_replay=false"
        )
        await send_status_embed(
            "⏸️ Export Skipped",
            {
                "Reason": "ProcConfig did not confirm success. No export was submitted.",
                "Next action": "Inspect the ProcConfig error and preparation ID; do not repeat the committed import.",
            },
            False,
            user,
            notify_channel,
            context_field=context_field,
        )
        return finish(
            success_excel,
            success_archive,
            success_sql,
            None,
            success_proc_import,
            str(out_archive or ""),
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
            export_result = await asyncio.wait_for(
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
                    **({"notification_run_id": notification_run_id} if notification_run_id else {}),
                ),
                timeout=EXPORT_TIMEOUT,
            )
            from services.export_submission import ExportSubmission

            if isinstance(export_result, ExportSubmission):
                success_export, out_export = "pending", export_result.log
                if notification_run_id:
                    from services.processing_notification_service import patch_run

                    await patch_run(
                        notification_run_id,
                        preparation_id=export_result.preparation_id,
                        job_id=export_result.job_id,
                        sheets="pending",
                    )
            else:
                success_export, out_export = export_result
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

    await send_status_embed(
        "📊 Google Sheets Export",
        {
            "Status": (
                "Queued"
                if success_export == "pending"
                else ("Success" if success_export else "Failure")
            ),
            "Log": out_export,
        },
        None if success_export == "pending" else bool(success_export),
        user,
        notify_channel,
        context_field=context_field,
    )

    # Defensive concatenation: keep things strings even if a future change returns None
    out_archive = out_archive or ""
    out_export = out_export or ""

    combined_log = f"{out_archive}\n\n{out_export}"

    return finish(
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
    notification_run_id = None
    import bot_config
    from services.legacy_export_snapshot_service import drain_thread
    from services.processing_notification_service import event, patch_run, register_run

    managed_notifications = bot_config.EXPORT_COORDINATION_ENABLED
    if managed_notifications:
        try:
            notification_run_id = await drain_thread(
                register_run,
                source_message_id=message.id,
                source_channel_id=channel_id,
                summary_channel_id=NOTIFY_CHANNEL_ID,
                sheets_channel_id=bot_config.GSHEETS_EXPORT_CHANNEL_ID,
            )
        except Exception as exc:
            event(
                None,
                "registration",
                "held",
                "repair_notification_journal_before_next_run",
                error=exc,
            )

    # Cache notify channel for consistent fallback behavior in this processing run
    notify_channel = get_channel_safe(bot, NOTIFY_CHANNEL_ID)
    if managed_notifications and not notification_run_id:
        logger.error(
            "processing_registration outcome=blocked source_message_id=%s source_channel_id=%s next_action=repair_runtime_or_notification_journal_before_resubmission",
            message.id,
            channel_id,
        )
        await send_embed_safe(
            user,
            "File processing not started",
            {
                "Reason": "Durable completion tracking is unavailable. No import was started.",
                "Admin action": (
                    "Check protected runtime availability and data/processing_outcomes.json. "
                    "Repair disk/permissions or resolve old journal entries, then submit this file again."
                ),
            },
            0xE74C3C,
            bot=bot,
            fallback_channel=notify_channel,
        )
        raise RuntimeError("Processing notification registration unavailable; no import started.")
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
            if (
                not job.get("processing_run_id")
                and job["filename"] == filename
                and job["user"] == str(message.author)
                and (
                    not job.get("source_message_id")
                    or job["source_message_id"] == getattr(message, "id", None)
                )
            ):
                job["status"] = "⚙️ Processing..."
                job["processing_run_id"] = notification_run_id
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
        rank,
        user=user,
        seed=seed,
        filename=filename,
        channel_id=channel_id,
        save_path=save_path,
        **({"notification_run_id": notification_run_id} if notification_run_id else {}),
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

    if notification_run_id:
        from services.processing_notification_store import notification_store

        try:
            current = await drain_thread(notification_store().get, notification_run_id)
            sheets_state = (
                "pending"
                if success_export == "pending"
                else ("uncertain" if success_proc_import is True else "failed")
            )
            handoff = await patch_run(
                notification_run_id,
                handoff=True,
                sheets=sheets_state,
                stats=current["stats"] if success_sql else "unavailable",
                steps=dict(
                    excel=success_excel,
                    archive=success_archive,
                    sql=success_sql,
                    proc_config=success_proc_import,
                ),
                **(
                    {
                        "duration_seconds": (utcnow() - start_time).total_seconds(),
                        "completed_at": utcnow().timestamp(),
                    }
                    if sheets_state in {"failed", "uncertain"}
                    else {}
                ),
            )
            if (
                handoff
                and handoff["sheets"] == sheets_state
                and sheets_state in {"failed", "uncertain"}
            ):
                event(
                    notification_run_id,
                    "export",
                    sheets_state,
                    "inspect_pipeline_and_exact_job_evidence",
                    duration=handoff.get("duration_seconds"),
                )
        except Exception as exc:
            event(notification_run_id, "handoff", "held", "inspect_notification_journal", error=exc)
            await _notification_intervention(user, notify_channel, notification_run_id)
            raise

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
        **({"managed_notifications": True} if managed_notifications else {}),
    )

    # Status icon based on archive/export results
    if success_export == "pending":
        failed = any(
            value is False
            for value in (success_excel, success_archive, success_sql, success_proc_import)
        )
        status_icon = "🔴 Export pending; other step failed" if failed else "⏳ Export pending"
    elif success_archive and success_export is True:
        status_icon = "🟢"
    elif success_archive or success_export:
        status_icon = "🟠"
    else:
        status_icon = "🔴"
    timestamp = utcnow().strftime("%Y-%m-%d %H:%M UTC")

    async with live_queue_lock:
        for job in live_queue["jobs"]:
            if (
                job.get("processing_run_id") == notification_run_id
                if notification_run_id
                else job["filename"] == filename and job["user"] == str(message.author)
            ):
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

    logger.info(
        "processing_handoff outcome=%s export=%s duration_seconds=%.1f action=%s",
        (
            "awaiting_export"
            if success_export == "pending"
            else (
                "completed"
                if all(
                    value is True
                    for value in (
                        success_excel,
                        success_archive,
                        success_sql,
                        success_export,
                        success_proc_import,
                    )
                )
                else "incomplete"
            )
        ),
        success_export,
        (utcnow() - start_time).total_seconds(),
        "await_durable_confirmation" if success_export == "pending" else "inspect_step_outcomes",
    )
