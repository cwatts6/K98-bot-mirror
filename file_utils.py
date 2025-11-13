# file_utils.py
"""
Shared file utilities for atomic IO and simple cross-process locking.

Functions provided:
- resolve_path(env_or_path) -> pathlib.Path
- atomic_write_json(path, obj)
- atomic_write_csv(path, header, rows)
- read_csv_rows_safe(path) -> list[list[str]]
- acquire_lock(path, timeout=5) -> contextmanager: acquires exclusive lock via O_EXCL file
- release_lock(path)
- Contains a small DB connection helper get_conn_with_retries() which delegates to
- the canonical constants._conn() factory and implements exponential backoff with
- full jitter for transient pyodbc.OperationalError failures.
- cursor_row_to_dict(cursor, row), fetch_all_dicts(cursor), fetch_one_dict(cursor)
- canonical DB row -> dict helpers
 - move_if_not_exists(src, dst) -> bool
"""

# ---------------------------------------------------------------------
# New: process helper wrappers (delegate to process_utils, lazy import)
# ---------------------------------------------------------------------
# Purpose:
# - Provide backwards-compatible helpers in file_utils so callers can continue
#   to call file_utils.pid_alive(...) or file_utils.get_process_info(...)
# - Delegate actual logic to the canonical process_utils module.
# - Use lazy imports so importing file_utils does not cause import cycles.
#
# Usage:
#   from file_utils import pid_alive, get_process_info, matches_process
#
# Note: If you prefer consumers to import process_utils directly, you can
# gradually migrate callers. These thin wrappers are intentionally tiny.
# ---------------------------------------------------------------------


from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
import csv
from datetime import datetime
import io
from io import StringIO
from itertools import zip_longest
import json
import logging
import os
from pathlib import Path
import random
import shutil
import time
from typing import Any

import aiofiles

# Use the repo canonical connector
from constants import _conn

logger = logging.getLogger(__name__)

DEFAULT_LOCK_RETRY_INTERVAL = 0.1

# Use PEP 604 | syntax for unions (pre-commit UP007)
PathLike = str | Path

# Env-configurable retry params (reasonable defaults)
_DB_RETRIES = int(os.getenv("DB_CONN_RETRIES", "5"))
_DB_BACKOFF_BASE = float(os.getenv("DB_BACKOFF_BASE", "1.0"))  # seconds
_DB_BACKOFF_MAX = float(os.getenv("DB_BACKOFF_MAX", "30.0"))  # seconds (cap)


def get_conn_with_retries(
    retries: int | None = None, backoff_base: float | None = None, backoff_max: float | None = None
):
    """
    Attempt to create a DB connection using constants._conn() with retry/backoff and
    full jitter for transient failures. Returns a live pyodbc.Connection or raises
    the last exception after retries.

    This function now lazy-imports pyodbc to avoid requiring the package at module import.
    """
    attempts = 0
    last_exc: Exception | None = None

    max_retries = retries if retries is not None else _DB_RETRIES
    base = backoff_base if backoff_base is not None else _DB_BACKOFF_BASE
    cap = backoff_max if backoff_max is not None else _DB_BACKOFF_MAX

    while attempts < max_retries:
        attempts += 1
        try:
            # _conn is the canonical factory in constants
            return _conn()
        except Exception as e:
            # Detect if this is a pyodbc.OperationalError if pyodbc is available.
            is_operational = False
            try:
                import pyodbc as _pyodbc  # lazy import

                is_operational = isinstance(e, _pyodbc.OperationalError)
            except Exception:
                # pyodbc not available or import failed - we cannot do an OperationalError check
                is_operational = False

            if is_operational:
                last_exc = e
                # exponential backoff with cap, then full jitter
                exp = base * (2 ** (attempts - 1))
                wait = min(exp, cap)
                jitter = random.uniform(0, wait) if wait > 0 else 0.0
                logger.warning(
                    "[DB] connection attempt %d/%d failed (OperationalError): %s; sleeping %.2fs (cap=%.2fs, exp=%.2fs)",
                    attempts,
                    max_retries,
                    e,
                    jitter,
                    cap,
                    exp,
                )
                if attempts >= max_retries:
                    break
                time.sleep(jitter)
            else:
                # If it's not an OperationalError or pyodbc isn't available, re-raise immediately:
                logger.exception("[DB] unexpected error while connecting: %s", e)
                raise

    logger.error(
        "[DB] All %d connection attempts failed. Last exception: %s", max_retries, last_exc
    )
    if last_exc:
        raise last_exc
    raise RuntimeError("Unknown DB connection failure")


def move_if_not_exists(src: PathLike, dst: PathLike) -> bool:
    """
    Move a file from src -> dst only if:
      - src exists and is a file
      - dst does not already exist

    Returns:
      True if the file was moved, False otherwise.

    Notes:
      - Parent directories for dst will be created if missing.
      - This function prefers an atomic rename (Path.rename) and falls back to
        shutil.move when necessary (e.g., across filesystems).
      - If dst appears after a race but before the move completes, the function
        will not overwrite; it logs and returns False.
      - Exceptions are caught and logged; False is returned on error.
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        # Must be an existing regular file to move
        if not src_path.is_file():
            logger.debug("move_if_not_exists: source missing or not a file: %s", src_path)
            return False

        # Do not overwrite existing destination
        if dst_path.exists():
            logger.debug("move_if_not_exists: destination already exists, skipping: %s", dst_path)
            return False

        # Ensure destination directory exists
        dst_parent = dst_path.parent
        if not dst_parent.exists():
            try:
                dst_parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Race or permission issue; continue and let rename/move decide
                logger.exception(
                    "move_if_not_exists: failed creating parent dirs for %s", dst_parent
                )

        # Try atomic rename first (fast, atomic on same filesystem)
        try:
            src_path.rename(dst_path)
        except FileExistsError:
            # dst created concurrently, do not overwrite
            logger.warning(
                "move_if_not_exists: destination created concurrently, skipping: %s", dst_path
            )
            return False
        except OSError:
            # Could be cross-device link or other OS error; fallback to shutil.move
            try:
                shutil.move(str(src_path), str(dst_path))
            except FileExistsError:
                logger.warning(
                    "move_if_not_exists: destination created concurrently during fallback, skipping: %s",
                    dst_path,
                )
                return False
            except Exception:
                logger.exception(
                    "move_if_not_exists: shutil.move failed for %s -> %s", src_path, dst_path
                )
                return False

        # Verify move success
        if dst_path.exists() and not src_path.exists():
            logger.info("move_if_not_exists: moved %s -> %s", src_path, dst_path)
            return True

        # Unexpected state (e.g., both exist). Log and return False.
        logger.warning(
            "move_if_not_exists: unexpected post-move state for %s -> %s (src_exists=%s, dst_exists=%s)",
            src_path,
            dst_path,
            src_path.exists(),
            dst_path.exists(),
        )
        return False

    except Exception:
        logger.exception("move_if_not_exists: unexpected error moving %s -> %s", src, dst)
        return False


def cursor_row_to_dict(cursor, row: Sequence[Any]) -> dict[str, Any]:
    """
    Robust mapping from DB cursor + row -> dict.

    - Uses cursor.description to determine column names.
    - Uses zip_longest so rows shorter than the number of columns get None for missing values.
    - Rows longer than the number of columns are tolerated: extra values are ignored.
    - Ensures no None keys (filters any zipped pair where the column name is None).
    - Returns {} if cursor.description is None.

    This is a generic DB-API (PEP 249) helper and is the canonical location for this logic.
    """
    if not getattr(cursor, "description", None):
        return {}
    cols = [d[0] for d in cursor.description]
    # zip_longest pairs (col, val); if row shorter, val==None; if row longer, col==None for extra vals
    pairs = zip_longest(cols, row, fillvalue=None)
    out: dict[str, Any] = {}
    for col, val in pairs:
        # only include pairs where we have a valid column name
        if col is None:
            # extra row values beyond columns -> ignore
            continue
        out[col] = val
    return out


def fetch_all_dicts(cur) -> list[dict[str, Any]]:
    """
    Read cur.description and cur.fetchall() and return list[dict] mapping column names -> values.
    Defensive: if cur.description is None, returns [].

    Behavior:
    - Only column names from cur.description are used as keys.
    - If a row has fewer values than the number of columns, missing values are filled with None.
    - If a row has more values than the number of columns, extra values are ignored.
    """
    if not getattr(cur, "description", None):
        return []
    rows = cur.fetchall() or []
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(cursor_row_to_dict(cur, r))
    return out


def fetch_one_dict(cur) -> dict[str, Any] | None:
    """
    Convenience helper: fetch a single row from cursor and return a dict mapping
    column names -> values, or None if no row is present.

    Returns:
      - dict[str, Any] for the single fetched row
      - None if cursor.description is falsy (no columns) or fetchone() returned None

    Notes:
      - This mirrors fetch_all_dicts but for a single row.
      - Caller is responsible for cursor lifecycle (closing, connection commit/rollback).
    """
    if not getattr(cur, "description", None):
        return None
    row = cur.fetchone()
    if row is None:
        return None
    return cursor_row_to_dict(cur, row)


def resolve_path(env_or_path: str | None) -> Path:
    """
    Resolve an environment variable name or a path string into an absolute Path.
    If env_or_path is None or empty, raises ValueError.
    If the string matches an existing env var name, use its value; otherwise treat as path.
    """
    if not env_or_path:
        raise ValueError("env_or_path must be a non-empty string")
    # If env var exists and is non-empty, prefer its value
    val = os.environ.get(env_or_path)
    if val:
        p = Path(val).expanduser().resolve()
    else:
        p = Path(env_or_path).expanduser().resolve()
    return p


def _ensure_parent(path: Path) -> None:
    parent = path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path | str, obj: Any, *, ensure_parent_dir: bool = True) -> None:
    """
    Write JSON atomically to path using a .tmp file + os.replace.
    """
    p = Path(path)
    if ensure_parent_dir:
        _ensure_parent(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def read_json_safe(path: str, default: Any | None = None) -> Any:
    """
    Safely read JSON from a file.

    Behaviour:
    - If the file does not exist -> returns `default`.
    - If the file exists but cannot be parsed as JSON -> logs the exception and returns `default`.
    - On successful parse -> returns the parsed object (dict/list/etc).

    Parameters:
    - path: Path to the JSON file.
    - default: Value to return when the file is missing or unreadable (defaults to None).

    Notes:
    - Uses UTF-8 encoding.
    - Does not raise exceptions for missing file or invalid JSON; it only logs them.
    - This mirrors atomic_read/write helpers: use atomic_write_json for writes and read_json_safe for reads.

    Example:
        data = read_json_safe("/tmp/state.json", default={})
    """
    if not path:
        return default

    try:
        if not os.path.exists(path):
            return default
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.exception("[file_utils] JSON decode failed for %s. Returning default.", path)
        return default
    except Exception:
        logger.exception("[file_utils] Error reading JSON file %s. Returning default.", path)
        return default


def atomic_write_csv(
    path: Path | str, header: Iterable[str], rows: Iterable[Iterable[str]]
) -> None:
    """
    Write CSV to path atomically. header is iterable of column names.
    rows is iterable of row iterables.
    """
    p = Path(path)
    _ensure_parent(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(list(header))
        for r in rows:
            w.writerow(list(r))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def read_csv_rows_safe(path: Path | str) -> list[list[str]]:
    """
    Read CSV file into a list of rows (list of strings). If file doesn't exist, returns [].
    Does minimal cleaning: strips newline only; leaves whitespace inside fields intact.
    """
    p = Path(path)
    if not p.exists():
        return []
    out: list[list[str]] = []
    # Use csv.reader to handle quoted fields properly
    with p.open("r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            # Normalize None to empty strings and strip only leading/trailing whitespace per cell
            out.append([("" if cell is None else cell).strip() for cell in row])
    return out


@contextmanager
def acquire_lock(
    path: Path | str, timeout: float = 5.0, poll: float = DEFAULT_LOCK_RETRY_INTERVAL
) -> Iterator[Path]:
    """
    Acquire a simple cross-process lock by creating a lockfile with O_CREAT|O_EXCL.
    Yields the lockfile Path for optional inspection. Raises TimeoutError on failure.
    Use like:
      with acquire_lock("/tmp/my.lock", timeout=5):
          do_write()
    """
    lock_path = Path(str(path))
    _ensure_parent(lock_path)
    deadline = time.time() + float(timeout)
    fd = None
    while True:
        try:
            # os.O_CREAT|os.O_EXCL ensures atomic create; O_RDWR to get a fd we can close
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            # Optionally write pid/timestamp for debugging
            try:
                os.write(fd, f"{os.getpid()}\n".encode())
            except Exception:
                pass
            # Return the lock file path while fd remains open (not strictly required)
            yield lock_path
            # On normal exit, close + remove file
            break
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"Timed out acquiring lock {lock_path!s}")
            time.sleep(poll)
        finally:
            # If we acquired fd and are at finally, close the fd (we remove the file below).
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
                fd = None
    # cleanup: remove lockfile if still present
    try:
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        pass


def release_lock(path: Path | str) -> None:
    """
    Remove a lockfile if present. Safe to call even if missing.
    """
    p = Path(path)
    try:
        if p.exists():
            p.unlink()
    except Exception:
        # Best effort only
        pass


async def append_csv_line(file_path, values):
    """Appends a line to a CSV file asynchronously using proper escaping."""
    # Use csv.writer to ensure proper CSV quoting/escaping, then write buffer to file asynchronously
    buf = io.StringIO()
    writer = csv.writer(buf)
    # Convert values to strings in a consistent way (None -> empty string)
    safe_values = ["" if v is None else v for v in values]
    writer.writerow(safe_values)
    async with aiofiles.open(file_path, mode="a", encoding="utf-8", newline="") as f:
        await f.write(buf.getvalue())


async def log_embed_to_file(embed):
    """Logs an embed title and description to a text file asynchronously."""
    # Defer importing utcnow to avoid circular import at module import time
    try:
        from utils import utcnow as _utcnow
    except Exception:
        _utcnow = None

    ts = _utcnow().isoformat() if _utcnow else datetime.utcnow().isoformat()
    async with aiofiles.open("embed_audit.log", "a", encoding="utf-8") as f:
        await f.write(f"[{ts}] {embed.title} - {embed.description}\n")


async def read_summary_log_rows(summary_log_path):
    async with aiofiles.open(summary_log_path, encoding="utf-8") as f:
        contents = await f.read()
    return list(csv.DictReader(StringIO(contents)))


def pid_alive(pid: int) -> bool:
    """
    Best-effort check whether a PID appears alive.
    Delegates to process_utils.pid_alive.

    This wrapper performs a lazy import to avoid circular import issues.
    """
    try:
        # Lazy import to prevent circular imports at module import time
        from process_utils import pid_alive as _pid_alive  # type: ignore

        return _pid_alive(pid)
    except Exception:
        # Fallback: conservative heuristic using os.kill
        try:
            if not isinstance(pid, int) or pid <= 0:
                return False
            try:
                os.kill(pid, 0)
                return True
            except Exception:
                return False
        except Exception:
            return False


def get_process_info(pid: int) -> dict[str, Any | None]:
    """
    Delegates to process_utils.get_process_info, returning a dict with keys:
      - pid_exists (bool)
      - is_running (bool)
      - exe (str|None)
      - create_time (float|None)
    Uses lazy import and returns a conservative default on failure.
    """
    try:
        from process_utils import get_process_info as _get_proc_info  # type: ignore

        return _get_proc_info(pid)
    except Exception:
        return {
            "pid_exists": False,
            "is_running": False,
            "exe": None,
            "create_time": None,
        }


def matches_process(
    pid: int, *, exe_path: str | None = None, created_before: float | None = None
) -> bool:
    """
    Delegate to process_utils.matches_process to decide whether a PID corresponds
    to a matching running process (exe path + create_time heuristics).
    """
    try:
        from process_utils import matches_process as _matches  # type: ignore

        return _matches(pid, exe_path=exe_path, created_before=created_before)
    except Exception:
        # Conservative fallback: if pid not alive, return False; otherwise True
        try:
            return pid_alive(pid)
        except Exception:
            return False
