from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import os

from event_calendar import runtime_cache as rc


def test_load_runtime_cache_missing(monkeypatch, tmp_path):
    p = tmp_path / "event_calendar_cache.json"
    monkeypatch.setattr(rc, "EVENT_CALENDAR_CACHE_FILE_PATH", str(p))
    out = rc.load_runtime_cache()
    assert out["ok"] is False
    assert out["error"] == "cache_missing"


def test_load_runtime_cache_stale(monkeypatch, tmp_path):
    p = tmp_path / "event_calendar_cache.json"
    p.write_text(json.dumps({"events": []}), encoding="utf-8")

    old = datetime.now(UTC) - timedelta(minutes=300)
    ts = old.timestamp()
    os.utime(p, (ts, ts))

    monkeypatch.setattr(rc, "EVENT_CALENDAR_CACHE_FILE_PATH", str(p))
    monkeypatch.setattr(rc, "EVENT_CALENDAR_STALE_WARN_MINUTES", 60)
    monkeypatch.setattr(rc, "EVENT_CALENDAR_STALE_DEGRADED_MINUTES", 240)

    out = rc.load_runtime_cache()
    assert out["ok"] is True
    assert out["degraded"] is True
    assert rc.stale_banner(out) is not None
