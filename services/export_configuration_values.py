"""Import-compatible, bounded configuration values checked before activation."""

from decimal import Decimal, InvalidOperation
import math

import pandas as pd

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.new_source_reporting import fits_decimal


def sql_text(value, limit):
    """SQL nchar/nvarchar lengths count UTF-16 code units, not code points."""
    try:
        return (
            isinstance(value, str)
            and bool(value.strip())
            and len(value.encode("utf-16-le")) // 2 <= limit
        )
    except UnicodeError:
        return False


def numeric_value(name, column, value):
    """Bound magnitude before conversion, including exponent-form text."""
    try:
        if isinstance(value, bool):
            raise ValueError("Boolean numeric input")
        number = Decimal(str(value))
        floating = column.startswith("Weight")
        limit = (
            Decimal("99999999999999999999999999.999999999999")
            if floating
            else (
                2**63 - 1
                if column in {"GovernorID", "MinPower"}
                else (
                    8
                    if column == "CampID"
                    else 255 if column == "WindowSeq" else 1 if column == "Exempt" else 2**31 - 1
                )
            )
        )
        minimum = (
            1
            if column in {"CampID", "StartScanID", "EndScanID", "KVK_NO"}
            or (name == "ProcConfig" and column in {"MATCHMAKING_SCAN", "DRAFTSCAN"})
            else 0
        )
        if not number.is_finite() or number < minimum or number > limit:
            raise ValueError("Numeric range")
        if floating:
            if not fits_decimal(number, 12) or not math.isfinite(float(number)):
                raise ValueError("Weight representation")
        elif number != number.to_integral_value():
            raise ValueError("Integer required")
        if name == "KVK_DKPWeights" and column == "KVK_NO" and int(str(value)) != number:
            raise ValueError("Source weight season requires plain integer text")
        return number
    except (ValueError, InvalidOperation, OverflowError) as exc:
        raise SourceConflict(f"{name}: {column} has an invalid numeric value.") from exc


def verify_import_values(name, rows, text_columns, date_columns):
    """Exercise the same pandas column conversions as the normal importer.

    A complete column matters: mixed blank/integer input can change pandas'
    intermediate dtype and lose precision even when individual tokens parse.
    """
    if not rows:
        return
    frame = pd.DataFrame(rows)
    for column in frame:
        if column in text_columns:
            continue
        original = frame[column]
        present = original.notna() & (original != "")
        try:
            if column in date_columns:
                tokens = original.astype("string").str.strip()
                parsed = pd.to_datetime(tokens, format="%d/%m/%Y", errors="coerce")
                missing = parsed.isna() & present
                parsed.loc[missing] = pd.to_datetime(
                    tokens[missing], format="%d/%m/%y", errors="coerce"
                )
                if parsed[present].isna().any():
                    raise ValueError("Unimportable date")
            else:
                parsed = pd.to_numeric(original, errors="coerce")
                floating = column.startswith("Weight") or column == "MinPower"
                if not floating:
                    parsed = parsed.astype("Int64")
                for index in original.index[present]:
                    actual = parsed[index]
                    expected = numeric_value(name, column, original[index])
                    if pd.isna(actual) or not math.isfinite(float(actual)):
                        raise ValueError("Unimportable number")
                    if column.startswith("Weight"):
                        if float(actual) != float(expected):
                            raise ValueError("Changed weight")
                    elif Decimal(str(actual)) != expected:
                        raise ValueError("Lossy integer conversion")
        except (ValueError, TypeError, OverflowError, InvalidOperation) as exc:
            raise SourceConflict(
                f"{name}: {column} would change or become empty during import. "
                "Use plain numeric formatting and DD/MM/YYYY dates, then check again."
            ) from exc
