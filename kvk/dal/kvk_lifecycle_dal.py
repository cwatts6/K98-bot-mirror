"""Data-access helpers for the shared KVK lifecycle metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import datetime as dt
from typing import Any

from file_utils import fetch_one_dict, get_conn_with_retries

LATEST_KVK_DETAILS_SQL = """
    SELECT TOP 1
        KVK_NO,
        KVK_NAME,
        KVK_REGISTRATION_DATE,
        KVK_START_DATE,
        KVK_END_DATE,
        CAST(MATCHMAKING_START_DATE AS date) AS MATCHMAKING_START_DATE,
        CAST(FIGHTING_START_DATE AS date) AS FIGHTING_START_DATE,
        NEXT_KVK_NO,
        MATCHMAKING_SCAN,
        PASS4_START_SCAN,
        KVK_END_SCAN
    FROM dbo.KVK_Details
    WHERE KVK_NO IS NOT NULL
    ORDER BY KVK_NO DESC
"""

MAX_SCAN_ORDER_SQL = "SELECT MAX(ScanOrder) AS MaxScanOrder FROM ROK_TRACKER.dbo.kingdomscandata4"

CURRENT_KVK_CONFIG_SQL = """
    SELECT MAX(TRY_CAST(ConfigValue AS int)) AS CurrentKVK
    FROM dbo.ProcConfig
    WHERE ConfigKey = 'CURRENTKVK3'
"""

KVK_WINDOW_CONFIG_SQL = """
    SELECT ConfigKey, ConfigValue
    FROM dbo.ProcConfig
    WHERE KVKVersion = ? AND ConfigKey IN ('MATCHMAKING_SCAN', 'KVK_END_SCAN')
"""


@dataclass(frozen=True, slots=True)
class KvkLifecycleDetailsRecord:
    """Canonical mapped values from the latest ``dbo.KVK_Details`` row."""

    kvk_no: int | None
    kvk_name: str | None
    registration: dt.date | None
    start_date: dt.date | None
    end_date: dt.date | None
    matchmaking_start_date: dt.date | None
    fighting_start_date: dt.date | None
    next_kvk_no: int | None
    matchmaking_scan: int | None
    pass4_start_scan: int | None
    kvk_end_scan: int | None


@dataclass(frozen=True, slots=True)
class ProcConfigWindowRecord:
    """Canonical mapped values from the current KVK ``ProcConfig`` rows."""

    current_kvk: int | None
    matchmaking_scan: int | None
    kvk_end_scan: int | None


def _as_date(value: Any) -> dt.date | None:
    if not value:
        return None
    if isinstance(value, dt.date):
        return value
    try:
        return dt.datetime.fromisoformat(str(value)).date()
    except Exception:
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _map_latest_kvk_details_row(row: Mapping[str, Any]) -> KvkLifecycleDetailsRecord:
    values = list(row.values())

    def by_name(*names: str, idx: int) -> Any:
        for name in names:
            if name in row:
                return row[name]
        return values[idx] if idx < len(values) else None

    return KvkLifecycleDetailsRecord(
        kvk_no=_as_int(by_name("KVK_NO", idx=0)),
        kvk_name=by_name("KVK_NAME", idx=1),
        registration=_as_date(by_name("KVK_REGISTRATION_DATE", idx=2)),
        start_date=_as_date(by_name("KVK_START_DATE", idx=3)),
        end_date=_as_date(by_name("KVK_END_DATE", idx=4)),
        matchmaking_start_date=_as_date(by_name("MATCHMAKING_START_DATE", idx=5)),
        fighting_start_date=_as_date(by_name("FIGHTING_START_DATE", idx=6)),
        next_kvk_no=_as_int(by_name("NEXT_KVK_NO", "NextKVKNo", idx=7)),
        matchmaking_scan=_as_int(by_name("MATCHMAKING_SCAN", idx=8)),
        pass4_start_scan=_as_int(by_name("PASS4_START_SCAN", idx=9)),
        kvk_end_scan=_as_int(by_name("KVK_END_SCAN", idx=10)),
    )


def fetch_latest_kvk_details_record() -> KvkLifecycleDetailsRecord | None:
    """Read and map the latest non-null KVK details row."""
    with get_conn_with_retries() as conn, conn.cursor() as cur:
        cur.execute(LATEST_KVK_DETAILS_SQL)
        row = fetch_one_dict(cur)
    if not row:
        return None
    return _map_latest_kvk_details_row(row)


def fetch_max_scan_order() -> int | None:
    """Read the latest imported ``KingdomScanData4`` scan order."""
    with get_conn_with_retries() as conn, conn.cursor() as cur:
        cur.execute(MAX_SCAN_ORDER_SQL)
        row = fetch_one_dict(cur)
    if not row:
        return None
    return _as_int(row.get("MaxScanOrder", next(iter(row.values()), None)))


def fetch_proc_config_window_record() -> ProcConfigWindowRecord:
    """Read and map the current KVK broad-window fallback configuration."""
    with get_conn_with_retries() as conn, conn.cursor() as cur:
        cur.execute(CURRENT_KVK_CONFIG_SQL)
        row = fetch_one_dict(cur)
        current_kvk = _as_int(row.get("CurrentKVK")) if row else None
        if not current_kvk:
            return ProcConfigWindowRecord(
                current_kvk=None,
                matchmaking_scan=None,
                kvk_end_scan=None,
            )

        cur.execute(KVK_WINDOW_CONFIG_SQL, (current_kvk,))
        kv_map = {item.ConfigKey: item.ConfigValue for item in cur.fetchall()}

    return ProcConfigWindowRecord(
        current_kvk=current_kvk,
        matchmaking_scan=_as_int(kv_map.get("MATCHMAKING_SCAN")),
        kvk_end_scan=_as_int(kv_map.get("KVK_END_SCAN")),
    )
