from __future__ import annotations

import asyncio
from datetime import date, datetime
import logging
from typing import Any

from kvk.dal import kvk_stats_card_dal
from kvk.models.kvk_stats_card import (
    KvkStatsCardContext,
    KvkStatsCardPayload,
    KvkTargetProgress,
)

logger = logging.getLogger(__name__)

PROGRESS_GOLD_HEX = "#FFD357"

PASS_KEYS = (
    "Pass 4 Kills",
    "Pass 6 Kills",
    "Pass 7 Kills",
    "Pass 8 Kills",
    "Pass 4 Deads",
    "Pass 6 Deads",
    "Pass 7 Deads",
    "Pass 8 Deads",
)


def _int_from_variants(row: dict[str, Any], keys: list[str], default: int = 0) -> int:
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


def _optional_int_from_variants(row: dict[str, Any], keys: list[str]) -> int | None:
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


def _float_from_variants(row: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if value in (None, ""):
            continue
        try:
            return float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            continue
    return None


def _str_from_variants(row: dict[str, Any], keys: list[str], default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


def _pct(current: int | float, target: int | float) -> float | None:
    if not target:
        return None
    return float(current) / float(target) * 100.0


def kill_progress_policy(percent: float | None, *, is_exempt: bool = False) -> tuple[str, str]:
    if is_exempt:
        return "#666666", "No targets assigned this KVK"
    value = float(percent or 0.0)
    if value >= 100:
        return PROGRESS_GOLD_HEX, "Smashed it! Don't stop!!"
    if value >= 85:
        return "#006400", "So close, push now!"
    if value >= 70:
        return "#2ecc71", "Fight more, still time!"
    if value >= 55:
        return "#FF8500", "Must work harder!"
    if value >= 40:
        return "#ff8c00", "Not enough yet!"
    if value >= 20:
        return "#e74c3c", "No excuses, more fighting!"
    return "#8B0000", "FIGHT NOW!!"


def _playstyle(tanking_score_percent: float | None) -> str | None:
    if tanking_score_percent is None:
        return None
    if tanking_score_percent < 80:
        return "Sniping Kills"
    if tanking_score_percent <= 110:
        return "Objective Focusing"
    return "Going All Out Fighting"


def _date_display(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M UTC") if value.tzinfo else value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return text


def _build_context(raw: dict[str, Any] | None) -> KvkStatsCardContext:
    raw = raw or {}
    return KvkStatsCardContext(
        kvk_name=_str_from_variants(raw, ["kvk_name", "KVK_NAME"], default="") or None,
        kingdom=_int_from_variants(raw, ["kingdom", "Kingdom"], default=0) or None,
        camp_id=_int_from_variants(raw, ["camp_id", "campid", "CampID"], default=0) or None,
        camp_name=_str_from_variants(raw, ["camp_name", "CampName"], default="") or None,
        overall_kvk_rank=_int_from_variants(raw, ["overall_kvk_rank", "OverallKvkRank"], default=0)
        or None,
        overall_kvk_total_governors=_int_from_variants(
            raw, ["overall_kvk_total_governors", "OverallKvkTotalGovernors"], default=0
        )
        or None,
        overall_kvk_top_percent=_float_from_variants(
            raw, ["overall_kvk_top_percent", "OverallKvkTopPercent"]
        ),
    )


async def load_kvk_stats_card_context(kvk_no: int | None, governor_id: str) -> KvkStatsCardContext:
    try:
        raw = await asyncio.to_thread(
            kvk_stats_card_dal.fetch_kvk_stats_card_context, kvk_no, governor_id
        )
    except Exception:
        logger.exception(
            "kvk_stats_card_context_load_failed kvk_no=%s governor_id=%s", kvk_no, governor_id
        )
        raw = {}
    return _build_context(raw)


async def build_kvk_stats_card_payload(
    row: dict[str, Any], *, context: KvkStatsCardContext | None = None
) -> KvkStatsCardPayload:
    governor_id = _str_from_variants(
        row, ["GovernorID", "Governor ID", "Gov_ID"], default="Unknown"
    )
    governor_name = _str_from_variants(
        row, ["GovernorName", "Governor_Name", "Governor Name"], default="Unknown"
    )
    kvk_no = _int_from_variants(row, ["KVK_NO", "KVK NO"], default=0) or None
    if context is None:
        context = await load_kvk_stats_card_context(kvk_no, governor_id)

    status = _str_from_variants(row, ["STATUS"], default="INCLUDED").upper()
    is_exempt = status == "EXEMPT"

    matchmaking_power = _int_from_variants(
        row, ["Starting Power", "Starting_Power", "StartingPower", "Power"], default=0
    )
    kp_gain = _int_from_variants(
        row, ["KillPointsDelta", "Kill Points Delta", "KillPoints_Delta", "KillPoints"], default=0
    )
    kills_gain = _int_from_variants(row, ["T4&T5_Kills", "T4&T5 Kills"], default=0)
    kill_target = _int_from_variants(row, ["Kill Target", "Kill_Target", "KillTarget"], default=0)
    kill_target_percent = (
        None if is_exempt else _float_from_variants(row, ["% of Kill Target", "% of Kill target"])
    )
    if kill_target_percent is None and not is_exempt:
        kill_target_percent = _pct(kills_gain, kill_target)
    progress_color, progress_quote = kill_progress_policy(kill_target_percent, is_exempt=is_exempt)

    deads = _int_from_variants(row, ["Deads_Delta", "Deads Delta", "Deads"], default=0)
    dead_target = _int_from_variants(row, ["Dead_Target", "Dead Target", "DeadTarget"], default=0)
    dead_target_percent = (
        None if is_exempt else _float_from_variants(row, ["% of Dead Target", "% of Dead_Target"])
    )
    if dead_target_percent is None and not is_exempt:
        dead_target_percent = _pct(deads, dead_target)

    dkp = _int_from_variants(row, ["DKP_SCORE", "DKP Score", "DKP_Score"], default=0)
    dkp_target = _int_from_variants(row, ["DKP_Target", "DKP Target", "DKPTarget"], default=0)
    dkp_target_percent = (
        None if is_exempt else _float_from_variants(row, ["% of DKP Target", "% of DKP_Target"])
    )
    if dkp_target_percent is None and not is_exempt:
        dkp_target_percent = _pct(dkp, dkp_target)

    healed = _optional_int_from_variants(
        row, ["HealedTroopsDelta", "Healed Troops Delta", "Healed_Troops_Delta"]
    )
    kp_loss = healed * 20 if healed is not None else None
    tanking_score_percent = _pct(kp_loss, kp_gain) if kp_loss is not None and kp_gain else None

    pass_stats = {
        key: value
        for key in PASS_KEYS
        if (value := _int_from_variants(row, [key, key.replace(" ", "_")], default=0)) > 0
    }

    last_kvk = row.get("last_kvk") if isinstance(row.get("last_kvk"), dict) else {}

    return KvkStatsCardPayload(
        governor_id=governor_id,
        governor_name=governor_name,
        kvk_no=kvk_no,
        kvk_name=context.kvk_name,
        kingdom=context.kingdom,
        camp_name=context.camp_name,
        last_refresh=_date_display(row.get("LAST_REFRESH")),
        status=status,
        kvk_rank=row.get("KVK_RANK") or None,
        kingdom_rank=row.get("Rank") or None,
        matchmaking_power=matchmaking_power or None,
        kp_gain=kp_gain,
        kills_gain=kills_gain,
        kill_target=kill_target,
        kill_progress=KvkTargetProgress(
            current=kills_gain,
            target=kill_target,
            percent=kill_target_percent,
            color_hex=progress_color,
            quote=progress_quote,
            is_exempt=is_exempt,
        ),
        deads=deads,
        dead_target=dead_target,
        dead_target_percent=dead_target_percent,
        power_loss=_int_from_variants(row, ["Power_Delta", "Power Delta"], default=0) or None,
        healed=healed,
        kp_loss=kp_loss,
        tanking_score_percent=tanking_score_percent,
        playstyle=_playstyle(tanking_score_percent),
        acclaim=_int_from_variants(row, ["Acclaim", "AcclaimScore"], default=0),
        dkp=dkp,
        dkp_target=dkp_target,
        dkp_target_percent=dkp_target_percent,
        overall_kvk_rank=context.overall_kvk_rank,
        overall_kvk_total_governors=context.overall_kvk_total_governors,
        overall_kvk_top_percent=context.overall_kvk_top_percent,
        pass_stats=pass_stats,
        prekvk_rank=_int_from_variants(row, ["PreKvk_Rank", "PreKvk Rank"], default=0) or None,
        prekvk_points=_int_from_variants(row, ["Max_PreKvk_Points", "Max PreKvk Points"], default=0)
        or None,
        honor_rank=_int_from_variants(row, ["Honor_Rank", "Honor Rank"], default=0) or None,
        honor_points=_int_from_variants(row, ["Max_HonorPoints", "Max Honor Points"], default=0)
        or None,
        history_summary={
            "Autarch": _int_from_variants(row, ["AutarchTimes", "Autarch Times"], default=0),
            "KVK Played": _int_from_variants(row, ["KvKPlayed", "KVK Played"], default=0),
            "Highest Acclaim": _int_from_variants(
                row, ["HighestAcclaim", "Highest Acclaim"], default=0
            ),
        },
        personal_bests={
            "Most Kills": _int_from_variants(row, ["MostKvKKill", "Most KvK Kill"], default=0),
            "Most Deads": _int_from_variants(row, ["MostKvKDead", "Most KvK Dead"], default=0),
            "Most Heal": _int_from_variants(row, ["MostKvKHeal", "Most KvK Heal"], default=0),
        },
        last_kvk_summary=_last_kvk_summary(last_kvk),
        matchmaking_snapshot={
            "MM KP": _int_from_variants(
                row, ["Starting_KillPoints", "Starting KillPoints"], default=0
            ),
            "MM Kills": _int_from_variants(
                row, ["Starting_T4&T5_KILLS", "Starting T4&T5 Kills"], default=0
            ),
            "MM Deads": _int_from_variants(row, ["Starting_Deads", "Starting Deads"], default=0),
            "MM Healed": _int_from_variants(
                row, ["Starting_HealedTroops", "Starting HealedTroops"], default=0
            ),
        },
    )


def _last_kvk_summary(last_kvk: dict[str, Any]) -> dict[str, int | float | str | None]:
    if not last_kvk:
        return {}
    kills = _int_from_variants(last_kvk, ["T4&T5_Kills", "T4&T5 Kills"], default=0)
    kill_target = _int_from_variants(last_kvk, ["Kill Target", "Kill_Target"], default=0)
    deads = _int_from_variants(last_kvk, ["Deads_Delta", "Deads Delta"], default=0)
    dead_target = _int_from_variants(last_kvk, ["Dead_Target", "Dead Target"], default=0)
    dkp = _int_from_variants(last_kvk, ["DKP_SCORE", "DKP Score"], default=0)
    dkp_target = _int_from_variants(last_kvk, ["DKP_Target", "DKP Target"], default=0)
    return {
        "KVK_NO": _int_from_variants(last_kvk, ["KVK_NO"], default=0) or None,
        "Kills": kills,
        "Kill Target": kill_target,
        "Kill Percent": _pct(kills, kill_target),
        "Deads": deads,
        "Dead Target": dead_target,
        "Dead Percent": _pct(deads, dead_target),
        "DKP": dkp,
        "DKP Target": dkp_target,
        "DKP Percent": _pct(dkp, dkp_target),
        "KP": _int_from_variants(last_kvk, ["KillPointsDelta", "KillPoints"], default=0),
        "Acclaim": _int_from_variants(last_kvk, ["Acclaim", "AcclaimScore"], default=0),
    }
