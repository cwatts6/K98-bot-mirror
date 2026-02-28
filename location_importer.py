import csv
import inspect
import io
import logging
import os

import pyodbc

from constants import DATABASE, PASSWORD, SERVER, USERNAME
from file_utils import fetch_one_dict

log = logging.getLogger(__name__)


def _get_conn():
    user = os.getenv("IMPORT_SQL_USERNAME", USERNAME)
    pwd = os.getenv("IMPORT_SQL_PASSWORD", PASSWORD)
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};DATABASE={DATABASE};UID={user};PWD={pwd}",
        autocommit=False,
    )


def parse_output_csv(csv_bytes: bytes) -> list[tuple]:
    """
    Returns tuples matching dbo.PlayerLocation_Staging insert order:
    (player_id, player_name, player_power, player_kills, player_ch, player_alliance, x, y)
    """
    text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[tuple] = []
    for r in reader:
        try:
            pid = int(str(r.get("player_id", "")).strip())
            name = (r.get("player_name") or "").strip()
            pwr = int(str(r.get("player_power", "0") or 0))
            kills = int(str(r.get("player_kills", "0") or 0))
            ch = int(str(r.get("player_ch", "0") or 0))
            ally = (r.get("player_alliance") or "").strip()
            x = int(str(r.get("x", "")).strip())
            y = int(str(r.get("y", "")).strip())
            rows.append((pid, name, pwr, kills, ch, ally, x, y))
        except Exception as e:
            log.warning(f"[location_import] Skipping bad row {r}: {e}")
    return rows


def _normalize_rows_args(*rows_args) -> list[tuple]:
    """
    Normalize a variety of calling forms into a single list of row tuples.

    Supported input shapes (defensive because offload helpers may expand args):
    - single argument that's a list/tuple of row-tuples: ([ (..), (..), ... ],)
    - multiple positional arguments each being a row-tuple: (row1, row2, row3, ...)
    - multiple positional arguments where each arg is itself a list/tuple of rows
      (this happens when the offload layer splits large payloads into multiple blobs).
    The function flattens and returns a single list of (pid, name, power, kills, ch, ally, x, y) tuples.
    """
    # Diagnostic: log incoming shape (count & sample types)
    try:
        sample_types = []
        for i, a in enumerate(rows_args[:6]):  # sample up to first 6 args
            t = type(a)
            if isinstance(a, (list, tuple)):
                sample_types.append(f"arg{i}:{t.__name__}[len={len(a)}]")
            else:
                sample_types.append(f"arg{i}:{t.__name__}")
        module_file = os.path.abspath(__file__) if "__file__" in globals() else "<unknown>"
        log.debug(
            "[location_import] _normalize_rows_args called; args_count=%d; sample=%s; module=%s; func_sig=%s",
            len(rows_args),
            sample_types,
            module_file,
            inspect.signature(_normalize_rows_args),
        )
    except Exception:
        # If diagnostics fail, don't stop execution
        log.debug("[location_import] _normalize_rows_args diagnostic logging failed", exc_info=True)

    if not rows_args:
        return []

    # If a single argument and it's already a list-like of rows, return it (shallow copy)
    if len(rows_args) == 1:
        single = rows_args[0]
        if isinstance(single, (list, tuple)):
            # If it's a list/tuple of row-tuples, coerce to list and return
            # If it's e.g. bytes/string/etc, fall through to ensure we don't try to iterate chars.
            # Check that elements look like rows (tuples of length >= 1 and ints/strs)
            try:
                if all(isinstance(r, (list, tuple)) for r in single):
                    return list(single)
            except Exception:
                pass

    # Otherwise we received multiple args; flatten them.
    flattened: list[tuple] = []
    for a in rows_args:
        if a is None:
            continue
        if isinstance(a, (list, tuple)):
            # If this is a sequence of row tuples, extend; else if it's a single row-tuple treat appropriately
            # Distinguish between a single row-tuple and a sequence of row-tuples by inspecting element types.
            if a and all(isinstance(x, (list, tuple)) for x in a):
                flattened.extend(list(a))
            else:
                # It's probably a single row tuple (or a heterogeneous iterable) — append as one row.
                flattened.append(tuple(a) if not isinstance(a, tuple) else a)
        else:
            # Single atomic arg — append as a 1-tuple wrapped value (unlikely for our use, but safe)
            flattened.append((a,))
    return flattened


def load_staging_and_merge(*rows_args) -> tuple[int, int]:
    """
    Truncate staging, bulk-insert rows, run merge proc.
    Returns (staging_rows, total_tracked).

    Accepts either:
      - a single argument that's a list of row-tuples, or
      - multiple positional row-tuples (defensive for offload callers that expand args).
    """
    # Diagnostic: record who we are and what we got
    try:
        module_file = os.path.abspath(__file__) if "__file__" in globals() else "<unknown>"
        log.info(
            "[location_import] load_staging_and_merge called; module=%s; raw_args=%d",
            module_file,
            len(rows_args),
        )
    except Exception:
        log.debug(
            "[location_import] load_staging_and_merge diagnostic logging failed", exc_info=True
        )

    rows = _normalize_rows_args(*rows_args)

    if not rows:
        return (0, 0)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # cur.execute("TRUNCATE TABLE dbo.PlayerLocation_Staging;")
            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.PlayerLocation_Staging
                (player_id, player_name, player_power, player_kills, player_ch, player_alliance, x, y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            cur.execute("EXEC dbo.sp_ImportPlayerLocationFromStaging;")
            result = fetch_one_dict(cur)
        conn.commit()

        # Normalize the procedure result to the expected (imported_rows, total_tracked)
        if not result:
            # If the proc returned nothing, fall back to sensible defaults
            staging_rows = len(rows)
            total_tracked = 0
            return staging_rows, total_tracked

        vals_iter = iter(result.values())
        first_val = next(vals_iter, None)
        second_val = next(vals_iter, None)

        staging_rows = int(first_val) if first_val is not None else len(rows)
        total_tracked = int(second_val) if second_val is not None else 0
        return staging_rows, total_tracked

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_staging_and_replace(*rows_args) -> tuple[int, int]:
    """
    Clears staging, bulk-inserts rows, then atomically replaces dbo.PlayerLocation
    only if staging has >0 rows. Returns (imported_rows, total_tracked).

    Accepts either:
      - a single argument that's a list of row-tuples, or
      - multiple positional row-tuples (defensive for offload callers that expand args).
    """
    # Diagnostic: log invocation shape and module file (helps confirm which copy is imported)
    try:
        module_file = os.path.abspath(__file__) if "__file__" in globals() else "<unknown>"
        preview = []
        for i, a in enumerate(rows_args[:6]):
            preview.append(f"{i}:{type(a).__name__}")
        log.info(
            "[location_import] load_staging_and_replace called; module=%s; raw_args=%d; preview=%s",
            module_file,
            len(rows_args),
            preview,
        )
    except Exception:
        log.debug(
            "[location_import] load_staging_and_replace diagnostic logging failed", exc_info=True
        )

    rows = _normalize_rows_args(*rows_args)

    # Log result of normalization (counts)
    try:
        log.info(
            "[location_import] _normalize_rows_args produced %d rows; first_row_sample=%s",
            len(rows),
            rows[0] if rows else None,
        )
    except Exception:
        log.debug("[location_import] normalization logging failed", exc_info=True)

    if not rows:
        return (0, 0)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Clear staging (requires ALTER on staging for TRUNCATE; otherwise use DELETE)
            cur.execute("TRUNCATE TABLE dbo.PlayerLocation_Staging;")

            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.PlayerLocation_Staging
                (player_id, player_name, player_power, player_kills, player_ch, player_alliance, x, y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

            # Atomic full-replace (only if >0 rows in staging)
            cur.execute("EXEC dbo.sp_ReplacePlayerLocationFromStaging;")
            result = fetch_one_dict(cur)

        conn.commit()

        # Normalize the procedure result to the expected (imported_rows, total_tracked)
        if not result:
            return (0, 0)

        vals_iter = iter(result.values())
        first_val = next(vals_iter, None)
        second_val = next(vals_iter, None)

        imported_rows = int(first_val) if first_val is not None else 0
        total_tracked = int(second_val) if second_val is not None else imported_rows
        return imported_rows, total_tracked

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
