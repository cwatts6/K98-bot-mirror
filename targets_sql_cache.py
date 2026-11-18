from __future__ import annotations

from collections.abc import Mapping
import os
from typing import Any

from kvk.models.kvk_target_cache import TargetCacheRefreshResult, TargetCacheSnapshot
from kvk.models.kvk_target_row import TargetRow
from kvk.services.kvk_target_publication_service import PUBLICATION_READ_FAILED
from kvk.target_cache_repository import (
    CACHE_LOCK_TIMEOUT_SECONDS as CACHE_WRITE_LOCK_TIMEOUT_SECONDS,
    CACHE_SCHEMA_VERSION,
    DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS,
    TargetCacheRepository,
    get_default_target_cache_repository,
)
from utils import normalize_governor_id


def _repository() -> TargetCacheRepository:
    return get_default_target_cache_repository()


def _maintenance_summary(
    repository: TargetCacheRepository,
    result: TargetCacheRefreshResult,
) -> dict[str, Any]:
    meta = repository.snapshot_to_cache_meta(result.snapshot)
    return {
        "_meta": meta,
        "summary": {
            "by_gov_count": len(result.snapshot.rows),
            "kvk_no": meta.get("kvk_no"),
            "publication_state": meta.get("publication_state", "UNKNOWN"),
            "publication_signature": meta.get("publication_signature"),
            "refresh_outcome": result.outcome.value,
        },
    }


def refresh_targets_cache(
    kvk_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility entrypoint for explicit target-cache maintenance refreshes."""
    repository = _repository()
    result = repository.refresh(kvk_context)
    if os.environ.get("MAINT_SUBPROC") == "1":
        return _maintenance_summary(repository, result)
    return repository.snapshot_to_cache_document(result.snapshot)


def _current_snapshot(
    kvk_context: Mapping[str, Any] | None = None,
) -> tuple[TargetCacheRepository, TargetCacheSnapshot]:
    repository = _repository()
    return repository, repository.read_snapshot(kvk_context)


def get_target_cache_entry(
    governor_id: int | str,
    kvk_context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Return the legacy row and metadata from one validated typed snapshot."""
    governor_key = normalize_governor_id(governor_id)
    if not governor_key or not governor_key.isdigit():
        return None, {
            "schema_version": CACHE_SCHEMA_VERSION,
            "kvk_no": None,
            "publication_state": "UNKNOWN",
            "publication_reason": PUBLICATION_READ_FAILED,
        }
    repository, snapshot = _current_snapshot(kvk_context)
    typed_row = snapshot.target_for(governor_key)
    row = (
        repository.target_row_to_cache_entry(snapshot, typed_row) if typed_row is not None else None
    )
    return row, repository.snapshot_to_cache_meta(snapshot)


def get_typed_target_cache_entry(
    governor_id: int | str,
    kvk_context: Mapping[str, Any] | None = None,
) -> tuple[TargetRow | None, dict[str, Any]]:
    """Return the canonical typed row and metadata from one validated snapshot."""
    governor_key = normalize_governor_id(governor_id)
    if not governor_key or not governor_key.isdigit():
        return None, {
            "schema_version": CACHE_SCHEMA_VERSION,
            "kvk_no": None,
            "publication_state": "UNKNOWN",
            "publication_reason": PUBLICATION_READ_FAILED,
        }
    repository, snapshot = _current_snapshot(kvk_context)
    return snapshot.target_for(governor_key), repository.snapshot_to_cache_meta(snapshot)


def get_current_target_cache_meta(
    kvk_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    repository, snapshot = _current_snapshot(kvk_context)
    return repository.snapshot_to_cache_meta(snapshot)


def get_targets_for_governor(governor_id: int | str) -> dict[str, Any] | None:
    row, _ = get_target_cache_entry(governor_id)
    return row


__all__ = [
    "CACHE_SCHEMA_VERSION",
    "CACHE_WRITE_LOCK_TIMEOUT_SECONDS",
    "DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS",
    "get_current_target_cache_meta",
    "get_target_cache_entry",
    "get_targets_for_governor",
    "get_typed_target_cache_entry",
    "refresh_targets_cache",
]
