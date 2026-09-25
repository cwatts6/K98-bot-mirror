"""Offline rollover journal/probe evidence; no SQL, provider or OS execution."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.services.new_source_export_service import GoogleSheetsTransport
from services.export_coordination_dal import bounded_json
from services.export_execution_authority import ExecutionUncertain
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import CATALOGUE_SEED, ProviderRequest, encode
from services.export_provider_adapter import ProviderOutcomeUnknown
from services.export_reconciliation_service import ClosedProbeReplay
from services.export_rollover_evidence import (
    RolloverCompletionProbe,
    RolloverDrainProbe,
    RolloverJournalVerifier,
    observe_rollover_completion,
    observe_rollover_drain,
)
from services.export_runtime_composition import OutputOperationStreams, output_operation_scope
from tests.test_export_reconciliation_service import sealed_publication_fixture
from tests.test_export_runtime_composition import operation_snapshot, recorded_google_memory


def rollover_fixture(*, uncertain=False, acknowledged=True, public=False, slot_count=2):
    args, api, messages = recorded_google_memory()
    registration = args["transport"].registration
    registration = replace(
        registration,
        audience="public_viewer" if public else "private",
        slot_file_ids=tuple(f"fake-{i}" for i in range(1, slot_count + 1)),
    )
    for file_id in registration.slot_file_ids:
        if file_id not in api.files_data:
            api.files_data[file_id] = dict(deepcopy(api.files_data["fake-1"]), id=file_id)
            api.grids[file_id] = deepcopy(api.grids["fake-1"])
    if public:
        for file in api.files_data.values():
            file["permissions"].append(
                dict(id="public-reader", type="anyone", role="reader", allowFileDiscovery=False)
            )
    setup_version = 4 * (slot_count + 1) + 4
    raw_execute = args["authority_stream"].client.execute.side_effect
    snapshot = operation_snapshot(running=True)
    op, context = snapshot["operation"], snapshot["pool"]
    pool = context["pool"]
    old_choice, new_choice = str(uuid4()), str(uuid4())
    pool.update(
        IndexFileID=registration.index_file_id,
        ExpectedOwner=registration.owner_email,
        RegistrationJson=bounded_json(asdict(registration)),
        RegistrationHash=digest(asdict(registration)).hex(),
        SourceKey="snapshot_report_v1",
        ActiveKVK=16,
        ChoiceID=old_choice,
        Fence=op["Fence"],
    )
    context.update(
        slots=[
            dict(FileID=file, PoolID=pool["PoolID"], Epoch=2, OwnerID=None, State="free")
            for file in registration.slot_file_ids
        ],
        jobs=[],
        attempts=[],
        parts=[],
        legacy_receipts=[],
    )
    original = deepcopy(context)
    original["pool"].update(PoolState="active", OwnerID=None, Fence=0, Version=9)
    plan = dict(
        snapshot=original,
        new_choice=dict(SourceKey=pool["SourceKey"], KVK_NO=17, ChoiceID=new_choice),
    )
    op.update(
        SourceKey=pool["SourceKey"],
        OldKVK=16,
        NewKVK=17,
        OldChoiceID=old_choice,
        NewChoiceID=new_choice,
        TargetEpoch=3,
        PlanJson=bounded_json(plan),
        PlanHash=digest(plan).hex(),
        CurrentFileID=registration.index_file_id,
        State="uncertain" if uncertain else "running",
        Phase="uncertain" if uncertain else ("setup_verified" if acknowledged else "setup_pending"),
        Version=setup_version + int(uncertain) + int(acknowledged),
    )
    targets = ExportExecutionDAL.proof_targets(snapshot)
    template = snapshot["resources"][0]
    snapshot["resources"] = [
        dict(template, ResourceKey=key)
        for key in sorted(["account:account-a", *("destination:" + file for file in targets)])
    ]
    proof_id = str(uuid4())
    proof_body = dict(
        state="confirmed",
        snapshot_hash=digest({"old_drain": True}).hex(),
        all_writers_terminated=True,
        remote_outcomes_reconciled=True,
        evidence_id=str(uuid4()),
    )
    membership = encode(
        dict(
            version=2,
            targets=targets,
            history=dict(count=0, sha256=CATALOGUE_SEED.hex()),
            probe=dict(stream_id=str(uuid4()), version=3),
        )
    ).decode()
    proof = dict(
        ProofID=proof_id,
        SessionID=str(uuid4()),
        AccountKey=op["AccountKey"],
        ProofKind="rollover_drain",
        Outcome="confirmed",
        SnapshotHash=bytes.fromhex(proof_body["snapshot_hash"]),
        RegistrationHash=bytes.fromhex(pool["RegistrationHash"]),
        EvidenceJson=bounded_json(proof_body),
        MembershipJson=membership,
        MembershipHash=hashlib.sha256(membership.encode("utf-16-le")).digest(),
    )
    progress = dict(
        drain_hash=proof_body["snapshot_hash"], proof=dict(proof_body, proof_id=proof_id), files={}
    )
    op["ProgressJson"] = bounded_json(progress)
    records, requests, private = {}, {}, {}

    def retain(observations, stream_id, purpose, version, scope_snapshot=None):
        dal, store, stream, documents = sealed_publication_fixture(
            dict(snapshot=scope_snapshot or snapshot, stream_id=stream_id), observations
        )
        for identifier in dal.request_ids(stream_id):
            request, _ = dal.read_request(identifier)
            payload = json.loads(documents[request["PayloadReference"]])
            request["RequestKind"] = (
                "mutation" if ProviderRequest.parse(payload).mutation else "read"
            )
            requests[identifier] = dal
        for reference in documents:
            private[reference] = store
        stream.update(
            Purpose=purpose,
            OutputOperationID=op["OperationID"],
            JobID=None,
            PreparationID=None,
            NestedToken=None,
            OwnerID=op["OwnerID"],
            Fence=op["Fence"],
            Epoch=op["OldEpoch"],
            ClaimVersion=version,
            ScopeJson=bounded_json(output_operation_scope(snapshot, purpose="probe")["ScopeJson"]),
        )
        records[stream_id] = dict(dal=dal, store=store, stream=stream, documents=documents)
        return stream

    def run_phase(version, action):
        stream_id, observations = str(uuid4()), []

        def execute(message):
            response = raw_execute(message)
            observations.append((deepcopy(message), deepcopy(response)))
            return response

        transport = GoogleSheetsTransport.from_authority(
            registration=registration,
            protected_file_ids=args["transport"].protected,
            reuse_guard=lambda *_: False,
            execution=execute,
            stream_id=stream_id,
            authorize=lambda **_: None,
        )
        transport._request_guard = lambda _: None
        result = action(transport)
        retain(observations, stream_id, "mutation", version)
        return result

    for offset, file_id in enumerate(targets):
        run_phase(4 + 4 * offset, lambda t: t.rollover_private(file_id))
        progress["files"][file_id] = run_phase(6 + 4 * offset, lambda t: t.rollover_clear(file_id))
    setup = run_phase(setup_version, lambda t: t.rollover_setup(registration.index_file_id, 16, 17))
    if acknowledged:
        progress["setup"] = setup
    progress["request"] = dict(
        phase="setup_verified" if acknowledged else "setup_pending",
        file_id=registration.index_file_id,
        evidence=setup if acknowledged else None,
    )
    op["ProgressJson"] = bounded_json(progress)
    trace = []

    def read(reference, expected):
        trace.append("private")
        return private[reference].read_reference(reference, expected)

    evidence = SimpleNamespace(
        read_proof=lambda identifier: deepcopy(proof) if identifier == proof_id else None,
        read_catalogue=lambda *_: (deepcopy(records[k]["stream"]) for k in sorted(records)),
        read_stream=lambda identifier: deepcopy(records[identifier]["stream"]),
        stream_digest=lambda identifier: records[identifier]["dal"].stream_digest(identifier),
        request_ids=lambda identifier: records[identifier]["dal"].request_ids(identifier),
        read_request=lambda identifier: requests[identifier].read_request(identifier),
    )
    return SimpleNamespace(
        snapshot=snapshot,
        registration=registration,
        protected=args["transport"].protected,
        api=api,
        messages=messages,
        raw_execute=raw_execute,
        dal=evidence,
        store=SimpleNamespace(read_reference=read),
        records=records,
        retain=retain,
        trace=trace,
        progress=progress,
        proof=proof,
    )


def verifier(fixture):
    return RolloverJournalVerifier(
        dal=fixture.dal,
        store=fixture.store,
        registration=fixture.registration,
        protected_file_ids=fixture.protected,
    )


def probe_arguments(fixture):
    observations = []

    def execute(message):
        assert not ProviderRequest.parse(message).mutation
        response = fixture.raw_execute(message)
        observations.append((deepcopy(message), deepcopy(response)))
        return response

    return (
        dict(
            snapshot=fixture.snapshot,
            registration=fixture.registration,
            protected_file_ids=fixture.protected,
            execute=execute,
            stream_id=str(uuid4()),
        ),
        observations,
    )


@pytest.mark.parametrize("uncertain", [False, True])
@pytest.mark.parametrize("acknowledged", [False, True])
@pytest.mark.parametrize("public", [False, True])
def test_original_closed_phases_and_current_completion_keep_old_clear_separate_from_marker(
    uncertain, acknowledged, public
):
    f = rollover_fixture(uncertain=uncertain, acknowledged=acknowledged, public=public)
    original = deepcopy(f.snapshot)
    calls = len(f.api.calls)
    assert len(verifier(f).verify(f.snapshot)) == 64
    assert len(f.api.calls) == calls
    args, observations = probe_arguments(f)
    result = observe_rollover_completion(**args)
    assert json.loads(result.original_clears_json)["fake-index"]["empty"] is True
    assert set(json.loads(result.current_slots_json)) == {"fake-1", "fake-2"}
    assert "empty" not in json.loads(result.setup_json)
    assert not hasattr(result, "writer_terminated") and not hasattr(result, "proof_id")
    assert len(observations) == 7 and f.snapshot == original


def test_maximum_sixteen_slot_pool_preserves_every_original_and_current_file():
    f = rollover_fixture(slot_count=16, public=True)
    f.snapshot["pool"]["registration_count"] = 8
    assert len(verifier(f).verify(f.snapshot)) == 64
    args, observations = probe_arguments(f)
    result = observe_rollover_completion(**args)
    assert len(json.loads(result.original_clears_json)) == 17
    assert len(json.loads(result.current_slots_json)) == 16
    assert len(observations) == 35


@pytest.mark.parametrize(
    "damage",
    [
        "state",
        "phase",
        "request",
        "file",
        "owner",
        "fence",
        "version",
        "resource",
        "blocked_resource",
        "pool_fence",
        "choice",
        "target_epoch",
        "source",
        "plan",
        "old_plan_owner",
        "registration_count",
        "missing_clear",
        "sheet_id",
        "empty_flag",
        "hash",
        "quarantined",
        "slot_owner",
        "slot_epoch",
        "slot_pool",
        "pending_job",
        "uncertain_legacy",
        "missing_setup",
        "request_evidence",
    ],
)
def test_completion_cannot_adopt_partial_stale_or_different_operation(damage):
    f = rollover_fixture()
    op, context = f.snapshot["operation"], f.snapshot["pool"]
    if damage in {
        "state",
        "phase",
        "file",
        "owner",
        "fence",
        "version",
        "choice",
        "target_epoch",
        "source",
        "plan",
    }:
        key, value = {
            "state": ("State", "blocked"),
            "phase": ("Phase", "clear_verified"),
            "file": ("CurrentFileID", "fake-1"),
            "owner": ("OwnerID", str(uuid4())),
            "fence": ("Fence", 99),
            "version": ("Version", 0),
            "choice": ("NewChoiceID", str(uuid4())),
            "target_epoch": ("TargetEpoch", 9),
            "source": ("SourceKey", "legacy"),
            "plan": ("PlanHash", "f" * 64),
        }[damage]
        op[key] = value
    elif damage == "resource":
        f.snapshot["resources"][0]["ActiveJobID"] = str(uuid4())
    elif damage == "blocked_resource":
        f.snapshot["resources"][0]["BlockedReason"] = "unknown"
    elif damage == "pool_fence":
        context["pool"]["Fence"] += 1
    elif damage == "registration_count":
        context["registration_count"] = True
    elif damage == "old_plan_owner":
        plan = json.loads(op["PlanJson"])
        plan["snapshot"]["pool"]["OwnerID"] = op["OperationID"]
        op.update(PlanJson=bounded_json(plan), PlanHash=digest(plan).hex())
    elif damage in {"quarantined", "slot_owner", "slot_epoch", "slot_pool"}:
        key, value = {
            "quarantined": ("State", "quarantined"),
            "slot_owner": ("OwnerID", op["OwnerID"]),
            "slot_epoch": ("Epoch", 9),
            "slot_pool": ("PoolID", str(uuid4())),
        }[damage]
        context["slots"][0][key] = value
    elif damage == "pending_job":
        context["jobs"].append(dict(State="uncertain"))
    elif damage == "uncertain_legacy":
        context["legacy_receipts"].append(dict(DeliveryState="uncertain"))
    else:
        progress = json.loads(op["ProgressJson"])
        if damage == "request":
            progress["request"]["phase"] = "clear_pending"
        elif damage == "missing_clear":
            progress["files"].pop("fake-2")
        elif damage == "missing_setup":
            progress.pop("setup")
        elif damage == "request_evidence":
            progress["request"]["evidence"]["sheet_id"] += 1
        else:
            key, value = {
                "sheet_id": ("sheet_id", True),
                "empty_flag": ("empty", 1),
                "hash": ("manifest_hash", "not-a-hash"),
            }[damage]
            progress["files"]["fake-1"][key] = value
        op["ProgressJson"] = bounded_json(progress)
    args, observations = probe_arguments(f)
    with pytest.raises((SourceConflict, ValueError)):
        observe_rollover_completion(**args)
    assert not observations


@pytest.mark.parametrize(
    "damage",
    [
        "proof_id",
        "proof_kind",
        "proof_account",
        "proof_snapshot",
        "proof_registration",
        "proof_type",
        "proof_membership",
        "missing_phase",
        "wrong_phase_version",
        "phase_owner",
        "phase_fence",
        "phase_epoch",
        "phase_registration",
        "phase_resources",
        "phase_nested",
        "phase_unclosed",
        "unknown_request",
        "missing_closure",
        "clear_hash",
        "clear_sheet",
        "setup_body",
        "read_projection",
        "duplicate_phase",
    ],
)
def test_original_journal_requires_protected_proof_and_every_exact_known_closed_phase(damage):
    f = rollover_fixture(uncertain=True)
    clear = next(r for r in f.records.values() if r["stream"]["ClaimVersion"] == 6)
    if damage.startswith("proof_"):
        if damage == "proof_type":
            body = json.loads(f.proof["EvidenceJson"])
            body["all_writers_terminated"] = 1
            f.proof["EvidenceJson"] = bounded_json(body)
        else:
            key, value = {
                "proof_id": ("ProofID", str(uuid4())),
                "proof_kind": ("ProofKind", "retirement"),
                "proof_account": ("AccountKey", "other"),
                "proof_snapshot": ("SnapshotHash", b"s" * 32),
                "proof_registration": ("RegistrationHash", b"r" * 32),
                "proof_membership": ("MembershipHash", b"h" * 32),
            }[damage]
            f.proof[key] = value
    elif damage == "missing_phase":
        f.records.pop(clear["stream"]["StreamID"])
    elif damage in {
        "wrong_phase_version",
        "phase_owner",
        "phase_fence",
        "phase_epoch",
        "phase_registration",
        "phase_resources",
        "phase_nested",
        "phase_unclosed",
    }:
        key, value = {
            "wrong_phase_version": ("ClaimVersion", 77),
            "phase_owner": ("OwnerID", str(uuid4())),
            "phase_fence": ("Fence", 99),
            "phase_epoch": ("Epoch", 9),
            "phase_registration": ("RegistrationHash", b"z" * 32),
            "phase_resources": ("ScopeJson", '{"resources":[]}'),
            "phase_nested": ("NestedToken", str(uuid4())),
            "phase_unclosed": ("State", "frozen"),
        }[damage]
        clear["stream"][key] = value
    elif damage == "missing_closure":
        clear["documents"][clear["stream"]["ClosureReference"]] += b" "
    elif damage == "duplicate_phase":
        extra = deepcopy(clear["stream"])
        extra["StreamID"] = str(uuid4())
        f.records[extra["StreamID"]] = dict(clear, stream=extra)
    elif damage in {"clear_hash", "clear_sheet"}:
        progress = json.loads(f.snapshot["operation"]["ProgressJson"])
        progress["files"]["fake-1"]["manifest_hash" if damage == "clear_hash" else "sheet_id"] = (
            "f" * 64 if damage == "clear_hash" else 700
        )
        f.snapshot["operation"]["ProgressJson"] = bounded_json(progress)
    else:
        record = clear
        if damage == "setup_body":
            record = next(r for r in f.records.values() if r["stream"]["ClaimVersion"] == 16)
        identities = list(record["dal"].request_ids(record["stream"]["StreamID"]))
        request, events = record["dal"].read_request(
            identities[0] if damage == "setup_body" else identities[-2]
        )
        if damage == "unknown_request":
            events[-1]["State"] = "unknown"
        else:
            payload = json.loads(record["documents"][request["PayloadReference"]])
            if damage == "setup_body":
                payload["arguments"]["body"]["values"] = [["not the exact marker"]]
            else:
                payload["arguments"]["includeGridData"] = False
            raw = encode(payload)
            record["documents"][request["PayloadReference"]] = raw
            request["PayloadHash"] = hashlib.sha256(raw).digest()
            prepared = json.loads(record["documents"][events[0]["EvidenceReference"]])
            prepared["payload_hash"] = request["PayloadHash"].hex()
            raw = encode(prepared)
            record["documents"][events[0]["EvidenceReference"]] = raw
            events[0]["EvidenceHash"] = hashlib.sha256(raw).digest()
    calls = len(f.api.calls)
    with pytest.raises((SourceConflict, ValueError, AssertionError, ProviderOutcomeUnknown)):
        verifier(f).verify(f.snapshot)
    assert len(f.api.calls) == calls


@pytest.mark.parametrize(
    "damage", ["slot_values", "slot_sheet", "index_sheet", "index_marker", "index_name"]
)
def test_current_readback_never_reuses_an_old_clear_as_current_truth(damage):
    f = rollover_fixture()
    assert verifier(f).verify(f.snapshot)
    if damage == "slot_values":
        f.api.values["fake-1", "Sheet1"] = [["late old content"]]
    elif damage == "slot_sheet":
        f.api.grids["fake-1"]["Sheet1"]["sheetId"] += 1
    elif damage == "index_sheet":
        f.api.grids["fake-index"]["Sheet1"]["sheetId"] += 1
    elif damage == "index_marker":
        f.api.values["fake-index", "Sheet1"] = [["wrong season"]]
    else:
        f.api.named_ranges["fake-index"] = [dict(namedRangeId="retained")]
    args, observations = probe_arguments(f)
    with pytest.raises(SourceConflict):
        observe_rollover_completion(**args)
    assert observations and all(not ProviderRequest.parse(m).mutation for m, _ in observations)


def test_full_completion_transcript_replays_without_provider_or_journal_rewrite():
    f = rollover_fixture(uncertain=True, acknowledged=False)
    args, observations = probe_arguments(f)
    original = observe_rollover_completion(**args)
    f.retain(observations, args["stream_id"], "probe", f.snapshot["operation"]["Version"])
    calls = len(f.api.calls)
    with ClosedProbeReplay(
        dal=f.dal,
        store=f.store,
        account="account-a",
        snapshot=f.snapshot,
        stream_id=args["stream_id"],
    ) as replay:
        assert observe_rollover_completion(**(args | dict(execute=replay.execute))) == original
    assert len(f.api.calls) == calls


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "close",
        "snapshot",
        "catalogue",
        "original_unknown",
        "origin",
        "origin_drift",
        "origin_snapshot",
    ],
)
def test_completion_probe_closes_rechecks_and_seals_without_issue_or_settlement(
    monkeypatch, failure
):
    from tests.test_export_reconciliation_service import stub_origin_journal

    f = rollover_fixture(uncertain=True, acknowledged=False)
    origins, origin_hash = stub_origin_journal(
        monkeypatch,
        failure,
        lambda: f.snapshot["operation"].update(Version=f.snapshot["operation"]["Version"] + 1),
    )
    pools = Mock(execution_evidence=True)
    pools.operation_snapshot.side_effect = lambda _: deepcopy(f.snapshot)
    args, observations = probe_arguments(f)
    original_snapshot = deepcopy(f.snapshot)
    if failure == "original_unknown":
        record = next(r for r in f.records.values() if r["stream"]["ClaimVersion"] == 16)
        request_id = next(record["dal"].request_ids(record["stream"]["StreamID"]))
        record["dal"].read_request(request_id)[1][-1]["State"] = "unknown"

    @contextmanager
    def probe(snapshot):
        assert origins.call_count == 1
        assert snapshot == original_snapshot
        f.trace.append("open")
        try:
            yield SimpleNamespace(stream_id=args["stream_id"], execute=args["execute"])
        finally:
            f.trace.append("close")
            if failure == "close":
                raise ExecutionUncertain("Close acknowledgment lost")
            f.retain(observations, args["stream_id"], "probe", snapshot["operation"]["Version"])
            if failure == "snapshot":
                f.snapshot["operation"]["Version"] += 1
            elif failure == "catalogue":
                f.retain([], str(uuid4()), "probe", snapshot["operation"]["Version"])

    streams = SimpleNamespace(pools=pools, completion_probe=probe)
    service = RolloverCompletionProbe(
        pools=pools,
        streams=streams,
        dal=f.dal,
        store=f.store,
        registration=f.registration,
        protected_file_ids=f.protected,
    )
    operation_id = f.snapshot["operation"]["OperationID"]
    if failure:
        with pytest.raises((SourceConflict, ExecutionUncertain)):
            service.run(operation_id)
    else:
        result = service.run(operation_id)
        assert result.origin_hash == origin_hash and origins.call_count == 2
        assert result.original_journal_hash == verifier(f).verify(f.snapshot)
        assert json.loads(result.membership_json)["history"]["count"] == 7
        assert not hasattr(result, "proof_id")
    assert (
        f.trace.count("open")
        == f.trace.count("close")
        == (0 if failure in {"original_unknown", "origin"} else 1)
    )
    pools.reconcile_complete.assert_not_called()
    pools.complete.assert_not_called()
    pools.ready.assert_not_called()


@pytest.mark.parametrize("purpose", ["closing", "completion"])
def test_operation_probe_rechecks_snapshot_and_never_claims_or_adopts(purpose):
    snapshot = operation_snapshot(running=purpose == "completion")
    pools, client = Mock(execution_evidence=True), Mock()
    pools.operation_snapshot.return_value = {}
    streams = OutputOperationStreams(pools=pools, client=client)
    method = streams.completion_probe if purpose == "completion" else streams.closing_probe
    with pytest.raises(SourceConflict, match="snapshot changed"):
        method(snapshot)
    client.stream.assert_not_called()
    pools.operation_snapshot.return_value = snapshot
    method(snapshot)
    scope = client.stream.call_args.args[0]
    assert scope["Purpose"] == "probe"
    assert scope["OwnerID"] == snapshot["operation"]["OwnerID"]
    assert (
        scope["SnapshotHash"]
        == digest(snapshot if purpose == "completion" else snapshot["pool"]).hex()
    )
    pools.claim.assert_not_called()


def drain_fixture(*, public=False, slot_count=2):
    f = rollover_fixture(public=public, slot_count=slot_count)
    f.snapshot["operation"].update(
        OwnerID=None,
        Fence=0,
        Version=1,
        State="closing",
        Phase="draining",
        CurrentFileID=None,
        ProgressJson="{}",
    )
    for resource in f.snapshot["resources"]:
        resource.update(OwnerID=None, ActiveOutputOperationID=None)
    # Model an existing old representation without granting release/termination.
    # Retain the fully sealed fake history for catalogue verification.
    f.api.values["fake-index", "Sheet1"] = [["old publication remains retained"]]
    if public:
        for file in f.api.files_data.values():
            file["permissions"].append(
                dict(id="public-reader", type="anyone", role="reader", allowFileDiscovery=False)
            )
    return f


@pytest.mark.parametrize("public", [False, True])
@pytest.mark.parametrize("slot_count", [2, 16])
def test_drain_observes_every_registered_file_without_adopting_or_clearing(public, slot_count):
    f = drain_fixture(public=public, slot_count=slot_count)
    original = deepcopy(f.snapshot)
    f.snapshot["pool"]["registration_count"] = 8
    args, observations = probe_arguments(f)
    result = observe_rollover_drain(**args)
    assert len(observations) == slot_count + 1
    assert all(m["operation"] == "drive.files.get" for m, _ in observations)
    assert result.snapshot_hash == digest(f.snapshot["pool"]).hex()
    assert result.operation_snapshot_hash == digest(f.snapshot).hex()
    assert set(json.loads(result.files_json)) == set(ExportExecutionDAL.proof_targets(f.snapshot))
    assert not any(hasattr(result, k) for k in ("proof_id", "all_writers_terminated", "empty"))
    assert f.snapshot["operation"] == original["operation"]
    assert f.api.values["fake-index", "Sheet1"] == [["old publication remains retained"]]


@pytest.mark.parametrize(
    "damage",
    [
        lambda s: s["operation"].update(State="ready"),
        lambda s: s["operation"].update(State="uncertain"),
        lambda s: s["operation"].update(Phase="private_pending"),
        lambda s: s["operation"].update(Version=2),
        lambda s: s["operation"].update(CurrentFileID="fake-1"),
        lambda s: s["operation"].update(ProgressJson='{"files":{}}'),
        lambda s: s["operation"].update(OwnerID=str(uuid4())),
        lambda s: s["operation"].update(Fence=1),
        lambda s: s["resources"][0].update(ActivePreparationID=str(uuid4())),
        lambda s: s["resources"][0].update(ActiveJobID=str(uuid4())),
        lambda s: s["resources"][0].update(BlockedReason="unknown budget"),
        lambda s: s["pool"]["jobs"].append(dict(State="uncertain")),
        lambda s: s["pool"]["jobs"].append(dict(State="running")),
        lambda s: s["pool"]["jobs"].append(dict(State="ready")),
        lambda s: s["pool"]["jobs"].append(dict(State="waiting")),
        lambda s: s["pool"]["legacy_receipts"].append(dict(DeliveryState="uncertain")),
        lambda s: s["pool"]["legacy_receipts"].append(dict(DeliveryState="claimed")),
        lambda s: s["pool"]["slots"][0].update(State="quarantined"),
        lambda s: s["pool"]["slots"][0].update(State="retired"),
        lambda s: s["pool"]["slots"][0].update(State="staging"),
        lambda s: s["pool"]["slots"][0].update(OwnerID=str(uuid4())),
        lambda s: s["pool"]["slots"][0].update(Epoch=3),
        lambda s: s["operation"].update(TargetEpoch=3.0),
    ],
)
def test_drain_refuses_incomplete_ownership_or_reconciliation_before_reads(damage):
    f = drain_fixture()
    damage(f.snapshot)
    args, observations = probe_arguments(f)
    with pytest.raises((SourceConflict, ValueError)):
        observe_rollover_drain(**args)
    assert not observations


@pytest.mark.parametrize("damage", ["trashed", "owner", "extra_editor", "public_writer"])
def test_drain_contradictory_file_identity_or_acl_never_triggers_repair(damage):
    from kvk.services.new_source_delivery_service import DestinationSetupRequired

    f = drain_fixture()
    file = f.api.files_data["fake-1"]
    if damage == "trashed":
        file["trashed"] = True
    elif damage == "owner":
        file["permissions"][0]["emailAddress"] = "other@example.invalid"
    else:
        file["permissions"].append(
            dict(type="anyone" if damage == "public_writer" else "user", role="writer")
        )
    args, observations = probe_arguments(f)
    with pytest.raises(DestinationSetupRequired):
        observe_rollover_drain(**args)
    assert all(not ProviderRequest.parse(m).mutation for m, _ in observations)


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "close",
        "operation",
        "pool",
        "catalogue",
        "unknown",
        "bytes",
        "origin",
        "origin_drift",
        "origin_snapshot",
    ],
)
def test_drain_seals_exact_pool_snapshot_and_retains_unowned_operation(monkeypatch, failure):
    from tests.test_export_reconciliation_service import stub_origin_journal

    f = drain_fixture()
    origins, origin_hash = stub_origin_journal(
        monkeypatch,
        failure,
        lambda: f.snapshot["operation"].update(Version=f.snapshot["operation"]["Version"] + 1),
    )
    pools = Mock(execution_evidence=True)
    pools.operation_snapshot.side_effect = lambda _: deepcopy(f.snapshot)
    args, observations = probe_arguments(f)
    original = deepcopy(f.snapshot)
    if failure == "unknown":
        record = next(iter(f.records.values()))
        request_id = next(record["dal"].request_ids(record["stream"]["StreamID"]))
        record["dal"].read_request(request_id)[1][-1]["State"] = "unknown"

    @contextmanager
    def probe(snapshot):
        assert origins.call_count == 1
        assert snapshot == original
        f.trace.append("open")
        try:
            yield SimpleNamespace(stream_id=args["stream_id"], execute=args["execute"])
        finally:
            f.trace.append("close")
            if failure == "close":
                raise ExecutionUncertain("Close acknowledgment lost")
            stream = f.retain(observations, args["stream_id"], "probe", 1, snapshot["pool"])
            if failure == "operation":
                f.snapshot["operation"]["Version"] += 1
            elif failure == "pool":
                f.snapshot["pool"]["pool"]["Version"] += 1
            elif failure == "catalogue":
                f.retain([], str(uuid4()), "probe", 1, snapshot["pool"])
            elif failure == "bytes":
                f.records[args["stream_id"]]["documents"][stream["ClosureReference"]] += b" "

    service = RolloverDrainProbe(
        pools=pools,
        streams=SimpleNamespace(pools=pools, closing_probe=probe),
        dal=f.dal,
        store=f.store,
        registration=f.registration,
        protected_file_ids=f.protected,
    )
    if failure:
        with pytest.raises((SourceConflict, ExecutionUncertain, AssertionError)):
            service.run(f.snapshot["operation"]["OperationID"])
    else:
        result = service.run(f.snapshot["operation"]["OperationID"])
        assert result.origin_hash == origin_hash and origins.call_count == 2
        assert result.drain.snapshot_hash == digest(original["pool"]).hex()
        assert result.drain.operation_snapshot_hash == digest(original).hex()
        assert json.loads(result.membership_json)["history"]["count"] == 7
    assert (
        f.trace.count("open")
        == f.trace.count("close")
        == (0 if failure in {"unknown", "origin"} else 1)
    )
    pools.ready.assert_not_called()
    pools.claim.assert_not_called()
    pools.complete.assert_not_called()
    pools.reconcile_complete.assert_not_called()
