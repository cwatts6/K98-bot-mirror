"""Service helpers for player location CSV imports."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import logging

from location_importer import load_staging_and_merge, parse_output_csv

logger = logging.getLogger(__name__)

MAX_LOCATION_CSV_BYTES = 10 * 1024 * 1024

CsvParser = Callable[[bytes], list[tuple]]
LocationMerge = Callable[[list[tuple]], tuple[int, int]]
SuccessCallback = Callable[[], None]
AsyncThreadRunner = Callable[..., Awaitable[tuple[int, int]]]


@dataclass(frozen=True, slots=True)
class LocationCsvValidation:
    ok: bool
    message: str | None = None


@dataclass(frozen=True, slots=True)
class LocationImportResult:
    ok: bool
    message: str
    rows_parsed: int = 0
    staging_rows: int = 0
    total_tracked: int | None = None


def validate_location_csv_attachment(
    *, filename: str | None, size: int | None
) -> LocationCsvValidation:
    display_name = str(filename)
    lowered = (filename or "").lower()
    if not lowered.endswith(".csv"):
        return LocationCsvValidation(
            ok=False,
            message=f"❌ `{display_name}` isn’t a CSV file. Please upload a `.csv` (e.g., `output.csv`).",
        )

    if isinstance(size, int) and size > MAX_LOCATION_CSV_BYTES:
        return LocationCsvValidation(
            ok=False,
            message=f"❌ File too large ({size/1024/1024:.1f} MB). Please keep CSV under **10 MB**.",
        )

    return LocationCsvValidation(ok=True)


async def import_location_csv_bytes(
    csv_bytes: bytes,
    *,
    filename: str | None = None,
    size: int | None = None,
    parser: CsvParser = parse_output_csv,
    merge_rows: LocationMerge = load_staging_and_merge,
    on_success: SuccessCallback | None = None,
    thread_runner: AsyncThreadRunner = asyncio.to_thread,
    started_at_utc: datetime | None = None,
) -> LocationImportResult:
    validation = validate_location_csv_attachment(filename=filename, size=size)
    if not validation.ok:
        return LocationImportResult(ok=False, message=validation.message or "❌ Invalid CSV file.")

    started = started_at_utc or datetime.now(UTC)

    try:
        rows = parser(csv_bytes)
    except Exception as exc:
        logger.exception("[/import_locations] parse_output_csv crashed")
        return LocationImportResult(
            ok=False,
            message=f"❌ Failed to parse CSV: `{type(exc).__name__}: {exc}`",
        )

    if not rows:
        return LocationImportResult(ok=False, message="⚠️ No valid rows found in the CSV.")

    try:
        staging_rows, total_tracked = await thread_runner(merge_rows, rows)
    except Exception as exc:
        logger.exception("[/import_locations] load_staging_and_merge failed")
        return LocationImportResult(
            ok=False,
            rows_parsed=len(rows),
            message=f"❌ Failed to import rows: `{type(exc).__name__}: {exc}`",
        )

    if on_success is not None:
        try:
            on_success()
        except Exception:
            logger.exception("[/import_locations] refresh success callback failed")

    duration = (datetime.now(UTC) - started).total_seconds()
    count_part = f"Imported **{staging_rows}** row{'s' if staging_rows != 1 else ''}."
    tracked_part = f" Total tracked now **{total_tracked}**." if total_tracked is not None else ""
    message = f"✅ {count_part}{tracked_part} ⏱ {duration:.1f}s"

    return LocationImportResult(
        ok=True,
        message=message,
        rows_parsed=len(rows),
        staging_rows=staging_rows,
        total_tracked=total_tracked,
    )
