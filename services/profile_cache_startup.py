"""Verify the original profile result without warming or querying SQL."""

import json
import math


def _verify(output):
    from profile_cache import PLAYER_PROFILE_CACHE, _parse_generated_at, _service

    summary = _service.verify(output)
    if output.persistence == "failed_preserved":
        # Available in memory is useful, but is deliberately not durability proof.
        summary["disk_verification"] = "failed_preserved"
        return summary
    if output.source in {"refreshed", "disk_loaded"}:
        with open(PLAYER_PROFILE_CACHE, "rb") as source:
            raw = source.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("profile_readback_too_large")
        from utils import json_default

        snapshot = _service.snapshot()
        _service.verify(output)
        persisted = json.loads(raw)
        if persisted.get("players") != json.loads(
            json.dumps(snapshot, default=json_default)
        ) or not math.isclose(
            _parse_generated_at(persisted.get("generated_at")),
            output.source_time,
            rel_tol=0,
            abs_tol=0.000001,
        ):
            raise ValueError("profile_readback_differs")
        summary["disk_verification"] = "original_snapshot"
    return summary


async def verify_completion(output):
    from services.legacy_export_snapshot_service import drain_thread

    return await drain_thread(_verify, output)
