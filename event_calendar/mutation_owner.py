"""Shared event-loop admission, with retained physical work and one scheduled intent."""

import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
import threading
import uuid
from weakref import WeakKeyDictionary

from core.owned_work import drain_awaitable
from event_calendar.sync_audit import SyncAudit


@dataclass
class Run:
    kind: str
    reference: str = field(default_factory=lambda: uuid.uuid4().hex)
    stop: threading.Event = field(default_factory=threading.Event)
    task: asyncio.Task | None = None
    stage: str = "not_started"
    phase: str = "admitted"
    observer: str = "waiting"
    raw: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    cleanup_unconfirmed: bool = False

    def snapshot(self):
        return deepcopy(
            dict(
                reference=self.reference,
                kind=self.kind,
                stage=self.stage,
                phase=self.phase,
                observer=self.observer,
                stop_after_current=self.stop.is_set(),
                cleanup="unconfirmed" if self.cleanup_unconfirmed else self.phase,
                stages=self.results,
                result=self.result,
            )
        )


class MutationOwner:
    def __init__(self):
        self.active = None
        self.last = None
        self.closed = False
        self.deferred = False
        self.audit = SyncAudit()
        self.shutdown_task = None

    def refusal(self, status):
        return dict(
            ok=False,
            status=status,
            stage="not_admitted",
            severity="pending",
            details={
                "busy": "Calendar work is still running. This request did not start.",
                "already_deferred": "A scheduled refresh is already waiting. This request did not start.",
                "admission_closed": "Calendar is shutting down. This request did not start.",
                "cleanup_unconfirmed": "Earlier database cleanup is unconfirmed. New calendar work is blocked; elapsed time cannot release it.",
            }[status],
            pipeline_run_id=None,
            blocking_run_id=self.active.reference if self.active else None,
        )

    async def execute(self, kind, function, *, scheduled=False):
        if self.closed:
            return self.refusal("admission_closed")
        if self.active is not None and self.active.cleanup_unconfirmed:
            return self.refusal("cleanup_unconfirmed")
        if self.active is not None or self.deferred:
            if not scheduled:
                return self.refusal("busy")
            if self.deferred:
                return self.refusal("already_deferred")
            self.deferred = True
            previous = self.active
            try:
                # Cancelling a waiting schedule drops only its own intent.
                await asyncio.shield(previous.task)
            finally:
                self.deferred = False
            if self.closed:
                return self.refusal("admission_closed")
            if self.active is not None:
                return self.refusal("cleanup_unconfirmed")
        run = Run(kind)
        self.active = run

        async def own():
            try:
                run.result = await function(run)
                return run.result
            finally:
                run.phase = "cleanup_unconfirmed" if run.cleanup_unconfirmed else "settled"
                self.last = run
                if not run.cleanup_unconfirmed:
                    self.active = None

        run.task = asyncio.create_task(own())
        try:
            result = await asyncio.shield(run.task)
            return deepcopy(result)
        except asyncio.CancelledError:
            run.observer = "cancelled_draining"
            run.stop.set()
            try:
                await drain_awaitable(run.task)
            finally:
                run.observer = (
                    "cancelled_settled"
                    if not run.cleanup_unconfirmed
                    else "cancelled_cleanup_unconfirmed"
                )
                run.result["observer"] = run.observer
            raise

    def close_admission(self):
        self.closed = True
        self.audit.close_admission()
        if self.active is not None:
            self.active.stop.set()

    async def drain(self):
        self.close_admission()

        async def join():
            if self.active is not None:
                await drain_awaitable(self.active.task)
            audit_ok = await self.audit.drain()
            return dict(
                ok=self.active is None and audit_ok,
                business_cleanup="unconfirmed" if self.active else "settled",
                audit_cleanup="settled" if audit_ok else "unconfirmed",
            )

        if self.shutdown_task is None:
            self.shutdown_task = asyncio.create_task(join())
        return await drain_awaitable(self.shutdown_task)

    def snapshot(self):
        return dict(
            admission_closed=self.closed,
            deferred_scheduled=self.deferred,
            active=self.active.snapshot() if self.active else None,
            last=self.last.snapshot() if self.last else None,
            audit=self.audit.snapshot(),
        )


_owners = WeakKeyDictionary()


def get_owner():
    loop = asyncio.get_running_loop()
    if loop not in _owners:
        _owners[loop] = MutationOwner()
    return _owners[loop]
