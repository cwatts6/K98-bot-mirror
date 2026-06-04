from __future__ import annotations

import asyncio
from typing import Any

from prekvk.dal import report_dal
from prekvk.models import (
    PREKVK_REPORT_LIMITS,
    PreKvkReportPayload,
    PreKvkReportRow,
    PreKvkReportSort,
    PreKvkScheduledSummary,
    PreKvkScheduledTopBlocks,
    PreKvkScheduledTopEntry,
)

SORT_LABELS = {
    PreKvkReportSort.OVERALL: "Overall",
    PreKvkReportSort.STAGE1: "Stage 1",
    PreKvkReportSort.STAGE2: "Stage 2",
    PreKvkReportSort.STAGE3: "Stage 3",
}


def parse_report_sort(value: str | None) -> PreKvkReportSort:
    normalized = (value or PreKvkReportSort.OVERALL.value).strip().lower().replace(" ", "")
    aliases = {
        "overall": PreKvkReportSort.OVERALL,
        "total": PreKvkReportSort.OVERALL,
        "stage1": PreKvkReportSort.STAGE1,
        "stagei": PreKvkReportSort.STAGE1,
        "p1": PreKvkReportSort.STAGE1,
        "stage2": PreKvkReportSort.STAGE2,
        "stageii": PreKvkReportSort.STAGE2,
        "p2": PreKvkReportSort.STAGE2,
        "stage3": PreKvkReportSort.STAGE3,
        "stageiii": PreKvkReportSort.STAGE3,
        "p3": PreKvkReportSort.STAGE3,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("Sort must be Overall, Stage 1, Stage 2, or Stage 3.") from exc


def normalize_report_limit(value: int | None) -> int:
    try:
        requested = int(value or PREKVK_REPORT_LIMITS[0])
    except Exception:
        requested = PREKVK_REPORT_LIMITS[0]
    return requested if requested in PREKVK_REPORT_LIMITS else PREKVK_REPORT_LIMITS[0]


def _to_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _sort_value(row: PreKvkReportRow, sort_by: PreKvkReportSort) -> int:
    if sort_by == PreKvkReportSort.STAGE1:
        return int(row.stage1_points or 0)
    if sort_by == PreKvkReportSort.STAGE2:
        return int(row.stage2_points or 0)
    if sort_by == PreKvkReportSort.STAGE3:
        return int(row.stage3_points or 0)
    return int(row.overall_points or 0)


def _rank_rows(rows: list[PreKvkReportRow], sort_by: PreKvkReportSort) -> list[PreKvkReportRow]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (-_sort_value(row, sort_by), -(row.power or 0), row.governor_id),
    )
    ranked: list[PreKvkReportRow] = []
    previous_value: int | None = None
    current_rank = 0
    for index, row in enumerate(sorted_rows, start=1):
        value = _sort_value(row, sort_by)
        if previous_value is None or value != previous_value:
            current_rank = index
            previous_value = value
        ranked.append(
            PreKvkReportRow(
                rank=current_rank,
                governor_id=row.governor_id,
                governor_name=row.governor_name,
                power=row.power,
                stage1_points=row.stage1_points,
                stage2_points=row.stage2_points,
                stage3_points=row.stage3_points,
                overall_points=row.overall_points,
            )
        )
    return ranked


def _max_int(left: int | None, right: int | None) -> int | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


def _rows_from_raw(raw_rows: list[dict[str, Any]]) -> list[PreKvkReportRow]:
    rows_by_governor: dict[int, PreKvkReportRow] = {}
    for raw in raw_rows:
        governor_id = _to_int_or_none(raw.get("GovernorID"))
        if governor_id is None:
            continue
        governor_name = str(raw.get("GovernorName") or governor_id).strip() or str(governor_id)
        candidate = PreKvkReportRow(
            rank=0,
            governor_id=governor_id,
            governor_name=governor_name,
            power=_to_int_or_none(raw.get("Power")),
            stage1_points=_to_int_or_none(raw.get("Stage1Points")),
            stage2_points=_to_int_or_none(raw.get("Stage2Points")),
            stage3_points=_to_int_or_none(raw.get("Stage3Points")),
            overall_points=int(_to_int_or_none(raw.get("OverallPoints")) or 0),
        )
        existing = rows_by_governor.get(governor_id)
        if existing is None:
            rows_by_governor[governor_id] = candidate
            continue
        rows_by_governor[governor_id] = PreKvkReportRow(
            rank=0,
            governor_id=governor_id,
            governor_name=existing.governor_name or candidate.governor_name,
            power=_max_int(existing.power, candidate.power),
            stage1_points=_max_int(existing.stage1_points, candidate.stage1_points),
            stage2_points=_max_int(existing.stage2_points, candidate.stage2_points),
            stage3_points=_max_int(existing.stage3_points, candidate.stage3_points),
            overall_points=int(_max_int(existing.overall_points, candidate.overall_points) or 0),
        )
    return list(rows_by_governor.values())


def build_report_payload_from_rows(
    kvk_no: int,
    raw_rows: list[dict[str, Any]],
    *,
    sort_by: PreKvkReportSort = PreKvkReportSort.OVERALL,
    limit: int = 10,
) -> PreKvkReportPayload:
    normalized_limit = normalize_report_limit(limit)
    scan_id = None
    scan_timestamp_utc = None
    source_filename = None
    for raw in raw_rows:
        if scan_id is None:
            scan_id = _to_int_or_none(raw.get("ScanID"))
            scan_timestamp_utc = raw.get("ScanTimestampUTC")
            source_filename = raw.get("SourceFileName")
            if scan_id is not None or scan_timestamp_utc is not None or source_filename:
                break
    rows = _rows_from_raw(raw_rows)
    ranked = _rank_rows(rows, sort_by)[:normalized_limit]
    return PreKvkReportPayload(
        kvk_no=int(kvk_no),
        sort_by=sort_by,
        limit=normalized_limit,
        rows=ranked,
        scan_id=scan_id,
        scan_timestamp_utc=scan_timestamp_utc,
        source_filename=source_filename,
    )


def resolve_current_kvk_no() -> int | None:
    from stats_alerts.kvk_meta import get_latest_kvk_metadata_sql

    meta = get_latest_kvk_metadata_sql()
    if not meta or meta.get("kvk_no") is None:
        return None
    return int(meta["kvk_no"])


async def build_prekvk_report_payload(
    *,
    kvk_no: int | None = None,
    sort_by: PreKvkReportSort = PreKvkReportSort.OVERALL,
    limit: int = 10,
) -> PreKvkReportPayload:
    resolved_kvk_no = (
        int(kvk_no) if kvk_no is not None else await asyncio.to_thread(resolve_current_kvk_no)
    )
    if not resolved_kvk_no:
        raise ValueError("Could not determine the current KVK number.")
    raw_rows = await asyncio.to_thread(
        report_dal.fetch_latest_prekvk_report_rows, int(resolved_kvk_no)
    )
    return build_report_payload_from_rows(
        int(resolved_kvk_no),
        raw_rows,
        sort_by=sort_by,
        limit=limit,
    )


def _normalize_scheduled_limit(value: int | None, default: int) -> int:
    try:
        limit = int(value if value is not None else default)
    except Exception:
        limit = default
    return max(1, limit)


def _stage_points(row: PreKvkReportRow, sort_by: PreKvkReportSort) -> int | None:
    if sort_by == PreKvkReportSort.STAGE1:
        return row.stage1_points
    if sort_by == PreKvkReportSort.STAGE2:
        return row.stage2_points
    if sort_by == PreKvkReportSort.STAGE3:
        return row.stage3_points
    return row.overall_points


def _scheduled_entries(
    rows: list[PreKvkReportRow],
    *,
    sort_by: PreKvkReportSort,
    limit: int,
) -> list[PreKvkScheduledTopEntry]:
    entries: list[PreKvkScheduledTopEntry] = []
    for row in _rank_rows(rows, sort_by):
        points = _stage_points(row, sort_by)
        if points is None:
            continue
        entries.append(
            PreKvkScheduledTopEntry(
                name=row.governor_name,
                points=int(points),
            )
        )
        if len(entries) >= limit:
            break
    return entries


def build_scheduled_top_blocks_from_rows(
    raw_rows: list[dict[str, Any]],
    *,
    limit: int = 3,
) -> PreKvkScheduledTopBlocks:
    normalized_limit = _normalize_scheduled_limit(limit, 3)
    rows = _rows_from_raw(raw_rows)
    return PreKvkScheduledTopBlocks(
        overall=_scheduled_entries(
            rows,
            sort_by=PreKvkReportSort.OVERALL,
            limit=normalized_limit,
        ),
        p1=_scheduled_entries(
            rows,
            sort_by=PreKvkReportSort.STAGE1,
            limit=normalized_limit,
        ),
        p2=_scheduled_entries(
            rows,
            sort_by=PreKvkReportSort.STAGE2,
            limit=normalized_limit,
        ),
        p3=_scheduled_entries(
            rows,
            sort_by=PreKvkReportSort.STAGE3,
            limit=normalized_limit,
        ),
    )


def build_prekvk_scheduled_summary_sync(
    *,
    kvk_no: int,
    previous_kvk_no: int | None = None,
    current_limit: int = 3,
    previous_limit: int = 1,
) -> PreKvkScheduledSummary:
    resolved_kvk_no = int(kvk_no)
    current_rows = report_dal.fetch_latest_prekvk_report_rows(resolved_kvk_no)
    previous_blocks = PreKvkScheduledTopBlocks()
    resolved_previous_kvk_no = int(previous_kvk_no) if previous_kvk_no is not None else None
    if resolved_previous_kvk_no is not None and resolved_previous_kvk_no <= 0:
        resolved_previous_kvk_no = None
    if resolved_previous_kvk_no is not None and resolved_previous_kvk_no > 0:
        previous_rows = report_dal.fetch_latest_prekvk_report_rows(resolved_previous_kvk_no)
        previous_blocks = build_scheduled_top_blocks_from_rows(
            previous_rows,
            limit=previous_limit,
        )
    return PreKvkScheduledSummary(
        kvk_no=resolved_kvk_no,
        current=build_scheduled_top_blocks_from_rows(current_rows, limit=current_limit),
        previous_kvk_no=resolved_previous_kvk_no,
        previous=previous_blocks,
    )


async def build_prekvk_scheduled_summary(
    *,
    kvk_no: int,
    previous_kvk_no: int | None = None,
    current_limit: int = 3,
    previous_limit: int = 1,
) -> PreKvkScheduledSummary:
    return await asyncio.to_thread(
        build_prekvk_scheduled_summary_sync,
        kvk_no=int(kvk_no),
        previous_kvk_no=previous_kvk_no,
        current_limit=current_limit,
        previous_limit=previous_limit,
    )
