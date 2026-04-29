# prekvk_importer.py
import hashlib
import io
import logging
import os

import pandas as pd
import pyodbc

from file_utils import fetch_one_dict
from sheet_importer import executemany_batched  # NEW: shared batching helper

logger = logging.getLogger(__name__)


def _conn():
    """
    Prefer central connection-with-retries helper (env/config driven).
    Falls back to constants._conn if retry helper is unavailable.
    """
    try:
        from file_utils import get_conn_with_retries

        return get_conn_with_retries()
    except Exception:
        from constants import _conn as _conn_env

        return _conn_env()


def _emit_telemetry(payload: dict) -> None:
    try:
        from file_utils import emit_telemetry_event

        emit_telemetry_event(payload)
    except Exception:
        return


def import_prekvk_bytes(
    xlsx_bytes: bytes,
    filename: str,
    *,
    kvk_no: int,
) -> tuple[bool, str, int]:
    phase = "start"
    scan_id: int | None = None
    rows_imported = 0

    try:
        filehash = hashlib.sha256(xlsx_bytes).digest()
        hash_prefix = hashlib.sha256(xlsx_bytes).hexdigest()[:8]
    except Exception:
        filehash = b""
        hash_prefix = "unknown"

    bytes_len = len(xlsx_bytes) if xlsx_bytes is not None else 0

    logger.info("[PREKVK] import start kvk_no=%s file=%s bytes=%s", kvk_no, filename, bytes_len)
    _emit_telemetry(
        {
            "event": "prekvk_import_start",
            "kvk_no": kvk_no,
            "filename": filename,
            "bytes_len": bytes_len,
            "hash_prefix": hash_prefix,
        }
    )

    try:
        phase = "read_excel"
        try:
            df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="prekvk")
        except Exception:
            sheets = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=None)
            if not sheets:
                logger.warning(
                    "[PREKVK] import failed phase=%s kvk_no=%s file=%s: no sheets found",
                    phase,
                    kvk_no,
                    filename,
                )
                _emit_telemetry(
                    {
                        "event": "prekvk_import_failed",
                        "phase": phase,
                        "kvk_no": kvk_no,
                        "filename": filename,
                        "bytes_len": bytes_len,
                        "hash_prefix": hash_prefix,
                        "error_type": "NoSheets",
                        "error_text": "No sheets found in workbook",
                    }
                )
                return (False, "No sheets found in workbook.", 0)

            pick = next(
                (name for name in sheets.keys() if str(name).strip().lower() == "prekvk"), None
            )
            df = sheets[pick] if pick else next(iter(sheets.values()))

        phase = "normalize"
        cols_lc = {str(c).strip().lower(): c for c in df.columns}
        gid_col = cols_lc.get("governorid") or cols_lc.get("governor_id") or "GovernorID"
        name_col = cols_lc.get("name") or "Name"
        pts_col = None
        for c in df.columns:
            if str(c).strip().lower().startswith("prekvk"):
                pts_col = c
                break
        pts_col = pts_col or "Prekvk Points"

        required_cols = [gid_col, name_col, pts_col]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            found = ", ".join(str(c) for c in list(df.columns))
            miss = ", ".join(str(c) for c in missing)
            msg = f"Missing required column(s): {miss}. Found columns: {found}"

            logger.warning(
                "[PREKVK] import failed phase=%s kvk_no=%s file=%s: %s",
                phase,
                kvk_no,
                filename,
                msg,
            )
            _emit_telemetry(
                {
                    "event": "prekvk_import_failed",
                    "phase": phase,
                    "kvk_no": kvk_no,
                    "filename": filename,
                    "bytes_len": bytes_len,
                    "hash_prefix": hash_prefix,
                    "error_type": "MissingColumns",
                    "error_text": msg,
                }
            )
            return (False, msg, 0)

        out = df[required_cols].copy()
        out.columns = ["GovernorID", "GovernorName", "Points"]

        out["GovernorID"] = pd.to_numeric(out["GovernorID"], errors="coerce").astype("Int64")

        try:
            out["GovernorName"] = out["GovernorName"].where(out["GovernorName"].notna(), "")
        except Exception:
            out["GovernorName"] = ""
        out["GovernorName"] = out["GovernorName"].astype(str).str.strip()
        out["GovernorName"] = out["GovernorName"].replace(
            {"nan": "", "NaN": "", "None": "", "none": ""}
        )

        out["Points"] = pd.to_numeric(out["Points"], errors="coerce").fillna(0).astype(int)

        out = out.dropna(subset=["GovernorID"])
        if out.empty:
            logger.warning(
                "[PREKVK] import failed phase=%s kvk_no=%s file=%s: no valid rows after cleaning",
                phase,
                kvk_no,
                filename,
            )
            _emit_telemetry(
                {
                    "event": "prekvk_import_failed",
                    "phase": phase,
                    "kvk_no": kvk_no,
                    "filename": filename,
                    "bytes_len": bytes_len,
                    "hash_prefix": hash_prefix,
                    "error_type": "NoValidRows",
                    "error_text": "No valid governor rows after cleaning",
                }
            )
            return (False, "No valid governor rows after cleaning.", 0)

        out["GovernorID"] = out["GovernorID"].astype("int64")

        dup_mask = out["GovernorID"].duplicated(keep=False)
        if bool(dup_mask.any()):
            dup_ids = out.loc[dup_mask, "GovernorID"].astype("int64").tolist()
            # Unique + stable order for message (sorted)
            uniq = sorted(set(int(x) for x in dup_ids))
            sample = ", ".join(str(x) for x in uniq[:20])
            more = f" (+{len(uniq) - 20} more)" if len(uniq) > 20 else ""
            msg = (
                f"Duplicate GovernorID(s) detected in file: {sample}{more}. "
                "Please remove duplicates and re-upload."
            )

            logger.warning(
                "[PREKVK] import failed phase=%s kvk_no=%s file=%s: %s",
                phase,
                kvk_no,
                filename,
                msg,
            )
            _emit_telemetry(
                {
                    "event": "prekvk_import_failed",
                    "phase": "validate_duplicates",
                    "kvk_no": kvk_no,
                    "filename": filename,
                    "bytes_len": bytes_len,
                    "hash_prefix": hash_prefix,
                    "error_type": "DuplicateGovernorIDs",
                    "error_text": msg,
                    "duplicate_count": len(uniq),
                }
            )
            return (False, msg, 0)

        phase = "db"
        with _conn() as conn:
            cur = conn.cursor()
            try:
                phase = "db_dedupe_check"
                cur.execute(
                    "SELECT 1 FROM dbo.PreKvk_Scan WHERE KVK_NO=? AND FileHash=?",
                    (kvk_no, filehash),
                )
                if fetch_one_dict(cur):
                    logger.info(
                        "[PREKVK] import skipped duplicate kvk_no=%s file=%s hash=%s",
                        kvk_no,
                        filename,
                        hash_prefix,
                    )
                    _emit_telemetry(
                        {
                            "event": "prekvk_import_skip_duplicate",
                            "phase": phase,
                            "kvk_no": kvk_no,
                            "filename": filename,
                            "bytes_len": bytes_len,
                            "hash_prefix": hash_prefix,
                            "rows": 0,
                        }
                    )
                    return (True, "Duplicate file skipped (hash match).", 0)

                phase = "db_insert_header"
                cur.execute(
                    """
                    INSERT INTO dbo.PreKvk_Scan (KVK_NO, ScanTimestampUTC, SourceFileName, FileHash, row_count)
                    OUTPUT INSERTED.ScanID
                    VALUES (?, SYSUTCDATETIME(), ?, ?, ?)
                """,
                    (kvk_no, filename, filehash, len(out)),
                )
                scan_row = fetch_one_dict(cur)
                if not scan_row:
                    raise RuntimeError("Failed to obtain ScanID after inserting PreKvk_Scan")
                scan_id = int(scan_row.get("ScanID", next(iter(scan_row.values()))))

                phase = "db_insert_rows"
                rows = [
                    (kvk_no, scan_id, int(r.GovernorID), str(r.GovernorName)[:64], int(r.Points))
                    for r in out.itertuples(index=False)
                ]

                # Keep fast_executemany ON (works with executemany_batched)
                cur.fast_executemany = True

                batch_size = 5000
                try:
                    batch_size = int(os.getenv("PREKVK_IMPORT_BATCH_SIZE", "5000"))
                except Exception:
                    batch_size = 5000
                if batch_size <= 0:
                    batch_size = 5000

                inserted = executemany_batched(
                    cur,
                    conn,
                    """
                    INSERT INTO dbo.PreKvk_Scores (KVK_NO, ScanID, GovernorID, GovernorName, Points)
                    VALUES (?,?,?,?,?)
                    """,
                    rows,
                    batch_size=batch_size,
                    commit_per_batch=False,
                )

                # Keep semantics: one commit for whole scan
                conn.commit()

                rows_imported = int(inserted)
                logger.info(
                    "[PREKVK] import success kvk_no=%s file=%s scan_id=%s rows=%s hash=%s",
                    kvk_no,
                    filename,
                    scan_id,
                    rows_imported,
                    hash_prefix,
                )
                _emit_telemetry(
                    {
                        "event": "prekvk_import_success",
                        "phase": phase,
                        "kvk_no": kvk_no,
                        "filename": filename,
                        "bytes_len": bytes_len,
                        "hash_prefix": hash_prefix,
                        "scan_id": scan_id,
                        "rows": rows_imported,
                    }
                )

            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise

        return (True, f"Imported {rows_imported} rows as scan {scan_id}.", rows_imported)

    except pyodbc.IntegrityError as e:
        if "UQ_PreKvk_Scan" in str(e) or "unique" in str(e).lower():
            logger.info(
                "[PREKVK] import skipped duplicate (unique) kvk_no=%s file=%s hash=%s",
                kvk_no,
                filename,
                hash_prefix,
            )
            _emit_telemetry(
                {
                    "event": "prekvk_import_skip_duplicate",
                    "phase": phase,
                    "kvk_no": kvk_no,
                    "filename": filename,
                    "bytes_len": bytes_len,
                    "hash_prefix": hash_prefix,
                    "rows": 0,
                    "dedupe": "unique_constraint",
                }
            )
            return (True, "Duplicate file skipped (unique constraint).", 0)

        logger.warning(
            "[PREKVK] import failed phase=%s kvk_no=%s file=%s integrity_error=%s",
            phase,
            kvk_no,
            filename,
            str(e),
        )
        _emit_telemetry(
            {
                "event": "prekvk_import_failed",
                "phase": phase,
                "kvk_no": kvk_no,
                "filename": filename,
                "bytes_len": bytes_len,
                "hash_prefix": hash_prefix,
                "error_type": "IntegrityError",
                "error_text": str(e),
            }
        )
        return (False, f"IntegrityError: {e}", 0)

    except Exception as e:
        logger.exception(
            "[PREKVK] import failed phase=%s kvk_no=%s file=%s", phase, kvk_no, filename
        )
        _emit_telemetry(
            {
                "event": "prekvk_import_failed",
                "phase": phase,
                "kvk_no": kvk_no,
                "filename": filename,
                "bytes_len": bytes_len,
                "hash_prefix": hash_prefix,
                "error_type": type(e).__name__,
                "error_text": str(e),
            }
        )
        return (False, f"{type(e).__name__}: {e}", 0)
