"""Passive evidence components and bounded, actor-bound disposable downloads."""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
import hashlib
import io
import json
import math
import os
import re
import secrets
import sys
import threading
import time
import zipfile

from core.operator_diagnostic_payloads import redact_diagnostic_text
from kvk.dal.new_source_import_dal import SourceConflict

MAX_ATTACHMENT = 8 * 1024 * 1024
MAX_SESSION = 17 * 1024 * 1024
_request = ContextVar("evidence_report_request", default=None)
_admission = threading.Lock()
_active = None
_stopped = False
_sessions = {}
_plain_guid = re.compile(r"[0-9a-fA-F-]{36}\Z")


def utc():
    return datetime.now(UTC).isoformat()


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(
        "utf-8"
    )


def sha(data):
    return hashlib.sha256(data).hexdigest()


def budget(value):
    if type(value) is not int or not 65536 <= value <= MAX_ATTACHMENT:
        raise SourceConflict("A supported attachment budget is required.")
    return value


class ReportBudgetExceeded(SourceConflict):
    """Only collection is bounded; entered work retains physical ownership."""


class ReportLease:
    def __init__(self):
        self.cancelled = threading.Event()
        self.deadline = time.monotonic() + 30
        self.redactions = {}

    def check_active(self):
        if self.cancelled.is_set() or _stopped:
            raise SourceConflict("Report collection stopped; download again when available.")

    def check(self):
        self.check_active()
        if time.monotonic() >= self.deadline:
            raise ReportBudgetExceeded(
                "Report collection reached its time bound; use report parts."
            )


@contextmanager
def report_request():
    """One physical build/delivery; ContextVar propagation does not create leases."""
    global _active
    inherited = _request.get()
    if inherited is not None:
        if inherited is not _active:
            raise SourceConflict("Report request has expired.")
        yield inherited
        return
    if _stopped or not _admission.acquire(blocking=False):
        raise SourceConflict(
            "A report is already being collected or delivered. Try again after it finishes."
        )
    token = None
    try:
        if _stopped:
            raise SourceConflict("Report admission is closed.")
        lease = ReportLease()
        _active = lease
        token = _request.set(lease)
        yield lease
    finally:
        if token is not None:
            _request.reset(token)
        if _active is not None:
            _active.redactions.clear()
        _active = None
        _admission.release()


def redact_report_text(value):
    """Memoize bounded redacted output by digest, within this physical request."""
    # UUID-shaped text cannot contain assignment, URL-query or bearer syntax.
    # It is unchanged by the canonical redactor and has high report cardinality.
    if type(value) is str and _plain_guid.fullmatch(value):
        return value
    lease = _request.get()
    cache = lease.redactions if lease is _active and lease is not None else None
    key = None
    if cache is not None and type(value) is str and len(value) <= 256:
        raw = value.encode("utf-8")
        if len(raw) <= 512:
            key = hashlib.sha256(raw).digest()
    if key is not None and key in cache:
        return cache[key]
    redacted = redact_diagnostic_text(value)
    # Store only a fixed digest and the existing redactor's bounded output.
    # Credential-bearing originals never enter the memo; no cross-request state.
    if key is not None and len(cache) < 128 and len(redacted.encode("utf-8")) <= 512:
        cache[key] = redacted
    return redacted


def stop_admission():
    global _stopped
    _stopped = True
    if _active is not None:
        _active.cancelled.set()


def safe(value, depth=0, *, max_depth=4, remaining=None):
    """Bound primitives without invoking user object repr/properties."""
    if remaining is None:
        remaining = [32768]
    remaining[0] -= 1
    if depth > max_depth or remaining[0] < 0:
        raise ValueError("Diagnostic primitive bound")
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        return value if -(2**63) < value < 2**63 else "unavailable_number_bound"
    if type(value) is float:
        return value if math.isfinite(value) and abs(value) <= 1e20 else "unavailable_number_bound"
    if type(value) is str:
        if len(value.encode("utf-8")) > 8192:
            raise ValueError("Diagnostic primitive bound")
        return redact_diagnostic_text(value)
    if type(value) is dict:
        if len(value) > 256 or any(type(key) is not str or len(key) > 80 for key in value):
            raise ValueError("Diagnostic primitive bound")
        return {
            key: safe(item, depth + 1, max_depth=max_depth, remaining=remaining)
            for key, item in value.items()
        }
    if type(value) in (list, tuple):
        if len(value) > 256:
            raise ValueError("Diagnostic primitive bound")
        return [safe(item, depth + 1, max_depth=max_depth, remaining=remaining) for item in value]
    raise ValueError("Diagnostic primitive bound")


def guarded(function, limit=131072, *, max_depth=4):
    started = utc()
    try:
        source = function()
    except Exception:
        return {"status": "unavailable"}, dict(
            status="unavailable",
            reason="source_unavailable",
            captured_from_utc=started,
            captured_through_utc=utc(),
        )
    try:
        result = safe(source, max_depth=max_depth)
        data = encode(result)
        if len(data) > limit:
            raise ValueError("Component bound")
        return result, dict(
            status="available", captured_from_utc=started, captured_through_utc=utc()
        )
    except Exception:
        return {"status": "unavailable"}, dict(
            status="unavailable",
            reason="source_invalid_or_bound",
            captured_from_utc=started,
            captured_through_utc=utc(),
        )


def drain_reports():
    """Shutdown runs this in owned offload after closing admission."""
    with _admission:
        _sessions.clear()


def loaded_call(module, function):
    source = sys.modules.get(module)
    if source is None:
        raise ValueError("Source not loaded")
    result = (
        source.refresh_service.report()
        if module == "event_cache" and function == "report"
        else getattr(source, function)()
    )
    if module == "services.operation_diagnostics" and function == "report":
        # Operation rows have their own validated component. Do not feed their
        # nested milestones through the bounded health primitive projection.
        return {key: value for key, value in result.items() if key != "operations"}
    return result


def monitor_snapshot(limit=12288):
    """Keep monitor state even when one retained history field exceeds its budget.

    Monitor failure frames are deeper than generic cache primitives. Their
    independent depth/node/byte bounds do not widen other diagnostic schemas.
    """
    started = utc()
    try:
        source = loaded_call("services.recovery_health", "observation")
        if type(source) is not dict or len(source) > 64:
            raise ValueError("Invalid monitor snapshot")
    except Exception:
        return {"status": "unavailable"}, dict(
            status="unavailable",
            reason="source_unavailable",
            captured_from_utc=started,
            captured_through_utc=utc(),
        )
    result, omitted, trimmed = {}, [], []
    names = {
        "healthy",
        "status",
        "last_success_utc",
        "check_failure",
        "notification_failure",
        "cycle",
        "checks",
        "observer_state",
        "check_state",
        "completed_check_age_seconds",
        "last_completed_cycle",
        "last_failed_cycle",
        "history",
        "no_progress_seconds",
        "freshness_seconds",
        "stall_seconds",
        "cycle_limit_seconds",
    }
    # Current state and original failure precede bulky duplicated cycle histories.
    history = {"cycle", "checks", "last_completed_cycle", "last_failed_cycle", "history"}
    for key in sorted(names.intersection(source), key=lambda key: (key in history, key)):
        try:
            item = safe({key: source[key]}, max_depth=8)
            if len(encode(result | item)) > limit - 2048:
                if (
                    key not in {"cycle", "last_completed_cycle", "last_failed_cycle"}
                    or type(source[key]) is not dict
                ):
                    raise ValueError("Monitor field bound")
                bulky = {"checks", "stages", "original_history_failure"}.intersection(source[key])
                compact = {k: v for k, v in source[key].items() if k not in bulky}
                compact["report_omitted_fields"] = sorted(bulky)
                item = safe({key: compact}, max_depth=8)
                if len(encode(result | item)) > limit - 2048:
                    raise ValueError("Monitor field bound")
                trimmed.append(key)
            result.update(item)
        except Exception:
            omitted.append(key)
    coverage = dict(
        status="partial" if omitted or trimmed or source.keys() - names else "available",
        reason=(
            "monitor_fields_invalid_or_bound"
            if omitted or trimmed or source.keys() - names
            else None
        ),
        omitted_fields=omitted,
        trimmed_fields=trimmed,
        unknown_fields=len(source.keys() - names),
        captured_from_utc=started,
        captured_through_utc=utc(),
    )
    result["coverage"] = coverage
    return result, coverage


def collect_components(*, lease=None):
    from core import operation_evidence
    from core.startup_diagnostics import report as startup_report
    from services import operation_diagnostics

    started = utc()
    components, descriptors = {}, {}

    def checked(function):
        if lease is not None:
            lease.check_active()
        return function()

    try:
        snapshot = checked(operation_diagnostics.full_snapshot)
        if type(snapshot) is not dict or type(snapshot.get("operations")) is not list:
            raise ValueError("Invalid operations source")
    except Exception:
        snapshot = {"operations": [], "status": "unavailable"}
    rows = snapshot.get("operations", [])
    valid, rejected = [], 0
    validator = operation_diagnostics.DiagnosticSink()
    for row in rows[:512]:
        try:
            projected = validator._restore_row(row)
            data = encode(projected) + b"\n"
            if len(data) > 32768:
                raise ValueError("Operation bound")
            valid.append(data)
        except Exception:
            rejected += 1
    operations = b"".join(valid)
    if len(operations) <= 16 * 1024 * 1024:
        components["operations.jsonl"] = operations
        descriptors["operations.jsonl"] = dict(
            status=(
                "unavailable"
                if snapshot.get("status") == "unavailable"
                else "partial" if rejected else "available"
            ),
            included=len(valid),
            available=len(rows) if snapshot.get("status") != "unavailable" else "unknown",
            omitted=(
                max(0, len(rows) - len(valid))
                if snapshot.get("status") != "unavailable"
                else "unknown"
            ),
            rejected=rejected,
            generation=snapshot.get("generation"),
            source_observed_utc=snapshot.get("observed_utc", "unknown"),
            publication_watermark=guarded(
                lambda: snapshot.get("publication", "unknown"), limit=4096
            )[0],
            retention_days=snapshot.get("retention_days", "unknown"),
            captured_from_utc=started,
            captured_through_utc=utc(),
        )
    else:
        descriptors["operations.jsonl"] = dict(status="unavailable", reason="component_bound")

    def startup_projection():
        rows = startup_report()
        if type(rows) is not list or len(rows) > 64:
            raise ValueError("Startup inventory bound")
        allowed = {
            "step",
            "state",
            "observed_utc",
            "reference",
            "observer",
            "physical",
            "returned",
            "feature",
            "parent_return",
            "result",
            "worker_result",
            "verification_state",
        }
        return [{key: value for key, value in row.items() if key in allowed} for row in rows]

    startup, status = guarded(lambda: checked(startup_projection))
    components["startup.json"] = encode(startup)
    descriptors["startup.json"] = status
    descriptors["startup.json"].update(
        included=len(startup) if type(startup) is list else 0,
        available=len(startup) if type(startup) is list else "unknown",
        omitted=0 if type(startup) is list else "unknown",
    )
    health = {}
    for name, module, function in (
        ("monitor", "services.recovery_health", "observation"),
        ("sink", "services.operation_diagnostics", "report"),
        ("admission", "services.cache_admission_diagnostics", "report"),
        ("stats_cache", "services.player_stats_cache_service", "report"),
        ("profile_cache", "profile_cache", "get_cache_stats"),
        ("name_cache", "target_utils", "name_outcome_report"),
        ("event_startup", "core.scheduler_lifecycle", "event_startup_report"),
        ("event_cache", "event_cache", "report"),
        ("event_delivery", "services.event_delivery_service", "report"),
        ("event_dm_startup", "event_scheduler", "dm_startup_report"),
    ):
        if lease is not None:
            lease.check_active()
        if name == "monitor":
            value, state = monitor_snapshot()
        else:
            value, state = guarded(
                lambda m=module, f=function: checked(lambda: loaded_call(m, f)), limit=12288
            )
        health[name] = dict(coverage=state, observation=value)
    components["diagnostic-health.json"] = encode(health)
    descriptors["diagnostic-health.json"] = dict(
        status=(
            "partial"
            if any(v["coverage"]["status"] != "available" for v in health.values())
            else "available"
        ),
        captured_from_utc=started,
        captured_through_utc=utc(),
        included=len(health),
        available=len(health),
        omitted=0,
    )
    identity = dict(
        pid=os.getpid(),
        process_incarnation=operation_evidence._incarnation,
        native_process_creation="unavailable_not_collected",
        bot_commit="unavailable_not_collected",
        build_descriptor="p012a_passive_evidence_bundle_v1",
    )
    return components, descriptors, identity


def descriptor(data, **facts):
    return dict(facts, bytes=len(data), sha256=sha(data))


def manifest(descriptors, identity, **extra):
    exported = utc()
    schemas = {
        "operations.jsonl": "operation-observations/2",
        "startup.json": "startup-outcome-projection/1",
        "diagnostic-health.json": "passive-diagnostic-health/1",
        "incidents.jsonl": "k98-recovery-report-v1",
        "summary.json": "k98-recovery-complete-report-v1",
    }
    descriptors = {
        name: dict(
            {
                "schema": schemas[name],
                "source_kind": (
                    "saved_incident_projection"
                    if name in {"incidents.jsonl", "summary.json"}
                    else "passive_memory_projection"
                ),
                "reason": (
                    None if facts.get("status") == "available" else "source_coverage_incomplete"
                ),
                "source_observed_utc": "unknown",
                "publication_watermark": "unknown",
                "retention_cutoff_utc": "unknown",
                "included": "unknown",
                "available": "unknown",
                "omitted": "unknown",
                "exported_utc": exported,
            },
            **facts,
        )
        for name, facts in descriptors.items()
    }
    return encode(
        dict(
            schema="k98-evidence-bundle/1",
            generated_utc=exported,
            authority="diagnostic_only",
            atomic_snapshot=False,
            identity=identity,
            components=descriptors,
            **extra,
        )
    )


def binding(service, actor):
    return (actor.user_id, actor.guild_id, actor.channel_id, service.store.scope)


def retain(service, actor, components, identity, descriptors=None):
    if not components:
        return None
    if sum(len(data) for data in components.values()) > MAX_SESSION:
        raise SourceConflict("Diagnostic continuation exceeds its retention bound.")
    now = time.monotonic()
    for key, session in list(_sessions.items()):
        if session["expires"] <= now:
            del _sessions[key]
    while len(_sessions) >= 2:
        del _sessions[next(iter(_sessions))]
    token = secrets.token_urlsafe(32)
    _sessions[token] = dict(
        binding=binding(service, actor),
        components=components,
        identity=identity,
        expires=now + 600,
        generation=secrets.token_hex(16),
        part=1,
        previous_sha256=None,
        offsets={name: 0 for name in components},
        component_hashes={name: sha(data) for name, data in components.items()},
        descriptors={name: dict((descriptors or {}).get(name, {})) for name in components},
    )
    return token


def initial_chain(token):
    return (
        {"generation": _sessions[token]["generation"], "part": 0, "previous_sha256": None}
        if token
        else {}
    )


def anchor_initial(token, content):
    if token:
        _sessions[token]["previous_sha256"] = sha(content)


def continuation(service, actor, token, max_bytes):
    service.report_authorize(actor)
    budget(max_bytes)
    with report_request():
        session = _sessions.get(token) if type(token) is str else None
        if (
            session is None
            or session["expires"] <= time.monotonic()
            or session["binding"] != binding(service, actor)
        ):
            raise SourceConflict(
                "This diagnostic continuation expired or belongs to another scope. Collect a new report."
            )
        # Freeze rows; never split an operation. Other JSON members use explicit
        # byte fragments so even an incompressible 128 KiB source fits 64 KiB.
        name, remaining = next(iter(session["components"].items()))
        allowance = max_bytes - 32768
        if name == "operations.jsonl":
            used = 0
            for line in io.BytesIO(remaining):
                if used + len(line) > allowance:
                    break
                used += len(line)
            if not used and remaining:
                raise SourceConflict("One diagnostic row exceeds the attachment budget.")
        else:
            used = min(len(remaining), allowance)
        chunk = remaining[:used]
        original = session["descriptors"][name]
        included = (
            len(chunk.splitlines()) if name == "operations.jsonl" else "unknown_byte_fragment"
        )
        available = original.get("available", "unknown")
        desc = {
            name: descriptor(
                chunk,
                **{
                    key: value
                    for key, value in session["descriptors"][name].items()
                    if key
                    not in {
                        "status",
                        "bytes",
                        "sha256",
                        "reason",
                        "included",
                        "available",
                        "omitted",
                    }
                },
                status="partial",
                reason="diagnostic_continuation",
                count_scope="this_part",
                included=included,
                available=available,
                omitted=(
                    available - included
                    if type(available) is int and type(included) is int
                    else "unknown"
                ),
                component_coverage={
                    key: original.get(key, "unknown")
                    for key in ("included", "available", "omitted")
                },
                component_sha256=session["component_hashes"][name],
                offset=session["offsets"][name],
                encoding="utf8_byte_fragment" if name != "operations.jsonl" else "jsonl_whole_rows",
            )
        }
        meta = manifest(
            desc,
            session["identity"],
            generation=session["generation"],
            part=session["part"],
            previous_sha256=session["previous_sha256"],
        )
        with io.BytesIO() as output:
            with zipfile.ZipFile(
                output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
            ) as archive:
                archive.writestr(name, chunk)
                archive.writestr("manifest.json", meta)
            content = output.getvalue()
        if len(content) > max_bytes:
            raise SourceConflict("Diagnostic part exceeds the attachment budget.")
        # Single use token; the returned successor is the sole next capability.
        del _sessions[token]
        session["offsets"][name] += used
        if used == len(remaining):
            del session["components"][name]
        else:
            session["components"][name] = remaining[used:]
        session["previous_sha256"] = sha(content)
        session["part"] += 1
        successor = None
        if session["components"]:
            successor = secrets.token_urlsafe(32)
            _sessions[successor] = session
        return dict(
            content=content,
            filename="K98-diagnostic-continuation.zip",
            diagnostic_token=successor,
            sha256=sha(content),
            count=0,
            complete=False,
        )
