# stats_alerts/guard.py
"""
CSV log guard and migration helpers.

Provides:
- ensure_log_exists(): create/migrate CSV log to headered 3-col format
- iter_log_rows(): iterator yielding normalized dicts: {'date','time_utc','kind'}
- read_counts_for(kind, date_iso)
- sent_today(kind), sent_today_any(kinds)
- claim_send(kind, max_per_day=1) -> bool (atomic append with lock)
"""

from collections.abc import Iterator
import logging

from constants import STATS_ALERT_LOG
from file_utils import (
    acquire_lock,
    atomic_write_csv,
    read_csv_rows_safe,
    resolve_path,
)
from stats_alerts.formatters import normalize_row
from utils import format_time_utc, utcnow

logger = logging.getLogger(__name__)

LOG_PATH = str(resolve_path(STATS_ALERT_LOG))
HEADER = ["date", "time_utc", "kind"]
_LOCK_PATH = f"{LOG_PATH}.lock"


def ensure_log_exists() -> None:
    """
    Ensure the CSV log exists and is in a headered 3-col format:
    - If missing -> create with header only.
    - If header missing -> attempt to migrate rows (2-col -> 3-col using default kind).
    - If corrupted rows encountered -> skip them and write only valid rows.
    """
    try:
        rows = read_csv_rows_safe(LOG_PATH)
        if not rows:
            atomic_write_csv(LOG_PATH, HEADER, [])
            logger.info("[STATS_ALERT] created log at %s", LOG_PATH)
            return

        first = rows[0] if rows else None
        has_header = bool(
            first
            and len(first) >= 1
            and isinstance(first[0], str)
            and first[0].strip().lower() == "date"
        )
        data_rows = rows[1:] if has_header else rows

        upgraded = []
        changed = False
        for ln in data_rows:
            # Skip empty / whitespace-only rows
            if not ln or not any((cell or "").strip() for cell in ln):
                # if header was present and there are blank rows, treat them as removable (changed = True)
                if has_header:
                    changed = True
                continue
            nr = normalize_row(ln)
            if nr is None:
                # corrupt -> skip and mark changed
                changed = True
                continue
            upgraded.append([nr["date"], nr["time_utc"], nr["kind"]])
            # if header was absent, we'll write header later (changed flag)
            if not has_header:
                changed = True

        if (not has_header) or changed:
            atomic_write_csv(LOG_PATH, HEADER, upgraded)
            logger.info("[STATS_ALERT] migrated log to headered 3-col format at %s", LOG_PATH)
    except Exception:
        logger.exception("[STATS_ALERT] failed to ensure/migrate stats alert log")


def iter_log_rows() -> Iterator[dict]:
    """Yield normalized log rows (date, time_utc, kind)."""
    ensure_log_exists()
    try:
        rows = read_csv_rows_safe(LOG_PATH)
        if not rows:
            return
        idx = 0
        first = rows[0]
        if first and isinstance(first, list) and first and first[0].strip().lower() == "date":
            idx = 1
        for row in rows[idx:]:
            if not row:
                continue
            nr = normalize_row(row)
            if nr:
                yield nr
    except Exception:
        logger.exception("[STATS_ALERT] Failed iterating log rows")
        return


def read_counts_for(kind: str, date_iso: str) -> int:
    """Return how many times 'kind' was logged for date_iso."""
    c = 0
    for row in iter_log_rows():
        if row["date"] == date_iso and row["kind"] == kind:
            c += 1
    return c


def sent_today(kind: str) -> bool:

    today = utcnow().date().isoformat()
    return read_counts_for(kind, today) > 0


def sent_today_any(kinds: list[str]) -> bool:
    today = __import__("utils").utcnow().date().isoformat()
    ks = set(kinds)
    for row in iter_log_rows():
        if row["date"] == today and row["kind"] in ks:
            return True
    return False


def claim_send(kind: str, *, max_per_day: int = 1) -> bool:
    """
    Atomically append a row to the log using an acquire_lock on LOG_PATH.lock.

    Returns True if this process claimed the slot (appended). Returns False if the daily quota reached
    or on lock/acquire/write failures.
    """
    ensure_log_exists()

    today = utcnow().date().isoformat()
    try:
        with acquire_lock(_LOCK_PATH, timeout=5):
            sends_today = read_counts_for(kind, today)
            if sends_today >= max_per_day:
                logger.info(
                    "[SEND GUARD] '%s' already sent %d/%d for %s — skipping.",
                    kind,
                    sends_today,
                    max_per_day,
                    today,
                )
                return False

            rows = read_csv_rows_safe(LOG_PATH)
            header = []
            data_rows = rows
            if rows and rows[0] and rows[0][0].strip().lower() == "date":
                header = rows[0]
                data_rows = rows[1:]

            time_str = format_time_utc(utcnow(), "%H:%M:%S")
            data_rows.append([today, time_str, kind])

            if not header:
                header = HEADER
            atomic_write_csv(LOG_PATH, header, data_rows)
            logger.info(
                "[SEND GUARD] Claimed slot %d/%d for '%s' on %s (log=%s).",
                sends_today + 1,
                max_per_day,
                kind,
                today,
                LOG_PATH,
            )
            return True
    except TimeoutError:
        logger.exception("[SEND GUARD] Failed to acquire lock to claim send")
        return False
    except Exception:
        logger.exception("[SEND GUARD] Failed to claim send")
        return False
