"""DAL for MGE SQL access."""

from __future__ import annotations

import logging
from typing import Any

from stats_alerts.db import run_query

logger = logging.getLogger(__name__)

SQL_SELECT_ACTIVE_COMMANDERS = """
SELECT CommanderId, CommanderName, IsActive, ReleaseStartUtc, ReleaseEndUtc, ImageUrl, CreatedUtc, UpdatedUtc
FROM dbo.MGE_Commanders
WHERE IsActive = 1;
"""

SQL_SELECT_ACTIVE_VARIANT_COMMANDERS = """
SELECT
    vc.VariantCommanderId,
    vc.VariantId,
    vc.CommanderId,
    v.VariantName,
    c.CommanderName,
    vc.IsActive,
    vc.CreatedUtc
FROM dbo.MGE_VariantCommanders vc
JOIN dbo.MGE_Variants v ON vc.VariantId = v.VariantId
JOIN dbo.MGE_Commanders c ON vc.CommanderId = c.CommanderId
WHERE vc.IsActive = 1
  AND v.IsActive = 1
  AND c.IsActive = 1;
"""

SQL_SELECT_EVENT_COMMANDER_OVERRIDES = """
SELECT o.OverrideId, o.EventId, o.CommanderId, c.CommanderName, o.IsAdded
FROM dbo.MGE_EventCommanderOverrides o
JOIN dbo.MGE_Commanders c ON o.CommanderId = c.CommanderId
WHERE o.EventId = ? AND o.IsAdded = 1;
"""


def fetch_active_commanders() -> list[dict[str, Any]]:
    """Fetch active commanders."""
    try:
        rows = run_query(SQL_SELECT_ACTIVE_COMMANDERS)
        logger.info("mge_dal_fetch_active_commanders_success count=%s", len(rows))
        return rows
    except Exception:
        logger.exception("mge_dal_fetch_active_commanders_failed")
        return []


def fetch_active_variant_commanders() -> list[dict[str, Any]]:
    """Fetch active variant->commander mappings."""
    try:
        rows = run_query(SQL_SELECT_ACTIVE_VARIANT_COMMANDERS)
        logger.info("mge_dal_fetch_active_variant_commanders_success count=%s", len(rows))
        return rows
    except Exception:
        logger.exception("mge_dal_fetch_active_variant_commanders_failed")
        return []


def fetch_event_commander_overrides(event_id: int) -> list[dict[str, Any]]:
    """Fetch event-specific commander overrides (future task use)."""
    try:
        rows = run_query(SQL_SELECT_EVENT_COMMANDER_OVERRIDES, (event_id,))
        logger.info(
            "mge_dal_fetch_event_commander_overrides_success event_id=%s count=%s",
            event_id,
            len(rows),
        )
        return rows
    except Exception:
        logger.exception("mge_dal_fetch_event_commander_overrides_failed event_id=%s", event_id)
        return []
