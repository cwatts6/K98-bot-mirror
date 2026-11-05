"""Bounded, non-authoritative upload observations, isolated from the main queue."""

from collections import OrderedDict
from datetime import UTC, datetime
import json
import threading
import time
from uuid import uuid4

MAX_COUNTER = 2**63 - 1
UPLOAD_STAGES = frozenset({"upload_audit", "download_log"})


def is_upload_row(row):
    events = list(row.get("transitions", ()))
    events += [e for e in (row.get("first_failure"), row.get("result")) if e]
    events += list(row.get("milestones", {}).values())
    return bool(events) and all(e.get("stage") in UPLOAD_STAGES for e in events)


class UploadObservations:
    capacity = 64

    def __init__(self, wake):
        self.lock = threading.Lock()
        self.wake = wake
        self.slots = OrderedDict()
        self.closed = False
        self.partial = False
        self.counts = {k: 0 for k in ("coalesced", "refused", "invalid", "retention_omitted")}
        self.workers = {}
        self.prior = None
        self.retention_omitted = 0  # Sink-thread-only counter, separate from producer counters.
        self.summary_dirty = False

    def _count(self, key):
        if key == "retention_omitted":
            self.retention_omitted = min(MAX_COUNTER, self.retention_omitted + 1)
            return
        self.counts = dict(self.counts, **{key: min(MAX_COUNTER, self.counts[key] + 1)})

    def offer(self, reference, state, loss, kind):
        if kind not in {"sql", "file"} or state not in {
            "observed",
            "failed",
            "completed",
            "settled",
        }:
            self.partial = True
            return False
        if type(reference) is not str or len(reference) > 36 or type(loss) is not int or loss < 0:
            self.partial = True
            return False
        if not self.lock.acquire(blocking=False):
            # Contended losses cannot be counted exactly without waiting. Do not
            # fabricate exact totals or recursively emit another event.
            self.partial = True
            if not self.summary_dirty:
                self.summary_dirty = True
                self.wake.set()
            return False
        try:
            # Reserve one slot for the single file owner during SQL storms.
            sql_slots = sum(latest["stage"] == "upload_audit" for _, latest in self.slots.values())
            full = len(self.slots) >= self.capacity or (kind == "sql" and sql_slots >= 63)
            if self.closed or (reference not in self.slots and full):
                self._count("refused")
                return False
            event = dict(
                reference=reference,
                stage="upload_audit" if kind == "sql" else "download_log",
                state=state,
                observed_utc=datetime.now(UTC).isoformat(),
                diagnostic_loss=min(MAX_COUNTER, loss),
                schema="operation-boundary/2",
                event_id=str(uuid4()),
                sequence=time.monotonic_ns(),
                role="parent",
                origin="code_owned",
                actor="system",
            )
            previous = self.slots.get(reference)
            first = previous[0] if previous else None
            if first is None and state == "failed":
                first = event
            if previous:
                event["diagnostic_loss"] = max(
                    event["diagnostic_loss"], previous[1]["diagnostic_loss"]
                )
            slot = (first, event)
            if len(json.dumps(slot, separators=(",", ":")).encode()) > 4096:
                self._count("invalid")
                return False
            if previous:
                self._count("coalesced")
            self.slots[reference] = slot
            if previous is None:
                self.wake.set()
            return True
        finally:
            self.lock.release()

    def summary(self, kind, state, unavailable, error_type, dropped=0, failures=0):
        if kind not in {"sql", "file"}:
            return
        if type(state) is not str or len(state) > 40:
            self.partial = True
            return
        if any(type(value) is not int or value < 0 for value in (unavailable, dropped, failures)):
            self.partial = True
            return
        if error_type is not None and (type(error_type) is not str or len(error_type) > 80):
            self.partial = True
            error_type = "unavailable"
        if not self.lock.acquire(blocking=False):
            self.partial = True
            return
        try:
            if self.closed:
                return
            self.workers = dict(
                self.workers,
                **{
                    kind: dict(
                        state=str(state)[:40],
                        unavailable=min(MAX_COUNTER, max(0, unavailable)),
                        dropped=min(MAX_COUNTER, dropped),
                        failures=min(MAX_COUNTER, failures),
                        error_type=error_type,
                        observed_utc=datetime.now(UTC).isoformat(),
                    )
                },
            )
            if not self.summary_dirty:
                self.summary_dirty = True
                self.wake.set()
        finally:
            self.lock.release()

    def take(self, limit=16):
        with self.lock:
            self.summary_dirty = False
            slots = [self.slots.popitem(last=False)[1] for _ in range(min(limit, len(self.slots)))]
        return [
            event
            for first, latest in slots
            for event in ([first, latest] if first and first != latest else [latest])
        ]

    def close(self):
        with self.lock:
            self.closed = True

    def report(self):
        counts = dict(self.counts, retention_omitted=self.retention_omitted)
        return dict(
            schema="optional-upload-observations/1",
            **counts,
            coverage="partial" if self.partial or any(counts.values()) else "available",
            counters_exact=not self.partial,
            pending=len(self.slots),
            diagnostic_loss_coverage="lower_bound",
            workers={k: dict(v) for k, v in self.workers.items()},
            prior=self.prior if self.prior is not None else "unknown",
            authority="diagnostic_only",
        )

    def restore(self, value):
        if type(value) is not dict or value.get("schema") != "optional-upload-observations/1":
            return
        counts = {k: value.get(k) for k in self.counts}
        if not all(type(v) is int and 0 <= v <= MAX_COUNTER for v in counts.values()):
            self.partial = True
            return
        prior = value.get("prior")
        if type(prior) is dict:
            for key in counts:
                old = prior.get(key)
                if type(old) is int and 0 <= old <= MAX_COUNTER:
                    counts[key] = min(MAX_COUNTER, counts[key] + old)
                else:
                    self.partial = True
        # Never restore a live worker, mailbox, handle or recursively nested past.
        self.prior = dict(counts, coverage="partial", authority="historical_diagnostic_only")
