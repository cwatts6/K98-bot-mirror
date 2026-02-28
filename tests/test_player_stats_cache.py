from datetime import UTC, datetime
import json
from pathlib import Path

import pytest


def _read_json(p: Path) -> dict:
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def test_build_and_persist_success_writes_atomic_and_utc(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    # Force a deterministic output from builder
    fake_out = {
        "123": {"GovernorID": "123", "STATUS": "INCLUDED", "LAST_REFRESH": "2025-01-01T00:00:00"},
        "_meta": {"source": "SQL:dbo.STATS_FOR_UPLOAD", "generated_at": "OLD", "count": 1},
    }
    monkeypatch.setattr(mod, "_build_cache_sync", lambda: fake_out)

    # Track atomic_write_json usage
    calls = {"n": 0, "path": None, "obj": None}

    def fake_atomic_write_json(path, obj, **kwargs):
        calls["n"] += 1
        calls["path"] = str(path)
        calls["obj"] = obj
        # emulate write for test
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    monkeypatch.setattr("file_utils.atomic_write_json", fake_atomic_write_json)

    out = mod._build_and_persist_cache_sync()
    assert isinstance(out, dict)
    assert calls["n"] == 1
    assert calls["path"] == str(cache_path)

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
    assert out is None
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
    assert "error" in persisted["_meta"]

    dt = datetime.fromisoformat(persisted["_meta"]["generated_at"])
    assert dt.tzinfo == UTC


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
            "_meta": {"source": "SQL:dbo.STATS_FOR_UPLOAD", "count": 1},
        },
    )
    monkeypatch.setattr("file_utils.atomic_write_json", lambda *a, **k: None)

    await mod.build_player_stats_cache()
    assert called["n"] == 1
    assert called["func"].__name__ == "_build_and_persist_cache_sync"


def test_build_and_persist_uses_acquire_lock(monkeypatch, tmp_path):
    import player_stats_cache as mod

    cache_path = tmp_path / "player_stats_cache.json"
    monkeypatch.setattr(mod, "PLAYER_STATS_CACHE", str(cache_path))

    # Avoid DB work
    monkeypatch.setattr(
        mod, "_build_cache_sync", lambda: {"_meta": {"count": 0}, "123": {"GovernorID": "123"}}
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
    assert out is None
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
            "_meta": {"source": "SQL:dbo.STATS_FOR_UPLOAD", "count": 1},
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

    events = []
    monkeypatch.setattr(
        "file_utils.emit_telemetry_event", lambda payload, **k: events.append(payload)
    )

    out = mod._build_and_persist_cache_sync()
    assert isinstance(out, dict)
    assert events, "expected telemetry event"
    assert events[-1].get("event") == "player_stats_cache.build"
    assert events[-1].get("status") == "ok"
    assert events[-1].get("cache_path") == str(cache_path)
