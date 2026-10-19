"""Bounded worker diagnostics without exception prose, SQL text or payloads."""

from datetime import UTC, datetime
import re
from uuid import uuid4

_CODE_FILES = {
    "export_coordination_service.py",
    "export_coordination_dal.py",
    "export_provider_adapter.py",
    "export_runtime_composition.py",
    "export_execution_authority.py",
    "export_request_budget.py",
    "export_snapshot_store.py",
    "legacy_export_snapshot_service.py",
}


def failure_record(error, *, job_id=None, stage="delivery"):
    """Retain code locations and driver codes; never include exception messages."""
    types, frames, states, numbers = [], [], set(), set()
    current, seen = error, set()
    for _ in range(4):
        if not isinstance(current, BaseException) or id(current) in seen:
            break
        seen.add(id(current))
        name = type(current).__name__
        types.append(name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name) else "Exception")
        args = current.args
        if (
            type(current).__module__ == "pyodbc"
            and args
            and isinstance(args[0], str)
            and re.fullmatch(r"[A-Z0-9]{5}", args[0])
        ):
            states.add(args[0])
            for arg in args[1:5]:
                if isinstance(arg, str):
                    numbers.update(int(n) for n in re.findall(r"\((\d{3,6})\)", arg[:4096])[:8])
        tb = current.__traceback__
        for _ in range(64):
            if tb is None:
                break
            code = tb.tb_frame.f_code
            filename = code.co_filename.replace("\\", "/").rsplit("/", 1)[-1]
            if filename in _CODE_FILES and re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]{0,63}", code.co_name
            ):
                frames.append(dict(file=filename, function=code.co_name, line=tb.tb_lineno))
            tb = tb.tb_next
        current = current.__cause__ or current.__context__
    return dict(
        diagnostic_id=str(uuid4()),
        observed_utc=datetime.now(UTC).isoformat(),
        job_id=(
            job_id.lower()
            if isinstance(job_id, str)
            and re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", job_id)
            else None
        ),
        stage=(
            stage
            if stage in {"authorization", "snapshot", "delivery", "terminal_record"}
            else "unknown"
        ),
        exception_types=types,
        sqlstates=sorted(states)[:4],
        sql_numbers=sorted(numbers)[:8],
        code_locations=frames[-16:],
    )


def safe_failure_record(value):
    """Strictly project persisted diagnostics; no arbitrary prose or extra keys."""
    if not isinstance(value, dict):
        return None
    try:
        from uuid import UUID

        job = str(UUID(value["job_id"]))
        diagnostic = str(UUID(value["diagnostic_id"]))
        observed = datetime.fromisoformat(value["observed_utc"])
        if observed.tzinfo is None:
            return None
        stage = value["stage"]
        if stage not in {"authorization", "snapshot", "delivery", "terminal_record", "unknown"}:
            return None
        types = value["exception_types"]
        states, numbers, locations = (
            value["sqlstates"],
            value["sql_numbers"],
            value["code_locations"],
        )
        if not all(isinstance(v, list) for v in (types, states, numbers, locations)):
            return None
        return dict(
            job_id=job,
            diagnostic_id=diagnostic,
            observed_utc=observed.isoformat(),
            stage=stage,
            exception_types=[
                v
                for v in types[:4]
                if isinstance(v, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", v)
            ],
            sqlstates=[
                v for v in states[:4] if isinstance(v, str) and re.fullmatch(r"[A-Z0-9]{5}", v)
            ],
            sql_numbers=[v for v in numbers[:8] if type(v) is int and 0 <= v <= 999999],
            code_locations=[
                dict(file=v["file"], function=v["function"], line=v["line"])
                for v in locations[:16]
                if isinstance(v, dict)
                and v.get("file") in _CODE_FILES
                and isinstance(v.get("function"), str)
                and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", v["function"])
                and type(v.get("line")) is int
                and 0 < v["line"] < 100000
            ],
        )
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def recovery_failure_context(job, provenance):
    record = safe_failure_record(provenance.get("first_failure"))
    latest = safe_failure_record(provenance.get("latest_failure"))
    record = record if record and record["job_id"] == str(job["JobID"]).lower() else None
    latest = latest if latest and latest["job_id"] == str(job["JobID"]).lower() else None
    if not record:
        return dict(
            original_fault="not_recorded",
            latest=latest,
            summary="The original failure details were not saved with this historical export. The retained job proves its execution state, but does not identify an input/configuration fault or prove that one has been corrected.",
        )
    stage = {
        "snapshot": "reading or validating retained input",
        "authorization": "checking export ownership",
        "delivery": "preparing or delivering the spreadsheet",
        "terminal_record": "recording the final outcome",
        "unknown": "an unidentified export stage",
    }[record["stage"]]
    types = ", ".join(record["exception_types"]) or "unclassified error"
    return dict(
        original_fault="recorded",
        original=record,
        latest=latest,
        summary=f"The original failure occurred while {stage} ({types}). SQL codes and code locations are included in the complete report. These facts identify where it failed; they do not by themselves prove the cause or its correction.",
    )


def replacement_decision_context(job, registration):
    """Bounded job-linked facts for an admin decision; never infer an old fault."""
    import json

    from services.legacy_export_snapshot_service import configuration_digest

    provenance = json.loads(job["ProvenanceJson"])
    context = recovery_failure_context(job, provenance)
    producer = provenance.get("producer")
    filename = producer.get("completed_filename") if isinstance(producer, dict) else None
    filename = (
        filename
        if isinstance(filename, str) and re.fullmatch(r"stats_[0-9a-f]{32}\.ready\.csv", filename)
        else "not recorded"
    )
    created = job.get("CreatedUTC")
    created = created.isoformat(sep=" ") if isinstance(created, datetime) else "not recorded"
    original = provenance.get("registration_sha256")
    original = (
        original if isinstance(original, str) and re.fullmatch(r"[0-9a-f]{64}", original) else None
    )
    current = registration.get("legacy_configuration", {}).get(job["ConsumerKind"])
    current_hash = configuration_digest(current) if isinstance(current, dict) else None
    comparison = (
        "matches current"
        if original and original == current_hash
        else "differs from current" if original and current_hash else "comparison unavailable"
    )
    context.update(
        original_created_utc=created,
        input_file=filename,
        original_registration_sha256=original,
        current_registration_sha256=current_hash,
        configuration_comparison=comparison,
    )
    context["summary"] = (
        f"Created: {created} (UTC). Input: {filename}. Configuration: {comparison}. "
        + context["summary"]
    )
    return context
