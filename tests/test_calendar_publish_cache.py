from __future__ import annotations

from datetime import UTC, datetime
import json

from event_calendar import cache_publisher as mod


def test_build_event_type_index_payload_groups_and_sorts():
    payload = {
        "generated_utc": "2026-03-06T00:00:00+00:00",
        "events": [
            {"instance_id": "2", "type": "war"},
            {"instance_id": "1", "type": "war"},
            {"instance_id": "3", "type": "raid"},
        ],
    }
    out = mod.build_event_type_index_payload(
        payload=payload,
        horizon_days=365,
        generated_utc=payload["generated_utc"],
    )
    assert out["event_type_index"]["war"] == ["1", "2"]
    assert out["event_type_index"]["raid"] == ["3"]


def test_publish_preserve_on_empty(monkeypatch, tmp_path):
    cache_path = tmp_path / "event_calendar_cache.json"
    index_path = tmp_path / "event_type_index.json"
    cache_path.write_text('{"events":[{"instance_id":"x"}]}', encoding="utf-8")

    monkeypatch.setattr(mod, "_CACHE_PATH", cache_path)
    monkeypatch.setattr(mod, "_TYPE_INDEX_PATH", index_path)
    monkeypatch.setattr(mod, "load_runtime_instances", lambda *_a, **_k: [])

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(mod, "get_conn_with_retries", lambda **_k: _Conn())

    out = mod.publish_event_calendar_cache(horizon_days=7, force_empty=False)
    assert out.ok is True
    assert out.status == "skipped_empty_preserve_existing"


def test_publish_writes_two_files(monkeypatch, tmp_path):
    cache_path = tmp_path / "event_calendar_cache.json"
    index_path = tmp_path / "event_type_index.json"

    monkeypatch.setattr(mod, "_CACHE_PATH", cache_path)
    monkeypatch.setattr(mod, "_TYPE_INDEX_PATH", index_path)

    instances = [
        {
            "instance_id": 1,
            "title": "A",
            "type": "war",
            "start_utc": datetime(2026, 3, 7, 0, 0, tzinfo=UTC),
            "end_utc": datetime(2026, 3, 7, 1, 0, tzinfo=UTC),
        }
    ]

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(mod, "get_conn_with_retries", lambda **_k: _Conn())
    monkeypatch.setattr(mod, "load_runtime_instances", lambda *_a, **_k: instances)

    out = mod.publish_event_calendar_cache(horizon_days=30, force_empty=False)
    assert out.ok is True
    assert cache_path.exists()
    assert index_path.exists()

    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    idx = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(cache["events"]) == 1
    assert "war" in idx["event_type_index"]
