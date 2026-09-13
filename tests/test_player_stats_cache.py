from datetime import UTC, datetime
import json
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("9,007,199,254,740,993", 9_007_199_254_740_993),
        ("456.7", 456),
        ("NaN", 0),
    ],
)
def test_cache_integer_parsing_avoids_float_precision_loss(raw_value, expected):
    import player_stats_cache as mod

    assert mod._to_int(raw_value) == expected


def _read_json(p: Path) -> dict:
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def _source_columns_and_row(
    mod,
    *,
    governor_id: str = "123",
    kvk_no: int = 16,
    last_refresh: str = "2026-08-28T08:12:00",
):
    columns = [candidates[0] for candidates in mod._CANONICAL_FIELD_CANDIDATES.values()]
    values = []
    for canonical in mod._CANONICAL_FIELD_CANDIDATES:
        if canonical == "GovernorID":
            values.append(governor_id)
        elif canonical == "GovernorName":
            values.append(f"Governor {governor_id}")
        elif canonical == "KVK_NO":
            values.append(kvk_no)
        elif canonical == "LAST_REFRESH":
            values.append(last_refresh)
        elif canonical in {"STATUS", "Civilization"}:
            values.append("INCLUDED" if canonical == "STATUS" else "Rome")
        else:
            values.append(0)
    return columns, tuple(values)


class _FakeStatsCursor:
    def __init__(self, *, expected_kvk, columns, rows):
        self.expected_kvk = expected_kvk
        self.columns = columns
        self.rows = rows
        self.mode = None
        self.returned_rows = False
        self.description = None

    def execute(self, sql):
        if "FROM dbo.ProcConfig" in sql:
            self.mode = "expected_kvk"
            self.description = [("KVKVersion",)]
        elif "STATS_FOR_UPLOAD" in sql:
            self.mode = "stats"
            self.returned_rows = False
            self.description = [(column,) for column in self.columns]
        else:
            raise AssertionError(f"Unexpected SQL in fake cursor: {sql}")
        return self

    def fetchone(self):
        return (self.expected_kvk,) if self.mode == "expected_kvk" else None

    def fetchmany(self, _size):
        if self.mode != "stats" or self.returned_rows:
            return []
        self.returned_rows = True
        return self.rows

    def close(self):
        return None


class _FakeStatsConnection:
    def __init__(self, *, expected_kvk, columns, rows):
        self.cursor_instance = _FakeStatsCursor(
            expected_kvk=expected_kvk,
            columns=columns,
            rows=rows,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_instance


def _install_fake_stats_connection(monkeypatch, mod, *, rows, columns, expected_kvk=16):
    connection = _FakeStatsConnection(
        expected_kvk=expected_kvk,
        columns=columns,
        rows=rows,
    )
    monkeypatch.setattr(
        "file_utils.get_conn_with_retries",
        lambda **_kwargs: connection,
    )
    return connection


def test_build_cache_reports_refreshed_source(monkeypatch):
    import player_stats_cache as mod

    columns, row = _source_columns_and_row(mod)
    _install_fake_stats_connection(monkeypatch, mod, rows=[row], columns=columns)
    monkeypatch.setattr(mod, "_REFRESH_BEFORE_BUILD", True)
    monkeypatch.setattr(mod, "_execute_sp_with_retries", lambda _cn: None)

    result = mod._build_cache_sync()
    meta = result["_meta"]

    assert meta["source_refresh_status"] == "refreshed"
    assert meta["source_refresh_succeeded"] is True
    assert meta["source_kvk_no"] == 16
    assert meta["source_last_refresh"] == "2026-08-28T08:12:00"
    assert meta["source_row_count"] == 1
    assert "sp_executed" not in meta


def test_build_cache_reuses_valid_last_known_good_without_error_leak(monkeypatch):
    import player_stats_cache as mod

    columns, row = _source_columns_and_row(mod)
    _install_fake_stats_connection(monkeypatch, mod, rows=[row], columns=columns)
    monkeypatch.setattr(mod, "_REFRESH_BEFORE_BUILD", True)

    def fail_refresh(_cn):
        raise mod.pyodbc.Error("password=should-not-leak")

    monkeypatch.setattr(mod, "_execute_sp_with_retries", fail_refresh)

    result = mod._build_cache_sync()
    serialized = json.dumps(result)

    assert result["_meta"]["source_refresh_status"] == "last_known_good"
    assert result["_meta"]["source_refresh_succeeded"] is False
    assert result["_meta"]["source_refresh_error_code"] == "sql_refresh_failed"
    assert "should-not-leak" not in serialized


def test_build_cache_reports_skipped_refresh(monkeypatch):
    import player_stats_cache as mod

    columns, row = _source_columns_and_row(mod)
    _install_fake_stats_connection(monkeypatch, mod, rows=[row], columns=columns)
    monkeypatch.setattr(mod, "_REFRESH_BEFORE_BUILD", False)

    result = mod._build_cache_sync()

    assert result["_meta"]["source_refresh_status"] == "skipped"
    assert result["_meta"]["source_refresh_succeeded"] is None
    assert result["_meta"]["sp_attempted"] is False


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("empty", "source_snapshot_empty"),
        ("mixed_kvk", "source_kvk_mismatch"),
        ("duplicate_governor", "source_governor_duplicate"),
        ("incoherent_refresh", "source_last_refresh_incoherent"),
    ],
)
def test_build_cache_rejects_invalid_sql_snapshots(monkeypatch, mutation, expected_code):
    import player_stats_cache as mod

    columns, row = _source_columns_and_row(mod)
    rows = [row]
    if mutation == "empty":
        rows = []
    elif mutation == "mixed_kvk":
        _, second = _source_columns_and_row(mod, governor_id="456", kvk_no=15)
        rows.append(second)
    elif mutation == "duplicate_governor":
        rows.append(row)
    elif mutation == "incoherent_refresh":
        _, second = _source_columns_and_row(
            mod,
            governor_id="456",
            last_refresh="2026-08-28T08:13:00",
        )
        rows.append(second)

    _install_fake_stats_connection(monkeypatch, mod, rows=rows, columns=columns)
    monkeypatch.setattr(mod, "_REFRESH_BEFORE_BUILD", False)

    with pytest.raises(mod.CacheSnapshotValidationError) as exc_info:
        mod._build_cache_sync()

    assert exc_info.value.code == expected_code


def test_build_cache_rejects_mapping_schema_loss(monkeypatch, caplog):
    import player_stats_cache as mod

    columns, row = _source_columns_and_row(mod)
    missing_index = columns.index("LAST_REFRESH")
    columns.pop(missing_index)
    row = row[:missing_index] + row[missing_index + 1 :]
    _install_fake_stats_connection(monkeypatch, mod, rows=[row], columns=columns)
    monkeypatch.setattr(mod, "_REFRESH_BEFORE_BUILD", False)

    with pytest.raises(mod.CacheSnapshotValidationError) as exc_info:
        mod._build_cache_sync()

    assert exc_info.value.code == "source_schema_mismatch"
    assert "LAST_REFRESH" in caplog.text


def test_last_refresh_validation_normalizes_equivalent_offsets():
    import player_stats_cache as mod

    expected = "2026-08-28T08:12:00+00:00"
    assert mod._validate_last_refresh("2026-08-28T08:12:00Z") == expected
    assert mod._validate_last_refresh("2026-08-28T08:12:00+00:00") == expected
    assert mod._validate_last_refresh("2026-08-28T09:12:00+01:00") == expected


def test_build_and_persist_success_writes_atomic_and_utc(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    # Force a deterministic output from builder
    fake_out = {
        "123": {"GovernorID": "123", "STATUS": "INCLUDED", "LAST_REFRESH": "2025-01-01T00:00:00"},
        "_meta": {
            "source": "SQL:dbo.STATS_FOR_UPLOAD",
            "generated_at": "OLD",
            "count": 1,
            "source_refresh_status": "refreshed",
        },
    }
    monkeypatch.setattr(mod, "_build_cache_sync", lambda: fake_out)

    # Track atomic_write_json usage — use a list so multiple writes don't overwrite each other
    calls = {"n": 0, "paths": [], "obj": None}

    def fake_atomic_write_json(path, obj, **kwargs):
        calls["n"] += 1
        calls["paths"].append(str(path))
        calls["obj"] = obj
        # emulate write for test
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    monkeypatch.setattr("file_utils.atomic_write_json", fake_atomic_write_json)

    out = mod._build_and_persist_cache_sync()
    assert isinstance(out, dict)
    assert calls["n"] >= 1
    # The main cache_path must have been written (may not be the last write if last-KVK also writes)
    assert (
        str(cache_path) in calls["paths"]
    ), f"Expected main cache_path {cache_path} in written paths: {calls['paths']}"

    persisted = _read_json(cache_path)
    assert "_meta" in persisted
    assert persisted["_meta"]["source"] == "SQL:dbo.STATS_FOR_UPLOAD"

    # Must be UTC-aware and parseable as ISO (and NOT the old placeholder)
    ts = persisted["_meta"]["generated_at"]
    assert ts != "OLD"
    dt = datetime.fromisoformat(ts)
    assert dt.tzinfo == UTC


def test_build_and_persist_failure_preserves_existing_cache(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    # Existing cache file
    cache_path.write_text(json.dumps({"ok": True}), encoding="utf-8")

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(mod, "_build_cache_sync", boom)

    # If atomic_write_json gets called here, that's a bug (should preserve existing)
    def fail_atomic(*args, **kwargs):
        raise AssertionError("atomic_write_json should not be called when cache exists")

    monkeypatch.setattr("file_utils.atomic_write_json", fail_atomic)

    out = mod._build_and_persist_cache_sync()
    assert out["_meta"]["source_refresh_status"] == "failed"
    assert out["_meta"]["cache_write_status"] == "preserved_existing"
    assert out["_meta"]["existing_json_preserved"] is True
    assert _read_json(cache_path) == {"ok": True}


def test_build_and_persist_failure_writes_fallback_when_missing(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(mod, "_build_cache_sync", boom)

    # Avoid flaky Windows os.replace behavior: patch atomic_write_json to a deterministic writer.
    def stable_atomic_write_json(path, obj, **kwargs):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    monkeypatch.setattr("file_utils.atomic_write_json", stable_atomic_write_json)

    out = mod._build_and_persist_cache_sync()
    assert isinstance(out, dict)
    persisted = _read_json(cache_path)

    assert persisted["_meta"]["count"] == 0
    assert persisted["_meta"]["source_refresh_status"] == "failed"
    assert persisted["_meta"]["source_refresh_error_code"] == "runtimeerror_failure"
    assert "db down" not in json.dumps(persisted)

    dt = datetime.fromisoformat(persisted["_meta"]["generated_at"])
    assert dt.tzinfo == UTC


def test_build_and_persist_unexpected_write_failure_propagates(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))
    monkeypatch.setattr(
        mod,
        "_build_cache_sync",
        lambda: {
            "123": {"GovernorID": "123"},
            "_meta": {"count": 1, "source_refresh_status": "refreshed"},
        },
    )

    def fail_write(*_args, **_kwargs):
        raise OSError("simulated cache write failure")

    monkeypatch.setattr(mod, "_atomic_write_json_with_retries", fail_write)

    with pytest.raises(OSError, match="simulated cache write failure"):
        mod._build_and_persist_cache_sync()


@pytest.mark.asyncio
async def test_async_build_uses_run_blocking_in_thread(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    called = {"n": 0, "func": None}

    async def fake_run_blocking_in_thread(func, *args, **kwargs):
        called["n"] += 1
        called["func"] = func
        return func()

    monkeypatch.setattr("file_utils.run_blocking_in_thread", fake_run_blocking_in_thread)

    # IMPORTANT: do NOT monkeypatch _build_and_persist_cache_sync.
    # Patch its dependencies so it can run without DB/disk concerns.
    monkeypatch.setattr(
        mod,
        "_build_cache_sync",
        lambda: {
            "123": {"GovernorID": "123"},
            "_meta": {
                "source": "SQL:dbo.STATS_FOR_UPLOAD",
                "count": 1,
                "source_refresh_status": "refreshed",
            },
        },
    )
    monkeypatch.setattr("file_utils.atomic_write_json", lambda *a, **k: None)

    result = await mod.build_player_stats_cache()
    assert called["n"] == 1
    assert called["func"].__name__ == "_build_and_persist_cache_sync"
    assert result["_meta"]["source_refresh_status"] == "refreshed"


def test_build_and_persist_uses_acquire_lock(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    # Avoid DB work
    monkeypatch.setattr(
        mod,
        "_build_cache_sync",
        lambda: {
            "_meta": {"count": 0, "source_refresh_status": "refreshed"},
            "123": {"GovernorID": "123"},
        },
    )

    calls = {"lock_path": None, "timeout": None, "entered": 0}

    class DummyLock:
        def __enter__(self):
            calls["entered"] += 1
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_acquire_lock(path, timeout=0, poll=None):
        calls["lock_path"] = str(path)
        calls["timeout"] = timeout
        return DummyLock()

    monkeypatch.setattr("file_utils.acquire_lock", fake_acquire_lock)
    monkeypatch.setattr("file_utils.atomic_write_json", lambda *a, **k: None)

    out = mod._build_and_persist_cache_sync()
    assert isinstance(out, dict)
    assert calls["entered"] == 1
    assert calls["lock_path"] == f"{cache_path!s}.lock"
    assert calls["timeout"] == pytest.approx(float(mod._CACHE_LOCK_TIMEOUT))


def test_build_and_persist_lock_timeout_aborts_without_writing(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    def fake_acquire_lock(*a, **k):
        raise TimeoutError("simulated lock timeout")

    monkeypatch.setattr("file_utils.acquire_lock", fake_acquire_lock)

    wrote = {"n": 0}

    def fake_atomic_write_json(*a, **k):
        wrote["n"] += 1

    monkeypatch.setattr("file_utils.atomic_write_json", fake_atomic_write_json)

    out = mod._build_and_persist_cache_sync()
    assert out["_meta"]["source_refresh_status"] == "failed"
    assert out["_meta"]["cache_write_status"] == "not_written"
    assert wrote["n"] == 0


def test_map_row_uses_canonical_normalize_governor_id(monkeypatch):
    import player_stats_cache as mod

    cols = ["Governor ID", "Governor_Name", "STATUS", "LAST_REFRESH"]

    class FakeRow:
        def __init__(self, values):
            self._values = values

        def __getitem__(self, idx):
            return self._values[idx]

    # '123.0' should normalize to '123'
    row = FakeRow(["123.0", "Name", "INCLUDED", "2025-01-01T00:00:00"])
    out = mod._map_row(row, cols)
    assert isinstance(out, dict)
    assert out["GovernorID"] == "123"

    # '0' should be excluded
    row2 = FakeRow(["0", "Name", "INCLUDED", "2025-01-01T00:00:00"])
    assert mod._map_row(row2, cols) is None

    # 'nan' should be excluded
    row3 = FakeRow(["nan", "Name", "INCLUDED", "2025-01-01T00:00:00"])
    assert mod._map_row(row3, cols) is None


def test_map_row_maps_conduct_from_conduct_or_credit_and_preserves_blank_as_none():
    import player_stats_cache as mod

    class FakeRow:
        def __init__(self, values):
            self._values = values

        def __getitem__(self, idx):
            return self._values[idx]

    conduct_row = FakeRow(["123", "Name", "88.25"])
    conduct_out = mod._map_row(conduct_row, ["Governor ID", "Governor_Name", "Conduct"])
    assert conduct_out["Conduct"] == pytest.approx(88.25)

    credit_row = FakeRow(["123", "Name", "99.5"])
    credit_out = mod._map_row(credit_row, ["Governor ID", "Governor_Name", "Credit"])
    assert credit_out["Conduct"] == pytest.approx(99.5)

    blank_row = FakeRow(["123", "Name", ""])
    blank_out = mod._map_row(blank_row, ["Governor ID", "Governor_Name", "Credit"])
    assert blank_out["Conduct"] is None

    missing_row = FakeRow(["123", "Name"])
    missing_out = mod._map_row(missing_row, ["Governor ID", "Governor_Name"])
    assert missing_out["Conduct"] is None


def test_map_excel_row_maps_conduct_from_credit_and_preserves_blank_as_none():
    import player_stats_cache as mod

    class FakeRow:
        def __init__(self, values):
            self._values = values

        def __getitem__(self, idx):
            return self._values[idx]

    credit_row = FakeRow(["123", "Name", 77.75])
    credit_out = mod._map_excel_row(credit_row, ["Governor ID", "Governor_Name", "Credit"], 15)
    assert credit_out["Conduct"] == pytest.approx(77.75)
    assert credit_out["KVK_NO"] == 15

    blank_row = FakeRow(["123", "Name", None])
    blank_out = mod._map_excel_row(blank_row, ["Governor ID", "Governor_Name", "Conduct"], 15)
    assert blank_out["Conduct"] is None


def test_score_player_stats_rec_prefers_newer_datetime(monkeypatch):
    # Test the shared scoring helper directly (Phase 3)
    import utils

    a = {"STATUS": "INCLUDED", "LAST_REFRESH": "2025-01-01T00:00:00+00:00"}
    b = {"STATUS": "INCLUDED", "LAST_REFRESH": "2025-01-01T01:00:00+00:00"}

    assert utils.score_player_stats_rec(b) > utils.score_player_stats_rec(a)


def test_build_emits_telemetry_ok(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    # Avoid DB work
    monkeypatch.setattr(
        mod,
        "_build_cache_sync",
        lambda: {
            "123": {"GovernorID": "123"},
            "_meta": {
                "source": "SQL:dbo.STATS_FOR_UPLOAD",
                "count": 1,
                "source_refresh_status": "refreshed",
                "source_kvk_no": 16,
                "source_last_refresh": "2026-08-28T08:12:00",
                "source_row_count": 1,
            },
        },
    )

    # Ensure lock acquisition works
    class DummyLock:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("file_utils.acquire_lock", lambda *a, **k: DummyLock())
    monkeypatch.setattr("file_utils.atomic_write_json", lambda *a, **k: None)
    # Stub last-KVK cache builder to avoid hitting DB in unit tests
    monkeypatch.setattr(mod, "_build_last_kvk_cache_sync", lambda: None)

    events = []
    monkeypatch.setattr(
        "file_utils.emit_telemetry_event", lambda payload, **k: events.append(payload)
    )

    out = mod._build_and_persist_cache_sync()
    assert isinstance(out, dict)
    assert events, "expected telemetry event"
    cache_build_events = [e for e in events if e.get("event") == "player_stats_cache.build"]
    assert cache_build_events, "expected player_stats_cache.build telemetry event"
    assert cache_build_events[0].get("status") == "refreshed"
    assert cache_build_events[0].get("cache_path") == str(cache_path)
    assert cache_build_events[0].get("source_refresh_status") == "refreshed"
    assert cache_build_events[0].get("source_kvk_no") == 16
