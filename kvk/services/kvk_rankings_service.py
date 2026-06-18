from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from kvk.dal import kvk_rankings_dal
from kvk.models.kvk_rankings import (
    CURRENT_RANKING_MODES,
    HALL_OF_FAME_METRIC_LABELS,
    HALL_OF_FAME_RECORD_LIMIT,
    PRIMARY_RANKING_LIMITS,
    HallOfFameMetric,
    RankingPayload,
    RankingRow,
)
from prekvk import report_service
from prekvk.models import PreKvkReportPayload, PreKvkReportRow, PreKvkReportSort
from stats_alerts.honors import get_latest_honor_top
from utils import load_stat_cache, parse_last_refresh_utc

KVK_COMPACT_RANKING_METRIC_LABELS: dict[str, str] = {
    "power": "Power",
    "kills": "Kills (T4+T5)",
    "pct_kill_target": "% Kill Target",
    "deads": "Deads",
    "dkp": "DKP",
}
KVK_CARD_RANKING_METRIC_LABELS: dict[str, str] = {
    "kills": "Kills (T4+T5)",
    "pct_kill_target": "% Kill Target",
    "deads": "Deads",
    "dkp": "DKP",
    "acclaim": "Acclaim",
    "tanking_score": "Tanking Score",
}
KVK_RANKING_METRIC_LABELS: dict[str, str] = {
    **KVK_COMPACT_RANKING_METRIC_LABELS,
    **KVK_CARD_RANKING_METRIC_LABELS,
}

PREKVK_RANKING_METRIC_LABELS: dict[str, str] = {
    PreKvkReportSort.OVERALL.value: "Overall",
    PreKvkReportSort.STAGE1.value: "Stage 1",
    PreKvkReportSort.STAGE2.value: "Stage 2",
    PreKvkReportSort.STAGE3.value: "Stage 3",
}

CURRENT_RANKING_METRIC_LABELS: dict[str, dict[str, str]] = {
    "kvk": KVK_RANKING_METRIC_LABELS,
    "honor": {"honor": "Honor"},
    "prekvk": PREKVK_RANKING_METRIC_LABELS,
}

CURRENT_RANKING_MODE_LABELS: dict[str, str] = {
    "kvk": "KVK",
    "honor": "Honor",
    "prekvk": "PreKvK",
}

DEFAULT_CURRENT_RANKING_METRICS: dict[str, str] = {
    "kvk": "kills",
    "honor": "honor",
    "prekvk": PreKvkReportSort.OVERALL.value,
}

KVK_RANKING_FILTERS = ("STATUS = INCLUDED", "Starting Power >= 40M")
KVK_MIN_POWER = 40_000_000


def normalize_ranking_limit(value: int | None, *, default: int = 10) -> int:
    try:
        requested = int(value if value is not None else default)
    except Exception:
        requested = default
    if requested in PRIMARY_RANKING_LIMITS:
        return requested
    return default if default in PRIMARY_RANKING_LIMITS else PRIMARY_RANKING_LIMITS[0]


def normalize_hall_of_fame_limit(_value: int | None = None) -> int:
    return HALL_OF_FAME_RECORD_LIMIT


def parse_current_ranking_mode(value: str | None) -> str:
    normalized = (value or "kvk").strip().lower()
    if normalized not in CURRENT_RANKING_MODES:
        raise ValueError("Unknown current ranking mode.")
    return normalized


def current_ranking_metric_labels(mode: str, *, limit: int | None = None) -> dict[str, str]:
    parsed_mode = parse_current_ranking_mode(mode)
    if parsed_mode == "kvk":
        return (
            KVK_CARD_RANKING_METRIC_LABELS
            if normalize_ranking_limit(limit) == 10
            else KVK_COMPACT_RANKING_METRIC_LABELS
        )
    return CURRENT_RANKING_METRIC_LABELS[parsed_mode]


def normalize_current_ranking_metric(
    mode: str,
    metric: str | None = None,
    *,
    limit: int | None = None,
) -> str:
    parsed_mode = parse_current_ranking_mode(mode)
    default = DEFAULT_CURRENT_RANKING_METRICS[parsed_mode]
    normalized = (metric or default).strip().lower().replace(" ", "_")
    aliases = {
        "kp": "killpoints",
        "%_kill_target": "pct_kill_target",
        "kill_target": "pct_kill_target",
        "stage_1": PreKvkReportSort.STAGE1.value,
        "stage_2": PreKvkReportSort.STAGE2.value,
        "stage_3": PreKvkReportSort.STAGE3.value,
        "tanking": "tanking_score",
    }
    normalized = aliases.get(normalized, normalized)
    labels = current_ranking_metric_labels(parsed_mode, limit=limit)
    if normalized in labels:
        return normalized
    return default


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


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except Exception:
        return default


def _display_name(raw: dict[str, Any], *, id_keys: tuple[str, ...] = ("GovernorID",)) -> str:
    raw_name = raw.get("GovernorName") or raw.get("Governor_Name")
    if raw_name and str(raw_name).strip():
        return str(raw_name).strip()
    for key in id_keys:
        value = raw.get(key)
        if value not in (None, ""):
            return str(_to_int(value) or value)
    return "Unknown"


def _row_governor_id(raw: dict[str, Any]) -> int:
    return _to_int(raw.get("GovernorID") or raw.get("Gov_ID"))


def _kvk_power(row: dict[str, Any]) -> int:
    return _to_int(row.get("Starting Power") or row.get("Power"))


def _kvk_kills(row: dict[str, Any]) -> int:
    total = _to_int(row.get("T4&T5_Kills"))
    if total == 0:
        total = _to_int(row.get("T4_Kills")) + _to_int(row.get("T5_Kills"))
    return total


def _kvk_deads(row: dict[str, Any]) -> int:
    return _to_int(row.get("Deads_Delta") or row.get("Deads"))


def _kvk_dkp(row: dict[str, Any]) -> float:
    return _to_float(row.get("DKP_SCORE") or row.get("DKP Score"))


def _kvk_acclaim(row: dict[str, Any]) -> int:
    return _to_int(row.get("Acclaim") or row.get("AcclaimScore"))


def _kvk_kill_points(row: dict[str, Any]) -> float:
    return _to_float(
        row.get("KillPointsDelta")
        or row.get("Kill Points Delta")
        or row.get("KillPoints_Delta")
        or row.get("KillPoints")
    )


def _kvk_healed(row: dict[str, Any]) -> int:
    return _to_int(
        row.get("HealedTroopsDelta")
        or row.get("Healed Troops Delta")
        or row.get("Healed_Troops_Delta")
    )


def _kvk_tanking_score(row: dict[str, Any]) -> float:
    kp_gain = _kvk_kill_points(row)
    healed = _kvk_healed(row)
    if not kp_gain or not healed:
        return 0.0
    return healed * 20 / kp_gain * 100.0


def _kvk_has_tanking_score(row: dict[str, Any]) -> bool:
    return _kvk_kill_points(row) > 0 and _kvk_healed(row) > 0


def _kvk_pct_kill_target(row: dict[str, Any]) -> float:
    return _to_float(row.get("% of Kill Target") or row.get("% of Kill target"))


def _kvk_metric_getter(metric: str) -> Callable[[dict[str, Any]], int | float]:
    getters: dict[str, Callable[[dict[str, Any]], int | float]] = {
        "power": _kvk_power,
        "kills": _kvk_kills,
        "pct_kill_target": _kvk_pct_kill_target,
        "deads": _kvk_deads,
        "dkp": _kvk_dkp,
        "acclaim": _kvk_acclaim,
        "tanking_score": _kvk_tanking_score,
    }
    return getters.get(metric, _kvk_kills)


def _latest_refresh_label(rows: list[dict[str, Any]]) -> str | None:
    parsed: list[datetime] = []
    fallback: list[str] = []
    for row in rows:
        raw = row.get("LAST_REFRESH") or row.get("ScanTimestampUTC")
        if not raw:
            continue
        dt = parse_last_refresh_utc(raw)
        if dt is not None:
            parsed.append(dt)
        else:
            fallback.append(str(raw))
    if parsed:
        return max(parsed).strftime("%Y-%m-%d %H:%M UTC")
    if fallback:
        return max(fallback)
    return None


def _filter_kvk_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("STATUS", "")).upper() == "INCLUDED" and _kvk_power(row) >= KVK_MIN_POWER
    ]


def build_kvk_rankings_payload_from_rows(
    rows: list[dict[str, Any]] | None,
    *,
    metric: str = "kills",
    limit: int = 10,
) -> RankingPayload:
    normalized_limit = normalize_ranking_limit(limit)
    normalized_metric = normalize_current_ranking_metric("kvk", metric, limit=normalized_limit)
    raw_rows = list(rows or [])
    filtered = _filter_kvk_rows(raw_rows)
    getter = _kvk_metric_getter(normalized_metric)
    rankable_rows = (
        [row for row in filtered if _kvk_has_tanking_score(row)]
        if normalized_metric == "tanking_score"
        else filtered
    )
    sort_key: Callable[[dict[str, Any]], tuple[int | float, int | float, int]]
    if normalized_metric == "tanking_score":
        sort_key = lambda row: (getter(row), -_kvk_power(row), _row_governor_id(row))
    else:
        sort_key = lambda row: (-getter(row), -_kvk_power(row), _row_governor_id(row))
    sorted_rows = sorted(
        rankable_rows,
        key=sort_key,
    )
    ranking_rows: list[RankingRow] = []
    for index, raw in enumerate(sorted_rows[:normalized_limit], start=1):
        ranking_rows.append(
            RankingRow(
                rank=index,
                governor_id=_row_governor_id(raw),
                governor_name=_display_name(raw, id_keys=("GovernorID", "Gov_ID")),
                value=getter(raw),
                supporting_values={
                    "Power": _kvk_power(raw),
                    "Kills": _kvk_kills(raw),
                    "% K/T": _kvk_pct_kill_target(raw),
                    "Deads": _kvk_deads(raw),
                    "DKP": _kvk_dkp(raw),
                    "Acclaim": _kvk_acclaim(raw),
                    "Tanking Score": _kvk_tanking_score(raw),
                    "Kill Points": _kvk_kill_points(raw),
                    "Healed": _kvk_healed(raw),
                },
                raw=dict(raw),
            )
        )
    source_state = "fresh"
    if not raw_rows:
        source_state = "unavailable"
    elif not ranking_rows:
        source_state = "empty"
    return RankingPayload(
        mode="kvk",
        mode_label=CURRENT_RANKING_MODE_LABELS["kvk"],
        metric=normalized_metric,
        metric_label=current_ranking_metric_labels("kvk", limit=normalized_limit)[
            normalized_metric
        ],
        limit=normalized_limit,
        rows=ranking_rows,
        source_note="Stats cache",
        source_state=source_state,
        freshness_label=_latest_refresh_label(filtered or raw_rows),
        filters=KVK_RANKING_FILTERS,
        total_rows=len(rankable_rows),
        empty_message=(
            "No KVK ranking rows match the current included-player filters."
            if raw_rows
            else "No stats cache available yet. Try again after the next scan/export."
        ),
    )


async def build_kvk_rankings_payload(
    *,
    metric: str = "kills",
    limit: int = 10,
) -> RankingPayload:
    cache = await asyncio.to_thread(load_stat_cache)
    rows = [row for key, row in cache.items() if key != "_meta"]
    return build_kvk_rankings_payload_from_rows(rows, metric=metric, limit=limit)


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
                kvk_no=_to_int(raw.get("KVK_NO")) if raw.get("KVK_NO") not in (None, "") else None,
                supporting_values={"Honor": _to_int(raw.get("HonorPoints"))},
                raw=dict(raw),
            )
        )
    first = (rows or [{}])[0] if rows else {}
    return RankingPayload(
        mode="honor",
        mode_label=CURRENT_RANKING_MODE_LABELS["honor"],
        metric="honor",
        metric_label="Honor",
        limit=normalized_limit,
        rows=ranking_rows,
        kvk_no=_to_int(first.get("KVK_NO")) if first.get("KVK_NO") not in (None, "") else None,
        freshness_label=_latest_refresh_label(list(rows or [])),
        source_note="Latest imported honor scan",
        source_state="fresh" if ranking_rows else "empty",
        total_rows=len(rows or []),
        empty_message="No honor data found for the latest KVK.",
    )


async def build_honor_rankings_payload(*, limit: int = 10) -> RankingPayload:
    normalized_limit = normalize_ranking_limit(limit)
    rows = await get_latest_honor_top(normalized_limit)
    return build_honor_rankings_payload_from_rows(rows, limit=normalized_limit)


def _prekvk_value(row: PreKvkReportRow, metric: str) -> int:
    if metric == PreKvkReportSort.STAGE1.value:
        return int(row.stage1_points or 0)
    if metric == PreKvkReportSort.STAGE2.value:
        return int(row.stage2_points or 0)
    if metric == PreKvkReportSort.STAGE3.value:
        return int(row.stage3_points or 0)
    return int(row.overall_points or 0)


def build_prekvk_rankings_payload_from_report(
    payload: PreKvkReportPayload,
) -> RankingPayload:
    metric = normalize_current_ranking_metric("prekvk", payload.sort_by.value)
    ranking_rows = [
        RankingRow(
            rank=row.rank,
            governor_id=int(row.governor_id),
            governor_name=row.governor_name,
            value=_prekvk_value(row, metric),
            kvk_no=payload.kvk_no,
            supporting_values={
                "Power": row.power,
                "Stage 1": row.stage1_points,
                "Stage 2": row.stage2_points,
                "Stage 3": row.stage3_points,
                "Overall": row.overall_points,
            },
            raw={
                "GovernorID": row.governor_id,
                "GovernorName": row.governor_name,
                "Power": row.power,
                "Stage1Points": row.stage1_points,
                "Stage2Points": row.stage2_points,
                "Stage3Points": row.stage3_points,
                "OverallPoints": row.overall_points,
            },
        )
        for row in payload.rows
    ]
    filters: tuple[str, ...] = ()
    if not payload.has_stage_data:
        filters = ("Legacy total-only import",)
    return RankingPayload(
        mode="prekvk",
        mode_label=CURRENT_RANKING_MODE_LABELS["prekvk"],
        metric=metric,
        metric_label=PREKVK_RANKING_METRIC_LABELS[metric],
        limit=payload.limit,
        rows=ranking_rows,
        kvk_no=payload.kvk_no,
        freshness_label=_latest_refresh_label(
            [{"ScanTimestampUTC": payload.scan_timestamp_utc}] if payload.scan_timestamp_utc else []
        ),
        source_note=payload.source_filename or "Latest PreKvK import",
        source_state="fresh" if ranking_rows else "empty",
        filters=filters,
        total_rows=None,
        empty_message=f"No PreKvK import found for KVK {payload.kvk_no}.",
    )


async def build_prekvk_rankings_payload(
    *,
    metric: str = PreKvkReportSort.OVERALL.value,
    limit: int = 10,
) -> RankingPayload:
    normalized_metric = normalize_current_ranking_metric("prekvk", metric)
    sort_by = report_service.parse_report_sort(normalized_metric)
    payload = await report_service.build_prekvk_report_payload(
        kvk_no=None,
        sort_by=sort_by,
        limit=normalize_ranking_limit(limit),
    )
    return build_prekvk_rankings_payload_from_report(payload)


async def build_current_rankings_payload(
    *,
    mode: str,
    metric: str | None = None,
    limit: int = 10,
) -> RankingPayload:
    parsed_mode = parse_current_ranking_mode(mode)
    normalized_limit = normalize_ranking_limit(limit)
    normalized_metric = normalize_current_ranking_metric(
        parsed_mode,
        metric,
        limit=normalized_limit,
    )
    if parsed_mode == "kvk":
        return await build_kvk_rankings_payload(metric=normalized_metric, limit=normalized_limit)
    if parsed_mode == "honor":
        return await build_honor_rankings_payload(limit=normalized_limit)
    return await build_prekvk_rankings_payload(metric=normalized_metric, limit=normalized_limit)


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
    parsed_metric = (
        metric if isinstance(metric, HallOfFameMetric) else parse_hall_of_fame_metric(metric)
    )
    normalized_limit = normalize_hall_of_fame_limit(limit)
    rows = await asyncio.to_thread(
        kvk_rankings_dal.fetch_hall_of_fame_records,
        parsed_metric,
        limit=normalized_limit,
    )
    return build_hall_of_fame_payload_from_rows(parsed_metric, rows, limit=normalized_limit)
