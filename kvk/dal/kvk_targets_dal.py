from __future__ import annotations

import json
import logging
import os
from typing import Any

from constants import PLAYER_TARGETS_CACHE
from file_utils import fetch_one_dict, get_conn_with_retries
from targets_sql_cache import get_targets_for_governor

logger = logging.getLogger(__name__)


def fetch_target_row(governor_id: str | int) -> dict[str, Any] | None:
    """Return the cached target row for a governor, refreshing through the cache module if needed."""
    try:
        gid = int(str(governor_id).strip())
    except (TypeError, ValueError):
        return None
    row = get_targets_for_governor(gid)
    return dict(row) if isinstance(row, dict) else None


def fetch_target_cache_meta() -> dict[str, Any]:
    """Return target cache metadata without exposing the cache file format to services."""
    if not os.path.exists(PLAYER_TARGETS_CACHE):
        return {}
    try:
        with open(PLAYER_TARGETS_CACHE, encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception:
        logger.debug("kvk_targets_cache_meta_read_failed", exc_info=True)
        return {}
    meta = raw.get("_meta") if isinstance(raw, dict) else None
    return dict(meta) if isinstance(meta, dict) else {}


def fetch_exemption_row(governor_id: str | int, kvk_no: int | None = None) -> dict[str, Any] | None:
    """
    Return the current exemption row for a governor.

    The SQL source-of-truth table currently exposes GovernorID, GovernorName, Exempt, and KVK_NO.
    Do not depend on legacy Python-only fields such as Status, IsExempt, or Exempt_Reason here.
    """
    try:
        gid = int(str(governor_id).strip())
    except (TypeError, ValueError):
        return None

    params: list[Any] = [gid]
    where_kvk = ""
    if kvk_no is not None:
        where_kvk = "AND (TRY_CONVERT(int, KVK_NO) = ? OR KVK_NO = 0 OR KVK_NO IS NULL)"
        params.append(int(kvk_no))
    else:
        where_kvk = "AND (KVK_NO = 0 OR KVK_NO IS NULL)"

    sql = f"""
        SELECT TOP 1
            TRY_CONVERT(bigint, GovernorID) AS GovernorID,
            CAST(GovernorName AS nvarchar(255)) AS GovernorName,
            TRY_CONVERT(bit, Exempt) AS Exempt,
            TRY_CONVERT(int, KVK_NO) AS KVK_NO
        FROM dbo.EXEMPT_FROM_STATS
        WHERE TRY_CONVERT(bigint, GovernorID) = ?
          {where_kvk}
        ORDER BY
            CASE WHEN TRY_CONVERT(int, KVK_NO) = ? THEN 0 ELSE 1 END,
            KVK_NO DESC
    """
    query_params = params + [int(kvk_no or 0)]

    try:
        with get_conn_with_retries() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, query_params)
                row = fetch_one_dict(cursor)
    except Exception:
        logger.exception("kvk_target_exemption_lookup_failed governor_id=%s", gid)
        return None
    return dict(row) if row else None
