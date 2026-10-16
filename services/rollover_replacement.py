"""Guided replacement continuation and verification of the independent new rollover."""

from contextlib import closing
import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_execution_protocol import proof_membership
from services.export_reconciliation_service import ClosedStreamVerifier
from services.export_replacement_workflow import ReplacementWorkflow, choice


class RolloverReplacementContinuation:
    def __init__(self, *, dal, authority, next_workflow=None):
        self.dal, self.authority = dal, authority
        self.next_workflow = next_workflow

    def verify(self, operation, activation):
        progress = json.loads(operation["ProgressJson"])
        association = progress.get("reconciliation", {}).get("proof", {})
        proof_id = identity(association.get("proof_id"))
        row = self.authority.dal.read_proof(proof_id)
        pool = next(
            p for p in activation["registration"]["pools"] if p["pool_id"] == operation["PoolID"]
        )
        if row is None:
            raise SourceConflict("The replacement rollover completion proof is unavailable.")
        body = json.loads(row["EvidenceJson"])
        membership = proof_membership(row["MembershipJson"])
        targets = sorted([pool["index_file_id"], *pool["slot_file_ids"]])
        if (
            operation["State"] != "completed"
            or operation["Phase"] != "complete"
            or operation["OwnerID"] is not None
            or operation["ActivePoolID"] is not None
            or row["AccountKey"] != operation["AccountKey"]
            or (row["ProofKind"], row["Outcome"]) != ("rollover_complete", "completed")
            or bytes(row["RegistrationHash"]).hex() != pool["registration_sha256"]
            or bytes(row["SnapshotHash"]).hex() != body.get("snapshot_hash")
            or dict(body, proof_id=proof_id) != association
            or body.get("writer_terminated") is not True
            or body.get("state") != "completed"
            or progress.get("files") != body.get("files")
            or progress.get("setup") != body.get("setup")
            or set(body.get("files", {})) != set(targets)
            or (body.get("setup", {}).get("old_kvk"), body.get("setup", {}).get("new_kvk"))
            != (operation["OldKVK"], operation["NewKVK"])
            or membership["targets"] != targets
            or hashlib.sha256(row["MembershipJson"].encode("utf-16-le")).digest()
            != bytes(row["MembershipHash"])
        ):
            raise SourceConflict(
                "Replacement rollover does not match its complete independent verification."
            )
        closed = ClosedStreamVerifier(dal=self.authority.dal, store=self.authority.store)
        probe = self.authority.dal.read_stream(membership["probe"]["stream_id"])
        if (
            probe is None
            or identity(probe["OutputOperationID"]) != operation["OperationID"]
            or probe["Version"] != membership["probe"]["version"]
            or probe["Purpose"] != "probe"
        ):
            raise SourceConflict("Final verification belongs to another rollover.")
        closed.verify(
            identity(probe["StreamID"]),
            account=operation["AccountKey"],
            registration_hash=bytes.fromhex(pool["registration_sha256"]),
            require_observation=True,
        )
        mutations = set()
        with closing(
            self.authority.dal.read_catalogue(operation["AccountKey"], targets)
        ) as streams:
            for stream in streams:
                if str(stream["OutputOperationID"]).lower() != operation["OperationID"]:
                    continue
                if stream["AccountKey"] != operation["AccountKey"]:
                    raise SourceConflict("Replacement rollover stream crosses account scope.")
                closed.verify(
                    identity(stream["StreamID"]),
                    account=operation["AccountKey"],
                    registration_hash=bytes.fromhex(pool["registration_sha256"]),
                    require_observation=False,
                )
                if stream["Purpose"] == "mutation":
                    if stream["ClaimVersion"] in mutations:
                        raise SourceConflict("Duplicate replacement rollover phase.")
                    mutations.add(stream["ClaimVersion"])
        if len(mutations) != 2 * len(targets) + 1:
            raise SourceConflict("Replacement rollover journal is missing.")

    def inspect(self, original_id, activation):
        operation = self.dal.read(original_id, activation)
        if operation is None:
            return dict(
                stage="rollover_continuation_required",
                explanation="The fresh pool is verified and active. Continue the original season change on these replacements, then verify the complete rollover before resolving this incident.",
                resolved=False,
                operation_id=None,
                actions={
                    "start_replacement_rollover": choice(
                        "Start replacement rollover",
                        f"Confirm the original season {activation['input_commitment']['OldKVK']} to {activation['input_commitment']['NewKVK']} change should proceed on the verified fresh pool.",
                        "Queue one durable replacement operation. Keep all original files permanently isolated. Require separate final verification before completion.",
                    )
                },
            )
        state = operation["State"]
        if state == "uncertain" and self.next_workflow is not None:
            from services.export_replacement_dal import ExportReplacementDAL

            plans = ExportReplacementDAL(self.dal.pools.connect, owner_kind="rollover")
            if plans.for_job(operation["OperationID"], account=operation["AccountKey"]):
                _, _, replaced = self.next_workflow(operation["OperationID"]).inspect(
                    operation["OperationID"]
                )
                if replaced:
                    return dict(
                        stage="replacement_rollover_completed",
                        explanation="The subsequent guided replacement rollover is verified. Earlier uncertain operations remain permanently isolated in the audit history.",
                        resolved=True,
                        operation_id=operation["OperationID"],
                        actions={},
                    )
        if state == "completed":
            self.verify(operation, activation)
        actions = {}
        if state in {"running", "uncertain"} and json.loads(operation["ProgressJson"]).get(
            "request", {}
        ).get("phase") in {"setup_pending", "setup_verified"}:
            actions["verify_replacement_rollover"] = choice(
                "Verify replacement rollover",
                "Keep the new pool unchanged while the bot checks every recorded phase and the final season setup.",
                "Verify the original private journal and fresh readback, then atomically finish this replacement rollover and release its exact reservations.",
            )
        return dict(
            stage="replacement_rollover_" + state,
            explanation=(
                "The replacement rollover and its independent final verification are complete. The original uncertain operation remains permanently isolated in the audit history."
                if state == "completed"
                else "The replacement rollover is recorded. Review its progress and verify completion here. If this new operation is interrupted, open its guided recovery; do not replay an uncertain phase."
            ),
            resolved=state == "completed",
            operation_id=operation["OperationID"],
            operation_token=digest(operation).hex(),
            actions=actions,
        )

    def execute(self, *_args, **_kwargs):
        raise SourceConflict("Rollover continuation requires the composed bot runtime.")

    def reconcile(self, original_id, activation, action):
        operation = self.dal.read(original_id, activation)
        if action["ActionKind"] == "start_replacement_rollover":
            return (
                "verified" if operation and operation["OperationID"] == action["ActionID"] else None
            )
        if action["ActionKind"] == "verify_replacement_rollover":
            if operation and operation["State"] == "completed":
                self.verify(operation, activation)
                return "verified"
            return "not_applied"
        return None


class RolloverReplacementWorkflow(ReplacementWorkflow):
    def inspect(self, operation_id):
        evidence, token, resolved = super().inspect(operation_id)
        evidence["title"] = "Interrupted rollover replacement"
        delivery = evidence.get("delivery")
        if delivery and delivery.get("operation_id") and not resolved:
            evidence["recovery_links"] = [
                dict(
                    label="Review replacement rollover",
                    kind="export_rollover",
                    source_id=delivery["operation_id"],
                )
            ]
        if evidence["outcome"] == "isolation_required":
            evidence["explanation"] = (
                "A rollover phase may still change the old files. Permanently retire the complete old pool, verify a fresh pool, then perform the original season change there. The old write will remain uncertain in the audit history."
            )
            evidence["actions"]["isolate_targets"][
                "effect"
            ] = "Fence the complete old pool and release only this rollover's exact reservations. Continue here through replacement verification and the original season change."
        elif evidence["outcome"] == "activation_required":
            evidence["explanation"] = (
                "All replacement files passed owner, sharing and blank-content checks. Confirm activation, then continue and verify the original season change on the fresh pool."
            )
            evidence["actions"]["activate_replacements"][
                "effect"
            ] = "Seal the fresh pool registration. Keep this incident open through the replacement rollover and its independent final verification."
        return evidence, token, resolved
