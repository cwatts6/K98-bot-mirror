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


def retirement_snapshot_fixture(*, retain=False):
    from kvk.dal.new_source_import_dal import canonical

    document = dict(generation=dict(export_key="old-key", retain=retain), parts=[])
    return dict(
        pool=dict(
            PoolID="pool",
            Epoch=1,
            Version=4,
            Fence=0,
            AccountKey="acct",
            SourceKey="snapshot_report_v1",
            ActiveKVK=16,
            ChoiceID="choice",
        ),
        jobs=[dict(JobID="old-job", State="confirmed")],
        attempts=[
            dict(
                AttemptID="old-attempt",
                JobID="old-job",
                Phase="published",
                Fence=2,
                PartCount=3,
                ManifestJson=canonical(document),
                ReceiptJson=canonical(
                    dict(
                        attempt_id="old-attempt",
                        export_key="old-key",
                        fence=2,
                        files=["index", "a", "b"],
                    )
                ),
            )
        ],
        parts=[
            dict(
                AttemptID="old-attempt",
                FileID=file,
                PartNo=i + 1,
                Role="index" if i == 0 else "generation",
            )
            for i, file in enumerate(["index", "a", "b"])
        ],
        slots=[
            dict(
                FileID=file,
                AttemptID="old-attempt",
                PartNo=i + 2,
                State="active",
                OwnerID=None,
                Fence=2,
                Version=3,
                AssignmentID="assignment",
                Epoch=1,
            )
            for i, file in enumerate(["a", "b"])
        ],
    )


@pytest.mark.parametrize(
    "case",
    [
        "final",
        "unknown",
        "current",
        "uncertain",
        "quarantined",
        "owned",
        "retired",
        "receipt",
        "mapping",
    ],
)
def test_retirement_never_releases_protected_or_uncertain_assignments(case):
    from kvk.dal.source_output_pool_dal import reusable_attempts

    s = retirement_snapshot_fixture(
        retain=True if case == "final" else None if case == "unknown" else False
    )
    if case == "uncertain":
        s["jobs"][0]["State"] = "uncertain"
    if case in {"quarantined", "retired"}:
        s["slots"][0]["State"] = case
    if case == "owned":
        s["slots"][0]["OwnerID"] = "old-writer"
    if case == "receipt":
        s["attempts"][0]["ReceiptJson"] = "{}"
    if case == "mapping":
        s["slots"][0]["PartNo"] = 99
    assert reusable_attempts(s, "old-attempt" if case == "current" else "new-attempt") == []


@pytest.mark.parametrize(
    "missing",
    [
        "snapshot_hash",
        "writer_terminated",
        "current_pointer_verified",
        "no_live_references",
        "evidence_id",
        "current_attempt_id",
        "old_attempt_id",
    ],
)
def test_retirement_requires_independent_exact_proof_before_sql(missing):
    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL

    s = retirement_snapshot_fixture()
    proof = dict(
        snapshot_hash=digest(s).hex(),
        writer_terminated=True,
        current_pointer_verified=True,
        no_live_references=True,
        evidence_id="proof",
        current_attempt_id="new",
        old_attempt_id="old-attempt",
    )
    del proof[missing]
    connect = Mock(side_effect=AssertionError("No SQL without proof"))
    with pytest.raises(SourceConflict, match="evidence"):
        SourceOutputPoolDAL(connect).retire_generation(
            Mock(), Mock(), "new", s, "old-attempt", proof
        )
    connect.assert_not_called()


def test_retirement_appends_intent_then_clear_with_exact_cas_and_retained_receipts(monkeypatch):
    from copy import deepcopy

    from kvk.dal import source_output_pool_dal as mod

    s = retirement_snapshot_fixture()
    claim = SimpleNamespace(owner_id=str(uuid4()), fence=5)
    job = dict(Actor="operator")
    proof = dict(
        snapshot_hash=digest(s).hex(),
        writer_terminated=True,
        current_pointer_verified=True,
        no_live_references=True,
        evidence_id="independent",
        current_attempt_id="new",
        old_attempt_id="old-attempt",
    )
    repository = mod.SourceOutputPoolDAL(Mock())
    cursor = Mock()
    snapshot = deepcopy(s)

    @contextmanager
    def owned(*args):
        yield cursor, job, snapshot

    monkeypatch.setattr(repository, "_retirement_owned", owned)
    writes = []

    def cas(c, sql, *args):
        assert sql.count("?") == len(args)
        writes.append((sql, args))
        return dict(Version=5)

    monkeypatch.setattr(mod, "_cas", cas)
    monkeypatch.setattr(mod, "one", lambda c: dict(SequenceNo=1))
    token = repository.retire_generation(Mock(), claim, "new", s, "old-attempt", proof)
    assert len(token["slots"]) == 2
    assert sum("State='retired'" in sql for sql, _ in writes) == 2
    assert not any("State='free'" in sql for sql, _ in writes)
    assert all(
        "AssignmentID=? AND AttemptID=? AND PartNo=?" in sql
        for sql, _ in writes
        if "SourceOutputSlot SET" in sql
    )
    member = token["slots"][0]
    slot = snapshot["slots"][0]
    slot.update(State="retired", Version=member["version"], LastDispositionID=member["event"])
    monkeypatch.setattr(
        mod,
        "one",
        lambda c: dict(
            SequenceNo=3,
            EvidenceHash=bytes.fromhex(member["evidence_hash"]),
            OwnerID=claim.owner_id,
            Fence=5,
        ),
    )
    with pytest.raises(SourceConflict, match="readback"):
        repository.clear_retired_slot(
            Mock(),
            claim,
            token,
            member,
            dict(file_id="wrong", private=True, empty=True, manifest_hash="hash"),
        )
    repository.clear_retired_slot(
        Mock(),
        claim,
        token,
        member,
        dict(file_id="a", private=True, empty=True, manifest_hash="hash"),
    )
    assert "State='free'" in writes[-1][0]
    assert (
        "Epoch=? AND State='retired' AND OwnerID IS NULL AND Fence=? AND Version=? AND LastDispositionID=?"
        in writes[-1][0]
    )
    inserts = [c.args for c in cursor.execute.call_args_list if c.args[0].startswith("INSERT")]
    assert len(inserts) == 3 and all(q.count("?") == len(a) for q, *a in inserts)
    assert not any("UPDATE dbo.ExportAttempt" in sql or "DELETE" in sql for sql, _ in writes)
    assert snapshot["attempts"] == s["attempts"]


@pytest.mark.parametrize("failure", ["private", "clear", "commit"])
def test_retirement_provider_or_commit_uncertainty_never_frees_slot(failure):
    from kvk.services.source_output_pool_service import retire_superseded_generations

    s = retirement_snapshot_fixture()
    pools, transport = Mock(), Mock()
    pools.retirement_snapshot.return_value = s
    pools.retire_generation.return_value = dict(slots=[dict(file_id="a")])
    if failure == "commit":
        pools.clear_retired_slot.side_effect = SourceConflict("unknown commit")
    else:
        getattr(transport, "rollover_" + failure).side_effect = SourceConflict(
            "unknown provider outcome"
        )
    with pytest.raises(SourceConflict):
        retire_superseded_generations(
            pools=pools,
            coordinator=Mock(),
            claim=Mock(),
            current_attempt_id="new",
            transport=transport,
            verifier=Mock(),
        )
    assert pools.retire_generation.call_count == 1
    assert pools.clear_retired_slot.call_count == (failure == "commit")


def test_repeated_two_part_nonfinal_generations_do_not_exhaust_sixteen_slots(monkeypatch):
    from copy import deepcopy

    from kvk.services.source_output_pool_service import (
        capacity_for_snapshot,
        retire_superseded_generations,
    )

    monkeypatch.setattr(
        "kvk.services.source_output_pool_service.GoogleSheetsTransport.partition_manifest",
        lambda _: [[], []],
    )
    s = retirement_snapshot_fixture()
    pools, transport = Mock(), Mock()
    pools.retirement_snapshot.side_effect = lambda *a: deepcopy(s)
    trace = []

    def retire(*args):
        assert args[4] == "old-attempt"
        trace.append("retire")
        for slot in s["slots"]:
            slot["State"] = "retired"
        return dict(slots=[dict(file_id=slot["FileID"]) for slot in s["slots"]])

    pools.retire_generation.side_effect = retire
    transport.rollover_private.side_effect = lambda file: trace.append("private " + file)
    transport.rollover_clear.side_effect = lambda file: trace.append("clear " + file) or dict(
        file_id=file, private=True, empty=True, manifest_hash="hash"
    )

    def cleared(c, claim, token, member, evidence):
        trace.append("free " + member["file_id"])
        next(slot for slot in s["slots"] if slot["FileID"] == member["file_id"]).update(
            State="free", AttemptID=None
        )

    pools.clear_retired_slot.side_effect = cleared
    for number in range(24):
        s = retirement_snapshot_fixture()
        s["slots"] += [dict(FileID=f"free-{i}", State="free", AttemptID=None) for i in range(14)]
        assert capacity_for_snapshot({}, s).required_files <= 17
        retire_superseded_generations(
            pools=pools,
            coordinator=Mock(),
            claim=Mock(),
            current_attempt_id="new",
            transport=transport,
            verifier=Mock(),
        )
        assert all(slot["State"] == "free" for slot in s["slots"])
    assert trace[:4] == ["retire", "private a", "clear a", "free a"]


def test_audited_clear_can_rebind_without_deleting_unrelated_app_properties():
    from tests.test_kvk_source_delivery import google_delivery

    args, _, api = google_delivery()
    transport = args["transport"]
    transport._request_guard = lambda _: None
    api.files_data["fake-1"]["appProperties"] = {"k98Generation": "old", "unrelated": "keep"}
    transport.rollover_clear("fake-1")
    transport.prepare_generation(args["generation"])
    transport.ensure_private(
        args["destination"], args["generation"].key, args["generation"].manifest()
    )
    assert api.files_data["fake-1"]["appProperties"]["unrelated"] == "keep"
    assert api.files_data["fake-1"]["appProperties"]["k98Generation"] == args["generation"].key


@pytest.mark.parametrize("when", ["before_probe", "during_probe"])
def test_rollover_closing_skips_new_retirement_and_allows_owned_delivery_to_drain(when):
    from kvk.services.source_output_pool_service import retire_superseded_generations

    s = retirement_snapshot_fixture()
    if when == "before_probe":
        s["pool"]["PoolState"] = "closing"
    pools, transport, verifier = Mock(), Mock(), Mock()
    pools.retirement_snapshot.return_value = s
    pools.retire_generation.return_value = None
    retire_superseded_generations(
        pools=pools,
        coordinator=Mock(),
        claim=Mock(),
        current_attempt_id="new",
        transport=transport,
        verifier=verifier,
    )
    assert verifier.call_count == (when == "during_probe")
    transport.rollover_private.assert_not_called()
    transport.rollover_clear.assert_not_called()


@pytest.mark.parametrize(
    "mismatch", [None, "PoolID", "AccountKey", "OldEpoch", "State", "Phase", "OwnerID"]
)
def test_retirement_owned_recognizes_only_the_exact_closing_reservation(monkeypatch, mismatch):
    from kvk.dal import source_output_pool_dal as mod

    coordinator, cursor = Mock(), Mock()
    claim = SimpleNamespace(
        account="acct",
        resources=(("destination:index", 1), ("destination:a", 1), ("destination:b", 1)),
    )
    snapshot = retirement_snapshot_fixture()
    snapshot["pool"].update(PoolState="closing", OwnerID="operation", IndexFileID="index")
    operation = dict(
        PoolID="pool",
        AccountKey="acct",
        OldEpoch=1,
        State="closing",
        Phase="draining",
        OwnerID=None,
    )
    if mismatch:
        operation[mismatch] = "different"

    @contextmanager
    def owned(_):
        yield cursor, dict(ConsumerKind="new_source", AccountKey="acct", KVK_NO=16, PoolEpoch=1)

    coordinator._owned = owned
    coordinator._attempt.return_value = (
        dict(Phase="publication_pending"),
        [dict(Role="index", FileID="index")],
    )
    repository = mod.SourceOutputPoolDAL(Mock())
    monkeypatch.setattr(mod, "one", lambda c: dict(PoolID="pool"))
    monkeypatch.setattr(mod, "_mutex", lambda *a: None)
    monkeypatch.setattr(repository, "_snapshot", lambda *a: snapshot)
    monkeypatch.setattr(repository, "_operation", lambda *a: operation)
    if mismatch:
        with pytest.raises(SourceConflict, match="Closing reservation"):
            repository.retirement_snapshot(coordinator, claim, "new")
    else:
        assert repository.retirement_snapshot(coordinator, claim, "new") == snapshot


def test_rollover_start_during_retirement_probe_does_not_start_retirement(monkeypatch):
    from copy import deepcopy

    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL

    snapshot = retirement_snapshot_fixture()
    closing = deepcopy(snapshot)
    closing["pool"].update(PoolState="closing", OwnerID="operation", Version=5, Fence=1)
    proof = dict(
        snapshot_hash=digest(snapshot).hex(),
        writer_terminated=True,
        current_pointer_verified=True,
        no_live_references=True,
        evidence_id="proof",
        current_attempt_id="new",
        old_attempt_id="old-attempt",
    )
    cursor = Mock()

    @contextmanager
    def owned(*a):
        yield cursor, {}, closing

    repository = SourceOutputPoolDAL(Mock())
    monkeypatch.setattr(repository, "_retirement_owned", owned)
    assert (
        repository.retire_generation(Mock(), Mock(), "new", snapshot, "old-attempt", proof) is None
    )
    cursor.execute.assert_not_called()


def test_already_started_retirement_clear_preserves_rollover_pool_owner_cas(monkeypatch):
    from kvk.dal import source_output_pool_dal as mod

    s = retirement_snapshot_fixture()
    pool = s["pool"]
    pool.update(PoolState="closing", OwnerID="rollover-reservation", Fence=1)
    cursor = Mock()
    monkeypatch.setattr(mod, "one", lambda c: dict(SequenceNo=1))
    cas = Mock(return_value=dict(Version=5))
    monkeypatch.setattr(mod, "_cas", cas)
    mod.SourceOutputPoolDAL._retirement_event(
        cursor,
        pool,
        s["slots"][0],
        SimpleNamespace(owner_id="job-owner", fence=5),
        dict(Actor="operator"),
        "cleanup",
        "clear",
        dict(empty=True),
    )
    sql = cas.call_args.args[1]
    assert "OwnerID=? OR (OwnerID IS NULL AND CAST(? AS uniqueidentifier) IS NULL)" in sql
    assert cas.call_args.args[-2:] == ("rollover-reservation", "rollover-reservation")
    assert "SET OwnerID=" not in sql and "Fence=Fence" not in sql
