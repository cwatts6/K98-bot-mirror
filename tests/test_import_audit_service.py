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
