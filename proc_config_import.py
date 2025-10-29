# proc_config_import.py
from __future__ import annotations

import datetime
import os
import random
import socket
import ssl
import time
import traceback

from dotenv import load_dotenv
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import httplib2
import pandas as pd
import pyodbc
import tenacity

from constants import (
    BASE_DIR,
    CREDENTIALS_FILE,
    DATABASE,
    IMPORT_PASSWORD,
    IMPORT_USERNAME,
    KVK_SHEET_ID,
    SERVER,
)
from gsheet_module import run_single_export


def _build_sheets_with_timeout(creds, timeout: int = 30):
    """
    Build the Sheets service using an HTTP client that enforces a per-request timeout.
    """
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
    attempt = 0
    while True:
        try:
            # disable googleapiclient's internal retries; we handle retries ourselves
            return request.execute(num_retries=0)
        except Exception as exc:
            attempt += 1
            is_transient = _is_transient_error(exc)
            if attempt > retries or not is_transient:
                print(f"[GSHEET] Request failed after {attempt} attempts: {exc}")
                raise
            sleep_s = min(max_sleep, base_sleep * (2 ** (attempt - 1))) * random.uniform(0.8, 1.2)
            print(
                f"[GSHEET] Transient error ({type(exc).__name__}). Retry {attempt}/{retries} in {sleep_s:.2f}s"
            )
            time.sleep(sleep_s)


# ---------------------------------------------------------------------------
# Connection (retry on transient SQL issues)
# ---------------------------------------------------------------------------
@tenacity.retry(
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_fixed(10),
    retry=tenacity.retry_if_exception_type(pyodbc.OperationalError),
    reraise=True,
)
def connect_with_retry(server, database, username, password):
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )


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
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    service = _build_sheets_with_timeout(creds, timeout=30)
    return service.spreadsheets()


def _read_sheet_to_df(sheet, spreadsheet_id: str, range_name: str) -> pd.DataFrame:
    """
    Read a tab range into a DataFrame with first row as header.
    Also strips whitespace-only cells to None and trims strings.
    """
    time.sleep(random.uniform(0.10, 0.60))
    request = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueRenderOption="FORMATTED_VALUE",
        dateTimeRenderOption="FORMATTED_STRING",
    )
    try:
        result = _safe_execute(request, retries=5)
    except Exception as exc:
        print(f"[GSHEET] Final failure reading range '{range_name}': {exc}")
        raise

    values = result.get("values", [])
    if not values or not values[0]:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

    # Standard clean: empty -> None, trim strings
    df.replace(to_replace=r"^\s*$", value=None, regex=True, inplace=True)
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(object).map(lambda x: x.strip() if isinstance(x, str) else x)

    return df


def _normalize_headers(df: pd.DataFrame, rename_map: dict[str, list[str]]) -> pd.DataFrame:
    """Trim header whitespace and apply case-insensitive synonym renames."""
    if df is None or df.empty:
        return df
    # Trim header whitespace first
    df.rename(columns=lambda c: c.strip() if isinstance(c, str) else c, inplace=True)
    # Build lowercase lookup
    lower_map = {(c.lower() if isinstance(c, str) else c): c for c in df.columns}
    for want, alts in rename_map.items():
        found = None
        for alt in alts:
            key = alt.lower()
            if key in lower_map:
                found = lower_map[key]
                break
        if found and found != want:
            df.rename(columns={found: want}, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Type coercion utilities
# ---------------------------------------------------------------------------
def _coerce_int(df: pd.DataFrame, cols: list[str]):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")


def _coerce_float(df: pd.DataFrame, cols: list[str]):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")


def _coerce_date_uk(df: pd.DataFrame, cols: list[str]):
    """
    Parse UK dates reliably without pandas' slow inference warnings.
    Tries DD/MM/YYYY first, then DD/MM/YY. Leaves blanks/invalids as NaT.
    """
    for c in cols:
        if c not in df.columns:
            continue
        s = df[c].astype("string").str.strip()
        s = s.where(s.notna() & (s != ""), None)
        # Try 4-digit year format first
        parsed = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
        # For any remaining NaT, try 2-digit year
        mask = parsed.isna() & s.notna()
        if mask.any():
            parsed.loc[mask] = pd.to_datetime(s[mask], format="%d/%m/%y", errors="coerce")
        df[c] = parsed.dt.date


def _to_db_rows(df: pd.DataFrame) -> list[tuple]:
    """
    Convert a DataFrame to DB-ready rows:
    - pandas NA/NaT -> None
    - pandas nullable ints -> native int or None
    - ensure dates are datetime.date or None
    """
    df2 = df.copy()
    # Replace pandas NA/NaT with None across the board first
    df2 = df2.astype(object).where(pd.notnull(df2), None)
    return [tuple(row) for row in df2.itertuples(index=False, name=None)]


def _log_date_parse_stats(df: pd.DataFrame, col: str, label: str):
    if col in df.columns:
        total = len(df)
        parsed = df[col].notna().sum()
        blanks = (df[col].isna()).sum()
        print(f"[OK] {label}: parsed={parsed}/{total}, blanks_or_invalid={blanks}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_proc_config_import() -> bool:
    load_dotenv()

    RANGE_NAME = "ProcConfig!A1:J"
    BAND_RANGE_NAME = "KVKTargetBands!A1:E"
    EXEMPT_RANGE_NAME = "EXEMPT!A1:D"
    DETAILS_RANGE_NAME = "KVK_Details!A1:K"  # NEW
    WEIGHTS_RANGE_NAME = "KVK_DKPWeights!A1:D"  # NEW
    WINDOWS_RANGE_NAME = (
        "KVK_Windows!A1:F"  # KVK_NO, WindowName, WindowSeq, StartScanID, EndScanID, Notes
    )
    CAMP_RANGE_NAME = "KVK_CampMap!A1:D"  # KVK_NO, Kingdom, CampID, CampName

    conn = None

    try:
        sheet = _get_sheet_service()

        # === ProcConfig sheet ===
        print("[INFO] Importing ProcConfig...")
        df = _read_sheet_to_df(sheet, KVK_SHEET_ID, RANGE_NAME)
        if df.empty or "KVK_NO" not in df.columns:
            raise RuntimeError("ProcConfig tab empty or missing KVK_NO.")

        df = df[df["KVK_NO"].notna()]
        conn = connect_with_retry(SERVER, DATABASE, IMPORT_USERNAME, IMPORT_PASSWORD)
        cursor = conn.cursor()

        cursor.execute("TRUNCATE TABLE dbo.ProcConfig_Staging")
        insert_sql = f"INSERT INTO dbo.ProcConfig_Staging ({','.join(df.columns)}) VALUES ({','.join(['?'] * len(df.columns))})"
        fe = _enable_fast_executemany(cursor)
        cursor.executemany(insert_sql, _to_db_rows(df))
        print(
            f"[PERF] fast_executemany={'ON' if fe else 'off'} for ProcConfig_Staging ({len(df)} rows)."
        )
        cursor.execute("EXEC dbo.sp_Upsert_ProcConfig_From_Staging")
        conn.commit()
        print(f"[OK] ProcConfig rows staged: {len(df)}")

        # === KVKTargetBands sheet ===
        try:
            print("[INFO] Importing KVKTargetBands...")
            df_bands = _read_sheet_to_df(sheet, KVK_SHEET_ID, BAND_RANGE_NAME)
            if not df_bands.empty:
                _coerce_int(df_bands, ["KVKVersion", "KillTarget", "MinKillTarget", "DeadTarget"])
                _coerce_float(df_bands, ["MinPower"])
                cursor.execute("DELETE FROM dbo.KVKTargetBands")
                insert_sql = f"INSERT INTO dbo.KVKTargetBands ({','.join(df_bands.columns)}) VALUES ({','.join(['?'] * len(df_bands.columns))})"
                fe = _enable_fast_executemany(cursor)
                cursor.executemany(insert_sql, _to_db_rows(df_bands))
                print(
                    f"[PERF] fast_executemany={'ON' if fe else 'off'} for KVKTargetBands ({len(df_bands)} rows)."
                )
                conn.commit()
            print(f"[OK] KVKTargetBands rows: {len(df_bands)}")
        except Exception as e:
            print(f"[WARN] KVKTargetBands import failed: {e}")

        # === EXEMPT sheet ===
        try:
            print("[INFO] Importing EXEMPT...")
            df_exempt = _read_sheet_to_df(sheet, KVK_SHEET_ID, EXEMPT_RANGE_NAME)
            if not df_exempt.empty:
                _coerce_int(df_exempt, ["GovernorID", "KVK_NO", "Exempt"])

                cursor.execute("DELETE FROM dbo.EXEMPT_FROM_STATS")
                insert_sql = f"INSERT INTO dbo.EXEMPT_FROM_STATS ({','.join(df_exempt.columns)}) VALUES ({','.join(['?'] * len(df_exempt.columns))})"
                fe = _enable_fast_executemany(cursor)
                cursor.executemany(insert_sql, _to_db_rows(df_exempt))
                print(
                    f"[PERF] fast_executemany={'ON' if fe else 'off'} for EXEMPT_FROM_STATS ({len(df_exempt)} rows)."
                )
                conn.commit()
            print(f"[OK] EXEMPT rows: {len(df_exempt)}")
        except Exception as e:
            print(f"[WARN] EXEMPT import failed: {e}")

        # Recompute targets (unchanged)
        cursor.execute("EXEC dbo.sp_TARGETS_MASTER")
        conn.commit()
        print("[OK] sp_TARGETS_MASTER executed.")

        # === NEW: KVK_Details sheet ===
        try:
            print("[INFO] Importing KVK_Details...")
            df_details = _read_sheet_to_df(sheet, KVK_SHEET_ID, DETAILS_RANGE_NAME)

            if df_details.empty:
                print(
                    "[WARN] KVK_Details returned no rows; table will be truncated and left empty."
                )
                cursor.execute("TRUNCATE TABLE dbo.KVK_Details")
                conn.commit()
                # Skip the rest of the processing for this tab
                print("[OK] KVK_Details rows: 0")
            else:
                # Expected columns: KVK_NO, KVK_NAME, KVK_REGISTRATION_DATE, KVK_START_DATE, KVK_END_DATE, MATCHMAKING_SCAN, KVK_END_SCAN, NEXT_KVK_NO, PASS4_START_SCAN
                # Coerce types safely (UK dates and integers)
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
                _log_date_parse_stats(df_details, "KVK_REGISTRATION_DATE", "KVK_REGISTRATION_DATE")
                _log_date_parse_stats(df_details, "KVK_START_DATE", "KVK_START_DATE")
                _log_date_parse_stats(df_details, "KVK_END_DATE", "KVK_END_DATE")
                _log_date_parse_stats(
                    df_details, "MATCHMAKING_START_DATE", "MATCHMAKING_START_DATE"
                )
                _log_date_parse_stats(df_details, "FIGHTING_START_DATE", "FIGHTING_START_DATE")

                # Keep just known columns and order them for SQL insert
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
                if "KVK_NAME" in df_details.columns:
                    df_details["KVK_NAME"] = (
                        df_details["KVK_NAME"]
                        .astype("string")
                        .str.strip()
                        .where(lambda s: s.ne(""), None)
                    )

                missing = [c for c in ordered_cols if c not in df_details.columns]
                if missing:
                    raise RuntimeError(f"KVK_Details missing columns: {missing}")
                # Ensure KVK_NO is int for primary-key safety during insert
                df_details["KVK_NO"] = pd.to_numeric(df_details["KVK_NO"], errors="coerce").astype(
                    "Int64"
                )
                df_details = df_details.dropna(subset=["KVK_NO"])

                df_details = df_details[ordered_cols].dropna(subset=["KVK_NO"])  # must have key

                # Ensure native Python types for ints/dates (no pandas NA/NaT)
                for c in [
                    "KVK_NO",
                    "MATCHMAKING_SCAN",
                    "KVK_END_SCAN",
                    "NEXT_KVK_NO",
                    "PASS4_START_SCAN",
                ]:
                    if c in df_details.columns:
                        df_details[c] = df_details[c].apply(
                            lambda x: int(x) if x is not None and pd.notna(x) else None
                        )
                for c in [
                    "KVK_REGISTRATION_DATE",
                    "KVK_START_DATE",
                    "KVK_END_DATE",
                    "MATCHMAKING_START_DATE",
                    "FIGHTING_START_DATE",
                ]:
                    if c in df_details.columns:

                        def _as_date(v):
                            if v is None or (isinstance(v, float) and pd.isna(v)):
                                return None
                            if isinstance(v, datetime.date):
                                return v
                            # If any stray strings slipped through, last attempt to parse
                            try:
                                return pd.to_datetime(v, dayfirst=True, errors="coerce").date()
                            except Exception:
                                return None

                        df_details[c] = df_details[c].apply(_as_date)

                # Small sheet – full refresh is simplest and safe:
                cursor.execute("TRUNCATE TABLE dbo.KVK_Details")

                insert_sql = f"INSERT INTO dbo.KVK_Details ({','.join(ordered_cols)}) VALUES ({','.join(['?'] * len(ordered_cols))})"
                fe = _enable_fast_executemany(cursor)
                assert (
                    insert_sql.count("?") == len(ordered_cols) == len(df_details.columns)
                ), f"KVK_Details insert mismatch: sql expects {insert_sql.count('?')}, df has {len(df_details.columns)}"
                cursor.executemany(insert_sql, _to_db_rows(df_details))
                print(
                    f"[PERF] fast_executemany={'ON' if fe else 'off'} for KVK_Details ({len(df_details)} rows)."
                )
                conn.commit()
                print(f"[OK] KVK_Details rows: {len(df_details)}")
        except Exception as e:
            print(f"[WARN] KVK_Details import failed: {e}")

        # === NEW: KVK_DKPWeights sheet ===
        try:
            print("[INFO] Importing KVK_DKPWeights...")
            df_weights = _read_sheet_to_df(sheet, KVK_SHEET_ID, WEIGHTS_RANGE_NAME)

            if df_weights.empty:
                print("[WARN] KVK_DKPWeights returned no rows; skipping.")
                print("[OK] KVK_DKPWeights rows: 0")
            else:
                required = ["KVK_NO", "WeightT4X", "WeightT5Y", "WeightDeadsZ"]
                missing = [c for c in required if c not in df_weights.columns]
                if missing:
                    raise RuntimeError(f"KVK_DKPWeights missing columns: {missing}")

                _coerce_int(df_weights, ["KVK_NO"])
                _coerce_float(df_weights, ["WeightT4X", "WeightT5Y", "WeightDeadsZ"])

                # Keep only required cols in the right order and drop blank KVK_NO
                df_weights = df_weights[required]
                df_weights = df_weights.dropna(subset=["KVK_NO"])

                # Replace-all per KVK_NO (usually 1 row per KVK)
                kvks = sorted(set(int(v) for v in df_weights["KVK_NO"].tolist() if pd.notna(v)))
                for kvk_no in kvks:
                    cursor.execute("DELETE FROM KVK.KVK_DKPWeights WHERE KVK_NO = ?", kvk_no)

                # Insert without EffectiveFromUTC to use the table's DEFAULT (SYSUTCDATETIME)
                insert_sql = "INSERT INTO KVK.KVK_DKPWeights (KVK_NO, WeightT4X, WeightT5Y, WeightDeadsZ) VALUES (?,?,?,?)"
                fe = _enable_fast_executemany(cursor)
                cursor.executemany(insert_sql, _to_db_rows(df_weights))
                print(
                    f"[PERF] fast_executemany={'ON' if fe else 'off'} for KVK_DKPWeights ({len(df_weights)} rows)."
                )
                conn.commit()
                print(f"[OK] KVK_DKPWeights rows: {len(df_weights)}")
        except Exception as e:
            print(f"[WARN] KVK_DKPWeights import failed: {e}")

        # === NEW: KVK_Windows sheet ===
        try:
            print("[INFO] Importing KVK_Windows...")
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

            if df_win.empty:
                print("[WARN] KVK_Windows returned no rows; skipping.")
                print("[OK] KVK_Windows rows: 0")
            else:
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

                # Types
                _coerce_int(df_win, ["KVK_NO", "WindowSeq", "StartScanID", "EndScanID"])
                # Keep only required columns/order
                df_win = df_win[required]

                # Drop rows without a KVK_NO or WindowName
                df_win = df_win.dropna(subset=["KVK_NO", "WindowName"])

                # Replace-all per KVK present in this batch
                kvks = sorted(set(int(v) for v in df_win["KVK_NO"].tolist() if pd.notna(v)))
                for kvk_no in kvks:
                    cursor.execute("DELETE FROM KVK.KVK_Windows WHERE KVK_NO = ?", kvk_no)

                insert_sql = """
                    INSERT INTO KVK.KVK_Windows
                        (KVK_NO, WindowName, WindowSeq, StartScanID, EndScanID, Notes)
                    VALUES (?,?,?,?,?,?)
                """
                fe = _enable_fast_executemany(cursor)
                cursor.executemany(insert_sql, _to_db_rows(df_win))
                print(
                    f"[PERF] fast_executemany={'ON' if fe else 'off'} for KVK_Windows ({len(df_win)} rows)."
                )
                conn.commit()
                print(f"[OK] KVK_Windows rows: {len(df_win)}")

                # Soft validation: warn if Start/End reference non-existent scans
                # (EndScanID may be blank by design; StartScanID too early in KVK)
                for kvk_no in kvks:
                    # StartScanID not present in KVK_Scan
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM KVK.KVK_Windows w
                        WHERE w.KVK_NO = ? AND w.StartScanID IS NOT NULL
                          AND NOT EXISTS (
                              SELECT 1 FROM KVK.KVK_Scan s
                              WHERE s.KVK_NO = w.KVK_NO AND s.ScanID = w.StartScanID
                          )
                    """,
                        kvk_no,
                    )
                    bad_starts = cursor.fetchone()[0] or 0

                    # EndScanID not present in KVK_Scan (allowed; recompute uses Max if NULL)
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM KVK.KVK_Windows w
                        WHERE w.KVK_NO = ? AND w.EndScanID IS NOT NULL
                          AND NOT EXISTS (
                              SELECT 1 FROM KVK.KVK_Scan s
                              WHERE s.KVK_NO = w.KVK_NO AND s.ScanID = w.EndScanID
                          )
                    """,
                        kvk_no,
                    )
                    bad_ends = cursor.fetchone()[0] or 0

                    if bad_starts or bad_ends:
                        print(
                            f"[WARN] KVK_Windows scan refs for KVK {kvk_no}: "
                            f"{bad_starts} bad StartScanID, {bad_ends} bad EndScanID (ok if early in KVK)."
                        )
        except Exception as e:
            print(f"[WARN] KVK_Windows import failed: {e}")

        # === NEW: KVK_CampMap sheet ===
        try:
            print("[INFO] Importing KVK_CampMap...")
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

            if df_camp.empty:
                print("[WARN] KVK_CampMap returned no rows; skipping.")
                print("[OK] KVK_CampMap rows: 0")
            else:
                required = ["KVK_NO", "Kingdom", "CampID", "CampName"]
                missing = [c for c in required if c not in df_camp.columns]
                if missing:
                    raise RuntimeError(f"KVK_CampMap missing columns: {missing}")

                _coerce_int(df_camp, ["KVK_NO", "Kingdom", "CampID"])
                df_camp = df_camp[required]
                df_camp = df_camp.dropna(subset=["KVK_NO", "Kingdom", "CampID", "CampName"])

                kvks = sorted(set(int(v) for v in df_camp["KVK_NO"].tolist() if pd.notna(v)))
                for kvk_no in kvks:
                    cursor.execute("DELETE FROM KVK.KVK_CampMap WHERE KVK_NO = ?", kvk_no)

                insert_sql = """
                    INSERT INTO KVK.KVK_CampMap (KVK_NO, Kingdom, CampID, CampName)
                    VALUES (?,?,?,?)
                """
                fe = _enable_fast_executemany(cursor)
                cursor.executemany(insert_sql, _to_db_rows(df_camp))
                print(
                    f"[PERF] fast_executemany={'ON' if fe else 'off'} for KVK_CampMap ({len(df_camp)} rows)."
                )
                conn.commit()
                print(f"[OK] KVK_CampMap rows: {len(df_camp)}")
        except Exception as e:
            print(f"[WARN] KVK_CampMap import failed: {e}")

        # === Export Targets (unchanged) ===
        try:
            single_config_path = os.path.join(BASE_DIR, "config", "single_export_targets_only.json")
            print("[INFO] Exporting Targets sheet using single config...")
            run_single_export(
                SERVER, DATABASE, IMPORT_USERNAME, IMPORT_PASSWORD, config_path=single_config_path
            )
            print("[OK] Targets sheet exported.")
        except Exception as e:
            print(f"[WARN] Export Targets failed: {e}")

        return True

    except (pyodbc.OperationalError, HttpError) as e:
        print(f"[❌ ERROR] Transient failure (will have been retried as applicable): {e}")
        return False
    except Exception:
        print(f"[❌ ERROR] ProcConfig import critical failure:\n{traceback.format_exc()}")
        return False
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
