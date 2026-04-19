import datetime as dt

import pandas as pd
import pytest

import honor_importer as hi
import kvk_state


class DummyConn:
    def __init__(self):
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        raise AssertionError("cursor() should not be called in this test")


def test_conn_prefers_get_conn_with_retries(monkeypatch):
    called = {"retry": 0}

    def fake_get_conn_with_retries():
        called["retry"] += 1
        return DummyConn()

    import file_utils

    monkeypatch.setattr(file_utils, "get_conn_with_retries", fake_get_conn_with_retries)

    conn = hi._conn()
    assert isinstance(conn, DummyConn)
    assert called["retry"] == 1


def test_current_kvk_no_uses_kvk_state(monkeypatch):
    # Arrange: make kvk_state.get_kvk_context_today return known kvk_no
    monkeypatch.setattr(
        kvk_state,
        "get_kvk_context_today",
        lambda: {
            "kvk_no": 314,
            "kvk_name": "X",
            "start_date": None,
            "end_date": None,
            "state": "DRAFT",
            "next_kvk_no": None,
        },
    )

    # Act: call _current_kvk_no with a dummy cursor (should not be used when kvk_state returns a value)
    class DummyCursor:
        def execute(self, *args, **kwargs):
            raise AssertionError(
                "_current_kvk_no should not use cursor when kvk_state provides kvk_no"
            )

    kvk_no = hi._current_kvk_no(DummyCursor())
    assert kvk_no == 314


def _fake_df_with_columns(columns, rows):
    return pd.DataFrame(rows, columns=columns)


def test_parse_honor_xlsx_missing_columns_returns_error(monkeypatch):
    # DataFrame missing HonorPoints
    df = _fake_df_with_columns(["GovernorID", "Name"], [{"GovernorID": 1, "Name": "Alice"}])
    monkeypatch.setattr(hi.pd, "read_excel", lambda bio, sheet_name="honor": df)

    with pytest.raises(ValueError) as ei:
        hi.parse_honor_xlsx(b"dummy")
    assert "Missing required column" in str(ei.value) or "Missing required column(s)" in str(
        ei.value
    )


def test_parse_honor_xlsx_nan_name_becomes_empty_string(monkeypatch):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Honor Points"],
        [
            {"GovernorID": 123, "Name": None, "Honor Points": 10},
            {"GovernorID": 456, "Name": float("nan"), "Honor Points": 20},
        ],
    )
    monkeypatch.setattr(hi.pd, "read_excel", lambda bio, sheet_name="honor": df)

    result = hi.parse_honor_xlsx(b"bytes")
    assert result.shape[0] == 2
    # GovernorName for both rows should be empty string (not 'nan' or 'None')
    assert all((n == "") for n in result["GovernorName"].tolist())


class MockCursor:
    def __init__(self, fail_executemany=False):
        self.executed = []
        self.executemany_calls = []
        self.fast_executemany = False
        self.fail_executemany = fail_executemany

    def execute(self, sql, *params):
        self.executed.append((sql, params))

    def executemany(self, sql, rows):
        self.executemany_calls.append((sql, rows))
        if self.fail_executemany:
            raise RuntimeError("simulated insert failure")

    def close(self):
        pass


class MockConn:
    def __init__(self, cursor: MockCursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_ingest_honor_snapshot_rolls_back_on_failure(monkeypatch):
    # Minimal DataFrame valid for parsing
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Honor Points"], [{"GovernorID": 1, "Name": "A", "Honor Points": 5}]
    )
    monkeypatch.setattr(hi.pd, "read_excel", lambda bio, sheet_name="honor": df)

    # Provide deterministic _current_kvk_no and _next_scan_id so code proceeds to insert
    monkeypatch.setattr(hi, "_current_kvk_no", lambda cur: 13)
    monkeypatch.setattr(hi, "_next_scan_id", lambda cur, kvk_no: 7)

    cur = MockCursor(fail_executemany=True)
    conn = MockConn(cur)
    monkeypatch.setattr(hi, "_conn", lambda: conn)

    # Capture telemetry calls
    emitted = []
    import file_utils

    def fake_emit(payload, **kw):
        emitted.append(payload)

    monkeypatch.setattr(file_utils, "emit_telemetry_event", fake_emit)

    # Expect the specific runtime error raised by the mocked executemany
    with pytest.raises(RuntimeError):
        hi.ingest_honor_snapshot(
            b"bytes", source_filename="f.xlsx", scan_ts_utc=dt.datetime.utcnow()
        )

    # rollback should have been attempted and no commit should have occurred
    assert conn.rollbacks >= 1
    assert conn.commits == 0

    # telemetry should have recorded start and fail
    events = [p.get("event") for p in emitted]
    assert "honor_import_start" in events
    assert "honor_import_fail" in events


def test_ingest_honor_snapshot_success_commits_emits_telemetry(monkeypatch):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Honor Points"], [{"GovernorID": 1, "Name": "A", "Honor Points": 5}]
    )
    monkeypatch.setattr(hi.pd, "read_excel", lambda bio, sheet_name="honor": df)

    # Provide deterministic values via monkeypatching to avoid DB queries
    monkeypatch.setattr(hi, "_current_kvk_no", lambda cur: 99)
    monkeypatch.setattr(hi, "_next_scan_id", lambda cur, kvk_no: 55)

    cur = MockCursor(fail_executemany=False)
    conn = MockConn(cur)
    monkeypatch.setattr(hi, "_conn", lambda: conn)

    emitted = []
    import file_utils

    def fake_emit(payload, **kw):
        emitted.append(payload)

    monkeypatch.setattr(file_utils, "emit_telemetry_event", fake_emit)

    kvk_no, scan_id = hi.ingest_honor_snapshot(
        b"bytes", source_filename="file.xlsx", scan_ts_utc=dt.datetime.utcnow()
    )
    assert kvk_no == 99
    assert scan_id == 55
    assert conn.commits == 1

    events = [p.get("event") for p in emitted]
    assert "honor_import_start" in events
    assert "honor_import_success" in events
