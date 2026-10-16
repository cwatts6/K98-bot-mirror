"""Guided continuation for unstarted exports behind permanently retired outputs."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity


class WaitingReplacementWorkflow:
    def __init__(
        self, *, discovery, continuation, blocking_jobs, original_workflow, project_activation=None
    ):
        self.discovery, self.continuation = discovery, continuation
        self.blocking_jobs, self.original_workflow = blocking_jobs, original_workflow
        self.project_activation = project_activation

    def _state(self, job_id):
        snapshot = self.discovery.job(job_id)
        if snapshot["attempts"] or snapshot["streams"] or not snapshot.get("isolated_targets"):
            raise SourceConflict("The queued export now needs its own execution recovery.")
        if any(r["ActiveJobID"] == job_id for r in snapshot["resources"]):
            raise SourceConflict(
                "The queued export still owns reservations; recheck after its worker settles."
            )
        blockers = self.blocking_jobs(job_id, self.discovery.account)
        if not blockers or job_id in blockers:
            raise SourceConflict("Queued export has no distinct original target recovery.")
        targets = sorted(
            r["ResourceKey"][12:]
            for r in snapshot["resources"]
            if r["ResourceKey"].startswith("destination:")
        )
        activation = None
        pending = []
        for blocker in blockers:
            state = self.original_workflow(blocker)._state(blocker)
            candidate = state["activation"]
            if not state.get("delivery") or not state["delivery"]["resolved"]:
                pending.append(blocker)
            elif candidate is not None and set(targets) <= set(candidate["mapping"]):
                if activation is not None:
                    raise SourceConflict("Queued output mapping has conflicting activations.")
                activation = candidate
        if pending:
            activation = None
        elif self.project_activation is not None:
            activation = self.project_activation(snapshot)
        return dict(
            snapshot=snapshot,
            blockers=pending or blockers,
            targets=targets,
            activation=activation,
            delivery=self.continuation.inspect(job_id, activation) if activation else None,
        )

    def inspect(self, job_id):
        state = self._state(identity(job_id))
        delivery = state["delivery"]
        evidence = dict(
            title="Queued export replacement recovery",
            outcome=delivery["stage"] if delivery else "waiting_for_output_replacement",
            explanation=(
                delivery["explanation"]
                if delivery
                else (
                    "This export never started, but its output files were retired by another recovery. "
                    "Open the linked blocking recovery below to verify replacement files, then return here "
                    "to publish this export's retained data. Its SQL import will not run again."
                )
            ),
            targets=state["targets"],
            replacements=state["activation"]["mapping"] if state["activation"] else {},
            blocking_job_ids=state["blockers"],
            actions=delivery["actions"] if delivery else {},
            delivery=delivery,
        )
        return evidence, digest(state).hex(), bool(delivery and delivery["resolved"])

    def _reviewed(self, job_id, token):
        evidence, actual, resolved = self.inspect(job_id)
        state = self._state(job_id)
        if resolved or actual != token or digest(state).hex() != token:
            raise SourceConflict("Queued replacement changed. Review the current choices.")
        return evidence, state

    def execute(self, job_id, action, token, actor, reason, *, payload=None):
        evidence, state = self._reviewed(job_id, token)
        if payload is not None or action not in evidence["actions"]:
            raise SourceConflict("This queued replacement action is unavailable.")
        self.continuation.execute(job_id, state["activation"], action, actor=actor, reason=reason)

    def reconcile(self, job_id, action):
        state = self._state(job_id)
        if state["activation"] is None:
            return "not_applied"
        return self.continuation.reconcile(job_id, state["activation"], action)
