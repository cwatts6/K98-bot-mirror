# logging_setup.py
import atexit
import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
import os
import queue
import sys
import threading
import time

from constants import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)  # 🔐 safe fallback

#
# Never let logging raise in production (prevents obscure crashes)
logging.raiseExceptions = False

# Keep references to the original stdio streams (before any redirection)
ORIG_STDOUT = sys.stdout
ORIG_STDERR = sys.stderr


# === UTF-8 console helper (for emoji/icons) ===
def ensure_utf8_console():
    """
    Force UTF-8 output so emoji/icons (✅ ❌ etc.) render correctly.
    Safe no-op on non-Windows or already-UTF8 terminals.
    """
    try:
        os.environ.setdefault("PYTHONUTF8", "1")
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
        if os.name == "nt":
            try:
                import ctypes

                ctypes.windll.kernel32.SetConsoleOutputCP(65001)
                ctypes.windll.kernel32.SetConsoleCP(65001)
            except Exception:
                # Older terminals may not support this
                pass
    except Exception as e:
        logging.debug(f"[UTF8] Console UTF-8 setup skipped: {e}")


ensure_utf8_console()


# === Safe Rotating File Handler (stdlib) ===
class SafeRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler wrapped to avoid raising during rollover/emit."""

    def _eprint(self, msg: str):
        try:
            sys.__stderr__.write(msg + "\n")
            sys.__stderr__.flush()
        except Exception:
            try:
                os.write(2, (msg + "\n").encode("utf-8", errors="replace"))
            except Exception:
                pass

    def doRollover(self):
        try:
            super().doRollover()
        except Exception as e:
            self._eprint(f"[LOGGING] Rollover issue: {e}")

    def emit(self, record):
        try:
            super().emit(record)
            try:
                self.flush()
            except Exception as fe:
                self._eprint(f"[LOGGING] Flush failed: {fe}")
        except Exception as e:
            self._eprint(f"[LOGGING] Emit failed: {e}")


# === Log File Paths ===
ERROR_LOG_PATH = os.path.join(LOG_DIR, "error_log.txt")
FULL_LOG_PATH = os.path.join(LOG_DIR, "log.txt")
CRASH_LOG_PATH = os.path.join(LOG_DIR, "crash.log")

# === Formatter ===
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# === Root Logger Setup & shared queue/listener ===
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.captureWarnings(True)
_LOG_QUEUE: "queue.SimpleQueue[logging.LogRecord]" = queue.SimpleQueue()
_LISTENER: QueueListener | None = None
# Idempotent shutdown state
_LISTENER_LOCK = threading.Lock()
_IS_SHUT_DOWN = False


def _build_file_handlers():
    error_h = SafeRotatingFileHandler(
        ERROR_LOG_PATH, maxBytes=3_000_000, backupCount=5, encoding="utf-8", delay=True
    )
    error_h.setLevel(logging.WARNING)
    error_h.setFormatter(formatter)
    error_h.is_our_error_rotator = True

    full_h = SafeRotatingFileHandler(
        FULL_LOG_PATH, maxBytes=3_000_000, backupCount=5, encoding="utf-8", delay=True
    )
    full_h.setLevel(logging.INFO)
    full_h.setFormatter(formatter)
    full_h.is_our_full_rotator = True

    crash_h = SafeRotatingFileHandler(
        CRASH_LOG_PATH, maxBytes=2_000_000, backupCount=3, encoding="utf-8", delay=True
    )
    crash_h.setLevel(logging.ERROR)
    crash_h.setFormatter(formatter)
    crash_h.is_our_crash_rotator = True
    return error_h, full_h, crash_h


# === Queue-based non-blocking setup ===
def _ensure_queue_logging():
    global _LISTENER
    if any(isinstance(h, QueueHandler) for h in logger.handlers):
        return
    qh = QueueHandler(_LOG_QUEUE)
    qh.is_our_queue = True
    logger.addHandler(qh)
    # Listener owns the file handlers; no StreamHandler by default
    error_h, full_h, crash_h = _build_file_handlers()
    _LISTENER = QueueListener(_LOG_QUEUE, error_h, full_h, crash_h, respect_handler_level=True)
    _LISTENER.start()


_ensure_queue_logging()


# === Capture Uncaught Exceptions ===
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logging.critical("💥 Uncaught Exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_uncaught_exception


# === Redirect stdout/stderr to logging ===
class StreamToLogger:
    def __init__(self, logger_obj, level):
        self.logger = logger_obj
        self.level = level

    def write(self, message):
        if not message:
            return
        for line in message.rstrip().splitlines():
            if line.strip():
                self.logger.log(self.level, line.rstrip())

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):  # some libs call flush frequently
        pass

    def isatty(self):
        return False


# Redirect AFTER handlers are set up; console handler keeps ORIG_STDOUT
# NOTE: We still redirect prints to logging (non-blocking via queue).
sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)


# === Explicit Flush Utility ===
def flush_logs():
    try:
        # Listener owns file handlers; flush them too
        if _LISTENER and getattr(_LISTENER, "handlers", None):
            for h in list(_LISTENER.handlers):
                try:
                    h.flush()
                except Exception:
                    pass
    except Exception:
        pass


# === Clear Lock files on Startup ===
def clean_old_lock_files(log_dir, age_seconds=3600):
    now = time.time()
    removed_files, kept_files = [], []

    try:
        filenames = os.listdir(log_dir)
    except Exception as e:
        logging.info(f"[LOCK_FILES] Skipping cleanup; cannot list directory: {e}")
        return []

    # Only touch our legacy *.lock files; leave .lck alone
    lock_paths = [os.path.join(log_dir, f) for f in filenames if f.endswith(".lock")]
    if not lock_paths:
        logging.info("[LOCK_FILES] No legacy .lock files found.")
        return []

    for path in lock_paths:
        try:
            file_age = now - os.path.getmtime(path)
            file_size = os.path.getsize(path)
            if file_age <= age_seconds and file_size > 0:
                kept_files.append(path)
                continue

            # Probe: try exclusive open to see if it's actually free
            try:
                with open(path, "a"):
                    pass
            except Exception:
                kept_files.append(path)
                continue

            try:
                os.remove(path)
                removed_files.append(path)
            except Exception:
                kept_files.append(path)
        except Exception:
            kept_files.append(path)

    logging.info(
        f"[LOCK_FILES] Cleanup Summary: Removed {len(removed_files)} | Kept {len(kept_files)}"
    )
    return removed_files


def configure_logging(level=logging.INFO):
    root = logging.getLogger()
    root.setLevel(level)

    # Stop & remove existing listener if any
    global _LISTENER
    if _LISTENER:
        try:
            _LISTENER.stop()
        except Exception:
            pass
        _LISTENER = None

    # Remove existing handlers (queue + any residual)
    for h in list(root.handlers):
        try:
            root.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass
        except Exception:
            pass

    # Rebuild queue + file handlers
    _ensure_queue_logging()

    # Optional console echo (DANGEROUS for event loop; keep off by default)
    if os.environ.get("LOG_TO_CONSOLE") == "1":
        sh = logging.StreamHandler(stream=ORIG_STDOUT)
        sh.setFormatter(formatter)
        sh.setLevel(level)
        sh.is_our_console = True
        root.addHandler(sh)


def shutdown_logging():
    """Idempotent stop/flush/close to release file locks (safe to call multiple times)."""
    global _IS_SHUT_DOWN, _LISTENER
    with _LISTENER_LOCK:
        if _IS_SHUT_DOWN:
            return
        try:
            root = logging.getLogger()
            # Stop listener first so file handlers flush/close cleanly
            if _LISTENER:
                try:
                    _LISTENER.stop()
                except Exception:
                    pass
                _LISTENER = None

            # Flush/close root handlers
            for h in list(root.handlers):
                try:
                    h.flush()
                except Exception:
                    pass
            for h in list(root.handlers):
                try:
                    h.close()
                except Exception:
                    pass
                try:
                    root.removeHandler(h)
                except Exception:
                    pass

            # Flush/close all named logger handlers
            for name in list(logging.Logger.manager.loggerDict.keys()):
                lg = logging.getLogger(name)
                for h in list(getattr(lg, "handlers", ())):
                    try:
                        h.flush()
                    except Exception:
                        pass
                for h in list(getattr(lg, "handlers", ())):
                    try:
                        h.close()
                    except Exception:
                        pass
                    try:
                        lg.removeHandler(h)
                    except Exception:
                        pass
        finally:
            _IS_SHUT_DOWN = True


# Ensure the listener is always closed on interpreter exit (Windows-safe)
atexit.register(shutdown_logging)


# === Exported ===
__all__ = [
    "LOG_DIR",
    "clean_old_lock_files",
    "configure_logging",
    "ensure_utf8_console",
    "flush_logs",
    "shutdown_logging",
]
