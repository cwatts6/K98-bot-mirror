"""Strict schema validation for KVK_ALL Full Data workbooks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
import hashlib
from typing import Any

FULL_DATA_SHEET_NAME = "Full Data"
SCHEMA_VERSION = "kvk_all_full_data_v2"

EXPECTED_FULL_DATA_COLUMNS = (
    "rank",
    "governor_id",
    "name",
    "kingdom",
    "campid",
    "max_units_healed_difference",
    "max_contribute_diff",
    "minkill_points",
    "minpower",
    "mindead",
    "mintroop_power",
    "minmax_units_healed",
    "minkills_iv",
    "minkills_v",
    "max_contribute_min",
    "maxkill_points",
    "maxpower",
    "maxdead",
    "maxtroop_power",
    "maxmax_units_healed",
    "maxkills_iv",
    "maxkills_v",
    "max_contribute_max",
    "min_points",
    "max_points",
    "points_difference",
    "min_power",
    "max_power",
    "cur_contribute_min",
    "cur_contribute_max",
    "power_difference",
    "first_updateUTC",
    "last_updateUTC",
    "latest_power",
    "kill_points_diff",
    "power_diff",
    "dead_diff",
    "troop_power_diff",
    "max_units_healed_diff",
    "kills_iv_diff",
    "kills_v_diff",
    "cur_contribute_diff",
    "healed_troops",
)


def normalize_sheet_name(value: str) -> str:
    return "".join(str(value).strip().lower().replace("_", " ").split())


def normalize_column_name(value: str) -> str:
    return str(value).strip()


@dataclass(frozen=True)
class KvkAllSchemaValidationError(ValueError):
    code: str
    message: str
    expected_sheet: str = FULL_DATA_SHEET_NAME
    available_sheets: tuple[str, ...] = ()
    missing_columns: tuple[str, ...] = ()
    unknown_columns: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "schema_version": self.schema_version,
            "expected_sheet": self.expected_sheet,
            "available_sheets": list(self.available_sheets),
            "missing_columns": list(self.missing_columns),
            "unknown_columns": list(self.unknown_columns),
        }


@dataclass(frozen=True)
class KvkAllSchemaValidationResult:
    schema_version: str
    sheet_name: str
    expected_columns: tuple[str, ...]
    actual_columns: tuple[str, ...]
    unknown_columns: tuple[str, ...] = field(default_factory=tuple)

    @property
    def column_count(self) -> int:
        return len(self.actual_columns)

    @property
    def column_hash(self) -> str:
        joined = "\n".join(self.actual_columns)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sheet_name": self.sheet_name,
            "column_count": self.column_count,
            "column_hash": self.column_hash,
            "unknown_columns": list(self.unknown_columns),
        }


def select_full_data_sheet(sheet_names: Iterable[str]) -> str:
    available = tuple(str(name) for name in sheet_names)
    target = normalize_sheet_name(FULL_DATA_SHEET_NAME)
    for name in available:
        if normalize_sheet_name(name) == target:
            return name
    raise KvkAllSchemaValidationError(
        code="missing_full_data_sheet",
        message=(
            "KVK_ALL workbook must contain a 'Full Data' sheet. "
            "Basic Data and fallback sheets are not accepted for this import."
        ),
        available_sheets=available,
    )


def validate_full_data_columns(
    columns: Iterable[Any],
    *,
    sheet_name: str = FULL_DATA_SHEET_NAME,
) -> KvkAllSchemaValidationResult:
    actual_columns = tuple(normalize_column_name(column) for column in columns)
    expected = EXPECTED_FULL_DATA_COLUMNS
    expected_set = set(expected)
    actual_set = set(actual_columns)
    missing = tuple(column for column in expected if column not in actual_set)
    unknown = tuple(column for column in actual_columns if column not in expected_set)

    if missing:
        raise KvkAllSchemaValidationError(
            code="missing_required_full_data_columns",
            message=(
                "KVK_ALL Full Data sheet is missing required column(s): " + ", ".join(missing)
            ),
            missing_columns=missing,
            unknown_columns=unknown,
        )

    return KvkAllSchemaValidationResult(
        schema_version=SCHEMA_VERSION,
        sheet_name=sheet_name,
        expected_columns=expected,
        actual_columns=actual_columns,
        unknown_columns=unknown,
    )
