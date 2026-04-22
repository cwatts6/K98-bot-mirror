from __future__ import annotations

from dataclasses import asdict
import hashlib
import logging
from typing import Any

from mge.dal import mge_results_dal
from mge.mge_xlsx_parser import parse_mge_results_xlsx

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


def import_results_auto(
    content: bytes, filename: str, actor_discord_id: int | None
) -> dict[str, Any]:
    event_id = mge_results_dal.get_last_completed_event_id()
    if event_id is None:
        raise ValueError("No completed MGE event found for auto import.")

    event_mode = mge_results_dal.get_event_mode(event_id)
    file_hash = sha256_hex(content)

    if mge_results_dal.has_successful_import_for_event_filehash(event_id, file_hash):
        raise ValueError(
            "Duplicate import rejected: same file hash already imported for this event."
        )
    if mge_results_dal.has_successful_import_for_event(event_id):
        raise ValueError(
            "Duplicate import rejected: this event already has a completed import (auto mode)."
        )

    parsed = parse_mge_results_xlsx(content, filename)
    payload_rows = [asdict(r) for r in parsed]

    import_id = mge_results_dal.create_import_batch(
        event_id=event_id,
        event_mode=event_mode,
        source="auto",
        filename=filename,
        file_hash=file_hash,
        actor_discord_id=actor_discord_id,
    )

    try:
        inserted = mge_results_dal.replace_event_results(
            import_id, event_id, event_mode, payload_rows
        )
        mge_results_dal.mark_import_completed(import_id, inserted)

        report: dict[str, Any] = {}
        try:
            report = _build_import_report(event_id, event_mode)
        except Exception:
            logger.exception(
                "mge_import_report_generation_failed import_id=%s event_id=%s",
                import_id,
                event_id,
            )

        return {
            "import_id": import_id,
            "event_id": event_id,
            "event_mode": event_mode,
            "rows": inserted,
            "report": report,
        }
    except Exception as e:
        try:
            mge_results_dal.mark_import_failed(import_id, str(e))
        except Exception:
            logger.exception("mark_import_failed_failed import_id=%s", import_id)
        raise


def import_results_manual(
    content: bytes,
    filename: str,
    event_id: int,
    actor_discord_id: int | None,
    force_overwrite: bool,
) -> dict[str, Any]:
    # enforce completed-event-only manual import
    if not mge_results_dal.is_event_completed(event_id):
        raise ValueError(
            f"Event {event_id} is not completed. Manual results import is allowed only for completed events."
        )

    event_mode = mge_results_dal.get_event_mode(event_id)
    file_hash = sha256_hex(content)

    has_any = mge_results_dal.has_successful_import_for_event(event_id)
    if has_any and not force_overwrite:
        raise OverwriteConfirmationRequired("Overwrite confirmation required.")

    parsed = parse_mge_results_xlsx(content, filename)
    payload_rows = [asdict(r) for r in parsed]

    import_id = mge_results_dal.create_import_batch(
        event_id=event_id,
        event_mode=event_mode,
        source="manual",
        filename=filename,
        file_hash=file_hash,
        actor_discord_id=actor_discord_id,
    )

    try:
        inserted = mge_results_dal.replace_event_results(
            import_id, event_id, event_mode, payload_rows
        )
        mge_results_dal.mark_import_completed(import_id, inserted)
        report = _build_import_report(event_id, event_mode)
        return {
            "import_id": import_id,
            "event_id": event_id,
            "event_mode": event_mode,
            "rows": inserted,
            "report": report,
        }
    except Exception as e:
        try:
            mge_results_dal.mark_import_failed(import_id, str(e))
        except Exception:
            logger.exception("mark_import_failed_failed import_id=%s", import_id)
        raise
