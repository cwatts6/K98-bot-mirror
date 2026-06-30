from __future__ import annotations

from datetime import UTC, datetime, timedelta

from services import mge_results_import_audit_service as audit
from stats.dal.import_audit_dal import ImportAuditBatchRef


def test_mge_results_external_batch_id_uses_import_id():
    assert audit.mge_results_external_batch_id(77) == "77"


def test_audit_duration_ms_accepts_naive_utc_timestamp():
    started = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


def test_audit_duration_ms_accepts_aware_utc_timestamp():
    started = datetime.now(UTC) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


def test_start_mge_results_audit_batch_populates_generic_taxonomy(monkeypatch):
    seen = {}

    def fake_start_batch_best_effort(**kwargs):
        seen.update(kwargs)
        return ImportAuditBatchRef(12, "cid")

    monkeypatch.setattr(
        audit.import_audit_service,
        "start_batch_best_effort",
        fake_start_batch_best_effort,
    )

    context = audit.MgeResultsImportAuditContext(
        source_filename="mge_rankings_kd1198_20260311.xlsx",
        source_message_id=123,
        source_channel_id=456,
        actor_discord_id=789,
    )

    ref = audit.start_mge_results_audit_batch(context, b"mge workbook")

    assert ref == ImportAuditBatchRef(12, "cid")
    assert seen["import_kind"] == audit.MGE_RESULTS_AUDIT_IMPORT_KIND
    assert seen["source_type"] == audit.MGE_RESULTS_AUDIT_SOURCE_TYPE
    assert seen["source_filename"] == "mge_rankings_kd1198_20260311.xlsx"
    assert seen["source_message_id"] == 123
    assert seen["source_channel_id"] == 456
    assert seen["actor_discord_id"] == 789
    assert len(seen["source_file_hash_sha256"]) == 64
    assert seen["details"] == {
        "entry_point": "mge_results_upload",
        "source": "auto",
    }


def test_complete_mge_results_audit_batch_sets_mge_external_table(monkeypatch):
    seen = {}

    def fake_complete_batch_best_effort(batch_ref, **kwargs):
        seen["batch_ref"] = batch_ref
        seen.update(kwargs)

    monkeypatch.setattr(
        audit.import_audit_service,
        "complete_batch_best_effort",
        fake_complete_batch_best_effort,
    )

    audit.complete_mge_results_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        rows_in_source=4,
        rows_staged=4,
        rows_written=4,
        external_batch_id="77",
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] == audit.MGE_RESULTS_AUDIT_EXTERNAL_TABLE
    assert seen["external_batch_id"] == "77"
    assert seen["rows_in_source"] == 4
    assert seen["rows_staged"] == 4
    assert seen["rows_written"] == 4


def test_fail_mge_results_audit_batch_leaves_uncorrelated_without_import_id(monkeypatch):
    seen = {}

    def fake_fail_batch_best_effort(batch_ref, **kwargs):
        seen["batch_ref"] = batch_ref
        seen.update(kwargs)

    monkeypatch.setattr(
        audit.import_audit_service,
        "fail_batch_best_effort",
        fake_fail_batch_best_effort,
    )

    audit.fail_mge_results_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        error_type="ValueError",
        error_text="bad workbook",
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] is None
    assert seen["external_batch_id"] is None
    assert seen["error_type"] == "ValueError"
    assert seen["error_text"] == "bad workbook"
