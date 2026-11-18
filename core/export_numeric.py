"""Exact SQL number materialization and RAW spreadsheet representation.

Frames must be built from original SQL scalars, before pandas float inference.
Only new captures use these rules; retained payload bytes are never rewritten.
"""

from decimal import Decimal
from numbers import Integral

import pandas as pd

MAX_EXACT_SHEET_INTEGER = 2**53


def sql_output_frame(rows, columns):
    """Preserve nullable bigint/decimal values before any dtype inference."""
    frame = pd.DataFrame([tuple(row) for row in rows], columns=columns, dtype=object)
    for column in frame.columns:
        values = frame[column].tolist()
        present = [v for v in values if v is not None]
        if present and all(type(v) is int and -(2**63) <= v < 2**63 for v in present):
            frame[column] = pd.array(values, dtype="Int64")
        elif not any(isinstance(v, (Integral, Decimal)) for v in present):
            # Preserve ordinary date/string/float inference for other report paths.
            frame[column] = pd.Series(values, index=frame.index)
    return frame


def sheet_integer(value):
    """RAW text beyond double's consecutive integer range; numeric otherwise.

    Applies to IDs and counts. Arithmetic on large textual counts requires an
    exact-number consumer; sending a rounded numeric cell is never an alternative.
    """
    value = int(value)
    return str(value) if abs(value) > MAX_EXACT_SHEET_INTEGER else value
