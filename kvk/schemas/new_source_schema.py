"""Versioned, dependency-free contracts for snapshot_report_v1 XLSX input."""

from dataclasses import dataclass, fields
from enum import StrEnum

SOURCE_KEY = "snapshot_report_v1"
PLAYER_SCHEMA_VERSION = "snapshot_report_players_v1"
AGGREGATE_SCHEMA_VERSION = "snapshot_report_aggregate_v1"
BIGINT_MAX = 9_223_372_036_854_775_807
INT_MAX = 2_147_483_647
PLAYER_SHEET = "Scan"
KINGDOM_SHEET = "Kingdom Stats"
CAMP_SHEET = "Camp Stats"
PLAYER_HEADERS = (
    "Governor ID",
    "Name",
    "Alliance",
    "Power",
    "City Hall",
    "VIP",
    "Civilization",
    "T1 Kills",
    "T2 Kills",
    "T3 Kills",
    "T4 Kills",
    "T5 Kills",
    "Total Kill Points",
    "Ranged Points",
    "Dead",
    "Healed",
    "RSS Assistance",
    "Alliance Helps",
    "RSS Gathered",
    "Troops Power",
    "Tech Power",
    "Building Power",
    "Commander Power",
    "KvK Played",
    "Autarch Times",
    "Most KvK Kill",
    "Most KvK Dead",
    "Most KvK Heal",
    "Acclaim",
    "Highest Acclaim",
    "AoO Joined",
    "AoO Won",
    "AoO Avg Kill",
    "AoO Avg Dead",
    "AoO Avg Heal",
    "Kingdom",
)
PLAYER_TEXT_HEADERS = frozenset(("Name", "Alliance", "Civilization"))
AGGREGATE_METRICS = (
    "T4 Kills",
    "T5 Kills",
    "KP (T4+T5)",
    "Dead",
    "T4+T5DEAD",
    "Healed",
    "Acclaim",
    "DKP",
)
KINGDOM_HEADERS = ("Camp", "KD", *AGGREGATE_METRICS)
CAMP_HEADERS = ("CAMP", *AGGREGATE_METRICS)


class SourceKind(StrEnum):
    PLAYERS = "players"
    AGGREGATE = "aggregate"


class TimePrecision(StrEnum):
    MINUTE = "minute"
    SECOND = "second"


class MetricState(StrEnum):
    AVAILABLE = "available"
    MISSING_START = "missing_start"
    MISSING_END = "missing_end"
    INVALID_SOURCE_VALUE = "invalid_source_value"
    COUNTER_REGRESSION = "counter_regression"
    UNSUPPORTED = "unsupported"
    MISSING_CONFIGURATION = "missing_configuration"
    NOT_APPLICABLE = "not_applicable"


class ReportState(StrEnum):
    NOT_RECEIVED = "not_received"
    VALIDATION_FAILED = "validation_failed"
    LIVE = "live"
    FINAL = "final"
    CORRECTED_FINAL = "corrected_final"


class SourceValidationError(ValueError):
    """Safe structural reason; never includes uploaded values or filenames."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ParseLimits:
    max_compressed_bytes: int = 20 * 1024 * 1024
    max_uncompressed_bytes: int = 250 * 1024 * 1024
    max_entry_bytes: int = 100 * 1024 * 1024
    max_zip_members: int = 2_000
    max_compression_ratio: int = 200
    max_player_rows: int = 50_000
    max_kingdom_rows: int = 512
    max_camps: int = 8
    max_columns: int = 64
    max_populated_cells: int = 2_000_000
    max_cell_characters: int = 32_767

    def __post_init__(self):
        if any(
            type(getattr(self, f.name)) is not int or getattr(self, f.name) <= 0
            for f in fields(self)
        ):
            raise ValueError("Parse limits must be positive integers.")


def validate_headers(actual: tuple[str, ...], expected: tuple[str, ...]) -> None:
    """Column order may vary; membership and uniqueness may not."""
    if len(actual) != len(expected) or set(actual) != set(expected):
        raise SourceValidationError("schema_headers", "Require exactly the recognized headers.")
