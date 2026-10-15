"""One durable verification dispatch, original-receipt reconciliation and guided discard.

No provider call is repeated after an uncertain admission or response. A later
admin action may discard a complete typed read ledger and start a new attempt.
"""

import hashlib
import json
import logging
import threading
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_read_containment import read_ledger, stream_wire
from services.export_coordination_dal import identity
from services.export_enrollment_service import enrollment_scope
from services.export_execution_authority import ExportExecutionAuthority
from services.export_execution_protocol import ProviderRequest, decode, encode
from services.export_replacement_verification import (
    METADATA,
    ReplacementVerificationEvidence,
    ReplacementVerificationPlan,
    discovered_grid,
    replacement_readback,
    replacement_requests,
    verification_plan,
)

logger = logging.getLogger(__name__)


class ReplacementVerificationService:
    def __init__(self, *, dal, authority, proposals):
        self.dal, self.authority, self.proposals = dal, authority, proposals

    def _snapshot(self, verification_id):
        snapshot = self.dal.snapshot(
            verification_id, account=self.proposals.registration.value()["account"]
        )
        if snapshot is None:
            return None
        plan = ReplacementVerificationPlan(json.loads(snapshot["preparation"]["RequestJson"]))
        attempt = snapshot["attempt"]
        proposal = self.proposals.inspect(attempt["ReplacementID"])
        self._check_plan(plan, proposal)
        if (
            plan.value()["plan_id"] != attempt["VerificationID"]
            or plan.value()["replacement_id"] != attempt["ReplacementID"]
            or plan.digest.hex() != snapshot["preparation"]["RequestHash"]
            or plan.digest.hex() != attempt["PlanHash"]
            or sorted(f["file_id"] for f in plan.value()["files"])
            != sorted(proposal["mapping"].values())
            or identity(snapshot["preparation"]["PreparationID"]) != attempt["VerificationID"]
            or identity(snapshot["preparation"]["OwnerID"]) != attempt["VerificationID"]
        ):
            raise SourceConflict(
                "Verification differs from its sealed proposal or original identity."
            )
        return snapshot, plan

    def _check_plan(self, plan, proposal):
        value = plan.value()
        expected = verification_plan(
            self.proposals.registration,
            proposal,
            verification_id=value["plan_id"],
            manifest_hash=value["manifest_sha256"],
            profile_hash=value["credential_profile_sha256"],
            project_id=value["project_id"],
        )
        if plan.document != expected.document:
            raise SourceConflict("Verification access policy differs from the protected proposal.")

    def _admit(self, plan, *, actor, reason):
        if not isinstance(plan, ReplacementVerificationPlan):
            raise SourceConflict("Protected replacement verification plan required.")
        value = plan.value()
        if actor != "recovery:" + value["plan_id"]:
            raise SourceConflict("Verification requires its durable admin action identity.")
        with self.authority._lock:
            existing = self._snapshot(value["plan_id"])
            if existing is not None:
                if existing[1].document != plan.document:
                    raise SourceConflict("This action already owns a different verification plan.")
                return None
            if self.authority._closed:
                raise SourceConflict("Authority is stopping; no new verification may start.")
            proposal = self.proposals.inspect(value["replacement_id"])
            self._check_plan(plan, proposal)
            if sorted(f["file_id"] for f in value["files"]) != sorted(proposal["mapping"].values()):
                raise SourceConflict("Verification must cover the complete sealed proposal.")
            self.dal.transition(
                verification_id=value["plan_id"],
                replacement_id=value["replacement_id"],
                session_id=self.authority.session_id,
                account=value["account"],
                action="begin",
                plan=plan,
                actor=actor,
                reason=reason,
            )
            snapshot, retained = self._snapshot(value["plan_id"])
            if retained.document != plan.document or snapshot["attempt"]["State"] != "checking":
                raise SourceConflict("Fresh verification claim differs from its acknowledged plan.")
            claim = dict(snapshot["preparation"])
            claim["RequestHash"] = bytes.fromhex(claim["RequestHash"])
            claim["ResourcesJson"] = json.dumps(
                [dict(key=r["ResourceKey"], version=r["Version"]) for r in snapshot["resources"]]
            )

            def guard():
                if self.authority._closed:
                    raise SourceConflict("Authority is stopping; verification dispatch is closed.")
                if self.authority.dispatch_guard is not None:
                    self.authority.dispatch_guard()

            worker = ExportExecutionAuthority(
                dal=self.authority.dal,
                store=self.authority.store,
                host=self.authority.host,
                budget_factory=self.authority.budget_factory,
                session_id=self.authority.session_id,
                enrollment_plan=plan,
                dispatch_guard=guard,
            )
            # Retain the owned child even if opening or closing loses its reply.
            self.authority._replacement_readers[value["plan_id"]] = worker
            return worker, claim

    def run(self, plan, *, actor, reason):
        admitted = self._admit(plan, actor=actor, reason=reason)
        if admitted is not None:
            self._run_owned(plan, *admitted)
        return self.inspect(plan.value()["plan_id"])

    def start(self, plan, *, actor, reason):
        """Acknowledge the durable claim promptly; never redispatch an existing ID."""
        with self.authority._lock:
            admitted = self._admit(plan, actor=actor, reason=reason)
            if admitted is not None:
                key = plan.value()["plan_id"]

                def work():
                    try:
                        self._run_owned(plan, *admitted)
                    except Exception:
                        # SQL retains the original checking attempt. The guided
                        # controls inspect its ledger and offer finish/discard.
                        logger.warning("Replacement verification requires investigation: %s", key)

                thread = threading.Thread(target=work, name="replacement-check-" + key, daemon=True)
                self.authority._replacement_threads[key] = thread
                thread.start()
            return self.inspect(plan.value()["plan_id"])

    def _run_owned(self, plan, worker, claim):
        stream_id = str(uuid4())
        try:
            worker.open_stream(stream_id=stream_id, scope=enrollment_scope(plan, claim))
            for policy in plan.value()["files"]:

                def request(operation, arguments):
                    typed = ProviderRequest.parse(
                        dict(
                            version=1,
                            request_id=str(uuid4()),
                            stream_id=stream_id,
                            operation=operation,
                            target=policy["file_id"],
                            arguments=arguments,
                        ),
                        enrollment=True,
                    )
                    return worker.execute(typed.message())

                grid = discovered_grid(policy["file_id"], request(*METADATA))
                responses = [request(op, args) for op, args in replacement_requests(grid)]
                replacement_readback(plan, policy, grid, responses)
        finally:
            if stream_id in worker._streams:
                worker.close_stream(stream_id)
        return self.finish(plan.value()["plan_id"])

    def _evidence(self, plan, snapshot):
        if len(snapshot["streams"]) != 1:
            raise SourceConflict("One complete verification stream is required.")
        stream = snapshot["streams"][0]
        sealed = ReplacementVerificationEvidence(
            dal=self.authority.dal, store=self.authority.store
        ).eligibility(plan, identity(stream["StreamID"]))
        proposal = self.proposals.inspect(plan.value()["replacement_id"])
        pool_files = {
            f
            for pool in self.proposals.registration.value()["pools"]
            for f in (pool["index_file_id"], *pool["slot_file_ids"])
        }
        if set(proposal["mapping"]) & pool_files and any(
            file["title"] != "Sheet1" for file in sealed["files"]
        ):
            raise SourceConflict(
                "Each replacement report-pool file needs one blank worksheet named Sheet1. Correct the worksheet name, discard this read check, then choose Check replacement files again."
            )
        return stream, sealed

    def _persist(self, audit):
        raw = encode(audit)
        receipt = self.authority.store.put(raw)
        reference = identity(receipt.key)
        if self.authority.store.read_reference(reference, bytes.fromhex(receipt.sha256)) != raw:
            raise SourceConflict("Private replacement verification receipt did not verify.")
        return dict(reference=reference, sha256=receipt.sha256)

    def finish(self, verification_id):
        with self.authority._lock:
            snapshot, plan = self._snapshot(verification_id)
            if snapshot["attempt"]["State"] != "checking":
                return self.inspect(verification_id)
            stream, evidence = self._evidence(plan, snapshot)
            audit = dict(
                kind="export_replacement_verification/1",
                before=snapshot,
                evidence=evidence,
                outcome="verified",
                provider_observation=True,
            )
            receipt = self._persist(audit)
            self.dal.transition(
                verification_id=verification_id,
                replacement_id=plan.value()["replacement_id"],
                session_id=self.authority.session_id,
                account=plan.value()["account"],
                action="verify",
                receipt=receipt,
                stream=stream,
                ledger=dict(
                    last_sequence=stream["LastSequence"], event_digest=stream["EventDigest"]
                ),
            )
            return self.inspect(verification_id)

    def discard(self, verification_id, *, token, actor, reason):
        """An explicit admin decision, never an automatic timeout release."""
        if not isinstance(actor, str) or actor != "recovery:" + identity(
            actor.removeprefix("recovery:")
        ):
            raise SourceConflict("Durable admin discard action required.")
        if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 512:
            raise SourceConflict("Bounded discard reason required.")
        with self.authority._lock:
            snapshot, plan = self._snapshot(verification_id)
            if snapshot["attempt"]["State"] == "discarded":
                result = self.inspect(verification_id)
                if result["actor"] != actor or result["reason"] != reason:
                    raise SourceConflict("Another admin action owns this discard.")
                return result
            if snapshot["attempt"]["State"] != "checking" or digest(snapshot).hex() != token:
                raise SourceConflict("Verification evidence changed; review the current check.")
            if len(snapshot["streams"]) > 1:
                raise SourceConflict("Unexpected verification stream membership.")
            ledger, stream = None, None
            if snapshot["streams"]:
                stream = snapshot["streams"][0]
                current = self.authority.dal.read_stream(identity(stream["StreamID"]))
                if stream_wire(current) != stream_wire(stream):
                    raise SourceConflict("Verification stream changed during investigation.")
                ledger = read_ledger(self.authority.dal, current)
            if self._snapshot(verification_id)[0] != snapshot:
                raise SourceConflict("Verification ownership changed during investigation.")
            receipt = self._persist(
                dict(
                    kind="export_replacement_read_discard/1",
                    before=snapshot,
                    ledger=ledger,
                    actor=actor,
                    reason=reason,
                    provider_observation=False,
                    child_termination_verified=False,
                )
            )
            self.dal.transition(
                verification_id=verification_id,
                replacement_id=plan.value()["replacement_id"],
                session_id=self.authority.session_id,
                account=plan.value()["account"],
                action="discard",
                receipt=receipt,
                stream=stream,
                ledger=ledger,
            )
            return self.inspect(verification_id)

    def inspect(self, verification_id):
        found = self._snapshot(verification_id)
        if found is None:
            return None
        snapshot, plan = found
        attempt = snapshot["attempt"]
        result = dict(
            verification_id=verification_id,
            replacement_id=attempt["ReplacementID"],
            state=attempt["State"],
            token=digest(snapshot).hex(),
            files=[],
            actor=attempt["Actor"],
            reason=attempt["Reason"],
        )
        if attempt["State"] == "checking":
            completed = min(
                plan.value()["file_count"],
                sum(s["LastSequence"] for s in snapshot["streams"]) // 5,
            )
            result.update(
                can_finish=False,
                files_requested=completed,
                files_total=plan.value()["file_count"],
                diagnostic="The original read check has not produced a complete verified journal.",
            )
            if snapshot["streams"] and all(s["State"] == "closed" for s in snapshot["streams"]):
                try:
                    self._evidence(plan, snapshot)
                    result.update(
                        can_finish=True,
                        diagnostic="The original readback is complete and can be settled without another provider request.",
                    )
                except SourceConflict as exc:
                    result["diagnostic"] = str(exc)[:512]
            return result
        raw = self.proposals._read_receipt(attempt["ReceiptReference"], attempt["ReceiptHash"])
        if hashlib.sha256(raw).hexdigest() != attempt["ReceiptHash"]:
            raise SourceConflict("Replacement verification receipt hash differs.")
        audit = decode(raw)
        before = audit.get("before", {})
        if (
            before.get("attempt", {}).get("VerificationID") != verification_id
            or before.get("preparation", {}).get("RequestJson") != plan.sql_json
            or before.get("attempt", {}).get("State") != "checking"
            or snapshot["preparation"]["Version"] != before["preparation"]["Version"] + 1
            or snapshot["preparation"]["State"]
            != ("completed" if attempt["State"] == "verified" else "unavailable")
            or any(
                identity(r["ActivePreparationID"]) == verification_id
                for r in snapshot["resources"]
                if r["ActivePreparationID"] is not None
            )
        ):
            raise SourceConflict("Verification settlement differs from its private receipt.")
        if attempt["State"] == "verified":
            if (
                audit.get("kind") != "export_replacement_verification/1"
                or audit.get("provider_observation") is not True
            ):
                raise SourceConflict("Successful replacement observation is unproven.")
            _, actual = self._evidence(plan, snapshot)
            if actual != audit["evidence"]:
                raise SourceConflict("Replacement readback differs from its original receipt.")
            result["files"] = actual["files"]
        else:
            if (
                audit.get("kind") != "export_replacement_read_discard/1"
                or audit.get("provider_observation") is not False
                or audit.get("child_termination_verified") is not False
            ):
                raise SourceConflict("Read discard cannot assert provider success or termination.")
            if snapshot["streams"]:
                stream = snapshot["streams"][0]
                if (
                    stream["State"] != "read_contained"
                    or stream["ActiveAccountKey"] is not None
                    or identity(stream["ClosureReference"]) != attempt["ReceiptReference"]
                    or stream["ClosureHash"] != attempt["ReceiptHash"]
                    or stream["EventDigest"] != audit["ledger"]["event_digest"]
                    or stream["Version"] != before["streams"][0]["Version"] + 1
                ):
                    raise SourceConflict("Discarded read dispatch fence does not verify.")
            result.update(actor=audit["actor"], reason=audit["reason"])
        return result
