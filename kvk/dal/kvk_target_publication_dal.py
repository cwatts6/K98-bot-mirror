from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from file_utils import fetch_all_dicts, fetch_one_dict, get_conn_with_retries
from kvk.models.kvk_target_publication import (
    TargetPublicationMetadata,
    TargetPublicationSnapshot,
)
from kvk.services.kvk_target_publication_service import (
    parse_target_publication_metadata,
    resolve_target_publication_state,
)
from utils import normalize_governor_id

logger = logging.getLogger(__name__)

BOT_VIEW_NAME = "dbo.v_KVK_TARGETS_FOR_BOT"

_METADATA_COLUMNS = """
    PublicationId,
    KVK_NO,
    PublicationState,
    SourceScanOrder,
    SourceScanType,
    ConfiguredDraftScan,
    ConfiguredMatchmakingScan,
    PublishedAtUtc,
    TargetRowCount,
    OutputObjectName,
    PublicationVersion,
    PublicationSignature
"""


class TargetPublicationContractError(RuntimeError):
    """The bot-facing SQL publication rowset did not satisfy its provenance contract."""


def _open_connection():
    return get_conn_with_retries(meta={"operation": "kvk_target_publication_read"})


def _metadata_from_row(row: Mapping[str, Any] | None) -> TargetPublicationMetadata:
    metadata = parse_target_publication_metadata(row)
    if metadata is None:
        raise TargetPublicationContractError("Target publication metadata was absent.")
    return metadata


def _normalise_target_row(row: Mapping[str, Any], kvk_no: int) -> dict[str, Any]:
    governor_raw = row.get("GovernorID")
    try:
        governor_id = normalize_governor_id(governor_raw)
    except Exception as exc:
        raise TargetPublicationContractError(
            "Target publication contained an invalid GovernorID."
        ) from exc
    if not governor_id or not governor_id.isdigit() or int(governor_id) <= 0:
        raise TargetPublicationContractError("Target publication contained an invalid GovernorID.")

    def required_nonnegative(name: str) -> int:
        value = row.get(name)
        if isinstance(value, bool):
            raise TargetPublicationContractError(f"Target publication contained an invalid {name}.")
        try:
            converted = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise TargetPublicationContractError(
                f"Target publication contained an invalid {name}."
            ) from exc
        if converted < 0:
            raise TargetPublicationContractError(f"Target publication contained an invalid {name}.")
        return converted

    power_value = row.get("Power")
    power: int | None = None
    if power_value not in (None, ""):
        try:
            power = int(str(power_value).replace(",", "").replace(" ", ""))
        except (TypeError, ValueError, OverflowError):
            power = None

    rank_value = row.get("TargetRank")
    try:
        target_rank = int(rank_value) if rank_value is not None else None
    except (TypeError, ValueError, OverflowError):
        target_rank = None

    return {
        "GovernorID": governor_id,
        "GovernorName": str(row.get("GovernorName") or "").strip(),
        "Power": power,
        "DKP_Target": required_nonnegative("DKP_Target"),
        "Kill_Target": required_nonnegative("Kill_Target"),
        "Deads_Target": required_nonnegative("Deads_Target"),
        "Min_Kill_Target": required_nonnegative("Min_Kill_Target"),
        "TargetRank": target_rank,
        "KVK_NO": kvk_no,
    }


def fetch_current_publication_metadata(kvk_no: int) -> TargetPublicationMetadata | None:
    if not isinstance(kvk_no, int) or isinstance(kvk_no, bool) or kvk_no <= 0:
        raise ValueError("kvk_no must be a positive integer")
    sql = f"""
        SELECT TOP (1)
            {_METADATA_COLUMNS}
        FROM {BOT_VIEW_NAME}
        WHERE KVK_NO = ?
        ORDER BY PublicationVersion DESC, GovernorID ASC
    """
    conn = _open_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, [kvk_no])
            row = fetch_one_dict(cursor)
        finally:
            cursor.close()
    finally:
        conn.close()
    if row is None:
        return None
    return _metadata_from_row(row)


def fetch_current_target_publication(kvk_no: int) -> TargetPublicationSnapshot | None:
    if not isinstance(kvk_no, int) or isinstance(kvk_no, bool) or kvk_no <= 0:
        raise ValueError("kvk_no must be a positive integer")
    sql = f"""
        SELECT
            {_METADATA_COLUMNS},
            TargetRank,
            GovernorID,
            GovernorName,
            Power,
            Kill_Target,
            Min_Kill_Target,
            Deads_Target,
            DKP_Target
        FROM {BOT_VIEW_NAME}
        WHERE KVK_NO = ?
        ORDER BY TargetRank ASC, GovernorID ASC
    """
    conn = _open_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, [kvk_no])
            raw_rows = fetch_all_dicts(cursor)
        finally:
            cursor.close()
    finally:
        conn.close()

    if not raw_rows:
        return None

    metadata = _metadata_from_row(raw_rows[0])
    normalised_rows: list[dict[str, Any]] = []
    seen_governors: set[str] = set()
    for raw_row in raw_rows:
        if _metadata_from_row(raw_row) != metadata:
            raise TargetPublicationContractError(
                "Target publication rows carried inconsistent publication identities."
            )
        row = _normalise_target_row(raw_row, kvk_no)
        governor_id = row["GovernorID"]
        if governor_id in seen_governors:
            raise TargetPublicationContractError(
                "Target publication contained duplicate GovernorID rows."
            )
        seen_governors.add(governor_id)
        normalised_rows.append(row)

    resolution = resolve_target_publication_state(
        metadata,
        requested_kvk_no=kvk_no,
        fighting_state=None,
        observed_row_count=len(normalised_rows),
    )
    if not resolution.is_verified:
        raise TargetPublicationContractError(
            f"Target publication failed provenance validation: {resolution.reason}."
        )

    return TargetPublicationSnapshot(metadata=metadata, rows=tuple(normalised_rows))
