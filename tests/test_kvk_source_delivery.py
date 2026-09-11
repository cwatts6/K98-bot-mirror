"""Fake destinations and durable-repository simulation; never contacts external systems."""

from contextlib import contextmanager
from dataclasses import replace
import json
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_delivery_dal import (
    DeliveryClaim,
    DeliveryRepository,
    Destination,
    _selected,
)
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.services.new_source_delivery_service import (
    deliver_discord,
    deliver_export,
    reconcile_delivery,
)
from kvk.services.new_source_export_service import build_generation, compact_sheets_generation
from tests.test_kvk_source_exports import export_input


class FakeRepository:
    def __init__(self):
        self.claims = {}
        self.selected = None
        self.busy = False
        self.fence = 0

    @contextmanager
    def serialize(self, destination):
        if self.busy:
            raise SourceConflict("busy")
        self.busy = True
        try:
            yield
        finally:
            self.busy = False

    def check_selections(self, selections):
        if self.selected not in selections:
            raise SourceConflict("stale")

    def claim(self, selection, destination, key):
        if selection != self.selected:
            raise SourceConflict("stale")
        old = self.claims.get(destination)
        if old and old.state in ("claimed", "uncertain"):
            raise SourceConflict("reconciliation required")
        if old and old.state == "confirmed" and old.selection == selection:
            return old
        self.fence += 1
        claim = DeliveryClaim(
            selection,
            destination,
            "owner",
            self.fence,
            "claimed",
            json.dumps(
                {
                    "export_key": key,
                    "publication_id": selection.publication_id,
                    "selection_version": selection.selection_version,
                }
            ),
        )
        self.claims[destination] = claim
        return claim

    @contextmanager
    def publication_gate(self, claim, selections):
        if claim.selection != self.selected or self.claims[claim.destination].fence != claim.fence:
            raise SourceConflict("stale")
        yield

    def finish(self, claim, state, receipt):
        data, previous = json.loads(receipt), json.loads(claim.receipt)
        for field in ("attempt_slots", "quarantined_slots", "audience"):
            if field in previous:
                data[field] = previous[field]
        receipt = json.dumps(data, separators=(",", ":"))
        self.claims[claim.destination] = replace(claim, state=state, receipt=receipt)
        return receipt

    def checkpoint(self, claim, **updates):
        data = json.loads(claim.receipt)
        data.update(updates)
        claim = replace(claim, receipt=json.dumps(data))
        self.claims[claim.destination] = claim
        return claim

    def quarantined_files(self, destination):
        claim = self.claims.get(destination)
        return (
            frozenset(json.loads(claim.receipt).get("quarantined_slots", []))
            if claim
            else frozenset()
        )

    def read_receipt(self, selection, destination):
        return self.claims.get(destination)


class FakeTransport:
    def __init__(self):
        self.private = {}
        self.current = "previous"
        self.calls = []
        self.fail_write = False
        self.fail_publish = False
        self.verify_hook = None

    def ensure_private(self, destination, key, manifest):
        self.private.setdefault(key, {})

    def write_range(self, destination, key, name, cell, values, *, value_input_option):
        assert value_input_option == "RAW" and cell == "A1"
        self.calls.append((key, name, cell))
        self.private[key][name] = values
        if self.fail_write:
            self.fail_write = False
            raise TimeoutError("private partial")

    def verify(self, destination, key):
        from kvk.rendering.new_source_export import ExportTable

        if self.verify_hook:
            self.verify_hook()
        return {
            name: dict(
                sha256=ExportTable(
                    name, tuple(values[0]), tuple(tuple(row) for row in values[1:])
                ).sha256,
                rows=len(values) - 1,
                columns=len(values[0]),
            )
            for name, values in self.private[key].items()
        }

    def publish_current(self, destination, key, fence):
        self.current = key
        if self.fail_publish:
            raise TimeoutError("response lost")
        return "fake-private-generation"


def setup_delivery():
    selection, snapshot = export_input()
    generation = build_generation(((selection, snapshot),))
    repo, transport = FakeRepository(), FakeTransport()
    repo.selected = selection
    args = dict(
        generation=generation,
        selection=selection,
        destination=Destination("sheets", "fake-sheet"),
        repository=repo,
        transport=transport,
    )
    return args, repo, transport


def test_success_has_three_independent_outcomes_and_idempotent_repeat():
    args, repo, transport = setup_delivery()
    result = deliver_export(**args)
    assert result.sql_selected and result.export_complete and result.delivery_state == "confirmed"
    assert len(transport.calls) == 12
    assert transport.current == args["generation"].key
    assert deliver_export(**args) == result
    assert len(transport.calls) == 12


@pytest.mark.parametrize("changed_period", [0, 1])
def test_multi_period_delivery_uses_changed_anchor_and_deduplicates(monkeypatch, changed_period):
    """Real claim/service/Sheets adapter composition; SQL I/O and Google are synthetic."""
    from contextlib import nullcontext
    from copy import deepcopy
    from decimal import Decimal

    import kvk.dal.new_source_delivery_dal as dal
    from kvk.services.new_source_export_service import ExportSelection, load_sheets_generation

    first, first_data = export_input()
    second = replace(
        first,
        period_id="00000000-0000-0000-0000-000000000003",
        publication_id="00000000-0000-0000-0000-000000000004",
    )
    second_data = deepcopy(first_data)
    second_data["envelope"]["period_id"] = second.period_id
    second_data["envelope"]["publication"].update(
        PublicationID=second.publication_id, PeriodKey="fight:pass7"
    )
    for config in second_data["metadata"]["configs"].values():
        config["PeriodKey"] = "fight:pass7"
    selections = [first, second]
    snapshots = {first: first_data, second: second_data}
    selected = {s.period_id: s for s in selections}
    history = {}

    class Repository(FakeRepository):
        def check_selections(self, items):
            if any(selected.get(s.period_id) != s for s in items):
                raise SourceConflict("stale period")

        def claim(self, selection, destination, key):
            # Exercise the actual production generation/anchor/fence decision;
            # replace only its database connection and persisted row reads.
            claim = DeliveryRepository(Mock()).claim(selection, destination, key)
            self.claims[destination] = claim
            self.selected = selection
            return claim

        @contextmanager
        def publication_gate(self, claim, items):
            self.check_selections(items)
            with super().publication_gate(claim, items):
                yield

        def finish(self, claim, state, receipt):
            receipt = super().finish(claim, state, receipt)
            history[claim.selection.publication_id] = self.claims[claim.destination]
            return receipt

    monkeypatch.setattr(dal, "transaction", lambda connect: nullcontext(Mock()))
    monkeypatch.setattr(dal, "_selected", lambda cursor, s: Repository().check_selections((s,)))
    monkeypatch.setattr(
        dal,
        "rows",
        lambda cursor: [
            dict(
                PublicationID=c.selection.publication_id,
                DeliveryState=c.state,
                Fence=c.fence,
                OwnerID=c.owner_id,
                Receipt=c.receipt,
            )
            for c in history.values()
        ],
    )
    args, _, api = google_delivery()
    transport, destination = args["transport"], args["destination"]

    def generation(items):
        return load_sheets_generation(
            connect=Mock(side_effect=AssertionError("No live SQL")),
            selections=items,
            snapshot_loader=lambda **kw: snapshots[kw["selection"]],
        )

    unchanged = selections[1 - changed_period]
    initial = generation(selections)
    args.update(generation=initial, selection=unchanged, repository=Repository())
    original = deliver_export(**args)
    assert original.delivery_state == "confirmed"
    original_file = transport._file(destination, initial.key)["id"]
    old_grids = deepcopy(api.grids[original_file])
    old_values = deepcopy(api.values)

    prior = selections[changed_period]
    revised = ExportSelection(
        prior.kvk_no,
        prior.period_id,
        "00000000-0000-0000-0000-000000000005",
        prior.selection_version + 1,
    )
    revised_data = deepcopy(snapshots[prior])
    revised_data["envelope"]["publication"]["PublicationID"] = revised.publication_id
    revised_data["envelope"]["selection"]["SelectionVersion"] = revised.selection_version
    revised_data["envelope"]["players"][0]["dkp"] = Decimal("987654")
    snapshots[revised] = revised_data
    selected[prior.period_id] = revised
    selections[changed_period] = revised
    updated = generation(selections)
    assert updated.key != initial.key
    assert generation(tuple(reversed(selections))).key == updated.key
    # A confirmed unchanged anchor must not swallow a changed combined manifest.
    calls = len(api.calls)
    args.update(generation=updated, repository=Repository())
    with pytest.raises(SourceConflict, match="another generation manifest"):
        deliver_export(**args)
    assert len(api.calls) == calls
    args["selection"] = revised
    result = deliver_export(**args)
    assert result.delivery_state == "confirmed"
    assert json.loads(result.receipt)["export_key"] == updated.key
    assert history[revised.publication_id].fence > history[unchanged.publication_id].fence
    assert transport.verify(destination, updated.key) == updated.manifest()
    assert transport._pointer(transport._index(destination, updated.key))[0][0] == updated.key
    assert api.grids[original_file] == old_grids
    assert all(api.values[k] == v for k, v in old_values.items() if k[0] == original_file)
    # The untouched period retains identical facts; both periods remain in ALL_WINDOWS.
    windows = next(t for t in updated.tables if t.name == "ALL_WINDOWS")
    assert {r[windows.columns.index("period_key")] for r in windows.rows} == {
        "fight:pass4",
        "fight:pass7",
        "overall",
    }
    assert all(
        r[windows.columns.index("status")] == "not_received"
        for r in windows.rows
        if r[windows.columns.index("period_key")] == "overall"
    )
    unchanged_only = {t.name: t for t in generation((unchanged,)).tables}
    for after in updated.tables:
        stable = unchanged_only[after.name]
        assert stable.columns == after.columns
        assert set(stable.rows).issubset(set(after.rows))
    players = next(t for t in updated.tables if t.name == "KVK_Player_Windowed")
    assert any(r[players.columns.index("dkp::value")] == "987654" for r in players.rows)
    calls = len(api.calls)
    args["repository"] = Repository()  # Reload saved receipts, discard instance state.
    assert deliver_export(**args).receipt == result.receipt
    assert len(api.calls) == calls


def test_t57_partial_private_write_keeps_old_current_and_retries_same_ranges():
    args, repo, transport = setup_delivery()
    transport.fail_write = True
    result = deliver_export(**args)
    assert result.delivery_state == "failed" and not result.export_complete
    assert transport.current == "previous"
    assert deliver_export(**args).delivery_state == "confirmed"
    assert transport.calls[0] == transport.calls[1]


def test_verification_detects_extra_stale_tab_before_current():
    args, repo, transport = setup_delivery()
    transport.private[args["generation"].key] = {"stale": [["column"], ["value"]]}
    assert deliver_export(**args).delivery_state == "failed"
    assert transport.current == "previous"


def test_t58_selected_generation_changes_during_private_writes():
    args, repo, transport = setup_delivery()
    transport.verify_hook = lambda: setattr(
        repo, "selected", replace(repo.selected, selection_version=8)
    )
    result = deliver_export(**args)
    assert result.export_complete and result.delivery_state == "failed"
    assert transport.current == "previous"


def test_stale_queued_work_does_not_write():
    args, repo, transport = setup_delivery()
    repo.selected = replace(repo.selected, selection_version=8)
    with pytest.raises(SourceConflict):
        deliver_export(**args)
    assert transport.calls == []


def test_publish_timeout_is_uncertain_and_blocks_newer_generation():
    args, repo, transport = setup_delivery()
    transport.fail_publish = True
    result = deliver_export(**args)
    assert result.export_complete and result.delivery_state == "uncertain"
    with pytest.raises(SourceConflict, match="reconciliation"):
        deliver_export(**args)
    repo.selected = replace(repo.selected, selection_version=8)
    with pytest.raises(SourceConflict):
        repo.claim(repo.selected, args["destination"], "new")
    assert len(transport.calls) == 12


@pytest.mark.parametrize("message_id", [None, "123456789"])
def test_t59_uncertain_discord_send_or_edit_never_blind_replacement(message_id):
    args, repo, _ = setup_delivery()
    export = deliver_export(**args)
    transport = Mock()
    transport.deliver.side_effect = TimeoutError("uncertain")
    kwargs = dict(
        selection=args["selection"],
        destination=Destination("discord", "fake-channel"),
        export_key=args["generation"].key,
        export_receipt=export.receipt,
        repository=repo,
        transport=transport,
        cadence_admitted=True,
        message_id=message_id,
    )
    assert deliver_discord(**kwargs).delivery_state == "uncertain"
    with pytest.raises(SourceConflict):
        deliver_discord(**kwargs)
    assert transport.deliver.call_count == 1
    assert transport.deliver.call_args.kwargs["message_id"] == message_id


def test_cadence_admission_is_required_without_mutating_daily_ownership():
    args, repo, _ = setup_delivery()
    export = deliver_export(**args)
    transport = Mock()
    with pytest.raises(ValueError, match="cadence"):
        deliver_discord(
            selection=args["selection"],
            destination=Destination("discord", "fake-channel"),
            export_key=args["generation"].key,
            export_receipt=export.receipt,
            repository=repo,
            transport=transport,
            cadence_admitted=False,
        )
    transport.deliver.assert_not_called()


def test_restart_reconciliation_unknown_then_confirmed_no_resend():
    args, repo, transport = setup_delivery()
    transport.fail_publish = True
    result = deliver_export(**args)
    probe = Mock()
    probe.reconcile.return_value = ("unknown", None)
    kwargs = dict(
        selection=args["selection"],
        destination=args["destination"],
        repository=repo,
        transport=probe,
    )
    assert reconcile_delivery(**kwargs).state == "uncertain"
    receipt = json.loads(result.receipt)
    receipt.update(phase="published", remote_id="fake-reconciled")
    probe.reconcile.return_value = ("confirmed", json.dumps(receipt))
    assert reconcile_delivery(**kwargs).state == "confirmed"
    assert deliver_export(**args).delivery_state == "confirmed"
    assert len(transport.calls) == 12


def test_dal_destination_lock_is_parameterized_released_and_closed():
    connection = Mock()
    connection.cursor.return_value.fetchone.return_value = (0,)
    repo = DeliveryRepository(lambda: connection)
    with repo.serialize(Destination("sheets", "fake-';--")):
        pass
    calls = connection.cursor.return_value.execute.call_args_list
    assert "sp_getapplock" in calls[0].args[0]
    assert "fake-';--" not in calls[0].args[0]
    assert "sp_releaseapplock" in calls[-1].args[0]
    connection.close.assert_called_once()


@pytest.mark.parametrize("value", ["", " x", "x ", "x\n", "x" * 129])
def test_invalid_destinations_fail_before_io(value):
    with pytest.raises(ValueError):
        Destination("sheets", value)


def test_dal_checks_selected_version_and_pending_config(monkeypatch):
    import kvk.dal.new_source_delivery_dal as dal

    selection, _ = export_input()
    monkeypatch.setattr(
        dal,
        "locked_period",
        lambda *a: (None, dict(PublicationID=selection.publication_id, SelectionVersion=7), []),
    )
    monkeypatch.setattr(dal, "desired_config", lambda *a: "desired")
    monkeypatch.setattr(dal, "one", lambda *a: dict(ConfigVersionID="old", BuildState="complete"))
    with pytest.raises(SourceConflict, match="Pending"):
        _selected(Mock(), selection)
    monkeypatch.setattr(
        dal, "one", lambda *a: dict(ConfigVersionID="desired", BuildState="complete")
    )
    _selected(Mock(), selection)
    with pytest.raises(SourceConflict, match="Stale"):
        _selected(Mock(), replace(selection, selection_version=8))


@pytest.mark.parametrize("state", ["claimed", "uncertain"])
def test_actual_dal_blocks_unresolved_other_publication(monkeypatch, state):
    from contextlib import nullcontext

    import kvk.dal.new_source_delivery_dal as dal

    selection, _ = export_input()
    cursor = Mock()
    monkeypatch.setattr(dal, "transaction", lambda connect: nullcontext(cursor))
    monkeypatch.setattr(dal, "_selected", lambda *args: None)
    monkeypatch.setattr(
        dal, "rows", lambda cursor: [dict(PublicationID="other", DeliveryState=state, Fence=8)]
    )
    repo = DeliveryRepository(Mock(side_effect=AssertionError("SQL forbidden")))
    with pytest.raises(SourceConflict, match="reconciliation"):
        repo.claim(selection, Destination("sheets", "fake"), "a" * 64)
    assert not any(
        "UPDATE" in c.args[0] or "INSERT" in c.args[0] for c in cursor.execute.call_args_list
    )


def test_t65_actual_dal_rollback_reclaims_reconciled_receipt_with_increasing_fence(monkeypatch):
    from contextlib import nullcontext

    import kvk.dal.new_source_delivery_dal as dal

    selection, _ = export_input()
    cursor = Mock()
    monkeypatch.setattr(dal, "transaction", lambda connect: nullcontext(cursor))
    monkeypatch.setattr(dal, "_selected", lambda *args: None)
    receipt = json.dumps(
        dict(export_key="old", publication_id=selection.publication_id, selection_version=6)
    )
    monkeypatch.setattr(
        dal,
        "rows",
        lambda cursor: [
            dict(
                PublicationID=selection.publication_id,
                DeliveryState="confirmed",
                Fence=8,
                Receipt=receipt,
                OwnerID="old-owner",
            ),
            dict(PublicationID="other-publication", DeliveryState="confirmed", Fence=12),
        ],
    )
    claim = DeliveryRepository(Mock()).claim(selection, Destination("sheets", "fake"), "new")
    assert claim.fence == 13 and claim.state == "claimed"
    assert json.loads(claim.receipt)["selection_version"] == 7
    assert any("AttemptCount=AttemptCount+1" in c.args[0] for c in cursor.execute.call_args_list)


def test_actual_dal_receipt_cas_rejects_old_owner_and_fence(monkeypatch):
    from contextlib import nullcontext

    import kvk.dal.new_source_delivery_dal as dal

    selection, _ = export_input()
    cursor = Mock()
    monkeypatch.setattr(dal, "transaction", lambda connect: nullcontext(cursor))
    monkeypatch.setattr(
        dal, "one", lambda cursor: dict(OwnerID="new-owner", Fence=9, DeliveryState="claimed")
    )
    claim = DeliveryClaim(selection, Destination("sheets", "fake"), "old-owner", 8, "claimed", "{}")
    with pytest.raises(SourceConflict, match="fence"):
        DeliveryRepository(Mock()).finish(claim, "confirmed", "{}")
    assert not any("UPDATE" in c.args[0] for c in cursor.execute.call_args_list)


def test_no_remote_receipt_cannot_claim_success():
    args, repo, transport = setup_delivery()
    transport.publish_current = lambda *args: None
    result = deliver_export(**args)
    assert result.export_complete and result.delivery_state == "uncertain"


def test_crash_after_claim_is_not_reclaimed_after_restart():
    args, repo, transport = setup_delivery()
    transport.ensure_private = Mock(side_effect=KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        deliver_export(**args)
    assert repo.claims[args["destination"]].state == "claimed"
    with pytest.raises(SourceConflict, match="reconciliation"):
        deliver_export(**args)


def test_cross_publication_export_receipt_cannot_be_sent():
    args, repo, _ = setup_delivery()
    outcome = deliver_export(**args)
    selection = replace(args["selection"], publication_id="00000000-0000-0000-0000-000000000009")
    with pytest.raises(ValueError, match="selection"):
        deliver_discord(
            selection=selection,
            destination=Destination("discord", "fake-channel"),
            export_key=args["generation"].key,
            export_receipt=outcome.receipt,
            repository=repo,
            transport=Mock(),
            cadence_admitted=True,
        )


def test_delayed_private_write_is_isolated_from_new_generation():
    args, repo, transport = setup_delivery()
    transport.fail_write = True
    assert deliver_export(**args).delivery_state == "failed"
    old_key = args["generation"].key
    old_table = args["generation"].tables[0]
    selection, snapshot = export_input()
    selection = replace(selection, selection_version=8)
    snapshot["envelope"]["selection"]["SelectionVersion"] = 8
    newer = build_generation(((selection, snapshot),))
    repo.selected = selection
    assert (
        deliver_export(**(args | dict(selection=selection, generation=newer))).delivery_state
        == "confirmed"
    )
    transport.write_range(
        args["destination"],
        old_key,
        old_table.name,
        "A1",
        old_table.raw_values(),
        value_input_option="RAW",
    )
    assert transport.current == newer.key


class GoogleMemoryAPI:
    """Stateful fake of discovery request shapes; adapter itself executes unchanged."""

    def __init__(self):
        self.files_data = {}
        self.grids = {}
        self.values = {}
        self.calls = []
        self.fail_create = False
        self.fail_pointer = False
        self.fail_write = False
        self.next_sheet_id = 1

    def client(self, path=""):
        from types import SimpleNamespace

        root = SimpleNamespace()
        for method in ("files", "spreadsheets", "values", "permissions"):
            setattr(root, method, lambda method=method: self.client(path + "/" + method))
        for method in ("get", "list", "create", "update", "batchUpdate", "batchGet", "delete"):

            def request(method=method, **kwargs):
                return SimpleNamespace(
                    execute=lambda num_retries: self.execute(path, method, kwargs, num_retries),
                    method="GET" if method in ("get", "batchGet", "list") else "POST",
                    methodId=("drive" if path in ("/files", "/permissions") else "sheets")
                    + path.replace("/", ".")
                    + "."
                    + method,
                )

            setattr(root, method, request)
        return root

    def execute(self, path, method, args, retries):
        from copy import deepcopy
        import re

        assert retries == 0
        self.calls.append((path, method, deepcopy(args)))
        if path == "/files":
            if method == "list":
                predicates = re.findall(r"key='([^']+)' and value='([^']+)'", args["q"])
                return {
                    "files": [
                        {"id": id}
                        for id, f in self.files_data.items()
                        if all(f["appProperties"].get(k) == v for k, v in predicates)
                    ]
                }
            if method == "get":
                if args["fileId"] not in self.files_data:
                    from googleapiclient.errors import HttpError
                    from httplib2 import Response

                    raise HttpError(Response({"status": "404"}), b"missing")
                return deepcopy(self.files_data[args["fileId"]])
            if method == "update":
                body = deepcopy(args["body"])
                if "appProperties" in body:
                    self.files_data[args["fileId"]].setdefault("appProperties", {}).update(
                        body.pop("appProperties")
                    )
                self.files_data[args["fileId"]].update(body)
                return {"id": args["fileId"]}
            if method == "create":
                id = f"fake-{len(self.files_data) + 1}"
                self.files_data[id] = dict(
                    args["body"],
                    id=id,
                    shared=False,
                    permissions=[dict(type="user", role="owner")],
                    webViewLink=f"https://example.invalid/{id}",
                )
                self.grids[id] = {
                    "Sheet1": dict(
                        sheetId=0,
                        title="Sheet1",
                        gridProperties=dict(rowCount=1000, columnCount=26),
                    )
                }
                if self.fail_create:
                    raise TimeoutError("create response lost")
                return {"id": id}
        if path == "/permissions":
            permissions = self.files_data[args["fileId"]]["permissions"]
            if method == "create":
                permissions.append(dict(args["body"], id="public-reader"))
                return {"id": "public-reader"}
            if method == "delete":
                permissions[:] = [p for p in permissions if p.get("id") != args["permissionId"]]
                return {}
        id = args["spreadsheetId"]
        if path == "/spreadsheets":
            if method == "get":
                return {"sheets": [{"properties": deepcopy(p)} for p in self.grids[id].values()]}
            if method == "batchUpdate":
                for req in args["body"]["requests"]:
                    if "addSheet" in req:
                        prop = deepcopy(req["addSheet"]["properties"])
                        prop["sheetId"] = self.next_sheet_id
                        self.next_sheet_id += 1
                        self.grids[id][prop["title"]] = prop
                    elif "updateSheetProperties" in req:
                        prop = req["updateSheetProperties"]["properties"]
                        for grid in self.grids[id].values():
                            if grid["sheetId"] == prop["sheetId"]:
                                # Google validates shrink against the currently frozen rows.
                                if prop["gridProperties"].get("rowCount", 1000) <= grid[
                                    "gridProperties"
                                ].get("frozenRowCount", 0):
                                    raise ValueError("Cannot delete all non-frozen rows")
                                grid["gridProperties"].update(prop["gridProperties"])
                    else:
                        if len(self.grids[id]) == 1:
                            raise ValueError("Cannot remove all sheets")
                        sid = req["deleteSheet"]["sheetId"]
                        for title, props in list(self.grids[id].items()):
                            if props["sheetId"] == sid:
                                self.values.pop((id, title), None)
                        self.grids[id] = {
                            k: v for k, v in self.grids[id].items() if v["sheetId"] != sid
                        }
                return {}
        if path == "/spreadsheets/values":
            if method == "batchGet":
                return {
                    "valueRanges": [
                        dict(
                            self.execute(path, "get", dict(spreadsheetId=id, range=r), retries),
                            range=r,
                        )
                        for r in args["ranges"]
                    ]
                }
            name, area = (
                args["range"].split("!") if "!" in args["range"] else ("Sheet1", args["range"])
            )
            name = name.strip("'")
            numbers = [int(n) for n in re.findall(r"\d+", area)]
            if not numbers:
                name, numbers = area, [1, 1000000]
            if name not in self.grids[id]:
                raise ValueError("Unknown generation tab")
            start = numbers[0] - 1
            rows = self.values.setdefault((id, name), [])
            if method == "update":
                assert args["valueInputOption"] == "RAW"
                incoming = deepcopy(args["body"]["values"])
                while len(rows) < start + len(incoming):
                    rows.append([])
                rows[start : start + len(incoming)] = incoming
                if self.fail_write and name != "Sheet1":
                    raise TimeoutError("write response lost")
                if self.fail_pointer and name == "Sheet1":
                    raise TimeoutError("pointer response lost")
                return {}
            result = deepcopy(rows[start : numbers[-1]])
            # Emulate Sheets omitting trailing empty cells and rows.
            for row in result:
                while row and row[-1] == "":
                    row.pop()
            while result and not result[-1]:
                result.pop()
            return {"values": result}
        raise AssertionError((path, method))


def google_delivery():
    from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration

    args, repo, _ = setup_delivery()
    api = GoogleMemoryAPI()
    registration = SheetsRegistration(
        "fake-index",
        ("fake-1", "fake-2"),
        "owner@example.invalid",
        "bot@synthetic.iam.gserviceaccount.com",
    )
    for id in (registration.index_file_id, *registration.slot_file_ids):
        api.files_data[id] = dict(
            id=id,
            mimeType=GoogleSheetsTransport._MIME,
            appProperties={},
            capabilities={"canEdit": True, "canShare": True},
            permissions=[
                dict(type="user", role="owner", emailAddress=registration.owner_email),
                dict(type="user", role="writer", emailAddress=registration.service_account_email),
            ],
        )
        api.grids[id] = {
            "Sheet1": dict(
                sheetId=0, title="Sheet1", gridProperties=dict(rowCount=1000, columnCount=26)
            )
        }
    args["destination"] = Destination("sheets", registration.index_file_id)
    args["transport"] = GoogleSheetsTransport(
        drive=api.client(),
        sheets=api.client(),
        registration=registration,
        reuse_guard=lambda *args: False,
        protected_file_ids={"config-workbook"},
        rows_per_request=3,
    )
    from kvk.services.new_source_export_service import compact_sheets_generation

    args["generation"] = compact_sheets_generation(args["generation"])
    return args, repo, api


def test_registered_google_adapter_initializes_twelve_tabs_without_creating_files():
    args, repo, api = google_delivery()
    outcome = deliver_export(**args)
    assert outcome.delivery_state == "confirmed"
    assert len(api.files_data) == 3 and len(api.grids["fake-1"]) == 13
    assert (
        args["transport"].verify(args["destination"], args["generation"].key)
        == args["generation"].manifest()
    )
    assert deliver_export(**args) == outcome
    assert not any(
        path == "/files" and method in ("create", "list") for path, method, _ in api.calls
    )
    assert all(
        len(call[2]["body"]["values"]) <= 3
        for call in api.calls
        if call[0] == "/spreadsheets/values" and call[1] == "update"
    )


def test_registered_google_restart_confirms_lost_pointer():
    from kvk.services.new_source_export_service import GoogleSheetsTransport

    args, repo, api = google_delivery()
    api.fail_pointer = True
    assert deliver_export(**args).delivery_state == "uncertain"
    old = args["transport"]
    restarted = GoogleSheetsTransport(
        drive=api.client(),
        sheets=api.client(),
        registration=old.registration,
        reuse_guard=old.reuse_guard,
        protected_file_ids=old.protected,
    )
    assert (
        reconcile_delivery(
            selection=args["selection"],
            destination=args["destination"],
            repository=repo,
            transport=restarted,
        ).state
        == "confirmed"
    )


@pytest.mark.parametrize(
    "mutation", ["missing", "wrong_owner", "reader", "public", "no_edit", "protected"]
)
def test_registered_google_setup_errors_do_not_mutate_files(mutation):
    args, repo, api = google_delivery()
    f = api.files_data["fake-1"]
    if mutation == "missing":
        del api.files_data["fake-1"]
    elif mutation == "wrong_owner":
        f["permissions"][0]["emailAddress"] = "other@example.invalid"
    elif mutation == "reader":
        f["permissions"][1]["role"] = "reader"
    elif mutation == "public":
        f["permissions"].append(dict(type="anyone", role="reader"))
    elif mutation == "no_edit":
        f["capabilities"]["canEdit"] = False
    else:
        args["transport"].protected = frozenset({"fake-1"})
    result = deliver_export(**args)
    assert result.delivery_state == "failed" and result.setup_required
    assert not result.export_complete
    assert all(method in ("get", "list") for _, method, _ in api.calls)


def test_registered_google_private_write_timeout_blocks_all_reuse():
    args, repo, api = google_delivery()
    api.fail_write = True
    assert deliver_export(**args).delivery_state == "uncertain"
    with pytest.raises(SourceConflict, match="reconciliation"):
        deliver_export(**args)
    assert (
        reconcile_delivery(
            selection=args["selection"],
            destination=args["destination"],
            repository=repo,
            transport=args["transport"],
        ).state
        == "uncertain"
    )


def next_google_generation(args, repo):
    selection, snapshot = export_input()
    selection = replace(selection, selection_version=args["selection"].selection_version + 1)
    snapshot["envelope"]["selection"]["SelectionVersion"] = selection.selection_version
    # Physical reuse tests use explicitly live, unreferenced generations.
    for key in ("PlayerState", "AggregateState", "PeriodState"):
        snapshot["envelope"]["publication"][key] = (
            "live" if key != "AggregateState" else "not_received"
        )
    snapshot["envelope"]["current_period_state"] = "live"
    repo.selected = selection
    return args | dict(
        selection=selection,
        generation=compact_sheets_generation(build_generation(((selection, snapshot),))),
    )


def test_registered_google_reuse_requires_release_and_uses_new_tab_identity():
    args, repo, api = google_delivery()
    args = next_google_generation(args, repo)
    assert deliver_export(**args).delivery_state == "confirmed"
    old_key = args["generation"].key
    old_tab = args["transport"]._tab(old_key, "KVK_Windows")
    args = next_google_generation(args, repo)
    assert deliver_export(**args).delivery_state == "confirmed"
    args = next_google_generation(args, repo)
    refused = deliver_export(**args)
    assert refused.setup_required and "No reusable slot" in refused.setup_required
    args["transport"].reuse_guard = lambda destination, key: key == old_key
    assert deliver_export(**args).delivery_state == "confirmed"
    assert len(api.files_data) == 3 and old_tab not in api.grids["fake-1"]
    # A provider request queued before retirement addresses the old unique tab name.
    with pytest.raises(ValueError, match="Unknown generation tab"):
        api.client().spreadsheets().values().update(
            spreadsheetId="fake-1",
            range=f"'{old_tab}'!A1",
            valueInputOption="RAW",
            body={"values": [["late"]]},
        ).execute(num_retries=0)
    assert (
        args["transport"].verify(args["destination"], args["generation"].key)
        == args["generation"].manifest()
    )


def test_registered_google_retains_final_even_if_reuse_guard_allows():
    args, repo, api = google_delivery()
    assert deliver_export(**args).delivery_state == "confirmed"
    api.files_data["fake-1"]["appProperties"]["k98Retain"] = "True"
    args = next_google_generation(args, repo)
    assert deliver_export(**args).delivery_state == "confirmed"
    args["transport"].reuse_guard = lambda *args: True
    args = next_google_generation(args, repo)
    assert deliver_export(**args).setup_required


@pytest.mark.parametrize(
    "mutation", ["extra_tab", "changed_cell", "different_write", "stale_fence"]
)
def test_registered_google_rejects_tampered_generation(mutation):
    args, repo, api = google_delivery()
    assert deliver_export(**args).delivery_state == "confirmed"
    transport, destination, key = args["transport"], args["destination"], args["generation"].key
    if mutation == "changed_cell":
        api.values[("fake-1", transport._tab(key, "KVK_Windows"))][1][0] = "tampered"
        assert transport.verify(destination, key) != args["generation"].manifest()
        return
    with pytest.raises(SourceConflict):
        if mutation == "extra_tab":
            api.grids["fake-1"]["stale"] = dict(title="stale")
            transport.verify(destination, key)
        elif mutation == "different_write":
            transport.write_range(
                destination, key, "KVK_Windows", "A1", [["wrong"]], value_input_option="RAW"
            )
        else:
            api.values[("fake-index", "Sheet1")][0][1] = "99"
            transport.publish_current(destination, key, 2)


def test_registered_google_cell_budget_rejects_before_any_remote_call():
    from kvk.services.new_source_delivery_service import DestinationSetupRequired

    args, _, api = google_delivery()
    manifest = args["generation"].manifest()
    manifest["KVK_Player_Windowed"] = dict(rows=18 * 10000, columns=40, sha256="a" * 64)
    manifest["ALL_WINDOWS"] = dict(rows=18 * 10000, columns=40, sha256="b" * 64)
    manifest["COMPARISONS"] = dict(rows=18 * 10000, columns=41, sha256="c" * 64)
    with pytest.raises(DestinationSetupRequired, match="slots"):
        args["transport"].ensure_private(args["destination"], args["generation"].key, manifest)
    assert not api.calls


@pytest.mark.parametrize("case", ["selected", "final", "uncertain", "discord", "unreferenced"])
def test_actual_dal_slot_reuse_requires_terminal_unselected_live_export(monkeypatch, case):
    from contextlib import nullcontext

    import kvk.dal.new_source_delivery_dal as dal

    cursor = Mock()
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    receipt = json.dumps(dict(export_key="a" * 64))
    matches = [
        dict(
            Receipt=receipt,
            PublicationID="publication",
            DeliveryState="uncertain" if case == "uncertain" else "confirmed",
        )
    ]
    batches = iter(
        [
            matches,
            [dict(Receipt=receipt, PublicationID="publication")] if case == "discord" else [],
        ]
    )
    monkeypatch.setattr(dal, "rows", lambda _: next(batches))
    monkeypatch.setattr(
        dal,
        "one",
        lambda _: dict(
            SelectedID="publication" if case == "selected" else None,
            PeriodState="final" if case == "final" else "live",
        ),
    )
    assert dal.DeliveryRepository(Mock()).slot_reusable(
        Destination("sheets", "fake-index"), "a" * 64
    ) == (case == "unreferenced")


def test_registered_google_split_parts_verify_all_rows_and_directory(monkeypatch):
    from copy import deepcopy
    from dataclasses import replace

    from kvk.services.new_source_export_service import GoogleSheetsTransport

    args, repo, api = google_delivery()
    # Small budgets exercise real splitting, header repetition and exact reconstruction.
    monkeypatch.setattr(GoogleSheetsTransport, "MAX_CELLS", 10_500)
    count = len(args["transport"].partition_manifest(args["generation"].manifest()))
    assert count > 1
    ids = tuple(f"part-{i}" for i in range(count * 2))
    for id in ids:
        api.files_data[id] = deepcopy(api.files_data["fake-1"])
        api.files_data[id]["id"] = id
        api.grids[id] = deepcopy(api.grids["fake-1"])
    args["transport"].registration = replace(args["transport"].registration, slot_file_ids=ids)
    result = deliver_export(**args)
    assert result.delivery_state == "confirmed"
    assert (
        args["transport"].verify(args["destination"], args["generation"].key)
        == args["generation"].manifest()
    )
    files = args["transport"]._files(args["destination"], args["generation"].key)
    assert len(files) == count
    for file in files:
        assert (
            sum(
                p["gridProperties"]["rowCount"] * p["gridProperties"]["columnCount"]
                for p in api.grids[file["id"]].values()
            )
            <= GoogleSheetsTransport.MAX_CELLS
        )
    # A later part cannot be missing while the directory claims a complete generation.
    del api.files_data[files[-1]["id"]]
    from kvk.services.new_source_delivery_service import DestinationSetupRequired

    with pytest.raises(DestinationSetupRequired):
        args["transport"].verify(args["destination"], args["generation"].key)


def test_registered_google_replacement_never_deletes_last_sheet():
    args, _, api = google_delivery()
    assert deliver_export(**args).delivery_state == "confirmed"
    for path, method, payload in api.calls:
        if method == "batchUpdate":
            kinds = [next(iter(req)) for req in payload["body"]["requests"]]
            assert kinds.index("addSheet") < kinds.index("deleteSheet")


def test_google_credentials_factory_sets_real_http_timeout_without_cache(monkeypatch):
    from types import SimpleNamespace

    import googleapiclient.discovery

    from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration

    clients = []

    def build(api, version, *, http, **kwargs):
        clients.append(http)
        return Mock()

    monkeypatch.setattr(googleapiclient.discovery, "build", build)
    email = "synthetic@synthetic.iam.gserviceaccount.com"
    GoogleSheetsTransport.from_credentials(
        credentials=SimpleNamespace(service_account_email=email),
        registration=SheetsRegistration(
            "index", ("slot-one", "slot-two"), "owner@example.test", email
        ),
        reuse_guard=lambda *args: False,
        protected_file_ids=(),
        timeout=17,
    )
    assert len(clients) == 2
    for client in clients:
        assert client.http.timeout == 17
        assert client.http.cache is None


def google_http_error(status, message="private cell secret must not be logged"):
    from googleapiclient.errors import HttpError
    from httplib2 import Response

    return HttpError(
        Response({"status": str(status)}), json.dumps({"error": {"message": message}}).encode()
    )


def test_terminal_google_rejection_is_diagnostic_and_resumes_bound_blank_slot():
    args, repo, api = google_delivery()
    original = api.execute
    rejected = []

    def execute(path, method, payload, retries):
        if method == "batchUpdate" and not rejected:
            rejected.append(True)
            raise google_http_error(
                400, "Sorry, it is not possible to delete all non-frozen rows. private cell secret"
            )
        return original(path, method, payload, retries)

    api.execute = execute
    outcome = deliver_export(**args)
    assert outcome.delivery_state == "failed"
    assert outcome.diagnostic == {
        "operation": "sheets.spreadsheets.batchUpdate",
        "status": 400,
        "reason": "frozen_rows_shrink",
    }
    assert "private cell secret" not in outcome.receipt
    assert api.files_data["fake-1"]["appProperties"]["k98Stage"] == "preparing"
    assert deliver_export(**args).delivery_state == "confirmed"


def test_public_viewer_is_revoked_for_staging_and_granted_only_after_verification():
    args, repo, api = google_delivery()
    t = args["transport"]
    t.registration = replace(t.registration, audience="public_viewer")
    api.files_data["fake-1"]["permissions"].append(
        dict(id="old-public", type="anyone", role="reader", allowFileDiscovery=False)
    )
    result = deliver_export(**args)
    assert result.delivery_state == "confirmed"
    assert json.loads(result.receipt)["audience"] == "public_viewer"
    calls = api.calls
    revoke = next(i for i, c in enumerate(calls) if c[0] == "/permissions" and c[1] == "delete")
    write = next(
        i for i, c in enumerate(calls) if c[0] == "/spreadsheets/values" and c[1] == "update"
    )
    verify = next(i for i, c in enumerate(calls) if c[1] == "batchGet")
    grant = next(i for i, c in enumerate(calls) if c[0] == "/permissions" and c[1] == "create")
    assert revoke < write < verify < grant
    for fid in ("fake-1", "fake-index"):
        assert [p for p in api.files_data[fid]["permissions"] if p["type"] == "anyone"] == [
            dict(id="public-reader", type="anyone", role="reader", allowFileDiscovery=False)
        ]
    assert (
        t.reconcile(args["destination"], repo.read_receipt(args["selection"], args["destination"]))[
            0
        ]
        == "confirmed"
    )
    assert len([c for c in calls if c[1] == "batchGet"]) < 12


def test_public_permission_timeout_keeps_publication_uncertain_and_never_retries():
    args, repo, api = google_delivery()
    args["transport"].registration = replace(
        args["transport"].registration, audience="public_viewer"
    )
    original = api.execute

    def execute(path, method, payload, retries):
        result = original(path, method, payload, retries)
        if path == "/permissions" and method == "create":
            raise TimeoutError("permission response lost")
        return result

    api.execute = execute
    outcome = deliver_export(**args)
    assert outcome.export_complete and outcome.delivery_state == "uncertain"
    assert json.loads(outcome.receipt)["phase"] == "publish_uncertain"
    assert ("fake-index", "Sheet1") not in api.values or not api.values[("fake-index", "Sheet1")]
    with pytest.raises(SourceConflict, match="reconciliation"):
        deliver_export(**args)


@pytest.mark.parametrize(
    "permission",
    [
        dict(type="anyone", role="writer", allowFileDiscovery=False),
        dict(type="anyone", role="reader", allowFileDiscovery=True),
        dict(type="domain", role="reader"),
    ],
)
def test_public_mode_rejects_editor_searchable_or_domain_audiences(permission):
    args, _, api = google_delivery()
    args["transport"].registration = replace(
        args["transport"].registration, audience="public_viewer"
    )
    api.files_data["fake-1"]["permissions"].append(permission)
    assert deliver_export(**args).setup_required
    assert not any(c[1] in ("update", "batchUpdate", "create", "delete") for c in api.calls)


def test_safe_read_retries_are_bounded_and_mutation_rejection_is_not_retried():
    from types import SimpleNamespace

    from kvk.services.new_source_delivery_service import RemoteRequestRejected

    args, _, _ = google_delivery()
    t = args["transport"]
    t._request_pacer = Mock()
    t._retry_sleep = Mock()
    read = SimpleNamespace(
        method="GET",
        methodId="sheets.spreadsheets.values.batchGet",
        execute=Mock(side_effect=[google_http_error(429), google_http_error(503), {"ok": True}]),
    )
    assert t._execute(read) == {"ok": True}
    assert read.execute.call_count == 3 and t._retry_sleep.call_count == 2
    mutation = SimpleNamespace(
        method="POST",
        methodId="sheets.spreadsheets.batchUpdate",
        execute=Mock(side_effect=google_http_error(429)),
    )
    with pytest.raises(RemoteRequestRejected):
        t._mutate(mutation)
    assert mutation.execute.call_count == 1


@pytest.mark.parametrize(
    "phase,state,complete,allowed",
    [
        ("private_incomplete", "uncertain", False, True),
        ("private_started", "claimed", False, True),
        ("publication_pending", "claimed", True, False),
        ("publish_uncertain", "uncertain", True, False),
        ("private_incomplete", "claimed", False, False),
    ],
)
def test_dal_private_recovery_fences_and_quarantines_without_reclaiming_publication(
    monkeypatch, phase, state, complete, allowed
):
    from contextlib import nullcontext

    import kvk.dal.new_source_delivery_dal as dal

    selection, _ = export_input()
    cursor = Mock()
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    monkeypatch.setattr(dal, "_selected", lambda *a: None)
    row = dict(
        PublicationID=selection.publication_id,
        DeliveryState=state,
        Fence=3,
        Receipt=json.dumps(
            dict(
                export_key="a" * 64,
                selection_version=selection.selection_version,
                publication_id=selection.publication_id,
                phase=phase,
                export_complete=complete,
                attempt_slots=["old-one", "old-two"],
            )
        ),
    )
    monkeypatch.setattr(dal, "rows", lambda _: [row])
    repo = DeliveryRepository(Mock())
    if not allowed:
        with pytest.raises(SourceConflict, match="private"):
            repo.recover_private_claim(
                selection,
                Destination("sheets", "index"),
                "a" * 64,
                ("old-one", "old-two"),
                ("new-one", "new-two"),
            )
        assert not any("UPDATE" in c.args[0] for c in cursor.execute.call_args_list)
        return
    claim = repo.recover_private_claim(
        selection,
        Destination("sheets", "index"),
        "a" * 64,
        ("old-one", "old-two"),
        ("new-one", "new-two"),
    )
    assert claim.fence == 4
    assert json.loads(claim.receipt)["quarantined_slots"] == ["old-one", "old-two"]
    with pytest.raises(SourceConflict, match="disjoint"):
        repo.recover_private_claim(
            selection,
            Destination("sheets", "index"),
            "a" * 64,
            ("old-one", "old-two"),
            ("old-one", "new-two"),
        )


def test_quarantine_is_preserved_by_finish_and_blocks_future_slot_registration(monkeypatch):
    from contextlib import nullcontext

    import kvk.dal.new_source_delivery_dal as dal

    selection, _ = export_input()
    previous = dict(
        export_key="a" * 64,
        selection_version=selection.selection_version,
        quarantined_slots=["old-one"],
        attempt_slots=["new-one", "new-two"],
    )
    claim = DeliveryClaim(
        selection, Destination("sheets", "index"), "owner", 4, "claimed", json.dumps(previous)
    )
    cursor = Mock()
    repo = DeliveryRepository(Mock())
    monkeypatch.setattr(dal, "transaction", lambda _: nullcontext(cursor))
    monkeypatch.setattr(repo, "_check_claim", lambda *a: dict(Receipt=claim.receipt))
    result = repo.finish(
        claim,
        "confirmed",
        json.dumps(dict(export_key="a" * 64, selection_version=selection.selection_version)),
    )
    assert json.loads(result)["quarantined_slots"] == ["old-one"]
    args, _, api = google_delivery()
    args["transport"].quarantined = frozenset(["fake-1"])
    with pytest.raises(SourceConflict, match="quarantined"):
        args["transport"].ensure_private(
            args["destination"], args["generation"].key, args["generation"].manifest()
        )
    assert not api.calls
