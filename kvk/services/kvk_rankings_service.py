from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from kvk.dal import kvk_rankings_dal
from kvk.models.kvk_rankings import (
    HALL_OF_FAME_METRIC_LABELS,
    PRIMARY_RANKING_LIMITS,
    HallOfFameMetric,
    RankingPayload,
    RankingRow,
)
from stats_alerts.honors import get_latest_honor_top


def normalize_ranking_limit(value: int | None, *, default: int = 10) -> int:
    try:
        requested = int(value if value is not None else default)
    except Exception:
        requested = default
    if requested in PRIMARY_RANKING_LIMITS:
        return requested
    return default if default in PRIMARY_RANKING_LIMITS else PRIMARY_RANKING_LIMITS[0]


def parse_hall_of_fame_metric(value: str | None) -> HallOfFameMetric:
    normalized = (value or HallOfFameMetric.KILLS.value).strip().lower()
    normalized = normalized.replace("_", "").replace(" ", "")
    aliases = {
        "kills": HallOfFameMetric.KILLS,
        "killpoints": HallOfFameMetric.KILL_POINTS,
        "kp": HallOfFameMetric.KILL_POINTS,
        "deads": HallOfFameMetric.DEADS,
        "dead": HallOfFameMetric.DEADS,
        "dkp": HallOfFameMetric.DKP,
        "healed": HallOfFameMetric.HEALED,
        "heals": HallOfFameMetric.HEALED,
        "acclaim": HallOfFameMetric.ACCLAIM,
        "honor": HallOfFameMetric.HONOR,
        "prekvk": HallOfFameMetric.PREKVK,
        "prekvkpoints": HallOfFameMetric.PREKVK,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("Unknown Hall of Fame metric.") from exc


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, Decimal):
            return int(value)
        return int(float(value))
    except Exception:
        return default


def _to_value(value: Any) -> int | float:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    try:
        numeric = float(value)
    except Exception:
        return 0
    return int(numeric) if numeric.is_integer() else numeric


def build_honor_rankings_payload_from_rows(
    rows: list[dict[str, Any]] | None,
    *,
    limit: int = 10,
) -> RankingPayload:
    normalized_limit = normalize_ranking_limit(limit)
    ranking_rows: list[RankingRow] = []
    for index, raw in enumerate((rows or [])[:normalized_limit], start=1):
        governor_id = _to_int(raw.get("GovernorID"))
        name = str(raw.get("GovernorName") or governor_id or "Unknown").strip() or "Unknown"
        ranking_rows.append(
            RankingRow(
                rank=index,
                governor_id=governor_id,
                governor_name=name,
                value=_to_int(raw.get("HonorPoints")),
                raw=dict(raw),
            )
        )
    return RankingPayload(
        mode="honor",
        metric="honor",
        metric_label="Honor",
        limit=normalized_limit,
        rows=ranking_rows,
        source_note="Latest imported honor scan",
    )


async def build_honor_rankings_payload(*, limit: int = 10) -> RankingPayload:
    normalized_limit = normalize_ranking_limit(limit)
    rows = await get_latest_honor_top(normalized_limit)
    return build_honor_rankings_payload_from_rows(rows, limit=normalized_limit)


def build_hall_of_fame_payload_from_rows(
    metric: HallOfFameMetric,
    rows: list[dict[str, Any]] | None,
    *,
    limit: int = 10,
) -> RankingPayload:
    normalized_limit = normalize_ranking_limit(limit)
    metric_label = HALL_OF_FAME_METRIC_LABELS[metric]
    ranking_rows: list[RankingRow] = []
    for raw in (rows or [])[:normalized_limit]:
        rank = _to_int(raw.get("RecordRank"), len(ranking_rows) + 1)
        governor_id = _to_int(raw.get("GovernorID"))
        governor_name = str(raw.get("GovernorName") or governor_id or "Unknown").strip()
        kvk_no_raw = raw.get("KVK_NO")
        kvk_no = _to_int(kvk_no_raw) if kvk_no_raw not in (None, "") else None
        kvk_name_raw = raw.get("KVK_NAME")
        ranking_rows.append(
            RankingRow(
                rank=rank,
                governor_id=governor_id,
                governor_name=governor_name or "Unknown",
                value=_to_value(raw.get("MetricValue")),
                kvk_no=kvk_no,
                kvk_name=str(kvk_name_raw).strip() if kvk_name_raw else None,
                raw=dict(raw),
            )
        )
    return RankingPayload(
        mode="records",
        metric=metric.value,
        metric_label=metric_label,
        limit=normalized_limit,
        rows=ranking_rows,
        source_note="Single-KVK performances across started KVKs",
    )


async def build_hall_of_fame_payload(
    *,
    metric: HallOfFameMetric | str = HallOfFameMetric.KILLS,
    limit: int = 10,
) -> RankingPayload:
    parsed_metric = metric if isinstance(metric, HallOfFameMetric) else parse_hall_of_fame_metric(metric)
    normalized_limit = normalize_ranking_limit(limit)
    rows = await asyncio.to_thread(
        kvk_rankings_dal.fetch_hall_of_fame_records,
        parsed_metric,
        limit=normalized_limit,
    )
    return build_hall_of_fame_payload_from_rows(parsed_metric, rows, limit=normalized_limit)
