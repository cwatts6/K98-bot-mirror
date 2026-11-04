"""One observed health offload per process; a UI deadline never abandons it.

None means deferred/no fresh observation, not healthy and not a provider failure.
SQL/authority ownership remains the restart-safe source of truth.
"""

import asyncio
import logging
import time

from services.health_observation import Observation, utc

logger = logging.getLogger(__name__)


class HealthProbe:
    def __init__(self, *, stalled_after=300.0, clock=time.monotonic, label="GSheets"):
        self._task = None
        self._started = None
        self._clock = clock
        self._stalled_after = stalled_after
        self._label = label
        self._closed = False
        self._scope = None
        self._sequence = 0
        self._published = (None, Observation(label, "observed check"), None, None)

    def snapshot(self, *, scope=None):
        """Non-consuming immutable records; no task inspection or work creation."""
        bound, current, latest, failure = self._published
        if scope is not None and scope != bound:
            return (
                Observation(self._label, "configured check", reason="scope_mismatch"),
                None,
                None,
            )
        return current, latest, failure

    def _record(self, execution, outcome, reason, *, action=None):
        # Optional evidence cannot change worker results, ownership or drain.
        try:
            record = Observation(
                self._label,
                "observed check",
                utc(),
                execution,
                outcome,
                reason,
                f"{self._label}-{self._sequence}",
                action,
                started_monotonic=self._started if execution == "in_progress" else None,
            )
            bound, _, latest, failure = self._published
            if bound != self._scope:
                latest = failure = None
            if execution == "settled":
                latest = record
                if outcome == "failure":
                    failure = record
            self._published = (self._scope, record, latest, failure)
        except Exception:
            pass

    def close(self):
        self._closed = True

    async def shutdown(self):
        self.close()
        task = self._task
        if task is not None:
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue

    async def observe(self, run, *, timeout, scope=None):
        if self._closed:
            return None, f"{self._label} probe closed for shutdown"
        # No await between checking and storing the task: concurrent health
        # refreshes on the bot loop share this exact operation and its cleanup.
        if self._task is None:
            self._started = self._clock()
            self._scope = scope
            self._sequence += 1
            self._record("in_progress", "unknown", "owned_operation")
            self._task = asyncio.create_task(self._run(run), name=f"{self._label}-health-probe")
        elif scope != self._scope:
            return None, f"{self._label} retained probe belongs to another scope"
        task = self._task
        try:
            result = await asyncio.wait_for(asyncio.shield(task), timeout)
        except TimeoutError:
            if self._clock() - self._started >= self._stalled_after:
                return (
                    False,
                    f"{self._label} probe stalled; retained operation requires investigation",
                )
            return (
                None,
                f"{self._label} probe in progress; waiting for admission or authority completion",
            )
        # Cancellation propagates to the observer, never to the offload. Retain
        # the completed result until observed; late failures cannot be lost.
        if self._task is task:
            self._task = None
        return result

    async def _run(self, run):
        try:
            result = await run()
        except Exception as exc:
            logger.warning(
                "%s health operation failed error_type=%s", self._label, type(exc).__name__
            )
            self._record(
                "settled",
                "failure",
                "access_denied" if isinstance(exc, PermissionError) else "check_failed",
                action="verify_access" if isinstance(exc, PermissionError) else None,
            )
            return False, f"{self._label} health operation failed; inspect retained evidence"
        try:
            outcome = (
                "success" if result[0] is True else "failure" if result[0] is False else "deferred"
            )
            self._record(
                "settled",
                outcome,
                "check_completed" if outcome != "deferred" else "admission_deferred",
            )
        except Exception:
            pass
        return result


_probe = HealthProbe()


def health_snapshot():
    # Only already loaded configuration; never bootstrap provider/config readers.
    import sys

    config = sys.modules.get("constants")
    if config is None:
        return (Observation("GSheets", "configured check", reason="source_unavailable"), None, None)
    credentials = getattr(config, "CREDENTIALS_FILE", None)
    targets = tuple(
        getattr(config, key, None) for key in ("SHEET_ID", "KVK_SHEET_ID", "STATS_SHEET_ID")
    )
    bound = _probe._published[0]
    if bound not in tuple((credentials, target) for target in targets if target):
        return (Observation("GSheets", "configured check", reason="scope_mismatch"), None, None)
    return _probe.snapshot(scope=bound)


async def check_health(credentials_file, sheet_id, *, timeout=5.0):
    """Explicit active compatibility API. Presentation must use snapshots."""
    from file_utils import run_blocking_in_thread
    from gsheet_module import check_basic_gsheets_access
    from services.cache_admission_diagnostics import observation_context

    if not sheet_id:
        return None, "No sheet configured for probe"

    async def run():
        with observation_context("health_probe", "health"):
            return await run_blocking_in_thread(
                check_basic_gsheets_access,
                credentials_file,
                sheet_id,
                name="check_basic_gsheets_access",
                meta={"sheet_id": sheet_id},
            )

    return await _probe.observe(run, timeout=timeout, scope=(credentials_file, sheet_id))
