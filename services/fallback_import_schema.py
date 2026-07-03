"""Schema detection and normalization for main fallback stat imports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import re
from typing import Any

import pandas as pd

from utils import utcnow

FULL_FALLBACK_SNAPSHOT = "full_fallback_snapshot"
INTERIM_AUTO_PARTIAL_SNAPSHOT = "interim_auto_partial_snapshot"
UNKNOWN_OR_INVALID = "unknown_or_invalid"

SCORE_SOURCE_CREDIT = "Credit"
SCORE_SOURCE_CONDUCT_SCORE = "Conduct Score"
CANONICAL_SCORE_COLUMN = "Credit"


def _normalize_header(header: object) -> str:
    text = str(header or "").strip().casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


CANONICAL_COLUMNS: list[str] = [
    "Governor ID",
    "Name",
    "Power",
    "Alliance",
    "T1-Kills",
    "T2-Kills",
    "T3-Kills",
    "T4-Kills",
    "T5-Kills",
    "Total Kill Points",
    "Dead Troops",
    "Healed Troops",
    "Rss Assistance",
    "Alliance Helps",
    "Rss Gathered",
    "City Hall",
    "Troops Power",
    "Tech Power",
    "Building Power",
    "Commander Power",
    "Civilization",
    "Autarch Times",
    "Ranged Points",
    "KvK Played",
    "Most KvK Kill",
    "Most KvK Dead",
    "Most KvK Heal",
    "Acclaim",
    "Highest Acclaim",
    "AOO Joined",
    "AOO Won",
    "AOO Avg Kill",
    "AOO Avg Dead",
    "AOO Avg Heal",
    CANONICAL_SCORE_COLUMN,
    "updated_on",
]

PARTIAL_COLUMNS: list[str] = [
    "Governor ID",
    "Name",
    "Power",
    "Alliance",
    "T1-Kills",
    "T2-Kills",
    "T3-Kills",
    "T4-Kills",
    "T5-Kills",
    "Total Kill Points",
    "Dead Troops",
    "Healed Troops",
    "City Hall",
    "Civilization",
    "Autarch Times",
    "Ranged Points",
    "KvK Played",
    "Most KvK Kill",
    "Most KvK Dead",
    "Most KvK Heal",
    "Acclaim",
    "Highest Acclaim",
    "AOO Joined",
    "AOO Won",
    "AOO Avg Kill",
    "AOO Avg Dead",
    "AOO Avg Heal",
]

FULL_REQUIRED_COLUMNS: list[str] = [
    col for col in CANONICAL_COLUMNS if col not in {CANONICAL_SCORE_COLUMN, "updated_on"}
]

SCORE_ALIASES = (SCORE_SOURCE_CREDIT, SCORE_SOURCE_CONDUCT_SCORE)

TEXT_COLUMNS = {"Name", "Alliance", "Civilization", "updated_on"}
TEXT_COLUMN_MAX_LENGTHS = {
    "Name": 200,
    "Alliance": 100,
    "Civilization": 100,
    "updated_on": 200,
}
DECIMAL_COLUMNS = {CANONICAL_SCORE_COLUMN}
INTEGER_COLUMNS = tuple(
    col for col in CANONICAL_COLUMNS if col not in TEXT_COLUMNS | DECIMAL_COLUMNS
)

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RE = re.compile(r"\s+")

_HEADER_ALIASES: dict[str, str] = {
    _normalize_header(col): col for col in CANONICAL_COLUMNS if col not in {CANONICAL_SCORE_COLUMN}
}
_HEADER_ALIASES[_normalize_header(SCORE_SOURCE_CREDIT)] = CANONICAL_SCORE_COLUMN
_HEADER_ALIASES[_normalize_header(SCORE_SOURCE_CONDUCT_SCORE)] = SCORE_SOURCE_CONDUCT_SCORE


@dataclass(frozen=True, slots=True)
class FallbackImportMetadata:
    source_type: str
    source_filename: str | None
    rows_in_source: int
    rows_written: int
    score_header: str | None
    columns_present: tuple[str, ...]
    generated_at_utc: datetime

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_filename": self.source_filename,
            "rows_in_source": self.rows_in_source,
            "rows_written": self.rows_written,
            "score_header": self.score_header,
            "columns_present": list(self.columns_present),
            "generated_at_utc": self.generated_at_utc.isoformat(),
        }

    def as_json(self) -> str:
        return json.dumps(self.as_json_dict(), ensure_ascii=False, indent=2)


@dataclass(frozen=True, slots=True)
class NormalizedFallbackImport:
    dataframe: pd.DataFrame
    metadata: FallbackImportMetadata


def _normalize_governor_key(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return str(int(float(text.replace(",", ""))))
    except Exception:
        return text


def _canonicalize_headers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    columns: dict[str, str] = {}
    rename: dict[object, str] = {}
    seen_canonical: dict[str, str] = {}

    for raw_col in df.columns:
        raw_text = str(raw_col or "").strip()
        canonical = _HEADER_ALIASES.get(_normalize_header(raw_text), raw_text)
        if canonical in seen_canonical:
            raise ValueError(
                f"Duplicate fallback import column after normalization: {raw_text!r} "
                f"conflicts with {seen_canonical[canonical]!r}"
            )
        seen_canonical.setdefault(canonical, raw_text)
        columns[canonical] = raw_text
        rename[raw_col] = canonical

    normalized = df.rename(columns=rename).copy()
    return normalized, columns


def _score_values_identical(left: pd.Series, right: pd.Series) -> bool:
    left_norm = left.fillna("").astype(str).str.strip()
    right_norm = right.fillna("").astype(str).str.strip()
    return bool(left_norm.equals(right_norm))


def _prepare_score_column(df: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    has_credit = CANONICAL_SCORE_COLUMN in df.columns
    has_conduct_score = SCORE_SOURCE_CONDUCT_SCORE in df.columns
    score_header: str | None = None

    if has_credit and has_conduct_score:
        if not _score_values_identical(df[CANONICAL_SCORE_COLUMN], df[SCORE_SOURCE_CONDUCT_SCORE]):
            raise ValueError("Both Credit and Conduct Score are present with conflicting values.")
        score_header = f"{SCORE_SOURCE_CREDIT}+{SCORE_SOURCE_CONDUCT_SCORE}"
    elif has_conduct_score:
        df[CANONICAL_SCORE_COLUMN] = df[SCORE_SOURCE_CONDUCT_SCORE]
        score_header = SCORE_SOURCE_CONDUCT_SCORE
    elif has_credit:
        score_header = SCORE_SOURCE_CREDIT

    if SCORE_SOURCE_CONDUCT_SCORE in df.columns:
        df = df.drop(columns=[SCORE_SOURCE_CONDUCT_SCORE])

    if CANONICAL_SCORE_COLUMN not in df.columns:
        df[CANONICAL_SCORE_COLUMN] = pd.NA

    return df, score_header


def classify_fallback_columns(columns_present: set[str]) -> str:
    if "Governor ID" not in columns_present:
        return UNKNOWN_OR_INVALID
    non_score_full = set(FULL_REQUIRED_COLUMNS)
    partial = set(PARTIAL_COLUMNS)
    if non_score_full.issubset(columns_present):
        return FULL_FALLBACK_SNAPSHOT
    if partial.issubset(columns_present):
        return INTERIM_AUTO_PARTIAL_SNAPSHOT
    return UNKNOWN_OR_INVALID


def detect_fallback_source_type(df: pd.DataFrame) -> str:
    """Detect source type without requiring latest SQL rows for partial overlay."""
    normalized, _original_columns = _canonicalize_headers(df)
    normalized, _score_header = _prepare_score_column(normalized)
    columns_present = set(normalized.columns)
    if _score_header is None:
        columns_present.discard(CANONICAL_SCORE_COLUMN)
    return classify_fallback_columns(columns_present)


def _blank_canonical_frame(row_count: int) -> pd.DataFrame:
    return pd.DataFrame(
        {col: pd.Series([pd.NA] * row_count, dtype="object") for col in CANONICAL_COLUMNS}
    )


def _canonical_full_frame(df: pd.DataFrame, columns_present: set[str]) -> pd.DataFrame:
    out = _blank_canonical_frame(len(df))
    for col in CANONICAL_COLUMNS:
        if col in df.columns and col != "updated_on":
            out[col] = df[col]
    return out


def _is_blank_value(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    text = str(value).strip()
    return text == "" or text.casefold() in {"nan", "none", "<na>"}


def _decimal_from_cell(value: object, column: str) -> Decimal | None:
    if _is_blank_value(value):
        return None
    text = str(value).strip().replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric value for {column}: {value!r}") from exc


def _format_integer_cell_for_bulk(value: object, column: str) -> str:
    number = _decimal_from_cell(value, column)
    if number is None:
        return ""
    integral = number.to_integral_value()
    if number != integral:
        raise ValueError(f"Non-integer value for {column}: {value!r}")
    return str(int(integral))


def _format_decimal_cell_for_bulk(value: object, column: str) -> str:
    number = _decimal_from_cell(value, column)
    if number is None:
        return ""
    return format(number, "f")


def _format_text_cell_for_bulk(value: object, column: str) -> str:
    if _is_blank_value(value):
        return ""

    text = str(value)
    text = _CONTROL_CHARS_RE.sub(" ", text)
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    max_length = TEXT_COLUMN_MAX_LENGTHS[column]
    return text[:max_length]


def prepare_fallback_csv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format canonical fallback rows for SQL Server BULK INSERT typed staging columns."""
    out = df.copy()
    for col in TEXT_COLUMNS:
        if col in out.columns:
            out[col] = out[col].map(
                lambda value, column=col: _format_text_cell_for_bulk(value, column)
            )
    for col in INTEGER_COLUMNS:
        if col in out.columns:
            out[col] = out[col].map(
                lambda value, column=col: _format_integer_cell_for_bulk(value, column)
            )
    for col in DECIMAL_COLUMNS:
        if col in out.columns:
            out[col] = out[col].map(
                lambda value, column=col: _format_decimal_cell_for_bulk(value, column)
            )
    return out


def _overlay_partial_on_latest(
    incoming: pd.DataFrame,
    latest_rows: pd.DataFrame,
    columns_present: set[str],
) -> pd.DataFrame:
    if latest_rows.empty:
        raise ValueError("Interim partial fallback import requires an existing latest snapshot.")

    latest = _canonical_full_frame(latest_rows, set(latest_rows.columns))
    latest["_gov_key"] = latest["Governor ID"].map(_normalize_governor_key)
    incoming_full = _canonical_full_frame(incoming, columns_present)
    incoming_full["_gov_key"] = incoming_full["Governor ID"].map(_normalize_governor_key)

    latest = latest[latest["_gov_key"] != ""].drop_duplicates("_gov_key", keep="last")
    incoming_full = incoming_full[incoming_full["_gov_key"] != ""].drop_duplicates(
        "_gov_key", keep="last"
    )

    latest_by_key = latest.set_index("_gov_key", drop=False)
    incoming_by_key = incoming_full.set_index("_gov_key", drop=False)

    for key, row in incoming_by_key.iterrows():
        if key not in latest_by_key.index:
            latest_by_key.loc[key, :] = pd.NA
            latest_by_key.loc[key, "_gov_key"] = key
        for col in columns_present:
            if col in CANONICAL_COLUMNS and col != "updated_on":
                latest_by_key.loc[key, col] = row[col]

    result = latest_by_key.reset_index(drop=True)
    return result[CANONICAL_COLUMNS]


def normalize_fallback_dataframe(
    df: pd.DataFrame,
    *,
    source_filename: str | None = None,
    latest_rows: pd.DataFrame | None = None,
    generated_at_utc: datetime | None = None,
) -> NormalizedFallbackImport:
    """Normalize a source fallback workbook/CSV into the fixed SQL bulk-import CSV shape."""
    if df.empty:
        raise ValueError("Fallback import file contains no rows.")

    normalized, _original_columns = _canonicalize_headers(df)
    normalized, score_header = _prepare_score_column(normalized)
    columns_present = set(normalized.columns)
    if score_header is None:
        columns_present.discard(CANONICAL_SCORE_COLUMN)
    source_type = classify_fallback_columns(columns_present)
    if source_type == UNKNOWN_OR_INVALID:
        missing = sorted(set(PARTIAL_COLUMNS) - columns_present)
        raise ValueError(
            "Fallback import schema is not recognized. "
            f"Missing minimum columns: {', '.join(missing[:8]) or 'unknown'}"
        )

    generated_at = generated_at_utc or utcnow()
    updated_on = generated_at.strftime("%d%b%y-%Hh%Mm")

    if source_type == INTERIM_AUTO_PARTIAL_SNAPSHOT:
        canonical = _overlay_partial_on_latest(
            normalized,
            latest_rows if latest_rows is not None else pd.DataFrame(),
            columns_present,
        )
    else:
        canonical = _canonical_full_frame(normalized, columns_present)

    canonical["updated_on"] = updated_on
    canonical = canonical.loc[:, CANONICAL_COLUMNS]

    metadata = FallbackImportMetadata(
        source_type=source_type,
        source_filename=source_filename,
        rows_in_source=len(df),
        rows_written=len(canonical),
        score_header=score_header,
        columns_present=tuple(col for col in CANONICAL_COLUMNS if col in columns_present),
        generated_at_utc=generated_at,
    )
    return NormalizedFallbackImport(dataframe=canonical, metadata=metadata)
