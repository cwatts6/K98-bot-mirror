from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime

from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
from kvk.models.kvk_target_row import TargetRow
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
        TargetRow("123", "Alice", 1000, 100, 200, 10, 50, 1, 16),
        TargetRow("456", "Bob", 2000, 120, 240, 12, 60, 2, 16),
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


def test_refresh_persists_verified_publication_with_unset_target_amounts(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    snapshot = _snapshot()
    rows = tuple(
        replace(
            row,
            dkp_target=None,
            kill_target=None,
            deads_target=None,
            min_kill_target=None,
        )
        for row in snapshot.rows
    )
    _install_sql_snapshot(
        monkeypatch,
        TargetPublicationSnapshot(snapshot.metadata, rows),
    )

    result = cache.refresh_targets_cache()

    assert result["_meta"]["publication_state"] == "OFFICIAL"
    assert result["by_gov"]["123"]["Kill_Target"] is None
    row, meta = cache.get_target_cache_entry("123")
    assert row is not None
    assert row["DKP_Target"] is None
    assert meta["publication_state"] == "OFFICIAL"


def test_typed_cache_entry_deserializes_schema_two_row(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())
    cache.refresh_targets_cache()

    row, meta = cache.get_typed_target_cache_entry("123")

    assert row == TargetRow("123", "Alice", 1000, 100, 200, 10, 50, 1, 16)
    assert meta["publication_state"] == "OFFICIAL"


def test_schema_two_cache_rejects_missing_canonical_target_field(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())
    cache.refresh_targets_cache()
    persisted = cache._read_json(str(cache_path))
    del persisted["by_gov"]["123"]["Kill_Target"]
    cache._write_json(str(cache_path), persisted)
    monkeypatch.setattr(cache, "fetch_current_publication_metadata", lambda _kvk_no: None)

    row, meta = cache.get_typed_target_cache_entry("123")

    assert row is None
    assert meta["publication_state"] == "UNKNOWN"


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
    clock = [0.0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: clock[0])
    _install_sql_snapshot(monkeypatch, _snapshot(state="DRAFT"))
    cache.refresh_targets_cache()

    official = _snapshot(version=2)
    _install_sql_snapshot(monkeypatch, official)
    clock[0] += cache.DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS + 1
    row, meta = cache.get_target_cache_entry("123")

    assert row is not None
    assert row["TargetState"] == "OFFICIAL"
    assert meta["publication_state"] == "OFFICIAL"
    assert meta["publication_version"] == 2


def test_draft_cache_hot_reads_poll_metadata_once_per_interval(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    clock = [100.0]
    monkeypatch.setattr(cache.time, "monotonic", lambda: clock[0])
    draft = _snapshot(state="DRAFT")
    _install_sql_snapshot(monkeypatch, draft)
    cache.refresh_targets_cache()

    metadata_reads: list[int] = []

    def fetch_metadata(kvk_no: int) -> TargetPublicationMetadata:
        metadata_reads.append(kvk_no)
        return draft.metadata

    monkeypatch.setattr(cache, "fetch_current_publication_metadata", fetch_metadata)

    first_row, first_meta = cache.get_target_cache_entry("123")
    second_row, second_meta = cache.get_target_cache_entry("456")

    assert first_row is not None
    assert second_row is not None
    assert first_meta["publication_state"] == "DRAFT"
    assert second_meta["publication_state"] == "DRAFT"
    assert metadata_reads == []

    clock[0] += cache.DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS + 1
    cache.get_target_cache_entry("123")
    cache.get_target_cache_entry("456")

    assert metadata_reads == [16]


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


def test_invalid_cache_reports_refresh_failure_reason(monkeypatch, tmp_path):
    cache_path = tmp_path / "targets.json"
    cache_path.write_text(
        '{"_meta":{"kvk_no":16,"state":"ACTIVE"},"by_gov":{}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(cache_path))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    monkeypatch.setattr(
        cache,
        "fetch_current_publication_metadata",
        lambda _kvk_no: (_ for _ in ()).throw(RuntimeError("temporary SQL outage")),
    )

    row, meta = cache.get_target_cache_entry("123")

    assert row is None
    assert meta["publication_state"] == "UNKNOWN"
    assert meta["publication_reason"] == cache.PUBLICATION_READ_FAILED


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


def test_disabled_maintenance_subprocess_marker_returns_full_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("MAINT_SUBPROC", "0")
    monkeypatch.setattr(cache, "PLAYER_TARGETS_CACHE", str(tmp_path / "targets.json"))
    monkeypatch.setattr(cache, "get_kvk_context_today", lambda: _context())
    _install_sql_snapshot(monkeypatch, _snapshot())

    result = cache.refresh_targets_cache()

    assert "summary" not in result
    assert len(result["by_gov"]) == 2
