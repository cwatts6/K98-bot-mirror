"""Discord recovery adapter: private decisions via authority; retained spool via Bot."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_failure_diagnostics import replacement_decision_context
from services.export_recovery_service import job_token, skipped_export_verified
from services.export_replacement_delivery import ReplacementDelivery
from services.export_replacement_delivery_dal import ReplacementDeliveryDAL

STEPS = frozenset(
    (
        "isolate_targets",
        "choose_replacements",
        "verify_replacements",
        "finish_replacement_check",
        "discard_replacement_check",
        "activate_replacements",
        "publish_replacement",
        "retire_failed_export",
        "allow_next_export",
    )
)


class ReplacementRecoveryAdapter:
    kind = "export_job"

    def __init__(self, base, *, runtime, store):
        self.base, self.runtime, self.store = base, runtime, store
        self.client = runtime.client

    def pending_recovery(self, *, after=None):
        return self.base.pending_recovery(after=after)

    def published_outputs(self, *, after=None):
        return self.base.published_outputs(after=after)

    def inspect(self, job_id):
        return self._inspect(job_id, ())

    def _inspect(self, job_id, ancestors):
        if job_id in ancestors or len(ancestors) >= 32:
            raise SourceConflict(
                "Repair ancestry cannot be verified; original history is retained."
            )
        snapshot = self.base.discovery.job(job_id)
        if snapshot["job"]["ConsumerKind"] in {"scan_data", "all_kvk"} and (
            snapshot.get("legacy_closeout", False)
            or (snapshot["job"]["State"] == "uncertain" and snapshot["streams"])
        ):
            result = self.client.failed_export_recovery(job_id, "inspect")
            return result["evidence"], result["token"], result["resolved"]
        # A saved retirement remains authoritative even if shared destinations
        # are subsequently isolated. Only private receipt verification may
        # resolve it; a malformed/unverifiable marker must not enable replacement.
        if "failed_export_retired" in json.loads(snapshot["job"]["ProvenanceJson"]):
            result = self.client.failed_export_recovery(job_id, "inspect")
            return (
                self._with_parent(snapshot, result["evidence"]),
                result["token"],
                result["resolved"],
            )
        if skipped_export_verified(snapshot):
            return self.base.inspect(job_id)
        if (
            snapshot["job"]["State"] == "failed"
            and snapshot["streams"]
            and snapshot["job"]["ConsumerKind"] in {"scan_data", "all_kvk"}
            and not snapshot.get("isolated_targets")
        ):
            result = self.client.failed_export_recovery(job_id, "inspect")
            return result["evidence"], result["token"], result["resolved"]
        if snapshot.get("isolated_targets") or (
            snapshot["job"]["State"] in {"running", "uncertain"} and snapshot["streams"]
        ):
            result = self.client.replacement_recovery(job_id, "inspect")
            result["evidence"]["failure_context"] = replacement_decision_context(
                snapshot["job"], self.runtime.registration.value()
            )
            original, _, _ = self.base.inspect(job_id)
            for action in ("verify_publication", "skip_unstarted"):
                if (
                    action in original["actions"]
                    and (action != "verify_publication" or not snapshot.get("isolated_targets"))
                    and not (result["evidence"].get("delivery") or {}).get("job_id")
                ):
                    result["evidence"]["actions"][action] = original["actions"][action]
            return (
                self._with_parent(snapshot, result["evidence"]),
                result["token"],
                result["resolved"],
            )
        evidence, token, resolved = self.base.inspect(job_id)
        repairs = [
            link
            for link in evidence.get("recovery_links", [])
            if link["label"] == "Review repair export"
        ]
        if repairs:
            members = self.base.discovery.repairs(job_id)
            if len(members) > 32:
                raise SourceConflict(
                    "Repair membership exceeds the verification bound; history is retained."
                )
            children = [self._inspect(child["JobID"], (*ancestors, job_id)) for child in members]
            resolved = bool(children) and all(
                done
                and child.get("outcome")
                in {"confirmed", "replacement_delivered", "repair_delivered"}
                for child, _, done in children
            )
            if resolved:
                evidence.update(
                    outcome="repair_delivered",
                    explanation="The separate repair and any verified replacement successor have confirmed delivery. The original outcome and receipts remain unchanged.",
                    actions={},
                )
                token = digest([token, [value for _, value, _ in children]]).hex()
            else:
                evidence["explanation"] = (
                    "A separate recovery export still needs verified delivery or further repair. Use Review repair export; the original incident remains open and its history is unchanged."
                )
        return evidence, token, resolved

    @staticmethod
    def _with_parent(snapshot, evidence):
        original = (
            json.loads(snapshot["job"]["ProvenanceJson"])
            .get("repair", {})
            .get("snapshot", {})
            .get("job", {})
        )
        if original.get("JobID"):
            evidence.setdefault("recovery_links", []).append(
                dict(
                    label="Return to original export",
                    kind="export_job",
                    source_id=original["JobID"],
                )
            )
        return evidence

    def input_fields(self, job_id, action, token):
        return self.client.replacement_recovery(job_id, "fields", step=action, token=token)

    def validate_input(self, job_id, action, token, payload):
        return self.client.replacement_recovery(
            job_id, "validate", step=action, token=token, payload=payload
        )

    def _delivery(self):
        def authority_verification_required(*_):
            raise SourceConflict("Final replacement verification requires the private authority.")

        return ReplacementDelivery(
            dal=ReplacementDeliveryDAL(self.runtime.connect, self.runtime.dal),
            discovery=self.base.discovery,
            store=self.store,
            source_plan=self.runtime.replacement_source_plan,
            verify_delivery=authority_verification_required,
        )

    def execute(self, job_id, action, token, actor, reason, *, payload=None):
        if action in {"retire_failed_export", "allow_next_export"}:
            return self.client.failed_export_recovery(
                job_id,
                "execute",
                step=action,
                token=token,
                actor=actor,
                reason=reason,
                payload=payload,
            )
        if action not in STEPS:
            if action in {"verify_publication", "skip_unstarted"}:
                original_token = job_token(self.base.discovery.job(job_id))
                evidence, current, _ = self.inspect(job_id)
                if current != token or action not in evidence["actions"]:
                    raise SourceConflict(
                        "Export evidence changed. Review the current recovery choices."
                    )
                token = original_token
            return self.base.execute(job_id, action, token, actor, reason)
        if action == "publish_replacement":
            # The authority validates the reviewed state and returns only its
            # sealed activation. The Bot never supplies a replacement registry.
            activation = self.client.replacement_recovery(job_id, "context", token=token)
            with self.runtime.reconfigure(recovery=True):
                self.runtime.refresh_replacement_registration()
                self._delivery().execute(job_id, activation, action, actor=actor, reason=reason)
            from services.export_coordination_service import wake_exports

            wake_exports()
        elif action == "activate_replacements":
            with self.runtime.reconfigure(recovery=True):
                self.client.replacement_recovery(
                    job_id,
                    "execute",
                    step=action,
                    token=token,
                    actor=actor,
                    reason=reason,
                    payload=payload,
                )
                self.runtime.refresh_replacement_registration()
        else:
            self.client.replacement_recovery(
                job_id,
                "execute",
                step=action,
                token=token,
                actor=actor,
                reason=reason,
                payload=payload,
            )

    def reconcile(self, job_id, action):
        if action["ActionKind"] not in STEPS:
            if action["ActionKind"] in {"verify_publication", "skip_unstarted"}:
                original_token = job_token(self.base.discovery.job(job_id))
                _, current, _ = self.inspect(job_id)
                if current == action["EvidenceHash"]:
                    action = dict(action, EvidenceHash=original_token)
            return self.base.reconcile(job_id, action)
        # Only bounded immutable action fields cross IPC; SQL driver dates and
        # diagnostic bodies never become caller-authored authority evidence.
        document = {
            k: action.get(k)
            for k in ("ActionID", "ActionKind", "EvidenceHash", "Reason", "InputJson")
        }
        if action["ActionKind"] in {"retire_failed_export", "allow_next_export"}:
            return self.client.failed_export_recovery(job_id, "reconcile", recovery_action=document)
        if action["ActionKind"] == "publish_replacement":
            # Reconciliation on the authority reads the atomic queue receipt.
            # If none exists, only the Bot's registered spool owner may retry
            # this exact intent after a fresh evidence comparison.
            result = self.client.replacement_recovery(job_id, "inspect")
            if result["token"] == action["EvidenceHash"]:
                self.execute(
                    job_id,
                    action["ActionKind"],
                    action["EvidenceHash"],
                    "recovery:" + action["ActionID"],
                    action["Reason"],
                )
        result = self.client.replacement_recovery(job_id, "reconcile", recovery_action=document)
        if action["ActionKind"] == "activate_replacements" and result == "verified":
            with self.runtime.reconfigure(recovery=True):
                self.runtime.refresh_replacement_registration()
        return result
