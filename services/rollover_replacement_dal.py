"""Atomic replacement linkage in the immutable rollover plan, never an old-phase retry."""

import json
from types import SimpleNamespace

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from kvk.services.source_output_pool_service import checked_plan
from services.export_coordination_dal import identity


def validate_replacement(cursor, operation_id, plan):
    """Called inside the normal pool/account confirmation transaction."""
    link = plan.get("replacement_rollover")
    if link is None:
        return
    if not isinstance(link, dict) or set(link) != {
        "operation_id",
        "activation_id",
        "replacement_id",
        "action_id",
    }:
        raise SourceConflict("Exact rollover replacement linkage required.")
    if any(identity(v) != v for v in link.values()) or link["action_id"] != operation_id:
        raise SourceConflict("Rollover replacement action differs.")
    pool = plan["snapshot"]["pool"]
    cursor.execute(
        "SELECT o.* FROM KVK.SourceOutputOperation o "
        "JOIN dbo.ExportTargetContainment c ON c.OutputOperationID=o.OperationID AND c.AccountKey=o.AccountKey "
        "JOIN dbo.ExportReplacementPlan p ON p.ContainmentID=c.ContainmentID AND p.AccountKey=c.AccountKey "
        "JOIN dbo.ExportReplacementActivation a ON a.ReplacementID=p.ReplacementID AND a.AccountKey=p.AccountKey "
        "WHERE o.OperationID=? AND a.ActivationID=? AND p.ReplacementID=? AND a.NewPoolID=? "
        "AND o.AccountKey=? AND o.State='uncertain' AND o.Phase='uncertain' AND a.OldPoolID=o.PoolID",
        link["operation_id"],
        link["activation_id"],
        link["replacement_id"],
        pool["PoolID"],
        pool["AccountKey"],
    )
    original = one(cursor)
    if original is None or (pool["ActiveKVK"], identity(pool["ChoiceID"]), plan["new_choice"]) != (
        original["OldKVK"],
        identity(original["OldChoiceID"]),
        dict(
            KVK_NO=original["NewKVK"],
            SourceKey=original["SourceKey"],
            ChoiceID=identity(original["NewChoiceID"]),
        ),
    ):
        raise SourceConflict("Replacement must preserve the exact original season choices.")
    cursor.execute(
        "SELECT OperationID FROM KVK.SourceOutputOperation WHERE PoolID=?", pool["PoolID"]
    )
    if rows(cursor):
        raise SourceConflict(
            "A rollover already owns this replacement pool; inspect its original operation."
        )
    cursor.execute(
        "SELECT ResourceKey FROM dbo.ExportResource WHERE ActiveOutputOperationID=?",
        link["operation_id"],
    )
    if rows(cursor):
        raise SourceConflict("Original rollover custody is not released.")


class RolloverReplacementDAL:
    def __init__(self, pools):
        self.pools = pools

    def read(self, original_id, activation):
        with transaction(self.pools.connect) as cursor:
            cursor.execute(
                "SELECT * FROM KVK.SourceOutputOperation WHERE PoolID=? AND AccountKey=? "
                "AND JSON_VALUE(PlanJson,'$.replacement_rollover.operation_id')=? "
                "AND JSON_VALUE(PlanJson,'$.replacement_rollover.activation_id')=?",
                activation["replacement_id"],
                activation["registration"]["account"],
                identity(original_id),
                activation["activation_id"],
            )
            found = rows(cursor)
            if len(found) > 1:
                raise SourceConflict("Replacement rollover linkage is ambiguous.")
            if not found:
                return None
            operation = _wire(found[0])
            plan = json.loads(operation["PlanJson"])
            original = activation["input_commitment"]
            if (
                digest(plan).hex() != operation["PlanHash"]
                or plan.get("replacement_rollover")
                != dict(
                    operation_id=identity(original_id),
                    activation_id=activation["activation_id"],
                    replacement_id=activation["replacement_id"],
                    action_id=operation["OperationID"],
                )
                or any(
                    operation[k] != original[k]
                    for k in ("SourceKey", "OldKVK", "OldChoiceID", "NewKVK", "NewChoiceID")
                )
                or plan["new_choice"]
                != dict(
                    KVK_NO=original["NewKVK"],
                    SourceKey=original["SourceKey"],
                    ChoiceID=original["NewChoiceID"],
                )
            ):
                raise SourceConflict("Immutable replacement rollover linkage differs.")
            return operation

    def enqueue(self, original_id, activation, *, actor, reason):
        action_id = identity(actor.removeprefix("recovery:"))
        if actor != "recovery:" + action_id:
            raise SourceConflict("Durable rollover recovery action required.")
        previous = self.read(original_id, activation)
        if previous is not None:
            if previous["OperationID"] != action_id or previous["Reason"] != reason:
                raise SourceConflict("Another action already owns this replacement rollover.")
            return previous
        original = self.pools.operation(original_id)
        snapshot = self.pools.snapshot(activation["replacement_id"])
        plan = checked_plan(
            snapshot,
            self.pools.choice(original["NewKVK"]),
            actor=SimpleNamespace(
                user_id=actor, guild_id=original["GuildID"], channel_id=original["ChannelID"]
            ),
            reason=reason,
        )
        plan["replacement_rollover"] = dict(
            operation_id=identity(original_id),
            activation_id=activation["activation_id"],
            replacement_id=activation["replacement_id"],
            action_id=action_id,
        )
        return self.pools.confirm(action_id, plan)
