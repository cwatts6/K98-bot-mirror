"""
process_utils.py

Centralized process inspection helpers.

Provides:
- pid_alive(pid) -> bool
- get_process_info(pid) -> dict with keys:
    - pid_exists: bool
    - is_running: bool
    - exe: str | None
    - create_time: float | None
- matches_process(pid, *, exe_path=None, created_before=None) -> bool

Notes:
- Prefer importing these helpers instead of duplicating pid-existence/exe/ctime logic.
- Uses psutil when available; falls back to os.kill-based heuristics.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

try:
    import psutil  # optional dependency
except Exception:
    psutil = None  # type: ignore


def pid_alive(pid: int) -> bool:
    """
    Best-effort check whether a PID appears alive.

    - Uses psutil.pid_exists when psutil is available.
    - Otherwise falls back to os.kill(pid, 0) when supported.
    - Returns False for non-positive PIDs.
    """
    if not isinstance(pid, int) or pid <= 0:
        return False
    if psutil:
        try:
            return psutil.pid_exists(pid)
        except Exception:
            # Fall back to os.kill heuristic
            pass
    try:
        # POSIX: signal 0 checks for permission/error but doesn't deliver a signal.
        # On modern Windows Python, os.kill exists and will raise appropriately.
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def get_process_info(pid: int) -> dict[str, Any | None]:
    """
    Gather process information in a safe, best-effort manner.

    Returns dict:
      {
        "pid_exists": bool,
        "is_running": bool,
        "exe": str | None,
        "create_time": float | None,
      }

    - All fields will be present; missing values are None.
    - This function is resilient to psutil errors and permissions issues.
    """
    out: dict[str, Any | None] = {
        "pid_exists": False,
        "is_running": False,
        "exe": None,
        "create_time": None,
    }

    if not isinstance(pid, int) or pid <= 0:
        return out

    # Prefer psutil for richer info
    if psutil:
        try:
            out["pid_exists"] = psutil.pid_exists(pid)
            try:
                proc = psutil.Process(pid)
                out["is_running"] = proc.is_running()
                try:
                    out["exe"] = proc.exe()
                except Exception:
                    out["exe"] = None
                try:
                    out["create_time"] = proc.create_time()
                except Exception:
                    out["create_time"] = None
            except psutil.NoSuchProcess:
                # process does not exist
                out["is_running"] = False
            except Exception:
                # Unexpected psutil error — fall back to pid_exists only
                pass
        except Exception:
            # psutil.pid_exists failed unexpectedly — fallback to os.kill
            out["pid_exists"] = False

    # Fallback heuristics if psutil is unavailable or incomplete
    if not out["pid_exists"] and not psutil:
        try:
            alive = pid_alive(pid)
            out["pid_exists"] = alive
            out["is_running"] = alive
            out["exe"] = None
            out["create_time"] = None
        except Exception:
            pass

    return out


def matches_process(
    pid: int, *, exe_path: str | None = None, created_before: float | None = None
) -> bool:
    """
    Determine whether the process identified by pid should be treated as the same running
    program described by exe_path/created_before criteria.

    - If the process is not running, returns False.
    - If exe_path is provided, returns True only if proc.exe() equals exe_path (absolute path compare).
      If proc.exe() is unavailable, falls back to True if pid is alive (conservative).
    - If created_before is provided (epoch seconds), treats the process as "matched" only if
      the process create_time is <= created_before + 1s margin. If create_time is unavailable,
      falls back to treating as matched (conservative).
    """
    info = get_process_info(pid)
    if not info.get("is_running"):
        return False

    # Check exe match if requested
    if exe_path:
        proc_exe = info.get("exe")
        try:
            if proc_exe:
                if os.path.abspath(proc_exe) != os.path.abspath(exe_path):
                    return False
            else:
                # cannot determine exe — be conservative and assume match
                pass
        except Exception:
            # Comparison failed — be conservative and assume match
            pass

    # Check creation time to detect PID reuse
    if created_before is not None:
        proc_ct = info.get("create_time")
        if proc_ct is not None:
            try:
                # if process started after the saved creation time (plus a small tolerance),
                # treat as PID reuse -> do not match
                if proc_ct > float(created_before) + 1.0:
                    return False
            except Exception:
                pass
        else:
            # No create_time available — be conservative and assume match
            pass

    return True


__all__ = ["get_process_info", "matches_process", "pid_alive"]
