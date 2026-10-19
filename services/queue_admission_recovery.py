"""Guided review and verification for account queue admissions."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity


class QueueAdmissionRecovery:
    kind = "queue_admission"
    observe_healthy = False

    def __init__(self, dal, domains=None):
        self.dal = dal
        self.domains = domains if domains is not None else {}

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
        read_closed = self.dal.withdrawn_read(state, closed=True)
        closed = closed or read_closed
        if self.dal.withdrawn_read(state):
            actions["close_withdrawn_read"] = dict(
                label="Close withdrawn read",
                check="This older configuration read was withdrawn before admission. Its original input files and publication intent were not saved. Confirm closing this cancelled read's queue record; this does not confirm that current configuration is correct or start an import.",
                effect="Recheck the exact request, initial withdrawal fence and absence of execution, captured output and held access. Save your decision and verify it independently. No provider request, SQL import or release of another owner's access occurs.",
            )
        elif self.dal.eligible(state):
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
            linked_source = producer.get("parent") or source_id
            if self.dal.configuration_read_continuation_candidate(state):
                kind = "configuration_read_continuation"
                linked_source = source_id
            if kind:
                links.append(
                    dict(
                        label="Review execution and ownership",
                        kind=kind,
                        source_id=linked_source,
                    )
                )
        domain_proof, domain_resolved = None, False
        # Admission alone is not resolution. Preserve the guided handoff while
        # execution is active/uncertain; terminal metadata also needs the owning
        # domain's verification before this queue incident can close.
        if links and prep["State"] in {"completed", "materialized", "unavailable"}:
            link = links[0]
            domain = self.domains.get(link["kind"])
            if domain is not None:
                _, domain_token, verified = domain.inspect(link["source_id"])
                domain_resolved = verified is True
                domain_proof = dict(link=link, token=domain_token, resolved=domain_resolved)
        evidence = dict(
            title="Account queue admission",
            actions=actions,
            recovery_links=links,
            outcome=(
                "withdrawn"
                if closed
                else (
                    "domain_recovery_verified"
                    if domain_resolved
                    else "unstarted"
                    if actions
                    else "execution_review_required"
                )
            ),
            queue_ticket=prep["EnqueueSequence"],
            preparation_state=prep["State"],
            failure_context=dict(
                original_created_utc=prep["CreatedUTC"],
                original_request_sha256=prep["RequestHash"],
                operation=prep["ConsumerKind"],
                original_fault=(
                    "admission_not_obtained"
                    if actions.get("close_withdrawn_read") or read_closed
                    else "not_established"
                ),
                input_identity=(
                    "not_recorded"
                    if prep["ConsumerKind"] == "config"
                    and not document.get("request", {}).get("configuration_import")
                    else "see_linked_workflow"
                ),
                summary=(
                    "The saved request identifies a configuration read only. Original input files, sheet ranges and publication intent were not recorded. Its exact initial withdrawal and absence of execution are verified; no configuration contents have been validated."
                    if actions.get("close_withdrawn_read") or read_closed
                    else "Review the linked operation for original input and configuration details."
                ),
            ),
            explanation=(
                "The unstarted ticket was fenced and withdrawn. Other operations retain their own verification requirements."
                if closed
                else (
                    "The owning recovery workflow verified this queue handoff or closure. Provider delivery and other operations retain their own verification requirements."
                    if domain_resolved
                    else (
                        "This read was already withdrawn before admission and holds no access. Close its queue record after reviewing the verified evidence."
                        if actions.get("close_withdrawn_read")
                        else "Review the offered cancellation or follow its execution recovery. Pending admissions can delay newer work; a timeout alone never authorizes releasing access."
                    )
                )
            ),
        )
        return (
            evidence,
            digest(dict(queue=state, domain=domain_proof) if domain_proof else state).hex(),
            closed or domain_resolved,
        )

    def execute(self, source_id, action, token, actor, reason):
        if action not in {"withdraw_queued", "close_withdrawn_read"} or not actor.startswith(
            "recovery:"
        ):
            raise SourceConflict("A confirmed queue withdrawal is required.")
        apply = (
            self.dal.close_withdrawn_read if action == "close_withdrawn_read" else self.dal.withdraw
        )
        apply(source_id, token, actor.removeprefix("recovery:"))

    def reconcile(self, source_id, action):
        state = self.dal.snapshot(source_id)
        prep = state["preparation"]
        close_read = action["ActionKind"] == "close_withdrawn_read"
        marker = json.loads(prep["GenerationJson"] or "{}").get(
            "withdrawn_read_closeout" if close_read else "queue_withdrawal", {}
        )
        if marker == dict(action=identity(action["ActionID"]), token=action["EvidenceHash"]):
            return "verified" if self.inspect(source_id)[2] else None
        eligible = self.dal.withdrawn_read(state) if close_read else self.dal.eligible(state)
        if digest(state).hex() != action["EvidenceHash"] or not eligible:
            return "not_applied"
        self.execute(
            source_id,
            action["ActionKind"],
            action["EvidenceHash"],
            "recovery:" + str(action["ActionID"]),
            action["Reason"],
        )
        return "verified" if self.inspect(source_id)[2] else None
