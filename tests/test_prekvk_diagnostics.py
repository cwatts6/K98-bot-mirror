from __future__ import annotations

from datetime import UTC, datetime
import inspect

import pandas as pd

from commands.prekvk_admin_cmds import register_prekvk_admin
from kvk.dal import kvk_stats_dal
from prekvk import diagnostics_service
from prekvk.dal import import_history_dal
import prekvk_importer as pki


def _df(columns, rows):
    return pd.DataFrame(rows, columns=columns)


class MockCursor:
    def __init__(self, *, fail_executemany: bool = False):
        self.executed = []
        self.executemany_calls = []
        self.fast_executemany = False
        self.description = None
        self._fetchone_queue = []
        self.fail_executemany = fail_executemany

    def queue_fetchone(self, row, columns=("col",)):
        self._fetchone_queue.append((row, columns))

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        sql_l = str(sql).lower()
        if sql_l.strip().startswith("select"):
            self.description = [("x",)]
        elif "output inserted" in sql_l:
            self.description = [("ScanID",)]
        return None

    def executemany(self, sql, rows):
        if self.fail_executemany:
            raise RuntimeError("simulated insert failure")
        self.executemany_calls.append((sql, rows))

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        row, columns = self._fetchone_queue.pop(0)
        if row is None:
            return None
        self.description = [(c,) for c in columns]
        return row

    def fetchall(self):
        return []


class MockConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _patch_excel(monkeypatch, df):
    monkeypatch.setattr(pki.pd, "read_excel", lambda *_a, **_kw: df)


def _patch_conn(monkeypatch, cur):
    conn = MockConn(cur)
    monkeypatch.setattr(pki, "_conn", lambda: conn)
    return conn


def _capture_history(monkeypatch):
    monkeypatch.delenv("PREKVK_IMPORT_HISTORY_DISABLED", raising=False)
    captured = []
    monkeypatch.setattr(
        diagnostics_service, "record_import_outcome", lambda **kw: captured.append(kw)
    )
    return captured


def test_import_records_accepted_history(monkeypatch):
    captured = _capture_history(monkeypatch)
    _patch_excel(
        monkeypatch,
        _df(
            ["GovernorID", "Name", "Prekvk Points"],
            [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
        ),
    )
    cur = MockCursor()
    cur.queue_fetchone(None, columns=("x",))
    cur.queue_fetchone((7,), columns=("ScanID",))
    _patch_conn(monkeypatch, cur)

    ok, _msg, rows = pki.import_prekvk_bytes(
        b"bytes",
        "1198_prekvk.xlsx",
        kvk_no=13,
        uploader_discord_id=123,
        channel_id=456,
        message_id=789,
    )

    assert ok is True
    assert rows == 1
    assert captured[-1]["status"] == "accepted"
    assert captured[-1]["scan_id"] == 7
    assert captured[-1]["row_count"] == 1
    assert captured[-1]["uploader_discord_id"] == 123
    assert captured[-1]["channel_id"] == 456
    assert captured[-1]["message_id"] == 789


def test_import_records_duplicate_history(monkeypatch):
    captured = _capture_history(monkeypatch)
    _patch_excel(
        monkeypatch,
        _df(
            ["GovernorID", "Name", "Prekvk Points"],
            [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
        ),
    )
    cur = MockCursor()
    cur.queue_fetchone((1,), columns=("x",))
    _patch_conn(monkeypatch, cur)

    ok, msg, rows = pki.import_prekvk_bytes(b"same", "1198_prekvk.xlsx", kvk_no=13)

    assert ok is True
    assert rows == 0
    assert "Duplicate file skipped" in msg
    assert captured[-1]["status"] == "duplicate"
    assert captured[-1]["row_count"] == 0


def test_import_records_validation_rejection_history(monkeypatch):
    captured = _capture_history(monkeypatch)
    _patch_excel(monkeypatch, _df(["Wrong"], [{"Wrong": 1}]))
    monkeypatch.setattr(
        pki,
        "_conn",
        lambda: (_ for _ in ()).throw(AssertionError("validation should not import rows")),
    )

    ok, msg, rows = pki.import_prekvk_bytes(b"bad", "1198_prekvk.xlsx", kvk_no=13)

    assert ok is False
    assert rows == 0
    assert "Missing required column" in msg
    assert captured[-1]["status"] == "rejected"
    assert captured[-1]["error_type"] == "MissingColumns"


def test_import_records_database_failure_history(monkeypatch):
    captured = _capture_history(monkeypatch)
    _patch_excel(
        monkeypatch,
        _df(
            ["GovernorID", "Name", "Prekvk Points"],
            [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
        ),
    )
    cur = MockCursor(fail_executemany=True)
    cur.queue_fetchone(None, columns=("x",))
    cur.queue_fetchone((7,), columns=("ScanID",))
    _patch_conn(monkeypatch, cur)

    ok, msg, rows = pki.import_prekvk_bytes(b"bytes", "1198_prekvk.xlsx", kvk_no=13)

    assert ok is False
    assert rows == 0
    assert "simulated insert failure" in msg
    assert captured[-1]["status"] == "failed"
    assert captured[-1]["scan_id"] == 7
    assert captured[-1]["error_type"] == "RuntimeError"


def test_record_import_history_uses_sql_backed_state(monkeypatch):
    calls = {}

    class Cursor:
        def execute(self, sql, params):
            calls["sql"] = sql
            calls["params"] = params

        def fetchone(self):
            return (42,)

    monkeypatch.setattr(import_history_dal, "exec_with_cursor", lambda cb: cb(Cursor()))

    history_id = import_history_dal.record_import_history(
        kvk_no=13,
        filename="PreKvK.xlsx",
        status="accepted",
        hash_prefix="abcdef12",
        file_hash_sha256="a" * 64,
        row_count=2,
        scan_id=9,
        created_utc=datetime(2026, 5, 8, tzinfo=UTC),
    )

    assert history_id == 42
    assert "dbo.PreKvk_ImportHistory" in calls["sql"]
    assert calls["params"][0] == 13
    assert calls["params"][4] == "accepted"
    assert calls["params"][6] == 2


def test_fetch_recent_import_history_filters(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        import_history_dal,
        "run_query",
        lambda sql, params=(): captured.setdefault("call", (sql, params)) or [],
    )

    import_history_dal.fetch_recent_import_history(kvk_no=13, status="failed", limit=99)

    sql, params = captured["call"]
    assert "TOP (25)" in sql
    assert "KVK_NO = ?" in sql
    assert "ImportStatus = ?" in sql
    assert params == (13, "failed")


def test_format_history_rows_for_admin_output():
    body = diagnostics_service.format_history_rows(
        [
            {
                "CreatedUTC": "2026-05-08 10:00",
                "KVK_NO": 13,
                "Filename": "PreKvK.xlsx",
                "ImportStatus": "failed",
                "RowCount": 0,
                "ErrorType": "InvalidWorkbook",
            }
        ]
    )

    assert "PreKvK.xlsx" in body
    assert "failed" in body
    assert "InvalidWorkbook" in body


def test_prekvk_import_history_command_has_admin_gate():
    source = inspect.getsource(register_prekvk_admin)

    assert "@is_admin_and_notify_channel()" in source
    assert "@safe_command" in source
    assert "@track_usage()" in source


def test_fetch_prekvk_phase_list_uses_direct_stage_columns(monkeypatch):
    executed = {}

    class Cursor:
        def __init__(self):
            self.description = [("GovernorID",), ("Name",), ("Points",)]

        def execute(self, sql, params):
            executed["sql"] = sql
            executed["params"] = params

        def fetchall(self):
            return [(1, "Alice", 20)]

    class Conn:
        def cursor(self):
            return Cursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(kvk_stats_dal, "_get_conn", lambda: Conn())

    rows = kvk_stats_dal.fetch_prekvk_phase_list(13, 2)

    assert rows == [{"GovernorID": 1, "Name": "Alice", "Points": 20}]
    assert "Stage2Points" in executed["sql"]
    assert "PreKvk_Phases" not in executed["sql"]
    assert executed["params"] == (13, 13)


def test_fetch_prekvk_phase_list_invalid_phase_returns_empty(monkeypatch):
    monkeypatch.setattr(
        kvk_stats_dal,
        "_get_conn",
        lambda: (_ for _ in ()).throw(AssertionError("DB should not be used")),
    )

    assert kvk_stats_dal.fetch_prekvk_phase_list(13, 9) == []
