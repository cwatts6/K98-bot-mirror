# prekvk_importer.py
import hashlib
import io
import logging

import pandas as pd
import pyodbc

logger = logging.getLogger(__name__)


def _conn(server, db, user, pwd):
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={db};UID={user};PWD={pwd}",
        autocommit=False,
    )


def import_prekvk_bytes(
    xlsx_bytes: bytes, filename: str, *, kvk_no: int, server: str, db: str, user: str, pwd: str
) -> tuple[bool, str, int]:
    try:
        # --- Read Excel robustly (accept "prekvk" sheet or fallback to first sheet)
        try:
            df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="prekvk")
        except Exception:
            sheets = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=None)
            if not sheets:
                return (False, "No sheets found in workbook.", 0)
            # Prefer sheet named like 'prekvk' (case/space tolerant), else first
            pick = next(
                (name for name in sheets.keys() if str(name).strip().lower() == "prekvk"), None
            )
            df = sheets[pick] if pick else next(iter(sheets.values()))

        # --- Normalize columns
        cols_lc = {str(c).strip().lower(): c for c in df.columns}
        gid_col = cols_lc.get("governorid") or cols_lc.get("governor_id") or "GovernorID"
        name_col = cols_lc.get("name") or "Name"
        pts_col = None
        for c in df.columns:
            if str(c).strip().lower().startswith("prekvk"):
                pts_col = c
                break
        pts_col = pts_col or "Prekvk Points"

        out = df[[gid_col, name_col, pts_col]].copy()

        # --- Coerce types safely
        out.columns = ["GovernorID", "GovernorName", "Points"]
        out["GovernorID"] = pd.to_numeric(out["GovernorID"], errors="coerce").astype("Int64")
        out["GovernorName"] = out["GovernorName"].astype(str).str.strip()
        out["Points"] = pd.to_numeric(out["Points"], errors="coerce").fillna(0).astype(int)

        # Drop rows with missing GovernorID
        out = out.dropna(subset=["GovernorID"])
        if out.empty:
            return (False, "No valid governor rows after cleaning.", 0)

        # Cast GovernorID to plain int for DB insert
        out["GovernorID"] = out["GovernorID"].astype("int64")

        # --- Idempotency hash
        filehash = hashlib.sha256(xlsx_bytes).digest()

        with _conn(server, db, user, pwd) as conn:
            cur = conn.cursor()

            # Skip if exact hash already seen for this KVK
            cur.execute(
                "SELECT 1 FROM dbo.PreKvk_Scan WHERE KVK_NO=? AND FileHash=?", (kvk_no, filehash)
            )
            if cur.fetchone():
                return (True, "Duplicate file skipped (hash match).", 0)

            # Header insert (returns ScanID)
            cur.execute(
                """
                INSERT INTO dbo.PreKvk_Scan (KVK_NO, ScanTimestampUTC, SourceFileName, FileHash, row_count)
                OUTPUT INSERTED.ScanID
                VALUES (?, SYSUTCDATETIME(), ?, ?, ?)
            """,
                (kvk_no, filename, filehash, len(out)),
            )
            scan_id = int(cur.fetchone()[0])

            # Bulk rows
            rows = [
                (kvk_no, scan_id, int(r.GovernorID), str(r.GovernorName)[:64], int(r.Points))
                for r in out.itertuples(index=False)
            ]
            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.PreKvk_Scores (KVK_NO, ScanID, GovernorID, GovernorName, Points)
                VALUES (?,?,?,?,?)
            """,
                rows,
            )

            conn.commit()

        return (True, f"Imported {len(out)} rows as scan {scan_id}.", len(out))

    except pyodbc.IntegrityError as e:
        # Race-safe duplicate protection (in case another process inserted same hash)
        if "UQ_PreKvk_Scan" in str(e) or "unique" in str(e).lower():
            return (True, "Duplicate file skipped (unique constraint).", 0)
        return (False, f"IntegrityError: {e}", 0)
    except Exception as e:
        logger.exception("[PREKVK] Import failed")
        return (False, f"{type(e).__name__}: {e}", 0)
