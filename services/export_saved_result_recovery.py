"""Settle one retained mutation result, reseal and abandon an exact partial export.

The protected runner supplies an authenticated target and durable private journal.
Projected history is used ONLY for preflight through the existing full verifier;
SQL receipts, never that projection, decide whether an action committed.
"""

from contextlib import closing
from copy import deepcopy
import hashlib
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_read_containment import stream_wire
from services.export_coordination_dal import identity
from services.export_execution_protocol import decode, encode, uuid_text
from services.export_saved_result_recovery_dal import RecoveryWaiting, journal_digest
from services.legacy_export_closeout import LegacyExportCloseout


def run_saved_recovery(service, review, token, connections, *, clock, sleep, notify):
    """Owned retry of exact steps; optional progress output cannot change outcome."""
    started = clock()
    delay = 0.25
    warned = False
    while True:
        try:
            result = connections.checkpoint(lambda: service.step(review, token))
            if result["stage"] == "PARTIAL_EXPORT_CLOSED":
                return result
            started, delay, warned = clock(), 0.25, False
        except RecoveryWaiting:
            service.check_boundary()
            elapsed = clock() - started
            if elapsed >= 300 and not warned:
                try:
                    notify(
                        dict(
                            stage="RECOVERY_WAITING",
                            progress="no_confirmed_progress_for_five_minutes",
                        )
                    )
                except Exception:
                    pass  # Optional presentation must not invalidate retained work.
                warned = True
            sleep(30 if elapsed > 15 else delay)
            delay = min(delay * 2, 5)


class ProjectedHistory:
    """Recovery-only validation of the sole missing terminal event and renewed seal."""

    def __init__(self, execution, store, stream, target, event):
        self.execution, self.store = execution, store
        self.stream, self.target, self.event = deepcopy(stream), target, event
        self.document = None

    def request_records(self, stream_id, *, original=False):
        if stream_id != self.target["stream_id"]:
            raise SourceConflict("Foreign recovery history.")
        found = False
        with closing(self.execution.request_records(stream_id)) as records:
            for identifier, request, events in records:
                if identifier == self.target["request_id"]:
                    found = True
                    if request["Sequence"] != self.target["last_sequence"]:
                        raise SourceConflict("Only the last outstanding request may settle.")
                    if [e["State"] for e in events] == ["prepared", "dispatch_intent", "succeeded"]:
                        if any(
                            events[-1][k] != v
                            for k, v in self.event.items()
                            if k not in {"EventID", "RequestID", "EvidenceReference"}
                        ):
                            raise SourceConflict("Saved terminal event differs.")
                        if any(
                            str(events[-1][k]).lower() != self.event[k]
                            for k in ("EventID", "RequestID", "EvidenceReference")
                        ):
                            raise SourceConflict("Saved terminal identity differs.")
                        events = events[:-1]
                    if [e["State"] for e in events] != ["prepared", "dispatch_intent"]:
                        raise SourceConflict("Exact unresolved dispatched request required.")
                    events = list(events) if original else [*events, self.event]
                yield identifier, request, events
        if not found:
            raise SourceConflict("Retained response request is absent.")

    def stream_digest(self, stream_id):
        return journal_digest(self.request_records(stream_id))

    def read_stream(self, stream_id):
        if stream_id != self.target["stream_id"]:
            raise SourceConflict("Foreign projected stream.")
        return deepcopy(self.stream)

    def read_reference(self, reference, expected_hash):
        if str(reference).lower() == self.stream["ClosureReference"]:
            raw = encode(self.document)
            if hashlib.sha256(raw).digest() != bytes(expected_hash):
                raise SourceConflict("Projected closure digest differs.")
            return raw
        return self.store.read_reference(reference, expected_hash)


class SavedResultRecovery:
    def __init__(self, *, closeout, execution, store, journal, check_boundary, target):
        self.closeout, self.execution, self.store = closeout, execution, store
        self.journal, self.check_boundary, self.target = journal, check_boundary, deepcopy(target)
        for key in (
            "job_id",
            "owner_id",
            "session_id",
            "stream_id",
            "child_id",
            "request_id",
            "response_reference",
            "closure_reference",
        ):
            uuid_text(target[key])
        for key in ("response_sha256", "closure_sha256", "registration_sha256", "manifest_sha256"):
            value = target[key]
            if (
                not isinstance(value, str)
                or len(value) != 64
                or bytes.fromhex(value).hex() != value
            ):
                raise ValueError("Canonical recovery hash required.")
        for key in ("fence", "job_version", "stream_version", "last_sequence"):
            if type(target[key]) is not int or target[key] <= 0:
                raise ValueError("Positive exact recovery version required.")

    @staticmethod
    def token(review):
        return digest(review).hex()

    def _document(self, reference, sha256):
        return decode(self.store.read_reference(reference, bytes.fromhex(sha256)))

    def _snapshot(self):
        self.check_boundary()
        return self.closeout.dal.snapshot(self.target["job_id"])

    def _initial(self, state):
        t, job = self.target, state["job"]
        if len(state["streams"]) != 1:
            raise SourceConflict("One exact original stream required.")
        s = state["streams"][0]
        if s["RegistrationHash"] != t["registration_sha256"] or json.loads(
            job["ProvenanceJson"]
        ).get("safe_retry", {}).get("requested"):
            raise SourceConflict("Registered recovery scope or retry decision differs.")
        if (job["JobID"], job["OwnerID"], job["Fence"], job["Version"], job["State"]) != (
            t["job_id"],
            t["owner_id"],
            t["fence"],
            t["job_version"],
            "uncertain",
        ):
            raise SourceConflict("Exact uncertain job required.")
        if (
            s["StreamID"],
            s["SessionID"],
            s["ChildIdentity"],
            s["Version"],
            s["LastSequence"],
            s["State"],
            s["Purpose"],
        ) != (
            t["stream_id"],
            t["session_id"],
            t["child_id"],
            t["stream_version"],
            t["last_sequence"],
            "frozen",
            "mutation",
        ) or s[
            "ActiveAccountKey"
        ] != job[
            "AccountKey"
        ]:
            raise SourceConflict("Exact frozen mutation stream required.")
        if any(
            s[k] is not None
            for k in ("ClosureHash", "ClosureReference", "EventDigest", "ClosedUTC")
        ):
            raise SourceConflict("Unsealed original stream required.")
        if any(
            state.get(k)
            for k in ("closeout", "receipt", "foreign_streams", "contained_targets", "replacements")
        ):
            raise SourceConflict("Another recovery or writer prevents adoption.")
        if any(
            r["ActiveJobID"] != job["JobID"]
            or r["OwnerID"] != job["OwnerID"]
            or r["Fence"] != job["Fence"]
            or r["ActivePreparationID"] is not None
            or r["ActiveOutputOperationID"] is not None
            for r in state["resources"]
        ):
            raise SourceConflict("Exact original resource ownership required.")
        self._session(state)

    def _session(self, state):
        session = self.execution.read_session(self.target["session_id"])
        if (
            session is None
            or session["State"] != "open"
            or (
                session["AuthorityPrincipal"] != state["principal"]
                or bytes(session["ManifestHash"]).hex() != self.target["manifest_sha256"]
                or str(session["SessionID"]).lower() != self.target["session_id"]
            )
        ):
            raise SourceConflict("Pinned original authority session required.")

    def _proof(self, original, event_id):
        t = self.target
        old = self._document(t["closure_reference"], t["closure_sha256"])
        observed = old.get("closure", {})
        if (
            (old.get("stream_id"), old.get("version"), old.get("last_sequence"))
            != (t["stream_id"], t["stream_version"], t["last_sequence"])
            or observed.get("child_id") != t["child_id"]
            or observed.get("job_empty") is not True
            or observed.get("process_signaled") is not True
            or observed.get("termination_method") is not None
        ):
            raise SourceConflict("Original stopped-child seal differs.")
        event = dict(
            EventID=event_id,
            RequestID=t["request_id"],
            EventSequence=3,
            State="succeeded",
            EvidenceHash=bytes.fromhex(t["response_sha256"]),
            EvidenceReference=t["response_reference"],
        )
        raw = self.execution.read_stream(t["stream_id"])
        projected = ProjectedHistory(self.execution, self.store, raw, t, event)
        count, original_digest = journal_digest(
            projected.request_records(t["stream_id"], original=True)
        )
        if count != t["last_sequence"] or original_digest.hex() != old.get("event_digest"):
            raise SourceConflict("Original complete journal differs from retained seal.")
        count, renewed = projected.stream_digest(t["stream_id"])
        document = dict(old, version=t["stream_version"] + 1, event_digest=renewed.hex())
        reference = str(uuid4())  # Virtual preflight seal only; never an SQL receipt.
        projected.stream.update(
            State="closed",
            ActiveAccountKey=None,
            Version=t["stream_version"] + 2,
            ClosureReference=reference,
            ClosureHash=hashlib.sha256(encode(document)).digest(),
            EventDigest=renewed,
        )
        projected.document = document
        state = deepcopy(original)
        state["streams"] = [stream_wire(projected.stream)]
        checker = LegacyExportCloseout(
            dal=self.closeout.dal,
            execution=projected,
            store=projected,
            registration=self.closeout.registration,
        )
        checker._proofs(state)  # Full payload/result/history/registration validation, unchanged.
        return event, document

    def inspect(self):
        original = self._snapshot()
        self._initial(original)
        _, events = self.execution.read_request(self.target["request_id"])
        if [e["State"] for e in events] != ["prepared", "dispatch_intent"]:
            raise SourceConflict("Inspect requires the missing terminal event.")
        self._proof(original, str(uuid4()))
        if self._snapshot() != original:
            raise SourceConflict("Recovery state changed during private verification.")
        return dict(kind="saved_result_recovery/1", target=self.target, original=original)

    def _save(self, document):
        raw = encode(document)
        saved = self.store.put(raw)
        marker = dict(reference=identity(saved.key), sha256=saved.sha256)
        if self.store.read_reference(marker["reference"], bytes.fromhex(marker["sha256"])) != raw:
            raise SourceConflict("Recovery document did not read back.")
        return marker

    def step(self, review, token):
        """One owned resumable step. Caller reschedules only after exact revalidation."""
        if (
            token != self.token(review)
            or review["target"] != self.target
            or review["kind"] != "saved_result_recovery/1"
        ):
            raise SourceConflict("Exact accepted recovery review required.")
        self.check_boundary()
        original = review["original"]
        self._initial(original)
        intent = self.journal.read("intent")
        if intent is None:
            if self._snapshot() != original:
                raise SourceConflict("Original recovery state changed before intent.")
            intent = dict(token=token, event_id=str(uuid4()), action_id=str(uuid4()))
            self.journal.write("intent", intent)
        if intent["token"] != token:
            raise SourceConflict("Recovery intent belongs to another review.")
        uuid_text(intent["event_id"])
        uuid_text(intent["action_id"])
        state = self._snapshot()
        closeout_intent = self.journal.read("closeout-intent")
        if state["closeout"] is not None:
            if closeout_intent is None:
                raise SourceConflict("Unowned closeout receipt.")
            checked, proofs = self.closeout._read(self.target["job_id"])
            body = self.closeout._receipt(checked, proofs)
            if body != closeout_intent["body"]:
                raise SourceConflict("Closeout receipt differs from accepted intent.")
            result = dict(
                stage="PARTIAL_EXPORT_CLOSED",
                job_id=self.target["job_id"],
                action_id=intent["action_id"],
                provider_requests=0,
            )
            self.journal.write("verified", result)
            return result
        event, closure = self._proof(original, intent["event_id"])
        s = state["streams"][0] if len(state["streams"]) == 1 else {}
        expected = deepcopy(original)
        expected_stream = expected["streams"][0]
        version = s.get("Version")
        if version == self.target["stream_version"]:
            if state != original:
                raise SourceConflict("Original recovery state changed.")
            self.check_boundary()
            self.execution.checked_transition(
                state,
                "event",
                SessionID=self.target["session_id"],
                StreamID=self.target["stream_id"],
                AccountKey=state["job"]["AccountKey"],
                ExpectedVersion=version,
                **{k: v for k, v in event.items() if k != "EventSequence"},
            )
            return dict(stage="RESULT_RECORDED")
        expected_stream["Version"] += 1
        if version == self.target["stream_version"] + 1:
            if state != expected:
                raise SourceConflict("Recovery changed beyond the exact result append.")
            saved = self.journal.read("closure")
            if saved is None:
                saved = self._save(closure)
                self.journal.write("closure", saved)
            if self._document(saved["reference"], saved["sha256"]) != closure:
                raise SourceConflict("Renewed closure changed.")
            self.check_boundary()
            self.execution.checked_transition(
                state,
                "stream",
                SessionID=self.target["session_id"],
                StreamID=self.target["stream_id"],
                AccountKey=state["job"]["AccountKey"],
                Action="close",
                ExpectedVersion=version,
                ChildIdentity=self.target["child_id"],
                LastSequence=self.target["last_sequence"],
                EventDigest=bytes.fromhex(closure["event_digest"]),
                ClosureHash=bytes.fromhex(saved["sha256"]),
                ClosureReference=saved["reference"],
            )
            return dict(stage="STREAM_CLOSED")
        saved = self.journal.read("closure")
        if saved is None:
            raise SourceConflict("Renewed closure intent missing.")
        expected_stream.update(
            Version=self.target["stream_version"] + 2,
            State="closed",
            ActiveAccountKey=None,
            ClosureReference=saved["reference"],
            ClosureHash=saved["sha256"],
            EventDigest=closure["event_digest"],
            ClosedUTC=s.get("ClosedUTC"),
        )
        if state != expected or not s.get("ClosedUTC"):
            raise SourceConflict("Closed recovery state differs.")
        checked, proofs = self.closeout._read(self.target["job_id"])
        if checked != state:
            raise SourceConflict("Closeout state changed during verification.")
        if closeout_intent is None:
            body = dict(
                kind="legacy_export_closeout/1",
                original=state,
                proofs=proofs,
                token=digest(state).hex(),
                action_id=intent["action_id"],
                actor="recovery:" + intent["action_id"],
                reason="Abandon the reviewed partial export; retain existing URLs.",
            )
            closeout_intent = dict(body=body, marker=self._save(body))
            self.journal.write("closeout-intent", closeout_intent)
        body = closeout_intent["body"]
        if (
            body["original"] != state
            or body["proofs"] != proofs
            or body["action_id"] != intent["action_id"]
            or self._document(
                **dict(
                    reference=closeout_intent["marker"]["reference"],
                    sha256=closeout_intent["marker"]["sha256"],
                )
            )
            != body
        ):
            raise SourceConflict("Saved closeout decision differs.")
        # _initial + exact state comparison preserve uncertain/no-safe-retry and
        # exact owned membership; _read above supplies full real closure proofs.
        # Calling inspect here would repeat that entire private history twice.
        if digest(state).hex() != body["token"]:
            raise SourceConflict("Exact legacy closeout is not eligible.")
        self.check_boundary()
        self.closeout.dal.settle(
            state,
            action_id=body["action_id"],
            token=body["token"],
            marker=closeout_intent["marker"],
            actor=body["actor"],
            reason=body["reason"],
        )
        return dict(stage="CLOSEOUT_RECORDED")
