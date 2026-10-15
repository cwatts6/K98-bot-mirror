"""Protected composition for guided replacement and authenticated registration history."""

import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import ExportCoordinationDAL, identity
from services.export_execution_protocol import encode
from services.export_manual_enrollment import manual_profile
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_replacement_activation import (
    ReplacementActivationService,
    effective_registration,
)
from services.export_replacement_activation_dal import ReplacementActivationDAL
from services.export_replacement_dal import ExportReplacementDAL
from services.export_replacement_delivery import ReplacementDelivery
from services.export_replacement_delivery_dal import ReplacementDeliveryDAL
from services.export_replacement_service import ExportReplacementService
from services.export_replacement_verification import verification_plan
from services.export_replacement_verification_dal import ReplacementVerificationDAL
from services.export_replacement_verification_service import ReplacementVerificationService
from services.export_replacement_workflow import ReplacementWorkflow
from services.export_runtime_composition import RuntimeRegistration
from services.export_target_recovery_authority import _service as containment_service


class HistoricalRecoveryDiscovery:
    def __init__(self, connect, registrations):
        self.registrations = tuple(registrations)
        self.members = [ExportRecoveryDAL(connect, registration=r) for r in self.registrations]
        self.account = self.members[0].account

    def job(self, key):
        for member in reversed(self.members):
            try:
                return member.job(key)
            except SourceConflict:
                continue
        raise SourceConflict("Export is outside the authenticated registration history.")


class HistoricalContainment:
    """Verify each original owner against an already authenticated registration."""

    def __init__(self, authority, registrations):
        self.members = [containment_service(authority, r) for r in registrations]
        self.dal = self.members[-1].dal

    def _member(self, job_id):
        for member in reversed(self.members):
            try:
                result = member.inspect(job_id)
                return member, result
            except SourceConflict:
                continue
        raise SourceConflict(
            "Original containment does not verify in the authenticated registration history."
        )

    def inspect(self, job_id):
        return self._member(job_id)[1]

    def apply(self, job_id, **kwargs):
        return self._member(job_id)[0].apply(job_id, **kwargs)


class ReplacementAuthority:
    def __init__(self, broker):
        self.broker, self.authority, self.base = broker, broker.authority, broker.registration
        self.connect = self.authority.dal.connect
        self.activation_dal = ReplacementActivationDAL(self.connect)

    def services(self, registration, *, history=()):
        proposals = ExportReplacementService(
            dal=ExportReplacementDAL(self.connect),
            containment=HistoricalContainment(self.authority, history or (registration,)),
            registration=registration,
            store=self.authority.store,
        )
        verification = ReplacementVerificationService(
            dal=ReplacementVerificationDAL(self.connect),
            authority=self.authority,
            proposals=proposals,
        )
        return ReplacementActivationService(
            dal=self.activation_dal,
            proposals=proposals,
            verification=verification,
            authority=self.authority,
        )

    def authenticated_history(self):
        with self.authority._lock:
            authenticated = []

            def services(registration):
                authenticated.append(registration)
                return self.services(registration, history=tuple(authenticated))

            return effective_registration(
                self.base, self.activation_dal.chain(self.base.value()["account"]), services
            )

    def registrations(self):
        current, history = self.authenticated_history()
        return [
            self.base,
            *(RuntimeRegistration(item["registration"]) for item in history),
        ], current

    def queued_activation(self, snapshot):
        from services.export_replacement_projection import continuation_activation

        _, history = self.authenticated_history()
        job = snapshot["job"]
        anchor = ReplacementDeliveryDAL(self.connect, None).continuation_anchor(
            job["JobID"], job["AccountKey"]
        )
        return continuation_activation(
            history,
            targets=[
                r["ResourceKey"][12:]
                for r in snapshot["resources"]
                if r["ResourceKey"].startswith("destination:")
            ],
            consumer=job["ConsumerKind"],
            anchor_id=anchor,
        )

    def current(self):
        registrations, current = self.registrations()
        return dict(
            base_sha256=self.base.fingerprint,
            registration=current.value(),
            registration_sha256=current.fingerprint,
            history=[r.value() for r in registrations],
        )

    def workflow(self, job_id):
        registrations, current = self.registrations()
        discovery = HistoricalRecoveryDiscovery(self.connect, registrations)
        coordinator = ExportCoordinationDAL(
            self.connect, preparations=True, output_operations=True, execution_evidence=True
        )
        delivery_dal = ReplacementDeliveryDAL(self.connect, coordinator)
        continuation = ReplacementDelivery(
            dal=delivery_dal,
            discovery=discovery,
            verify_delivery=self.verify_delivery,
            next_activation=self.activated_replacement,
        )
        plans = ExportReplacementDAL(self.connect)
        keys = plans.for_job(job_id, account=self.base.value()["account"])
        snapshot = discovery.job(job_id)
        if (
            not keys
            and snapshot.get("isolated_targets")
            and not snapshot["attempts"]
            and not snapshot["streams"]
        ):
            from services.export_replacement_waiting import WaitingReplacementWorkflow

            return WaitingReplacementWorkflow(
                discovery=discovery,
                continuation=continuation,
                blocking_jobs=delivery_dal.blocking_jobs,
                original_workflow=self.workflow,
                project_activation=self.queued_activation,
            )
        selected = None
        if keys:
            first = plans.read(keys[-1], account=self.base.value()["account"])
            selected = next(
                (
                    r
                    for r in registrations
                    if r.fingerprint == first["plan"]["BaseRegistrationHash"]
                ),
                None,
            )
        else:
            for registration in reversed(registrations):
                try:
                    containment_service(self.authority, registration).inspect(job_id)
                except SourceConflict:
                    continue
                selected = registration
                break
        if selected is None:
            raise SourceConflict("The original output registration cannot be authenticated.")
        service = self.services(selected, history=registrations)
        current_service = self.services(current, history=registrations)
        profile = manual_profile(self.broker.boundary._manifest)
        session = self.authority.dal.read_session(self.authority.session_id)
        if session is None:
            raise SourceConflict("Original authority session is unavailable.")
        plan_factory = lambda proposal, key: verification_plan(
            selected,
            proposal,
            verification_id=key,
            manifest_hash=bytes(session["ManifestHash"]).hex(),
            profile_hash=hashlib.sha256(encode(profile)).hexdigest(),
            project_id=profile["project_id"],
        )
        return ReplacementWorkflow(
            proposals=service.proposals,
            verification=service.verification,
            activation=service,
            plan_factory=plan_factory,
            continuation=continuation,
            proposal_writer=current_service.proposals,
        )

    def activated_replacement(self, job_id):
        registrations, _ = self.registrations()
        proposals = ExportReplacementDAL(self.connect).for_job(
            job_id, account=self.base.value()["account"]
        )
        matches = [
            row
            for row in self.activation_dal.chain(self.base.value()["account"])
            if identity(row["ReplacementID"]) in proposals
        ]
        if not matches:
            return None
        if len(matches) != 1:
            raise SourceConflict("Replacement delivery has conflicting activations.")
        row = matches[0]
        base = next(
            (r for r in registrations if r.fingerprint == row["BaseRegistrationHash"]), None
        )
        if base is None:
            raise SourceConflict("Replacement delivery registration history is incomplete.")
        return self.services(base, history=registrations).verify(row, base)

    def verify_delivery(self, snapshot, activation):
        from services.config_read_containment import stream_wire
        from services.export_coordination_dal import (
            checked_attempt_manifest,
            legacy_attempt_audiences,
        )
        from services.export_reconciliation_service import ClosedStreamVerifier

        job = snapshot["job"]
        if (
            job["State"] != "confirmed"
            or len(snapshot["attempts"]) != 1
            or not snapshot["streams"]
            or any(r["ActiveJobID"] == job["JobID"] for r in snapshot["resources"])
        ):
            raise SourceConflict("Replacement publication and released ownership are not verified.")
        attempt = snapshot["attempts"][0]
        if attempt["ReceiptJson"] is None:
            raise SourceConflict("Replacement publication receipt is missing.")
        parts = ReplacementDeliveryDAL(self.connect, None).publication_parts(job)
        document = checked_attempt_manifest(attempt, parts)
        receipt = json.loads(attempt["ReceiptJson"])
        files = [p["FileID"] for p in parts]
        audiences = legacy_attempt_audiences(document, files, job["ConsumerKind"])
        if (
            attempt["JobID"] != job["JobID"]
            or attempt["Phase"] != "published"
            or identity(receipt.get("attempt_id")) != identity(attempt["AttemptID"])
            or receipt.get("fence") != job["Fence"]
            or receipt.get("export_key") != document["generation"]["export_key"]
            or receipt.get("files") != files
            or not files
            or not set(files) <= set(activation["mapping"].values())
            or not receipt.get("remote_id")
            or receipt.get("audience") not in {"private", "public_viewer", "legacy_registered"}
            or ((receipt.get("audience") == "legacy_registered") != (audiences is not None))
            or (audiences is not None and receipt.get("file_audiences") != audiences)
            or any(p["VerificationState"] != "verified" for p in parts)
        ):
            raise SourceConflict("Replacement receipt differs from its retained publication.")
        registration = RuntimeRegistration(activation["registration"])
        verifier = ClosedStreamVerifier(dal=self.authority.dal, store=self.authority.store)
        for entry in snapshot["streams"]:
            key = identity(entry["StreamID"])
            stream = self.authority.dal.read_stream(key)
            if stream is None or identity(stream["JobID"]) != job["JobID"]:
                raise SourceConflict("Replacement execution membership changed.")
            wire = stream_wire(stream)
            if wire["Fence"] != job["Fence"] or identity(wire["OwnerID"]) != identity(
                job["OwnerID"]
            ):
                raise SourceConflict("Replacement execution owner differs from its publication.")
            scope = dict(wire, OwnerKind="job", ScopeJson=json.loads(wire["ScopeJson"]))
            registration.authorize_scope(scope)
            verifier.verify(
                key,
                account=job["AccountKey"],
                registration_hash=bytes(stream["RegistrationHash"]),
                require_observation=False,
            )

    def dispatch(self, message):
        expected = {"version", "action", "job_id", "operation"}
        operation = message.get("operation")
        if operation in {"execute", "fields", "validate", "context"}:
            expected |= {"token"}
        if operation in {"execute", "fields", "validate"}:
            expected |= {"step"}
        if operation in {"execute", "validate"}:
            expected |= {"payload"}
        if operation == "execute":
            expected |= {"actor", "reason"}
        if operation == "reconcile":
            expected |= {"recovery_action"}
        if set(message) != expected or operation not in {
            "inspect",
            "execute",
            "fields",
            "validate",
            "context",
            "reconcile",
        }:
            raise SourceConflict("Exact bounded replacement recovery message required.")
        job_id = identity(message["job_id"])
        with self.authority._lock:
            self.broker.boundary.recheck()
            workflow = self.workflow(job_id)
            if operation == "fields":
                return workflow.input_fields(job_id, message["step"], message["token"])
            if operation == "validate":
                return workflow.validate_input(
                    job_id, message["step"], message["token"], message["payload"]
                )
            if operation == "context":
                _, state = workflow._reviewed(job_id, message["token"])
                if state["activation"] is None:
                    raise SourceConflict("Verified activation is required before continuation.")
                return state["activation"]
            if operation == "reconcile":
                return workflow.reconcile(job_id, message["recovery_action"])
            if operation == "execute":
                workflow.execute(
                    job_id,
                    message["step"],
                    message["token"],
                    message["actor"],
                    message["reason"],
                    payload=message["payload"],
                )
            evidence, token, resolved = workflow.inspect(job_id)
            return dict(evidence=evidence, token=token, resolved=resolved)
