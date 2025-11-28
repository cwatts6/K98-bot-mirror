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
- get_conn_with_retries() -> resilient DB connection factory
- run_post_import_stats_update(...) -> centralized DB maintenance helper (moved from processing_pipeline)
- run_blocking_in_thread(...) -> new helper to run blocking work in a thread with telemetry
- run_maintenance_subprocess(...) -> spawn maintenance_worker.py in a subprocess (async)
- run_maintenance_with_isolation(...) -> wrapper that hides process vs thread branching
- add a small telemetry helper here to centralize safe emission and trimming of large fields such as tracebacks or long outputs.
"""
from __future__ import annotations  # PEP 563 style

import asyncio
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
import csv
from datetime import datetime
import inspect
import io
from io import StringIO
from itertools import zip_longest
import json
import logging
import os
from pathlib import Path
import random
import shutil
import sys
import time
import traceback
from typing import Any

import aiofiles

# Use the repo canonical connector
from constants import _conn
from utils import utcnow  # ensure we have utcnow for telemetry timestamps

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

DEFAULT_LOCK_RETRY_INTERVAL = 0.1

# Use PEP 604 | syntax for unions (pre-commit UP007)
PathLike = str | Path

# Env-configurable retry params (reasonable defaults)
_DB_RETRIES = int(os.getenv("DB_CONN_RETRIES", "5"))
_DB_BACKOFF_BASE = float(os.getenv("DB_BACKOFF_BASE", "1.0"))  # seconds
_DB_BACKOFF_MAX = float(os.getenv("DB_BACKOFF_MAX", "30.0"))  # seconds (cap)


# ---------------------------
# New telemetry helper
# ---------------------------
def emit_telemetry_event(payload: dict[str, Any], *, max_snippet: int = 2000) -> None:
    """
    Safely emit a telemetry JSON line via the 'telemetry' logger.

    - Trims excessively long string fields that tend to blow up telemetry sinks,
      such as 'traceback', 'detail', 'output', 'out', 'error'.
    - Ensures the call never raises (best-effort).
    """
    try:
        if not isinstance(payload, dict):
            try:
                payload = {"event": str(payload)}
            except Exception:
                payload = {"event": "unknown"}

        def _trim_val(v):
            try:
                if isinstance(v, str) and len(v) > max_snippet:
                    return v[:max_snippet] + "...(truncated)"
                return v
            except Exception:
                return v

        safe_payload = {}
        for k, v in payload.items():
            if (
                k
                and isinstance(k, str)
                and k.lower()
                in (
                    "traceback",
                    "detail",
                    "error",
                    "output",
                    "out",
                    "log",
                )
            ):
                safe_payload[k] = _trim_val(v)
            else:
                # try to convert common non-serializable types safely
                try:
                    safe_payload[k] = v
                except Exception:
                    try:
                        safe_payload[k] = str(v)
                    except Exception:
                        safe_payload[k] = "<unserializable>"

        telemetry_logger.info(json.dumps(safe_payload, default=str))
    except Exception:
        try:
            # Best-effort fallback: log via module logger (non-telemetry)
            logger.exception("emit_telemetry_event failed for payload=%r", payload)
        except Exception:
            pass


def get_conn_with_retries(
    retries: int | None = None,
    backoff_base: float | None = None,
    backoff_max: float | None = None,
    meta: dict | None = None,
):
    """
    Attempt to create a DB connection using constants._conn() with retry/backoff and
    full jitter for transient failures. Returns a live pyodbc.Connection or raises
    the last exception after retries.

    Optional `meta` is attached to telemetry (best-effort).
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

            # Expose full repr in debug logs for rich diagnostics
            logger.debug("[DB] connection attempt %d failed: %s", attempts, repr(e), exc_info=True)

            if is_operational:
                last_exc = e
                # exponential backoff with cap, then full jitter
                exp = base * (2 ** (attempts - 1))
                wait = min(exp, cap)
                jitter = random.uniform(0, wait) if wait > 0 else 0.0
                # Emit informative logs and telemetry with pyodbc specifics where available
                try:
                    telemetry_logger.info(
                        json.dumps(
                            {
                                "event": "db_conn_retry",
                                "attempt": attempts,
                                "retries": max_retries,
                                "error_type": type(e).__name__,
                                "error_args": getattr(e, "args", None),
                                "meta": meta,
                                "timestamp": utcnow().isoformat(),
                            }
                        )
                    )
                except Exception:
                    logger.debug("[DB] telemetry emit failed for connection retry", exc_info=True)

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
        "[DB] All %d connection attempts failed. Last exception: %s", max_retries, repr(last_exc)
    )
    # Emit telemetry for final failure
    try:
        telemetry_logger.error(
            json.dumps(
                {
                    "event": "db_conn_failed",
                    "retries": max_retries,
                    "last_error_type": type(last_exc).__name__ if last_exc else None,
                    "last_error_args": getattr(last_exc, "args", None) if last_exc else None,
                    "meta": meta,
                    "timestamp": utcnow().isoformat(),
                }
            )
        )
    except Exception:
        logger.debug("[DB] telemetry emit failed for final connection failure", exc_info=True)

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


# ---------------------------
# New: centralized post-import stats maintenance
# ---------------------------
def run_post_import_stats_update(
    server: str, database: str, username: str, password: str, timeout_seconds: int = 300
) -> None:
    """
    Run the post-import stored procedure to refresh DB statistics.

    This is synchronous and intended to be called off the event loop (e.g. via
    asyncio.to_thread or run_step(..., offload_sync_to_thread=True)).

    It uses get_conn_with_retries() so transient connection failures get retried
    with exponential backoff and jitter.

    Emits a telemetry JSON line on success or failure.
    """
    try:
        conn = get_conn_with_retries(meta={"operation": "post_import_stats"})
    except Exception as e:
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "post_import_stats",
                    "status": "conn_failed",
                    "error_type": type(e).__name__,
                    "error_args": getattr(e, "args", None),
                }
            )
        )
        logger.warning("[MAINT] Could not obtain DB connection for sp_updatestats: %s", e)
        # Re-raise so callers can decide how to handle (processing_pipeline treats this as best-effort)
        raise

    try:
        # Ensure autocommit so the stored proc can run unhindered
        try:
            conn.autocommit = True  # type: ignore[attr-defined]
        except Exception:
            pass
        cur = conn.cursor()
        try:
            # Some DB drivers expose a timeout property on the cursor
            try:
                cur.timeout = timeout_seconds
            except Exception:
                pass
            cur.execute("EXEC [dbo].[usp_update_stats]")
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "post_import_stats",
                        "status": "success",
                        "database": database,
                    }
                )
            )
            logger.info("[MAINT] sp_updatestats completed.")
        except Exception as e:
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "post_import_stats",
                        "status": "failure",
                        "database": database,
                        "error_type": type(e).__name__,
                        "error_args": getattr(e, "args", None),
                    }
                )
            )
            logger.warning("[MAINT] sp_updatestats failed (continuing): %s", e)
            # Re-raise so callers can log/handle; processing_pipeline will catch and continue.
            raise
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


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


# --------------------------- New helper: run blocking work in thread + telemetry ---------------------------
async def run_blocking_in_thread(
    func: Callable[..., Any],
    *args,
    name: str | None = None,
    meta: dict | None = None,
    timeout: float | None = None,
    **kwargs,
) -> Any:
    """
    Run a blocking function in a background thread (async-friendly) and emit
    structured telemetry events on start / completion / cancellation / timeout / failure.

    Parameters:
      - func: blocking callable (or coroutine function)
      - name: optional short event name used in telemetry (defaults to func.__name__)
      - meta: optional dict attached to telemetry for context (e.g., {"filename": "xxx"})
      - timeout: optional float seconds to bound the wait; if exceeded raises asyncio.TimeoutError
      - args/kwargs forwarded to func

    Telemetry events emitted (logger "telemetry"):
      - {"event":"run_block.start", "name": <name>, "meta": {...}, "timestamp": ...}
      - {"event":"run_block.complete", "name": <name>, "meta": {...}, "duration_s": ... , "timestamp": ...}
      - {"event":"run_block.cancelled", "name": <name>, "meta": {...}, "duration_s": ... , "timestamp": ...}
      - {"event":"run_block.failed", "name": <name>, "meta": {...}, "error_type": ..., "error": ..., "traceback": ..., "duration_s": ..., "timestamp": ...}
      - Timeout is represented as event "run_block.failed" with error_type "TimeoutError"
    """
    _evt_name = name or getattr(func, "__name__", "run_blocking")
    meta = meta or {}
    try:
        start_iso = utcnow().isoformat()
    except Exception:
        start_iso = datetime.utcnow().isoformat()
    start_t = time.monotonic()

    # Emit start
    try:
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "run_block.start",
                    "name": _evt_name,
                    "meta": meta,
                    "timestamp": start_iso,
                }
            ),
            extra={},
        )
    except Exception:
        logger.debug("emit start telemetry failed for %s", _evt_name, exc_info=True)

    def _worker():
        return func(*args, **kwargs)

    try:
        if inspect.iscoroutinefunction(func):
            # coroutine function: await it directly, optionally with timeout
            if timeout is not None:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                result = await func(*args, **kwargs)
        else:
            # sync function: offload to thread, optionally wrapped with wait_for for timeout
            if timeout is not None:
                result = await asyncio.wait_for(asyncio.to_thread(_worker), timeout=timeout)
            else:
                result = await asyncio.to_thread(_worker)

        duration = round(time.monotonic() - start_t, 6)
        try:
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "run_block.complete",
                        "name": _evt_name,
                        "meta": meta,
                        "duration_s": duration,
                        "timestamp": utcnow().isoformat(),
                    }
                )
            )
        except Exception:
            logger.debug("emit complete telemetry failed for %s", _evt_name, exc_info=True)
        return result

    except asyncio.CancelledError:
        # Propagate cancellation but emit a lightweight cancelled telemetry entry
        duration = round(time.monotonic() - start_t, 6)
        try:
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "run_block.cancelled",
                        "name": _evt_name,
                        "meta": meta,
                        "duration_s": duration,
                        "timestamp": utcnow().isoformat(),
                    }
                )
            )
        except Exception:
            logger.debug("emit cancelled telemetry failed for %s", _evt_name, exc_info=True)
        raise

    except TimeoutError:
        duration = round(time.monotonic() - start_t, 6)
        payload = {
            "event": "run_block.failed",
            "name": _evt_name,
            "meta": meta,
            "error_type": "TimeoutError",
            "error": f"wait_for exceeded {timeout}s",
            "duration_s": duration,
            "timestamp": utcnow().isoformat(),
        }
        try:
            telemetry_logger.error(json.dumps(payload))
        except Exception:
            logger.exception("emit timeout telemetry failed for %s", _evt_name)
        raise

    except Exception as exc:
        duration = round(time.monotonic() - start_t, 6)
        tb = traceback.format_exc()
        payload = {
            "event": "run_block.failed",
            "name": _evt_name,
            "meta": meta,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": tb,
            "duration_s": duration,
            "timestamp": utcnow().isoformat(),
        }
        try:
            telemetry_logger.error(json.dumps(payload))
        except Exception:
            logger.exception("emit failure telemetry failed for %s", _evt_name)
        raise


# --------------------------- New helper: build maintenance command ---------------------------
def build_maintenance_cmd(
    command: str, args: list[str] | None = None, kwargs: dict[str, Any] | None = None
) -> list[str]:
    """
    Build the command list for invoking maintenance_worker.py.

    - command: 'post_stats' | 'proc_import' | 'test_sleep' etc.
    - args: list of extra positional args (kept in order)
    - kwargs: mapping of keyword arguments -> values; converted to flags:
        * key -> --key-name
        * True -> include flag without value
        * False or None -> omitted
        * other -> --key value

    Returns the full command list starting with sys.executable and the worker path.
    """
    worker_path = Path(__file__).resolve().parent / "maintenance_worker.py"
    cmd = [sys.executable, str(worker_path), command]
    if args:
        cmd += [str(a) for a in args]
    if kwargs:
        # preserve insertion order of dict; convert keys to flag form
        for k, v in kwargs.items():
            if k is None:
                continue
            key = str(k).lstrip("-")
            flag = f"--{key.replace('_', '-')}"
            if v is True:
                cmd.append(flag)
            elif v is False or v is None:
                continue
            else:
                cmd.append(flag)
                cmd.append(str(v))
    return cmd


# --------------------------- New helper: run maintenance in a subprocess ---------------------------
async def run_maintenance_subprocess(
    command: str,
    args: list[str] | None = None,
    *,
    kwargs: dict[str, Any] | None = None,
    timeout: float | None = 300,
    name: str | None = None,
    meta: dict | None = None,
    build_only: bool = False,
) -> tuple[bool, str] | list[str]:
    """
    Spawn a short-lived maintenance worker process (maintenance_worker.py) to run `command`.
    Returns (success: bool, output: str) where output is combined stdout+stderr.

    New:
      - Accepts kwargs mapping which will be flattened to flag-style args (--key val).
      - If build_only=True returns the built cmd list (useful for unit tests).

    Behavior:
      - Uses sys.executable to run the maintenance_worker.py script located next to this file.
      - Captures stdout/stderr. If the worker exits with code 0 => success True.
      - If timeout occurs, kills the process and returns success=False with captured output and a timeout marker.
      - Emits telemetry events for start/complete/failed/timeout.
      - On success, emits trimmed stdout/stderr snippet in telemetry to aid debugging.
    """
    meta = meta or {}
    _evt_name = name or f"maintenance:{command}"
    try:
        worker_path = Path(__file__).resolve().parent / "maintenance_worker.py"
        if not worker_path.exists():
            msg = f"maintenance_worker not found at {worker_path}"
            telemetry_logger.error(
                json.dumps(
                    {
                        "event": "maintenance_subproc",
                        "status": "failed",
                        "reason": "missing_worker",
                        "command": command,
                        "meta": meta,
                    }
                )
            )
            return False, msg

        # Build command (supports both args list and kwargs mapping)
        cmd = build_maintenance_cmd(command, args=args, kwargs=kwargs)
        telemetry_logger.info(
            json.dumps(
                {"event": "maintenance_subproc.start", "command": command, "cmd": cmd, "meta": meta}
            )
        )

        if build_only:
            return cmd

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except TimeoutError:
            # attempt to kill the process; be aggressive to avoid leaks
            try:
                proc.kill()
            except Exception:
                pass
            try:
                await proc.wait()
            except Exception:
                pass
            out_b = b""
            err_b = b""
            try:
                if proc.stdout:
                    out_b = await proc.stdout.read()
                if proc.stderr:
                    err_b = await proc.stderr.read()
            except Exception:
                pass
            out = (
                (out_b or b"").decode("utf-8", errors="replace")
                + "\n"
                + (err_b or b"").decode("utf-8", errors="replace")
            )
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "maintenance_subproc",
                        "status": "timeout",
                        "command": command,
                        "meta": meta,
                    }
                )
            )
            return False, f"Timed out after {timeout}s. Output:\n{out}"

        # process finished within timeout
        out_b = b""
        err_b = b""
        try:
            if proc.stdout:
                out_b = await proc.stdout.read()
            if proc.stderr:
                err_b = await proc.stderr.read()
        except Exception:
            pass
        out = (out_b or b"").decode("utf-8", errors="replace")
        err = (err_b or b"").decode("utf-8", errors="replace")
        combined = out + "\n" + err
        rc = proc.returncode if proc.returncode is not None else -1
        # trim for telemetry
        MAX_SNIPPET = int(os.getenv("MAINT_SUBPROC_TELEMETRY_SNIPPET", "4000"))
        snippet = combined[:MAX_SNIPPET]
        if rc == 0:
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "maintenance_subproc",
                        "status": "success",
                        "command": command,
                        "meta": meta,
                        "output_snippet": snippet,
                    }
                )
            )
            return True, combined
        else:
            telemetry_logger.info(
                json.dumps(
                    {
                        "event": "maintenance_subproc",
                        "status": "failed",
                        "command": command,
                        "returncode": rc,
                        "meta": meta,
                        "output_snippet": snippet,
                    }
                )
            )
            return False, f"Return code {rc}. Output:\n{combined}"

    except asyncio.CancelledError:
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "maintenance_subproc",
                    "status": "cancelled",
                    "command": command,
                    "meta": meta,
                }
            )
        )
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        telemetry_logger.error(
            json.dumps(
                {
                    "event": "maintenance_subproc",
                    "status": "error",
                    "command": command,
                    "error": str(exc),
                    "traceback": tb,
                    "meta": meta,
                }
            )
        )
        return False, f"Error spawning subprocess: {exc}"


# --------------------------- New wrapper: run maintenance with isolation ---------------------------
async def run_maintenance_with_isolation(
    command: str,
    args: list[str] | None = None,
    *,
    kwargs: dict[str, Any] | None = None,
    timeout: float | None = 300,
    name: str | None = None,
    meta: dict | None = None,
    prefer_process: bool | None = None,
) -> tuple[bool, str]:
    """
    Unified wrapper to run maintenance tasks either in a subprocess (isolated) or
    in-thread (legacy). Returns (ok: bool, output: str). Emits unified telemetry.

    - command: 'post_stats' | 'proc_import' | other recognized tasks
    - args/kwargs: forwarded to subprocess invocation (when using process) or to the target function (when using thread)
    - timeout: seconds to bound the operation
    - name: telemetry-friendly name
    - meta: optional telemetry context (e.g., {"filename": "..."})
    - prefer_process: if True forces subprocess mode; if False forces threaded mode; if None, uses env var MAINT_WORKER_MODE or defaults to threaded.
    """
    meta = meta or {}
    _evt = name or f"maintenance:{command}"

    # Resolve preference
    if prefer_process is None:
        prefer_process = os.getenv("MAINT_WORKER_MODE", "thread").lower() == "process"

    telemetry_logger.info(
        json.dumps(
            {
                "event": "maintenance_run.start",
                "command": command,
                "prefer_process": prefer_process,
                "meta": meta,
                "timestamp": utcnow().isoformat(),
            }
        )
    )

    # Prefer subprocess mode when requested
    if prefer_process:
        ok, out = await run_maintenance_subprocess(
            command, args=args, kwargs=kwargs, timeout=timeout, name=name, meta=meta
        )
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "maintenance_run.complete",
                    "command": command,
                    "mode": "process",
                    "ok": bool(ok),
                    "meta": meta,
                }
            )
        )
        return ok, out

    # Threaded path: map command -> callable and call via run_blocking_in_thread
    try:
        if command == "post_stats":
            # Expect kwargs to contain server/database/username/password OR rely on env
            server = (kwargs or {}).get("server")
            database = (kwargs or {}).get("database")
            username = (kwargs or {}).get("username")
            password = (kwargs or {}).get("password")
            try:
                # This function raises on failure; run in thread with telemetry + timeout
                await run_blocking_in_thread(
                    run_post_import_stats_update,
                    server,
                    database,
                    username,
                    password,
                    name=name or "run_post_import_stats_update",
                    meta=meta,
                    timeout=timeout,
                )
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "maintenance_run.complete",
                            "command": command,
                            "mode": "thread",
                            "ok": True,
                            "meta": meta,
                        }
                    )
                )
                return True, "post_stats completed"
            except Exception as exc:
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "maintenance_run.complete",
                            "command": command,
                            "mode": "thread",
                            "ok": False,
                            "meta": meta,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
                )
                return False, f"post_stats failed: {exc}"

        elif command == "proc_import":
            # Import lazily to keep dependencies light
            try:
                from proc_config_import import run_proc_config_import  # type: ignore
            except Exception as e:
                telemetry_logger.error(
                    json.dumps(
                        {
                            "event": "maintenance_run",
                            "command": command,
                            "mode": "thread",
                            "ok": False,
                            "meta": meta,
                            "error": f"import_error: {e}",
                        }
                    )
                )
                return False, f"import_error: {e}"

            try:
                res = await run_blocking_in_thread(
                    run_proc_config_import,
                    name=name or "run_proc_config_import",
                    meta=meta,
                    timeout=timeout,
                )
                # Normalize result to bool
                ok = bool(res)
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "maintenance_run.complete",
                            "command": command,
                            "mode": "thread",
                            "ok": ok,
                            "meta": meta,
                        }
                    )
                )
                return ok, "proc_import thread completed" if ok else "proc_import returned failure"
            except Exception as exc:
                telemetry_logger.info(
                    json.dumps(
                        {
                            "event": "maintenance_run.complete",
                            "command": command,
                            "mode": "thread",
                            "ok": False,
                            "meta": meta,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
                )
                return False, f"proc_import failed: {exc}"
        else:
            # Unknown command: attempt subprocess as fallback
            telemetry_logger.info(
                json.dumps(
                    {"event": "maintenance_run.unknown_command", "command": command, "meta": meta}
                )
            )
            ok, out = await run_maintenance_subprocess(
                command, args=args, kwargs=kwargs, timeout=timeout, name=name, meta=meta
            )
            return ok, out
    except asyncio.CancelledError:
        telemetry_logger.info(
            json.dumps(
                {
                    "event": "maintenance_run.cancelled",
                    "command": command,
                    "meta": meta,
                }
            )
        )
        raise
    except Exception as exc:
        telemetry_logger.error(
            json.dumps(
                {
                    "event": "maintenance_run.error",
                    "command": command,
                    "meta": meta,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc()[:2000],
                }
            )
        )
        return False, f"Exception: {exc}"


# Export helper in module-level __all__
__all__ = [
    # existing exports...
    "emit_telemetry_event",
]
