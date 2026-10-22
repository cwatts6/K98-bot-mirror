"""One guided decision per unfinished stage, with original unknowns retained."""

import asyncio
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity
from services.processing_pipeline_receipt_dal import STAGES
from services.processing_pipeline_receipts import (
    continuation_scope,
    producer_evidence,
    stage as run_stage,
)

LABELS = dict(
    import_="scan import",
    player_cache="player cache",
    name_cache="name cache",
    maintenance="SQL maintenance",
    configuration="configuration publication",
    target_cache="target cache",
    export="export admission",
)
LABELS["import"] = LABELS.pop("import_")


class ProcessingPipelineRecovery:
    kind = "processing_pipeline"

    def __init__(self, dal, *, runner=None):
        self.dal = dal
        self.runner = runner or self._run

    def pending_recovery(self, *, after=None):
        return self.dal.pending_recovery(after=after)

    def _state(self, source_id):
        state = self.dal.review_snapshot(source_id)
        children, reads = {}, {}
        for name in ("import", "player_cache", "configuration"):
            operation = state["stages"][name]["OperationID"]
            children[name] = self.dal.preparation(operation)
            if name == "configuration":
                reads[name] = self.dal.configuration_read(operation)
                children[name] = self.dal.configuration_result(operation)
        self.dal.assert_review_current(self.dal.review_snapshot(source_id), state)
        state.update(children=children, reads=reads)
        return state

    def inspect(self, source_id):
        state = self._state(source_id)
        stages = state["stages"]
        unfinished = [
            name for name in STAGES if stages[name]["State"] not in {"observed", "skipped"}
        ]
        actions, links = {}, []
        for name, child in state["children"].items():
            if child:
                links.append(
                    dict(
                        label="Review " + LABELS[name] + " result",
                        kind={
                            "import": "stats_import",
                            "player_cache": "player_report",
                            "configuration": "configuration_producer",
                        }[name],
                        source_id=identity(child["PreparationID"]),
                    )
                )
        read = state["reads"].get("configuration")
        if read:
            links.append(
                dict(
                    label="Review configuration read",
                    kind="configuration_read",
                    source_id=identity(read["PreparationID"]),
                )
            )
        verified = None
        selected = unfinished[0] if unfinished else None
        if selected:
            row = stages[selected]
            actions["retain_stage"] = dict(
                label="Leave this stage unfinished",
                check=f"Confirm {LABELS[selected]} should remain unfinished for this invocation. Its earlier outcome will remain recorded as unknown where no receipt exists.",
                effect="Save and verify this explicit decision. It does not release producer reservations, close linked incidents, refresh data or certify delivery.",
            )
            if selected in {"import", "configuration"} and state["children"][selected]:
                verified, complete = producer_evidence(
                    self.dal, selected, identity(row["OperationID"])
                )
                if complete:
                    actions["verify_stage"] = dict(
                        label="Record verified stage result",
                        check="Confirm this exact independently committed producer result belongs to the unfinished pipeline.",
                        effect="Bind its durable completion receipt to this stage. No producer or export is dispatched.",
                    )
                else:
                    verified = None
            import_complete = stages["import"]["State"] == "observed"
            may_continue = selected != "import" and import_complete
            if selected == "configuration":
                # Existing reads/publications retain their own recovery. A new
                # pipeline dispatch never adopts or overrides their reservations.
                may_continue = may_continue and state["children"][selected] is None and read is None
            if selected == "player_cache" and state["children"][selected] is not None:
                child = state["children"][selected]
                may_continue = may_continue and child["State"] in {
                    "captured",
                    "materialized",
                    "unavailable",
                }
            if selected == "export":
                child = state["children"]["configuration"]
                disposition = (
                    json.loads(child["RequestJson"])["request"]["producer"].get(
                        "export_disposition"
                    )
                    if child
                    else None
                )
                may_continue = may_continue and bool(
                    child
                    and child["State"] in {"captured", "materialized"}
                    and disposition == "pipeline_export_v1"
                )
            if may_continue and verified is None:
                actions["continue_stage"] = dict(
                    label="Continue " + LABELS[selected],
                    review_details=True,
                    review_title="Review remaining pipeline stage",
                    review_description="Review the original input, current sources and registered outputs before confirming this separate stage decision.",
                    check=f"Confirm a separately identified {LABELS[selected]} operation using the displayed current configuration. Earlier unknown results remain in history. No scan import or committed reporting stage will run again.",
                    effect="Save this decision before dispatch, exclude live pipeline work, run only the selected stage and verify its own result. A lost reply is reconciled before another decision.",
                )
        summary = {
            name: dict(state=row["State"], evidence=json.loads(row["EvidenceJson"] or "null"))
            for name, row in stages.items()
        }
        evidence = dict(
            title="Unfinished processing pipeline",
            outcome="decisions_complete" if not unfinished else "stage_decision_required",
            explanation=(
                "Each stage has its own recorded result or explicit unfinished disposition. Queued export is not spreadsheet delivery; memory-cache verification describes the process at receipt time."
                if not unfinished
                else "Review the first unfinished stage. Linked producer/capture incidents retain their independent ownership and recovery. A timeout, old cache or released reservation is not completion."
            ),
            input=json.loads(state["run"]["InputsJson"]),
            stage_results=summary,
            selected_stage=selected,
            actions=actions,
            recovery_links=links,
        )
        self.dal.assert_review_current(self.dal.review_snapshot(source_id), state)
        return evidence, self.dal.token(state), not unfinished

    def review_details(self, source_id, action, token):
        from services.producer_recovery_review import registration_review

        evidence, current, complete = self.inspect(source_id)
        if (
            complete
            or current != token
            or action != "continue_stage"
            or action not in evidence["actions"]
        ):
            raise SourceConflict("Pipeline review changed; reopen the incident.")
        state = self._state(source_id)
        if self.dal.token(state) != token:
            raise SourceConflict("Pipeline review changed; reopen the incident.")
        original = json.loads(state["run"]["RegistrationJson"])
        fields = []
        for consumer in ("config", "scan_data"):
            fields.extend(
                registration_review(
                    dict(
                        preparation={
                            "RequestJson": json.dumps({"request": {"config": original[consumer]}})
                        },
                        current_registration=state["current_registration"][consumer],
                        producer={
                            "inputs": {
                                "operation": LABELS[evidence["selected_stage"]] + "; no scan import"
                            }
                        },
                    )
                )
            )
        return fields

    def execute(self, source_id, action, token, actor, reason):
        if not actor.startswith("recovery:"):
            raise SourceConflict("A confirmed pipeline decision is required.")
        action_id = identity(actor.removeprefix("recovery:"))
        with self.dal.guard(source_id):
            evidence, current, complete = self.inspect(source_id)
            if complete or token != current or action not in evidence["actions"]:
                raise SourceConflict("Pipeline evidence changed; review the current decision.")
            selected = evidence["selected_stage"]
            state = self._state(source_id)
            if self.dal.token(state) != token:
                raise SourceConflict("Pipeline evidence changed; reopen the confirmation.")
            result = None
            if action == "verify_stage":
                result, verified = producer_evidence(
                    self.dal, selected, identity(state["stages"][selected]["OperationID"])
                )
                if not verified:
                    raise SourceConflict("The independent producer receipt no longer verifies.")
            self.dal.decide(
                source_id,
                selected,
                token,
                dict(
                    action=action_id,
                    token=token,
                    reason=reason,
                    choice=action,
                    registration=state["current_registration"],
                ),
                reviewed_state=state,
                disposition=action == "retain_stage",
                evidence=result,
            )
            if action == "continue_stage":
                from services.legacy_export_snapshot_service import (
                    producer_capture_scope,
                    use_runtime,
                )

                with (
                    use_runtime(self.dal.runtime),
                    producer_capture_scope(),
                    continuation_scope(self.dal, source_id, action_id),
                ):
                    asyncio.run(run_stage(selected, lambda: self.runner(selected, source_id)))

    def reconcile(self, source_id, action):
        with self.dal.guard(source_id):
            state = self.dal.snapshot(source_id)
            matches = []
            for name, row in state["stages"].items():
                decisions = json.loads(row["DecisionJson"] or "[]")
                if decisions and decisions[-1].get("action") == identity(action["ActionID"]):
                    matches.append((name, row, decisions[-1]))
            if not matches:
                return "not_applied"
            if len(matches) != 1 or matches[0][2].get("token") != action["EvidenceHash"]:
                raise SourceConflict("Pipeline action does not match its saved decision.")
            name, row, marker = matches[0]
            if marker["choice"] != action["ActionKind"]:
                raise SourceConflict("Pipeline action kind changed.")
            if row["State"] in {"observed", "skipped"}:
                return "verified"
            if row["State"] == "running":
                # The worker guard has ended. Re-read business receipts; never
                # dispatch a second business call to repair an unknown response.
                result, verified = (
                    producer_evidence(self.dal, name, identity(row["OperationID"]))
                    if name in {"import", "configuration"}
                    else (dict(outcome="receipt_unconfirmed"), False)
                )
                self.dal.observe(source_id, name, row["OperationID"], result, verified=verified)
                return "verified" if verified else "not_applied"
            return "not_applied"

    def _run(self, name, source_id):
        if name == "player_cache":
            from constants import PLAYER_STATS_CACHE
            from player_stats_cache import rebuild_validated_cache_only

            rebuild_validated_cache_only()
            with open(PLAYER_STATS_CACHE, "rb") as source:
                raw = source.read(64 * 1024 * 1024 + 1)
            if len(raw) > 64 * 1024 * 1024:
                raise SourceConflict("Player cache exceeds its verified bound.")
            return json.loads(raw)
        if name == "configuration":
            from proc_config_import import run_proc_config_import

            return run_proc_config_import(source_actor="guided_pipeline_continuation")
        if name == "export":
            from services.export_submission import ExportSubmission

            state = self.dal.snapshot(source_id)
            prep = self.dal.configuration_result(state["stages"]["configuration"]["OperationID"])
            if (
                not prep
                or json.loads(prep["RequestJson"])["request"]["producer"].get("export_disposition")
                != "pipeline_export_v1"
            ):
                raise SourceConflict(
                    "A configuration-only successor cannot be exported by the pipeline."
                )
            self.dal.runtime.verified_snapshot(identity(prep["PreparationID"]))
            preparation_id = identity(prep["PreparationID"])
            return ExportSubmission(
                self.dal.runtime.enqueue_snapshot(preparation_id), preparation_id
            )
        if name in {"name_cache", "target_cache", "maintenance"}:
            # strict_work owns these known workers and verifies their result.
            return None
        raise SourceConflict("Pipeline recovery cannot dispatch a scan import.")
