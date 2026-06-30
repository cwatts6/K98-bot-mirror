from __future__ import annotations

from dataclasses import asdict
import hashlib
import logging
from typing import Any

from mge.dal import mge_results_dal
from mge.mge_xlsx_parser import parse_mge_results_xlsx
from services.mge_results_import_audit_service import (
    MGE_RESULTS_AUDIT_INGEST_PHASE,
    MGE_RESULTS_AUDIT_PARSE_PHASE,
    MGE_RESULTS_AUDIT_PRECHECK_PHASE,
    MgeResultsImportAuditContext,
    audit_duration_ms,
    complete_mge_results_audit_batch,
    fail_mge_results_audit_batch,
    mge_results_audit_details,
    mge_results_external_batch_id,
    record_mge_results_audit_phase,
    start_mge_results_audit_batch,
)
from utils import utcnow

logger = logging.getLogger(__name__)


class OverwriteConfirmationRequired(ValueError):
    """Raised when manual import detects existing event results and needs explicit confirmation."""


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _build_import_report(event_id: int, event_mode: str) -> dict[str, Any]:
    if event_mode == "open":
        top = mge_results_dal.fetch_open_top_15(event_id)
        return {"type": "open_top15", "rows": top}

    rows = mge_results_dal.fetch_controlled_awarded_vs_actual(event_id)
    matched = sum(1 for r in rows if r.get("ActualRank") is not None)
    return {
        "type": "controlled_awarded_vs_actual",
        "awarded_total": len(rows),
        "matched_actual_total": matched,
        "rows": rows[:25],
    }


def _audit_context(
    *,
    source: str,
    filename: str,
    actor_discord_id: int | None,
    event_id: int | None = None,
    event_mode: str | None = None,
    audit_context: object | None = None,
) -> MgeResultsImportAuditContext:
    if isinstance(audit_context, MgeResultsImportAuditContext):
        return audit_context
    if isinstance(audit_context, dict):
        return MgeResultsImportAuditContext(
            source_filename=str(audit_context.get("source_filename") or filename),
            source_message_id=_optional_int(audit_context.get("source_message_id")),
            source_channel_id=_optional_int(audit_context.get("source_channel_id")),
            actor_discord_id=_optional_int(
                audit_context.get("actor_discord_id", actor_discord_id)
            ),
            event_id=_optional_int(audit_context.get("event_id", event_id)),
            event_mode=(
                str(audit_context["event_mode"])
                if audit_context.get("event_mode")
                else event_mode
            ),
            source=str(audit_context.get("source") or source),
            entry_point=str(audit_context.get("entry_point") or f"mge_results_{source}"),
        )
    return MgeResultsImportAuditContext(
        source_filename=filename,
        actor_discord_id=actor_discord_id,
        event_id=event_id,
        event_mode=event_mode,
        source=source,
        entry_point=f"mge_results_{source}",
    )


def _optional_int(value: object | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _with_event(
    context: MgeResultsImportAuditContext,
    *,
    event_id: int,
    event_mode: str,
) -> MgeResultsImportAuditContext:
    return MgeResultsImportAuditContext(
        source_filename=context.source_filename,
        source_message_id=context.source_message_id,
        source_channel_id=context.source_channel_id,
        actor_discord_id=context.actor_discord_id,
        event_id=event_id,
        event_mode=event_mode,
        source=context.source,
        entry_point=context.entry_point,
    )


def _record_precheck_failure(
    audit_ref: Any,
    context: MgeResultsImportAuditContext,
    started,
    exc: Exception,
) -> None:
    record_mge_results_audit_phase(
        audit_ref,
        phase_name=MGE_RESULTS_AUDIT_PRECHECK_PHASE,
        phase_status="failed",
        started_at_utc=started.replace(tzinfo=None),
        duration_ms=audit_duration_ms(started),
        error_type=type(exc).__name__,
        error_text=str(exc),
        details=mge_results_audit_details(context, error=str(exc)),
    )
    fail_mge_results_audit_batch(
        audit_ref,
        error_type=type(exc).__name__,
        error_text=str(exc),
        details=mge_results_audit_details(context, error=str(exc)),
    )


def _audit_result_fields(audit_ref: Any) -> dict[str, Any]:
    return {
        "import_audit_batch_id": (
            getattr(audit_ref, "import_audit_batch_id", None) if audit_ref else None
        ),
        "import_audit_correlation_id": (
            getattr(audit_ref, "correlation_id", None) if audit_ref else None
        ),
    }


def import_results_auto(
    content: bytes,
    filename: str,
    actor_discord_id: int | None,
    audit_context: MgeResultsImportAuditContext | None = None,
) -> dict[str, Any]:
    context = _audit_context(
        source="auto",
        filename=filename,
        actor_discord_id=actor_discord_id,
        audit_context=audit_context,
    )
    file_hash = sha256_hex(content)
    audit_ref = start_mge_results_audit_batch(
        context, content, source_file_hash_sha256=file_hash
    )
    audit_terminal_recorded = False
    rows_parsed: int | None = None
    inserted: int | None = None
    import_id: int | None = None

    precheck_started = utcnow()
    try:
        event_id = mge_results_dal.get_last_completed_event_id()
        if event_id is None:
            raise ValueError("No completed MGE event found for auto import.")

        event_mode = mge_results_dal.get_event_mode(event_id)
        context = _with_event(context, event_id=event_id, event_mode=event_mode)

        if mge_results_dal.has_successful_import_for_event_filehash(event_id, file_hash):
            duplicate_reason = "same_file_hash"
            details = mge_results_audit_details(
                context,
                duplicate_reason=duplicate_reason,
            )
            record_mge_results_audit_phase(
                audit_ref,
                phase_name=MGE_RESULTS_AUDIT_PRECHECK_PHASE,
                phase_status="duplicate",
                started_at_utc=precheck_started.replace(tzinfo=None),
                duration_ms=audit_duration_ms(precheck_started),
                details=details,
                set_batch_status="duplicate",
            )
            complete_mge_results_audit_batch(
                audit_ref,
                status="duplicate",
                details=details,
            )
            audit_terminal_recorded = True
            raise ValueError(
                "Duplicate import rejected: same file hash already imported for this event."
            )
        if mge_results_dal.has_successful_import_for_event(event_id):
            duplicate_reason = "event_already_completed_import"
            details = mge_results_audit_details(
                context,
                duplicate_reason=duplicate_reason,
            )
            record_mge_results_audit_phase(
                audit_ref,
                phase_name=MGE_RESULTS_AUDIT_PRECHECK_PHASE,
                phase_status="duplicate",
                started_at_utc=precheck_started.replace(tzinfo=None),
                duration_ms=audit_duration_ms(precheck_started),
                details=details,
                set_batch_status="duplicate",
            )
            complete_mge_results_audit_batch(
                audit_ref,
                status="duplicate",
                details=details,
            )
            audit_terminal_recorded = True
            raise ValueError(
                "Duplicate import rejected: this event already has a completed import (auto mode)."
            )

        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_PRECHECK_PHASE,
            phase_status="completed",
            started_at_utc=precheck_started.replace(tzinfo=None),
            duration_ms=audit_duration_ms(precheck_started),
            details=mge_results_audit_details(context),
        )
    except ValueError as exc:
        if not audit_terminal_recorded:
            _record_precheck_failure(audit_ref, context, precheck_started, exc)
            audit_terminal_recorded = True
        raise
    except Exception as exc:
        _record_precheck_failure(audit_ref, context, precheck_started, exc)
        audit_terminal_recorded = True
        raise

    parse_started = utcnow()
    try:
        parsed = parse_mge_results_xlsx(content, filename)
        rows_parsed = len(parsed)
        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_PARSE_PHASE,
            phase_status="completed",
            started_at_utc=parse_started.replace(tzinfo=None),
            rows_out=rows_parsed,
            duration_ms=audit_duration_ms(parse_started),
            details=mge_results_audit_details(context, rows_parsed=rows_parsed),
        )
    except Exception as exc:
        details = mge_results_audit_details(context, rows_parsed=0, error=str(exc))
        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_PARSE_PHASE,
            phase_status="failed",
            started_at_utc=parse_started.replace(tzinfo=None),
            rows_out=0,
            duration_ms=audit_duration_ms(parse_started),
            error_type=type(exc).__name__,
            error_text=str(exc),
            details=details,
        )
        fail_mge_results_audit_batch(
            audit_ref,
            error_type=type(exc).__name__,
            error_text=str(exc),
            rows_in_source=0,
            rows_staged=0,
            rows_written=0,
            rows_skipped=0,
            details=details,
        )
        raise

    payload_rows = [asdict(r) for r in parsed]

    ingest_started = utcnow()
    try:
        import_id = mge_results_dal.create_import_batch(
            event_id=event_id,
            event_mode=event_mode,
            source="auto",
            filename=filename,
            file_hash=file_hash,
            actor_discord_id=actor_discord_id,
        )
        inserted = mge_results_dal.replace_event_results(
            import_id, event_id, event_mode, payload_rows
        )
        mge_results_dal.mark_import_completed(import_id, inserted)
        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_INGEST_PHASE,
            phase_status="completed",
            started_at_utc=ingest_started.replace(tzinfo=None),
            rows_in=rows_parsed,
            rows_out=inserted,
            duration_ms=audit_duration_ms(ingest_started),
            details=mge_results_audit_details(
                context,
                import_id=import_id,
                rows_parsed=rows_parsed,
                rows_written=inserted,
            ),
            set_batch_status="staged",
        )

        report: dict[str, Any] = {}
        try:
            report = _build_import_report(event_id, event_mode)
        except Exception:
            logger.exception(
                "mge_import_report_generation_failed import_id=%s event_id=%s",
                import_id,
                event_id,
            )

        complete_mge_results_audit_batch(
            audit_ref,
            rows_in_source=rows_parsed,
            rows_staged=rows_parsed,
            rows_written=inserted,
            rows_skipped=0,
            external_batch_id=mge_results_external_batch_id(import_id),
            details=mge_results_audit_details(
                context,
                import_id=import_id,
                rows_parsed=rows_parsed,
                rows_written=inserted,
                report_type=report.get("type") if report else None,
            ),
        )
        audit_terminal_recorded = True

        return {
            "import_id": import_id,
            "event_id": event_id,
            "event_mode": event_mode,
            "rows": inserted,
            "report": report,
            **_audit_result_fields(audit_ref),
        }
    except Exception as e:
        try:
            if import_id is not None:
                mge_results_dal.mark_import_failed(import_id, str(e))
        except Exception:
            logger.exception("mark_import_failed_failed import_id=%s", import_id)
        if not audit_terminal_recorded:
            details = mge_results_audit_details(
                context,
                import_id=import_id,
                rows_parsed=rows_parsed,
                rows_written=inserted,
                error=str(e),
            )
            record_mge_results_audit_phase(
                audit_ref,
                phase_name=MGE_RESULTS_AUDIT_INGEST_PHASE,
                phase_status="failed",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=rows_parsed,
                rows_out=inserted,
                duration_ms=audit_duration_ms(ingest_started),
                error_type=type(e).__name__,
                error_text=str(e),
                details=details,
            )
            fail_mge_results_audit_batch(
                audit_ref,
                error_type=type(e).__name__,
                error_text=str(e),
                rows_in_source=rows_parsed,
                rows_staged=0 if import_id is not None else None,
                rows_written=inserted,
                rows_skipped=rows_parsed if inserted in (None, 0) else None,
                external_batch_id=(
                    mge_results_external_batch_id(import_id) if import_id is not None else None
                ),
                details=details,
            )
        raise


def import_results_manual(
    content: bytes,
    filename: str,
    event_id: int,
    actor_discord_id: int | None,
    force_overwrite: bool,
    audit_context: MgeResultsImportAuditContext | None = None,
) -> dict[str, Any]:
    context = _audit_context(
        source="manual",
        filename=filename,
        actor_discord_id=actor_discord_id,
        event_id=event_id,
        audit_context=audit_context,
    )
    file_hash = sha256_hex(content)
    audit_ref = start_mge_results_audit_batch(
        context, content, source_file_hash_sha256=file_hash
    )
    audit_terminal_recorded = False
    rows_parsed: int | None = None
    inserted: int | None = None
    import_id: int | None = None

    precheck_started = utcnow()
    try:
        # enforce completed-event-only manual import
        if not mge_results_dal.is_event_completed(event_id):
            raise ValueError(
                f"Event {event_id} is not completed. Manual results import is allowed only for completed events."
            )

        event_mode = mge_results_dal.get_event_mode(event_id)
        context = _with_event(context, event_id=event_id, event_mode=event_mode)

        has_any = mge_results_dal.has_successful_import_for_event(event_id)
        if has_any and not force_overwrite:
            details = mge_results_audit_details(context, overwrite_confirmed=False)
            record_mge_results_audit_phase(
                audit_ref,
                phase_name=MGE_RESULTS_AUDIT_PRECHECK_PHASE,
                phase_status="skipped",
                started_at_utc=precheck_started.replace(tzinfo=None),
                duration_ms=audit_duration_ms(precheck_started),
                details=details,
                set_batch_status="skipped",
            )
            complete_mge_results_audit_batch(
                audit_ref,
                status="skipped",
                details=details,
            )
            audit_terminal_recorded = True
            raise OverwriteConfirmationRequired("Overwrite confirmation required.")

        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_PRECHECK_PHASE,
            phase_status="completed",
            started_at_utc=precheck_started.replace(tzinfo=None),
            duration_ms=audit_duration_ms(precheck_started),
            details=mge_results_audit_details(
                context,
                overwrite_confirmed=bool(force_overwrite),
            ),
        )
    except OverwriteConfirmationRequired:
        raise
    except ValueError as exc:
        if not audit_terminal_recorded:
            _record_precheck_failure(audit_ref, context, precheck_started, exc)
            audit_terminal_recorded = True
        raise
    except Exception as exc:
        _record_precheck_failure(audit_ref, context, precheck_started, exc)
        audit_terminal_recorded = True
        raise

    parse_started = utcnow()
    try:
        parsed = parse_mge_results_xlsx(content, filename)
        rows_parsed = len(parsed)
        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_PARSE_PHASE,
            phase_status="completed",
            started_at_utc=parse_started.replace(tzinfo=None),
            rows_out=rows_parsed,
            duration_ms=audit_duration_ms(parse_started),
            details=mge_results_audit_details(context, rows_parsed=rows_parsed),
        )
    except Exception as exc:
        details = mge_results_audit_details(context, rows_parsed=0, error=str(exc))
        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_PARSE_PHASE,
            phase_status="failed",
            started_at_utc=parse_started.replace(tzinfo=None),
            rows_out=0,
            duration_ms=audit_duration_ms(parse_started),
            error_type=type(exc).__name__,
            error_text=str(exc),
            details=details,
        )
        fail_mge_results_audit_batch(
            audit_ref,
            error_type=type(exc).__name__,
            error_text=str(exc),
            rows_in_source=0,
            rows_staged=0,
            rows_written=0,
            rows_skipped=0,
            details=details,
        )
        raise

    payload_rows = [asdict(r) for r in parsed]

    ingest_started = utcnow()
    try:
        import_id = mge_results_dal.create_import_batch(
            event_id=event_id,
            event_mode=event_mode,
            source="manual",
            filename=filename,
            file_hash=file_hash,
            actor_discord_id=actor_discord_id,
        )
        inserted = mge_results_dal.replace_event_results(
            import_id, event_id, event_mode, payload_rows
        )
        mge_results_dal.mark_import_completed(import_id, inserted)
        record_mge_results_audit_phase(
            audit_ref,
            phase_name=MGE_RESULTS_AUDIT_INGEST_PHASE,
            phase_status="completed",
            started_at_utc=ingest_started.replace(tzinfo=None),
            rows_in=rows_parsed,
            rows_out=inserted,
            duration_ms=audit_duration_ms(ingest_started),
            details=mge_results_audit_details(
                context,
                import_id=import_id,
                rows_parsed=rows_parsed,
                rows_written=inserted,
            ),
            set_batch_status="staged",
        )
        report = _build_import_report(event_id, event_mode)
        complete_mge_results_audit_batch(
            audit_ref,
            rows_in_source=rows_parsed,
            rows_staged=rows_parsed,
            rows_written=inserted,
            rows_skipped=0,
            external_batch_id=mge_results_external_batch_id(import_id),
            details=mge_results_audit_details(
                context,
                import_id=import_id,
                rows_parsed=rows_parsed,
                rows_written=inserted,
                report_type=report.get("type") if report else None,
                overwrite_confirmed=bool(force_overwrite),
            ),
        )
        audit_terminal_recorded = True
        return {
            "import_id": import_id,
            "event_id": event_id,
            "event_mode": event_mode,
            "rows": inserted,
            "report": report,
            **_audit_result_fields(audit_ref),
        }
    except Exception as e:
        try:
            if import_id is not None:
                mge_results_dal.mark_import_failed(import_id, str(e))
        except Exception:
            logger.exception("mark_import_failed_failed import_id=%s", import_id)
        if not audit_terminal_recorded:
            details = mge_results_audit_details(
                context,
                import_id=import_id,
                rows_parsed=rows_parsed,
                rows_written=inserted,
                error=str(e),
            )
            record_mge_results_audit_phase(
                audit_ref,
                phase_name=MGE_RESULTS_AUDIT_INGEST_PHASE,
                phase_status="failed",
                started_at_utc=ingest_started.replace(tzinfo=None),
                rows_in=rows_parsed,
                rows_out=inserted,
                duration_ms=audit_duration_ms(ingest_started),
                error_type=type(e).__name__,
                error_text=str(e),
                details=details,
            )
            fail_mge_results_audit_batch(
                audit_ref,
                error_type=type(e).__name__,
                error_text=str(e),
                rows_in_source=rows_parsed,
                rows_staged=0 if import_id is not None else None,
                rows_written=inserted,
                rows_skipped=rows_parsed if inserted in (None, 0) else None,
                external_batch_id=(
                    mge_results_external_batch_id(import_id) if import_id is not None else None
                ),
                details=details,
            )
        raise
