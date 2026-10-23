"""Read back the original startup cache result without repeating SQL work.

This is a cache observation, not an import, report-procedure or export receipt.
Shutdown continues to drain the existing worker and propagate cancellation.
"""

from datetime import UTC, datetime
import hashlib
import json


def _verify_completion(output):
    from file_utils import acquire_lock
    from player_stats_cache import (
        _CACHE_LOCK_TIMEOUT,
        PLAYER_STATS_CACHE,
        CacheSnapshotValidationError,
        _cache_lock_path,
    )

    if not isinstance(output, dict) or not isinstance(output.get("_meta"), dict):
        raise CacheSnapshotValidationError("startup_cache_result_missing")
    meta = output["_meta"]
    status = meta.get("source_refresh_status")
    if status not in {"refreshed", "last_known_good", "skipped"}:
        raise CacheSnapshotValidationError("startup_cache_build_failed")
    count = meta.get("count")
    if (
        meta.get("cache_write_status") != "written"
        or meta.get("existing_json_preserved") is not False
        or type(count) is not int
        or count <= 0
        or count != len(output) - 1
        or count != meta.get("source_row_count")
    ):
        raise CacheSnapshotValidationError("startup_cache_result_invalid")
    # Use the writer's existing lock. A different or absent snapshot is not proof
    # of this invocation's completion, and must never trigger a second calculation.
    with acquire_lock(_cache_lock_path(), timeout=_CACHE_LOCK_TIMEOUT):
        with open(PLAYER_STATS_CACHE, "rb") as source:
            raw = source.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise CacheSnapshotValidationError("cache_snapshot_too_large")
        if json.loads(raw) != output:
            raise CacheSnapshotValidationError("startup_cache_readback_differs")
    return {
        "kind": "player_cache_readback",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "verified_utc": datetime.now(UTC).isoformat(),
        "source_refresh_status": status,
        "source_kvk_no": meta.get("source_kvk_no"),
        "source_last_refresh": meta.get("source_last_refresh"),
        "source_row_count": count,
        "sql_execution_receipt": False,
    }


async def verify_completion(output):
    from services.legacy_export_snapshot_service import drain_thread

    return await drain_thread(_verify_completion, output)
