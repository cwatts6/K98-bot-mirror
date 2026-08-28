"""
sheet_importer.py

Shared helpers for writing pandas DataFrames into SQL Server tables and related utilities.

Functions:
- detect_transient_error(exc) -> bool
- executemany_batched(cursor, conn, sql, rows, batch_size=..., commit_per_batch=True) -> int
- quote_sql_columns(cols) -> str
- write_df_to_table(cursor, conn, df, table_name, mode='truncate', key_cols=None, batch_size=..., commit_per_batch=True, transactional=False) -> dict
- write_df_to_staging_and_upsert(cursor, conn, df, staging_table, upsert_proc, transactional=True) -> dict

These helpers are intentionally conservative and return structured dicts for callers to include in run reports.
"""

from __future__ import annotations

from collections.abc import Iterable
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def detect_transient_error(exc: BaseException) -> bool:
    """
    Lightweight predicate to classify common transient errors (network/timeouts/server busy).
    This mirrors the similar logic used in gsheet callers and SQL connection retries.
    """
    try:
        import socket
        import ssl

        from googleapiclient.errors import HttpError  # type: ignore
    except Exception:
        socket = None
        ssl = None
        HttpError = ()

    # Conservative, obvious cases
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    try:
        if socket and isinstance(exc, socket.timeout):
            return True
    except Exception:
        pass
    try:
        if ssl and isinstance(exc, ssl.SSLError):
            return True
    except Exception:
        pass
    try:
        if HttpError and isinstance(exc, HttpError):
            try:
                code = int(exc.resp.status)
                return code >= 500 or code in (408, 429)
            except Exception:
                return True
    except Exception:
        pass
    return False


def quote_sql_columns(cols: Iterable[str]) -> str:
    """
    Quote SQL Server identifiers using square brackets and escape any closing bracket by doubling it.
    Returns comma-separated quoted identifiers.
    """
    quoted: list[str] = []
    for c in cols:
        s = str(c)
        s = s.replace("]", "]]")
        quoted.append(f"[{s}]")
    return ",".join(quoted)


def executemany_batched(
    cursor,
    conn,
    sql: str,
    rows: list[tuple],
    batch_size: int = 5000,
    *,
    commit_per_batch: bool = True,
) -> int:
    """
    Execute parameterized SQL in batches to handle large datasets safely.

    Returns the number of rows inserted. Raises on failure.
    """
    if not rows:
        logger.debug("[BATCH] No rows to insert")
        return 0

    total_rows = len(rows)

    # Single-batch optimisation
    if total_rows <= batch_size:
        cursor.executemany(sql, rows)
        if commit_per_batch:
            try:
                conn.commit()
            except Exception:
                # Let caller handle commit errors separately
                pass
        logger.debug("[BATCH] Inserted %d rows in single batch", total_rows)
        return total_rows

    logger.info("[BATCH] Inserting %d rows in batches of %d", total_rows, batch_size)
    inserted = 0
    for i in range(0, total_rows, batch_size):
        batch = rows[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_rows + batch_size - 1) // batch_size
        try:
            cursor.executemany(sql, batch)
            if commit_per_batch:
                try:
                    conn.commit()
                except Exception:
                    pass
            inserted += len(batch)
            if batch_num % 10 == 0 or batch_num == total_batches:
                logger.info(
                    "[BATCH] Progress: %d/%d batches (%d/%d rows)",
                    batch_num,
                    total_batches,
                    inserted,
                    total_rows,
                )
        except Exception as e:
            logger.error(
                "[BATCH] Failed at batch %d/%d (rows %d-%d): %s",
                batch_num,
                total_batches,
                i,
                i + len(batch),
                e,
            )
            if not commit_per_batch:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
    logger.info("[BATCH] Completed: inserted %d rows in %d batches", inserted, total_batches)
    return inserted


def to_db_rows(df: pd.DataFrame) -> list[tuple]:
    """
    Convert DataFrame to DB-ready rows: replace pandas NA/NaT with None and return tuples.
    """
    df2 = df.copy()
    df2 = df2.astype(object).where(pd.notnull(df2), None)
    return [tuple(row) for row in df2.itertuples(index=False, name=None)]


def write_df_to_table(
    cursor,
    conn,
    df: pd.DataFrame,
    table_name: str,
    mode: str = "truncate",
    key_cols: list[str] | None = None,
    batch_size: int = 5000,
    commit_per_batch: bool = True,
    transactional: bool = False,
) -> dict:
    """
    Write a DataFrame into SQL Server table using batched INSERTs.

    Returns structured dict:
      {"table": table_name, "rows": int, "mode": mode, "status": "ok"|"error", "error": str|None}

    - transactional=True -> do not perform commits inside this helper (caller will commit/rollback)
    """
    out = {"table": table_name, "rows": 0, "mode": mode, "status": "ok", "error": None}
    try:
        if df is None or df.empty:
            logger.info("[%s] No rows to import.", table_name)
            return out

        cols = list(df.columns)
        if not cols:
            out["status"] = "ok"
            return out

        # Pre-delete behaviour
        if mode == "truncate":
            try:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
                if not transactional:
                    conn.commit()
            except Exception as e:
                logger.debug("TRUNCATE failed for %s: %s - falling back to DELETE", table_name, e)
                cursor.execute(f"DELETE FROM {table_name}")
                if not transactional:
                    conn.commit()
        elif mode == "replace":
            cursor.execute(f"DELETE FROM {table_name}")
            if not transactional:
                conn.commit()
        elif mode == "delete_by_kvk":
            if not key_cols:
                raise RuntimeError("delete_by_kvk mode requires key_cols")
            if len(key_cols) == 1:
                key = key_cols[0]
                vals = sorted(set(v for v in df[key].tolist() if v is not None and pd.notna(v)))
                if vals:
                    chunksize = max(1000, batch_size)
                    for i in range(0, len(vals), chunksize):
                        chunk = vals[i : i + chunksize]
                        qmarks = ",".join(["?"] * len(chunk))
                        sql = f"DELETE FROM {table_name} WHERE [{key}] IN ({qmarks})"
                        cursor.execute(sql, *chunk)
                    if not transactional:
                        conn.commit()
            else:
                uniq = df[key_cols].drop_duplicates().dropna()
                for row in uniq.itertuples(index=False, name=None):
                    where = " AND ".join(f"[{k}]=?" for k in key_cols)
                    cursor.execute(f"DELETE FROM {table_name} WHERE {where}", *row)
                if not transactional:
                    conn.commit()
        else:
            raise RuntimeError(f"Unknown mode: {mode}")

        cols_sql = quote_sql_columns(cols)
        qmarks = ",".join(["?"] * len(cols))
        insert_sql = f"INSERT INTO {table_name} ({cols_sql}) VALUES ({qmarks})"

        fe = False
        try:
            cursor.fast_executemany = True
            fe = bool(getattr(cursor, "fast_executemany", False))
        except Exception:
            fe = False

        rows = to_db_rows(df)
        use_commit_per_batch = False if transactional else commit_per_batch
        inserted = executemany_batched(
            cursor, conn, insert_sql, rows, batch_size, commit_per_batch=use_commit_per_batch
        )
        out["rows"] = inserted
        logger.info(
            "[%s] Inserted %d rows (fast_executemany=%s)",
            table_name,
            inserted,
            "ON" if fe else "off",
        )
        return out

    except Exception as e:
        out["status"] = "error"
        out["error"] = str(e)
        logger.exception("[%s] write_df_to_table failed: %s", table_name, e)
        return out


def write_df_to_staging_and_upsert(
    cursor,
    conn,
    df: pd.DataFrame,
    staging_table: str,
    upsert_proc: str,
    batch_size: int = 5000,
    transactional: bool = True,
) -> dict:
    """
    Convenience wrapper: write df to staging_table (truncate + insert) and call upsert_proc.

    Returns dict containing both write result and upsert result status.
    """
    result = {"staging": None, "upsert": None}
    # Write staging (do not commit if transactional True)
    res = write_df_to_table(
        cursor,
        conn,
        df,
        staging_table,
        mode="truncate",
        batch_size=batch_size,
        commit_per_batch=False,
        transactional=transactional,
    )
    result["staging"] = res
    if res.get("status") != "ok":
        return result

    try:
        cursor.execute(f"EXEC {upsert_proc}")
        # Upsert executed; caller may commit when desired
        result["upsert"] = {"proc": upsert_proc, "status": "ok", "error": None}
    except Exception as e:
        result["upsert"] = {"proc": upsert_proc, "status": "error", "error": str(e)}
    return result


__all__ = [
    "detect_transient_error",
    "executemany_batched",
    "quote_sql_columns",
    "to_db_rows",
    "write_df_to_staging_and_upsert",
    "write_df_to_table",
]
