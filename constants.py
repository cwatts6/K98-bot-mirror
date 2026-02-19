# constants.py (hardened)
from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()


# ---------- helpers ----------
def _env_str(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    return v.strip()


def _env_required(name: str) -> str:
    v = _env_str(name)
    if not v:
        raise RuntimeError(f"[CONFIG] Required environment variable missing: {name}")
    return v


def _env_int(name: str, default: int | None = None) -> int:
    v = _env_str(name)
    if v is None:
        if default is None:
            raise RuntimeError(f"[CONFIG] Required integer env var missing: {name}")
        return int(default)
    try:
        return int(v)
    except ValueError:
        raise RuntimeError(f"[CONFIG] {name} must be an integer (got {v!r})")


def _env_bool(name: str, default: bool = True) -> bool:
    v = _env_str(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on", "y")


# ---------- base paths ----------
BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")

for _p in (LOG_DIR, DATA_DIR, DOWNLOAD_FOLDER):
    os.makedirs(_p, exist_ok=True)

# unified cache path
CACHE_FILE_PATH = os.path.join(DATA_DIR, "event_cache.json")

# ---------- trackers / state files ----------
REMINDER_TRACKING_FILE = os.path.join(DATA_DIR, "active_reminders.json")
RESTART_FLAG_PATH = os.path.join(LOG_DIR, ".restart_flag.json")
EXIT_CODE_FILE = os.path.join(LOG_DIR, ".exit_code")
RESTART_LOG_FILE = os.path.join(LOG_DIR, "restart_log.csv")
LAST_RESTART_INFO = os.path.join(LOG_DIR, "last_restart.json")
SHUTDOWN_MARKER_FILE = os.path.join(LOG_DIR, ".shutdown_marker")
SHUTDOWN_LOG_FILE = os.path.join(LOG_DIR, "shutdown_log.csv")
SHUTDOWN_LOG_PATH = os.path.join(LOG_DIR, "shutdown_log.txt")
LAST_SHUTDOWN_INFO = os.path.join(LOG_DIR, "last_shutdown_info.json")
STATS_ALERT_LOG = os.path.join(LOG_DIR, "stats_alert_log.csv")
EMBED_TRACKING_FILE = os.path.join(DATA_DIR, "live_event_embeds.json")
DAILY_KVK_OVERVIEW_TRACKER = os.path.join(DATA_DIR, "daily_overview_tracker.json")
VIEW_TRACKING_FILE = os.path.join(DATA_DIR, "view_tracker.json")
SUBSCRIPTION_FILE = os.path.join(DATA_DIR, "subscription_tracker.json")
DM_SENT_TRACKER_FILE = os.path.join(DATA_DIR, "dm_sent_tracker.json")
DM_SCHEDULED_TRACKER_FILE = os.path.join(DATA_DIR, "dm_scheduled_tracker.json")
FAILED_DM_LOG = os.path.join(DATA_DIR, "failed_dm_log.json")
REGISTRY_FILE = os.path.join(DATA_DIR, "governor_registry.json")
PLAYER_STATS_CACHE = os.path.join(DATA_DIR, "player_stats_cache.json")
PLAYER_STATS_LAST_CACHE = os.path.join(DATA_DIR, "player_stats_cache_lastkvk.json")
PLAYER_TARGETS_CACHE = os.path.join(DATA_DIR, "player_targets_cache.json")
PLAYER_PROFILE_CACHE = os.path.join(DATA_DIR, "player_profile_cache.json")

RESTART_EXIT_CODE = 15
TARGET_SCRIPT = os.path.join(BASE_DIR, "DL_bot.py").lower()

# CSV logs (now under LOG_DIR)
CSV_LOG = os.path.join(LOG_DIR, "download_log.csv")
INPUT_LOG = os.path.join(LOG_DIR, "input_log.csv")
SUMMARY_LOG = os.path.join(LOG_DIR, "summary_log.csv")
FAILED_LOG = os.path.join(LOG_DIR, "failed_log.csv")

# Runtime caches (now under DATA_DIR)
INPUT_CACHE_FILE = os.path.join(DATA_DIR, "kingdom_input_cache.json")
# Allow override via environment variable for test flexibility / runtime control
QUEUE_CACHE_FILE = os.getenv("QUEUE_CACHE_FILE", os.path.join(DATA_DIR, "live_queue_cache.json"))
COMMAND_CACHE_FILE = os.path.join(DATA_DIR, "command_cache.json")

# ---------- credentials / config ----------
CREDENTIALS_FILE_NAME = _env_str("GOOGLE_CREDENTIALS_FILE", "credentials.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, CREDENTIALS_FILE_NAME)
CONFIG_FILE = os.path.join(BASE_DIR, "config", "sheet_config.json")

# ---------- SQL (required at runtime if DB is used) ----------
SQL_SERVER = _env_str("SQL_SERVER")
SERVER = _env_str("SQL_SERVER")
SQL_DATABASE = _env_str("SQL_DATABASE")
DATABASE = _env_str("SQL_DATABASE")
SQL_USERNAME = _env_str("SQL_USERNAME")
USERNAME = _env_str("SQL_USERNAME")
SQL_PASSWORD = _env_str("SQL_PASSWORD")
PASSWORD = _env_str("SQL_PASSWORD")
ODBC_DRIVER = _env_str("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")


# lazy import + validated connection string
def _conn():
    import pyodbc  # lazy to avoid hard dependency for modules that don't need DB

    conn_str = (
        f"DRIVER={{{ODBC_DRIVER}}};"
        f"SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};"
        f"UID={SQL_USERNAME};PWD={SQL_PASSWORD}"
    )
    return pyodbc.connect(conn_str, autocommit=False, timeout=5)


# lazy import + validated connection string
def _conn_trusted():
    import pyodbc  # lazy to avoid hard dependency for modules that don't need DB

    conn_str = (
        f"DRIVER={{{ODBC_DRIVER}}};"
        f"SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str, autocommit=False, timeout=5)


USAGE_TABLE = "[dbo].[BotCommandUsage]"

# ---------- Google Sheet IDs (mark required if truly mandatory at runtime) ----------
SHEET_ID = _env_str("GOOGLE_KINGDOM_SUMMARY_ID")  # optional
KVK_SHEET_ID = _env_str("GOOGLE_KVK_LIST_ID")  # optional
TARGETS_SHEET_ID = _env_str("GOOGLE_TARGETS_ID")  # optional
TIMELINE_SHEET_ID = _env_str("GOOGLE_TIMELINE_ID")  # optional
STATS_SHEET_ID = _env_str("GOOGLE_STATS_ID")  # optional
ALL_KVK_SHEET_ID = _env_str("KVK_SHEET_ID")  # optional

# Import-service creds (optional separate account)
IMPORT_USERNAME = _env_str("IMPORT_SQL_USERNAME")
IMPORT_PASSWORD = _env_str("IMPORT_SQL_PASSWORD")


# lazy import + validated connection string
def _conn_import():
    import pyodbc  # lazy to avoid hard dependency for modules that don't need DB

    conn_str = (
        f"DRIVER={{{ODBC_DRIVER}}};"
        f"SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};"
        f"UID={IMPORT_USERNAME};PWD={IMPORT_PASSWORD}"
    )
    return pyodbc.connect(conn_str, autocommit=False, timeout=5)


# ---------- visual assets / banners ----------
KVK_BANNER_MAP = {
    "heroic anthem": "https://i.ibb.co/9kB99Swt/kvk-banner-heroic-anthem-slim1.png",
    "desert conquest": "https://your-link-for-desert.png",
    "strife of the eight": "https://your-link-for-strife.png",
    "tides": "https://i.ibb.co/Pv6bxrsd/tides-of-war.jpg",
    "koab": "https://i.ibb.co/gMPWkkZX/KOAB.png",
    "storm of stratagems": "https://i.ibb.co/sJdSFQN9/stratagems.jpg",
    "invictus": "https://i.ibb.co/Fqh6bhRK/alliance-invictus.png",
}
SHOW_KVK_BANNER = _env_bool("SHOW_KVK_BANNER", True)

# Profile imagery (can be moved to env if you want full mirror privacy)
PROFILE_HEADER_BANNER_PATH = _env_str(
    "PROFILE_HEADER_BANNER_PATH",
    "assets/rise-of-kingdoms-best-commander-pariring.jpg",
)
PROFILE_HEADER_BANNER_URL = _env_str(
    "PROFILE_HEADER_BANNER_URL",
    "https://i.ibb.co/1YdC0GZ0/rise-of-kingdoms-best-commander-pariring.jpg",
)
CUSTOM_AVATAR_URL = _env_str(
    "CUSTOM_AVATAR_URL",
    "https://i.ibb.co/vv403V8F/Helper.png",
)
SHOW_PROFILE_AVATAR_IN_CARD = _env_bool("SHOW_PROFILE_AVATAR_IN_CARD", False)

# Timeout for interactive stats views (14 minutes - leaves 1min buffer before Discord's 15min limit)
STATS_VIEW_TIMEOUT = 840  # seconds

# Emojis (keep configurable to avoid hard server fingerprinting)
DRAFT_TARGET_EMOJI = _env_str("DRAFT_TARGET_EMOJI", "<:draft_target:1419657556124504064>")
ACTIVE_TARGET_EMOJI = _env_str("ACTIVE_TARGET_EMOJI", "<:actual_target:1419657581173018695>")
HISTORIC_TARGET_EMOJI = _env_str("HISTORIC_TARGET_EMOJI", "<:historic_target:1419657602069168360>")
UP_ARROW_EMOJI = _env_str("UP_ARROW_EMOJI", "<:98up_arrow:1420053683366006854>")
DOWN_ARROW_EMOJI = _env_str("DOWN_ARROW_EMOJI", "<:98down_arrow:1420053660838400031>")
RIGHT_ARROW_EMOJI = _env_str("RIGHT_ARROW_EMOJI", "<:98right_arrow:1420053673471508480>")

# Singleton lock files (now under LOG_DIR)
WATCHDOG_LOCK_PATH = os.path.join(LOG_DIR, "WATCHDOG_LOCK.json")
BOT_LOCK_PATH = os.path.join(LOG_DIR, "BOT_LOCK.json")

# New: per-tracker configurable lock timeouts (seconds)
# Can be tuned via environment in high-contention environments
VIEW_TRACKER_LOCK_TIMEOUT = float(os.getenv("VIEW_TRACKER_LOCK_TIMEOUT", "5.0"))
VIEW_TRACKER_LOCK_POLL = float(os.getenv("VIEW_TRACKER_LOCK_POLL", "0.1"))

# New: control pruning on Forbidden exceptions (default: False)
# If True, discord.Forbidden will be treated as a terminal/prunable error.
VIEW_PRUNE_ON_FORBIDDEN = _env_bool("VIEW_PRUNE_ON_FORBIDDEN", False)

# Event timings / aliases
TIMELINE_DURATIONS = {
    "ruins": timedelta(hours=1),
    "altar": timedelta(hours=3),
    "altars": timedelta(hours=3),
    "chronicle": timedelta(hours=12),
    "major": timedelta(hours=12),
}
EVENT_TYPE_ALIASES = {
    "next ruins": "ruins",
    "next altar fight": "altars",
    "altar fight": "altars",
}

# All-kingdoms export
KVK_AUTO_EXPORT: bool = _env_bool("KVK_AUTO_EXPORT", True)
KVK_SHEET_NAME: str = _env_str("KVK_SHEET_NAME", "KVK LIST") or "KVK LIST"

OUR_KINGDOM = _env_int("OUR_KINGDOM")

# Defaults / allowed values for subscriptions
DEFAULT_REMINDER_TIMES: list[str] = ["24h", "12h", "4h", "1h", "now"]
VALID_TYPES: list[str] = ["ruins", "altars", "major", "fights", "all"]

# centralized reminder token -> timedelta mapping (use here to avoid duplication)
REMINDER_MAP = {
    "24h": timedelta(hours=24),
    "12h": timedelta(hours=12),
    "4h": timedelta(hours=4),
    "1h": timedelta(hours=1),
    "now": timedelta(seconds=0),
}

REMINDER_WINDOWS = [
    timedelta(hours=24),
    timedelta(hours=12),
    timedelta(hours=4),
    timedelta(hours=1),
    timedelta(minutes=0),
]

TEST_REMINDER_WINDOWS = [
    timedelta(minutes=1),
    timedelta(seconds=30),
    timedelta(seconds=10),
    timedelta(seconds=0),
]

# NEW: default timeout (seconds) for Google Sheets loader calls (can be tuned via env)
GSHEETS_CALL_TIMEOUT: float = float(os.getenv("GSHEETS_CALL_TIMEOUT", "30"))
