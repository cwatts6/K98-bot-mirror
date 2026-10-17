"""Read-only, credential-free incident reports from persisted observations."""

from datetime import UTC, datetime
import json

from core.operator_diagnostic_payloads import redact_diagnostic_text
from services import recovery_health
from services.recovery_service import SourceConflict


def _safe(value):
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_diagnostic_text(value)


def incident_report(service, row):
    """Allowlist diagnostic fields; never serialize raw evidence or action inputs."""
    current = service.present(row)
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
                        else "resolved" if row["State"] == "resolved" else "guided_confirmation"
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
                    "check_unavailable",
                    "blocking_job_ids",
                    "recovery_links",
                    "receipt_diagnostics",
                )
                if key in evidence
            },
            required_repairs=required,
            pending_verification=current.get("pending_action"),
            release_restriction=current.get("release_notice"),
            adapter_available=row["SourceKind"] in service.adapters,
            next_step=(
                "Open this incident in the recovery centre; review the checks and confirm the repair."
                if actions and not blocked and row["State"] == "open"
                else (
                    "Open the linked recovery incident for its guided actions."
                    if evidence.get("recovery_links")
                    else (
                        "No repair is authorized by the saved evidence. The diagnosis and required repairs above identify the blocker."
                        if row["State"] == "open"
                        else "Resolved; no repair required."
                    )
                )
            ),
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
                monitor=recovery_health.report(),
                collection_failure=recovery_health.failure_detail(error),
                next_step="Incident collection failed. Share this diagnostic report, then download again after connectivity or registration recovers. This is not an empty incident list.",
            )
        ),
        filename="K98-recovery-report-unavailable.json",
        unavailable=True,
        next_after=None,
    )


def build_report(service, actor, after=None, through=None, part=1, max_bytes=8 * 1024 * 1024):
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
        monitor=recovery_health.report(),
        incidents=[],
    )
    next_after = after
    for row in page["rows"]:
        document["incidents"].append(incident_report(service, row))
        if len(encode(document)) > max_bytes - 1024:
            document["incidents"].pop()
            if not document["incidents"]:
                raise SourceConflict("One incident exceeds this destination's attachment budget.")
            break
        next_after = row["IncidentID"]
    more = page["more"] or len(document["incidents"]) < len(page["rows"])
    document["more_parts"] = more
    document["complete"] = not more and after is None
    document["parts_complete_through_this_part"] = not more
    document["included_incidents"] = len(document["incidents"])
    return dict(
        content=encode(document),
        filename=f"K98-recovery-report-part-{part}.json",
        next_after=next_after if more else None,
        through=page["through"],
        part=part,
        count=len(document["incidents"]),
        total=page["total"],
    )
