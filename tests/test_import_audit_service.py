from datetime import UTC, datetime, timedelta
import json

from services import import_audit_service
from stats.dal.import_audit_dal import ImportAuditBatchRef


def test_start_batch_best_effort_serializes_details():
    seen = {}

    def writer(**kwargs):
        seen.update(kwargs)
        return ImportAuditBatchRef(
            import_audit_batch_id=12,
            correlation_id="11111111-1111-1111-1111-111111111111",
        )

    ref = import_audit_service.start_batch_best_effort(
        import_kind="fallback",
        source_filename="stats.xlsx",
        details={"name": "ç¾©VÃ¬perç¾©"},
        writer=writer,
    )

    assert ref and ref.import_audit_batch_id == 12
    assert json.loads(seen["details_json"]) == {"name": "ç¾©VÃ¬perç¾©"}


def test_start_batch_best_effort_swallows_writer_failure():
    def writer(**kwargs):
        raise RuntimeError("audit unavailable")

    assert (
        import_audit_service.start_batch_best_effort(
            import_kind="fallback",
            writer=writer,
        )
        is None
    )


def test_record_phase_best_effort_truncates_error_fields():
    seen = {}

    def writer(**kwargs):
        seen.update(kwargs)
        return 5

    phase_id = import_audit_service.record_phase_best_effort(
        ImportAuditBatchRef(12, "cid"),
        phase_name="fallback_update_all2",
        phase_status="failed",
        error_type="x" * 200,
        error_text="y" * 3000,
        details={"ok": False},
        writer=writer,
    )

    assert phase_id == 5
    assert len(seen["error_type"]) == import_audit_service.MAX_ERROR_TYPE_LENGTH
    assert len(seen["error_text"]) == import_audit_service.MAX_ERROR_TEXT_LENGTH
    assert json.loads(seen["details_json"]) == {"ok": False}


def test_record_phase_best_effort_clamps_completed_before_started():
    seen = {}
    started = datetime(2026, 7, 1, 12, 0, 0)
    completed = started - timedelta(milliseconds=3)

    def writer(**kwargs):
        seen.update(kwargs)
        return 5

    phase_id = import_audit_service.record_phase_best_effort(
        ImportAuditBatchRef(12, "cid"),
        phase_name="kvk_all_schema_parse",
        phase_status="completed",
        started_at_utc=started,
        completed_at_utc=completed,
        duration_ms=0,
        writer=writer,
    )

    assert phase_id == 5
    assert seen["started_at_utc"] == started
    assert seen["completed_at_utc"] == started
    assert seen["duration_ms"] == 0


def test_record_phase_best_effort_preserves_valid_completed_timestamp():
    seen = {}
    started = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)
    completed = started + timedelta(milliseconds=7)

    def writer(**kwargs):
        seen.update(kwargs)
        return 5

    import_audit_service.record_phase_best_effort(
        ImportAuditBatchRef(12, "cid"),
        phase_name="rally_forts_daily_ingest",
        phase_status="completed",
        started_at_utc=started,
        completed_at_utc=completed,
        writer=writer,
    )

    assert seen["completed_at_utc"] == completed


def test_record_phase_best_effort_clamps_mixed_timezone_awareness():
    seen = {}
    started = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)
    completed = datetime(2026, 7, 1, 11, 59, 59, 997000)

    def writer(**kwargs):
        seen.update(kwargs)
        return 5

    phase_id = import_audit_service.record_phase_best_effort(
        ImportAuditBatchRef(12, "cid"),
        phase_name="weekly_activity_sql_ingest",
        phase_status="completed",
        started_at_utc=started,
        completed_at_utc=completed,
        writer=writer,
    )

    assert phase_id == 5
    assert seen["completed_at_utc"] == started


def test_fetch_batch_by_external_id_best_effort_passes_lookup_fields():
    seen = {}

    def reader(**kwargs):
        seen.update(kwargs)
        return ImportAuditBatchRef(44, "cid")

    ref = import_audit_service.fetch_batch_by_external_id_best_effort(
        import_kind="inventory",
        external_batch_table="dbo.InventoryImportBatch",
        external_batch_id="123",
        reader=reader,
    )

    assert ref == ImportAuditBatchRef(44, "cid")
    assert seen == {
        "import_kind": "inventory",
        "external_batch_table": "dbo.InventoryImportBatch",
        "external_batch_id": "123",
    }


def test_fetch_batch_by_external_id_best_effort_swallows_reader_failure():
    def reader(**kwargs):
        raise RuntimeError("audit unavailable")

    assert (
        import_audit_service.fetch_batch_by_external_id_best_effort(
            import_kind="inventory",
            external_batch_table="dbo.InventoryImportBatch",
            external_batch_id="123",
            reader=reader,
        )
        is None
    )


def test_complete_and_fail_best_effort_ignore_missing_batch_ref():
    assert import_audit_service.complete_batch_best_effort(None) is False
    assert import_audit_service.fail_batch_best_effort(None) is False


def test_complete_and_fail_best_effort_pass_rows_in_source():
    seen = []

    def writer(**kwargs):
        seen.append(kwargs)

    assert (
        import_audit_service.complete_batch_best_effort(
            12,
            rows_in_source=3,
            rows_staged=2,
            writer=writer,
        )
        is True
    )
    assert (
        import_audit_service.fail_batch_best_effort(
            12,
            rows_in_source=4,
            rows_skipped=4,
            writer=writer,
        )
        is True
    )

    assert seen[0]["rows_in_source"] == 3
    assert seen[1]["rows_in_source"] == 4


def test_complete_and_fail_best_effort_swallow_writer_failure():
    def writer(**kwargs):
        raise RuntimeError("audit unavailable")

    assert import_audit_service.complete_batch_best_effort(12, writer=writer) is False
    assert import_audit_service.fail_batch_best_effort(12, writer=writer) is False
