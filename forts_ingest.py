import datetime as dt
import hashlib
import os
import re

import pandas as pd
import pyodbc

from constants import DATABASE, IMPORT_PASSWORD, IMPORT_USERNAME, SERVER


def _get_conn():
    user = IMPORT_USERNAME
    pwd = IMPORT_PASSWORD
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};DATABASE={DATABASE};UID={user};PWD={pwd};"
        "Encrypt=Yes;TrustServerCertificate=Yes",
        autocommit=False,
    )


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _insert_log(cur, source, filename, filehash, as_of, rows, status, error=None):
    """Write a row to IngestionLog. Caller is responsible for committing."""
    cur.execute(
        """
        INSERT INTO dbo.IngestionLog
            (Source, FileName, FileHash, AsOfDate, RowsIn, EndedAt, Status, ErrorMessage)
        VALUES (?, ?, ?, ?, ?, SYSUTCDATETIME(), ?, ?)
        """,
        (source, filename, filehash, as_of, rows, status, error),
    )


def _normalise_cols(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {str(c).lower().strip(): c for c in df.columns}
    pid = mapping.get("participant_id") or mapping.get("governor_id")
    pname = mapping.get("participant_name") or mapping.get("governor_name")
    tr = mapping.get("total rallies")
    rl = mapping.get("rallies launched")
    rj = mapping.get("rallies joined")
    if not all([pid, pname, tr, rl, rj]):
        raise ValueError(f"Missing required columns; found: {list(df.columns)}")

    # Robust coercion
    gov_id = pd.to_numeric(df[pid], errors="coerce").fillna(0).astype("int64")
    gov_nm = df[pname].astype("string").fillna("").str.strip()
    total = pd.to_numeric(df[tr], errors="coerce").fillna(0).astype("int64")
    launched = pd.to_numeric(df[rl], errors="coerce").fillna(0).astype("int64")
    joined = pd.to_numeric(df[rj], errors="coerce").fillna(0).astype("int64")

    df2 = pd.DataFrame(
        {
            "GovernorID": gov_id,
            "GovernorName": gov_nm,
            "TotalRallies": total,
            "RalliesLaunched": launched,
            "RalliesJoined": joined,
        }
    )
    # drop rows with empty/zero GovID if any
    df2 = df2[df2["GovernorID"] != 0]
    return df2


def import_rally_daily_xlsx(path: str):
    m = re.search(r"Rally_data_(\d{2}-\d{2}-\d{4})\.xlsx$", os.path.basename(path), re.I)
    if not m:
        raise ValueError("Filename must be Rally_data_DD-MM-YYYY.xlsx for daily ingest.")
    as_of = dt.datetime.strptime(m.group(1), "%d-%m-%Y").date()

    try:
        df_raw = pd.read_excel(path, engine="openpyxl")
    except ModuleNotFoundError as e:
        raise RuntimeError("openpyxl is required to read .xlsx; install it in the bot venv") from e
    df = _normalise_cols(df_raw)
    if df.empty:
        return {"status": "skipped", "reason": "no rows", "as_of": str(as_of)}
    df.insert(0, "AsOfDate", as_of)

    filehash = sha256_file(path)
    src = "rally_daily"

    with _get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT 1 FROM dbo.IngestionLog WHERE Source=? AND FileName=?",
                (src, os.path.basename(path)),
            )
            if cur.fetchone():
                return {"status": "skipped", "reason": "duplicate filename", "as_of": str(as_of)}

            cur.execute("DELETE FROM dbo.stg_RallyDaily;")
            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.stg_RallyDaily
                    (AsOfDate, GovernorID, GovernorName, TotalRallies, RalliesLaunched, RalliesJoined)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                list(df.itertuples(index=False, name=None)),
            )

            cur.execute("EXEC dbo.sp_Import_Rally_Daily @AsOfDate=?", (as_of,))
            _insert_log(cur, src, os.path.basename(path), filehash, as_of, len(df), "success", None)

            conn.commit()
            return {"status": "success", "rows": len(df), "as_of": str(as_of)}
        except Exception as e:
            # roll back data changes
            try:
                conn.rollback()
            except Exception:
                pass
            # try to persist the error log
            try:
                _insert_log(
                    cur, src, os.path.basename(path), filehash, as_of, len(df), "error", str(e)
                )
                conn.commit()
            except Exception:
                pass
            raise


def import_rally_alltime_xlsx(path: str):
    try:
        df_raw = pd.read_excel(path, engine="openpyxl")
    except ModuleNotFoundError as e:
        raise RuntimeError("openpyxl is required to read .xlsx; install it in the bot venv") from e
    df = _normalise_cols(df_raw)
    if df.empty:
        return {"status": "skipped", "reason": "no rows"}

    filehash = sha256_file(path)
    src = "rally_alltime"

    with _get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT 1 FROM dbo.IngestionLog WHERE Source=? AND FileName=?",
                (src, os.path.basename(path)),
            )
            if cur.fetchone():
                return {"status": "skipped", "reason": "duplicate filename"}

            cur.execute("DELETE FROM dbo.stg_RallyAllTime;")
            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.stg_RallyAllTime
                    (GovernorID, GovernorName, TotalRallies, RalliesLaunched, RalliesJoined)
                VALUES (?, ?, ?, ?, ?)
            """,
                list(df.itertuples(index=False, name=None)),
            )

            cur.execute("EXEC dbo.sp_Import_Rally_AllTime;")
            _insert_log(cur, src, os.path.basename(path), filehash, None, len(df), "success", None)

            conn.commit()
            return {"status": "success", "rows": len(df)}
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                _insert_log(
                    cur, src, os.path.basename(path), filehash, None, len(df), "error", str(e)
                )
                conn.commit()
            except Exception:
                pass
            raise
