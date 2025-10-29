# gsheet_module.py
# Full file with requested fixes and improved gspread retry and logging behavior.
import asyncio
import datetime as _dt
import json
import logging

logger = logging.getLogger(__name__)

import platform
import random
import socket
import ssl
import sys
import time
import traceback
import uuid

import discord
from google.oauth2.service_account import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound
import httplib2
import pandas as pd
from pandas.api import types as ptypes
import pyodbc
import requests
from sqlalchemy import create_engine

from constants import CONFIG_FILE, CREDENTIALS_FILE

# Optional: try to collect versions for diagnostics
try:
    import importlib.metadata as _importlib_metadata

    _get_dist_version = lambda name: _importlib_metadata.version(name)
except Exception:
    try:
        import pkg_resources as _pkg_resources

        _get_dist_version = lambda name: _pkg_resources.get_distribution(name).version
    except Exception:
        _get_dist_version = lambda name: "unknown"

GSPREAD_VERSION = getattr(gspread, "__version__", "unknown")
GOOGLE_API_CLIENT_VERSION = (
    _get_dist_version("google-api-python-client") if _get_dist_version else "unknown"
)

if CREDENTIALS_FILE is None:
    raise RuntimeError("GOOGLE_CREDENTIALS_FILE not set in .env")


def _stringify_datetimes_inplace(df: pd.DataFrame, fmt: str = "%Y-%m-%d %H:%M:%S") -> None:
    """
    Convert any datetime-like columns (tz-aware/naive) and object columns
    containing datetime/Timestamp/date into plain strings for Sheets.
    Operates IN PLACE.
    """
    if df is None or df.empty:
        return

    for col in list(df.columns):
        s = df[col]
        # 1) Proper datetime dtypes (including tz-aware)
        if ptypes.is_datetime64_any_dtype(s) or getattr(s.dtype, "name", "").startswith(
            "datetime64["
        ):
            df[col] = pd.to_datetime(s, errors="coerce").dt.strftime(fmt).fillna("")
            continue

        # 2) Object columns that may hold datetime-like objects
        if s.dtype == object:
            # Quick scan: if nothing is datetime-like, skip the map
            if not s.map(lambda v: isinstance(v, (pd.Timestamp, _dt.datetime, _dt.date))).any():
                continue

            def _to_str(v):
                if isinstance(v, (pd.Timestamp, _dt.datetime)):
                    return v.strftime(fmt)
                if isinstance(v, _dt.date):
                    return v.strftime("%Y-%m-%d")
                return "" if pd.isna(v) else v

            df[col] = s.map(_to_str)


def _get_or_create_ws(ss: gspread.Spreadsheet, title: str, cols: int = 26) -> gspread.Worksheet:
    """
    Return a worksheet by title; create if not found.
    - Normalizes titles (trim + collapse spaces, casefold) for fallback search.
    - Handles duplicate-create race by refetching if Google says it exists.
    Uses retry wrapper for create path.
    """
    # 1) Exact match first (fast path)
    try:
        return ss.worksheet(title)
    except gspread.WorksheetNotFound:
        pass

    # 2) Fallback: normalized match (trim/collapse spaces, casefold)
    def norm(s: str) -> str:
        # remove all whitespace differences and lowercase
        return "".join(str(s).strip().split()).casefold()

    wanted = norm(title)
    for ws in ss.worksheets():
        if norm(ws.title) == wanted:
            return ws

    # 3) Create, but tolerate "already exists" races
    try:
        # Use low-level add with retries
        return _retry_gspread_call(lambda: ss.add_worksheet(title=title, rows=2, cols=max(1, cols)))
    except APIError as e:
        # If another process created it in-between, refetch exact
        if "already exists" in str(e).lower():
            return ss.worksheet(title)
        raise


# === Setup ===
def get_sql_engine(server, database, username, password):
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )
    return create_engine(connection_string)


def get_gsheet_client(credentials_file):
    """
    Authorize gspread using modern google-auth credentials (not oauth2client).
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


def get_sort_service(credentials_file):
    """
    Build the Google Sheets API service using the same google-auth credentials,
    but with an explicit per-request timeout.
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return _build_sheets_with_timeout(creds, timeout=30)


def set_number_format(service, spreadsheet_id, sheet_id, column_indexes: list[int], pattern="0"):
    """
    Applies raw number format to specific columns to prevent Google Sheets
    from shortening values (e.g., turning 16700000 into '16.7M').
    """
    requests = []
    for col_idx in column_indexes:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,  # skip header
                        "startColumnIndex": col_idx,
                        "endColumnIndex": col_idx + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": pattern}
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            }
        )

    body = {"requests": requests}
    req = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body)
    _safe_execute(req)


# --- Google API robustness helpers ---
def _build_sheets_with_timeout(creds, timeout: int = 30):
    """Build a Sheets service with an HTTP client that enforces timeouts."""
    http = AuthorizedHttp(credentials=creds, http=httplib2.Http(timeout=timeout))
    return build("sheets", "v4", cache_discovery=False, http=http)


def _is_transient_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout, ConnectionError, ssl.SSLError, HttpError)):
        if isinstance(exc, HttpError):
            try:
                code = int(exc.resp.status)
                return code >= 500 or code in (408, 429)
            except Exception:
                return True
        return True
    return False


def _safe_execute(request, *, retries: int = 5, base_sleep: float = 0.5, max_sleep: float = 5.0):
    """Execute googleapiclient request with bounded retries + jitter."""
    attempt = 0
    while True:
        try:
            # disable googleapiclient's internal retries; we handle retries ourselves
            return request.execute(num_retries=0)
        except Exception as exc:
            attempt += 1
            is_transient = _is_transient_error(exc)
            if attempt > retries or not is_transient:
                logger.log(
                    logger.WARNING if is_transient else logger.ERROR,
                    "[GSHEET] Request failed after %d attempts: %s",
                    attempt,
                    exc,
                    exc_info=True,
                )
                raise
            sleep_s = min(max_sleep, base_sleep * (2 ** (attempt - 1))) * random.uniform(0.8, 1.2)
            logger.info(
                "[GSHEET] Transient error (%s). Retry %d/%d in %.2fs",
                type(exc).__name__,
                attempt,
                retries,
                sleep_s,
            )
            time.sleep(sleep_s)


def _dfs_from_proc(engine, proc_sql: str, params: tuple = ()):
    """
    Execute a stored procedure (or any SQL batch) that returns multiple result sets.
    Returns: [DataFrame, DataFrame, ...] in order.
    """
    dfs = []
    raw_conn = engine.raw_connection()  # this is a pyodbc connection under SQLAlchemy
    try:
        cursor: pyodbc.Cursor = raw_conn.cursor()
        cursor.execute(proc_sql, params)
        while True:
            cols = [col[0] for col in cursor.description] if cursor.description else None
            if cols:
                rows = cursor.fetchall()
                df = pd.DataFrame.from_records(rows, columns=cols)
                dfs.append(df)
            if not cursor.nextset():
                break
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        raw_conn.close()
    return dfs


# --- Added helpers to extract details from gspread APIError / response ---
def _extract_api_error_details(e: Exception) -> dict:
    """
    Return a dict with keys: status_code, headers, text, json, status (if present), code (if present).
    Works for gspread.exceptions.APIError and requests.Response wrappers.
    """
    out = {
        "status_code": None,
        "headers": None,
        "text": None,
        "json": None,
        "status": None,
        "code": None,
    }
    try:
        # gspread.APIError often has .response attribute which is requests.Response
        resp = getattr(e, "response", None)
        if resp is not None:
            out["status_code"] = getattr(resp, "status_code", None)
            try:
                out["headers"] = dict(resp.headers) if getattr(resp, "headers", None) else {}
            except Exception:
                out["headers"] = None
            try:
                text = resp.text
                out["text"] = text[:4000] if isinstance(text, str) else str(text)[:4000]
            except Exception:
                out["text"] = None
            try:
                out["json"] = resp.json()
            except Exception:
                # sometimes response body is not JSON
                out["json"] = None
    except Exception:
        pass

    # gspread.APIError may also include a parsed dict as first arg
    try:
        if getattr(e, "args", None):
            first = e.args[0]
            if isinstance(first, dict):
                out["json"] = out["json"] or first
                out["code"] = out["code"] or first.get("code")
                out["status"] = out["status"] or first.get("status")
    except Exception:
        pass

    # fallback to string
    out["repr"] = str(e)[:2000]
    # If Retry-After header present, surface it as float (seconds) when possible
    try:
        headers = out.get("headers") or {}
        ra = headers.get("Retry-After") or headers.get("retry-after")
        if ra:
            try:
                out["retry_after"] = float(ra)
            except Exception:
                try:
                    # sometimes Retry-After is a date — ignore for now
                    out["retry_after"] = None
                except Exception:
                    out["retry_after"] = None
    except Exception:
        out["retry_after"] = None

    return out


def _is_retryable_gspread_details(details: dict) -> bool:
    """Return True if details indicate a retryable transient server-side problem."""
    sc = details.get("status_code")
    status = details.get("status")
    if status and str(status).upper() == "UNAVAILABLE":
        return True
    try:
        if sc:
            sc = int(sc)
            return sc >= 500 or sc in (429, 408)
    except Exception:
        pass
    # fallback to check repr
    if "unavailable" in str(details.get("repr", "")).lower():
        return True
    return False


def _retry_gspread_call(
    fn,
    *,
    retries: int = 5,
    base_sleep: float = 1.0,
    max_sleep: float = 20.0,
    action_desc: str = "gspread_call",
    correlation_id: str | None = None,
):
    """
    Generic wrapper to perform a gspread operation with retries on transient server errors.
    - fn: callable that performs the gspread call and returns a result.
    - returns fn() result or raises last exception.
    Logs details including headers/text and Retry-After when available.
    """
    attempt = 0
    while True:
        attempt += 1
        start = time.time()
        try:
            result = fn()
            elapsed = time.time() - start
            logger.debug(
                "[%s] correlation=%s action=%s attempt=%d success elapsed=%.3fs",
                platform.node(),
                correlation_id or "-",
                action_desc,
                attempt,
                elapsed,
            )
            return result
        except Exception as exc:
            elapsed = time.time() - start
            details = _extract_api_error_details(exc)
            retryable = _is_retryable_gspread_details(details)
            logger.warning(
                "[%s] correlation=%s action=%s attempt=%d failed elapsed=%.3fs retryable=%s status=%s code=%s repr=%s",
                platform.node(),
                correlation_id or "-",
                action_desc,
                attempt,
                elapsed,
                retryable,
                details.get("status") or details.get("status_code"),
                details.get("code"),
                (details.get("repr") or "")[:400],
            )
            # log headers + json at debug level
            logger.debug(
                "[%s] correlation=%s action=%s attempt=%d headers=%s json=%s text(trunc)=%s",
                platform.node(),
                correlation_id or "-",
                action_desc,
                attempt,
                details.get("headers"),
                (
                    json.dumps(details.get("json"), default=str)[:2000]
                    if details.get("json")
                    else None
                ),
                details.get("text"),
            )

            if not retryable or attempt >= retries:
                logger.exception(
                    "[%s] correlation=%s action=%s giving up after %d attempts",
                    platform.node(),
                    correlation_id or "-",
                    action_desc,
                    attempt,
                )
                raise
            # respect Retry-After header if present
            retry_after = details.get("retry_after")
            if retry_after and isinstance(retry_after, (int, float)):
                sleep_s = float(retry_after)
            else:
                # exponential backoff with jitter
                sleep_s = min(max_sleep, base_sleep * (2 ** (attempt - 1))) * random.uniform(
                    0.8, 1.2
                )
            logger.info(
                "[%s] correlation=%s action=%s retrying attempt=%d/%d in %.2fs (retryable=%s)",
                platform.node(),
                correlation_id or "-",
                action_desc,
                attempt,
                retries,
                sleep_s,
                retryable,
            )
            time.sleep(sleep_s)


# --- NEW: KVK proc export (10 result sets) ---
_KVK_TABS_IN_ORDER = [
    "KVK_Scan_Log",
    "KVK_Windows",
    "KVK_DKP_Weights",
    "KVK_Player_Windowed",
    "KVK_Kingdom_Windowed",
    "KVK_Camp_Windowed",
    "KVK_Player_Full",
    "KVK_Kingdom_Full",
    "KVK_Camp_Full",
    "KVK_Ingest_Negatives",
]

# Optional: light formatting hints per tab (column names must exist to apply)
_KVK_FORMAT_NUMBERS = {
    "KVK_Player_Windowed": [
        "governor_id",
        "starting_power",
        "kp_gain",
        "kp_gain_recalc",
        "kills_gain",
        "t4_kills",
        "t5_kills",
        "kp_loss",
        "healed_troops",
        "deads",
        "last_scan_id",
    ],
    "KVK_Player_Full": [
        "governor_id",
        "starting_power",
        "kp_gain",
        "kills_gain",
        "t4_kills",
        "t5_kills",
        "kp_loss",
        "healed_troops",
        "deads",
        "last_scan_id",
    ],
    "KVK_Kingdom_Windowed": [
        "campid",
        "kingdom",
        "kp_gain",
        "kills_gain",
        "t4_kills",
        "t5_kills",
        "kp_loss",
        "healed_troops",
        "deads",
        "last_scan_id",
    ],
    "KVK_Kingdom_Full": [
        "campid",
        "kingdom",
        "kp_gain",
        "kills_gain",
        "t4_kills",
        "t5_kills",
        "kp_loss",
        "healed_troops",
        "deads",
        "last_scan_id",
    ],
    "KVK_Camp_Windowed": [
        "campid",
        "kp_gain",
        "kills_gain",
        "t4_kills",
        "t5_kills",
        "kp_loss",
        "healed_troops",
        "deads",
        "last_scan_id",
    ],
    "KVK_Camp_Full": [
        "campid",
        "kp_gain",
        "kills_gain",
        "t4_kills",
        "t5_kills",
        "kp_loss",
        "healed_troops",
        "deads",
        "last_scan_id",
    ],
}

_KVK_DATE_COLS = {
    "KVK_Scan_Log": ["ScanTimestampUTC", "ImportedAtUTC"],
    "KVK_DKP_Weights": ["EffectiveFromUTC"],
}


def run_kvk_proc_exports(
    server,
    database,
    username,
    password,
    kvk_no: int,
    sheet_name: str = "KVK LIST",
    credentials_file=CREDENTIALS_FILE,
):
    """
    Executes KVK.sp_KVK_Get_Exports @KVK_NO=? and publishes the 10 result sets
    into tabs of `sheet_name` with matching names in _KVK_TABS_IN_ORDER.
    """
    assert all([server, database, username, password, credentials_file])

    engine = get_sql_engine(server, database, username, password)
    client = get_gsheet_client(credentials_file)
    service = get_sort_service(credentials_file)

    # 1) Run proc and capture all result sets in order
    dfs = _dfs_from_proc(engine, "EXEC KVK.sp_KVK_Get_Exports @KVK_NO = ?", (kvk_no,))
    if len(dfs) != len(_KVK_TABS_IN_ORDER):
        raise RuntimeError(f"Expected {len(_KVK_TABS_IN_ORDER)} result sets, got {len(dfs)}")

    # 2) Push each DF to its tab
    # wrap client.open in retry
    ss = _retry_gspread_call(
        lambda: client.open(sheet_name), action_desc=f"open_spreadsheet:{sheet_name}"
    )
    for df, tab in zip(dfs, _KVK_TABS_IN_ORDER, strict=False):
        # Keep consistent types for Google Sheets
        df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
        df = df.fillna("")

        # 🔧 NEW: ensure ALL datetime-like values are strings
        _stringify_datetimes_inplace(df)

        ws = _get_or_create_ws(ss, tab, cols=len(df.columns))

        export_dataframe_to_sheet(
            ws, df, service=service, format_columns=_KVK_FORMAT_NUMBERS.get(tab, [])
        )

    return True


def _aggregate_windowed_dfs(
    dfs: list[pd.DataFrame], window_names: list[str], src_idx: int, agg_type: str
):
    """
    Aggregate (sum) numeric columns across a list of dfs filtered by specific WindowName values.
    - dfs: list of result-set DataFrames returned by proc (same ordering as _KVK_TABS_IN_ORDER)
    - window_names: list of window display names to include (e.g., ["Pass 4", "1st Altar"])
    - src_idx: index into dfs for which type (3=Player,4=Kingdom,5=Camp)
    - agg_type: 'player'|'kingdom'|'camp' - used to select grouping keys
    Returns aggregated DataFrame (may be empty).
    """
    if src_idx >= len(dfs):
        return pd.DataFrame()

    df_src = dfs[src_idx].copy()
    if df_src.empty:
        return pd.DataFrame()

    # Filter rows for specified windows
    if "WindowName" in df_src.columns:
        df_filtered = df_src[df_src["WindowName"].isin(window_names)].copy()
    else:
        df_filtered = df_src.copy()

    if df_filtered.empty:
        return pd.DataFrame()

    # Determine group keys
    if agg_type == "player":
        group_keys = [
            k for k in ["governor_id", "name", "kingdom", "campid"] if k in df_filtered.columns
        ]
    elif agg_type == "kingdom":
        group_keys = [k for k in ["kingdom", "campid", "camp_name"] if k in df_filtered.columns]
    else:  # camp
        group_keys = [k for k in ["campid", "camp_name"] if k in df_filtered.columns]

    # Numeric columns to sum
    numeric_cols = [c for c in df_filtered.columns if pd.api.types.is_numeric_dtype(df_filtered[c])]
    # Exclude identifiers accidentally numeric (like campid/governor_id sometimes numeric we want to keep)
    numeric_cols = [c for c in numeric_cols if c not in group_keys]

    # Perform aggregation: sum numeric columns, keep first of non-numeric columns
    agg_dict = {c: "sum" for c in numeric_cols}
    # For non-numeric, keep first
    nonagg_cols = [c for c in df_filtered.columns if c not in numeric_cols and c not in group_keys]
    for c in nonagg_cols:
        agg_dict[c] = "first"

    # If no group keys exist, just sum all numeric columns across all rows and return a single-row DF
    if not group_keys:
        summed = df_filtered[numeric_cols].sum(numeric_only=True).to_frame().T
        # attach any non-numeric firsts as columns
        for c in nonagg_cols:
            summed[c] = df_filtered[c].astype(object).iat[0] if not df_filtered[c].empty else ""
        return summed

    grouped = df_filtered.groupby(group_keys, dropna=False).agg(agg_dict).reset_index()
    # Add a WindowName column to indicate this is an aggregate across windows
    if "WindowName" in grouped.columns:
        grouped["WindowName"] = "ALL_WINDOWS"
    else:
        grouped.insert(0, "WindowName", "ALL_WINDOWS")
    return grouped


def _safe_send_embed(
    notify_channel, bot_loop, embed: discord.Embed, view: discord.ui.View | None = None
):
    """Schedule sending an embed on the bot loop safely."""
    if not notify_channel or not bot_loop:
        return
    try:
        asyncio.run_coroutine_threadsafe(notify_channel.send(embed=embed, view=view), bot_loop)
    except Exception:
        logger.exception("Failed to schedule embed send")


# New async helper that constructs the View on the event loop and sends the message.
async def _send_embed_with_buttons_async(
    notify_channel, embed: discord.Embed, buttons: list[tuple[str, str]] | None = None
):
    """
    Buttons: list of (label, url) tuples. Created on the event loop to avoid cross-thread UI issues.
    """
    try:
        view = None
        if buttons:
            view = discord.ui.View()
            # create link-style buttons; safe-guard label length if needed
            for label, url in buttons:
                try:
                    view.add_item(
                        discord.ui.Button(
                            label=str(label)[:100], url=str(url), style=discord.ButtonStyle.link
                        )
                    )
                except Exception:
                    logger.exception("Failed to add button for %s -> %s", label, url)
                    # continue adding others
        await notify_channel.send(embed=embed, view=view)
    except Exception:
        logger.exception("Failed to send embed with buttons")


def _safe_send_embed_with_buttons(
    notify_channel, bot_loop, embed: discord.Embed, buttons: list[tuple[str, str]] | None = None
):
    """
    Thread-safe scheduling helper that will create the View and Buttons on the bot loop.
    Use this in contexts where this module might be running off the main event loop.
    """
    if not notify_channel or not bot_loop:
        return
    try:
        asyncio.run_coroutine_threadsafe(
            _send_embed_with_buttons_async(notify_channel, embed, buttons=buttons), bot_loop
        )
    except Exception:
        logger.exception("Failed to schedule embed-with-buttons send")


def create_additional_kvk_spreadsheets(
    dfs: list[pd.DataFrame],
    client: gspread.Client,
    service,
    kvk_no: int,
    notify_channel=None,
    bot_loop=None,
):
    """
    Create/Update the PASS4, 1ST_ALTAR and PASS7 style spreadsheets based on dfs from the proc.
    Returns a dict containing results for each target spreadsheet:
      {
        "KVK_PASS4_ALL_PLAYER_OUTPUT": {created: bool, spreadsheet_url, written_tabs: [...], skipped_tabs: [...]},
        "KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT": {...},
        "KVK_PASS7_ALL_PLAYER_OUTPUT": {...}
      }
    This function does NOT send Discord notifications by itself unless notify_channel and bot_loop are provided;
    it will still return metadata so callers (or tests) can assert on results.
    """
    results = {}

    def _create_and_write(target_ss_name: str, tabs_to_write: list[dict]):
        """
        tabs_to_write: list of dicts:
          {
            "type": "filtered" | "raw" | "aggregate",
            "src_idx": index in dfs (for filtered/raw/aggregate),
            "filter_window": optional window name (for filtered),
            "target_tab": sheet tab name,
            "agg_windows": list of window names for 'aggregate' type,
            "agg_type": 'player'|'kingdom'|'camp' for aggregate logic
          }
        Only creates the spreadsheet and tabs if there is at least one non-empty DF among the tabs_to_write.
        Returns a metadata dict.
        """
        # Pre-evaluate which specs would produce data
        to_write_results = []
        for spec in tabs_to_write:
            src_idx = spec.get("src_idx")
            df_candidate = pd.DataFrame()
            try:
                if spec["type"] == "raw":
                    if src_idx is not None and src_idx < len(dfs):
                        df_candidate = dfs[src_idx].copy()
                    else:
                        df_candidate = pd.DataFrame()
                elif spec["type"] == "filtered":
                    if src_idx is not None and src_idx < len(dfs):
                        df_src = dfs[src_idx].copy()
                        if "WindowName" in df_src.columns and spec.get("filter_window"):
                            df_candidate = df_src.loc[
                                df_src["WindowName"] == spec["filter_window"]
                            ].copy()
                        else:
                            df_candidate = pd.DataFrame()
                    else:
                        df_candidate = pd.DataFrame()
                elif spec["type"] == "aggregate":
                    agg_windows = spec.get("agg_windows", [])
                    agg_type = spec.get("agg_type", "player")
                    df_candidate = _aggregate_windowed_dfs(
                        dfs, agg_windows, spec.get("src_idx"), agg_type
                    )
                else:
                    df_candidate = pd.DataFrame()
            except Exception:
                logger.exception("Error while evaluating spec %s for %s", spec, target_ss_name)
                df_candidate = pd.DataFrame()

            has_data = not (df_candidate is None or df_candidate.empty)
            to_write_results.append((spec, df_candidate, has_data))

        # If nothing has data, skip creating the spreadsheet at all
        any_has_data = any(has_data for (_, _, has_data) in to_write_results)
        if not any_has_data:
            logger.info(
                "Skipping creation of %s because no tabs had data to write.", target_ss_name
            )
            return {
                "created": False,
                "reason": "no_data",
                "written_tabs": [],
                "skipped_tabs": [spec["target_tab"] for spec in tabs_to_write],
            }

        # Create/open spreadsheet now that we know there is something to write
        try:
            try:
                target_ss = _retry_gspread_call(
                    lambda: client.open(target_ss_name),
                    action_desc=f"open_spreadsheet:{target_ss_name}",
                )
                created_new = False
            except SpreadsheetNotFound:
                target_ss = _retry_gspread_call(
                    lambda: client.create(target_ss_name),
                    action_desc=f"create_spreadsheet:{target_ss_name}",
                )
                created_new = True
        except Exception as e:
            logger.exception("Could not open/create spreadsheet %s: %s", target_ss_name, e)
            return {
                "created": False,
                "reason": "create_failed",
                "error": str(e),
                "written_tabs": [],
                "skipped_tabs": [spec["target_tab"] for spec in tabs_to_write],
            }

        # Ensure we have a reliable spreadsheet_id and spreadsheet_url for notifications
        spreadsheet_id = getattr(target_ss, "id", None)
        if not spreadsheet_id:
            # gspread sometimes stores raw properties under _properties
            try:
                spreadsheet_id = getattr(target_ss, "_properties", {}).get("spreadsheetId")
            except Exception:
                spreadsheet_id = None

        # If we just created it, re-open by key to ensure consistent attributes from gspread
        try:
            if created_new and spreadsheet_id:
                try:
                    target_ss = _retry_gspread_call(
                        lambda: client.open_by_key(spreadsheet_id),
                        action_desc=f"open_by_key:{spreadsheet_id}",
                    )
                except Exception:
                    # best effort: continue with original target_ss if re-open fails
                    pass
        except Exception:
            pass

        # canonical url
        spreadsheet_url = None
        if spreadsheet_id:
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

        written = []
        skipped = []
        # Write only those tabs that have data (we already evaluated)
        for spec, df_candidate, has_data in to_write_results:
            target_tab = spec["target_tab"]
            if not has_data:
                skipped.append(target_tab)
                logger.info(
                    "Skipping tab %s in %s because there is no data to write.",
                    target_tab,
                    target_ss_name,
                )
                continue

            df_to_write = df_candidate.copy()
            # Normalize and stringify dates
            if df_to_write is None:
                df_to_write = pd.DataFrame()
            if not df_to_write.empty:
                df_to_write.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
                df_to_write = df_to_write.fillna("")
                _stringify_datetimes_inplace(df_to_write)

                try:
                    ws = _get_or_create_ws(
                        target_ss, target_tab, cols=max(1, len(df_to_write.columns))
                    )
                    # Determine format columns from original mappings where relevant
                    format_cols = []
                    if spec.get("agg_type") == "player" or spec.get("src_idx") == 3:
                        format_cols = _KVK_FORMAT_NUMBERS.get("KVK_Player_Windowed", [])
                    elif spec.get("agg_type") == "kingdom" or spec.get("src_idx") == 4:
                        format_cols = _KVK_FORMAT_NUMBERS.get("KVK_Kingdom_Windowed", [])
                    elif spec.get("agg_type") == "camp" or spec.get("src_idx") == 5:
                        format_cols = _KVK_FORMAT_NUMBERS.get("KVK_Camp_Windowed", [])
                    else:
                        format_cols = []

                    export_dataframe_to_sheet(
                        ws, df_to_write, service=service, format_columns=format_cols
                    )
                    written.append(target_tab)
                    logger.info(
                        "Wrote tab %s in %s (%d rows, %d cols)",
                        target_tab,
                        target_ss_name,
                        len(df_to_write.index),
                        len(df_to_write.columns),
                    )
                except Exception:
                    logger.exception("Failed to write tab %s in %s", target_tab, target_ss_name)
                    skipped.append(target_tab)
            else:
                skipped.append(target_tab)
                logger.info(
                    "Skipping tab %s in %s because there is no data to write.",
                    target_tab,
                    target_ss_name,
                )

        # Return metadata including spreadsheet id/url for notifications
        out = {
            "created": True,
            "created_new": created_new,
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "written_tabs": written,
            "skipped_tabs": skipped,
        }
        return out

    # Build specs for each of the three new spreadsheets

    # 1) KVK_PASS4_ALL_PLAYER_OUTPUT (Pass 4 only)
    pass4_specs = [
        # add KVK_Scan_Log (src_idx 0) so PASS4 sheet includes the same scan log as KVK_ALLPLAYER_OUTPUT
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {"type": "filtered", "src_idx": 3, "filter_window": "Pass 4", "target_tab": "PASS4_PLAYER"},
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "Pass 4",
            "target_tab": "PASS4_KINGDOM",
        },
        {"type": "filtered", "src_idx": 5, "filter_window": "Pass 4", "target_tab": "PASS4_CAMP"},
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
    ]

    # Quick, cheap pre-check: produce PASS4 spreadsheet only if PASS4_PLAYER (src_idx=3 filtered by "Pass 4") has data.
    try:
        has_pass4_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_pass4_player = not df3[df3["WindowName"] == "Pass 4"].empty
            else:
                has_pass4_player = False
    except Exception:
        has_pass4_player = False

    if has_pass4_player:
        pass4_result = _create_and_write("KVK_PASS4_ALL_PLAYER_OUTPUT", pass4_specs)
    else:
        # No primary data => skip creating spreadsheet
        pass4_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in pass4_specs],
        }
    results["KVK_PASS4_ALL_PLAYER_OUTPUT"] = pass4_result

    # 2) KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT
    # includes 1st Altar filtered tabs, KVK_Windows, KVK_DKP_Weights, and KVK_ALL_WINDOWS_* = Pass4 + 1st Altar
    altar_specs = [
        # include scan log to mirror primary output
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {
            "type": "filtered",
            "src_idx": 3,
            "filter_window": "1st Altar",
            "target_tab": "1ST_ALTAR_PLAYER",
        },
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "1st Altar",
            "target_tab": "1ST_ALTAR_KINGDOM",
        },
        {
            "type": "filtered",
            "src_idx": 5,
            "filter_window": "1st Altar",
            "target_tab": "1ST_ALTAR_CAMP",
        },
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        # Aggregates: Pass 4 + 1st Altar
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": ["Pass 4", "1st Altar"],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": ["Pass 4", "1st Altar"],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": ["Pass 4", "1st Altar"],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    # Produce 1st Altar spreadsheet only if 1ST_ALTAR_PLAYER (src_idx=3 filtered by "1st Altar") has data.
    try:
        has_altar_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_altar_player = not df3[df3["WindowName"] == "1st Altar"].empty
            else:
                has_altar_player = False
    except Exception:
        has_altar_player = False

    if has_altar_player:
        altar_result = _create_and_write("KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT", altar_specs)
    else:
        altar_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in altar_specs],
        }
    results["KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT"] = altar_result

    # 3) KVK_PASS7_ALL_PLAYER_OUTPUT
    # includes Pass7 filtered tabs, KVK_Windows, KVK_DKP_Weights, and KVK_ALL_WINDOWS_* = Pass4 + 1st Altar + Pass7
    pass7_specs = [
        # include scan log to mirror primary output
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {"type": "filtered", "src_idx": 3, "filter_window": "Pass 7", "target_tab": "PASS7_PLAYER"},
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "Pass 7",
            "target_tab": "PASS7_KINGDOM",
        },
        {"type": "filtered", "src_idx": 5, "filter_window": "Pass 7", "target_tab": "PASS7_CAMP"},
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        # Aggregates: Pass 4 + 1st Altar + Pass 7
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": ["Pass 4", "1st Altar", "Pass 7"],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": ["Pass 4", "1st Altar", "Pass 7"],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": ["Pass 4", "1st Altar", "Pass 7"],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    # Produce PASS7 spreadsheet only if PASS7_PLAYER (src_idx=3 filtered by "Pass 7") has data.
    try:
        has_pass7_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_pass7_player = not df3[df3["WindowName"] == "Pass 7"].empty
            else:
                has_pass7_player = False
    except Exception:
        has_pass7_player = False

    if has_pass7_player:
        pass7_result = _create_and_write("KVK_PASS7_ALL_PLAYER_OUTPUT", pass7_specs)
    else:
        pass7_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in pass7_specs],
        }
    results["KVK_PASS7_ALL_PLAYER_OUTPUT"] = pass7_result

    # --- NEW: log metadata for verification (IDs/URLs etc)
    try:
        logger.info(
            "create_additional_kvk_spreadsheets results for KVK %s:\n%s",
            kvk_no,
            json.dumps(results, indent=2, default=str),
        )
    except Exception:
        logger.exception("Failed to log additional KVK spreadsheets metadata")

    # Optionally send a single consolidated notification embed with buttons (if notify_channel/bot_loop provided)
    if notify_channel and bot_loop:
        try:
            created_items = [(name, meta) for name, meta in results.items() if meta.get("created")]
            skipped_items = [
                (name, meta) for name, meta in results.items() if not meta.get("created")
            ]

            if created_items:
                title = f"📤 Export complete: KVK {kvk_no} → Additional Sheets"
                color = discord.Color.green()
                desc = f"Created {len(created_items)} additional spreadsheet(s)."
            else:
                title = f"ℹ️ Export skipped: KVK {kvk_no} → Additional Sheets"
                color = discord.Color.blue()
                desc = "No additional spreadsheets were created."

            embed = discord.Embed(title=title, description=desc, color=color)

            if created_items:
                created_names = []
                for name, meta in created_items:
                    created_names.append(name)
                embed.add_field(
                    name="Created",
                    value=", ".join(created_names),
                    inline=False,
                )

            if skipped_items:
                skipped_msgs = []
                for name, meta in skipped_items:
                    reason = meta.get("reason", "no_data")
                    skipped_msgs.append(f"{name} ({reason})")
                embed.add_field(name="Skipped", value=", ".join(skipped_msgs), inline=False)

            # Optionally include written / skipped tabs summary per created sheet (concise)
            details_lines = []
            for name, meta in created_items:
                wt = meta.get("written_tabs") or []
                st = meta.get("skipped_tabs") or []
                details_lines.append(f"{name}: wrote {len(wt)} tab(s), skipped {len(st)} tab(s)")
            if details_lines:
                embed.add_field(name="Details", value="\n".join(details_lines), inline=False)

            # Build simple buttons metadata (label, url) and schedule send on bot loop,
            # creating the actual discord.ui.View on the event loop to avoid cross-thread UI issues.
            buttons = []
            try:
                if created_items:
                    # limit to 5 buttons to be safe; should be <=3 in our use-case
                    for name, meta in created_items[:5]:
                        ss_url = meta.get("spreadsheet_url")
                        if ss_url:
                            buttons.append((name, ss_url))
            except Exception:
                # Ensure nothing breaks the notification path; buttons optional
                logger.exception("Failed to collect button metadata for created additional sheets")

            # schedule send on bot loop, creating view there
            _safe_send_embed_with_buttons(notify_channel, bot_loop, embed, buttons=buttons)
        except Exception:
            logger.exception("Failed sending consolidated notification for additional spreadsheets")

    return results


def run_kvk_proc_exports_with_alerts(
    server,
    database,
    username,
    password,
    kvk_no: int,
    sheet_name: str = "KVK LIST",
    credentials_file=CREDENTIALS_FILE,
    notify_channel=None,
    bot_loop=None,
):
    retries = 3
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            ok = run_kvk_proc_exports(
                server, database, username, password, kvk_no, sheet_name, credentials_file
            )
            if ok:
                # After successful creation of primary sheet, also create the PASS4 + 1st Altar + PASS7 spreadsheets.
                try:
                    engine = get_sql_engine(server, database, username, password)
                    dfs = _dfs_from_proc(
                        engine, "EXEC KVK.sp_KVK_Get_Exports @KVK_NO = ?", (kvk_no,)
                    )

                    client = get_gsheet_client(credentials_file)
                    service = get_sort_service(credentials_file)

                    # create additional spreadsheets (no assignment needed here)
                    create_additional_kvk_spreadsheets(
                        dfs,
                        client,
                        service,
                        kvk_no,
                        notify_channel=notify_channel,
                        bot_loop=bot_loop,
                    )

                    return True
                except Exception as second_exc:
                    # log and optionally alert about failure creating the additional outputs but do not treat as overall proc failure
                    logger.exception("Failed to create additional KVK spreadsheets: %s", second_exc)
                    if notify_channel and bot_loop:
                        try:
                            embed = discord.Embed(
                                title="⚠️ Additional KVK Sheet Creation Failed",
                                description=f"KVK `{kvk_no}` → Additional PASS4/ALTAR/PASS7 outputs",
                                color=discord.Color.orange(),
                            )
                            embed.add_field(
                                name="Error",
                                value=f"```{type(second_exc).__name__}: {str(second_exc)[:900]}```",
                                inline=False,
                            )
                            asyncio.run_coroutine_threadsafe(
                                notify_channel.send(embed=embed), bot_loop
                            )
                        except Exception:
                            pass
                return True
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(min(10, 2**attempt))
    # alert on failure
    if notify_channel and bot_loop:
        try:
            embed = discord.Embed(
                title="🚨 KVK Export Failed",
                description=f"KVK `{kvk_no}` → Sheet `{sheet_name}`",
                color=discord.Color.red(),
            )
            embed.add_field(
                name="Error",
                value=f"```{type(last_exc).__name__}: {str(last_exc)[:900]}```",
                inline=False,
            )
            asyncio.run_coroutine_threadsafe(notify_channel.send(embed=embed), bot_loop)
        except Exception:
            pass
    return False


# === Sheet Ops ===
def export_dataframe_to_sheet(
    sheet, df, service=None, format_columns=None, correlation_id: str | None = None
):
    """
    Export DataFrame to worksheet with retries around gspread update operations.
    """
    # clear might fail transiently; wrap in retry
    _retry_gspread_call(
        lambda: sheet.clear(),
        action_desc=f"sheet.clear:{getattr(sheet,'title', '')}",
        correlation_id=correlation_id,
    )
    # optional jitter:
    time.sleep(random.uniform(0.1, 0.6))
    df = df.replace([float("inf"), float("-inf")], "").fillna("")
    rows = [df.columns.values.tolist()] + df.values.tolist()

    def _do_update():
        # gspread update might raise APIError; allow retry wrapper to handle it
        return sheet.update(rows)

    _retry_gspread_call(
        _do_update,
        action_desc=f"sheet.update:{getattr(sheet,'title', '')}",
        correlation_id=correlation_id,
    )

    if service and format_columns:
        sheet_id = getattr(sheet, "id", None)
        spreadsheet_id = getattr(sheet.spreadsheet, "id", None)
        # Convert column names to indexes
        col_indexes = [df.columns.get_loc(col) for col in format_columns if col in df.columns]
        if col_indexes and spreadsheet_id and sheet_id is not None:
            set_number_format(service, spreadsheet_id, sheet_id, col_indexes)

        missing = [col for col in format_columns if col not in df.columns]
        if missing:
            logger.warning(f"[GSHEET] format_columns not found in dataframe: {missing}")


def sort_sheet(service, spreadsheet_id, sheet_id, column_index, order="ASCENDING"):
    sort_request = {
        "requests": [
            {
                "sortRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": 0,
                    },
                    "sortSpecs": [{"dimensionIndex": column_index, "sortOrder": order}],
                }
            }
        ]
    }
    req = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=sort_request)
    _safe_execute(req)


# === Specific Transfers ===
def transfer_and_sort(
    engine,
    client,
    service,
    query,
    sheet_name,
    tab_name,
    sort_column_index=None,
    date_cols=None,
    sort_order="ASCENDING",
    format_columns=None,
):
    """
    Transfer a query to a sheet tab and optionally sort. Uses retry on the gspread open/worksheet operations.
    """
    correlation_id = str(uuid.uuid4())
    start_total = time.time()
    df = pd.read_sql(query, engine)

    if date_cols:
        for col in date_cols:
            df[col] = (
                pd.to_datetime(df[col], errors="coerce")
                .fillna(pd.Timestamp("1900-01-01"))
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

    # Open spreadsheet with retry wrapper
    ss = _retry_gspread_call(
        lambda: client.open(sheet_name),
        action_desc=f"open_spreadsheet:{sheet_name}",
        correlation_id=correlation_id,
    )
    # Obtain worksheet (worksheet() can raise WorksheetNotFound, so wrap)
    try:
        ws = _retry_gspread_call(
            lambda: ss.worksheet(tab_name),
            action_desc=f"get_worksheet:{sheet_name}>{tab_name}",
            correlation_id=correlation_id,
        )
    except gspread.WorksheetNotFound:
        # Create if not exists
        ws = _get_or_create_ws(ss, tab_name, cols=max(1, len(df.columns)))

    df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
    df = df.fillna("")

    export_dataframe_to_sheet(
        ws, df, service=service, format_columns=format_columns, correlation_id=correlation_id
    )

    elapsed_total = time.time() - start_total
    logger.info(
        "[transfer] correlation=%s exported %s > %s rows=%d cols=%d elapsed=%.3fs gspread=%s google-api-client=%s",
        correlation_id,
        sheet_name,
        tab_name,
        len(df.index),
        len(df.columns),
        elapsed_total,
        GSPREAD_VERSION,
        GOOGLE_API_CLIENT_VERSION,
    )
    print(f"[SUCCESS] Exported to {sheet_name} > {tab_name}")

    if sort_column_index is not None:
        sort_sheet(service, ws.spreadsheet.id, ws.id, sort_column_index, order=sort_order)
        print(
            f"[SUCCESS] Sorted {sheet_name} > {tab_name} by column {sort_column_index + 1} ({sort_order})"
        )


# === Validate JSON CONFIG FOR EXPORTS ===
def validate_export_config(config):
    required_fields = {"query", "sheet", "tab"}
    for i, job in enumerate(config):
        if not isinstance(job, dict):
            raise ValueError(f"Export job at index {i} is not a dictionary.")
        missing = required_fields - job.keys()
        if missing:
            raise ValueError(
                f"Export job at index {i} is missing required fields: {', '.join(missing)}"
            )
        if "dates" in job and not isinstance(job["dates"], list):
            raise ValueError(f"Export job at index {i} has 'dates' but it's not a list.")


# === Main Process ===
def run_all_exports(
    server,
    database,
    username,
    password,
    credentials_file=CREDENTIALS_FILE,
    notify_channel=None,
    bot_loop=None,
):

    assert all(
        [server, database, username, password, credentials_file]
    ), "One or more required parameters are missing"
    engine = get_sql_engine(server, database, username, password)
    client = get_gsheet_client(credentials_file)
    service = get_sort_service(credentials_file)

    log_messages = []

    def log(msg):
        print(msg)
        log_messages.append(msg)

    def wrapped_transfer(*args, **kwargs):
        retries = 5
        base_delay = 2.0  # seconds

        sheet_name = kwargs.get("sheet_name", "")
        tab_name = kwargs.get("tab_name", "")
        notify = kwargs.get("notify_channel")
        loop = kwargs.get("bot_loop")

        correlation_id = str(uuid.uuid4())

        e = None
        tb = ""

        for attempt in range(1, retries + 1):
            try:
                # filter non-transfer args (these aren't params of transfer_and_sort)
                safe_kwargs = {
                    k: v for k, v in kwargs.items() if k not in ("notify_channel", "bot_loop")
                }
                # add correlation id into the transfer indirectly by passing through client/service (they are closures)
                transfer_and_sort(*args, **safe_kwargs)
                return
            except APIError as ex:
                e = ex
                tb = traceback.format_exc()
                details = _extract_api_error_details(ex)
                retry_after = details.get("retry_after")
                msg = f"[⚠️ RETRY {attempt}] {sheet_name} > {tab_name}: GSheet APIError: {details.get('status') or details.get('status_code')}"
                # log detailed debug information
                logger.info(
                    "[wrapped_transfer] correlation=%s attempt=%d sheet=%s tab=%s api_status=%s retry_after=%s",
                    correlation_id,
                    attempt,
                    sheet_name,
                    tab_name,
                    details.get("status") or details.get("status_code"),
                    retry_after,
                )
            except Exception as ex:
                e = ex
                tb = traceback.format_exc()
                details = _extract_api_error_details(ex)
                msg = f"[⚠️ RETRY {attempt}] {sheet_name} > {tab_name}: General error: {e!s}"
                logger.info(
                    "[wrapped_transfer] correlation=%s attempt=%d sheet=%s tab=%s exception=%s",
                    correlation_id,
                    attempt,
                    sheet_name,
                    tab_name,
                    type(ex).__name__,
                )

            print(msg)
            print(tb)
            log_messages.append(msg)
            log_messages.append(tb)

            # determine if we should retry
            details = _extract_api_error_details(e)
            retryable = _is_retryable_gspread_details(details)
            if attempt < retries and retryable:
                # use Retry-After if present
                retry_after = details.get("retry_after")
                if retry_after and isinstance(retry_after, (int, float)):
                    delay = float(retry_after)
                else:
                    delay = min(20.0, base_delay * (2 ** (attempt - 1))) * random.uniform(0.8, 1.3)
                logger.info(
                    "[wrapped_transfer] correlation=%s will retry in %.2fs (attempt %d/%d) (retryable=%s)",
                    correlation_id,
                    delay,
                    attempt,
                    retries,
                    retryable,
                )
                time.sleep(delay)
                continue
            else:
                final_msg = (
                    f"[❌ FINAL FAIL] {sheet_name} > {tab_name} failed after {retries} attempts."
                )
                print(final_msg)
                log_messages.append(final_msg)

                if notify and loop:
                    try:
                        embed = discord.Embed(
                            title="🚨 Google Sheet Export Failed",
                            description=f"**Sheet:** `{sheet_name}`\n**Tab:** `{tab_name}`\n**Attempts:** {retries}\n**correlation_id:** `{correlation_id}`",
                            color=discord.Color.red(),
                        )
                        embed.add_field(name="Error", value=f"```{str(e)[:1000]}```", inline=False)
                        embed.add_field(name="Traceback", value=f"```{tb[-1000:]}```", inline=False)
                        embed.set_footer(
                            text=f"gsheet_module.py export failure | gspread={GSPREAD_VERSION} google-client={GOOGLE_API_CLIENT_VERSION}"
                        )

                        asyncio.run_coroutine_threadsafe(notify.send(embed=embed), loop)
                    except Exception as alert_error:
                        print(f"[⚠️ ALERT FAILURE] Could not send Discord alert: {alert_error}")
                break  # out of retry loop

    with open(CONFIG_FILE, encoding="utf-8") as f:
        export_jobs = json.load(f)

    validate_export_config(export_jobs)

    for job in export_jobs:
        job.setdefault("sort", None)
        job.setdefault("order", None)
        job.setdefault("dates", [])
        job.setdefault("format_numbers", [])
        wrapped_transfer(
            engine,
            client,
            service,
            query=job["query"],
            sheet_name=job["sheet"],
            tab_name=job["tab"],
            sort_column_index=job["sort"],
            sort_order=job["order"],
            date_cols=job["dates"],
            format_columns=job["format_numbers"],
            notify_channel=notify_channel,
            bot_loop=bot_loop,
        )

    return True, "\n".join(log_messages)


def run_single_export(
    server, database, username, password, config_path, credentials_file=CREDENTIALS_FILE
):
    assert all(
        [server, database, username, password, credentials_file]
    ), "One or more required parameters are missing"
    engine = get_sql_engine(server, database, username, password)
    client = get_gsheet_client(credentials_file)
    service = get_sort_service(credentials_file)

    with open(config_path, encoding="utf-8") as f:
        export_jobs = json.load(f)

    validate_export_config(export_jobs)

    for job in export_jobs:
        job.setdefault("format_numbers", [])
        transfer_and_sort(
            engine,
            client,
            service,
            query=job["query"],
            sheet_name=job["sheet"],
            tab_name=job["tab"],
            sort_column_index=job.get("sort"),
            sort_order=job.get("order", "ASCENDING"),
            date_cols=job.get("dates", []),
            format_columns=job["format_numbers"],
        )

    return True


def check_basic_gsheets_access(
    credentials_file: str, sheet_id: str, max_retries: int = 2, retry_backoff_sec: float = 1.0
):
    """
    Synchronous function that checks basic Google Sheets access.
    Returns (success: bool, message: str)
    Should not raise on transient network errors; instead return (False, message).
    """
    try:
        # Use same client creation path for consistent behavior
        client = get_gsheet_client(credentials_file)
    except Exception as e:
        logger.exception("Failed to create gspread client")
        return False, f"Failed to create gspread client: {e}"

    attempt = 0
    while attempt <= max_retries:
        try:
            attempt += 1
            sheet = _retry_gspread_call(
                lambda: client.open_by_key(sheet_id), action_desc=f"open_by_key:{sheet_id}"
            )
            # basic read to ensure metadata is accessible
            _ = sheet.sheet1.title  # just touching metadata
            # log diagnostic metadata
            try:
                logger.info(
                    "GSheets access check OK host=%s python=%s gspread=%s google-api-client=%s",
                    platform.node(),
                    sys.version.split()[0],
                    GSPREAD_VERSION,
                    GOOGLE_API_CLIENT_VERSION,
                )
            except Exception:
                pass
            return True, "GSheets access OK"
        except APIError as api_err:
            # gspread APIError contains HTTP code and message
            details = _extract_api_error_details(api_err)
            logger.warning(
                "GSheets APIError (attempt %s/%s): status=%s code=%s headers=%s",
                attempt,
                max_retries + 1,
                details.get("status") or details.get("status_code"),
                details.get("code"),
                details.get("headers"),
            )
            # If it's a transient server-side error, retry; otherwise return with info
            if attempt > max_retries:
                return False, f"APIError after {attempt} attempts: {details.get('repr')}"
        except requests.RequestException as req_err:
            # Network-level error from the requests layer
            logger.warning(
                "Network error contacting GSheets (attempt %s/%s): %s",
                attempt,
                max_retries + 1,
                req_err,
            )
            if attempt > max_retries:
                return False, f"Network error: {req_err}"
        except Exception as exc:
            logger.exception("Unexpected exception during GSheets check")
            return False, f"Unexpected exception: {exc}"

        # backoff before retrying
        time.sleep(retry_backoff_sec * attempt)

    return False, "GSheets check failed (unknown reason)"


# === Test helpers / manual export runner ===
def run_kvk_export_test(
    server,
    database,
    username,
    password,
    kvk_no: int,
    sheet_name: str = "KVK LIST",
    credentials_file=CREDENTIALS_FILE,
    create_primary: bool = True,
    export_pass4: bool = True,
    export_altar: bool = True,
    export_pass7: bool = True,
):
    """
    Run the export pipeline for a given KVK without needing an import.
    - If create_primary True, writes the main KVK LIST spreadsheet tabs (same as run_kvk_proc_exports).
    - Always evaluates and conditionally creates the PASS4 / 1ST ALTAR / PASS7 spreadsheets,
      but only creates each spreadsheet if it would contain at least one non-empty tab.
    - Returns a dict with metadata about what was written/skipped for each target spreadsheet.
    - Does not send Discord notifications (it's a test/manual API). Caller can inspect the returned metadata.
    Usage: call from an admin REPL or a test harness to verify exports end-to-end.
    """
    assert all([server, database, username, password, credentials_file])
    engine = get_sql_engine(server, database, username, password)
    client = get_gsheet_client(credentials_file)
    service = get_sort_service(credentials_file)

    # Run proc once and reuse dfs for everything (avoid double proc)
    dfs = _dfs_from_proc(engine, "EXEC KVK.sp_KVK_Get_Exports @KVK_NO = ?", (kvk_no,))
    if len(dfs) != len(_KVK_TABS_IN_ORDER):
        raise RuntimeError(f"Expected {len(_KVK_TABS_IN_ORDER)} result sets, got {len(dfs)}")

    meta = {"kvk_no": kvk_no, "primary": None, "additional": {}}

    if create_primary:
        # Write the normal primary sheet (KVK LIST)
        try:
            ss = _retry_gspread_call(
                lambda: client.open(sheet_name), action_desc=f"open_spreadsheet:{sheet_name}"
            )
        except SpreadsheetNotFound:
            ss = _retry_gspread_call(
                lambda: client.create(sheet_name), action_desc=f"create_spreadsheet:{sheet_name}"
            )
        written_tabs = []
        skipped_tabs = []
        for df, tab in zip(dfs, _KVK_TABS_IN_ORDER, strict=False):
            df_local = df.copy()
            df_local.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
            df_local = df_local.fillna("")
            _stringify_datetimes_inplace(df_local)
            if df_local is None or df_local.empty:
                # still create an empty tab (to preserve structure)
                ws = _get_or_create_ws(ss, tab, cols=max(1, len(df_local.columns)))
                export_dataframe_to_sheet(
                    ws,
                    pd.DataFrame(columns=df_local.columns),
                    service=service,
                    format_columns=_KVK_FORMAT_NUMBERS.get(tab, []),
                )
                skipped_tabs.append(tab)
            else:
                ws = _get_or_create_ws(ss, tab, cols=max(1, len(df_local.columns)))
                export_dataframe_to_sheet(
                    ws, df_local, service=service, format_columns=_KVK_FORMAT_NUMBERS.get(tab, [])
                )
                written_tabs.append(tab)
        meta["primary"] = {
            "spreadsheet_id": getattr(ss, "id", None),
            "spreadsheet_url": getattr(ss, "url", None)
            or f"https://docs.google.com/spreadsheets/d/{getattr(ss,'id','')}",
            "written_tabs": written_tabs,
            "skipped_tabs": skipped_tabs,
        }

    # Run the additional spreadsheets creation (this helper will skip creation if no data)
    client = get_gsheet_client(credentials_file)  # refresh client
    service = get_sort_service(credentials_file)
    additional_results = create_additional_kvk_spreadsheets(
        dfs, client, service, kvk_no, notify_channel=None, bot_loop=None
    )

    # Optionally remove results for PASS4/ALTAR/PASS7 if the caller disabled them
    if not export_pass4:
        additional_results.pop("KVK_PASS4_ALL_PLAYER_OUTPUT", None)
    if not export_altar:
        additional_results.pop("KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT", None)
    if not export_pass7:
        additional_results.pop("KVK_PASS7_ALL_PLAYER_OUTPUT", None)

    meta["additional"] = additional_results
    return meta


__all__ = [
    "check_basic_gsheets_access",
    "create_additional_kvk_spreadsheets",
    "get_gsheet_client",
    "get_sort_service",
    "run_all_exports",
    "run_kvk_export_test",
    "run_single_export",
]
