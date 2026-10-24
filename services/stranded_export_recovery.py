"""Explicit administrator recovery of one stranded legacy writer; never delivery.

Runs beside, not inside or in place of, the installed Bot. The caller verifies
the protected installed source and retains both original process identities.
There is no provider client, queue operation, claim release or session adoption.
"""

from copy import deepcopy
import hashlib
import json
from uuid import UUID

from core.export_child_lifecycle import read_birth
from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import Claim, checked_attempt_manifest, identity
from services.export_execution_protocol import encode
from services.export_reconciliation_service import ClosedStreamVerifier
from services.legacy_export_snapshot_service import configuration_digest


class StrandedExportRecovery:
    def __init__(
        self, *, closeout, execution, coordinator, store, host, journal, check_boundary, expected
    ):
        self.closeout, self.execution, self.coordinator = closeout, execution, coordinator
        self.store, self.host, self.journal = store, host, journal
        self.check_boundary, self.expected = check_boundary, deepcopy(expected)

    def _read(self):
        self.check_boundary()
        state = self.coordinator.snapshot(self.expected["job_id"])
        if len(state["streams"]) != 1:
            raise SourceConflict("Exactly one reviewed writer stream is required.")
        return state, state["job"], state["streams"][0]

    def inspect(self):
        state, job, stream = self._read()
        registered = self.closeout.registration.value()
        configs = [
            c
            for c in registered["legacy_configuration"].values()
            if c["consumer"] == job["ConsumerKind"]
        ]
        if len(configs) != 1:
            raise SourceConflict("One unchanged registered legacy configuration is required.")
        config = configs[0]
        targets = sorted(config["destinations"])
        membership = ["account:" + registered["account"], *("destination:" + t for t in targets)]
        expected = self.expected
        if (
            job["ConsumerKind"] not in {"scan_data", "all_kvk"}
            or job["State"] != "running"
            or (job["JobID"], str(UUID(job["OwnerID"])), job["Fence"], job["Version"])
            != (
                expected["job_id"],
                expected["owner_id"],
                expected["fence"],
                expected["job_version"],
            )
            or job["AccountKey"] != registered["account"]
            or job["StorageOwner"] != registered["storage_owner"]
            or job.get("IntentID") is not None
            or job.get("PoolEpoch") is not None
            or not targets
            or len(targets) != expected["destination_count"]
            or state["membership"] != membership
            or job["DestinationSetHash"] != digest(targets).hex()
            or configuration_digest(config) != expected["configuration_sha256"]
            or json.loads(job["ProvenanceJson"]).get("registration_sha256")
            != expected["configuration_sha256"]
            or json.loads(job["ProvenanceJson"]).get("safe_retry", {}).get("requested")
            or any(
                state.get(k)
                for k in (
                    "foreign_streams",
                    "receipt",
                    "closeout",
                    "contained_targets",
                    "replacements",
                )
            )
        ):
            raise SourceConflict("Reviewed legacy job, destinations or recovery state changed.")
        self._check_attempt(state, targets)
        if (
            (
                stream["StreamID"],
                stream["SessionID"],
                stream["ChildIdentity"],
                stream["Version"],
                stream["LastSequence"],
            )
            != (
                expected["stream_id"],
                expected["session_id"],
                expected["child_id"],
                expected["stream_version"],
                expected["last_sequence"],
            )
            or stream["State"] != "open"
            or stream["Purpose"] != "mutation"
            or stream["JobID"] != job["JobID"]
            or stream["AccountKey"] != job["AccountKey"]
            or stream["ActiveAccountKey"] != job["AccountKey"]
            or stream["OwnerID"] != job["OwnerID"]
            or stream["Fence"] != job["Fence"]
            or stream["ClaimVersion"] != job["Version"]
            or stream["RegistrationHash"] != expected["configuration_sha256"]
            or any(
                stream[k] is not None
                for k in (
                    "PreparationID",
                    "OutputOperationID",
                    "NestedToken",
                    "Epoch",
                    "ClosureHash",
                    "ClosureReference",
                    "EventDigest",
                    "ClosedUTC",
                )
            )
        ):
            raise SourceConflict("Exact original open mutation stream is required.")
        resources = state["resources"]
        scope = json.loads(stream["ScopeJson"])
        if (
            [r["ResourceKey"] for r in resources] != membership
            or scope.get("resources")
            != [dict(key=r["ResourceKey"], version=r["Version"]) for r in resources]
            or any(
                r["ActiveJobID"] != job["JobID"]
                or r["OwnerID"] != job["OwnerID"]
                or r["Fence"] != job["Fence"]
                or r["BlockedReason"] is not None
                or r["ActivePreparationID"] is not None
                or r["ActiveOutputOperationID"] is not None
                for r in resources
            )
        ):
            raise SourceConflict("Original reservation membership or ownership changed.")
        session = self.execution.read_session(stream["SessionID"])
        if (
            session is None
            or session["State"] != "open"
            or session["AuthorityPrincipal"] != state["principal"]
            or bytes(session["ManifestHash"]).hex() != expected["manifest_sha256"]
            or str(session["SessionID"]).lower() != stream["SessionID"]
        ):
            raise SourceConflict("Stream is not owned by the pinned running authority session.")
        birth, birth_hash = read_birth(self.store, stream)
        # Retain handles only during this inspection. Apply independently reopens
        # and verifies the same private named job before its first mutation.
        with self.host.retain(birth) as child:
            child.inspect()
        if self._read()[0] != state:
            raise SourceConflict("Recovery state changed during inspection.")
        return dict(
            kind="stranded_export_recovery/1",
            expected=expected,
            original=state,
            birth=birth,
            birth_sha256=birth_hash,
        )

    @staticmethod
    def token(review):
        return digest(review).hex()

    @staticmethod
    def _check_attempt(state, targets):
        """Accept only the original, unverified legacy output attempt, if present."""
        attempts, parts, job = state["attempts"], state["attempt_parts"], state["job"]
        if not attempts and not parts:
            return
        if len(attempts) != 1:
            raise SourceConflict("Exactly one original attempt is required.")
        attempt = attempts[0]
        if (
            any(identity(attempt.get(k)) != identity(job[k]) for k in ("JobID", "OwnerID"))
            or attempt.get("ConsumerKind") != job["ConsumerKind"]
            or attempt.get("Fence") != job["Fence"]
            or attempt.get("RemoteSequence") != job["Fence"]
            or attempt.get("AttemptNo") != 1
            or attempt.get("Version") != 1
            or attempt.get("Phase") != "private_started"
            or any(
                attempt.get(k) is not None
                for k in (
                    "Epoch",
                    "VerifiedUTC",
                    "PublishedUTC",
                    "ReceiptJson",
                    "LegacyPublicationID",
                    "LegacySourceKey",
                    "LegacyKVK_NO",
                    "LegacyPeriodID",
                    "LegacyDestinationKind",
                    "LegacyDestinationID",
                )
            )
        ):
            raise SourceConflict("Original unverified attempt ownership or history differs.")
        document = checked_attempt_manifest(attempt, parts)
        if (
            document["generation"].get("export_key") != job["InputHash"]
            or sorted(p["FileID"] for p in parts) != targets
            or any(
                identity(p["AttemptID"]) != identity(attempt["AttemptID"])
                or p["PartCount"] != attempt["PartCount"]
                or p["Role"] != "output"
                or p["Version"] != 1
                or p["VerificationState"] != "pending"
                or p["AclState"] != "pending"
                or p["QuarantineState"] != "none"
                or any(
                    p.get(k) is not None
                    for k in (
                        "VerifiedUTC",
                        "AclCheckedUTC",
                        "QuarantinedUTC",
                        "QuarantineReason",
                        "EvidenceJson",
                    )
                )
                for p in parts
            )
        ):
            raise SourceConflict("Original attempt output membership or evidence differs.")

    def _current(self, review):
        """Accept only exact original state or this journal's known transitions."""
        state, job, stream = self._read()
        original = review["original"]
        prior_stream = original["streams"][0]
        wanted = deepcopy(original)
        expected_stream = dict(prior_stream)
        if stream["State"] == "frozen":
            expected_stream.update(State="frozen", Version=prior_stream["Version"] + 1)
        elif stream["State"] == "closed":
            saved = self.journal.read("closure")
            if saved is None:
                raise SourceConflict("Closed stream has no matching recovery journal.")
            expected_stream.update(
                State="closed",
                Version=prior_stream["Version"] + 2,
                ActiveAccountKey=None,
                ClosureHash=saved["sha256"],
                ClosureReference=saved["reference"],
                EventDigest=saved["document"]["event_digest"],
                ClosedUTC=stream["ClosedUTC"],
            )
            if stream["ClosedUTC"] is None:
                raise SourceConflict("Closure timestamp is missing.")
        elif stream["State"] != "open":
            raise SourceConflict("Stream changed outside the reviewed recovery.")
        wanted["streams"] = [expected_stream]
        if job["State"] == "uncertain":
            if stream["State"] != "closed" or self.journal.read("failure-intent") is None:
                raise SourceConflict("Uncertain job has no matching failure intent.")
            wanted["job"].update(
                State="uncertain",
                Version=original["job"]["Version"] + 1,
                UpdatedUTC=job["UpdatedUTC"],
            )
            for resource in wanted["resources"]:
                resource.update(
                    Version=resource["Version"] + 1, BlockedReason="Outcome requires reconciliation"
                )
            if len(state["attempts"]) != len(wanted["attempts"]) or len(
                state["attempt_parts"]
            ) != len(wanted["attempt_parts"]):
                raise SourceConflict("Attempt history membership changed.")
            for expected, actual in zip(wanted["attempts"], state["attempts"], strict=True):
                if not actual["UpdatedUTC"] or actual["UpdatedUTC"] < expected["UpdatedUTC"]:
                    raise SourceConflict("Attempt settlement timestamp differs.")
                expected.update(
                    Phase="uncertain",
                    Version=expected["Version"] + 1,
                    UpdatedUTC=actual["UpdatedUTC"],
                )
            for expected, actual in zip(
                wanted["attempt_parts"], state["attempt_parts"], strict=True
            ):
                if not actual["QuarantinedUTC"]:
                    raise SourceConflict("Part settlement timestamp is missing.")
                expected.update(
                    QuarantineState="quarantined",
                    QuarantinedUTC=actual["QuarantinedUTC"],
                    QuarantineReason="Outcome requires reconciliation",
                    Version=expected["Version"] + 1,
                )
        if state != wanted:
            raise SourceConflict("Ownership, history or recovery state changed; preserve evidence.")
        return state, job, stream

    def apply(self, review, token):
        if (
            review.get("kind") != "stranded_export_recovery/1"
            or review.get("expected") != self.expected
            or self.token(review) != token
        ):
            raise SourceConflict("Exact reviewed recovery token required.")
        original = self.journal.read("intent")
        if original is None:
            if self.inspect() != review:
                raise SourceConflict("Inspection is stale; no recovery started.")
            self.journal.write("intent", review)
        elif original != review:
            raise SourceConflict("Another recovery intent exists; preserve it.")
        state, job, stream = self._current(review)
        if stream["State"] != "closed":
            birth, birth_hash = read_birth(self.store, stream)
            if birth != review["birth"] or birth_hash != review["birth_sha256"]:
                raise SourceConflict("Private writer birth changed.")
            terminated = self.journal.read("termination")
            if terminated is None:
                with self.host.retain(birth) as child:
                    child.inspect()
                    self._current(review)
                    if stream["State"] == "open":
                        self.execution.transition(
                            "stream",
                            SessionID=stream["SessionID"],
                            StreamID=stream["StreamID"],
                            AccountKey=stream["AccountKey"],
                            Action="freeze",
                            ExpectedVersion=stream["Version"],
                        )
                    _, _, stream = self._current(review)
                    if stream["State"] != "frozen":
                        raise SourceConflict("Exact SQL freeze was not independently observed.")
                    terminated = child.terminate_and_observe()
                    self.journal.write("termination", terminated)
            else:
                if stream["State"] != "frozen":
                    raise SourceConflict(
                        "Saved termination requires this recovery's frozen stream."
                    )
                self.host.verify_terminated(birth, terminated)
            sequence, event_digest = self.execution.stream_digest(stream["StreamID"])
            if sequence != review["expected"]["last_sequence"]:
                raise SourceConflict(
                    "Request membership changed; original outcome remains unknown."
                )
            document = dict(
                stream_id=stream["StreamID"],
                version=stream["Version"],
                closure=terminated,
                last_sequence=sequence,
                event_digest=event_digest.hex(),
                administrator_recovery=dict(review_sha256=token, birth_sha256=birth_hash),
            )
            saved = self.journal.read("closure")
            if saved is None:
                receipt = self.store.put(encode(document))
                saved = dict(
                    reference=str(UUID(receipt.key)), sha256=receipt.sha256, document=document
                )
                self.journal.write("closure", saved)
            if (
                saved["document"] != document
                or hashlib.sha256(encode(document)).hexdigest() != saved["sha256"]
            ):
                raise SourceConflict("Retained closure evidence differs.")
            self._current(review)
            self.execution.transition(
                "stream",
                SessionID=stream["SessionID"],
                StreamID=stream["StreamID"],
                AccountKey=stream["AccountKey"],
                Action="close",
                ExpectedVersion=stream["Version"],
                ChildIdentity=stream["ChildIdentity"],
                ClosureHash=bytes.fromhex(saved["sha256"]),
                ClosureReference=saved["reference"],
                EventDigest=event_digest,
                LastSequence=sequence,
            )
        state, job, stream = self._current(review)
        ClosedStreamVerifier(dal=self.execution, store=self.store).verify(
            stream["StreamID"],
            account=job["AccountKey"],
            registration_hash=bytes.fromhex(stream["RegistrationHash"]),
            require_observation=False,
        )
        if job["State"] == "running":
            self.journal.write("failure-intent", dict(review_sha256=token))
            self.coordinator.fail_reviewed(
                Claim(
                    job["JobID"],
                    job["AccountKey"],
                    job["OwnerID"],
                    job["Fence"],
                    job["Version"],
                    tuple((r["ResourceKey"], r["Version"]) for r in state["resources"]),
                ),
                state,
            )
        state, job, stream = self._current(review)
        evidence, _, resolved = self.closeout.inspect(job["JobID"])
        if (
            job["State"] != "uncertain"
            or resolved
            or "allow_next_export" not in evidence["actions"]
        ):
            raise SourceConflict(
                "Closure recorded, but explicit legacy closeout is not yet verified."
            )
        result = dict(
            stage="CLOSURE_VERIFIED_CLOSEOUT_REQUIRED",
            job_id=job["JobID"],
            stream_id=stream["StreamID"],
            outcome="unconfirmed",
            destination_count=self.expected["destination_count"],
            reservations_released=False,
            provider_requests=0,
            deployment_changed=False,
        )
        self.journal.write("verified", result)
        return result
