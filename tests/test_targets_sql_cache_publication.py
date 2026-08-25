from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
import targets_sql_cache as cache


def _context(*, kvk_no: int = 16, state: str = "DRAFT") -> dict[str, object]:
    return {
        "kvk_no": kvk_no,
        "kvk_name": "KVK",
        "state": state,
        "state_reason": "test_fighting_state",
    }


def _metadata(*, state: str = "OFFICIAL", version: int = 1) -> TargetPublicationMetadata:
    official = state == "OFFICIAL"
    return TargetPublicationMetadata(
        publication_id=40 + version,
        kvk_no=16,
        publication_state=state,
        source_scan_order=1059 if official else 1040,
        source_scan_type="MATCHMAKING_SCAN" if official else "DRAFTSCAN",
        configured_draft_scan=1040,
        configured_matchmaking_scan=1059,
        published_at_utc=datetime(2026, 8, 25, 12, version, tzinfo=UTC),
        target_row_count=2,
        output_object_name="dbo.EXCEL_EXPORT_KVK_TARGETS_16",
        publication_version=version,
        publication_signature=(
            "2ad2a141-c5bf-4075-927b-832e44477e55"
            if version == 1
            else "b2a3f1f3-5470-42fa-a98c-ae797f23c669"
        ),
    )


def _snapshot(*, state: str = "OFFICIAL", version: int = 1) -> TargetPublicationSnapshot:
    rows = (
        {
            "GovernorID": "123",
            "GovernorName": "Alice",
            "Power": 1000,
            "DKP_Target": 100,
            "Kill_Target": 200,
            "Deads_Target": 10,
            "Min_Kill_Target": 50,
            "TargetRank": 1,
            "KVK_NO": 16,
        },
        {
            "GovernorID": "456",
            "GovernorName": "Bob",
            "Power": 2000,
            "DKP_Target": 120,
            "Kill_Target": 240,
            "Deads_Target": 12,
            "Min_Kill_Target": 60,
            "TargetRank": 2,
            "KVK_NO": 16,
        },
    )
    return TargetPublicationSnapshot(_metadata(state=state, version=version), rows)


def _install_sql_snapshot(monkeypatch, snapshot: TargetPublicationSnapshot) -> None:
    monkeypatch.setattr(
        cache,
        "fetch_current_publication_metadata",
        lambda _kvk_no: snapshot.metadata,
    )
    monkeypatch.setattr(
        cache,
        "fetch_current_target_publication",
        lambda _kvk_no: snapshot,
    )


def test_refresh_persists_verified_official_publication(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())

    result = cache.refresh_targets_cache()

    assert result["_meta"]["schema_version"] == 2
    assert result["_meta"]["publication_state"] == "OFFICIAL"
    assert result["_meta"]["persisted_publication_state"] == "OFFICIAL"
    assert result["_meta"]["target_source_scan"] == 1059
    assert result["_meta"]["publication_version"] == 1
    assert result["by_gov"]["123"]["TargetState"] == "OFFICIAL"
    assert result["by_gov"]["123"]["TargetSourceScan"] == 1059
    assert result["by_gov"]["123"]["PublicationReason"] == "matchmaking_source_confirmed"
    assert cache_path.exists()


def test_matching_official_identity_is_not_rewritten_and_becomes_historic_live(
    monkeypatch, tmp_path
):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    fighting = _context()
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: fighting)
    snapshot = _snapshot()
    _install_sql_snapshot(monkeypatch, snapshot)
    cache.refresh_targets_cache()
    original_bytes = cache_path.read_bytes()

    monkeypatch.setattr(
        cache,
        "fetch_current_target_publication",
        lambda _kvk_no: (_ for _ in ()).throw(AssertionError("full rowset should not be read")),
    )
    fighting["state"] = "ENDED"
    result = cache.refresh_targets_cache()

    assert result["_meta"]["publication_state"] == "HISTORIC"
    assert result["by_gov"]["123"]["TargetState"] == "HISTORIC"
    assert cache_path.read_bytes() == original_bytes


def test_draft_cache_refreshes_to_new_official_identity(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot(state="DRAFT"))
    cache.refresh_targets_cache()

    official = _snapshot(version=2)
    _install_sql_snapshot(monkeypatch, official)
    row, meta = cache.get_target_cache_entry("123")

    assert row is not None
    assert row["TargetState"] == "OFFICIAL"
    assert meta["publication_state"] == "OFFICIAL"
    assert meta["publication_version"] == 2


def test_matching_last_known_good_official_survives_transient_sql_failure(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())
    cache.refresh_targets_cache()
    monkeypatch.setattr(
        cache,
        "fetch_current_publication_metadata",
        lambda _kvk_no: (_ for _ in ()).throw(RuntimeError("temporary SQL outage")),
    )

    result = cache.refresh_targets_cache()

    assert result["_meta"]["publication_state"] == "OFFICIAL"
    assert result["by_gov"]["123"]["GovernorName"] == "Alice"


def test_cache_write_lock_rechecks_disk_after_waiting_writer(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    context = _context()
    older = _snapshot(version=1)
    newer = _snapshot(version=2)
    _install_sql_snapshot(monkeypatch, older)

    @contextmanager
    def publish_newer_before_older_enters(_path, **_kwargs):
        cache._write_json(
            str(cache_path),
            cache._build_cache(newer.metadata, newer.rows, context),
        )
        yield

    monkeypatch.setattr(cache, "FileLock", publish_newer_before_older_enters)

    result = cache.refresh_targets_cache(context)

    assert result["_meta"]["publication_version"] == 2
    assert cache._read_json(str(cache_path))["_meta"]["publication_version"] == 2


def test_explicit_context_is_reused_for_refresh_and_lookup(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(
        cache,
        "get_kvk_context_today",
        lambda: (_ for _ in ()).throw(AssertionError("context must remain bound")),
    )
    context = _context()
    _install_sql_snapshot(monkeypatch, _snapshot())

    cache.refresh_targets_cache(context)
    row, meta = cache.get_target_cache_entry("123", context)

    assert row is not None
    assert row["KVK_NO"] == 16
    assert meta["kvk_no"] == 16


def test_previous_kvk_cache_is_never_served_as_current(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())
    cache.refresh_targets_cache()

    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context(kvk_no=17))
    monkeypatch.setattr(cache, "fetch_current_publication_metadata", lambda _kvk_no: None)
    row, meta = cache.get_target_cache_entry("123")

    assert row is None
    assert meta["kvk_no"] == 17
    assert meta["publication_state"] == "UNKNOWN"


def test_legacy_cache_is_unverified_and_not_served(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    cache_path.write_text(
        '{"_meta":{"kvk_no":16,"state":"ACTIVE"},'
        '"by_gov":{"123":{"GovernorID":"123","TargetState":"ACTIVE"}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    monkeypatch.setattr(cache, "fetch_current_publication_metadata", lambda _kvk_no: None)

    row, meta = cache.get_target_cache_entry("123")

    assert row is None
    assert meta["publication_state"] == "UNKNOWN"


def test_maintenance_subprocess_returns_provenance_summary(monkeypatch, tmp_path):
    monkeypatch.setenv("MAINT_SUBPROC", "1")
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(tmp_path / "targets.json"))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())

    result = cache.refresh_targets_cache()

    assert "by_gov" not in result
    assert result["summary"]["by_gov_count"] == 2
    assert result["summary"]["publication_state"] == "OFFICIAL"
    assert result["summary"]["publication_signature"]
