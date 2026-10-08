"""Service helpers for player location CSV imports."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import logging
from typing import Any

from location_importer import load_staging_and_merge, parse_output_csv
from services import import_audit_service

logger = logging.getLogger(__name__)

MAX_LOCATION_CSV_BYTES = 10 * 1024 * 1024
LOCATION_AUDIT_IMPORT_KIND = "player_location"
LOCATION_AUDIT_SOURCE_TYPE = "discord_upload_csv"
LOCATION_AUDIT_PARSE_PHASE = "location_csv_parse"
LOCATION_AUDIT_MERGE_PHASE = "location_sql_merge"
LOCATION_AUDIT_REPLACE_PHASE = "location_sql_replace"
LOCATION_AUDIT_REFRESH_PHASE = "location_post_import_refresh"

CsvParser = Callable[[bytes], list[tuple]]
LocationMerge = Callable[[list[tuple]], tuple[int, int]]
SuccessCallback = Callable[[], None]
AsyncThreadRunner = Callable[..., Awaitable[tuple[int, int]]]
AuditThreadRunner = Callable[..., Awaitable[Any]]


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


@dataclass(frozen=True, slots=True)
class LocationImportAuditContext:
    source_filename: str | None = None
    source_message_id: int | None = None
    source_channel_id: int | None = None
    actor_discord_id: int | None = None
    entry_point: str = "location_import"
    sql_operation: str = "merge"


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


def _audit_timestamp_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _duration_ms(started: datetime) -> int:
    return max(0, int((datetime.now(UTC) - started).total_seconds() * 1000))


def _sha256_hex(content: bytes | None) -> str | None:
    if content is None:
        return None
    try:
        return hashlib.sha256(content).hexdigest()
    except Exception:
        logger.debug("location_audit_hash_failed", exc_info=True)
        return None


def _start_location_audit_batch_sync(
    context: LocationImportAuditContext,
    csv_bytes: bytes | None,
):
    return import_audit_service.start_batch_best_effort(
        import_kind=LOCATION_AUDIT_IMPORT_KIND,
        source_type=LOCATION_AUDIT_SOURCE_TYPE,
        source_filename=context.source_filename,
        source_file_hash_sha256=_sha256_hex(csv_bytes),
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        details=_audit_details(context),
    )


def _audit_details(
    context: LocationImportAuditContext,
    *,
    rows_parsed: int | None = None,
    staging_rows: int | None = None,
    total_tracked: int | None = None,
    error: str | None = None,
) -> dict[str, object]:
    details: dict[str, object] = {
        "entry_point": context.entry_point,
        "sql_operation": context.sql_operation,
    }
    if rows_parsed is not None:
        details["rows_parsed"] = rows_parsed
    if staging_rows is not None:
        details["staging_rows"] = staging_rows
    if total_tracked is not None:
        details["total_tracked"] = total_tracked
    if error:
        details["error"] = error
    return details


async def start_location_audit_batch(
    *,
    context: LocationImportAuditContext,
    csv_bytes: bytes | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
):
    try:
        return await audit_runner(
            _start_location_audit_batch_sync,
            context,
            csv_bytes,
        )
    except Exception:
        logger.warning("location_audit_start_failed; continuing import", exc_info=True)
        return None


async def record_location_audit_phase(
    batch_ref,
    *,
    phase_name: str,
    phase_status: str,
    started_at_utc: datetime | None = None,
    rows_in: int | None = None,
    rows_out: int | None = None,
    duration_ms: int | None = None,
    error_type: str | None = None,
    error_text: str | None = None,
    details: object = None,
    set_batch_status: str | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.record_phase_best_effort,
            batch_ref,
            phase_name=phase_name,
            phase_status=phase_status,
            started_at_utc=started_at_utc,
            completed_at_utc=_audit_timestamp_utc(),
            rows_in=rows_in,
            rows_out=rows_out,
            duration_ms=duration_ms,
            error_type=error_type,
            error_text=error_text,
            details=details,
            set_batch_status=set_batch_status,
        )
    except Exception:
        logger.warning(
            "location_audit_phase_failed phase=%s; continuing import", phase_name, exc_info=True
        )


async def complete_location_audit_batch(
    batch_ref,
    *,
    status: str = "completed",
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    details: object = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.complete_batch_best_effort,
            batch_ref,
            status=status,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            details=details,
        )
    except Exception:
        logger.warning("location_audit_complete_failed; continuing import", exc_info=True)


async def fail_location_audit_batch(
    batch_ref,
    *,
    status: str = "failed",
    error_type: str | None = None,
    error_text: str | None = None,
    rows_in_source: int | None = None,
    rows_staged: int | None = None,
    rows_written: int | None = None,
    rows_skipped: int | None = None,
    details: object = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> None:
    if batch_ref is None:
        return
    try:
        await audit_runner(
            import_audit_service.fail_batch_best_effort,
            batch_ref,
            status=status,
            error_type=error_type,
            error_text=error_text,
            rows_in_source=rows_in_source,
            rows_staged=rows_staged,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            details=details,
        )
    except Exception:
        logger.warning("location_audit_fail_failed; continuing import", exc_info=True)


def _location_sql_phase(context: LocationImportAuditContext) -> str:
    return (
        LOCATION_AUDIT_REPLACE_PHASE
        if context.sql_operation == "replace"
        else LOCATION_AUDIT_MERGE_PHASE
    )


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
    audit_context: LocationImportAuditContext | None = None,
    audit_runner: AuditThreadRunner = asyncio.to_thread,
) -> LocationImportResult:
    validation = validate_location_csv_attachment(filename=filename, size=size)
    if not validation.ok:
        return LocationImportResult(ok=False, message=validation.message or "❌ Invalid CSV file.")

    started = started_at_utc or datetime.now(UTC)
    audit_context = audit_context or LocationImportAuditContext(
        source_filename=filename,
        entry_point="location_command_import",
        sql_operation="merge",
    )
    audit_ref = await start_location_audit_batch(
        context=audit_context,
        csv_bytes=csv_bytes,
        audit_runner=audit_runner,
    )

    parse_started = datetime.now(UTC)
    try:
        rows = parser(csv_bytes)
    except Exception as exc:
        logger.exception("[/import_locations] parse_output_csv crashed")
        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_PARSE_PHASE,
            phase_status="failed",
            started_at_utc=parse_started.replace(tzinfo=None),
            duration_ms=_duration_ms(parse_started),
            error_type=type(exc).__name__,
            error_text=str(exc),
            details=_audit_details(audit_context, error=str(exc)),
            audit_runner=audit_runner,
        )
        await fail_location_audit_batch(
            audit_ref,
            error_type=type(exc).__name__,
            error_text=str(exc),
            details=_audit_details(audit_context, error=str(exc)),
            audit_runner=audit_runner,
        )
        return LocationImportResult(
            ok=False,
            message=f"❌ Failed to parse CSV: `{type(exc).__name__}: {exc}`",
        )

    if not rows:
        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_PARSE_PHASE,
            phase_status="skipped",
            started_at_utc=parse_started.replace(tzinfo=None),
            rows_out=0,
            duration_ms=_duration_ms(parse_started),
            error_type="NoValidLocationRows",
            error_text="No valid rows found in CSV.",
            details=_audit_details(audit_context, rows_parsed=0),
            audit_runner=audit_runner,
        )
        await fail_location_audit_batch(
            audit_ref,
            status="skipped",
            error_type="NoValidLocationRows",
            error_text="No valid rows found in CSV.",
            rows_in_source=0,
            rows_skipped=0,
            details=_audit_details(audit_context, rows_parsed=0),
            audit_runner=audit_runner,
        )
        return LocationImportResult(ok=False, message="⚠️ No valid rows found in the CSV.")

    await record_location_audit_phase(
        audit_ref,
        phase_name=LOCATION_AUDIT_PARSE_PHASE,
        phase_status="completed",
        started_at_utc=parse_started.replace(tzinfo=None),
        rows_out=len(rows),
        duration_ms=_duration_ms(parse_started),
        details=_audit_details(audit_context, rows_parsed=len(rows)),
        audit_runner=audit_runner,
    )

    sql_started = datetime.now(UTC)
    try:
        staging_rows, total_tracked = await thread_runner(merge_rows, rows)
    except Exception as exc:
        logger.exception("[/import_locations] load_staging_and_merge failed")
        await record_location_audit_phase(
            audit_ref,
            phase_name=_location_sql_phase(audit_context),
            phase_status="failed",
            started_at_utc=sql_started.replace(tzinfo=None),
            rows_in=len(rows),
            duration_ms=_duration_ms(sql_started),
            error_type=type(exc).__name__,
            error_text=str(exc),
            details=_audit_details(audit_context, rows_parsed=len(rows), error=str(exc)),
            audit_runner=audit_runner,
        )
        await fail_location_audit_batch(
            audit_ref,
            error_type=type(exc).__name__,
            error_text=str(exc),
            rows_in_source=len(rows),
            rows_staged=0,
            rows_written=0,
            rows_skipped=len(rows),
            details=_audit_details(audit_context, rows_parsed=len(rows), error=str(exc)),
            audit_runner=audit_runner,
        )
        return LocationImportResult(
            ok=False,
            rows_parsed=len(rows),
            message=f"❌ Failed to import rows: `{type(exc).__name__}: {exc}`",
        )

    await record_location_audit_phase(
        audit_ref,
        phase_name=_location_sql_phase(audit_context),
        phase_status="completed",
        started_at_utc=sql_started.replace(tzinfo=None),
        rows_in=len(rows),
        rows_out=staging_rows,
        duration_ms=_duration_ms(sql_started),
        details=_audit_details(
            audit_context,
            rows_parsed=len(rows),
            staging_rows=staging_rows,
            total_tracked=total_tracked,
        ),
        set_batch_status="staged",
        audit_runner=audit_runner,
    )

    refresh_failed: Exception | None = None
    if on_success is not None:
        refresh_started = datetime.now(UTC)
        try:
            on_success()
        except Exception as exc:
            refresh_failed = exc
            logger.exception("[/import_locations] refresh success callback failed")
        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_REFRESH_PHASE,
            phase_status="failed" if refresh_failed else "completed",
            started_at_utc=refresh_started.replace(tzinfo=None),
            duration_ms=_duration_ms(refresh_started),
            error_type=type(refresh_failed).__name__ if refresh_failed else None,
            error_text=str(refresh_failed) if refresh_failed else None,
            details=_audit_details(
                audit_context,
                rows_parsed=len(rows),
                staging_rows=staging_rows,
                total_tracked=total_tracked,
                error=str(refresh_failed) if refresh_failed else None,
            ),
            audit_runner=audit_runner,
        )
    else:
        await record_location_audit_phase(
            audit_ref,
            phase_name=LOCATION_AUDIT_REFRESH_PHASE,
            phase_status="skipped",
            rows_in=staging_rows,
            rows_out=staging_rows,
            details=_audit_details(
                audit_context,
                rows_parsed=len(rows),
                staging_rows=staging_rows,
                total_tracked=total_tracked,
            ),
            audit_runner=audit_runner,
        )

    await complete_location_audit_batch(
        audit_ref,
        status="failed" if refresh_failed else "completed",
        rows_in_source=len(rows),
        rows_staged=staging_rows,
        rows_written=staging_rows,
        rows_skipped=max(0, len(rows) - int(staging_rows or 0)),
        details=_audit_details(
            audit_context,
            rows_parsed=len(rows),
            staging_rows=staging_rows,
            total_tracked=total_tracked,
            error=str(refresh_failed) if refresh_failed else None,
        ),
        audit_runner=audit_runner,
    )

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
