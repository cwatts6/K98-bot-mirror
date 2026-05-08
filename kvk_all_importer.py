# kvk_all_importer.py
from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any

from constants import (
    CREDENTIALS_FILE,
    DATABASE,
    KVK_SHEET_NAME,
    PASSWORD,
    SERVER,
    USERNAME,
)
from gsheet_module import run_kvk_proc_exports_with_alerts
from kvk.dal import kvk_all_import_dal
from kvk.schemas.kvk_all_schema import SCHEMA_VERSION, KvkAllSchemaValidationError
from kvk.services import kvk_all_import_service
from kvk.services.kvk_all_import_service import (
    KvkAllImportPreparationError,
    prepare_kvk_all_import,
)

logger = logging.getLogger(__name__)

# Compatibility exports for older tests/tools that imported importer internals.
STAGE_COL_ORDER = kvk_all_import_dal.STAGE_COL_ORDER
STAGE_INSERT_COLUMNS = kvk_all_import_dal.STAGE_INSERT_COLUMNS
STAGE_INSERT_SQL = kvk_all_import_dal.STAGE_INSERT_SQL
STAGE_PHASE2_REQUIRED_COLUMNS = kvk_all_import_dal.STAGE_PHASE2_REQUIRED_COLUMNS
CALL_INGEST_SQL = kvk_all_import_dal.CALL_INGEST_SQL
RECOMPUTE_SQL = kvk_all_import_dal.RECOMPUTE_SQL
NEGATIVE_COUNT_SQL = kvk_all_import_dal.NEGATIVE_COUNT_SQL
_read_excel = kvk_all_import_service.read_full_data_workbook
_coerce = kvk_all_import_service.coerce_full_data_frame
_with_source_metadata = kvk_all_import_service.attach_source_metadata
_rows_for_stage = kvk_all_import_dal.rows_for_stage


def ingest_kvk_all_excel(
    *,
    content: bytes,
    source_filename: str,
    uploader_id: int,
    scan_ts_utc: dt.datetime,
    server: str,
    database: str,
    username: str,
    password: str,
) -> dict[str, Any]:
    """
    Compatibility wrapper for the KVK_ALL Full Data import pipeline.

    Expected validation failures return structured dictionaries. Unexpected database
    or runtime failures still propagate so callers can log tracebacks.
    """
    started = time.perf_counter()
    try:
        prepared = prepare_kvk_all_import(content, source_filename)
    except KvkAllSchemaValidationError as exc:
        logger.info("[KVK] Import schema validation failed for %s: %s", source_filename, exc)
        return {
            "success": False,
            "error": str(exc),
            "sheet": exc.sheet_name,
            "schema_version": exc.schema_version,
            "validation_error": exc.to_dict(),
        }
    except KvkAllImportPreparationError as exc:
        logger.info("[KVK] Import failed for %s: %s", source_filename, exc)
        return {
            "success": False,
            "error": str(exc),
            "sheet": exc.sheet_name,
            "schema_version": SCHEMA_VERSION,
            "schema": exc.schema_metadata,
        }
    except ValueError as exc:
        logger.info("[KVK] Import failed for %s: %s", source_filename, exc)
        return {
            "success": False,
            "error": str(exc),
            "sheet": "Full Data",
            "schema_version": SCHEMA_VERSION,
        }

    if prepared.dataframe.empty:
        logger.info("[KVK] Import failed for %s: No rows found in uploaded file.", source_filename)
        return {
            "success": False,
            "error": "No rows found in uploaded file.",
            "sheet": prepared.sheet_name,
            "schema_version": SCHEMA_VERSION,
            "schema": prepared.schema_metadata,
        }

    con = kvk_all_import_dal.connect_sql_server(
        server=server,
        database=database,
        username=username,
        password=password,
    )
    try:
        result = kvk_all_import_dal.ingest_prepared_import(
            con=con,
            prepared=prepared,
            content=content,
            source_filename=source_filename,
            uploader_id=uploader_id,
            scan_ts_utc=scan_ts_utc,
        )
    finally:
        try:
            con.close()
        except Exception:
            pass

    result.setdefault("duration_s", round(time.perf_counter() - started, 2))
    return result


async def _auto_export_kvk(kvk_no: int, notify_channel, bot_loop):
    try:
        from file_utils import run_blocking_in_thread

        ok = await run_blocking_in_thread(
            run_kvk_proc_exports_with_alerts,
            SERVER,
            DATABASE,
            USERNAME,
            PASSWORD,
            kvk_no,
            KVK_SHEET_NAME,
            CREDENTIALS_FILE,
            notify_channel,
            bot_loop,
            name="run_kvk_proc_exports_with_alerts",
            meta={"kvk_no": kvk_no},
        )
        if ok and notify_channel:
            await notify_channel.send(
                f"\U0001f4e4 Export complete: **KVK {kvk_no} \u2192 {KVK_SHEET_NAME}**"
            )
    except Exception as exc:
        logger.exception("[KVK_EXPORT] Auto-export crashed")
        if notify_channel:
            await notify_channel.send(
                f"\u26a0\ufe0f Export failed for **KVK {kvk_no}**: "
                f"`{type(exc).__name__}: {exc}`"
            )
