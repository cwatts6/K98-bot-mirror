"""Retain the real zero-index capture and diagnose guards without replay."""

from copy import deepcopy
import importlib
import json
import os
from pathlib import Path

import pytest
from test_poststate_capture_packet import qualification as qualification


@pytest.fixture
def diagnostic(qualification):
    return importlib.import_module("poststate_index_diagnostic")


@pytest.fixture
def captured():
    value = os.environ.get("K98_P02_CAPTURED_RECEIPTS")
    if not value:
        pytest.skip("Exact completed capture evidence directory required")
    p = Path(value)
    return [
        json.loads((p / name).read_bytes())
        for name in (
            "integration/receipt.json",
            "integration.launch.json",
            "chain-workload/receipt.json",
        )
    ]


def test_actual_completed_capture_is_retained(diagnostic, captured):
    diagnostic.require_stop(*captured)


@pytest.mark.parametrize(
    "damage",
    [
        "custody",
        "child",
        "coordinator",
        "capture",
        "publisher",
        "index",
        "cleanup",
        "launch",
    ],
)
def test_uncertain_or_advanced_stop_refuses(diagnostic, captured, damage):
    parent, launch, worker = deepcopy(captured)
    if damage == "custody":
        parent["physical_custody_retained"] = True
    elif damage == "child":
        parent["children"][0]["settled"] = False
    elif damage == "coordinator":
        parent["coordinator"][0]["acknowledged"] = False
    elif damage == "capture":
        worker["cases"][0]["writer_closed"] = False
    elif damage == "publisher":
        worker["publication"]["response_acknowledged"] = False
    elif damage == "index":
        worker["index_actions"][0]["acknowledged"] = True
    elif damage == "cleanup":
        worker["application_cleanup"]["all_closed_by_callers"] = False
    else:
        launch["receipt_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        diagnostic.require_stop(parent, launch, worker)


def settled():
    return dict(
        database_id=27,
        entry_count=0,
        entry_state=0,
        exit_count=0,
        exit_state=0,
        own_application_locks=0,
        output_session_mode="NoLock",
        schema_session_mode="NoLock",
        phase="complete",
        output_result=0,
        schema_result=0,
        output_mode="Exclusive",
        schema_mode="Exclusive",
    )


@pytest.mark.parametrize("phase", ["complete", "output", "schema"])
def test_probe_distinguishes_refusal_from_clean_completion(diagnostic, phase):
    row = settled()
    row["phase"] = phase
    if phase == "output":
        row.update(output_result=-1, schema_result=None, output_mode="NoLock", schema_mode="NoLock")
    elif phase == "schema":
        row.update(schema_result=-1, schema_mode="NoLock")
    assert diagnostic.require_probe([row]) == (phase == "complete")


@pytest.mark.parametrize(
    "key,value",
    [
        ("exit_count", 1),
        ("exit_state", -1),
        ("own_application_locks", 1),
        ("output_session_mode", "Exclusive"),
        ("schema_session_mode", "Shared"),
        ("database_id", 18),
        ("phase", "unknown"),
        ("schema_result", -1),
        ("output_mode", "NoLock"),
    ],
)
def test_unreleased_or_inconsistent_probe_refuses(diagnostic, key, value):
    row = settled()
    row[key] = value
    with pytest.raises(ValueError):
        diagnostic.require_probe([row])


@pytest.mark.parametrize("damage", ["none", "hash", "generation", "identity", "length"])
def test_full_capture_registration_remains_bound(diagnostic, captured, damage):
    capture = captured[2]["cases"][0]["capture"]
    snapshot = capture["snapshot"]
    row = dict(
        PreparationID=capture["preparation_id"],
        State="captured",
        StorageOwner=snapshot["storage_owner"],
        SpoolKey=snapshot["key"],
        SpoolBytes=snapshot["byte_count"],
        SpoolHash=snapshot["sha256"],
        GenerationJson=json.dumps(capture["generation"]),
    )
    if damage == "hash":
        row["SpoolHash"] = "0" * 64
    elif damage == "generation":
        row["GenerationJson"] = "{}"
    elif damage == "identity":
        row["PreparationID"] = "another"
    elif damage == "length":
        row["SpoolBytes"] += 1
    if damage == "none":
        diagnostic.require_capture_row(row, capture)
    else:
        with pytest.raises(ValueError):
            diagnostic.require_capture_row(row, capture)
