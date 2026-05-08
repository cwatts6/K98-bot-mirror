# prekvk_importer.py
import hashlib
import io
import logging
import os
import re

import pandas as pd
import pyodbc

from file_utils import fetch_one_dict
from sheet_importer import executemany_batched  # NEW: shared batching helper

logger = logging.getLogger(__name__)


NEW_PREKVK_SHEET_NAME = "pre-kvk rankings"
INVALID_WORKBOOK_MESSAGE = (
    "Unable to read workbook. The file may be corrupted or not a valid Excel workbook."
)


class NoSheetsError(ValueError):
    """Raised when a readable workbook returns no sheets at all."""

    pass


class InvalidWorkbookError(Exception):
    """Raised when the uploaded file cannot be parsed as a valid workbook."""

    pass


def _normalize_column_name(value) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _columns_by_normalized_name(df: pd.DataFrame) -> dict[str, object]:
    return {_normalize_column_name(c): c for c in df.columns}


def _coerce_required_int_series(series: pd.Series, column_name: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    bad_mask = series.notna() & values.isna()
    if bool(bad_mask.any()):
        sample = ", ".join(str(x) for x in series.loc[bad_mask].head(5).tolist())
        raise ValueError(f"Non-numeric value(s) in {column_name}: {sample}")
    return values.fillna(0).astype(int)


def _clean_governor_names(series: pd.Series) -> pd.Series:
    try:
        cleaned = series.where(series.notna(), "")
    except Exception:
        cleaned = pd.Series([""] * len(series), index=series.index)
    cleaned = pd.Series(cleaned, index=series.index).astype(str).str.strip()
    return cleaned.replace({"nan": "", "NaN": "", "None": "", "none": ""})


def _read_prekvk_workbook(xlsx_bytes: bytes) -> pd.DataFrame:
    try:
        return pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name="prekvk")
    except Exception:
        try:
            sheets = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=None)
        except Exception as exc:
            raise InvalidWorkbookError(INVALID_WORKBOOK_MESSAGE) from exc
        if not sheets:
            raise NoSheetsError("No sheets found in workbook")

        pick = next(
            (
                name
                for name in sheets.keys()
                if str(name).strip().lower() in {"prekvk", NEW_PREKVK_SHEET_NAME}
            ),
            None,
        )
        return sheets[pick] if pick else next(iter(sheets.values()))


def _normalize_prekvk_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cols = _columns_by_normalized_name(df)

    new_schema = {
        "rank": "SourceRank",
        "name": "GovernorName",
        "governorid": "GovernorID",
        "kd": "KingdomID",
        "stageipoints": "Stage1Points",
        "stageiipoints": "Stage2Points",
        "stageiiipoints": "Stage3Points",
        "totalpoints": "TotalPoints",
    }

    if all(key in cols for key in new_schema):
        out = pd.DataFrame()
        for source_key, canonical_name in new_schema.items():
            out[canonical_name] = df[cols[source_key]]

        out["GovernorID"] = pd.to_numeric(out["GovernorID"], errors="coerce").astype("Int64")
        out["GovernorName"] = _clean_governor_names(out["GovernorName"])

        for col in (
            "KingdomID",
            "SourceRank",
            "Stage1Points",
            "Stage2Points",
            "Stage3Points",
            "TotalPoints",
        ):
            out[col] = _coerce_required_int_series(out[col], col)

        out["Points"] = out["TotalPoints"]
        return out[
            [
                "GovernorID",
                "GovernorName",
                "KingdomID",
                "SourceRank",
                "Stage1Points",
                "Stage2Points",
                "Stage3Points",
                "TotalPoints",
                "Points",
            ]
        ]

    gid_col = cols.get("governorid") or cols.get("governor_id") or "GovernorID"
    name_col = cols.get("name") or "Name"
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
        raise KeyError(f"Missing required column(s): {miss}. Found columns: {found}")

    out = df[required_cols].copy()
    out.columns = ["GovernorID", "GovernorName", "Points"]
    out["GovernorID"] = pd.to_numeric(out["GovernorID"], errors="coerce").astype("Int64")
    out["GovernorName"] = _clean_governor_names(out["GovernorName"])
    out["Points"] = pd.to_numeric(out["Points"], errors="coerce").fillna(0).astype(int)
    out["KingdomID"] = None
    out["SourceRank"] = None
    out["Stage1Points"] = None
    out["Stage2Points"] = None
    out["Stage3Points"] = None
    out["TotalPoints"] = out["Points"]
    return out[
        [
            "GovernorID",
            "GovernorName",
            "KingdomID",
            "SourceRank",
            "Stage1Points",
            "Stage2Points",
            "Stage3Points",
            "TotalPoints",
            "Points",
        ]
    ]


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
    uploader_discord_id: int | None = None,
    channel_id: int | None = None,
    message_id: int | None = None,
) -> tuple[bool, str, int]:
    phase = "start"
    scan_id: int | None = None
    rows_imported = 0

    try:
        filehash = hashlib.sha256(xlsx_bytes).digest()
        filehash_hex = hashlib.sha256(xlsx_bytes).hexdigest()
        hash_prefix = filehash_hex[:8]
    except Exception:
        filehash = b""
        filehash_hex = None
        hash_prefix = "unknown"

    bytes_len = len(xlsx_bytes) if xlsx_bytes is not None else 0

    def _record_history(
        status: str,
        *,
        phase_name: str | None = None,
        row_count: int | None = None,
        error_type: str | None = None,
        error_text: str | None = None,
    ) -> None:
        if os.getenv("PREKVK_IMPORT_HISTORY_DISABLED", "").strip() == "1":
            return
        try:
            from prekvk.diagnostics_service import record_import_outcome

            record_import_outcome(
                kvk_no=kvk_no,
                filename=filename,
                status=status,
                hash_prefix=hash_prefix,
                file_hash_sha256=filehash_hex,
                phase=phase_name or phase,
                row_count=row_count,
                scan_id=scan_id,
                error_type=error_type,
                error_text=error_text,
                uploader_discord_id=uploader_discord_id,
                channel_id=channel_id,
                message_id=message_id,
            )
        except Exception:
            logger.exception("[PREKVK] import history hook failed")

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
            df = _read_prekvk_workbook(xlsx_bytes)
        except NoSheetsError as e:
            logger.warning(
                "[PREKVK] import failed phase=%s kvk_no=%s file=%s: %s",
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
                    "error_type": "NoSheets",
                    "error_text": str(e),
                }
            )
            _record_history(
                "rejected",
                phase_name=phase,
                row_count=0,
                error_type="NoSheets",
                error_text=str(e),
            )
            return (False, f"{e}.", 0)
        except InvalidWorkbookError as e:
            logger.warning(
                "[PREKVK] import failed phase=%s kvk_no=%s file=%s: %s",
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
                    "error_type": "InvalidWorkbook",
                    "error_text": str(e),
                }
            )
            _record_history(
                "rejected",
                phase_name=phase,
                row_count=0,
                error_type="InvalidWorkbook",
                error_text=str(e),
            )
            return (False, str(e), 0)

        phase = "normalize"
        try:
            out = _normalize_prekvk_dataframe(df)
        except KeyError as e:
            msg = str(e).strip("'")

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
            _record_history(
                "rejected",
                phase_name=phase,
                row_count=0,
                error_type="MissingColumns",
                error_text=msg,
            )
            return (False, msg, 0)
        except ValueError as e:
            msg = str(e)
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
                    "error_type": "InvalidNumericValue",
                    "error_text": msg,
                }
            )
            _record_history(
                "rejected",
                phase_name=phase,
                row_count=0,
                error_type="InvalidNumericValue",
                error_text=msg,
            )
            return (False, msg, 0)

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
            _record_history(
                "rejected",
                phase_name=phase,
                row_count=0,
                error_type="NoValidRows",
                error_text="No valid governor rows after cleaning",
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
            _record_history(
                "rejected",
                phase_name="validate_duplicates",
                row_count=0,
                error_type="DuplicateGovernorIDs",
                error_text=msg,
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
                    _record_history("duplicate", phase_name=phase, row_count=0)
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
                    (
                        kvk_no,
                        scan_id,
                        int(r.GovernorID),
                        str(r.GovernorName)[:64],
                        int(r.Points),
                        None if pd.isna(r.KingdomID) else int(r.KingdomID),
                        None if pd.isna(r.SourceRank) else int(r.SourceRank),
                        None if pd.isna(r.Stage1Points) else int(r.Stage1Points),
                        None if pd.isna(r.Stage2Points) else int(r.Stage2Points),
                        None if pd.isna(r.Stage3Points) else int(r.Stage3Points),
                        None if pd.isna(r.TotalPoints) else int(r.TotalPoints),
                    )
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
                    INSERT INTO dbo.PreKvk_Scores (
                        KVK_NO,
                        ScanID,
                        GovernorID,
                        GovernorName,
                        Points,
                        KingdomID,
                        SourceRank,
                        Stage1Points,
                        Stage2Points,
                        Stage3Points,
                        TotalPoints
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
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
                _record_history("accepted", phase_name=phase, row_count=rows_imported)

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
            _record_history("duplicate", phase_name=phase, row_count=0)
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
        _record_history(
            "failed",
            phase_name=phase,
            row_count=0,
            error_type="IntegrityError",
            error_text=str(e),
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
        _record_history(
            "failed",
            phase_name=phase,
            row_count=0,
            error_type=type(e).__name__,
            error_text=str(e),
        )
        return (False, f"{type(e).__name__}: {e}", 0)
