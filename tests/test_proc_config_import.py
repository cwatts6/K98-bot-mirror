import importlib
import json
import os
from pathlib import Path

import pandas as pd
import pytest

import gsheet_module as gm
import proc_config_import as pci


def _make_df(cols, rows=0):
    # rows of None to provide header-only DataFrame if rows==0
    if rows == 0:
        return pd.DataFrame(columns=cols)
    data = [dict(zip(cols, [None] * len(cols), strict=True)) for _ in range(rows)]
    return pd.DataFrame(data)


def test_missing_config_returns_false(monkeypatch, tmp_path):
    # Simulate missing config
    monkeypatch.setattr(pci, "KVK_SHEET_ID", None)
    monkeypatch.setattr(pci, "CREDENTIALS_FILE", str(tmp_path / "no-such-file.json"))
    monkeypatch.setattr(pci, "SERVER", None)
    monkeypatch.setattr(pci, "DATABASE", None)
    monkeypatch.setattr(pci, "IMPORT_USERNAME", None)
    monkeypatch.setattr(pci, "IMPORT_PASSWORD", None)

    success, report = pci.run_proc_config_import(dry_run=True)
    assert success is False
    assert "errors" in report
    assert report["errors"], "Expected errors in report for missing config"


def test_valid_config_dry_run_with_schema_checks_succeeds(monkeypatch, tmp_path):
    cred = tmp_path / "credentials.json"
    cred.write_text('{"type": "service_account", "project_id": "test"}', encoding="utf-8")

    monkeypatch.setattr(pci, "KVK_SHEET_ID", "SHEET123")
    monkeypatch.setattr(pci, "CREDENTIALS_FILE", str(cred))
    monkeypatch.setattr(pci, "SERVER", "srv")
    monkeypatch.setattr(pci, "DATABASE", "db")
    monkeypatch.setattr(pci, "IMPORT_USERNAME", "user")
    monkeypatch.setattr(pci, "IMPORT_PASSWORD", "pass")

    proc_df = _make_df(["KVK_NO", "KVK_NAME"])
    details_df = _make_df(
        [
            "KVK_NO",
            "KVK_NAME",
            "KVK_REGISTRATION_DATE",
            "KVK_START_DATE",
            "KVK_END_DATE",
            "MATCHMAKING_SCAN",
            "KVK_END_SCAN",
            "NEXT_KVK_NO",
            "MATCHMAKING_START_DATE",
            "FIGHTING_START_DATE",
            "PASS4_START_SCAN",
        ]
    )
    weights_df = _make_df(["KVK_NO", "WeightT4X", "WeightT5Y", "WeightDeadsZ"])
    windows_df = _make_df(
        ["KVK_NO", "WindowName", "WindowSeq", "StartScanID", "EndScanID", "Notes"]
    )
    camp_df = _make_df(["KVK_NO", "Kingdom", "CampID", "CampName"])

    def fake_read(sheet, spreadsheet_id, range_name):
        if range_name.startswith("ProcConfig"):
            return proc_df
        if range_name.startswith("KVK_Details"):
            return details_df
        if range_name.startswith("KVK_DKPWeights"):
            return weights_df
        if range_name.startswith("KVK_Windows"):
            return windows_df
        if range_name.startswith("KVK_CampMap"):
            return camp_df
        return pd.DataFrame()

    monkeypatch.setattr(pci, "_read_sheet_to_df", fake_read)
    monkeypatch.setattr(pci, "_get_sheet_service", lambda: object())

    success, report = pci.run_proc_config_import(dry_run=True)
    assert success is True
    assert report.get("sheets_ok", False) is True


def test_dry_run_schema_failure_detected(monkeypatch, tmp_path):
    cred = tmp_path / "credentials.json"
    cred.write_text('{"type": "service_account", "project_id": "test"}', encoding="utf-8")

    monkeypatch.setattr(pci, "KVK_SHEET_ID", "SHEET123")
    monkeypatch.setattr(pci, "CREDENTIALS_FILE", str(cred))
    monkeypatch.setattr(pci, "SERVER", "srv")
    monkeypatch.setattr(pci, "DATABASE", "db")
    monkeypatch.setattr(pci, "IMPORT_USERNAME", "user")
    monkeypatch.setattr(pci, "IMPORT_PASSWORD", "pass")

    proc_df = _make_df(["SomeOtherColumn"])
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: proc_df if rng.startswith("ProcConfig") else pd.DataFrame(),
    )
    monkeypatch.setattr(pci, "_get_sheet_service", lambda: object())

    success, report = pci.run_proc_config_import(dry_run=True)
    assert success is False
    assert "errors" in report


def test_kvk_details_validation_failure():
    # DataFrame missing required columns should raise RuntimeError from validator
    df = pd.DataFrame(
        columns=["KVK_NO", "KVK_NAME", "KVK_REGISTRATION_DATE"]
    )  # missing many columns
    with pytest.raises(RuntimeError):
        pci._validate_kvk_details_dataframe(df)


def test_schema_read_exception_logged(monkeypatch, caplog, tmp_path):
    # Simulate read failure for the ProcConfig range and ensure dry-run returns False and logs error
    cred = tmp_path / "credentials.json"
    cred.write_text('{"type": "service_account", "project_id": "test"}', encoding="utf-8")

    monkeypatch.setattr(pci, "KVK_SHEET_ID", "SHEET123")
    monkeypatch.setattr(pci, "CREDENTIALS_FILE", str(cred))
    monkeypatch.setattr(pci, "SERVER", "srv")
    monkeypatch.setattr(pci, "DATABASE", "db")
    monkeypatch.setattr(pci, "IMPORT_USERNAME", "user")
    monkeypatch.setattr(pci, "IMPORT_PASSWORD", "pass")

    def fake_read(sheet, spreadsheet_id, range_name):
        if range_name.startswith("ProcConfig"):
            raise RuntimeError("simulated sheet read failure")
        return pd.DataFrame()

    monkeypatch.setattr(pci, "_read_sheet_to_df", fake_read)
    monkeypatch.setattr(pci, "_get_sheet_service", lambda: object())

    caplog.clear()
    caplog.set_level("ERROR")
    success, report = pci.run_proc_config_import(dry_run=True)
    assert success is False
    # Check that an error message about ProcConfig read failure was logged
    assert any("ProcConfig: failed to read sheet" in rec.getMessage() for rec in caplog.records)


def test_connection_uses_configured_odbc_driver(monkeypatch):
    """
    Verify that the connection helper uses the ODBC_DRIVER from constants.
    We patch constants._conn_import to capture its behavior and ensure it's called.
    """
    # Track whether constants._conn_import was invoked
    called = {"count": 0}

    # Mock constants._conn_import to avoid actual DB connection and track calls
    def mock_conn_import():
        called["count"] += 1

        # Return a mock connection object (we won't actually use it)
        class MockConnection:
            pass

        return MockConnection()

    # Patch constants._conn_import
    monkeypatch.setattr("proc_config_import._conn_import", mock_conn_import)

    # Call the helper
    try:
        _conn = pci._get_import_connection_with_retry()
    except Exception:
        pass  # The retry wrapper may raise if mock raises; we're just checking invocation

    # Verify constants._conn_import was called
    assert (
        called["count"] > 0
    ), "Expected constants._conn_import to be invoked by _get_import_connection_with_retry"


"""
Unit tests for Task 6: batched executemany functionality in proc_config_import.py
"""


@pytest.fixture
def mock_cursor_and_conn(monkeypatch, tmp_path):
    """Mock cursor and connection for batching tests."""
    executed_batches = []
    committed_count = [0]

    class MockCursor:
        def executemany(self, sql, rows):
            executed_batches.append({"sql": sql, "row_count": len(rows)})

    class MockConn:
        def commit(self):
            committed_count[0] += 1

    return MockCursor(), MockConn(), executed_batches, committed_count


def test_executemany_batched_empty_rows(mock_cursor_and_conn):
    """Test batching with empty row list."""
    cursor, conn, executed_batches, committed_count = mock_cursor_and_conn

    inserted = pci._executemany_batched(cursor, conn, "INSERT INTO test VALUES (?)", [])

    assert inserted == 0
    assert len(executed_batches) == 0
    assert committed_count[0] == 0


def test_executemany_batched_single_batch(mock_cursor_and_conn):
    """Test batching with rows <= batch_size (single batch)."""
    cursor, conn, executed_batches, committed_count = mock_cursor_and_conn

    rows = [(i,) for i in range(100)]  # 100 rows < default 5000
    inserted = pci._executemany_batched(
        cursor, conn, "INSERT INTO test VALUES (? )", rows, batch_size=5000
    )

    assert inserted == 100
    assert len(executed_batches) == 1
    assert executed_batches[0]["row_count"] == 100
    assert committed_count[0] == 1  # commit_per_batch=True by default


def test_executemany_batched_multiple_batches(mock_cursor_and_conn):
    """Test batching with rows > batch_size (multiple batches)."""
    cursor, conn, executed_batches, committed_count = mock_cursor_and_conn

    rows = [(i,) for i in range(12000)]  # 12000 rows with batch_size=5000 = 3 batches
    inserted = pci._executemany_batched(
        cursor, conn, "INSERT INTO test VALUES (?)", rows, batch_size=5000
    )

    assert inserted == 12000
    assert len(executed_batches) == 3
    assert executed_batches[0]["row_count"] == 5000
    assert executed_batches[1]["row_count"] == 5000
    assert executed_batches[2]["row_count"] == 2000
    assert committed_count[0] == 3  # commit per batch


def test_executemany_batched_exact_batch_size(mock_cursor_and_conn):
    """Test batching with rows exactly equal to batch_size."""
    cursor, conn, executed_batches, committed_count = mock_cursor_and_conn

    rows = [(i,) for i in range(5000)]  # exactly batch_size
    inserted = pci._executemany_batched(
        cursor, conn, "INSERT INTO test VALUES (? )", rows, batch_size=5000
    )

    assert inserted == 5000
    assert len(executed_batches) == 1  # single batch optimization
    assert executed_batches[0]["row_count"] == 5000
    assert committed_count[0] == 1


def test_executemany_batched_no_commit_per_batch(mock_cursor_and_conn):
    """Test batching with commit_per_batch=False."""
    cursor, conn, executed_batches, committed_count = mock_cursor_and_conn

    rows = [(i,) for i in range(12000)]
    inserted = pci._executemany_batched(
        cursor, conn, "INSERT INTO test VALUES (?)", rows, batch_size=5000, commit_per_batch=False
    )

    assert inserted == 12000
    assert len(executed_batches) == 3
    assert committed_count[0] == 0  # no commits


def test_executemany_batched_batch_failure(monkeypatch):
    """Test that batch failure raises exception and logs appropriately."""
    executed_count = [0]

    class FailingCursor:
        def executemany(self, sql, rows):
            executed_count[0] += 1
            if executed_count[0] == 2:  # fail on second batch
                raise Exception("Simulated batch failure")

    class MockConn:
        def commit(self):
            pass

        def rollback(self):
            pass

    cursor = FailingCursor()
    conn = MockConn()

    rows = [(i,) for i in range(12000)]

    with pytest.raises(Exception, match="Simulated batch failure"):
        pci._executemany_batched(cursor, conn, "INSERT INTO test VALUES (?)", rows, batch_size=5000)

    assert executed_count[0] == 2  # failed on second batch


def test_batch_size_environment_override(monkeypatch):
    """Test that PROC_IMPORT_BATCH_SIZE environment variable is respected."""
    monkeypatch.setenv("PROC_IMPORT_BATCH_SIZE", "1000")

    # Reload the module to pick up the env var

    importlib.reload(pci)

    assert pci.BATCH_SIZE == 1000


def test_transactional_rollback_and_manifest(monkeypatch, tmp_path):
    """
    Simulate transactional flow: staging write succeeded but later write or upsert fails.
    Ensure rollback is attempted and a manifest file is produced.
    """
    # Prepare a fake sheet service and simple dataframes
    monkeypatch.setattr(pci, "KVK_SHEET_ID", "SHEET123")
    monkeypatch.setattr(pci, "_get_sheet_service", lambda: object())

    # Create a real credentials file so validation passes
    cred_path = tmp_path / "credentials.json"
    cred_path.write_text('{"type": "service_account", "project_id": "test"}', encoding="utf-8")
    monkeypatch.setattr(pci, "CREDENTIALS_FILE", str(cred_path))

    monkeypatch.setattr(pci, "SERVER", "srv")
    monkeypatch.setattr(pci, "DATABASE", "db")
    monkeypatch.setattr(pci, "IMPORT_USERNAME", "user")
    monkeypatch.setattr(pci, "IMPORT_PASSWORD", "pass")

    proc_df = _make_df(["KVK_NO", "KVK_NAME"], rows=1)
    # Make read return proc_df for ProcConfig and empty for others; we'll simulate later writes failing
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: proc_df if rng.startswith("ProcConfig") else pd.DataFrame(),
    )

    # Mock connection & cursor via _get_import_connection_with_retry to return controllable conn
    class MockCursor:
        def __init__(self):
            self.executed = []

        def execute(self, *args, **kwargs):
            self.executed.append(args)
            # Simulate DBCC SQLPERF being called; if called, return empty fetch
            return None

        def executemany(self, sql, rows):
            pass

        def fetchall(self):
            return []

        def fetchone(self):
            return [0]

    class MockConn:
        def __init__(self):
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def cursor(self):
            return MockCursor()

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    mock_conn = MockConn()

    # Patch constants._conn_import to return our mock connection
    def fake_conn_import():
        return mock_conn

    monkeypatch.setattr("proc_config_import._conn_import", fake_conn_import)

    # Monkeypatch write_df_to_table:
    original_write = pci.write_df_to_table

    def fake_write(
        cursor,
        conn,
        df,
        table_name,
        mode="truncate",
        key_cols=None,
        batch_size=5000,
        commit_per_batch=True,
        transactional=False,
    ):
        # Pretend staging write works, but subsequent table writes raise error to force rollback
        if table_name == "dbo.ProcConfig_Staging":
            return {"table": table_name, "rows": 1, "mode": mode, "status": "ok", "error": None}
        # Simulate an error for subsequent tables
        raise Exception("simulated mid-run failure")

    monkeypatch.setattr(pci, "write_df_to_table", fake_write)

    # Run import (non-dry-run)
    try:
        success, report = pci.run_proc_config_import(dry_run=False)
    finally:
        # restore original
        monkeypatch.setattr(pci, "write_df_to_table", original_write)

    assert success is False
    assert "errors" in report
    # Because we used transactional mode, partial_commits should be empty and rollback attempted
    assert report.get("partial_commits", []) == []
    assert mock_conn.rolled_back is True
    # Manifest path should be present and file should exist
    manifest_path = report.get("manifest_path")
    assert manifest_path and os.path.exists(manifest_path)
    # Manifest should be valid JSON
    with open(manifest_path, encoding="utf-8") as mf:
        m = json.load(mf)
    assert m.get("errors")


def test_make_report_template_and_persist(tmp_path, monkeypatch):
    # Point DATA_DIR to temporary directory for safe persistence
    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))

    # Create a template report
    report = pci._make_import_report_template(dry_run=True)
    assert isinstance(report, dict)
    assert report["dry_run"] is True
    assert "start_time" in report

    # Persist the report
    persisted = pci._persist_import_report(report)
    assert persisted is not None

    p = Path(persisted)
    assert p.exists()

    # Load and validate JSON content
    with open(p, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["dry_run"] is True
    assert loaded["version"] == "proc_import_v1"


def test_set_last_import_report_sets_global_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))

    report = pci._make_import_report_template(dry_run=False)
    report["errors"].append("sample error")

    pci._set_last_import_report(report, persist=True)
    # module global should be set
    assert pci.last_import_report is not None
    assert pci.last_import_report["errors"][0] == "sample error"

    # persisted file should exist
    persisted_path = os.path.join(str(tmp_path), "last_proc_import_report.json")
    assert os.path.exists(persisted_path)
    with open(persisted_path, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["errors"][0] == "sample error"


def test_require_preflight_aborts_when_missing(monkeypatch, tmp_path):
    """
    When IMPORT_REQUIRE_PREFLIGHT=1 and log_health module is unavailable,
    the import should abort early and report an error.
    """
    # Prepare minimal valid config so _validate_import_config passes
    cred = tmp_path / "credentials.json"
    cred.write_text('{"type": "service_account", "project_id": "test"}', encoding="utf-8")

    monkeypatch.setattr(pci, "KVK_SHEET_ID", "SHEET123")
    monkeypatch.setattr(pci, "CREDENTIALS_FILE", str(cred))
    monkeypatch.setattr(pci, "SERVER", "srv")
    monkeypatch.setattr(pci, "DATABASE", "db")
    monkeypatch.setattr(pci, "IMPORT_USERNAME", "user")
    monkeypatch.setattr(pci, "IMPORT_PASSWORD", "pass")

    # Simulate log_health being unavailable
    monkeypatch.setattr(pci, "LOG_HEALTH_AVAILABLE", False)

    # Require preflight via env var
    monkeypatch.setenv("IMPORT_REQUIRE_PREFLIGHT", "1")
    # Force module to pick up env var (module-level value read at import time)
    monkeypatch.setattr(pci, "IMPORT_REQUIRE_PREFLIGHT", True)

    success, report = pci.run_proc_config_import(dry_run=False)
    assert success is False
    assert "errors" in report
    assert any(
        "preflight" in e.lower() or "log-health" in e.lower() for e in report["errors"]
    ), f"Expected preflight-related error; got: {report['errors']}"


def test_read_sheet_to_df_prefers_gm(monkeypatch):
    """If gm.get_sheet_values is available and returns rows, _read_sheet_to_df should use it."""
    rows = [["A", "B"], ["1", "2"], ["3", "4"]]

    monkeypatch.setattr(gm, "get_sheet_values", lambda ss, rng, timeout=None: rows)

    # pass sheet=None since _read_sheet_to_df will prefer gm wrapper
    df = pci._read_sheet_to_df(None, "FAKE_ID", "Sheet!A1:B3")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["A", "B"]
    assert df.iloc[0]["A"] == "1"
    assert df.shape[0] == 2


def test_read_sheet_to_df_fallback_to_safe_execute(monkeypatch):
    """
    If gm.get_sheet_values returns None, _read_sheet_to_df should fall back to using the
    provided sheet.values().get(...) + _safe_execute() path.
    """
    monkeypatch.setattr(gm, "get_sheet_values", lambda ss, rng, timeout=None: None)

    # Fake sheet that will be used by fallback path
    class FakeReq:
        pass

    class FakeValues:
        def get(self, **kwargs):
            return FakeReq()

    class FakeSheet:
        def values(self):
            return FakeValues()

    # Have _safe_execute return a results dict matching the expected shape
    fake_result = {"values": [["C", "D"], ["x", "y"]]}

    monkeypatch.setattr(pci, "_safe_execute", lambda req, retries=5: fake_result)

    df = pci._read_sheet_to_df(FakeSheet(), "FAKE_ID", "Tab!A1:B2")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["C", "D"]
    assert df.iloc[0]["C"] == "x"


def test_get_sheet_service_adapter_uses_gm(monkeypatch):
    """_get_sheet_service should return a sheet-like object backed by gm.get_sheet_values."""
    rows = [["H1", "H2"], ["v1", "v2"]]
    monkeypatch.setattr(gm, "get_sheet_values", lambda ss, rng, timeout=None: rows)

    sheet = pci._get_sheet_service()
    vals = sheet.values().get(spreadsheetId="ID", range="RANGE").execute()
    assert isinstance(vals, dict)
    assert vals.get("values") == rows
