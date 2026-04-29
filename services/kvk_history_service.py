"""Service layer for KVK history account resolution and data shaping."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import logging
import re
from typing import Any

import pandas as pd

from account_picker import ACCOUNT_ORDER
from kvk.dal import kvk_history_dal

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


def empty_history_frame() -> pd.DataFrame:
    """Return an empty history dataframe with the canonical schema."""
    return pd.DataFrame(columns=HISTORY_COLUMNS)


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


def fetch_history_for_governors(governor_ids: Iterable[Any] | Any) -> pd.DataFrame:
    """Return a canonical history dataframe for the supplied governors."""
    ids = normalize_governor_ids(governor_ids)
    if not ids:
        return empty_history_frame()

    rows = kvk_history_dal.fetch_history_rows_for_governors(ids)
    df = pd.DataFrame.from_records(rows, columns=HISTORY_COLUMNS)
    started = kvk_history_dal.get_started_kvks()

    if df.empty:
        return empty_history_frame()

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
