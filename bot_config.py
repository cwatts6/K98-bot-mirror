# bot_config.py (hardened)
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

# ---- REQUIRED ENV TRACKER (must exist before any use) ----
_required: set[str] = set()

# Global toggle (optional): set CONFIG_STRICT=1 to make parsing fail on bad entries
STRICT_CONFIG = os.getenv("CONFIG_STRICT", "").strip().lower() in {"1", "true", "yes"}


def _mark_required(name: str) -> None:
    """Record missing required env var without crashing at import time."""
    _required.add(name)


def _fail_if_required() -> None:
    """Call later (e.g., in scripts/validate_env.py) to fail fast if any required envs are missing."""
    if _required:
        raise RuntimeError(f"[CONFIG] Missing required env(s): {', '.join(sorted(_required))}")


def _get_env(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    """Fetch env var; if required and missing/blank, mark for later failure."""
    val = os.getenv(name, default)
    if required and (val is None or str(val).strip() == ""):
        _mark_required(name)
    return val


def _env_int(name: str, default: int = 0) -> int:
    val = os.getenv(name)
    if val is None or val == "":
        return int(default)
    try:
        return int(val)
    except ValueError:
        raise ValueError(f"[CONFIG] {name} must be an integer (got: {val!r})")


def _env_list_int(name: str, default=None, strict: bool | None = None) -> list[int]:
    """
    Parse env var as a list of ints from either:
      - JSON:  [123, "456"]
      - CSV:   123,456  (also accepts semicolons; optional surrounding [] () {})

    On bad tokens:
      * strict=True  -> raise ValueError
      * strict=False -> log a warning and skip the token
      * strict=None  -> use module-level STRICT_CONFIG
    """
    # Resolve strictness
    if strict is None:
        strict = STRICT_CONFIG

    raw = os.getenv(name, "")
    if not raw or not raw.strip():
        return [] if default is None else default

    # Try JSON first
    try:
        val = json.loads(raw)
        if isinstance(val, list):
            out: list[int] = []
            for x in val:
                s = str(x).strip()
                if not s:
                    continue
                try:
                    out.append(int(s))
                except ValueError:
                    msg = f"[CONFIG] {name} contains a non-integer entry (JSON): {s!r}"
                    if strict:
                        raise ValueError(msg)
                    logger.warning(msg + " — skipping")
            return out
        # if it's valid JSON but not a list, fall through to CSV handling
    except Exception:
        pass  # fall back to CSV

    # CSV/lenient form: allow [](){} wrappers; accept "," or ";" separators; strip quotes
    s = raw.strip().strip("[](){}")
    parts = [p.strip().strip("\"'") for p in s.replace(";", ",").split(",")]
    out: list[int] = []
    for p in parts:
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            msg = f"[CONFIG] {name} contains a non-integer entry: {p!r}"
            if strict:
                raise ValueError(msg)
            logger.warning(msg + " — skipping")

    return out


# === Core Bot Configuration ===
GUILD_ID = _env_int("GUILD_ID")
ADMIN_USER_ID = _env_int("ADMIN_USER_ID")
ADMIN_USER_MENTION = _get_env("ADMIN_USER_MENTION", "")  # e.g. "<@1234567890>"

NOTIFY_CHANNEL_ID = _env_int("NOTIFY_CHANNEL_ID")
STATUS_CHANNEL_ID = _env_int("STATUS_CHANNEL_ID")
DELETE_AFTER_DOWNLOAD_CHANNEL_ID = _env_int("DELETE_AFTER_DOWNLOAD_CHANNEL_ID")
LEADERSHIP_CHANNEL_ID = _env_int("LEADERSHIP_CHANNEL_ID")
LOCATION_CHANNEL_ID = _env_int("LOCATION_CHANNEL_ID")
PROKINGDOM_CHANNEL_ID = _env_int("PROKINGDOM_CHANNEL_ID")
PREKVK_CHANNEL_ID = _env_int("PREKVK_CHANNEL_ID")
HONOR_CHANNEL_ID = _env_int("HONOR_CHANNEL_ID")

LEADERSHIP_ROLE_IDS = _env_list_int("LEADERSHIP_ROLE_IDS")

# Split + trim names; allow empty
LEADERSHIP_ROLE_NAMES: list[str] = [
    s.strip()
    for s in _get_env("LEADERSHIP_ROLE_NAMES", "Kingdom Leadership,DHE Officers").split(",")
    if s.strip()
]

# Channels to monitor (comma-separated IDs)
CHANNEL_IDS = _env_list_int("MONITOR_CHANNEL_IDS")

FORT_RALLY_CHANNEL_ID = _env_int("FORT_RALLY_CHANNEL_ID")
ACTIVITY_UPLOAD_CHANNEL_ID = _env_int("ACTIVITY_UPLOAD_CHANNEL_ID")
PLAYER_LOCATION_CHANNEL_ID = _env_int("PLAYER_LOCATION_CHANNEL_ID")

# Required secret (record missing, don't crash here)
DISCORD_BOT_TOKEN = _get_env("DISCORD_BOT_TOKEN", required=True)

STATS_ALERT_CHANNEL_ID = _env_int("STATS_ALERT_CHANNEL_ID")

KVK_EVENT_CHANNEL_ID = _env_int("KVK_EVENT_CHANNEL_ID")
KVK_NOTIFICATION_CHANNEL_ID = _env_int("KVK_NOTIFICATION_CHANNEL_ID")
OFFSEASON_STATS_CHANNEL_ID = _env_int("OFFSEASON_STATS_CHANNEL_ID")

# Optional sanity warning (safe: does not print token)
if not all([GUILD_ID, NOTIFY_CHANNEL_ID, ADMIN_USER_ID]):
    logger.warning(
        "[CONFIG] One or more core bot config values are missing or zero. Check your .env."
    )

__all__ = [
    "ACTIVITY_UPLOAD_CHANNEL_ID",
    "ADMIN_USER_ID",
    "ADMIN_USER_MENTION",
    "CHANNEL_IDS",
    "DELETE_AFTER_DOWNLOAD_CHANNEL_ID",
    "DISCORD_BOT_TOKEN",
    "FORT_RALLY_CHANNEL_ID",
    "GUILD_ID",
    "HONOR_CHANNEL_ID",
    "KVK_EVENT_CHANNEL_ID",
    "KVK_NOTIFICATION_CHANNEL_ID",
    "LEADERSHIP_CHANNEL_ID",
    "LEADERSHIP_ROLE_IDS",
    "LEADERSHIP_ROLE_NAMES",
    "LOCATION_CHANNEL_ID",
    "NOTIFY_CHANNEL_ID",
    "OFFSEASON_STATS_CHANNEL_ID",
    "PLAYER_LOCATION_CHANNEL_ID",
    "PREKVK_CHANNEL_ID",
    "PROKINGDOM_CHANNEL_ID",
    "STATS_ALERT_CHANNEL_ID",
    "STATUS_CHANNEL_ID",
    "_fail_if_required",  # expose so scripts/validate_env.py can call it
]
