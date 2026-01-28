# file_utils.py (patched - root-fix for arg serialization)
"""
Shared file utilities for atomic IO and simple cross-process locking.

This copy includes a robust root-fix to avoid accidental character-splitting of
path/string arguments when callers pass a single path as a positional argument
to run_maintenance_with_isolation (or similar helpers).

Key changes (root-fix):
- Added normalize_args_for_maintenance(args) which consistently normalizes the
  "args" parameter into a list. This handles the common mistake where a caller
  passes a single string/path as the second positional argument (which previously
  got treated as an iterable and expanded into characters).
- run_maintenance_with_isolation now uses normalize_args_for_maintenance to
  ensure subprocess argv tokens are built from a proper list (prevents char-split).
- Minor doc clarifications and usage of the normalised args variable internally.

All other behavior (offload file tokenization, OFFLOAD_FILE_PREFIX/JSON, temp file
management, telemetry, etc.) is unchanged.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
import csv
from datetime import datetime
import importlib
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
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Any
import uuid

import aiofiles

# Use the repo canonical connector
from constants import DATA_DIR, _conn
from utils import utcnow  # ensure we have utcnow for telemetry timestamps

# Optional enhanced process handling
try:
    import psutil  # optional dependency for robust process termination
except Exception:
    psutil = None

# Re-export pid/process helpers from canonical module
try:
    from process_utils import get_process_info, matches_process, pid_alive  # type: ignore
except Exception:
    # Fallback shims to avoid ImportError in weird test envs; these defer to simple heuristics.
    def pid_alive(pid: int) -> bool:
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
            return pid_alive(pid)
        except Exception:
            return False


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


# ---------------------------
# Sanitize subprocess cmd tokens for telemetry
# ---------------------------
def _sanitize_token_for_telemetry(tok: Any, *, max_str: int = 200) -> str:
    """
    Convert a single argv token into a short, safe string for telemetry/logging.
    - Offload tokens -> show prefix + basename only (no absolute path)
    - Long strings -> truncated
    - Non-strings -> short repr()
    """
    try:
        if not isinstance(tok, str):
            r = repr(tok)
            return r if len(r) <= max_str else r[:max_str] + "...(truncated)"

        # OFFLOAD token prefixes are defined later in this module (globals) but are safe to reference here.
        if tok.startswith(
            globals().get("OFFLOAD_FILE_PREFIX", "__OFFLOAD_FILE__:")
        ) or tok.startswith(globals().get("OFFLOAD_JSON_PREFIX", "__OFFLOAD_JSON__:")):
            try:
                # Split only on first colon to preserve the token prefix
                prefix, payload = tok.split(":", 1)
                bn = os.path.basename(payload)
                return f"{prefix}:{bn}"
            except Exception:
                return tok.split(":", 1)[0] + ":<path>"

        if len(tok) > max_str:
            return tok[:max_str] + "...(truncated)"
        return tok
    except Exception:
        return "<unserializable>"


def sanitize_cmd_for_telemetry(cmd: Iterable[Any] | None, *, max_tokens: int = 12) -> list[str]:
    """
    Return a sanitized list suitable for telemetry/logging:
    - per-token sanitization (basenames for offloaded files)
    - crop long token lists to first max_tokens and append a summary token
    """
    toks = list(cmd) if cmd is not None else []
    sanitized = [_sanitize_token_for_telemetry(t) for t in toks[:max_tokens]]
    if len(toks) > max_tokens:
        sanitized.append(f"...(+{len(toks) - max_tokens} more tokens)")
    return sanitized


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
                # Emit informative telemetry with pyodbc specifics where available
                try:
                    emit_telemetry_event(
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
        emit_telemetry_event(
            {
                "event": "db_conn_failed",
                "retries": max_retries,
                "last_error_type": type(last_exc).__name__ if last_exc else None,
                "last_error_args": getattr(last_exc, "args", None) if last_exc else None,
                "meta": meta,
                "timestamp": utcnow().isoformat(),
            }
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
    if not getattr(cur, "description", None):
        return []
    rows = cur.fetchall() or []
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(cursor_row_to_dict(cur, r))
    return out


def fetch_one_dict(cur) -> dict[str, Any] | None:
    if not getattr(cur, "description", None):
        return None
    row = cur.fetchone()
    if row is None:
        return None
    return cursor_row_to_dict(cur, row)


def resolve_path(env_or_path: str | None) -> Path:
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
    p = Path(path)
    if ensure_parent_dir:
        _ensure_parent(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
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
    try:
        conn = get_conn_with_retries(meta={"operation": "post_import_stats"})
    except Exception as e:
        emit_telemetry_event(
            {
                "event": "post_import_stats",
                "status": "conn_failed",
                "error_type": type(e).__name__,
                "error_args": getattr(e, "args", None),
            }
        )
        logger.warning("[MAINT] Could not obtain DB connection for sp_updatestats: %s", e)
        raise

    try:
        try:
            conn.autocommit = True  # type: ignore[attr-defined]
        except Exception:
            pass
        cur = conn.cursor()
        try:
            try:
                cur.timeout = timeout_seconds
            except Exception:
                pass
            cur.execute("EXEC [dbo].[usp_update_stats]")
            emit_telemetry_event(
                {"event": "post_import_stats", "status": "success", "database": database}
            )
            logger.info("[MAINT] sp_updatestats completed.")
        except Exception as e:
            emit_telemetry_event(
                {
                    "event": "post_import_stats",
                    "status": "failure",
                    "database": database,
                    "error_type": type(e).__name__,
                    "error_args": getattr(e, "args", None),
                }
            )
            logger.warning("[MAINT] sp_updatestats failed (continuing): %s", e)
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
            if attempt == 1:
                telemetry_logger.debug(
                    json.dumps(
                        {"event": "run_with_retries_success", "func": func_name, "attempt": attempt}
                    )
                )
            return res
        except retry_exceptions as exc:
            last_exc = exc
            try:
                emit_telemetry_event(
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
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("run_with_retries failed without capturing an exception")


# ---------------------------
# New: lockfile introspection helper
# ---------------------------
def get_lockfile_info(path: PathLike) -> dict[str, Any]:
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


# ---------------------------
# Offload registry (persistent)
# ---------------------------
_OFFLOAD_REGISTRY_PATH = os.path.join(DATA_DIR, "offload_registry.json")
_offload_registry: dict[str, dict[str, Any]] = {}
_offload_registry_lock = threading.Lock()


def _load_persistent_registry():
    global _offload_registry
    try:
        if os.path.exists(_OFFLOAD_REGISTRY_PATH):
            with open(_OFFLOAD_REGISTRY_PATH, encoding="utf-8") as f:
                data = json.load(f) or {}
            if isinstance(data, dict):
                _offload_registry = data
            else:
                _offload_registry = {}
        else:
            _offload_registry = {}
    except Exception:
        logger.exception("Failed to load offload registry; starting empty")
        _offload_registry = {}


def _persist_offload_registry():
    try:
        tmp = f"{_OFFLOAD_REGISTRY_PATH}.tmp"
        os.makedirs(os.path.dirname(_OFFLOAD_REGISTRY_PATH), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_offload_registry, f, default=str, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, _OFFLOAD_REGISTRY_PATH)
    except Exception:
        logger.exception("Failed to persist offload registry")


# Initialize registry on import
_load_persistent_registry()


def start_offload(meta: dict | None = None) -> str:
    offload_id = uuid.uuid4().hex
    entry = {
        "offload_id": offload_id,
        "meta": meta or {},
        "start_time": (utcnow().isoformat() if utcnow else datetime.utcnow().isoformat()),
        "pid": None,
        "cmd": None,
        "status": "started",
        "end_time": None,
        "ok": None,
        "output_snippet": None,
        "worker_parsed": None,
        "cancel_requested": None,
        "cancel_actor": None,
        "cancel_time": None,
    }
    with _offload_registry_lock:
        _offload_registry[offload_id] = entry
        _persist_offload_registry()
    return offload_id


def record_process_offload(offload_id: str, pid: int | None, cmd: list[str] | None) -> None:
    with _offload_registry_lock:
        ent = _offload_registry.get(offload_id)
        if not ent:
            return
        ent["pid"] = int(pid) if pid is not None else None
        ent["cmd"] = cmd
        _persist_offload_registry()


def mark_offload_complete(
    offload_id: str, ok: bool, output_snippet: str | None = None, worker_parsed: dict | None = None
) -> None:
    with _offload_registry_lock:
        ent = _offload_registry.get(offload_id)
        if not ent:
            return
        ent["status"] = "completed"
        ent["end_time"] = utcnow().isoformat() if utcnow else datetime.utcnow().isoformat()
        ent["ok"] = bool(ok)
        ent["output_snippet"] = (output_snippet or "")[:4000]
        if worker_parsed:
            ent["worker_parsed"] = worker_parsed
        _persist_offload_registry()


def mark_offload_cancel_requested(offload_id: str, actor: str | None = None) -> None:
    with _offload_registry_lock:
        ent = _offload_registry.get(offload_id)
        if not ent:
            return
        ent["cancel_requested"] = True
        ent["cancel_actor"] = actor
        ent["cancel_time"] = utcnow().isoformat() if utcnow else datetime.utcnow().isoformat()
        _persist_offload_registry()


def list_offloads() -> list[dict[str, Any]]:
    with _offload_registry_lock:
        return list(_offload_registry.values())


def get_offload_info(offload_id: str) -> dict[str, Any] | None:
    with _offload_registry_lock:
        return _offload_registry.get(offload_id)


def find_offload_by_meta(meta: dict | None = None, window_seconds: int = 3600) -> dict | None:
    if not meta:
        return None
    candidates = []
    cutoff = time.time() - float(window_seconds)
    with _offload_registry_lock:
        for ent in _offload_registry.values():
            try:
                st = ent.get("start_time")
                if st:
                    try:
                        t = datetime.fromisoformat(st).timestamp()
                        if t < cutoff:
                            continue
                    except Exception:
                        pass
                ent_meta = ent.get("meta") or {}
                match = True
                for k, v in (meta or {}).items():
                    if k not in ent_meta:
                        match = False
                        break
                    if ent_meta.get(k) != v:
                        match = False
                        break
                if match:
                    candidates.append(ent)
            except Exception:
                continue
    if not candidates:
        return None
    candidates.sort(key=lambda e: e.get("start_time") or "", reverse=True)
    return candidates[0]


def build_callable_cmd(module: str, function: str, args: list | None = None) -> list[str]:
    worker_path = Path(__file__).resolve().parent / "scripts" / "callable_worker.py"
    cmd = [sys.executable, str(worker_path), "--module", module, "--function", function]
    if args:
        try:
            args_json = json.dumps(args)
            cmd += ["--args", args_json]
        except Exception:
            cmd += ["--args", str(args)]
    return cmd


def start_callable_offload(
    module: str,
    function: str,
    args: list | None = None,
    meta: dict | None = None,
    cwd: str | None = None,
) -> dict:
    meta = meta or {}
    cmd = build_callable_cmd(module, function, args=args)
    try:
        emit_telemetry_event(
            {
                "event": "callable_offload.start",
                "cmd": sanitize_cmd_for_telemetry(cmd),
                "cmd_count": len(cmd) if isinstance(cmd, (list, tuple)) else None,
                "meta": meta,
            }
        )
    except Exception:
        try:
            emit_telemetry_event({"event": "callable_offload.start", "meta": meta})
        except Exception:
            pass
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd or None,
            close_fds=True,
        )
    except Exception as e:
        emit_telemetry_event(
            {
                "event": "callable_offload.start_failed",
                "cmd": sanitize_cmd_for_telemetry(cmd),
                "error": str(e),
                "meta": meta,
            }
        )
        raise

    offload_id = start_offload(meta=meta)
    record_process_offload(offload_id, getattr(proc, "pid", None), cmd)
    emit_telemetry_event(
        {
            "event": "callable_offload.registered",
            "offload_id": offload_id,
            "pid": getattr(proc, "pid", None),
            "cmd": sanitize_cmd_for_telemetry(cmd),
            "cmd_count": len(cmd) if isinstance(cmd, (list, tuple)) else None,
            "meta": meta,
        }
    )
    return {"offload_id": offload_id, "pid": getattr(proc, "pid", None), "cmd": cmd}


async def run_callable_subprocess(
    module: str,
    function: str,
    args: list | None = None,
    *,
    timeout: float | None = 300,
    name: str | None = None,
    meta: dict | None = None,
    build_only: bool = False,
) -> tuple[bool, str] | list[str] | tuple[Any, dict]:
    meta = meta or {}
    _evt_name = name or f"callable:{module}.{function}"
    offload_id = None
    try:
        cmd = build_callable_cmd(module, function, args=args)
        emit_telemetry_event(
            {
                "event": "callable_subproc.start",
                "cmd": sanitize_cmd_for_telemetry(cmd),
                "cmd_count": len(cmd) if isinstance(cmd, (list, tuple)) else None,
                "meta": meta,
            }
        )
        if build_only:
            return cmd

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            offload_id = start_offload(meta=meta)
            record_process_offload(offload_id, getattr(proc, "pid", None), cmd)
            emit_telemetry_event(
                {
                    "event": "callable_subproc.registered",
                    "module": module,
                    "function": function,
                    "offload_id": offload_id,
                    "pid": getattr(proc, "pid", None),
                    "meta": meta,
                }
            )
        except Exception:
            logger.debug("[CALLABLE] failed to register offload in registry", exc_info=True)

        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except TimeoutError:
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
                ((out_b or b"").decode("utf-8", errors="replace"))
                + "\n"
                + ((err_b or b"").decode("utf-8", errors="replace"))
            )
            emit_telemetry_event(
                {
                    "event": "callable_subproc",
                    "status": "timeout",
                    "module": module,
                    "function": function,
                    "meta": meta,
                    "offload_id": offload_id,
                    "pid": getattr(proc, "pid", None),
                }
            )
            try:
                mark_offload_complete(offload_id or "", False, out[:4000], worker_parsed=None)
            except Exception:
                pass
            return False, f"Timed out after {timeout}s. Output:\n{out}"

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

        worker_parsed = _try_parse_worker_json(out)
        snippet = combined[: int(os.getenv("MAINT_SUBPROC_TELEMETRY_SNIPPET", "4000"))]

        if rc == 0:
            payload = {
                "event": "callable_subproc",
                "status": "success",
                "module": module,
                "function": function,
                "meta": meta,
                "output_snippet": snippet,
                "offload_id": offload_id,
                "pid": getattr(proc, "pid", None),
            }
            if worker_parsed:
                payload["worker_parsed"] = worker_parsed
            emit_telemetry_event(payload)
            try:
                mark_offload_complete(offload_id or "", True, snippet, worker_parsed=worker_parsed)
            except Exception:
                pass
            if worker_parsed and isinstance(worker_parsed, dict) and "result" in worker_parsed:
                return worker_parsed["result"], worker_parsed
            return True, combined
        else:
            payload = {
                "event": "callable_subproc",
                "status": "failed",
                "module": module,
                "function": function,
                "returncode": rc,
                "meta": meta,
                "output_snippet": snippet,
                "offload_id": offload_id,
                "pid": getattr(proc, "pid", None),
            }
            if worker_parsed:
                payload["worker_parsed"] = worker_parsed
            emit_telemetry_event(payload)
            try:
                mark_offload_complete(offload_id or "", False, snippet, worker_parsed=worker_parsed)
            except Exception:
                pass
            return False, f"Return code {rc}. Output:\n{combined}"

    except asyncio.CancelledError:
        emit_telemetry_event(
            {
                "event": "callable_subproc",
                "status": "cancelled",
                "module": module,
                "function": function,
                "offload_id": offload_id,
                "meta": meta,
            }
        )
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        emit_telemetry_event(
            {
                "event": "callable_subproc",
                "status": "error",
                "module": module,
                "function": function,
                "error": str(exc),
                "traceback": tb,
                "offload_id": offload_id,
                "meta": meta,
            }
        )
        try:
            mark_offload_complete(offload_id or "", False, str(exc)[:4000], worker_parsed=None)
        except Exception:
            pass
        return False, f"Error spawning callable subprocess: {exc}"


# --------------------------- New: run blocking work in thread + telemetry ---------------------------
async def run_blocking_in_thread(
    func: Callable[..., Any],
    *args,
    name: str | None = None,
    meta: dict | None = None,
    timeout: float | None = None,
    **kwargs,
) -> Any:
    _evt_name = name or getattr(func, "__name__", "run_blocking")
    meta = meta or {}
    try:
        start_iso = utcnow().isoformat()
    except Exception:
        start_iso = datetime.utcnow().isoformat()
    start_t = time.monotonic()

    try:
        emit_telemetry_event(
            {
                "event": "run_block.start",
                "name": _evt_name,
                "meta": meta,
                "timestamp": start_iso,
            }
        )
    except Exception:
        logger.debug("emit start telemetry failed for %s", _evt_name, exc_info=True)

    def _worker():
        return func(*args, **kwargs)

    try:
        if inspect.iscoroutinefunction(func):
            if timeout is not None:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            else:
                result = await func(*args, **kwargs)
        else:
            if timeout is not None:
                result = await asyncio.wait_for(asyncio.to_thread(_worker), timeout=timeout)
            else:
                result = await asyncio.to_thread(_worker)

        duration = round(time.monotonic() - start_t, 6)
        try:
            emit_telemetry_event(
                {
                    "event": "run_block.complete",
                    "name": _evt_name,
                    "meta": meta,
                    "duration_s": duration,
                    "timestamp": utcnow().isoformat(),
                }
            )
        except Exception:
            logger.debug("emit complete telemetry failed for %s", _evt_name, exc_info=True)
        return result

    except asyncio.CancelledError:
        duration = round(time.monotonic() - start_t, 6)
        try:
            emit_telemetry_event(
                {
                    "event": "run_block.cancelled",
                    "name": _evt_name,
                    "meta": meta,
                    "duration_s": duration,
                    "timestamp": utcnow().isoformat(),
                }
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
            emit_telemetry_event(payload)
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
            emit_telemetry_event(payload)
        except Exception:
            logger.exception("emit failure telemetry failed for %s", _evt_name)
        raise


# ---------------------------
# New: run_step wrapper
# ---------------------------
async def run_step(
    func: Callable[..., Any],
    *args,
    name: str | None = None,
    meta: dict | None = None,
    timeout: float | None = None,
    **kwargs,
) -> Any:
    _meta = meta or {}
    _name = name or (f"step:{getattr(func, '__name__', 'callable')}")
    try:
        if inspect.iscoroutinefunction(func):
            if timeout is not None:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            return await func(*args, **kwargs)
        return await run_blocking_in_thread(
            func, *args, name=_name, meta=_meta, timeout=timeout, **kwargs
        )
    except Exception as exc:
        try:
            emit_telemetry_event(
                {
                    "event": "run_step.failed",
                    "name": _name,
                    "meta": _meta,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "timestamp": utcnow().isoformat(),
                }
            )
        except Exception:
            logger.debug("emit run_step failed telemetry failed", exc_info=True)
        raise


# --------------------------- Robust offload argument serialization ---------------------------
OFFLOAD_FILE_PREFIX = "__OFFLOAD_FILE__:"
OFFLOAD_JSON_PREFIX = "__OFFLOAD_JSON__:"

# Tunable threshold: if args is a list of many small row-like sequences, group them into one OFFLOAD_JSON
OFFLOAD_GROUP_THRESHOLD = int(os.getenv("OFFLOAD_GROUP_THRESHOLD", "50"))


def _write_bytes_to_tempfile(b: bytes, tmp_dir: str | None = None) -> str:
    dir_to_use = tmp_dir or (os.path.join(DATA_DIR, "offload_tmp") if DATA_DIR else None)
    if dir_to_use:
        try:
            os.makedirs(dir_to_use, exist_ok=True)
        except Exception:
            dir_to_use = None
    fd, path = tempfile.mkstemp(prefix="offload_", suffix=".bin", dir=dir_to_use)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(b)
    except Exception:
        try:
            os.unlink(path)
        except Exception:
            pass
        raise
    return os.path.abspath(path)


def _serialize_single_arg(arg: Any, tmp_dir: str | None = None) -> tuple[str, str | None]:
    try:
        if callable(arg):
            mod = getattr(arg, "__module__", None)
            name = getattr(arg, "__name__", None)
            if mod and name:
                return f"{mod}:{name}", None
            if name:
                return name, None
            return repr(arg), None

        if isinstance(arg, os.PathLike):
            return os.fspath(arg), None

        if isinstance(arg, (bytes, bytearray, memoryview)):
            p = _write_bytes_to_tempfile(bytes(arg), tmp_dir=tmp_dir)
            return (OFFLOAD_FILE_PREFIX + p, p)

        if isinstance(arg, str):
            return arg, None

        if isinstance(arg, Iterable) and not isinstance(arg, (dict, str, os.PathLike)):
            try:
                seq = list(arg)
            except Exception:
                seq = None
            if seq is not None and seq and all(isinstance(x, int) and 0 <= x <= 255 for x in seq):
                try:
                    p = _write_bytes_to_tempfile(bytes(seq), tmp_dir=tmp_dir)
                    return (OFFLOAD_FILE_PREFIX + p, p)
                except Exception:
                    pass

        try:
            j = json.dumps(arg, ensure_ascii=False, separators=(",", ":"), default=str).encode(
                "utf-8"
            )
            p = _write_bytes_to_tempfile(j, tmp_dir=tmp_dir)
            return (OFFLOAD_JSON_PREFIX + p, p)
        except Exception:
            return str(arg), None
    except Exception:
        try:
            return str(arg), None
        except Exception:
            return "<unserializable>", None


def _args_list_looks_like_byte_stream(args: list[Any]) -> bool:
    if not args or len(args) <= 1:
        return False
    all_ints = True
    all_digit_strings = True
    for a in args:
        if not isinstance(a, int) or not (0 <= a <= 255):
            all_ints = False
        if not (isinstance(a, str) and a.isdigit() and 0 <= int(a) <= 255):
            all_digit_strings = False
    return all_ints or all_digit_strings


def _can_group_offloadable_rows(args: list[Any]) -> bool:
    """
    Heuristic to determine whether `args` is a (potentially large) list of small
    row-like sequences that is safe and beneficial to group into a single JSON file.
    """
    try:
        if not isinstance(args, list):
            return False
        n = len(args)
        if n < OFFLOAD_GROUP_THRESHOLD:
            return False
        # Ensure elements are small list/tuple of simple scalars
        for a in args:
            if not isinstance(a, (list, tuple)):
                return False
            if len(a) > 64:
                return False
            for el in a:
                if not isinstance(el, (str, int, float, type(None), bool)):
                    return False
        return True
    except Exception:
        return False


def serialize_args_for_subprocess(
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    tmp_dir: str | None = None,
) -> tuple[list[str], list[str]]:
    argv_tokens: list[str] = []
    temp_paths: list[str] = []
    args = args or []
    kwargs = kwargs or {}

    # If args is a large list of small row-like sequences, offload them as a single JSON
    if _can_group_offloadable_rows(args):
        try:
            j = json.dumps(args, ensure_ascii=False, default=str).encode("utf-8")
            p = _write_bytes_to_tempfile(j, tmp_dir=tmp_dir)
            argv_tokens.append(OFFLOAD_JSON_PREFIX + p)
            temp_paths.append(p)
            try:
                emit_telemetry_event(
                    {
                        "event": "offload_grouping",
                        "target": "args",
                        "count": len(args),
                        "threshold": OFFLOAD_GROUP_THRESHOLD,
                        "tmp": os.path.basename(p),
                    }
                )
            except Exception:
                logger.debug("emit telemetry for offload grouping failed", exc_info=True)
        except Exception:
            # fallback to per-arg behavior below
            pass
    else:
        if _args_list_looks_like_byte_stream(args):
            try:
                if all(isinstance(a, int) for a in args):
                    b = bytes(args)  # type: ignore[arg-type]
                else:
                    b = bytes(int(a) for a in args)  # type: ignore[arg-type]
                p = _write_bytes_to_tempfile(b, tmp_dir=tmp_dir)
                argv_tokens.append(OFFLOAD_FILE_PREFIX + p)
                temp_paths.append(p)
            except Exception:
                pass
        else:
            for a in args:
                tok, tmp = _serialize_single_arg(a, tmp_dir=tmp_dir)
                argv_tokens.append(tok)
                if tmp:
                    temp_paths.append(tmp)

    # Handle kwargs; allow grouping a large list value per-key
    for k, v in kwargs.items():
        if k is None:
            continue
        key = str(k).lstrip("-")
        flag = f"--{key.replace('_', '-')}"
        # Boolean flags
        if v is True:
            argv_tokens.append(flag)
            continue
        if v is False or v is None:
            continue

        # If the kw value is a large list-like that is eligible for grouping, offload as single JSON and emit telemetry
        if isinstance(v, list) and _can_group_offloadable_rows(v):
            try:
                j = json.dumps(v, ensure_ascii=False, default=str).encode("utf-8")
                p = _write_bytes_to_tempfile(j, tmp_dir=tmp_dir)
                argv_tokens.append(flag)
                argv_tokens.append(OFFLOAD_JSON_PREFIX + p)
                temp_paths.append(p)
                try:
                    emit_telemetry_event(
                        {
                            "event": "offload_grouping",
                            "target": "kwargs",
                            "key": key,
                            "count": len(v),
                            "threshold": OFFLOAD_GROUP_THRESHOLD,
                            "tmp": os.path.basename(p),
                        }
                    )
                except Exception:
                    logger.debug(
                        "emit telemetry for offload grouping (kwargs) failed", exc_info=True
                    )
                continue
            except Exception:
                # fallback to per-value serialization
                pass

        tok, tmp = _serialize_single_arg(v, tmp_dir=tmp_dir)
        argv_tokens.append(flag)
        argv_tokens.append(tok)
        if tmp:
            temp_paths.append(tmp)

    return argv_tokens, temp_paths


def cleanup_temp_paths(paths: list[str]) -> None:
    for p in paths:
        try:
            os.unlink(p)
        except Exception:
            pass


def _serialize_arg_for_subprocess(arg: Any) -> str:
    try:
        if callable(arg):
            mod = getattr(arg, "__module__", None)
            name = getattr(arg, "__name__", None)
            if mod and name:
                return f"{mod}:{name}"
            if name:
                return name
            return repr(arg)

        if isinstance(arg, os.PathLike):
            return os.fspath(arg)
        if isinstance(arg, bytes):
            return arg.decode("utf-8", errors="surrogateescape")
        if isinstance(arg, str):
            return arg
        try:
            return json.dumps(arg, default=str)
        except Exception:
            return str(arg)
    except Exception:
        try:
            return str(arg)
        except Exception:
            return "<unserializable>"


def build_maintenance_cmd(
    command: Any,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    tmp_dir: str | None = None,
) -> tuple[list[str], list[str]]:
    worker_path = Path(__file__).resolve().parent / "maintenance_worker.py"
    if callable(command):
        try:
            module = getattr(command, "__module__", None) or ""
            funcname = getattr(command, "__name__", None) or str(command)
            command_str = f"{module}:{funcname}"
        except Exception:
            command_str = str(command)
    else:
        command_str = str(command)
    base_cmd = [sys.executable, str(worker_path), command_str]
    argv_tokens, temp_paths = serialize_args_for_subprocess(
        args=args, kwargs=kwargs, tmp_dir=tmp_dir
    )
    full_cmd = base_cmd + argv_tokens
    full_cmd = [str(c) for c in full_cmd]
    return full_cmd, temp_paths


def _try_parse_worker_json(stdout_text: str) -> dict | None:
    if not stdout_text:
        return None
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict) and any(
                k in parsed for k in ("worker_result", "worker_event", "event")
            ):
                return parsed
            if isinstance(parsed, dict) and "status" in parsed and "command" in parsed:
                return parsed
        except Exception:
            continue
    return None


# ---------------------------
# Normalization helper (root fix)
# ---------------------------
def normalize_args_for_maintenance(args: Any | None) -> list[Any]:
    """
    Normalize the caller-supplied `args` parameter into a list suitable for
    serialize_args_for_subprocess/build_maintenance_cmd.

    Accepts:
      - None -> []
      - list/tuple -> list(...) (returned unchanged)
      - scalar (str, PathLike, bytes, dict, etc) -> [args]

    Rationale: many call-sites pass a single path/string as the second positional
    argument (e.g. run_maintenance_with_isolation(command, local_path, ...)). In that
    situation Python binds that string to the `args` parameter; earlier code then
    iterated that string treating it as an iterable of characters. This helper
    ensures the common-case single value is wrapped into a one-element list so the
    subprocess argv tokens preserve the intended single-argument semantics.
    """
    if args is None:
        return []
    if isinstance(args, (list, tuple)):
        return list(args)
    # If it's a string or pathlike, or any other scalar, wrap in a list
    return [args]


# --------------------------- New: run maintenance in a subprocess ---------------------------
async def run_maintenance_subprocess(
    command: Any,
    args: list[Any] | None = None,
    *,
    kwargs: dict[str, Any] | None = None,
    timeout: float | None = 300,
    name: str | None = None,
    meta: dict | None = None,
    build_only: bool | None = False,
    tmp_dir: str | None = None,
) -> tuple[bool, str] | list[str] | tuple[Any, dict]:
    """
    Spawn maintenance_worker.py to run `command`.

    Key change: we pass a marker env var MAINT_SUBPROC=1 to the child process so
    worker callables can detect subprocess context and choose to return only a
    safe, small summary (while still persisting full cache files to disk).
    """
    meta = meta or {}
    offload_id = None
    temp_paths: list[str] = []
    try:
        worker_path = Path(__file__).resolve().parent / "maintenance_worker.py"
        if not worker_path.exists():
            msg = f"maintenance_worker not found at {worker_path}"
            emit_telemetry_event(
                {
                    "event": "maintenance_subproc",
                    "status": "failed",
                    "reason": "missing_worker",
                    "command": str(command),
                    "meta": meta,
                }
            )
            return False, msg

        # Build command and robustly serialize args
        cmd, temp_paths = build_maintenance_cmd(command, args=args, kwargs=kwargs, tmp_dir=tmp_dir)

        emit_telemetry_event(
            {
                "event": "maintenance_subproc.start",
                "command": str(command),
                "cmd": sanitize_cmd_for_telemetry(cmd),
                "cmd_count": len(cmd) if isinstance(cmd, (list, tuple)) else None,
                "meta": meta,
            }
        )

        if build_only:
            return cmd

        # Prepare environment for child: copy current env and set marker
        child_env = os.environ.copy()
        # Marker used by cache builders and other callables to detect subprocess context.
        child_env["MAINT_SUBPROC"] = "1"

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=child_env,
        )

        try:
            offload_id = start_offload(meta=meta)
            record_process_offload(offload_id, getattr(proc, "pid", None), cmd)
            emit_telemetry_event(
                {
                    "event": "maintenance_subproc.registered",
                    "command": str(command),
                    "offload_id": offload_id,
                    "pid": getattr(proc, "pid", None),
                    "meta": meta,
                }
            )
        except Exception:
            logger.debug("[MAINT] failed to register offload in registry", exc_info=True)

        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            try:
                await proc.wait()
            except Exception:
                pass
            out_b, err_b = b"", b""
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
            emit_telemetry_event(
                {
                    "event": "maintenance_subproc",
                    "status": "timeout",
                    "command": str(command),
                    "meta": meta,
                    "offload_id": offload_id,
                    "pid": getattr(proc, "pid", None),
                }
            )
            try:
                mark_offload_complete(offload_id or "", False, out[:4000], worker_parsed=None)
            except Exception:
                pass
            return False, f"Timed out after {timeout}s. Output:\n{out}"

        # Process finished normally
        out_b, err_b = b"", b""
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

        MAX_SNIPPET = int(os.getenv("MAINT_SUBPROC_TELEMETRY_SNIPPET", "4000"))
        worker_parsed = _try_parse_worker_json(out)

        if worker_parsed:
            try:
                snippet_candidate = json.dumps(worker_parsed, default=str)
            except Exception:
                snippet_candidate = str(worker_parsed)
            snippet = snippet_candidate[:MAX_SNIPPET]
        else:
            snippet = combined[:MAX_SNIPPET]

        output_length = len(combined)

        if rc == 0:
            emit_payload = {
                "event": "maintenance_subproc",
                "status": "success",
                "command": str(command),
                "meta": meta,
                "output_snippet": snippet,
                "output_length": output_length,
                "output_truncated": output_length > len(snippet),
                "offload_id": offload_id,
                "pid": getattr(proc, "pid", None),
            }
            if worker_parsed:
                emit_payload["worker_parsed"] = worker_parsed
            emit_telemetry_event(emit_payload)
            try:
                mark_offload_complete(offload_id or "", True, snippet, worker_parsed=worker_parsed)
            except Exception:
                pass
            if worker_parsed and isinstance(worker_parsed, dict) and "result" in worker_parsed:
                return worker_parsed["result"], worker_parsed
            return True, combined
        else:
            emit_payload = {
                "event": "maintenance_subproc",
                "status": "failed",
                "command": str(command),
                "returncode": rc,
                "meta": meta,
                "output_snippet": snippet,
                "output_length": output_length,
                "output_truncated": output_length > len(snippet),
                "offload_id": offload_id,
                "pid": getattr(proc, "pid", None),
            }
            if worker_parsed:
                emit_payload["worker_parsed"] = worker_parsed
            emit_telemetry_event(emit_payload)
            try:
                mark_offload_complete(offload_id or "", False, snippet, worker_parsed=worker_parsed)
            except Exception:
                pass
            return False, f"Return code {rc}. Output:\n{combined}"

    except asyncio.CancelledError:
        emit_telemetry_event(
            {
                "event": "maintenance_subproc",
                "status": "cancelled",
                "command": str(command),
                "meta": meta,
                "offload_id": offload_id,
            }
        )
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        emit_telemetry_event(
            {
                "event": "maintenance_subproc",
                "status": "error",
                "command": str(command),
                "error": str(exc),
                "traceback": tb,
                "meta": meta,
                "offload_id": offload_id,
            }
        )
        try:
            mark_offload_complete(offload_id or "", False, str(exc)[:4000], worker_parsed=None)
        except Exception:
            pass
        return False, f"Error spawning subprocess: {exc}"


# --------------------------- New wrapper: run maintenance with isolation (root-fix applied) ---------------------------
async def run_maintenance_with_isolation(
    command: Any,
    args: list[Any] | None = None,
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

    Root-fix: callers sometimes pass a single string/path as the second positional
    argument (e.g. run_maintenance_with_isolation(command, local_path, ...)).
    In that case Python binds a str into `args` and earlier implementations treated
    that string as an iterable and expanded it into character tokens. We now
    normalize the `args` parameter into a list consistently using
    normalize_args_for_maintenance().
    """
    meta = meta or {}
    _evt = name or f"maintenance:{command}"

    # Normalize args into a list (root-fix)
    args_list = normalize_args_for_maintenance(args)

    if prefer_process is None:
        prefer_process = os.getenv("MAINT_WORKER_MODE", "thread").lower() == "process"

    emit_telemetry_event(
        {
            "event": "maintenance_run.start",
            "command": str(command),
            "prefer_process": prefer_process,
            "meta": meta,
            "timestamp": utcnow().isoformat(),
        }
    )

    if prefer_process:
        needs_fallback = False
        try:
            if callable(command):
                mod_name = getattr(command, "__module__", None)
                fn_name = getattr(command, "__name__", None)
                if not mod_name or not fn_name:
                    needs_fallback = True
                else:
                    try:
                        mod = importlib.import_module(mod_name)
                        attr = getattr(mod, fn_name, None)
                        if attr is not command:
                            needs_fallback = True
                    except Exception:
                        needs_fallback = True
            elif isinstance(command, str) and ":" in command:
                mod_name, fn_name = command.split(":", 1)
                try:
                    mod = importlib.import_module(mod_name)
                    if not hasattr(mod, fn_name):
                        needs_fallback = True
                except Exception:
                    needs_fallback = True
            else:
                emit_telemetry_event(
                    {
                        "event": "maintenance_run.unverified_command",
                        "command": str(command),
                        "meta": meta,
                        "note": "command is neither callable nor module:function string",
                    }
                )
        except Exception as exc:
            emit_telemetry_event(
                {
                    "event": "maintenance_run.validation_error",
                    "command": str(command),
                    "meta": meta,
                    "error": str(exc),
                    "traceback": traceback.format_exc()[:2000],
                }
            )
            needs_fallback = True

        if needs_fallback:
            msg = {
                "event": "maintenance_run.fallback_non_importable",
                "command_repr": repr(command),
                "command_str": str(command),
                "meta": meta,
                "reason": "not_importable_module_level",
                "timestamp": utcnow().isoformat(),
            }
            emit_telemetry_event(msg)
            logger.info(
                "[MAINT] Falling back to in-thread execution because command is not importable in child process: %r",
                command,
            )
            # Preserve detailed traceback at DEBUG level for troubleshooting.
            logger.debug(
                "Offload child-process import error (traceback):\n%s", traceback.format_exc()
            )
            prefer_process = False

    if prefer_process:
        ok, out = await run_maintenance_subprocess(
            command, args=args_list, kwargs=kwargs, timeout=timeout, name=name, meta=meta
        )
        emit_telemetry_event(
            {
                "event": "maintenance_run.complete",
                "command": str(command),
                "mode": "process",
                "ok": bool(ok),
                "meta": meta,
            }
        )
        return ok, out

    try:
        resolved_command = command
        if isinstance(command, str) and ":" in command:
            try:
                mod_name, fn_name = command.split(":", 1)
                mod = importlib.import_module(mod_name)
                resolved_command = getattr(mod, fn_name)
            except Exception:
                resolved_command = command

        if resolved_command == "post_stats" or (
            callable(resolved_command)
            and getattr(resolved_command, "__name__", "") == "run_post_import_stats_update"
        ):
            server = (kwargs or {}).get("server")
            database = (kwargs or {}).get("database")
            username = (kwargs or {}).get("username")
            password = (kwargs or {}).get("password")
            try:
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
                emit_telemetry_event(
                    {
                        "event": "maintenance_run.complete",
                        "command": str(command),
                        "mode": "thread",
                        "ok": True,
                        "meta": meta,
                    }
                )
                return True, "post_stats completed"
            except Exception as exc:
                emit_telemetry_event(
                    {
                        "event": "maintenance_run.complete",
                        "command": str(command),
                        "mode": "thread",
                        "ok": False,
                        "meta": meta,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                return False, f"post_stats failed: {exc}"

        elif resolved_command == "proc_import" or (
            callable(resolved_command)
            and getattr(resolved_command, "__name__", "") == "run_proc_config_import"
        ):
            try:
                from proc_config_import import run_proc_config_import  # type: ignore
            except Exception as e:
                emit_telemetry_event(
                    {
                        "event": "maintenance_run",
                        "command": str(command),
                        "mode": "thread",
                        "ok": False,
                        "meta": meta,
                        "error": f"import_error: {e}",
                    }
                )
                return False, f"import_error: {e}"

            try:
                res = await run_blocking_in_thread(
                    run_proc_config_import,
                    name=name or "run_proc_config_import",
                    meta=meta,
                    timeout=timeout,
                )
                ok = bool(res)
                emit_telemetry_event(
                    {
                        "event": "maintenance_run.complete",
                        "command": str(command),
                        "mode": "thread",
                        "ok": ok,
                        "meta": meta,
                    }
                )
                return ok, "proc_import thread completed" if ok else "proc_import returned failure"
            except Exception as exc:
                emit_telemetry_event(
                    {
                        "event": "maintenance_run.complete",
                        "command": str(command),
                        "mode": "thread",
                        "ok": False,
                        "meta": meta,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                return False, f"proc_import failed: {exc}"
        else:
            emit_telemetry_event(
                {"event": "maintenance_run.unknown_command", "command": str(command), "meta": meta}
            )
            ok, out = await run_maintenance_subprocess(
                command, args=args_list, kwargs=kwargs, timeout=timeout, name=name, meta=meta
            )
            return ok, out
    except asyncio.CancelledError:
        emit_telemetry_event(
            {
                "event": "maintenance_run.cancelled",
                "command": str(command),
                "meta": meta,
            }
        )
        raise
    except Exception as exc:
        emit_telemetry_event(
            {
                "event": "maintenance_run.error",
                "command": str(command),
                "meta": meta,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc()[:2000],
            }
        )
        return False, f"Exception: {exc}"


# ---------------- Cancel offload API (PR E)
# Replace the duplicated _pid_exists implementation with a delegating shim
def _pid_exists(pid: int) -> bool:
    """
    Delegating shim: prefer the canonical process_utils.pid_alive implementation.
    Keeps backwards-compatible name for internal callers but avoids duplication.
    """
    try:
        # Prefer canonical implementation
        from process_utils import pid_alive as _pid_alive  # type: ignore

        return bool(_pid_alive(pid))
    except Exception:
        # Fallback to local heuristic if import fails for any reason.
        try:
            if pid is None:
                return False
            pid = int(pid)
        except Exception:
            return False
        try:
            if psutil:
                return psutil.pid_exists(pid)
            else:
                os.kill(pid, 0)
                return True
        except Exception:
            return False


def _terminate_pid_with_escalation(pid: int, grace_period: float = 5.0) -> tuple[bool, str]:
    try:
        if psutil:
            p = psutil.Process(pid)
            try:
                p.terminate()
            except Exception:
                pass
            gone, alive = psutil.wait_procs([p], timeout=grace_period)
            if alive:
                try:
                    p.kill()
                except Exception:
                    pass
                gone2, alive2 = psutil.wait_procs([p], timeout=2.0)
                if alive2:
                    return False, "Process still alive after kill"
                return True, "Killed after terminate"
            else:
                return True, "Terminated gracefully"
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
            end = time.time() + float(grace_period)
            while time.time() < end:
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except Exception:
                    return True, "Terminated gracefully"
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                os.kill(pid, 0)
                return False, "Still alive after SIGKILL"
            except Exception:
                return True, "Killed after SIGKILL"
    except Exception as e:
        return False, f"Error during terminate/kill: {e}"


def cancel_offload(
    offload_id: str | None = None,
    pid: int | None = None,
    actor: str | None = None,
    grace_period: float = 5.0,
) -> dict[str, Any]:
    try:
        if offload_id:
            ent = get_offload_info(offload_id)
            if not ent:
                return {
                    "ok": False,
                    "offload_id": offload_id,
                    "pid": None,
                    "msg": "offload not found",
                }
            pid = ent.get("pid") or pid
        if not pid:
            return {"ok": False, "offload_id": offload_id, "pid": None, "msg": "no pid available"}

        try:
            pid = int(pid)
        except Exception:
            return {"ok": False, "offload_id": offload_id, "pid": pid, "msg": "invalid pid"}

        emit_telemetry_event(
            {
                "event": "offload_cancel.request",
                "offload_id": offload_id,
                "pid": pid,
                "actor": actor,
                "timestamp": utcnow().isoformat(),
            }
        )

        if offload_id:
            try:
                mark_offload_cancel_requested(offload_id, actor=actor)
            except Exception:
                logger.debug("failed to mark offload cancel requested", exc_info=True)

        if not _pid_exists(pid):
            result = {"ok": False, "offload_id": offload_id, "pid": pid, "msg": "pid not running"}
            emit_telemetry_event({"event": "offload_cancel.result", **result, "actor": actor})
            return result

        ok, reason = _terminate_pid_with_escalation(pid, grace_period=grace_period)

        if offload_id:
            try:
                mark_offload_complete(
                    offload_id,
                    ok=False,
                    output_snippet=f"cancel_requested_by={actor}; result={reason}",
                    worker_parsed=None,
                )
            except Exception:
                logger.debug("failed to mark offload complete after cancel", exc_info=True)

        res = {
            "ok": ok,
            "offload_id": offload_id,
            "pid": pid,
            "msg": "cancelled" if ok else "cancel_failed",
            "details": reason,
        }
        emit_telemetry_event({"event": "offload_cancel.result", **res, "actor": actor})
        return res
    except Exception as exc:
        tb = traceback.format_exc()[:2000]
        emit_telemetry_event(
            {
                "event": "offload_cancel.error",
                "offload_id": offload_id,
                "pid": pid,
                "actor": actor,
                "error": str(exc),
                "traceback": tb,
            }
        )
        return {"ok": False, "offload_id": offload_id, "pid": pid, "msg": f"error: {exc}"}


__all__ = [
    "build_maintenance_cmd",
    "cancel_offload",
    "emit_telemetry_event",
    "find_offload_by_meta",
    "get_offload_info",
    "get_process_info",
    "list_offloads",
    "mark_offload_complete",
    "matches_process",
    "normalize_args_for_maintenance",
    "pid_alive",
    "record_process_offload",
    "run_callable_subprocess",
    "run_maintenance_with_isolation",
    "run_step",
    "start_callable_offload",
    "start_offload",
    # exported for testing and reuse
]
