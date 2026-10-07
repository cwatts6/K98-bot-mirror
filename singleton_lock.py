"""
Safer singleton lockfile helper (updated to use process_utils).

This module provides:
- acquire_singleton_lock(lock_path, *, exit_on_conflict=True, raise_on_conflict=False)
- release_singleton_lock(lock_path)

Default behaviour preserves the historical semantics: if another instance is
detected, the function will call sys.exit(0). To use in tests or library code,
set exit_on_conflict=False and/or raise_on_conflict=True.

Lockfile format (JSON):
{
  "pid": <int>,
  "created": <float epoch seconds>,
  "exe": "<path to python executable>",
  "cwd": "<working directory>",
  "version": 1
}
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any

from file_utils import emit_telemetry_event
from process_utils import matches_process  # centralized helpers

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")


# In singleton_lock.py, update acquire_singleton_lock():


def acquire_singleton_lock(
    lock_path: str, *, exit_on_conflict: bool = True, raise_on_conflict: bool = False
) -> dict[str, Any] | None:
    """
    Acquire a singleton lock at lock_path.

    Parameters:
      - lock_path: path to the lock file (string)
      - exit_on_conflict: if True (default) call sys.exit(0) when another live instance is detected
      - raise_on_conflict: if True raise RuntimeError instead of sys.exit when conflict detected

    Returns:
      - metadata dict written to the lock file on success
      - None if acquisition aborted and exit_on_conflict is False (and raise_on_conflict False)
    """
    p = Path(lock_path)

    # If a lockfile exists, try to parse and determine whether it's live
    if p.exists():
        try:
            raw = p.read_text(encoding="utf-8")
            data = json.loads(raw) if raw else {}
            pid = int(data.get("pid", 0))
            saved_exe = data.get("exe")
            saved_created = float(data.get("created", 0))
        except Exception:
            pid = 0
            saved_exe = None
            saved_created = 0.0

        if pid > 0:
            # --- CRITICAL FIX: Wrap matches_process in a broad try/except to prevent crash ---
            try:
                # Use centralized helper to decide if the PID belongs to a live, matching process
                is_live = matches_process(pid, exe_path=saved_exe, created_before=saved_created)
            except Exception as e:
                # If matches_process raises (or if psutil crashes and raises), treat as stale
                logger.warning(
                    "[singleton] matches_process failed for pid=%s (treating as stale): %s", pid, e
                )
                emit_telemetry_event(
                    {"event": "singleton_lock. psutil_fallback", "pid": pid, "error": str(e)}
                )
                is_live = False

            if is_live:
                msg = f"[singleton] Another instance is running (PID {pid})."
                if logger.handlers:
                    logger.error(msg)
                else:
                    print(msg, file=sys.stderr)
                if raise_on_conflict:
                    raise RuntimeError(msg)
                if exit_on_conflict:
                    sys.exit(0)
                return None
            # else: treat as stale and remove below

        # Remove stale or unreadable lockfile (best-effort)
        try:
            p.unlink(missing_ok=True)
        except Exception:
            try:
                logger.debug("[singleton] Failed to remove stale lock file %s", p)
            except Exception:
                pass

    # Build lock metadata
    lock_data: dict[str, Any] = {
        "pid": os.getpid(),
        "created": time.time(),
        "exe": sys.executable,
        "cwd": os.getcwd(),
        "version": 1,
    }

    # Prefer atomic_write_json if available
    try:
        from file_utils import atomic_write_json  # type: ignore

        atomic_write_json(p, lock_data)
    except Exception:
        # Fallback to tmp+replace with fsync where possible
        try:
            tmp = p.with_suffix(p.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(lock_data, f, indent=2)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            os.replace(tmp, p)
        except Exception as e:
            try:
                p.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
            except Exception:
                try:
                    logger.exception("[singleton] Failed to write lock file %s:  %s", p, e)
                except Exception:
                    print(f"[singleton] Failed to write lock file {p}: {e}", file=sys.stderr)

    try:
        logger.info("[singleton] Lock acquired at %s (PID %d)", lock_path, os.getpid())
    except Exception:
        print(f"[singleton] Lock acquired at {lock_path} (PID {os.getpid()})", file=sys.stderr)

    return lock_data


def release_singleton_lock(lock_path: str) -> None:
    """
    Remove the singleton lock file at lock_path, best-effort.
    """
    try:
        Path(lock_path).unlink(missing_ok=True)
    except Exception:
        try:
            logger.exception("[singleton] Failed to release lock %s", lock_path)
        except Exception:
            pass
