"""Guided retirement only after complete private proof of no dispatched writes."""

from dataclasses import asdict
import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_read_containment import stream_wire
from services.export_coordination_dal import identity
from services.export_execution_protocol import decode, encode
from services.export_failure_diagnostics import recovery_failure_context
from services.export_reconciliation_service import ClosedStreamVerifier
from services.legacy_export_snapshot_service import configuration_digest

ACTION = "retire_failed_export"


class CloseoutBlocked(SourceConflict):
    def __init__(self, code, message):
        super().__init__(message)
        self.recovery_code = code


class FailedExportCloseout:
    def __init__(self, *, dal, execution, store, registrations):
        self.dal, self.execution, self.store = dal, execution, store
        self.registrations = tuple(registrations)

    def _verify(self, state):
        job = state["job"]
        provenance = json.loads(job["ProvenanceJson"])
        if (
            job["State"] != "failed"
            or job["OwnerID"] is None
            or job["Fence"] <= 0
            or state["attempts"]
            or state["held"]
            or not 1 <= len(state["streams"]) <= 4096
            or provenance.get("safe_retry", {}).get("requested")
        ):
            raise CloseoutBlocked(
                "execution_or_access_retained",
                "This closeout requires a failed legacy export with no attempt, held access or requested retry.",
            )
        targets = sorted(k[12:] for k in state["membership"] if k.startswith("destination:"))
        if (
            not targets
            or state["membership"]
            != ["account:" + self.dal.account, *("destination:" + f for f in targets)]
            or digest(targets).hex() != job["DestinationSetHash"]
        ):
            raise CloseoutBlocked(
                "destination_membership_differs",
                "The original export destination membership does not verify.",
            )
        registration = next(
            (
                r
                for r in reversed(self.registrations)
                if any(
                    c["consumer"] == job["ConsumerKind"]
                    and configuration_digest(c) == provenance.get("registration_sha256")
                    for c in r.value()["legacy_configuration"].values()
                )
            ),
            None,
        )
        if registration is None:
            raise CloseoutBlocked(
                "original_configuration_unavailable",
                "Original export configuration is absent from authenticated history.",
            )
        principals = {identity(s["SessionID"]): s["AuthorityPrincipal"] for s in state["sessions"]}
        verifier = ClosedStreamVerifier(dal=self.execution, store=self.store)
        proofs = []
        for stream in state["streams"]:
            if stream_wire(self.execution.read_stream(stream["StreamID"])) != stream:
                raise SourceConflict("The original execution stream changed during verification.")
            if (
                (
                    stream["JobID"],
                    stream["AccountKey"],
                    stream["OwnerID"],
                    stream["Fence"],
                    stream["RegistrationHash"],
                )
                != (
                    job["JobID"],
                    job["AccountKey"],
                    job["OwnerID"],
                    job["Fence"],
                    provenance["registration_sha256"],
                )
                or stream["PreparationID"] is not None
                or stream["OutputOperationID"] is not None
                or stream["Epoch"] is not None
                or stream["NestedToken"] is not None
                or stream["ClaimVersion"] >= job["Version"]
                or principals.get(stream["SessionID"]) != state["principal"]
            ):
                raise SourceConflict("Original stream ownership or authority differs.")
            scope = json.loads(stream["ScopeJson"])
            if sorted(r["key"] for r in scope["resources"]) != state["membership"]:
                raise SourceConflict("Original stream destination scope differs.")
            registration.authorize_scope(
                dict(
                    AccountKey=job["AccountKey"],
                    OwnerKind="job",
                    RegistrationHash=stream["RegistrationHash"],
                    ScopeJson=scope,
                    Epoch=None,
                    NestedToken=None,
                    Purpose=stream["Purpose"],
                )
            )
            proof = verifier.verify(
                stream["StreamID"],
                account=self.dal.account,
                registration_hash=bytes.fromhex(stream["RegistrationHash"]),
                require_observation=False,
                allow_failed_reads=True,
                require_no_writes=True,
            )
            proofs.append(asdict(proof))
        return proofs

    def _read(self, job_id):
        state = self.dal.snapshot(job_id)
        proofs = self._verify(state)
        # Close a race between the locked SQL snapshot and private journal reads.
        if self.dal.snapshot(job_id) != state:
            raise SourceConflict("Export evidence changed during verification.")
        return state, proofs

    def _receipt(self, state, proofs):
        job = state["job"]
        marker = json.loads(job["ProvenanceJson"]).get("failed_export_retired")
        if marker is None:
            return None
        if not isinstance(marker, dict) or set(marker) != {"reference", "sha256"}:
            raise SourceConflict("The saved failed-export decision is malformed.")
        try:
            body = decode(
                self.store.read_reference(
                    identity(marker["reference"]), bytes.fromhex(marker["sha256"])
                )
            )
        except Exception as exc:
            raise SourceConflict("Private failed-export decision is unavailable.") from exc
        original = body["original_job"]
        expected = dict(original)
        original_provenance = json.loads(original["ProvenanceJson"])
        original_provenance["failed_export_retired"] = marker
        expected.update(
            ProvenanceJson=job["ProvenanceJson"],
            Version=original["Version"] + 1,
            UpdatedUTC=job["UpdatedUTC"],
        )
        if (
            body["kind"] != "failed_export_retirement/1"
            or body["job_id"] != job["JobID"]
            or expected != job
            or json.loads(job["ProvenanceJson"]) != original_provenance
            or body["membership"] != state["membership"]
            or body["proofs"] != proofs
            or body["actor"] != "recovery:" + identity(body["action_id"])
        ):
            raise SourceConflict("The failed-export decision does not match independent readback.")
        return body

    def inspect(self, job_id):
        state = self.dal.snapshot(job_id)
        job = state["job"]
        provenance = json.loads(job["ProvenanceJson"])
        context = recovery_failure_context(job, provenance)
        producer = provenance.get("producer", {})
        inputs = producer.get("completed_filename") if isinstance(producer, dict) else None
        filename = (
            inputs
            if isinstance(inputs, str) and re.fullmatch(r"stats_[0-9a-f]{32}\.ready\.csv", inputs)
            else "not recorded"
        )
        context.update(
            original_created_utc=job["CreatedUTC"],
            input_file=filename,
            original_registration_sha256=provenance.get("registration_sha256"),
            input_sha256=job["InputHash"],
        )
        current_configs = self.registrations[-1].value()["legacy_configuration"].values()
        matches_current = any(
            c["consumer"] == job["ConsumerKind"]
            and configuration_digest(c) == provenance.get("registration_sha256")
            for c in current_configs
        )
        context.update(
            configuration_matches_current=matches_current,
            destination_count=sum(k.startswith("destination:") for k in state["membership"]),
        )
        configuration = (
            "matches current" if matches_current else "differs from current or is unavailable"
        )
        context["summary"] = (
            f"Created {job['CreatedUTC']} UTC. Input: {filename}. KVK: {job.get('KVK_NO') or 'not recorded'}. Original configuration {configuration}. "
            + context["summary"]
        )
        actions, resolved = {}, False
        try:
            verified_state, proofs = self._read(job_id)
            if verified_state != state:
                raise SourceConflict("Export identity changed during review. Reopen this incident.")
            receipt = self._receipt(state, proofs)
            resolved = receipt is not None
            explanation = (
                "This obsolete export was retired and independently verified. No provider write was dispatched by its original streams. SQL data and retained input are unchanged; no spreadsheet delivery is certified."
                if resolved
                else "The original children are closed and the complete private journal proves no provider write was dispatched. If this old output is no longer needed, retire it. If still needed, leave it open for retained-input recovery."
            )
            if not resolved:
                actions[ACTION] = dict(
                    label="Retire failed export",
                    check="Confirm this dated export is obsolete. Its SQL data stays intact; its output will not be published. Leave it open if still needed or unidentified.",
                    effect="Reverify every original stream and the exact input/configuration identity, save your decision and independently read it back. No import replay, provider write, resource release or deletion occurs.",
                )
        except (SourceConflict, ValueError, KeyError, TypeError, OSError) as exc:
            code = getattr(exc, "recovery_code", "private_execution_unverified")
            context["closeout_blocker"] = code
            explanation = {
                "execution_or_access_retained": "Execution, held access or a requested retry remains. This export needs its execution/ownership recovery before any retirement can be authorized.",
                "destination_membership_differs": "The saved destination list does not match this export. Its original configuration must be reconciled before retirement is available.",
                "original_configuration_unavailable": "The original export configuration is missing from authenticated history. The bot cannot identify this work safely enough to retire it.",
                "private_execution_unverified": "The complete private journal, original child closure, ownership or saved decision does not verify. A possible write cannot be ruled out. This export remains open for evidence or unknown-write recovery.",
            }[code]
        return (
            dict(
                title="Failed export recovery",
                outcome="retired" if resolved else "failed",
                explanation=explanation,
                actions=actions,
                failure_context=context,
            ),
            digest(state).hex(),
            resolved,
        )

    def execute(self, job_id, action, token, actor, reason, *, payload=None):
        if (
            action != ACTION
            or payload is not None
            or actor != "recovery:" + identity(actor.removeprefix("recovery:"))
        ):
            raise SourceConflict("Exact confirmed failed-export retirement required.")
        if not isinstance(reason, str) or not 1 <= len(reason) <= 512:
            raise SourceConflict("Bounded admin decision reason required.")
        state, proofs = self._read(job_id)
        if digest(state).hex() != token or self._receipt(state, proofs) is not None:
            raise SourceConflict("Failed-export evidence changed; review it again.")
        raw = encode(
            dict(
                kind="failed_export_retirement/1",
                job_id=job_id,
                action_id=actor.removeprefix("recovery:"),
                actor=actor,
                reason=reason,
                token=token,
                original_job=state["job"],
                membership=state["membership"],
                proofs=proofs,
            )
        )
        saved = self.store.put(raw)
        marker = dict(reference=identity(saved.key), sha256=saved.sha256)
        if self.store.read_reference(marker["reference"], bytes.fromhex(marker["sha256"])) != raw:
            raise SourceConflict("Private closeout decision did not verify.")
        self.dal.retire(state, marker)

    def reconcile(self, job_id, action):
        if action["ActionKind"] != ACTION or action.get("InputJson") is not None:
            raise SourceConflict("Exact failed-export retirement decision required.")
        state, proofs = self._read(job_id)
        body = self._receipt(state, proofs)
        if body is not None:
            return (
                "verified"
                if (body["action_id"], body["token"], body["reason"])
                == (action["ActionID"], action["EvidenceHash"], action["Reason"])
                else "not_applied"
            )
        if digest(state).hex() != action["EvidenceHash"]:
            return "not_applied"
        self.execute(
            job_id,
            action["ActionKind"],
            action["EvidenceHash"],
            "recovery:" + action["ActionID"],
            action["Reason"],
        )
        return None
