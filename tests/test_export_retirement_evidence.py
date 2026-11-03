from contextlib import contextmanager
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import Claim, bounded_json
from services.export_provider_adapter import ProviderOutcomeUnknown
from services.export_retirement_evidence import (
    RetirementProbe,
    observe_closed_retirement,
    observe_retirement,
)
from services.export_runtime_composition import NewSourceJobStreams
from tests.test_export_reconciliation_service import (
    publication_observation_fixture,
    sealed_publication_fixture,
)


def retirement_observation_fixture(monkeypatch, *, public=False):
    args, api, observations, _receipt = publication_observation_fixture(monkeypatch, public=public)
    full = args["snapshot"]
    context = full["pool"]
    job, attempt, parts = full["job"], full["attempts"][0], full["parts"]
    job.update(State="running", ProvenanceJson="{}")
    attempt["Phase"] = "publication_pending"
    pool = context["pool"]
    pool.update(PoolID=str(uuid4()), PoolState="active", OwnerID=None, Version=5)
    old_job = dict(job, JobID=str(uuid4()), OwnerID=str(uuid4()), State="confirmed", Fence=3)
    old_attempt = dict(
        attempt,
        AttemptID=str(uuid4()),
        JobID=old_job["JobID"],
        OwnerID=old_job["OwnerID"],
        Fence=3,
        Phase="published",
    )
    old_parts = deepcopy(parts)
    for part in old_parts:
        part["AttemptID"] = old_attempt["AttemptID"]
        if part["Role"] == "generation":
            part["FileID"] = "fake-2"
    old_document = json.loads(attempt["ManifestJson"])
    current_key = old_document["generation"]["export_key"]
    old_key = "e" * 64
    assert current_key != old_key and len(parts) == 2
    old_document["generation"].update(export_key=old_key, retain=False)
    old_document["parts"][1]["file_id"] = "fake-2"
    old_attempt.update(
        ManifestJson=bounded_json(old_document), ManifestHash=digest(old_document).hex()
    )

    # Seed an earlier, distinct generation in the second registered workbook.
    # Its complete contents/directory are still checked by the real transport.
    api.files_data["fake-2"] = deepcopy(api.files_data["fake-1"])
    api.files_data["fake-2"]["id"] = "fake-2"
    api.files_data["fake-2"]["appProperties"].update(k98Generation=old_key, k98Retain="False")
    api.grids["fake-2"] = {
        title.replace(current_key[:24], old_key[:24]): dict(
            deepcopy(grid), title=title.replace(current_key[:24], old_key[:24])
        )
        for title, grid in api.grids["fake-1"].items()
    }
    for (file_id, title), values in list(api.values.items()):
        if file_id == "fake-1":
            old_title = title.replace(current_key[:24], old_key[:24])
            api.values["fake-2", old_title] = [
                [
                    (
                        cell.replace(current_key, old_key).replace("/fake-1/", "/fake-2/")
                        if isinstance(cell, str)
                        else cell
                    )
                    for cell in row
                ]
                for row in values
            ]
    directory_id = api.grids["fake-2"][old_key[:24] + "__DIRECTORY"]["sheetId"]
    old_receipt = dict(
        export_key=old_key,
        fence=3,
        attempt_id=old_attempt["AttemptID"],
        files=["fake-index", "fake-2"],
        audience=args["registration"].audience,
        remote_id=f"https://docs.google.com/spreadsheets/d/fake-2/edit#gid={directory_id}",
    )
    old_attempt["ReceiptJson"] = bounded_json(old_receipt)
    context.update(
        jobs=[old_job, job],
        attempts=[old_attempt, attempt],
        parts=old_parts + parts,
        legacy_receipts=[],
        registration_count=1,
    )
    for slot in context["slots"]:
        old = slot["FileID"] == "fake-2"
        slot.update(
            PoolID=pool["PoolID"],
            AttemptID=(old_attempt if old else attempt)["AttemptID"],
            PartNo=2,
            OwnerID=None if old else job["OwnerID"],
            Epoch=1,
            Fence=3 if old else 10,
            Version=2,
            AssignmentID=str(uuid4()),
        )
    full["resources"] = [
        dict(
            ResourceKey=key,
            Version=4,
            ActiveJobID=job["JobID"],
            OwnerID=job["OwnerID"],
            Fence=10,
            ActivePreparationID=None,
            ActiveOutputOperationID=None,
            BlockedReason=None,
        )
        for key in (
            "account:account-a",
            "destination:fake-1",
            "destination:fake-2",
            "destination:fake-index",
        )
    ]
    claim = Claim(
        job["JobID"],
        "account-a",
        job["OwnerID"],
        10,
        job["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in full["resources"]),
        job["IntentID"],
    )
    args.update(
        snapshot=context,
        current_attempt_id=attempt["AttemptID"],
        old_attempt_id=old_attempt["AttemptID"],
    )
    return args, api, observations, full, claim


@pytest.mark.parametrize("public", [False, True])
def test_retirement_observes_current_pointer_old_content_and_exact_receipts(monkeypatch, public):
    args, api, observations, _full, _claim = retirement_observation_fixture(
        monkeypatch, public=public
    )
    original = deepcopy(args["snapshot"])
    calls = len(api.calls)
    result = observe_retirement(**args)
    assert result.snapshot_hash == digest(original).hex()
    assert result.old_files == ("fake-2",)
    assert result.old_receipt_json == original["attempts"][0]["ReceiptJson"]
    assert result.current_receipt_json == original["attempts"][1]["ReceiptJson"]
    assert args["snapshot"] == original
    assert all(method in {"get", "batchGet"} for _path, method, _arguments in api.calls[calls:])
    assert {message["target"] for message, _response in observations} == {
        "fake-index",
        "fake-1",
        "fake-2",
    }
    assert not hasattr(result, "proof_id") and not hasattr(result, "writer_terminated")
    assert not hasattr(result, "no_live_references")


@pytest.mark.parametrize(
    "damage",
    [
        "retained",
        "unknown_retention",
        "unconfirmed",
        "old_phase",
        "current_phase",
        "current_state",
        "duplicate_job",
        "duplicate_attempt",
        "missing_current",
        "same_attempt",
        "same_generation",
        "part_hash",
        "part_order",
        "oversized_part",
        "slot_owner",
        "slot_quarantine",
        "slot_epoch",
        "slot_pool",
        "slot_fence",
        "slot_version",
        "slot_assignment",
        "old_owner",
        "old_account",
        "old_destinations",
        "closing",
        "pool_owner",
        "registration_bound",
    ],
)
def test_ineligible_or_mismatched_retirement_fails_before_provider(monkeypatch, damage):
    args, _api, observations, _full, _claim = retirement_observation_fixture(monkeypatch)
    snapshot = args["snapshot"]
    old, current = snapshot["attempts"]
    document = json.loads(old["ManifestJson"])
    if damage in {"retained", "unknown_retention"}:
        document["generation"]["retain"] = True if damage == "retained" else None
    elif damage == "unconfirmed":
        snapshot["jobs"][0]["State"] = "uncertain"
    elif damage == "old_phase":
        old["Phase"] = "uncertain"
    elif damage == "current_phase":
        current["Phase"] = "published"
    elif damage == "current_state":
        snapshot["jobs"][1]["State"] = "uncertain"
    elif damage == "duplicate_job":
        snapshot["jobs"].append(deepcopy(snapshot["jobs"][0]))
    elif damage == "duplicate_attempt":
        snapshot["attempts"].append(deepcopy(old))
    elif damage == "missing_current":
        snapshot["attempts"].pop()
    elif damage == "same_attempt":
        args["old_attempt_id"] = args["current_attempt_id"]
    elif damage == "same_generation":
        document["generation"]["export_key"] = json.loads(current["ManifestJson"])["generation"][
            "export_key"
        ]
        receipt = json.loads(old["ReceiptJson"])
        receipt["export_key"] = document["generation"]["export_key"]
        old["ReceiptJson"] = bounded_json(receipt)
    elif damage == "part_hash":
        snapshot["parts"][1]["ManifestHash"] = "1" * 64
    elif damage == "part_order":
        snapshot["parts"][0], snapshot["parts"][1] = snapshot["parts"][1], snapshot["parts"][0]
    elif damage == "oversized_part":
        document["parts"][1]["cells"] = snapshot["parts"][1]["CellCount"] = 9_000_001
    elif damage.startswith("slot_"):
        field, value = {
            "slot_owner": ("OwnerID", str(uuid4())),
            "slot_quarantine": ("State", "quarantined"),
            "slot_epoch": ("Epoch", 2),
            "slot_pool": ("PoolID", str(uuid4())),
            "slot_fence": ("Fence", 4),
            "slot_version": ("Version", 0),
            "slot_assignment": ("AssignmentID", "not-a-uuid"),
        }[damage]
        snapshot["slots"][1][field] = value
    elif damage == "old_owner":
        old["OwnerID"] = str(uuid4())
    elif damage == "old_account":
        snapshot["jobs"][0]["AccountKey"] = "another-account"
    elif damage == "old_destinations":
        snapshot["jobs"][0]["DestinationSetHash"] = "0" * 64
    elif damage == "closing":
        snapshot["pool"]["PoolState"] = "closing"
    elif damage == "pool_owner":
        snapshot["pool"]["OwnerID"] = str(uuid4())
    elif damage == "registration_bound":
        snapshot["registration_count"] = 9
    old.update(ManifestJson=bounded_json(document), ManifestHash=digest(document).hex())
    with pytest.raises((SourceConflict, ValueError)):
        observe_retirement(**args)
    assert not observations


@pytest.mark.parametrize(
    "damage",
    [
        "retention",
        "missing_retention",
        "binding",
        "content",
        "directory",
        "current_pointer",
        "receipt_bytes",
        "old_url",
    ],
)
def test_provider_or_receipt_mismatch_never_becomes_retirement_authority(monkeypatch, damage):
    args, api, _observations, _full, _claim = retirement_observation_fixture(monkeypatch)
    props = api.files_data["fake-2"]["appProperties"]
    title = "e" * 24 + "__DIRECTORY"
    if damage == "retention":
        props["k98Retain"] = "True"
    elif damage == "missing_retention":
        props.pop("k98Retain")
    elif damage == "binding":
        props["k98Destination"] = "another-destination"
    elif damage == "content":
        data_title = next(t for t in api.grids["fake-2"] if t != title)
        api.values["fake-2", data_title][0][0] = "changed"
    elif damage == "directory":
        api.values["fake-2", title][1][-1] = "https://example.invalid/other"
    elif damage == "current_pointer":
        api.values["fake-index", "Sheet1"][0][0] = "e" * 64
    elif damage == "receipt_bytes":
        args["snapshot"]["attempts"][0]["ReceiptJson"] += " "
    elif damage == "old_url":
        old = args["snapshot"]["attempts"][0]
        receipt = json.loads(old["ReceiptJson"])
        receipt["remote_id"] = "https://example.invalid/changed"
        old["ReceiptJson"] = bounded_json(receipt)
    with pytest.raises(SourceConflict):
        observe_retirement(**args)


def test_retirement_replays_complete_private_transcript_without_more_provider_calls(monkeypatch):
    args, api, observations, _full, _claim = retirement_observation_fixture(monkeypatch)
    observed = observe_retirement(**args)
    dal, store, _stream, _documents = sealed_publication_fixture(args, observations)
    calls = len(api.calls)
    result = observe_closed_retirement(
        dal=dal, store=store, **{k: v for k, v in args.items() if k != "execute"}
    )
    assert result == observed and len(api.calls) == calls


def test_unsettled_current_receipt_and_legacy_history_remain_unmodified(monkeypatch):
    args, _api, _observations, _full, _claim = retirement_observation_fixture(monkeypatch)
    context = args["snapshot"]
    context["attempts"][1]["ReceiptJson"] = None
    context["legacy_receipts"] = [dict(Receipt=' {"historical":"retain exact bytes"} ')]
    original = deepcopy(context)
    result = observe_retirement(**args)
    assert result.current_receipt_json and context == original
    # The presence or absence of legacy records cannot become external coverage.
    assert not hasattr(result, "no_live_references")
    assert result.snapshot_hash == digest(original).hex()


@pytest.mark.parametrize("damage", ["truncated", "extra", "wrong_snapshot"])
def test_retirement_replay_requires_all_and_only_exact_snapshot_observations(monkeypatch, damage):
    args, api, observations, _full, _claim = retirement_observation_fixture(monkeypatch)
    observe_retirement(**args)
    if damage == "truncated":
        observations.pop()
    elif damage == "extra":
        message, response = deepcopy(observations[-1])
        message["request_id"] = str(uuid4())
        observations.append((message, response))
    dal, store, stream, _documents = sealed_publication_fixture(args, observations)
    if damage == "wrong_snapshot":
        stream["SnapshotHash"] = b"x" * 32
    calls = len(api.calls)
    expected = ProviderOutcomeUnknown if damage == "truncated" else SourceConflict
    with pytest.raises(expected) as error:
        observe_closed_retirement(
            dal=dal, store=store, **{k: v for k, v in args.items() if k != "execute"}
        )
    if damage == "truncated":
        assert isinstance(error.value.__cause__, SourceConflict)
        assert "no further observed request" in str(error.value.__cause__)
    assert len(api.calls) == calls


@pytest.mark.parametrize("damage", ["pools", "coordinator", "operations", "streams"])
def test_retirement_probe_refuses_mixed_composition(damage):
    pools = Mock(execution_evidence=damage != "pools")
    coordinator = Mock(
        execution_evidence=damage != "coordinator", output_operations=damage != "operations"
    )
    streams = Mock(coordinator=Mock() if damage == "streams" else coordinator)
    with pytest.raises(SourceConflict, match="same complete"):
        RetirementProbe(
            pools=pools,
            coordinator=coordinator,
            streams=streams,
            dal=Mock(),
            store=Mock(),
            registration=Mock(),
            protected_file_ids=(),
        )


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "readback",
        "close",
        "context",
        "catalogue",
        "bytes",
        "replay_context",
        "origin",
        "origin_drift",
        "origin_snapshot",
    ],
)
def test_retirement_probe_uses_exact_pool_context_and_seals_before_return(monkeypatch, failure):
    from services.export_execution_authority import ExecutionUncertain
    from tests.test_export_reconciliation_service import stub_origin_journal

    args, api, observations, full, claim = retirement_observation_fixture(monkeypatch)
    snapshot = args["snapshot"]
    origins, origin_hash = stub_origin_journal(
        monkeypatch,
        failure,
        lambda: snapshot["pool"].update(Version=snapshot["pool"]["Version"] + 1),
    )
    pools, coordinator = Mock(execution_evidence=True), Mock(
        execution_evidence=True, output_operations=True
    )
    pools.retirement_snapshot.side_effect = lambda *_: deepcopy(snapshot)
    coordinator.operator_snapshot.side_effect = lambda *_: deepcopy(full)
    catalogue, sealed, trace = [], {}, []

    def private(reference, expected_hash):
        trace.append("private")
        if failure == "bytes":
            raise SourceConflict("Private bytes unavailable.")
        if failure == "replay_context":
            snapshot["pool"]["Version"] += 1
        return sealed["store"].read_reference(reference, expected_hash)

    dal = SimpleNamespace(
        read_catalogue=lambda *_: (r for r in catalogue),
        read_stream=lambda identifier: next(r for r in catalogue if r["StreamID"] == identifier),
        stream_digest=lambda identifier: sealed["dal"].stream_digest(identifier),
        request_ids=lambda identifier: sealed["dal"].request_ids(identifier),
        read_request=lambda identifier: sealed["dal"].read_request(identifier),
    )

    @contextmanager
    def stream(scope):
        assert origins.call_count == 1
        assert scope["SnapshotHash"] == digest(snapshot).hex() != digest(full).hex()
        assert scope["ObjectID"] == claim.job_id and scope["ClaimVersion"] == claim.version
        assert scope["OwnerID"] == claim.owner_id and scope["Purpose"] == "probe"
        trace.append("open")
        try:
            yield SimpleNamespace(stream_id=args["stream_id"], execute=args["execute"])
        finally:
            trace.append("close")
            if failure == "close":
                raise ExecutionUncertain("Closure reply lost.")
            sealed_dal, store, row, _documents = sealed_publication_fixture(args, observations)
            sealed.update(dal=sealed_dal, store=store)
            catalogue.append(row)
            if failure == "context":
                snapshot["pool"]["Version"] += 1
            elif failure == "catalogue":
                catalogue.append(dict(row, StreamID=str(uuid4()), State="open"))
                catalogue.sort(key=lambda r: r["StreamID"])

    service = RetirementProbe(
        pools=pools,
        coordinator=coordinator,
        streams=NewSourceJobStreams(coordinator=coordinator, client=SimpleNamespace(stream=stream)),
        dal=dal,
        store=SimpleNamespace(read_reference=private),
        registration=args["registration"],
        protected_file_ids=args["protected_file_ids"],
    )
    if failure == "readback":
        api.values["fake-index", "Sheet1"][0][1] = "changed"
    if failure:
        with pytest.raises((SourceConflict, ExecutionUncertain)):
            service.run(snapshot, claim, args["current_attempt_id"], args["old_attempt_id"])
    else:
        result = service.run(snapshot, claim, args["current_attempt_id"], args["old_attempt_id"])
        assert result.origin_hash == origin_hash and origins.call_count == 2
        assert result.retirement.snapshot_hash == digest(snapshot).hex()
        assert json.loads(result.membership_json)["probe"]["stream_id"] == args["stream_id"]
        assert trace.index("close") < trace.index("private")
        assert not hasattr(result, "proof_id")
    assert trace.count("open") == trace.count("close") == (0 if failure == "origin" else 1)
    pools.retire_generation.assert_not_called()
    pools.clear_retired_slot.assert_not_called()


@pytest.mark.parametrize("damage", ["context", "claim", "state", "phase", "attempt", "nested"])
def test_retirement_stream_cannot_adopt_a_changed_or_nested_owner(monkeypatch, damage):
    args, _api, _observations, full, claim = retirement_observation_fixture(monkeypatch)
    supplied = deepcopy(args["snapshot"])
    if damage == "context":
        supplied["pool"]["Version"] += 1
    elif damage == "claim":
        full["resources"][0]["Version"] += 1
    elif damage == "state":
        full["job"]["State"] = "uncertain"
    elif damage == "phase":
        full["attempts"][0]["Phase"] = "published"
    elif damage == "attempt":
        args["current_attempt_id"] = str(uuid4())
    elif damage == "nested":
        pool = supplied["pool"]
        full["job"]["ProvenanceJson"] = bounded_json(
            dict(
                retirement_recovery=dict(
                    state="owned",
                    version=claim.version,
                    pool_id=pool["PoolID"],
                    epoch=pool["Epoch"],
                    registration_hash=pool["RegistrationHash"],
                    token=str(uuid4()),
                    attempt_id=args["current_attempt_id"],
                )
            )
        )
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = full
    client = Mock()
    with pytest.raises(SourceConflict):
        NewSourceJobStreams(coordinator=coordinator, client=client).retirement_probe(
            supplied, claim, args["current_attempt_id"]
        )
    client.stream.assert_not_called()
