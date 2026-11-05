from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from file_utils import fetch_all_dicts, fetch_one_dict, get_conn_with_retries
from kvk.models.kvk_target_row import TargetRow
from kvk.services.kvk_target_publication_service import PUBLICATION_READ_FAILED
from kvk.target_cache_repository import (
    CACHE_SCHEMA_VERSION,
    get_default_target_cache_repository,
)

logger = logging.getLogger(__name__)


def fetch_governor_lookup_rows() -> list[dict[str, Any]]:
    """Return the authoritative governor directory shape used by target lookup."""
    sql = """
        SELECT
            GovernorID,
            GovernorName,
            CityHallLevel
        FROM dbo.vw_All_Governors_Clean
        WHERE GovernorName IS NOT NULL
    """
    try:
        with get_conn_with_retries() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                return fetch_all_dicts(cursor)
    except Exception:
        logger.exception("kvk_target_governor_directory_read_failed")
        raise


def fetch_target_row(governor_id: str | int) -> dict[str, Any] | None:
    """Compatibility wrapper returning the verified current-KVK target row."""
    try:
        gid = int(str(governor_id).strip())
    except (TypeError, ValueError):
        return None
    repository = get_default_target_cache_repository()
    snapshot = repository.read_snapshot()
    typed_row = snapshot.target_for(str(gid))
    if typed_row is None:
        return None
    return repository.target_row_to_cache_entry(snapshot, typed_row)


def fetch_target_cache_meta() -> dict[str, Any]:
    """Compatibility wrapper returning verified current-KVK publication metadata."""
    repository = get_default_target_cache_repository()
    snapshot = repository.read_snapshot()
    return repository.snapshot_to_cache_meta(snapshot)


def fetch_target_entry(
    governor_id: str | int,
    kvk_context: Mapping[str, Any] | None = None,
) -> tuple[TargetRow | None, dict[str, Any]]:
    """Return a target row and publication metadata from one cache snapshot."""
    try:
        governor_key = str(int(str(governor_id).strip()))
    except (TypeError, ValueError):
        governor_key = ""
    if not governor_key.isdigit():
        return None, {
            "schema_version": CACHE_SCHEMA_VERSION,
            "kvk_no": None,
            "publication_state": "UNKNOWN",
            "publication_reason": PUBLICATION_READ_FAILED,
        }
    repository = get_default_target_cache_repository()
    snapshot = repository.read_snapshot(kvk_context)
    return snapshot.target_for(governor_key), repository.snapshot_to_cache_meta(snapshot)


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
