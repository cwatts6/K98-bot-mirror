"""Offline pool capacity and provider-boundary failures; no live evidence."""

from contextlib import contextmanager
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from kvk.services.source_output_pool_service import SourceOutputPoolService, capacity


def test_database_guid_strings_are_canonical_but_file_ids_stay_byte_exact():
    from kvk.dal.source_output_pool_dal import _wire

    guid = str(uuid4()).upper()
    assert _wire(
        dict(PoolID=guid, OperationID=guid, ActiveOutputOperationID=guid, FileID="MiXeD_File-ID")
    ) == dict(
        PoolID=guid.lower(),
        OperationID=guid.lower(),
        ActiveOutputOperationID=guid.lower(),
        FileID="MiXeD_File-ID",
    )


def test_capacity_uses_complete_partition_manifest(monkeypatch):
    partition = Mock(return_value=[[{"name": "section"}], [{"name": "directory-and-section"}]])
    monkeypatch.setattr(
        "kvk.services.source_output_pool_service.GoogleSheetsTransport.partition_manifest",
        partition,
    )
    manifest = {"complete": "including directory"}
    result = capacity(manifest, quarantined_parts=3, protected_parts=1, slot_count=10)
    assert result.required_files == 11  # 1+2+2+max(2,3)+2+1
    partition.assert_called_once_with(manifest)
    with pytest.raises(SourceConflict, match="capacity"):
        capacity(manifest, quarantined_parts=3, protected_parts=1, slot_count=9)


@pytest.mark.parametrize("slots", [0, 1, 17, True, -1])
def test_capacity_registration_bounds(slots):
    with pytest.raises((SourceConflict, ValueError)):
        capacity({}, quarantined_parts=0, protected_parts=0, slot_count=slots)


def test_s7_p2_allowance_is_nine_files_for_two_quarantined_parts(monkeypatch):
    monkeypatch.setattr(
        "kvk.services.source_output_pool_service.GoogleSheetsTransport.partition_manifest",
        lambda _: [[], []],
    )
    assert capacity({}, quarantined_parts=2, protected_parts=0, slot_count=8).required_files == 9
    assert capacity({}, quarantined_parts=3, protected_parts=0, slot_count=9).required_files == 10
    assert capacity({}, quarantined_parts=0, protected_parts=2, slot_count=10).required_files == 11


def rollover():
    repository = Mock()
    repository.operation.return_value = {
        "State": "closing",
        "PlanJson": json.dumps({"snapshot": {"pool": {"IndexFileID": "file-a"}}}),
        "OldKVK": 16,
        "NewKVK": 17,
    }
    repository.drain_snapshot.return_value = {"old": "exact writer snapshot"}
    repository.claim.return_value = SimpleNamespace(account="account-a")
    verifier = Mock(
        return_value=dict(
            snapshot_hash=digest(repository.drain_snapshot.return_value).hex(),
            all_writers_terminated=True,
            remote_outcomes_reconciled=True,
            evidence_id="independent-proof",
        )
    )
    service = SourceOutputPoolService(
        repository, transport_factory=Mock(), termination_verifier=verifier, budget_factory=Mock()
    )
    return service, repository, verifier


@pytest.mark.parametrize(
    "field",
    ["snapshot_hash", "all_writers_terminated", "remote_outcomes_reconciled", "evidence_id"],
)
def test_rollover_cannot_claim_from_incomplete_termination(field):
    service, repository, verifier = rollover()
    del verifier.return_value[field]
    with pytest.raises(SourceConflict, match="termination"):
        service.advance("operation")
    repository.claim.assert_not_called()
    service.transport_factory.assert_not_called()


@pytest.mark.parametrize("state", ["uncertain", "running", "blocked"])
def test_rollover_never_blindly_resumes_owned_or_uncertain_work(state):
    service, repository, _ = rollover()
    repository.operation.return_value = {"State": state}
    with pytest.raises(SourceConflict, match="Reconcile"):
        service.advance("operation")
    repository.claim.assert_not_called()


@pytest.mark.parametrize("failure", ["private", "clear"])
def test_provider_failure_retains_claims_and_cannot_complete(failure):
    service, repository, _ = rollover()
    repository.files.return_value = ("file-a",)
    repository.phase.side_effect = lambda claim, *args: claim
    transport = service.transport_factory.return_value
    getattr(transport, "rollover_" + failure).side_effect = RuntimeError("lost acknowledgment")
    with pytest.raises(RuntimeError):
        service.advance("operation")
    repository.uncertain.assert_called_once_with(repository.claim.return_value)
    repository.complete.assert_not_called()


def test_rollover_records_phase_before_each_provider_mutation():
    service, repository, _ = rollover()
    repository.files.return_value = ("file-a",)
    trace = []
    repository.phase.side_effect = lambda claim, phase, *args: (trace.append(phase) or claim)
    transport = service.transport_factory.return_value
    transport.rollover_private.side_effect = lambda file: (
        trace.append("private IO") or {"file_id": file, "private": True}
    )
    transport.rollover_clear.side_effect = lambda file: (
        trace.append("clear IO") or {"file_id": file, "private": True, "empty": True}
    )
    transport.rollover_setup.side_effect = lambda *args: (
        trace.append("setup IO") or dict(file_id=args[0], private=True, setup=True)
    )
    service.advance("operation")
    assert trace == [
        "private_pending",
        "private IO",
        "private_verified",
        "clear_pending",
        "clear IO",
        "clear_verified",
        "setup_pending",
        "setup IO",
        "setup_verified",
    ]
    repository.complete.assert_called_once()


def test_complete_requires_every_file_and_keeps_append_only_history(monkeypatch):
    from kvk.dal import source_output_pool_dal as mod

    pool_id, operation_id, owner, old_choice, new_choice = (str(uuid4()) for _ in range(5))
    pool = dict(PoolID=pool_id, IndexFileID="index-id", Epoch=1, Version=5, Fence=3)
    slots = {
        name: dict(FileID=name, Version=1, Epoch=1, State="active", OwnerID=None)
        for name in ("slot-a", "slot-b")
    }
    progress = dict(
        files={name: dict(file_id=name, private=True, empty=True) for name in ("index-id", *slots)},
        proof={"evidence_id": "terminated"},
        setup=dict(private=True, setup=True, file_id="index-id", old_kvk=16, new_kvk=17),
    )
    op = dict(
        Phase="setup_verified",
        ProgressJson=json.dumps(progress),
        PlanJson=json.dumps(dict(snapshot=dict(slots=list(slots.values())))),
        PlanHash="a" * 64,
        AccountKey="account-a",
        SourceKey="snapshot_report_v1",
        OldKVK=16,
        OldChoiceID=old_choice,
        NewKVK=17,
        NewChoiceID=new_choice,
        OldEpoch=1,
        TargetEpoch=2,
        ConfirmedBy="1",
        Reason="new season",
    )

    class Cursor:
        def __init__(self):
            self.statements = []
            self.current = None

        def execute(self, sql, *args):
            assert sql.count("?") == len(args), (sql, len(args))
            self.statements.append((sql, args))
            if sql.startswith("SELECT ISNULL(MAX(SequenceNo)"):
                self.current = {"SequenceNo": 0}
            elif sql.startswith("SELECT * FROM KVK.SourceOutputSlot"):
                self.current = slots.get(args[-1])
            else:
                self.current = {"Version": 6}

    cursor = Cursor()
    repository = mod.SourceOutputPoolDAL(Mock(side_effect=AssertionError("No SQL connection")))

    @contextmanager
    def owned(claim):
        yield cursor, pool, op

    monkeypatch.setattr(repository, "_owned", owned)
    monkeypatch.setattr(mod, "one", lambda c: c.current)
    monkeypatch.setattr(mod, "_cas", lambda c, sql, *args: (c.execute(sql, *args) or c.current))
    monkeypatch.setattr(
        repository, "_operation", lambda c, key: {"State": "completed", "OperationID": key}
    )
    claim = mod.OutputClaim(operation_id, "account-a", owner, 3, 2, (("account:account-a", 2),), 5)
    result = repository.complete(claim)
    assert result["State"] == "completed"
    events = [
        args
        for sql, args in cursor.statements
        if sql.startswith("INSERT KVK.SourceOutputDisposition")
    ]
    assert len(events) == 6 and {args[4] for args in events} == {"index-id", "slot-a", "slot-b"}
    assert sum("'retire'" in sql for sql, _ in cursor.statements if sql.startswith("INSERT")) == 3
    assert sum("'clear'" in sql for sql, _ in cursor.statements if sql.startswith("INSERT")) == 3
    assert not any(
        sql.startswith(("DELETE", "UPDATE KVK.SourceOutputDisposition"))
        for sql, _ in cursor.statements
    )
    del progress["files"]["slot-b"]
    op["ProgressJson"] = json.dumps(progress)
    cursor.statements.clear()
    with pytest.raises(SourceConflict, match="Every exact registered file"):
        repository.complete(claim)
    assert cursor.statements == []


@pytest.mark.parametrize(
    "confirmed,state,expected",
    [
        (True, "staging", "active"),
        (True, "quarantined", "quarantined"),
        (False, "quarantined", "quarantined"),
    ],
)
def test_reconciled_slots_keep_quarantine_and_exact_owner_cas(
    monkeypatch, confirmed, state, expected
):
    from kvk.dal import source_output_pool_dal as mod

    claim = SimpleNamespace(owner_id=str(uuid4()), fence=7)
    slot = dict(
        PoolID="pool",
        FileID="file",
        AttemptID="attempt",
        Epoch=2,
        State=state,
        OwnerID=claim.owner_id,
        Fence=7,
        Version=9,
    )
    cursor = Mock()
    monkeypatch.setattr(mod, "rows", lambda _: [slot])
    writes = []
    monkeypatch.setattr(mod, "_cas", lambda c, sql, *args: writes.append((sql, args)))
    mod.settle_reconciled_parts(cursor, claim, "attempt", confirmed=confirmed)
    assert writes[0][1] == (expected, "pool", "file", "attempt", 2, state, claim.owner_id, 7, 9)
    assert not any(
        field + "=" in writes[0][0]
        for field in ("AssignmentID", "LastDispositionID", "QuarantineReason", "ReceiptJson")
    )
    writes.clear()
    slot["OwnerID"] = str(uuid4())
    with pytest.raises(SourceConflict, match="another assigned slot"):
        mod.settle_reconciled_parts(cursor, claim, "attempt", confirmed=confirmed)
    assert not writes


@pytest.mark.parametrize("file_id,columns", [("fake-index", 3), ("fake-1", 1)])
def test_real_rollover_adapter_removes_complete_old_representation_offline(file_id, columns):
    from dataclasses import replace

    from tests.test_kvk_source_delivery import google_delivery

    args, _, api = google_delivery()
    transport = args["transport"]
    transport.registration = replace(transport.registration, audience="public_viewer")
    transport._request_guard = lambda _: None
    api.files_data[file_id]["permissions"].append(
        dict(id="old-public", type="anyone", role="reader", allowFileDiscovery=False)
    )
    api.files_data[file_id].update(
        appProperties=dict(k98Export="old", unrelated="keep"), description="old pointer"
    )
    api.grids[file_id]["OldTab"] = dict(
        sheetId=11,
        title="OldTab",
        gridProperties=dict(rowCount=10, columnCount=20, frozenRowCount=3),
    )
    api.values[file_id, "OldTab"] = [["retained old values"]]
    api.named_ranges[file_id] = [dict(namedRangeId="old-range")]
    api.metadata[file_id] = [dict(metadataId=123)]
    evidence = transport.rollover_clear(file_id)
    assert evidence["empty"] is True and len(evidence["manifest_hash"]) == 64
    assert list(api.grids[file_id]) == ["Sheet1"]
    assert api.grids[file_id]["Sheet1"]["gridProperties"] == dict(rowCount=1, columnCount=columns)
    assert not api.named_ranges[file_id] and not api.metadata[file_id]
    assert (file_id, "OldTab") not in api.values
    assert api.files_data[file_id]["appProperties"] == dict(unrelated="keep")
    assert not any(p["type"] == "anyone" for p in api.files_data[file_id]["permissions"])
    if file_id == "fake-index":
        setup = transport.rollover_setup(file_id, 16, 17)
        assert setup["setup"] and api.values[file_id, "Sheet1"] == [[setup["marker"]]]
    assert not any(path == "/files" and method == "create" for path, method, _ in api.calls)


@pytest.mark.parametrize(
    "contamination", ["namedRanges", "developerMetadata", "dataSources", "cell_format"]
)
def test_clear_readback_contamination_cannot_be_accepted(contamination):
    from tests.test_kvk_source_delivery import google_delivery

    args, _, api = google_delivery()
    transport = args["transport"]
    transport._request_guard = lambda _: None
    execute = api.execute

    def contaminated(path, method, kwargs, retries):
        result = execute(path, method, kwargs, retries)
        if kwargs.get("includeGridData"):
            if contamination == "cell_format":
                result["sheets"][0]["data"] = [
                    dict(
                        rowData=[
                            dict(values=[dict(userEnteredFormat=dict(textFormat=dict(bold=True)))])
                        ]
                    )
                ]
            else:
                result[contamination] = [{"unexpected": "retained"}]
        return result

    api.execute = contaminated
    with pytest.raises(SourceConflict, match="empty manifest"):
        transport.rollover_clear("fake-1")
