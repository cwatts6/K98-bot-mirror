"""Abandon obsolete legacy output without retiring its spreadsheet URLs."""

from dataclasses import asdict
import json

from core.export_execution_host import HostBoundaryError
from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_read_containment import stream_wire
from services.export_coordination_dal import identity
from services.export_execution_protocol import decode, encode
from services.export_reconciliation_service import ClosedStreamVerifier
from services.legacy_export_snapshot_service import configuration_digest

ACTION = "allow_next_export"


class HistoricalStream:
    """Read the sealed original stream without changing its current disabled state."""

    def __init__(self, execution, current, original):
        self.execution, self.current, self.original = execution, current, original

    def __getattr__(self, name):
        return getattr(self.execution, name)

    def read_stream(self, stream_id):
        if (
            stream_id != self.current["StreamID"]
            or stream_wire(self.execution.read_stream(stream_id)) != self.current
        ):
            raise SourceConflict("Contained stream changed during original closure verification.")
        raw = dict(self.original)
        for key in ("RegistrationHash", "ClosureHash", "EventDigest", "SnapshotHash"):
            if raw.get(key) is not None:
                raw[key] = bytes.fromhex(raw[key])
        return raw


class LegacyExportCloseout:
    def __init__(self, *, dal, execution, store, registration, registrations=()):
        self.dal, self.execution, self.store, self.registration = (
            dal,
            execution,
            store,
            registration,
        )
        self.registrations = (*registrations, registration)

    def _original(self, state, stream):
        if stream["State"] != "target_contained":
            return self.execution
        receipt = state["receipt"]
        if receipt is None:
            raise SourceConflict("Original containment decision is missing.")
        audit = decode(
            self.store.read_reference(
                identity(receipt["ReceiptReference"]), bytes.fromhex(receipt["ReceiptHash"])
            )
        )
        before = audit["before"]
        originals = {s["StreamID"]: s for s in before["streams"]}
        original = originals[stream["StreamID"]]
        changed = {
            "State",
            "Version",
            "ActiveAccountKey",
            "ClosureHash",
            "ClosureReference",
            "EventDigest",
            "ClosedUTC",
        }
        if (
            audit["kind"] != "export_target_containment/1"
            or audit["containment_id"] != receipt["ContainmentID"]
            or audit["token"] != receipt["SnapshotHash"]
            or digest(dict(snapshot=before, seals=audit["seals"])).hex() != audit["token"]
            or before["job"]["JobID"] != state["job"]["JobID"]
            or original["State"] != "closed"
            or stream["Version"] != original["Version"] + 1
            or stream["ClosureReference"] != receipt["ReceiptReference"]
            or stream["ClosureHash"] != receipt["ReceiptHash"]
            or {k: v for k, v in stream.items() if k not in changed}
            != {k: v for k, v in original.items() if k not in changed}
            or set(originals) != {s["StreamID"] for s in state["streams"]}
            or audit["targets"] != [r["FileID"] for r in state["contained_targets"]]
            or stream["EventDigest"] != audit["seals"][stream["StreamID"]]["event_digest"]
        ):
            raise SourceConflict("Contained execution lacks a matching original closed stream.")
        return HistoricalStream(self.execution, stream, original)

    def _proofs(self, state):
        job = state["job"]
        registration = self.registration
        provenance = json.loads(job["ProvenanceJson"])
        if state["closeout"] is not None:
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
                raise SourceConflict("Original configuration is absent from authenticated history.")
        elif state.get("foreign_streams"):
            raise SourceConflict("Another execution currently owns this account.")
        registered = registration.value()
        configs = [
            c
            for c in registered["legacy_configuration"].values()
            if c["consumer"] == job["ConsumerKind"]
        ]
        targets = sorted(k[12:] for k in state["membership"] if k.startswith("destination:"))
        if (
            job["ConsumerKind"] not in {"scan_data", "all_kvk"}
            or job["AccountKey"] != registered["account"]
            or job["StorageOwner"] != registered["storage_owner"]
            or len(configs) != 1
            or configuration_digest(configs[0]) != provenance.get("registration_sha256")
            or sorted(configs[0]["destinations"]) != targets
            or not targets
            or digest(targets).hex() != job["DestinationSetHash"]
            or state["membership"]
            != ["account:" + job["AccountKey"], *("destination:" + t for t in targets)]
            or not 1 <= len(state["streams"]) <= 4096
            or state["replacements"]
        ):
            raise SourceConflict(
                "Original configuration, target membership or replacement work differs."
            )
        principals = {r["SessionID"]: r["AuthorityPrincipal"] for r in state["sessions"]}
        proofs = []
        for stream in state["streams"]:
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
                or stream["ActiveAccountKey"] is not None
                or stream["State"] not in {"closed", "target_contained"}
                or stream["Purpose"] not in {"mutation", "probe"}
                or any(
                    stream[k] is not None
                    for k in ("PreparationID", "OutputOperationID", "NestedToken", "Epoch")
                )
                or principals.get(stream["SessionID"]) != state["principal"]
                or stream["ClaimVersion"] >= job["Version"]
                or stream_wire(self.execution.read_stream(stream["StreamID"])) != stream
            ):
                raise SourceConflict(
                    "Original writer is not verifiably stopped in its registered scope."
                )
            scope = json.loads(stream["ScopeJson"])
            if sorted(r["key"] for r in scope["resources"]) != state["membership"]:
                raise SourceConflict("Original stream resource scope differs.")
            registration.authorize_scope(
                dict(
                    AccountKey=job["AccountKey"],
                    OwnerKind="job",
                    Purpose=stream["Purpose"],
                    RegistrationHash=stream["RegistrationHash"],
                    ScopeJson=scope,
                    Epoch=None,
                    NestedToken=None,
                )
            )
            verifier = ClosedStreamVerifier(dal=self._original(state, stream), store=self.store)
            proof = verifier.verify(
                stream["StreamID"],
                account=job["AccountKey"],
                registration_hash=bytes.fromhex(stream["RegistrationHash"]),
                require_observation=False,
            )
            proofs.append(asdict(proof))
        return proofs

    def _read(self, job_id):
        state = self.dal.snapshot(job_id)
        proofs = self._proofs(state)
        if self.dal.snapshot(job_id) != state:
            raise SourceConflict("Export evidence changed during verification.")
        return state, proofs

    def _receipt(self, state, proofs):
        receipt = state["closeout"]
        if receipt is None:
            return None
        body = decode(
            self.store.read_reference(
                identity(receipt["ReceiptReference"]), bytes.fromhex(receipt["ReceiptHash"])
            )
        )
        original = body["original"]
        job = state["job"]
        expected = dict(
            original["job"],
            State="failed",
            Version=original["job"]["Version"] + 1,
            UpdatedUTC=job["UpdatedUTC"],
        )
        if (
            body["kind"] != "legacy_export_closeout/1"
            or expected != job
            or body["proofs"] != proofs
            or body["token"] != receipt["SnapshotHash"]
            or digest(original).hex() != body["token"]
            or body["action_id"] != receipt["ActionID"]
            or receipt["JobID"] != job["JobID"]
            or body["actor"] != receipt["Actor"]
            or body["reason"] != receipt["Reason"]
            or receipt["Actor"] != "recovery:" + receipt["ActionID"]
            or receipt["OwnerVersion"] != original["job"]["Version"]
            or receipt["AccountKey"] != job["AccountKey"]
            or receipt["ContainmentID"]
            != (original["receipt"]["ContainmentID"] if original["receipt"] else None)
            or any(
                state[k] != original[k]
                for k in ("membership", "streams", "attempts", "contained_targets")
            )
            or any(r["ActiveJobID"] == job["JobID"] for r in state["resources"])
        ):
            raise SourceConflict("Independent closeout readback does not match the saved decision.")
        return body

    def inspect(self, job_id):
        state = self.dal.snapshot(job_id)
        actions, resolved = {}, False
        explanation = "The old export still needs verified execution evidence before its write restriction can be lifted. Keep the existing spreadsheet URLs."
        try:
            checked, proofs = self._read(job_id)
            if checked != state:
                raise SourceConflict("Review changed during verification.")
            resolved = self._receipt(state, proofs) is not None
            if resolved:
                explanation = "The old partial export was abandoned. The same spreadsheet URLs are available for a later normal export. The committed import and reports are unchanged; no new delivery is certified."
            else:
                job = state["job"]
                if job["State"] not in {"failed", "uncertain"} or json.loads(
                    job["ProvenanceJson"]
                ).get("safe_retry", {}).get("requested"):
                    raise SourceConflict("Another decision or live job prevents closeout.")
                if any(
                    r["ActivePreparationID"] is not None
                    or r["ActiveOutputOperationID"] is not None
                    or (r["ActiveJobID"] is not None and r["ActiveJobID"] != job_id)
                    for r in state["resources"]
                ):
                    raise SourceConflict(
                        "Another operation currently owns access to these outputs."
                    )
                explanation = "Every original request and worker closure verifies. Leave this partial export in history and allow a later normal export to overwrite the same spreadsheet URLs."
                actions[ACTION] = dict(
                    label="Allow next export",
                    check="Confirm this old export is no longer needed. The next normal scan will refresh the same spreadsheet URLs; until then the sheets may contain mixed scan results.",
                    effect="Save this decision, keep the old execution disabled, and lift only its verified write restriction. No spreadsheet is replaced, no import/report is rerun, and no export is dispatched by this action.",
                )
        except (HostBoundaryError, SourceConflict, ValueError, KeyError, TypeError, OSError) as exc:
            explanation += " " + (
                str(exc)
                if isinstance(exc, SourceConflict)
                else "Private recovery evidence is incomplete."
            )
        return (
            dict(
                title="Allow the next export to existing sheets",
                outcome="abandoned" if resolved else "closeout_review_required",
                explanation=explanation,
                actions=actions,
            ),
            digest(state).hex(),
            resolved,
        )

    def execute(self, job_id, action, token, actor, reason, *, payload=None):
        if (
            action != ACTION
            or payload is not None
            or not isinstance(actor, str)
            or not actor.startswith("recovery:")
        ):
            raise SourceConflict("Exact confirmed closeout required.")
        action_id = identity(actor[9:])
        if (
            actor != "recovery:" + action_id
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise SourceConflict("Bounded recovery actor and reason required.")
        state, proofs = self._read(job_id)
        if state["closeout"] is not None or digest(state).hex() != token:
            raise SourceConflict("Closeout evidence changed; review the current decision.")
        evidence, current, _ = self.inspect(job_id)
        if current != token or ACTION not in evidence["actions"]:
            raise SourceConflict("Closeout is not currently available.")
        raw = encode(
            dict(
                kind="legacy_export_closeout/1",
                original=state,
                proofs=proofs,
                token=token,
                action_id=action_id,
                actor=actor,
                reason=reason,
            )
        )
        saved = self.store.put(raw)
        marker = dict(reference=identity(saved.key), sha256=saved.sha256)
        if self.store.read_reference(marker["reference"], bytes.fromhex(marker["sha256"])) != raw:
            raise SourceConflict("Private closeout decision did not verify.")
        self.dal.settle(
            state, action_id=action_id, token=token, marker=marker, actor=actor, reason=reason
        )

    def reconcile(self, job_id, action):
        if action["ActionKind"] != ACTION or action.get("InputJson") is not None:
            raise SourceConflict("Exact saved closeout action required.")
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
            ACTION,
            action["EvidenceHash"],
            "recovery:" + action["ActionID"],
            action["Reason"],
        )
        return None
