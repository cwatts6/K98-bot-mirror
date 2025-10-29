# startup_utils.py
from __future__ import annotations

import logging
import os
import shutil

from constants import (
    BASE_DIR,
    BOT_LOCK_PATH,
    COMMAND_CACHE_FILE,
    # CSVs now canonical under LOG_DIR
    CSV_LOG,
    EXIT_CODE_FILE,
    FAILED_LOG,
    # JSON trackers/caches now canonical under DATA_DIR or LOG_DIR
    INPUT_CACHE_FILE,
    INPUT_LOG,
    LAST_RESTART_INFO,
    LAST_SHUTDOWN_INFO,
    QUEUE_CACHE_FILE,
    RESTART_FLAG_PATH,
    RESTART_LOG_FILE,
    SHUTDOWN_LOG_FILE,
    SHUTDOWN_MARKER_FILE,
    STATS_ALERT_LOG,
    SUMMARY_LOG,
    WATCHDOG_LOCK_PATH,
)

logger = logging.getLogger(__name__)


def _move_if_exists(src_abs: str, dst_abs: str) -> bool:
    """
    Move a single file if it exists at src and dst doesn't exist yet.
    Returns True if moved, False otherwise.
    """
    try:
        if os.path.isfile(src_abs) and not os.path.exists(dst_abs):
            os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
            shutil.move(src_abs, dst_abs)
            logger.info("[MIGRATE] Moved legacy %s -> %s", src_abs, dst_abs)
            return True
    except Exception:
        logger.exception("[MIGRATE] Failed moving %s -> %s", src_abs, dst_abs)
    return False


def migrate_legacy_artifacts_once() -> None:
    """
    One-time migration of legacy root-level artifacts to LOG_DIR/DATA_DIR.

    Safe to call multiple times (idempotent). Logs a single line per file moved.
    """
    # Map of legacy filenames (previously at repo root) -> new absolute destination
    root_to_target = {
        # CSVs
        "download_log.csv": CSV_LOG,
        "failed_log.csv": FAILED_LOG,
        "input_log.csv": INPUT_LOG,
        "summary_log.csv": SUMMARY_LOG,
        "restart_log.csv": RESTART_LOG_FILE,  # just in case it existed at root
        "shutdown_log.csv": SHUTDOWN_LOG_FILE,  # just in case it existed at root
        "stats_alert_log.csv": STATS_ALERT_LOG,  # just in case it existed at root
        # Caches / trackers that used to live at root
        "kingdom_input_cache.json": INPUT_CACHE_FILE,
        "live_queue_cache.json": QUEUE_CACHE_FILE,
        "command_cache.json": COMMAND_CACHE_FILE,
        # Locks / markers that used to live at root
        "WATCHDOG_LOCK.json": WATCHDOG_LOCK_PATH,
        "BOT_LOCK.json": BOT_LOCK_PATH,
        "last_shutdown_info.json": LAST_SHUTDOWN_INFO,
        "last_restart.json": LAST_RESTART_INFO,
        ".exit_code": EXIT_CODE_FILE,
        ".restart_flag.json": RESTART_FLAG_PATH,
        ".shutdown_marker": SHUTDOWN_MARKER_FILE,
    }

    # Primary scan location: repository root (BASE_DIR)
    any_moved = False
    for legacy_name, dst_abs in root_to_target.items():
        src_abs = os.path.join(BASE_DIR, legacy_name)
        moved = _move_if_exists(src_abs, dst_abs)
        any_moved = any_moved or moved

    # Optional: handle very old layout where people had a stray "./logs" at BASE_DIR
    # e.g., files sitting under BASE_DIR without our constants aware of them.
    # (No-op if not present.)
    # You can expand this if you find more edge-cases in the wild.

    if any_moved:
        logger.info("[MIGRATE] Legacy artifact migration complete.")
    else:
        logger.debug("[MIGRATE] No legacy artifacts to migrate.")
