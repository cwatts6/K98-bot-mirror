from __future__ import annotations

from collections.abc import Mapping
import json
import logging
import os
import threading
import time
from typing import Any

from filelock import FileLock

from constants import PLAYER_TARGETS_CACHE
from file_utils import atomic_json_write
from kvk.dal.kvk_target_publication_dal import (
    TargetPublicationContractError,
    fetch_current_publication_metadata,
    fetch_current_target_publication,
)
from kvk.models.kvk_target_publication import TargetPublicationMetadata
from kvk.services.kvk_target_publication_service import (
    CACHE_ROW_INVALID,
    LEGACY_CACHE_UNVERIFIED,
    MISSING_PUBLICATION_METADATA,
    PUBLICATION_READ_FAILED,
    metadata_to_cache_fields,
    parse_target_publication_metadata,
    resolve_target_publication_state,
)
from kvk_state import get_kvk_context_today
from utils import normalize_governor_id, utcnow

logger = logging.getLogger(__name__)

CACHE_SCHEMA_VERSION = 2
CACHE_WRITE_LOCK_TIMEOUT_SECONDS = 5.0
DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS = 60.0

_draft_poll_lock = threading.Lock()
_draft_poll_deadlines: dict[tuple[str, int, int, str], float] = {}


def _read_json(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except Exception:
        logger.debug("target_publication_cache_read_failed path=%s", path, exc_info=True)
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: str, data: dict[str, Any]) -> None:
    atomic_json_write(path, data)


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        converted = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return converted if converted > 0 else None


def _context() -> dict[str, Any] | None:
    try:
        raw = get_kvk_context_today()
    except Exception:
        logger.exception("target_publication_kvk_context_failed")
        return None
    if not isinstance(raw, Mapping):
        return None
    kvk_no = _positive_int(raw.get("kvk_no"))
    if kvk_no is None:
        return None
    return dict(raw)


def _bound_context(kvk_context: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if kvk_context is None:
        return _context()
    if _positive_int(kvk_context.get("kvk_no")) is None:
        return None
    return dict(kvk_context)


def _cache_parts(cache: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    meta = cache.get("_meta")
    by_gov = cache.get("by_gov")
    return (
        dict(meta) if isinstance(meta, Mapping) else {},
        dict(by_gov) if isinstance(by_gov, Mapping) else {},
    )


def _validate_cache(
    cache: Mapping[str, Any],
    ctx: Mapping[str, Any],
) -> tuple[TargetPublicationMetadata, str, str] | None:
    meta, by_gov = _cache_parts(cache)
    if meta.get("schema_version") != CACHE_SCHEMA_VERSION:
        return None
    metadata = parse_target_publication_metadata(meta)
    resolution = resolve_target_publication_state(
        metadata,
        requested_kvk_no=_positive_int(ctx.get("kvk_no")),
        fighting_state=str(ctx.get("state") or ""),
        observed_row_count=len(by_gov),
    )
    if metadata is None or not resolution.is_verified:
        return None
    for governor_id, row in by_gov.items():
        if not isinstance(row, Mapping):
            return None
        if normalize_governor_id(row.get("GovernorID")) != str(governor_id):
            return None
        if _positive_int(row.get("KVK_NO")) != metadata.kvk_no:
            return None
        for field in ("DKP_Target", "Kill_Target", "Deads_Target", "Min_Kill_Target"):
            value = row.get(field)
            if value in (None, ""):
                continue
            if isinstance(value, bool):
                return None
            try:
                if int(value) < 0:
                    return None
            except (TypeError, ValueError, OverflowError):
                return None
    return metadata, resolution.state, resolution.reason


def _cache_failure_reason(cache: Mapping[str, Any], ctx: Mapping[str, Any]) -> str:
    meta, by_gov = _cache_parts(cache)
    if not cache:
        return MISSING_PUBLICATION_METADATA
    if meta.get("schema_version") != CACHE_SCHEMA_VERSION:
        return LEGACY_CACHE_UNVERIFIED
    metadata = parse_target_publication_metadata(meta)
    resolution = resolve_target_publication_state(
        metadata,
        requested_kvk_no=_positive_int(ctx.get("kvk_no")),
        fighting_state=str(ctx.get("state") or ""),
        observed_row_count=len(by_gov),
    )
    if not resolution.is_verified:
        return resolution.reason
    return CACHE_ROW_INVALID


def _unknown_meta(ctx: Mapping[str, Any] | None, reason: str) -> dict[str, Any]:
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "kvk_no": _positive_int((ctx or {}).get("kvk_no")),
        "publication_state": "UNKNOWN",
        "publication_reason": reason,
    }


def _resolved_cache_copy(
    cache: Mapping[str, Any],
    ctx: Mapping[str, Any],
) -> dict[str, Any]:
    validated = _validate_cache(cache, ctx)
    if validated is None:
        return {}
    _, state, reason = validated
    meta, by_gov = _cache_parts(cache)
    meta["publication_state"] = state
    meta["publication_reason"] = reason
    meta["kvk_fighting_state"] = str(ctx.get("state") or "") or None
    meta["kvk_fighting_state_reason"] = ctx.get("state_reason")
    rows: dict[str, Any] = {}
    for governor_id, raw_row in by_gov.items():
        row = dict(raw_row)
        row["TargetState"] = state
        row["PublicationReason"] = reason
        row["TargetSourceScan"] = meta.get("target_source_scan")
        row["TargetSourceType"] = meta.get("target_source_type")
        row["TargetPublishedAt"] = meta.get("target_published_at")
        row["PublicationVersion"] = meta.get("publication_version")
        row["PublicationSignature"] = meta.get("publication_signature")
        rows[str(governor_id)] = row
    return {"_meta": meta, "by_gov": rows}


def _summary(cache: Mapping[str, Any]) -> dict[str, Any]:
    meta, by_gov = _cache_parts(cache)
    return {
        "_meta": meta,
        "summary": {
            "by_gov_count": len(by_gov),
            "kvk_no": meta.get("kvk_no"),
            "publication_state": meta.get("publication_state", "UNKNOWN"),
            "publication_signature": meta.get("publication_signature"),
        },
    }


def _result(cache: dict[str, Any]) -> dict[str, Any]:
    return _summary(cache) if os.environ.get("MAINT_SUBPROC") == "1" else cache


def _last_known_good(
    existing: Mapping[str, Any],
    ctx: Mapping[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    if ctx is not None:
        resolved = _resolved_cache_copy(existing, ctx)
        if resolved:
            logger.warning(
                "target_publication_using_last_known_good kvk_no=%s reason=%s state=%s",
                (resolved.get("_meta") or {}).get("kvk_no"),
                reason,
                (resolved.get("_meta") or {}).get("publication_state"),
            )
            return resolved
    return {"_meta": _unknown_meta(ctx, reason), "by_gov": {}}


def _same_publication(
    cached: TargetPublicationMetadata | None,
    current: TargetPublicationMetadata | None,
) -> bool:
    return (
        cached is not None
        and current is not None
        and cached.cache_identity is not None
        and cached.cache_identity == current.cache_identity
    )


def _draft_poll_key(
    metadata: TargetPublicationMetadata,
) -> tuple[str, int, int, str] | None:
    identity = metadata.cache_identity
    if identity is None:
        return None
    kvk_no, publication_version, publication_signature = identity
    return (
        os.path.abspath(PLAYER_TARGETS_CACHE),
        kvk_no,
        publication_version,
        publication_signature,
    )


def _claim_draft_publication_poll(metadata: TargetPublicationMetadata) -> bool:
    """Bound hot-path Draft metadata polling to once per publication interval."""
    key = _draft_poll_key(metadata)
    if key is None:
        return True
    now = time.monotonic()
    with _draft_poll_lock:
        if now < _draft_poll_deadlines.get(key, 0.0):
            return False
        _draft_poll_deadlines.clear()
        _draft_poll_deadlines[key] = now + DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS
    return True


def _mark_draft_publication_polled(metadata: TargetPublicationMetadata) -> None:
    key = _draft_poll_key(metadata)
    if key is None:
        return
    with _draft_poll_lock:
        _draft_poll_deadlines.clear()
        _draft_poll_deadlines[key] = time.monotonic() + DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS


def _disk_has_newer_publication(
    snapshot: TargetPublicationMetadata,
    ctx: Mapping[str, Any],
) -> dict[str, Any] | None:
    disk_cache = _read_json(PLAYER_TARGETS_CACHE)
    validated = _validate_cache(disk_cache, ctx)
    if validated is None:
        return None
    disk_metadata = validated[0]
    if disk_metadata.kvk_no != snapshot.kvk_no:
        return None
    disk_version = disk_metadata.publication_version or 0
    snapshot_version = snapshot.publication_version or 0
    if disk_version > snapshot_version:
        return _resolved_cache_copy(disk_cache, ctx)
    if disk_version == snapshot_version and disk_metadata.cache_identity != snapshot.cache_identity:
        logger.error(
            "target_publication_conflicting_identity kvk_no=%s version=%s",
            snapshot.kvk_no,
            snapshot_version,
        )
        return _resolved_cache_copy(disk_cache, ctx)
    return None


def _build_cache(
    metadata: TargetPublicationMetadata,
    rows: tuple[Mapping[str, Any], ...],
    ctx: Mapping[str, Any],
) -> dict[str, Any]:
    resolution = resolve_target_publication_state(
        metadata,
        requested_kvk_no=_positive_int(ctx.get("kvk_no")),
        fighting_state=str(ctx.get("state") or ""),
        observed_row_count=len(rows),
    )
    if not resolution.is_verified:
        raise TargetPublicationContractError(
            f"Target publication failed cache validation: {resolution.reason}."
        )
    written_at = utcnow().isoformat()
    meta = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "generated_at": written_at,
        "cache_written_at_utc": written_at,
        **metadata_to_cache_fields(metadata),
        "publication_state": resolution.state,
        "publication_reason": resolution.reason,
        "kvk_fighting_state": str(ctx.get("state") or "") or None,
        "kvk_fighting_state_reason": ctx.get("state_reason"),
    }
    by_gov: dict[str, dict[str, Any]] = {}
    for raw_row in rows:
        row = dict(raw_row)
        governor_id = normalize_governor_id(row.get("GovernorID"))
        row["GovernorID"] = governor_id
        row["KVK_NO"] = metadata.kvk_no
        row["TargetState"] = resolution.state
        row["PublicationReason"] = resolution.reason
        row["TargetSourceScan"] = metadata.source_scan_order
        row["TargetSourceType"] = metadata.source_scan_type
        row["TargetPublishedAt"] = meta["target_published_at"]
        row["PublicationVersion"] = metadata.publication_version
        row["PublicationSignature"] = metadata.publication_signature
        by_gov[governor_id] = row
    return {"_meta": meta, "by_gov": by_gov}


def refresh_targets_cache(
    kvk_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Refresh the target cache only when verified publication identity changes."""
    existing = _read_json(PLAYER_TARGETS_CACHE)
    ctx = _bound_context(kvk_context)
    if ctx is None:
        return _result(_last_known_good(existing, None, PUBLICATION_READ_FAILED))
    kvk_no = _positive_int(ctx.get("kvk_no"))
    if kvk_no is None:
        return _result(_last_known_good(existing, ctx, PUBLICATION_READ_FAILED))

    valid_existing = _validate_cache(existing, ctx)
    try:
        current_metadata = fetch_current_publication_metadata(kvk_no)
    except Exception:
        logger.exception("target_publication_metadata_read_failed kvk_no=%s", kvk_no)
        return _result(_last_known_good(existing, ctx, PUBLICATION_READ_FAILED))
    if current_metadata is None:
        return _result(_last_known_good(existing, ctx, MISSING_PUBLICATION_METADATA))

    current_resolution = resolve_target_publication_state(
        current_metadata,
        requested_kvk_no=kvk_no,
        fighting_state=str(ctx.get("state") or ""),
    )
    if not current_resolution.is_verified:
        logger.error(
            "target_publication_metadata_invalid kvk_no=%s reason=%s",
            kvk_no,
            current_resolution.reason,
        )
        return _result(_last_known_good(existing, ctx, current_resolution.reason))

    if current_resolution.state == "DRAFT":
        _mark_draft_publication_polled(current_metadata)

    if valid_existing and _same_publication(valid_existing[0], current_metadata):
        return _result(_resolved_cache_copy(existing, ctx))

    try:
        snapshot = fetch_current_target_publication(kvk_no)
    except Exception:
        logger.exception("target_publication_rowset_read_failed kvk_no=%s", kvk_no)
        return _result(_last_known_good(existing, ctx, PUBLICATION_READ_FAILED))
    if snapshot is None:
        return _result(_last_known_good(existing, ctx, MISSING_PUBLICATION_METADATA))

    if not _same_publication(current_metadata, snapshot.metadata):
        logger.info("target_publication_changed_during_refresh kvk_no=%s", kvk_no)
        try:
            snapshot = fetch_current_target_publication(kvk_no)
        except Exception:
            logger.exception("target_publication_retry_failed kvk_no=%s", kvk_no)
            return _result(_last_known_good(existing, ctx, PUBLICATION_READ_FAILED))
        if snapshot is None:
            return _result(_last_known_good(existing, ctx, MISSING_PUBLICATION_METADATA))

    try:
        data = _build_cache(snapshot.metadata, snapshot.rows, ctx)
    except TargetPublicationContractError:
        logger.exception("target_publication_cache_build_failed kvk_no=%s", kvk_no)
        return _result(_last_known_good(existing, ctx, PUBLICATION_READ_FAILED))

    try:
        lock_directory = os.path.dirname(PLAYER_TARGETS_CACHE)
        if lock_directory:
            os.makedirs(lock_directory, exist_ok=True)
        with FileLock(
            f"{PLAYER_TARGETS_CACHE}.lock",
            timeout=CACHE_WRITE_LOCK_TIMEOUT_SECONDS,
        ):
            newer = _disk_has_newer_publication(snapshot.metadata, ctx)
            if newer is not None:
                return _result(newer)
            _write_json(PLAYER_TARGETS_CACHE, data)
    except Exception:
        logger.exception("target_publication_cache_write_failed path=%s", PLAYER_TARGETS_CACHE)
        disk_fallback = _last_known_good(
            _read_json(PLAYER_TARGETS_CACHE), ctx, PUBLICATION_READ_FAILED
        )
        if disk_fallback.get("by_gov") or {}:
            return _result(disk_fallback)
        fallback = _last_known_good(existing, ctx, PUBLICATION_READ_FAILED)
        if fallback.get("by_gov") or {}:
            return _result(fallback)
    return _result(data)


def _load_current_cache(
    kvk_context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = _bound_context(kvk_context)
    if ctx is None:
        return {}, _unknown_meta(None, PUBLICATION_READ_FAILED)
    existing = _read_json(PLAYER_TARGETS_CACHE)
    validated = _validate_cache(existing, ctx)
    if validated is None:
        cache_reason = _cache_failure_reason(existing, ctx)
        refreshed = refresh_targets_cache(ctx)
        refreshed_meta, _ = _cache_parts(refreshed)
        if "summary" in refreshed:
            refreshed = _read_json(PLAYER_TARGETS_CACHE)
        resolved = _resolved_cache_copy(refreshed, ctx)
        if not resolved:
            refresh_reason = refreshed_meta.get("publication_reason")
            return {}, _unknown_meta(
                ctx,
                str(refresh_reason) if refresh_reason else cache_reason,
            )
        return _cache_parts(resolved)[1], _cache_parts(resolved)[0]

    metadata, state, _ = validated
    if state == "DRAFT" and _claim_draft_publication_poll(metadata):
        refreshed = refresh_targets_cache(ctx)
        if "summary" in refreshed:
            refreshed = _read_json(PLAYER_TARGETS_CACHE)
        resolved = _resolved_cache_copy(refreshed, ctx)
    else:
        resolved = _resolved_cache_copy(existing, ctx)
    if not resolved:
        return {}, _unknown_meta(ctx, PUBLICATION_READ_FAILED)
    meta, by_gov = _cache_parts(resolved)
    if _positive_int(meta.get("kvk_no")) != metadata.kvk_no:
        return {}, _unknown_meta(ctx, PUBLICATION_READ_FAILED)
    return by_gov, meta


def get_target_cache_entry(
    governor_id: int | str,
    kvk_context: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Return a row and its metadata from the same validated cache snapshot."""
    governor_key = normalize_governor_id(governor_id)
    if not governor_key or not governor_key.isdigit():
        return None, _unknown_meta(None, PUBLICATION_READ_FAILED)
    by_gov, meta = _load_current_cache(kvk_context)
    row = by_gov.get(governor_key)
    return (dict(row) if isinstance(row, Mapping) else None), dict(meta)


def get_current_target_cache_meta(
    kvk_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return current-KVK verified cache metadata, or explicit Unknown metadata."""
    _, meta = _load_current_cache(kvk_context)
    return meta


def get_targets_for_governor(governor_id: int | str) -> dict[str, Any] | None:
    row, _ = get_target_cache_entry(governor_id)
    return row
