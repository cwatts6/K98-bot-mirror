from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import bounded_json
from services.export_execution_dal import ExportExecutionDAL
from services.export_execution_protocol import CATALOGUE_SEED, encode
from services.export_provider_adapter import ProviderOutcomeUnknown
from services.export_retirement_recovery_evidence import (
    RetirementJournalVerifier,
    RetirementRecoveryProbe,
    observe_closed_retirement_recovery,
    observe_retirement_recovery,
)
from services.export_runtime_composition import NewSourceJobStreams
from tests.test_export_reconciliation_service import (
    closed_stream_fixture,
    sealed_publication_fixture,
)
from tests.test_export_retirement_evidence import retirement_observation_fixture


def recovery_fixture(monkeypatch, *, nested=False, empty=False, count=1):
    args, api, observations, snapshot, _claim = retirement_observation_fixture(monkeypatch)
    args.pop("current_attempt_id")
    args.pop("old_attempt_id")
    args["snapshot"] = snapshot
    job, context = snapshot["job"], snapshot["pool"]
    pool = context["pool"]
    pool.update(SourceKey="snapshot_report_v1", ChoiceID=str(uuid4()))
    if count == 2:
        prior_job = dict(context["jobs"][0], JobID=str(uuid4()), OwnerID=str(uuid4()))
        prior_attempt = dict(
            context["attempts"][0],
            AttemptID=str(uuid4()),
            JobID=prior_job["JobID"],
            OwnerID=prior_job["OwnerID"],
        )
        manifest = json.loads(prior_attempt["ManifestJson"])
        manifest["generation"]["export_key"] = "f" * 64
        manifest["parts"][1]["file_id"] = "fake-3"
        prior_attempt.update(
            ManifestJson=bounded_json(manifest), ManifestHash=digest(manifest).hex()
        )
        receipt = json.loads(prior_attempt["ReceiptJson"])
        receipt.update(
            export_key="f" * 64,
            attempt_id=prior_attempt["AttemptID"],
            files=["fake-index", "fake-3"],
            remote_id=receipt["remote_id"].replace("/fake-2/", "/fake-3/"),
        )
        prior_attempt["ReceiptJson"] = bounded_json(receipt)
        prior_parts = [
            dict(
                p,
                AttemptID=prior_attempt["AttemptID"],
                FileID="fake-index" if p["Role"] == "index" else "fake-3",
            )
            for p in context["parts"]
            if p["AttemptID"] == context["attempts"][0]["AttemptID"]
        ]
        context["jobs"].append(prior_job)
        context["attempts"].append(prior_attempt)
        context["parts"].extend(prior_parts)
        context["slots"].append(
            dict(
                deepcopy(context["slots"][1]),
                FileID="fake-3",
                AssignmentID=str(uuid4()),
                AttemptID=prior_attempt["AttemptID"],
            )
        )
        api.files_data["fake-3"] = dict(deepcopy(api.files_data["fake-2"]), id="fake-3")
        api.files_data["fake-3"]["appProperties"]["k98Generation"] = "f" * 64
        api.grids["fake-3"] = {
            title.replace("e" * 24, "f" * 24): dict(
                deepcopy(grid), title=title.replace("e" * 24, "f" * 24)
            )
            for title, grid in api.grids["fake-2"].items()
        }
        for (file, title), values in list(api.values.items()):
            if file == "fake-2":
                api.values["fake-3", title.replace("e" * 24, "f" * 24)] = [
                    [
                        (
                            cell.replace("e" * 64, "f" * 64).replace("/fake-2/", "/fake-3/")
                            if isinstance(cell, str)
                            else cell
                        )
                        for cell in row
                    ]
                    for row in values
                ]
        args["registration"] = replace(
            args["registration"], slot_file_ids=("fake-1", "fake-2", "fake-3")
        )
        snapshot["resources"].insert(
            3, dict(snapshot["resources"][1], ResourceKey="destination:fake-3")
        )
        for row in context["jobs"]:
            row["DestinationSetHash"] = digest(
                tuple(ExportExecutionDAL.proof_targets(snapshot))
            ).hex()
    proofs, events = {}, []
    for n, slot in enumerate(context["slots"][1:], 1):
        previous = deepcopy(slot)
        proof_id = str(uuid4())
        proof_body = dict(
            state="confirmed",
            snapshot_hash=digest(context).hex(),
            current_attempt_id=snapshot["attempts"][0]["AttemptID"],
            old_attempt_id=slot["AttemptID"],
            writer_terminated=True,
            current_pointer_verified=True,
            no_live_references=True,
            evidence_id=str(uuid4()),
        )
        membership = dict(
            version=2,
            targets=ExportExecutionDAL.proof_targets(snapshot),
            history=dict(count=0, sha256=CATALOGUE_SEED.hex()),
            probe=dict(stream_id=str(uuid4()), version=3),
        )
        raw = encode(membership).decode()
        proofs[proof_id] = dict(
            ProofID=proof_id,
            SessionID=str(uuid4()),
            AccountKey=job["AccountKey"],
            SnapshotHash=bytes.fromhex(proof_body["snapshot_hash"]),
            RegistrationHash=bytes.fromhex(pool["RegistrationHash"]),
            ProofKind="retirement",
            Outcome="confirmed",
            EvidenceJson=bounded_json(proof_body),
            MembershipJson=raw,
            MembershipHash=hashlib.sha256(raw.encode("utf-16-le")).digest(),
        )
        evidence = dict(
            previous_assignment=previous,
            current_attempt_id=proof_body["current_attempt_id"],
            proof=dict(proof_body, proof_id=proof_id),
        )
        disposition = str(uuid4())
        slot.update(
            State="retired",
            Version=slot["Version"] + 1,
            LastAction="retire",
            LastDispositionID=disposition,
        )
        events.append(
            dict(
                DispositionID=disposition,
                OperationID=str(uuid4()),
                PoolID=pool["PoolID"],
                SequenceNo=n,
                FileID=slot["FileID"],
                FileKind="slot",
                SlotFileID=slot["FileID"],
                IndexFileID=None,
                ResourceKey="destination:" + slot["FileID"],
                AccountKey=job["AccountKey"],
                SourceKey=pool["SourceKey"],
                KVK_NO=pool["ActiveKVK"],
                ChoiceID=pool["ChoiceID"],
                NewKVK_NO=pool["ActiveKVK"],
                NewChoiceID=pool["ChoiceID"],
                OldEpoch=pool["Epoch"],
                NewEpoch=pool["Epoch"],
                Action="retire",
                OwnerID=job["OwnerID"],
                Fence=job["Fence"],
                FromPoolVersion=pool["Version"],
                ToPoolVersion=pool["Version"] + 1,
                FromSlotVersion=previous["Version"],
                ToSlotVersion=slot["Version"],
                EvidenceJson=bounded_json(evidence),
                EvidenceHash=digest(evidence).hex(),
            )
        )
        pool["Version"] += 1
        if empty:
            api.files_data[slot["FileID"]].update(appProperties={}, description="")
            api.grids[slot["FileID"]] = {
                "Sheet1": dict(
                    title="Sheet1", sheetId=991 + n, gridProperties=dict(rowCount=1, columnCount=1)
                )
            }
    snapshot["retirement_events"] = events
    job.update(State="uncertain", Version=job["Version"] + 1)
    for r in snapshot["resources"]:
        r["BlockedReason"] = "interrupted retirement"
    if nested:
        job["ProvenanceJson"] = bounded_json(
            dict(
                retirement_recovery=dict(
                    token=str(uuid4()),
                    state="owned",
                    version=job["Version"] - 1,
                    attempt_id=snapshot["attempts"][0]["AttemptID"],
                    pool_id=pool["PoolID"],
                    epoch=pool["Epoch"],
                    registration_hash=pool["RegistrationHash"],
                )
            )
        )
    return args, api, observations, proofs


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("count", [1, 2])
def test_recovery_observes_every_pending_slot_without_retry_or_authority(
    monkeypatch, nested, empty, count
):
    args, api, observations, proofs = recovery_fixture(
        monkeypatch, nested=nested, empty=empty, count=count
    )
    original = deepcopy(args["snapshot"])
    calls = len(api.calls)
    verifier = RetirementJournalVerifier(
        dal=SimpleNamespace(read_proof=lambda p: deepcopy(proofs.get(p)))
    )
    assert len(verifier.verify(args["snapshot"])) == 64
    result = observe_retirement_recovery(**args)
    assert len(result.slots) == count and result.snapshot_hash == digest(original).hex()
    assert result.receipt_json == original["attempts"][0]["ReceiptJson"]
    assert bool(result.nested_token) == nested
    assert all(bool(s.empty_json) == empty for s in result.slots)
    assert {s.file_id for s in result.slots} == {"fake-2", *(["fake-3"] if count == 2 else [])}
    assert args["snapshot"] == original and observations
    assert all(method in {"get", "batchGet"} for _path, method, _args in api.calls[calls:])
    assert not hasattr(result, "no_delayed_retirement_effects") and not hasattr(result, "proof_id")
    if empty:
        assert all(json.loads(s.empty_json)["private"] is True for s in result.slots)


@pytest.mark.parametrize(
    "damage",
    [
        "missing_event",
        "extra_event",
        "duplicate_event",
        "bad_hash",
        "current_attempt",
        "previous_assignment",
        "owner",
        "fence",
        "slot_version",
        "pool_version",
        "event_account",
        "event_source",
        "event_choice",
        "event_resource",
        "event_file_kind",
        "event_order",
        "released_resource",
        "another_resource_owner",
        "current_file_retired",
        "completed_job",
        "nested_version",
        "nested_complete",
        "nested_pool",
    ],
)
def test_recovery_rejects_incomplete_or_stale_journal_before_provider(monkeypatch, damage):
    args, _api, observations, _proofs = recovery_fixture(
        monkeypatch, nested=damage.startswith("nested_"), count=2
    )
    snapshot = args["snapshot"]
    event = snapshot["retirement_events"][0]
    if damage == "missing_event":
        snapshot["retirement_events"].pop()
    elif damage == "extra_event":
        snapshot["retirement_events"].append(dict(event, DispositionID=str(uuid4())))
    elif damage == "duplicate_event":
        snapshot["retirement_events"][1] = deepcopy(event)
    elif damage == "bad_hash":
        event["EvidenceHash"] = "0" * 64
    elif damage in {"current_attempt", "previous_assignment"}:
        evidence = json.loads(event["EvidenceJson"])
        if damage == "current_attempt":
            evidence["current_attempt_id"] = str(uuid4())
        else:
            evidence["previous_assignment"]["AssignmentID"] = str(uuid4())
        event.update(EvidenceJson=bounded_json(evidence), EvidenceHash=digest(evidence).hex())
    elif damage in {
        "owner",
        "fence",
        "pool_version",
        "event_account",
        "event_source",
        "event_choice",
        "event_resource",
        "event_file_kind",
        "event_order",
    }:
        key, value = {
            "owner": ("OwnerID", str(uuid4())),
            "fence": ("Fence", 99),
            "pool_version": ("ToPoolVersion", 999),
            "event_account": ("AccountKey", "other"),
            "event_source": ("SourceKey", "other"),
            "event_choice": ("ChoiceID", str(uuid4())),
            "event_resource": ("ResourceKey", "destination:other-file"),
            "event_file_kind": ("FileKind", "index"),
            "event_order": ("SequenceNo", 3),
        }[damage]
        event[key] = value
    elif damage == "slot_version":
        snapshot["pool"]["slots"][1]["Version"] += 1
    elif damage == "released_resource":
        snapshot["resources"][0].update(ActiveJobID=None, OwnerID=None)
    elif damage == "another_resource_owner":
        snapshot["resources"][0]["OwnerID"] = str(uuid4())
    elif damage == "current_file_retired":
        snapshot["parts"][1]["FileID"] = "fake-2"
    elif damage == "completed_job":
        snapshot["job"]["State"] = "confirmed"
    elif damage.startswith("nested_"):
        provenance = json.loads(snapshot["job"]["ProvenanceJson"])
        recovery = provenance["retirement_recovery"]
        if damage == "nested_version":
            recovery["version"] -= 1
        elif damage == "nested_complete":
            recovery["state"] = "complete"
        else:
            recovery["pool_id"] = str(uuid4())
        snapshot["job"]["ProvenanceJson"] = bounded_json(provenance)
    with pytest.raises(SourceConflict):
        observe_retirement_recovery(**args)
    assert not observations


@pytest.mark.parametrize(
    "damage",
    [
        "missing_reference",
        "missing_row",
        "wrong_id",
        "account",
        "kind",
        "outcome",
        "registration",
        "snapshot",
        "body",
        "membership_hash",
        "targets",
        "session",
        "body_proof_id",
    ],
)
def test_original_retirement_flags_and_hashes_cannot_replace_trusted_proof(monkeypatch, damage):
    args, _api, observations, proofs = recovery_fixture(monkeypatch)
    identifier, row = next(iter(proofs.items()))
    if damage == "missing_reference":
        event = args["snapshot"]["retirement_events"][0]
        body = json.loads(event["EvidenceJson"])
        body["proof"].pop("proof_id")
        event.update(EvidenceJson=bounded_json(body), EvidenceHash=digest(body).hex())
    elif damage == "missing_row":
        proofs.clear()
    elif damage in {
        "wrong_id",
        "account",
        "kind",
        "outcome",
        "registration",
        "snapshot",
        "membership_hash",
        "session",
    }:
        key, value = {
            "wrong_id": ("ProofID", str(uuid4())),
            "account": ("AccountKey", "another"),
            "kind": ("ProofKind", "publication"),
            "outcome": ("Outcome", "absent"),
            "registration": ("RegistrationHash", b"r" * 32),
            "snapshot": ("SnapshotHash", b"s" * 32),
            "membership_hash": ("MembershipHash", b"m" * 32),
            "session": ("SessionID", "bad"),
        }[damage]
        row[key] = value
    elif damage in {"body", "body_proof_id"}:
        body = json.loads(row["EvidenceJson"])
        body["proof_id" if damage == "body_proof_id" else "evidence_id"] = identifier
        row["EvidenceJson"] = bounded_json(body)
    elif damage == "targets":
        membership = json.loads(row["MembershipJson"])
        membership["targets"] = ["other-file"]
        row["MembershipJson"] = bounded_json(membership)
        row["MembershipHash"] = hashlib.sha256(row["MembershipJson"].encode("utf-16-le")).digest()
    with pytest.raises((SourceConflict, ValueError)):
        RetirementJournalVerifier(dal=SimpleNamespace(read_proof=lambda p: proofs.get(p))).verify(
            args["snapshot"]
        )
    assert not observations


@pytest.mark.parametrize("replacement", [1, 1.0])
def test_retirement_proof_association_preserves_json_types(monkeypatch, replacement):
    args, _api, observations, proofs = recovery_fixture(monkeypatch)
    row = next(iter(proofs.values()))
    body = json.loads(row["EvidenceJson"])
    body["writer_terminated"] = replacement
    row["EvidenceJson"] = bounded_json(body)
    dal = SimpleNamespace(read_proof=lambda identifier: deepcopy(proofs[identifier]))
    with pytest.raises(SourceConflict, match="immutable SQL proof"):
        RetirementJournalVerifier(dal=dal).verify(args["snapshot"])
    assert not observations


@pytest.mark.parametrize("empty", [False, True])
def test_recovery_replays_full_private_observation_without_provider(monkeypatch, empty):
    args, api, observations, _proofs = recovery_fixture(
        monkeypatch, nested=True, empty=empty, count=2
    )
    original = observe_retirement_recovery(**args)
    dal, store, _stream, _documents = sealed_publication_fixture(args, observations)
    calls = len(api.calls)
    result = observe_closed_retirement_recovery(
        dal=dal, store=store, **{k: v for k, v in args.items() if k != "execute"}
    )
    assert original == result and len(api.calls) == calls


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "old_proof",
        "readback",
        "close",
        "snapshot",
        "catalogue",
        "bytes",
        "proof_drift",
        "origin",
        "origin_drift",
        "origin_snapshot",
    ],
)
def test_recovery_probe_checks_historical_proofs_and_closes_before_sealed_evaluation(
    monkeypatch, failure
):
    from services.export_execution_authority import ExecutionUncertain
    from tests.test_export_reconciliation_service import stub_origin_journal

    args, api, observations, proofs = recovery_fixture(monkeypatch, nested=True, empty=True)
    snapshot = args["snapshot"]
    origins, origin_hash = stub_origin_journal(
        monkeypatch,
        failure,
        lambda: snapshot["job"].update(Version=snapshot["job"]["Version"] + 1),
    )
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.side_effect = lambda _: deepcopy(snapshot)
    rows, sealed, trace = [], {}, []

    def private(reference, expected_hash):
        trace.append("private")
        if failure == "bytes":
            raise SourceConflict("Private bytes are unavailable.")
        return sealed["store"].read_reference(reference, expected_hash)

    dal = SimpleNamespace(
        read_proof=lambda p: deepcopy(proofs.get(p)),
        read_catalogue=lambda *_: (r for r in rows),
        read_stream=lambda identifier: next(r for r in rows if r["StreamID"] == identifier),
        stream_digest=lambda identifier: sealed["dal"].stream_digest(identifier),
        request_ids=lambda identifier: sealed["dal"].request_ids(identifier),
        read_request=lambda identifier: sealed["dal"].read_request(identifier),
    )

    @contextmanager
    def stream(scope):
        assert origins.call_count == 1
        trace.append("open")
        assert scope["SnapshotHash"] == digest(snapshot).hex()
        assert (
            scope["NestedToken"]
            == json.loads(snapshot["job"]["ProvenanceJson"])["retirement_recovery"]["token"]
        )
        assert scope["Purpose"] == "probe" and scope["ClaimVersion"] == snapshot["job"]["Version"]
        try:
            yield SimpleNamespace(stream_id=args["stream_id"], execute=args["execute"])
        finally:
            trace.append("close")
            if failure == "close":
                raise ExecutionUncertain("Closure reply lost.")
            sealed_dal, store, row, _docs = sealed_publication_fixture(args, observations)
            sealed.update(dal=sealed_dal, store=store)
            rows.append(row)
            if failure == "snapshot":
                snapshot["job"]["Version"] += 1
            elif failure == "catalogue":
                rows.append(dict(row, StreamID=str(uuid4()), State="open"))
                rows.sort(key=lambda r: r["StreamID"])
            elif failure == "proof_drift":
                next(iter(proofs.values()))["EvidenceJson"] += " "

    service = RetirementRecoveryProbe(
        coordinator=coordinator,
        streams=NewSourceJobStreams(coordinator=coordinator, client=SimpleNamespace(stream=stream)),
        dal=dal,
        store=SimpleNamespace(read_reference=private),
        registration=args["registration"],
        protected_file_ids=args["protected_file_ids"],
    )
    if failure == "old_proof":
        proofs.clear()
    elif failure == "readback":
        api.values["fake-index", "Sheet1"][0][1] = "wrong-fence"
    if failure:
        with pytest.raises((SourceConflict, ProviderOutcomeUnknown, ExecutionUncertain)):
            service.run(snapshot["job"]["JobID"])
    else:
        result = service.run(snapshot["job"]["JobID"])
        assert result.origin_hash == origin_hash and origins.call_count == 2
        assert result.recovery.slots[0].empty_json
        assert result.retirement_proofs_hash == RetirementJournalVerifier(dal=dal).verify(snapshot)
        assert trace.index("close") < trace.index("private")
        assert not hasattr(result, "proof_id") and not hasattr(
            result, "no_delayed_retirement_effects"
        )
    assert (
        trace.count("open")
        == trace.count("close")
        == (0 if failure in {"old_proof", "origin"} else 1)
    )
    coordinator.reconcile_operator.assert_not_called()


@pytest.mark.parametrize("failure", [False, True])
def test_historical_proof_reader_is_parameterized_and_closes_before_evaluation(failure):
    identifier = str(uuid4())
    cursor = Mock(description=[("ProofID",)], fetchone=Mock(return_value=(identifier,)))
    connection = Mock(cursor=Mock(return_value=cursor))
    if failure:
        cursor.execute.side_effect = RuntimeError("read failed")
    dal = ExportExecutionDAL(Mock(return_value=connection))
    if failure:
        with pytest.raises(RuntimeError, match="read failed"):
            dal.read_proof(identifier)
    else:
        assert dal.read_proof(identifier) == dict(ProofID=identifier)
    cursor.execute.assert_called_once_with(
        "SELECT * FROM dbo.ExportReconciliationProof WHERE ProofID=?", identifier
    )
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
    connection.commit.assert_not_called()


def test_invalid_historical_proof_id_cannot_open_sql():
    connect = Mock(side_effect=AssertionError("No SQL expected"))
    with pytest.raises(ValueError):
        ExportExecutionDAL(connect).read_proof("';EXEC bad--")
    connect.assert_not_called()


@pytest.mark.parametrize(
    "failure", ["unknown_request", "live_child", "unfinished_stream", "missing_private_bytes"]
)
def test_empty_current_readback_never_overrides_unresolved_former_nested_writer(
    monkeypatch, failure
):
    from services.export_execution_protocol import decode
    from tests.test_export_reconciliation_service import stub_origin_journal

    args, api, observations, proofs = recovery_fixture(monkeypatch, nested=True, empty=True)
    stub_origin_journal(monkeypatch)
    snapshot = args["snapshot"]
    verifier, old, request, events, documents = closed_stream_fixture()

    def replace_private(reference, value):
        documents[reference] = encode(value)
        return hashlib.sha256(documents[reference]).digest()

    payload = decode(documents[request["PayloadReference"]])
    payload["target"] = request["TargetID"] = "fake-2"
    request["PayloadHash"] = replace_private(request["PayloadReference"], payload)
    prepared = decode(documents[events[0]["EvidenceReference"]])
    prepared["payload_hash"] = request["PayloadHash"].hex()
    events[0]["EvidenceHash"] = replace_private(events[0]["EvidenceReference"], prepared)
    response = decode(documents[events[-1]["EvidenceReference"]])
    response["response"]["spreadsheetId"] = "fake-2"
    events[-1]["EvidenceHash"] = replace_private(events[-1]["EvidenceReference"], response)
    old.update(
        JobID=snapshot["job"]["JobID"],
        NestedToken=str(uuid4()),
        ScopeJson=bounded_json(dict(resources=[dict(key="destination:fake-2", version=1)])),
    )
    if failure == "unknown_request":
        events[-1]["State"] = "unknown"
    elif failure == "live_child":
        closure = decode(documents[old["ClosureReference"]])
        closure["closure"]["job_empty"] = False
        old["ClosureHash"] = replace_private(old["ClosureReference"], closure)
    elif failure == "unfinished_stream":
        old["State"] = "frozen"
    else:
        documents[old["ClosureReference"]] += b" "
    dal = verifier.dal
    dal.read_proof = lambda p: deepcopy(proofs[p])
    dal.read_catalogue = lambda *_: (row for row in [old])
    coordinator = Mock(execution_evidence=True, output_operations=True)
    coordinator.operator_snapshot.return_value = snapshot
    streams = Mock(coordinator=coordinator)
    service = RetirementRecoveryProbe(
        coordinator=coordinator,
        streams=streams,
        dal=dal,
        store=verifier.store,
        registration=args["registration"],
        protected_file_ids=args["protected_file_ids"],
    )
    calls = len(api.calls)
    rejection = {
        "unknown_request": "Unknown request outcome",
        "live_child": "Private closure evidence",
        "unfinished_stream": "Exact registered closed stream",
        "missing_private_bytes": "private hash mismatch",
    }[failure]
    with pytest.raises(SourceConflict, match=rejection):
        service.run(snapshot["job"]["JobID"])
    assert len(api.calls) == calls and not observations
    streams.probe.assert_not_called()
    coordinator.reconcile_operator.assert_not_called()
