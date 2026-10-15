"""Guided export decisions backed by existing exact proof-consuming DAL actions."""

from copy import deepcopy
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity


def job_token(snapshot):
    # Resource versions can advance independently after a failed job released
    # them. They are freshly scoped and proof-checked at execution; they must not
    # falsely retire a pending safe-retry intent whose job CAS can still commit.
    durable = deepcopy({key: snapshot[key] for key in ("job", "attempts")})
    durable["job"].pop("Stalled", None)
    return digest(durable).hex()


def _unchanged(actual, token):
    if actual != token:
        raise SourceConflict("Export evidence changed. Review the current recovery choices.")


class ExportRecoveryAdapter:
    kind = "export_job"

    def __init__(self, discovery, coordinator, reconciler, *, retirement=None, rebuild_plan=None):
        self.discovery, self.coordinator, self.reconciler = discovery, coordinator, reconciler
        self.retirement, self.rebuild_plan = retirement, rebuild_plan

    def pending_recovery(self, *, after=None):
        return self.discovery.pending_jobs(after=after)

    def inspect(self, source_id):
        snapshot = self.discovery.job(source_id)
        job, attempts = snapshot["job"], snapshot["attempts"]
        provenance = json.loads(job["ProvenanceJson"])
        queued = provenance.get("safe_retry", {}).get("requested") is True
        history = provenance.get("reconciliations", [])
        damaged = bool(history and history[-1].get("proof", {}).get("state") == "damaged")
        repairs = []
        actions = {}
        explanation = "The export has not reached a verified terminal outcome. Its current reservation and attempt evidence are retained."
        if job["State"] == "failed" and not attempts and not queued:
            actions["retry_unstarted"] = dict(
                label="Queue verified safe retry",
                check="Confirm that the input/configuration issue has been corrected and this retained export should be retried.",
                effect="Recheck that no export attempt exists, retain the same queue identity and input, and request normal fenced admission. No attempted provider write is replayed.",
            )
            explanation = "This export failed before creating a provider attempt. A retry can use its retained input after a fresh exact-state check."
        elif job["ConsumerKind"] == "new_source" and job["State"] in {"running", "uncertain"}:
            actions["verify_publication"] = dict(
                label="Verify & settle publication",
                check="Confirm that the bot should check this retained publication. Keep its registered Sheets and receipts intact while verification runs.",
                effect="Verify every old writer and current publication. If proven safe, finish clearing only retired, unreferenced slots, verify again and settle the exact outcome. Unknown writes remain held.",
            )
        elif job["ConsumerKind"] == "new_source" and job["State"] == "confirmed" and damaged:
            repairs = self.discovery.repairs(source_id)
            if repairs:
                explanation = "A separate repair export has been queued for this damaged publication. Its delivery and any new failure are monitored under that export; the original receipts are preserved."
            elif self.rebuild_plan is not None:
                actions["rebuild_damaged"] = dict(
                    label="Rebuild verified damage",
                    check="Confirm that this report should be rebuilt from its retained generation. Keep the registered files unchanged while the bot verifies the damage and available capacity.",
                    effect="Recheck original writer closure and damage, quarantine the old report parts and queue one new physical export with a durable repair identity. The original receipt remains intact.",
                )
                explanation = "The original export completed but its latest verified publication is damaged. A rebuild needs a fresh authority proof, retained source generation and safe output capacity."
        if queued:
            explanation = "The safe retry is recorded. Normal queue admission will take its original turn and acquire a fresh fence. This does not yet confirm delivery."
        resolved = job["State"] in {"confirmed", "cancelled", "coalesced"} or queued
        if job["State"] == "confirmed" and damaged:
            resolved = bool(repairs)
        if (
            job["State"] == "running"
            and provenance.get("safe_retry_history")
            and not job["Stalled"]
        ):
            resolved = True
            explanation = (
                "The requested retry has been admitted. Delivery remains monitored separately."
            )
        return (
            dict(
                title="Spreadsheet export recovery",
                outcome=job["State"],
                scan=job.get("KVK_NO"),
                explanation=explanation,
                actions=actions,
            ),
            job_token(snapshot),
            resolved,
        )

    def execute(self, source_id, action, token, actor, reason):
        snapshot = self.discovery.job(source_id)
        _unchanged(job_token(snapshot), token)
        job = snapshot["job"]
        if action == "retry_unstarted":
            if job["ConsumerKind"] == "new_source":
                self.discovery.registered_publication(source_id, self.coordinator)
            self.coordinator.request_safe_retry(
                source_id,
                self.discovery.account,
                expected_version=job["Version"],
                expected_epoch=job["PoolEpoch"],
                actor=actor,
                reason=reason,
            )
        elif action == "verify_publication" and job["ConsumerKind"] == "new_source":
            current = self.discovery.registered_publication(source_id, self.coordinator)
            if {k: v for k, v in job.items() if k != "Stalled"} != current["job"]:
                raise SourceConflict("Publication changed after review.")
            self._settle_publication(source_id, current, actor)
        elif action == "rebuild_damaged" and self.rebuild_plan is not None:
            self.discovery.registered_publication(source_id, self.coordinator)
            plan = self.rebuild_plan(source_id, reason)
            if {k: v for k, v in job.items() if k != "Stalled"} != plan["snapshot"]["job"]:
                raise SourceConflict("Publication changed while preparing its repair.")
            # The centre persists the initiating Discord admin; the downstream
            # audit uses the durable action identity for acknowledgement recovery.
            plan["actor"] = actor
            self.coordinator.admit_repair(identity(actor.removeprefix("recovery:")), plan)
        else:
            raise SourceConflict("This export recovery action is unavailable.")

    def _settle_publication(self, source_id, current, actor):
        proof = self.reconciler.probe(deepcopy(current))
        if any(s["State"] == "retired" for s in current.get("pool", {}).get("slots", [])):
            if self.retirement is None:
                raise SourceConflict("Retirement recovery is unavailable; reservations retained.")
            self.retirement.resume(current, proof, actor=actor)
            current = self.discovery.registered_publication(source_id, self.coordinator)
            proof = self.reconciler.probe(deepcopy(current))
        self.coordinator.reconcile_operator(current, proof, actor=actor)

    def reconcile(self, source_id, action):
        snapshot = self.discovery.job(source_id)
        provenance = json.loads(snapshot["job"]["ProvenanceJson"])
        actor = f"recovery:{action['ActionID']}"
        if action["ActionKind"] == "rebuild_damaged":
            receipt = self.coordinator.repair_receipt(action["ActionID"])
            if receipt is not None:
                repair = self.discovery.job(receipt["job_id"])["job"]
                original = json.loads(repair["ProvenanceJson"])["repair"]["snapshot"]["job"]
                if receipt["actor"] != actor or original["JobID"] != snapshot["job"]["JobID"]:
                    raise SourceConflict("Repair receipt does not belong to this recovery.")
                return "verified"
            if job_token(snapshot) != action["EvidenceHash"]:
                return "not_applied"
            self.execute(
                source_id, action["ActionKind"], action["EvidenceHash"], actor, action["Reason"]
            )
            return None
        history_key = {
            "retry_unstarted": "safe_retry_history",
            "verify_publication": "reconciliations",
        }.get(action["ActionKind"])
        if history_key is None:
            raise SourceConflict("Unknown export recovery action.")
        if any(item.get("actor") == actor for item in provenance.get(history_key, [])):
            return "verified"
        if (
            action["ActionKind"] == "verify_publication"
            and provenance.get("retirement_recovery", {}).get("actor") == actor
        ):
            # Resume only the original approved retirement operation, always with
            # fresh authority closure/request proofs. An unknown clear cannot pass.
            current = self.discovery.registered_publication(source_id, self.coordinator)
            self._settle_publication(source_id, current, actor)
            return None
        if job_token(snapshot) != action["EvidenceHash"]:
            # Consuming DAL actions compare the original durable job version under
            # their account lock. A changed receipt cannot accept the old intent.
            return "not_applied"
        self.execute(
            source_id, action["ActionKind"], action["EvidenceHash"], actor, action["Reason"]
        )
        return None  # Fresh independent read verifies the durable postcondition.


class RolloverRecoveryAdapter:
    kind = "export_rollover"

    def __init__(self, discovery, pools, reconciler):
        self.discovery, self.pools, self.reconciler = discovery, pools, reconciler

    def pending_recovery(self, *, after=None):
        return self.discovery.pending_rollovers(after=after)

    def inspect(self, source_id):
        snapshot = self.discovery.rollover(source_id, self.pools)
        operation = snapshot["operation"]
        request = json.loads(operation["ProgressJson"]).get("request", {})
        actions = {}
        if operation["State"] in {"running", "uncertain"} and request.get("phase") in {
            "setup_pending",
            "setup_verified",
        }:
            actions["verify_rollover"] = dict(
                label="Verify & finish rollover",
                check="Confirm that the bot should verify the recorded rollover. Keep the old and new season files unchanged during verification.",
                effect="Verify every original clear, final setup and terminated writer through the authority; finish only this exact confirmed rollover and release its reservations atomically.",
            )
        return (
            dict(
                title="Spreadsheet rollover recovery",
                outcome=operation["State"],
                explanation=f"Season {operation['OldKVK']} to {operation['NewKVK']}; retained phase: {operation['Phase']}. Completion requires the recorded phase journal and fresh authority verification.",
                actions=actions,
            ),
            digest(snapshot).hex(),
            operation["State"] == "completed",
        )

    def execute(self, source_id, action, token, actor, reason):
        if action != "verify_rollover":
            raise SourceConflict("Unknown rollover recovery action.")
        snapshot = self.discovery.rollover(source_id, self.pools)
        _unchanged(digest(snapshot).hex(), token)
        proof = self.reconciler.probe_rollover(deepcopy(snapshot))
        self.pools.reconcile_complete(snapshot, proof, actor=actor)

    def reconcile(self, source_id, action):
        snapshot = self.discovery.rollover(source_id, self.pools)
        operation = snapshot["operation"]
        progress = json.loads(operation["ProgressJson"])
        actor = f"recovery:{action['ActionID']}"
        if (
            operation["State"] == "completed"
            and progress.get("reconciliation", {}).get("actor") == actor
        ):
            return "verified"
        if digest(snapshot).hex() != action["EvidenceHash"]:
            return "not_applied"
        self.execute(
            source_id, action["ActionKind"], action["EvidenceHash"], actor, action["Reason"]
        )
        return None
