# stats_alerts/prekvk_stats.py
"""
Helpers to load Pre-KVK top lists (overall + direct stage values).

Provides:
- load_prekvk_top3(kvk_no: int, limit: int = 3) -> dict[str, list[dict]]
  returns dict with keys 'overall','p1','p2','p3', each a list of dicts with keys Name, Points.
"""

import logging

from prekvk import report_service
from prekvk.models import PreKvkScheduledTopBlocks

logger = logging.getLogger(__name__)


def _blocks_to_legacy_dict(blocks: PreKvkScheduledTopBlocks) -> dict:
    return {
        "overall": [{"Name": entry.name, "Points": entry.points} for entry in blocks.overall],
        "p1": [{"Name": entry.name, "Points": entry.points} for entry in blocks.p1],
        "p2": [{"Name": entry.name, "Points": entry.points} for entry in blocks.p2],
        "p3": [{"Name": entry.name, "Points": entry.points} for entry in blocks.p3],
    }


def load_prekvk_top3(kvk_no: int, limit: int = 3) -> dict:
    """Compatibility wrapper for older callers that expect compact Top blocks."""
    out = {"overall": [], "p1": [], "p2": [], "p3": []}
    try:
        if not kvk_no:
            return out
        summary = report_service.build_prekvk_scheduled_summary_sync(
            kvk_no=int(kvk_no),
            current_limit=limit,
        )
        return _blocks_to_legacy_dict(summary.current)
    except Exception:
        logger.exception("[PREKVK] Failed to load Pre-KVK Top lists")
    return out
