"""Bounded optional diagnostic projection; no business admission, replay or repair API.

Only the sink thread touches disk. Producers and report readers never wait for it.
An entered disk write must settle before shutdown can claim this sink drained.
"""

from collections import deque
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import stat
import threading

from core.operation_evidence import optional

MAX_EVENT = 8192
MAX_PROJECTION = 32768
MAX_OPERATIONS = 512
MAX_FILE = MAX_PROJECTION * MAX_OPERATIONS
_critical = {
    "failed",
    "interrupted",
    "settled",
    "completed",
    "completed_after_deadline",
    "verification_unavailable",
    "cancelled_outcome_unconfirmed",
    "deadline_elapsed_outcome_unconfirmed",
}
_sink = None


def _reject_links(path):
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Diagnostic reparse/link path refused")


class DiagnosticSink:
    def __init__(self, directory=None, *, capacity=1024, reserve=128):
        self.directory = Path(directory) if directory is not None else None
        self.capacity, self.reserve = capacity, reserve
        self.queue = deque()
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.closed = False
        self.dropped = 0
        self.failures = 0
        self.evicted = 0
        self.records = {}
        self.snapshot = {"operations": [], "status": "starting"}
        # logging_setup owns explicit close plus an atexit close/join. A daemon
        # flag permits that atexit hook to run (Python joins non-daemons first).
        self.thread = threading.Thread(target=self._run, name="operation-diagnostics", daemon=True)

    def start(self):
        self.wake.set()
        self.thread.start()
        return self

    def offer(self, event):
        # Bound primitive shapes before copying. No conversion of caller objects.
        if (
            type(event) is not dict
            or len(event) > 26
            or any(
                type(k) is not str
                or len(k) > 40
                or not (
                    type(v) is bool
                    or (type(v) is str and len(v) <= 80)
                    or (type(v) in (int, float) and 0 <= v <= 1e20)
                )
                for k, v in event.items()
            )
        ):
            self.dropped += 1
            return False
        if not self.lock.acquire(blocking=False):
            self.dropped += 1
            return False
        try:
            limit = (
                self.capacity if event.get("state") in _critical else self.capacity - self.reserve
            )
            if self.closed or len(self.queue) >= limit:
                self.dropped += 1
                return False
            self.queue.append(dict(event))
            self.wake.set()
            return True
        finally:
            self.lock.release()

    def close(self):
        # Called only after business owners drain. Retain all accepted observations.
        with self.lock:
            self.closed = True
            self.wake.set()
        if self.thread.ident is not None:
            self.thread.join()  # No timeout that could falsely certify physical settlement.

    def report(self):
        snapshot = self.snapshot  # Writer publishes by replacement, never mutation.
        result = {key: value for key, value in snapshot.items() if key != "operations"}
        result["operations"] = []
        used = 0
        # Bounded passive report copy. First failures outrank routine completions.
        rows = sorted(snapshot["operations"], key=lambda row: row["first_failure"] is None)
        for row in rows:
            # Report first failure and latest state; the bounded disk projection
            # retains the intervening transitions for incident investigation.
            summary = {key: value for key, value in row.items() if key != "transitions"}
            summary["latest"] = row["transitions"][-1] if row["transitions"] else None
            size = len(json.dumps(summary, indent=2)) + 256
            if used + size > 12000:
                break
            result["operations"].append(deepcopy(summary))
            used += size
        result["omitted_operations"] = len(rows) - len(result["operations"])
        result.update(
            dropped=self.dropped,
            sink_failures=self.failures,
            evicted=self.evicted,
            worker_alive=self.thread.is_alive(),
            authority="diagnostic_only",
            sql_holder="unavailable_P02",
        )
        return result

    def _load(self):
        if self.directory is None:
            return
        _reject_links(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        temp = self.directory / "observations.tmp"
        _reject_links(temp)
        # A previous process can leave an incomplete optional temp. Unlinking a
        # hard link removes only this directory entry; never open it for writing.
        temp.unlink(missing_ok=True)
        path = self.directory / "observations.json"
        _reject_links(path)
        if not path.exists():
            return
        if path.stat().st_size > MAX_FILE:
            raise ValueError("Diagnostic projection too large")
        with path.open("rb") as stream:
            payload = stream.read(MAX_FILE + 1)
        if len(payload) > MAX_FILE:
            raise ValueError("Diagnostic projection too large")
        document = json.loads(payload)
        if document.get("schema") != "operation-observations/1":
            raise ValueError("Unknown diagnostic schema")
        rows = document["operations"]
        if type(rows) is not list or len(rows) > MAX_OPERATIONS:
            raise ValueError("Diagnostic inventory too large")
        for name in ("dropped", "sink_failures", "evicted"):
            value = document.get(name, 0)
            if type(value) is not int or not 0 <= value < 2**63:
                raise ValueError("Invalid diagnostic counter")
            setattr(self, "failures" if name == "sink_failures" else name, value)
        for row in rows:
            # Revalidate every value from disk using the same primitive allowlist.
            events = row["transitions"]
            if type(events) is not list or len(events) > 32:
                raise ValueError("Diagnostic transition bound")
            first = row.get("first_failure")
            if first is not None:
                self._accept(first)
            retained_result = row.get("result")
            if retained_result is not None:
                self._accept(retained_result)
            for event in events:
                self._accept(event)
            omitted = row.get("omitted", 0)
            if type(omitted) is not int or not 0 <= omitted < 2**63:
                raise ValueError("Invalid omitted count")
            retained = self.records.get(row.get("reference"))
            if retained is not None:
                retained["omitted"] += omitted

    def _accept(self, event):
        from uuid import UUID

        from core.operation_evidence import STAGES, STATES, label

        allowed = {
            "reference",
            "local_holder_reference",
            "stage",
            "state",
            "observed_utc",
            "process_incarnation",
            "pid",
            "thread_id",
            "native_process_creation",
            "sql_holder",
            "attempt_id",
            "operation_id",
            "elapsed_ms",
            "timing_scope",
            "reported_success",
            "attempt_recording",
            "attempt_outcome",
            "import_reported_success",
            "error_type",
            "sqlstate",
            "native_error",
            "failure_function",
            "failure_line",
        }
        if (
            type(event) is not dict
            or not set(event) <= allowed
            or len(json.dumps(event)) > MAX_EVENT
        ):
            raise ValueError("Invalid diagnostic event")
        for key, value in event.items():
            if key in {
                "reference",
                "process_incarnation",
                "attempt_id",
                "operation_id",
                "local_holder_reference",
            }:
                if type(value) is not str or len(value) > 36:
                    raise ValueError("Invalid diagnostic identity")
                UUID(value)
            elif key == "observed_utc":
                if (
                    type(value) is not str
                    or len(value) > 40
                    or datetime.fromisoformat(value).tzinfo is None
                ):
                    raise ValueError("Invalid observation time")
            elif key in {"pid", "thread_id", "elapsed_ms", "native_error", "failure_line"}:
                if type(value) not in (int, float) or not 0 <= value <= 1e20:
                    raise ValueError("Invalid diagnostic number")
            elif key in {"reported_success", "import_reported_success"}:
                if type(value) is not bool:
                    raise ValueError("Invalid diagnostic boolean")
            elif key == "sqlstate":
                import re

                if type(value) is not str or re.fullmatch(r"[0-9A-Z]{5}", value) is None:
                    raise ValueError("Invalid SQLSTATE")
            elif label(value) != value:
                raise ValueError("Invalid diagnostic label")
        if event.get("stage") not in STAGES or event.get("state") not in STATES:
            raise ValueError("Unknown diagnostic stage/state")
        for key, values in {
            "native_process_creation": {"unavailable_not_collected"},
            "sql_holder": {"unavailable_P02"},
            "timing_scope": {"inclusive"},
            "attempt_recording": {"recorded", "unrecorded"},
            "attempt_outcome": {
                "unconfirmed",
                "reported_success",
                "failed_before_inputs",
                "failed_after_inputs",
            },
        }.items():
            if key in event and event[key] not in values:
                raise ValueError("Unknown diagnostic fact")
        reference = event["reference"]
        row = self.records.get(reference)
        if row is None:
            if len(self.records) >= MAX_OPERATIONS:
                completed = next(
                    (key for key, value in self.records.items() if value["complete"]), None
                )
                if completed is None:
                    self.dropped += 1
                    return
                del self.records[completed]
                self.evicted += 1
            row = self.records[reference] = dict(
                reference=reference,
                transitions=[],
                first_failure=None,
                result=None,
                omitted=0,
                complete=False,
            )
        if "reported_success" in event or "attempt_recording" in event:
            row["result"] = event
        failure = event["state"] in {"failed", "interrupted", "verification_unavailable"}
        if failure and row["first_failure"] is None:
            row["first_failure"] = event
        # Repeated ordinary observations coalesce, with explicit loss count.
        transitions = row["transitions"]
        if transitions and (transitions[-1]["stage"], transitions[-1]["state"]) == (
            event["stage"],
            event["state"],
        ):
            transitions.pop()
            row["omitted"] += 1
        transitions.append(event)
        while len(transitions) > 32 or len(json.dumps(row)) > MAX_PROJECTION:
            transitions.pop(0)
            row["omitted"] += 1
        row["complete"] = (
            event["stage"] == "operation"
            and event["state"] == "settled"
            and row["first_failure"] is None
        )

    def _publish(self):
        cutoff = datetime.now(UTC) - timedelta(days=30)
        for key, row in list(self.records.items()):
            if (
                row["complete"]
                and datetime.fromisoformat(row["transitions"][-1]["observed_utc"]) < cutoff
            ):
                del self.records[key]
                self.evicted += 1
        document = dict(
            schema="operation-observations/1",
            operations=list(self.records.values()),
            retention_days=30,
            dropped=self.dropped,
            sink_failures=self.failures,
            evicted=self.evicted,
            observed_utc=datetime.now(UTC).isoformat(),
            status="closed" if self.closed else "observing",
        )
        self.snapshot = deepcopy(document)
        if self.directory is not None:
            path = self.directory / "observations.json"
            temp = self.directory / "observations.tmp"
            _reject_links(path)
            _reject_links(temp)
            data = json.dumps(document, allow_nan=False).encode("utf-8")
            if len(data) > MAX_FILE:
                raise ValueError("Diagnostic file bound")
            with temp.open("xb") as stream:
                try:
                    stream.write(data)
                    stream.flush()
                except BaseException:
                    stream.close()
                    temp.unlink(missing_ok=True)
                    raise
            try:
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)

    def _run(self):
        try:
            self._load()
        except Exception:
            self.failures += 1
        while True:
            self.wake.wait()
            with self.lock:
                events = list(self.queue)
                self.queue.clear()
                self.wake.clear()
                closed = self.closed
            for event in events:
                try:
                    self._accept(event)
                except Exception:
                    self.failures += 1
            try:
                self._publish()
            except Exception:
                self.failures += 1
            if closed:
                return


def configure(directory):
    global _sink
    if _sink is None:
        _sink = DiagnosticSink(directory).start()


def offer(event):
    if _sink is not None:
        optional(_sink.offer, event)


def shutdown():
    if _sink is not None:
        _sink.close()


def report():
    result = optional(_sink.report) if _sink is not None else None
    return result or {"operations": [], "status": "unavailable", "authority": "diagnostic_only"}
