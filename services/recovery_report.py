"""Read-only, credential-free incident reports from persisted observations."""

from datetime import UTC, datetime
import json

from services import operation_diagnostics
from services.recovery_execution_guard import execution_progress
from services.recovery_service import SourceConflict


def _safe(value):
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    from services.recovery_evidence_bundle import redact_report_text

    return redact_report_text(value)


def _next_step(row, evidence, actions, blocked):
    if row.get("pending_action"):
        return "A repair is already accepted and awaiting verification. Use Recheck to follow its recorded outcome; do not submit another repair."
    if evidence.get("check_unavailable"):
        return "Verification is unavailable. Use Recheck after the check recovers; no repair or healthy outcome is established."
    publication = row.get("publication_check")
    if publication and publication["outcome"] != "confirmed":
        return publication["explanation"]
    if (
        row["SourceKind"] in {"evidence_batch", "historical_batch"}
        and evidence.get("outcome") == "completed_with_exceptions"
    ):
        return "The group has finished with exceptions. Open the recovery centre and browse individual incidents to review changed or unrepaired evidence. Group completion does not resolve those incidents."
    if row["State"] == "resolved":
        if any(
            link.get("kind") == "configuration_continuation"
            for link in evidence.get("recovery_links", [])
        ):
            return "This attempt is resolved. Open Choose configuration continuation to review whether to retry publication or keep the prior configuration; that separate decision still requires current verification."
        return "Resolved; no repair required."
    if row.get("last_repair") and row["last_repair"]["state"] == "not_applied":
        return row["last_repair"]["explanation"]
    if (
        row["SourceKind"] in {"evidence_batch", "historical_batch"}
        and evidence.get("outcome") == "running"
    ):
        return "The approved group is running. Use Recheck to follow verified, pending and changed counts. Do not submit another decision for pending members; review any exceptions when the group finishes."
    if row["SourceKind"] == "player_report" and "complete_cache_only" in actions and not blocked:
        return "The bot will verify the original cache-only intent and close this capture automatically. Use Recheck to follow verification; no spreadsheet export is requested."
    if (
        row["SourceKind"] == "configuration_producer"
        and "complete_configuration_only" in actions
        and not blocked
    ):
        return "The bot will verify the original SQL-only configuration intent and close this capture automatically. Use Recheck to follow verification; no spreadsheet export is requested."
    if actions and not blocked:
        return (
            "Open this incident in the recovery centre; review the checks and confirm the repair."
        )
    if evidence.get("recovery_links"):
        return "Open the linked recovery incident for its guided actions."
    if row.get("release_notice"):
        return "The required repair is not enabled in this release. The incident remains open; Recheck cannot unlock it."
    if evidence.get("required_evidence"):
        return "Follow the evidence-collection steps in this report. Recheck after collecting the required evidence; no release, replay or successful outcome is authorised by missing evidence."
    return "No repair is authorized by the saved evidence. The diagnosis and required repairs above identify the blocker."


def incident_report(service, row):
    """Allowlist diagnostic fields; never serialize raw evidence or action inputs."""
    # report_page includes pending-action state in the scoped page query. Apply
    # only the presentation policy here; present() would query each row again.
    current = service.presentation_policy(row) if service.presentation_policy else row
    evidence = current["evidence"]
    actions = evidence.get("actions", {})
    blocked = bool(
        current.get("pending_action")
        or evidence.get("check_unavailable")
        or row["SourceKind"] not in service.adapters
    )
    required = []
    for name, details in row["evidence"].get("actions", {}).items():
        required.append(
            dict(
                action=name,
                availability=(
                    "not_enabled_in_release"
                    if name not in actions
                    else (
                        "verification_required"
                        if blocked
                        else "resolved"
                        if row["State"] == "resolved"
                        else "guided_confirmation"
                    )
                ),
                **{key: details[key] for key in ("label", "check", "effect") if key in details},
            )
        )
    return _safe(
        dict(
            incident_id=row["IncidentID"],
            source_kind=row["SourceKind"],
            source_id=row["SourceID"],
            state=row["State"],
            revision=row["Revision"],
            first_seen_utc=row["FirstSeenUTC"],
            last_checked_utc=row["LastSeenUTC"],
            diagnosis={
                key: evidence[key]
                for key in (
                    "title",
                    "outcome",
                    "explanation",
                    "scan",
                    "season",
                    "resolution",
                    "evidence_reference",
                    "evidence_kinds",
                    "copies",
                    "backup_candidate",
                    "required_evidence",
                    "check_unavailable",
                    "check_diagnostic",
                    "blocking_job_ids",
                    "recovery_links",
                    "receipt_diagnostics",
                    "completed_reporting_stages",
                    "failure_context",
                    "group_id",
                    "approved_count",
                    "verified_count",
                    "pending_count",
                    "changed_count",
                    "queue_ticket",
                    "preparation_state",
                    "replica_diagnostics",
                )
                if key in evidence
            }
            | (
                dict(
                    members=[
                        {k: m[k] for k in ("id", "created", "input", "procedure") if k in m}
                        for m in evidence.get("members", [])
                    ],
                    configuration_fingerprints={
                        k: evidence.get("configuration", {}).get(k) for k in ("original", "current")
                    },
                )
                if row["SourceKind"] == "historical_batch"
                else {}
            ),
            required_repairs=required,
            pending_verification=current.get("pending_action"),
            publication_check=current.get("publication_check"),
            last_repair=current.get("last_repair"),
            execution_progress=(
                execution_progress(row["IncidentID"]) if current.get("pending_action") else None
            ),
            release_restriction=current.get("release_notice"),
            adapter_available=row["SourceKind"] in service.adapters,
            next_step=_next_step(current, evidence, actions, blocked),
        )
    )


def encode(document):
    return json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8")


def unavailable_report(error):
    """Still provide actionable monitor diagnostics when the incident store is down."""
    return dict(
        content=encode(
            dict(
                format="k98-recovery-report-v1",
                generated_utc=datetime.now(UTC).isoformat(),
                complete=False,
                incidents_available=False,
                monitor=_monitor_report(),
                operation_observations=_operation_report(),
                collection_failure={"error_type": type(error).__name__},
                next_step="Incident collection failed. Share this diagnostic report, then download again after connectivity or registration recovers. This is not an empty incident list.",
            )
        ),
        filename="K98-recovery-report-unavailable.json",
        unavailable=True,
        next_after=None,
    )


def build_report(service, actor, after=None, through=None, part=1, max_bytes=8 * 1024 * 1024):
    from services.recovery_evidence_bundle import report_request

    service.report_authorize(actor)
    with report_request():
        return _build_report(service, actor, after, through, part, max_bytes)


def _monitor_report():
    from services.recovery_evidence_bundle import (
        guarded,
        loaded_call,
        monitor_snapshot,
        startup_snapshot,
    )

    result, monitor_coverage = monitor_snapshot(limit=6000)
    coverage, details = {}, {"monitor": monitor_coverage}

    def include(name, value, state, *, cache=False):
        # Reserve room for all coverage descriptors in the final pretty JSON.
        candidate = dict(result)
        if cache:
            candidate["cache_outcomes_v1"] = dict(
                result.get("cache_outcomes_v1", {}), **{name: value}
            )
        else:
            candidate[name] = value
        if len(encode(candidate)) > 24576:
            value = {"status": "omitted_report_budget"}
            state = dict(
                state,
                source_status=state["status"],
                status="partial",
                reason="ordinary_report_byte_bound",
                included=0,
                omitted=state.get("available", "unknown"),
            )
        if cache:
            result.setdefault("cache_outcomes_v1", {})[name] = value
        else:
            result[name] = value
        coverage[name] = state["status"]
        details[name] = state

    include("startup", *startup_snapshot(limit=8192))

    for name, module, function in (
        ("admission_observations_v1", "services.cache_admission_diagnostics", "report"),
        ("event_cache", "event_cache", "report"),
        ("event_startup", "core.scheduler_lifecycle", "event_startup_report"),
        ("event_dm_startup", "event_scheduler", "dm_startup_report"),
        ("event_delivery_v1", "services.event_delivery_service", "report"),
    ):
        include(name, *guarded(lambda m=module, f=function: loaded_call(m, f), limit=2048))
    for name, module, function in (
        ("stats", "services.player_stats_cache_service", "report"),
        ("profile", "profile_cache", "get_cache_stats"),
        ("name", "target_utils", "name_outcome_report"),
    ):
        value, state = guarded(lambda m=module, f=function: loaded_call(m, f), limit=1024)
        if name == "profile" and type(value) is dict:
            value = value.get("outcome", value)
        include(name, value, state, cache=True)
    include(
        "health_observations_v1",
        *guarded(
            lambda: loaded_call("services.operator_status_service", "snapshot"),
            limit=16384,
            max_depth=8,
        ),
    )
    result["source_coverage"] = coverage
    result["component_coverage"] = details
    return result


def _operation_report():
    """Keep validated nested operation summaries within the ordinary-report budget."""
    from services.recovery_evidence_bundle import safe

    try:
        source = operation_diagnostics.report()
        if type(source) is not dict or type(source.get("operations")) is not list:
            raise ValueError("Invalid operation report")
        if len(source["operations"]) > 512:
            raise ValueError("Operation report inventory bound")
        result = safe({key: value for key, value in source.items() if key != "operations"})
        result["operations"] = []
        if len(encode(result)) > 16384:
            raise ValueError("Operation report byte bound")
        validator = operation_diagnostics.DiagnosticSink()
        rejected = 0
        for row in source["operations"]:
            try:
                if type(row) is not dict:
                    raise ValueError("Invalid operation summary")
                latest = row.get("latest")
                projected = validator._restore_row(
                    dict(row, transitions=[] if latest is None else [latest])
                )
                projected.pop("transitions")
                projected["latest"] = latest
                if len(encode(dict(result, operations=result["operations"] + [projected]))) > 15360:
                    raise ValueError("Operation report byte bound")
                result["operations"].append(projected)
            except Exception:
                rejected += 1
        omitted = source.get("omitted_operations", 0)
        if type(omitted) is not int or omitted < 0:
            omitted = 0
        result["omitted_operations"] = omitted + rejected
        upload = result.get("upload_observations", {})
        upload_partial = type(upload) is dict and (
            upload.get("coverage") == "partial" or upload.get("pending", 0) != 0
        )
        result["coverage"] = dict(
            status="partial" if omitted or rejected or upload_partial else "available",
            reason="operation_preview_invalid_or_bound" if omitted or rejected else None,
            available=len(source["operations"]) + omitted,
            included=len(result["operations"]),
            omitted=omitted + rejected,
            rejected=rejected,
        )
        if len(encode(result)) > 16384:
            raise ValueError("Final operation component bound")
        return result
    except Exception:
        return {"status": "unavailable", "reason": "source_unavailable_invalid_or_bound"}


def _build_report(service, actor, after=None, through=None, part=1, max_bytes=8 * 1024 * 1024):
    service.authorize(actor)
    if type(part) is not int or part < 1 or type(max_bytes) is not int or max_bytes < 65536:
        raise SourceConflict("A valid report continuation and attachment budget are required.")
    page = service.store.report_page(after=after, through=through)
    document = dict(
        format="k98-recovery-report-v1",
        generated_utc=datetime.now(UTC).isoformat(),
        incidents_first_seen_through_utc=str(page["through"]),
        part=part,
        total_recorded_incidents=page["total"],
        complete=False,
        more_parts=True,
        coverage=(
            "All recorded incident states in the configured account, storage and guild scope. "
            "Observations can change while downloading parts; this is not a transactional snapshot. "
            "A healthy monitor does not prove there are no incidents. Undiscovered failures are not included. "
            "Downloading reads saved observations only; it never applies or reconciles a repair."
        ),
        monitor=_monitor_report(),
        operation_observations=_operation_report(),
        incidents=[],
    )
    next_after = after
    encoded_size = len(encode(document))
    observations_omitted = False
    for row in page["rows"]:
        incident = incident_report(service, row)
        encoded_incident = encode(incident)
        # Each line is indented four spaces inside the incidents array. The
        # first item adds its array newlines/closing indent; later items add ,\n.
        item_size = len(encoded_incident) + 4 * (encoded_incident.count(b"\n") + 1)
        addition = item_size + (2 if document["incidents"] else 4)
        if not document["incidents"] and encoded_size + addition > max_bytes - 1024:
            # Optional evidence must not prevent an otherwise fitting incident
            # from being delivered. The final omission marker uses the existing
            # reserved metadata allowance rather than the incident budget.
            document.pop("operation_observations", None)
            observations_omitted = True
            encoded_size = len(encode(document))
            if encoded_size + addition > max_bytes - 1024:
                document["monitor"] = {"status": "omitted_attachment_budget"}
                encoded_size = len(encode(document))
        if encoded_size + addition > max_bytes - 1024:
            if not document["incidents"]:
                raise SourceConflict(
                    f"One incident requires at least {encoded_size + addition + 1024} bytes. "
                    "Use a destination with a larger attachment budget; the incident cursor has not advanced."
                )
            break
        document["incidents"].append(incident)
        encoded_size += addition
        next_after = row["IncidentID"]
    more = page["more"] or len(document["incidents"]) < len(page["rows"])
    document["more_parts"] = more
    document["complete"] = not more and after is None
    document["parts_complete_through_this_part"] = not more
    document["included_incidents"] = len(document["incidents"])
    if observations_omitted:
        document["operation_observations"] = {"status": "omitted_attachment_budget"}
    content = encode(document)
    if len(content) > max_bytes:
        raise SourceConflict("Report exceeds its attachment budget; cursor has not advanced.")
    return dict(
        content=content,
        filename=f"K98-recovery-report-part-{part}.json",
        next_after=next_after if more else None,
        through=page["through"],
        part=part,
        count=len(document["incidents"]),
        total=page["total"],
    )
