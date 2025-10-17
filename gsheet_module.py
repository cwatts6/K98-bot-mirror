# gsheet_module.py
import asyncio
import datetime as _dt
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

import random
import socket
import ssl
import time
import traceback

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
from sqlalchemy import create_engine

from constants import CONFIG_FILE, CREDENTIALS_FILE

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
        return ss.add_worksheet(title=title, rows=2, cols=max(1, cols))
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
    ss = client.open(sheet_name)
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
                return True
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(min(10, 2**attempt))
    # alert on failure
    if notify_channel and bot_loop:
        try:
            import asyncio

            import discord

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
def export_dataframe_to_sheet(sheet, df, service=None, format_columns=None):
    sheet.clear()
    # optional jitter:
    time.sleep(random.uniform(0.1, 0.6))
    df = df.replace([float("inf"), float("-inf")], "").fillna("")
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

    if service and format_columns:
        sheet_id = sheet.id
        spreadsheet_id = sheet.spreadsheet.id
        # Convert column names to indexes
        col_indexes = [df.columns.get_loc(col) for col in format_columns if col in df.columns]
        if col_indexes:
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
    df = pd.read_sql(query, engine)

    if date_cols:
        for col in date_cols:
            df[col] = (
                pd.to_datetime(df[col], errors="coerce")
                .fillna(pd.Timestamp("1900-01-01"))
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

    sheet = client.open(sheet_name).worksheet(tab_name)
    df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
    df = df.fillna("")

    export_dataframe_to_sheet(sheet, df, service=service, format_columns=format_columns)

    print(f"[SUCCESS] Exported to {sheet_name} > {tab_name}")

    if sort_column_index is not None:
        sort_sheet(service, sheet.spreadsheet.id, sheet.id, sort_column_index, order=sort_order)
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

        e = None
        tb = ""

        for attempt in range(1, retries + 1):
            try:
                # filter non-transfer args (these aren't params of transfer_and_sort)
                safe_kwargs = {
                    k: v for k, v in kwargs.items() if k not in ("notify_channel", "bot_loop")
                }
                transfer_and_sort(*args, **safe_kwargs)
                return
            except APIError as ex:
                e = ex
                tb = traceback.format_exc()
                msg = f"[⚠️ RETRY {attempt}] {sheet_name} > {tab_name}: GSheet APIError: {e!s}"
            except Exception as ex:
                e = ex
                tb = traceback.format_exc()
                msg = f"[⚠️ RETRY {attempt}] {sheet_name} > {tab_name}: General error: {e!s}"

            print(msg)
            print(tb)
            log_messages.append(msg)
            log_messages.append(tb)

            if attempt < retries:
                delay = min(20.0, base_delay * (2 ** (attempt - 1))) * random.uniform(0.8, 1.3)
                time.sleep(delay)
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
                            description=f"**Sheet:** `{sheet_name}`\n**Tab:** `{tab_name}`\n**Attempts:** {retries}",
                            color=discord.Color.red(),
                        )
                        embed.add_field(name="Error", value=f"```{str(e)[:1000]}```", inline=False)
                        embed.add_field(name="Traceback", value=f"```{tb[-1000:]}```", inline=False)
                        embed.set_footer(text="gsheet_module.py export failure")

                        asyncio.run_coroutine_threadsafe(notify.send(embed=embed), loop)
                    except Exception as alert_error:
                        print(f"[⚠️ ALERT FAILURE] Could not send Discord alert: {alert_error}")

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


def check_basic_gsheets_access(credentials_file, sheet_id, test_cell="Z1", test_value=None):
    """
    Performs a minimal write/read test on the first worksheet of the specified Google Sheet.
    Returns (success: bool, message: str)
    """
    try:
        client = get_gsheet_client(credentials_file)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheets()[
            0
        ]  # Alternatively: worksheet = sheet.worksheet("YourTabName")

        if test_value is None:
            test_value = f"✅ BOT_TEST {datetime.utcnow().strftime('%H:%M:%S')}"

        worksheet.update(test_cell, [[test_value]])
        read_back = worksheet.acell(test_cell).value
        worksheet.update(test_cell, [[""]])  # Clear after test

        if read_back != test_value:
            return False, "Read-after-write failed"

        return True, "Access OK (read/write verified)"
    except SpreadsheetNotFound:
        return False, "Spreadsheet not found"
    except APIError as e:
        return False, f"APIError: {str(e)[:100]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"


__all__ = [
    "check_basic_gsheets_access",
    "get_gsheet_client",
    "get_sort_service",
    "run_all_exports",
    "run_single_export",
]
