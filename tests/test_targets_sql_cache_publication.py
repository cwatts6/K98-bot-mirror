from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json

from kvk.dal import kvk_targets_dal
from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
from kvk.models.kvk_target_row import TargetRow
from kvk.target_cache_repository import TargetCacheRepository
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


def _install_repository(monkeypatch, tmp_path, snapshot=None, context=None):
    installed = snapshot or _snapshot()
    ctx = context or _context()
    repository = TargetCacheRepository(
        tmp_path / "targets.json",
        context_provider=lambda: ctx,
        metadata_fetcher=lambda _kvk_no: installed.metadata,
        publication_fetcher=lambda _kvk_no: installed,
    )
    monkeypatch.setattr(cache, "_repository", lambda: repository)
    return repository


def test_refresh_persists_verified_official_publication(monkeypatch, tmp_path):
    repository = _install_repository(monkeypatch, tmp_path)

    result = cache.refresh_targets_cache()

    assert result["_meta"]["schema_version"] == 2
    assert result["_meta"]["publication_state"] == "OFFICIAL"
    assert result["_meta"]["persisted_publication_state"] == "OFFICIAL"
    assert result["_meta"]["target_source_scan"] == 1059
    assert result["_meta"]["publication_version"] == 1
    assert result["by_gov"]["123"]["TargetState"] == "OFFICIAL"
    assert result["by_gov"]["123"]["TargetSourceScan"] == 1059
    assert result["by_gov"]["123"]["PublicationReason"] == "matchmaking_source_confirmed"
    assert (tmp_path / "targets.json").exists()
    assert repository.coordination_path.endswith("targets.json.coordination.json")


def test_refresh_preserves_nullable_target_amounts(monkeypatch, tmp_path):
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
    _install_repository(
        monkeypatch,
        tmp_path,
        TargetPublicationSnapshot(snapshot.metadata, rows),
    )

    result = cache.refresh_targets_cache()
    row, meta = cache.get_typed_target_cache_entry("123")

    assert result["by_gov"]["123"]["Kill_Target"] is None
    assert row is not None and row.dkp_target is None
    assert meta["publication_state"] == "OFFICIAL"


def test_single_row_and_meta_reads_do_not_serialize_full_snapshot(monkeypatch, tmp_path):
    repository = _install_repository(monkeypatch, tmp_path)
    cache.refresh_targets_cache()
    monkeypatch.setattr(
        repository,
        "snapshot_to_cache_document",
        lambda _snapshot: (_ for _ in ()).throw(
            AssertionError("hot-path lookup must not serialize all target rows")
        ),
    )

    legacy_row, legacy_meta = cache.get_target_cache_entry("123")
    typed_row, typed_meta = cache.get_typed_target_cache_entry("123")
    current_meta = cache.get_current_target_cache_meta()

    assert legacy_row is not None and legacy_row["GovernorID"] == "123"
    assert typed_row is not None and typed_row.governor_id == "123"
    assert legacy_meta == typed_meta == current_meta


def test_dal_invalid_target_entry_uses_shared_cache_schema_version(monkeypatch):
    monkeypatch.setattr(kvk_targets_dal, "CACHE_SCHEMA_VERSION", 99)

    row, meta = kvk_targets_dal.fetch_target_entry("not-a-governor-id")

    assert row is None
    assert meta["schema_version"] == 99


def test_schema_two_cache_rejects_missing_canonical_field(monkeypatch, tmp_path):
    repository = _install_repository(monkeypatch, tmp_path)
    cache.refresh_targets_cache()
    document = json.loads((tmp_path / "targets.json").read_text(encoding="utf-8"))
    del document["by_gov"]["123"]["Kill_Target"]
    (tmp_path / "targets.json").write_text(json.dumps(document), encoding="utf-8")
    repository._metadata_fetcher = lambda _kvk_no: None

    row, meta = cache.get_typed_target_cache_entry("123")

    assert row is None
    assert meta["publication_state"] == "UNKNOWN"


def test_matching_official_identity_is_not_rewritten_and_projects_historic(monkeypatch, tmp_path):
    fighting = _context()
    repository = _install_repository(monkeypatch, tmp_path, context=fighting)
    cache.refresh_targets_cache()
    original_bytes = (tmp_path / "targets.json").read_bytes()
    repository._publication_fetcher = lambda _kvk_no: (_ for _ in ()).throw(
        AssertionError("full rowset should not be read")
    )
    fighting["state"] = "ENDED"

    result = cache.refresh_targets_cache()

    assert result["_meta"]["publication_state"] == "HISTORIC"
    assert result["by_gov"]["123"]["TargetState"] == "HISTORIC"
    assert (tmp_path / "targets.json").read_bytes() == original_bytes


def test_previous_kvk_cache_is_never_served_as_current(monkeypatch, tmp_path):
    context = _context()
    repository = _install_repository(monkeypatch, tmp_path, context=context)
    cache.refresh_targets_cache()
    context["kvk_no"] = 17
    repository._metadata_fetcher = lambda _kvk_no: None

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
    repository = TargetCacheRepository(
        cache_path,
        context_provider=lambda: _context(),
        metadata_fetcher=lambda _kvk_no: None,
    )
    monkeypatch.setattr(cache, "_repository", lambda: repository)

    row, meta = cache.get_target_cache_entry("123")

    assert row is None
    assert meta["publication_state"] == "UNKNOWN"


def test_explicit_context_is_reused_for_refresh_and_lookup(monkeypatch, tmp_path):
    repository = TargetCacheRepository(
        tmp_path / "targets.json",
        context_provider=lambda: (_ for _ in ()).throw(AssertionError("context must remain bound")),
        metadata_fetcher=lambda _kvk_no: _snapshot().metadata,
        publication_fetcher=lambda _kvk_no: _snapshot(),
    )
    monkeypatch.setattr(cache, "_repository", lambda: repository)

    cache.refresh_targets_cache(_context())
    row, meta = cache.get_target_cache_entry("123", _context())

    assert row is not None and row["KVK_NO"] == 16
    assert meta["kvk_no"] == 16


def test_invalid_governor_id_fails_without_reading_cache(monkeypatch):
    monkeypatch.setattr(
        cache,
        "_repository",
        lambda: (_ for _ in ()).throw(AssertionError("cache must not be read")),
    )

    row, meta = cache.get_typed_target_cache_entry("not-a-governor")

    assert row is None
    assert meta["publication_state"] == "UNKNOWN"
