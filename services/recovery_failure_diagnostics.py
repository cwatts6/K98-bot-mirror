"""Action-bound recovery diagnostics; exception prose is never persisted."""

import json
from uuid import UUID

from services.export_failure_diagnostics import failure_record, safe_failure_record


def action_failure(error, action_id):
    return failure_record(error, job_id=str(action_id), stage="recovery")


def retained_failure(action):
    if not action:
        return None
    try:
        result = json.loads(action.get("ResultJson") or "{}")
        record = safe_failure_record(result.get("failure"))
        if record and record["job_id"] == str(UUID(str(action["ActionID"]))):
            return record
    except (ValueError, TypeError, AttributeError, KeyError):
        pass
    return None


def action_result(action):
    """A diagnostic cannot authorize a retry or change durable settlement."""
    if not action or action.get("State") not in {
        "dispatched",
        "unknown",
        "not_applied",
        "verified",
    }:
        return None
    record = retained_failure(action)
    if not record:
        return None
    state = action["State"]
    if state == "verified":
        explanation = (
            "The repair reported an error, but its durable outcome was subsequently verified."
        )
    elif state == "not_applied":
        explanation = "The repair failed to complete. Retained receipts identify any stages already committed."
    else:
        explanation = "The repair reported an error and its outcome is still awaiting verification. Do not submit another repair."
    if 229 in record["sql_numbers"] and state != "verified":
        explanation += (
            " SQL denied permission (229). Review the corrective release before retrying."
        )
    elif state == "not_applied":
        explanation += (
            " Download the recovery report and resolve the recorded failure before retrying."
        )
    return dict(action_id=record["job_id"], state=state, failure=record, explanation=explanation)
