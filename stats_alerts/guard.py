"""Compatible CSV success log, serialized with stats dispatch transactions.

The public claim API retains its existing meaning for KVK/Kingdom Summary.
Reservations are separate records; they are never written as successful sends.
"""

from collections.abc import Iterator
import logging

from filelock import FileLock

from constants import STATS_ALERT_LOG
from file_utils import atomic_write_csv, read_csv_rows_safe, resolve_path
from stats_alerts.formatters import normalize_row
from utils import utcnow

logger = logging.getLogger(__name__)
LOG_PATH = str(resolve_path(STATS_ALERT_LOG))
HEADER = ["date", "time_utc", "kind"]
LOCK_TIMEOUT_SECONDS = 5.0


def coordination_lock(log_path: str | None = None) -> FileLock:
    """A short OS-backed lock; legacy startup cleanup leaves .lck files alone."""
    return FileLock(f"{log_path or LOG_PATH}.dispatch.lck", timeout=LOCK_TIMEOUT_SECONDS)


def _read_rows_unlocked(log_path: str) -> tuple[list[str], list[list[str]]]:
    """Read/migrate under the caller's coordination lock; errors propagate."""
    rows = read_csv_rows_safe(log_path)
    if not rows:
        atomic_write_csv(log_path, HEADER, [])
        logger.info("[STATS_ALERT] created log at %s", log_path)
        return list(HEADER), []
    has_header = bool(rows[0] and rows[0][0].strip().lower() == "date")
    header = rows[0] if has_header else list(HEADER)
    data = rows[1:] if has_header else rows
    normalized = [normalize_row(row) for row in data]
    changed = not has_header or any(row is None for row in normalized)
    if changed:
        data = [[row["date"], row["time_utc"], row["kind"]] for row in normalized if row]
        header = list(HEADER)
        atomic_write_csv(log_path, header, data)
        logger.info("[STATS_ALERT] migrated log to headered 3-col format at %s", log_path)
    return header, data


def _count_rows(rows: list[list[str]], kind: str, day: str) -> int:
    return sum(
        1
        for raw in rows
        if (row := normalize_row(raw)) and row["date"] == day and row["kind"] == kind
    )


def _append_success_unlocked(log_path: str, kind: str, when, max_per_day: int = 1) -> bool:
    header, rows = _read_rows_unlocked(log_path)
    day = when.date().isoformat()
    count = _count_rows(rows, kind, day)
    if count >= max_per_day:
        logger.info(
            "[SEND GUARD] '%s' already sent %d/%d for %s — skipping.",
            kind,
            count,
            max_per_day,
            day,
        )
        return False
    rows.append([day, when.strftime("%H:%M:%S"), kind])
    atomic_write_csv(log_path, header, rows)
    logger.info(
        "[SEND GUARD] Claimed slot %d/%d for '%s' on %s (log=%s).",
        count + 1,
        max_per_day,
        kind,
        day,
        log_path,
    )
    return True


def ensure_log_exists() -> None:
    try:
        with coordination_lock():
            _read_rows_unlocked(LOG_PATH)
    except Exception:
        logger.exception("[STATS_ALERT] failed to ensure/migrate stats alert log")


def iter_log_rows() -> Iterator[dict]:
    try:
        with coordination_lock():
            _, rows = _read_rows_unlocked(LOG_PATH)
        for raw in rows:
            row = normalize_row(raw)
            if row:
                yield row
    except Exception:
        logger.exception("[STATS_ALERT] Failed iterating log rows")


def read_counts_for(kind: str, date_iso: str) -> int:
    return sum(1 for row in iter_log_rows() if row["date"] == date_iso and row["kind"] == kind)


def sent_today(kind: str) -> bool:
    return read_counts_for(kind, utcnow().date().isoformat()) > 0


def sent_today_any(kinds: list[str]) -> bool:
    today = utcnow().date().isoformat()
    return any(row["date"] == today and row["kind"] in kinds for row in iter_log_rows())


def claim_send(kind: str, *, max_per_day: int = 1) -> bool:
    """Legacy locked success/ping claim; never grants dispatch ownership."""
    try:
        with coordination_lock():
            return _append_success_unlocked(LOG_PATH, kind, utcnow(), max_per_day)
    except TimeoutError:
        logger.exception("[SEND GUARD] Failed to acquire lock to claim send")
    except Exception:
        logger.exception("[SEND GUARD] Failed to claim send")
    return False
