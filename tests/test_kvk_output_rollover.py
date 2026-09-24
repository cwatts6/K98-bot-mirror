"""Offline pool capacity and provider-boundary failures; no live evidence."""

from contextlib import contextmanager, nullcontext
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


def test_s11_rollover_rotates_and_closes_stream_before_each_verified_phase():
    service, repository, _ = rollover()
    repository.execution_evidence = True
    repository.files.return_value = ("file-a",)
    trace = []
    version = 0

    def phase(claim, name, *_args):
        nonlocal version
        if name.endswith("verified"):
            assert trace[-1] == ("closed", name.removesuffix("_verified") + "_pending")
        version += 1
        trace.append(("phase", name, version))
        return SimpleNamespace(account="account-a", version=version)

    repository.phase.side_effect = phase

    @contextmanager
    def stream_for(claim, _operation, name, file_id):
        assert claim.version == version and file_id == "file-a"

        class Stream:
            stream_id = str(uuid4())

            def execute(self, message):
                return message

        stream = Stream()
        trace.append(("open", name, version))
        try:
            yield stream
        finally:
            trace.append(("closed", name))

    def transport_for(_operation, stream):
        adapter = SimpleNamespace(stream_id=stream.stream_id, execution=stream.execute)
        transport = SimpleNamespace(_authority_adapter=adapter)
        transport.rollover_private = lambda file_id: {"file_id": file_id, "private": True}
        transport.rollover_clear = lambda file_id: {
            "file_id": file_id,
            "private": True,
            "empty": True,
        }
        transport.rollover_setup = lambda file_id, old, new: {
            "file_id": file_id,
            "private": True,
            "setup": True,
            "old_kvk": old,
            "new_kvk": new,
        }
        return transport

    service.authority_stream_factory = stream_for
    service.transport_factory = transport_for
    service.advance("operation")
    assert [entry[1] for entry in trace if entry[0] == "open"] == [
        "private_pending",
        "clear_pending",
        "setup_pending",
    ]
    repository.complete.assert_called_once()


def test_s11_rollover_rejects_unscoped_transport_before_provider_call():
    service, repository, _ = rollover()
    repository.execution_evidence = True
    repository.files.return_value = ("file-a",)
    repository.phase.side_effect = lambda claim, *_args: claim
    service.authority_stream_factory = lambda *_args: nullcontext(
        SimpleNamespace(stream_id=str(uuid4()))
    )
    transport = Mock()
    transport._authority_adapter = SimpleNamespace(stream_id=str(uuid4()), execution=Mock())
    service.transport_factory = Mock(return_value=transport)
    with pytest.raises(SourceConflict, match="recorded provider transport"):
        service.advance("operation")
    transport.rollover_private.assert_not_called()
    repository.uncertain.assert_called_once_with(repository.claim.return_value)


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


def setup_readback_fixture():
    from kvk.services.new_source_export_service import rollover_marker
    from tests.test_export_runtime_composition import recorded_google_memory

    args, api, messages = recorded_google_memory()
    api.grids["fake-index"] = {
        "Sheet1": dict(sheetId=7, title="Sheet1", gridProperties=dict(rowCount=1, columnCount=3))
    }
    api.values["fake-index", "Sheet1"] = [[rollover_marker(16, 17)]]
    return args, api, messages


@pytest.mark.parametrize("computed_fields", [False, True])
def test_complete_setup_readback_is_read_only_and_never_calls_index_empty(computed_fields):
    from kvk.services.new_source_export_service import rollover_marker

    args, api, messages = setup_readback_fixture()
    original = api.execute

    def execute(path, method, kwargs, retries):
        result = original(path, method, kwargs, retries)
        if computed_fields and kwargs.get("includeGridData"):
            cell = result["sheets"][0]["data"][0]["rowData"][0]["values"][0]
            cell.update(
                effectiveValue={"stringValue": rollover_marker(16, 17)},
                formattedValue=rollover_marker(16, 17),
                effectiveFormat={"numberFormat": {"type": "TEXT"}},
            )
        return result

    api.execute = execute
    with args["authority_stream"]:
        result = args["transport"].rollover_setup_readback(
            "fake-index", 16, 17, expected_sheet_id=7
        )
    assert result["private"] and result["setup"] and result["sheet_id"] == 7
    assert len(result["manifest_hash"]) == 64
    assert "empty" not in result and "proof_id" not in result
    assert [(m.operation, m.target) for m in messages] == [
        ("sheets.get", "fake-index"),
        ("sheets.values.get", "fake-index"),
        ("drive.files.get", "fake-index"),
    ]
    assert all(not m.mutation for m in messages)


@pytest.mark.parametrize(
    "damage",
    [
        "extra_tab",
        "extra_cell",
        "namedRanges",
        "developerMetadata",
        "dataSources",
        "rows",
        "columns",
        "sheet_id",
        "title",
        "chart",
        "description",
        "properties",
        "public",
        "formula",
        "note",
        "format",
        "effective_value",
        "formatted_value",
        "grid_extra_cell",
        "grid_extra_row",
        "grid_offset",
        "grid_duplicate",
        "grid_missing",
    ],
)
def test_setup_marker_cannot_hide_old_grid_metadata_sharing_or_contradictory_cells(damage):
    from dataclasses import replace

    args, api, messages = setup_readback_fixture()
    transport = args["transport"]
    transport.registration = replace(transport.registration, audience="public_viewer")
    original = api.execute

    def execute(path, method, kwargs, retries):
        result = original(path, method, kwargs, retries)
        if path == "/files":
            if damage == "description":
                result["description"] = "old pointer"
            elif damage == "properties":
                result["appProperties"]["k98Export"] = "old"
            elif damage == "public":
                result["permissions"].append(
                    dict(type="anyone", role="reader", allowFileDiscovery=False)
                )
        elif path == "/spreadsheets/values" and damage == "extra_cell":
            result["values"][0].append("old receipt")
        elif kwargs.get("includeGridData"):
            grid = result["sheets"][0]
            block = grid["data"][0]
            cells = block["rowData"][0]["values"]
            if damage == "extra_tab":
                result["sheets"].append(dict(properties=dict(title="OldTab")))
            elif damage in {"namedRanges", "developerMetadata", "dataSources"}:
                result[damage] = [dict(retained=True)]
            elif damage in {"rows", "columns"}:
                grid["properties"]["gridProperties"][
                    "rowCount" if damage == "rows" else "columnCount"
                ] += 1
            elif damage == "sheet_id":
                grid["properties"]["sheetId"] += 1
            elif damage == "title":
                grid["properties"]["title"] = "Other"
            elif damage == "chart":
                grid["charts"] = [dict(chartId=123)]
            elif damage == "formula":
                cells[0]["userEnteredValue"] = dict(formulaValue='="same displayed marker"')
            elif damage == "note":
                cells[0]["note"] = "retained data"
            elif damage == "format":
                cells[0]["userEnteredFormat"] = dict(textFormat=dict(bold=True))
            elif damage == "effective_value":
                cells[0]["effectiveValue"] = dict(stringValue="different")
            elif damage == "formatted_value":
                cells[0]["formattedValue"] = "different"
            elif damage == "grid_extra_cell":
                cells.append(dict(note="hidden old content"))
            elif damage == "grid_extra_row":
                block["rowData"].append(dict(values=[dict(note="old")]))
            elif damage == "grid_offset":
                block["startColumn"] = 1
            elif damage == "grid_duplicate":
                grid["data"].append(block)
            elif damage == "grid_missing":
                grid["data"] = []
        return result

    api.execute = execute
    with args["authority_stream"]:
        assert transport.rollover_setup_readback("fake-index", 16, 17, expected_sheet_id=7) is None
    assert len(messages) == 3 and all(not m.mutation for m in messages)


@pytest.mark.parametrize(
    "file_id,old,new,sheet_id",
    [
        ("fake-1", 16, 17, 7),
        ("fake-index", 0, 17, 7),
        ("fake-index", 16, 16, 7),
        ("fake-index", True, 17, 7),
        ("fake-index", "16", 17, 7),
        ("fake-index", 16, 17, -1),
        ("fake-index", 16, 17, True),
        ("fake-index", 16, 17, 2**31),
    ],
)
def test_setup_readback_rejects_wrong_index_season_or_sheet_before_requests(
    file_id, old, new, sheet_id
):
    args, api, messages = setup_readback_fixture()
    with pytest.raises(SourceConflict):
        args["transport"].rollover_setup_readback(file_id, old, new, expected_sheet_id=sheet_id)
    assert not messages and not api.calls


def test_setup_write_uses_complete_readback_and_never_repairs_contradiction():
    args, api, messages = setup_readback_fixture()
    transport = args["transport"]
    transport._request_guard = lambda _: None
    api.named_ranges["fake-index"] = [dict(namedRangeId="old-name")]
    with args["authority_stream"], pytest.raises(SourceConflict, match="Complete private"):
        transport.rollover_setup("fake-index", 16, 17)
    assert [m.operation for m in messages if m.mutation] == ["sheets.values.update"]
    assert api.named_ranges["fake-index"] == [dict(namedRangeId="old-name")]


@pytest.mark.parametrize("failed_path", ["/spreadsheets", "/spreadsheets/values", "/files"])
def test_setup_readback_failure_never_retries_or_mutates(failed_path):
    from services.export_provider_adapter import ProviderOutcomeUnknown

    args, api, messages = setup_readback_fixture()
    original = api.execute
    failures = []

    def execute(path, method, kwargs, retries):
        if path == failed_path:
            failures.append(path)
            raise TimeoutError("Read acknowledgment lost")
        return original(path, method, kwargs, retries)

    api.execute = execute
    with args["authority_stream"], pytest.raises(ProviderOutcomeUnknown):
        args["transport"].rollover_setup_readback("fake-index", 16, 17)
    assert failures == [failed_path] and all(not m.mutation for m in messages)


def test_complete_setup_evaluator_consumes_sealed_readback_without_provider():
    from copy import deepcopy

    from kvk.services.new_source_export_service import GoogleSheetsTransport
    from services.export_reconciliation_service import ClosedProbeReplay
    from tests.test_export_reconciliation_service import sealed_publication_fixture

    args, api, messages = setup_readback_fixture()
    stream = args["authority_stream"]
    real_execute = stream.client.execute.side_effect
    observations = []

    def execute(message):
        response = real_execute(message)
        observations.append((deepcopy(message), deepcopy(response)))
        return response

    stream.client.execute.side_effect = execute
    with stream:
        original = args["transport"].rollover_setup_readback("fake-index", 16, 17)
    scope = dict(snapshot=dict(pool=dict(RegistrationHash="a" * 64)), stream_id=stream.stream_id)
    dal, store, _, _ = sealed_publication_fixture(scope, observations)
    calls = len(api.calls)
    with ClosedProbeReplay(dal=dal, store=store, account="account-a", **scope) as replay:
        transport = GoogleSheetsTransport.from_authority(
            registration=args["transport"].registration,
            reuse_guard=lambda *_: False,
            protected_file_ids=args["transport"].protected,
            execution=replay.execute,
            stream_id=stream.stream_id,
            authorize=lambda **_: None,
        )
        assert transport.rollover_setup_readback("fake-index", 16, 17) == original
    assert len(api.calls) == calls and len(messages) == 3


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


def interrupted_retirement_fixture():
    from copy import deepcopy

    from kvk.dal.new_source_import_dal import canonical

    pool = retirement_snapshot_fixture()
    pool["pool"].update(
        IndexFileID="fake-index", RegistrationHash="registration", PoolState="active", OwnerID=None
    )
    pool["slots"] = [dict(pool["slots"][0], FileID="fake-1")]
    slot = pool["slots"][0]
    prior = deepcopy(slot)
    slot.update(State="retired", Version=4, LastDispositionID="retire-event", LastAction="retire")
    evidence = dict(
        previous_assignment=prior,
        current_attempt_id="current",
        proof=dict(
            current_attempt_id="current",
            old_attempt_id="old-attempt",
            writer_terminated=True,
            current_pointer_verified=True,
            no_live_references=True,
            evidence_id="retire-proof",
        ),
    )
    event = dict(
        DispositionID="retire-event",
        OperationID="operation",
        PoolID="pool",
        FileID="fake-1",
        OldEpoch=1,
        NewEpoch=1,
        Action="retire",
        OwnerID="owner",
        Fence=5,
        ToSlotVersion=4,
        EvidenceJson=canonical(evidence),
        EvidenceHash=digest(evidence).hex(),
    )
    snapshot = dict(
        pool=pool,
        job=dict(
            JobID="job",
            AccountKey="acct",
            OwnerID="owner",
            Fence=5,
            Version=8,
            State="uncertain",
            ConsumerKind="new_source",
            IntentID="intent",
            ProvenanceJson="{}",
        ),
        attempts=[
            dict(
                AttemptID="current",
                ManifestJson=canonical(dict(generation=dict(export_key="key"))),
                ReceiptJson=None,
            )
        ],
        parts=[dict(FileID="fake-index"), dict(FileID="current-part")],
        retirement_events=[event],
        resources=[
            dict(
                ResourceKey=k,
                ActiveJobID="job",
                OwnerID="owner",
                Fence=5,
                Version=6,
                ActivePreparationID=None,
                ActiveOutputOperationID=None,
            )
            for k in ("account:acct", "destination:fake-1", "destination:fake-index")
        ],
    )
    proof = dict(
        snapshot_hash=digest(snapshot).hex(),
        writer_terminated=True,
        evidence_id="fresh-proof",
        state="confirmed",
        retirement_outcomes_reconciled=True,
        no_delayed_retirement_effects=True,
        receipt=dict(
            export_key="key",
            attempt_id="current",
            fence=5,
            files=["fake-index", "current-part"],
            audience="private",
            remote_id="fake-index",
        ),
    )
    return snapshot, proof


@pytest.mark.parametrize(
    "damage", [None, "hash", "owner", "epoch", "assignment", "version", "current", "missing"]
)
def test_restart_reconstructs_only_exact_retirement_journal(damage):
    from kvk.dal.source_output_pool_dal import pending_retirements

    snapshot, _ = interrupted_retirement_fixture()
    if damage == "hash":
        snapshot["retirement_events"][0]["EvidenceHash"] = "bad"
    if damage == "owner":
        snapshot["retirement_events"][0]["OwnerID"] = "other"
    if damage == "epoch":
        snapshot["pool"]["pool"]["Epoch"] = 2
    if damage == "assignment":
        snapshot["pool"]["slots"][0]["AssignmentID"] = "other"
    if damage == "version":
        snapshot["pool"]["slots"][0]["Version"] += 1
    if damage == "current":
        snapshot["attempts"][0]["AttemptID"] = "other"
    if damage == "missing":
        snapshot["retirement_events"] = []
    if damage:
        with pytest.raises(SourceConflict):
            pending_retirements(snapshot)
    else:
        token = pending_retirements(snapshot)[0]
        assert token["operation_id"] == "operation"
        assert token["slots"] == [
            dict(
                file_id="fake-1",
                version=4,
                event="retire-event",
                evidence_hash=snapshot["retirement_events"][0]["EvidenceHash"],
            )
        ]
        snapshot["pool"]["slots"][0]["State"] = "free"
        assert pending_retirements(snapshot) == []  # SQL clear committed before restart.


@pytest.mark.parametrize(
    "damage", [None, "stale", "receipt", "termination", "delayed", "membership", "owner"]
)
def test_recovery_claim_requires_positive_proof_and_exact_snapshot_cas(monkeypatch, damage):
    from kvk.dal import source_output_pool_dal as mod

    snapshot, proof = interrupted_retirement_fixture()
    if damage == "receipt":
        proof["receipt"]["fence"] = 4
    if damage == "termination":
        proof["writer_terminated"] = False
    if damage == "delayed":
        proof["no_delayed_retirement_effects"] = False
    if damage == "membership":
        snapshot["resources"].pop()
    if damage == "owner":
        snapshot["resources"][0]["OwnerID"] = "other"
    if damage in {"membership", "owner"}:
        proof["snapshot_hash"] = digest(snapshot).hex()
    cursor = Mock()
    coordinator = Mock(output_operations=True)
    coordinator._account.return_value = nullcontext(cursor)
    coordinator._operator_snapshot.return_value = {} if damage == "stale" else snapshot
    monkeypatch.setattr(mod, "_mutex", lambda *a: None)
    writes = []

    def cas(c, sql, *args):
        assert sql.count("?") == len(args)
        writes.append((sql, args))
        return dict(Version=9 if "ExportJob" in sql else 7)

    monkeypatch.setattr(mod, "_cas", cas)
    repo = mod.SourceOutputPoolDAL(Mock())
    if damage:
        with pytest.raises(SourceConflict):
            repo.claim_retirement_recovery(coordinator, snapshot, proof, actor="admin")
        if damage != "owner":
            assert writes == []
    else:
        claim = repo.claim_retirement_recovery(coordinator, snapshot, proof, actor="admin")
        assert claim.version == 9 and claim.owner_id == "owner" and claim.fence == 5
        assert all(v == 7 for _, v in claim.resources)
        audit = json.loads(writes[0][1][0])
        assert audit["retirement_recovery"]["token"]
        assert audit["retirement_recovery"]["proof"] == proof
        assert all("ExportAttempt" not in sql and "SET Fence=" not in sql for sql, _ in writes)


@pytest.mark.parametrize(
    "already_empty,fail", [(True, None), (False, None), (False, "provider"), (True, "sql")]
)
def test_recovery_reads_before_clear_and_retains_failure_for_fresh_reconciliation(
    monkeypatch, already_empty, fail
):
    from dataclasses import replace

    from kvk.services.source_output_pool_service import RetirementRecovery
    from tests.test_kvk_source_delivery import google_delivery

    snapshot, proof = interrupted_retirement_fixture()
    args, _, _ = google_delivery()
    transport = args["transport"]
    transport.registration = replace(transport.registration, slot_file_ids=("fake-1", "fake-2"))
    snapshot["pool"]["slots"].append(dict(FileID="fake-2", State="free"))
    trace = []
    empty = dict(file_id="fake-1", private=True, empty=True, manifest_hash="exact")
    transport.retirement_readback = Mock(
        side_effect=lambda f: trace.append("read") or (empty if already_empty else None)
    )
    transport.rollover_clear = Mock(
        side_effect=(
            RuntimeError("lost ack")
            if fail == "provider"
            else lambda f: trace.append("clear") or empty
        )
    )
    pools = Mock()
    pools.claim_retirement_recovery.return_value = SimpleNamespace(account="acct")
    pools._recovery_owned.return_value = nullcontext()
    pools.clear_retired_slot.side_effect = (
        RuntimeError("lost commit") if fail == "sql" else lambda *a, **kw: trace.append("commit")
    )
    pools.finish_retirement_recovery.side_effect = lambda *a: trace.append("revoke")
    recovery = RetirementRecovery(
        pools=pools,
        coordinator=Mock(),
        transport_factory=lambda s: transport,
        budget_factory=lambda a: Mock(),
    )
    if fail:
        with pytest.raises(RuntimeError):
            recovery.resume(snapshot, proof, actor="admin")
        pools.interrupt_retirement_recovery.assert_called_once()
        pools.finish_retirement_recovery.assert_not_called()
    else:
        recovery.resume(snapshot, proof, actor="admin")
        assert trace == (
            ["read", "commit", "revoke"] if already_empty else ["read", "clear", "commit", "revoke"]
        )
        pools.interrupt_retirement_recovery.assert_not_called()
        assert pools.clear_retired_slot.call_args.kwargs == {"recovery": True}


def test_retirement_readback_of_lost_ack_is_read_only():
    from tests.test_kvk_source_delivery import google_delivery

    args, _, api = google_delivery()
    transport = args["transport"]
    transport._request_guard = lambda _: None
    expected = transport.rollover_clear("fake-1")
    transport._mutate = Mock(side_effect=AssertionError("readback must not mutate"))
    assert transport.retirement_readback("fake-1") == expected
    api.files_data["fake-1"]["description"] = "not empty"
    assert transport.retirement_readback("fake-1") is None


def test_plain_reconciliation_cannot_release_unfinished_retirement():
    from services.export_coordination_dal import ExportCoordinationDAL

    snapshot, proof = interrupted_retirement_fixture()
    coordinator = ExportCoordinationDAL(Mock(), preparations=True, output_operations=True)
    with pytest.raises(SourceConflict, match="explicit retirement recovery"):
        coordinator.reconcile_operator(snapshot, proof, actor="admin")
    coordinator.connect.assert_not_called()


@pytest.mark.parametrize(
    "case", ["valid", "revoked", "version", "epoch", "closing", "wrong_closing"]
)
def test_recovery_guard_rechecks_nested_owner_and_rollover_reservation(monkeypatch, case):
    from kvk.dal import source_output_pool_dal as mod

    snapshot, _ = interrupted_retirement_fixture()
    audit = dict(
        state="owned",
        attempt_id="current",
        version=9,
        token="nested",
        pool_id="pool",
        epoch=1,
        registration_hash="registration",
    )
    if case == "revoked":
        audit["state"] = "complete"
    if case == "version":
        audit["version"] = 8
    if case == "epoch":
        snapshot["pool"]["pool"]["Epoch"] = 2
    if "closing" in case:
        snapshot["pool"]["pool"].update(PoolState="closing", OwnerID="rollover")
    coordinator, cursor = Mock(), Mock()
    coordinator._owned.return_value = nullcontext(
        (cursor, dict(ProvenanceJson=json.dumps(dict(retirement_recovery=audit))))
    )
    coordinator._operator_snapshot.return_value = snapshot
    repo = mod.SourceOutputPoolDAL(Mock())
    repo._operation = Mock(
        return_value=dict(
            PoolID="pool",
            AccountKey="acct",
            OldEpoch=1,
            State="closing",
            Phase="draining",
            OwnerID=None,
        )
    )
    if case == "wrong_closing":
        repo._operation.return_value["OwnerID"] = "another-worker"
    monkeypatch.setattr(mod, "_mutex", lambda *a: None)
    claim = SimpleNamespace(job_id="job", account="acct", version=9)
    if case in {"valid", "closing"}:
        with repo._recovery_owned(coordinator, claim, "current") as (_, _, pool):
            assert pool == snapshot["pool"]
    else:
        with pytest.raises(SourceConflict), repo._recovery_owned(coordinator, claim, "current"):
            pass


def test_recovery_completion_revokes_provider_before_publication_reprobe(monkeypatch):
    from kvk.dal import source_output_pool_dal as mod

    snapshot, _ = interrupted_retirement_fixture()
    cursor = Mock()
    coordinator = Mock()
    snapshot["pool"]["slots"][0]["State"] = "free"
    coordinator._operator_snapshot.return_value = snapshot
    repo = mod.SourceOutputPoolDAL(Mock())
    repo._recovery_owned = Mock(return_value=nullcontext((cursor, {}, snapshot["pool"])))
    writes = []
    monkeypatch.setattr(mod, "_cas", lambda c, sql, *a: writes.append((sql, a)))
    claim = SimpleNamespace(job_id="job", version=9, owner_id="owner", fence=5)
    repo.finish_retirement_recovery(coordinator, claim, "current")
    assert "State='uncertain'" in writes[0][0] and "'complete'" in writes[0][0]
    assert writes[0][1] == ("job", 9, "owner", 5)
    assert "ExportResource" not in writes[0][0]  # Claims retained until fresh settlement.
