"""Guided retained-input continuation; queue admission never means resolution."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import JobSpec
from services.export_replacement_snapshot import rebind_snapshot
from services.export_snapshot_store import SnapshotReceipt
from services.legacy_export_snapshot_service import LegacySnapshot


class ReplacementDelivery:
    def __init__(
        self,
        *,
        dal,
        discovery,
        verify_delivery,
        store=None,
        source_plan=None,
        next_activation=None,
        verify_input=None,
    ):
        self.dal, self.discovery, self.verify_delivery = dal, discovery, verify_delivery
        self.store, self.source_plan = store, source_plan
        self.next_activation = next_activation
        self.verify_input = verify_input

    def inspect(self, job_id, activation, *, _visited=frozenset()):
        if job_id in _visited or len(_visited) >= 64:
            raise SourceConflict("Replacement delivery lineage is cyclic or exceeds its bound.")
        _visited = _visited | {job_id}
        receipt = self.dal.read(job_id, activation["activation_id"], self.discovery.account)
        if receipt is None:
            return dict(
                stage="publication_required",
                resolved=False,
                job_id=None,
                explanation="The replacement registration is active. Publish the retained input to these fresh files; the original SQL import will not run again.",
                actions=dict(
                    publish_replacement=dict(
                        label="Publish retained output",
                        check="Confirm the original retained report should be published to the new output links.",
                        effect="Queue one separately identified export using the original committed data. The incident remains open until delivery and request closure verify.",
                    )
                ),
            )
        snapshot = self.discovery.job(receipt["ReplacementJobID"])
        job = snapshot["job"]
        original = self.discovery.job(job_id)["job"]
        lineage = json.loads(job["ProvenanceJson"]).get("replacement", {})
        if (
            receipt["OriginalJobID"] != job_id
            or receipt["ActivationID"] != activation["activation_id"]
            or receipt["ReplacementInputHash"] != job["InputHash"]
            or receipt["OriginalInputHash"] != original["InputHash"]
            or job["ConsumerKind"] != original["ConsumerKind"]
            or (
                job["ConsumerKind"] == "new_source"
                and (job["InputHash"], job["IntentID"])
                != (original["InputHash"], original["IntentID"])
            )
            or lineage.get("original_job_id") != job_id
            or lineage.get("activation_id") != activation["activation_id"]
            or lineage.get("original_input_sha256") != receipt["OriginalInputHash"]
        ):
            raise SourceConflict("Replacement delivery differs from its immutable input lineage.")
        root = self.verify_input(snapshot, activation) if self.verify_input is not None else None
        resolved = False
        if job["State"] == "confirmed":
            self.verify_delivery(snapshot, activation)
            resolved = True
        elif snapshot.get("isolated_targets") and self.next_activation is not None:
            successor = self.next_activation(job["JobID"])
            if successor is not None:
                if root is not None:
                    successor = dict(successor, content_commitment=root)
                result = self.inspect(job["JobID"], successor, _visited=_visited)
                # Actions belong to the linked incident's exact evidence, never
                # to the original incident's decision or registration.
                return dict(
                    result,
                    actions={},
                    job_id=result.get("job_id") or job["JobID"],
                    explanation=(
                        "The replacement required another recovery. Its retained-input chain "
                        "and final delivery are now verified; all uncertain history remains preserved."
                        if result["resolved"]
                        else "The replacement required another recovery. Open its linked recovery "
                        "to continue; this incident stays open until final delivery verifies."
                    ),
                )
        failed = job["State"] in {"failed", "uncertain", "cancelled", "coalesced"}
        return dict(
            stage="replacement_delivered"
            if resolved
            else "replacement_needs_attention"
            if failed
            else "replacement_queued",
            resolved=resolved,
            job_id=job["JobID"],
            job_state=job["State"],
            actions={},
            explanation="Replacement delivery and execution evidence verified. The original uncertain history remains preserved."
            if resolved
            else "The replacement export needs attention. Open its linked recovery here; the original incident remains open until that delivery is resolved."
            if failed
            else "The retained export is queued or running on the replacement files. This incident will close only after delivery and execution evidence verify.",
        )

    def execute(self, job_id, activation, action, *, actor, reason):
        if action != "publish_replacement":
            raise SourceConflict("Unknown replacement delivery action.")
        prior = self.dal.read(job_id, activation["activation_id"], self.discovery.account)
        if prior is not None:
            if prior["Actor"] != actor or prior["Reason"] != reason:
                raise SourceConflict("Another admin decision already queued this delivery.")
            return
        snapshot = self.discovery.job(job_id)
        job = snapshot["job"]
        if job["ConsumerKind"] == "new_source":
            if self.source_plan is None:
                raise SourceConflict("Retained source publication planner is unavailable.")
            spec = self.source_plan(snapshot, activation, actor, reason)
        else:
            if self.store is None:
                raise SourceConflict(
                    "Retained output must be queued by its registered spool owner."
                )
            receipt = SnapshotReceipt(
                job["SpoolKey"], job["SpoolBytes"], job["InputHash"], job["StorageOwner"]
            )
            original = LegacySnapshot.load(self.store.read(receipt))
            rebound = rebind_snapshot(original, job=job, activation=activation)
            stored = rebound.persist(self.store)
            spec = JobSpec(
                account=job["AccountKey"],
                consumer=job["ConsumerKind"],
                kvk_no=job["KVK_NO"],
                input_hash=bytes.fromhex(stored.sha256),
                destinations=tuple(rebound.metadata()["config"]["destinations"]),
                actor=actor,
                reason=reason,
                spool_key=stored.key,
                spool_bytes=stored.byte_count,
                storage_owner=stored.storage_owner,
                provenance=json.dumps(
                    rebound.metadata()["generation"], sort_keys=True, separators=(",", ":")
                ),
            )
        self.dal.enqueue(original=job, activation=activation, spec=spec, actor=actor, reason=reason)

    def reconcile(self, job_id, activation, action):
        if action["ActionKind"] != "publish_replacement":
            return None
        receipt = self.dal.read(job_id, activation["activation_id"], self.discovery.account)
        if receipt is None:
            return None
        if (
            receipt["ActionID"] != action["ActionID"]
            or receipt["Actor"] != "recovery:" + action["ActionID"]
            or receipt["Reason"] != action["Reason"]
        ):
            raise SourceConflict("Replacement queue receipt belongs to another admin decision.")
        self.inspect(job_id, activation)
        return "verified"
