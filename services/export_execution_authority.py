"""Independent request-journal coordinator, with injected SQL, storage and OS host.

No default clients, credentials or in-memory recovery claims. Each stream belongs
to one exact supervised child. Only its trusted parent can author response events.
"""

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


class ExportExecutionAuthority:
    def __init__(self, *, dal, store, host, budget_factory, session_id, enrollment_plan=None):
        self.dal, self.store, self.host = dal, store, host
        self.budget_factory, self.session_id = budget_factory, session_id
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

        resources = json.loads(scope["ScopeJson"])["resources"]
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
                child.terminate_and_observe()
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
                budget()
                # Procedure checks current owner/fence/version AFTER the wait.
                # Any commit exception prevents send. A lost acknowledgment may
                # still leave dispatch_intent in SQL and therefore retains claims.
                self._event(stream, request, "dispatch_intent", {"request_id": request.request_id})
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
            if stream is None or stream.frozen:
                raise ExecutionUncertain("Stream closure is already pending or unavailable.")
            stream.frozen = True
            try:
                row = self.dal.transition(
                    "stream",
                    SessionID=self.session_id,
                    StreamID=stream_id,
                    AccountKey=stream.account,
                    Action="freeze",
                    ExpectedVersion=stream.version,
                )
                stream.version = row["Version"]
                evidence = stream.child.terminate_and_observe()
                last_sequence, event_digest = self.dal.stream_digest(stream_id)
                receipt = self.store.put(
                    encode(
                        {
                            "stream_id": stream_id,
                            "version": stream.version,
                            "closure": evidence,
                            "last_sequence": last_sequence,
                            "event_digest": event_digest.hex(),
                        }
                    )
                )
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
            if stream.frozen:
                failures.append(stream_id)
                continue
            try:
                self.close_stream(stream_id)
            except ExecutionUncertain:
                failures.append(stream_id)
        return not failures and all(stream.closed for stream in self._streams.values())
