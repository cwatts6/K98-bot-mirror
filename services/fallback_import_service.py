"""Service orchestration for fallback stats import file preparation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import re
import secrets
import shutil

import pandas as pd

from file_utils import atomic_write_json
from services.fallback_import_schema import (
    INTERIM_AUTO_PARTIAL_SNAPSHOT,
    detect_fallback_source_type,
    normalize_fallback_dataframe,
    prepare_fallback_csv_dataframe,
)
from utils import utcnow

logger = logging.getLogger(__name__)

COMPLETED_FILE_PATTERN = re.compile(r"^stats_[0-9a-f]{32}\.ready\.csv$")
PUBLICATION_MANIFEST_VERSION = 1
_RECOVERABLE_PUBLICATION_STATES = frozenset({"prepared", "published", "sql_owned"})


@dataclass(frozen=True, slots=True)
class FallbackImportPaths:
    download_folder: str
    source_file_2: str
    archive_dir_1: str
    archive_dir_2: str
    ready_dir: str
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
    atomic_write_json(metadata_path, metadata, ensure_parent_dir=True)


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


def is_completed_filename(value: object) -> bool:
    return isinstance(value, str) and COMPLETED_FILE_PATTERN.fullmatch(value) is not None


def set_import_metadata_state(metadata_path: str, metadata: dict, state: str) -> None:
    metadata["publication_state"] = state
    metadata["publication_state_updated_at_utc"] = utcnow().isoformat()
    write_import_metadata(metadata, metadata_path)


def resolve_published_completed_filename(
    *,
    metadata_path: str,
    ready_dir: str,
    metadata: dict | None = None,
) -> str:
    """Resolve one durable immutable identity, failing closed on ambiguous state."""
    manifest = metadata if isinstance(metadata, dict) else load_import_metadata(metadata_path)
    if manifest.get("publication_manifest_version") != PUBLICATION_MANIFEST_VERSION:
        raise ValueError("Fallback import publication manifest is missing or unsupported")

    completed_filename = manifest.get("completed_filename")
    if not is_completed_filename(completed_filename):
        raise ValueError("Fallback import manifest contains an invalid completed filename")

    state = manifest.get("publication_state")
    if state in {"private_writing", "failed"}:
        token = completed_filename[len("stats_") : -len(".ready.csv")]
        temporary_path = Path(ready_dir) / f".stats_{token}.tmp"
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            logger.warning(
                "[EXCEL] Failed to clean private interrupted publication %s",
                temporary_path,
                exc_info=True,
            )
    if state not in _RECOVERABLE_PUBLICATION_STATES:
        raise ValueError("Fallback import manifest does not identify a published CSV")

    if state == "prepared":
        token = completed_filename[len("stats_") : -len(".ready.csv")]
        temporary_path = Path(ready_dir) / f".stats_{token}.tmp"
        ready_path = Path(ready_dir) / completed_filename
        if not ready_path.is_file() or temporary_path.exists():
            raise ValueError("Fallback import publication was interrupted before atomic rename")
        set_import_metadata_state(metadata_path, manifest, "published")

    return completed_filename


def publish_fallback_csv(
    csv_df: pd.DataFrame,
    *,
    paths: FallbackImportPaths,
    metadata: dict,
    token_factory: Callable[[], str] = lambda: secrets.token_hex(16),
    rename_file: Callable[[str, str], None] = os.rename,
    sync_file: Callable[[int], None] = os.fsync,
) -> str:
    """Publish a closed CSV under one unique, immutable Ready identity."""
    token = token_factory()
    if not isinstance(token, str) or re.fullmatch(r"[0-9a-f]{32}", token) is None:
        raise ValueError("Fallback import token must be 32 lowercase hexadecimal characters")

    ready_dir = Path(paths.ready_dir)
    ready_dir.mkdir(parents=True, exist_ok=True)
    completed_filename = f"stats_{token}.ready.csv"
    temporary_path = ready_dir / f".stats_{token}.tmp"
    ready_path = ready_dir / completed_filename
    if temporary_path.exists() or ready_path.exists():
        raise FileExistsError(f"Fallback import identity already exists: {completed_filename}")

    metadata.update(
        {
            "publication_manifest_version": PUBLICATION_MANIFEST_VERSION,
            "completed_filename": completed_filename,
            "publication_state": "private_writing",
            "publication_state_updated_at_utc": utcnow().isoformat(),
        }
    )
    write_import_metadata(metadata, paths.import_metadata_file_path)

    try:
        with open(temporary_path, "x", encoding="utf-8-sig", newline="") as handle:
            csv_df.to_csv(handle, index=False)
            handle.flush()
            sync_file(handle.fileno())

        set_import_metadata_state(paths.import_metadata_file_path, metadata, "prepared")
        rename_file(str(temporary_path), str(ready_path))
        if not ready_path.is_file() or temporary_path.exists():
            raise OSError("Atomic Ready publication could not be verified")
        set_import_metadata_state(paths.import_metadata_file_path, metadata, "published")
        logger.info("[EXCEL] Published immutable CSV identity=%s", completed_filename)
        return completed_filename
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            logger.warning(
                "[EXCEL] Failed to remove private publication file %s",
                temporary_path,
                exc_info=True,
            )
        if not ready_path.exists():
            try:
                set_import_metadata_state(paths.import_metadata_file_path, metadata, "failed")
            except Exception:
                logger.warning("[EXCEL] Failed to persist publication failure state", exc_info=True)
        raise


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
        publish_fallback_csv(csv_df, paths=paths, metadata=metadata)

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
