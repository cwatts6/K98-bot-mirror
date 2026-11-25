"""Retained capture continuation: real evidence authentication and no replay."""

from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest
from test_poststate_capture_packet import qualification as qualification


@pytest.fixture
def retained(qualification, monkeypatch):
    raw = os.environ.get("K98_P02_CAPTURED_RECEIPTS")
    if not raw:
        pytest.skip("Explicit retained native capture directory required")
    root = Path(raw).parent
    for name, stamp in (
        ("poststate_index_diagnostic", "20261123163556234"),
        ("poststate_installed", "20261123160455336"),
        ("poststate_continue", "20261123150616134"),
    ):
        monkeypatch.setattr(
            importlib.import_module(name), "PRIOR", root / ("poststate-capture-" + stamp)
        )
    module = importlib.import_module("poststate_captured")
    diagnostic = root / "poststate-capture-20261123170039650"
    monkeypatch.setattr(module, "DIAGNOSTIC", diagnostic)
    prior = root / "poststate-capture-20261123163556234"
    with zipfile.ZipFile(prior / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
    manifest["continuation"] = module.TOKEN
    value = module.authenticate(prior, manifest)
    return SimpleNamespace(
        module=module, value=value, manifest=manifest, packet=prior, diagnostic=diagnostic
    )


def test_real_failed_diagnostic_and_completed_capture_authenticate_without_replay(retained):
    assert retained.value["capture"]["preparation_id"] == "7d96e6d1-3976-49aa-adaf-8b74ec6542e5"
    assert retained.value["published"]["output"]
    assert retained.value["diagnostic"]["integration/receipt.json"]["outcome"] == "failed"


@pytest.mark.parametrize(
    "damage", ["custody", "child", "locks", "schema", "business", "capture", "before"]
)
def test_changed_or_uncertain_diagnostic_cannot_authorize_successors(retained, damage):
    values = deepcopy(retained.value["diagnostic"])
    record = values["integration/receipt.json"]
    before = values["index-diagnostic-before.json"]
    launch = values["integration.launch.json"]
    if damage == "custody":
        record["physical_custody_retained"] = True
    elif damage == "child":
        launch["settled"] = False
    elif damage == "locks":
        record["probe"][0]["own_application_locks"] = 1
    elif damage == "schema":
        record["probe"][0]["schema_result"] = -1
    elif damage == "business":
        record["business_operations"] = 1
    elif damage == "capture":
        record["retained_snapshot"]["snapshot"]["sha256"] = "0" * 64
    else:
        before["indexes"] = [{"name": "advanced"}]
    with pytest.raises(ValueError):
        retained.module.require_diagnostic_stop(
            record, launch, before, retained.value["record"], retained.value["capture"]
        )


@pytest.mark.parametrize(
    "damage",
    ["none", "transaction", "generation", "capture", "owner", "index", "publication", "missing"],
)
def test_live_state_requires_standalone_zero_and_complete_durable_equality(retained, damage):
    expected = retained.value["diagnostic"]["index-diagnostic-before.json"]
    actual = deepcopy(expected)
    actual["session"][0].update(session_id=99, transaction_state=0)
    if damage == "transaction":
        actual["session"][0]["transaction_state"] = 1
    elif damage == "generation":
        actual["sequence"][0]["generation"] += 1
    elif damage == "capture":
        actual["preparations"][0]["SpoolHash"] = "0" * 64
    elif damage == "owner":
        actual["resources"][0]["OwnerID"] = "someone"
    elif damage == "index":
        actual["indexes"] = [{"name": "unexpected"}]
    elif damage == "publication":
        actual["incarnation"][0]["object_id"] += 1
    elif damage == "missing":
        actual.pop("work")
    if damage == "none":
        retained.module.require_live_state(actual, expected)
    else:
        with pytest.raises(ValueError):
            retained.module.require_live_state(actual, expected)


@pytest.mark.parametrize("fail_first", [False, True])
def test_resume_runs_only_unstarted_indexes_and_reports(
    retained, monkeypatch, tmp_path, fail_first
):
    cases = importlib.import_module("poststate_report_cases")
    work = importlib.import_module("cost_workload")
    monkeypatch.setattr(cases, "verify_old_captures", lambda *args: None)
    monkeypatch.setattr(work, "runtime", lambda *args: None)
    monkeypatch.setattr(work, "contracts", lambda *args: {"bound": True})
    monkeypatch.setattr(retained.module, "authenticate", lambda *args: retained.value)
    events = []

    def add(record, save, count):
        events.append(("index", count))
        if fail_first:
            raise ValueError("original index failure")

    def capture(packet, manifest, bound, connections, record, save, previous):
        events.append(("capture", len(previous)))
        value = dict(previous[0], preparation_id="new-" + str(len(previous)))
        return value

    monkeypatch.setattr(cases, "add_index", add)
    monkeypatch.setattr(cases, "index_state", lambda record, save, count: [count])
    monkeypatch.setattr(cases, "report_capture", capture)
    publisher = importlib.import_module("poststate_publisher")
    monkeypatch.setattr(publisher, "run", lambda *args: pytest.fail("Publisher must not replay"))
    record = {}
    if fail_first:
        with pytest.raises(ValueError, match="original index"):
            cases.run(tmp_path, retained.manifest, record, lambda: None, None)
        assert events == [("index", 1)]
        assert not (tmp_path / "chain-captures.json").exists()
    else:
        cases.run(tmp_path, retained.manifest, record, lambda: None, None)
        assert events == [
            ("index", 1),
            ("capture", 1),
            ("index", 2),
            ("capture", 2),
            ("capture", 3),
        ]
        assert record["actual_report_writes"] == 3
        assert record["actual_legacy_publications"] == 0
        assert record["captures"][0] == retained.value["capture"]
        assert len(record["captures"]) == 4
        assert record["zero_index_capture_replayed"] is False


def test_transaction_state_is_captured_before_metadata_and_after_rollback(qualification):
    diagnostic = importlib.import_module("poststate_index_diagnostic")
    assert diagnostic.SESSION.index("@state int=XACT_STATE()") < diagnostic.SESSION.index("DB_ID()")
    assert diagnostic.PROBE.index("@exit_state int=XACT_STATE()") > diagnostic.PROBE.index(
        "END CATCH;"
    )
    assert "@exit_state AS exit_state" in diagnostic.PROBE
    assert "XACT_STATE() AS exit_state" not in diagnostic.PROBE
