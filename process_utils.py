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

Notes / changes in this hardened version:
- Accepts numeric strings for pid parameters (coerces via int()).
- If psutil is present but a psutil call raises unexpectedly, falls back to os.kill-based
  heuristic (pid_alive) instead of silently returning a false-negative.
- exe path comparison uses os.path.realpath + os.path.normcase for robust matching across
  symlinks and case-insensitive filesystems.
- Conservative default matching semantics retained (when exe/create_time are unavailable we
  assume a match); added debug logging when fallbacks / conservative assumptions are used.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Optional dependency
try:
    import psutil  # optional dependency
except Exception:
    psutil = None  # type: ignore


def _coerce_pid(pid: Any) -> int | None:
    """Try to coerce various PID representations into an int; return None if invalid."""
    try:
        if isinstance(pid, int):
            return pid
        if isinstance(pid, str):
            pid = pid.strip()
            if not pid:
                return None
            return int(pid)
        # allow other numeric-like (float that is integral)
        if isinstance(pid, float):
            return int(pid)
        # Try generic conversion
        return int(pid)
    except Exception:
        return None


def pid_alive(pid: Any) -> bool:
    """
    Best-effort check whether a PID appears alive.

    - Accepts ints or strings that can be coerced to int.
    - Uses psutil.pid_exists when psutil is available and working.
    - If psutil is present but raises, falls back to os.kill(pid, 0) heuristic.
    - Returns False for non-positive/invalid PIDs.
    """
    pid_int = _coerce_pid(pid)
    if pid_int is None or pid_int <= 0:
        return False

    # Prefer psutil when available but guard against exceptions
    if psutil:
        try:
            return bool(psutil.pid_exists(pid_int))
        except Exception as e:
            logger.debug("[PROCESS_UTILS] psutil.pid_exists raised, falling back to os.kill: %s", e)

    # Fallback heuristic using os.kill(pid, 0)
    try:
        os.kill(pid_int, 0)
        return True
    except Exception:
        return False


# In process_utils.py, update get_process_info():


def get_process_info(pid: Any) -> dict[str, Any | None]:
    """
    Gather process information in a safe, best-effort manner.

    Returns dict:
      {
        "pid_exists": bool,
        "is_running": bool,
        "exe": str | None,
        "create_time": float | None,
      }

    - All fields are present; missing values are None.
    - psutil is preferred; if psutil calls raise unexpectedly we fall back to os.kill.
    - If psutil crashes (seg fault), this function cannot catch it; caller must isolate.
    """
    out: dict[str, Any | None] = {
        "pid_exists": False,
        "is_running": False,
        "exe": None,
        "create_time": None,
    }

    pid_int = _coerce_pid(pid)
    if pid_int is None or pid_int <= 0:
        return out

    psutil_available_and_ok = False

    if psutil:
        try:
            exists = psutil.pid_exists(pid_int)
            psutil_available_and_ok = True
            out["pid_exists"] = bool(exists)
            if out["pid_exists"]:
                try:
                    proc = psutil.Process(pid_int)
                    # --- CRITICAL: Wrap each psutil call individually to catch failures ---
                    try:
                        out["is_running"] = bool(proc.is_running())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        out["is_running"] = False
                    except Exception as e:
                        logger.debug(
                            "[PROCESS_UTILS] proc.is_running() failed for pid=%s: %s", pid_int, e
                        )
                        out["is_running"] = False

                    try:
                        out["exe"] = proc.exe()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        out["exe"] = None
                    except Exception as e:
                        logger.debug(
                            "[PROCESS_UTILS] proc.exe() unavailable for pid=%s: %s", pid_int, e
                        )
                        out["exe"] = None

                    try:
                        out["create_time"] = proc.create_time()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        out["create_time"] = None
                    except Exception as e:
                        logger.debug(
                            "[PROCESS_UTILS] proc.create_time() unavailable for pid=%s: %s",
                            pid_int,
                            e,
                        )
                        out["create_time"] = None

                except psutil.NoSuchProcess:
                    out["is_running"] = False
                except Exception as e:
                    logger.debug("[PROCESS_UTILS] psutil.Process failed for pid=%s: %s", pid_int, e)
                    # Mark as unavailable so fallback below runs
                    psutil_available_and_ok = False
        except Exception as e:
            # psutil. pid_exists failed in an unexpected way; we'll fall back below
            logger.debug(
                "[PROCESS_UTILS] psutil.pid_exists raised unexpected error for pid=%s: %s",
                pid_int,
                e,
            )
            psutil_available_and_ok = False

    # If psutil was not available or had errors, use fallback heuristic
    if not psutil_available_and_ok:
        try:
            alive = pid_alive(pid_int)
            out["pid_exists"] = alive
            out["is_running"] = alive
            # exe/create_time remain None since we cannot fetch them without psutil
        except Exception:
            logger.debug("[PROCESS_UTILS] pid_alive fallback failed for pid=%s", pid_int)

    return out


def matches_process(
    pid: Any, *, exe_path: str | None = None, created_before: float | None = None
) -> bool:
    """
    Determine whether the process identified by pid should be treated as the same running
    program described by exe_path/created_before criteria.

    Conservative defaults:
      - If proc isn't running -> False
      - If exe_path provided and proc.exe() available -> compare via realpath + normcase
      - If proc.exe() unavailable -> assume match (conservative)
      - If created_before provided and proc.create_time available -> ensure proc_ct <= created_before + 1s
      - If create_time unavailable -> assume match (conservative)

    NOTE: This function is conservative by default to avoid erroneously killing live processes.
    """
    pid_int = _coerce_pid(pid)
    if pid_int is None or pid_int <= 0:
        return False

    info = get_process_info(pid_int)
    if not info.get("is_running"):
        return False

    # EXE path checking (use realpath + normcase to be robust)
    if exe_path:
        proc_exe = info.get("exe")
        if proc_exe:
            try:
                proc_real = os.path.normcase(os.path.realpath(str(proc_exe)))
                expected_real = os.path.normcase(os.path.realpath(str(exe_path)))
                if proc_real != expected_real:
                    logger.debug(
                        "[PROCESS_UTILS] exe mismatch pid=%s proc_exe=%s expected=%s",
                        pid_int,
                        proc_real,
                        expected_real,
                    )
                    return False
            except Exception as e:
                # If comparison fails for any reason, be conservative and assume match
                logger.debug(
                    "[PROCESS_UTILS] exe comparison failed for pid=%s proc_exe=%s expected=%s: %s",
                    pid_int,
                    proc_exe,
                    exe_path,
                    e,
                )
        else:
            logger.debug(
                "[PROCESS_UTILS] proc.exe unavailable for pid=%s; assuming exe matches (conservative)",
                pid_int,
            )

    # Creation time check: detect PID reuse
    if created_before is not None:
        proc_ct = info.get("create_time")
        if proc_ct is not None:
            try:
                if float(proc_ct) > float(created_before) + 1.0:
                    logger.debug(
                        "[PROCESS_UTILS] process create_time too new -> treated as PID reuse pid=%s proc_ct=%s created_before=%s",
                        pid_int,
                        proc_ct,
                        created_before,
                    )
                    return False
            except Exception as e:
                logger.debug(
                    "[PROCESS_UTILS] create_time comparison failed for pid=%s: %s (proc_ct=%s created_before=%s)",
                    pid_int,
                    e,
                    proc_ct,
                    created_before,
                )
        else:
            logger.debug(
                "[PROCESS_UTILS] proc.create_time unavailable for pid=%s; assuming match (conservative)",
                pid_int,
            )

    return True


__all__ = ["get_process_info", "matches_process", "pid_alive"]
