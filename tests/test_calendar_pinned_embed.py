from datetime import UTC, datetime
import json
import logging
from pathlib import Path

import pytest

from event_calendar import pinned_embed as pe
import file_utils as fu


class DummyMsg:
    def __init__(self, mid=1):
        self.id = mid
        self.pinned = False
        self.edit_calls = []
        self.pin_calls = []

    async def edit(self, **kwargs):
        self.edit_calls.append(kwargs)

    async def pin(self, **kwargs):
        self.pinned = True
        self.pin_calls.append(kwargs)


class DummyChannel:
    def __init__(self):
        self.msg = DummyMsg(10)
        self.sent = []
        self.send_calls = []
        self.fetch_calls = []

    async def fetch_message(self, mid):
        self.fetch_calls.append(mid)
        if mid != self.msg.id:
            raise RuntimeError("missing")
        return self.msg

    async def send(self, **kwargs):
        m = DummyMsg(11)
        self.sent.append(m)
        self.send_calls.append(kwargs)
        return m


class DummyBot:
    def __init__(self):
        self.ch = DummyChannel()

    def get_channel(self, _):
        return self.ch


def _stub_calendar_rendering(monkeypatch):
    monkeypatch.setattr(
        pe,
        "load_runtime_cache",
        lambda: {"ok": True, "events": [], "payload": {}},
    )
    monkeypatch.setattr(pe, "stale_banner", lambda _state: None)
    monkeypatch.setattr(pe, "filter_events", lambda *args, **kwargs: [])
    monkeypatch.setattr(pe, "cache_footer", lambda _state: "footer")
    monkeypatch.setattr(pe, "build_pinned_calendar_embed", lambda **kwargs: object())
    monkeypatch.setattr(pe, "_build_view", lambda _state: object())


def test_save_tracker_hands_exact_path_and_payload_to_atomic_helper(monkeypatch, tmp_path: Path):
    tracker_path = tmp_path / "calendar_pinned_tracker.json"
    payload = {"channel_id": 123, "message_id": 456, "updated_at_utc": "stamp"}
    calls = []

    def fake_atomic_write_json(path, data, **kwargs):
        calls.append((path, data, kwargs))

    monkeypatch.setattr(pe, "_TRACKER_PATH", tracker_path)
    monkeypatch.setattr(pe, "atomic_write_json", fake_atomic_write_json)

    pe._save_tracker(payload)

    assert calls == [(tracker_path, payload, {"ensure_parent_dir": True})]
    assert calls[0][1] is payload


def test_save_and_load_tracker_round_trip_uses_real_temporary_path(monkeypatch, tmp_path: Path):
    tracker_path = tmp_path / "nested" / "calendar_pinned_tracker.json"
    payload = {
        "channel_id": 123,
        "message_id": 456,
        "updated_at_utc": "2026-09-01T12:00:00+00:00",
    }
    monkeypatch.setattr(pe, "_TRACKER_PATH", tracker_path)

    pe._save_tracker(payload)

    assert pe._load_tracker() == payload
    persisted = tracker_path.read_text(encoding="utf-8")
    assert json.loads(persisted) == payload
    assert '\n  "channel_id": 123' in persisted


def test_save_tracker_failed_replace_logs_and_preserves_prior_tracker(
    monkeypatch,
    tmp_path: Path,
    caplog,
):
    tracker_path = tmp_path / "calendar_pinned_tracker.json"
    prior = {"channel_id": 1, "message_id": 2, "updated_at_utc": "prior"}
    replacement = {"channel_id": 3, "message_id": 4, "updated_at_utc": "new"}
    pe.atomic_write_json(tracker_path, prior, ensure_parent_dir=True)
    monkeypatch.setattr(pe, "_TRACKER_PATH", tracker_path)

    def fail_replace(*_args, **_kwargs):
        raise OSError("replace blocked")

    monkeypatch.setattr(fu.os, "replace", fail_replace)

    with caplog.at_level(logging.ERROR, logger=pe.__name__):
        pe._save_tracker(replacement)

    assert json.loads(tracker_path.read_text(encoding="utf-8")) == prior
    assert not tracker_path.with_suffix(".json.tmp").exists()
    assert "[CALENDAR][PINNED] tracker save failed" in caplog.text


def test_load_tracker_returns_empty_for_missing_file(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(pe, "_TRACKER_PATH", tmp_path / "missing.json")

    assert pe._load_tracker() == {}


def test_load_tracker_logs_and_returns_empty_for_malformed_file(
    monkeypatch,
    tmp_path: Path,
    caplog,
):
    tracker_path = tmp_path / "malformed.json"
    tracker_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(pe, "_TRACKER_PATH", tracker_path)

    with caplog.at_level(logging.ERROR, logger=pe.__name__):
        assert pe._load_tracker() == {}

    assert "[CALENDAR][PINNED] tracker load failed" in caplog.text


def test_load_tracker_logs_and_returns_empty_for_unreadable_file(
    monkeypatch,
    tmp_path: Path,
    caplog,
):
    tracker_path = tmp_path / "unreadable.json"
    tracker_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(pe, "_TRACKER_PATH", tracker_path)
    real_read_text = Path.read_text

    def fail_target_read(self, *args, **kwargs):
        if self == tracker_path:
            raise OSError("read blocked")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_target_read)

    with caplog.at_level(logging.ERROR, logger=pe.__name__):
        assert pe._load_tracker() == {}

    assert "[CALENDAR][PINNED] tracker load failed" in caplog.text


@pytest.mark.asyncio
async def test_update_calendar_embed_create_persists_loaded_shape(monkeypatch):
    tracker = {"retained": "value"}
    saved = []
    telemetry = []
    monkeypatch.setattr(pe, "_load_tracker", lambda: tracker)
    monkeypatch.setattr(pe, "_save_tracker", lambda data: saved.append(dict(data)))
    monkeypatch.setattr(pe, "emit_telemetry_event", telemetry.append)
    _stub_calendar_rendering(monkeypatch)
    b = DummyBot()

    out = await pe.update_calendar_embed(b, 123)

    assert out["ok"] is True
    assert out["status"] == "created"
    assert out["message_id"] == 11
    assert saved == [{"retained": "value", "channel_id": 123, "message_id": 11}]
    assert "updated_at_utc" not in saved[0]
    assert len(b.ch.sent) == 1
    assert b.ch.sent[0].pinned is True
    assert telemetry == [{"event": "calendar_pinned_embed_update", "status": "created", "ok": True}]


@pytest.mark.asyncio
async def test_update_calendar_embed_edit_persists_exact_payload_without_duplicate_send(
    monkeypatch,
):
    saved = []
    telemetry = []
    fixed_now = datetime(2026, 9, 1, 12, 34, 56, tzinfo=UTC)
    monkeypatch.setattr(
        pe,
        "_load_tracker",
        lambda: {
            "channel_id": 123,
            "message_id": 10,
            "updated_at_utc": "old",
            "discarded_on_edit": True,
        },
    )
    monkeypatch.setattr(pe, "_save_tracker", lambda data: saved.append(dict(data)))
    monkeypatch.setattr(pe, "emit_telemetry_event", telemetry.append)
    monkeypatch.setattr(pe, "now_utc", lambda: fixed_now)
    _stub_calendar_rendering(monkeypatch)
    b = DummyBot()

    out = await pe.update_calendar_embed(b, 123)

    assert out == {"ok": True, "status": "edited", "message_id": 10, "events": 0}
    assert saved == [
        {
            "channel_id": 123,
            "message_id": 10,
            "updated_at_utc": fixed_now.isoformat(),
        }
    ]
    assert len(b.ch.msg.edit_calls) == 1
    assert b.ch.sent == []
    assert b.ch.msg.pinned is True
    assert telemetry == [{"event": "calendar_pinned_embed_update", "status": "edited", "ok": True}]


@pytest.mark.asyncio
async def test_update_calendar_embed_save_failure_still_returns_edited(
    monkeypatch,
    tmp_path: Path,
    caplog,
):
    tracker_path = tmp_path / "calendar_pinned_tracker.json"
    prior = {"channel_id": 123, "message_id": 10, "updated_at_utc": "prior"}
    pe.atomic_write_json(tracker_path, prior, ensure_parent_dir=True)
    monkeypatch.setattr(pe, "_TRACKER_PATH", tracker_path)
    monkeypatch.setattr(
        pe,
        "atomic_write_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("write failed")),
    )
    monkeypatch.setattr(pe, "emit_telemetry_event", lambda _payload: None)
    _stub_calendar_rendering(monkeypatch)
    b = DummyBot()

    with caplog.at_level(logging.ERROR, logger=pe.__name__):
        out = await pe.update_calendar_embed(b, 123)

    assert out == {"ok": True, "status": "edited", "message_id": 10, "events": 0}
    assert json.loads(tracker_path.read_text(encoding="utf-8")) == prior
    assert "[CALENDAR][PINNED] tracker save failed" in caplog.text


@pytest.mark.asyncio
async def test_rehydrate_pinned_calendar_view_edits_existing_message_view(monkeypatch):
    view = object()
    monkeypatch.setattr(pe, "_load_tracker", lambda: {"channel_id": 123, "message_id": 10})
    monkeypatch.setattr(
        pe,
        "load_runtime_cache",
        lambda: {"ok": True, "events": [], "payload": {}},
    )
    monkeypatch.setattr(pe, "_build_view", lambda _state: view)
    monkeypatch.setattr(
        pe,
        "_save_tracker",
        lambda _data: pytest.fail("valid rehydration must not rewrite the tracker"),
    )
    b = DummyBot()

    out = await pe.rehydrate_pinned_calendar_view(b)

    assert out == {"ok": True, "status": "rehydrated"}
    assert b.ch.msg.edit_calls == [{"view": view}]
    assert b.ch.sent == []


@pytest.mark.asyncio
async def test_rehydrate_pinned_calendar_view_missing_target_clears_tracker(monkeypatch):
    saved = []
    monkeypatch.setattr(pe, "_load_tracker", lambda: {"channel_id": 123, "message_id": 999})
    monkeypatch.setattr(pe, "_save_tracker", lambda data: saved.append(dict(data)))
    b = DummyBot()

    out = await pe.rehydrate_pinned_calendar_view(b)

    assert out == {"ok": False, "status": "message_or_channel_missing"}
    assert saved == [{}]
    assert b.ch.sent == []
