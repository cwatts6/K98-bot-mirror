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
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
import csv
from datetime import datetime
import io
from io import StringIO
import json
import logging
import os
from pathlib import Path
import random
import time
from typing import Any

import aiofiles
import pyodbc

# Use the repo canonical connector
from constants import _conn

logger = logging.getLogger(__name__)

DEFAULT_LOCK_RETRY_INTERVAL = 0.1

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

    - retries: number of attempts (default from DB_CONN_RETRIES env)
    - backoff_base: exponential base (seconds) (default DB_BACKOFF_BASE)
    - backoff_max: cap on exponential backoff (default DB_BACKOFF_MAX)
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
        except pyodbc.OperationalError as e:
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
        except Exception as e:
            # Non-operational unexpected error: log and re-raise immediately
            logger.exception("[DB] unexpected error while connecting: %s", e)
            raise

    logger.error(
        "[DB] All %d connection attempts failed. Last exception: %s", max_retries, last_exc
    )
    if last_exc:
        raise last_exc
    raise pyodbc.OperationalError("Unknown DB connection failure")


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
