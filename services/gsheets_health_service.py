"""One observed health offload per process; a UI deadline never abandons it.

None means deferred/no fresh observation, not healthy and not a provider failure.
SQL/authority ownership remains the restart-safe source of truth.
"""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class HealthProbe:
    def __init__(self, *, stalled_after=300.0, clock=time.monotonic):
        self._task = None
        self._started = None
        self._clock = clock
        self._stalled_after = stalled_after

    async def observe(self, run, *, timeout):
        # No await between checking and storing the task: concurrent health
        # refreshes on the bot loop share this exact operation and its cleanup.
        if self._task is None:
            self._started = self._clock()
            self._task = asyncio.create_task(self._run(run), name="gsheets-health-probe")
        task = self._task
        try:
            result = await asyncio.wait_for(asyncio.shield(task), timeout)
        except TimeoutError:
            if self._clock() - self._started >= self._stalled_after:
                return False, "GSheets probe stalled; retained operation requires investigation"
            return None, "GSheets probe in progress; waiting for admission or authority completion"
        # Cancellation propagates to the observer, never to the offload. Retain
        # the completed result until observed; late failures cannot be lost.
        if self._task is task:
            self._task = None
        return result

    @staticmethod
    async def _run(run):
        try:
            return await run()
        except Exception as exc:
            logger.warning("GSheets health operation failed error_type=%s", type(exc).__name__)
            return False, "GSheets health operation failed; inspect retained evidence"


_probe = HealthProbe()


async def check_health(credentials_file, sheet_id, *, timeout=5.0):
    """Share one retained health operation across dashboard and admin requests."""
    from file_utils import run_blocking_in_thread
    from gsheet_module import check_basic_gsheets_access

    if not sheet_id:
        return None, "No sheet configured for probe"
    return await _probe.observe(
        lambda: run_blocking_in_thread(
            check_basic_gsheets_access,
            credentials_file,
            sheet_id,
            name="check_basic_gsheets_access",
            meta={"sheet_id": sheet_id},
        ),
        timeout=timeout,
    )
