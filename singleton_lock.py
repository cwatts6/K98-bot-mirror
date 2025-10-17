# singleton_lock.py
import json
import os
from pathlib import Path
import sys
import time

try:
    import psutil  # optional but nice to have
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
    # Fallback heuristic if psutil isn't available
    try:
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
            if _pid_alive(pid):
                print(f"[singleton] Another instance is running (PID {pid}). Exiting.")
                sys.exit(0)
        except Exception:
            # corrupted / unreadable → treat as stale
            pass
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    try:
        p.write_text(
            json.dumps({"pid": os.getpid(), "created": time.time()}, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"[singleton] WARNING: failed to write lock file {p}: {e}", file=sys.stderr)


def release_singleton_lock(lock_path: str) -> None:
    try:
        Path(lock_path).unlink(missing_ok=True)
    except Exception:
        pass
