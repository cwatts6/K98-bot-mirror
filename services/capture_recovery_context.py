"""Safe capture diagnostics and private review of the retained output contract."""

import json
import re

from kvk.dal.new_source_import_dal import SourceConflict
from services.producer_recovery_review import registration_review


def _diagnostic_document(value):
    try:
        result = json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}
    return result if isinstance(result, dict) else {}


def capture_context(prep, execution, recovery):
    """Describe observations, not an invented historical exception or success."""
    execution = execution or {}
    request = _diagnostic_document(prep.get("RequestJson"))
    generation = _diagnostic_document(prep.get("GenerationJson"))
    producer = generation.get("producer") or {}
    current = json.loads(recovery.runtime.configuration)[recovery.consumer]
    inner = request.get("request")
    matches = isinstance(inner, dict) and inner.get("config") == current
    filename = execution.get("CompletedFileName")
    context = dict(
        registration_matches=matches,
        producer_format=(
            "normal_completion"
            if isinstance(producer, dict) and "phases" in producer
            else (
                "execution_receipt"
                if isinstance(producer, dict) and "execution_preparation_id" in producer
                else (
                    "atomic_report"
                    if isinstance(producer, dict) and producer.get("atomic_checkpoint") == 1
                    else "unrecognised"
                )
            )
        ),
        original_fault="not_recorded",
        input_file=(
            filename
            if isinstance(filename, str)
            and re.fullmatch(r"stats_[0-9a-f]{32}\.ready\.csv", filename)
            else None
        ),
        sql_error_number=(
            execution.get("ErrorNumber") if type(execution.get("ErrorNumber")) is int else None
        ),
        sql_error_line=(
            execution.get("ErrorLine") if type(execution.get("ErrorLine")) is int else None
        ),
    )
    procedure = execution.get("ErrorProcedure")
    if isinstance(procedure, str) and re.fullmatch(
        r"(?:dbo|KVK)\.[A-Za-z_][A-Za-z0-9_]{0,100}", procedure
    ):
        context["sql_error_procedure"] = procedure
    if context["sql_error_number"] is not None:
        context["original_fault"] = "sql_receipt"
    if generation.get("capture_abandoned"):
        context["current_blocker"] = None
        context["summary"] = (
            "Admin chose to skip this export. The retained SQL result and original evidence are preserved; no capture or queue repair remains for this incident. This does not certify spreadsheet delivery."
        )
    elif prep.get("JobID") and prep.get("State") == "materialized":
        context["current_blocker"] = None
        context["summary"] = (
            "The retained output has a durable queue admission. Provider delivery is verified separately; no original exception message was saved for the capture stage."
        )
    elif not generation and execution.get("State") != "completed":
        context["current_blocker"] = "completion_unproven"
        context["summary"] = (
            "No exact SQL completion receipt or producer checkpoint is available. The original execution outcome is unproven; the saved preparation alone does not establish a successful import or a safe replay."
        )
    elif not matches:
        context["current_blocker"] = "registration_changed"
        context["summary"] = (
            "The retained output settings differ from the current registered settings. Review the original and current destinations; do not rerun the import."
        )
    elif generation.get("capture_failure"):
        context["current_blocker"] = "output_verification_failed"
        context["summary"] = (
            "A capture repair could not verify its retained output. The committed SQL result remains preserved; review the supported skip decision."
        )
    else:
        context["current_blocker"] = (
            "awaiting_verified_queue"
            if prep.get("SpoolKey") and not prep.get("JobID")
            else "capture_or_queue_verification"
        )
        context["summary"] = (
            "The SQL result is retained; its capture or queue handoff needs verification. No original exception message was saved for this stage. This does not establish an input/configuration fault."
        )
    if context["sql_error_number"] is not None:
        context[
            "summary"
        ] += f" The SQL execution receipt records error {context['sql_error_number']} (line {context['sql_error_line']}); inspect the recorded procedure and retained input in the review."
    return context


def capture_review(adapter, source_id, action, token):
    preview = adapter.dal.inspect(source_id)
    if preview["token"] != token:
        raise SourceConflict("Capture evidence changed. Reopen this incident.")
    evidence, current_token, resolved = adapter.inspect(source_id)
    if current_token != token or resolved or action not in evidence["actions"]:
        raise SourceConflict("This capture decision is no longer available.")
    prep, execution = preview["preparation"], preview["execution"] or {}
    recovery = adapter.capture_recovery
    context = capture_context(prep, execution, recovery)
    fields = [dict(label="Why this needs attention", text=context["summary"])]
    diagnostic = json.dumps(context, sort_keys=True)
    fields.extend(
        dict(label="Original failure evidence", text=diagnostic[offset : offset + 400])
        for offset in range(0, len(diagnostic), 400)
    )
    fields.extend(
        registration_review(
            dict(
                preparation=prep,
                current_registration=json.loads(recovery.runtime.configuration)[recovery.consumer],
                producer=dict(
                    inputs=dict(
                        input_file=context["input_file"],
                        scan=execution.get("ScanOrder"),
                        sql_state=execution.get("State"),
                        output_captured=bool(prep.get("SpoolKey")),
                    )
                ),
            )
        )
    )
    return fields


def add_capture_context(evidence, prep, execution, recovery):
    context = capture_context(prep, execution, recovery)
    evidence["failure_context"] = context
    for name, action in evidence["actions"].items():
        if name in {"resume_capture", "queue_capture", "abandon_capture"}:
            action.update(
                review_details=True,
                review_title="Review retained output and original fault",
                review_description="Check the retained input, failure evidence and destinations. Queue continues this saved output; skip keeps SQL and accepts no spreadsheet update. Neither repeats the import or report calculation.",
            )
