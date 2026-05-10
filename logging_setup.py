# logging_setup.py
import atexit
import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
import os
from pathlib import Path
import queue
import sys
import threading
import time

from constants import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)  # 🔐 safe fallback

# Never let logging raise in production (prevents obscure crashes)
logging.raiseExceptions = False

# Keep references to the original stdio streams (before any redirection)
ORIG_STDOUT = sys.stdout
ORIG_STDERR = sys.stderr

# --- Configurable rotation defaults (can be overridden via setup_logging)
_LOG_MAX_BYTES = 3_000_000
_LOG_BACKUP_COUNT = 5


# === UTF-8 console helper (for emoji/icons) ===
def ensure_utf8_console():
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
TELEMETRY_LOG_PATH = os.path.join(LOG_DIR, "telemetry_log.jsonl")  # NEW


# === Formatter (UTC) ===
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
try:
    formatter.converter = time.gmtime
except Exception:
    pass


# === Root Logger Setup & shared queue/listener ===
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.captureWarnings(True)
_LOG_QUEUE: "queue.SimpleQueue[logging.LogRecord]" = queue.SimpleQueue()
_LISTENER: QueueListener | None = None
# Idempotent shutdown state
_LISTENER_LOCK = threading.Lock()
_IS_SHUT_DOWN = False


# === Filters to route telemetry cleanly ===
class OnlyTelemetryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # send only 'telemetry' logger records to the telemetry file
        return record.name == "telemetry"


class ExcludeTelemetryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # exclude telemetry JSON lines from normal logs
        return record.name != "telemetry"


def _build_file_handlers(max_bytes: int = None, backup_count: int = None):
    """
    Build the file handlers using configured rotation params.
    The formatter already enforces UTC timestamps.
    Returns: (error_h, full_h, crash_h, telemetry_h)
    """
    mb = _LOG_MAX_BYTES if max_bytes is None else max_bytes
    bc = _LOG_BACKUP_COUNT if backup_count is None else backup_count

    error_h = SafeRotatingFileHandler(
        ERROR_LOG_PATH, maxBytes=mb, backupCount=bc, encoding="utf-8", delay=True
    )
    error_h.setLevel(logging.WARNING)
    error_h.setFormatter(formatter)
    error_h.addFilter(ExcludeTelemetryFilter())
    error_h.is_our_error_rotator = True

    full_h = SafeRotatingFileHandler(
        FULL_LOG_PATH, maxBytes=mb, backupCount=bc, encoding="utf-8", delay=True
    )
    full_h.setLevel(logging.INFO)
    full_h.setFormatter(formatter)
    full_h.addFilter(ExcludeTelemetryFilter())
    full_h.is_our_full_rotator = True

    crash_h = SafeRotatingFileHandler(
        CRASH_LOG_PATH,
        maxBytes=max(1_000_000, mb // 2),
        backupCount=max(1, bc // 2),
        encoding="utf-8",
        delay=True,
    )
    crash_h.setLevel(logging.ERROR)
    crash_h.setFormatter(formatter)
    crash_h.addFilter(ExcludeTelemetryFilter())
    crash_h.is_our_crash_rotator = True

    # NEW telemetry handler (JSON lines emitted by telemetry logger)
    telemetry_h = SafeRotatingFileHandler(
        TELEMETRY_LOG_PATH, maxBytes=mb, backupCount=bc, encoding="utf-8", delay=True
    )
    telemetry_h.setLevel(logging.INFO)
    telemetry_h.setFormatter(formatter)
    telemetry_h.addFilter(OnlyTelemetryFilter())
    telemetry_h.is_our_telemetry_rotator = True

    return error_h, full_h, crash_h, telemetry_h


# === Queue-based non-blocking setup ===
def _ensure_queue_logging(max_bytes: int = None, backup_count: int = None):
    """
    Initialize queue-based logging once per process. Safe to call multiple times.
    """
    global _LISTENER
    if any(isinstance(h, QueueHandler) for h in logger.handlers):
        return
    qh = QueueHandler(_LOG_QUEUE)
    qh.is_our_queue = True
    logger.addHandler(qh)
    # Listener owns the file handlers; include telemetry handler as the 4th
    handlers = _build_file_handlers(max_bytes=max_bytes, backup_count=backup_count)
    _LISTENER = QueueListener(_LOG_QUEUE, *handlers, respect_handler_level=True)
    _LISTENER.start()


# Initialize queue logging at import time (safe and idempotent)
_ensure_queue_logging()


# === Dedicated stdio logger to avoid recursion ===
# Non-propagating logger that only writes to the queue, never to StreamHandlers
_STDIO_LOGGER = logging.getLogger("stdio")
try:
    _STDIO_LOGGER.setLevel(logging.INFO)
    _STDIO_LOGGER.propagate = False
    # Replace any existing handlers
    for _h in list(_STDIO_LOGGER.handlers):
        try:
            _STDIO_LOGGER.removeHandler(_h)
        except Exception:
            pass
    _STDIO_LOGGER.addHandler(QueueHandler(_LOG_QUEUE))
except Exception:
    # If anything fails, fall back to root (still guarded with re-entrancy)
    _STDIO_LOGGER = logger


# === Capture Uncaught Exceptions ===
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logging.critical("💥 Uncaught Exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_uncaught_exception


# Thread-local guard to avoid re-entrancy
_TL = threading.local()


# === Redirect stdout/stderr to logging (safe) ===
class StreamToLogger:
    def __init__(self, logger_obj, level):
        self.logger = logger_obj
        self.level = level

    def write(self, message):
        if not message:
            return
        # Re-entrancy guard: if we’re already inside write(), bypass logging and
        # write to the original OS streams to avoid recursion.
        if getattr(_TL, "in_write", False):
            try:
                target = ORIG_STDERR if self.level >= logging.ERROR else ORIG_STDOUT
                target.write(message)
                target.flush()
            except Exception:
                pass
            return

        try:
            _TL.in_write = True
            for line in message.rstrip().splitlines():
                if line.strip():
                    # Use the dedicated stdio logger which does not propagate to StreamHandlers
                    _STDIO_LOGGER.log(self.level, line.rstrip())
        finally:
            _TL.in_write = False

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):  # some libs call flush frequently
        try:
            (ORIG_STDERR if self.level >= logging.ERROR else ORIG_STDOUT).flush()
        except Exception:
            pass

    def isatty(self):
        return False


# Redirect AFTER handlers are set up; console handler keeps ORIG_STDOUT
# NOTE: We still redirect prints to logging (non-blocking via queue).
sys.stdout = StreamToLogger(_STDIO_LOGGER, logging.INFO)
sys.stderr = StreamToLogger(_STDIO_LOGGER, logging.ERROR)


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


def _attach_console_stream(console_stream, level=logging.INFO):
    """
    Attach an explicit console StreamHandler (to ORIG_STDOUT by default).
    This is separate from the queued file handlers. Caller must pass a file-like.
    """
    try:
        root = logging.getLogger()
        # Remove any existing console handlers we marked earlier
        for h in list(root.handlers):
            try:
                if getattr(h, "is_our_console", False):
                    root.removeHandler(h)
                    try:
                        h.close()
                    except Exception:
                        pass
            except Exception:
                pass

        if console_stream is not None:
            sh = logging.StreamHandler(stream=console_stream)
            sh.setFormatter(formatter)
            sh.setLevel(level)
            sh.is_our_console = True
            root.addHandler(sh)
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


def configure_logging(
    level=logging.INFO,
    console_stream: object | None = None,
    max_bytes: int | None = None,
    backup_count: int | None = None,
):
    """
    Reconfigure the queue listener and optionally attach a console stream.
    This function is safe to call multiple times; it will stop the existing listener
    and replace it with a fresh one using the provided rotation params.
    """
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

    # Rebuild queue + file handlers with optional rotation params
    _ensure_queue_logging(max_bytes=max_bytes, backup_count=backup_count)

    # Attach optional console echo to a specific stream (ORIG_STDOUT recommended)
    if console_stream is not None:
        _attach_console_stream(console_stream, level=level)
    elif os.environ.get("LOG_TO_CONSOLE") == "1":
        _attach_console_stream(ORIG_STDOUT, level=level)


def setup_logging(
    *,
    logfile: str | None = None,
    console_stream: object | None = None,
    level: int = logging.INFO,
    rotate: bool = True,
    max_bytes: int | None = None,
    backup_count: int | None = None,
) -> None:
    """
    Public helper to initialize logging from a process entrypoint.

    Parameters:
    - logfile: optional path to write the primary full logfile. If provided it overrides FULL_LOG_PATH.
               NOTE: queue/listener still writes ERROR_LOG_PATH, CRASH_LOG_PATH, TELEMETRY_LOG_PATH.
    - console_stream: file-like stream to attach a console handler to (e.g. sys.stdout or ORIG_STDOUT).
    - level: root logging level.
    - rotate: whether rotating file handlers should be used (True by default). If False, handlers fall back to FileHandler behavior.
    - max_bytes, backup_count: optional overrides for rotation sizes/backups.
    """
    global FULL_LOG_PATH, _LOG_MAX_BYTES, _LOG_BACKUP_COUNT

    try:
        if logfile:
            FULL_LOG_PATH = str(Path(logfile).resolve())
        if max_bytes is not None:
            _LOG_MAX_BYTES = int(max_bytes)
        if backup_count is not None:
            _LOG_BACKUP_COUNT = int(backup_count)
    except Exception:
        pass

    # configure queue & file handlers using the desired rotation params
    if rotate:
        configure_logging(
            level=level,
            console_stream=console_stream,
            max_bytes=_LOG_MAX_BYTES,
            backup_count=_LOG_BACKUP_COUNT,
        )
    else:
        # If rotate is False, simulate by setting max_bytes very large so handlers do not rotate
        configure_logging(
            level=level, console_stream=console_stream, max_bytes=10**9, backup_count=1
        )


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
    "ORIG_STDERR",
    "ORIG_STDOUT",
    "TELEMETRY_LOG_PATH",
    "clean_old_lock_files",
    "configure_logging",
    "ensure_utf8_console",
    "flush_logs",
    "setup_logging",
    "shutdown_logging",
]
