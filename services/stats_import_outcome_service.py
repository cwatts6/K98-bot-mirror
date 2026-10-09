"""Import outcome decisions independent of Discord and provider execution."""

import json
import logging

from kvk.dal.new_source_import_dal import SourceConflict
from services.stats_import_outcome_dal import StatsImportOutcomeDAL

logger = logging.getLogger(__name__)


def outcome_dal(runtime):
    return StatsImportOutcomeDAL(
        runtime.dal.connect, account=runtime.account, storage_owner=runtime.store.storage_owner
    )


def event(preparation_id, stage, outcome, *, action, error=None, **facts):
    from services.legacy_export_snapshot_dal import _diagnostic_uuid

    record = dict(
        preparation_id=_diagnostic_uuid(preparation_id),
        stage=stage,
        outcome=outcome,
        next_action=action,
        **facts,
    )
    if error is not None:
        from services.export_contention import sql_error_facts

        record.update(sql_error_facts(error))
    try:
        logger.log(
            logging.WARNING if error is not None or outcome == "held" else logging.INFO,
            "stats_import_outcome %s",
            json.dumps(record, sort_keys=True),
        )
    except Exception:
        # A diagnostic sink must not turn an acknowledged settlement into a
        # failed operation or cause an import to be replayed.
        return


def settle_known_failure(runtime, preparation_id):
    """Only a durable rolled-back receipt admits unattended release; never replay."""
    dal = outcome_dal(runtime)
    try:
        preview = dal.inspect(preparation_id)
        if preview["action"] == "resolved":
            return True
        if preview["action"] != "release_failure":
            event(
                preparation_id,
                "automatic_resolution",
                "held",
                action="ops import_resolution: preview; committed import requires explicit supersession decision",
                sql_state=(preview["execution"] or {}).get("State"),
            )
            return False
        action = dal.settle(
            preparation_id,
            token=preview["token"],
            actor="system:import_outcome",
            reason="Exact unstarted/rolled-back receipt and exclusive execution/producer locks verified",
        )
        event(
            preparation_id,
            "automatic_resolution",
            "resolved",
            action="correct source or configuration, then submit a fresh upload",
            resolution=action,
            import_replayed=False,
        )
        return True
    except Exception as exc:
        event(
            preparation_id,
            "automatic_resolution",
            "held",
            action="ops import_resolution: status; retain input and exact SQL evidence",
            error=exc,
        )
        return False


def register_execution(completed_filename):
    from services.legacy_export_snapshot_service import current_owner, require_runtime

    owner = current_owner()
    if owner is None:
        return None
    outcome_dal(require_runtime()).prepare(owner.claim, completed_filename)
    owner.stats_execution_registered = True
    event(owner.claim.preparation_id, "execution_registration", "prepared", action="execute once")
    return owner.claim.preparation_id


def recover_completed_writer(runtime, owner):
    """Finish a proven SQL commit while the original snapshot session is still held.

    No provider call, procedure rerun, resource stealing or new preparation occurs.
    A capture whose durable acknowledgment is uncertain is retained for inspection.
    """
    from dataclasses import replace

    if not owner.stats_execution_registered:
        return False
    evidence = outcome_dal(runtime).read(owner.claim.preparation_id)
    if not evidence or evidence["State"] != "completed":
        return False
    row = runtime.dal.read(owner.claim.preparation_id)
    if str(row["OwnerID"]).lower() != owner.claim.owner or row["Fence"] != owner.claim.fence:
        raise SourceConflict("Completion recovery ownership differs.")
    if row["State"] == "captured":
        runtime.collect_capture(owner)
        event(
            owner.claim.preparation_id,
            "completion_recovery",
            "captured",
            action="continue pipeline; do not import again",
        )
        return True
    if row["State"] not in {"writing", "committed"} or row["SpoolKey"] is not None:
        raise SourceConflict("Completion recovery requires the same unexported writer.")
    owner.claim = replace(owner.claim, version=row["Version"])
    owner.failed = False
    if row["State"] == "writing":
        runtime.checkpoint_writer(
            owner,
            dict(
                procedure="dbo.UPDATE_ALL2",
                completed_filename=evidence["CompletedFileName"],
                execution_preparation_id=owner.claim.preparation_id,
                scan_order=evidence["ScanOrder"],
                last_run_counter=evidence["LastRunCounter"],
            ),
        )
    else:
        pending = json.loads(row["GenerationJson"])
        if pending.get("capture") != "pending":
            raise SourceConflict(
                "Capture already started; inspect its durable spool acknowledgment before recovery."
            )
        owner.completion = pending
    runtime.finish_writer(owner)
    event(
        owner.claim.preparation_id,
        "completion_recovery",
        "captured",
        action="continue pipeline; do not import again",
        sql_state="completed",
    )
    return True
