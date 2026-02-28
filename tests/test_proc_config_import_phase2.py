import os
from types import SimpleNamespace

import pandas as pd

import proc_config_import as pci


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.closed = False

    def execute(self, sql, *args, **kwargs):
        self.executed.append(sql)

    def fetchall(self):
        return []

    def close(self):
        self.closed = True


class FakeConn:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self._cursor = FakeCursor()

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def make_sample_df():
    return pd.DataFrame([{"KVK_NO": 1, "SomeCol": "A"}, {"KVK_NO": 2, "SomeCol": "B"}])


def test_transactional_success(monkeypatch, tmp_path):
    # Prepare environment and monkeypatches
    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(pci, "KVK_SHEET_ID", "sheet-id")
    monkeypatch.setattr(pci, "IMPORT_TRANSACTIONAL", True)

    # Mock sheet service / read
    monkeypatch.setattr(pci, "_get_sheet_service", lambda: SimpleNamespace())
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: make_sample_df() if rng == "ProcConfig!A1:J" else pd.DataFrame(),
    )

    # Provide fake connection
    fake_conn = FakeConn()
    monkeypatch.setattr(pci, "_get_import_connection_with_retry", lambda: fake_conn)

    # Mock preflight and log_backup_context
    monkeypatch.setattr(pci, "preflight_or_raise", lambda *a, **k: None)
    monkeypatch.setattr(pci, "log_backup_context", lambda *a, **k: None)

    # Mock centralized helper to return success
    def fake_write_df_to_staging_and_upsert(
        cursor, conn, df, staging_table, upsert_proc, batch_size, transactional
    ):
        return {
            "staging": {"table": staging_table, "rows": len(df), "status": "ok", "error": None},
            "upsert": {"proc": upsert_proc, "status": "ok", "error": None},
        }

    monkeypatch.setattr(pci, "write_df_to_staging_and_upsert", fake_write_df_to_staging_and_upsert)

    # Run import
    success, report = pci.run_proc_config_import(dry_run=False)
    assert success is True
    assert report["tables"]["dbo.ProcConfig_Staging"]["status"] == "ok"
    assert report["tables"]["dbo.ProcConfig_Staging_upsert"]["status"] == "ok"
    assert fake_conn.committed is True
    # persisted report file exists
    assert os.path.exists(os.path.join(str(tmp_path), "last_proc_import_report.json"))


def test_transactional_upsert_failure_triggers_rollback(monkeypatch, tmp_path):
    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(pci, "KVK_SHEET_ID", "sheet-id")
    monkeypatch.setattr(pci, "IMPORT_TRANSACTIONAL", True)

    monkeypatch.setattr(pci, "_get_sheet_service", lambda: SimpleNamespace())
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: make_sample_df() if rng == "ProcConfig!A1:J" else pd.DataFrame(),
    )

    fake_conn = FakeConn()
    monkeypatch.setattr(pci, "_get_import_connection_with_retry", lambda: fake_conn)
    monkeypatch.setattr(pci, "preflight_or_raise", lambda *a, **k: None)
    monkeypatch.setattr(pci, "log_backup_context", lambda *a, **k: None)

    def failing_write(cursor, conn, df, staging_table, upsert_proc, batch_size, transactional):
        return {
            "staging": {"table": staging_table, "rows": len(df), "status": "ok", "error": None},
            "upsert": {"proc": upsert_proc, "status": "error", "error": "proc failed"},
        }

    monkeypatch.setattr(pci, "write_df_to_staging_and_upsert", failing_write)

    success, report = pci.run_proc_config_import(dry_run=False)
    assert success is False
    assert "ProcConfig upsert failed" in report["errors"][0] or any(
        "upsert" in k for k in report["tables"].keys()
    )
    assert fake_conn.rolled_back is True


def test_non_transactional_calls_helper_and_commits(monkeypatch, tmp_path):
    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(pci, "KVK_SHEET_ID", "sheet-id")
    # Set non-transactional mode
    monkeypatch.setattr(pci, "IMPORT_TRANSACTIONAL", False)

    monkeypatch.setattr(pci, "_get_sheet_service", lambda: SimpleNamespace())
    monkeypatch.setattr(
        pci,
        "_read_sheet_to_df",
        lambda sheet, sid, rng: make_sample_df() if rng == "ProcConfig!A1:J" else pd.DataFrame(),
    )

    fake_conn = FakeConn()
    monkeypatch.setattr(pci, "_get_import_connection_with_retry", lambda: fake_conn)
    monkeypatch.setattr(pci, "preflight_or_raise", lambda *a, **k: None)
    monkeypatch.setattr(pci, "log_backup_context", lambda *a, **k: None)

    called = {"args": None}

    def fake_write_non_tx(cursor, conn, df, staging_table, upsert_proc, batch_size, transactional):
        called["args"] = {"staging_table": staging_table, "transactional": transactional}
        return {
            "staging": {"table": staging_table, "rows": len(df), "status": "ok", "error": None},
            "upsert": {"proc": upsert_proc, "status": "ok", "error": None},
        }

    monkeypatch.setattr(pci, "write_df_to_staging_and_upsert", fake_write_non_tx)

    success, report = pci.run_proc_config_import(dry_run=False)
    assert success is True
    assert called["args"]["transactional"] is False
    assert fake_conn.committed is True
