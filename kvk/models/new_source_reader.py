"""Immutable logical reader tables; provider writes remain a separate contract."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json

from kvk.rendering.new_source_export import text_value

READER_VERSION = "snapshot_report_reader_v1"


def no_fight(window):
    """Match the pinned WindowConfig no-fight classification without live lookups."""
    return window["PeriodKind"] == "no_fight" or (
        window["StartScanID"] is not None and window["StartScanID"] == window["EndScanID"]
    )


@dataclass(frozen=True)
class ReaderColumn:
    label: str
    kind: str = "text"
    number_format: str = "@"

    def __post_init__(self):
        if not self.label or self.kind not in ("text", "number", "datetime"):
            raise ValueError("Reader columns need a label and a supported cell kind.")


@dataclass(frozen=True)
class ReaderLink:
    row: int
    column: int
    target: str


def spreadsheet_number(value):
    """Conservative shared Excel/Sheets 15-digit boundary, without float coercion."""
    if type(value) not in (int, Decimal) or not Decimal(value).is_finite():
        raise ValueError("Reader numbers require finite exact integers or decimals.")
    number = Decimal(value)
    digits = list(number.as_tuple().digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
    return (
        number.copy_abs() <= 999_999_999_999_999
        and (number == 0 or number.copy_abs() >= Decimal("1e-307"))
        and len(digits) <= 15
    )


@dataclass(frozen=True)
class ReaderSheet:
    key: str
    title: str
    period: str
    purpose: str
    availability: str
    columns: tuple[ReaderColumn, ...]
    rows: tuple[tuple, ...]
    exact_rows: tuple[tuple[str, ...], ...]
    notes: tuple[str, ...] = ()
    links: tuple[ReaderLink, ...] = ()

    def __post_init__(self):
        if not self.key or not self.title or not self.columns:
            raise ValueError("Reader sheet identity and columns are required.")
        if len({c.label for c in self.columns}) != len(self.columns):
            raise ValueError("Reader columns must be unique.")
        if any(
            not isinstance(x, tuple)
            for x in (self.columns, self.rows, self.exact_rows, self.notes, self.links)
        ):
            raise ValueError("Reader tables require immutable tuples.")
        if len(self.rows) != len(self.exact_rows):
            raise ValueError("Every reader row requires lossless audit values.")
        for row, exact in zip(self.rows, self.exact_rows, strict=True):
            if (
                not isinstance(row, tuple)
                or not isinstance(exact, tuple)
                or len(row) != len(self.columns)
                or len(exact) != len(row)
            ):
                raise ValueError("Reader row shape differs from its columns.")
            for column, value, original in zip(self.columns, row, exact, strict=True):
                if type(original) is not str:
                    raise ValueError("Audit values must be exact text.")
                if column.kind not in ("text", "number", "datetime"):
                    raise ValueError("Unsupported reader cell kind.")
                if value is None:
                    continue
                if column.kind == "text" and type(value) is not str:
                    raise ValueError("Identifiers and labels must remain literal text.")
                if column.kind == "number" and not spreadsheet_number(value):
                    raise ValueError("Unsafe spreadsheet numeric precision.")
                if column.kind == "datetime" and (
                    not isinstance(value, datetime) or value.utcoffset() != UTC.utcoffset(value)
                ):
                    raise ValueError("Reader times must be timezone-aware UTC.")
                if text_value(value) != original:
                    raise ValueError("Reader and exact audit values differ.")
        if any(
            not 0 <= link.row < len(self.rows) or not 0 <= link.column < len(self.columns)
            for link in self.links
        ):
            raise ValueError("Invalid reader link cell.")


@dataclass(frozen=True)
class ReaderProjection:
    sheets: tuple[ReaderSheet, ...]
    audit: object
    history: object
    version: str = READER_VERSION
    checkpoints: tuple = ()

    def __post_init__(self):
        keys = {s.key for s in self.sheets}
        if not isinstance(self.sheets, tuple) or len(keys) != len(self.sheets):
            raise ValueError("Reader sheet keys must be unique and immutable.")
        if not self.sheets or self.sheets[0].key != "guide":
            raise ValueError("Report Guide must be first.")
        if any(link.target not in keys for s in self.sheets for link in s.links):
            raise ValueError("Reader links must resolve within this projection.")
        if not isinstance(self.checkpoints, tuple) or any(
            key not in keys for checkpoint in self.checkpoints for key in checkpoint.sheet_keys
        ):
            raise ValueError("Checkpoint sheets must belong to this immutable projection.")

    @property
    def key(self):
        payload = [
            self.version,
            self.audit.key,
            self.history.content_hash.hex(),
            self.history.guild_id,
        ]
        if self.checkpoints:
            payload.append([c.canonical for c in self.checkpoints])
        payload += [
            [
                s.key,
                s.title,
                s.period,
                s.purpose,
                s.availability,
                [(c.label, c.kind, c.number_format) for c in s.columns],
                s.exact_rows,
                [[text_value(v) for v in row] for row in s.rows],
                s.notes,
                [(link.row, link.column, link.target) for link in s.links],
            ]
            for s in self.sheets
        ]
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()
