# startup_utils.py
from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil

from constants import (
    BASE_DIR,
    BOT_LOCK_PATH,
    COMMAND_CACHE_FILE,
    CSV_LOG,
    EXIT_CODE_FILE,
    FAILED_LOG,
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

# Prefer the central implementation from file_utils (now safe to import)
from file_utils import move_if_not_exists

# Central small helper from utils for compact number formatting
from utils import fmt_short


def _local_move_if_not_exists(src: Path, dst: Path) -> bool:
    """
    Local fallback to move_if_not_exists semantics if file_utils implementation is not importable.
    Moves src -> dst only if src exists and dst does not exist. Returns True if moved.
    """
    try:
        if not src.is_file():
            logger.debug("[MIGRATE] source missing or not a file: %s", src)
            return False
        if dst.exists():
            logger.debug("[MIGRATE] destination already exists, skipping: %s", dst)
            return False

        dst.parent.mkdir(parents=True, exist_ok=True)

        # Prefer atomic rename (fast on same filesystem); fall back to shutil.move
        try:
            src.rename(dst)
        except FileExistsError:
            # race: someone else created dst
            logger.warning("[MIGRATE] destination created concurrently, skipping: %s", dst)
            return False
        except OSError:
            try:
                shutil.move(str(src), str(dst))
            except FileExistsError:
                logger.warning(
                    "[MIGRATE] destination created concurrently during fallback, skipping: %s", dst
                )
                return False
            except Exception:
                logger.exception("[MIGRATE] fallback move failed for %s -> %s", src, dst)
                return False

        if dst.exists() and not src.exists():
            logger.info("[MIGRATE] Moved legacy %s -> %s", src, dst)
            return True

        logger.warning(
            "[MIGRATE] unexpected post-move state for %s -> %s (src_exists=%s dst_exists=%s)",
            src,
            dst,
            src.exists(),
            dst.exists(),
        )
        return False
    except Exception:
        logger.exception("[MIGRATE] unexpected error moving %s -> %s", src, dst)
        return False


def _move_if_exists(src_abs: str | Path, dst_abs: str | Path) -> bool:
    """
    Adapter that prefers the central file_utils.move_if_not_exists if available,
    otherwise falls back to the local resilient implementation above.
    """
    src = Path(src_abs)
    dst = Path(dst_abs)

    # Call central move_if_not_exists but guard against unexpected errors
    try:
        return move_if_not_exists(src, dst)
    except Exception:
        logger.exception(
            "[MIGRATE] central move_if_not_exists failed for %s -> %s; falling back", src, dst
        )
        return _local_move_if_not_exists(src, dst)


def migrate_legacy_artifacts_once(
    dry_run: bool = False, return_moved: bool = False
) -> None | list[str]:
    """
    One-time migration of legacy root-level artifacts to LOG_DIR/DATA_DIR.

    - Safe to call multiple times (idempotent).
    - dry_run: if True, only logs what would be moved (no filesystem changes).
    - return_moved: if True, return a list of moved destination paths (strings).
                    Otherwise returns None to preserve previous behavior.

    Migration may be disabled entirely using the environment variable:
      MIGRATE_LEGACY_ARTIFACTS=0 | false | no | off
    """
    if os.getenv("MIGRATE_LEGACY_ARTIFACTS", "1").strip().lower() in ("0", "false", "no", "off"):
        logger.debug("[MIGRATE] Migration disabled via MIGRATE_LEGACY_ARTIFACTS env")
        return [] if return_moved else None

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

    any_moved = False
    moved_list: list[str] = []

    for legacy_name, dst_abs in root_to_target.items():
        src_abs = Path(BASE_DIR) / legacy_name
        if dry_run:
            if src_abs.exists():
                logger.info("[MIGRATE][DRY] Would move %s -> %s", src_abs, dst_abs)
                moved_list.append(str(dst_abs))
            continue

        moved = _move_if_exists(src_abs, dst_abs)
        if moved:
            any_moved = True
            moved_list.append(str(dst_abs))

    if any_moved:
        try:
            count_str = fmt_short(len(moved_list))
        except Exception:
            count_str = str(len(moved_list))
        logger.info("[MIGRATE] Legacy artifact migration complete. Moved %s file(s).", count_str)
    else:
        logger.debug("[MIGRATE] No legacy artifacts to migrate.")

    if return_moved:
        return moved_list
    return None
