"""The report route cannot imply genuine legacy-KVK capture qualification."""

from copy import deepcopy
import importlib
import json
from types import SimpleNamespace

import pytest
from test_poststate_capture_packet import qualification as qualification


@pytest.fixture
def reports(qualification):
    return importlib.import_module("poststate_report_cases")


def source_rows():
    return [
        dict(
            latest_scan=1244,
            selected_kvk=16,
            end_scan=1193,
            final_scan=1193,
            publisher_source_rows=414,
            report_source_rows=410,
        )
    ]


@pytest.mark.parametrize(
    "field,value",
    [
        ("latest_scan", 1243),
        ("selected_kvk", 17),
        ("final_scan", 1250),
        ("end_scan", 1244),
        ("final_scan", 1244),
        ("publisher_source_rows", 0),
        ("report_source_rows", 0),
        ("report_source_rows", 250001),
        ("report_source_rows", True),
        ("selected_kvk", None),
    ],
)
def test_report_prerequisite_refuses_wrong_or_missing_genuine_source(reports, field, value):
    rows = source_rows()
    reports.require_report_source(rows)
    rows[0][field] = value
    with pytest.raises(ValueError):
        reports.require_report_source(rows)


@pytest.mark.parametrize("size", [0, 1000001])
def test_zero_legacy_input_does_not_block_report_or_become_legacy_acceptance(reports, size):
    calls = []

    def read(sql):
        calls.append(sql)
        if sql == reports.REPORT_SOURCE:
            return source_rows()
        if sql == reports.LEGACY_SIZE:
            return [dict(rows=size)]
        if sql == reports.LEGACY_CENSUS:
            return [dict(KVK_NO=16, scans=0, raw_rows=0, SourceKey=None)]
        pytest.fail("Unexpected SQL")

    result = reports.prerequisites(SimpleNamespace(read=read), {}, lambda: None)
    assert result["report_source"] == source_rows()
    assert "qualified" not in result
    assert (reports.LEGACY_CENSUS in calls) is (size <= 1000000)
    assert result["legacy_census_status"] == (
        "read_only_counts_not_admission_or_capture"
        if size == 0
        else "not_read_source_exceeds_bounded_inventory"
    )


@pytest.mark.parametrize("route", [None, "", "snapshot_report_v1", "unknown"])
def test_missing_or_ambiguous_capture_route_refuses(qualification, route):
    with pytest.raises(ValueError, match="Explicit"):
        qualification.chain.capture_cases(dict(capture_route=route))


def capture(number):
    return dict(
        preparation_id=str(number),
        consumer="scan_data",
        row_count=2000,
        section_count=2,
        sections_sha256="a" * 64,
    )


@pytest.mark.parametrize("damage", ["wrong_kind", "empty", "duplicate", "different_output"])
def test_report_capture_requires_distinct_equal_nonempty_actual_output(
    reports, monkeypatch, damage
):
    import cost_workload

    previous = [capture(1)]
    actual = capture(2)
    if damage == "wrong_kind":
        actual["consumer"] = "all_kvk"
    elif damage == "empty":
        actual["row_count"] = 0
    elif damage == "duplicate":
        actual["preparation_id"] = "1"
    else:
        actual["sections_sha256"] = "b" * 64
    writes = []
    monkeypatch.setattr(
        cost_workload,
        "report",
        lambda packet, manifest, bound, connections, record, save, mode: record.update(
            preparation_id="2", writer_closed=True
        ),
    )
    monkeypatch.setattr(cost_workload, "runtime", lambda *a: object())
    monkeypatch.setattr(reports, "capture_facts", lambda *a: actual)
    monkeypatch.setattr(reports, "verify_old_captures", lambda *a: writes.append("old_checked"))
    with pytest.raises(ValueError):
        reports.report_capture(None, {}, {}, None, {}, lambda: writes.append("saved"), previous)
    assert writes == []
    assert previous == [capture(1)]


def test_report_capture_preserves_previous_and_records_no_legacy_credit(reports, monkeypatch):
    import cost_workload

    events = []
    monkeypatch.setattr(
        cost_workload,
        "report",
        lambda packet, manifest, bound, connections, record, save, mode: record.update(
            preparation_id="2", writer_closed=True
        ),
    )
    monkeypatch.setattr(cost_workload, "runtime", lambda *a: object())
    monkeypatch.setattr(reports, "capture_facts", lambda *a: capture(2))
    monkeypatch.setattr(
        reports, "verify_old_captures", lambda rt, old: events.append(deepcopy(old))
    )
    record = {}
    result = reports.report_capture(None, {}, {}, None, record, lambda: None, [capture(1)])
    assert result == capture(2) and events == [[capture(1)]]
    assert "actual_kvk_recomputes" not in record


@pytest.mark.parametrize("damage", ["wrong_kind", "empty", "duplicate", "different_output"])
def test_independent_consumer_refuses_substitute_capture_before_connecting(
    reports, monkeypatch, tmp_path, damage
):
    import cost_workload

    captures = [capture(i) for i in range(4)]
    if damage == "wrong_kind":
        captures[0]["consumer"] = "all_kvk"
    elif damage == "empty":
        captures[0]["row_count"] = 0
    elif damage == "duplicate":
        captures[0]["preparation_id"] = captures[1]["preparation_id"]
    else:
        captures[0]["sections_sha256"] = "b" * 64
    (tmp_path / "chain-captures.json").write_text(json.dumps(captures))
    monkeypatch.setattr(cost_workload, "contracts", lambda *a: pytest.fail("SQL must not start"))
    with pytest.raises(ValueError, match="four distinct"):
        reports.consume(tmp_path, {}, {}, lambda: None, None)


@pytest.mark.parametrize("route", ["player_report", "all_kvk"])
def test_isolated_bootstrap_validates_manifest_before_importing_routes(qualification, route):
    """Exercise the real -I -S loader, not pytest's preloaded module search path."""
    import subprocess
    import sys

    program = r"""
import hashlib, json, os, pathlib, runpy, sys, tempfile
module = runpy.run_path(sys.argv[1])
os.environ["COMPUTERNAME"] = "MINI_AMD"
with tempfile.TemporaryDirectory(prefix="p02-bootstrap-") as root:
    packet = pathlib.Path(root) / "20261123123456789"
    packet.mkdir()
    member = packet / "sealed.txt"
    member.write_bytes(b"sealed")
    manifest = dict(
        capture_route=sys.argv[2], purpose="p02-poststate-capture-chain",
        production_eligible=False, vm_id="2ac1b401-7076-4965-af71-de36ee0f9f9c",
        guest_directory=str(packet), databases=["K98_P02CaptureChain_" + packet.name],
        new_disk_bytes=192*1024**3, drive_letter="T",
        data_directory="T:\\P02Capture_" + packet.name,
        files={"sealed.txt": hashlib.sha256(member.read_bytes()).hexdigest()},
    )
    module["require_packet"](packet, manifest)
    assert "poststate_report_cases" not in sys.modules
    assert "poststate_cases" not in sys.modules
    assert "pyodbc" not in sys.modules
    member.write_bytes(b"changed")
    try:
        module["require_packet"](packet, manifest)
    except ValueError as error:
        assert "Sealed capture-chain member differs" in str(error)
    else:
        raise AssertionError("Changed member accepted")
print("isolated_manifest_verified_without_route_or_sql_import")
"""
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", program, qualification.chain.__file__, route],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "isolated_manifest_verified_without_route_or_sql_import"


def test_completed_season_final_scan_differs_from_latest_publisher_input(reports):
    rows = source_rows()
    reports.require_report_source(rows)
    assert rows[0]["latest_scan"] > rows[0]["final_scan"]
    assert rows[0]["end_scan"] == rows[0]["final_scan"] == 1193


@pytest.mark.parametrize("damage", ["final_scan", "missing_source", "wrong_type", "legacy_size"])
def test_prerequisite_failure_retains_actual_values_before_refusal(reports, damage):
    rows = source_rows()
    if damage == "final_scan":
        rows[0]["final_scan"] = 1244
    elif damage == "missing_source":
        rows[0]["report_source_rows"] = 0
    elif damage == "wrong_type":
        rows[0]["final_scan"] = 1193.0
    calls = []
    record = {}
    saved = []

    def read(sql):
        calls.append(sql)
        if sql == reports.REPORT_SOURCE:
            return rows
        if sql == reports.LEGACY_SIZE and damage == "legacy_size":
            return [dict(rows=None)]
        pytest.fail("Failure must stop before any later query")

    with pytest.raises(ValueError):
        reports.prerequisites(
            SimpleNamespace(read=read), record, lambda: saved.append(deepcopy(record))
        )
    assert saved[0]["source_prerequisites"]["report_source"] == rows
    assert saved[0]["source_prerequisites"]["report_source_types"][0]["final_scan"] == (
        "float" if damage == "wrong_type" else "int"
    )
    assert reports.LEGACY_CENSUS not in calls
    if damage == "legacy_size":
        assert saved[-1]["source_prerequisites"]["legacy_size"] == [dict(rows=None)]
    else:
        assert calls == [reports.REPORT_SOURCE]
