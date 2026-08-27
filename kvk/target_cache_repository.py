from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any
from uuid import uuid4

from filelock import FileLock

from constants import PLAYER_TARGETS_CACHE
from file_utils import atomic_json_write
from kvk.dal.kvk_target_publication_dal import (
    TargetPublicationContractError,
    fetch_current_publication_metadata,
    fetch_current_target_publication,
)
from kvk.models.kvk_target_cache import (
    TargetCacheRefreshOutcome,
    TargetCacheRefreshResult,
    TargetCacheSnapshot,
)
from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
from kvk.models.kvk_target_row import (
    TargetRowContractError,
    serialize_target_row,
    target_row_from_mapping,
)
from kvk.services.kvk_target_publication_service import (
    CACHE_ROW_INVALID,
    MISSING_PUBLICATION_METADATA,
    PUBLICATION_READ_FAILED,
    metadata_to_cache_fields,
    parse_target_publication_metadata,
    resolve_target_publication_state,
)
from kvk_state import get_kvk_context_today
from process_utils import get_process_info, matches_process

logger = logging.getLogger(__name__)

CACHE_SCHEMA_VERSION = 2
COORDINATION_SCHEMA_VERSION = 1
CACHE_LOCK_TIMEOUT_SECONDS = 5.0
REFRESH_LEASE_SECONDS = 60.0
FOLLOWER_WAIT_SECONDS = 5.0
FOLLOWER_POLL_SECONDS = 0.05
DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS = 60.0

_COORDINATION_OWNERSHIP_LOST = "coordination_ownership_lost"
_COORDINATION_WAIT_EXPIRED = "coordination_wait_expired"
_PUBLICATION_DOWNGRADE_REJECTED = "publication_downgrade_rejected"
_PUBLICATION_IDENTITY_CONFLICT = "publication_identity_conflict"


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        converted = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return converted if converted > 0 else None


def _utc_iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, UTC).isoformat()


def _epoch(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.timestamp()


class TargetCacheRepository:
    """Own target cache validation, refresh, serialization, and single-flight state."""

    def __init__(
        self,
        cache_path: str | Path,
        *,
        context_provider: Callable[[], Mapping[str, Any] | None] = get_kvk_context_today,
        metadata_fetcher: Callable[[int], TargetPublicationMetadata | None] = (
            fetch_current_publication_metadata
        ),
        publication_fetcher: Callable[[int], TargetPublicationSnapshot | None] = (
            fetch_current_target_publication
        ),
        wall_clock: Callable[[], float] = time.time,
        sleeper: Callable[[float], None] = time.sleep,
        process_matcher: Callable[..., bool] = matches_process,
        lease_seconds: float = REFRESH_LEASE_SECONDS,
        follower_wait_seconds: float = FOLLOWER_WAIT_SECONDS,
        follower_poll_seconds: float = FOLLOWER_POLL_SECONDS,
        draft_poll_seconds: float = DRAFT_PUBLICATION_POLL_INTERVAL_SECONDS,
    ) -> None:
        self.cache_path = str(Path(cache_path).resolve())
        self.lock_path = f"{self.cache_path}.lock"
        self.coordination_path = f"{self.cache_path}.coordination.json"
        self._context_provider = context_provider
        self._metadata_fetcher = metadata_fetcher
        self._publication_fetcher = publication_fetcher
        self._wall_clock = wall_clock
        self._sleeper = sleeper
        self._process_matcher = process_matcher
        self._lease_seconds = max(0.01, float(lease_seconds))
        self._follower_wait_seconds = max(0.0, float(follower_wait_seconds))
        self._follower_poll_seconds = max(0.001, float(follower_poll_seconds))
        self._draft_poll_seconds = max(0.0, float(draft_poll_seconds))

    def read_snapshot(
        self,
        kvk_context: Mapping[str, Any] | None = None,
    ) -> TargetCacheSnapshot:
        """Return one validated current-KVK snapshot, refreshing only when required."""
        ctx = self._bound_context(kvk_context)
        if ctx is None:
            return self._unknown_snapshot(None, PUBLICATION_READ_FAILED)
        snapshot = self._read_validated_snapshot(ctx)
        if snapshot is None:
            return self.refresh(ctx).snapshot
        if snapshot.publication_state != "DRAFT":
            return snapshot
        return self.refresh(ctx, respect_draft_poll=True).snapshot

    def refresh(
        self,
        kvk_context: Mapping[str, Any] | None = None,
        *,
        respect_draft_poll: bool = False,
    ) -> TargetCacheRefreshResult:
        """Refresh through one bounded, crash-recoverable cross-process owner."""
        result = self._refresh(kvk_context, respect_draft_poll=respect_draft_poll)
        if result.outcome != TargetCacheRefreshOutcome.REUSED or not respect_draft_poll:
            metadata = result.snapshot.metadata
            logger.info(
                "target_cache_refresh_outcome outcome=%s kvk_no=%s state=%s version=%s "
                "signature=%s reason=%s",
                result.outcome.value,
                result.snapshot.requested_kvk_no,
                result.snapshot.publication_state,
                metadata.publication_version if metadata else None,
                metadata.publication_signature if metadata else None,
                result.reason,
            )
        return result

    def _refresh(
        self,
        kvk_context: Mapping[str, Any] | None = None,
        *,
        respect_draft_poll: bool = False,
    ) -> TargetCacheRefreshResult:
        ctx = self._bound_context(kvk_context)
        if ctx is None:
            return self._result_without_owner(
                None,
                TargetCacheRefreshOutcome.UNAVAILABLE,
                PUBLICATION_READ_FAILED,
            )
        kvk_no = _positive_int(ctx.get("kvk_no"))
        if kvk_no is None:
            return self._result_without_owner(
                ctx,
                TargetCacheRefreshOutcome.UNAVAILABLE,
                PUBLICATION_READ_FAILED,
            )

        try:
            claim, token, snapshot = self._claim_refresh(ctx, respect_draft_poll)
        except Exception:
            logger.exception("target_publication_coordination_claim_failed kvk_no=%s", kvk_no)
            return self._result_without_owner(
                ctx,
                TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD,
                PUBLICATION_READ_FAILED,
            )
        if claim == "reuse":
            assert snapshot is not None
            return TargetCacheRefreshResult(
                TargetCacheRefreshOutcome.REUSED,
                snapshot,
                snapshot.publication_reason,
            )
        if claim == "follower":
            if snapshot is not None:
                return TargetCacheRefreshResult(
                    TargetCacheRefreshOutcome.REUSED,
                    snapshot,
                    snapshot.publication_reason,
                )
            return self._wait_for_owner(ctx)
        assert token is not None

        try:
            current_metadata = self._metadata_fetcher(kvk_no)
        except Exception:
            logger.exception("target_publication_metadata_read_failed kvk_no=%s", kvk_no)
            return self._finish_failure(
                token,
                ctx,
                TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD,
                PUBLICATION_READ_FAILED,
            )
        if current_metadata is None:
            return self._finish_failure(
                token,
                ctx,
                TargetCacheRefreshOutcome.FAILED_CLOSED,
                MISSING_PUBLICATION_METADATA,
            )

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
            return self._finish_failure(
                token,
                ctx,
                TargetCacheRefreshOutcome.REJECTED_MISMATCH,
                current_resolution.reason,
            )

        disk_snapshot = self._read_validated_snapshot(ctx)
        if self._same_publication(
            disk_snapshot.metadata if disk_snapshot else None,
            current_metadata,
        ):
            assert disk_snapshot is not None
            return self._finish_reuse(token, ctx, disk_snapshot, current_metadata)

        try:
            publication = self._publication_fetcher(kvk_no)
        except Exception:
            logger.exception("target_publication_rowset_read_failed kvk_no=%s", kvk_no)
            return self._finish_failure(
                token,
                ctx,
                TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD,
                PUBLICATION_READ_FAILED,
            )
        if publication is None:
            return self._finish_failure(
                token,
                ctx,
                TargetCacheRefreshOutcome.FAILED_CLOSED,
                MISSING_PUBLICATION_METADATA,
            )

        if not self._same_publication(current_metadata, publication.metadata):
            logger.info("target_publication_changed_during_refresh kvk_no=%s", kvk_no)
            try:
                publication = self._publication_fetcher(kvk_no)
            except Exception:
                logger.exception("target_publication_retry_failed kvk_no=%s", kvk_no)
                return self._finish_failure(
                    token,
                    ctx,
                    TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD,
                    PUBLICATION_READ_FAILED,
                )
            if publication is None or not self._same_publication(
                current_metadata, publication.metadata
            ):
                return self._finish_failure(
                    token,
                    ctx,
                    TargetCacheRefreshOutcome.REJECTED_MISMATCH,
                    _PUBLICATION_IDENTITY_CONFLICT,
                )

        try:
            candidate = self._snapshot_from_publication(publication, ctx)
            document = self.snapshot_to_cache_document(candidate)
        except Exception:
            logger.exception("target_publication_cache_build_failed kvk_no=%s", kvk_no)
            return self._finish_failure(
                token,
                ctx,
                TargetCacheRefreshOutcome.FAILED_CLOSED,
                CACHE_ROW_INVALID,
            )

        return self._commit_candidate(token, ctx, candidate, document)

    def snapshot_to_cache_document(
        self,
        snapshot: TargetCacheSnapshot,
    ) -> dict[str, Any]:
        """Serialize a typed snapshot to the stable schema-version-2 cache document."""
        if not snapshot.is_verified or snapshot.metadata is None:
            return {
                "_meta": {
                    "schema_version": CACHE_SCHEMA_VERSION,
                    "kvk_no": snapshot.requested_kvk_no,
                    "publication_state": "UNKNOWN",
                    "publication_reason": snapshot.publication_reason,
                },
                "by_gov": {},
            }
        metadata = snapshot.metadata
        written_at = snapshot.cache_written_at_utc or datetime.now(UTC).isoformat()
        meta = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "generated_at": snapshot.generated_at or written_at,
            "cache_written_at_utc": written_at,
            **metadata_to_cache_fields(metadata),
            "publication_state": snapshot.publication_state,
            "publication_reason": snapshot.publication_reason,
            "kvk_fighting_state": snapshot.kvk_fighting_state,
            "kvk_fighting_state_reason": snapshot.kvk_fighting_state_reason,
        }
        by_gov: dict[str, dict[str, Any]] = {}
        for typed_row in snapshot.rows:
            row = serialize_target_row(typed_row)
            row["TargetState"] = snapshot.publication_state
            row["PublicationReason"] = snapshot.publication_reason
            row["TargetSourceScan"] = metadata.source_scan_order
            row["TargetSourceType"] = metadata.source_scan_type
            row["TargetPublishedAt"] = meta.get("target_published_at")
            row["PublicationVersion"] = metadata.publication_version
            row["PublicationSignature"] = metadata.publication_signature
            by_gov[typed_row.governor_id] = row
        return {"_meta": meta, "by_gov": by_gov}

    def _bound_context(
        self,
        kvk_context: Mapping[str, Any] | None,
    ) -> dict[str, Any] | None:
        if kvk_context is None:
            try:
                kvk_context = self._context_provider()
            except Exception:
                logger.exception("target_publication_kvk_context_failed")
                return None
        if not isinstance(kvk_context, Mapping):
            return None
        if _positive_int(kvk_context.get("kvk_no")) is None:
            return None
        return dict(kvk_context)

    def _read_json(self, path: str) -> dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as handle:
                value = json.load(handle)
        except FileNotFoundError:
            return {}
        except Exception:
            logger.debug("target_publication_json_read_failed path=%s", path, exc_info=True)
            return {}
        return value if isinstance(value, dict) else {}

    def _read_validated_snapshot(
        self,
        ctx: Mapping[str, Any],
    ) -> TargetCacheSnapshot | None:
        return self._snapshot_from_document(self._read_json(self.cache_path), ctx)

    def _snapshot_from_document(
        self,
        document: Mapping[str, Any],
        ctx: Mapping[str, Any],
    ) -> TargetCacheSnapshot | None:
        raw_meta = document.get("_meta")
        raw_rows = document.get("by_gov")
        if not isinstance(raw_meta, Mapping) or not isinstance(raw_rows, Mapping):
            return None
        if raw_meta.get("schema_version") != CACHE_SCHEMA_VERSION:
            return None
        metadata = parse_target_publication_metadata(raw_meta)
        resolution = resolve_target_publication_state(
            metadata,
            requested_kvk_no=_positive_int(ctx.get("kvk_no")),
            fighting_state=str(ctx.get("state") or ""),
            observed_row_count=len(raw_rows),
        )
        if metadata is None or not resolution.is_verified:
            return None
        rows = []
        for governor_id, raw_row in raw_rows.items():
            if not isinstance(raw_row, Mapping):
                return None
            try:
                typed_row = target_row_from_mapping(
                    raw_row,
                    expected_kvk_no=metadata.kvk_no,
                )
            except TargetRowContractError:
                return None
            if typed_row.governor_id != str(governor_id):
                return None
            rows.append(typed_row)
        rows.sort(
            key=lambda row: ((row.target_rank is None), row.target_rank or 0, row.governor_id)
        )
        return TargetCacheSnapshot(
            requested_kvk_no=_positive_int(ctx.get("kvk_no")),
            metadata=metadata,
            rows=tuple(rows),
            publication_state=resolution.state,
            publication_reason=resolution.reason,
            cache_written_at_utc=(
                str(raw_meta.get("cache_written_at_utc"))
                if raw_meta.get("cache_written_at_utc")
                else None
            ),
            generated_at=(
                str(raw_meta.get("generated_at")) if raw_meta.get("generated_at") else None
            ),
            kvk_fighting_state=str(ctx.get("state") or "") or None,
            kvk_fighting_state_reason=(
                str(ctx.get("state_reason")) if ctx.get("state_reason") else None
            ),
        )

    def _snapshot_from_publication(
        self,
        publication: TargetPublicationSnapshot,
        ctx: Mapping[str, Any],
    ) -> TargetCacheSnapshot:
        metadata = publication.metadata
        rows = publication.rows
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
        seen: set[str] = set()
        for row in rows:
            if row.kvk_no != metadata.kvk_no or row.governor_id in seen:
                raise TargetPublicationContractError(
                    "Target publication rows did not match their publication identity."
                )
            seen.add(row.governor_id)
        written_at = _utc_iso(self._wall_clock())
        return TargetCacheSnapshot(
            requested_kvk_no=_positive_int(ctx.get("kvk_no")),
            metadata=metadata,
            rows=tuple(rows),
            publication_state=resolution.state,
            publication_reason=resolution.reason,
            cache_written_at_utc=written_at,
            generated_at=written_at,
            kvk_fighting_state=str(ctx.get("state") or "") or None,
            kvk_fighting_state_reason=(
                str(ctx.get("state_reason")) if ctx.get("state_reason") else None
            ),
        )

    def _claim_refresh(
        self,
        ctx: Mapping[str, Any],
        respect_draft_poll: bool,
    ) -> tuple[str, str | None, TargetCacheSnapshot | None]:
        self._ensure_parent()
        with FileLock(self.lock_path, timeout=CACHE_LOCK_TIMEOUT_SECONDS):
            snapshot = self._read_validated_snapshot(ctx)
            coordination = self._read_coordination()
            now = self._wall_clock()
            if (
                respect_draft_poll
                and snapshot is not None
                and self._draft_poll_active(coordination, snapshot, now)
            ):
                return "reuse", None, snapshot

            active = coordination.get("active_refresh")
            if (
                isinstance(active, Mapping)
                and _positive_int(active.get("requested_kvk_no"))
                == _positive_int(ctx.get("kvk_no"))
                and self._active_owner_is_current(active, now)
            ):
                return "follower", None, snapshot

            token = uuid4().hex
            process_info = get_process_info(os.getpid())
            coordination["active_refresh"] = {
                "requested_kvk_no": _positive_int(ctx.get("kvk_no")),
                "owner_token": token,
                "owner_pid": os.getpid(),
                "owner_executable": process_info.get("exe") or sys.executable,
                "owner_process_created_at_utc": (
                    _utc_iso(float(process_info["create_time"]))
                    if process_info.get("create_time") is not None
                    else None
                ),
                "claimed_at_utc": _utc_iso(now),
                "lease_expires_at_utc": _utc_iso(now + self._lease_seconds),
            }
            if respect_draft_poll and snapshot is not None:
                self._set_draft_poll(coordination, snapshot, now)
            self._write_coordination(coordination)
            return "owner", token, snapshot

    def _wait_for_owner(self, ctx: Mapping[str, Any]) -> TargetCacheRefreshResult:
        deadline = self._wall_clock() + self._follower_wait_seconds
        while self._wall_clock() < deadline:
            snapshot = self._read_validated_snapshot(ctx)
            if snapshot is not None:
                return TargetCacheRefreshResult(
                    TargetCacheRefreshOutcome.REUSED,
                    snapshot,
                    snapshot.publication_reason,
                )
            self._sleeper(self._follower_poll_seconds)
            coordination = self._read_coordination()
            active = coordination.get("active_refresh")
            if (
                not isinstance(active, Mapping)
                or _positive_int(active.get("requested_kvk_no")) != _positive_int(ctx.get("kvk_no"))
                or not self._active_owner_is_current(active, self._wall_clock())
            ):
                completed = self._read_validated_snapshot(ctx)
                if completed is not None:
                    return TargetCacheRefreshResult(
                        TargetCacheRefreshOutcome.REUSED,
                        completed,
                        completed.publication_reason,
                    )
                return self.refresh(ctx)
        return TargetCacheRefreshResult(
            TargetCacheRefreshOutcome.FAILED_CLOSED,
            self._unknown_snapshot(ctx, _COORDINATION_WAIT_EXPIRED),
            _COORDINATION_WAIT_EXPIRED,
        )

    def _active_owner_is_current(self, active: Mapping[str, Any], now: float) -> bool:
        expires_at = _epoch(active.get("lease_expires_at_utc"))
        claimed_at = _epoch(active.get("claimed_at_utc"))
        owner_token = active.get("owner_token")
        if (
            not isinstance(owner_token, str)
            or not owner_token
            or claimed_at is None
            or expires_at is None
            or claimed_at > now + 1.0
            or expires_at <= claimed_at
            or expires_at > claimed_at + self._lease_seconds + 1.0
            or expires_at <= now
        ):
            return False
        pid = _positive_int(active.get("owner_pid"))
        if pid is None:
            return False
        return bool(
            self._process_matcher(
                pid,
                exe_path=(
                    str(active.get("owner_executable")) if active.get("owner_executable") else None
                ),
                created_before=claimed_at,
            )
        )

    def _draft_poll_active(
        self,
        coordination: Mapping[str, Any],
        snapshot: TargetCacheSnapshot,
        now: float,
    ) -> bool:
        poll = coordination.get("draft_poll")
        identity = snapshot.metadata.cache_identity if snapshot.metadata else None
        if not isinstance(poll, Mapping) or identity is None:
            return False
        return (
            _positive_int(poll.get("kvk_no")) == identity[0]
            and _positive_int(poll.get("publication_version")) == identity[1]
            and str(poll.get("publication_signature") or "") == identity[2]
            and (_epoch(poll.get("not_before_utc")) or 0.0) > now
        )

    def _set_draft_poll(
        self,
        coordination: dict[str, Any],
        snapshot: TargetCacheSnapshot,
        now: float,
    ) -> None:
        identity = snapshot.metadata.cache_identity if snapshot.metadata else None
        if identity is None or snapshot.publication_state != "DRAFT":
            coordination.pop("draft_poll", None)
            return
        coordination["draft_poll"] = {
            "kvk_no": identity[0],
            "publication_version": identity[1],
            "publication_signature": identity[2],
            "not_before_utc": _utc_iso(now + self._draft_poll_seconds),
        }

    def _commit_candidate(
        self,
        token: str,
        ctx: Mapping[str, Any],
        candidate: TargetCacheSnapshot,
        document: dict[str, Any],
    ) -> TargetCacheRefreshResult:
        try:
            with FileLock(self.lock_path, timeout=CACHE_LOCK_TIMEOUT_SECONDS):
                coordination = self._read_coordination()
                if not self._owns(coordination, token):
                    disk = self._read_validated_snapshot(ctx)
                    return TargetCacheRefreshResult(
                        TargetCacheRefreshOutcome.REJECTED_MISMATCH,
                        disk or self._unknown_snapshot(ctx, _COORDINATION_OWNERSHIP_LOST),
                        _COORDINATION_OWNERSHIP_LOST,
                    )
                disk = self._read_validated_snapshot(ctx)
                if (
                    disk is not None
                    and disk.metadata is not None
                    and candidate.metadata is not None
                    and disk.metadata.cache_identity == candidate.metadata.cache_identity
                ):
                    coordination.pop("active_refresh", None)
                    self._set_draft_poll(coordination, disk, self._wall_clock())
                    self._write_coordination(coordination)
                    return TargetCacheRefreshResult(
                        TargetCacheRefreshOutcome.REUSED,
                        disk,
                        disk.publication_reason,
                    )
                rejection = self._candidate_rejection_reason(disk, candidate)
                if rejection is not None:
                    coordination.pop("active_refresh", None)
                    if disk is not None:
                        self._set_draft_poll(coordination, disk, self._wall_clock())
                    self._write_coordination(coordination)
                    return TargetCacheRefreshResult(
                        TargetCacheRefreshOutcome.REJECTED_MISMATCH,
                        disk or self._unknown_snapshot(ctx, rejection),
                        rejection,
                    )
                atomic_json_write(self.cache_path, document)
                coordination.pop("active_refresh", None)
                self._set_draft_poll(coordination, candidate, self._wall_clock())
                self._write_coordination(coordination)
        except Exception:
            logger.exception("target_publication_cache_write_failed path=%s", self.cache_path)
            return self._result_without_owner(
                ctx,
                TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD,
                PUBLICATION_READ_FAILED,
            )
        return TargetCacheRefreshResult(
            TargetCacheRefreshOutcome.REFRESHED,
            candidate,
            candidate.publication_reason,
        )

    def _candidate_rejection_reason(
        self,
        disk: TargetCacheSnapshot | None,
        candidate: TargetCacheSnapshot,
    ) -> str | None:
        if disk is None or disk.metadata is None or candidate.metadata is None:
            return None
        if disk.metadata.kvk_no != candidate.metadata.kvk_no:
            return None
        disk_version = disk.metadata.publication_version or 0
        candidate_version = candidate.metadata.publication_version or 0
        if disk_version > candidate_version:
            return _PUBLICATION_DOWNGRADE_REJECTED
        if disk_version == candidate_version:
            return _PUBLICATION_IDENTITY_CONFLICT
        if (
            disk.metadata.publication_state == "OFFICIAL"
            and candidate.metadata.publication_state == "DRAFT"
        ):
            return _PUBLICATION_DOWNGRADE_REJECTED
        return None

    def _finish_reuse(
        self,
        token: str,
        ctx: Mapping[str, Any],
        snapshot: TargetCacheSnapshot,
        metadata: TargetPublicationMetadata,
    ) -> TargetCacheRefreshResult:
        try:
            with FileLock(self.lock_path, timeout=CACHE_LOCK_TIMEOUT_SECONDS):
                coordination = self._read_coordination()
                if not self._owns(coordination, token):
                    disk = self._read_validated_snapshot(ctx)
                    return TargetCacheRefreshResult(
                        TargetCacheRefreshOutcome.REJECTED_MISMATCH,
                        disk or self._unknown_snapshot(ctx, _COORDINATION_OWNERSHIP_LOST),
                        _COORDINATION_OWNERSHIP_LOST,
                    )
                coordination.pop("active_refresh", None)
                if metadata.publication_state == "DRAFT":
                    self._set_draft_poll(coordination, snapshot, self._wall_clock())
                self._write_coordination(coordination)
        except Exception:
            logger.exception("target_publication_coordination_reuse_failed")
            return self._result_without_owner(
                ctx,
                TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD,
                PUBLICATION_READ_FAILED,
            )
        return TargetCacheRefreshResult(
            TargetCacheRefreshOutcome.REUSED,
            snapshot,
            snapshot.publication_reason,
        )

    def _finish_failure(
        self,
        token: str,
        ctx: Mapping[str, Any],
        requested_outcome: TargetCacheRefreshOutcome,
        reason: str,
    ) -> TargetCacheRefreshResult:
        self._clear_owner_if_token(token)
        return self._result_without_owner(ctx, requested_outcome, reason)

    def _result_without_owner(
        self,
        ctx: Mapping[str, Any] | None,
        requested_outcome: TargetCacheRefreshOutcome,
        reason: str,
    ) -> TargetCacheRefreshResult:
        snapshot = self._read_validated_snapshot(ctx) if ctx is not None else None
        if snapshot is not None:
            logger.warning(
                "target_publication_using_last_known_good kvk_no=%s reason=%s state=%s",
                snapshot.requested_kvk_no,
                reason,
                snapshot.publication_state,
            )
            outcome = (
                requested_outcome
                if requested_outcome == TargetCacheRefreshOutcome.REJECTED_MISMATCH
                else TargetCacheRefreshOutcome.RETAINED_LAST_KNOWN_GOOD
            )
            return TargetCacheRefreshResult(outcome, snapshot, reason)
        outcome = (
            TargetCacheRefreshOutcome.UNAVAILABLE
            if requested_outcome == TargetCacheRefreshOutcome.UNAVAILABLE
            else TargetCacheRefreshOutcome.FAILED_CLOSED
        )
        return TargetCacheRefreshResult(
            outcome,
            self._unknown_snapshot(ctx, reason),
            reason,
        )

    def _unknown_snapshot(
        self,
        ctx: Mapping[str, Any] | None,
        reason: str,
    ) -> TargetCacheSnapshot:
        return TargetCacheSnapshot(
            requested_kvk_no=_positive_int((ctx or {}).get("kvk_no")),
            metadata=None,
            rows=(),
            publication_state="UNKNOWN",
            publication_reason=reason,
            kvk_fighting_state=str((ctx or {}).get("state") or "") or None,
            kvk_fighting_state_reason=(
                str((ctx or {}).get("state_reason")) if (ctx or {}).get("state_reason") else None
            ),
        )

    @staticmethod
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

    def _read_coordination(self) -> dict[str, Any]:
        raw = self._read_json(self.coordination_path)
        if raw.get("schema_version") != COORDINATION_SCHEMA_VERSION:
            return {"schema_version": COORDINATION_SCHEMA_VERSION}
        return dict(raw)

    def _write_coordination(self, coordination: dict[str, Any]) -> None:
        coordination["schema_version"] = COORDINATION_SCHEMA_VERSION
        atomic_json_write(self.coordination_path, coordination)

    @staticmethod
    def _owns(coordination: Mapping[str, Any], token: str) -> bool:
        active = coordination.get("active_refresh")
        return isinstance(active, Mapping) and active.get("owner_token") == token

    def _clear_owner_if_token(self, token: str) -> None:
        try:
            with FileLock(self.lock_path, timeout=CACHE_LOCK_TIMEOUT_SECONDS):
                coordination = self._read_coordination()
                if self._owns(coordination, token):
                    coordination.pop("active_refresh", None)
                    self._write_coordination(coordination)
        except Exception:
            logger.exception("target_publication_coordination_release_failed")

    def _ensure_parent(self) -> None:
        Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)


def get_default_target_cache_repository() -> TargetCacheRepository:
    """Return a target-domain repository bound to the configured production cache path."""
    return TargetCacheRepository(PLAYER_TARGETS_CACHE)
