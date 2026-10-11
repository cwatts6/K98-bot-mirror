"""Private grouped export controls. Preview tokens are process-local, never authority."""

from copy import deepcopy
from dataclasses import dataclass
import json
import threading
import time
from uuid import UUID, uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.services.new_source_admin_service import CONFIRM_SECONDS
from kvk.services.new_source_export_service import compact_sheets_generation
from kvk.services.source_output_pool_service import capacity_for_snapshot
from services.export_coordination_dal import JobSpec, bounded_json
from services.legacy_export_snapshot_service import bound_runtime

EXPORT_ACTIONS = frozenset(
    {
        "export",
        "export_status",
        "export_reconcile",
        "export_rebuild",
        "rollover_preview",
        "rollover_confirm",
    }
)


@dataclass(frozen=True)
class Preview:
    token: str
    action: str
    actor: tuple[int, int, int]
    expires: float
    payload: str


class SourceExportOperatorService:
    def __init__(
        self,
        *,
        access_factory,
        pools,
        coordinator,
        rollover,
        generation_loader,
        reconciler,
        retirement_recovery=None,
        now=time.monotonic,
    ):
        if not coordinator.output_operations:
            raise SourceConflict("The full S10E writer contract must be explicitly composed.")
        self.access_factory, self.pools, self.coordinator = access_factory, pools, coordinator
        self.rollover, self.generation_loader, self.reconciler = (
            rollover,
            generation_loader,
            reconciler,
        )
        self.retirement_recovery = retirement_recovery
        self.now = now
        self._previews = {}
        self._lock = threading.RLock()

    def authorize(self, actor, action):
        self.access_factory().authorize(actor, action)

    @staticmethod
    def _actor(actor):
        return actor.user_id, actor.guild_id, actor.channel_id

    def _preview(self, actor, action, payload):
        token = str(uuid4())
        row = Preview(
            token, action, self._actor(actor), self.now() + CONFIRM_SECONDS, bounded_json(payload)
        )
        with self._lock:
            self._previews = {k: v for k, v in self._previews.items() if v.expires > self.now()}
            if len(self._previews) >= 128:
                raise SourceConflict("Too many outstanding previews; allow them to expire.")
            self._previews[token] = row
        return row

    @bound_runtime
    def status(self, actor, kvk_no, index_file_id=None):
        self.authorize(actor, "export_status")
        context = self.pools.export_context(self.pools.resolve(kvk_no, index_file_id))
        pool = context["pool"]
        intent = context.get("intent")
        matching = [j for j in context["jobs"] if intent and j["IntentID"] == intent["IntentID"]]
        latest = matching[-1] if matching else None
        confirmed = bool(
            latest and latest["State"] == "confirmed" and pool["PoolState"] == "active"
        )
        if latest and any(
            r.get("proof", {}).get("state") == "damaged"
            for r in json.loads(latest.get("ProvenanceJson", "{}")).get("reconciliations", [])
        ):
            confirmed = False
        return dict(
            pool_id=pool["PoolID"],
            epoch=pool["Epoch"],
            pool_state=pool["PoolState"],
            operation_id=(context.get("operation") or {}).get("OperationID"),
            operation_phase=(context.get("operation") or {}).get("Phase"),
            intent_id=intent["IntentID"] if intent else None,
            job_id=latest["JobID"] if latest else None,
            state=latest["State"] if latest else "waiting_destination",
            link=(
                f"https://docs.google.com/spreadsheets/d/{pool['IndexFileID']}"
                if confirmed
                else None
            ),
        )

    @bound_runtime
    def export(self, actor, kvk_no, index_file_id=None):
        self.authorize(actor, "export")
        context = self.pools.export_context(self.pools.resolve(kvk_no, index_file_id))
        pool, intent = context["pool"], context.get("intent")
        if not intent:
            raise SourceConflict("No complete accepted export intent exists for this season.")
        if pool["PoolState"] != "active" or pool["OwnerID"] is not None:
            raise SourceConflict("Pool admission is closed.")
        matching = [j for j in context["jobs"] if j["IntentID"] == intent["IntentID"]]
        if matching:
            # Zero provider calls and no generation loading for an exact confirmed no-op.
            previous = matching[-1]
            if (
                previous["State"] == "failed"
                and "attempts" in context
                and not any(a["JobID"] == previous["JobID"] for a in context["attempts"])
            ):
                self.coordinator.request_safe_retry(
                    previous["JobID"],
                    pool["AccountKey"],
                    expected_version=previous["Version"],
                    expected_epoch=pool["Epoch"],
                    actor=str(actor.user_id),
                    reason="Operator requested retry of proven pre-attempt failure",
                )
                return dict(job_id=previous["JobID"], state="queued", no_op=False)
            return dict(job_id=previous["JobID"], state=previous["State"], no_op=True)
        generation = compact_sheets_generation(
            self.generation_loader(intent["IntentID"], bytes.fromhex(intent["VectorHash"]))
        )
        result = capacity_for_snapshot(generation.manifest(), context)
        proof = dict(
            pool_id=pool["PoolID"],
            pool_version=pool["Version"],
            registration_hash=pool["RegistrationHash"],
            epoch=pool["Epoch"],
            generation_key=generation.key,
            manifest_hash=digest(generation.manifest()).hex(),
            parts=result.current_parts,
            required_files=result.required_files,
        )
        job = self.coordinator.enqueue(
            JobSpec(
                account=pool["AccountKey"],
                consumer="new_source",
                input_hash=bytes.fromhex(intent["VectorHash"]),
                destinations=tuple(
                    sorted((pool["IndexFileID"], *(s["FileID"] for s in context["slots"])))
                ),
                actor=str(actor.user_id),
                reason="Operator requested accepted complete export",
                kvk_no=kvk_no,
                intent_id=intent["IntentID"],
                epoch=pool["Epoch"],
                provenance=bounded_json(dict(output_preflight=proof)),
            )
        )
        return dict(job_id=str(job["JobID"]).lower(), state=job["State"], no_op=False)

    @bound_runtime
    def preview_rollover(self, actor, kvk_no, new_kvk, *, reason, index_file_id=None):
        self.authorize(actor, "rollover_preview")
        plan = self.rollover.preview(
            self.pools.resolve(kvk_no, index_file_id), new_kvk, actor=actor, reason=reason
        )
        return self._preview(actor, "rollover_confirm", plan)

    @bound_runtime
    def confirm(self, actor, token):
        token = str(UUID(str(token)))
        # Confirmed operations outlive the disposable preview and process. A duplicate
        # confirmation can read its outcome, but cannot acquire new authority or work.
        self.authorize(actor, "rollover_confirm")
        try:
            durable = self.pools.operation(token)
        except SourceConflict:
            durable = None
        if durable is not None:
            if (durable["ConfirmedBy"], durable["GuildID"], durable["ChannelID"]) != tuple(
                str(v) for v in self._actor(actor)
            ):
                raise PermissionError("This operation belongs to another actor or channel.")
            return {
                k: durable[k]
                for k in (
                    "OperationID",
                    "State",
                    "Phase",
                    "OldKVK",
                    "NewKVK",
                    "OldEpoch",
                    "TargetEpoch",
                )
            }
        repair = self.coordinator.repair_receipt(token)
        if isinstance(repair, dict):
            self.authorize(actor, "export_rebuild")
            if (repair["actor"], repair["guild"], repair["channel"]) != tuple(
                str(v) for v in self._actor(actor)
            ):
                raise PermissionError("This repair belongs to another actor or channel.")
            return {k: repair[k] for k in ("job_id", "repair_id", "state")}
        with self._lock:
            row = self._previews.get(token)
            if row is None or row.actor != self._actor(actor):
                raise SourceConflict(
                    "Preview is unavailable after restart or belongs to another actor/channel."
                )
            self.authorize(actor, row.action)
            if self.now() >= row.expires:
                raise SourceConflict("Preview expired; review fresh identities and versions.")
            plan = json.loads(row.payload)
            if row.action == "rollover_confirm":
                durable = self.rollover.confirm(row.token, plan)
                return {
                    k: durable[k]
                    for k in (
                        "OperationID",
                        "State",
                        "Phase",
                        "OldKVK",
                        "NewKVK",
                        "OldEpoch",
                        "TargetEpoch",
                    )
                }
            if row.action == "export_rebuild":
                return self.coordinator.admit_repair(row.token, plan)
            raise SourceConflict("Unsupported confirmation.")

    @bound_runtime
    def reconcile(self, actor, job_id):
        self.authorize(actor, "export_reconcile")
        job_id = str(UUID(str(job_id)))
        try:
            operation = self.pools.operation(job_id)
        except SourceConflict:
            operation = None
        if operation is not None:
            snapshot = self.pools.operation_snapshot(job_id)
            proof = self.reconciler.probe_rollover(deepcopy(snapshot))
            outcome = self.pools.reconcile_complete(snapshot, proof, actor=str(actor.user_id))
            return {
                k: outcome[k]
                for k in (
                    "OperationID",
                    "State",
                    "Phase",
                    "OldKVK",
                    "NewKVK",
                    "OldEpoch",
                    "TargetEpoch",
                )
            }
        snapshot = self.coordinator.operator_snapshot(str(UUID(str(job_id))))
        if snapshot["job"]["ConsumerKind"] != "new_source":
            raise SourceConflict("Use the owning consumer's reconciliation workflow.")
        proof = self.reconciler.probe(deepcopy(snapshot))
        if any(s["State"] == "retired" for s in snapshot.get("pool", {}).get("slots", [])):
            if self.retirement_recovery is None:
                raise SourceConflict("Explicit retirement recovery adapter is not composed.")
            self.retirement_recovery.resume(snapshot, proof, actor=str(actor.user_id))
            # Recovery revoked its provider owner. Re-probe the fresh durable snapshot;
            # never relabel a proof from before the clear/version changes.
            snapshot = self.coordinator.operator_snapshot(str(UUID(str(job_id))))
            proof = self.reconciler.probe(deepcopy(snapshot))
        # Provider reads and positive termination verification have returned before SQL.
        return self.coordinator.reconcile_operator(snapshot, proof, actor=str(actor.user_id))

    @bound_runtime
    def preview_rebuild(self, actor, job_id, *, reason):
        self.authorize(actor, "export_rebuild")
        if not reason or not reason.strip() or len(reason.encode("utf-16-le")) > 2048:
            raise ValueError("A bounded repair reason is required.")
        snapshot = self.coordinator.operator_snapshot(str(UUID(str(job_id))))
        proof = self.reconciler.probe(deepcopy(snapshot))
        if (
            snapshot["job"]["State"] != "confirmed"
            or proof.get("state") != "damaged"
            or proof.get("snapshot_hash") != digest(snapshot).hex()
            or proof.get("writer_terminated") is not True
            or not proof.get("evidence_id")
        ):
            raise SourceConflict(
                "Repair requires confirmed damage and exact old-writer termination."
            )
        pool_context = snapshot["pool"]
        pool = pool_context["pool"]
        if pool["IndexFileID"] in proof.get("damaged_files", []):
            raise SourceConflict("A damaged index requires explicit registration retirement.")
        job = snapshot["job"]
        generation = compact_sheets_generation(
            self.generation_loader(job["IntentID"], bytes.fromhex(job["InputHash"]))
        )
        old_parts = {p["FileID"] for p in snapshot["parts"] if p["Role"] != "index"}
        result = capacity_for_snapshot(
            generation.manifest(), pool_context, extra_quarantined=old_parts
        )
        preflight = dict(
            pool_id=pool["PoolID"],
            pool_version=pool["Version"],
            registration_hash=pool["RegistrationHash"],
            epoch=pool["Epoch"],
            generation_key=generation.key,
            manifest_hash=digest(generation.manifest()).hex(),
            parts=result.current_parts,
            required_files=result.required_files,
        )
        return self._preview(
            actor,
            "export_rebuild",
            dict(
                snapshot=snapshot,
                proof=proof,
                actor=str(actor.user_id),
                guild=str(actor.guild_id),
                channel=str(actor.channel_id),
                reason=reason.strip(),
                output_preflight=preflight,
            ),
        )

    @staticmethod
    def summary(row):
        if isinstance(row, Preview):
            payload = json.loads(row.payload)
            pool = payload.get("snapshot", {}).get("pool")
            if row.action == "rollover_confirm" and pool:
                files = [pool["IndexFileID"], *(s["FileID"] for s in payload["snapshot"]["slots"])]
                return (
                    f"Rollover preview {row.token}\nSeason {pool['ActiveKVK']} → {payload['new_choice']['KVK_NO']}; epoch {pool['Epoch']} → {pool['Epoch']+1}.\n"
                    "Closes admission, drains/reconciles old writers, then privately clears all listed files.\n"
                    + "\n".join(files)
                    + "\nConfirm within five minutes. Restart expires this preview."
                )
            return f"Repair preview / RepairID {row.token}\nOriginal job: {payload['snapshot']['job']['JobID']}\nReason: {payload['reason']}\nFresh physical attempt; original receipts retained. Confirm within five minutes."
        return "\n".join(f"{k}: {v}" for k, v in row.items() if v is not None)


def configured_operator_service():
    from services.export_runtime_composition import configured_runtime

    return configured_runtime().operator
