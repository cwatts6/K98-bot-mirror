"""Guided review and verification for account queue admissions."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity


class QueueAdmissionRecovery:
    kind = "queue_admission"
    observe_healthy = False

    def __init__(self, dal):
        self.dal = dal

    def pending_recovery(self, *, after=None):
        return self.dal.pending(after)

    def inspect(self, source_id):
        state = self.dal.snapshot(source_id)
        prep = state["preparation"]
        actions, links = {}, []
        document = json.loads(prep["RequestJson"])
        producer = document.get("request", {}).get("producer", {})
        marker = json.loads(prep["GenerationJson"] or "{}").get("queue_withdrawal")
        closed = bool(
            marker
            and prep["State"] == "unavailable"
            and prep["Version"] == 2
            and not any(state["counts"].values())
        )
        if self.dal.eligible(state):
            actions["withdraw_queued"] = dict(
                label="Cancel unstarted queue entry",
                check="Confirm this queued request should be cancelled. It has never acquired admission: no execution stream, SQL receipt, resource membership, held reservation or captured output exists.",
                effect="Recheck the exact initial state under the account lock, fence the old ticket and preserve an audit receipt. A late worker cannot claim it. No business write is replayed and no other owner's access is released.",
            )
        elif not closed:
            kind = {
                "config": "configuration_read",
                "all_kvk": "all_kvk_capture",
                "scan_data": "stats_import",
            }.get(prep["ConsumerKind"])
            kind = {
                "stats_import": "producer_refusal",
                "configuration_import": "configuration_producer",
                "player_stats_report": "player_report",
            }.get(producer.get("kind"), kind)
            if kind:
                links.append(
                    dict(
                        label="Review execution and ownership",
                        kind=kind,
                        source_id=producer.get("parent") or source_id,
                    )
                )
        evidence = dict(
            title="Account queue admission",
            actions=actions,
            recovery_links=links,
            outcome="withdrawn"
            if closed
            else "unstarted"
            if actions
            else "execution_review_required",
            queue_ticket=prep["EnqueueSequence"],
            preparation_state=prep["State"],
            explanation=(
                "The unstarted ticket was fenced and withdrawn. Other operations retain their own verification requirements."
                if closed
                else "This queued request can prevent newer work from entering the account. Review the offered cancellation or follow its execution recovery. A timeout alone never authorizes releasing access."
            ),
        )
        return (
            evidence,
            digest(state).hex(),
            closed or prep["State"] not in {"pending", "sql_pending"},
        )

    def execute(self, source_id, action, token, actor, reason):
        if action != "withdraw_queued" or not actor.startswith("recovery:"):
            raise SourceConflict("A confirmed queue withdrawal is required.")
        self.dal.withdraw(source_id, token, actor.removeprefix("recovery:"))

    def reconcile(self, source_id, action):
        state = self.dal.snapshot(source_id)
        prep = state["preparation"]
        marker = json.loads(prep["GenerationJson"] or "{}").get("queue_withdrawal", {})
        if marker == dict(action=identity(action["ActionID"]), token=action["EvidenceHash"]):
            return "verified" if self.inspect(source_id)[2] else None
        if digest(state).hex() != action["EvidenceHash"] or not self.dal.eligible(state):
            return "not_applied"
        self.execute(
            source_id,
            action["ActionKind"],
            action["EvidenceHash"],
            "recovery:" + str(action["ActionID"]),
            action["Reason"],
        )
        return "verified" if self.inspect(source_id)[2] else None
