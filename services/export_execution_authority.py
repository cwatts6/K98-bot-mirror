"""Independent request-journal coordinator, with injected SQL, storage and OS host.

No default clients, credentials or in-memory recovery claims. Each stream belongs
to one exact supervised child. Only its trusted parent can author response events.
"""

from copy import deepcopy
from dataclasses import dataclass
import logging
import threading
from uuid import UUID, uuid4

from services.export_execution_protocol import (
    ProviderRequest,
    ProviderThrottled,
    encode,
    validate_response,
)
from services.export_request_budget import BudgetCompletionUnknown

logger = logging.getLogger(__name__)


class ExecutionUncertain(BudgetCompletionUnknown):
    """Retain SQL ownership and request evidence; never replay the mutation."""


@dataclass
class OwnedStream:
    stream_id: str
    account: str
    version: int
    child: object
    purpose: str
    destinations: frozenset[str]
    frozen: bool = False
    uncertain: bool = False
    closed: bool = False
    enrollment_phase: str | None = None
    enrollment_ordinal: int | None = None
    termination_evidence: dict | None = None
    closure_receipt: object | None = None
    closure_document: dict | None = None


class ExportExecutionAuthority:
    def __init__(
        self,
        *,
        dal,
        store,
        host,
        budget_factory,
        session_id,
        enrollment_plan=None,
        dispatch_guard=None,
    ):
        self.dal, self.store, self.host = dal, store, host
        self.budget_factory, self.session_id = budget_factory, session_id
        self.dispatch_guard = dispatch_guard
        if enrollment_plan is not None:
            from services.export_enrollment_service import EnrollmentPlan

            if not isinstance(enrollment_plan, EnrollmentPlan):
                raise ValueError("Protected typed enrollment plan required.")
        self.enrollment_plan = enrollment_plan
        # SQL owns cross-process exclusion. This lock also serializes local
        # freeze vs dispatch, including the final commit-before-send boundary.
        self._lock = threading.RLock()
        self._streams = {}
        self._closed = False

    def open_stream(self, *, stream_id, scope):
        """Called by the authenticated broker after immutable manifest validation."""
        from services.export_execution_protocol import uuid_text

        if self._closed:
            raise ExecutionUncertain("Authority admission is closed.")
        uuid_text(stream_id)
        expected = {
            "AccountKey",
            "OwnerKind",
            "ObjectID",
            "OwnerID",
            "Fence",
            "ClaimVersion",
            "NestedToken",
            "RegistrationHash",
            "Epoch",
            "SnapshotHash",
            "ScopeJson",
            "Purpose",
        }
        if set(scope) != expected:
            raise ValueError("Complete exact owner scope required.")
        import json

        supplied_scope = json.loads(scope["ScopeJson"])
        expected_detail = (
            {"resources", "enrollment"} if self.enrollment_plan is not None else {"resources"}
        )
        if set(supplied_scope) != expected_detail:
            raise ValueError("Only the registered resource/enrollment scope may be supplied.")
        resources = supplied_scope["resources"]
        destinations = frozenset(
            r["key"].removeprefix("destination:")
            for r in resources
            if r["key"].startswith("destination:")
        )
        enrollment = None
        if self.enrollment_plan is not None:
            enrollment = self.enrollment_plan.authorize_scope(scope)
            if enrollment["phase"] == "create":
                destinations = frozenset({scope["ObjectID"]})
        elif not destinations or scope["Purpose"] not in {"mutation", "probe"}:
            raise ValueError("Registered destinations and explicit stream purpose required.")
        with self._lock:
            if self._closed or stream_id in self._streams:
                raise ExecutionUncertain("Authority closed or stream already known.")
            child = self.host.create_suspended(str(uuid4()))
            stream = OwnedStream(
                stream_id, scope["AccountKey"], 1, child, scope["Purpose"], destinations
            )
            if enrollment is not None:
                stream.enrollment_phase = enrollment["phase"]
                stream.enrollment_ordinal = enrollment["ordinal"]
            # Retain the handle even if SQL's acknowledgment is lost. Do not
            # resume it or infer whether the durable stream exists.
            self._streams[stream_id] = stream
            try:
                birth = getattr(child, "birth_evidence", None)
                if (
                    birth is not None
                    and enrollment is None
                    and scope["OwnerKind"] == "preparation"
                    and scope["Purpose"] == "probe"
                ):
                    from core.export_child_lifecycle import validate_host_birth

                    validate_host_birth(birth)
                    if birth["child_id"] != child.identity:
                        raise ExecutionUncertain("Host birth belongs to another child.")
                    receipt = self.store.put(
                        encode(
                            dict(
                                kind="provider_child_birth/1",
                                stream_id=stream_id,
                                session_id=self.session_id,
                                account=scope["AccountKey"],
                                host=birth,
                            )
                        )
                    )
                    scope = deepcopy(scope)
                    scope["ScopeJson"] = encode(
                        dict(
                            resources=resources,
                            host_birth=dict(
                                reference=str(UUID(receipt.key)), sha256=receipt.sha256
                            ),
                        )
                    ).decode()
                row = self.dal.transition(
                    "stream",
                    SessionID=self.session_id,
                    StreamID=stream_id,
                    Action="open",
                    ExpectedVersion=0,
                    ChildIdentity=child.identity,
                    **scope,
                )
                stream.version = row["Version"]
                child.resume()
            except BaseException as exc:
                stream.uncertain = True
                stream.frozen = True
                self._terminate_child(stream)
                raise ExecutionUncertain(
                    "Stream admission/child startup requires reconciliation."
                ) from exc
            return stream_id

    def _evidence(self, value):
        # Store must be authority-private, encrypted, fsynced and read back.
        receipt = self.store.put(encode(value))
        return dict(
            EvidenceHash=bytes.fromhex(receipt.sha256), EvidenceReference=str(UUID(receipt.key))
        )

    def _event(self, stream, request, state, evidence, **extra):
        row = self.dal.transition(
            "event",
            SessionID=self.session_id,
            StreamID=stream.stream_id,
            AccountKey=stream.account,
            ExpectedVersion=stream.version,
            RequestID=request.request_id,
            EventID=str(uuid4()),
            State=state,
            **self._evidence(evidence),
            **extra,
        )
        stream.version = row["Version"]

    def execute(self, message):
        request = ProviderRequest.parse(message, enrollment=self.enrollment_plan is not None)
        with self._lock:
            stream = self._streams.get(request.stream_id)
            if stream is None or stream.frozen or stream.uncertain:
                raise ExecutionUncertain("Unknown, frozen or uncertain stream.")
            if request.target not in stream.destinations or (
                stream.purpose == "probe" and request.mutation
            ):
                raise ValueError("Request outside the admitted scope.")
            if self.enrollment_plan is not None:
                self.enrollment_plan.authorize_request(
                    request, phase=stream.enrollment_phase, ordinal=stream.enrollment_ordinal
                )
            # An IPC replay never calls the child. The response may have been lost
            # after dispatch; return uncertainty rather than creating a new write.
            existing, _ = self.dal.read_request(request.request_id)
            if existing is not None:
                raise ExecutionUncertain(
                    "RequestID already exists; reconcile its retained outcome."
                )
            budget = self.budget_factory(stream.account)
            dispatched = False
            durable_success = False
            prepared = False
            intent_attempted = False
            intent_confirmed = False
            outcome_attempted = False
            try:
                payload = self.store.put(encode(request.message()))
                self._event(
                    stream,
                    request,
                    "prepared",
                    {"request_id": request.request_id, "payload_hash": payload.sha256},
                    Operation=request.operation,
                    RequestKind="mutation" if request.mutation else "read",
                    TargetID=request.target,
                    PayloadHash=bytes.fromhex(payload.sha256),
                    PayloadReference=str(UUID(payload.key)),
                )
                prepared = True
                budget()
                if self.dispatch_guard is not None:
                    self.dispatch_guard()
                # Procedure checks current owner/fence/version AFTER the wait.
                # Any commit exception prevents send. A lost acknowledgment may
                # still leave dispatch_intent in SQL and therefore retains claims.
                intent_attempted = True
                self._event(stream, request, "dispatch_intent", {"request_id": request.request_id})
                intent_confirmed = True
                if self.dispatch_guard is not None:
                    self.dispatch_guard()
                dispatched = True
                try:
                    response = stream.child.execute(request.message())
                except ProviderThrottled as exc:
                    # Persist shared feedback, but never infer non-delivery or
                    # replay. A lost cooldown acknowledgment is uncertain too.
                    stream.uncertain = True
                    budget.rejected(exc)
                    raise
                validate_response(request, response)
                outcome_attempted = True
                self._event(
                    stream,
                    request,
                    "succeeded",
                    {"request_id": request.request_id, "response": response},
                )
                durable_success = True
                budget.completed()
                return response
            except BaseException as exc:
                stream.uncertain = True
                # A read may fail without leaving a permanent account blockage.
                # Seal only an acknowledged prefix. Unknown journal commits are
                # never repaired by guessing a version or retrying an event.
                if stream.purpose == "probe" and not request.mutation:
                    terminal = (
                        "not_sent"
                        if prepared and not intent_attempted
                        else "unknown"
                        if intent_confirmed and not outcome_attempted
                        else None
                    )
                    if terminal is not None:
                        try:
                            self._event(
                                stream, request, terminal, {"request_id": request.request_id}
                            )
                        except BaseException as terminal_error:
                            logger.warning(
                                "Read terminal checkpoint unresolved stream=%s error_type=%s",
                                stream.stream_id,
                                type(terminal_error).__name__,
                            )
                # Never attempt another event when persistence itself is unknown:
                # a retained dispatch_intent is already sufficient to block reuse.
                logger.warning(
                    "Export request retained request=%s stream=%s dispatched=%s durable_success=%s error_type=%s",
                    request.request_id,
                    stream.stream_id,
                    dispatched,
                    durable_success,
                    type(exc).__name__,
                )
                raise ExecutionUncertain(
                    "Request outcome/checkpoint requires reconciliation."
                ) from exc

    def close_stream(self, stream_id):
        """Freeze, observe exact child termination, then commit closure; no release."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                raise ExecutionUncertain("Stream is not owned by this authority.")
            if stream.closed:
                return {"stream_id": stream_id, "version": stream.version}
            recover = stream.frozen or stream.uncertain
            stream.frozen = True
            try:
                state = "open"
                if recover:
                    retained = self.dal.read_stream(stream_id)
                    if not retained or (
                        str(retained["StreamID"]).lower(),
                        str(retained["SessionID"]).lower(),
                        str(retained["ChildIdentity"]).lower(),
                        retained["AccountKey"],
                    ) != (stream_id, self.session_id, stream.child.identity, stream.account):
                        raise ExecutionUncertain("Closure recovery identity differs.")
                    state = retained["State"]
                    if state == "closed":
                        receipt, document = stream.closure_receipt, stream.closure_document
                        sequence, event_digest = self.dal.stream_digest(stream_id)
                        if (
                            receipt is None
                            or document is None
                            or bytes(retained["ClosureHash"]).hex() != receipt.sha256
                            or str(retained["ClosureReference"]).lower() != str(UUID(receipt.key))
                            or retained["Version"] != document["version"] + 1
                            or retained["LastSequence"] != document["last_sequence"]
                            or retained["LastSequence"] != sequence
                            or bytes(retained["EventDigest"]).hex() != document["event_digest"]
                            or event_digest.hex() != document["event_digest"]
                        ):
                            raise ExecutionUncertain(
                                "Committed closure differs from retained evidence."
                            )
                        stream.version, stream.closed = retained["Version"], True
                        return {"stream_id": stream_id, "version": stream.version}
                    if state not in {"open", "frozen"}:
                        raise ExecutionUncertain("Stream has no recoverable closure transition.")
                    stream.version = retained["Version"]
                if state == "open":
                    row = self.dal.transition(
                        "stream",
                        SessionID=self.session_id,
                        StreamID=stream_id,
                        AccountKey=stream.account,
                        Action="freeze",
                        ExpectedVersion=stream.version,
                    )
                    stream.version = row["Version"]
                if stream.termination_evidence is None:
                    self._terminate_child(stream)
                elif callable(getattr(stream.child, "retry_handle_cleanup", None)):
                    stream.child.retry_handle_cleanup()
                last_sequence, event_digest = self.dal.stream_digest(stream_id)
                document = {
                    "stream_id": stream_id,
                    "version": stream.version,
                    "closure": stream.termination_evidence,
                    "last_sequence": last_sequence,
                    "event_digest": event_digest.hex(),
                }
                if stream.closure_document is not None and stream.closure_document != document:
                    raise ExecutionUncertain("Frozen journal changed after closure evidence.")
                stream.closure_document = deepcopy(document)
                if stream.closure_receipt is None:
                    stream.closure_receipt = self.store.put(encode(document))
                receipt = stream.closure_receipt
                row = self.dal.transition(
                    "stream",
                    SessionID=self.session_id,
                    StreamID=stream_id,
                    AccountKey=stream.account,
                    Action="close",
                    ExpectedVersion=stream.version,
                    ChildIdentity=stream.child.identity,
                    ClosureHash=bytes.fromhex(receipt.sha256),
                    ClosureReference=str(UUID(receipt.key)),
                    EventDigest=event_digest,
                    LastSequence=last_sequence,
                )
                stream.version = row["Version"]
                stream.closed = True
                return {"stream_id": stream_id, "version": stream.version}
            except BaseException as exc:
                stream.uncertain = True
                raise ExecutionUncertain(
                    "Stream closure requires reconciliation; retain claims."
                ) from exc

    @staticmethod
    def _terminate_child(stream):
        try:
            stream.termination_evidence = deepcopy(stream.child.terminate_and_observe())
        except BaseException:
            retained = getattr(stream.child, "termination_evidence", None)
            if (
                isinstance(retained, dict)
                and retained.get("child_id") == stream.child.identity
                and retained.get("job_empty") is True
                and retained.get("process_signaled") is True
            ):
                stream.termination_evidence = deepcopy(retained)
            raise

    def recover_owned_closure(self, stream_id):
        """Finish an interrupted local closure; never adopt another session's child."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None or not (stream.uncertain or stream.frozen):
                raise ExecutionUncertain("No interrupted locally owned stream closure.")
            return self.close_stream(stream_id)

    def recover_abandoned_read_closure(self, stream_id):
        """Close an old-session read only from its private birth and retired exact job."""
        from core.export_child_lifecycle import read_birth, validate_retirement

        with self._lock:
            row = self.dal.read_stream(stream_id)
            if (
                row is None
                or str(row["StreamID"]).lower() != stream_id
                or row["Purpose"] != "probe"
                or row["PreparationID"] is None
                or row.get("JobID") is not None
                or row.get("OutputOperationID") is not None
                or str(row["SessionID"]).lower() == self.session_id
                or row["State"] not in {"open", "frozen"}
            ):
                raise ExecutionUncertain("Exact old-session configuration read required.")
            birth, birth_hash = read_birth(self.store, row)
            # Observe first: a live child or inaccessible/missing birth is not abandoned.
            observed = self.host.observe_retired_child(birth)
            observed = dict(observed, birth_sha256=birth_hash)
            validate_retirement(observed, birth, birth_hash)
            old_session = str(row["SessionID"]).lower()
            version = row["Version"]
            if row["State"] == "open":
                version = self.dal.transition(
                    "stream",
                    SessionID=old_session,
                    StreamID=stream_id,
                    AccountKey=row["AccountKey"],
                    Action="freeze",
                    ExpectedVersion=version,
                )["Version"]
            sequence, event_digest = self.dal.stream_digest(stream_id)
            receipt = self.store.put(
                encode(
                    dict(
                        stream_id=stream_id,
                        version=version,
                        closure=observed,
                        last_sequence=sequence,
                        event_digest=event_digest.hex(),
                    )
                )
            )
            result = self.dal.transition(
                "stream",
                SessionID=old_session,
                StreamID=stream_id,
                AccountKey=row["AccountKey"],
                Action="close",
                ExpectedVersion=version,
                ChildIdentity=birth["child_id"],
                ClosureHash=bytes.fromhex(receipt.sha256),
                ClosureReference=str(UUID(receipt.key)),
                EventDigest=event_digest,
                LastSequence=sequence,
            )
            # Closure alone never releases the preparation. The caller must still
            # verify every private request/event and exact ownership before settlement.
            return dict(stream_id=stream_id, version=result["Version"])

    def recover_object_closures(self, account, object_id):
        """A registered proof request can finish only its interrupted local children."""
        with self._lock:
            for stream_id, owned in tuple(self._streams.items()):
                if (
                    owned.account != account
                    or owned.closed
                    or not (owned.frozen or owned.uncertain)
                ):
                    continue
                row = self.dal.read_stream(stream_id)
                if row and object_id in {
                    str(row.get("JobID")).lower(),
                    str(row.get("OutputOperationID")).lower(),
                }:
                    self.recover_owned_closure(stream_id)

    def stop(self):
        """Close admission. Caller drains owned streams; no automatic adoption/retry."""
        with self._lock:
            self._closed = True

    def drain(self):
        """Close admission, then terminate every locally owned live child.

        A failed or already uncertain closure leaves its SQL claim intact. No
        old stream is adopted from SQL when the authority restarts.
        """
        self.stop()
        failures = []
        for stream_id, stream in tuple(self._streams.items()):
            if stream.closed:
                continue
            try:
                self.close_stream(stream_id)
            except ExecutionUncertain:
                failures.append(stream_id)
        return not failures and all(stream.closed for stream in self._streams.values())
