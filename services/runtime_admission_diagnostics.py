"""One startup admission observation in the existing log, never recovery authority."""

from contextvars import ContextVar
from datetime import UTC, datetime
import hashlib
import json
import logging
import os
from pathlib import Path

from core.operation_evidence import optional

logger = logging.getLogger(__name__)
MARKER = "K98_STARTUP_ADMISSION_RESULT "
_attempt = ContextVar("startup_admission_attempt", default=None)
STAGES = frozenset(
    {
        "runtime_install",
        "manifest",
        "source_inventory",
        "fixed_sql_contract",
        "legacy_sql_contract",
        "application_sql_contract",
        "recovery_isolation",
        "authority_ready",
        "runtime_construct",
        "replacement_registration",
        "runtime_publish",
    }
)


def stage(name):
    """Code-owned labels only; observations cannot change admission outcomes."""
    attempt = _attempt.get()
    if attempt is not None and name in STAGES:
        attempt["stage"] = name


def _identity():
    # This is correlation only. The installer independently validates custody,
    # bytes, source and identity; the updater compares the exact journal hash.
    with Path(os.environ["K98_EXPORT_RUNTIME_MANIFEST"]).open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if not raw or len(raw) > 1024 * 1024:
        raise ValueError("Bounded runtime manifest required")
    binding = json.loads(raw)["authority"]["process_bindings"]["bot"]
    return dict(
        pid=os.getpid(),
        created_filetime=binding["created_filetime"],
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
    )


def _emit(attempt, outcome, error=None):
    from services.export_failure_diagnostics import failure_record
    from services.recovery_health import failure_detail

    record = dict(
        version=1,
        **attempt,
        outcome=outcome,
        observed_utc=datetime.now(UTC).isoformat(),
        reason="admission_" + outcome,
    )
    if error is not None:
        record["diagnostic"] = failure_detail(error)
        record["diagnostic"]["chain_frames"] = failure_record(error)["code_locations"]
        # Compare only known code-owned prose; never render an arbitrary message.
        reasons = {
            "Application schema observation is busy or refused; no retry performed.": "schema_observation_refused",
            "Installed application schema/dependencies differ from reviewed source shapes.": "application_schema_mismatch",
            "Application schema observation retained for cleanup review.": "schema_cleanup_unconfirmed",
        }
        if type(error).__name__ in {
            "SourceConflict",
            "SchemaObservationRefused",
            "SqlCleanupUnknown",
        }:
            record["reason"] = reasons.get(str(error), "admission_failed")
    logger.info("%s%s", MARKER, json.dumps(record, sort_keys=True, separators=(",", ":")))


def install_startup_runtime():
    """Observe the initial real worker through settlement, including cleanup.

    Explicit recovery activation retains its existing separate semantics and
    cannot overwrite this initial failed attempt with a later success.
    """
    from services.export_runtime_composition import install_configured_runtime

    attempt = dict(optional(_identity) or {}, stage="runtime_install")
    token = _attempt.set(attempt)
    try:
        result = install_configured_runtime()
    except BaseException as error:
        optional(_emit, attempt, "failed", error)
        raise
    else:
        optional(_emit, attempt, "installed" if result is not None else "disabled")
        return result
    finally:
        _attempt.reset(token)
