"""V2 export tables: exact text values, RAW Sheets and inert CSV cells."""

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import io
import json

from kvk.rendering.kvk_rankings_csv import _csv_text_cell


def text_value(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Export values must be finite.")
        return format(value, "f")
    if isinstance(value, datetime):
        # datetime2 source columns are explicitly UTC.
        return (
            value.replace(tzinfo=UTC).isoformat()
            if value.tzinfo is None
            else value.astimezone(UTC).isoformat()
        )
    if type(value) in (str, int, bool):
        return str(value)
    raise ValueError("V2 exports forbid binary floats and implicit object conversion.")


@dataclass(frozen=True)
class ExportTable:
    name: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def __post_init__(self):
        if not self.columns or len(set(self.columns)) != len(self.columns):
            raise ValueError("Export columns must be explicit and unique.")
        if not isinstance(self.rows, tuple) or any(
            not isinstance(row, tuple)
            or len(row) != len(self.columns)
            or any(type(cell) is not str for cell in row)
            for row in self.rows
        ):
            raise ValueError("Export rows require immutable, exact text cells.")

    @property
    def sha256(self):
        payload = json.dumps(
            (self.name, self.columns, self.rows), ensure_ascii=False, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def raw_values(self):
        """Caller must use value_input_option=RAW; IDs/Decimals remain strings."""
        return [list(self.columns), *(list(row) for row in self.rows)]

    def csv_bytes(self):
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        for row in (self.columns, *self.rows):
            writer.writerow([_csv_text_cell(value) for value in row])
        return output.getvalue().encode("utf-8-sig")


def table(name, columns, rows):
    return ExportTable(
        name,
        tuple(columns),
        tuple(tuple(text_value(row.get(c)) for c in columns) for row in rows),
    )
