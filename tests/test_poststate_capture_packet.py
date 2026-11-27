"""Offline safety and settlement checks for the finite isolated DB27 capture chain."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def qualification(monkeypatch):
    source = os.environ.get("K98_OBSERVER_SQL_SOURCE")
    if not source:
        pytest.skip("Explicit SQL qualification source is required")
    monkeypatch.syspath_prepend(str(Path(source) / "qualification/p02_observer"))
    chain = importlib.import_module("poststate_chain")
    cases = importlib.import_module("poststate_cases")
    owner = importlib.import_module("poststate_owner")
    physical = importlib.import_module("fresh_business_owner")
    monkeypatch.setattr(owner, "NAMES", ())
    monkeypatch.setattr(owner, "GUIDS", {18: "9dc35927-02a8-4c11-bc05-210381eca28d"})
    monkeypatch.setattr(physical, "HELD", [])
    return SimpleNamespace(chain=chain, cases=cases, owner=owner, physical=physical)


def source_rows():
    return [dict(scans=2, raw_rows=20, weights=1, windows=3, baselines=10, admitted_season=1)]


@pytest.mark.parametrize(
    "field,value",
    [
        ("scans", 0),
        ("raw_rows", 1000001),
        ("weights", True),
        ("windows", -1),
        ("baselines", None),
        ("admitted_season", 0),
        ("admitted_season", 2),
    ],
)
def test_missing_or_ambiguous_genuine_source_refuses(qualification, field, value):
    rows = source_rows()
    qualification.cases.require_kvk_source(rows)
    rows[0][field] = value
    with pytest.raises(ValueError):
        qualification.cases.require_kvk_source(rows)


def bind(qualification, tmp_path, *, number=27):
    stamp = "20261123123456789"
    manifest = dict(
        guest_directory="Q:/P02Observer/" + stamp,
        purpose="p02-poststate-capture-chain",
        production_eligible=False,
        vm_id="2ac1b401-7076-4965-af71-de36ee0f9f9c",
        databases=["K98_P02CaptureChain_" + stamp],
        data_directory="T:/P02Capture_" + stamp,
    )
    item = dict(
        name=manifest["databases"][0],
        database_id=number,
        database_guid="e2e29e76-b0ba-4a08-b099-d32a8576c280",
        family_guid="c4de892e-fd68-46e4-ab63-245e74bfc07b",
        data=manifest["data_directory"] + "/CHAIN.mdf",
        log=manifest["data_directory"] + "/CHAIN.ldf",
    )
    raw = json.dumps(dict(fixtures=[item])).encode()
    (tmp_path / "restore-bindings.json").write_bytes(raw)
    return manifest, item, hashlib.sha256(raw).hexdigest()


def test_restore_binding_is_exact_and_one_use(qualification, tmp_path):
    manifest, item, digest = bind(qualification, tmp_path)
    with pytest.raises(ValueError):
        qualification.owner.bind_fixture(tmp_path, manifest, "0" * 64)
    assert qualification.owner.bind_fixture(tmp_path, manifest, digest) == item
    with pytest.raises(ValueError, match="only once"):
        qualification.owner.bind_fixture(tmp_path, manifest, digest)


@pytest.mark.parametrize("number", [16, 18, 24, 25, 26, 28])
def test_existing_or_unplanned_database_binding_refused(qualification, tmp_path, number):
    manifest, _, digest = bind(qualification, tmp_path, number=number)
    with pytest.raises(ValueError):
        qualification.owner.bind_fixture(tmp_path, manifest, digest)
    assert qualification.owner.NAMES == ()
    assert 27 not in qualification.owner.GUIDS


def test_name_acknowledgement_cannot_hide_other_database_changes(qualification, tmp_path):
    manifest, item, digest = bind(qualification, tmp_path)
    qualification.owner.bind_fixture(tmp_path, manifest, digest)
    rows = [
        dict(
            database_id=18,
            database_guid=qualification.owner.GUIDS[18],
            name="preserved",
            create_date="2026-11-23T12:00:00",
            user_access_desc="MULTI_USER",
        ),
        dict(
            database_id=27,
            database_guid=item["database_guid"],
            name=item["name"],
            create_date="2026-11-23T12:00:00",
            user_access_desc="RESTRICTED_USER",
        ),
    ]
    action = dict(
        database_id=27,
        kind="rename",
        acknowledged=True,
        **{
            "from": item["name"],
            "to": "ROK_TRACKER",
            "before": "2026-11-23T12:01:00",
            "after": "2026-11-23T12:01:01",
        },
    )
    after = deepcopy(rows)
    after[1].update(name="ROK_TRACKER", create_date="2026-11-23T12:01:00.500")
    assert qualification.owner.transition(rows, after, action, ["files"], ["files"]) == after
    after[0]["user_access_desc"] = "SINGLE_USER"
    with pytest.raises(ValueError, match="outside"):
        qualification.owner.transition(rows, after, action, ["files"], ["files"])
    with pytest.raises(ValueError, match="Physical"):
        qualification.owner.transition(rows, rows, action, ["files"], ["replacement"])


@pytest.mark.parametrize("alteration", ["descending", "extra", "disabled", "wrong_column"])
def test_index_readback_refuses_nonpermitted_shape_before_mutation(
    qualification, monkeypatch, alteration
):
    rows = [
        dict(
            name=qualification.cases.INDEX_NAMES[0],
            type=2,
            is_unique=False,
            is_disabled=False,
            has_filter=False,
            column_name="Gov_ID",
            key_ordinal=1,
            is_included_column=False,
            is_descending_key=False,
        )
    ]
    if alteration == "descending":
        rows[0]["is_descending_key"] = True
    elif alteration == "extra":
        rows.append(dict(rows[0], name="unreviewed"))
    elif alteration == "disabled":
        rows[0]["is_disabled"] = True
    else:
        rows[0]["column_name"] = "GovernorID"
    commands = []

    @contextmanager
    def owned(*args, **kwargs):
        def read(sql):
            commands.append(sql)
            return rows if sql == qualification.cases.INDEXES else []

        yield SimpleNamespace(read=read)

    monkeypatch.setattr(qualification.owner, "owned", owned)
    state = importlib.import_module("fresh_business_state")
    monkeypatch.setattr(state, "require_identity", lambda *args: None)
    with pytest.raises(ValueError, match="index state"):
        qualification.cases.add_index({}, lambda: None, 2)
    assert not any("CREATE NONCLUSTERED INDEX" in sql for sql in commands)


@pytest.mark.parametrize("running", [False, True])
def test_failed_or_unsettled_child_is_never_replayed(qualification, monkeypatch, tmp_path, running):
    calls = []

    class Child:
        pid = 12345
        returncode = None if running else 1

        def poll(self):
            return self.returncode

        def wait(self):
            return self.returncode

    child = Child()

    def launch(*args, **kwargs):
        calls.append(args)
        return child

    monkeypatch.setattr(qualification.chain.subprocess, "Popen", launch)
    clock = iter([0.0, 1000.0, 1001.0])
    monkeypatch.setattr(qualification.chain.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(qualification.chain.time, "sleep", lambda _: None)
    root = tmp_path / "chain-workload"
    root.mkdir()
    raw = json.dumps(
        dict(
            outcome="failed",
            first_failure={"stage": "original failure"},
            cleanup_failures=[],
            physical_custody_retained=False,
            credential_environment_cleared=True,
        )
    ).encode()
    (root / "receipt.json").write_bytes(raw)
    record = dict(children=[])
    with pytest.raises((ValueError, TimeoutError)):
        qualification.chain.launch(tmp_path, {}, "a" * 64, "workload", record, lambda: None)
    assert len(calls) == 1
    assert (root / "receipt.json").read_bytes() == raw
    assert record["children"][0]["acknowledged"] is False
    if running:
        assert qualification.physical.HELD == [child]
        assert all(not h.closed for h in child._p02_output_handles)
        for handle in child._p02_output_handles:
            handle.close()
    else:
        assert qualification.physical.HELD == []
        assert record["children"][0]["receipt_sha256"] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("entry", ["role", "parent", "preservation"])
@pytest.mark.parametrize("failed_write", ["save", "receipt"])
@pytest.mark.parametrize("safe_to_exit", [False, True])
def test_receipt_failure_cannot_release_uncertain_physical_owner(
    qualification, monkeypatch, tmp_path, entry, failed_write, safe_to_exit
):
    """Exercise real finalizers: output failure must not escape retained custody."""
    from contextlib import nullcontext
    import sys

    import cost_execution
    import independent_readers
    import poststate_preservation
    import producer_runtime
    import pyodbc
    import release_boundary

    class RetainedForOperator(BaseException):
        pass

    packet = tmp_path / "20261123123456789"
    packet.mkdir()
    manifest = dict(
        capture_route="all_kvk",
        purpose="p02-poststate-capture-chain",
        production_eligible=False,
        vm_id="2ac1b401-7076-4965-af71-de36ee0f9f9c",
        guest_directory=str(packet),
        databases=["K98_P02CaptureChain_" + packet.name],
        files={},
    )
    (packet / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    original = ValueError("original body failure")
    output_error = OSError("receipt storage failed")
    held_owner = object()
    qualification.physical.HELD[:] = [] if safe_to_exit else [held_owner]
    records = []
    events = []

    def fail_body(*args, **kwargs):
        raise original

    def writer(root, record):
        records.append(record)

        def save():
            events.append("save")
            if failed_write == "save":
                raise output_error

        return save

    def write_new(path, value):
        events.append(path.name)
        if path.name == "receipt.json" and failed_write == "receipt":
            raise output_error
        path.write_text(json.dumps(value), encoding="utf-8")

    def hold(seconds):
        events.append("hold")
        assert seconds == 1
        assert qualification.physical.HELD == [held_owner]
        raise RetainedForOperator()

    monkeypatch.setattr(cost_execution, "writer", writer)
    monkeypatch.setattr(independent_readers, "write_new", write_new)
    monkeypatch.setattr(qualification.chain.time, "sleep", hold)
    monkeypatch.setattr(qualification.owner, "bind_fixture", lambda *args: {})
    monkeypatch.setattr(poststate_preservation, "context", fail_body)
    monkeypatch.setattr(
        pyodbc, "connect", lambda *args, **kwargs: pytest.fail("Native SQL is forbidden")
    )
    monkeypatch.setattr(pyodbc, "pooling", False)

    if entry == "role":
        monkeypatch.setattr(
            producer_runtime, "application_credentials", lambda *args: nullcontext()
        )
        monkeypatch.setattr(
            producer_runtime,
            "Connections",
            lambda: SimpleNamespace(
                finish=lambda: dict(safe_to_exit=safe_to_exit, all_closed_by_callers=safe_to_exit)
            ),
        )
        monkeypatch.setattr(qualification.cases, "consume", fail_body)
        call = lambda: qualification.chain.role(packet, manifest, "a" * 64, "consumer")
    elif entry == "parent":
        call = lambda: qualification.chain.parent(packet, manifest, "a" * 64)
    else:
        monkeypatch.setattr(
            poststate_preservation,
            "__file__",
            str(packet / "qualification/p02_observer/poststate_preservation.py"),
        )
        monkeypatch.setenv("COMPUTERNAME", "MINI_AMD")
        monkeypatch.setattr(sys, "argv", ["poststate_preservation.py", "before"])
        monkeypatch.setattr(release_boundary, "native_paths", lambda *args: None)
        call = poststate_preservation.main

    with pytest.raises(OSError if safe_to_exit else RetainedForOperator) as caught:
        call()
    assert records[0]["first_failure"]["detail"] == str(original)
    assert records[0]["outcome"] == "failed"
    assert records[0]["physical_custody_retained"] is (not safe_to_exit)
    if safe_to_exit:
        assert caught.value is output_error
        assert "hold" not in events
    else:
        assert events[-1] == "hold"
        assert qualification.physical.HELD == [held_owner]
    assert events.count("save") == 1
    assert events.count("receipt.json") == (1 if failed_write == "receipt" else 0)
