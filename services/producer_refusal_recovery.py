"""Guided continuation of a proven admission refusal, never an unknown SQL write."""

import asyncio
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.producer_recovery_intent import stats_intent
from services.producer_refusal_dal import unused as unused


class ProducerRefusalRecovery:
    kind = "producer_refusal"
    observe_healthy = False

    def __init__(self, dal, imports, runner=None):
        self.dal, self.imports = dal, imports
        self.runner = runner or self._run

    def pending_recovery(self, *, after=None):
        return self.dal.pending(after)

    def inspect(self, source_id):
        state = self.dal.snapshot(source_id)
        active = [a for a in state["attempts"] if not unused(a)]
        if len(active) > 1:
            raise SourceConflict(
                "More than one continuation needs investigation; no import may replay."
            )
        links, actions = [], {}
        evidence = dict(
            title="SQL stage admission recovery",
            outcome="not_started",
            explanation="The saved SQL stage was refused before execution. Its exact input is retained. Review the blocker, then confirm continuation of this stage.",
            actions=actions,
            recovery_links=links,
        )
        resolved = False
        if state["original_phase"] == "execution_registered":
            if state["attempt_count"]:
                raise SourceConflict("Original and replacement execution cannot both be admitted.")
            child, _, resolved = self.imports.inspect(source_id)
            evidence.update(outcome=child["outcome"], explanation=child["explanation"])
            links.append(
                dict(label="Review original SQL stage", kind="stats_import", source_id=source_id)
            )
        elif state["original_phase"] == "unstarted":
            if active:
                raise SourceConflict("An unclosed admission cannot have a continuation.")
            evidence.update(
                outcome="admission_unconfirmed",
                explanation="Writer admission did not reach a confirmed execution receipt. The saved inputs are retained. Cancel this unstarted reservation before choosing whether to continue it.",
            )
            actions["close_unstarted_admission"] = dict(
                label="Cancel unstarted reservation",
                check="Confirm this interrupted admission should be cancelled. The bot will exclude active SQL execution and require no import receipt, provider stream, generation or captured output.",
                effect="Fence the exact original claim and release only its reservations. A late worker cannot enter SQL with that claim. Verify the closure, then offer a separate confirmation to resume the saved inputs.",
            )
        elif active:
            attempt = active[0]
            if attempt["ExecutionState"] is not None:
                child, _, child_resolved = self.imports.inspect(attempt["PreparationID"])
                evidence.update(outcome=child["outcome"], explanation=child["explanation"])
                links.append(
                    dict(
                        label="Review resumed SQL stage",
                        kind="stats_import",
                        source_id=attempt["PreparationID"],
                    )
                )
                # This is the admission incident, not proof of all remaining pipeline stages.
                resolved = child_resolved
            else:
                evidence.update(
                    outcome="continuation_checking",
                    explanation="A continuation reservation exists. Recovery is checking its execution evidence before offering another action.",
                )
        elif not state["blockers"]:
            current = state["current_registration"]
            original = json.loads(state["preparation"]["RequestJson"])["request"]["config"]
            if original != current:
                evidence.update(
                    outcome="registration_changed",
                    explanation="The original destination registration changed. The saved import remains unstarted. Review the currently registered destinations before confirming continuation with them.",
                )
                actions["resume_current_registration"] = dict(
                    label="Continue with current destinations",
                    review_details=True,
                    check="Review the retained scan and old/current destination pages. Confirm this exact scan should be imported using the displayed current registration. The original registration will remain in history.",
                    effect="Bind this approval to both registration hashes, run the exact retained SQL inputs under fresh admission, then verify its receipt. Excel and archive steps are not repeated. Committed imports cannot be replayed.",
                )
            else:
                actions["resume_sql_stage"] = dict(
                    label="Resume saved SQL stage",
                    review_details=True,
                    check="Confirm this retained scan should still be imported. The bot verified that the original refused attempt never entered SQL. Excel conversion and archive steps will not run again.",
                    effect="Run the exact saved SQL inputs under fresh writer admission. Retain the resulting receipt and output for guided capture and export recovery. An uncertain result will be investigated before any further continuation.",
                )
        else:
            queued_only = all(blocker["ResourceKey"] == "queue" for blocker in state["blockers"])
            evidence.update(
                outcome="waiting_in_queue" if queued_only else "waiting_for_access",
                explanation=(
                    "The saved SQL stage never started. Eligible work is ahead in the admission queue; it has not failed merely because this stage timed out. Let it finish, or review its current status below. This incident will offer continuation when access is available."
                    if queued_only
                    else "The original SQL stage never started. Another operation currently owns or blocks admission. Review its recovery below; healthy work is allowed to finish. Access is never released just because a timeout elapsed."
                ),
            )
            for blocker in state["blockers"]:
                if blocker["ActiveOutputOperationID"]:
                    links.append(
                        dict(
                            label="Review blocking rollover",
                            kind="export_rollover",
                            source_id=blocker["ActiveOutputOperationID"],
                        )
                    )
                elif blocker["ActiveJobID"]:
                    links.append(
                        dict(
                            label="Review blocking export",
                            kind="export_job",
                            source_id=blocker["ActiveJobID"],
                        )
                    )
                elif blocker["ActivePreparationID"]:
                    linked_source = blocker["ActivePreparationID"]
                    kind = {
                        "config": "configuration_read",
                        "scan_data": "stats_import",
                        "all_kvk": "all_kvk_capture",
                    }.get(blocker["ConsumerKind"])
                    if (
                        blocker["ConsumerKind"] == "scan_data"
                        and blocker.get("ProducerKind") == "player_stats_report"
                    ):
                        kind = "player_report"
                    elif (
                        blocker["ConsumerKind"] == "scan_data"
                        and blocker.get("ProducerKind") == "stats_import"
                        and not blocker.get("HasImportReceipt", True)
                    ):
                        kind = "producer_refusal"
                        linked_source = blocker.get("ProducerParent") or linked_source
                    if kind:
                        links.append(
                            dict(
                                label="Review blocking stage",
                                kind=kind,
                                source_id=linked_source,
                            )
                        )
        return evidence, digest(state).hex(), resolved

    def review_details(self, source_id, action, token):
        from services.producer_recovery_review import registration_review

        state = self.dal.snapshot(source_id)
        if (
            action not in {"resume_current_registration", "resume_sql_stage"}
            or digest(state).hex() != token
        ):
            raise SourceConflict("Recovery details changed. Reopen the incident before confirming.")
        return registration_review(state)

    def execute(self, source_id, action, token, actor, reason):
        if action not in {
            "resume_sql_stage",
            "resume_current_registration",
            "close_unstarted_admission",
        } or not actor.startswith("recovery:"):
            raise SourceConflict("Exact confirmed continuation action required.")
        action_id = identity(actor.removeprefix("recovery:"))
        with self.dal.serialized(source_id):
            evidence, current, resolved = self.inspect(source_id)
            if resolved or current != token or action not in evidence["actions"]:
                raise SourceConflict("Continuation evidence changed. Review the current incident.")
            if action == "close_unstarted_admission":
                return self.dal.close_admission(source_id, token, action_id)
            state = self.dal.snapshot(source_id)
            identifier = self.dal.reserve(
                source_id,
                action_id,
                use_current_registration=action == "resume_current_registration",
            )
            # A prior reconciliation may have left a terminal tombstone. It can
            # never be turned back into a producer request by a late callback.
            preparation = self.dal.runtime.dal.read(identifier)
            if preparation["State"] != "pending" or preparation["Version"] != 1:
                raise SourceConflict("This continuation action has already been consumed.")
            from services.legacy_export_snapshot_service import use_runtime

            with use_runtime(self.dal.runtime):
                with stats_intent(
                    state["producer"]["inputs"],
                    action_id=action_id,
                    parent=source_id,
                    registration_recovery=json.loads(preparation["RequestJson"])["request"][
                        "producer"
                    ].get("registration_recovery"),
                ):
                    self.runner(state["producer"]["inputs"])

    def reconcile(self, source_id, action):
        if action["ActionKind"] == "close_unstarted_admission":
            with self.dal.serialized(source_id):
                state = self.dal.snapshot(source_id)
                marker = json.loads(state["preparation"]["GenerationJson"] or "{}").get(
                    "producer_admission_closed", {}
                )
                if (
                    marker.get("action") == identity(action["ActionID"])
                    and marker.get("token") == action["EvidenceHash"]
                ):
                    return "verified"
                if digest(state).hex() != action["EvidenceHash"]:
                    return "not_applied"
                self.dal.close_admission(source_id, action["EvidenceHash"], action["ActionID"])
                return None
        if action["ActionKind"] not in {"resume_sql_stage", "resume_current_registration"}:
            raise SourceConflict("Unsupported producer continuation receipt.")
        with self.dal.serialized(source_id):
            # Reserve even when the dispatch never began: this durable tombstone
            # excludes a late original callback before another action is offered.
            identifier = self.dal.reserve(
                source_id,
                action["ActionID"],
                use_current_registration=action["ActionKind"] == "resume_current_registration",
            )
            if self.dal.close_unused(source_id, action["ActionID"]):
                return "not_applied"
            state = self.dal.snapshot(source_id)
            attempt = next(p for p in state["attempts"] if p["PreparationID"] == identifier)
            if attempt["ExecutionState"] is not None:
                # Handoff to the exact receipt is durable. The incident itself
                # stays open until the import adapter verifies settlement/capture.
                self.imports.inspect(identifier)
                return "verified"
            return None

    @staticmethod
    def _run(inputs):
        from stats_module import run_sql_procedure

        return asyncio.run(
            run_sql_procedure(
                rank=inputs["rank"],
                seed=inputs["seed"],
                completed_filename=inputs["completed_filename"],
                timeout_seconds=inputs["timeout_seconds"],
                import_metadata=dict(inputs["metadata"]),
            )
        )
