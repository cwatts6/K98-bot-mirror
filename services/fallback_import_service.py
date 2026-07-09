"""Service orchestration for fallback stats import file preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
import shutil

import pandas as pd

from services.fallback_import_schema import (
    INTERIM_AUTO_PARTIAL_SNAPSHOT,
    detect_fallback_source_type,
    normalize_fallback_dataframe,
    prepare_fallback_csv_dataframe,
)
from utils import utcnow

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FallbackImportPaths:
    download_folder: str
    source_file_2: str
    archive_dir_1: str
    archive_dir_2: str
    csv_file_path: str
    import_metadata_file_path: str


def robust_move(src: str, dst: str) -> None:
    try:
        shutil.move(src, dst)
    except Exception:
        shutil.copy2(src, dst)
        try:
            os.remove(src)
        except Exception:
            pass


def read_source_dataframe(source_filepath: str) -> pd.DataFrame:
    ext = os.path.splitext(source_filepath)[1].lower()
    if ext == ".csv":
        return pd.read_csv(source_filepath, encoding="utf-8-sig")

    with pd.ExcelFile(source_filepath, engine="openpyxl") as xf:
        sheet_name = "Data" if "Data" in xf.sheet_names else xf.sheet_names[-1]
        return pd.read_excel(xf, sheet_name=sheet_name, engine="openpyxl")


def write_import_metadata(metadata: dict, metadata_path: str) -> None:
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)


def load_import_metadata(metadata_path: str) -> dict:
    try:
        with open(metadata_path, encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        logger.debug("[EXCEL] Failed to read import metadata sidecar", exc_info=True)
        return {}


def delete_import_metadata(metadata_path: str) -> None:
    try:
        os.remove(metadata_path)
    except FileNotFoundError:
        return
    except Exception:
        logger.debug("[EXCEL] Failed to remove consumed import metadata sidecar", exc_info=True)


def process_fallback_source_file(
    source_filepath: str,
    *,
    paths: FallbackImportPaths,
    fetch_latest_snapshot: Callable[[], pd.DataFrame],
    read_dataframe: Callable[[str], pd.DataFrame] = read_source_dataframe,
    move_file: Callable[[str, str], None] = robust_move,
    now_fn: Callable[[], datetime] = utcnow,
) -> tuple[bool, str, None]:
    """Normalize an uploaded fallback file and prepare the SQL bulk CSV."""
    if not os.path.isfile(source_filepath):
        logger.error("[EXCEL] Source file does not exist: %s", source_filepath)
        return False, f"[ERROR] Source file not found: {source_filepath}", None

    try:
        logger.info("[EXCEL] Processing %s", source_filepath)
        source_df = read_dataframe(source_filepath)
        source_type = detect_fallback_source_type(source_df)
        latest_rows = (
            fetch_latest_snapshot() if source_type == INTERIM_AUTO_PARTIAL_SNAPSHOT else None
        )
        normalized = normalize_fallback_dataframe(
            source_df,
            source_filename=os.path.basename(source_filepath),
            latest_rows=latest_rows,
        )
        df = normalized.dataframe
        metadata = normalized.metadata.as_json_dict()
        write_import_metadata(metadata, paths.import_metadata_file_path)

        credit_non_null = int(pd.to_numeric(df["Credit"], errors="coerce").notna().sum())
        logger.info(
            "[EXCEL] Fallback import source_type=%s score_header=%s rows_in_source=%d rows_written=%d credit_non_null=%d",
            normalized.metadata.source_type,
            normalized.metadata.score_header,
            normalized.metadata.rows_in_source,
            normalized.metadata.rows_written,
            credit_non_null,
        )

        output_path = os.path.join(paths.download_folder, "stats.xlsx")
        df.to_excel(output_path, index=False, engine="openpyxl")
        if not os.path.isfile(output_path):
            logger.error("[EXCEL] to_excel reported no error but file missing: %s", output_path)
            return False, f"[ERROR] Failed to write Excel to {output_path}", None
        logger.info("[EXCEL] Wrote Excel -> %s", output_path)

        os.makedirs(paths.archive_dir_1, exist_ok=True)
        base_name, ext = os.path.splitext(os.path.basename(source_filepath))
        timestamp_str = now_fn().strftime("%Y-%m-%d_%H%M")
        archive_path = os.path.join(paths.archive_dir_1, f"{base_name}_{timestamp_str}{ext}")
        move_file(source_filepath, archive_path)
        logger.info("[EXCEL] Archived original -> %s", archive_path)

        csv_df = prepare_fallback_csv_dataframe(df)
        csv_df.to_csv(paths.csv_file_path, index=False, encoding="utf-8-sig")
        if not os.path.isfile(paths.csv_file_path):
            logger.error("[EXCEL] Failed to write CSV to %s", paths.csv_file_path)
            return False, f"[ERROR] Failed to write CSV to {paths.csv_file_path}", None
        logger.info("[EXCEL] Wrote CSV -> %s", paths.csv_file_path)

        return True, "[INFO] Excel processed successfully.", None

    except Exception as e:
        logger.exception("[EXCEL] Excel processing failed for %s: %s", source_filepath, e)
        return False, f"[ERROR] Excel processing failed: {e}", None


def archive_secondary_file(
    *,
    paths: FallbackImportPaths,
    move_file: Callable[[str, str], None] = robust_move,
    now_fn: Callable[[], datetime] = utcnow,
) -> tuple[bool, str, None]:
    if not os.path.isfile(paths.source_file_2):
        return False, f"[ERROR] Second source file not found: {paths.source_file_2}", None

    try:
        os.makedirs(paths.archive_dir_2, exist_ok=True)
        base_name, ext = os.path.splitext(os.path.basename(paths.source_file_2))
        timestamp_str = now_fn().strftime("%Y-%m-%d_%H%M")
        archive_path = os.path.join(paths.archive_dir_2, f"{base_name}_{timestamp_str}{ext}")
        move_file(paths.source_file_2, archive_path)
        return True, "[INFO] Second file archived.", None
    except Exception as e:
        logger.exception("Archiving second file failed: %s", e)
        return False, f"[ERROR] Archiving second file failed: {e}", None
