"""Fixed failed-export decisions inside the registered private authority boundary."""

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity
from services.failed_export_closeout import FailedExportCloseout
from services.failed_export_closeout_dal import FailedExportCloseoutDAL


def dispatch(broker, message):
    operation = message.get("operation")
    expected = {"version", "action", "job_id", "operation"}
    if operation == "execute":
        expected |= {"step", "token", "actor", "reason", "payload"}
    elif operation == "reconcile":
        expected |= {"recovery_action"}
    elif operation != "inspect":
        raise SourceConflict("Fixed failed-export operation required.")
    if set(message) != expected or message["action"] != "failed_export_recovery":
        raise SourceConflict("Exact failed-export recovery message required.")
    if broker.boundary is None or broker.replacements is None:
        raise SourceConflict("Protected recovery authority and registration history required.")
    job_id = identity(message["job_id"])
    with broker.authority._lock:
        broker.boundary.recheck()
        registrations, current = broker.replacements.registrations()
        registered = current.value()
        service = FailedExportCloseout(
            dal=FailedExportCloseoutDAL(
                broker.authority.dal.connect,
                account=registered["account"],
                storage_owner=registered["storage_owner"],
            ),
            execution=broker.authority.dal,
            store=broker.authority.store,
            registrations=registrations,
        )
        if operation == "execute":
            service.execute(
                job_id,
                message["step"],
                message["token"],
                message["actor"],
                message["reason"],
                payload=message["payload"],
            )
        if operation == "reconcile":
            action = message["recovery_action"]
            if (
                not isinstance(action, dict)
                or set(action) != {"ActionID", "ActionKind", "EvidenceHash", "Reason", "InputJson"}
                or action["InputJson"] is not None
            ):
                raise SourceConflict("Exact immutable recovery action required.")
            return service.reconcile(job_id, action)
        evidence, token, resolved = service.inspect(job_id)
        return dict(evidence=evidence, token=token, resolved=resolved)
