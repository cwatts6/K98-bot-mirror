"""Owned, keyed refresh work; a request during execution guarantees another pass.

Only for replaceable reads/presentation, never business mutations. State is local
to this process; callers must restore from their authoritative store after restart.
"""

import asyncio
from collections import Counter
import logging

from core.owned_work import drain_awaitable

logger = logging.getLogger(__name__)


class CoalescedWork:
    def __init__(self):
        self._pending = {}
        self._closed = False
        self.counts = Counter()

    def request(self, key, factory):
        if self._closed:
            raise RuntimeError("Refresh admission is closed")
        self.counts["requests"] += 1
        current = self._pending.get(key)
        if current is not None:
            current["revision"] += 1
            current["factory"] = factory
            self.counts["coalesced"] += 1
            return current["task"]
        current = {"revision": 1, "factory": factory}

        async def run():
            try:
                while True:
                    revision = current["revision"]
                    self.counts["passes"] += 1
                    try:
                        result = await current["factory"]()
                    except Exception as exc:
                        self.counts["failed_passes"] += 1
                        self.counts["exceptions"] += 1
                        logger.warning("coalesced_refresh_failed error_type=%s", type(exc).__name__)
                        if revision == current["revision"]:
                            raise
                        # A newer request owns another pass; do not replay this one.
                        continue
                    if result is False:
                        self.counts["failed_passes"] += 1
                    if revision == current["revision"]:
                        return result
            finally:
                self._pending.pop(key, None)

        task = asyncio.create_task(run(), name="coalesced_refresh")
        current["task"] = task
        self._pending[key] = current

        def observe(done):
            if not done.cancelled():
                done.exception()  # Every failing pass is recorded inside run().

        task.add_done_callback(observe)
        return task

    async def run(self, key, factory):
        return await drain_awaitable(self.request(key, factory))

    async def drain(self):
        self._closed = True
        tasks = [entry["task"] for entry in self._pending.values()]
        if tasks:
            await drain_awaitable(asyncio.gather(*tasks, return_exceptions=True))

    def reopen(self):
        if self._pending:
            raise RuntimeError("Cannot reopen while refreshes are still running")
        self._closed = False

    def snapshot(self):
        return {**self.counts, "pending": len(self._pending), "closed": self._closed}
