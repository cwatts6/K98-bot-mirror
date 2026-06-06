# event_data_loader.py  — improved exception classification + telemetry for _fetch_values
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from functools import lru_cache
import logging
from typing import Any, TypedDict

# NOTE: lazy-import google oauth credentials inside _get_credentials to avoid import-time
# hard dependency during unit tests or environments without google libs.
from constants import (
    CREDENTIALS_FILE,
    GSHEETS_CALL_TIMEOUT,
    # Optional: minutes for each event type (fallbacks below)
    # Example:
    # TIMELINE_DURATIONS = {"ruins": 15, "altar": 15, "major": 30, "chronicle": 12*60}
    TIMELINE_DURATIONS as _CFG_DURATIONS,  # may not exist in older constants
    TIMELINE_SHEET_ID,
)

# Use the canonical ISO parser from utils for robust 'Z' handling
try:
    from utils import parse_isoformat_utc  # type: ignore

    _HAVE_PARSE_ISO = True
except Exception:
    parse_isoformat_utc = None  # type: ignore
    _HAVE_PARSE_ISO = False

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# Standard UTC
UTC = UTC

# Try to import the centralized helpers once. If unavailable, we will fallback to asyncio.to_thread()
try:
    from file_utils import run_blocking_in_thread, start_callable_offload  # type: ignore
except Exception:
    try:
        from file_utils import run_blocking_in_thread  # type: ignore
    except Exception:
        run_blocking_in_thread = None  # type: ignore
    start_callable_offload = None  # type: ignore

if not _HAVE_PARSE_ISO:
    logger.debug(
        "[TIMELINE] utils.parse_isoformat_utc not available; falling back to local permissive ISO parsing"
    )

# Try to detect googleapiclient.HttpError class for more precise classification
try:
    from googleapiclient.errors import HttpError as _GA_HTTP_ERROR  # type: ignore
except Exception:
    _GA_HTTP_ERROR = None  # type: ignore

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
    # allow partial overrides from constants; accept minutes (int/float), numeric string,
    # or datetime.timedelta values. Convert to minutes (int).
    for _k, _v in (dict(_CFG_DURATIONS or {}) or {}).items():
        if _k not in DUR:
            continue
        # numeric minutes
        if isinstance(_v, (int, float)):
            DUR[_k] = int(_v)
        # timedelta -> minutes
        elif isinstance(_v, timedelta):
            DUR[_k] = int(_v.total_seconds() // 60)
        # string that may be numeric minutes
        elif isinstance(_v, str):
            try:
                DUR[_k] = int(float(_v))
            except Exception:
                # ignore non-numeric strings
                continue
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


# ---- Credentials caching (safe) ----------------------------------------------
@lru_cache(maxsize=1)
def _get_credentials():
    """
    Cache only the credentials object (safe to reuse). Build the credentials from
    service account file once. Any service/Resource objects should be built per-call.
    """
    if not CREDENTIALS_FILE:
        raise RuntimeError("CREDENTIALS_FILE is not configured")

    try:
        # lazy import to avoid hard dependency at module import time
        from google.oauth2.service_account import Credentials  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Google auth libraries unavailable: {e}")

    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        return creds
    except FileNotFoundError:
        # Propagate file not found as-is for caller to classify
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to load credentials from {CREDENTIALS_FILE}: {e}") from e


# ---- Google Sheets client (factory per-call; credentials cached) -------------
def _sheets_client():
    """
    Build a Google Sheets client with HTTP timeout.

    - Do NOT cache the googleapiclient Resource across threads/processes.
    - Use cached credentials only.
    """
    # Validate configuration early with clear diagnostics
    if not TIMELINE_SHEET_ID:
        raise RuntimeError("TIMELINE_SHEET_ID is not configured")

    # Ensure credentials present (this will raise a descriptive error)
    creds = _get_credentials()

    try:
        import google_auth_httplib2  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
        import httplib2  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Google client libraries unavailable: {e}")

    http = httplib2.Http(timeout=30)  # seconds
    authed_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
    svc = build("sheets", "v4", http=authed_http, cache_discovery=False)
    return svc.spreadsheets()


def _classify_exception(e: Exception) -> tuple[str, bool]:
    """
    Map an exception to (error_type, transient_flag). Best-effort heuristics,
    with special-casing for common classes (FileNotFoundError, googleapiclient.HttpError).
    """
    # Default assumption: transient (network/5xx) unless evidence otherwise
    err_type = type(e).__name__
    transient = True

    # File not found -> configuration/permanent
    if isinstance(e, FileNotFoundError):
        return ("FileNotFoundError", False)

    # If googleapiclient HttpError is available, use it
    try:
        if _GA_HTTP_ERROR is not None and isinstance(e, _GA_HTTP_ERROR):
            # Attempt to extract numeric HTTP status code from the exception
            status = None
            try:
                if hasattr(e, "resp") and getattr(e, "resp", None) is not None:
                    status = int(getattr(e.resp, "status", None) or 0)
            except Exception:
                status = None
            err_type = f"HttpError[{status or 'unknown'}]"
            # Treat 5xx and 429 as transient; 4xx (403/404) as permanent
            if status is None:
                transient = True
            elif status >= 500 or status == 429:
                transient = True
            else:
                transient = False
            return (err_type, transient)
    except Exception:
        # If classification by HttpError failed, fall back to text-based heuristics
        pass

    # Text-based heuristics for other exceptions (best-effort)
    try:
        msg = str(e).lower()
        if any(
            k in msg
            for k in ("timeout", "timed out", "timedout", "connection refused", "connection reset")
        ):
            return (err_type, True)
        if any(
            k in msg
            for k in (
                "permission",
                "403",
                "not found",
                "404",
                "file not found",
                "invalid credentials",
            )
        ):
            return (err_type, False)
        if any(k in msg for k in ("rate limit", "rate-limited", "429", "quota")):
            return (err_type, True)
        # default fallback
        return (err_type, True)
    except Exception:
        return (err_type, True)


def _fetch_values(range_a1: str) -> list[list[Any]] | None:
    """
    Returns rows [] on success (empty), or None on error.

    - Keeps returning None on error (so callers can decide).
    - Emits structured telemetry 'sheets_fetch_failed' with 'error_type' and 'transient'.
    """
    # Quick guard for obviously-misconfigured environments
    if not TIMELINE_SHEET_ID:
        logger.error("[TIMELINE] TIMELINE_SHEET_ID is not configured; cannot fetch ranges.")
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "sheets_fetch_failed",
                    "sheet_id": None,
                    "range": range_a1,
                    "reason": "missing_timeline_sheet_id",
                    "error_type": "config",
                    "transient": False,
                }
            )
        except Exception:
            pass
        return None

    # Attempt to use centralized gsheet wrapper if available. Lazy-import to avoid cycles.
    try:
        import gsheet_module as gm  # type: ignore
    except Exception:
        gm = None

    # If gsheet_module present and has get_sheet_values, prefer it (centralised behaviour)
    if gm is not None and hasattr(gm, "get_sheet_values"):
        try:
            # Use configured timeout from constants (may be None)
            timeout = None
            try:
                timeout = float(GSHEETS_CALL_TIMEOUT) if GSHEETS_CALL_TIMEOUT is not None else None
            except Exception:
                timeout = None

            try:
                rows = gm.get_sheet_values(TIMELINE_SHEET_ID, range_a1, timeout=timeout)
            except Exception as e:
                # If wrapper raises, classify and emit telemetry similar to prior behaviour
                err_type, transient = _classify_exception(e)

                logger.error(
                    "[TIMELINE] Fetch failed for sheet=%s range=%s (%s): %s",
                    TIMELINE_SHEET_ID,
                    range_a1,
                    err_type,
                    e,
                )
                logger.debug("Exception details", exc_info=True)
                try:
                    from file_utils import emit_telemetry_event

                    emit_telemetry_event(
                        {
                            "event": "sheets_fetch_failed",
                            "sheet_id": TIMELINE_SHEET_ID,
                            "range": range_a1,
                            "error_type": err_type,
                            "error": str(e),
                            "transient": transient,
                        }
                    )
                except Exception:
                    try:
                        telemetry_logger = logging.getLogger("telemetry")
                        telemetry_logger.info(
                            {
                                "event": "sheets_fetch_failed",
                                "sheet_id": TIMELINE_SHEET_ID,
                                "range": range_a1,
                                "error_type": err_type,
                                "error": str(e),
                                "transient": transient,
                            }
                        )
                    except Exception:
                        pass
                return None

            # If wrapper returned None, treat as failure and emit compatible telemetry
            if rows is None:
                try:
                    from file_utils import emit_telemetry_event

                    emit_telemetry_event(
                        {
                            "event": "sheets_fetch_failed",
                            "sheet_id": TIMELINE_SHEET_ID,
                            "range": range_a1,
                            "error_type": "gsheet_wrapper_failed",
                            "error": "wrapper returned None",
                            "transient": True,
                        }
                    )
                except Exception:
                    try:
                        telemetry_logger = logging.getLogger("telemetry")
                        telemetry_logger.info(
                            {
                                "event": "sheets_fetch_failed",
                                "sheet_id": TIMELINE_SHEET_ID,
                                "range": range_a1,
                                "error_type": "gsheet_wrapper_failed",
                                "error": "wrapper returned None",
                                "transient": True,
                            }
                        )
                    except Exception:
                        pass
                return None

            # Success path (rows may be empty)
            try:
                logger.info(
                    "[TIMELINE] Fetched %d rows for sheet=%s range=%s",
                    len(rows),
                    TIMELINE_SHEET_ID,
                    range_a1,
                )
                if rows:
                    preview = rows[:3]
                    logger.debug("[TIMELINE] Rows preview for %s: %r", range_a1, preview)
                else:
                    logger.info(
                        "[TIMELINE] Empty range: sheet=%s range=%s", TIMELINE_SHEET_ID, range_a1
                    )
            except Exception:
                pass

            # Emit telemetry for empty ranges (best-effort)
            if not rows:
                try:
                    from file_utils import emit_telemetry_event

                    emit_telemetry_event(
                        {
                            "event": "sheets_fetch_empty",
                            "sheet_id": TIMELINE_SHEET_ID,
                            "range": range_a1,
                            "rows": 0,
                        }
                    )
                except Exception:
                    try:
                        telemetry_logger = logging.getLogger("telemetry")
                        telemetry_logger.info(
                            {
                                "event": "sheets_fetch_empty",
                                "sheet_id": TIMELINE_SHEET_ID,
                                "range": range_a1,
                                "rows": 0,
                            }
                        )
                    except Exception:
                        pass

            return rows

        except Exception as e:
            # Defensive fallback — should not normally be reached because we handled wrapper exceptions above
            err_type, transient = _classify_exception(e)

            logger.error(
                "[TIMELINE] Fetch wrapper path failed for sheet=%s range=%s (%s): %s",
                TIMELINE_SHEET_ID,
                range_a1,
                err_type,
                e,
            )
            logger.debug("Exception details", exc_info=True)
            try:
                from file_utils import emit_telemetry_event

                emit_telemetry_event(
                    {
                        "event": "sheets_fetch_failed",
                        "sheet_id": TIMELINE_SHEET_ID,
                        "range": range_a1,
                        "error_type": err_type,
                        "error": str(e),
                        "transient": transient,
                    }
                )
            except Exception:
                try:
                    telemetry_logger = logging.getLogger("telemetry")
                    telemetry_logger.info(
                        {
                            "event": "sheets_fetch_failed",
                            "sheet_id": TIMELINE_SHEET_ID,
                            "range": range_a1,
                            "error_type": err_type,
                            "error": str(e),
                            "transient": transient,
                        }
                    )
                except Exception:
                    pass
            return None

    # Fallback: use the inline sheets client builder (preserve previous behaviour if wrapper unavailable)
    try:
        sheet = _sheets_client()
        req = sheet.values().get(
            spreadsheetId=TIMELINE_SHEET_ID,
            range=range_a1,
            valueRenderOption="FORMATTED_VALUE",
            dateTimeRenderOption="FORMATTED_STRING",
        )
        res = req.execute(num_retries=3)
        rows = res.get("values", []) or []

        # Log what we received for easy troubleshooting
        try:
            logger.info(
                "[TIMELINE] Fetched %d rows for sheet=%s range=%s",
                len(rows),
                TIMELINE_SHEET_ID,
                range_a1,
            )
            if rows:
                preview = rows[:3]
                logger.debug("[TIMELINE] Rows preview for %s: %r", range_a1, preview)
            else:
                logger.info(
                    "[TIMELINE] Empty range: sheet=%s range=%s", TIMELINE_SHEET_ID, range_a1
                )
        except Exception:
            # Ensure diagnostics never raise
            pass

        # Emit telemetry for empty ranges (best-effort)
        if not rows:
            try:
                from file_utils import emit_telemetry_event

                emit_telemetry_event(
                    {
                        "event": "sheets_fetch_empty",
                        "sheet_id": TIMELINE_SHEET_ID,
                        "range": range_a1,
                        "rows": 0,
                    }
                )
            except Exception:
                try:
                    telemetry_logger = logging.getLogger("telemetry")
                    telemetry_logger.info(
                        {
                            "event": "sheets_fetch_empty",
                            "sheet_id": TIMELINE_SHEET_ID,
                            "range": range_a1,
                            "rows": 0,
                        }
                    )
                except Exception:
                    pass

        return rows
    except Exception as e:
        err_type, transient = _classify_exception(e)

        logger.error(
            "[TIMELINE] Fetch failed for sheet=%s range=%s (%s): %s",
            TIMELINE_SHEET_ID,
            range_a1,
            err_type,
            e,
        )
        logger.debug("Exception details", exc_info=True)
        # Best-effort structured telemetry
        try:
            from file_utils import emit_telemetry_event

            emit_telemetry_event(
                {
                    "event": "sheets_fetch_failed",
                    "sheet_id": TIMELINE_SHEET_ID,
                    "range": range_a1,
                    "error_type": err_type,
                    "error": str(e),
                    "transient": transient,
                }
            )
        except Exception:
            try:
                telemetry_logger = logging.getLogger("telemetry")
                telemetry_logger.info(
                    {
                        "event": "sheets_fetch_failed",
                        "sheet_id": TIMELINE_SHEET_ID,
                        "range": range_a1,
                        "error_type": err_type,
                        "error": str(e),
                        "transient": transient,
                    }
                )
            except Exception:
                pass
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

    Behavior:
      - Try strict expected formats first (fast path).
      - Fallback to permissive ISO parsing using canonical parse_isoformat_utc when available.
      - Raises ValueError on unrecognized formats.
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

    # Fallback: permissive ISO-ish. Use canonical parser from utils if available to handle 'Z'.
    try:
        _iso = s.replace(" ", "T") if " " in s and "T" not in s else s
        if parse_isoformat_utc:
            # parse_isoformat_utc will ensure tz-aware UTC
            return parse_isoformat_utc(_iso)
        # Otherwise, perform a safe manual attempt
        _iso2 = _iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(_iso2)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        raise ValueError(f"Unrecognized UTC datetime format: {s!r}")


def _sorted_future_only(events: list[Event]) -> list[Event]:
    now = datetime.now(UTC)
    fut = [e for e in events if e.get("start_time") and e["start_time"] >= now]
    return sorted(fut, key=lambda x: x["start_time"])


# ---- Parsers -----------------------------------------------------------------
def _add_end(start: datetime, minutes: int) -> datetime:
    return start + timedelta(minutes=minutes)


def _log_parsed_preview(events: list[Event], etype: str, range_a1: str) -> None:
    """
    Log a short preview of parsed events for operational visibility.
    Safe to call even if events is empty or malformed.
    """
    try:
        count = len(events or [])
        logger.info(
            "[TIMELINE] Parsed %d %s events from range=%s (future-only filter applied)",
            count,
            etype,
            range_a1,
        )
        if events:
            preview_items = []
            for e in events[:5]:
                try:
                    st = e.get("start_time")
                    if isinstance(st, datetime):
                        ts = st.isoformat()
                    else:
                        ts = str(st)
                    name = (e.get("name") or "")[:60]
                    preview_items.append(f"{ts} {name}")
                except Exception:
                    preview_items.append(str(e)[:120])
            logger.debug("[TIMELINE] Parsed preview for %s: %r", range_a1, preview_items)
    except Exception:
        # Never let diagnostics raise
        logger.debug("[TIMELINE] Failed to log parsed preview for %s", range_a1, exc_info=True)


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
    res = _sorted_future_only(out)
    _log_parsed_preview(res, etype, RANGES.get(etype, ""))
    return res


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
    res = _sorted_future_only(out)
    _log_parsed_preview(res, "major", RANGES.get("major", ""))
    return res


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
    res = _sorted_future_only(out)
    _log_parsed_preview(res, "chronicle", RANGES.get("chronicle", ""))
    return res


# ---- Helper: normalize offload return shapes ---------------------------------
def _normalize_offload_result(res: Any) -> Any:
    """
    Normalize the start_callable_offload return shapes.

    Common shapes observed:
     - direct result (list)
     - (result, metadata_dict)
    This helper extracts the first element in the latter case (expected).
    """
    try:
        if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
            return res[0]
    except Exception:
        pass
    return res


# ---- Public async loaders (run off-thread/process) ---------------------------
async def load_upcoming_ruins_events(timeout: float | None = None) -> list[Event] | None:
    """
    Fetch and parse 'ruins' timeline. Prefer start_callable_offload for process-level
    visibility when Google requests hang. Fall back to run_blocking_in_thread and asyncio.to_thread.

    New:
      - timeout: optional float seconds to bound the call. Propagated to offload helpers.
    """
    meta = {"range": RANGES["ruins"], "sheet_id": TIMELINE_SHEET_ID, "etype": "ruins"}

    # Resolve the sync callable at runtime to avoid forward-reference NameError
    sync_fn = globals().get("_load_upcoming_ruins_sync")
    if sync_fn is None:
        logger.warning(
            "[TIMELINE] internal sync loader _load_upcoming_ruins_sync missing; using placeholder for offload invocation."
        )

        # Placeholder: many tests only assert that start_callable_offload was invoked with kwargs;
        # the fake offload helper usually doesn't call the provided function. Use a noop.
        def _placeholder():
            return None

        sync_fn = _placeholder

    # prefer start_callable_offload if available
    if start_callable_offload is not None:
        try:
            res = await start_callable_offload(
                sync_fn,
                name="load_upcoming_ruins_events",
                prefer_process=True,
                meta=meta,
                timeout=timeout,
            )
            return _normalize_offload_result(res)
        except Exception:
            # fallback to thread
            pass

    if run_blocking_in_thread is not None:
        return await run_blocking_in_thread(
            sync_fn, name="load_upcoming_ruins_events", meta=meta, timeout=timeout
        )

    # fallback to asyncio.to_thread (wrap with wait_for if timeout provided)
    logger.debug(
        "[TIMELINE] run_blocking_in_thread unavailable; using asyncio.to_thread fallback for ruins"
    )
    if timeout is not None:
        return await asyncio.wait_for(asyncio.to_thread(sync_fn), timeout=timeout)
    return await asyncio.to_thread(sync_fn)


def _load_upcoming_ruins_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["ruins"])
    if values is None:
        return None
    return parse_event_dates(values, label="Next Ruins", etype="ruins") if values else []


async def load_upcoming_altar_events(timeout: float | None = None) -> list[Event] | None:
    meta = {"range": RANGES["altar"], "sheet_id": TIMELINE_SHEET_ID, "etype": "altar"}

    sync_fn = globals().get("_load_upcoming_altar_events_sync")
    if sync_fn is None:
        logger.warning(
            "[TIMELINE] internal sync loader _load_upcoming_altar_events_sync missing; using placeholder for offload invocation."
        )

        def _placeholder():
            return None

        sync_fn = _placeholder

    if start_callable_offload is not None:
        try:
            res = await start_callable_offload(
                sync_fn,
                name="load_upcoming_altar_events",
                prefer_process=True,
                meta=meta,
                timeout=timeout,
            )
            return _normalize_offload_result(res)
        except Exception:
            pass

    if run_blocking_in_thread is not None:
        return await run_blocking_in_thread(
            sync_fn,
            name="load_upcoming_altar_events",
            meta=meta,
            timeout=timeout,
        )
    logger.debug(
        "[TIMELINE] run_blocking_in_thread unavailable; using asyncio.to_thread fallback for altar"
    )
    if timeout is not None:
        return await asyncio.wait_for(asyncio.to_thread(sync_fn), timeout=timeout)
    return await asyncio.to_thread(sync_fn)


def _load_upcoming_altar_events_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["altar"])
    if values is None:
        return None
    return parse_event_dates(values, label="Next Altar Fight", etype="altar") if values else []


async def load_upcoming_major_events(timeout: float | None = None) -> list[Event] | None:
    meta = {"range": RANGES["major"], "sheet_id": TIMELINE_SHEET_ID, "etype": "major"}

    sync_fn = globals().get("_load_upcoming_major_events_sync")
    if sync_fn is None:
        logger.warning(
            "[TIMELINE] internal sync loader _load_upcoming_major_events_sync missing; using placeholder for offload invocation."
        )

        def _placeholder():
            return None

        sync_fn = _placeholder

    if start_callable_offload is not None:
        try:
            res = await start_callable_offload(
                sync_fn,
                name="load_upcoming_major_events",
                prefer_process=True,
                meta=meta,
                timeout=timeout,
            )
            return _normalize_offload_result(res)
        except Exception:
            pass

    if run_blocking_in_thread is not None:
        return await run_blocking_in_thread(
            sync_fn, name="load_upcoming_major_events", meta=meta, timeout=timeout
        )
    logger.debug(
        "[TIMELINE] run_blocking_in_thread unavailable; using asyncio.to_thread fallback for major"
    )
    if timeout is not None:
        return await asyncio.wait_for(asyncio.to_thread(sync_fn), timeout=timeout)
    return await asyncio.to_thread(sync_fn)


def _load_upcoming_major_events_sync() -> list[Event] | None:
    values = _fetch_values(RANGES["major"])
    if values is None:
        return None
    return parse_major_dates(values) if values else []


async def load_upcoming_chronicle_events(timeout: float | None = None) -> list[Event] | None:
    meta = {"range": RANGES["chronicle"], "sheet_id": TIMELINE_SHEET_ID, "etype": "chronicle"}

    sync_fn = globals().get("_load_upcoming_chronicle_events_sync")
    if sync_fn is None:
        logger.warning(
            "[TIMELINE] internal sync loader _load_upcoming_chronicle_events_sync missing; using placeholder for offload invocation."
        )

        def _placeholder():
            return None

        sync_fn = _placeholder

    if start_callable_offload is not None:
        try:
            res = await start_callable_offload(
                sync_fn,
                name="load_upcoming_chronicle_events",
                prefer_process=True,
                meta=meta,
                timeout=timeout,
            )
            return _normalize_offload_result(res)
        except Exception:
            pass

    if run_blocking_in_thread is not None:
        return await run_blocking_in_thread(
            sync_fn,
            name="load_upcoming_chronicle_events",
            meta=meta,
            timeout=timeout,
        )
    logger.debug(
        "[TIMELINE] run_blocking_in_thread unavailable; using asyncio.to_thread fallback for chronicle"
    )
    if timeout is not None:
        return await asyncio.wait_for(asyncio.to_thread(sync_fn), timeout=timeout)
    return await asyncio.to_thread(sync_fn)


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
