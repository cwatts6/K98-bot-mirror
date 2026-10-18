from __future__ import annotations

from datetime import UTC, datetime

from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
from kvk.models.kvk_target_row import TargetRow
from kvk.target_cache_repository import TargetCacheRepository
import targets_sql_cache as cache


def _repository(tmp_path) -> TargetCacheRepository:
    metadata = TargetPublicationMetadata(
        publication_id=1,
        kvk_no=16,
        publication_state="OFFICIAL",
        source_scan_order=1059,
        source_scan_type="MATCHMAKING_SCAN",
        configured_draft_scan=1040,
        configured_matchmaking_scan=1059,
        published_at_utc=datetime(2026, 8, 27, 12, tzinfo=UTC),
        target_row_count=1,
        output_object_name="dbo.EXCEL_EXPORT_KVK_TARGETS_16",
        publication_version=1,
        publication_signature="2ad2a141-c5bf-4075-927b-832e44477e55",
    )
    publication = TargetPublicationSnapshot(
        metadata,
        (TargetRow("123", "Alice", 1000, 100, 200, 10, 50, 1, 16),),
    )
    return TargetCacheRepository(
        tmp_path / "targets.json",
        context_provider=lambda: {
            "kvk_no": 16,
            "state": "DRAFT",
            "state_reason": "test",
        },
        metadata_fetcher=lambda _kvk_no: metadata,
        publication_fetcher=lambda _kvk_no: publication,
    )


def test_maintenance_subprocess_result_contains_summary_not_player_rows(monkeypatch, tmp_path):
    repository = _repository(tmp_path)
    monkeypatch.setattr(cache, "_repository", lambda: repository)
    monkeypatch.setenv("MAINT_SUBPROC", "1")

    result = cache.refresh_targets_cache()

    assert "by_gov" not in result
    assert result["summary"] == {
        "by_gov_count": 1,
        "kvk_no": 16,
        "publication_state": "OFFICIAL",
        "publication_signature": "2ad2a141-c5bf-4075-927b-832e44477e55",
        "refresh_outcome": "REFRESHED",
    }


def test_non_subprocess_result_preserves_full_schema_two_cache(monkeypatch, tmp_path):
    repository = _repository(tmp_path)
    monkeypatch.setattr(cache, "_repository", lambda: repository)
    monkeypatch.setenv("MAINT_SUBPROC", "0")

    result = cache.refresh_targets_cache()

    assert "summary" not in result
    assert result["_meta"]["schema_version"] == 2
    assert result["by_gov"]["123"]["GovernorName"] == "Alice"
