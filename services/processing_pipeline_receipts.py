"""Retain per-stage facts without treating a timeout or released claim as completion."""

import asyncio
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from functools import wraps
import hashlib
import inspect
import json
from pathlib import Path

from kvk.dal.new_source_import_dal import SourceConflict
from services.processing_pipeline_receipt_dal import PipelineReceiptDAL

_pipeline = ContextVar("processing_pipeline_receipts", default=None)
_operation = ContextVar("processing_pipeline_operation", default=None)
_held_guard = ContextVar("processing_pipeline_held_guard", default=None)
_approved_action = ContextVar("processing_pipeline_approved_action", default=None)


@contextmanager
def continuation_scope(dal, run_id, action_id):
    pipeline_token = _pipeline.set((dal, run_id))
    guard_token = _held_guard.set(run_id)
    action_token = _approved_action.set(action_id)
    try:
        yield
    finally:
        _approved_action.reset(action_token)
        _held_guard.reset(guard_token)
        _pipeline.reset(pipeline_token)


def producer_operation():
    """Bind a child request before dispatch, including a lost registration reply."""
    return _operation.get()


def pipeline_runtime():
    from services.legacy_export_snapshot_service import _writer_runtime

    return _writer_runtime()


def record_pipeline(function):
    @wraps(function)
    async def run(rank, **kwargs):
        from services.legacy_export_snapshot_service import drain_thread

        runtime = pipeline_runtime()
        if runtime is None:
            return await function(rank, **kwargs)
        dal = PipelineReceiptDAL(runtime)
        inputs = dict(
            rank=rank,
            seed=kwargs["seed"],
            filename=kwargs["filename"],
            channel_id=kwargs["channel_id"],
            notification_run_id=kwargs.get("notification_run_id"),
        )
        # Registration is the first protected action. If its acknowledgement is
        # lost, no import is dispatched; discovery retains the saved run.
        run_id = await drain_thread(dal.create, inputs)
        if inputs["notification_run_id"]:
            from services.processing_notification_service import patch_run

            # Bind before any business stage so later recovery can follow this
            # exact pipeline even when the original coroutine never reaches export.
            await patch_run(inputs["notification_run_id"], pipeline_run_id=run_id)
        token = _pipeline.set((dal, run_id))
        try:
            return await function(rank, **kwargs)
        finally:
            _pipeline.reset(token)

    return run


async def stage(name, function):
    from services.legacy_export_snapshot_service import drain_thread

    context = _pipeline.get()
    if context is None:
        result = function()
        return await result if inspect.isawaitable(result) else result
    dal, run_id = context

    async def work():
        # The task is shielded and drained below. An asyncio deadline cannot
        # release this guard while an uncancellable worker still runs.
        async with stage_guard(dal, run_id):
            operation = await drain_thread(
                dal.start, run_id, name, action_id=_approved_action.get()
            )
            token = _operation.set(operation)
            try:
                result = strict_work(name, function)
                result = await result if inspect.isawaitable(result) else result
                from core.sql_observation import ObservationBusy
                from kvk.dal.new_source_import_dal import SourceBusy

                try:
                    evidence, verified = await drain_thread(
                        result_evidence, dal, name, operation, result
                    )
                except (ObservationBusy, SourceBusy) as exc:
                    # Business work already returned. Later observer contention
                    # must not erase that result or replay the work.
                    evidence, verified = (
                        dict(outcome="observation_pending", error_type=type(exc).__name__),
                        False,
                    )
                await drain_thread(
                    dal.observe, run_id, name, operation, evidence, verified=verified
                )
                return result
            except BaseException as exc:
                try:
                    await drain_thread(
                        dal.observe,
                        run_id,
                        name,
                        operation,
                        dict(outcome="unconfirmed", error_type=type(exc).__name__),
                        verified=False,
                    )
                except Exception:
                    # A lost receipt write stays running, never becomes an inferred
                    # rollback. Recovery checks the exact operation independently.
                    pass
                raise
            finally:
                _operation.reset(token)

    pending = asyncio.create_task(work())
    try:
        return await asyncio.shield(pending)
    except asyncio.CancelledError:
        while not pending.done():
            try:
                await asyncio.shield(pending)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if pending.done() and not pending.cancelled():
            pending.exception()
        raise


@asynccontextmanager
async def stage_guard(dal, run_id):
    """Keep the SQL session alive without connecting on the Discord event loop."""
    from services.legacy_export_snapshot_service import drain_thread

    if _held_guard.get() == run_id:
        yield
        return
    guard = dal.guard(run_id)
    await drain_thread(guard.__enter__)
    try:
        yield
    finally:
        await drain_thread(guard.__exit__, None, None, None)


async def strict_work(name, fallback):
    """Use workers whose failure is observable and whose lifetime can be drained."""
    from services.legacy_export_snapshot_service import drain_thread

    if name == "name_cache":
        from target_utils import sync_refresh_worker

        return await drain_thread(sync_refresh_worker)
    if name == "target_cache":
        from kvk.target_cache_repository import get_default_target_cache_repository

        return await drain_thread(get_default_target_cache_repository().refresh)
    if name == "maintenance":
        from constants import DATABASE, PASSWORD, SERVER, USERNAME
        from file_utils import run_post_import_stats_update
        from processing_pipeline import POST_MAINT_TIMEOUT

        await drain_thread(
            run_post_import_stats_update,
            SERVER,
            DATABASE,
            USERNAME,
            PASSWORD,
            timeout_seconds=POST_MAINT_TIMEOUT,
        )
        return True, "SQL maintenance response consumed"
    result = fallback()
    return await result if inspect.isawaitable(result) else result


def result_evidence(dal, name, operation, result):
    if name in {"import", "configuration"}:
        return producer_evidence(dal, name, operation)
    if name == "player_cache":
        from constants import PLAYER_STATS_CACHE

        if (
            not isinstance(result, dict)
            or result.get("_meta", {}).get("cache_write_status") != "written"
        ):
            return dict(outcome="cache_unconfirmed"), False
        with Path(PLAYER_STATS_CACHE).open("rb") as source:
            raw = source.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024 or json.loads(raw) != result:
            raise SourceConflict("Player cache readback differs from this stage's result.")
        meta = result["_meta"]
        return (
            dict(
                outcome="cache_bytes_verified",
                sha256=hashlib.sha256(raw).hexdigest(),
                source_kvk_no=meta.get("source_kvk_no"),
                source_last_refresh=meta.get("source_last_refresh"),
                source_refresh_status=meta.get("source_refresh_status"),
            ),
            True,
        )
    if name == "maintenance":
        acknowledged = isinstance(result, tuple) and len(result) == 2 and result[0] is True
        return (
            dict(
                outcome="statement_acknowledged" if acknowledged else "unconfirmed",
                procedure="dbo.usp_update_stats",
            ),
            acknowledged,
        )
    if name == "name_cache":
        from target_utils import get_name_cache_rows

        if not isinstance(result, dict) or result.get("rows") != get_name_cache_rows():
            return dict(outcome="name_cache_unconfirmed"), False
        raw = json.dumps(result["rows"], sort_keys=True, default=str).encode()
        return (
            dict(
                outcome="memory_cache_verified_at_receipt",
                sha256=hashlib.sha256(raw).hexdigest(),
                row_count=len(result["rows"]),
                persists_across_restart=False,
            ),
            True,
        )
    if name == "target_cache":
        from kvk.models.kvk_target_cache import TargetCacheRefreshOutcome, TargetCacheRefreshResult
        from kvk.target_cache_repository import get_default_target_cache_repository

        if (
            not isinstance(result, TargetCacheRefreshResult)
            or result.outcome
            not in {TargetCacheRefreshOutcome.REFRESHED, TargetCacheRefreshOutcome.REUSED}
            or not result.snapshot.is_verified
        ):
            return dict(outcome="target_cache_unconfirmed"), False
        repository = get_default_target_cache_repository()
        reread = repository.read_snapshot()
        if reread != result.snapshot:
            raise SourceConflict("Target cache publication changed during readback.")
        document = repository.snapshot_to_cache_document(reread)
        raw = json.dumps(document, sort_keys=True, default=str).encode()
        return (
            dict(
                outcome="target_cache_verified",
                sha256=hashlib.sha256(raw).hexdigest(),
                metadata=repository.snapshot_to_cache_meta(reread),
            ),
            True,
        )
    if name == "export":
        from services.export_submission import ExportSubmission

        if isinstance(result, ExportSubmission):
            prep, _, _ = dal.runtime.verified_snapshot(result.preparation_id)
            if str(prep["JobID"]).lower() != str(result.job_id).lower():
                raise SourceConflict(
                    "Export admission reply differs from the retained preparation."
                )
            return (
                dict(outcome="queued", preparation_id=result.preparation_id, job_id=result.job_id),
                True,
            )
        return dict(outcome="queue_unconfirmed"), False
    # Legacy warm wrappers suppress errors and return None. They cannot certify
    # cache freshness. Guided refresh uses strict workers and separate readback.
    return dict(outcome="cache_unconfirmed", cache=name), False


def producer_evidence(dal, name, operation):
    prep = (
        dal.configuration_result(operation)
        if name == "configuration"
        else dal.preparation(operation)
    )
    if prep is None:
        return dict(outcome="request_not_recorded", operation_id=operation), False
    source_id = str(prep["PreparationID"]).lower()
    if name == "import":
        from services.stats_import_outcome_service import outcome_dal

        outcome = outcome_dal(dal.runtime).inspect(source_id)
        complete = bool(outcome["execution"] and outcome["execution"]["State"] == "completed")
        return (
            dict(
                outcome="sql_completed" if complete else "sql_unconfirmed",
                preparation_id=source_id,
                kind="stats_import",
            ),
            complete,
        )
    from services.configuration_producer_recovery import ConfigurationProducerDAL

    outcomes = ConfigurationProducerDAL(
        dal.connect, account=dal.runtime.account, storage_owner=dal.runtime.store.storage_owner
    )
    preview = outcomes.inspect(source_id)
    complete = preview["action"] == "resume_capture" or preview["captured"]
    return (
        dict(
            outcome="configuration_committed" if complete else "configuration_unconfirmed",
            preparation_id=source_id,
            kind="configuration_producer",
        ),
        complete,
    )
