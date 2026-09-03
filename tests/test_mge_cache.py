from __future__ import annotations

from datetime import UTC, datetime

import mge.mge_cache as cache


def test_build_commanders_cache_success(monkeypatch):
    written = {}
    sample = [
        {
            "CommanderId": 1,
            "CommanderName": "Attila",
            "IsActive": True,
            "ReleaseStartUtc": None,
            "ReleaseEndUtc": None,
        }
    ]

    monkeypatch.setattr(cache, "fetch_active_commanders", lambda: sample)
    monkeypatch.setattr(
        cache,
        "atomic_write_json",
        lambda path, obj: written.update({"path": path, "obj": obj}),
    )

    assert cache.build_commanders_cache() is True
    assert written["obj"][0]["CommanderName"] == "Attila"


def test_build_commanders_cache_blank_does_not_write(monkeypatch):
    called = {"write": False}
    monkeypatch.setattr(cache, "fetch_active_commanders", lambda: [])
    monkeypatch.setattr(
        cache,
        "atomic_write_json",
        lambda path, obj: called.update({"write": True}),
    )

    assert cache.build_commanders_cache() is False
    assert called["write"] is False


def test_build_commanders_cache_malformed_does_not_write(monkeypatch):
    called = {"write": False}
    monkeypatch.setattr(cache, "fetch_active_commanders", lambda: [{"CommanderId": 1}])
    monkeypatch.setattr(
        cache,
        "atomic_write_json",
        lambda path, obj: called.update({"write": True}),
    )

    assert cache.build_commanders_cache() is False
    assert called["write"] is False


def test_build_variant_cache_success(monkeypatch):
    written = {}
    sample = [
        {
            "VariantCommanderId": 10,
            "VariantId": 1,
            "CommanderId": 1,
            "VariantName": "Infantry",
            "CommanderName": "Ivar",
        }
    ]

    monkeypatch.setattr(cache, "fetch_active_variant_commanders", lambda: sample)
    monkeypatch.setattr(
        cache,
        "atomic_write_json",
        lambda path, obj: written.update({"path": path, "obj": obj}),
    )

    assert cache.build_variant_commanders_cache() is True
    assert written["obj"][0]["VariantName"] == "Infantry"


def test_build_variant_cache_blank_does_not_write(monkeypatch):
    called = {"write": False}
    monkeypatch.setattr(cache, "fetch_active_variant_commanders", lambda: [])
    monkeypatch.setattr(
        cache,
        "atomic_write_json",
        lambda path, obj: called.update({"write": True}),
    )

    assert cache.build_variant_commanders_cache() is False
    assert called["write"] is False


def test_is_commander_available_date_window():
    now = datetime(2026, 3, 11, 12, 0, 0, tzinfo=UTC)
    commander = {
        "IsActive": True,
        "ReleaseStartUtc": datetime(2026, 3, 1, 0, 0, 0),
        "ReleaseEndUtc": datetime(2026, 3, 31, 0, 0, 0),
    }
    assert cache.is_commander_available(commander, as_of=now) is True


def test_get_commanders_for_variant(monkeypatch):
    monkeypatch.setattr(
        cache,
        "read_variant_commanders_cache",
        lambda: [
            {"VariantName": "Infantry", "CommanderName": "Ivar"},
            {"VariantName": "Cavalry", "CommanderName": "Attila"},
        ],
    )

    result = cache.get_commanders_for_variant("Infantry")
    assert len(result) == 1
    assert result[0]["CommanderName"] == "Ivar"


def test_read_cache_safe_default(monkeypatch):
    monkeypatch.setattr(cache, "read_json_safe", lambda path, default=None: None)
    assert cache.read_commanders_cache() == []
    assert cache.read_variant_commanders_cache() == []
