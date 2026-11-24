"""Retained capture setup is authenticated; completed storage/backups never replay."""

from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_poststate_capture_packet import qualification as qualification


@pytest.fixture
def continuation(qualification):
    return importlib.import_module("poststate_continue")


@pytest.fixture
def retained():
    path = os.environ.get("K98_P02_CAPTURE_RECEIPTS")
    if not path:
        pytest.skip("Explicit retained native capture receipt directory is required")
    root = Path(path)
    return [
        json.loads((root / name).read_text())
        for name in (
            "integration/receipt.json",
            "integration.launch.json",
            "guest-receipt.json",
            "restore-bindings.json",
        )
    ]


def test_actual_native_stop_is_eligible_without_replaying_setup(continuation, retained):
    continuation.require_setup(*retained)
    assert retained[0]["children"] == []


@pytest.mark.parametrize(
    "damage",
    [
        "unsettled",
        "custody",
        "cleanup",
        "name",
        "child",
        "preflight_launched",
        "migration",
        "backup",
        "inventory",
        "binding",
    ],
)
def test_changed_or_advanced_retained_setup_refuses(continuation, retained, damage):
    record, launch, restore, binding = deepcopy(retained)
    if damage == "unsettled":
        launch["settled"] = False
    elif damage == "custody":
        record["physical_custody_retained"] = True
    elif damage == "cleanup":
        record["cleanup_failures"] = [dict(error_type="OSError")]
    elif damage == "name":
        record["original_name_restored"] = False
    elif damage == "child":
        record["children"] = [dict(role="workload")]
    elif damage == "preflight_launched":
        record["coordinator"][1]["pid"] = 123
    elif damage == "migration":
        restore["fixtures"][0]["observer_objects"] = [dict(name="P02ObservationGeneration")]
    elif damage == "backup":
        record["new_fixture_backups"][0]["verified"] = False
    elif damage == "inventory":
        record["name_inventory_after"] = deepcopy(record["name_inventory_after"])
        record["name_inventory_after"][0]["name"] = "changed"
    elif damage == "binding":
        binding["fixtures"][0]["database_guid"] = "another"
    with pytest.raises(ValueError):
        continuation.require_setup(record, launch, restore, binding)


def test_continuation_binds_old_fixture_and_fresh_execution_directory(qualification):
    manifest = dict(
        guest_directory="Q:/P02Observer/20261123170000000",
        continuation="status-before-preflight-20261123150616134",
    )
    assert qualification.chain.fixture_stamp(manifest) == "20261123150616134"
    manifest["continuation"] = "unreviewed"
    with pytest.raises(ValueError):
        qualification.chain.fixture_stamp(manifest)


def test_coordinator_logs_do_not_collide_with_host_preflight(qualification, tmp_path, monkeypatch):
    release = importlib.import_module("poststate_release")
    monkeypatch.setattr(release, "HELD", qualification.physical.HELD)
    from services.export_observer_contract import MIGRATION_ID, PROFILE_SHA256

    record = dict(coordinator=[])
    manifest = dict(
        purpose="p02-poststate-capture-chain",
        release=dict(sql=dict(commit="a" * 40), release_id="release"),
    )
    prior = {}
    for stream in ("stdout", "stderr"):
        p = tmp_path / ("preflight." + stream + ".txt")
        p.write_bytes(b"original host preflight")
        prior[p] = p.read_bytes()
    started = []

    def spawn(args, **kwargs):
        operation = args[args.index("-Operation") + 1]
        started.append(operation)
        expected = operation in ("Apply", "Verify")
        value = dict(
            state="committed" if expected else "unstarted",
            migration_id=MIGRATION_ID,
            profile_sha256=PROFILE_SHA256,
            sql_commit="a" * 40,
        )
        if expected:
            value.update(release_id="release", observation_installation=dict(database_id=27))
        kwargs["stdout"].write(json.dumps(value).encode())
        return SimpleNamespace(
            pid=101,
            returncode=10 if operation == "Status" else 0,
            poll=lambda: 0,
            wait=lambda: None,
        )

    monkeypatch.setattr(release.subprocess, "Popen", spawn)
    for operation in ("Status", "Preflight", "Apply", "Verify"):
        release.coordinator(tmp_path, manifest, operation, record, lambda: None)
    assert started == ["Status", "Preflight", "Apply", "Verify"]
    assert all(p.read_bytes() == raw for p, raw in prior.items())
    assert len(list(tmp_path.glob("coordinator-*.txt"))) == 8
    assert qualification.physical.HELD == []


def test_existing_coordinator_log_refuses_before_process(qualification, tmp_path, monkeypatch):
    release = importlib.import_module("poststate_release")
    monkeypatch.setattr(release, "HELD", qualification.physical.HELD)
    path = tmp_path / "coordinator-Preflight.stdout.txt"
    path.write_bytes(b"first result")
    monkeypatch.setattr(release.subprocess, "Popen", lambda *a, **k: pytest.fail("No relaunch"))
    manifest = dict(
        purpose="p02-poststate-capture-chain",
        release=dict(sql=dict(commit="a" * 40), release_id="release"),
    )
    with pytest.raises(FileExistsError):
        release.coordinator(tmp_path, manifest, "Preflight", dict(coordinator=[]), lambda: None)
    assert path.read_bytes() == b"first result"
    assert qualification.physical.HELD == []
