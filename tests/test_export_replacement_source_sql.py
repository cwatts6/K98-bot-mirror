"""Replacement pool queue, delivery and settlement on temporary SQL objects.

Immutable source-generation loading is injected; publication, authority journals,
pool ownership and queue transactions run unchanged against a simulated provider.
"""

from copy import deepcopy
from datetime import datetime
import json
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import one
from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
from kvk.services.new_source_delivery_service import deliver_coordinated_export
from kvk.services.new_source_export_service import GoogleSheetsTransport
from services.export_coordination_dal import ExportCoordinationDAL, identity
from services.export_execution_authority import ExecutionUncertain
from services.export_execution_protocol import ProviderRequest, encode, validate_response
from services.export_recovery_dal import ExportRecoveryDAL
from services.export_replacement_authority import ReplacementAuthority
from services.export_replacement_delivery import ReplacementDelivery
from services.export_replacement_delivery_dal import ReplacementDeliveryDAL
from services.export_runtime_composition import (
    AuthorityStream,
    ExportRuntime,
    NewSourceJobStreams,
    RuntimeRegistration,
)
from tests import test_export_target_containment_sql as fixture_module
from tests.test_export_enrollment_service import FakeChild
from tests.test_export_replacement_activation_sql import activation as activation
from tests.test_export_replacement_pool_sql import pytestmark as pytestmark, recovery as recovery
from tests.test_export_replacement_verification_sql import (
    contained_job as contained_job,
    proposal_service as proposal_service,
    verification as verification,
)
from tests.test_kvk_source_delivery import google_delivery


@pytest.fixture
def source_delivery(monkeypatch, request):
    rewrite = fixture_module.local_sql
    monkeypatch.setattr(
        fixture_module,
        "local_sql",
        lambda text: rewrite(text).replace("=ExportJob.", "=#ExportJob."),
    )
    monkeypatch.setattr(
        fixture_module,
        "TABLES",
        (
            *fixture_module.TABLES,
            "dbo.ExportAttemptPart",
            "dbo.ExportReplacementDelivery",
            "KVK.SourceOutputDisposition",
            "KVK.SourceExportIntent",
            "KVK.SeasonSource",
        ),
    )
    r = request.getfixturevalue("activation")
    cursor_type = type(r.f.connect().cursor())
    execute = cursor_type.execute

    def temporary_nulls(cursor, statement, *args):
        # SQLDescribeParam cannot resolve local temp tables and, with XACT_ABORT,
        # silently rolls back earlier statements before binding NULL. Express
        # fixture NULLs literally; all non-null values stay bound parameters.
        if any(value is None for value in args):
            pieces = statement.split("?")
            assert len(pieces) == len(args) + 1
            statement = pieces[0] + "".join(
                ("NULL" if value is None else "?") + tail
                for value, tail in zip(args, pieces[1:], strict=True)
            )
            args = tuple(value for value in args if value is not None)
        return execute(cursor, statement, *args)

    monkeypatch.setattr(cursor_type, "execute", temporary_nulls)
    r.activated = r.apply()
    original_registration = r.service.proposals.registration
    registration = RuntimeRegistration(r.activated["registration"])
    coordinator = ExportCoordinationDAL(
        r.f.connect, preparations=True, output_operations=True, execution_evidence=True
    )
    runtime = ExportRuntime.__new__(ExportRuntime)
    runtime.connect, runtime.registration, runtime.dal = r.f.connect, registration, coordinator
    runtime.pools = SourceOutputPoolDAL(r.f.connect, execution_evidence=True)
    runtime.registration_history = (original_registration, registration)
    discovery = ExportRecoveryDAL(
        r.f.connect, registration=registration, history=runtime.registration_history
    )
    original = discovery.job(r.f.job)["job"]
    old_pool = coordinator.operator_snapshot(r.f.job)["pool"]["pool"]
    now = datetime(2026, 10, 15)
    r.f.insert(
        "SeasonSource",
        dict(
            KVK_NO=7,
            SourceKey="snapshot_report_v1",
            ChoiceID=old_pool["ChoiceID"],
            ChosenBy="test",
            ChosenUTC=now,
            Reason="Synthetic retained source",
            ProvenanceJson="{}",
            SeasonState="open",
            SeasonVersion=1,
        ),
    )
    r.f.insert(
        "SourceExportIntent",
        dict(
            IntentID=original["IntentID"],
            SourceKey="snapshot_report_v1",
            KVK_NO=7,
            ChoiceID=old_pool["ChoiceID"],
            CommitSequence=1,
            VectorHash=bytes.fromhex(original["InputHash"]),
            ExportSchemaVersion="test",
            IntentState="materialized",
            CreatedUTC=now,
        ),
    )

    def retained_intent(cursor, intent_id):
        assert identity(intent_id) == original["IntentID"]
        cursor.execute("SELECT * FROM KVK.SourceExportIntent WHERE IntentID=?", intent_id)
        return one(cursor), []

    monkeypatch.setattr("kvk.dal.source_update_dal.read_export_intent", retained_intent)
    weights = Mock(side_effect=AssertionError("Replacement must preserve original weights"))
    monkeypatch.setattr("kvk.dal.source_weight_dal.require_current_export_weights", weights)
    memory, _, api = google_delivery()
    generation = memory["generation"]
    runtime.load_generation = Mock(return_value=generation)
    monkeypatch.setattr(
        "kvk.services.new_source_export_service.load_intent_generation", lambda **kwargs: generation
    )
    verifier = ReplacementAuthority.__new__(ReplacementAuthority)
    verifier.connect, verifier.authority = r.f.connect, r.service.authority
    r.delivery_verifier = verifier
    r.delivery = ReplacementDelivery(
        dal=ReplacementDeliveryDAL(r.f.connect, coordinator),
        discovery=discovery,
        source_plan=runtime.replacement_source_plan,
        verify_delivery=verifier.verify_delivery,
        verify_input=verifier.verify_input,
    )
    r.actor, r.reason = "recovery:" + str(uuid4()), "Publish retained original source"
    r.delivery.execute(r.f.job, r.activated, "publish_replacement", actor=r.actor, reason=r.reason)
    template = deepcopy(api.files_data["fake-index"])
    r.verification_host = r.service.authority.host
    r.verification_provider = r.runtime
    r.runtime, r.api, r.weights, r.coordinator = runtime, api, weights, coordinator

    def prepare_publication(activated):
        r.activated = activated
        registration = RuntimeRegistration(activated["registration"])
        r.claim = coordinator.claim_next("test-account")
        assert r.claim is not None
        r.running = coordinator.authorize(r.claim)
        pool = runtime.pools.snapshot(r.activated["replacement_id"])
        sheets_registration = registration.sheets(pool)
        for file_id in r.activated["mapping"].values():
            if file_id in api.files_data:
                continue
            api.files_data[file_id] = dict(
                deepcopy(template),
                id=file_id,
                permissions=[
                    dict(type="user", role="owner", emailAddress=sheets_registration.owner_email),
                    dict(
                        type="user",
                        role="writer",
                        emailAddress=sheets_registration.service_account_email,
                    ),
                ],
            )
            api.grids[file_id] = dict(
                Sheet1=dict(
                    sheetId=42, title="Sheet1", gridProperties=dict(rowCount=1000, columnCount=26)
                )
            )
        provider = SimpleNamespace(failure=None, sent=[])

        class Child(FakeChild):
            def execute(self, message):
                typed = ProviderRequest.parse(message)
                assert typed.target in r.activated["mapping"].values()
                provider.sent.append(typed)
                args = typed.arguments
                if typed.operation.startswith("drive."):
                    _, resource, method = typed.operation.split(".")
                    args["fileId"] = typed.target
                    result = api.execute("/" + resource, method, args, 0)
                else:
                    args["spreadsheetId"] = typed.target
                    method = typed.operation.split(".")[-1]
                    path = (
                        "/spreadsheets/values"
                        if typed.operation.startswith("sheets.values.")
                        else "/spreadsheets"
                    )
                    result = api.execute(path, method, args, 0)
                    if typed.operation == "sheets.values.get":
                        result["range"] = args["range"]
                    else:
                        result["spreadsheetId"] = typed.target
                    if typed.operation == "sheets.batchUpdate":
                        result["replies"] = [{} for _ in args["body"]["requests"]]
                    if typed.operation == "sheets.values.update":
                        values = args["body"]["values"]
                        result.update(
                            updatedRange=args["range"],
                            updatedRows=len(values),
                            updatedColumns=max(map(len, values), default=0),
                            updatedCells=sum(map(len, values)),
                        )
                validate_response(typed, result)
                if provider.failure == typed.operation:
                    raise TimeoutError("Injected lost response after provider success")
                return result

        authority = r.service.authority
        authority.host = SimpleNamespace(
            create_suspended=lambda identifier: Child(identifier, provider)
        )

        def open_stream(identifier, scope):
            registration.authorize_scope(scope)
            authority.open_stream(
                stream_id=identifier,
                scope=dict(
                    scope,
                    ScopeJson=encode(scope["ScopeJson"]).decode(),
                    RegistrationHash=bytes.fromhex(scope["RegistrationHash"]),
                    SnapshotHash=bytes.fromhex(scope["SnapshotHash"]),
                ),
            )

        client = SimpleNamespace(
            open_stream=open_stream, close_stream=authority.close_stream, execute=authority.execute
        )
        client.stream = lambda scope: AuthorityStream(client, scope)
        stream = NewSourceJobStreams(coordinator=coordinator, client=client).delivery(r.claim)
        transport = GoogleSheetsTransport.from_authority(
            registration=sheets_registration,
            reuse_guard=lambda *_: False,
            protected_file_ids=registration.value()["protected_file_ids"],
            execution=stream.execute,
            stream_id=stream.stream_id,
            authorize=lambda **_: None,
        )
        r.publish = lambda: deliver_coordinated_export(
            job=r.running,
            claim=r.claim,
            dal=coordinator,
            transport=transport,
            connect=r.f.connect,
            budget=Mock(),
            stop=Event(),
            authority_stream=stream,
            retirement_verifier=Mock(
                side_effect=AssertionError("Fresh pool has no prior generation")
            ),
            retirement_stream_factory=Mock(),
            retirement_transport_factory=Mock(),
        )
        r.provider = provider

    r.prepare_publication = prepare_publication
    prepare_publication(r.activated)
    return r


def test_complete_replacement_pool_publishes_retained_intent_and_verifies_delivery(source_delivery):
    r = source_delivery
    assert not r.delivery.inspect(r.f.job, r.activated)["resolved"]
    receipt = r.publish()
    final = r.delivery.inspect(r.f.job, r.activated)
    assert final["resolved"] and final["stage"] == "replacement_delivered", final
    assert receipt["files"][0] == r.activated["mapping"]["old-file"]
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    assert r.f.sql.execute("SELECT IntentState FROM #SourceExportIntent").fetchval() == "confirmed"
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #SourceOutputSlot WHERE FileID LIKE 'old-%' AND State='quarantined'"
        ).fetchval()
        == 4
    )
    r.weights.assert_not_called()


def test_matching_sql_lineage_cannot_replace_original_private_commitment(source_delivery):
    from kvk.dal.new_source_import_dal import SourceConflict

    r = source_delivery
    r.publish()
    provenance = json.loads(
        r.f.sql.execute(
            "SELECT ProvenanceJson FROM #ExportJob WHERE JobID=?", r.claim.job_id
        ).fetchval()
    )
    provenance["replacement"]["original_input_sha256"] = "ab" * 32
    r.f.sql.execute(
        "UPDATE #ExportJob SET ProvenanceJson=? WHERE JobID=?",
        json.dumps(provenance),
        r.claim.job_id,
    )
    r.f.sql.execute(
        "UPDATE #ExportReplacementDelivery SET OriginalInputHash=? WHERE OriginalJobID=?",
        bytes.fromhex("ab" * 32),
        r.f.job,
    )
    with pytest.raises(SourceConflict, match="lineage"):
        r.delivery.inspect(r.f.job, r.activated)


def test_lost_source_write_links_repair_without_replaying_original(source_delivery):
    r = source_delivery
    r.provider.failure = "sheets.values.update"
    with pytest.raises(ExecutionUncertain, match="closure"):
        r.publish()
    r.coordinator.fail(r.claim, retain_claims=True)
    final = r.delivery.inspect(r.f.job, r.activated)
    assert not final["resolved"] and final["stage"] == "replacement_needs_attention"
    assert final["job_id"] == r.claim.job_id
    assert sum(q.operation == "sheets.values.update" for q in r.provider.sent) == 1
    assert (
        r.f.sql.execute("SELECT IntentState FROM #SourceExportIntent").fetchval() == "materialized"
    )
    assert (
        r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", r.f.job).fetchval()
        == "uncertain"
    )
    r.delivery.execute(r.f.job, r.activated, "publish_replacement", actor=r.actor, reason=r.reason)
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval() == 1
    assert sum(q.operation == "sheets.values.update" for q in r.provider.sent) == 1


def test_lost_final_commit_reply_resolves_from_original_delivery_evidence(
    source_delivery, monkeypatch
):
    from kvk.dal.new_source_import_dal import UncertainCommit

    r = source_delivery
    confirm = r.coordinator.confirm

    def lost(*args, **kwargs):
        confirm(*args, **kwargs)
        raise UncertainCommit("Injected lost settlement acknowledgement")

    monkeypatch.setattr(r.coordinator, "confirm", lost)
    with pytest.raises(UncertainCommit):
        r.publish()
    calls = len(r.provider.sent)
    assert r.delivery.inspect(r.f.job, r.activated)["resolved"]
    assert len(r.provider.sent) == calls
    assert r.f.sql.execute("SELECT IntentState FROM #SourceExportIntent").fetchval() == "confirmed"


def test_confirmed_source_without_matching_receipt_does_not_resolve(source_delivery):
    from kvk.dal.new_source_import_dal import SourceConflict

    r = source_delivery
    r.publish()
    receipt = json.loads(
        r.f.sql.execute(
            "SELECT ReceiptJson FROM #ExportAttempt WHERE JobID=?", r.claim.job_id
        ).fetchval()
    )
    receipt["files"] = ["other-file"]
    r.f.sql.execute(
        "UPDATE #ExportAttempt SET ReceiptJson=? WHERE JobID=?", json.dumps(receipt), r.claim.job_id
    )
    r.f.sql.commit()
    with pytest.raises(SourceConflict, match="receipt"):
        r.delivery.inspect(r.f.job, r.activated)


def recover_failed_replacement(r, monkeypatch):
    """Use the actual guided actions to replace a replacement's unknown write."""
    from services.export_replacement_authority import HistoricalRecoveryDiscovery
    from services.export_replacement_verification import verification_plan
    from services.export_replacement_workflow import ReplacementWorkflow

    first_activation = r.activated
    first_job = r.claim.job_id
    r.provider.failure = "sheets.values.update"
    with pytest.raises(ExecutionUncertain):
        r.publish()
    r.coordinator.fail(r.claim, retain_claims=True)
    first_requests = tuple(r.provider.sent)
    assert sum(q.operation == "sheets.values.update" for q in first_requests) == 1
    authority = r.service.authority
    resolver = ReplacementAuthority(
        SimpleNamespace(authority=authority, registration=r.runtime.registration_history[0])
    )
    registrations, current = resolver.registrations()
    service = resolver.services(current, history=registrations)
    authority.host = r.verification_host

    def plan_factory(proposal, key):
        original = r.plan.value()
        plan = verification_plan(
            current,
            proposal,
            verification_id=key,
            manifest_hash=original["manifest_sha256"],
            profile_hash=original["credential_profile_sha256"],
            project_id=original["project_id"],
        )
        r.verification_provider.plan = plan
        return plan

    # The temporary connection has one thread. Production retains this worker
    # in the authority lifetime; that behavior has separate lifecycle tests.
    monkeypatch.setattr(service.verification, "start", service.verification.run)
    flow = ReplacementWorkflow(
        proposals=service.proposals,
        verification=service.verification,
        activation=service,
        plan_factory=plan_factory,
        continuation=r.delivery,
    )
    for action in (
        "isolate_targets",
        "choose_replacements",
        "verify_replacements",
        "activate_replacements",
    ):
        evidence, token, resolved = flow.inspect(first_job)
        assert not resolved and action in evidence["actions"], evidence
        payload = None
        if action == "choose_replacements":
            payload = dict(owner_email="owner@example.com")
            payload.update({old: "second-" + old for old in evidence["targets"]})
            assert flow.validate_input(first_job, action, token, payload)
        flow.execute(
            first_job,
            action,
            token,
            "recovery:" + str(uuid4()),
            "Recover failed replacement through reviewed action",
            payload=payload,
        )
    registrations, current = resolver.registrations()
    second = resolver.activated_replacement(first_job)
    r.runtime.registration = current
    r.runtime.registration_history = tuple(registrations)
    r.delivery.discovery = HistoricalRecoveryDiscovery(r.f.connect, registrations)
    r.delivery.next_activation = resolver.activated_replacement
    assert not r.delivery.inspect(r.f.job, first_activation)["resolved"]
    r.delivery.execute(
        first_job,
        second,
        "publish_replacement",
        actor="recovery:" + str(uuid4()),
        reason="Publish retained source to second verified replacement",
    )
    r.prepare_publication(second)
    r.publish()
    assert r.delivery.inspect(r.f.job, first_activation)["resolved"]
    assert r.delivery.inspect(first_job, second)["resolved"]
    assert all(q.target in second["mapping"].values() for q in r.provider.sent)
    assert len(resolver.authenticated_history()[1]) == 2
    for key in (r.f.job, first_job):
        assert (
            r.f.sql.execute("SELECT State FROM #ExportJob WHERE JobID=?", key).fetchval()
            == "uncertain"
        )
    return [first_activation, second]


@pytest.mark.parametrize("replacement_failed", [False, True])
def test_waiting_source_queues_its_own_retained_intent_after_blocker_finishes(
    source_delivery, monkeypatch, replacement_failed
):
    from dataclasses import replace

    from kvk.dal.new_source_import_dal import digest
    from services.export_replacement_projection import continuation_activation

    r = source_delivery
    if replacement_failed:
        history = recover_failed_replacement(r, monkeypatch)
    else:
        r.publish()
        history = [r.activated]
    r.f.sql.autocommit = True  # Synthetic fixture rows, outside application transactions.
    cursor = r.f.sql.execute("SELECT * FROM #ExportJob WHERE JobID=?", r.f.job)
    job = one(cursor)
    waiting_id, intent_id = str(uuid4()), str(uuid4())
    input_hash = digest("different committed source generation")
    previous_generation = r.runtime.load_generation.return_value
    waiting_generation = replace(
        previous_generation,
        selections=tuple(
            replace(s, selection_version=s.selection_version + 1)
            for s in previous_generation.selections
        ),
    )
    r.runtime.load_generation.return_value = waiting_generation
    monkeypatch.setattr(
        "kvk.services.new_source_export_service.load_intent_generation",
        lambda **kwargs: waiting_generation,
    )
    intent = one(r.f.sql.execute("SELECT * FROM #SourceExportIntent"))
    r.f.insert(
        "SourceExportIntent",
        dict(
            intent,
            IntentID=intent_id,
            CommitSequence=2,
            VectorHash=input_hash,
            IntentState="materialized",
        ),
    )
    r.f.insert(
        "ExportJob",
        dict(
            job,
            JobID=waiting_id,
            IntentID=intent_id,
            InputHash=input_hash,
            State="waiting",
            OwnerID=None,
            Fence=0,
            Version=1,
            EnqueueSequence=50,
            ProvenanceJson=json.dumps(
                dict(
                    output_preflight=dict(
                        generation_key=waiting_generation.key,
                        manifest_hash=digest(waiting_generation.manifest()).hex(),
                    )
                )
            ),
        ),
    )
    for key in r.f.sql.execute(
        "SELECT ResourceKey FROM #ExportJobResource WHERE JobID=?", r.f.job
    ).fetchall():
        r.f.insert("ExportJobResource", dict(JobID=waiting_id, ResourceKey=key[0]))

    def retained_intent(cursor, key):
        assert identity(key) == intent_id
        cursor.execute("SELECT * FROM KVK.SourceExportIntent WHERE IntentID=?", key)
        return one(cursor), []

    monkeypatch.setattr("kvk.dal.source_update_dal.read_export_intent", retained_intent)
    activation = continuation_activation(
        history, targets=list(history[0]["mapping"]), consumer="new_source"
    )
    activation = r.delivery_verifier.seal_waiting_input(
        r.delivery.discovery.job(waiting_id), activation
    )
    r.delivery.execute(
        waiting_id,
        activation,
        "publish_replacement",
        actor="recovery:" + str(uuid4()),
        reason="Continue waiting source export",
    )
    link = r.delivery.dal.read(waiting_id, activation["activation_id"], "test-account")
    queued = r.delivery.discovery.job(link["ReplacementJobID"])["job"]
    assert queued["IntentID"] == intent_id and queued["InputHash"] == input_hash.hex()
    assert queued["State"] in {"waiting", "ready"}
    assert (
        r.delivery.dal.continuation_anchor(waiting_id, "test-account")
        == activation["activation_id"]
    )
    assert (
        r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementDelivery").fetchval()
        == len(history) + 1
    )
    r.weights.assert_not_called()
    r.prepare_publication(activation)
    r.publish()
    assert r.delivery.inspect(waiting_id, activation)["resolved"]
