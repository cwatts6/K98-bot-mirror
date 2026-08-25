from __future__ import annotations

import asyncio
from datetime import datetime
import logging
from typing import Any

from kvk.dal import kvk_targets_dal
from kvk.models.kvk_targets_card import KvkTargetMetricProgress, KvkTargetsCardPayload
from kvk.services.kvk_stats_card_service import load_kvk_stats_card_context
from kvk_state import get_kvk_context_today
import stats_cache_helpers
from utils import load_stat_row

logger = logging.getLogger(__name__)


def _int_from_variants(row: dict[str, Any] | None, keys: list[str], default: int = 0) -> int:
    row = row or {}
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if value in (None, ""):
            continue
        try:
            return int(float(str(value).replace(",", "").strip()))
        except (TypeError, ValueError):
            continue
    return default


def _optional_int_from_variants(row: dict[str, Any] | None, keys: list[str]) -> int | None:
    row = row or {}
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if value in (None, ""):
            continue
        try:
            return int(float(str(value).replace(",", "").strip()))
        except (TypeError, ValueError):
            continue
    return None


def _str_from_variants(row: dict[str, Any] | None, keys: list[str], default: str = "") -> str:
    row = row or {}
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


def _display_datetime(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M UTC") if value.tzinfo else value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return text


def _progress(label: str, current: int | None, target: int | None) -> KvkTargetMetricProgress:
    if not target or target <= 0:
        return KvkTargetMetricProgress(
            label=label,
            current=current,
            target=target,
            percent=None,
            remaining=None,
        )
    percent = None if current is None else (float(current) / float(target)) * 100.0
    remaining = None if current is None else max(int(target) - int(current), 0)
    return KvkTargetMetricProgress(
        label=label,
        current=current,
        target=target,
        percent=percent,
        remaining=remaining,
    )


def _metric_actual(
    primary: dict[str, Any] | None,
    fallback: dict[str, Any] | None,
    legacy_targets: dict[str, Any] | None,
    keys: list[str],
    legacy_keys: list[str],
) -> int | None:
    value = _optional_int_from_variants(primary, keys)
    if value is not None:
        return value
    value = _optional_int_from_variants(fallback, keys)
    if value is not None:
        return value
    return _optional_int_from_variants(legacy_targets, legacy_keys)


def _target_metrics(
    targets: dict[str, Any] | None,
    actuals: dict[str, Any] | None,
    last_kvk: dict[str, Any] | None,
) -> tuple[KvkTargetMetricProgress, ...]:
    kills_current = _optional_int_from_variants(
        last_kvk, ["T4&T5_Kills", "T4&T5 Kills", "Kills KVK -1"]
    )
    if kills_current is None:
        kills_current = _metric_actual(
            actuals,
            last_kvk,
            targets,
            ["T4&T5_Kills", "T4&T5 Kills"],
            ["Kills KVK -1"],
        )
    deads_current = _metric_actual(
        last_kvk,
        actuals,
        targets,
        ["Deads_Delta", "Deads Delta", "Deads", "DEADS KVK -1"],
        ["DEADS KVK -1"],
    )
    dkp_current = _metric_actual(
        last_kvk,
        actuals,
        targets,
        ["DKP_SCORE", "DKP Score", "DKP_Score", "DKP KVK -1"],
        ["DKP KVK -1"],
    )
    acclaim_current = _optional_int_from_variants(last_kvk, ["Acclaim", "AcclaimScore"])

    metrics = [
        _progress(
            "Kills Target",
            kills_current,
            _optional_int_from_variants(targets, ["Kill_Target", "Kill Target", "KillTarget"]),
        ),
        _progress(
            "Deads Target",
            deads_current,
            _optional_int_from_variants(targets, ["Deads_Target", "Dead Target", "DeadTarget"]),
        ),
        _progress(
            "DKP Target",
            dkp_current,
            _optional_int_from_variants(targets, ["DKP_Target", "DKP Target", "DKPTarget"]),
        ),
    ]
    metrics.append(
        KvkTargetMetricProgress(
            label="Acclaim Target",
            current=acclaim_current,
            target=None,
            percent=None,
            remaining=None,
            note="Target coming next KVK",
        )
    )
    return tuple(metrics)


def _quote_for_last_performance(metrics: tuple[KvkTargetMetricProgress, ...]) -> str:
    percentages = [m.percent for m in metrics if m.has_target and m.percent is not None]
    if not percentages:
        return "Targets are set. Time to make this KVK count."
    floor = min(percentages)
    if floor >= 110:
        return "You smashed last KVK. Same energy again."
    if floor >= 100:
        return "Targets hit last time. Hold that standard."
    if floor >= 85:
        return "So close last time. A little more effort gets it done."
    if floor >= 50:
        return "Last KVK left work on the table. Push harder for the kingdom."
    return "Big reset needed. Show up early and fight for the kingdom."


def _status_for_metrics(metrics: tuple[KvkTargetMetricProgress, ...]) -> tuple[str, str, str, str]:
    actionable = [metric for metric in metrics if metric.has_target]
    if actionable and all(metric.is_complete for metric in actionable):
        return (
            "complete",
            "Complete",
            "Last KVK cleared every comparable target.",
            _quote_for_last_performance(metrics),
        )
    if actionable:
        remaining = [m for m in actionable if not m.is_complete]
        if remaining:
            return (
                "active",
                "Target review",
                "Last KVK compared against this KVK's target line.",
                _quote_for_last_performance(metrics),
            )
    return (
        "no_target_values",
        "No target values",
        "A target row exists, but no target amounts are set.",
        "Ask leadership to confirm whether targets are still being prepared.",
    )


async def build_kvk_targets_card_payload(governor_id: str | int) -> KvkTargetsCardPayload:
    gid = str(governor_id or "").strip()
    if not gid.isdigit():
        return KvkTargetsCardPayload(
            governor_id=gid or "unknown",
            governor_name="Unknown governor",
            kvk_no=None,
            kvk_name=None,
            camp_name=None,
            target_state="missing_governor",
            status_label="Invalid ID",
            status_detail="That Governor ID is not valid.",
            next_action="Use a numeric Governor ID or register an account.",
            power=None,
            metrics=(),
        )

    try:
        kvk_context = get_kvk_context_today() or {}
    except Exception:
        logger.exception("kvk_targets_context_lookup_failed governor_id=%s", gid)
        kvk_context = {}

    kvk_no = _int_from_variants(kvk_context, ["kvk_no"], default=0) or None
    kvk_name = _str_from_variants(kvk_context, ["kvk_name"], default="") or None
    context = await load_kvk_stats_card_context(kvk_no, gid)
    if context.kvk_name:
        kvk_name = context.kvk_name

    target_row = await asyncio.to_thread(kvk_targets_dal.fetch_target_row, gid)
    cache_meta = await asyncio.to_thread(kvk_targets_dal.fetch_target_cache_meta)
    last_refreshed = _display_datetime(cache_meta.get("generated_at"))
    source_state = _str_from_variants(cache_meta, ["state"], default="") or None

    if not target_row:
        exemption = await asyncio.to_thread(kvk_targets_dal.fetch_exemption_row, gid, kvk_no)
        if exemption and bool(exemption.get("Exempt")):
            return KvkTargetsCardPayload(
                governor_id=gid,
                governor_name=_str_from_variants(
                    exemption, ["GovernorName", "Governor_Name"], default=f"Governor {gid}"
                ),
                kvk_no=kvk_no or _int_from_variants(exemption, ["KVK_NO"], default=0) or None,
                kvk_name=kvk_name,
                camp_name=context.camp_name,
                target_state="exempt",
                status_label="Exempt",
                status_detail="This governor is exempt from KVK targets.",
                next_action="No action needed unless leadership asks for an update.",
                power=None,
                metrics=(),
                last_refreshed=last_refreshed,
                source_state=source_state,
            )
        return KvkTargetsCardPayload(
            governor_id=gid,
            governor_name=f"Governor {gid}",
            kvk_no=kvk_no,
            kvk_name=kvk_name,
            camp_name=context.camp_name,
            target_state="no_target",
            status_label="No target",
            status_detail="No target row was found for this governor.",
            next_action="Check the Governor ID or ask leadership if targets are still being prepared.",
            power=None,
            metrics=(),
            last_refreshed=last_refreshed,
            source_state=source_state,
        )

    try:
        last_kvk_map = await stats_cache_helpers.load_last_kvk_map()
        last_kvk = last_kvk_map.get(gid) if isinstance(last_kvk_map, dict) else {}
    except Exception:
        logger.debug("kvk_targets_last_kvk_map_unavailable governor_id=%s", gid, exc_info=True)
        last_kvk = {}

    stats_row = await asyncio.to_thread(load_stat_row, gid)
    stats_found = isinstance(stats_row, dict) and bool(stats_row)
    actuals = stats_row if stats_found else None
    last_kvk_row = last_kvk if isinstance(last_kvk, dict) else None
    metrics = _target_metrics(target_row, actuals, last_kvk_row)
    target_state, label, detail, next_action = _status_for_metrics(metrics)
    governor_name = _str_from_variants(
        stats_row if stats_found else target_row,
        ["GovernorName", "Governor_Name", "Governor Name"],
        default=_str_from_variants(
            target_row, ["GovernorName", "Governor_Name"], f"Governor {gid}"
        ),
    )

    warnings: list[str] = []
    if source_state and source_state.upper() == "DRAFT":
        warnings.append("Targets are marked as draft and may still change.")

    return KvkTargetsCardPayload(
        governor_id=gid,
        governor_name=governor_name,
        kvk_no=kvk_no or _int_from_variants(target_row, ["KVK_NO"], default=0) or None,
        kvk_name=kvk_name,
        camp_name=context.camp_name,
        target_state=target_state,
        status_label=label,
        status_detail=detail,
        next_action=next_action,
        power=_optional_int_from_variants(target_row, ["Power", "Starting Power"]),
        metrics=metrics,
        last_refreshed=last_refreshed,
        source_state=source_state,
        warnings=tuple(warnings),
    )
