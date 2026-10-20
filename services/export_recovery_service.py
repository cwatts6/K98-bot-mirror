"""Guided export decisions backed by existing exact proof-consuming DAL actions."""

from copy import deepcopy
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.export_failure_diagnostics import recovery_failure_context


def job_token(snapshot):
    # Resource versions can advance independently after a failed job released
    # them. They are freshly scoped and proof-checked at execution; they must not
    # falsely retire a pending safe-retry intent whose job CAS can still commit.
    durable = deepcopy({key: snapshot[key] for key in ("job", "attempts", "streams")})
    durable["job"].pop("Stalled", None)
    if snapshot["job"]["ConsumerKind"] == "new_source":
        durable["season"] = snapshot.get("season")
    if snapshot.get("isolated_targets"):
        durable["isolated_targets"] = snapshot["isolated_targets"]
    return digest(durable).hex()


def _unchanged(actual, token):
    if actual != token:
        raise SourceConflict("Export evidence changed. Review the current recovery choices.")


class PublicationCheckUnavailable(SourceConflict):
    """Preparation failed before repair admission, settlement or retirement."""


def skipped_export_verified(snapshot):
    job = snapshot["job"]
    return bool(
        json.loads(job["ProvenanceJson"]).get("export_skipped")
        and job["ConsumerKind"] in {"scan_data", "all_kvk"}
        and job["State"] in {"failed", "cancelled"}
        and not snapshot["attempts"]
        and not snapshot["streams"]
        and not any(r["ActiveJobID"] == job["JobID"] for r in snapshot["resources"])
    )


class ExportRecoveryAdapter:
    kind = "export_job"

    def __init__(self, discovery, coordinator, reconciler, *, retirement=None, rebuild_plan=None):
        self.discovery, self.coordinator, self.reconciler = discovery, coordinator, reconciler
        self.retirement, self.rebuild_plan = retirement, rebuild_plan

    def pending_recovery(self, *, after=None):
        return self.discovery.pending_jobs(after=after)

    def published_outputs(self, *, after=None):
        return self.discovery.published_outputs(after=after)

    def inspect(self, source_id):
        snapshot = self.discovery.job(source_id)
        job, attempts = snapshot["job"], snapshot["attempts"]
        provenance = json.loads(job["ProvenanceJson"])
        queued = provenance.get("safe_retry", {}).get("requested") is True
        history = provenance.get("reconciliations", [])
        damaged = bool(history and history[-1].get("proof", {}).get("state") == "damaged")
        absent = bool(history and history[-1].get("proof", {}).get("state") == "absent")
        repairs = []
        actions = {}
        explanation = "The export has not reached a verified terminal outcome. Its current reservation and attempt evidence are retained."
        if job["State"] == "failed" and not attempts and not snapshot["streams"] and not queued:
            actions["retry_unstarted"] = dict(
                label="Queue verified safe retry",
                check="Confirm that the input/configuration issue has been corrected and this retained export should be retried.",
                effect="Recheck that no export attempt or execution stream exists, retain the same queue identity and input, and request normal fenced admission. This queues work; delivery is verified separately. No attempted provider write is replayed.",
            )
            explanation = "This export failed before creating a provider attempt. A retry can use its retained input after a fresh exact-state check."
        elif job["State"] == "failed" and not attempts and snapshot["streams"]:
            explanation = "This export has execution-stream evidence. It cannot use an unstarted retry or skip; its original execution must be reconciled first. No new provider execution is authorized by this incident."
        elif job["ConsumerKind"] == "new_source" and job["State"] in {"running", "uncertain"}:
            actions["verify_publication"] = dict(
                label="Verify & settle publication",
                check="Confirm that the bot should check this retained publication. Keep its registered Sheets and receipts intact while verification runs.",
                effect="Verify every old writer and current publication. If proven safe, finish clearing only retired, unreferenced slots, verify again and settle the exact outcome. Unknown writes remain held.",
            )
        elif job["ConsumerKind"] == "new_source" and (
            (job["State"] == "confirmed" and damaged) or (job["State"] == "failed" and absent)
        ):
            repairs = self.discovery.repairs(source_id)
            if repairs:
                explanation = (
                    "The separate recovery export has a confirmed delivery. The original attempt and receipts are preserved."
                    if all(repair["State"] == "confirmed" for repair in repairs)
                    else "A separate recovery export is awaiting verified delivery. Use Review repair export for progress or any new failure; this original incident stays open until delivery is confirmed. The original attempt and receipts are preserved."
                )
            elif self.rebuild_plan is not None:
                actions["retry_absent" if absent else "rebuild_damaged"] = dict(
                    label="Retry verified absent export" if absent else "Rebuild verified damage",
                    check="Confirm that this retained report should be exported. Keep the registered files unchanged while the bot verifies the outcome and available capacity.",
                    effect="Recheck old writer closure and current publication. Require proof of no delayed write for an absent export; preserve the original attempt and quarantine, then queue one separate physical export with a durable repair identity.",
                )
                explanation = (
                    "The attempted publication was verified absent. A separate retry requires fresh proof that no mutation was dispatched, retained input and safe output capacity."
                    if absent
                    else "The original export completed but its latest verified publication is damaged. A rebuild needs a fresh authority proof, retained source generation and safe output capacity."
                )
        if job["State"] == "confirmed" and not damaged:
            explanation = "The export has a confirmed delivery outcome. No repair is required for this recorded outcome; this is not a fresh check of the current spreadsheet contents."
            if job["ConsumerKind"] == "new_source" and attempts:
                actions["verify_publication"] = dict(
                    label="Check published output",
                    check="Confirm this is the retained output you want checked. Keep its registered files unchanged during verification.",
                    effect="Read the registered publication and compare it with its retained receipt and contents. Record verified content damage for a separate repair decision. Missing ownership, permissions or pointer evidence never authorises a rebuild.",
                )
        if queued:
            explanation = "The safe retry is recorded. Normal queue admission will take its original turn and acquire a fresh fence. This does not yet confirm delivery."
        resolved = job["State"] in {"confirmed", "cancelled", "coalesced"} or queued
        if (job["State"] == "confirmed" and damaged) or (job["State"] == "failed" and absent):
            resolved = bool(repairs) and all(repair["State"] == "confirmed" for repair in repairs)
        if (
            job["State"] == "running"
            and provenance.get("safe_retry_history")
            and not job["Stalled"]
        ):
            resolved = True
            explanation = (
                "The requested retry has been admitted. Delivery remains monitored separately."
            )
        if provenance.get("export_skipped"):
            resolved = skipped_export_verified(snapshot)
            actions.clear()
            explanation = (
                "Admin chose to skip this export. Its input and history are preserved, no provider execution occurred, "
                "and its reservations are released. SQL data is unchanged; the spreadsheet may remain out of date."
                if resolved
                else "The recorded skip does not match its current evidence. The incident remains open."
            )
        elif (
            job["ConsumerKind"] in {"scan_data", "all_kvk"}
            and job["State"] in {"waiting", "ready", "running", "failed", "uncertain"}
            and not attempts
            and not snapshot["streams"]
            and not queued
        ):
            actions["skip_unstarted"] = dict(
                label="Keep SQL; skip queued export",
                check="Confirm you accept no spreadsheet update from this queued export. SQL data and retained files stay in place; the spreadsheet may remain out of date.",
                effect="Verify there is no provider attempt or execution stream, fence any stale worker, retain the original job and input, and release only its exact reservations. No provider write or SQL import is replayed.",
            )
        replacement_required = (
            bool(snapshot.get("isolated_targets"))
            and not (provenance.get("export_skipped") and resolved)
            and job["State"] not in {"cancelled", "coalesced"}
        )
        if replacement_required:
            resolved = False
            actions = {key: value for key, value in actions.items() if key == "skip_unstarted"}
            explanation = (
                "This export references permanently isolated spreadsheet files. Its input and original "
                "history are retained, and it cannot enter provider execution or block unrelated queue "
                "admission. A queued retry does not resolve this incident. Verified replacement files "
                "and a separately verified publication are required; no delivery is being claimed."
            )
        if "retry_unstarted" in actions and job["ConsumerKind"] == "new_source":
            season = snapshot.get("season")
            if not season or (season["SourceKey"], season["SeasonState"]) != (
                job["SourceKey"],
                "open",
            ):
                actions.pop("retry_unstarted")
                explanation = (
                    "This export's season is not open with its original source. A retry cannot "
                    "be admitted. Its input and history are retained for season recovery."
                )
        evidence = dict(
            title="Spreadsheet export recovery",
            outcome=(
                "replacement_required"
                if replacement_required
                else (
                    "export_skipped"
                    if provenance.get("export_skipped") and resolved
                    else job["State"]
                )
            ),
            season=job.get("KVK_NO"),
            failure_context=recovery_failure_context(job, provenance),
            recovery_links=[
                dict(label="Review repair export", kind="export_job", source_id=repair["JobID"])
                for repair in sorted(
                    repairs, key=lambda repair: (repair["CreatedUTC"], repair["JobID"])
                )[:3]
            ],
            explanation=explanation,
            actions=actions,
        )
        context = getattr(self.discovery, "decision_context", None)
        if callable(context):
            details = context(snapshot)
            if isinstance(details, dict):
                evidence.update(details)
        repair = provenance.get("repair", {}).get("snapshot", {}).get("job", {})
        if repair.get("JobID"):
            evidence["recovery_links"].append(
                dict(
                    label="Return to original export", kind="export_job", source_id=repair["JobID"]
                )
            )
        return evidence, job_token(snapshot), resolved

    def execute(self, source_id, action, token, actor, reason):
        snapshot = self.discovery.job(source_id)
        _unchanged(job_token(snapshot), token)
        job = snapshot["job"]
        if snapshot.get("isolated_targets") and action != "skip_unstarted":
            raise SourceConflict("Permanently isolated targets require verified replacements.")
        if action == "skip_unstarted":
            self.coordinator.skip_unstarted(
                source_id,
                self.discovery.account,
                storage_owner=self.discovery.storage_owner,
                expected_version=job["Version"],
                actor=actor,
                reason=reason,
            )
        elif action == "retry_unstarted":
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
            try:
                current = self.discovery.registered_publication(source_id, self.coordinator)
                if {k: v for k, v in job.items() if k != "Stalled"} != current["job"]:
                    raise SourceConflict("Publication changed after review.")
            except Exception as exc:
                raise PublicationCheckUnavailable(
                    "Publication registration could not be verified; no settlement was attempted."
                ) from exc
            self._settle_publication(source_id, current, actor)
        elif action in {"rebuild_damaged", "retry_absent"} and self.rebuild_plan is not None:
            try:
                self.discovery.registered_publication(source_id, self.coordinator)
                plan = self.rebuild_plan(source_id, reason)
                if {k: v for k, v in job.items() if k != "Stalled"} != plan["snapshot"]["job"]:
                    raise SourceConflict("Publication changed while preparing its repair.")
                expected_outcome = "absent" if action == "retry_absent" else "damaged"
                if plan["proof"].get("state") != expected_outcome:
                    raise SourceConflict(
                        "Publication outcome changed. Review its current recovery."
                    )
            except Exception as exc:
                raise PublicationCheckUnavailable(
                    "Repair preparation could not be verified; no export was admitted."
                ) from exc
            # The centre persists the initiating Discord admin; the downstream
            # audit uses the durable action identity for acknowledgement recovery.
            plan["actor"] = actor
            self.coordinator.admit_repair(identity(actor.removeprefix("recovery:")), plan)
        else:
            raise SourceConflict("This export recovery action is unavailable.")

    def _settle_publication(self, source_id, current, actor):
        try:
            proof = self.reconciler.probe(deepcopy(current))
        except Exception as exc:
            # This producer can only observe/close journals. No retirement or
            # outcome settlement has been entered, so a refused check must not
            # strand its admin action ahead of the separate replacement path.
            raise PublicationCheckUnavailable(
                "Publication could not be proven; original ownership and outcomes remain unchanged."
            ) from exc
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
        if action["ActionKind"] == "skip_unstarted":
            receipt = provenance.get("export_skipped", {})
            if receipt.get("actor") == actor and receipt.get("reason") == action["Reason"]:
                return "verified" if skipped_export_verified(snapshot) else None
            if job_token(snapshot) != action["EvidenceHash"]:
                return "not_applied"
            self.execute(
                source_id, "skip_unstarted", action["EvidenceHash"], actor, action["Reason"]
            )
            return None
        if action["ActionKind"] in {"rebuild_damaged", "retry_absent"}:
            receipt = self.coordinator.repair_receipt(action["ActionID"])
            if receipt is not None:
                repair = self.discovery.job(receipt["job_id"])["job"]
                original = json.loads(repair["ProvenanceJson"])["repair"]["snapshot"]["job"]
                if receipt["actor"] != actor or original["JobID"] != snapshot["job"]["JobID"]:
                    raise SourceConflict("Repair receipt does not belong to this recovery.")
                return "verified"
            if job_token(snapshot) != action["EvidenceHash"]:
                return "not_applied"
            if (
                action.get("State") == "unknown"
                and json.loads(action.get("ResultJson") or "{}").get("error_type")
                == "PublicationCheckUnavailable"
            ):
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
        if (
            action["ActionKind"] == "verify_publication"
            and action.get("State") == "unknown"
            and json.loads(action.get("ResultJson") or "{}").get("error_type")
            == "PublicationCheckUnavailable"
        ):
            # Only the durably recorded initial read refusal can finish this
            # way. A crash without that marker, or an unknown SQL/retirement
            # outcome, must continue through its own receipt reconciliation.
            return "not_applied"
        self.execute(
            source_id, action["ActionKind"], action["EvidenceHash"], actor, action["Reason"]
        )
        return None  # Fresh independent read verifies the durable postcondition.


class RolloverRecoveryAdapter:
    kind = "export_rollover"

    def __init__(self, discovery, pools, reconciler, *, rollover=None):
        self.discovery, self.pools, self.reconciler = discovery, pools, reconciler
        self.rollover = rollover

    def pending_recovery(self, *, after=None):
        return self.discovery.pending_rollovers(after=after)

    def inspect(self, source_id):
        snapshot = self.discovery.rollover(source_id, self.pools)
        operation = snapshot["operation"]
        request = json.loads(operation["ProgressJson"]).get("request", {})
        actions = {}
        links = []
        context = snapshot.get("pool", {})
        pending = [
            job
            for job in context.get("jobs", [])
            if job["State"] in {"running", "uncertain", "ready", "waiting"}
        ]
        if operation["State"] == "closing":
            links = [
                dict(label="Review old-season export", kind="export_job", source_id=j["JobID"])
                for j in pending[:3]
            ]
        if (
            self.rollover is not None
            and operation["State"] in {"closing", "ready"}
            and operation.get("OwnerID") is None
            and not pending
            and not any(
                row["DeliveryState"] in {"claimed", "uncertain"}
                for row in context.get("legacy_receipts", [])
            )
        ):
            actions["continue_unstarted_rollover"] = dict(
                label="Continue waiting rollover",
                check=f"Confirm the original season {operation['OldKVK']} to {operation['NewKVK']} rollover should proceed. Its registered old-season files will be made private and cleared, then prepared for the new season. Preserve any copies you still need before confirming.",
                effect="Verify the old writers and their outcomes, then use the original queued operation and exact registered files. Account admission and ownership are checked again. Each provider phase is recorded; an uncertain phase stops for its own recovery rather than being repeated.",
            )
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
                recovery_links=links,
            ),
            digest(snapshot).hex(),
            operation["State"] == "completed",
        )

    def execute(self, source_id, action, token, actor, reason):
        if action == "continue_unstarted_rollover":
            evidence, current, resolved = self.inspect(source_id)
            _unchanged(current, token)
            if resolved or action not in evidence["actions"]:
                raise SourceConflict("The original rollover is no longer waiting for admission.")
            return self.rollover.advance(source_id)
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
        if action["ActionKind"] == "continue_unstarted_rollover":
            # The immutable operation is the idempotency identity. Admission
            # CAS permits one owner; advance refuses all already-owned states.
            # A lost intent/queue reply may resume only its still-unowned entry.
            if operation["State"] in {"completed", "running", "uncertain"}:
                # Admission is verified; incident resolution still requires
                # completed. An uncertain phase receives its own repair choice.
                return "verified"
            if operation["State"] in {"closing", "ready"} and operation.get("OwnerID") is None:
                self.rollover.advance(source_id)
                return None
            return "not_applied"
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
