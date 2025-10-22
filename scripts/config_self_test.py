#!/usr/bin/env python3
"""
Minimal config self-test.
- Does NOT print secrets or IDs; only status.
- Exits 0 on success, 1 on any error.
"""

import os
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

errors = []


def env_exists(name: str) -> bool:
    return os.getenv(name) not in (None, "")


def require(name: str, redact_len: bool = False):
    if not env_exists(name):
        errors.append(f"Missing required variable: {name}")
    elif redact_len:
        val = os.getenv(name, "")
        print(f"✔ {name}: present (len={len(val)})")


def check_int(name: str, allow_zero: bool = False):
    raw = os.getenv(name, "")
    if raw == "":
        errors.append(f"{name}: missing")
        return
    try:
        v = int(raw)
        if not allow_zero and v == 0:
            errors.append(f"{name}: must be a non-zero integer")
        else:
            print(f"✔ {name}: OK ({'0 allowed' if allow_zero else 'non-zero'})")
    except ValueError:
        errors.append(f"{name}: must be an integer (got {raw!r})")


def check_list_int(name: str):
    raw = os.getenv(name, "")
    if raw.strip() == "":
        print(f"ℹ {name}: empty (OK if not used)")
        return
    bad = [p for p in [s.strip() for s in raw.split(",")] if not p.isdigit()]
    if bad:
        errors.append(f"{name}: non-integer entries found: {bad}")
    else:
        print(f"✔ {name}: OK (comma-separated ints)")


def check_bool(name: str):
    raw = os.getenv(name, "")
    if raw == "":
        print(f"ℹ {name}: empty -> defaults handled in code (OK)")
        return
    if raw.strip().lower() in ("1", "true", "yes", "on", "y", "0", "false", "no", "off", "n"):
        print(f"✔ {name}: OK (bool-ish)")
    else:
        errors.append(f"{name}: must be a boolean string (true/false/1/0/etc). Got {raw!r}")


def check_path(name: str):
    raw = os.getenv(name, "")
    if raw == "":
        print(f"ℹ {name}: empty (using default path in code)")
        return
    p = (ROOT / raw) if not os.path.isabs(raw) else Path(raw)
    if p.exists():
        print(f"✔ {name}: file found at {p}")
    else:
        print(f"ℹ {name}: {p} not found (OK if you use another creds method)")


print("== Required secrets ==")
require("DISCORD_BOT_TOKEN", redact_len=True)

print("\n== Required SQL config (if DB features used) ==")
require("SQL_SERVER")
require("SQL_DATABASE")
require("SQL_USERNAME")
require("SQL_PASSWORD")

print("\n== Discord IDs (ints) ==")
for key in [
    "GUILD_ID",
    "ADMIN_USER_ID",
    "NOTIFY_CHANNEL_ID",
    "STATUS_CHANNEL_ID",
    "DELETE_AFTER_DOWNLOAD_CHANNEL_ID",
    "LEADERSHIP_CHANNEL_ID",
    "LOCATION_CHANNEL_ID",
    "PROKINGDOM_CHANNEL_ID",
    "PREKVK_CHANNEL_ID",
    "HONOR_CHANNEL_ID",
    "STATS_ALERT_CHANNEL_ID",
    "KVK_EVENT_CHANNEL_ID",
    "KVK_NOTIFICATION_CHANNEL_ID",
    "OFFSEASON_STATS_CHANNEL_ID",
    "FORT_RALLY_CHANNEL_ID",
    "ACTIVITY_UPLOAD_CHANNEL_ID",
    "PLAYER_LOCATION_CHANNEL_ID",
    "OUR_KINGDOM",
]:
    # allow_zero for optional channels you set to 0 when unused
    allow_zero = key in {
        "OFFSEASON_STATS_CHANNEL_ID",
        "FORT_RALLY_CHANNEL_ID",
        "ACTIVITY_UPLOAD_CHANNEL_ID",
        "PLAYER_LOCATION_CHANNEL_ID",
    }
    if env_exists(key):
        check_int(key, allow_zero=allow_zero)
    else:
        print(f"ℹ {key}: missing (OK if not used)")

print("\n== Lists / toggles ==")
check_list_int("LEADERSHIP_ROLE_IDS")
# Names can be any string; skip strict check
check_list_int("MONITOR_CHANNEL_IDS")
check_bool("SHOW_KVK_BANNER")
check_bool("SHOW_PROFILE_AVATAR_IN_CARD")
check_bool("KVK_AUTO_EXPORT")

print("\n== Google credentials / IDs ==")
check_path("GOOGLE_CREDENTIALS_FILE")
for key in [
    "GOOGLE_KINGDOM_SUMMARY_ID",
    "GOOGLE_KVK_LIST_ID",
    "GOOGLE_TARGETS_ID",
    "GOOGLE_TIMELINE_ID",
    "GOOGLE_STATS_ID",
    "KVK_SHEET_ID",
    "KVK_SHEET_NAME",
]:
    if env_exists(key):
        print(f"✔ {key}: present")
    else:
        print(f"ℹ {key}: not set (OK if feature not used)")

print("\n== ODBC driver ==")
print(f"ℹ ODBC_DRIVER={os.getenv('ODBC_DRIVER','(default in code)')}")

if errors:
    print("\n❌ CONFIG ERRORS:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("\n✅ Config looks good!")
