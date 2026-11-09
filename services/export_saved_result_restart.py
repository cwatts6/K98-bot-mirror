"""Settle exact predecessor responses and seals before ordinary startup readiness.

No provider child is launched; no job, attempt or resource is released/adopted.
An abandoned partial job still requires its explicit business disposition.
"""

from copy import deepcopy
import hashlib

from core.export_child_lifecycle import read_birth, validate_retirement
from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_protocol import encode
from services.export_reconciliation_service import ClosedStreamVerifier
from services.export_request_settlement import fixed_reference, transient
from services.export_saved_result_recovery_dal import RecoveryWaiting


class SavedResultRestart:
    def __init__(self, settlement, *, account, hostname, observe_retired):
        self.settlement, self.account, self.hostname = settlement, account, hostname
        self.observe_retired = observe_retired

    def _read(self, work, termination):
        """Retry read-only receipts only after confirmed connection cleanup."""
        service = self.settlement
        started, delay = service.clock(), 0.25
        while True:
            termination.verify()
            try:
                return service.checkpoint(work)
            except RecoveryWaiting as error:
                service.check_boundary()
                if service.stop.wait(30 if service.clock() - started > 15 else delay):
                    raise RecoveryWaiting(
                        "Predecessor recovery interrupted; retain all ownership."
                    ) from error
                delay = min(delay * 2, 5)

    def __call__(self, previous_hash, termination):
        termination.verify()
        service = self.settlement
        sessions = self._read(
            lambda: service.execution.open_host_sessions(self.hostname), termination
        )
        if not sessions:
            return []
        if len(sessions) != 1 or bytes(sessions[0]["ManifestHash"]).hex() != previous_hash:
            raise SourceConflict("Saved-result restart requires the exact terminated predecessor.")
        session_id = str(sessions[0]["SessionID"]).lower()
        streams = self._read(
            lambda: service.execution.session_streams(session_id, self.account), termination
        )
        completed = []
        for initial in streams:
            if initial["Purpose"] not in {"mutation", "probe"}:
                raise SourceConflict("This retained stream has no normal runtime restart binding.")
            birth, birth_hash = read_birth(service.store, initial)
            termination.verify()
            observed = dict(self.observe_retired(birth), birth_sha256=birth_hash)
            validate_retirement(observed, birth, birth_hash)
            identifier = str(initial["StreamID"]).lower()
            last = self._read(lambda: service.execution.last_request(identifier), termination)
            if last is not None:
                _, events = self._read(lambda: service.execution.read_request(last), termination)
                if [event["State"] for event in events] == ["prepared", "dispatch_intent"]:
                    # The locator predates dispatch and is recovered by SQL's exact
                    # RequestID. Missing evidence remains uncertainty, never resend.
                    service.run(last, guard=termination.verify)
                elif [event["State"] for event in events] == [
                    "prepared",
                    "dispatch_intent",
                    "succeeded",
                ]:
                    # Resume a missing pacing completion too, but only for requests
                    # born under the fixed-locator protocol.
                    service.run(last, guard=termination.verify)
            self._close(initial, observed, termination)
            completed.append(identifier)
        return completed

    def _close(self, initial, observed, termination):
        service, execution = self.settlement, self.settlement.execution
        identifier = str(initial["StreamID"]).lower()
        from services.export_request_settlement import stream_binding

        started, delay = service.clock(), 0.25
        while True:
            termination.verify()
            row = self._read(lambda: execution.read_stream(identifier), termination)
            if row is None or stream_binding(row) != stream_binding(initial):
                raise SourceConflict("Retained predecessor stream binding changed.")
            if row["State"] == "closed":
                self._read(
                    lambda: ClosedStreamVerifier(dal=execution, store=service.store).verify(
                        identifier,
                        account=self.account,
                        registration_hash=bytes(row["RegistrationHash"]),
                        require_observation=False,
                        allow_failed_reads=row["Purpose"] == "probe",
                    ),
                    termination,
                )
                return
            try:
                if row["State"] == "open":
                    service.checkpoint(
                        lambda: execution.transition(
                            "stream",
                            SessionID=row["SessionID"],
                            StreamID=identifier,
                            AccountKey=self.account,
                            Action="freeze",
                            ExpectedVersion=row["Version"],
                        )
                    )
                    continue
                if row["State"] != "frozen":
                    raise SourceConflict("Retained stream has no compatible closure state.")
                count, digest = service.checkpoint(lambda: execution.stream_digest(identifier))
                document = dict(
                    stream_id=identifier,
                    version=row["Version"],
                    closure=observed,
                    last_sequence=count,
                    event_digest=digest.hex(),
                )
                reference = fixed_reference("closure-" + str(row["Version"]), identifier)
                raw = encode(document)
                try:
                    retained = service.store.read_fixed(reference)
                except FileNotFoundError:
                    retained = None
                if retained is not None:
                    # A prior worker may have saved its native process-handle
                    # observation before losing SQL admission. Reuse that exact
                    # immutable seal; verify it against the complete journal.
                    raw = retained
                # Verify complete payload/event history against a virtual seal
                # before the short SQL write. This projection never proves commit.
                projected = deepcopy(row)
                projected.update(
                    State="closed",
                    Version=row["Version"] + 1,
                    ActiveAccountKey=None,
                    ClosureReference=reference,
                    ClosureHash=hashlib.sha256(raw).digest(),
                    EventDigest=digest,
                )

                class Preview:
                    def read_stream(self, stream_id):
                        return (
                            deepcopy(projected)
                            if stream_id == identifier
                            else execution.read_stream(stream_id)
                        )

                    def read_reference(self, ref, expected):
                        if str(ref).lower() == reference:
                            if bytes(expected) != hashlib.sha256(raw).digest():
                                raise SourceConflict("Virtual closure hash differs.")
                            return raw
                        return service.store.read_reference(ref, expected)

                    def __getattr__(self, name):
                        return getattr(execution, name)

                preview = Preview()
                service.checkpoint(
                    lambda: ClosedStreamVerifier(dal=preview, store=preview).verify(
                        identifier,
                        account=self.account,
                        registration_hash=bytes(row["RegistrationHash"]),
                        require_observation=False,
                        allow_failed_reads=row["Purpose"] == "probe",
                    )
                )
                if retained is None:
                    service.retain(reference, raw)
                termination.verify()
                service.checkpoint(
                    lambda: execution.transition(
                        "stream",
                        SessionID=row["SessionID"],
                        StreamID=identifier,
                        AccountKey=self.account,
                        Action="close",
                        ExpectedVersion=row["Version"],
                        ChildIdentity=row["ChildIdentity"],
                        LastSequence=count,
                        EventDigest=digest,
                        ClosureReference=reference,
                        ClosureHash=hashlib.sha256(raw).digest(),
                    )
                )
            except Exception as error:
                after = self._read(lambda: execution.read_stream(identifier), termination)
                if after is not None and after["Version"] != row["Version"]:
                    continue  # Next pass verifies the exact persisted seal/history.
                if not transient(error):
                    raise
                service.check_boundary()
                if service.stop.wait(30 if service.clock() - started > 15 else delay):
                    raise RecoveryWaiting(
                        "Predecessor recovery interrupted; retain all ownership."
                    ) from error
                delay = min(delay * 2, 5)
