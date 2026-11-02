"""Request-bound saved results: reconcile bookkeeping, never dispatch or release claims."""

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import threading
from time import monotonic
from uuid import UUID, uuid5

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from services.export_contention import CoordinationLockRefused, sql_error_facts
from services.export_execution_dal import EvidenceCommitUnknown, ExportExecutionDAL
from services.export_execution_protocol import (
    ProviderRequest,
    decode,
    encode,
    uuid_text,
    validate_response,
)
from services.export_saved_result_recovery_dal import RecoveryConnections, RecoveryWaiting

_NAMESPACE = UUID("ba69bbda-ae20-4d7b-b75a-e6b74008bbba")
_BINDING = (
    "StreamID",
    "SessionID",
    "ChildIdentity",
    "AccountKey",
    "JobID",
    "PreparationID",
    "OutputOperationID",
    "OwnerID",
    "Fence",
    "ClaimVersion",
    "NestedToken",
    "RegistrationHash",
    "Epoch",
    "SnapshotHash",
    "ScopeJson",
    "Purpose",
)


def fixed_reference(kind, identifier):
    return str(uuid5(_NAMESPACE, kind + ":" + uuid_text(identifier)))


def stream_binding(row):
    from services.config_read_containment import stream_wire

    wire = stream_wire(row)
    return {key: wire[key] for key in _BINDING}


def transient(error):
    """Only known contention/connection failures; a wrapped refusal is not all uncertainty."""
    seen = set()
    current = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, SourceConflict) and not isinstance(current, EvidenceCommitUnknown):
            return False  # Failed cleanup/bindings cannot inherit a transient cause.
        if isinstance(current, CoordinationLockRefused):
            return current.result == -1
        facts = sql_error_facts(current)
        if (
            isinstance(current, (RecoveryWaiting, UncertainCommit))
            or facts["sqlstate"] in {"08S01", "08001", "08003", "HYT00", "HYT01"}
            or bool(set(facts["native_errors"]) & {1205, 1222})
        ):
            return True
        current = current.__cause__ or current.__context__
    return False


@dataclass(frozen=True)
class RetainedEvidence:
    key: str
    sha256: str


class RequestSettlement:
    """One immutable locator per accepted request; SQL remains the outcome authority."""

    def __init__(self, execution, store, *, check_boundary, complete_request=None, clock=monotonic):
        self.store, self.check_boundary, self.clock = store, check_boundary, clock
        self.connections = RecoveryConnections(execution.connect)
        self.execution = ExportExecutionDAL(self.connections.connect)
        if complete_request is None:
            from services.export_coordination_dal import ExportCoordinationDAL

            complete_request = ExportCoordinationDAL(self.connections.connect).complete_request
        self.complete_request = complete_request
        self.stop = threading.Event()

    def checkpoint(self, work):
        return self.connections.checkpoint(work)

    def prepare(self, request, payload, stream):
        """Must finish and read back before dispatch_intent/provider execution."""
        locator = dict(
            kind="provider_result_locator/1",
            request_id=request.request_id,
            payload_reference=str(UUID(payload.key)),
            payload_sha256=payload.sha256,
            response_reference=fixed_reference("response", request.request_id),
            event_id=fixed_reference("terminal", request.request_id),
            dispatch_version=stream["Version"] + 2,
            sequence=stream["LastSequence"] + 1,
            stream=stream_binding(stream),
        )
        raw = encode(locator)
        if len(raw) > 65536:
            raise SourceConflict("Request locator exceeds its fixed bound.")
        self.store.put_fixed(fixed_reference("locator", request.request_id), raw)
        if self.locator(request.request_id) != locator:
            raise SourceConflict("Request locator readback differs.")
        return locator

    def locator(self, request_id):
        uuid_text(request_id)
        raw = self.store.read_fixed(fixed_reference("locator", request_id))
        if len(raw) > 65536:
            raise SourceConflict("Request locator exceeds its fixed bound.")
        value = decode(raw)
        if (
            set(value)
            != {
                "kind",
                "request_id",
                "payload_reference",
                "payload_sha256",
                "response_reference",
                "event_id",
                "dispatch_version",
                "sequence",
                "stream",
            }
            or value["kind"] != "provider_result_locator/1"
            or value["request_id"] != request_id
            or value["response_reference"] != fixed_reference("response", request_id)
            or value["event_id"] != fixed_reference("terminal", request_id)
            or set(value["stream"]) != set(_BINDING)
            or type(value["dispatch_version"]) is not int
            or value["dispatch_version"] < 3
            or type(value["sequence"]) is not int
            or value["sequence"] < 1
        ):
            raise SourceConflict("Exact original request locator required.")
        uuid_text(value["payload_reference"])
        if (
            len(value["payload_sha256"]) != 64
            or bytes.fromhex(value["payload_sha256"]).hex() != value["payload_sha256"]
        ):
            raise SourceConflict("Canonical payload commitment required.")
        return value

    def save(self, locator, response):
        body = dict(request_id=locator["request_id"], response=response)
        return self.retain(locator["response_reference"], encode(body))

    def retain(self, reference, raw):
        """Reconcile post-dispatch evidence writes; locator preparation stays strict."""
        try:
            self.store.put_fixed(reference, raw)
        except Exception:
            # A primary can be durable before a replica/acknowledgement failure.
            # Accept only exact saved bytes, preserving all partial/conflicting files.
            if self.store.read_fixed(reference) != raw:
                raise SourceConflict("Saved settlement evidence conflicts.")
        return RetainedEvidence(UUID(reference).hex, hashlib.sha256(raw).hexdigest())

    def _read(self, request_id):
        locator = self.locator(request_id)
        row, events = self.execution.read_request(request_id)
        stream = self.execution.read_stream(locator["stream"]["StreamID"])
        if row is None or stream is None or stream_binding(stream) != locator["stream"]:
            raise SourceConflict("Saved request stream binding changed.")
        request = ProviderRequest.parse(
            decode(
                self.store.read_reference(
                    locator["payload_reference"], bytes.fromhex(locator["payload_sha256"])
                )
            ),
            enrollment=stream["Purpose"] == "enrollment",
        )
        if (
            request.request_id != request_id
            or request.stream_id != locator["stream"]["StreamID"]
            or str(row["RequestID"]).lower() != request_id
            or str(row["StreamID"]).lower() != request.stream_id
            or row["Sequence"] != locator["sequence"]
            or row["Operation"] != request.operation
            or row["TargetID"] != request.target
            or row["RequestKind"] != ("mutation" if request.mutation else "read")
            or bytes(row["PayloadHash"]).hex() != locator["payload_sha256"]
            or str(row["PayloadReference"]).lower() != locator["payload_reference"]
            or [e["State"] for e in events]
            not in (["prepared", "dispatch_intent"], ["prepared", "dispatch_intent", "succeeded"])
        ):
            raise SourceConflict("Saved result does not match the exact dispatched request.")
        for sequence, event in enumerate(events, 1):
            if event["EventSequence"] != sequence or str(event["RequestID"]).lower() != request_id:
                raise SourceConflict("Saved request event membership changed.")
            if sequence == 3:
                continue  # Fixed copies and the exact terminal commitment are checked below.
            document = decode(
                self.store.read_reference(event["EvidenceReference"], bytes(event["EvidenceHash"]))
            )
            if sequence == 1 and document != {
                "request_id": request_id,
                "payload_hash": locator["payload_sha256"],
            }:
                raise SourceConflict("Prepared request proof differs.")
            if sequence == 2 and document != {"request_id": request_id}:
                raise SourceConflict("Dispatch request proof differs.")
        raw = self.store.read_fixed(locator["response_reference"])
        result = decode(raw)
        if set(result) != {"request_id", "response"} or result["request_id"] != request_id:
            raise SourceConflict("Saved response belongs to another request.")
        validate_response(request, result["response"])
        event = dict(
            EventID=locator["event_id"],
            RequestID=request_id,
            State="succeeded",
            EvidenceHash=hashlib.sha256(raw).digest(),
            EvidenceReference=locator["response_reference"],
        )
        if len(events) == 3 and any(
            (
                str(events[-1][key]).lower()
                if key in {"EventID", "RequestID", "EvidenceReference"}
                else bytes(events[-1][key]) if key == "EvidenceHash" else events[-1][key]
            )
            != value
            for key, value in event.items()
        ):
            raise SourceConflict("Terminal event differs from the pre-dispatch identity.")
        return locator, stream, event, result["response"], len(events) == 3

    def step(self, request_id):
        self.check_boundary()
        locator, stream, event, response, recorded = self._read(request_id)
        if not recorded:
            if (
                stream["State"] not in {"open", "frozen"}
                or stream["LastSequence"] != locator["sequence"]
                or stream["Version"]
                != locator["dispatch_version"] + int(stream["State"] == "frozen")
            ):
                raise SourceConflict("Pending result has a changed stream version or history.")
            self.check_boundary()
            try:
                self.execution.transition(
                    "event",
                    SessionID=locator["stream"]["SessionID"],
                    StreamID=locator["stream"]["StreamID"],
                    AccountKey=stream["AccountKey"],
                    ExpectedVersion=stream["Version"],
                    **event,
                )
            except Exception as error:
                # Even a rejected/lost acknowledgement is first reconciled, never resent.
                _, _, _, _, recorded = self._read(request_id)
                if not recorded:
                    if transient(error):
                        raise RecoveryWaiting("Saved result awaits SQL admission.") from error
                    raise
            locator, stream, event, response, recorded = self._read(request_id)
            if not recorded:
                raise SourceConflict("Terminal acknowledgement has no matching durable receipt.")
        # This monotonic checkpoint may conservatively extend pacing after a lost
        # reply. It never sends provider work or changes the business outcome.
        marker = dict(
            kind="provider_result_settled/1",
            request_id=request_id,
            event_id=event["EventID"],
            response_sha256=event["EvidenceHash"].hex(),
        )
        reference = fixed_reference("settled", request_id)
        try:
            saved = decode(self.store.read_fixed(reference))
        except FileNotFoundError:
            saved = None
        if saved is not None and saved != marker:
            raise SourceConflict("Saved settlement completion conflicts.")
        if saved is None:
            try:
                self.complete_request(stream["AccountKey"])
            except Exception as error:
                if transient(error):
                    raise RecoveryWaiting("Saved result awaits its pacing checkpoint.") from error
                raise
            self.retain(reference, encode(marker))
        return dict(response=deepcopy(response), stream_version=stream["Version"])

    def run(self, request_id, *, progress=None, guard=None):
        started, delay, warned = self.clock(), 0.25, False
        while True:
            try:
                if guard is not None:
                    guard()
                return self.checkpoint(lambda: self.step(request_id))
            except RecoveryWaiting:
                self.check_boundary()
                elapsed = self.clock() - started
                if progress is not None:
                    progress("waiting", elapsed >= 300)
                if elapsed >= 300 and not warned:
                    from services.export_authority_diagnostics import report_authority_event

                    try:
                        report_authority_event(
                            "AUTHORITY_RESULT_SETTLEMENT_WAITING",
                            message={"action": "settlement", "request": {"request_id": request_id}},
                        )
                    except Exception:
                        pass  # Diagnostic failure cannot change retained work.
                    warned = True
                if self.stop.wait(30 if elapsed > 15 else delay):
                    raise SourceConflict("Settlement stopped with its durable intent retained.")
                delay = min(delay * 2, 5)
