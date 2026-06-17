"""Service layer for KVK history account resolution and data shaping."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation
import logging
import re
from typing import Any

import pandas as pd

from kvk.dal import kvk_history_dal
from kvk.models.kvk_history_payload import KvkHistoryPayload, KvkHistoryRow, KvkHistoryTrend
from registry.account_slots import ACCOUNT_ORDER

logger = logging.getLogger(__name__)

HISTORY_COLUMNS = [
    "Gov_ID",
    "Governor_Name",
    "KVK_NO",
    "T4_KILLS",
    "T5_KILLS",
    "T4T5_Kills",
    "KillPct",
    "Deads",
    "DeadPct",
    "DKP_SCORE",
    "DKPPct",
    "P4_Kills",
    "P6_Kills",
    "P7_Kills",
    "P8_Kills",
    "P4_Deads",
    "P6_Deads",
    "P7_Deads",
    "P8_Deads",
]

NUMERIC_HISTORY_COLUMNS = [c for c in HISTORY_COLUMNS if c != "Governor_Name"]

HISTORY_EXPORT_COLUMNS = [
    "Gov_ID",
    "Governor_Name",
    "KVK_NO",
    "Kingdom_Rank",
    "KVK_RANK",
    "T4_KILLS",
    "T5_KILLS",
    "T4T5_Kills",
    "Kill_Target",
    "KillPct",
    "Deads",
    "Dead_Target",
    "DeadPct",
    "DKP_SCORE",
    "DKP_Target",
    "DKPPct",
    "Acclaim",
    "HighestAcclaim",
    "KvKPlayed",
    "MostKvKKill",
    "MostKvKDead",
    "MostKvKHeal",
    "P4_Kills",
    "P6_Kills",
    "P7_Kills",
    "P8_Kills",
    "P4_Deads",
    "P6_Deads",
    "P7_Deads",
    "P8_Deads",
]


def empty_history_frame() -> pd.DataFrame:
    """Return an empty history dataframe with the canonical schema."""
    return pd.DataFrame(columns=HISTORY_COLUMNS)


def empty_history_export_frame() -> pd.DataFrame:
    """Return an empty modern history export dataframe with the canonical schema."""
    return pd.DataFrame(columns=HISTORY_EXPORT_COLUMNS)


def normalize_governor_ids(governor_ids: Iterable[Any] | Any) -> list[int]:
    """
    Normalize caller input into unique positive governor IDs.

    Accepts normal iterables like list/set/dict_keys. It also tolerates the
    legacy stringified form ``dict_keys([123])`` so failed offload retries do not
    explode on the first character of the string.
    """
    if governor_ids is None:
        return []

    if isinstance(governor_ids, str):
        values: Iterable[Any] = re.findall(r"\d+", governor_ids)
    elif isinstance(governor_ids, Mapping):
        values = governor_ids.keys()
    else:
        try:
            values = list(governor_ids)
        except TypeError:
            values = [governor_ids]

    out: set[int] = set()
    for raw in values:
        if raw is None:
            continue
        try:
            gid = int(str(raw).strip())
        except (TypeError, ValueError):
            logger.warning("[KVK_HISTORY] Skipping invalid governor_id=%r", raw)
            continue
        if gid > 0:
            out.add(gid)
    return sorted(out)


def build_ordered_account_map(accounts: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Return account metadata in the same slot order used by personal KVK commands."""
    if not accounts:
        return {}

    ordered: dict[str, dict[str, Any]] = {}
    for slot in ACCOUNT_ORDER:
        info = accounts.get(slot) if isinstance(accounts, Mapping) else None
        if isinstance(info, Mapping):
            gid = info.get("GovernorID") or info.get("GovernorId") or info.get("GovernorIdStr")
            if gid:
                try:
                    ordered[slot] = {
                        "GovernorID": int(gid),
                        "GovernorName": info.get("GovernorName") or info.get("Governor") or slot,
                    }
                except (TypeError, ValueError):
                    logger.warning(
                        "Skipping account slot %r: GovernorID %r is not a valid integer", slot, gid
                    )

    for slot in sorted(str(k) for k in accounts.keys() if k not in ordered):
        info = accounts.get(slot)
        if not isinstance(info, Mapping):
            continue
        gid = info.get("GovernorID") or info.get("GovernorId") or info.get("GovernorIdStr")
        if gid:
            try:
                ordered[slot] = {
                    "GovernorID": int(gid),
                    "GovernorName": info.get("GovernorName") or info.get("Governor") or slot,
                }
            except (TypeError, ValueError):
                logger.warning(
                    "Skipping account slot %r: GovernorID %r is not a valid integer", slot, gid
                )
    return ordered


def pick_default_governor_id(account_map: Mapping[str, Mapping[str, Any]]) -> str | None:
    """Prefer Main, then the first account, matching the personal KVK command convention."""
    if not account_map:
        return None
    for label, meta in account_map.items():
        if str(label).lower().startswith("main"):
            return str(meta.get("GovernorID"))
    try:
        return str(next(iter(account_map.values())).get("GovernorID"))
    except StopIteration:
        return None


def get_started_kvks() -> list[int]:
    return kvk_history_dal.get_started_kvks()


def select_last_started_kvks(started_kvks: Iterable[Any], count: int = 3) -> tuple[int, ...]:
    """Return the latest started KVK numbers, preserving missing-data semantics elsewhere."""
    normalized: set[int] = set()
    for raw in started_kvks or []:
        try:
            kvk_no = int(raw)
        except (TypeError, ValueError):
            continue
        if kvk_no > 0:
            normalized.add(kvk_no)
    if count <= 0:
        return tuple()
    return tuple(sorted(normalized)[-count:])


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return int(value)
    if isinstance(value, float):
        return int(value)
    cleaned = str(value).replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        try:
            return int(Decimal(cleaned))
        except (InvalidOperation, ValueError):
            return None
    except TypeError:
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _trim_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _trim_export_name(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def _history_row_from_source(kvk_no: int, source: Mapping[str, Any] | None) -> KvkHistoryRow:
    if not source:
        return KvkHistoryRow(kvk_no=kvk_no, row_present=False)
    return KvkHistoryRow(
        kvk_no=kvk_no,
        row_present=True,
        kvk_rank=_optional_int(source.get("KVK_RANK")),
        kingdom_rank=_optional_int(source.get("Kingdom_Rank")),
        kills=_optional_int(source.get("T4T5_Kills")),
        kill_target_percent=_optional_float(source.get("KillPct")),
        deads=_optional_int(source.get("Deads")),
        dead_target_percent=_optional_float(source.get("DeadPct")),
        dkp=_optional_int(source.get("DKP_SCORE")),
        dkp_target_percent=_optional_float(source.get("DKPPct")),
        acclaim=_optional_int(source.get("Acclaim")),
    )


def _max_optional(rows: Iterable[Mapping[str, Any]], key: str) -> int | None:
    values = [_optional_int(row.get(key)) for row in rows]
    present = [value for value in values if value is not None]
    return max(present) if present else None


def _trend(
    metric: str, rows: Iterable[KvkHistoryRow], attr: str, *, lower_is_better: bool = False
) -> KvkHistoryTrend:
    values = [
        getattr(row, attr) for row in rows if row.row_present and getattr(row, attr) is not None
    ]
    numeric = [float(value) for value in values]
    if not numeric:
        return KvkHistoryTrend(metric=metric, average=None, direction="missing")
    average = sum(numeric) / len(numeric)
    if len(numeric) < 2:
        return KvkHistoryTrend(
            metric=metric,
            average=average,
            direction="insufficient",
            first_value=numeric[0],
            last_value=numeric[-1],
            value_count=len(numeric),
        )
    first = numeric[0]
    last = numeric[-1]
    if last == first:
        direction = "flat"
    elif (last < first and lower_is_better) or (last > first and not lower_is_better):
        direction = "up"
    else:
        direction = "down"
    return KvkHistoryTrend(
        metric=metric,
        average=average,
        direction=direction,
        first_value=first,
        last_value=last,
        value_count=len(numeric),
    )


def fetch_history_export_for_governors(governor_ids: Iterable[Any] | Any) -> pd.DataFrame:
    """Return a null-preserving, expanded history dataframe for CSV export."""
    ids = normalize_governor_ids(governor_ids)
    if not ids:
        return empty_history_export_frame()

    rows = kvk_history_dal.fetch_modern_history_rows_for_governors(ids)
    df = pd.DataFrame.from_records(rows, columns=HISTORY_EXPORT_COLUMNS)
    if df.empty:
        return empty_history_export_frame()
    df["Governor_Name"] = df["Governor_Name"].map(_trim_export_name)
    return df.sort_values(["Gov_ID", "KVK_NO"], ignore_index=True)


def build_kvk_history_payload(governor_id: Any) -> KvkHistoryPayload:
    """Build the renderer-independent modern KVK history payload for one governor."""
    ids = normalize_governor_ids([governor_id])
    gid = ids[0] if ids else 0
    started_kvks = tuple(get_started_kvks())
    last3_kvks = select_last_started_kvks(started_kvks, 3)

    if gid <= 0:
        return KvkHistoryPayload(
            governor_id=str(governor_id or "unknown"),
            governor_name="Unknown governor",
            started_kvks=started_kvks,
            last3_kvks=last3_kvks,
            rows=tuple(_history_row_from_source(kvk, None) for kvk in started_kvks),
            last3_rows=tuple(_history_row_from_source(kvk, None) for kvk in last3_kvks),
        )

    source_rows = kvk_history_dal.fetch_modern_history_rows_for_governors([gid])
    rows_by_kvk: dict[int, Mapping[str, Any]] = {}
    for row in source_rows:
        kvk_no = _optional_int(row.get("KVK_NO"))
        if kvk_no is not None:
            rows_by_kvk[kvk_no] = row

    governor_name = str(gid)
    for row in source_rows:
        name = _trim_text(row.get("Governor_Name"))
        if name is not None:
            governor_name = name
            break

    all_kvks = started_kvks or tuple(sorted(rows_by_kvk))
    rows = tuple(_history_row_from_source(kvk, rows_by_kvk.get(kvk)) for kvk in all_kvks)
    last3_rows = tuple(_history_row_from_source(kvk, rows_by_kvk.get(kvk)) for kvk in last3_kvks)

    summary = {
        "KVK Played": _max_optional(source_rows, "KvKPlayed"),
        "Highest Acclaim": _max_optional(source_rows, "HighestAcclaim"),
        "Most Kills": _max_optional(source_rows, "MostKvKKill"),
        "Most Deads": _max_optional(source_rows, "MostKvKDead"),
        "Most Heal": _max_optional(source_rows, "MostKvKHeal"),
    }
    trends = {
        "rank": _trend("rank", last3_rows, "kvk_rank", lower_is_better=True),
        "kills": _trend("kills", last3_rows, "kills"),
        "deads": _trend("deads", last3_rows, "deads"),
        "dkp": _trend("dkp", last3_rows, "dkp"),
        "acclaim": _trend("acclaim", last3_rows, "acclaim"),
    }
    return KvkHistoryPayload(
        governor_id=str(gid),
        governor_name=governor_name,
        started_kvks=all_kvks,
        last3_kvks=last3_kvks,
        rows=rows,
        last3_rows=last3_rows,
        history_summary=summary,
        trends=trends,
    )


def fetch_history_for_governors(governor_ids: Iterable[Any] | Any) -> pd.DataFrame:
    """Return a canonical history dataframe for the supplied governors."""
    ids = normalize_governor_ids(governor_ids)
    if not ids:
        return empty_history_frame()

    rows = kvk_history_dal.fetch_history_rows_for_governors(ids)
    df = pd.DataFrame.from_records(rows, columns=HISTORY_COLUMNS)

    if df.empty:
        return empty_history_frame()

    started = kvk_history_dal.get_started_kvks()
    for col in NUMERIC_HISTORY_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    frames = []
    for gid, gdf in df.groupby("Gov_ID", dropna=False):
        gname = (
            gdf["Governor_Name"].dropna().iloc[0]
            if not gdf["Governor_Name"].dropna().empty
            else None
        )
        existing = set(int(x) for x in gdf["KVK_NO"].tolist())
        missing = [k for k in started if k not in existing]
        if missing:
            zeros = pd.DataFrame(
                {
                    "Gov_ID": gid,
                    "Governor_Name": gname,
                    "KVK_NO": missing,
                    "T4_KILLS": 0,
                    "T5_KILLS": 0,
                    "T4T5_Kills": 0,
                    "KillPct": 0.0,
                    "Deads": 0,
                    "DeadPct": 0.0,
                    "DKP_SCORE": 0,
                    "DKPPct": 0.0,
                    "P4_Kills": 0,
                    "P6_Kills": 0,
                    "P7_Kills": 0,
                    "P8_Kills": 0,
                    "P4_Deads": 0,
                    "P6_Deads": 0,
                    "P7_Deads": 0,
                    "P8_Deads": 0,
                }
            )
            gdf = pd.concat([gdf, zeros], ignore_index=True)
        frames.append(gdf.sort_values(["KVK_NO"]))

    if not frames:
        return empty_history_frame()
    return pd.concat(frames, ignore_index=True).sort_values(["Gov_ID", "KVK_NO"])
