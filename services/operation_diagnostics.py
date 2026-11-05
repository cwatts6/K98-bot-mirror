"""Bounded optional diagnostic projection; no business admission, replay or repair API.

Only the sink thread touches disk. Producers and report readers never wait for it.
An entered disk write must settle before shutdown can claim this sink drained.
"""

from collections import deque
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import stat
import threading
import time

from core.operation_evidence import optional
from services.optional_upload_observations import UploadObservations, is_upload_row

MAX_EVENT = 8192
MAX_V2_EVENT = 2048
MAX_COUNTER = 2**63 - 1
SLOTS = {
    "scope_entry",
    "physical_entry",
    "deadline",
    "cancellation",
    "failure",
    "parent_return",
    "verification",
    "terminal",
}
V2_FIELDS = {
    "schema",
    "event_id",
    "sequence",
    "role",
    "origin",
    "actor",
    "child_reference",
    "parent_reference",
    "value_kind",
    "value_meaning",
    "value_boolean",
    "feature_outcome",
    "verification_reason",
    "verification_source",
    "main_cache",
    "last_kvk_cache",
    "data_outcome",
    "execution_outcome",
    "persistence_outcome",
    "restoration_outcome",
    "attached",
    "pruned",
    "superseded",
    "failed_count",
    "unattempted",
    "outcome_unconfirmed",
    "diagnostic_loss",
}
NEW_STAGES = {
    "rehydrate_tracked_views",
    "rehydrate_vote_post_views",
    "rehydrate_survey_post_views",
    "rehydrate_pinned_calendar_view",
}


def encoded(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode(
        "utf-8"
    )


def encoded_document_parts(document):
    """Keep each serialization step bounded by one validated operation row."""
    yield b"{"
    for index, (key, value) in enumerate(document.items()):
        yield (b"," if index else b"") + encoded(key) + b":"
        if key != "operations":
            yield encoded(value)
            continue
        yield b"["
        for row_index, row in enumerate(value):
            yield (b"," if row_index else b"") + encoded(row)
        yield b"]"
    yield b"}"


def utc():
    return datetime.now(UTC).isoformat()


MAX_PROJECTION = 32768
MAX_OPERATIONS = 512
MAX_FILE = MAX_PROJECTION * MAX_OPERATIONS
PUBLISH_INTERVAL = 1.0
_critical = {
    "entered",
    "result_returned",
    "deadline_elapsed_draining",
    "deadline_elapsed_pending",
    "cancelled_draining",
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
        self.uploads = UploadObservations(self.wake)
        self.closing = threading.Event()
        self.closed = False
        self.dropped = 0
        self.failures = 0
        self.evicted = 0
        self.context_losses = 0
        self.prior_counters = {}
        self.critical_dropped = 0
        self.invalid = 0
        self.restore_failures = 0
        self.children_omitted = 0
        self.refused_operations = 0
        self.emission_failures = 0
        self.unknown_stages = 0
        self.unknown_historical_counters = set()
        self.eviction_provenance = {}
        self.eviction_history_available = True
        self.publication = {"v1": {}, "v2": {}}
        self.restore_status = "not_loaded"
        self.blocked_files = set()
        self.generation = 0
        self.queue_high_water = 0
        self.records = {}
        self._published_rows = {}
        self._dirty_rows = set()
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
            or len(event) > 56
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
            self._drop(event)
            return False
        if len(encoded(event)) > (MAX_V2_EVENT if event.get("schema") else MAX_EVENT):
            self._drop(event)
            return False
        if not self.lock.acquire(blocking=False):
            self._drop(event)
            return False
        try:
            limit = (
                self.capacity if event.get("state") in _critical else self.capacity - self.reserve
            )
            if self.closed or len(self.queue) >= limit:
                self._drop(event)
                return False
            self.queue.append(dict(event))
            self.queue_high_water = max(self.queue_high_water, len(self.queue))
            self.wake.set()
            return True
        finally:
            self.lock.release()

    def _drop(self, event):
        self.dropped = min(MAX_COUNTER, self.dropped + 1)
        if type(event) is dict and event.get("state") in _critical:
            self.critical_dropped = min(MAX_COUNTER, self.critical_dropped + 1)

    def _make_room(self, upload, reason):
        optional_rows = [key for key, row in self.records.items() if is_upload_row(row)]
        if upload and len(optional_rows) >= 64:
            victim = next((key for key in optional_rows if self.records[key]["complete"]), None)
            if victim is None:
                self.uploads._count("retention_omitted")
                return False
            self._evict(victim, reason)
        if len(self.records) < MAX_OPERATIONS:
            return True
        victim = next(iter(optional_rows), None)
        if victim is None and not upload:
            victim = next((key for key, row in self.records.items() if row["complete"]), None)
        if victim is None:
            if upload:
                self.uploads._count("retention_omitted")
            else:
                self.dropped += 1
                self.refused_operations += 1
            return False
        self._evict(victim, reason)
        return True

    def close(self):
        self.uploads.close()
        # Called only after business owners drain. Retain all accepted observations.
        with self.lock:
            self.closed = True
            self.closing.set()
            self.wake.set()
        if self.thread.ident is not None:
            self.thread.join()  # No timeout that could falsely certify physical settlement.

    def _live_counters(self):
        # Loading old evidence never writes the live producer counters. Saturate
        # totals within the restore contract rather than persisting unreadable counts.
        counters = dict(
            dropped=self.dropped,
            sink_failures=self.failures,
            evicted=self.evicted,
            context_losses=self.context_losses,
            critical_dropped=self.critical_dropped,
            invalid=self.invalid,
            restore_failures=self.restore_failures,
            children_omitted=self.children_omitted,
            refused_operations=self.refused_operations,
            emission_failures=self.emission_failures,
            unknown_stages=self.unknown_stages,
        )
        return {name: min(MAX_COUNTER, value) for name, value in counters.items()}

    def _counter_totals(self):
        live = self._live_counters()
        prior = self.prior_counters
        return {name: min(2**63 - 1, value + prior.get(name, 0)) for name, value in live.items()}

    def _counter_provenance(self):
        from core.operation_evidence import _incarnation

        return dict(
            process_incarnation=_incarnation or "unavailable",
            current=self._live_counters(),
            historical={
                name: (
                    "unknown"
                    if name in self.unknown_historical_counters
                    else self.prior_counters.get(name, 0)
                )
                for name in self._live_counters()
            },
            totals_coverage="partial" if self.unknown_historical_counters else "available",
        )

    def _evict(self, reference, reason, cutoff=None):
        from core.operation_evidence import _incarnation

        if is_upload_row(self.records[reference]):
            self.uploads._count("retention_omitted")
        del self.records[reference]
        self.evicted = min(MAX_COUNTER, self.evicted + 1)
        prior = self.eviction_provenance.get(reason, {})
        self.eviction_provenance[reason] = dict(
            count=min(MAX_COUNTER, prior.get("count", 0) + 1),
            observed_utc=utc(),
            process_incarnation=_incarnation or "unavailable",
            cutoff_utc=cutoff or "not_applicable",
        )

    def _restore_provenance(self, document):
        # Only the four bounded code-owned eviction reasons may cross restart.
        prior = document.get("counter_provenance", {})
        historical = prior.get("historical", {}) if type(prior) is dict else {}
        if type(historical) is dict:
            self.unknown_historical_counters.update(
                key for key in self._live_counters() if historical.get(key) == "unknown"
            )
        value = document.get("eviction_provenance")
        self.eviction_history_available = (
            type(value) is dict and document.get("eviction_history_available") is True
        )
        if type(value) is not dict or len(value) > 4:
            self.eviction_history_available = False
            if value is not None:
                self.invalid = min(MAX_COUNTER, self.invalid + 1)
            return
        for reason, row in value.items():
            try:
                if (
                    reason not in {"capacity", "retention", "file_bound", "restore_capacity"}
                    or type(row) is not dict
                ):
                    raise ValueError("Invalid eviction reason")
                if set(row) != {"count", "observed_utc", "process_incarnation", "cutoff_utc"}:
                    raise ValueError("Invalid eviction fields")
                if type(row["count"]) is not int or not 0 <= row["count"] <= MAX_COUNTER:
                    raise ValueError("Invalid eviction count")
                from uuid import UUID

                incarnation = row["process_incarnation"]
                if type(incarnation) is not str or len(incarnation) > 36:
                    raise ValueError("Invalid eviction identity")
                if incarnation != "unavailable":
                    UUID(incarnation)
                for key in ("observed_utc", "cutoff_utc"):
                    stamp = row[key]
                    if key == "cutoff_utc" and stamp == "not_applicable":
                        continue
                    if (
                        type(stamp) is not str
                        or len(stamp) > 40
                        or datetime.fromisoformat(stamp).tzinfo is None
                    ):
                        raise ValueError("Invalid eviction time")
                self.eviction_provenance[reason] = dict(row)
            except (ValueError, TypeError, AttributeError):
                self.invalid = min(MAX_COUNTER, self.invalid + 1)
                self.eviction_history_available = False

    def report(self):
        snapshot = self.snapshot  # Writer publishes by replacement, never mutation.
        result = {key: value for key, value in snapshot.items() if key != "operations"}
        result["operations"] = []
        used = 0
        # Bounded passive report copy. First failures outrank routine completions.
        # Newest evidence within each class must not be starved by restored
        # legacy history. Full first-failure records remain in the archive.
        rows = sorted(
            reversed(snapshot["operations"]),
            key=lambda row: (
                is_upload_row(row),
                row.get("schema") == "legacy_projection",
                row["first_failure"] is None,
            ),
        )
        for row in rows:
            # Report first failure and latest state; the bounded disk projection
            # retains the intervening transitions for incident investigation.
            summary = {key: value for key, value in row.items() if key != "transitions"}
            summary["latest"] = row["transitions"][-1] if row["transitions"] else None
            size = len(json.dumps(summary, indent=2)) + 256
            if used + size > 12000:
                continue
            result["operations"].append(deepcopy(summary))
            used += size
        result["omitted_operations"] = len(rows) - len(result["operations"])
        result.update(
            **self._counter_totals(),
            counter_provenance=self._counter_provenance(),
            eviction_provenance=deepcopy(self.eviction_provenance),
            eviction_history_available=self.eviction_history_available,
            worker_alive=self.thread.is_alive(),
            publication=deepcopy(self.publication),
            restore_status=self.restore_status,
            queue_high_water=self.queue_high_water,
            counter_saturated=any(
                value == MAX_COUNTER for value in self._counter_totals().values()
            ),
            upload_observations=self.uploads.report(),
            authority="diagnostic_only",
            sql_holder="unavailable_P02",
        )
        return result

    def full_snapshot(self):
        """Immutable published generation; no disk reads or sink lock."""
        return deepcopy(self.snapshot)

    def _read(self, path, schema):
        _reject_links(path)
        if path.stat().st_size > MAX_FILE:
            self.blocked_files.add(path.name)  # Preserve oversized original in place.
            raise ValueError("Diagnostic projection too large")
        with path.open("rb") as stream:
            payload = stream.read(MAX_FILE + 1)
        if len(payload) > MAX_FILE:
            raise ValueError("Diagnostic projection too large")
        document = json.loads(payload)
        if type(document) is not dict or document.get("schema") != schema:
            raise ValueError("Unknown diagnostic schema")
        rows = document.get("operations")
        if type(rows) is not list or len(rows) > MAX_OPERATIONS:
            raise ValueError("Diagnostic inventory too large")
        return document

    def _preserve_invalid(self, path):
        invalid = path.with_suffix(".invalid")
        _reject_links(invalid)
        if invalid.exists() or path.name in self.blocked_files:
            self.blocked_files.add(path.name)
        else:
            os.replace(path, invalid)

    def _restore_row(self, row):
        # Validate a row in isolation before installing any of its events. No
        # replay through _accept: that would count restored detail as fresh loss.
        if type(row) is not dict or len(encoded(row)) > MAX_PROJECTION:
            raise ValueError("Invalid diagnostic row")
        transitions = row.get("transitions")
        if type(transitions) is not list or len(transitions) > 32:
            raise ValueError("Invalid transitions")
        events = list(transitions)
        for key in ("first_failure", "result"):
            if row.get(key) is not None:
                events.append(row[key])
        milestones = row.get("milestones", {})
        if type(milestones) is not dict or not set(milestones) <= SLOTS:
            raise ValueError("Invalid milestones")
        events.extend(milestones.values())
        for event in events:
            self._validate(event)
            if event["reference"] != row.get("reference"):
                raise ValueError("Mixed diagnostic identities")
        if not events:
            raise ValueError("Missing diagnostic events")
        restored = dict(
            reference=row["reference"],
            transitions=transitions,
            first_failure=row.get("first_failure"),
            result=row.get("result"),
            complete=False,
            omitted=0,
        )
        for name in ("omitted", "coalesced", "trimmed", "deadline_count", "cancellation_count"):
            value = row.get(name, 0)
            if type(value) is not int or not 0 <= value <= MAX_COUNTER:
                raise ValueError("Invalid diagnostic counter")
            restored[name] = value
        if row.get("legacy_interval") == "v1_only_interval_unknown_loss_split":
            restored["legacy_interval"] = row["legacy_interval"]
        if row.get("schema") == "operation-projection/2" or milestones:
            restored["milestones"] = milestones
            restored["schema"] = "operation-projection/2"
            children = row.get("children", {})
            if type(children) is not dict or len(children) > 16 or len(encoded(children)) > 8192:
                raise ValueError("Invalid children")
            for identity, child in children.items():
                from uuid import UUID

                UUID(identity)
                if type(child) is not dict or len(encoded(child)) > 512:
                    raise ValueError("Invalid child")
                if not set(child) <= {
                    "child_reference",
                    "stage",
                    "first_utc",
                    "latest_utc",
                    "state",
                    "value_kind",
                    "value_boolean",
                    "failure",
                }:
                    raise ValueError("Unknown child field")
                if child.get("child_reference") != identity:
                    raise ValueError("Invalid child identity")
                from core.operation_evidence import STAGES, STATES

                if child.get("stage") not in STAGES or child.get("state") not in STATES:
                    raise ValueError("Invalid child stage/state")
                if child.get("value_kind", "unavailable") not in {
                    "unavailable",
                    "boolean",
                    "none",
                    "dict",
                    "tuple",
                    "list",
                }:
                    raise ValueError("Invalid child return kind")
                for stamp in ("first_utc", "latest_utc"):
                    if (
                        type(child.get(stamp)) is not str
                        or len(child[stamp]) > 40
                        or datetime.fromisoformat(child[stamp]).tzinfo is None
                    ):
                        raise ValueError("Invalid child timestamp")
                for flag in ("value_boolean", "failure"):
                    if flag in child and type(child[flag]) is not bool:
                        raise ValueError("Invalid child flag")
                for key, value in child.items():
                    if type(value) not in (str, bool) or (type(value) is str and len(value) > 80):
                        raise ValueError("Invalid child fact")
            restored["children"] = children
            for name in ("deadline_latest", "cancellation_latest"):
                if row.get(name) is not None:
                    self._validate(row[name])
                    if row[name]["reference"] != row["reference"]:
                        raise ValueError("Mixed repeat identity")
                    restored[name] = row[name]
        else:
            restored["schema"] = "legacy_projection"
            restored["legacy_loss_split"] = "unknown"
        terminal = milestones.get("terminal") or (transitions[-1] if transitions else {})
        restored["complete"] = (
            terminal.get("stage") == "operation"
            and terminal.get("state") == "settled"
            and restored["first_failure"] is None
        ) or (
            terminal.get("stage") in {"upload_audit", "download_log"}
            and terminal.get("state") == "settled"
        )
        return restored

    def _load(self):
        if self.directory is None:
            return
        # Fail closed on history completeness until a usable document or a
        # genuinely absent history is established, including filesystem errors.
        self.eviction_history_available = False
        self.unknown_historical_counters.update(self._live_counters())
        _reject_links(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        documents = {}
        for version, filename in (("v2", "observations-v2.json"), ("v1", "observations.json")):
            path = self.directory / filename
            temp = path.with_suffix(".tmp")
            _reject_links(temp)
            temp.unlink(missing_ok=True)
            if not path.exists():
                continue
            try:
                documents[version] = self._read(path, "operation-observations/" + version[-1])
            except Exception:
                self.restore_failures += 1
                self.failures += 1
                self.restore_status = "invalid_" + version
                try:
                    self._preserve_invalid(path)
                except Exception:
                    self.blocked_files.add(filename)
        selected = documents.get("v2", documents.get("v1"))
        if selected is None:
            quarantined = any(
                (self.directory / name).exists()
                for name in ("observations-v2.invalid", "observations.invalid")
            )
            if not self.restore_failures and not quarantined:
                self.restore_status = "absent"
                self.eviction_history_available = True
                self.unknown_historical_counters.clear()
            elif not self.restore_failures:
                self.restore_status = "unavailable_history"
            return
        self.unknown_historical_counters.clear()
        self.restore_status = ("v2" if "v2" in documents else "legacy_v1") + (
            "_older_fallback" if self.restore_failures else "_restored"
        )
        for name in self._counter_totals():
            if name not in selected:
                self.unknown_historical_counters.add(name)
            value = selected.get(name, 0)
            if type(value) is int and 0 <= value <= MAX_COUNTER:
                self.prior_counters[name] = value
            else:
                self.invalid += 1
                self.unknown_historical_counters.add(name)
        self._restore_provenance(selected)
        self.uploads.restore(selected.get("upload_observations"))
        for version, document in documents.items():
            for row in document["operations"]:
                try:
                    restored = self._restore_row(row)
                    # V2 wins shared identities. V1-only roots from a downgrade
                    # remain explicitly legacy; never fabricate missing milestones.
                    if restored["reference"] not in self.records:
                        if not self._make_room(is_upload_row(restored), "restore_capacity"):
                            continue
                        self.records[restored["reference"]] = restored
                    elif version == "v1" and restored["transitions"]:
                        existing = self.records.get(restored["reference"])
                        latest = (
                            max((e["observed_utc"] for e in existing["transitions"]), default="")
                            if existing
                            else ""
                        )
                        if existing and restored["transitions"][-1]["observed_utc"] > latest:
                            existing["legacy_interval"] = "v1_only_interval_unknown_loss_split"
                            if existing["first_failure"] is None:
                                existing["first_failure"] = restored["first_failure"]
                            for event in restored["transitions"]:
                                if event["observed_utc"] > latest:
                                    existing["transitions"].append(event)
                            while (
                                len(existing["transitions"]) > 32
                                or len(encoded(existing)) > MAX_PROJECTION
                            ):
                                existing["transitions"].pop(0)
                            existing["complete"] = False
                except Exception:
                    self.invalid += 1
                    self.failures += 1
            self.publication[version] = {
                "file_observed_on_restore": utc(),
                "prior_acknowledged": self._acknowledged(document, version),
            }

    @staticmethod
    def _acknowledged(document, version):
        import re

        try:
            value = document["publication"][version]["last_success"]
            if (
                type(value) is not dict
                or set(value) != {"utc", "sha256", "generation", "durability"}
                or type(value["utc"]) is not str
                or len(value["utc"]) > 40
                or datetime.fromisoformat(value["utc"]).tzinfo is None
                or type(value["sha256"]) is not str
                or not re.fullmatch(r"[a-f0-9]{64}", value["sha256"])
                or type(value["generation"]) is not int
                or not 0 <= value["generation"] <= MAX_COUNTER
                or value["durability"] != "flush_close_replace"
            ):
                return None
            return dict(value)
        except (KeyError, TypeError, ValueError):
            return None

    def _validate(self, event):
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
        allowed |= V2_FIELDS
        if (
            type(event) is not dict
            or not {"reference", "stage", "state", "observed_utc"} <= event.keys()
            or not set(event) <= allowed
            or len(encoded(event)) > (MAX_V2_EVENT if event.get("schema") else MAX_EVENT)
        ):
            raise ValueError("Invalid diagnostic event")
        for key, value in event.items():
            if key in {
                "reference",
                "event_id",
                "child_reference",
                "parent_reference",
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
            elif key in {
                "pid",
                "thread_id",
                "elapsed_ms",
                "native_error",
                "failure_line",
                "sequence",
                "attached",
                "pruned",
                "superseded",
                "failed_count",
                "unattempted",
                "outcome_unconfirmed",
                "diagnostic_loss",
            }:
                if type(value) not in (int, float) or not 0 <= value <= 1e20:
                    raise ValueError("Invalid diagnostic number")
            elif key in {"reported_success", "import_reported_success", "value_boolean"}:
                if type(value) is not bool:
                    raise ValueError("Invalid diagnostic boolean")
            elif key == "sqlstate":
                import re

                if type(value) is not str or re.fullmatch(r"[0-9A-Z]{5}", value) is None:
                    raise ValueError("Invalid SQLSTATE")
            elif key == "schema":
                if value != "operation-boundary/2":
                    raise ValueError("Unknown event version")
            elif label(value) != value:
                raise ValueError("Invalid diagnostic label")
        if event.get("stage") not in STAGES or event.get("state") not in STATES:
            raise ValueError("Unknown diagnostic stage/state")
        for key, values in {
            "value_kind": {"unavailable", "boolean", "none", "dict", "tuple", "list"},
            "value_meaning": {"unclassified_return"},
            "feature_outcome": {"succeeded", "partial", "failed", "unknown", "not_checked"},
            "main_cache": {"succeeded", "failed", "unknown"},
            "last_kvk_cache": {"succeeded", "failed", "unknown"},
            "data_outcome": {"loaded_populated", "loaded_empty", "unavailable", "unknown"},
            "execution_outcome": {"succeeded", "failed", "unknown"},
            "persistence_outcome": {
                "saved",
                "failed_preserved",
                "not_applicable",
                "verified_on_disk",
                "unconfirmed",
                "unchanged",
                "unknown",
            },
            "restoration_outcome": {"complete", "partial", "cancelled", "unavailable", "unknown"},
            "origin": {"code_owned", "startup"},
            "actor": {"unavailable_not_collected", "system"},
            "verification_source": {
                "unavailable",
                "proc_config_import",
                "build_player_stats_cache",
                "warm_profile_cache",
                "warm_name_cache",
                "rehydrate_tracked_views",
            },
            "verification_reason": {
                "no_checker",
                "pending",
                "malformed_result",
                "checker_failed",
                "checker_cancelled",
                "not_reached",
                "projection_unavailable",
                "incomplete_evidence",
                "unsupported_stage",
                "verified",
            },
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
        if event.get("schema") == "operation-boundary/2":
            if not {"event_id", "sequence", "role", "origin", "actor"} <= event.keys():
                raise ValueError("Missing event identity")
            if (
                event["role"] == "child"
                and not {"child_reference", "parent_reference"} <= event.keys()
            ):
                raise ValueError("Missing child identity")
            if event["role"] not in {"parent", "child"}:
                raise ValueError("Invalid event role")

    def _accept(self, event):
        self._validate(event)
        reference = event["reference"]
        row = self.records.get(reference)
        if event["stage"] in {"upload_audit", "download_log"} and row is not None:
            if not is_upload_row(row):
                self.uploads._count("retention_omitted")
                return
            prior_events = list(row["transitions"]) + [row.get("first_failure") or {}]
            event = dict(
                event,
                diagnostic_loss=max(
                    event.get("diagnostic_loss", 0),
                    *(old.get("diagnostic_loss", 0) for old in prior_events),
                ),
            )
        if row is None:
            if not self._make_room(event["stage"] in {"upload_audit", "download_log"}, "capacity"):
                return
            row = self.records[reference] = dict(
                reference=reference,
                transitions=[],
                first_failure=None,
                result=None,
                omitted=0,
                complete=False,
            )
        self._dirty_rows.add(reference)
        is_v2 = event.get("schema") == "operation-boundary/2"
        if is_v2:
            # Repeated delivery of the same event is not another deadline/loss.
            if any(old.get("event_id") == event["event_id"] for old in row["transitions"]):
                return
            if any(
                old.get("event_id") == event["event_id"]
                for old in row.get("milestones", {}).values()
            ):
                return
            self._milestones(row, event)
        if "reported_success" in event or "attempt_recording" in event:
            row["result"] = event
        failure = (
            event["state"] in {"failed", "interrupted", "verification_unavailable"}
            and event.get("error_type") != "CancelledError"
        )
        if failure and row["first_failure"] is None:
            row["first_failure"] = event
        # Repeated ordinary observations coalesce, with explicit loss count.
        transitions = row["transitions"]
        if (
            transitions
            and (transitions[-1]["stage"], transitions[-1]["state"])
            == (
                event["stage"],
                event["state"],
            )
            and transitions[-1].get("child_reference") == event.get("child_reference")
        ):
            transitions.pop()
            row["omitted"] = min(MAX_COUNTER, row["omitted"] + 1)
            row["coalesced"] = min(MAX_COUNTER, row.get("coalesced", 0) + 1)
        transitions.append(event)
        while transitions and (
            len(transitions) > 32
            or len(encoded(row)) > MAX_PROJECTION - 512
            or (is_v2 and len(encoded(transitions)) > 6144)
        ):
            transitions.pop(0)
            row["omitted"] = min(MAX_COUNTER, row["omitted"] + 1)
            row["trimmed"] = min(MAX_COUNTER, row.get("trimmed", 0) + 1)
        row["complete"] = (
            event["stage"] == "operation"
            and event["state"] == "settled"
            and row["first_failure"] is None
        ) or (event["stage"] in {"upload_audit", "download_log"} and event["state"] == "settled")

    def _milestones(self, row, event):
        row["schema"] = "operation-projection/2"
        slots = row.setdefault("milestones", {})
        state, stage = event["state"], event["stage"]
        kind = None
        if stage == "operation" and state == "entered":
            kind = "scope_entry"
        elif stage == "worker_execution" and state == "entered":
            kind = "physical_entry"
        elif state.startswith("deadline_elapsed"):
            kind = "deadline"
        elif state.startswith("cancelled"):
            kind = "cancellation"
        elif (
            state in {"failed", "interrupted", "verification_unavailable"}
            and event.get("error_type") != "CancelledError"
        ):
            kind = "failure"
        elif state == "result_returned" and event.get("role") == "parent":
            kind = "parent_return"
        elif "feature_outcome" in event:
            kind = "verification"
        elif stage == "operation" and state == "settled":
            kind = "terminal"
        if "feature_outcome" in event:
            # A deadline can precede verification. Retain its eventual outcome,
            # including unavailable verification, after rolling detail is trimmed.
            slots["verification"] = event
        if kind:
            slots.setdefault(kind, event)
            if kind in {"deadline", "cancellation"}:
                row[kind + "_count"] = min(MAX_COUNTER, row.get(kind + "_count", 0) + 1)
                # The latest repeat needs only time/identity, not another 2 KiB event.
                row[kind + "_latest"] = {
                    key: event[key] for key in ("reference", "stage", "state", "observed_utc")
                }
        if stage == "operation" and state in {"interrupted", "cancelled_outcome_unconfirmed"}:
            slots.setdefault("terminal", event)
        identity = event.get("child_reference")
        if identity:
            children = row.setdefault("children", {})
            child = children.get(identity)
            if child is None:
                if len(children) >= 16:
                    if kind == "failure" and not any(c.get("failure") for c in children.values()):
                        del children[next(iter(children))]
                    else:
                        if stage == "worker_execution" and state == "entered":
                            self.children_omitted = min(MAX_COUNTER, self.children_omitted + 1)
                        return
                child = children[identity] = dict(
                    child_reference=identity, stage=stage, first_utc=event["observed_utc"]
                )
            child.update(latest_utc=event["observed_utc"], state=state)
            for key in ("value_kind", "value_boolean"):
                if key in event:
                    child[key] = event[key]
            if kind == "failure":
                child["failure"] = True

    def _legacy(self, document):
        def old(event):
            if event is None:
                return None
            result = {key: value for key, value in event.items() if key not in V2_FIELDS}
            if result["stage"] in NEW_STAGES:
                result["stage"] = "unavailable"
            return result

        rows = []
        for row in document["operations"]:
            converted = {key: row[key] for key in ("reference", "complete", "omitted")}
            converted.update(
                first_failure=old(row["first_failure"]),
                result=old(row["result"]),
                transitions=[old(event) for event in row["transitions"]],
            )
            rows.append(converted)
        return dict(
            schema="operation-observations/1",
            operations=rows,
            observed_utc=document["observed_utc"],
            status=document["status"],
            **{
                key: document[key]
                for key in ("dropped", "sink_failures", "evicted", "context_losses")
            },
        )

    def _write(self, version, filename, document):
        path = self.directory / filename
        temp = path.with_suffix(".tmp")
        previous = self.publication[version]
        attempt = dict(previous, last_attempt=utc(), target_generation=self.generation)
        self.publication = {**self.publication, version: attempt}
        try:
            if filename in self.blocked_files:
                raise ValueError("Original diagnostic evidence preserved")
            _reject_links(path)
            _reject_links(temp)
            # Encoding the entire retained file in one C call holds the GIL
            # across every row. Bound that work while retaining the exact bytes,
            # pre-write size/hash checks and independent atomic publications.
            parts, size, hasher = [], 0, hashlib.sha256()
            for index, part in enumerate(encoded_document_parts(document)):
                size += len(part)
                if size > MAX_FILE:
                    raise ValueError("Diagnostic file bound")
                parts.append(part)
                hasher.update(part)
                if index % 16 == 15:
                    time.sleep(0)
            digest = hasher.hexdigest()
            attempt = dict(attempt, target_sha256=digest)
            self.publication = {**self.publication, version: attempt}
            try:
                with temp.open("xb") as stream:
                    for part in parts:
                        stream.write(part)
                    stream.flush()
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
            attempt = dict(
                attempt,
                last_success={
                    "utc": utc(),
                    "sha256": digest,
                    "generation": self.generation,
                    "durability": "flush_close_replace",
                },
                status="published",
            )
        except Exception:
            self.failures += 1
            attempt = dict(
                attempt, status="failed", failures=min(MAX_COUNTER, previous.get("failures", 0) + 1)
            )
        self.publication = {**self.publication, version: attempt}

    def _publish(self):
        cutoff = datetime.now(UTC) - timedelta(days=30)
        for key, row in list(self.records.items()):
            if (
                row["complete"]
                and row["transitions"]
                and datetime.fromisoformat(row["transitions"][-1]["observed_utc"]) < cutoff
            ):
                self._evict(key, "retention", cutoff.isoformat())
        self.generation += 1
        document = dict(
            schema="operation-observations/2",
            operations=list(self.records.values()),
            retention_days=30,
            upload_observations=self.uploads.report(),
            **self._counter_totals(),
            counter_provenance=self._counter_provenance(),
            eviction_provenance=deepcopy(self.eviction_provenance),
            eviction_history_available=self.eviction_history_available,
            observed_utc=utc(),
            generation=self.generation,
            publication=deepcopy(self.publication),
            status="closed" if self.closed else "observing",
            restore_status=self.restore_status,
        )
        # Cache only frozen rows and their exact encoded sizes. Re-encoding all
        # retained history just to measure it stalls producers under the GIL.
        self._published_rows = {
            key: value for key, value in self._published_rows.items() if key in self.records
        }
        for key, row in self.records.items():
            if key in self._dirty_rows or key not in self._published_rows:
                frozen = self._snapshot_row(row)
                self._published_rows[key] = (frozen, len(encoded(frozen)))
        self._dirty_rows.clear()

        def document_size():
            header = dict(document, operations=[])
            return (
                len(encoded(header))
                + sum(size for _, size in self._published_rows.values())
                + max(0, len(self._published_rows) - 1)
            )

        # Encoded overhead belongs inside the file bound. Failure roots remain
        # protected; saturation is visible rather than evicting original failures.
        while document_size() > MAX_FILE - 128:
            completed = next((key for key, row in self.records.items() if is_upload_row(row)), None)
            if completed is None:
                completed = next(
                    (key for key, row in self.records.items() if row["complete"]), None
                )
            if completed is None:
                trimmable = next(
                    (row for row in self.records.values() if len(row["transitions"]) > 1), None
                )
                if trimmable is None:
                    document["status"] = "saturated"
                    break
                trimmable["transitions"].pop(0)
                trimmable["trimmed"] = min(MAX_COUNTER, trimmable.get("trimmed", 0) + 1)
                trimmable["omitted"] = min(MAX_COUNTER, trimmable["omitted"] + 1)
                frozen = self._snapshot_row(trimmable)
                self._published_rows[trimmable["reference"]] = (frozen, len(encoded(frozen)))
                continue
            self._evict(completed, "file_bound")
            del self._published_rows[completed]
            document["operations"] = list(self.records.values())
            document.update(
                **self._counter_totals(),
                counter_provenance=self._counter_provenance(),
                eviction_provenance=deepcopy(self.eviction_provenance),
            )
        document.update(
            **self._counter_totals(),
            counter_provenance=self._counter_provenance(),
            eviction_provenance=deepcopy(self.eviction_provenance),
        )
        document["latest_event_utc"] = max(
            (
                event["observed_utc"]
                for row in self.records.values()
                for event in row["transitions"]
            ),
            default=None,
        )
        document["upload_observations"] = self.uploads.report()
        # The writer owns validated primitive events. Copy the small mutable
        # containers directly instead of recursively visiting every primitive
        # through deepcopy while business threads compete for the GIL. Events
        # are copied too, so neither a later writer update nor a report reader
        # can mutate an already published generation.
        self.snapshot = dict(
            document,
            operations=sorted((row for row, _ in self._published_rows.values()), key=is_upload_row),
        )
        if self.directory is not None:
            self._write("v2", "observations-v2.json", document)
            self._write("v1", "observations.json", self._legacy(document))

    @staticmethod
    def _snapshot_row(row):
        result = dict(row)
        result["transitions"] = [dict(event) for event in row["transitions"]]
        for name in ("first_failure", "result", "deadline_latest", "cancellation_latest"):
            if row.get(name) is not None:
                result[name] = dict(row[name])
        for name in ("milestones", "children"):
            if name in row:
                result[name] = {key: dict(value) for key, value in row[name].items()}
        return result

    def _run(self):
        try:
            self._load()
        except Exception:
            self.failures += 1
        while True:
            self.wake.wait()
            # Rewriting the bounded projection on every producer wake causes
            # avoidable GIL/disk contention as history grows. Batch on the sink
            # thread only; close interrupts this delay and flushes accepted work.
            self.closing.wait(PUBLISH_INTERVAL)
            with self.lock:
                events = list(self.queue)
                self.queue.clear()
                self.wake.clear()
                closed = self.closed
            for index, event in enumerate(events):
                try:
                    self._accept(event)
                except Exception:
                    self.failures += 1
                if index % 16 == 15:
                    # Yield the sink's batch to ready business/event-loop threads.
                    # No producer waits here and close still drains every event.
                    time.sleep(0)
            for event in self.uploads.take(64 if closed else 16):
                try:
                    self._accept(event)
                except Exception:
                    self.uploads.partial = True
            if self.uploads.slots:
                self.wake.set()
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
        try:
            _sink.offer(event)
        except Exception:
            optional(note_emission_failure, event.get("state") if type(event) is dict else None)


def note_emission_failure(state):
    if _sink is not None:
        _sink.emission_failures = min(MAX_COUNTER, _sink.emission_failures + 1)
        _sink.dropped = min(MAX_COUNTER, _sink.dropped + 1)
        if type(state) is str and state in _critical:
            _sink.critical_dropped = min(MAX_COUNTER, _sink.critical_dropped + 1)


def note_unknown_stage():
    if _sink is not None:
        _sink.unknown_stages = min(MAX_COUNTER, _sink.unknown_stages + 1)


def note_context_loss():
    if _sink is not None:
        _sink.context_losses = min(MAX_COUNTER, _sink.context_losses + 1)


def shutdown():
    if _sink is not None:
        _sink.close()


def report():
    result = optional(_sink.report) if _sink is not None else None
    return result or {"operations": [], "status": "unavailable", "authority": "diagnostic_only"}


def full_snapshot():
    return (
        _sink.full_snapshot() if _sink is not None else {"operations": [], "status": "unavailable"}
    )


def offer_upload_observation(reference, state, loss=0, *, kind="sql"):
    if _sink is not None:
        try:
            return _sink.uploads.offer(reference, state, loss, kind)
        except Exception:
            _sink.uploads.partial = True
    return False


def upload_worker_summary(kind, state, unavailable=0, error_type=None, dropped=0, failures=0):
    if _sink is not None:
        try:
            _sink.uploads.summary(kind, state, unavailable, error_type, dropped, failures)
        except Exception:
            _sink.uploads.partial = True
