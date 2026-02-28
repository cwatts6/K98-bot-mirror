# usage_tracker.py
"""
Extended usage tracker with lightweight metrics recording and alerting hooks.
...
"""

from __future__ import annotations

import asyncio
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
import io
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional

from constants import BASE_DIR, _conn
from utils import ensure_aware_utc, utcnow

log = logging.getLogger(__name__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

UsageEvent = dict[str, Any]

# Explicit UTC alias for clarity
UTC = timezone.utc


# Daily JSONL paths
def _jsonl_path_utc() -> str:
    # Use repository-wide utcnow() helper so filename date is consistent
    return os.path.join(DATA_DIR, f"command_usage_{utcnow().strftime('%Y%m%d')}.jsonl")


def _metrics_jsonl_path_utc() -> str:
    return os.path.join(DATA_DIR, f"metrics_{utcnow().strftime('%Y%m%d')}.jsonl")


def _alerts_jsonl_path_utc() -> str:
    return os.path.join(DATA_DIR, f"alerts_{utcnow().strftime('%Y%m%d')}.jsonl")


class AsyncUsageTracker:
    """Append to JSONL immediately (off-thread); batch-flush to SQL on a timer or when buffer fills."""

    def __init__(self, flush_interval_sec: int = 120, batch_size: int = 500, queue_max: int = 5000):
        self.flush_interval_sec = flush_interval_sec
        self.batch_size = batch_size
        self.queue: asyncio.Queue[UsageEvent] = asyncio.Queue(maxsize=queue_max)
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    # ---------- lifecycle ----------
    def start(self) -> None:
        if self._task is None:
            try:
                self._task = asyncio.create_task(self._run(), name="usage-tracker")
            except RuntimeError:
                # No running loop; leave it to caller to start the loop's task later.
                log.debug("[USAGE] No running loop; tracker task not created")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task
            self._task = None

    # ---------- public API ----------
    async def log(self, evt: UsageEvent) -> None:
        # 1) local JSONL (best-effort, offload blocking I/O)
        try:
            # Ensure executed_at_utc is serialisable: if it's a datetime, convert to ISO
            evt_copy = dict(evt)
            ts = evt_copy.get("executed_at_utc")
            if isinstance(ts, datetime):
                evt_copy["executed_at_utc"] = ensure_aware_utc(ts).isoformat()

            # Offload blocking file write to run_step/run_blocking_in_thread/to_thread (no start_callable_offload)
            def _sync_write(
                ecopy: UsageEvent, path_fn: Callable[[], str] = _jsonl_path_utc
            ) -> None:
                try:
                    line = json.dumps(ecopy, separators=(",", ":"), ensure_ascii=False)
                    with open(path_fn(), "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                except Exception:
                    # Log to the main logger — this runs in a thread/process; ensure exception is surfaced
                    log.exception("[USAGE] Local JSONL background write failed")

            # Local import to avoid module-level cycles; prefer run_step (standard wrapper),
            # then run_blocking_in_thread; finally fallback to asyncio.to_thread.
            try:
                from file_utils import run_blocking_in_thread, run_step  # type: ignore
            except Exception:
                run_step = None
                run_blocking_in_thread = None

            try:
                meta = {"command_name": evt_copy.get("command_name")}
                if run_step is not None:
                    # schedule run_step (async) fire-and-forget
                    try:
                        asyncio.create_task(
                            run_step(
                                _sync_write, evt_copy, name="usage_local_jsonl_write", meta=meta
                            )
                        )
                    except Exception:
                        # fallback to thread helper
                        if run_blocking_in_thread is not None:
                            asyncio.create_task(
                                run_blocking_in_thread(
                                    _sync_write, evt_copy, name="usage_local_jsonl_write", meta=meta
                                )
                            )
                        else:
                            asyncio.create_task(asyncio.to_thread(_sync_write, evt_copy))
                elif run_blocking_in_thread is not None:
                    asyncio.create_task(
                        run_blocking_in_thread(
                            _sync_write, evt_copy, name="usage_local_jsonl_write", meta=meta
                        )
                    )
                else:
                    # fallback to to_thread as before if helper not available
                    asyncio.create_task(asyncio.to_thread(_sync_write, evt_copy))
            except RuntimeError:
                # If there is no running loop (unlikely inside async usage), do inline write as fallback
                _sync_write(evt_copy)

        except Exception:
            log.exception("[USAGE] Preparing local JSONL write failed")

        # 2) enqueue for SQL
        try:
            self.queue.put_nowait(evt)
            # Per-event visibility (ensure your log level includes DEBUG to see this)
            log.debug(
                "[USAGE]+ cmd=%s v=%s ok=%s ms=%s q=%d/%d",
                evt.get("command_name"),
                evt.get("version"),
                evt.get("success", True),
                evt.get("latency_ms"),
                self.queue.qsize(),
                self.queue.maxsize,
            )
        except asyncio.QueueFull:
            log.warning(
                "[USAGE] Queue full; dropping usage event (q=%d/max=%d) cmd=%s",
                getattr(self.queue, "qsize", lambda: -1)(),
                getattr(self.queue, "maxsize", -1),
                evt.get("command_name"),
            )

    # ---------- worker ----------
    @staticmethod
    def _coerce_ts(ts: Any) -> Any:
        """
        Coerce timestamp input into a naive UTC datetime for SQL DATETIME/DATETIME2 parameters.
        """
        if isinstance(ts, str):
            try:
                if ts.endswith("Z"):
                    ts = ts[:-1] + "+00:00"
                dt = datetime.fromisoformat(ts)
            except Exception:
                return ts
            return ensure_aware_utc(dt).astimezone(UTC).replace(tzinfo=None)

        if isinstance(ts, datetime):
            return ensure_aware_utc(ts).astimezone(UTC).replace(tzinfo=None)

        return ts

    async def _flush(self, events: list[UsageEvent]) -> None:
        if not events:
            return

        def clip(s, n):
            return None if s is None else str(s)[:n]

        def row_from(e: UsageEvent):
            return (
                self._coerce_ts(e.get("executed_at_utc")),
                clip(e.get("command_name"), 64),
                clip(e.get("version"), 16),
                clip(e.get("app_context", "slash"), 16),
                e.get("user_id"),
                clip(e.get("user_display"), 128),
                e.get("guild_id"),
                e.get("channel_id"),
                1 if e.get("success", True) else 0,
                clip(e.get("error_code"), 64),
                e.get("latency_ms"),
                json.dumps(e.get("args_shape")) if e.get("args_shape") else None,
                e.get("error_text"),
            )

        rows = [row_from(e) for e in events]

        # Flush summary with command mix
        cmd_counts = Counter(r[1] for r in rows)
        log.info(
            "[USAGE] Flushing %d events: %s",
            len(rows),
            ", ".join(f"{k}={v}" for k, v in cmd_counts.most_common()),
        )

        rows.sort(
            key=lambda t: (
                -(len(t[1]) if isinstance(t[1], str) else 0),
                -(len(t[5]) if isinstance(t[5], str) else 0),
                -(len(t[9]) if isinstance(t[9], str) else 0),
                -(len(t[3]) if isinstance(t[3], str) else 0),
            )
        )

        SQL_INSERT = """
            INSERT INTO dbo.BotCommandUsage
            (ExecutedAtUtc, CommandName, Version, AppContext,
             UserId, UserDisplay, GuildId, ChannelId,
             Success, ErrorCode, LatencyMs, ArgsShape, ErrorText)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS NVARCHAR(MAX)), CAST(? AS NVARCHAR(MAX)))
        """

        try:
            conn = _conn()
            cur = conn.cursor()

            if hasattr(cur, "fast_executemany"):
                try:
                    cur.fast_executemany = False
                except Exception:
                    log.debug("[USAGE] Could not set fast_executemany on cursor; continuing safely")

            cur.executemany(SQL_INSERT, rows)
            conn.commit()
            cur.close()
            conn.close()
            log.info(
                "[USAGE] Flushed %d events to SQL (safe batch, no fast_executemany)", len(events)
            )

        except Exception:
            log.exception("[USAGE] Batch insert (safe) failed; attempting per-row.")
            try:
                conn = _conn()
                cur = conn.cursor()
                for r in rows:
                    cur.execute(SQL_INSERT, r)
                conn.commit()
                cur.close()
                conn.close()
                log.info("[USAGE] Per-row salvage OK (%d rows)", len(rows))
            except Exception:
                log.exception("[USAGE] SQL flush failed even per-row; will retry later")

    async def _run(self) -> None:
        last_flush = time.monotonic()
        buffer: list[UsageEvent] = []

        while not self._stop.is_set():
            try:
                timeout = max(0.1, self.flush_interval_sec - (time.monotonic() - last_flush))
                try:
                    evt = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                    buffer.append(evt)
                    if len(buffer) >= self.batch_size:
                        await self._flush(buffer)
                        buffer.clear()
                        last_flush = time.monotonic()
                except asyncio.TimeoutError:
                    if buffer:
                        await self._flush(buffer)
                        buffer.clear()
                        last_flush = time.monotonic()
            except Exception:
                log.exception("[USAGE] Flusher loop error")

        try:
            while True:
                buffer.append(self.queue.get_nowait())
        except asyncio.QueueEmpty:
            pass
        if buffer:
            await self._flush(buffer)


# -------------------------
# Global tracker singleton
# -------------------------
_GLOBAL_TRACKER: Optional[AsyncUsageTracker] = None
_GLOBAL_LOCK = threading.Lock()


def _ensure_global_tracker() -> AsyncUsageTracker:
    global _GLOBAL_TRACKER
    with _GLOBAL_LOCK:
        if _GLOBAL_TRACKER is None:
            _GLOBAL_TRACKER = AsyncUsageTracker()
            try:
                loop = asyncio.get_running_loop()
                _GLOBAL_TRACKER.start()
            except RuntimeError:
                log.debug("[USAGE] No running event loop; global tracker created but not started")
        return _GLOBAL_TRACKER


# -------------------------
# Metric counters and alerting
# -------------------------
# Sliding-window timestamps per metric name
_METRIC_WINDOWS: Dict[str, deque[float]] = defaultdict(lambda: deque())
_METRIC_LOCK = threading.Lock()

# Last time an alert was emitted per metric (to suppress duplicates)
_LAST_ALERT_AT: Dict[str, float] = defaultdict(lambda: 0.0)

# Configurable alert thresholds (env overrides)
USAGE_ALERT_THRESHOLD = int(os.getenv("USAGE_ALERT_THRESHOLD", "10"))  # events
USAGE_ALERT_WINDOW = int(os.getenv("USAGE_ALERT_WINDOW", "60"))  # seconds
USAGE_ALERT_SUPPRESS = int(os.getenv("USAGE_ALERT_SUPPRESS", "300"))  # seconds before re-alert

# Optional: define a callback hook (callable(name, count, window) -> None) for app to receive alerts
_alert_callback: Optional[Callable[[str, int, int], None]] = None


def set_alert_callback(fn: Callable[[str, int, int], None]) -> None:
    """Install a callback invoked when an alert condition is emitted."""
    global _alert_callback
    _alert_callback = fn


def _write_jsonl(path: str, obj: Any) -> None:
    """Helper to append an object to a JSONL file safely."""
    try:
        line = json.dumps(obj, default=str, ensure_ascii=False)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        log.exception("[USAGE] Failed to write JSONL to %s", path)


def _emit_alert(name: str, count: int, window: int) -> None:
    """Emit an alert: log, write alerts JSONL and enqueue an alert-tracking event."""
    ts = utcnow().isoformat()
    alert = {"metric": name, "count": count, "window_s": window, "emitted_at_utc": ts}
    log.warning(
        "[USAGE][ALERT] Metric spike detected: %s (count=%d window_s=%d)", name, count, window
    )
    try:
        _write_jsonl(_alerts_jsonl_path_utc(), alert)
    except Exception:
        log.exception("[USAGE] Could not persist alert JSONL")
    # Attempt to enqueue an alert event into the usage tracker so it gets flushed to SQL
    try:
        tracker = _ensure_global_tracker()
        # Build a compact usage event payload
        evt = {
            "executed_at_utc": utcnow(),
            "command_name": f"metric_alert:{name}",
            "version": "metric",
            "app_context": "internal",
            "user_id": None,
            "user_display": None,
            "guild_id": None,
            "channel_id": None,
            "success": False,
            "error_code": "metric_spike",
            "latency_ms": None,
            "args_shape": {"metric": name, "count": count, "window_s": window},
            "error_text": f"Metric spike alert: {name}={count} in {window}s",
        }

        # schedule async enqueue if loop exists
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(tracker.log(evt))
        except RuntimeError:
            # No loop: write JSONL as fallback
            _write_jsonl(_jsonl_path_utc(), evt)
    except Exception:
        log.exception("[USAGE] Failed to record alert event")

    # Call any user-defined callback for immediate handling (sync)
    try:
        if _alert_callback:
            try:
                _alert_callback(name, count, window)
            except Exception:
                log.exception("[USAGE] alert callback failed")
    except Exception:
        log.exception("[USAGE] error while invoking alert callback")


def _check_and_maybe_alert(name: str) -> None:
    """
    Add current timestamp to sliding window for metric 'name', and if the count in the
    configured window exceeds threshold and not recently alerted, emit an alert.
    """
    now = time.time()
    with _METRIC_LOCK:
        dq = _METRIC_WINDOWS[name]
        dq.append(now)
        # drop timestamps older than window
        cutoff = now - USAGE_ALERT_WINDOW
        while dq and dq[0] < cutoff:
            dq.popleft()
        count = len(dq)

        last_alert = _LAST_ALERT_AT.get(name, 0.0)
        if count >= USAGE_ALERT_THRESHOLD and (now - last_alert) >= USAGE_ALERT_SUPPRESS:
            _LAST_ALERT_AT[name] = now
            # emit alert outside the lock to avoid deadlocks
            # we will call _emit_alert without holding METRIC_LOCK
            pass_count = count
    # If we've just set last_alert, emit now
    if _LAST_ALERT_AT.get(name, 0.0) and (_LAST_ALERT_AT[name] + 0.0001) <= now:
        # Ensure we only emit when we actually updated it (approx)
        # (This condition is permissive but avoids duplicating alerts)
        _emit_alert(name, pass_count, USAGE_ALERT_WINDOW)


# -------------------------
# Public synchronous metric API
# -------------------------
def usage_event(name: str, value: int = 1, metadata: Optional[dict] = None) -> None:
    """
    Record a simple metric event synchronously.
    - name: metric name (string)
    - value: numeric increment (currently only 1 supported for windowing)
    - metadata: optional dict stored with metric JSONL
    Behavior:
    - Writes a line to daily metrics JSONL
    - Attempts to enqueue an event into the AsyncUsageTracker for SQL persistence
    - Updates in-memory sliding-window counters and emits an alert if threshold exceeded
    """
    ts = utcnow()
    metric = {
        "metric": name,
        "value": value,
        "metadata": metadata or {},
        "recorded_at_utc": ts.isoformat(),
    }
    # Best-effort write to metrics JSONL
    try:
        _write_jsonl(_metrics_jsonl_path_utc(), metric)
    except Exception:
        log.exception("[METRIC] Failed to write metric JSONL")

    # Update sliding-window and possibly alert
    try:
        # Use a single tick per call (value currently treated as number of events)
        for _ in range(max(1, int(value))):
            _check_and_maybe_alert(name)
    except Exception:
        log.exception("[METRIC] Sliding-window update failed for %s", name)

    # Attempt to enqueue to AsyncUsageTracker (best-effort, non-blocking)
    try:
        tracker = _ensure_global_tracker()
        # lightweight usage-entry for SQL flush
        evt = {
            "executed_at_utc": ts,
            "command_name": f"metric:{name}",
            "version": "metric",
            "app_context": "metric",
            "user_id": None,
            "user_display": None,
            "guild_id": None,
            "channel_id": None,
            "success": True,
            "error_code": None,
            "latency_ms": None,
            "args_shape": metadata or {},
            "error_text": None,
        }
        try:
            # schedule logging to tracker
            loop = asyncio.get_running_loop()
            asyncio.create_task(tracker.log(evt))
        except RuntimeError:
            # no loop: do a thread-based write to JSONL fallback (already persisted above)
            pass
    except Exception:
        log.exception("[METRIC] Failed to enqueue metric event for %s", name)


# -------------------------
# Admin / inspection helpers
# -------------------------
def metrics_window_count(name: str) -> int:
    """Return the current count of events for metric 'name' in the configured window."""
    with _METRIC_LOCK:
        dq = _METRIC_WINDOWS.get(name)
        if not dq:
            return 0
        now = time.time()
        cutoff = now - USAGE_ALERT_WINDOW
        # copy and trim without mutating original
        return sum(1 for ts in dq if ts >= cutoff)


def set_alert_thresholds(threshold: int, window_s: int, suppress_s: int = 300) -> None:
    """Programmatically override alert thresholds (useful for tests)."""
    global USAGE_ALERT_THRESHOLD, USAGE_ALERT_WINDOW, USAGE_ALERT_SUPPRESS
    USAGE_ALERT_THRESHOLD = int(threshold)
    USAGE_ALERT_WINDOW = int(window_s)
    USAGE_ALERT_SUPPRESS = int(suppress_s)


# Provide a convenience name for external modules
# so they can call usage_tracker.usage_event(...) to record metrics
__all__ = [
    "AsyncUsageTracker",
    "metrics_window_count",
    "set_alert_callback",
    "set_alert_thresholds",
    "usage_event",
]
