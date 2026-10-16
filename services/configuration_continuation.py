"""Guided fresh configuration retry after verified rollback, with durable handoff."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.producer_recovery_intent import configuration_retry_intent


class ConfigurationContinuation:
    kind = "configuration_continuation"
    observe_healthy = False

    def __init__(self, dal, producer, runner=None):
        self.dal, self.producer = dal, producer
        self.runner = runner or self._run

    def pending_recovery(self, *, after=None):
        return self.dal.pending(after)

    def inspect(self, source_id):
        state = self.dal.snapshot(source_id)
        marker, child = state["marker"], state["child"]
        actions, links = {}, []
        evidence = dict(
            title="Configuration continuation",
            outcome="choose_continuation",
            explanation="The original atomic configuration attempt rolled back and its reservation is verified released. Choose whether to read current registered configuration and publish it, or retain the prior configuration.",
            actions=actions,
            recovery_links=links,
        )
        resolved = bool(marker and marker.get("choice") == "keep_prior")
        if resolved:
            evidence.update(
                outcome="prior_configuration_retained",
                explanation="The admin confirmed retaining the prior configuration. No new publication or cache refresh is claimed.",
            )
        elif marker and not child:
            evidence.update(
                outcome="checking_attempt",
                explanation="The confirmed configuration attempt is being reconciled. No second write can be dispatched while its outcome is unknown.",
            )
        elif child:
            child_evidence, _, child_resolved = self.producer.inspect(child["PreparationID"])
            if child_evidence["outcome"] != "configuration_cancelled":
                evidence.update(
                    outcome=child_evidence["outcome"], explanation=child_evidence["explanation"]
                )
                links.append(
                    dict(
                        label="Review configuration result",
                        kind=self.producer.kind,
                        source_id=child["PreparationID"],
                    )
                )
                resolved = child_resolved
            else:
                child = None
        if not resolved and (not marker or (state["child"] and child is None)):
            actions.update(
                retry_configuration=dict(
                    label="Read & publish current config",
                    review_details=True,
                    review_title="Review configuration sources and outputs",
                    review_description="Open the registered source sheets and verify the configuration you want published now. Review the output destinations, then continue to a separate confirmation.",
                    check="Review every current configuration source and destination page. Verify the source sheets contain the configuration you want published now. Confirm a fresh read and atomic publication; this does not rerun the scan import.",
                    effect="Save this exact approval, read the registered configuration, publish configuration and targets in one transaction, then verify the durable result. An uncertain attempt is reconciled before another retry.",
                ),
                keep_prior=dict(
                    label="Keep prior configuration",
                    check="Confirm the prior configuration should remain in use and this failed import should not be retried. This does not claim that configuration or caches are current.",
                    effect="Record and verify your decision against the closed original attempt. No configuration write or unrelated reservation release occurs.",
                ),
            )
            if state["blocker"]:
                actions.pop("retry_configuration")
                evidence.update(
                    outcome="waiting_for_access",
                    explanation="The closed configuration attempt is safe to retain. Fresh publication is waiting for another operation. Review the blocking operation, then Recheck to restore the retry choice after verified settlement.",
                )
                owner = state["blocker"].get("owner")
                if owner:
                    links.append(
                        dict(
                            label="Review blocking operation",
                            kind=owner["kind"],
                            source_id=owner["source_id"],
                        )
                    )
        return evidence, digest(state).hex(), resolved

    def review_details(self, source_id, action, token):
        from services.producer_recovery_review import registration_review

        state = self.dal.snapshot(source_id)
        evidence, current, resolved = self.inspect(source_id)
        if resolved or token != current or action not in evidence["actions"]:
            raise SourceConflict("Configuration review changed; reopen the incident.")
        fields = registration_review(
            dict(
                preparation=state["root"],
                current_registration=state["current"]["scan_data"],
                producer=dict(
                    inputs={"operation": "Fresh configuration read; no scan import replay"}
                ),
            )
        )
        source = state["current"]["config"]
        # Reuse complete bounded pages and validated links for the input registration too.
        fields.extend(
            registration_review(
                dict(
                    preparation={"RequestJson": json.dumps({"request": {"config": source}})},
                    current_registration=source,
                    producer=dict(inputs={"operation": "Configuration source registration"}),
                )
            )
        )
        return fields

    def execute(self, source_id, action, token, actor, reason):
        if not actor.startswith("recovery:"):
            raise SourceConflict("Confirmed admin action required.")
        action_id = identity(actor.removeprefix("recovery:"))
        with self.dal.serialized(source_id):
            evidence, current, resolved = self.inspect(source_id)
            if resolved or current != token or action not in evidence["actions"]:
                raise SourceConflict("Configuration evidence changed; review the current incident.")
            state = self.dal.snapshot(source_id)
            marker = dict(
                action=action_id,
                token=token,
                reason=reason,
                choice="keep_prior" if action == "keep_prior" else "retry",
                configuration=state["current"],
            )
            self.dal.record(source_id, token, marker)
            if action == "keep_prior":
                return
            from services.legacy_export_snapshot_service import use_runtime

            with use_runtime(self.dal.runtime), configuration_retry_intent(action_id, source_id):
                self.runner()

    def reconcile(self, source_id, action):
        if action["ActionKind"] not in {"retry_configuration", "keep_prior"}:
            raise SourceConflict("Unsupported configuration continuation action.")
        choice = "keep_prior" if action["ActionKind"] == "keep_prior" else "retry"
        with self.dal.serialized(source_id):
            state = self.dal.snapshot(source_id)
            marker = state["marker"]
            if not marker or marker.get("action") != identity(action["ActionID"]):
                # Fence a callback that has not yet recorded its dispatch marker.
                if digest(state).hex() == action["EvidenceHash"]:
                    self.dal.record(
                        source_id,
                        action["EvidenceHash"],
                        dict(
                            action=identity(action["ActionID"]),
                            token=action["EvidenceHash"],
                            choice=choice,
                            configuration=state["current"],
                            reason="Dispatch not acknowledged; never replay automatically",
                        ),
                    )
                    state = self.dal.snapshot(source_id)
                    marker = state["marker"]
                else:
                    return "not_applied"
            if marker.get("token") != action["EvidenceHash"]:
                raise SourceConflict("Action does not match its saved configuration approval.")
            if marker.get("choice") != choice:
                raise SourceConflict(
                    "Saved configuration choice differs from the confirmed action."
                )
            if choice == "keep_prior":
                return "verified"
            identifier = self.dal.reserve_for_reconciliation(source_id, marker)
            if self.dal.close_uncommitted(identifier, marker):
                return "not_applied"
            self.producer.inspect(identifier)
            return "verified"

    @staticmethod
    def _run():
        from proc_config_import import run_proc_config_import

        return run_proc_config_import(source_actor="guided_configuration_recovery")
