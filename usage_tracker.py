# usage_tracker.py
from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Callable

from constants import BASE_DIR, _conn
from utils import ensure_aware_utc, utcnow

log = logging.getLogger(__name__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

UsageEvent = dict[str, Any]

# Explicit UTC alias for clarity
UTC = timezone.utc


def _jsonl_path_utc() -> str:
    # Use repository-wide utcnow() helper so filename date is consistent
    return os.path.join(DATA_DIR, f"command_usage_{utcnow().strftime('%Y%m%d')}.jsonl")


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
            self._task = asyncio.create_task(self._run(), name="usage-tracker")

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

            # Offload blocking file write to a thread — best-effort, fire-and-forget
            def _sync_write(
                ecopy: UsageEvent, path_fn: Callable[[], str] = _jsonl_path_utc
            ) -> None:
                try:
                    line = json.dumps(ecopy, separators=(",", ":"), ensure_ascii=False)
                    with open(path_fn(), "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                except Exception:
                    # Log to the main logger — this runs in a thread; ensure exception is surfaced
                    log.exception("[USAGE] Local JSONL background write failed")

            # create a background task that offloads the sync write to a thread
            try:
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
        Accepts:
          - ISO strings (with Z or +00:00 or without) -> parsed -> aware UTC -> naive UTC
          - datetime objects (naive or aware) -> normalized to aware UTC -> naive UTC
          - other values: returned unchanged (driver may accept string)
        """
        if isinstance(ts, str):
            try:
                # Accept trailing Z
                if ts.endswith("Z"):
                    ts = ts[:-1] + "+00:00"
                dt = datetime.fromisoformat(ts)
            except Exception:
                # leave as-is (string) if parsing fails
                return ts
            # Ensure aware UTC, then return naive UTC for DB
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
                # 0 ExecutedAtUtc -> provide naive UTC datetime for DATETIME2
                self._coerce_ts(e.get("executed_at_utc")),
                clip(e.get("command_name"), 64),  # 1 CommandName
                clip(e.get("version"), 16),  # 2 Version
                clip(e.get("app_context", "slash"), 16),  # 3 AppContext
                e.get("user_id"),  # 4 UserId (BIGINT in SQL)
                clip(e.get("user_display"), 128),  # 5 UserDisplay
                e.get("guild_id"),  # 6 GuildId (BIGINT)
                e.get("channel_id"),  # 7 ChannelId (BIGINT)
                1 if e.get("success", True) else 0,  # 8 Success (BIT)
                clip(e.get("error_code"), 64),  # 9 ErrorCode
                e.get("latency_ms"),  # 10 LatencyMs (INT/NULL)
                json.dumps(e.get("args_shape")) if e.get("args_shape") else None,  # 11 ArgsShape
                e.get("error_text"),  # 12 ErrorText
            )

        rows = [row_from(e) for e in events]

        # Flush summary with command mix
        cmd_counts = Counter(r[1] for r in rows)  # r[1] = CommandName
        log.info(
            "[USAGE] Flushing %d events: %s",
            len(rows),
            ", ".join(f"{k}={v}" for k, v in cmd_counts.most_common()),
        )

        # Sort longest-first to help driver sizing stability
        rows.sort(
            key=lambda t: (
                -(len(t[1]) if isinstance(t[1], str) else 0),  # CommandName
                -(len(t[5]) if isinstance(t[5], str) else 0),  # UserDisplay
                -(len(t[9]) if isinstance(t[9], str) else 0),  # ErrorCode
                -(len(t[3]) if isinstance(t[3], str) else 0),  # AppContext
            )
        )

        # Single statement: CAST MAX columns explicitly to avoid driver quirks.
        SQL_INSERT = """
            INSERT INTO dbo.BotCommandUsage
            (ExecutedAtUtc, CommandName, Version, AppContext,
             UserId, UserDisplay, GuildId, ChannelId,
             Success, ErrorCode, LatencyMs, ArgsShape, ErrorText)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS NVARCHAR(MAX)), CAST(? AS NVARCHAR(MAX)))
        """
        #             0   1    2    3    4    5    6    7    8    9    10         11                           12

        try:
            conn = _conn()
            cur = conn.cursor()

            # Critical: disable fast path when MAX columns exist (guard attribute access)
            if hasattr(cur, "fast_executemany"):
                try:
                    cur.fast_executemany = False
                except Exception:
                    # If driver rejects setting the attribute, ignore and continue
                    log.debug("[USAGE] Could not set fast_executemany on cursor; continuing safely")

            cur.executemany(SQL_INSERT, rows)

            conn.commit()
            cur.close()
            conn.close()
            log.info(
                "[USAGE] Flushed %d events to SQL (safe batch, no fast_executemany)", len(events)
            )

        except Exception:
            # If anything goes wrong, try per-row to salvage partials
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
                    # Wait for next event, but wake on timeout to flush
                    evt = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                    buffer.append(evt)
                    if len(buffer) >= self.batch_size:
                        await self._flush(buffer)
                        buffer.clear()
                        last_flush = time.monotonic()
                except asyncio.TimeoutError:
                    # Time to flush whatever we have
                    if buffer:
                        await self._flush(buffer)
                        buffer.clear()
                        last_flush = time.monotonic()
            except Exception:
                log.exception("[USAGE] Flusher loop error")

        # Final drain on stop
        try:
            while True:
                buffer.append(self.queue.get_nowait())
        except asyncio.QueueEmpty:
            pass
        if buffer:
            await self._flush(buffer)
