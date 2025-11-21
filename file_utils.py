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
- run_with_retries(...) -> centralized async/sync retry helper (logs telemetry)
- get_lockfile_info(path) -> dict with parsed pid/process info (best-effort)
- pid_alive(pid), get_process_info(pid), matches_process(...)
"""
from __future__ import annotations  # PEP 563 style

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
telemetry_logger = logging.getLogger("telemetry")

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
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.is_file():
            logger.debug("move_if_not_exists: source missing or not a file: %s", src_path)
            return False

        if dst_path.exists():
            logger.debug("move_if_not_exists: destination already exists, skipping: %s", dst_path)
            return False

        dst_parent = dst_path.parent
        if not dst_parent.exists():
            try:
                dst_parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                logger.exception(
                    "move_if_not_exists: failed creating parent dirs for %s", dst_parent
                )

        try:
            src_path.rename(dst_path)
        except FileExistsError:
            logger.warning(
                "move_if_not_exists: destination created concurrently, skipping: %s", dst_path
            )
            return False
        except OSError:
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

        if dst_path.exists() and not src_path.exists():
            logger.info("move_if_not_exists: moved %s -> %s", src_path, dst_path)
            return True

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
    pairs = zip_longest(cols, row, fillvalue=None)
    out: dict[str, Any] = {}
    for col, val in pairs:
        if col is None:
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


def atomic_write_json(
    path: Path | str, obj: Any, *, ensure_parent_dir: bool = True, default=None
) -> None:
    """
    Atomic JSON write. Accepts optional 'default' callable to pass into json.dump
    for serializing non-built-in types (e.g., datetimes).
    """
    p = Path(path)
    if ensure_parent_dir:
        _ensure_parent(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        # pass-through default serializer if provided
        json.dump(obj, f, ensure_ascii=False, indent=2, default=default)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def read_json_safe(path: str, default: Any | None = None) -> Any:
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
    p = Path(path)
    if not p.exists():
        return []
    out: list[list[str]] = []
    with p.open("r", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            out.append([("" if cell is None else cell).strip() for cell in row])
    return out


@contextmanager
def acquire_lock(
    path: Path | str, timeout: float = 5.0, poll: float = DEFAULT_LOCK_RETRY_INTERVAL
) -> Iterator[Path]:
    lock_path = Path(str(path))
    _ensure_parent(lock_path)
    deadline = time.time() + float(timeout)
    fd = None
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                os.write(fd, f"{os.getpid()}\n".encode())
            except Exception:
                pass
            yield lock_path
            break
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"Timed out acquiring lock {lock_path!s}")
            time.sleep(poll)
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
                fd = None
    try:
        if lock_path.exists():
            lock_path.unlink()
    except Exception:
        pass


def release_lock(path: Path | str) -> None:
    p = Path(path)
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass


async def append_csv_line(file_path, values):
    buf = io.StringIO()
    writer = csv.writer(buf)
    safe_values = ["" if v is None else v for v in values]
    writer.writerow(safe_values)
    async with aiofiles.open(file_path, mode="a", encoding="utf-8", newline="") as f:
        await f.write(buf.getvalue())


async def log_embed_to_file(embed):
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
    try:
        from process_utils import pid_alive as _pid_alive  # type: ignore

        return _pid_alive(pid)
    except Exception:
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


def get_process_info(pid: int) -> dict[str, Any] | None:
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
    try:
        from process_utils import matches_process as _matches  # type: ignore

        return _matches(pid, exe_path=exe_path, created_before=created_before)
    except Exception:
        try:
            return pid_alive(pid)
        except Exception:
            return False


# --------------------------- New: generic async retry wrapper ---------------------------
# Purpose:
# - Provide a small, reusable async utility to run a blocking or async callable
#   with retry semantics on specific exception types (e.g., TimeoutError from acquire_lock).
# - Keeps retry/backoff logic centralized for consistent behavior across modules.
import asyncio as _asyncio_module


async def run_with_retries(
    func,
    *args,
    retries: int = 3,
    base_backoff: float = 0.05,
    max_backoff: float = 0.5,
    retry_exceptions: tuple[type[BaseException], ...] = (TimeoutError,),
    **kwargs,
):
    """
    Run `func` with retries on specified exception types.

    - func: synchronous callable or coroutine function.
            If synchronous, it will be executed in a thread via asyncio.to_thread.
            If coroutine function, it will be awaited directly.
    - retries: number of attempts (>=1). Default 3.
    - base_backoff: base backoff (seconds) for exponential backoff multiplier.
    - max_backoff: cap for backoff (seconds).
    - retry_exceptions: tuple of exception classes that should be retried.

    Emits telemetry entries to logger 'telemetry' on each retry attempt.
    """
    if retries < 1:
        retries = 1

    last_exc: BaseException | None = None
    func_name = getattr(func, "__name__", str(func))
    for attempt in range(1, retries + 1):
        try:
            if _asyncio_module.iscoroutinefunction(func):
                res = await func(*args, **kwargs)
            else:
                res = await _asyncio_module.to_thread(func, *args, **kwargs)
            # Successful run - emit a telemetry event for success on first try?
            if attempt == 1:
                telemetry_logger.debug(
                    json.dumps(
                        {"event": "run_with_retries_success", "func": func_name, "attempt": attempt}
                    )
                )
            return res
        except retry_exceptions as exc:
            last_exc = exc
            # Emit telemetry about retryable exception
            try:
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "retry_attempt",
                            "func": func_name,
                            "attempt": attempt,
                            "retries": retries,
                            "exception": type(exc).__name__,
                            "msg": str(exc),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )
            except Exception:
                telemetry_logger.info(
                    f"[RETRY] func={func_name} attempt={attempt} exception={type(exc).__name__}"
                )

            if attempt >= retries:
                logger.debug(
                    "[RETRY] Exhausted retries (%d) for function %s; raising.", retries, func_name
                )
                raise
            exp = base_backoff * (2 ** (attempt - 1))
            wait = min(exp, max_backoff)
            jitter = random.uniform(0, wait)
            logger.debug(
                "[RETRY] Caught retryable exception %s on attempt %d/%d for func=%s; sleeping %.3fs and retrying",
                type(exc).__name__,
                attempt,
                retries,
                func_name,
                jitter,
            )
            await _asyncio_module.sleep(jitter)
        except Exception:
            # Non-retryable exception: propagate immediately
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("run_with_retries failed without capturing an exception")


# --------------------------- New: lockfile introspection helper ---------------------------
def get_lockfile_info(path: PathLike) -> dict[str, Any]:
    """
    Read a lockfile created by acquire_lock and return best-effort metadata:
      - pid: integer PID if parsable from first token in the file
      - content: full lockfile text
      - pid_alive: bool if pid resolved and appears alive
      - process: output of get_process_info(pid) if available
    Returns {} when file is missing/unreadable.
    """
    p = Path(str(path))
    if not p.exists():
        return {}
    try:
        text = p.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception:
        return {}
    out: dict[str, Any] = {"content": text}
    first_line = text.splitlines()[0] if text else ""
    pid = None
    try:
        pid_token = first_line.strip().split()[0] if first_line else ""
        pid = int(pid_token)
    except Exception:
        pid = None
    out["pid"] = pid
    if pid:
        try:
            out["pid_alive"] = pid_alive(pid)
        except Exception:
            out["pid_alive"] = False
        try:
            proc = get_process_info(pid)
            out["process"] = proc
        except Exception:
            out["process"] = None
    return out
