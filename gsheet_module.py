# gsheet_module.py
# Hardened Google Sheets helpers and full export pipeline (complete file)
# - uses requests + urllib3 Retry + AuthorizedSession for robust transport
# - unified safe execute + retry wrappers with full-jitter backoff
# - preserves original public API: run_all_exports, run_single_export, etc.
# - includes stored-proc multi-result helper _dfs_from_proc and other SQL helpers
from __future__ import annotations

import asyncio
from collections.abc import Callable
import datetime as _dt
import json
import logging
import os
import platform
import random
import ssl
import sys
import time
import traceback
from typing import Any
import uuid

import discord
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build as google_build
import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound
import numpy as np  # NEW: needed for robust numeric coercion
import pandas as pd
from pandas.api import types as ptypes
import pyodbc
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import create_engine
from urllib3.util.retry import Retry

from constants import CONFIG_FILE, CREDENTIALS_FILE
from sheet_importer import detect_transient_error

logger = logging.getLogger(__name__)

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
GOOGLE_API_CLIENT_VERSION = _get_dist_version("google-api-python-client") or "unknown"

# Config defaults (can be overridden by env vars)
DEFAULT_SHEETS_TIMEOUT = int(os.getenv("GSHEETS_HTTP_TIMEOUT", "60"))
DEFAULT_SHEETS_MAX_RETRIES = int(os.getenv("GSHEETS_MAX_RETRIES", "3"))
DEFAULT_SHEETS_BACKOFF_FACTOR = float(os.getenv("GSHEETS_BACKOFF_FACTOR", "0.5"))

if CREDENTIALS_FILE is None:
    raise RuntimeError("GOOGLE_CREDENTIALS_FILE not set in .env")


# -------------------------
# Utility helpers
# -------------------------
def _full_jitter_sleep(attempt: int, base: float, cap: float) -> float:
    """
    Full jitter sleep: uniform(0, min(cap, base * 2^(attempt-1))).
    """
    cap_val = min(cap, base * (2 ** (attempt - 1)))
    return random.uniform(0, cap_val)


def _record_sheets_error(kind: str, exc: Exception) -> None:
    """
    Lightweight hook to record sheets error metrics.
    Tries to record via usage_tracker if available; otherwise logs a structured warning.
    """
    try:
        # usage_tracker exists in repo and accepts usage events in many places
        # We'll attempt to call a common function; if not present, fallback to logging.
        from usage_tracker import usage_event

        try:
            usage_event(f"gsheets_error_{kind}", 1)
        except Exception:
            logger.warning("[GSHEETS_METRIC] failed to emit usage_event for %s: %s", kind, exc)
    except Exception:
        # Fallback: log a structured warning so external log processors can pick it up
        logger.warning(
            "[GSHEETS_METRIC] {kind}=1; exc=%s", str(exc), extra={"gsheets_error_kind": kind}
        )


# -------------------------
# Transport builder (requests + urllib3 Retry + AuthorizedSession)
# -------------------------
def _build_sheets_with_timeout(
    creds: Credentials,
    timeout: int | None = None,
    *,
    max_retries: int | None = None,
    backoff_factor: float | None = None,
):
    """
    Build a Sheets and Drive API service using an AuthorizedSession backed by requests + urllib3 Retry.
    Attaches _authorized_session and _request_timeout attributes to the service for direct REST use.
    """
    t = timeout or DEFAULT_SHEETS_TIMEOUT
    retries = max_retries if max_retries is not None else DEFAULT_SHEETS_MAX_RETRIES
    bf = backoff_factor if backoff_factor is not None else DEFAULT_SHEETS_BACKOFF_FACTOR

    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]),
        backoff_factor=bf,
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Construct AuthorizedSession in a defensive way to handle different google-auth versions
    authed = None
    last_exc: Exception | None = None
    try:
        # try keyword 'session' (works for some google-auth versions)
        authed = AuthorizedSession(creds, session=session)
    except TypeError as e1:
        last_exc = e1
        logger.debug("AuthorizedSession(..., session=...) failed: %s; trying positional", e1)
        try:
            # try positional second argument
            authed = AuthorizedSession(creds, session)
        except TypeError as e2:
            last_exc = e2
            logger.debug(
                "AuthorizedSession(creds, session) positional failed: %s; trying requests_session kw",
                e2,
            )
            try:
                # try 'requests_session' keyword (older/other versions)
                authed = AuthorizedSession(creds, requests_session=session)
            except TypeError as e3:
                last_exc = e3
                logger.debug(
                    "AuthorizedSession(..., requests_session=...) failed: %s; trying default constructor",
                    e3,
                )
                try:
                    # fallback: construct with only creds then attach the requests.Session if possible
                    authed = AuthorizedSession(creds)
                    try:
                        # Try common attribute names to attach the prepared requests.Session
                        if hasattr(authed, "session"):
                            authed.session = session
                        elif hasattr(authed, "_session"):
                            authed._session = session
                        elif hasattr(authed, "requests_session"):
                            authed.requests_session = session
                        else:
                            # Best-effort: attach to a private attribute for downstream checks
                            authed._attached_requests_session = session
                    except Exception:
                        logger.exception(
                            "Failed to attach requests.Session to AuthorizedSession instance"
                        )
                except Exception as e_final:
                    last_exc = e_final
                    logger.exception("All attempts to construct AuthorizedSession failed")
                    raise last_exc from None

    # Ensure we have an AuthorizedSession instance or raise the last exception
    if authed is None:
        raise last_exc or RuntimeError("Failed to construct AuthorizedSession")

    # Build discovery services; attach the AuthorizedSession for direct REST usage
    sheets_service = google_build("sheets", "v4", credentials=creds, cache_discovery=False)
    sheets_service._authorized_session = authed
    sheets_service._request_timeout = t
    sheets_service._transport_retry_strategy = {"max_retries": retries, "backoff_factor": bf}

    return sheets_service


# -------------------------
# API error parsing and retryability helpers
# -------------------------
def _extract_api_error_details(e: Exception) -> dict:
    """
    Extract details from gspread/API exceptions or requests.Response wrappers.
    Returns a dict with status_code, headers, text, json, status, code, repr, retry_after.
    """
    out = {
        "status_code": None,
        "headers": None,
        "text": None,
        "json": None,
        "status": None,
        "code": None,
        "repr": None,
        "retry_after": None,
    }
    try:
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
                out["json"] = None
    except Exception:
        pass

    try:
        if getattr(e, "args", None):
            first = e.args[0]
            if isinstance(first, dict):
                out["json"] = out["json"] or first
                out["code"] = out["code"] or first.get("code")
                out["status"] = out["status"] or first.get("status")
    except Exception:
        pass

    out["repr"] = str(e)[:2000]

    try:
        headers = out.get("headers") or {}
        ra = headers.get("Retry-After") or headers.get("retry-after")
        if ra:
            try:
                out["retry_after"] = float(ra)
            except Exception:
                out["retry_after"] = None
    except Exception:
        out["retry_after"] = None

    return out


def _is_retryable_gspread_details(details: dict) -> bool:
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
    if "unavailable" in str(details.get("repr", "")).lower():
        return True
    return False


# -------------------------
# Central safe execute for googleapiclient requests
# -------------------------
def _safe_execute(
    request: Any, *, retries: int = 5, base_sleep: float = 0.5, max_sleep: float = 20.0
):
    """
    Execute googleapiclient request with bounded retries + full-jitter.
    """
    attempt = 0
    while True:
        try:
            return request.execute(num_retries=0)
        except Exception as exc:
            attempt += 1
            # special-case SSL textual failures
            if (
                isinstance(exc, ssl.SSLError)
                or "DECRYPTION_FAILED_OR_BAD_RECORD_MAC" in str(exc).upper()
                or "EOF OCCURRED IN VIOLATION OF PROTOCOL" in str(exc).upper()
            ):
                logger.warning(
                    "[GSHEETS_SSL_ERROR] SSL/TLS error on attempt %d: %s",
                    attempt,
                    exc,
                    exc_info=True,
                )
                try:
                    _record_sheets_error("ssl_tls", exc)
                except Exception:
                    pass

            is_transient = detect_transient_error(exc)
            if attempt > retries or not is_transient:
                logger.log(
                    logger.warning if is_transient else logger.error,
                    "[GSHEET] Request failed after %d attempts: %s",
                    attempt,
                    exc,
                    exc_info=True,
                )
                raise
            sleep_s = _full_jitter_sleep(attempt, base_sleep, max_sleep)
            logger.info(
                "[GSHEET] Transient error (%s). Retry %d/%d in %.2fs",
                type(exc).__name__,
                attempt,
                retries,
                sleep_s,
            )
            time.sleep(sleep_s)


# -------------------------
# gspread retry wrapper (for gspread operations)
# -------------------------
def _retry_gspread_call(
    fn: Callable[[], Any],
    *,
    action_desc: str = "gspread_call",
    correlation_id: str | None = None,
    retries: int = 5,
    base_sleep: float = 1.0,
    max_sleep: float = 20.0,
):
    """
    Generic wrapper to perform a gspread operation with retries on transient server errors.
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
            logger.debug(
                "[%s] correlation=%s action=%s attempt=%d headers=%s json(trunc)=%s text(trunc)=%s",
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
                try:
                    _record_sheets_error("gspread_giveup", exc)
                except Exception:
                    pass
                raise

            retry_after = details.get("retry_after")
            if retry_after and isinstance(retry_after, (int, float)):
                sleep_s = float(retry_after)
            else:
                sleep_s = _full_jitter_sleep(attempt, base_sleep, max_sleep)

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


# -------------------------
# SQL helpers
# -------------------------
def get_sql_engine(server: str, database: str, username: str, password: str):
    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    return create_engine(connection_string)


def _dfs_from_proc(engine, proc_sql: str, params: tuple = ()):
    """
    Execute a stored procedure (or any SQL batch) that returns multiple result sets.
    Returns: [DataFrame, DataFrame, ...] in order.
    """
    dfs: list[pd.DataFrame] = []
    raw_conn = engine.raw_connection()  # this is a pyodbc connection under SQLAlchemy
    cursor = None
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
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            raw_conn.close()
        except Exception:
            pass
    return dfs


# -------------------------
# DataFrame helpers and conversion utilities
# -------------------------
def _stringify_datetimes_inplace(df: pd.DataFrame, fmt: str = "%Y-%m-%d %H:%M:%S") -> None:
    if df is None or df.empty:
        return
    for col in list(df.columns):
        s = df[col]
        if ptypes.is_datetime64_any_dtype(s) or (
            getattr(s, "name", "") and getattr(s.dtype, "name", "").startswith("datetime64[")
        ):
            df[col] = pd.to_datetime(s, errors="coerce").dt.strftime(fmt).fillna("")
            continue
        if s.dtype == object:
            if not s.map(lambda v: isinstance(v, (pd.Timestamp, _dt.datetime, _dt.date))).any():
                continue

            def _to_str(v):
                if isinstance(v, (pd.Timestamp, _dt.datetime)):
                    return v.strftime(fmt)
                if isinstance(v, _dt.date):
                    return v.strftime("%Y-%m-%d")
                return "" if pd.isna(v) else v

            df[col] = s.map(_to_str)


def _drop_cols_case_insensitive(df: pd.DataFrame, drop_names: list[str]) -> pd.DataFrame:
    if df is None:
        return df
    drop_set = {str(d).strip().lower() for d in (drop_names or [])}
    keep_cols = []
    for c in df.columns:
        key = c.strip().lower() if isinstance(c, str) else str(c).strip().lower()
        if key not in drop_set:
            keep_cols.append(c)
    return df[keep_cols]


def _ensure_kvk_no_first(df: pd.DataFrame, kvk_no: int) -> pd.DataFrame:
    """
    Ensure there is a KVK_NO column and it is the first column.
    Case-insensitive match if already present.
    """
    if df is None:
        return df

    cols = list(df.columns)
    kvk_col = None
    for c in cols:
        if isinstance(c, str) and c.strip().lower() == "kvk_no":
            kvk_col = c
            break

    if kvk_col is None:
        df.insert(0, "KVK_NO", kvk_no)
        return df

    if cols[0] != kvk_col:
        new_cols = [kvk_col] + [c for c in cols if c != kvk_col]
        df = df[new_cols]
    return df


def _find_col_index_case_insensitive(df: pd.DataFrame, names: list[str]) -> int | None:
    if df is None or df.empty:
        return None
    wanted = {str(n).strip().lower() for n in (names or [])}
    for i, c in enumerate(df.columns):
        key = c.strip().lower() if isinstance(c, str) else str(c).strip().lower()
        if key in wanted:
            return i
    return None


def _coerce_cell_for_sheet(v: Any) -> Any:
    """
    Keep numbers as numbers for Sheets; intify floats that are integral; stringify dates handled elsewhere.
    Map missing to "" for blank cells.
    """
    try:
        if (
            v is None
            or (isinstance(v, float) and (np.isnan(v)))
            or (isinstance(v, (pd._libs.missing.NAType,)))
        ):
            return ""
    except Exception:
        pass
    # Pandas NA/NaT
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass

    # Datetimes are already stringified by _stringify_datetimes_inplace
    if isinstance(v, (pd.Timestamp, _dt.datetime, _dt.date)):
        return v

    # Numpy scalars -> Python scalars
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        fv = float(v)
        if np.isfinite(fv) and fv.is_integer():
            return int(fv)
        return fv

    # Python numerics
    if isinstance(v, (int,)):
        return v
    if isinstance(v, (float,)):
        if not (v != v):  # check NaN
            if v.is_integer():
                return int(v)
        return v

    # Everything else: keep as-is (strings, etc.)
    return v


def _detect_integer_like_columns(df: pd.DataFrame) -> list[int]:
    """
    Detect columns that should be formatted as integer numbers ("0" pattern) in Sheets.
    - Includes true integer dtypes
    - Includes float columns whose non-null values are all integral
    """
    idxs: list[int] = []
    if df is None or df.empty:
        return idxs
    for i, col in enumerate(df.columns):
        s = df[col]
        try:
            if ptypes.is_integer_dtype(s):
                idxs.append(i)
                continue
            if ptypes.is_float_dtype(s):
                s_nonnull = s.dropna()
                if not s_nonnull.empty:
                    # If all finite and integral when rounded
                    vals = s_nonnull.to_numpy(dtype=float)
                    finite = np.isfinite(vals)
                    if finite.all():
                        if np.all(np.equal(vals, np.floor(vals))):
                            idxs.append(i)
        except Exception:
            continue
    return idxs


def _normalize_headers(df: pd.DataFrame, rename_map: dict[str, list[str]]) -> pd.DataFrame:
    """
    Normalise headers and rename columns using a map of desired_name -> [alt1, alt2...].
    Behavior matches the previous implementation in proc_config_import:
      - strips whitespace from headers
      - matches lowercased alt names to existing headers and renames to desired_name
    """
    if df is None:
        return df
    # Trim header whitespace first
    df.rename(columns=lambda c: c.strip() if isinstance(c, str) else c, inplace=True)
    # Build lowercase lookup
    lower_map = {(c.lower() if isinstance(c, str) else c): c for c in df.columns}
    for want, alts in (rename_map or {}).items():
        found = None
        for alt in alts or []:
            key = alt.lower()
            if key in lower_map:
                found = lower_map[key]
                break
        if found and found != want:
            df.rename(columns={found: want}, inplace=True)
    return df


def _coerce_int(df: pd.DataFrame, cols: list[str]):
    """
    Coerce listed columns to pandas nullable integer type (Int64), matching prior behavior.
    Non-present columns are ignored.
    """
    for c in cols or []:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")


def _coerce_float(df: pd.DataFrame, cols: list[str]):
    """
    Coerce listed columns to float (numeric). Non-present columns are ignored.
    """
    for c in cols or []:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")


def _coerce_date_uk(df: pd.DataFrame, cols: list[str]):
    """
    Parse date strings using UK format (DD/MM/YYYY and DD/MM/YY fallback).
    Result is pandas dtype 'object' of python.date values (matching prior code usage).
    """
    for c in cols or []:
        if c not in df.columns:
            continue
        s = df[c].astype("string").str.strip()
        s = s.where(s.notna() & (s != ""), None)
        parsed = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
        mask = parsed.isna() & s.notna()
        if mask.any():
            parsed.loc[mask] = pd.to_datetime(s[mask], format="%d/%m/%y", errors="coerce")
        # Keep same shape as before: .dt.date (may be NaT -> NaN)
        df[c] = parsed.dt.date


def _prepare_kvk_export_df(df: pd.DataFrame, kvk_no: int) -> pd.DataFrame:
    df = _drop_cols_case_insensitive(df, ["camp_id", "campid"])
    df = _ensure_kvk_no_first(df, kvk_no)
    return df


# -------------------------
# gspread convenience helpers
# -------------------------
def _get_or_create_ws(ss: gspread.Spreadsheet, title: str, cols: int = 26) -> gspread.Worksheet:
    """
    Return a worksheet by title; create if not found.
    Normalizes titles for fallback search and tolerates race-create.
    """
    try:
        return ss.worksheet(title)
    except gspread.WorksheetNotFound:
        pass

    def norm(s: str) -> str:
        return "".join(str(s).strip().split()).casefold()

    wanted = norm(title)
    for ws in ss.worksheets():
        if norm(ws.title) == wanted:
            return ws

    try:
        return _retry_gspread_call(
            lambda: ss.add_worksheet(title=title, rows=2, cols=max(1, cols)),
            action_desc=f"add_worksheet:{title}",
        )
    except APIError as e:
        if "already exists" in str(e).lower():
            return ss.worksheet(title)
        raise


def export_dataframe_to_sheet(
    ws: gspread.Worksheet,
    df: pd.DataFrame,
    service=None,
    format_columns: list[int] | list[str] | None = None,
    correlation_id: str | None = None,
):
    """
    Export DataFrame to worksheet with retries around gspread update operations.
    Uses batch update via Google Sheets API if service is provided (to get timeouts).
    Preserves numeric types. Auto-applies integer formatting for integer-like columns unless overridden.
    """
    # clear then update
    _retry_gspread_call(
        lambda: ws.clear(),
        action_desc=f"sheet.clear:{getattr(ws, 'title', '')}",
        correlation_id=correlation_id,
    )
    time.sleep(random.uniform(0.1, 0.6))

    # Work on a copy
    df_local = df.copy()

    # Replace infinities with NA, but do not fillna globally (we handle per-cell)
    df_local.replace([float("inf"), float("-inf")], pd.NA, inplace=True)

    # Stringify datetimes only
    _stringify_datetimes_inplace(df_local)

    # Build values preserving types:
    # Header
    values: list[list[Any]] = [list(df_local.columns)]
    # Rows
    for _, row in df_local.iterrows():
        values.append([_coerce_cell_for_sheet(v) for v in row.tolist()])

    # Prefer Sheets API batch update if available
    try:
        if service and getattr(service, "_authorized_session", None):
            spreadsheet_id = ws.spreadsheet.id
            range_name = f"{ws.title}!A1"
            body = {"values": values}
            req = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",  # keep provided types; we already pass numbers as numbers
                    body=body,
                )
            )
            _safe_execute(req)
        else:

            def _do_update():
                return ws.update(values, value_input_option="RAW")

            _retry_gspread_call(
                _do_update,
                action_desc=f"sheet.update:{getattr(ws, 'title', '')}",
                correlation_id=correlation_id,
            )
    except Exception:
        logger.exception(
            "[GSHEET] Failed to export dataframe to sheet %s/%s",
            getattr(ws.spreadsheet, "title", "?"),
            getattr(ws, "title", "?"),
        )
        raise

    # Determine columns to format as integers ("0" pattern)
    # 1) Auto-detect integer-like columns using the ORIGINAL df (pre-stringify)
    auto_int_idxs = _detect_integer_like_columns(df)

    # 2) Merge with user-provided format_columns (accepts names or indexes)
    def _resolve_format_indexes(
        fmt_cols: list[int] | list[str] | None, cols: list[str]
    ) -> list[int]:
        """
        Resolve user-provided format column specifiers (names or indexes) into integer indexes.
        Behavior improvements:
         - case-insensitive name matching via single-pass lookup
         - aggregate-not-found reporting at DEBUG to avoid log spam
         - warn only when none of the provided format columns matched (caller likely mis-specified)
         - keep index-out-of-range and unsupported-type warnings as WARN (they are clearly incorrect)
        """
        if not fmt_cols:
            return []
        out: list[int] = []
        not_found: list[str] = []

        # Build fast case-insensitive lookup for string column names
        cols_lookup: dict[str, int] = {}
        for i, colname in enumerate(cols):
            try:
                if isinstance(colname, str):
                    cols_lookup[colname] = i
                    cols_lookup[colname.lower()] = i
                else:
                    cols_lookup[str(colname)] = i
            except Exception:
                continue

        for c in fmt_cols:
            if isinstance(c, int):
                if 0 <= c < len(cols):
                    out.append(c)
                else:
                    logger.warning(
                        "[GSHEET] format column index %s out of range for %s/%s",
                        c,
                        getattr(ws.spreadsheet, "title", "?"),
                        getattr(ws, "title", "?"),
                    )
            elif isinstance(c, str):
                # Exact match first (preserve original behavior), then case-insensitive fallback
                idx = cols_lookup.get(c)
                if idx is None:
                    idx = cols_lookup.get(c.lower())
                if idx is not None:
                    out.append(idx)
                else:
                    not_found.append(c)
            else:
                logger.warning(
                    "[GSHEET] unsupported format column type %s for %s/%s",
                    type(c),
                    getattr(ws.spreadsheet, "title", "?"),
                    getattr(ws, "title", "?"),
                )

        if not_found:
            # Aggregate-not-found is probably expected in many comparison tabs; keep it debug-level.
            logger.debug(
                "[GSHEET] format column names not found for %s/%s: %s",
                getattr(ws.spreadsheet, "title", "?"),
                getattr(ws, "title", "?"),
                ", ".join(map(str, not_found)),
            )

        # If caller provided format columns but none resolved, warn once - this indicates a likely mistake.
        if fmt_cols and not out:
            logger.warning(
                "[GSHEET] none of the requested format_columns matched columns for %s/%s; provided=%s",
                getattr(ws.spreadsheet, "title", "?"),
                getattr(ws, "title", "?"),
                fmt_cols,
            )

        return out

    cols_list = list(df_local.columns)
    user_fmt_idxs = _resolve_format_indexes(format_columns or [], cols_list)

    # Final set to apply
    int_format_indexes = sorted(set(auto_int_idxs).union(user_fmt_idxs))

    # Apply number formats if we have service and columns to format
    if service and int_format_indexes:
        try:
            set_number_format(service, ws.spreadsheet.id, ws.id, int_format_indexes, pattern="0")
        except Exception:
            logger.exception(
                "[GSHEET] set_number_format failed for %s/%s",
                getattr(ws.spreadsheet, "title", "?"),
                getattr(ws, "title", "?"),
            )


def set_number_format(
    service, spreadsheet_id, sheet_id, column_indexes: list[int], pattern: str = "0"
):
    requests_payload = []
    for col_idx in column_indexes:
        requests_payload.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
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
    body = {"requests": requests_payload}
    req = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body)
    _safe_execute(req)


def sort_worksheet_multi(
    service,
    spreadsheet_id: str,
    sheet_id: int,
    total_rows: int,
    total_cols: int,
    sort_specs: list[tuple[int, str]],
    *,
    retries: int = 3,
) -> None:
    """
    sort_specs = [(dimensionIndex, 'ASCENDING'|'DESCENDING'), ...]
    Sorts data rows only (keeps header in row 1).
    """
    if not service or not sort_specs:
        return

    body = {
        "requests": [
            {
                "sortRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": total_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": total_cols,
                    },
                    "sortSpecs": [
                        {"dimensionIndex": idx, "sortOrder": order} for idx, order in sort_specs
                    ],
                }
            }
        ]
    }
    req = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body)
    _safe_execute(req, retries=retries)


def _reorder_sheet_tabs(
    service,
    spreadsheet_id: str,
    title_to_id: dict[str, int],
    desired_titles: list[str],
) -> None:
    if not service or not title_to_id:
        return

    requests_payload = []
    index = 0
    for title in desired_titles:
        sheet_id = title_to_id.get(title)
        if sheet_id is None:
            continue
        requests_payload.append(
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "index": index},
                    "fields": "index",
                }
            }
        )
        index += 1

    if not requests_payload:
        return

    body = {"requests": requests_payload}
    req = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body)
    _safe_execute(req, retries=3)


def _sort_kvk_export_sheet(
    service,
    spreadsheet_id: str,
    ws: gspread.Worksheet,
    df_to_write: pd.DataFrame,
    sheet_name: str,
    tab_name: str,
) -> None:
    if not service or df_to_write is None or df_to_write.empty:
        return

    dkp_idx = _find_col_index_case_insensitive(df_to_write, ["dkp", "dkp_score"])
    last_scan_idx = _find_col_index_case_insensitive(df_to_write, ["last_scan_id", "lastscanid"])

    if dkp_idx is None:
        return

    total_rows = len(df_to_write.index) + 1
    total_cols = len(df_to_write.columns)

    windowed_tabs = {
        "KVK_Player_Windowed",
        "KVK_Kingdom_Windowed",
        "KVK_Camp_Windowed",
    }

    if (
        sheet_name == "KVK_ALLPLAYER_OUTPUT"
        and tab_name in windowed_tabs
        and last_scan_idx is not None
    ):
        sort_worksheet_multi(
            service,
            spreadsheet_id,
            ws.id,
            total_rows,
            total_cols,
            [(last_scan_idx, "ASCENDING"), (dkp_idx, "DESCENDING")],
        )
    else:
        sort_worksheet_multi(
            service,
            spreadsheet_id,
            ws.id,
            total_rows,
            total_cols,
            [(dkp_idx, "DESCENDING")],
        )


# -------------------------
# High-level transfer: SQL -> Sheet -> optional sort
# -------------------------
def transfer_and_sort(
    engine,
    client,
    service,
    query: str,
    sheet_name: str,
    tab_name: str,
    sort_column_index: int | None = None,
    date_cols: list[str] | None = None,
    sort_order: str = "ASCENDING",
    format_columns: list[int] | None = None,
):
    correlation_id = str(uuid.uuid4())
    start_total = time.time()

    df = pd.read_sql(query, engine)
    if date_cols:
        for col in date_cols:
            if col in df.columns:
                df[col] = (
                    pd.to_datetime(df[col], errors="coerce")
                    .fillna(pd.Timestamp("1900-01-01"))
                    .dt.strftime("%Y-%m-%d %H:%M:%S")
                )

    ss = _retry_gspread_call(
        lambda: client.open(sheet_name),
        action_desc=f"open_spreadsheet:{sheet_name}",
        correlation_id=correlation_id,
    )

    try:
        ws = _retry_gspread_call(
            lambda: ss.worksheet(tab_name),
            action_desc=f"get_worksheet:{sheet_name}>{tab_name}",
            correlation_id=correlation_id,
        )
    except gspread.WorksheetNotFound:
        ws = _get_or_create_ws(ss, tab_name, cols=max(1, len(df.columns)))

    export_dataframe_to_sheet(
        ws, df, service=service, format_columns=format_columns or [], correlation_id=correlation_id
    )

    if sort_column_index is not None and service:
        try:
            # Ensure we sort only the data rows (exclude header row at index 0)
            # Compute the row/column bounds based on the exported dataframe
            total_rows = len(df.index) + 1  # +1 for header row
            total_cols = len(df.columns)
            # Build sortRange with startRowIndex=1 so header remains at top
            spa = {
                "requests": [
                    {
                        "sortRange": {
                            "range": {
                                "sheetId": ws.id,
                                "startRowIndex": 1,
                                "endRowIndex": total_rows,
                                "startColumnIndex": 0,
                                "endColumnIndex": total_cols,
                            },
                            "sortSpecs": [
                                {"dimensionIndex": sort_column_index, "sortOrder": sort_order}
                            ],
                        }
                    }
                ]
            }
            req = service.spreadsheets().batchUpdate(spreadsheetId=ss.id, body=spa)
            _safe_execute(req, retries=3)
        except Exception:
            logger.exception("[GSHEET] Sorting failed for %s/%s", sheet_name, tab_name)

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


# -------------------------
# Config validation
# -------------------------
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


# -------------------------
# run_all_exports: orchestrator with retry and optional alerting via Discord
# -------------------------
def run_all_exports(
    server,
    database,
    username,
    password,
    credentials_file: str = CREDENTIALS_FILE,
    notify_channel: Any | None = None,
    bot_loop: asyncio.AbstractEventLoop | None = None,
):
    """
    Run all exports as defined in CONFIG_FILE. Retries per-job and can send alerts to notify_channel (a discord.TextChannel-like object).
    Returns a tuple (success: bool, log_messages: str) for the run. The second element is a single string
    (joined lines) to remain compatible with callers expecting to call .strip().
    """
    assert all(
        [server, database, username, password, credentials_file]
    ), "One or more required parameters are missing"
    engine = get_sql_engine(server, database, username, password)
    client = get_gsheet_client(credentials_file)
    service = get_sort_service(credentials_file)

    log_messages: list[str] = []

    def _append_log(msg: str):
        print(msg)
        log_messages.append(msg)

    def wrapped_transfer(*args, **kwargs):
        retries = 5
        base_delay = 2.0
        sheet_name = kwargs.get("sheet_name", "")
        tab_name = kwargs.get("tab_name", "")
        notify = kwargs.get("notify_channel", notify_channel)
        loop = kwargs.get("bot_loop", bot_loop)
        correlation_id = str(uuid.uuid4())

        e = None
        tb = ""

        for attempt in range(1, retries + 1):
            try:
                safe_kwargs = {
                    k: v for k, v in kwargs.items() if k not in ("notify_channel", "bot_loop")
                }
                transfer_and_sort(*args, **safe_kwargs)
                msg = f"[OK] {sheet_name} > {tab_name}"
                _append_log(msg)
                return
            except APIError as ex:
                e = ex
                tb = traceback.format_exc()
                details = _extract_api_error_details(ex)
                retryable = _is_retryable_gspread_details(details)
                msg = f"[⚠️ RETRY {attempt}] {sheet_name} > {tab_name}: APIError: {ex}"
                logger.info(
                    "[wrapped_transfer] correlation=%s attempt=%d sheet=%s tab=%s exception=%s",
                    correlation_id,
                    attempt,
                    sheet_name,
                    tab_name,
                    type(ex).__name__,
                )
            except Exception as ex:
                e = ex
                tb = traceback.format_exc()
                details = _extract_api_error_details(ex)
                retryable = _is_retryable_gspread_details(details)
                msg = f"[⚠️ RETRY {attempt}] {sheet_name} > {tab_name}: General error: {ex}"
                logger.info(
                    "[wrapped_transfer] correlation=%s attempt=%d sheet=%s tab=%s exception=%s",
                    correlation_id,
                    attempt,
                    sheet_name,
                    tab_name,
                    type(ex).__name__,
                )

            _append_log(msg)
            _append_log(tb)

            if attempt < retries and retryable:
                retry_after = details.get("retry_after")
                if retry_after and isinstance(retry_after, (int, float)):
                    delay = float(retry_after)
                else:
                    delay = _full_jitter_sleep(attempt, base_delay, 60.0)
                _append_log(f"[INFO] sleeping {delay:.2f}s before retry {attempt + 1}/{retries}")
                time.sleep(delay)
                continue
            else:
                # give up and optionally alert via discord
                _append_log(f"[ERROR] Giving up on {sheet_name} > {tab_name}: {e}")
                if notify:
                    try:
                        # build embed (lightweight fallback)
                        embed = None
                        try:
                            import discord as _discord

                            embed = _discord.Embed(
                                title="KVK Export Failure",
                                description=f"Sheet: {sheet_name}\nTab: {tab_name}\nAttempts: {attempt}\ncorrelation_id: {correlation_id}",
                                color=_discord.Color.red(),
                            )
                            embed.add_field(
                                name="Error", value=f"```{str(e)[:1000]}```", inline=False
                            )
                            tb_text = tb if tb else "no traceback"
                            embed.add_field(
                                name="Traceback", value=f"```{tb_text[-1000:]}```", inline=False
                            )
                            embed.set_footer(
                                text=f"gsheet_module.py export failure | gspread={GSPREAD_VERSION} google-client={GOOGLE_API_CLIENT_VERSION}"
                            )
                        except Exception:
                            # notify via simple message
                            embed = None
                        # send via bot_loop thread-safe if possible
                        if loop and embed:
                            try:
                                coro = notify.send(embed=embed)
                                asyncio.run_coroutine_threadsafe(coro, loop)
                            except Exception:
                                try:
                                    # best effort direct send
                                    notify.send(embed=embed)
                                except Exception:
                                    logger.exception(
                                        "[wrapped_transfer] failed to send discord alert"
                                    )
                    except Exception:
                        logger.exception("[wrapped_transfer] alerting failure")
                return

    # Load config file and run jobs
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            export_jobs = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Failed to parse export config {CONFIG_FILE}: {e}"
        logger.error("[GSHEET] %s", msg, exc_info=True)
        try:
            _record_sheets_error("config_json_decode", e)
        except Exception:
            pass
        return False, msg
    except Exception as e:
        msg = f"Failed to read export config {CONFIG_FILE}: {e}"
        logger.exception("[GSHEET] %s", msg)
        try:
            _record_sheets_error("config_read_failed", e)
        except Exception:
            pass
        return False, msg

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
            sort_column_index=job.get("sort"),
            sort_order=job.get("order", "ASCENDING"),
            date_cols=job.get("dates", []),
            format_columns=job.get("format_numbers", []),
            notify_channel=notify_channel,
            bot_loop=bot_loop,
        )

    # Return success flag and collected logs as a single joined string so callers that do .strip() work
    return True, "\n".join(log_messages)


# -------------------------
# Public runner: run_single_export
# -------------------------
def get_gsheet_client(credentials_file: str):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


def get_sort_service(credentials_file: str, timeout: int | None = None):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return _build_sheets_with_timeout(creds, timeout=timeout)


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


# -------------------------
# Read values from a Google Sheets range and return rows or None on error
# -------------------------


def get_sheet_values(
    spreadsheet_id: str,
    range_a1: str,
    *,
    credentials_file: str | None = None,
    timeout: int | None = None,
    valueRenderOption: str = "FORMATTED_VALUE",
    dateTimeRenderOption: str = "FORMATTED_STRING",
) -> list[list[Any]] | None:
    """
    Read values from a Google Sheets range and return rows or None on error.

    Return semantics:
      - On success: returns list[list[Any]] (may be empty).
      - On error: returns None (caller can decide how to proceed).

    This function reuses the module's internal _build_sheets_with_timeout and
    error-recording helpers so callers get consistent retry/telemetry behavior.
    """
    # Lazy-import heavy dependency to avoid import-time failures in test env
    try:
        from google.oauth2.service_account import Credentials  # type: ignore
    except Exception as e:
        try:
            _record_sheets_error("credentials_unavailable", e)
        except Exception:
            logger.debug("Failed to record credentials_unavailable", exc_info=True)
        return None

    # Resolve credentials path: prefer explicit argument, fallback to module constant if available
    cred_path = credentials_file
    try:
        if cred_path is None:
            cred_path = (
                CREDENTIALS_FILE  # CREDENTIALS_FILE is expected to be available in this module
            )
    except Exception:
        # If CREDENTIALS_FILE not present in this module, require explicit credentials_file
        pass

    if not cred_path:
        try:
            _record_sheets_error(
                "credentials_missing", RuntimeError("credentials file not configured")
            )
        except Exception:
            logger.debug("Failed to record missing credentials", exc_info=True)
        return None

    try:
        creds = Credentials.from_service_account_file(
            cred_path, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
    except Exception as e:
        try:
            _record_sheets_error("credentials_load_failed", e)
        except Exception:
            logger.debug("Failed to record credentials load error", exc_info=True)
        return None

    try:
        sheets_service = _build_sheets_with_timeout(creds, timeout=timeout)

        req = (
            sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=range_a1,
                valueRenderOption=valueRenderOption,
                dateTimeRenderOption=dateTimeRenderOption,
            )
        )

        # Use module default for retries
        res = req.execute(num_retries=DEFAULT_SHEETS_MAX_RETRIES)
        rows = res.get("values", []) or []

        if not rows:
            logger.info("[GSHEET] Empty range: sheet=%s range=%s", spreadsheet_id, range_a1)

        return rows

    except Exception as e:
        try:
            _record_sheets_error("fetch_values", e)
        except Exception:
            logger.debug("Failed to record fetch_values error", exc_info=True)

        logger.error(
            "[GSHEET] Failed to fetch values sheet=%s range=%s: %s", spreadsheet_id, range_a1, e
        )
        logger.debug("Exception details for sheet fetch", exc_info=True)
        return None


# -------------------------
# Utility: Drive metadata helper
# -------------------------
def get_drive_service(credentials_file: str, timeout: int | None = None):
    creds = Credentials.from_service_account_file(
        credentials_file, scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"]
    )
    service = _build_sheets_with_timeout(creds, timeout=timeout)
    drive_service = google_build("drive", "v3", credentials=creds, cache_discovery=False)
    drive_service._authorized_session = getattr(service, "_authorized_session", None)
    drive_service._request_timeout = getattr(service, "_request_timeout", DEFAULT_SHEETS_TIMEOUT)
    return drive_service


def get_spreadsheet_modified_time(drive_service, spreadsheet_id: str) -> str | None:
    try:
        req = drive_service.files().get(fileId=spreadsheet_id, fields="modifiedTime")
        try:
            resp = _safe_execute(req, retries=3)
        except Exception:
            resp = req.execute(num_retries=0)
        return resp.get("modifiedTime")
    except Exception as exc:
        logger.warning(
            "[GSHEETS] Could not fetch modifiedTime for %s: %s", spreadsheet_id, exc, exc_info=True
        )
        try:
            _record_sheets_error("drive_metadata_fetch", exc)
        except Exception:
            pass
        return None


# -------------------------
# Basic connectivity check
# -------------------------
def check_basic_gsheets_access(
    credentials_file: str, sheet_id: str, max_retries: int = 2, retry_backoff_sec: float = 1.0
):
    client = get_gsheet_client(credentials_file)
    attempt = 0
    while True:
        attempt += 1
        try:
            ss = client.open_by_key(sheet_id)
            # Try a simple read of A1 to exercise permissions
            try:
                _ = ss.worksheet("Sheet1")
            except Exception:
                # fine; we just wanted to open the spreadsheet
                pass
            logger.info(
                "GSheets access check OK host=%s python=%s gspread=%s google-api-client=%s",
                platform.node(),
                sys.version.split()[0],
                GSPREAD_VERSION,
                GOOGLE_API_CLIENT_VERSION,
            )
            return True, "GSheets access OK"
        except APIError as api_err:
            details = _extract_api_error_details(api_err)
            logger.warning(
                "GSheets APIError (attempt %s/%s): status=%s code=%s headers=%s",
                attempt,
                max_retries + 1,
                details.get("status") or details.get("status_code"),
                details.get("code"),
                details.get("headers"),
            )
            if attempt > max_retries:
                return False, f"APIError: {details.get('repr')}"
            time.sleep(retry_backoff_sec)
        except Exception as exc:
            logger.exception("GSheets access generic failure: %s", exc)
            if attempt > max_retries:
                return False, str(exc)
            time.sleep(retry_backoff_sec)


# -------------------------
# Test helpers / manual export runner
# -------------------------
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
            _stringify_datetimes_inplace(df_local)
            if df_local is None or df_local.empty:
                df_to_write = _prepare_kvk_export_df(pd.DataFrame(columns=df_local.columns), kvk_no)
                ws = _get_or_create_ws(ss, tab, cols=max(1, len(df_to_write.columns)))
                export_dataframe_to_sheet(
                    ws,
                    df_to_write,
                    service=service,
                    format_columns=_KVK_FORMAT_NUMBERS.get(tab, []),
                )
                _sort_kvk_export_sheet(service, ss.id, ws, df_to_write, sheet_name, tab)
                skipped_tabs.append(tab)
            else:
                df_to_write = _prepare_kvk_export_df(df_local, kvk_no)
                ws = _get_or_create_ws(ss, tab, cols=max(1, len(df_to_write.columns)))
                export_dataframe_to_sheet(
                    ws,
                    df_to_write,
                    service=service,
                    format_columns=_KVK_FORMAT_NUMBERS.get(tab, []),
                )
                _sort_kvk_export_sheet(service, ss.id, ws, df_to_write, sheet_name, tab)
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
        df.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
        _stringify_datetimes_inplace(df)

        df_to_write = _prepare_kvk_export_df(df, kvk_no)
        ws = _get_or_create_ws(ss, tab, cols=len(df_to_write.columns))

        export_dataframe_to_sheet(
            ws, df_to_write, service=service, format_columns=_KVK_FORMAT_NUMBERS.get(tab, [])
        )
        _sort_kvk_export_sheet(service, ss.id, ws, df_to_write, sheet_name, tab)

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

    META_NUMERIC_AGG = {"kvk_no": "max", "last_scan_id": "max"}

    # remove meta numeric from sum list
    numeric_cols = [
        c
        for c in numeric_cols
        if not (isinstance(c, str) and c.strip().lower() in META_NUMERIC_AGG)
    ]

    # Perform aggregation: sum numeric columns, max for meta numeric, keep first of non-numeric columns
    agg_dict: dict[Any, str] = {c: "sum" for c in numeric_cols}

    # add meta numeric rules if present
    for c in df_filtered.columns:
        if isinstance(c, str):
            key = c.strip().lower()
            if key in META_NUMERIC_AGG:
                agg_dict[c] = META_NUMERIC_AGG[key]

    # For non-numeric, keep first
    for c in df_filtered.columns:
        if c in group_keys:
            continue
        if c not in agg_dict:
            agg_dict[c] = "first"

    # If no group keys exist, just sum all numeric columns across all rows and return a single-row DF
    if not group_keys:
        summed = df_filtered[numeric_cols].sum(numeric_only=True).to_frame().T
        META_NUMERIC_AGG = {"kvk_no": "max", "last_scan_id": "max"}

        for c in df_filtered.columns:
            if c in group_keys or c in numeric_cols:
                continue
            if isinstance(c, str) and c.strip().lower() in META_NUMERIC_AGG:
                agg = META_NUMERIC_AGG[c.strip().lower()]
                if agg == "max":
                    summed[c] = df_filtered[c].max()
                else:
                    summed[c] = df_filtered[c].iat[0] if not df_filtered[c].empty else ""
            else:
                summed[c] = df_filtered[c].astype(object).iat[0] if not df_filtered[c].empty else ""
        return summed

    grouped = df_filtered.groupby(group_keys, dropna=False, as_index=False).agg(agg_dict)
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
    Create/Update the PASS4, 1ST_ALTAR, PASS7 style spreadsheets based on dfs from the proc.
    Returns a dict containing results for each target spreadsheet:
      {
        "KVK_PASS4_ALL_PLAYER_OUTPUT": {created: bool, spreadsheet_url, written_tabs: [...], skipped_tabs: [...]},
        "KVK_1ST_ALTAR_ALL_PLAYER_OUTPUT": {...},
        "KVK_PASS7_ALL_PLAYER_OUTPUT": {...}
        ...
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
            if not df_to_write.empty:
                df_to_write.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
                _stringify_datetimes_inplace(df_to_write)

                try:
                    df_to_write = _prepare_kvk_export_df(df_to_write, kvk_no)
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

                    # Filter format_cols to those actually present in df_to_write (case-insensitive)
                    if format_cols:
                        df_cols_lower = {str(c).lower(): c for c in df_to_write.columns}
                        filtered_format_cols: list[Any] = []
                        for fc in format_cols:
                            if isinstance(fc, int):
                                # index will be validated/resolved inside export_dataframe_to_sheet,
                                # but we only accept integer indexes within bounds here to avoid noisy warnings.
                                if 0 <= fc < len(df_to_write.columns):
                                    filtered_format_cols.append(fc)
                            elif isinstance(fc, str):
                                # case-insensitive match to a column name
                                match = df_cols_lower.get(fc.lower())
                                if match is not None:
                                    filtered_format_cols.append(match)
                            else:
                                # unsupported type - keep it and let the resolver warn if needed
                                filtered_format_cols.append(fc)
                        format_cols = filtered_format_cols

                    df_to_write = _prepare_kvk_export_df(df_to_write, kvk_no)

                    # Export using the filtered format columns (reduces spurious warnings)
                    export_dataframe_to_sheet(
                        ws, df_to_write, service=service, format_columns=format_cols
                    )
                    _sort_kvk_export_sheet(
                        service, target_ss.id, ws, df_to_write, target_ss_name, target_tab
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

    # Build specs for each of the spreadsheets to create

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

    # 2ND ALTAR spreadsheet (existing/new)
    second_altar_specs = [
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {
            "type": "filtered",
            "src_idx": 3,
            "filter_window": "2nd Altar",
            "target_tab": "2ND_ALTAR_PLAYER",
        },
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "2nd Altar",
            "target_tab": "2ND_ALTAR_KINGDOM",
        },
        {
            "type": "filtered",
            "src_idx": 5,
            "filter_window": "2nd Altar",
            "target_tab": "2ND_ALTAR_CAMP",
        },
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        # Aggregates: Pass 4 + 1st Altar + 2nd Altar
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar"],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar"],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar"],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    try:
        has_2nd_altar_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_2nd_altar_player = not df3[df3["WindowName"] == "2nd Altar"].empty
            else:
                has_2nd_altar_player = False
    except Exception:
        has_2nd_altar_player = False

    if has_2nd_altar_player:
        second_altar_result = _create_and_write(
            "KVK_2ND_ALTAR_ALL_PLAYER_OUTPUT", second_altar_specs
        )
    else:
        second_altar_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in second_altar_specs],
        }
    results["KVK_2ND_ALTAR_ALL_PLAYER_OUTPUT"] = second_altar_result

    # 3RD ALTAR spreadsheet (existing/new)
    third_altar_specs = [
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {
            "type": "filtered",
            "src_idx": 3,
            "filter_window": "3rd Altar",
            "target_tab": "3RD_ALTAR_PLAYER",
        },
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "3rd Altar",
            "target_tab": "3RD_ALTAR_KINGDOM",
        },
        {
            "type": "filtered",
            "src_idx": 5,
            "filter_window": "3rd Altar",
            "target_tab": "3RD_ALTAR_CAMP",
        },
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        # Aggregates: Pass 4 + 1st Altar + 2nd Altar + 3rd Altar
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar"],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar"],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar"],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    try:
        has_3rd_altar_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_3rd_altar_player = not df3[df3["WindowName"] == "3rd Altar"].empty
            else:
                has_3rd_altar_player = False
    except Exception:
        has_3rd_altar_player = False

    if has_3rd_altar_player:
        third_altar_result = _create_and_write("KVK_3RD_ALTAR_ALL_PLAYER_OUTPUT", third_altar_specs)
    else:
        third_altar_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in third_altar_specs],
        }
    results["KVK_3RD_ALTAR_ALL_PLAYER_OUTPUT"] = third_altar_result

    # 3) KVK_PASS7_ALL_PLAYER_OUTPUT
    # includes Pass7 filtered tabs, KVK_Windows, KVK_DKP_Weights,
    # and KVK_ALL_WINDOWS_* = Pass4 + 1st Altar + 2nd Altar + 3rd Altar + Pass 7
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
        # Aggregates: Pass 4 + 1st Altar + 2nd Altar + 3rd Altar + Pass 7
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7"],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7"],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7"],
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

    # 4) KVK_PASS8_ALL_PLAYER_OUTPUT
    # includes Pass 8 filtered tabs, KVK_Windows, KVK_DKP_Weights,
    # and KVK_ALL_WINDOWS_* = Pass4 + 1st Altar + 2nd Altar + 3rd Altar + Pass7 + Pass 8
    pass8_specs = [
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {"type": "filtered", "src_idx": 3, "filter_window": "Pass 8", "target_tab": "PASS8_PLAYER"},
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "Pass 8",
            "target_tab": "PASS8_KINGDOM",
        },
        {"type": "filtered", "src_idx": 5, "filter_window": "Pass 8", "target_tab": "PASS8_CAMP"},
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7", "Pass 8"],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7", "Pass 8"],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": ["Pass 4", "1st Altar", "2nd Altar", "3rd Altar", "Pass 7", "Pass 8"],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    # Produce PASS8 spreadsheet only if PASS8_PLAYER (src_idx=3 filtered by "Pass 8") has data.
    try:
        has_pass8_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_pass8_player = not df3[df3["WindowName"] == "Pass 8"].empty
            else:
                has_pass8_player = False
    except Exception:
        has_pass8_player = False

    if has_pass8_player:
        pass8_result = _create_and_write("KVK_PASS8_ALL_PLAYER_OUTPUT", pass8_specs)
    else:
        pass8_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in pass8_specs],
        }
    results["KVK_PASS8_ALL_PLAYER_OUTPUT"] = pass8_result

    # 5) KVK_GREATZIG_ALL_PLAYER_OUTPUT
    # includes Great Zig filtered tabs, KVK_Windows, KVK_DKP_Weights,
    # and KVK_ALL_WINDOWS_* = Pass4 + 1st Altar + 2nd Altar + 3rd Altar + Pass7 + Pass 8 + Great Zig
    greatzig_specs = [
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {
            "type": "filtered",
            "src_idx": 3,
            "filter_window": "Great Zig",
            "target_tab": "GREATZIG_PLAYER",
        },
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "Great Zig",
            "target_tab": "GREATZIG_KINGDOM",
        },
        {
            "type": "filtered",
            "src_idx": 5,
            "filter_window": "Great Zig",
            "target_tab": "GREATZIG_CAMP",
        },
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": [
                "Pass 4",
                "1st Altar",
                "2nd Altar",
                "3rd Altar",
                "Pass 7",
                "Pass 8",
                "Great Zig",
            ],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": [
                "Pass 4",
                "1st Altar",
                "2nd Altar",
                "3rd Altar",
                "Pass 7",
                "Pass 8",
                "Great Zig",
            ],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": [
                "Pass 4",
                "1st Altar",
                "2nd Altar",
                "3rd Altar",
                "Pass 7",
                "Pass 8",
                "Great Zig",
            ],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    # Produce GREATZIG spreadsheet only if GREATZIG_PLAYER (src_idx=3 filtered by "Great Zig") has data.
    try:
        has_greatzig_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_greatzig_player = not df3[df3["WindowName"] == "Great Zig"].empty
            else:
                has_greatzig_player = False
    except Exception:
        has_greatzig_player = False

    if has_greatzig_player:
        greatzig_result = _create_and_write("KVK_GREATZIG_ALL_PLAYER_OUTPUT", greatzig_specs)
    else:
        greatzig_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in greatzig_specs],
        }
    results["KVK_GREATZIG_ALL_PLAYER_OUTPUT"] = greatzig_result

    # 6) KVK_PASS9_ALL_PLAYER_OUTPUT
    # includes Pass 9 filtered tabs, KVK_Windows, KVK_DKP_Weights,
    # and KVK_ALL_WINDOWS_* = Pass4 + 1st Altar + 2nd Altar + 3rd Altar + Pass7 + Pass8 + Great Zig + Pass 9
    pass9_specs = [
        {"type": "raw", "src_idx": 0, "target_tab": "KVK_Scan_Log"},
        {"type": "filtered", "src_idx": 3, "filter_window": "Pass 9", "target_tab": "PASS9_PLAYER"},
        {
            "type": "filtered",
            "src_idx": 4,
            "filter_window": "Pass 9",
            "target_tab": "PASS9_KINGDOM",
        },
        {"type": "filtered", "src_idx": 5, "filter_window": "Pass 9", "target_tab": "PASS9_CAMP"},
        {"type": "raw", "src_idx": 1, "target_tab": "KVK_Windows"},
        {"type": "raw", "src_idx": 2, "target_tab": "KVK_DKP_Weights"},
        {
            "type": "aggregate",
            "src_idx": 3,
            "agg_windows": [
                "Pass 4",
                "1st Altar",
                "2nd Altar",
                "3rd Altar",
                "Pass 7",
                "Pass 8",
                "Great Zig",
                "Pass 9",
            ],
            "agg_type": "player",
            "target_tab": "KVK_ALL_WINDOWS_PLAYER",
        },
        {
            "type": "aggregate",
            "src_idx": 4,
            "agg_windows": [
                "Pass 4",
                "1st Altar",
                "2nd Altar",
                "3rd Altar",
                "Pass 7",
                "Pass 8",
                "Great Zig",
                "Pass 9",
            ],
            "agg_type": "kingdom",
            "target_tab": "KVK_ALL_WINDOWS_KINGDOM",
        },
        {
            "type": "aggregate",
            "src_idx": 5,
            "agg_windows": [
                "Pass 4",
                "1st Altar",
                "2nd Altar",
                "3rd Altar",
                "Pass 7",
                "Pass 8",
                "Great Zig",
                "Pass 9",
            ],
            "agg_type": "camp",
            "target_tab": "KVK_ALL_WINDOWS_CAMP",
        },
    ]

    # Produce PASS9 spreadsheet only if PASS9_PLAYER (src_idx=3 filtered by "Pass 9") has data.
    try:
        has_pass9_player = False
        if len(dfs) > 3:
            df3 = dfs[3]
            if "WindowName" in df3.columns:
                has_pass9_player = not df3[df3["WindowName"] == "Pass 9"].empty
            else:
                has_pass9_player = False
    except Exception:
        has_pass9_player = False

    if has_pass9_player:
        pass9_result = _create_and_write("KVK_PASS9_ALL_PLAYER_OUTPUT", pass9_specs)
    else:
        pass9_result = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [spec["target_tab"] for spec in pass9_specs],
        }
    results["KVK_PASS9_ALL_PLAYER_OUTPUT"] = pass9_result

    # ---------------------------------------------------------------------
    # NEW: ALL_WINDOW_COMPARISON spreadsheet
    # Purpose: for each Camp / Kingdom / Player, present metric values per window side-by-side,
    # with an Overall column (aggregate across windows). One tab per level+metric:
    #   KINGDOM_KP_GAIN, PLAYER_KP_GAIN, CAMP_KP_GAIN, ... for metrics.
    # Ordered windows for columns
    windows_order = [
        "Pass 4",
        "1st Altar",
        "2nd Altar",
        "3rd Altar",
        "Pass 7",
        "Pass 8",
        "Great Zig",
        "Pass 9",
    ]

    def _build_comparison_df(src_idx: int, agg_type: str, metric: str) -> pd.DataFrame:
        """
        Build a comparison DataFrame for a given src_idx (3=player,4=kingdom,5=camp),
        agg_type matching "player"|"kingdom"|"camp", and metric column name.
        Returns a DataFrame with KVK_NO and grouping keys, one column per window (named '<Window> <metric>')
        in windows_order and an 'Overall <metric>' column aggregated across windows via _aggregate_windowed_dfs.
        """
        if src_idx >= len(dfs):
            return pd.DataFrame()
        df_src = dfs[src_idx].copy()
        if df_src.empty or "WindowName" not in df_src.columns:
            return pd.DataFrame()

        # Determine group keys consistent with _aggregate_windowed_dfs
        if agg_type == "player":
            group_keys = [
                k for k in ["governor_id", "name", "kingdom", "campid"] if k in df_src.columns
            ]
            # include camp_name if present for convenience
            if "camp_name" in df_src.columns and "camp_name" not in group_keys:
                group_keys.append("camp_name")
        elif agg_type == "kingdom":
            group_keys = [k for k in ["kingdom", "campid", "camp_name"] if k in df_src.columns]
        else:
            group_keys = [k for k in ["campid", "camp_name"] if k in df_src.columns]

        if not group_keys:
            # cannot meaningfully build comparison without keys
            return pd.DataFrame()

        # Ensure metric column exists; if not, create constant NaN so pivot still works (we can then drop)
        if metric not in df_src.columns:
            df_src[metric] = pd.NA

        # Filter to windows of interest
        df_filtered = df_src[df_src["WindowName"].isin(windows_order)].copy()
        if df_filtered.empty:
            # no per-window rows
            # still try to get Overall via aggregation
            agg_df = _aggregate_windowed_dfs(dfs, windows_order, src_idx, agg_type)
            if agg_df.empty:
                return pd.DataFrame()
            # select only group keys + metric if available
            cols_to_keep = [c for c in group_keys if c in agg_df.columns]
            if metric in agg_df.columns:
                cols_to_keep.append(metric)
            out = agg_df[cols_to_keep].copy()
            # rename metric column to Overall <metric>
            if metric in out.columns:
                out = out.rename(columns={metric: f"Overall {metric}"})
            out.insert(0, "KVK_NO", kvk_no)
            return out

        # Pivot per-window values
        try:
            pivot = (
                df_filtered.groupby(group_keys + ["WindowName"], dropna=False)[metric]
                .sum()
                .unstack(fill_value=0)
            )
        except Exception:
            # fallback using pivot_table
            pivot = df_filtered.pivot_table(
                index=group_keys, columns="WindowName", values=metric, aggfunc="sum", fill_value=0
            )

        # Ensure all windows are present as columns in the pivot (create zeros if missing)
        for w in windows_order:
            if w not in pivot.columns:
                pivot[w] = 0

        # Reindex columns to windows_order
        pivot = pivot.reindex(columns=windows_order, fill_value=0)

        # Flatten index to columns
        pivot_reset = pivot.reset_index()

        # Compute overall aggregate via existing helper (aggregates numeric sums across windows)
        agg_df = _aggregate_windowed_dfs(dfs, windows_order, src_idx, agg_type)
        # select only group_keys + metric
        if not agg_df.empty and metric in agg_df.columns:
            # agg_df may have group_keys + metric
            cols_to_take = [c for c in group_keys if c in agg_df.columns] + [metric]
            agg_sel = agg_df[cols_to_take].copy()
            # rename metric to 'Overall <metric>' and merge
            agg_sel = agg_sel.rename(columns={metric: f"Overall {metric}"})
            # Merge on group keys
            merged = pivot_reset.merge(
                agg_sel, on=[c for c in group_keys if c in agg_sel.columns], how="left"
            )
        else:
            # no overall info; add Overall column with zeros
            merged = pivot_reset.copy()
            merged[f"Overall {metric}"] = 0

        # Prefix window columns with "<Window> <metric>"
        for w in windows_order:
            col_old = w
            col_new = f"{w} {metric}"
            if col_old in merged.columns:
                merged.rename(columns={col_old: col_new}, inplace=True)

        # Ensure KVK_NO front column
        merged.insert(0, "KVK_NO", kvk_no)

        # Re-order columns: KVK_NO + group_keys + per-window cols + Overall
        window_cols = [f"{w} {metric}" for w in windows_order]
        overall_col = f"Overall {metric}"
        final_cols = (
            ["KVK_NO"]
            + [c for c in group_keys]
            + [c for c in window_cols if c in merged.columns]
            + ([overall_col] if overall_col in merged.columns else [])
        )
        merged = merged[final_cols]

        return merged

    # Build all comparison tabs (one spreadsheet "ALL_WINDOW_COMPARISON")
    comparison_tabs = [
        {"tab_name": "CAMP_DKP", "src_idx": 5, "agg_type": "camp", "metric": "dkp"},
        {"tab_name": "KINGDOM_DKP", "src_idx": 4, "agg_type": "kingdom", "metric": "dkp"},
        {"tab_name": "PLAYER_DKP", "src_idx": 3, "agg_type": "player", "metric": "dkp"},
        {"tab_name": "CAMP_KP_GAIN", "src_idx": 5, "agg_type": "camp", "metric": "kp_gain"},
        {"tab_name": "KINGDOM_KP_GAIN", "src_idx": 4, "agg_type": "kingdom", "metric": "kp_gain"},
        {"tab_name": "PLAYER_KP_GAIN", "src_idx": 3, "agg_type": "player", "metric": "kp_gain"},
        {"tab_name": "CAMP_KILLS_GAIN", "src_idx": 5, "agg_type": "camp", "metric": "kills_gain"},
        {
            "tab_name": "KINGDOM_KILLS_GAIN",
            "src_idx": 4,
            "agg_type": "kingdom",
            "metric": "kills_gain",
        },
        {
            "tab_name": "PLAYER_KILLS_GAIN",
            "src_idx": 3,
            "agg_type": "player",
            "metric": "kills_gain",
        },
        {"tab_name": "CAMP_T5_KILLS", "src_idx": 5, "agg_type": "camp", "metric": "t5_kills"},
        {"tab_name": "KINGDOM_T5_KILLS", "src_idx": 4, "agg_type": "kingdom", "metric": "t5_kills"},
        {"tab_name": "PLAYER_T5_KILLS", "src_idx": 3, "agg_type": "player", "metric": "t5_kills"},
        {"tab_name": "CAMP_T4_KILLS", "src_idx": 5, "agg_type": "camp", "metric": "t4_kills"},
        {"tab_name": "KINGDOM_T4_KILLS", "src_idx": 4, "agg_type": "kingdom", "metric": "t4_kills"},
        {"tab_name": "PLAYER_T4_KILLS", "src_idx": 3, "agg_type": "player", "metric": "t4_kills"},
        {"tab_name": "CAMP_DEADS", "src_idx": 5, "agg_type": "camp", "metric": "deads"},
        {"tab_name": "KINGDOM_DEADS", "src_idx": 4, "agg_type": "kingdom", "metric": "deads"},
        {"tab_name": "PLAYER_DEADS", "src_idx": 3, "agg_type": "player", "metric": "deads"},
        {"tab_name": "CAMP_KP_LOSS", "src_idx": 5, "agg_type": "camp", "metric": "kp_loss"},
        {"tab_name": "KINGDOM_KP_LOSS", "src_idx": 4, "agg_type": "kingdom", "metric": "kp_loss"},
        {"tab_name": "PLAYER_KP_LOSS", "src_idx": 3, "agg_type": "player", "metric": "kp_loss"},
        {
            "tab_name": "CAMP_HEALED_TROOPS",
            "src_idx": 5,
            "agg_type": "camp",
            "metric": "healed_troops",
        },
        {
            "tab_name": "KINGDOM_HEALED_TROOPS",
            "src_idx": 4,
            "agg_type": "kingdom",
            "metric": "healed_troops",
        },
        {
            "tab_name": "PLAYER_HEALED_TROOPS",
            "src_idx": 3,
            "agg_type": "player",
            "metric": "healed_troops",
        },
    ]

    # Pre-evaluate which comparison tabs have data
    comp_to_write = []
    for t in comparison_tabs:
        try:
            df_comp = _build_comparison_df(t["src_idx"], t["agg_type"], t["metric"])
            has_data = not (df_comp is None or df_comp.empty)
        except Exception:
            logger.exception("Error building comparison tab %s", t["tab_name"])
            df_comp = pd.DataFrame()
            has_data = False
        comp_to_write.append((t, df_comp, has_data))

    any_comp_has_data = any(has_data for (_, _, has_data) in comp_to_write)
    if not any_comp_has_data:
        logger.info("Skipping creation of ALL_WINDOW_COMPARISON because no comparison data exists.")
        results["ALL_WINDOW_COMPARISON"] = {
            "created": False,
            "reason": "no_data",
            "written_tabs": [],
            "skipped_tabs": [t["tab_name"] for (t, _, _) in comp_to_write],
        }
    else:
        # Create/open spreadsheet
        target_name = "ALL_WINDOW_COMPARISON"
        try:
            try:
                target_ss = _retry_gspread_call(
                    lambda: client.open(target_name), action_desc=f"open_spreadsheet:{target_name}"
                )
                created_new = False
            except SpreadsheetNotFound:
                target_ss = _retry_gspread_call(
                    lambda: client.create(target_name),
                    action_desc=f"create_spreadsheet:{target_name}",
                )
                created_new = True
        except Exception as e:
            logger.exception("Could not open/create spreadsheet %s: %s", target_name, e)
            results["ALL_WINDOW_COMPARISON"] = {
                "created": False,
                "reason": "create_failed",
                "error": str(e),
                "written_tabs": [],
                "skipped_tabs": [t["tab_name"] for (t, _, _) in comp_to_write],
            }
        else:
            spreadsheet_id = getattr(target_ss, "id", None) or getattr(
                target_ss, "_properties", {}
            ).get("spreadsheetId")
            spreadsheet_url = (
                f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
                if spreadsheet_id
                else None
            )
            written = []
            skipped = []
            for t, df_comp, has_data in comp_to_write:
                target_tab = t["tab_name"]
                if not has_data:
                    skipped.append(target_tab)
                    logger.info("Skipping comparison tab %s because no data.", target_tab)
                    continue
                try:
                    df_to_write = df_comp.copy()
                    df_to_write.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
                    _stringify_datetimes_inplace(df_to_write)
                    df_to_write = _prepare_kvk_export_df(df_to_write, kvk_no)

                    ws = _get_or_create_ws(
                        target_ss, target_tab, cols=max(1, len(df_to_write.columns))
                    )

                    # Format numeric columns; attempt to use metric name as numeric for formatting heuristics
                    format_cols = []
                    if t["agg_type"] == "player":
                        format_cols = _KVK_FORMAT_NUMBERS.get("KVK_Player_Windowed", [])
                    elif t["agg_type"] == "kingdom":
                        format_cols = _KVK_FORMAT_NUMBERS.get("KVK_Kingdom_Windowed", [])
                    elif t["agg_type"] == "camp":
                        format_cols = _KVK_FORMAT_NUMBERS.get("KVK_Camp_Windowed", [])
                    if t["metric"] not in format_cols:
                        format_cols = format_cols + [t["metric"]]

                    if format_cols:
                        df_cols_lower = {str(c).lower(): c for c in df_to_write.columns}
                        filtered_format_cols: list[Any] = []
                        for fc in format_cols:
                            if isinstance(fc, int):
                                if 0 <= fc < len(df_to_write.columns):
                                    filtered_format_cols.append(fc)
                            elif isinstance(fc, str):
                                match = df_cols_lower.get(fc.lower())
                                if match is not None:
                                    filtered_format_cols.append(match)
                            else:
                                filtered_format_cols.append(fc)
                        format_cols = filtered_format_cols

                    # Sort by Overall column DESC in pandas (last column)
                    if not df_to_write.empty:
                        overall_col = df_to_write.columns[-1]
                        df_to_write = df_to_write.sort_values(
                            by=overall_col, ascending=False, kind="mergesort"
                        )

                    export_dataframe_to_sheet(
                        ws, df_to_write, service=service, format_columns=format_cols
                    )

                    written.append(target_tab)
                except Exception:
                    logger.exception("Failed to write comparison tab %s", target_tab)
                    skipped.append(target_tab)
            # Reorder tabs to match explicit comparison_tabs order
            try:
                if spreadsheet_id:
                    title_to_id = {ws.title: ws.id for ws in target_ss.worksheets()}
                    desired_titles = [t["tab_name"] for t in comparison_tabs]
                    _reorder_sheet_tabs(service, spreadsheet_id, title_to_id, desired_titles)
            except Exception:
                logger.exception("Failed to reorder ALL_WINDOW_COMPARISON tabs")
            results["ALL_WINDOW_COMPARISON"] = {
                "created": True,
                "created_new": created_new,
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_url": spreadsheet_url,
                "written_tabs": written,
                "skipped_tabs": skipped,
            }

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
                    # Discord allows up to 25 buttons per message (5 rows * 5 buttons)
                    max_buttons = 25
                    for name, meta in created_items[:max_buttons]:
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


# -------------------------
# Public exports
# -------------------------
__all__ = [
    "_coerce_date_uk",
    "_coerce_float",
    "_coerce_int",
    "_dfs_from_proc",
    "_normalize_headers",
    "check_basic_gsheets_access",
    "create_additional_kvk_spreadsheets",
    "get_gsheet_client",
    "get_sheet_values",
    "get_sort_service",
    "run_all_exports",
    "run_kvk_export_test",
    "run_kvk_proc_exports_with_alerts",
    "run_single_export",
]
