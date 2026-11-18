# telemetry/dal/command_usage_dal.py
"""
Data-access layer for BotCommandUsage.  No Discord types; all SQL lives here.
Pattern follows ark/dal/ark_dal.py.
"""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import UTC, datetime
import json
import logging
from typing import Any

from constants import USAGE_TABLE
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Connection helper                                                             #
# --------------------------------------------------------------------------- #


def _get_conn():
    from file_utils import get_conn_with_retries

    return get_conn_with_retries()


# --------------------------------------------------------------------------- #
# Low-level query helpers                                                       #
# --------------------------------------------------------------------------- #


def ctx_filter_sql(context: str) -> tuple[str, tuple]:
    """Return a SQL fragment and params tuple to filter by AppContext."""
    if context == "all":
        return ("", tuple())
    return (" AND appcontext = ? ", (context,))


async def fetch_usage_rows(sql: str, params: tuple) -> list[dict]:
    """Run *sql* with *params* off the event loop; return list of row dicts."""

    def _run():
        with _get_conn() as cn:
            cur = cn.cursor()
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]

    return await asyncio.to_thread(_run)


# --------------------------------------------------------------------------- #
# Read-side summaries                                                           #
# --------------------------------------------------------------------------- #

# Period aliases accepted by the DAL layer (command uses "day"/"week", service
# canonical strings are "24h"/"7d"/"30d").
_PERIOD_ALIAS: dict[str, str] = {"day": "24h", "week": "7d"}


def _resolve_period_cutoff(period: str) -> datetime:
    from telemetry.service import period_cutoff

    normalised = _PERIOD_ALIAS.get(period, period)
    return period_cutoff(normalised)


async def fetch_usage_summary(
    by: str,
    period: str,
    context: str,
    limit: int,
) -> list[dict]:
    """
    Return aggregated usage rows.

    *by* is one of 'command', 'user', 'reliability'.
    *period* accepts '24h', '7d', '30d' or the command aliases 'day'/'week'.
    """
    limit = max(1, min(int(limit), 200))
    since = _resolve_period_cutoff(period)
    ctx_sql, ctx_params = ctx_filter_sql(context)

    if by == "user":
        sql = f"""
            SELECT TOP {limit} UserId,
                   MAX(UserDisplay) AS UserDisplay,
                   COUNT(*) AS Uses,
                   COUNT(DISTINCT CommandName) AS UniqueCommands
            FROM {USAGE_TABLE}
            WHERE ExecutedAtUtc >= ?{ctx_sql}
            GROUP BY UserId
            ORDER BY Uses DESC, UserId ASC;
        """
        return await fetch_usage_rows(sql, (since, *ctx_params))

    if by == "reliability":
        sql = f"""
            SELECT CommandName,
                   COUNT(*) AS Total,
                   SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes
            FROM {USAGE_TABLE}
            WHERE ExecutedAtUtc >= ?{ctx_sql}
            GROUP BY CommandName
        """
        rows = await fetch_usage_rows(sql, (since, *ctx_params))
        # Compute success % in Python and sort by worst first
        stats: list[dict] = []
        for r in rows:
            total = int(r.get("Total") or 0)
            ok = int(r.get("Successes") or 0)
            rate = (ok / total * 100.0) if total else 0.0
            stats.append(
                {
                    "CommandName": r.get("CommandName"),
                    "Total": total,
                    "Successes": ok,
                    "Rate": rate,
                }
            )
        stats.sort(key=lambda t: (100.0 - t["Rate"], -t["Total"]))
        return stats[:limit]

    # default: by command
    sql = f"""
        SELECT CommandName,
               COUNT(*) AS Uses,
               SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes,
               AVG(CAST(LatencyMs AS float)) AS AvgLatencyMs
        FROM {USAGE_TABLE}
        WHERE ExecutedAtUtc >= ?{ctx_sql}
        GROUP BY CommandName
        ORDER BY Uses DESC, CommandName ASC;
    """
    rows = await fetch_usage_rows(sql, (since, *ctx_params))
    return rows[:limit]


async def fetch_usage_detail(
    dimension: str,
    value: str,
    period: str,
    context: str,
    limit: int = 10,
) -> list[dict]:
    """
    Return detail rows for a single command or user.

    For dimension='command', returns a list with one summary dict that includes an
    'error_codes' key (list of {ErrorCode, Cnt} dicts).
    For dimension='user', returns a list of per-command usage dicts.
    """
    limit = max(1, min(int(limit), 200))
    since = _resolve_period_cutoff(period)
    ctx_sql, ctx_params = ctx_filter_sql(context)

    if dimension == "command":
        cmd = value.lstrip("/").strip()
        sql_pct = f"""
            WITH s AS (
              SELECT LatencyMs, Success
              FROM {USAGE_TABLE}
              WHERE ExecutedAtUtc >= ? AND CommandName = ?{ctx_sql}
            )
            SELECT
              (SELECT COUNT(*) FROM s) AS Total,
              (SELECT SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) FROM s) AS Successes,
              (SELECT SUM(CASE WHEN Success=0 THEN 1 ELSE 0 END) FROM s) AS Failures,
              (SELECT TOP 1 CAST(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY CAST(LatencyMs AS float)) OVER () AS int)
                 FROM s WHERE LatencyMs IS NOT NULL) AS P50,
              (SELECT TOP 1 CAST(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY CAST(LatencyMs AS float)) OVER () AS int)
                 FROM s WHERE LatencyMs IS NOT NULL) AS P95;
        """
        rows = await fetch_usage_rows(sql_pct, (since, cmd, *ctx_params))
        stats_row = dict(rows[0]) if rows else {}

        sql_errs = f"""
            SELECT TOP 10 ErrorCode, COUNT(*) AS Cnt
            FROM {USAGE_TABLE}
            WHERE ExecutedAtUtc >= ? AND CommandName = ? AND Success = 0{ctx_sql}
            GROUP BY ErrorCode
            ORDER BY Cnt DESC, ErrorCode ASC;
        """
        errs = await fetch_usage_rows(sql_errs, (since, cmd, *ctx_params))
        stats_row["error_codes"] = errs
        return [stats_row]

    # dimension == "user"
    import re

    m = re.search(r"\d{15,22}", value or "")
    uid = int(m.group(0)) if m else int(value)

    sql = f"""
        SELECT CommandName,
               COUNT(*) AS Uses,
               SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes,
               AVG(CAST(LatencyMs AS float)) AS AvgLatencyMs
        FROM {USAGE_TABLE}
        WHERE ExecutedAtUtc >= ? AND UserId = ?{ctx_sql}
        GROUP BY CommandName
        ORDER BY Uses DESC, CommandName ASC;
    """
    return await fetch_usage_rows(sql, (since, uid, *ctx_params))


# --------------------------------------------------------------------------- #
# Write-side flush                                                              #
# --------------------------------------------------------------------------- #


def _coerce_ts(ts: Any) -> Any:
    """
    Coerce a timestamp value to a naive UTC datetime for SQL DATETIME/DATETIME2 parameters.
    """
    if isinstance(ts, str):
        try:
            if ts.endswith("Z"):
                ts = ts[:-1] + "+00:00"
            dt = datetime.fromisoformat(ts)
        except Exception:
            return ts
        return ensure_aware_utc(dt).astimezone(UTC).replace(tzinfo=None)

    if isinstance(ts, datetime):
        return ensure_aware_utc(ts).astimezone(UTC).replace(tzinfo=None)

    return ts


def flush_events(events: list[dict]) -> None:
    """
    Synchronously flush a batch of usage events to SQL.

    Tries executemany first; falls back to per-row execute on failure.
    Logs a structured warning with dropped-count and command names if both paths fail.
    """
    if not events:
        return

    def clip(s: Any, n: int) -> Any:
        return None if s is None else str(s)[:n]

    def row_from(e: dict) -> tuple:
        return (
            _coerce_ts(e.get("executed_at_utc")),
            clip(e.get("command_name"), 64),
            clip(e.get("version"), 16),
            clip(e.get("app_context", "slash"), 16),
            e.get("user_id"),
            clip(e.get("user_display"), 128),
            e.get("guild_id"),
            e.get("channel_id"),
            1 if e.get("success", True) else 0,
            clip(e.get("error_code"), 64),
            e.get("latency_ms"),
            json.dumps(e.get("args_shape")) if e.get("args_shape") else None,
            e.get("error_text"),
        )

    rows = [row_from(e) for e in events]

    cmd_counts = Counter(r[1] for r in rows)
    logger.info(
        "[USAGE] Flushing %d events: %s",
        len(rows),
        ", ".join(f"{k}={v}" for k, v in cmd_counts.most_common()),
    )

    rows.sort(
        key=lambda t: (
            -(len(t[1]) if isinstance(t[1], str) else 0),
            -(len(t[5]) if isinstance(t[5], str) else 0),
            -(len(t[9]) if isinstance(t[9], str) else 0),
            -(len(t[3]) if isinstance(t[3], str) else 0),
        )
    )

    SQL_INSERT = f"""
        INSERT INTO {USAGE_TABLE}
        (ExecutedAtUtc, CommandName, Version, AppContext,
         UserId, UserDisplay, GuildId, ChannelId,
         Success, ErrorCode, LatencyMs, ArgsShape, ErrorText)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS NVARCHAR(MAX)), CAST(? AS NVARCHAR(MAX)))
    """

    try:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            if hasattr(cur, "fast_executemany"):
                try:
                    cur.fast_executemany = False
                except Exception:
                    logger.debug(
                        "[USAGE] Could not set fast_executemany on cursor; continuing safely"
                    )
            cur.executemany(SQL_INSERT, rows)
            conn.commit()
            logger.info(
                "[USAGE] Flushed %d events to SQL (safe batch, no fast_executemany)", len(events)
            )
            return
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        logger.exception("[USAGE] Batch insert (safe) failed; attempting per-row.")

    try:
        conn = _get_conn()
        cur = conn.cursor()
        try:
            for r in rows:
                cur.execute(SQL_INSERT, r)
            conn.commit()
            logger.info("[USAGE] Per-row salvage OK (%d rows)", len(rows))
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        cmd_names = ", ".join(
            str(r[1]) for r in rows if r[1] is not None  # r[1] is CommandName in SQL_INSERT order
        )
        logger.exception(
            "[USAGE] %d events dropped — SQL flush failed (batch and per-row both failed). Commands: %s",
            len(rows),
            cmd_names,
        )
