# stats_alerts/db.py
"""
Central DB wrapper helpers.

Purpose:
- Centralise get_conn_with_retries usage and common cursor patterns.
- Provide sync helpers (run_query, run_one, run_scalar, execute) and async wrappers.
- Convert pyodbc rows -> dict via stats_helpers.cursor_row_to_dict / fetch_all_dicts.
"""

import asyncio
from collections.abc import Callable, Sequence
import logging
from typing import Any

from file_utils import get_conn_with_retries
from stats_helpers import cursor_row_to_dict

logger = logging.getLogger(__name__)


def _exec_and_fetch_all_dicts(cursor) -> list[dict]:
    """Convert all fetched rows to list[dict] using cursor_row_to_dict."""
    rows = cursor.fetchall()
    return [cursor_row_to_dict(cursor, r) for r in rows]


def _params_for_execute(params: Sequence[Any] | None) -> tuple[Any, ...]:
    """Normalize params to tuple for safe passing to pyodbc execute."""
    if not params:
        return ()
    if isinstance(params, (list, tuple)):
        return tuple(params)
    return (params,)


def run_query(
    sql: str, params: Sequence[Any] | None = None, *, timeout_ms: int | None = None
) -> list[dict]:
    """
    Execute a SELECT-style query and return list[dict] rows.

    Example:
        rows = run_query("SELECT id, name FROM dbo.X WHERE foo = ?", (val,))
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            if timeout_ms:
                try:
                    cur.timeout = timeout_ms // 1000  # pyodbc uses seconds for timeout
                except Exception:
                    pass
            params_t = _params_for_execute(params)
            if params_t:
                cur.execute(sql, *params_t)
            else:
                cur.execute(sql)
            return [cursor_row_to_dict(cur, r) for r in cur.fetchall()]
    except Exception:
        logger.exception("[DB] run_query failed")
        return []


def run_query_raw(sql: str, params: Sequence[Any] | None = None) -> list[tuple]:
    """
    Execute a query and return raw tuples (no conversion to dict).
    Useful for scalar aggregation or when column metadata isn't needed.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            params_t = _params_for_execute(params)
            if params_t:
                cur.execute(sql, *params_t)
            else:
                cur.execute(sql)
            return [tuple(r) for r in cur.fetchall()]
    except Exception:
        logger.exception("[DB] run_query_raw failed")
        return []


def run_one(sql: str, params: Sequence[Any] | None = None) -> dict | None:
    """
    Execute a query and return the first row as a dict, or None.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            params_t = _params_for_execute(params)
            if params_t:
                cur.execute(sql, *params_t)
            else:
                cur.execute(sql)
            row = cur.fetchone()
            if not row:
                return None
            return cursor_row_to_dict(cur, row)
    except Exception:
        logger.exception("[DB] run_one failed")
        return None


def run_scalar(sql: str, params: Sequence[Any] | None = None) -> Any:
    """
    Execute a query and return the first column of the first row, or None.
    Useful for SELECT COUNT(*) or single-value lookups.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            params_t = _params_for_execute(params)
            if params_t:
                cur.execute(sql, *params_t)
            else:
                cur.execute(sql)
            row = cur.fetchone()
            return None if not row else row[0]
    except Exception:
        logger.exception("[DB] run_scalar failed")
        return None


def execute(sql: str, params: Sequence[Any] | None = None, *, commit: bool = True) -> int:
    """
    Execute a non-SELECT statement (INSERT/UPDATE/DELETE).
    Returns cursor.rowcount (may be -1 in some drivers). Commits if commit=True.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            params_t = _params_for_execute(params)
            if params_t:
                cur.execute(sql, *params_t)
            else:
                cur.execute(sql)
            rowcount = cur.rowcount if hasattr(cur, "rowcount") else -1
            if commit:
                conn.commit()
            return int(rowcount or 0)
    except Exception:
        logger.exception("[DB] execute failed")
        return -1


def exec_with_cursor(callback: Callable, *, close_conn: bool = True) -> Any:
    """
    Open a connection and pass the cursor to callback(cursor). Return callback result.
    Useful when you have multiple queries that must share the same cursor/connection.

    Example:
        def cb(cur):
            cur.execute("SELECT ...", ...)
            x = cur.fetchone()
            cur.execute("SELECT ...", ...)
            return [cursor_row_to_dict(cur, r) for r in cur.fetchall()]

        result = exec_with_cursor(cb)
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            return callback(cur)
    except Exception:
        logger.exception("[DB] exec_with_cursor failed")
        return None


# ------------------------
# Async wrappers
# ------------------------
# These simply run the blocking versions in a thread. Use these when calling from async code.


async def run_query_async(
    sql: str, params: Sequence[Any] | None = None, *, timeout_ms: int | None = None
) -> list[dict]:
    return await asyncio.to_thread(run_query, sql, params, timeout_ms=timeout_ms)


async def run_one_async(sql: str, params: Sequence[Any] | None = None) -> dict | None:
    return await asyncio.to_thread(run_one, sql, params)


async def run_scalar_async(sql: str, params: Sequence[Any] | None = None) -> Any:
    return await asyncio.to_thread(run_scalar, sql, params)


async def execute_async(
    sql: str, params: Sequence[Any] | None = None, *, commit: bool = True
) -> int:
    return await asyncio.to_thread(execute, sql, params, commit=commit)
