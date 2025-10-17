# event_data_loader.py  — upgraded
import asyncio
from datetime import UTC, datetime, timedelta
from functools import lru_cache
import logging
from typing import Any, TypedDict

from google.oauth2.service_account import Credentials

from constants import (
    CREDENTIALS_FILE,
    # Optional: minutes for each event type (fallbacks below)
    # Example:
    # TIMELINE_DURATIONS = {"ruins": 15, "altar": 15, "major": 30, "chronicle": 12*60}
    TIMELINE_DURATIONS as _CFG_DURATIONS,  # may not exist in older constants
    TIMELINE_SHEET_ID,
)

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
UTC = UTC

# ---- Centralised A1 ranges (easy to tweak) -----------------------------------
RANGES = {
    "ruins": "RUINS_BOT_DATES!A2:A",  # [datetime]
    "altar": "ALTARS_BOT_DATES!A2:A",  # [datetime]
    "major": "Major_BOT_DATES!A2:B",  # [datetime, name]
    "chronicle": "Chronicle_BOT_DATES!A2:C",  # [datetime, name, description]
}

# ---- Duration config (minutes) with sensible defaults ------------------------
DEFAULT_DURATIONS = {
    "ruins": 15,
    "altar": 15,
    "major": 30,
    "chronicle": 12 * 60,  # 12 hours
}
DUR = {**DEFAULT_DURATIONS}
try:
    # allow partial overrides from constants
    for _k, _v in (_CFG_DURATIONS or {}).items():
        if isinstance(_v, (int, float)) and _k in DUR:
            DUR[_k] = int(_v)
except Exception:
    pass


# ---- Typed event for clarity -------------------------------------------------
class Event(TypedDict, total=False):
    name: str
    type: str
    start_time: datetime
    end_time: datetime
    description: str
    zone: str


# ---- Google Sheets client (lazy, cached) -------------------------------------
@lru_cache(maxsize=1)
def _sheets_client():
    """
    Build a Google Sheets client with HTTP timeout.
    Lazy-imports heavy deps; cached to reuse the same HTTP session.
    """
    import google_auth_httplib2
    from googleapiclient.discovery import build
    import httplib2

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    http = httplib2.Http(timeout=30)  # seconds
    authed_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
    svc = build("sheets", "v4", http=authed_http, cache_discovery=False)
    return svc.spreadsheets()


def _fetch_values(range_a1: str) -> list[list[Any]] | None:
    """
    Returns rows [] on success (empty), or None on error.
    Uses dateTimeRenderOption=FORMATTED_STRING to avoid serials.
    """
    try:
        sheet = _sheets_client()
        req = sheet.values().get(
            spreadsheetId=TIMELINE_SHEET_ID,
            range=range_a1,
            valueRenderOption="FORMATTED_VALUE",
            dateTimeRenderOption="FORMATTED_STRING",
        )
        res = req.execute(num_retries=3)
        return res.get("values", []) or []
    except Exception as e:
        logger.error("[TIMELINE] Fetch failed for %s (%s): %s", TIMELINE_SHEET_ID, range_a1, e)
        return None


# ---- Date parsing (sheet is confirmed UTC) -----------------------------------
# Primary format (fast path): 'Mon 29 Sep 25 00:00'
_FMT_PRIMARY = "%a %d %b %y %H:%M"
# Secondary (if ever used without weekday)
_FMT_SECONDARY = "%d %b %y %H:%M"


def _parse_dt_str_utc(s: str) -> datetime:
    """
    Parse a datetime string that is ALREADY in UTC (as per sheet contract).
    Returns tz-aware UTC.
    """
    s = (s or "").strip()

    # Fast path: exact format expected
    try:
        return datetime.strptime(s, _FMT_PRIMARY).replace(tzinfo=UTC)
    except Exception:
        pass

    # Secondary: no weekday
    try:
        return datetime.strptime(s, _FMT_SECONDARY).replace(tzinfo=UTC)
    except Exception:
        pass

    # Fallback: permissive ISO-ish
    try:
        _iso = s.replace(" ", "T") if " " in s and "T" not in s else s
        # If it includes a 'Z' or offset, fromisoformat will keep it; we then convert to UTC.
        dt = datetime.fromisoformat(_iso)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        raise ValueError(f"Unrecognized UTC datetime format: {s!r}")


def _sorted_future_only(events: list[Event]) -> list[Event]:
    now = datetime.utcnow().replace(tzinfo=UTC)
    fut = [e for e in events if e.get("start_time") and e["start_time"] >= now]
    return sorted(fut, key=lambda x: x["start_time"])


# ---- Parsers -----------------------------------------------------------------
def _add_end(start: datetime, minutes: int) -> datetime:
    return start + timedelta(minutes=minutes)


def parse_event_dates(raw_list: list[list[Any]], *, label: str, etype: str) -> list[Event]:
    """
    Parse 1-column ranges of datetimes into standard event dicts.
    label: human-readable label (e.g., "Next Ruins")
    etype: canonical type key ("ruins" | "altar")
    """
    out: list[Event] = []
    duration = DUR.get(etype, 15)
    for row in raw_list:
        try:
            if not row or not row[0]:
                continue
            dt = _parse_dt_str_utc(str(row[0]))
            out.append(
                {
                    "name": label,
                    "type": etype,
                    "start_time": dt,
                    "end_time": _add_end(dt, duration),
                    "zone": None,
                }
            )
        except Exception as e:
            logger.warning("[TIMELINE] Skip invalid %s row %r: %s", etype, row, e)
    return _sorted_future_only(out)


def parse_major_dates(raw_list: list[list[Any]]) -> list[Event]:
    """
    Parse 2-column ranges: [datetime, name]
    """
    out: list[Event] = []
    duration = DUR["major"]
    for row in raw_list:
        try:
            if not row or not row[0]:
                continue
            date_str = str(row[0]).strip()
            name = str(row[1]).strip() if len(row) > 1 and row[1] else "Unnamed Major Event"
            dt = _parse_dt_str_utc(date_str)
            out.append(
                {
                    "name": name,
                    "type": "major",
                    "start_time": dt,
                    "end_time": _add_end(dt, duration),
                    "zone": None,
                }
            )
        except Exception as e:
            logger.warning("[TIMELINE] Skip invalid major row %r: %s", row, e)
    return _sorted_future_only(out)


def parse_chronicle_dates(raw_list: list[list[Any]]) -> list[Event]:
    """
    Parse 3-column ranges: [datetime, name, description]
    """
    out: list[Event] = []
    duration = DUR["chronicle"]
    for row in raw_list:
        try:
            if not row or not row[0]:
                continue
            date_str = str(row[0]).strip()
            name = str(row[1]).strip() if len(row) > 1 and row[1] else "Unnamed Chronicle Stage"
            description = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            dt = _parse_dt_str_utc(date_str)
            out.append(
                {
                    "name": name,
                    "type": "chronicle",
                    "description": description,
                    "start_time": dt,
                    "end_time": _add_end(dt, duration),
                    "zone": None,
                }
            )
        except Exception as e:
            logger.warning("[TIMELINE] Skip invalid chronicle row %r: %s", row, e)
    return _sorted_future_only(out)


# ---- Public async loaders (run off-thread) -----------------------------------
async def load_upcoming_ruins_events() -> list[Event] | None:
    return await asyncio.to_thread(_load_upcoming_ruins_sync)


def _load_upcoming_ruins_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["ruins"])
    if values is None:
        return None
    return parse_event_dates(values, label="Next Ruins", etype="ruins") if values else []


async def load_upcoming_altar_events() -> list[Event] | None:
    return await asyncio.to_thread(_load_upcoming_altar_events_sync)


def _load_upcoming_altar_events_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["altar"])
    if values is None:
        return None
    return parse_event_dates(values, label="Next Altar Fight", etype="altar") if values else []


async def load_upcoming_major_events() -> list[Event] | None:
    return await asyncio.to_thread(_load_upcoming_major_events_sync)


def _load_upcoming_major_events_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["major"])
    if values is None:
        return None
    return parse_major_dates(values) if values else []


async def load_upcoming_chronicle_events() -> list[Event] | None:
    return await asyncio.to_thread(_load_upcoming_chronicle_events_sync)


def _load_upcoming_chronicle_events_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["chronicle"])
    if values is None:
        return None
    return parse_chronicle_dates(values) if values else []


# --- Optional: one-call batch loader for all event types ----------------------
async def load_all_upcoming_events() -> list[Event] | None:
    """
    Concurrently load all event categories, return a single sorted list.
    Returns None if any fetch hard-fails (so caller can surface an error).
    """
    ruins, altar, major, chrono = await asyncio.gather(
        load_upcoming_ruins_events(),
        load_upcoming_altar_events(),
        load_upcoming_major_events(),
        load_upcoming_chronicle_events(),
    )

    if any(v is None for v in (ruins, altar, major, chrono)):
        return None

    merged: list[Event] = (ruins or []) + (altar or []) + (major or []) + (chrono or [])
    return sorted(merged, key=lambda e: e["start_time"])
