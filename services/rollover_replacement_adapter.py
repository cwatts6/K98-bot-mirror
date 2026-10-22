"""Admin-button routing for complete rollover replacement and final verification."""

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_recovery_service import rollover_decision_context, rollover_parent_link
from services.export_replacement_recovery_adapter import STEPS
from services.rollover_replacement_dal import RolloverReplacementDAL


class RolloverReplacementAdapter:
    kind = "export_rollover"

    def __init__(self, base, *, runtime):
        self.base, self.runtime = base, runtime

    @property
    def discovery(self):
        return self.base.discovery

    @discovery.setter
    def discovery(self, value):
        self.base.discovery = value

    def _call(self, source_id, operation, **values):
        return self.runtime.client.replacement_recovery(
            source_id, operation, owner_kind="rollover", **values
        )

    def pending_recovery(self, *, after=None):
        return self.base.pending_recovery(after=after)

    def inspect(self, source_id):
        snapshot = self.discovery.rollover(source_id, self.base.pools)
        if snapshot["operation"]["State"] not in {"running", "uncertain"}:
            return self.base.inspect(source_id)
        result = self._call(source_id, "inspect")
        result["evidence"]["failure_context"] = rollover_decision_context(snapshot)
        parent = rollover_parent_link(snapshot["operation"])
        if parent:
            result["evidence"].setdefault("recovery_links", []).insert(0, parent)
        original, _, _ = self.base.inspect(source_id)
        if (
            result["evidence"]["outcome"] == "isolation_required"
            and "verify_rollover" in original["actions"]
        ):
            result["evidence"]["actions"]["verify_rollover"] = original["actions"][
                "verify_rollover"
            ]
        return result["evidence"], result["token"], result["resolved"]

    def input_fields(self, source_id, action, token):
        return self._call(source_id, "fields", step=action, token=token)

    def validate_input(self, source_id, action, token, payload):
        return self._call(source_id, "validate", step=action, token=token, payload=payload)

    def execute(self, source_id, action, token, actor, reason, *, payload=None):
        if action == "continue_unstarted_rollover":
            return self.base.execute(source_id, action, token, actor, reason)
        original = self.discovery.rollover(source_id, self.base.pools)
        evidence, current, resolved = self.inspect(source_id)
        if token != current or resolved or action not in evidence["actions"]:
            raise SourceConflict("Rollover recovery changed; review its current choices.")
        if action == "verify_rollover":
            return self.base.execute(source_id, action, digest(original).hex(), actor, reason)
        if action in {"start_replacement_rollover", "verify_replacement_rollover"}:
            activation = self._call(source_id, "context", token=token)
            if action == "start_replacement_rollover":
                with self.runtime.reconfigure(recovery=True):
                    self.runtime.refresh_replacement_registration()
                    RolloverReplacementDAL(self.runtime.pools).enqueue(
                        source_id, activation, actor=actor, reason=reason
                    )
                from services.export_coordination_service import wake_exports

                wake_exports()
            else:
                operation = RolloverReplacementDAL(self.runtime.pools).read(source_id, activation)
                if operation is None:
                    raise SourceConflict("Replacement rollover is unavailable.")
                if digest(operation).hex() != evidence["delivery"]["operation_token"]:
                    raise SourceConflict("Replacement rollover changed after confirmation.")
                original = self.discovery.rollover(operation["OperationID"], self.base.pools)
                if digest(original["operation"]) != digest(operation):
                    raise SourceConflict("Replacement rollover changed after confirmation.")
                self.base.execute(
                    operation["OperationID"],
                    "verify_rollover",
                    digest(original).hex(),
                    actor,
                    reason,
                )
            return
        if action not in STEPS or action == "publish_replacement":
            raise SourceConflict("Unknown rollover replacement step.")
        if action == "activate_replacements":
            with self.runtime.reconfigure(recovery=True):
                self._call(
                    source_id,
                    "execute",
                    step=action,
                    token=token,
                    actor=actor,
                    reason=reason,
                    payload=payload,
                )
                self.runtime.refresh_replacement_registration()
        else:
            self._call(
                source_id,
                "execute",
                step=action,
                token=token,
                actor=actor,
                reason=reason,
                payload=payload,
            )

    def reconcile(self, source_id, action):
        kind = action["ActionKind"]
        if kind == "continue_unstarted_rollover":
            return self.base.reconcile(source_id, action)
        if kind == "verify_rollover":
            snapshot = self.discovery.rollover(source_id, self.base.pools)
            if snapshot["operation"]["State"] == "completed":
                return self.base.reconcile(source_id, action)
            _, current, _ = self.inspect(source_id)
            if current != action["EvidenceHash"]:
                return "not_applied"
            return self.base.reconcile(source_id, dict(action, EvidenceHash=digest(snapshot).hex()))
        document = {
            k: action.get(k)
            for k in ("ActionID", "ActionKind", "EvidenceHash", "Reason", "InputJson")
        }
        if kind == "start_replacement_rollover":
            result = self._call(source_id, "inspect")
            if result["token"] == action["EvidenceHash"]:
                self.execute(
                    source_id,
                    kind,
                    action["EvidenceHash"],
                    "recovery:" + action["ActionID"],
                    action["Reason"],
                )
        return self._call(source_id, "reconcile", recovery_action=document)
