from contextlib import nullcontext
import hashlib
import json
from unittest.mock import Mock

import pytest


def setup(monkeypatch, tmp_path):
    import file_utils
    import player_stats_cache as cache

    target = tmp_path / "cache.json"
    target.write_text('{"old": true}', encoding="utf-8")
    monkeypatch.setattr(cache, "PLAYER_STATS_CACHE", str(target))
    monkeypatch.setattr(file_utils, "acquire_lock", lambda *a, **k: nullcontext())
    data = {
        "123": {"GovernorID": "123"},
        "_meta": {
            "source_last_refresh": "2026-09-29T14:44:00",
            "source_kvk_no": 16,
            "source_row_count": 1,
            "source_refresh_status": "skipped",
        },
    }
    build = Mock(return_value=data)
    monkeypatch.setattr(cache, "_build_cache_sync", build)
    return cache, target, build


def test_cache_rebuild_reads_without_producer_and_verifies_written_bytes(monkeypatch, tmp_path):
    cache, target, build = setup(monkeypatch, tmp_path)
    receipt = cache.rebuild_validated_cache_only()
    build.assert_called_once_with(refresh=False)
    assert receipt["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert receipt["source_last_refresh"] == "2026-09-29T14:44:00"
    assert json.loads(target.read_bytes())["_meta"]["cache_write_status"] == "written"


def test_invalid_sql_preserves_existing_cache_without_fallback(monkeypatch, tmp_path):
    cache, target, build = setup(monkeypatch, tmp_path)
    before = target.read_bytes()
    build.side_effect = cache.CacheSnapshotValidationError("source_kvk_mismatch")
    with pytest.raises(cache.CacheSnapshotValidationError):
        cache.rebuild_validated_cache_only()
    assert target.read_bytes() == before


def test_changed_readback_cannot_issue_receipt(monkeypatch, tmp_path):
    cache, target, _ = setup(monkeypatch, tmp_path)
    monkeypatch.setattr(
        cache,
        "_atomic_write_json_with_retries",
        lambda *a: target.write_text('{"other":true}', encoding="utf-8"),
    )
    with pytest.raises(cache.CacheSnapshotValidationError, match="cache_readback_differs"):
        cache.rebuild_validated_cache_only()
