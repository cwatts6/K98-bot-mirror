# run_bot.py
from datetime import UTC, datetime
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

from constants import (
    EXIT_CODE_FILE,
    LAST_RESTART_INFO,
    LAST_SHUTDOWN_INFO,
    LOG_DIR,
    RESTART_FLAG_PATH,
    RESTART_LOG_FILE,
    SHUTDOWN_MARKER_FILE,
    WATCHDOG_LOCK_PATH,
)
from logging_setup import flush_logs

# ----------------------------
# Logging
# ----------------------------
WATCHDOG_LOG = os.path.join(LOG_DIR, "watchdog.log")

# Provide a standard UTC constant
UTC = UTC


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("watchdog")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [WATCHDOG] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (best-effort)
    try:
        fh = logging.FileHandler(WATCHDOG_LOG, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    # Stdout handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


log = _setup_logger()

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

acquire_singleton_lock(WATCHDOG_LOCK_PATH)


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
        with open(RESTART_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(UTC).isoformat()},{reason},SYSTEM,{status}\n")
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
    try:
        with open(RESTART_FLAG_PATH, encoding="utf-8") as f:
            data = json.load(f)
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
    nix_path = os.path.join(base_dir, "venv", "bin", "python3")
    if os.name == "nt" and os.path.exists(win_path):
        return win_path
    if os.name != "nt" and os.path.exists(nix_path):
        return nix_path
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
        with open(LAST_RESTART_INFO, "w", encoding="utf-8") as f:
            json.dump({"timestamp": timestamp, "user_id": user_id, "reason": reason}, f)
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

try:
    while True:
        bot_path = os.path.join(base_dir, "DL_bot.py")
        python_bin = resolve_python_bin()

        log.info("Launching %s with interpreter: %s", bot_path, python_bin)

        # Start child process
        try:
            env = child_env_utf8()
            env["WATCHDOG_RUN"] = "1"
            env["WATCHDOG_PARENT_PID"] = str(os.getpid())

            child = subprocess.Popen(
                [python_bin, bot_path],
                env=env,
                cwd=base_dir,  # stable CWD for child
                # close_fds=True,  # posix-only (optional)
            )
            _current_child = child
        except Exception as e:
            log.error("Failed to start DL_bot.py with %s: %s", python_bin, e, exc_info=True)
            time.sleep(5)
            continue

        # Save PID (atomic)
        try:
            tmp_path = pid_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(str(child.pid))
            os.replace(tmp_path, pid_path)
            log.info("Child PID %s written to %s", child.pid, pid_path)
        except Exception as e:
            log.warning("Failed to write %s: %s", pid_path, e)

        start_ts = time.time()
        exit_code = child.wait()  # block until child exits
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

        # Planned restart (SIGTERM 15 + restart flag)
        if exit_code == 15:
            if wait_for_restart_flag():
                timestamp, user_id, reason = read_restart_flag_metadata()
                log.info("Detected planned restart (exit code 15)")
                log.info("Restart at %s by user %s (reason: %s)", timestamp, user_id, reason)
                try:
                    safe_remove(RESTART_FLAG_PATH)
                    write_last_restart_info(timestamp, user_id, reason)
                except Exception as e:
                    log.warning("Failed handling restart flag cleanup: %s", e)
                log_restart("manual", "success")
            else:
                log.warning("Exit code 15 without .restart_flag — counting as crash")
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
            log.error(
                "Crash storm detected (%s crashes in %ss). Cooling down for %ss.",
                len(recent_crashes),
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
