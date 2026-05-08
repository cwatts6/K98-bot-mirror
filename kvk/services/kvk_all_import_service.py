"""Workbook parsing and canonical mapping for KVK_ALL Full Data imports."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import logging
from typing import Any

import pandas as pd

from kvk.schemas.kvk_all_schema import (
    COLUMN_ALIASES,
    FULL_DATA_NUMERIC_COLUMN_MAP,
    LEGACY_STAGE_NUMERIC_COLUMNS,
    REQUIRED_MIN_COLUMNS,
    SCHEMA_VERSION,
    KvkAllSchemaValidationError,
    select_full_data_sheet,
    validate_full_data_columns,
)
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KvkAllPreparedImport:
    dataframe: pd.DataFrame
    sheet_name: str
    schema_metadata: dict[str, Any]

    @property
    def staged_rows(self) -> int:
        return int(self.dataframe.shape[0])


class KvkAllImportPreparationError(ValueError):
    def __init__(self, message: str, *, sheet_name: str, schema_metadata: dict[str, Any]) -> None:
        super().__init__(message)
        self.sheet_name = sheet_name
        self.schema_metadata = schema_metadata


def _alias_key(value: str) -> str:
    return "".join(str(value).strip().lower().replace("_", " ").split())


def apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Apply legacy-compatible aliases before strict Full Data schema validation."""
    if df is None or df.empty:
        return df

    lookup = {_alias_key(column): column for column in df.columns}
    renames: dict[str, str] = {}
    for canonical, variants in COLUMN_ALIASES.items():
        if canonical in df.columns:
            continue
        for variant in variants:
            original = lookup.get(_alias_key(variant))
            if original:
                renames[original] = canonical
                break

    if not renames:
        return df

    logger.info("[KVK] Header aliases applied: %s", renames)
    return df.rename(columns=renames)


def read_full_data_workbook(
    content: bytes,
    source_filename: str | None = None,
) -> tuple[pd.DataFrame, str, dict[str, Any]]:
    """
    Read the authoritative KVK_ALL Full Data sheet and return raw frame plus schema metadata.

    Basic Data and fallback sheet selection are intentionally rejected for KVK_ALL imports.
    """
    if not content:
        raise ValueError("Empty file content")

    if source_filename and source_filename.lower().endswith(".csv"):
        raise KvkAllSchemaValidationError(
            code="unsupported_kvk_all_file_type",
            message="KVK_ALL imports require an Excel workbook containing the 'Full Data' sheet.",
        )

    try:
        xl = pd.ExcelFile(BytesIO(content))
    except Exception as exc:
        raise ValueError(f"Failed to open Excel file: {exc}") from exc

    sheet_names = xl.sheet_names or []
    if not sheet_names:
        raise ValueError("Excel file contains no sheets")

    chosen_sheet = select_full_data_sheet(sheet_names)

    try:
        df = xl.parse(chosen_sheet)
    except Exception as exc:
        raise ValueError(f"Failed to parse sheet '{chosen_sheet}': {exc}") from exc

    if df is None:
        raise ValueError("Parsed sheet is empty or invalid")

    df.columns = [str(column).strip() for column in df.columns]
    df = apply_column_aliases(df)
    schema_result = validate_full_data_columns(df.columns, sheet_name=chosen_sheet)
    logger.info("[KVK] Read sheet '%s' from uploaded file %s", chosen_sheet, source_filename)
    return df, chosen_sheet, schema_result.to_dict()


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _as_str(value: Any) -> str | None:
    return None if pd.isna(value) else str(value)[:64]


def _as_dt(value: Any) -> Any:
    if pd.isna(value):
        return None
    try:
        if isinstance(value, pd.Timestamp):
            return ensure_aware_utc(value.to_pydatetime())
        return ensure_aware_utc(pd.to_datetime(value, errors="coerce").to_pydatetime())
    except Exception:
        return None


def coerce_full_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Map Full Data v2 workbook columns into the canonical stage contract."""
    missing = [column for column in REQUIRED_MIN_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    out = pd.DataFrame()
    out["governor_id"] = df["governor_id"].map(_as_int)
    out["name"] = df["name"].map(_as_str) if "name" in df.columns else None
    out["kingdom"] = df["kingdom"].map(_as_int)
    out["campid"] = df.get("campid").map(_as_int) if "campid" in df.columns else None

    for source_col, target_col in FULL_DATA_NUMERIC_COLUMN_MAP.items():
        out[target_col] = df[source_col].map(_as_int) if source_col in df.columns else None

    for column in LEGACY_STAGE_NUMERIC_COLUMNS:
        out[column] = df[column].map(_as_int) if column in df.columns else None

    out["first_updateUTC"] = df.get("first_updateUTC", pd.Series([None] * len(df))).map(_as_dt)
    out["last_updateUTC"] = df.get("last_updateUTC", pd.Series([None] * len(df))).map(_as_dt)

    if out["governor_id"].isna().any() or out["kingdom"].isna().any():
        raise ValueError("One or more rows missing governor_id or kingdom after coercion.")
    return out


def attach_source_metadata(
    df: pd.DataFrame,
    *,
    sheet_name: str,
    schema_metadata: dict[str, Any],
) -> pd.DataFrame:
    df = df.copy()
    df["schema_version"] = str(schema_metadata.get("schema_version") or SCHEMA_VERSION)[:64]
    df["source_sheet_name"] = str(sheet_name)[:128]
    column_hash = schema_metadata.get("column_hash")
    df["source_column_hash"] = str(column_hash)[:64] if column_hash else None
    column_count = schema_metadata.get("column_count")
    df["source_column_count"] = int(column_count) if column_count is not None else None
    df["source_row_count"] = int(df.shape[0])
    return df


def prepare_kvk_all_import(content: bytes, source_filename: str) -> KvkAllPreparedImport:
    df_raw, sheet_name, schema_metadata = read_full_data_workbook(content, source_filename)
    try:
        coerced = coerce_full_data_frame(df_raw)
    except ValueError as exc:
        raise KvkAllImportPreparationError(
            str(exc),
            sheet_name=sheet_name,
            schema_metadata=schema_metadata,
        ) from exc
    enriched = attach_source_metadata(
        coerced,
        sheet_name=sheet_name,
        schema_metadata=schema_metadata,
    )
    return KvkAllPreparedImport(
        dataframe=enriched,
        sheet_name=sheet_name,
        schema_metadata=schema_metadata,
    )
