"""MGE admission, reply gates and observers over the existing coalescing executor."""

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import logging

from core.coalesced_work import CoalescedWork
from core.owned_work import drain_awaitable

logger = logging.getLogger(__name__)
_permits = ContextVar("mge_refresh_permits", default=frozenset())
_registration = ContextVar("mge_reply_registration", default=(None, False))


@contextmanager
def registration_scope(gate, existing_only):
    token = _registration.set((gate, existing_only))
    try:
        yield
    finally:
        _registration.reset(token)


def registration_options(gate, existing_only):
    inherited_gate, inherited_existing = _registration.get()
    return gate if gate is not None else inherited_gate, existing_only or inherited_existing


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    status: str

    def __bool__(self):
        return self.status == "delivered"


class RefreshHandle:
    """Observe a shared pass without handing its cancellation authority to callers."""

    def __init__(self, task):
        self.__task = task

    registered = True

    async def observe(self, timeout=None):
        if timeout is not None:
            done, _ = await asyncio.wait((self.__task,), timeout=timeout)
            if not done:
                return DeliveryResult("pending")
        try:
            result = await drain_awaitable(self.__task)
            return DeliveryResult("delivered" if result is True else "failed")
        except Exception:
            return DeliveryResult("failed")

    def __await__(self):
        return self.observe().__await__()


class RefusedRefresh:
    registered = False

    async def observe(self, timeout=None):
        return DeliveryResult("refused")

    def __await__(self):
        return self.observe().__await__()


class RefreshGroup:
    def __init__(self, handles):
        self.handles = handles

    @property
    def registered(self):
        return bool(self.handles) and all(handle.registered for handle in self.handles.values())

    async def observe(self, timeout=None):
        results = {
            kind: DeliveryResult("not_requested") for kind in ("public", "leadership", "awards")
        }
        keys = list(self.handles)
        values = await asyncio.gather(*(self.handles[key].observe(timeout) for key in keys))
        results.update(zip(keys, values, strict=True))
        return results

    def __await__(self):
        return self.observe().__await__()


class RefreshCoordinator:
    def __init__(self):
        self._work = CoalescedWork()
        self._gates = {}
        self._registered = {}
        self._direct = set()
        self._background_closed = False
        self._continuations_closed = False

    def close_background(self):
        self._background_closed = True

    def _admit(self):
        if not self._background_closed or self in _permits.get():
            return
        from core.interaction_safety import has_private_admission

        if not self._continuations_closed and has_private_admission():
            return
        raise RuntimeError("MGE refresh admission is closed")

    async def _permitted(self, factory):
        token = _permits.set(_permits.get() | {self})
        try:
            return await factory()
        finally:
            _permits.reset(token)

    def request(self, key, factory, *, gate=None):
        self._admit()
        gates = self._gates.setdefault(key, set())
        if gate is not None:
            gates.add(gate)

        async def run():
            captured = set()
            try:
                # Include gates admitted while this pass was waiting. There is no
                # suspension between the final check and entering the factory.
                while pending := gates - captured:
                    await asyncio.gather(*(entry.wait() for entry in pending))
                    captured.update(pending)
                return await self._permitted(factory)
            finally:
                gates.difference_update(captured)

        try:
            task = self._work.request(key, run)
        except BaseException:
            if gate is not None:
                gates.discard(gate)
            if not gates:
                self._gates.pop(key, None)
            raise

        def finished(_):
            # CoalescedWork owns the task until idle, including dirty follow-ups.
            if self._registered.get(key) is not task:
                return
            self._registered.pop(key, None)
            if self._gates.get(key) is gates and not gates:
                self._gates.pop(key, None)

        if self._registered.get(key) is not task:
            self._registered[key] = task
            task.add_done_callback(finished)
        return RefreshHandle(task)

    async def run_direct(self, factory):
        self._admit()
        task = asyncio.create_task(self._permitted(factory), name="mge_owned_presentation")
        self._direct.add(task)
        try:
            return await drain_awaitable(task)
        finally:
            self._direct.discard(task)

    async def drain(self):
        self.close_background()
        self._continuations_closed = True

        async def settle():
            while self._direct:
                await asyncio.gather(*tuple(self._direct), return_exceptions=True)
            await self._work.drain()
            while self._direct:
                await asyncio.gather(*tuple(self._direct), return_exceptions=True)

        task = asyncio.create_task(settle(), name="mge_refresh_drain")

        async def observe():
            while not task.done():
                done, _ = await asyncio.wait((task,), timeout=10)
                if not done:
                    logger.warning("mge_refresh_still_draining state=%s", self.snapshot())
            return await task

        await drain_awaitable(observe())

    def snapshot(self):
        return {
            **self._work.snapshot(),
            "direct": len(self._direct),
            "reply_gates": sum(len(gates) for gates in self._gates.values()),
            "background_closed": self._background_closed,
            "continuations_closed": self._continuations_closed,
        }
