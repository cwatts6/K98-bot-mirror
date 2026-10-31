"""Read-only, credential-free incident reports from persisted observations."""

from datetime import UTC, datetime
import json

from core.operator_diagnostic_payloads import redact_diagnostic_text
from services import recovery_health
from services.recovery_execution_guard import execution_progress
from services.recovery_service import SourceConflict


def _safe(value):
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_diagnostic_text(value)


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
    encoded_size = len(encode(document))
    for row in page["rows"]:
        incident = incident_report(service, row)
        encoded_incident = encode(incident)
        # Each line is indented four spaces inside the incidents array. The
        # first item adds its array newlines/closing indent; later items add ,\n.
        item_size = len(encoded_incident) + 4 * (encoded_incident.count(b"\n") + 1)
        addition = item_size + (2 if document["incidents"] else 4)
        if encoded_size + addition > max_bytes - 1024:
            if not document["incidents"]:
                raise SourceConflict("One incident exceeds this destination's attachment budget.")
            break
        document["incidents"].append(incident)
        encoded_size += addition
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
