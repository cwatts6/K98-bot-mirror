# run_bot.py
import json
import logging
import os
import random
import signal
import subprocess
import sys
import threading
import time
import traceback

# Constants / paths
from constants import (
    EXIT_CODE_FILE,
    LAST_RESTART_INFO,
    LAST_SHUTDOWN_INFO,
    LOG_DIR,
    RESTART_EXIT_CODE,
    RESTART_FLAG_PATH,
    RESTART_LOG_FILE,
    SHUTDOWN_MARKER_FILE,
    WATCHDOG_LOCK_PATH,
)

# Use central helpers from file_utils and utils (these modules are safe after your recent changes)
from file_utils import atomic_write_json, read_json_safe

# Use centralized logging setup (ensures UTC timestamps and consistent handlers)
from logging_setup import flush_logs, setup_logging
from utils import fmt_short, utcnow

# Prepare a watchdog-specific logfile and initialize centralized logging for this process.
WATCHDOG_LOG = os.path.join(LOG_DIR, "watchdog.log")
# Idempotent: safe to call even if logging was previously configured.
setup_logging(logfile=WATCHDOG_LOG, console_stream=sys.stdout)

log = logging.getLogger("watchdog")

# ----------------------------
# Venv enforcement + diagnostics (BEFORE taking the lock)
# ----------------------------
base_dir = os.path.abspath(os.path.dirname(__file__))
if os.name == "nt":
    expected = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    if os.path.abspath(sys.executable) != os.path.abspath(expected):
        log.error("❌ run_bot.py must be launched with: %s (got %s)", expected, sys.executable)
        sys.exit(1)

log.info(
    "[DIAG][parent] exe=%s | pid=%s | cwd=%s | WATCHDOG_RUN=%s",
    sys.executable,
    os.getpid(),
    os.getcwd(),
    os.environ.get("WATCHDOG_RUN"),
)

# ----------------------------
# Singleton lock (watchdog)
# ----------------------------
from singleton_lock import acquire_singleton_lock, release_singleton_lock

try:
    # Acquire watchdog singleton lock, but be defensive: if acquisition fails
    # (lock held or other error), log and exit with a clear code.
    try:
        acquire_singleton_lock(WATCHDOG_LOCK_PATH)
    except TimeoutError:
        log.error("Watchdog lock already held at %s; exiting.", WATCHDOG_LOCK_PATH)
        sys.exit(0)
    except Exception as e:
        log.exception("Failed to acquire watchdog lock (%s): %s", WATCHDOG_LOCK_PATH, e)
        sys.exit(1)
except Exception as e:
    # If the singleton_lock module itself is missing or raises, fail loudly.
    log.exception("Critical: unable to initialize watchdog lock: %s", e)
    sys.exit(1)


# --- Parent process exception fallbacks (watchdog) ---
def _sys_excepthook(exc_type, exc, tb):
    log.critical("FATAL: %s", "".join(traceback.format_exception(exc_type, exc, tb)).rstrip())


sys.excepthook = _sys_excepthook

try:

    def _threading_excepthook(args):
        log.critical(
            "FATAL THREAD: %s",
            "".join(
                traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
            ).rstrip(),
        )

    threading.excepthook = _threading_excepthook  # Py 3.8+
except Exception:
    pass


# ----------------------------
# Helpers
# ----------------------------
def log_restart(reason: str, status: str) -> None:
    try:
        # Use repo-wide utcnow() for consistent timezone-aware timestamps
        with open(RESTART_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{utcnow().isoformat()},{reason},SYSTEM,{status}\n")
        log.info("Logged restart: reason=%s status=%s", reason, status)
    except Exception as e:
        log.warning("Failed to log restart: %s", e)


def get_exit_code_file(max_attempts=5, delay=1) -> int | None:
    """Best-effort read of EXIT_CODE_FILE (parent/child protocol)."""
    for attempt in range(max_attempts):
        if os.path.exists(EXIT_CODE_FILE):
            try:
                with open(EXIT_CODE_FILE, encoding="utf-8") as f:
                    raw = f.read().strip()
                    code = int(raw) if raw != "" else None
                os.remove(EXIT_CODE_FILE)
                log.info("Detected .exit_code override from file: %s", code)
                return code
            except PermissionError:
                log.info("Attempt %s: .exit_code locked; retrying in %ss...", attempt + 1, delay)
                time.sleep(delay)
            except Exception as e:
                log.warning("Failed to read .exit_code: %s", e)
                break
    return None


def wait_for_restart_flag(timeout=5) -> bool:
    """Wait briefly for a .restart_flag to appear (manual restart workflow)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(RESTART_FLAG_PATH):
            log.info(".restart_flag detected")
            try:
                with open(RESTART_FLAG_PATH, encoding="utf-8") as f:
                    log.info("Restart flag contents: %s", f.read().strip())
            except Exception as e:
                log.warning("Failed to read restart flag: %s", e)
            return True
        time.sleep(0.2)
    log.info(".restart_flag not detected in %ss", timeout)
    return False


def read_restart_flag_metadata():
    """
    Safely read .restart_flag JSON using central file_utils.read_json_safe.
    Returns (timestamp, user_id, reason) with 'unknown' defaults on error.
    """
    try:
        data = read_json_safe(RESTART_FLAG_PATH, default={}) or {}
        if not isinstance(data, dict):
            return "unknown", "unknown", "unknown"
        return (
            data.get("timestamp", "unknown"),
            data.get("user_id", "unknown"),
            data.get("reason", "unknown"),
        )
    except Exception as e:
        log.warning("Failed to read .restart_flag metadata: %s", e)
        return "unknown", "unknown", "unknown"


def resolve_python_bin() -> str:
    """Pick the best Python interpreter to launch the child bot."""
    win_path = os.path.join(base_dir, "venv", "Scripts", "python.exe")
    nix_path1 = os.path.join(base_dir, "venv", "bin", "python3")
    nix_path2 = os.path.join(base_dir, "venv", "bin", "python")
    if os.name == "nt" and os.path.exists(win_path):
        return win_path
    if os.name != "nt" and os.path.exists(nix_path1):
        return nix_path1
    if os.name != "nt" and os.path.exists(nix_path2):
        return nix_path2
    return sys.executable or "python"


def child_env_utf8() -> dict[str, str]:
    """Return a copy of env with UTF-8 enforced for the child process."""
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def safe_remove(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        log.warning("Failed to remove %s: %s", path, e)


def write_last_restart_info(timestamp: str, user_id: str, reason: str) -> None:
    try:
        atomic_write_json(
            LAST_RESTART_INFO, {"timestamp": timestamp, "user_id": user_id, "reason": reason}
        )
    except Exception as e:
        log.warning("Failed to write LAST_RESTART_INFO: %s", e)


# ----------------------------
# Parent signal handling (forwarding shutdown intent)
# ----------------------------
_current_child: subprocess.Popen | None = None
_parent_shutdown = False


def _parent_signal_handler(signum, _frame):
    global _parent_shutdown
    _parent_shutdown = True
    sig_name = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}.get(signum, str(signum))
    log.info("Parent received %s — requesting graceful shutdown.", sig_name)
    try:
        with open(SHUTDOWN_MARKER_FILE, "w", encoding="utf-8") as f:
            f.write(f"parent_signal:{sig_name}")
    except Exception as e:
        log.warning("Failed to write SHUTDOWN_MARKER_FILE: %s", e)

    child = _current_child
    if child and child.poll() is None:
        try:
            log.info("Terminating child PID %s", child.pid)
            child.terminate()
        except Exception as e:
            log.warning("Failed to terminate child: %s", e)


signal.signal(signal.SIGINT, _parent_signal_handler)
try:
    signal.signal(signal.SIGTERM, _parent_signal_handler)
except Exception:
    pass  # SIGTERM may not exist on some platforms

# ----------------------------
# Previous graceful shutdown info (if any)
# ----------------------------
if os.path.exists(LAST_SHUTDOWN_INFO):
    try:
        with open(LAST_SHUTDOWN_INFO, encoding="utf-8") as f:
            shutdown_data = json.load(f)
        log.info("Detected previous graceful shutdown: %s", shutdown_data)
        log_restart("scheduled", "graceful")
    except Exception as e:
        log.warning("Failed to read LAST_SHUTDOWN_INFO: %s", e)

# ----------------------------
# Main supervision loop
# ----------------------------
backoff_seconds = 1
BACKOFF_CAP = 60
HEALTHY_SECONDS = 300
CRASH_WINDOW_SEC = 60
CRASH_THRESHOLD = 5
COOLDOWN_AFTER_STORM = 60

recent_crashes: list[float] = []
pid_path = os.path.join(base_dir, "bot_pid.txt")

# Child log handle (optional) - set when launching each child
_child_log_fh = None

try:
    while True:
        bot_path = os.path.join(base_dir, "DL_bot.py")
        python_bin = resolve_python_bin()

        log.info("Launching %s with interpreter: %s", bot_path, python_bin)

        # Prepare optional child stdout/stderr redirection
        child_log_path = os.getenv("WATCHDOG_CHILD_LOG")  # if set, append child output here
        child_log_fh = None
        if child_log_path:
            try:
                os.makedirs(os.path.dirname(child_log_path) or ".", exist_ok=True)
                child_log_fh = open(child_log_path, "a", encoding="utf-8")
                log.info("Child stdout/stderr redirected to %s", child_log_path)
            except Exception as e:
                child_log_fh = None
                log.warning("Failed to open WATCHDOG_CHILD_LOG %s: %s", child_log_path, e)

        # Start child process
        try:
            env = child_env_utf8()
            env["WATCHDOG_RUN"] = "1"
            env["WATCHDOG_PARENT_PID"] = str(os.getpid())

            child = subprocess.Popen(
                [python_bin, bot_path],
                env=env,
                cwd=base_dir,  # stable CWD for child
                stdout=child_log_fh or None,
                stderr=child_log_fh or None,
                # close_fds=True,  # posix-only (optional)
            )
            _current_child = child
        except Exception as e:
            log.error("Failed to start DL_bot.py with %s: %s", python_bin, e, exc_info=True)
            # Close file handle if open
            try:
                if child_log_fh:
                    child_log_fh.close()
            except Exception:
                pass
            time.sleep(5)
            continue

        # Save PID (atomic)
        try:
            tmp_path = pid_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(str(child.pid))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, pid_path)
            log.info("Child PID %s written to %s", child.pid, pid_path)
        except Exception as e:
            log.warning("Failed to write %s: %s", pid_path, e)

        start_ts = time.time()
        exit_code = child.wait()  # block until child exits
        # Ensure any child log buffers are flushed
        try:
            if child_log_fh:
                child_log_fh.flush()
                child_log_fh.close()
        except Exception:
            pass
        run_seconds = time.time() - start_ts
        log.info(
            "Subprocess (PID %s) exited with code %s after %.1fs", child.pid, exit_code, run_seconds
        )

        # Override/clarify via .exit_code
        file_exit_code = get_exit_code_file()
        if file_exit_code is not None:
            exit_code = file_exit_code
            log.info("Using overridden exit code from .exit_code: %s", exit_code)

        # PID file no longer valid
        safe_remove(pid_path)

        # Shutdown marker from child/parent
        if os.path.exists(SHUTDOWN_MARKER_FILE):
            try:
                with open(SHUTDOWN_MARKER_FILE, encoding="utf-8") as f:
                    reason_text = f.read().strip()
                log.info("Shutdown marker reason: %s", reason_text)
            except Exception as e:
                log.warning("Failed to read shutdown marker: %s", e)
            finally:
                safe_remove(SHUTDOWN_MARKER_FILE)
            log_restart("scheduled", "graceful")
            break

        # Planned restart (RESTART_EXIT_CODE + restart flag)
        if exit_code == RESTART_EXIT_CODE:
            if wait_for_restart_flag():
                timestamp, user_id, reason = read_restart_flag_metadata()
                log.info("Detected planned restart (exit code %s)", RESTART_EXIT_CODE)
                log.info("Restart at %s by user %s (reason: %s)", timestamp, user_id, reason)
                try:
                    safe_remove(RESTART_FLAG_PATH)
                    write_last_restart_info(timestamp, user_id, reason)
                except Exception as e:
                    log.warning("Failed handling restart flag cleanup: %s", e)
                log_restart("manual", "success")
            else:
                log.warning(
                    "Exit code %s without .restart_flag — counting as crash", RESTART_EXIT_CODE
                )
                log_restart("crash", "exit_15_no_flag")

        # Graceful file-based exit
        elif exit_code == 0:
            log_restart("scheduled", "graceful")
            break

        else:
            log.error("Bot crashed (exit code %s) — initiating recovery", exit_code)
            log_restart("crash", "crash_recovery")

        # Crash handling: backoff + storm control
        now = time.time()
        recent_crashes = [t for t in recent_crashes if now - t <= CRASH_WINDOW_SEC]
        recent_crashes.append(now)

        if len(recent_crashes) >= CRASH_THRESHOLD:
            crash_count_str = fmt_short(len(recent_crashes))
            log.error(
                "Crash storm detected (%s crashes in %ss). Cooling down for %ss.",
                crash_count_str,
                CRASH_WINDOW_SEC,
                COOLDOWN_AFTER_STORM,
            )
            flush_logs()
            time.sleep(COOLDOWN_AFTER_STORM)
            recent_crashes.clear()
            backoff_seconds = 1  # reset after cooldown
        else:
            backoff_seconds = (
                1 if run_seconds >= HEALTHY_SECONDS else min(BACKOFF_CAP, backoff_seconds * 2)
            )
            sleep_for = backoff_seconds + random.uniform(0, 0.5 * backoff_seconds)
            log.info("Backing off for %.1fs before restart.", sleep_for)
            flush_logs()
            time.sleep(sleep_for)

        # Parent asked to shut down
        if _parent_shutdown:
            log.info("Parent shutdown requested; exiting watchdog loop.")
            break
finally:
    # Cleanup on final exit
    safe_remove(pid_path)
    flush_logs()
    try:
        release_singleton_lock(WATCHDOG_LOCK_PATH)
    except Exception:
        pass
    log.info("Watchdog exiting. Goodbye.")
