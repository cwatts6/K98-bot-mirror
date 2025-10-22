import json
import os
from pathlib import Path
import sys
import time
from typing import Any

try:
    import psutil  # optional but highly recommended
except Exception:
    psutil = None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if psutil:
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    # Fallback: best-effort
    try:
        # On POSIX, this sends signal 0; on Windows, os.kill is available on modern Pythons.
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def acquire_singleton_lock(lock_path: str) -> None:
    p = Path(lock_path)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            saved_exe = data.get("exe")
            saved_created = float(data.get("created", 0))
            if pid > 0:
                if psutil:
                    try:
                        proc = psutil.Process(pid)
                        if proc.is_running():
                            # compare process exe/cmdline and creation time to avoid PID-reuse false-positives
                            try:
                                proc_exe = proc.exe()
                            except Exception:
                                proc_exe = None
                            try:
                                proc_ctime = proc.create_time()
                            except Exception:
                                proc_ctime = None

                            # If saved_exe is present, prefer exact match on the executable; otherwise fall back to pid_exists
                            if saved_exe:
                                # If exe matches and process start time is <= lock created time, treat as live.
                                if proc_exe and os.path.abspath(proc_exe) == os.path.abspath(
                                    saved_exe
                                ):
                                    # If process started after the lock file was created, assume PID was reused -> treat as stale
                                    if proc_ctime and proc_ctime > saved_created + 1:
                                        # PID reused - treat as stale
                                        pass
                                    else:
                                        print(
                                            f"[singleton] Another instance is running (PID {pid}). Exiting."
                                        )
                                        sys.exit(0)
                                else:
                                    # Different exe -> treat as stale (will remove below)
                                    pass
                            else:
                                # No saved exe in lock file: safest fallback is to assume pid_exists means live
                                print(
                                    f"[singleton] Another instance is running (PID {pid}). Exiting."
                                )
                                sys.exit(0)
                        # else not running -> fall through and remove lock
                    except psutil.NoSuchProcess:
                        # process gone -> treat as stale
                        pass
                    except Exception:
                        # if psutil failed for unexpected reason, be conservative and treat it as stale so restart can recover
                        pass
                else:
                    # No psutil available: use looser heuristic
                    if _pid_alive(pid):
                        # If lock file contains an 'exe' that differs from current python, assume it's a different process -> stale
                        if saved_exe and os.path.abspath(saved_exe) != os.path.abspath(
                            sys.executable
                        ):
                            # likely PID belongs to some other program -> treat as stale and remove
                            pass
                        else:
                            print(f"[singleton] Another instance is running (PID {pid}). Exiting.")
                            sys.exit(0)
        except Exception:
            # corrupted / unreadable → treat as stale
            pass
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    # Write the lock with extra metadata
    try:
        lock_data: dict[str, Any] = {
            "pid": os.getpid(),
            "created": time.time(),
            "exe": sys.executable,
            "cwd": os.getcwd(),
        }
        p.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[singleton] WARNING: failed to write lock file {p}: {e}", file=sys.stderr)


def release_singleton_lock(lock_path: str) -> None:
    try:
        Path(lock_path).unlink(missing_ok=True)
    except Exception:
        pass
