"""Event-cache execution ownership. No Discord, provider, or storage imports.

Availability is not freshness, persistence, admission, or delivery. One process
owns each refresh until its actual adapters finish; observers never own workers.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, replace
from datetime import datetime
import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UpcomingEventCacheSnapshot:
    ok: bool
    events: tuple[dict[str, Any], ...]
    last_refreshed: datetime | None
    stale: bool
    error: str | None = None
    generation: int = 0
    source: str = "unknown"
    persistence: str = "unknown"


@dataclass(frozen=True, slots=True)
class RefreshResult:
    attempt: int
    status: str
    fetch: str
    cache: str
    persistence: str
    count: int
    generation: int
    last_refreshed: datetime | None
    error: str | None = None
    joined: bool = False

    def report(self):
        result = asdict(self)
        result["last_refreshed"] = self.last_refreshed.isoformat() if self.last_refreshed else None
        return result


class EventCacheService:
    """Injected adapters must drain entered workers on cancellation.

    No automatic fetch retries. The configured fetch deadline cancels/drains the
    original loader group; caller observation deadlines only detach observers.
    """

    def __init__(self, *, snapshot, fetch, normalize, preserve, persist, publish, clock):
        self.snapshot = snapshot
        self.fetch = fetch
        self.normalize = normalize
        self.preserve = preserve
        self.persist = persist
        self.publish = publish
        self.clock = clock
        self._task = None
        self._attempt = 0
        self._closed = False
        self._phase = "idle"
        self._last = None

    def _result(self, status, fetch, cache="retained", persistence="not_attempted", error=None):
        state = self.snapshot()
        return RefreshResult(
            self._attempt,
            status,
            fetch,
            cache,
            persistence,
            len(state.events),
            state.generation,
            state.last_refreshed,
            error,
        )

    async def refresh(self, *, observation_seconds=None):
        if self._closed:
            return self._result("closed", "not_started", error="shutdown")
        joined = self._task is not None and not self._task.done()
        if not joined:
            self._attempt += 1
            self._task = asyncio.create_task(self._run(), name="event_cache_refresh_owner")
            self._task.add_done_callback(self._finished)
        task = self._task
        if observation_seconds is not None:
            done, _ = await asyncio.wait({task}, timeout=observation_seconds)
            if not done:
                return replace(self._result("pending", self._phase), joined=joined)
        return replace(await asyncio.shield(task), joined=joined)

    def _finished(self, task):
        # Observe orphaned exceptions even when every caller detached.
        if not task.cancelled():
            task.exception()
        if self._task is task:
            self._phase = "closed" if self._closed else "idle"

    async def _run(self):
        try:
            self._phase = "fetching"
            rows = await self.fetch()
            candidate = self.normalize(rows)
            stamp = self.clock()
            if self._closed:
                result = self._result("cancelled", "succeeded", error="shutdown")
            elif self.preserve(candidate):
                result = self._result("retained_by_policy", "succeeded")
            else:
                self._phase = "persisting"
                persistence, error = "saved", None
                try:
                    await self.persist(candidate, stamp)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    persistence, error = "failed", type(exc).__name__
                if self._closed:
                    result = self._result(
                        "cancelled", "succeeded", persistence=persistence, error="shutdown"
                    )
                else:
                    self.publish(candidate, stamp, persistence)
                    result = self._result(
                        "refreshed" if persistence == "saved" else "refreshed_memory_only",
                        "succeeded",
                        "replaced",
                        persistence,
                        error,
                    )
        except asyncio.CancelledError:
            self._last = self._result("cancelled", "unconfirmed", error="cancelled")
            raise
        except Exception as exc:
            result = self._result("failed", "failed", error=type(exc).__name__)
            logger.warning(
                "[EVENT_CACHE] Refresh failed error_type=%s; previous cache retained",
                type(exc).__name__,
            )
        self._last = result
        logger.info("[EVENT_CACHE] refresh outcome=%s", result.report())
        return result

    def close_admission(self):
        self._closed = True

    async def shutdown(self):
        self.close_admission()
        task = self._task
        if task is None or task.done():
            return
        task.cancel()
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if not task.cancelled():
            task.exception()

    def report(self):
        state = self.snapshot()
        return {
            "availability": (
                ("loaded_populated" if state.events else "loaded_empty")
                if state.ok
                else "unavailable"
            ),
            "stale": state.stale,
            "source": state.source,
            "persistence": state.persistence,
            "generation": state.generation,
            "event_count": len(state.events),
            "phase": self._phase,
            "admission_closed": self._closed,
            "last_attempt": self._last.report() if self._last else None,
        }


def refresh_message(result: RefreshResult) -> str:
    """Pure user-facing cache outcome, deliberately making no delivery claim."""
    if result.status == "pending":
        return "Event refresh is still running; no second refresh was started."
    if result.status == "closed":
        return "Event refresh is unavailable during shutdown."
    if result.status == "refreshed_memory_only":
        return "Event data refreshed in memory, but saving the cache failed."
    if result.status == "refreshed":
        return f"Event data refreshed: {result.count} upcoming events."
    if result.status == "retained_by_policy":
        return (
            "The fetch succeeded; the existing cache was retained by the empty-result protection."
        )
    return "Event refresh failed or was interrupted; any previously loaded data was retained."
