"""Durable, passive ProcConfig attempts recorded before SQL admission.

These receipts describe one invocation only. They never authorize replay, release
ownership, or certify provider delivery. A later attempt cannot erase a failure.
"""

from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
import hashlib
import heapq
import json
import logging
from pathlib import Path
import re
from uuid import UUID, uuid4

from file_utils import atomic_write_json
from kvk.dal.new_source_import_dal import SourceConflict, digest

logger = logging.getLogger(__name__)
_attempt = ContextVar("proc_config_attempt", default=None)
PHASES = {"before_inputs", "reading_inputs", "writes_may_start"}
OUTCOMES = {"unconfirmed", "reported_success", "failed_before_inputs", "failed_after_inputs"}


def journal_root(data_dir, runtime):
    scope = [runtime.account, runtime.store.storage_owner] if runtime else ["legacy_local"]
    key = hashlib.sha256(json.dumps(scope, separators=(",", ":")).encode()).hexdigest()
    return Path(data_dir) / "proc_config_attempts" / key


class AttemptJournal:
    def __init__(self, root):
        self.root = Path(root)

    def path(self, attempt_id):
        return self.root / (str(UUID(attempt_id)) + ".json")

    def save(self, value):
        atomic_write_json(self.path(value["attempt_id"]), value)

    def read(self, attempt_id):
        path = self.path(attempt_id)
        if path.stat().st_size > 16384:
            raise SourceConflict("Configuration attempt receipt exceeds its bound.")
        value = json.loads(path.read_text(encoding="utf-8"))
        allowed = {
            "schema",
            "attempt_id",
            "operation_id",
            "started_utc",
            "finished_utc",
            "phase",
            "outcome",
            "admission_failure",
        }
        if not isinstance(value, dict) or set(value) - allowed:
            raise SourceConflict("Configuration attempt receipt contains unsupported fields.")
        if (
            value.get("schema") != "configuration-attempt/1"
            or value.get("attempt_id") != str(UUID(attempt_id))
            or value.get("phase") not in PHASES
            or value.get("outcome") not in OUTCOMES
        ):
            raise SourceConflict("Configuration attempt receipt is unavailable or invalid.")
        try:
            if str(UUID(value["operation_id"])) != value["operation_id"]:
                raise ValueError()
            for key in ("started_utc", "finished_utc"):
                if key in value and datetime.fromisoformat(value[key]).utcoffset() is None:
                    raise ValueError()
            if "started_utc" not in value or (
                value["outcome"] != "unconfirmed" and "finished_utc" not in value
            ):
                raise ValueError()
            failure = value.get("admission_failure")
            if failure is not None:
                if set(failure) - {"phase_timings_ms"} != {
                    "error_type",
                    "sqlstate",
                    "native_errors",
                    "applock_result",
                    "sql_session_id",
                    "xact_state",
                    "transaction_count",
                    "resource_sha256",
                    "transaction_released",
                }:
                    raise ValueError()
                if (
                    failure["error_type"] != "CoordinationLockRefused"
                    or failure["sqlstate"] != "42000"
                    or failure["native_errors"] != [51400]
                    or failure["applock_result"] not in {-1, -2, -3, -999}
                    or not re.fullmatch(r"[a-f0-9]{64}", failure["resource_sha256"])
                    or type(failure["transaction_released"]) is not bool
                    or any(
                        type(failure[k]) is not int
                        for k in ("sql_session_id", "xact_state", "transaction_count")
                    )
                ):
                    raise ValueError()
                timings = failure.get("phase_timings_ms")
                if timings is not None and (
                    not isinstance(timings, dict)
                    or set(timings)
                    - {"connect", "cursor", "transaction_body", "commit", "rollback", "close"}
                    or any(type(v) is not int or v < 0 for v in timings.values())
                ):
                    raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise SourceConflict("Configuration attempt receipt fields are invalid.") from exc
        return value

    def pending(self, after=None):
        if not self.root.exists():
            return []
        # Bound payload reads to one page; rotate by filename without loading
        # every retained receipt. No history is expired or deleted.
        cursor = str(UUID(after)) if after else ""
        names = (p.stem for p in self.root.glob("*.json"))
        return heapq.nsmallest(100, names, key=lambda name: (name <= cursor, name))


def attempt_phase(phase):
    current = _attempt.get()
    if current is None:
        return
    if phase not in PHASES:
        raise ValueError("Known configuration phase required.")
    journal, value = current
    value["phase"] = phase
    journal.save(value)  # Refuse to start the next phase without its receipt.


def record_configuration_attempt(*, data_dir, report_sink):
    def decorate(function):
        @wraps(function)
        def run(dry_run=False, **kwargs):
            if dry_run:
                return function(dry_run, **kwargs)
            from services.legacy_export_snapshot_service import _writer_runtime
            from services.producer_recovery_intent import current_intent

            journal = AttemptJournal(journal_root(data_dir(), _writer_runtime()))
            value = dict(
                schema="configuration-attempt/1",
                attempt_id=str(uuid4()),
                operation_id=str(UUID(current_intent()["operation"])),
                started_utc=datetime.now(UTC).isoformat(),
                phase="before_inputs",
                outcome="unconfirmed",
            )
            report = dict(success=False, errors=[])
            try:
                journal.save(value)
            except Exception:
                logger.error(
                    "proc_config_attempt_unrecorded stage=begin attempt=%s", value["attempt_id"]
                )
                report.update(attempt_id=value["attempt_id"], attempt_recording="unrecorded")
                report["errors"] = [
                    "Configuration import did not start: its attempt could not be recorded."
                ]
                report_sink(report)
                return False, report
            token = _attempt.set((journal, value))
            try:
                ok, report = function(dry_run, **kwargs)
                value["outcome"] = (
                    "reported_success"
                    if ok
                    else (
                        "failed_before_inputs"
                        if value["phase"] == "before_inputs"
                        else "failed_after_inputs"
                    )
                )
                if "admission_failure" in report:
                    value["admission_failure"] = report["admission_failure"]
                value["finished_utc"] = datetime.now(UTC).isoformat()
                try:
                    journal.save(value)
                    report["attempt_recording"] = "recorded"
                except Exception:
                    logger.error(
                        "proc_config_attempt_unrecorded stage=finish attempt=%s",
                        value["attempt_id"],
                    )
                    report["attempt_recording"] = "unrecorded"
                    report["import_reported_success"] = bool(ok)
                    report.setdefault("errors", []).append(
                        "Configuration attempt outcome could not be recorded; verify the retained operation before retrying."
                    )
                    ok = False
                report.update(
                    success=bool(ok),
                    attempt_id=value["attempt_id"],
                    attempt_outcome=value["outcome"],
                )
                report_sink(report)
                return ok, report
            finally:
                # Exceptions/cancellation retain the last durable unconfirmed
                # phase. They cannot create a successful terminal receipt.
                _attempt.reset(token)

        return run

    return decorate


class ConfigurationAttemptRecovery:
    kind = "configuration_attempt"

    def __init__(self, journal):
        self.journal = journal

    def pending_recovery(self, *, after=None):
        return self.journal.pending(after)

    def inspect(self, source_id):
        value = self.journal.read(source_id)
        outcome = value["outcome"]
        explanation = {
            "unconfirmed": "This configuration attempt has no recorded final outcome. It may still be running or its recording may have failed. Verify the original operation before any retry.",
            "reported_success": "This configuration attempt reported success and its final receipt was saved. Provider delivery and other attempts retain their own verification requirements.",
            "failed_before_inputs": "The configuration import failed before reading inputs or starting writes. This attempt retained the previous configuration. A healthy monitor or later attempt does not clear this failure.",
            "failed_after_inputs": "The configuration import reported failure after inputs started. Verify its retained producer and SQL outcome; do not replay the whole import.",
        }[outcome]
        evidence = dict(
            title="ProcConfig import attempt",
            outcome=outcome,
            explanation=explanation,
            actions={},
            failure_context=value,
            required_evidence=(
                []
                if outcome == "reported_success"
                else [
                    "Review the attempt and original operation identifiers with the import report and retained configuration recovery receipts. Do not release ownership or infer success from incident counts."
                ]
            ),
        )
        return evidence, digest(value).hex(), outcome == "reported_success"


class ProcConfigImportFailed(RuntimeError):
    pass


async def verify_startup_import(result):
    if result is not True:
        raise ProcConfigImportFailed(
            "ProcConfig startup import did not report success; inspect its attempt receipt."
        )
    return {"import_reported_success": True}
