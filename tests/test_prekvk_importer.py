import pandas as pd

import prekvk_importer as pki


def test_conn_prefers_get_conn_with_retries(monkeypatch):
    """
    Task 6 Option A: prekvk_importer._conn() should prefer file_utils.get_conn_with_retries().
    """
    called = {"retry": 0, "fallback": 0}

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            # Not used in this test
            raise AssertionError("cursor() should not be called in this test")

    def fake_get_conn_with_retries():
        called["retry"] += 1
        return DummyConn()

    # Patch at the source module that prekvk_importer imports from dynamically
    import file_utils

    monkeypatch.setattr(file_utils, "get_conn_with_retries", fake_get_conn_with_retries)

    # If fallback is accidentally used, fail loudly
    import constants

    def fake_constants_conn():
        called["fallback"] += 1
        raise AssertionError("constants._conn() fallback should not be called when retry works")

    monkeypatch.setattr(constants, "_conn", fake_constants_conn)

    conn = pki._conn()
    assert isinstance(conn, DummyConn)
    assert called["retry"] == 1
    assert called["fallback"] == 0


def test_conn_falls_back_to_constants_conn_when_retry_helper_fails(monkeypatch):
    """
    Task 6 Option A: if get_conn_with_retries is unavailable or raises,
    prekvk_importer._conn() should fall back to constants._conn().
    """
    called = {"retry": 0, "fallback": 0}

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            raise AssertionError("cursor() should not be called in this test")

    # Make retry helper raise
    import file_utils

    def fake_get_conn_with_retries():
        called["retry"] += 1
        raise RuntimeError("simulated get_conn_with_retries failure")

    monkeypatch.setattr(file_utils, "get_conn_with_retries", fake_get_conn_with_retries)

    # Fallback should be used
    import constants

    def fake_constants_conn():
        called["fallback"] += 1
        return DummyConn()

    monkeypatch.setattr(constants, "_conn", fake_constants_conn)

    conn = pki._conn()
    assert isinstance(conn, DummyConn)
    assert called["retry"] == 1
    assert called["fallback"] == 1


def _fake_df_with_columns(columns, rows):
    """
    Build a DataFrame with provided columns and row dicts.

    rows: list[dict]
    """
    return pd.DataFrame(rows, columns=columns)


class MockCursor:
    """
    Minimal pyodbc-like cursor:
    - supports execute, executemany
    - supports description + fetchone to work with file_utils.fetch_one_dict
    """

    def __init__(self):
        self.executed = []  # list of (sql, params)
        self.executemany_calls = []  # list of (sql, rows)
        self.fast_executemany = False

        # fetch queue: list of tuples/lists representing rows for fetchone
        self._fetchone_queue = []
        self.description = None  # set when execute produces a result set

    def queue_fetchone(self, row, columns=("col",)):
        """
        Configure the next fetchone() result and cursor.description.
        row: tuple|list|None
        columns: iterable of column names; used for cursor.description
        """
        self._fetchone_queue.append((row, columns))

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

        # Heuristic: set description only for SELECT/OUTPUT-style statements where caller fetches
        sql_lc = str(sql).strip().lower()
        if sql_lc.startswith("select"):
            # For the dedupe check, importer calls fetch_one_dict; we should provide a description.
            # We'll keep it simple: one column named "x" unless queue provides different.
            self.description = [("x",)]
        elif "output inserted" in sql_lc:
            # For scan ID OUTPUT, description must include "ScanID" ideally
            self.description = [("ScanID",)]
        else:
            self.description = None

        return None

    def executemany(self, sql, rows):
        self.executemany_calls.append((sql, rows))
        return None

    def fetchone(self):
        if not self._fetchone_queue:
            return None
        row, columns = self._fetchone_queue.pop(0)
        if row is None:
            # No row; still keep description consistent with last statement
            return None
        self.description = [(c,) for c in columns]
        return row


class MockConn:
    def __init__(self, cursor: MockCursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    # Context manager protocol
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # pyodbc closes connection; we do nothing
        return False


def _patch_read_excel(monkeypatch, df: pd.DataFrame, *, sheet_name_required=True):
    """
    Patch pandas.read_excel behavior in importer:
    - When called with sheet_name="prekvk", return df (or raise if sheet_name_required=False)
    - When called with sheet_name=None, return dict of sheets
    """

    def fake_read_excel(_bio, sheet_name="prekvk"):
        if sheet_name == "prekvk":
            if sheet_name_required:
                return df
            raise Exception("sheet not found")
        if sheet_name is None:
            return {"Sheet1": df}
        raise AssertionError(f"Unexpected sheet_name: {sheet_name!r}")

    monkeypatch.setattr(pki.pd, "read_excel", fake_read_excel)


def _patch_conn(monkeypatch, cursor: MockCursor, conn: MockConn):
    def fake_conn():
        return conn

    monkeypatch.setattr(pki, "_conn", fake_conn)


def test_missing_required_columns_returns_false(monkeypatch):
    """
    Expect friendly error (no KeyError) when required columns are missing.
    """
    df = _fake_df_with_columns(
        ["SomeOtherColumn", "NameMaybe"],
        [{"SomeOtherColumn": 1, "NameMaybe": "Alice"}],
    )
    _patch_read_excel(monkeypatch, df)

    ok, msg, rows = pki.import_prekvk_bytes(
        b"dummy",
        "file.xlsx",
        kvk_no=13,
    )

    assert ok is False
    assert rows == 0
    # Should be an explicit missing-columns message (Phase 1 requirement)
    assert "Missing required column" in msg
    assert "Found columns" in msg


def test_governor_name_nan_becomes_empty_string(monkeypatch):
    """
    Ensure NaN/None in GovernorName doesn't become literal 'nan' string in DB insert rows.
    """
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [
            {"GovernorID": 123, "Name": None, "Prekvk Points": 10},
            {"GovernorID": 456, "Name": float("nan"), "Prekvk Points": 20},
        ],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    # Dedupe check returns no rows
    cur.queue_fetchone(None, columns=("x",))
    # ScanID OUTPUT returns ScanID=99
    cur.queue_fetchone((99,), columns=("ScanID",))

    ok, msg, rows = pki.import_prekvk_bytes(
        b"content-bytes",
        "1198_prekvk.xlsx",
        kvk_no=13,
    )

    assert ok is True
    assert rows == 2
    assert "scan 99" in msg

    assert len(cur.executemany_calls) == 1
    insert_sql, inserted_rows = cur.executemany_calls[0]
    assert "INSERT INTO dbo.PreKvk_Scores" in insert_sql

    # GovernorName is 4th column in inserted row tuple: (kvk_no, scan_id, gid, name, points)
    assert inserted_rows[0][3] == ""
    assert inserted_rows[1][3] == ""


def test_duplicate_hash_skips_import(monkeypatch):
    """
    If SELECT 1 finds an existing hash, importer should skip without inserting.
    """
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    # Dedupe check returns a row -> fetch_one_dict returns dict truthy
    cur.queue_fetchone((1,), columns=("x",))

    ok, msg, rows = pki.import_prekvk_bytes(
        b"same-bytes",
        "1198_prekvk.xlsx",
        kvk_no=13,
    )

    assert ok is True
    assert rows == 0
    assert "Duplicate file skipped" in msg

    # No header insert and no bulk insert should have occurred
    assert all("INSERT INTO dbo.PreKvk_Scan" not in (sql or "") for sql, _ in cur.executed)
    assert len(cur.executemany_calls) == 0
    assert conn.commits == 0


def test_db_failure_rolls_back(monkeypatch):
    """
    If bulk insert fails, importer should rollback explicitly (Phase 1 requirement).
    """
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    class FailingCursor(MockCursor):
        def executemany(self, sql, rows):
            raise RuntimeError("simulated insert failure")

    cur = FailingCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    # Dedupe check: no row
    cur.queue_fetchone(None, columns=("x",))
    # ScanID OUTPUT returns 7
    cur.queue_fetchone((7,), columns=("ScanID",))

    ok, msg, rows = pki.import_prekvk_bytes(
        b"bytes",
        "1198_prekvk.xlsx",
        kvk_no=13,
    )

    assert ok is False
    assert rows == 0
    # rollback should have been attempted
    assert conn.rollbacks >= 1
    assert conn.commits == 0
    assert "RuntimeError" in msg or "simulated insert failure" in msg


def test_scan_id_fallback_to_first_value(monkeypatch):
    """
    import_prekvk_bytes uses scan_row.get("ScanID", next(iter(scan_row.values()))).
    Validate fallback works if ScanID key is absent.
    """
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 42, "Name": "X", "Prekvk Points": 1}],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    # Dedupe check: no row
    cur.queue_fetchone(None, columns=("x",))

    # For scan id fetch, return a row with different column name
    cur.queue_fetchone((1234,), columns=("NotScanID",))

    ok, msg, rows = pki.import_prekvk_bytes(
        b"bytes2",
        "1198_prekvk.xlsx",
        kvk_no=13,
    )

    assert ok is True
    assert rows == 1
    assert "scan 1234" in msg


def test_rows_with_non_numeric_governor_id_are_dropped(monkeypatch):
    """
    GovernorID is coerced numeric; invalid values become NA and are dropped.
    """
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [
            {"GovernorID": "not-a-number", "Name": "Bad", "Prekvk Points": 10},
            {"GovernorID": "123", "Name": "Good", "Prekvk Points": 20},
        ],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    # Dedupe: no row
    cur.queue_fetchone(None, columns=("x",))
    # ScanID: 55
    cur.queue_fetchone((55,), columns=("ScanID",))

    ok, msg, rows = pki.import_prekvk_bytes(
        b"bytes3",
        "1198_prekvk.xlsx",
        kvk_no=13,
    )

    assert ok is True
    assert rows == 1
    assert "Imported 1 rows" in msg

    assert len(cur.executemany_calls) == 1
    _, inserted_rows = cur.executemany_calls[0]
    assert len(inserted_rows) == 1
    assert inserted_rows[0][2] == 123  # GovernorID coerced to int


def test_points_non_numeric_become_zero(monkeypatch):
    """
    Points are coerced numeric; invalid values become 0.
    """
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": "oops"}],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    cur.queue_fetchone(None, columns=("x",))
    cur.queue_fetchone((8,), columns=("ScanID",))

    ok, msg, rows = pki.import_prekvk_bytes(
        b"bytes4",
        "1198_prekvk.xlsx",
        kvk_no=13,
    )

    assert ok is True
    assert rows == 1

    _, inserted_rows = cur.executemany_calls[0]
    assert inserted_rows[0][4] == 0  # Points coerced to 0


def test_import_logs_start_and_success(monkeypatch, caplog):
    # Arrange: minimal valid df
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    # DB mocks
    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)
    cur.queue_fetchone(None, columns=("x",))  # dedupe -> none
    cur.queue_fetchone((7,), columns=("ScanID",))  # scan id

    # Patch telemetry to no-op (avoid depending on logging_setup file handler)
    import file_utils

    monkeypatch.setattr(file_utils, "emit_telemetry_event", lambda payload, **kw: None)

    caplog.set_level("INFO")

    # Act
    ok, msg, rows = pki.import_prekvk_bytes(b"bytes", "1198_prekvk.xlsx", kvk_no=13)

    # Assert behavior
    assert ok is True
    assert rows == 1
    assert "scan 7" in msg

    # Assert logs contain structured messages
    messages = [r.getMessage() for r in caplog.records]
    assert any(
        "[PREKVK] import start" in m and "kvk_no=13" in m and "file=1198_prekvk.xlsx" in m
        for m in messages
    )
    assert any(
        "[PREKVK] import success" in m and "kvk_no=13" in m and "scan_id=7" in m and "rows=1" in m
        for m in messages
    )


def test_import_logs_duplicate_skip_includes_hash_prefix(monkeypatch, caplog):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)

    # dedupe check returns row
    cur.queue_fetchone((1,), columns=("x",))

    import file_utils

    monkeypatch.setattr(file_utils, "emit_telemetry_event", lambda payload, **kw: None)

    caplog.set_level("INFO")
    ok, msg, rows = pki.import_prekvk_bytes(b"same-bytes", "1198_prekvk.xlsx", kvk_no=13)

    assert ok is True
    assert rows == 0
    assert "Duplicate file skipped" in msg

    messages = [r.getMessage() for r in caplog.records]
    # hash prefix is 8 hex chars; we just assert "hash=" is present and non-empty
    assert any("[PREKVK] import skipped duplicate" in m and "hash=" in m for m in messages)


def test_import_emits_telemetry_events(monkeypatch):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)
    cur.queue_fetchone(None, columns=("x",))
    cur.queue_fetchone((7,), columns=("ScanID",))

    emitted = []

    import file_utils

    monkeypatch.setattr(
        file_utils, "emit_telemetry_event", lambda payload, **kw: emitted.append(payload)
    )

    ok, msg, rows = pki.import_prekvk_bytes(b"bytes", "1198_prekvk.xlsx", kvk_no=13)
    assert ok is True
    assert rows == 1

    events = [p.get("event") for p in emitted]
    assert "prekvk_import_start" in events
    assert "prekvk_import_success" in events


def test_import_uses_executemany_batched(monkeypatch):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    # DB mocks
    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)
    cur.queue_fetchone(None, columns=("x",))
    cur.queue_fetchone((7,), columns=("ScanID",))

    # Capture executemany_batched calls
    captured = {}

    def fake_executemany_batched(
        cursor, conn_obj, sql, rows, batch_size=5000, *, commit_per_batch=True
    ):
        captured["cursor"] = cursor
        captured["conn"] = conn_obj
        captured["sql"] = sql
        captured["rows"] = rows
        captured["batch_size"] = batch_size
        captured["commit_per_batch"] = commit_per_batch
        # Simulate successful insert count
        return len(rows)

    # Patch the symbol imported into prekvk_importer
    monkeypatch.setattr(pki, "executemany_batched", fake_executemany_batched)

    # Ensure telemetry doesn’t interfere
    import file_utils

    monkeypatch.setattr(file_utils, "emit_telemetry_event", lambda payload, **kw: None)

    ok, msg, rows = pki.import_prekvk_bytes(b"bytes", "1198_prekvk.xlsx", kvk_no=13)
    assert ok is True
    assert rows == 1
    assert "scan 7" in msg

    assert captured["cursor"] is cur
    assert captured["conn"] is conn
    assert "INSERT INTO dbo.PreKvk_Scores" in captured["sql"]
    assert captured["commit_per_batch"] is False  # critical transactional guarantee


def test_import_uses_executemany_batched_and_respects_env_batch_size(monkeypatch):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [{"GovernorID": 1, "Name": "A", "Prekvk Points": 5}],
    )
    _patch_read_excel(monkeypatch, df)

    # DB mocks
    cur = MockCursor()
    conn = MockConn(cur)
    _patch_conn(monkeypatch, cur, conn)
    cur.queue_fetchone(None, columns=("x",))
    cur.queue_fetchone((7,), columns=("ScanID",))

    # Env override
    monkeypatch.setenv("PREKVK_IMPORT_BATCH_SIZE", "123")

    captured = {}

    def fake_executemany_batched(
        cursor,
        conn_obj,
        sql,
        rows,
        batch_size=5000,
        *,
        commit_per_batch=True,
    ):
        captured["batch_size"] = batch_size
        captured["commit_per_batch"] = commit_per_batch
        captured["rows_len"] = len(rows)
        return len(rows)

    # Patch the symbol imported into prekvk_importer
    monkeypatch.setattr(pki, "executemany_batched", fake_executemany_batched)

    # Ensure telemetry doesn’t interfere
    import file_utils

    monkeypatch.setattr(file_utils, "emit_telemetry_event", lambda payload, **kw: None)

    ok, msg, rows = pki.import_prekvk_bytes(b"bytes", "1198_prekvk.xlsx", kvk_no=13)
    assert ok is True
    assert rows == 1
    assert "scan 7" in msg

    assert captured["rows_len"] == 1
    assert captured["commit_per_batch"] is False  # transactional guarantee
    assert captured["batch_size"] == 123  # env override respected


def test_duplicate_governor_ids_are_rejected_before_db(monkeypatch):
    df = _fake_df_with_columns(
        ["GovernorID", "Name", "Prekvk Points"],
        [
            {"GovernorID": 123, "Name": "A", "Prekvk Points": 10},
            {"GovernorID": 123, "Name": "A2", "Prekvk Points": 20},
        ],
    )
    _patch_read_excel(monkeypatch, df)

    # If importer tries to open DB connection, fail the test
    def fail_conn():
        raise AssertionError("_conn() should not be called when duplicates are present")

    monkeypatch.setattr(pki, "_conn", fail_conn)

    emitted = []
    import file_utils

    monkeypatch.setattr(
        file_utils, "emit_telemetry_event", lambda payload, **kw: emitted.append(payload)
    )

    ok, msg, rows = pki.import_prekvk_bytes(b"bytes", "1198_prekvk.xlsx", kvk_no=13)

    assert ok is False
    assert rows == 0
    assert "Duplicate GovernorID" in msg

    # Telemetry should mark the correct failure type
    assert any(p.get("error_type") == "DuplicateGovernorIDs" for p in emitted)
