"""Bounded, loop-local ownership for personal reads and image preparation.

UI observers can leave; physical jobs retain capacity until actual settlement.
Nothing here calls Discord, retries work, or performs a health probe.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import logging
import time
from typing import Any

from core.operation_evidence import optional
from core.owned_work import drain_awaitable, drain_thread
from event_calendar.sql_lifecycle import SqlOutcome, error_facts
from player_self_service.stats_models import PersonalStatsUnavailable

logger = logging.getLogger(__name__)
SQL_LIMIT = 8
RENDER_LIMIT = 2
OBSERVER_LIMIT = 32


@dataclass(eq=False)
class ReadRun:
    kind: str
    key: Any = None
    epoch: int = 0
    valid: bool = True
    task: asyncio.Task | None = None
    started: bool = False
    entered: bool = False
    settled: bool = False
    outcome: SqlOutcome = field(default_factory=SqlOutcome)
    result: Any = None
    error: BaseException | None = None
    ready_at: float | None = None
    observed: str = "waiting"
    created_at: float = field(default_factory=time.monotonic)
    created_utc: str | None = None
    completed_utc: str | None = None
    cache: str = "not_applicable"

    def __post_init__(self):
        optional(lambda: setattr(self, "created_utc", datetime.now(UTC).isoformat()))

    def data_ready(self):
        self.ready_at = time.monotonic()

    def snapshot(self):
        return dict(
            kind=self.kind,
            phase=(
                "cleanup_uncertain"
                if self.outcome.cleanup == "unconfirmed"
                else "settled" if self.settled else "owned"
            ),
            observer=self.observed,
            read=(
                "failed"
                if self.error
                else (
                    "not_started"
                    if not self.entered
                    else "completed" if self.settled else "pending"
                )
            ),
            cleanup=self.outcome.cleanup,
            cache=self.cache,
            started_utc=self.created_utc,
            settled_utc=self.completed_utc,
            error=error_facts(self.error) if self.error else {},
            cleanup_error=dict(self.outcome.cleanup_error),
            rollback=self.outcome.rollback,
        )


@dataclass
class Journey:
    runtime: StatsRuntime
    task: asyncio.Task
    expiry: float | None


_journey: ContextVar[Journey | None] = ContextVar("personal_stats_journey", default=None)


class StatsRuntime:
    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.closed = False
        self.close_reason = None
        self.observers = 0
        self.jobs: dict[int, ReadRun] = {}
        self.inflight: dict[Any, ReadRun] = {}
        self.cache = OrderedDict()
        self.epoch = 0
        self.terminal = deque(maxlen=32)
        self.render_executor = None

    def renderer_executor(self):
        self.check()
        if self.render_executor is None:
            self.render_executor = ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="me-stats-render"
            )
        return self.render_executor

    def check(self):
        if self.closed:
            raise PersonalStatsUnavailable("Personal Stats is temporarily unavailable")
        journey = _journey.get()
        if journey and journey.task is asyncio.current_task() and journey.expiry is not None:
            if time.monotonic() >= journey.expiry:
                raise TimeoutError("Personal Stats view expired")

    @contextmanager
    def journey(self, *, expiry=None):
        self.check()
        current = _journey.get()
        if current and current.runtime is self and current.task is asyncio.current_task():
            yield current
            return
        if self.observers >= OBSERVER_LIMIT:
            raise PersonalStatsUnavailable("Personal Stats is busy; please try later")
        self.observers += 1
        token = _journey.set(Journey(self, asyncio.current_task(), expiry))
        try:
            yield _journey.get()
        finally:
            _journey.reset(token)
            self.observers -= 1

    def deadline(self, seconds):
        self.check()
        deadline = time.monotonic() + seconds
        journey = _journey.get()
        if journey and journey.task is asyncio.current_task() and journey.expiry is not None:
            deadline = min(deadline, journey.expiry)
        return deadline

    def invalidate(self, user_id=None):
        if user_id is None:
            self.epoch += 1
            self.cache.clear()
        else:
            for key in tuple(self.cache):
                if key[0] == user_id:
                    self.cache.pop(key, None)
            for key, run in self.inflight.items():
                if key[0] == user_id:
                    run.valid = False

    def close_admission(self, reason="shutdown"):
        self.closed = True
        if self.close_reason != "cleanup_uncertain":
            self.close_reason = reason
        self.invalidate()

    def submit(self, kind, function, *, key=None, publish=None, executor=None):
        self.check()
        if key is not None and key in self.inflight:
            return self.inflight[key]
        render = kind == "render"
        limit = RENDER_LIMIT if render else SQL_LIMIT
        if sum((r.kind == "render") == render for r in self.jobs.values()) >= limit:
            raise PersonalStatsUnavailable("Personal Stats is busy; please try later")
        run = ReadRun(kind=kind, key=key, epoch=self.epoch)
        self.jobs[id(run)] = run
        if key is not None:
            self.inflight[key] = run

        def work():
            run.entered = True
            try:
                run.result = function(run)
                if run.ready_at is None:
                    run.data_ready()
                return run.result
            except BaseException as error:
                run.error = error
                raise

        async def own():
            run.started = True
            try:
                if render:
                    context = copy_context()
                    future = self.loop.run_in_executor(executor, context.run, work)
                    return await drain_awaitable(future)
                return await drain_thread(work)
            except Exception as error:
                if run.error is None:
                    run.error = error
                raise
            finally:
                self._settle(run, publish)

        coroutine = own()
        try:
            run.task = self.loop.create_task(coroutine)
        except BaseException:
            coroutine.close()
            self._settle(run, None)
            raise

        def completed(task):
            # A cancellation before coroutine entry has submitted no native work.
            if not run.started:
                self._settle(run, None)
            if not task.cancelled():
                task.exception()

        run.task.add_done_callback(completed)
        return run

    def _settle(self, run, publish):
        if run.settled:
            return
        run.settled = True
        optional(lambda: setattr(run, "completed_utc", datetime.now(UTC).isoformat()))
        if run.outcome.cleanup not in {"settled", "not_needed"}:
            self.close_admission("cleanup_uncertain")
            run.result = None
            run.cache = "cleanup_uncertain"
            return  # retain connection/outcome, exact key and physical reservation
        try:
            if publish is not None and run.error is None and run.started:
                publish(run)
        except Exception:
            run.cache = "publication_failed"
            logger.debug("personal_stats_cache_publication_failed", exc_info=True)
        finally:
            if self.inflight.get(run.key) is run:
                self.inflight.pop(run.key)
            self.jobs.pop(id(run), None)
            optional(lambda: self.terminal.append(run.snapshot()))

    async def observe(self, run, deadline):
        try:
            async with asyncio.timeout_at(deadline):
                result = await asyncio.shield(run.task)
            self.check()
            return result
        except TimeoutError:
            run.observed = "timed_out"
            raise
        except asyncio.CancelledError:
            run.observed = "cancelled"
            raise

    def delivery(self, outcome):
        optional(
            lambda: self.terminal.append(
                dict(kind="delivery", outcome=outcome, captured_utc=datetime.now(UTC).isoformat())
            )
        )

    async def drain(self):
        self.close_admission()
        # Join each physical owner, even when another owner failed/cancelled.
        for run in tuple(self.jobs.values()):
            try:
                await drain_awaitable(run.task)
            except (asyncio.CancelledError, Exception):
                continue
        if not any(run.kind == "render" for run in self.jobs.values()) and self.render_executor:
            await drain_thread(self.render_executor.shutdown, wait=True)
        return not self.jobs

    def snapshot(self):
        reads = [r.snapshot() for r in self.jobs.values() if r.kind != "render"]
        renders = [r.snapshot() for r in self.jobs.values() if r.kind == "render"]
        value = dict(
            observed=True,
            admission_closed=self.closed,
            reason=self.close_reason,
            sql_owned=len(reads),
            render_owned=len(renders),
            observers=self.observers,
            cache_entries=len(self.cache),
            cleanup_uncertain=self.close_reason == "cleanup_uncertain",
            captured_utc=datetime.now(UTC).isoformat(),
            reads=reads,
            renders=renders,
            recent=list(self.terminal)[-8:],
            omitted_terminal=max(0, len(self.terminal) - 8),
        )
        while value["recent"] and len(json.dumps(value).encode("utf-8")) > 8192:
            value["recent"].pop(0)
            value["omitted_terminal"] += 1
        return value


_runtime: StatsRuntime | None = None


def get_runtime():
    global _runtime
    loop = asyncio.get_running_loop()
    if _runtime is None or _runtime.loop is not loop:
        if _runtime is not None and _runtime.jobs:
            raise PersonalStatsUnavailable("Previous Personal Stats workers remain unsettled")
        if _runtime is not None and _runtime.render_executor is not None:
            _runtime.render_executor.shutdown(wait=False)
        _runtime = StatsRuntime()
    return _runtime


def current_runtime():
    """Never initialize a runtime during report collection or process cleanup."""
    return _runtime


def snapshot():
    return _runtime.snapshot() if _runtime is not None else dict(observed=False)
