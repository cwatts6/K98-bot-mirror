"""Observation context for complete fixed read-only authority requests.

Selectors are deliberately explicit. Execute, reconcile, context (which may seal
input), proof publication and transport failures retain their original semantics.
The broker still authenticates and validates each request before accessing data.
"""

from core.sql_observation import ObservationBusy, observe_call
from kvk.dal.new_source_import_dal import SourceBusy
from services.export_proof_progress import AuthorityProofBusy


def is_observation(message):
    if (
        not isinstance(message, dict)
        or type(message.get("version")) is not int
        or message["version"] != 1
    ):
        return False
    fields = set(message) - {"deployment_hash"}
    action = message.get("action")
    if action in {
        "failed_export_recovery",
        "replacement_recovery",
        "rollover_replacement_recovery",
    }:
        return message.get("operation") == "inspect" and fields == {
            "version",
            "action",
            "operation",
            "job_id",
        }
    if action == "inspect_configuration_recovery":
        return fields == {"version", "action", "preparation_id"}
    if action == "inspect_target_recovery":
        return fields == {"version", "action", "job_id"}
    if action == "evidence_recovery":
        operation = message.get("operation")
        if operation == "inspect":
            return fields == {"version", "action", "operation", "reference"}
        if operation in {"pending", "pending_page"}:
            return fields == {"version", "action", "operation", "after"}
    return False


def dispatch_observation(dispatch, message):
    if not is_observation(message):
        return dispatch(message)
    try:
        return observe_call(dispatch, message)
    except (ObservationBusy, SourceBusy) as error:
        raise AuthorityProofBusy("Recovery observation is waiting for active work.") from error
