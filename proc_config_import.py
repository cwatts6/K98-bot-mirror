# proc_config_import.py
from __future__ import annotations

import json
import logging
import os
import random
import time

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import pandas as pd
import pyodbc
import tenacity

from constants import (
    CREDENTIALS_FILE,
    DATA_DIR,
    DATABASE,
    IMPORT_PASSWORD,
    IMPORT_USERNAME,
    KVK_SHEET_ID,
    SERVER,
    _conn_import,
)
from gsheet_module import (
    DEFAULT_SHEETS_BACKOFF_FACTOR,
    DEFAULT_SHEETS_MAX_RETRIES,
    DEFAULT_SHEETS_TIMEOUT,
    _build_sheets_with_timeout,
    _coerce_date_uk,
    _coerce_float,
    _coerce_int,
    _normalize_headers,
    _safe_execute,
)

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

# Import centralized helpers from sheet_importer (Phase 3 centralization)
from sheet_importer import (
    detect_transient_error,
    write_df_to_staging_and_upsert,
    write_df_to_table,
)

# Optional log health helpers (module may or may not exist in your environment)
LOG_HEALTH_AVAILABLE = True
try:
    from log_health import (
        LogHeadroomError,
        emit_telemetry_event,
        log_backup_context,
        preflight_or_raise,
    )
except Exception:
    # If log_health import fails, fall back to no-op but record the fact and notify
    LOG_HEALTH_AVAILABLE = False
    LogHeadroomError = Exception  # fallback; preflight_or_raise may not be available
    log_backup_context = lambda *a, **k: None
    preflight_or_raise = lambda *a, **k: None
    # Emit a clear warning so operators notice silent fallback; attempt telemetry if available
    try:
        logger.warning(
            "[IMPORT][HARDEN] log_health module unavailable — preflight/log-backup checks will be skipped"
        )
        emit_telemetry_event(
            {
                "service": "proc_config_import",
                "event": "log_health_missing",
                "message": "log_health import failed",
            }
        )
    except Exception:
        # Best-effort only: do not raise during module import
        logger.debug("[IMPORT][HARDEN] emit_telemetry_event unavailable or failed (suppressed)")

# Allow strict deployments to require preflight/log_health to be present
IMPORT_REQUIRE_PREFLIGHT = os.getenv("IMPORT_REQUIRE_PREFLIGHT", "0").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Optional telemetry emitter (best-effort)
try:
    from file_utils import emit_telemetry_event
except Exception:
    emit_telemetry_event = lambda *a, **k: None

# ---------------------------------------------------------------------------
# Phase 1 helpers: structured report template + persistence (kept)
# ---------------------------------------------------------------------------


def _make_import_report_template(dry_run: bool = False) -> dict:
    return {
        "version": "proc_import_v1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dry_run": bool(dry_run),
        "tables": {},  # table_name -> {rows:int, status: "ok"|"error", error: str|None}
        "errors": [],
        "start_time": time.time(),
        "duration_sec": None,
        "transactional": bool(
            os.getenv("IMPORT_TRANSACTIONAL", "1").strip().lower() in ("1", "true", "yes")
        ),
        "meta": {"spreadsheet_id": KVK_SHEET_ID},
    }


def _persist_import_report(report: dict, *, filename: str | None = None) -> str | None:
    path = filename or os.path.join(DATA_DIR, "last_proc_import_report.json")
    try:
        try:
            from file_utils import atomic_write_json  # type: ignore
        except Exception:
            atomic_write_json = None

        if atomic_write_json:
            atomic_write_json(path, report)
        else:
            tmp = f"{path}.tmp"
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            os.replace(tmp, path)
        logger.debug("[IMPORT] Persisted import report to %s", path)
        return path
    except Exception:
        logger.exception("[IMPORT] Failed to persist import report to %s", path)
        return None


def _set_last_import_report(report: dict, *, persist: bool = True) -> None:
    global last_import_report
    try:
        last_import_report = report
        if persist:
            p = _persist_import_report(report)
            if p:
                report["persisted_to"] = p
    except Exception:
        logger.exception("[IMPORT] _set_last_import_report failed (suppressed)")


# Expose last run report for backward compatibility / programmatic inspection
last_import_report: dict | None = None


# Honor environment overrides
GSHEETS_TIMEOUT = int(os.getenv("GSHEETS_HTTP_TIMEOUT", str(DEFAULT_SHEETS_TIMEOUT)))
GSHEETS_MAX_RETRIES = int(os.getenv("GSHEETS_MAX_RETRIES", str(DEFAULT_SHEETS_MAX_RETRIES)))
GSHEETS_BACKOFF_FACTOR = float(
    os.getenv("GSHEETS_BACKOFF_FACTOR", str(DEFAULT_SHEETS_BACKOFF_FACTOR))
)

# Configurable batch size
DEFAULT_BATCH_SIZE = 5000
BATCH_SIZE = int(os.getenv("PROC_IMPORT_BATCH_SIZE", str(DEFAULT_BATCH_SIZE)))

# Feature toggles
IMPORT_TRANSACTIONAL = os.getenv("IMPORT_TRANSACTIONAL", "1").strip().lower() in (
    "1",
    "true",
    "yes",
)
IMPORT_CAPTURE_LOGSPACE = os.getenv("IMPORT_CAPTURE_LOGSPACE", "1").strip().lower() in (
    "1",
    "true",
    "yes",
)
IMPORT_TRANSACTIONAL_TABLES = os.getenv(
    "IMPORT_TRANSACTIONAL_TABLES",
    "dbo.ProcConfig_Staging,dbo.KVKTargetBands,dbo.EXEMPT_FROM_STATS,dbo.KVK_Details,KVK.KVK_DKPWeights,KVK.KVK_Windows,KVK.KVK_CampMap",
)


# ---------------------------------------------------------------------------
# Connection Helpers (use centralized constants._conn_import with retry)
# ---------------------------------------------------------------------------
def _retry_predicate(exc: BaseException) -> bool:
    try:
        return isinstance(exc, pyodbc.OperationalError) or detect_transient_error(exc)
    except Exception:
        return False


@tenacity.retry(
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_fixed(10),
    retry=tenacity.retry_if_exception(_retry_predicate),
    reraise=True,
)
def _get_import_connection_with_retry():
    return _conn_import()


def _enable_fast_executemany(cursor) -> bool:
    """Try to enable pyodbc cursor.fast_executemany if supported; return True if enabled."""
    try:
        cursor.fast_executemany = True
        return bool(getattr(cursor, "fast_executemany", False))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# GSheet helpers
# ---------------------------------------------------------------------------
def _get_sheet_service():
    """
    Adapter that returns a sheet-like object whose values().get(...).execute() will
    delegate to gsheet_module.get_sheet_values(...). This preserves the original
    call shape while centralizing Sheets access.

    Fallback: if gm.get_sheet_values is unavailable or fails, fall back to the
    previous behaviour that builds a service via service_account + _build_sheets_with_timeout.
    """
    # Try to build an adapter backed by gm.get_sheet_values
    try:
        import gsheet_module as gm  # local import to avoid cycle at top-level

        if hasattr(gm, "get_sheet_values"):

            class _Req:
                def __init__(self, spreadsheet_id, range_name, timeout):
                    self._ssid = spreadsheet_id
                    self._range = range_name
                    self._timeout = timeout

                def execute(self, num_retries=0):
                    rows = gm.get_sheet_values(self._ssid, self._range, timeout=self._timeout)
                    # gm returns None on error; convert to empty list to match execute() expectations
                    return {"values": rows or []}

            class _Values:
                def get(self, **kwargs):
                    # The original callers pass spreadsheetId and range (named args)
                    ss = kwargs.get("spreadsheetId")
                    rng = kwargs.get("range")
                    return _Req(ss, rng, timeout=GSHEETS_TIMEOUT)

            class _Sheet:
                def values(self):
                    return _Values()

            return _Sheet()
    except Exception:
        # adapter creation failed; fall through to legacy fallback
        pass

    # Legacy fallback: preserve previous behaviour (build a real Sheets service)
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=scopes
        )
    except FileNotFoundError:
        logger.error("Google credentials file not found:  %s", CREDENTIALS_FILE)
        raise
    except Exception:
        logger.exception("Failed to load Google credentials from %s", CREDENTIALS_FILE)
        raise

    try:
        service = _build_sheets_with_timeout(
            creds,
            timeout=GSHEETS_TIMEOUT,
            max_retries=GSHEETS_MAX_RETRIES,
            backoff_factor=GSHEETS_BACKOFF_FACTOR,
        )
    except TypeError:
        service = _build_sheets_with_timeout(creds, timeout=GSHEETS_TIMEOUT)
    return service.spreadsheets()


def _read_sheet_to_df(sheet, spreadsheet_id: str, range_name: str) -> pd.DataFrame:
    """
    Read a sheet range into a pandas DataFrame.

    Preferred path: use gm.get_sheet_values to get rows list (centralized helper).
    Fallback: use sheet.values().get(...).execute() with _safe_execute for compatibility.
    """
    # small jitter to reduce thundering herd
    time.sleep(random.uniform(0.10, 0.60))

    # Preferred: centralized wrapper
    try:
        import gsheet_module as gm  # local import to reduce startup coupling

        if hasattr(gm, "get_sheet_values"):
            try:
                rows = gm.get_sheet_values(spreadsheet_id, range_name, timeout=GSHEETS_TIMEOUT)
            except Exception:
                rows = None

            # gm.get_sheet_values returns:
            #   - list[list] on success (may be empty)
            #   - None on error
            if rows is not None:
                # Empty or missing header -> empty DataFrame
                if not rows or not rows[0]:
                    return pd.DataFrame()

                headers = rows[0]
                rows_data = rows[1:]
                df = pd.DataFrame(rows_data, columns=headers)
                # Standard clean: empty -> None, trim strings
                df.replace(to_replace=r"^\s*$", value=None, regex=True, inplace=True)
                return df
    except Exception:
        # If wrapper import or conversion failed, silently fall back to existing code below.
        logger.debug(
            "gm.get_sheet_values wrapper unavailable or failed; falling back", exc_info=True
        )

    # Fallback: original behaviour using 'sheet' and _safe_execute
    request = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueRenderOption="FORMATTED_VALUE",
        dateTimeRenderOption="FORMATTED_STRING",
    )
    try:
        result = _safe_execute(request, retries=GSHEETS_MAX_RETRIES)
    except Exception:
        logger.exception(
            "Final failure reading range '%s' from spreadsheet %s", range_name, spreadsheet_id
        )
        raise

    values = result.get("values", [])
    if not values or not values[0]:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

    # Standard clean: empty -> None, trim strings
    df.replace(to_replace=r"^\s*$", value=None, regex=True, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Type coercion utilities (unchanged)
# ---------------------------------------------------------------------------


def _log_date_parse_stats(df: pd.DataFrame, col: str, label: str):
    if col in df.columns:
        total = len(df)
        parsed = df[col].notna().sum()
        blanks = (df[col].isna()).sum()
        logger.info("%s: parsed=%s/%s, blanks_or_invalid=%s", label, parsed, total, blanks)


# ---------------------------------------------------------------------------
# DB helper: run DBCC SQLPERF(LOGSPACE) and parse for target DB (best-effort)
# ---------------------------------------------------------------------------
def _get_db_logspace(cursor, dbname: str) -> dict | None:
    try:
        cursor.execute("DBCC SQLPERF(LOGSPACE)")
        rows = cursor.fetchall()
        for r in rows:
            # r[0] -> database name, r[1] -> log size MB, r[2] -> log space used %
            try:
                name = str(r[0]).strip()
                if name.lower() == dbname.lower():
                    size_mb = float(r[1])
                    used_pct = float(r[2])
                    used_mb = size_mb * (used_pct / 100.0)
                    return {
                        "name": name,
                        "size_mb": size_mb,
                        "used_mb": used_mb,
                        "used_pct": used_pct,
                    }
            except Exception:
                continue
    except Exception as e:
        # Permission failure or DBCC not allowed for this principal
        logger.debug("DBCC SQLPERF failed or not permitted: %s", e)
        return None
    return None


# ---------------------------------------------------------------------------
# Validation helpers (Task 1 + enhanced logging for Task 5 debugging)
# ---------------------------------------------------------------------------
def _validate_import_config() -> tuple[bool, list[str]]:
    """
    Validate runtime configuration required to run the import.
    Returns (is_valid, missing_list).
    """
    missing = []

    # Enhanced logging for diagnostics (use logger.info so it appears in normal logs)
    logger.info("[IMPORT][VALIDATION] Checking configuration...")
    logger.info("[IMPORT][VALIDATION] KVK_SHEET_ID=%s", "✓ set" if KVK_SHEET_ID else "✗ missing")
    logger.info(
        "[IMPORT][VALIDATION] CREDENTIALS_FILE=%s",
        CREDENTIALS_FILE if CREDENTIALS_FILE else "✗ missing",
    )
    logger.info("[IMPORT][VALIDATION] SERVER=%s", "✓ set" if SERVER else "✗ missing")
    logger.info("[IMPORT][VALIDATION] DATABASE=%s", "✓ set" if DATABASE else "✗ missing")
    logger.info(
        "[IMPORT][VALIDATION] IMPORT_USERNAME=%s", "✓ set" if IMPORT_USERNAME else "✗ missing"
    )
    logger.info(
        "[IMPORT][VALIDATION] IMPORT_PASSWORD=%s", "✓ set" if IMPORT_PASSWORD else "✗ missing"
    )

    if not KVK_SHEET_ID:
        missing.append("KVK_SHEET_ID")

    if not CREDENTIALS_FILE:
        missing.append("CREDENTIALS_FILE (environment variable not set)")
    elif not os.path.isfile(CREDENTIALS_FILE):
        # Log detailed path info for debugging subprocess working directory issues
        abs_path = os.path.abspath(CREDENTIALS_FILE)
        cwd = os.getcwd()
        logger.error(
            "[IMPORT][VALIDATION] CREDENTIALS_FILE not found:  configured=%s, absolute=%s, exists=%s, cwd=%s",
            CREDENTIALS_FILE,
            abs_path,
            os.path.exists(abs_path),
            cwd,
        )
        missing.append(f"CREDENTIALS_FILE (not found at {CREDENTIALS_FILE})")
    else:
        logger.info("[IMPORT][VALIDATION] CREDENTIALS_FILE exists: %s", CREDENTIALS_FILE)

    if not SERVER:
        missing.append("SERVER")
    if not DATABASE:
        missing.append("DATABASE")
    if not IMPORT_USERNAME:
        missing.append("IMPORT_USERNAME")
    if not IMPORT_PASSWORD:
        missing.append("IMPORT_PASSWORD")

    if missing:
        logger.error("[IMPORT][VALIDATION] Validation failed.  Missing:  %s", ", ".join(missing))
    else:
        logger.info("[IMPORT][VALIDATION] All checks passed ✓")

    return (len(missing) == 0, missing)


def _validate_kvk_details_dataframe(df: pd.DataFrame) -> None:
    """
    Validate KVK_Details DataFrame shape and required columns prior to any destructive DB operation.
    Raises RuntimeError on validation failures.
    """
    ordered_cols = [
        "KVK_NO",
        "KVK_NAME",
        "KVK_REGISTRATION_DATE",
        "KVK_START_DATE",
        "KVK_END_DATE",
        "MATCHMAKING_SCAN",
        "KVK_END_SCAN",
        "NEXT_KVK_NO",
        "MATCHMAKING_START_DATE",
        "FIGHTING_START_DATE",
        "PASS4_START_SCAN",
    ]
    missing = [c for c in ordered_cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"KVK_Details missing required columns: {missing}")


def _validate_sheet_schemas(sheet) -> tuple[bool, list[str]]:
    """
    Minimal schema checks for the configured sheet ranges.
    Returns (ok, errors).
    """
    errors: list[str] = []

    # ProcConfig:  ensure KVK_NO header exists
    try:
        df = _read_sheet_to_df(sheet, KVK_SHEET_ID, "ProcConfig!A1:J")
        cols = set(df.columns.tolist()) if isinstance(df, pd.DataFrame) else set()
        if "KVK_NO" not in cols:
            errors.append("ProcConfig:  missing 'KVK_NO' column")
    except Exception as exc:
        errors.append(f"ProcConfig: failed to read sheet ({exc})")

    # KVK_Details
    try:
        df_details = _read_sheet_to_df(sheet, KVK_SHEET_ID, "KVK_Details!A1:K")
        cols = set(df_details.columns.tolist()) if isinstance(df_details, pd.DataFrame) else set()
        if cols:
            ordered_cols = [
                "KVK_NO",
                "KVK_NAME",
                "KVK_REGISTRATION_DATE",
                "KVK_START_DATE",
                "KVK_END_DATE",
                "MATCHMAKING_SCAN",
                "KVK_END_SCAN",
                "NEXT_KVK_NO",
                "MATCHMAKING_START_DATE",
                "FIGHTING_START_DATE",
                "PASS4_START_SCAN",
            ]
            missing = [c for c in ordered_cols if c not in cols]
            if missing:
                errors.append(f"KVK_Details:  missing columns:  {missing}")
    except Exception as exc:
        errors.append(f"KVK_Details:  failed to read sheet ({exc})")

    # KVK_DKPWeights
    try:
        df_weights = _read_sheet_to_df(sheet, KVK_SHEET_ID, "KVK_DKPWeights!A1:D")
        cols = set(df_weights.columns.tolist()) if isinstance(df_weights, pd.DataFrame) else set()
        if cols:
            required = ["KVK_NO", "WeightT4X", "WeightT5Y", "WeightDeadsZ"]
            missing = [c for c in required if c not in cols]
            if missing:
                errors.append(f"KVK_DKPWeights:  missing columns: {missing}")
    except Exception as exc:
        errors.append(f"KVK_DKPWeights: failed to read sheet ({exc})")

    # KVK_Windows
    try:
        df_win = _read_sheet_to_df(sheet, KVK_SHEET_ID, "KVK_Windows!A1:F")
        cols = set(df_win.columns.tolist()) if isinstance(df_win, pd.DataFrame) else set()
        if cols:
            df_win = _normalize_headers(
                df_win,
                {
                    "KVK_NO": ["KVK_NO"],
                    "WindowName": ["WindowName"],
                    "WindowSeq": ["WindowSeq", "Seq", "Order"],
                    "StartScanID": ["StartScanID", "Start Scan", "Start ScanID"],
                    "EndScanID": ["EndScanID", "End Scan", "End ScanID"],
                    "Notes": ["Notes", "Note"],
                },
            )
            cols_after = set(df_win.columns.tolist())
            required = ["KVK_NO", "WindowName", "WindowSeq", "StartScanID", "EndScanID", "Notes"]
            missing = [c for c in required if c not in cols_after]
            if missing:
                errors.append(f"KVK_Windows: missing columns after normalization: {missing}")
    except Exception as exc:
        errors.append(f"KVK_Windows: failed to read sheet ({exc})")

    # KVK_CampMap
    try:
        df_camp = _read_sheet_to_df(sheet, KVK_SHEET_ID, "KVK_CampMap!A1:D")
        cols = set(df_camp.columns.tolist()) if isinstance(df_camp, pd.DataFrame) else set()
        if cols:
            df_camp = _normalize_headers(
                df_camp,
                {
                    "KVK_NO": ["KVK_NO"],
                    "Kingdom": ["Kingdom"],
                    "CampID": ["CampID", "Camp Id", "Camp"],
                    "CampName": ["CampName", "Campname", "Camp Name"],
                },
            )
            cols_after = set(df_camp.columns.tolist())
            required = ["KVK_NO", "Kingdom", "CampID", "CampName"]
            missing = [c for c in required if c not in cols_after]
            if missing:
                errors.append(f"KVK_CampMap: missing columns after normalization: {missing}")
    except Exception as exc:
        errors.append(f"KVK_CampMap: failed to read sheet ({exc})")

    ok = len(errors) == 0
    return ok, errors


# ---------------------------------------------------------------------------
# Main import entrypoint (modified to use write_df_to_staging_and_upsert)
# ---------------------------------------------------------------------------
def run_proc_config_import(dry_run: bool = False) -> tuple[bool, dict]:
    global last_import_report
    load_dotenv()

    report: dict = _make_import_report_template(dry_run)

    ok, missing = _validate_import_config()
    if not ok:
        msg = f"Missing required configuration:  {', '.join(missing)}"
        logger.error("[IMPORT] %s", msg)
        report["errors"].append(msg)
        _set_last_import_report(report)
        return False, report

    # NEW: If deployment requests preflight to be required but log_health utilities
    # are not available, abort early and record the failure.
    if IMPORT_REQUIRE_PREFLIGHT and not LOG_HEALTH_AVAILABLE:
        msg = "Required preflight/log-health helpers unavailable (IMPORT_REQUIRE_PREFLIGHT=1)"
        logger.error("[IMPORT] %s", msg)
        report["errors"].append(msg)
        _set_last_import_report(report)
        return False, report

    if dry_run:
        logger.info("[IMPORT] Dry-run requested - validating Google Sheets schemas (no DB changes)")
        try:
            try:
                sheet_service = _get_sheet_service()
            except Exception as exc:
                logger.error("[IMPORT][DRYRUN] Failed to create sheet service: %s", exc)
                report["errors"].append(f"Failed to create sheet service: {exc}")
                _set_last_import_report(report)
                return False, report

            ok_sheets, sheet_errors = _validate_sheet_schemas(sheet_service)
            if not ok_sheets:
                for e in sheet_errors:
                    logger.error("[IMPORT][DRYRUN] Schema check:  %s", e)
                    report["errors"].append(str(e))
                logger.error("[IMPORT][DRYRUN] One or more sheet schema checks failed")
                report["sheets_ok"] = False
                _set_last_import_report(report)
                return False, report

            logger.info("[IMPORT][DRYRUN] All sheet schema checks passed")
            report["sheets_ok"] = True
            _set_last_import_report(report)
            return True, report
        except Exception:
            logger.exception("[IMPORT][DRYRUN] Unexpected error during dry-run schema checks")
            report["errors"].append("Unexpected error during dry-run schema checks")
            _set_last_import_report(report)
            return False, report

    RANGE_NAME = "ProcConfig!A1:J"
    BAND_RANGE_NAME = "KVKTargetBands!A1:E"
    EXEMPT_RANGE_NAME = "EXEMPT!A1:D"
    DETAILS_RANGE_NAME = "KVK_Details!A1:K"
    WEIGHTS_RANGE_NAME = "KVK_DKPWeights!A1:D"
    WINDOWS_RANGE_NAME = "KVK_Windows!A1:F"
    CAMP_RANGE_NAME = "KVK_CampMap!A1:D"

    conn = None
    cursor = None
    committed_tables: list[str] = []
    _tx_tables = [t.strip() for t in IMPORT_TRANSACTIONAL_TABLES.split(",") if t.strip()]

    try:
        sheet = _get_sheet_service()

        logger.info("Importing ProcConfig (range=%s spreadsheet=%s)", RANGE_NAME, KVK_SHEET_ID)
        df = _read_sheet_to_df(sheet, KVK_SHEET_ID, RANGE_NAME)
        if df.empty or "KVK_NO" not in df.columns:
            msg = "ProcConfig tab empty or missing KVK_NO. Aborting import"
            logger.error(msg)
            report["errors"].append(msg)
            _set_last_import_report(report)
            return False, report

        df = df[df["KVK_NO"].notna()]
        conn = _get_import_connection_with_retry()
        cursor = conn.cursor()

        try:
            preflight_or_raise(conn, dbname=DATABASE, warn_threshold=85.0)
        except LogHeadroomError as e:
            msg = f"SQL log headroom insufficient: {e}"
            logger.error(msg)
            report["errors"].append(msg)
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            _set_last_import_report(report)
            return False, report

        try:
            log_backup_context(cursor, DATABASE)
        except Exception:
            logger.debug("Failed to log backup context", exc_info=True)

        tx_start = None
        log_before = None
        log_after = None
        try:
            if IMPORT_TRANSACTIONAL:
                logger.info("[IMPORT][TX] Starting transactional import for config tables")
                try:
                    conn.autocommit = False
                except Exception:
                    pass

                if IMPORT_CAPTURE_LOGSPACE:
                    try:
                        log_before = _get_db_logspace(cursor, DATABASE)
                        if log_before:
                            report["log_before_mb"] = log_before.get("used_mb")
                    except Exception:
                        logger.debug("Failed to capture logspace before transaction", exc_info=True)

                tx_start = time.time()

                # === REPLACED: use centralized write_df_to_staging_and_upsert for ProcConfig staging + upsert
                try:
                    write_res = write_df_to_staging_and_upsert(
                        cursor,
                        conn,
                        df,
                        "dbo.ProcConfig_Staging",
                        "dbo.sp_Upsert_ProcConfig_From_Staging",
                        batch_size=BATCH_SIZE,
                        transactional=True,
                    )
                except Exception:
                    logger.exception(
                        "[IMPORT] write_df_to_staging_and_upsert failed for ProcConfig"
                    )
                    raise

                # Record both staging and upsert outcomes into report
                report["tables"]["dbo.ProcConfig_Staging"] = write_res.get("staging", {})
                report["tables"]["dbo.ProcConfig_Staging_upsert"] = write_res.get("upsert", {})

                # Check for errors in either stage
                staging_ok = write_res.get("staging", {}).get("status") == "ok"
                upsert_ok = write_res.get("upsert", {}).get("status") == "ok"
                if not staging_ok:
                    raise RuntimeError(
                        f"ProcConfig staging failed: {write_res.get('staging', {}).get('error')}"
                    )
                if not upsert_ok:
                    raise RuntimeError(
                        f"ProcConfig upsert failed: {write_res.get('upsert', {}).get('error')}"
                    )

                # Continue with other table writes inside same transaction (unchanged)
                df_bands = _read_sheet_to_df(sheet, KVK_SHEET_ID, BAND_RANGE_NAME)
                if not df_bands.empty:
                    _coerce_int(
                        df_bands, ["KVKVersion", "KillTarget", "MinKillTarget", "DeadTarget"]
                    )
                    _coerce_float(df_bands, ["MinPower"])
                res = write_df_to_table(
                    cursor,
                    conn,
                    df_bands,
                    "dbo.KVKTargetBands",
                    mode="truncate",
                    transactional=True,
                )
                report["tables"]["dbo.KVKTargetBands"] = res
                if res.get("status") != "ok":
                    raise RuntimeError(f"KVKTargetBands write failed: {res.get('error')}")

                # EXEMPT
                df_exempt = _read_sheet_to_df(sheet, KVK_SHEET_ID, EXEMPT_RANGE_NAME)
                if not df_exempt.empty:
                    _coerce_int(df_exempt, ["GovernorID", "KVK_NO", "Exempt"])
                res = write_df_to_table(
                    cursor,
                    conn,
                    df_exempt,
                    "dbo.EXEMPT_FROM_STATS",
                    mode="truncate",
                    transactional=True,
                )
                report["tables"]["dbo.EXEMPT_FROM_STATS"] = res
                if res.get("status") != "ok":
                    raise RuntimeError(f"EXEMPT write failed: {res.get('error')}")

                # KVK_Details (unchanged)
                df_details = _read_sheet_to_df(sheet, KVK_SHEET_ID, DETAILS_RANGE_NAME)
                if not df_details.empty:
                    try:
                        _validate_kvk_details_dataframe(df_details)
                    except Exception:
                        logger.exception("KVK_Details validation failed")
                        raise
                    _coerce_int(
                        df_details,
                        [
                            "KVK_NO",
                            "MATCHMAKING_SCAN",
                            "KVK_END_SCAN",
                            "NEXT_KVK_NO",
                            "PASS4_START_SCAN",
                        ],
                    )
                    _coerce_date_uk(
                        df_details,
                        [
                            "KVK_REGISTRATION_DATE",
                            "KVK_START_DATE",
                            "KVK_END_DATE",
                            "MATCHMAKING_START_DATE",
                            "FIGHTING_START_DATE",
                        ],
                    )
                    df_details["KVK_NO"] = pd.to_numeric(
                        df_details["KVK_NO"], errors="coerce"
                    ).astype("Int64")
                    df_details = df_details.dropna(subset=["KVK_NO"])
                    ordered_cols = [
                        "KVK_NO",
                        "KVK_NAME",
                        "KVK_REGISTRATION_DATE",
                        "KVK_START_DATE",
                        "KVK_END_DATE",
                        "MATCHMAKING_SCAN",
                        "KVK_END_SCAN",
                        "NEXT_KVK_NO",
                        "MATCHMAKING_START_DATE",
                        "FIGHTING_START_DATE",
                        "PASS4_START_SCAN",
                    ]
                    df_details = df_details[ordered_cols].dropna(subset=["KVK_NO"])
                res = write_df_to_table(
                    cursor, conn, df_details, "dbo.KVK_Details", mode="truncate", transactional=True
                )
                report["tables"]["dbo.KVK_Details"] = res
                if res.get("status") != "ok":
                    raise RuntimeError(f"KVK_Details write failed: {res.get('error')}")

                # KVK_DKPWeights
                df_weights = _read_sheet_to_df(sheet, KVK_SHEET_ID, WEIGHTS_RANGE_NAME)
                if not df_weights.empty:
                    required = ["KVK_NO", "WeightT4X", "WeightT5Y", "WeightDeadsZ"]
                    missing = [c for c in required if c not in df_weights.columns]
                    if missing:
                        raise RuntimeError(f"KVK_DKPWeights missing columns: {missing}")
                    _coerce_int(df_weights, ["KVK_NO"])
                    _coerce_float(df_weights, ["WeightT4X", "WeightT5Y", "WeightDeadsZ"])
                    df_weights = df_weights[required].dropna(subset=["KVK_NO"])
                res = write_df_to_table(
                    cursor,
                    conn,
                    df_weights,
                    "KVK.KVK_DKPWeights",
                    mode="delete_by_kvk",
                    key_cols=["KVK_NO"],
                    transactional=True,
                )
                report["tables"]["KVK.KVK_DKPWeights"] = res
                if res.get("status") != "ok":
                    raise RuntimeError(f"KVK_DKPWeights write failed: {res.get('error')}")

                # KVK_Windows
                df_win = _read_sheet_to_df(sheet, KVK_SHEET_ID, WINDOWS_RANGE_NAME)
                df_win = _normalize_headers(
                    df_win,
                    {
                        "KVK_NO": ["KVK_NO"],
                        "WindowName": ["WindowName"],
                        "WindowSeq": ["WindowSeq", "Seq", "Order"],
                        "StartScanID": ["StartScanID", "Start Scan", "Start ScanID"],
                        "EndScanID": ["EndScanID", "End Scan", "End ScanID"],
                        "Notes": ["Notes", "Note"],
                    },
                )
                if not df_win.empty:
                    required = [
                        "KVK_NO",
                        "WindowName",
                        "WindowSeq",
                        "StartScanID",
                        "EndScanID",
                        "Notes",
                    ]
                    missing = [c for c in required if c not in df_win.columns]
                    if missing:
                        raise RuntimeError(f"KVK_Windows missing columns: {missing}")
                    _coerce_int(df_win, ["KVK_NO", "WindowSeq", "StartScanID", "EndScanID"])
                    df_win = df_win[required].dropna(subset=["KVK_NO", "WindowName"])
                res = write_df_to_table(
                    cursor,
                    conn,
                    df_win,
                    "KVK.KVK_Windows",
                    mode="delete_by_kvk",
                    key_cols=["KVK_NO"],
                    transactional=True,
                )
                report["tables"]["KVK.KVK_Windows"] = res
                if res.get("status") != "ok":
                    raise RuntimeError(f"KVK_Windows write failed: {res.get('error')}")

                # KVK_CampMap
                df_camp = _read_sheet_to_df(sheet, KVK_SHEET_ID, CAMP_RANGE_NAME)
                df_camp = _normalize_headers(
                    df_camp,
                    {
                        "KVK_NO": ["KVK_NO"],
                        "Kingdom": ["Kingdom"],
                        "CampID": ["CampID", "Camp Id", "Camp"],
                        "CampName": ["CampName", "Campname", "Camp Name"],
                    },
                )
                if not df_camp.empty:
                    required = ["KVK_NO", "Kingdom", "CampID", "CampName"]
                    missing = [c for c in required if c not in df_camp.columns]
                    if missing:
                        raise RuntimeError(f"KVK_CampMap missing columns:  {missing}")
                    _coerce_int(df_camp, ["KVK_NO", "Kingdom", "CampID"])
                    df_camp = df_camp[required].dropna(
                        subset=["KVK_NO", "Kingdom", "CampID", "CampName"]
                    )
                res = write_df_to_table(
                    cursor,
                    conn,
                    df_camp,
                    "KVK.KVK_CampMap",
                    mode="delete_by_kvk",
                    key_cols=["KVK_NO"],
                    transactional=True,
                )
                report["tables"]["KVK.KVK_CampMap"] = res
                if res.get("status") != "ok":
                    raise RuntimeError(f"KVK_CampMap write failed: {res.get('error')}")

                # Commit transaction
                try:
                    conn.commit()
                except Exception:
                    logger.exception("Commit failed after transactional writes")
                    raise

                tx_end = time.time()
                report["transaction_duration_sec"] = (tx_end - tx_start) if tx_start else None

                if IMPORT_CAPTURE_LOGSPACE:
                    try:
                        log_after = _get_db_logspace(cursor, DATABASE)
                        if log_after:
                            report["log_after_mb"] = log_after.get("used_mb")
                    except Exception:
                        logger.debug("Failed to capture logspace after transaction", exc_info=True)
            else:
                # Non-transactional: write staging & upsert via central helper but let helper perform per-table commits
                try:
                    write_res = write_df_to_staging_and_upsert(
                        cursor,
                        conn,
                        df,
                        "dbo.ProcConfig_Staging",
                        "dbo.sp_Upsert_ProcConfig_From_Staging",
                        batch_size=BATCH_SIZE,
                        transactional=False,
                    )
                except Exception:
                    logger.exception(
                        "[IMPORT] write_df_to_staging_and_upsert (non-transactional) failed"
                    )
                    report["errors"].append("ProcConfig non-transactional staging/upsert failed")
                    _set_last_import_report(report)
                    return False, report

                report["tables"]["dbo.ProcConfig_Staging"] = write_res.get("staging", {})
                report["tables"]["dbo.ProcConfig_Staging_upsert"] = write_res.get("upsert", {})
                # Ensure final commit for upsert (write_df_to_staging_and_upsert leaves commit control to caller)
                try:
                    conn.commit()
                except Exception:
                    logger.exception("Commit failed after non-transactional upsert")
                    raise

        except Exception as e:
            logger.exception("[IMPORT][TX] Transactional block failed")
            try:
                if conn:
                    conn.rollback()
                    logger.info("[IMPORT][TX] Rollback executed")
            except Exception:
                logger.exception("[IMPORT][TX] Rollback attempt failed")
            report["errors"].append(str(e))
            report["partial_commits"] = []  # transactional block rolled back; nothing committed
            _set_last_import_report(report)

            try:
                os.makedirs(os.path.join(DATA_DIR, "imports"), exist_ok=True)
                manifest_path = os.path.join(
                    DATA_DIR, "imports", f"proc_import_manifest_{int(time.time())}.json"
                )
                with open(manifest_path, "w", encoding="utf-8") as mf:
                    json.dump(report, mf, indent=2, default=str)
                report["manifest_path"] = manifest_path
                logger.info("[IMPORT] Persisted import manifest to %s", manifest_path)
            except Exception:
                logger.exception("Failed to write import manifest on failure")

            return False, report

        # Determine the latest KVK from SQL (more robust than parsing imported DataFrame)
        latest_kvk = None
        try:
            # Use existing kvk_meta helper to get latest KVK from dbo.KVK_Details
            from stats_alerts.kvk_meta import get_latest_kvk_metadata_sql

            kvk_meta = get_latest_kvk_metadata_sql()
            if kvk_meta and kvk_meta.get("kvk_no"):
                latest_kvk = int(kvk_meta["kvk_no"])
                logger.info(
                    "[IMPORT] Latest KVK from SQL metadata: %s (%s)",
                    latest_kvk,
                    kvk_meta.get("kvk_name", "Unknown"),
                )
            else:
                logger.warning(
                    "[IMPORT] get_latest_kvk_metadata_sql returned None or missing kvk_no; "
                    "falling back to DataFrame parsing"
                )
                # Fallback: parse from imported DataFrame
                if not df.empty and "KVK_NO" in df.columns:
                    kvk_values = pd.to_numeric(df["KVK_NO"], errors="coerce").dropna()
                    if len(kvk_values) > 0:
                        latest_kvk = int(kvk_values.max())
                        logger.info(
                            "[IMPORT] Latest KVK from imported DataFrame (fallback): %s", latest_kvk
                        )
        except ImportError:
            logger.warning(
                "[IMPORT] kvk_meta module not available; falling back to DataFrame parsing",
                exc_info=True,
            )
            # Fallback: parse from imported DataFrame
            try:
                if not df.empty and "KVK_NO" in df.columns:
                    kvk_values = pd.to_numeric(df["KVK_NO"], errors="coerce").dropna()
                    if len(kvk_values) > 0:
                        latest_kvk = int(kvk_values.max())
                        logger.info(
                            "[IMPORT] Latest KVK from imported DataFrame (fallback): %s", latest_kvk
                        )
            except Exception:
                logger.exception("[IMPORT] DataFrame fallback also failed")
        except Exception:
            logger.warning(
                "[IMPORT] get_latest_kvk_metadata_sql failed; falling back to DataFrame parsing",
                exc_info=True,
            )
            # Fallback: parse from imported DataFrame
            try:
                if not df.empty and "KVK_NO" in df.columns:
                    kvk_values = pd.to_numeric(df["KVK_NO"], errors="coerce").dropna()
                    if len(kvk_values) > 0:
                        latest_kvk = int(kvk_values.max())
                        logger.info(
                            "[IMPORT] Latest KVK from imported DataFrame (fallback): %s", latest_kvk
                        )
            except Exception:
                logger.exception("[IMPORT] DataFrame fallback also failed")

        # Post-transaction stored proc
        try:
            if latest_kvk is not None:
                logger.info(
                    "Running sp_TARGETS_MASTER for KVK %s (incremental refresh)", latest_kvk
                )
                cursor.execute("EXEC dbo.sp_TARGETS_MASTER @KVK = ?", (latest_kvk,))
                report["targets_master_mode"] = "incremental"
                report["targets_master_kvk"] = latest_kvk
            else:
                logger.info(
                    "Running sp_TARGETS_MASTER (full refresh - no KVK determined from SQL or data)"
                )
                cursor.execute("EXEC dbo.sp_TARGETS_MASTER")
                report["targets_master_mode"] = "full"
                report["targets_master_kvk"] = None

            conn.commit()
            report["targets_master_executed"] = True
        except Exception:
            logger.exception("sp_TARGETS_MASTER execution failed")
            report["errors"].append("sp_TARGETS_MASTER execution failed")

        report["duration_sec"] = time.time() - report["start_time"]
        success = len(report.get("errors", [])) == 0
        report["success"] = success
        report["partial_commits"] = committed_tables.copy()

        try:
            os.makedirs(os.path.join(DATA_DIR, "imports"), exist_ok=True)
            manifest_path = os.path.join(
                DATA_DIR, "imports", f"proc_import_manifest_{int(time.time())}.json"
            )
            with open(manifest_path, "w", encoding="utf-8") as mf:
                json.dump(report, mf, indent=2, default=str)
            report["manifest_path"] = manifest_path
            logger.info("[IMPORT] Persisted import manifest to %s", manifest_path)
        except Exception:
            logger.exception("Failed to write import manifest (suppressed)")

        # Emit telemetry (best-effort) and also log structured JSON to telemetry logger
        try:
            telemetry_payload = {
                "service": "proc_config_import",
                "success": success,
                "transactional": IMPORT_TRANSACTIONAL,
                "duration_sec": report["duration_sec"],
                "transaction_duration_sec": report.get("transaction_duration_sec"),
                "tables_processed": len(report["tables"]),
                "errors": report["errors"][:5],
            }
            emit_telemetry_event(telemetry_payload)
            try:
                telemetry_logger.info(json.dumps(report, default=str))
            except Exception:
                telemetry_logger.info("proc_config_import report emitted")
        except Exception:
            logger.debug("emit_telemetry_event failed (suppressed)")

        _set_last_import_report(report)
        if not success:
            logger.error("[IMPORT] Import completed with errors: %s", report["errors"])
        else:
            logger.info("[IMPORT] Import completed successfully in %.1fs", report["duration_sec"])
        return success, report

    except (pyodbc.OperationalError, HttpError) as e:
        logger.exception("Transient failure (will have been retried as applicable): %s", e)
        report["errors"].append(str(e))
        report["success"] = False
        _set_last_import_report(report)
        return False, report
    except Exception:
        logger.exception("ProcConfig import critical failure")
        report["errors"].append("ProcConfig import critical failure")
        report["success"] = False
        _set_last_import_report(report)
        return False, report
    finally:
        try:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Phase 3: Offload wrapper (async) — allow safe invocation from async code
# ---------------------------------------------------------------------------
async def run_proc_config_import_offload(
    dry_run: bool = False, *, prefer_process: bool = True, meta: dict | None = None
) -> tuple[bool, dict]:
    """
    Async wrapper to run run_proc_config_import in an isolated worker (preferred)
    or thread fallback. Tries, in order:
      1) file_utils.run_maintenance_with_isolation (preferred)
      2) file_utils.start_callable_offload
      3) file_utils.run_blocking_in_thread
      4) asyncio.to_thread (last resort)

    Returns the (success_bool, report_dict) tuple that run_proc_config_import returns.
    """
    try:
        # For testability: if the test/module has explicitly set module-level names, respect them
        # (even if they are None). Only import from file_utils if the name is NOT present in globals().
        if "run_maintenance_with_isolation" in globals():
            run_maintenance_with_isolation = globals()["run_maintenance_with_isolation"]
        else:
            try:
                from file_utils import run_maintenance_with_isolation as _rmi  # type: ignore

                run_maintenance_with_isolation = _rmi
            except Exception:
                run_maintenance_with_isolation = None

        if "start_callable_offload" in globals():
            start_callable_offload = globals()["start_callable_offload"]
        else:
            try:
                from file_utils import start_callable_offload as _sco  # type: ignore

                start_callable_offload = _sco
            except Exception:
                start_callable_offload = None

        if "run_blocking_in_thread" in globals():
            run_blocking_in_thread = globals()["run_blocking_in_thread"]
        else:
            try:
                from file_utils import run_blocking_in_thread as _rbit  # type: ignore

                run_blocking_in_thread = _rbit
            except Exception:
                run_blocking_in_thread = None

        # 1) run_maintenance_with_isolation: expects a callable and returns result (or (result, meta))
        if run_maintenance_with_isolation is not None:
            res = await run_maintenance_with_isolation(
                run_proc_config_import,
                dry_run,
                name="proc_config_import",
                prefer_process=prefer_process,
                meta=meta or {},
            )
            # Return whatever the isolation helper returned
            return res

        # 2) start_callable_offload: start a subprocess/task and await its completion
        if start_callable_offload is not None:
            res = await start_callable_offload(
                run_proc_config_import,
                dry_run,
                name="proc_config_import",
                prefer_process=prefer_process,
                meta=meta or {},
            )
            return res

        # 3) run_blocking_in_thread: offload to thread
        if run_blocking_in_thread is not None:
            res = await run_blocking_in_thread(
                run_proc_config_import, dry_run, name="proc_config_import", meta=meta or {}
            )
            return res

        # 4) fallback to asyncio.to_thread
        import asyncio as _asyncio

        res = await _asyncio.to_thread(run_proc_config_import, dry_run)
        return res
    except Exception:
        logger.exception("[IMPORT] run_proc_config_import_offload failed")
        return False, {"errors": ["offload wrapper failed"]}
