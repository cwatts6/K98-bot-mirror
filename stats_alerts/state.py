# stats_alerts/state.py
import logging
from pathlib import Path
from typing import Any

from constants import STATS_ALERT_LOG
from file_utils import acquire_lock, atomic_write_json, read_json_safe, resolve_path

logger = logging.getLogger(__name__)

# Single file beside the CSV log to preserve original layout and make migration simple.
STATE_PATH = f"{resolve_path(STATS_ALERT_LOG)!s}.state.json"
_STATE_LOCK_PATH = f"{STATE_PATH}.lock"
_LOCK_TIMEOUT_SECS = 5.0


def _repair_empty_state_file() -> bool:
    """Rewrite an empty/whitespace state file as a valid empty JSON object."""
    path = Path(STATE_PATH)
    if not path.exists():
        return False

    try:
        with acquire_lock(_STATE_LOCK_PATH, timeout=_LOCK_TIMEOUT_SECS):
            if not path.exists():
                return False

            try:
                raw = path.read_text(encoding="utf-8")
            except Exception:
                logger.exception("[STATE] Failed reading state file %s for repair.", STATE_PATH)
                return False

            if raw.strip():
                return False

            atomic_write_json(path, {})
            logger.warning(
                "[STATE] State file %s was empty; repaired with an empty JSON object.",
                STATE_PATH,
            )
            return True
    except TimeoutError:
        logger.warning(
            "[STATE] Timeout acquiring state lock while checking empty state file %s.",
            STATE_PATH,
        )
        return False
    except Exception:
        logger.exception("[STATE] Failed checking empty state file %s.", STATE_PATH)
        return False


def load_state() -> dict[str, Any]:
    """
    Load persisted state from JSON file.

    Returns an empty dict if the file does not exist or cannot be parsed.
    Uses file_utils.read_json_safe which logs JSON errors and returns a default.
    """
    try:
        if _repair_empty_state_file():
            return {}

        data = read_json_safe(STATE_PATH, default={})
        if isinstance(data, dict):
            return data
        # If file contains something other than a dict, return empty dict but log a warning.
        logger.warning(
            "[STATE] State file %s did not contain a JSON object; returning empty dict.", STATE_PATH
        )
        return {}
    except Exception:
        logger.exception("[STATE] Unexpected error loading state; returning empty dict.")
        return {}


def save_state(state: dict[str, Any]) -> None:
    """
    Persist state to disk atomically.

    - Uses acquire_lock to avoid concurrent writers (simple cross-process guard).
    - Uses atomic_write_json for safe writes (write to temp + rename).
    """
    try:
        # Use a short lock to avoid races; atomic_write_json itself is atomic on POSIX.
        with acquire_lock(_STATE_LOCK_PATH, timeout=_LOCK_TIMEOUT_SECS):
            atomic_write_json(STATE_PATH, state)
    except TimeoutError:
        logger.exception(
            "[STATE] Timeout acquiring state lock; save_state aborted for %s", STATE_PATH
        )
    except Exception:
        logger.exception("[STATE] Failed to persist state to %s", STATE_PATH)
