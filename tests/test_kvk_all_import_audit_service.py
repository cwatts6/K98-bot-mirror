from __future__ import annotations

import hashlib

import pytest

from services import kvk_all_import_audit_service as audit
from stats.dal.import_audit_dal import ImportAuditBatchRef


@pytest.mark.asyncio
async def test_start_kvk_all_audit_batch_passes_metadata_and_hash(monkeypatch):
    seen = {}

    def fake_start_batch_best_effort(**kwargs):
        seen.update(kwargs)
        return ImportAuditBatchRef(12, "cid")

    monkeypatch.setattr(
        audit.import_audit_service,
        "start_batch_best_effort",
        fake_start_batch_best_effort,
    )
    context = audit.KvkAllImportAuditContext(
        source_filename="kvk.xlsx",
        source_type="discord_upload_xlsx",
        source_message_id=123,
        source_channel_id=456,
        actor_discord_id=789,
    )

    ref = await audit.start_kvk_all_audit_batch(context=context, content=b"abc")

    assert ref == ImportAuditBatchRef(12, "cid")
    assert seen["import_kind"] == audit.KVK_ALL_AUDIT_IMPORT_KIND
    assert seen["source_type"] == "discord_upload_xlsx"
    assert seen["source_filename"] == "kvk.xlsx"
    assert seen["source_file_hash_sha256"] == hashlib.sha256(b"abc").hexdigest()
    assert seen["source_message_id"] == 123
    assert seen["source_channel_id"] == 456
    assert seen["actor_discord_id"] == 789
    assert seen["details"] == {"entry_point": "kvk_all_upload"}


@pytest.mark.asyncio
async def test_complete_kvk_all_audit_batch_correlates_kvk_scan(monkeypatch):
    seen = {}

    def fake_complete_batch_best_effort(batch_ref, **kwargs):
        seen["batch_ref"] = batch_ref
        seen.update(kwargs)
        return True

    monkeypatch.setattr(
        audit.import_audit_service,
        "complete_batch_best_effort",
        fake_complete_batch_best_effort,
    )

    await audit.complete_kvk_all_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        rows_in_source=7,
        rows_staged=7,
        rows_written=7,
        rows_skipped=0,
        external_batch_id=audit.kvk_all_external_batch_id(15, 92),
        details={"ok": True},
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] == audit.KVK_ALL_AUDIT_EXTERNAL_TABLE
    assert seen["external_batch_id"] == "15:92"
    assert seen["rows_in_source"] == 7
    assert seen["rows_written"] == 7
    assert seen["details"] == {"ok": True}


@pytest.mark.asyncio
async def test_fail_kvk_all_audit_batch_can_correlate_diagnostic(monkeypatch):
    seen = {}

    def fake_fail_batch_best_effort(batch_ref, **kwargs):
        seen["batch_ref"] = batch_ref
        seen.update(kwargs)
        return True

    monkeypatch.setattr(
        audit.import_audit_service,
        "fail_batch_best_effort",
        fake_fail_batch_best_effort,
    )

    await audit.fail_kvk_all_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        error_type="KvkDetailsTimestampRejected",
        error_text="outside KVK_Details",
        rows_staged=3,
        rows_written=0,
        rows_skipped=3,
        external_batch_table=audit.KVK_ALL_AUDIT_DIAGNOSTIC_TABLE,
        external_batch_id=audit.kvk_all_diagnostic_external_batch_id(44),
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] == audit.KVK_ALL_AUDIT_DIAGNOSTIC_TABLE
    assert seen["external_batch_id"] == "44"
    assert seen["error_type"] == "KvkDetailsTimestampRejected"
    assert seen["rows_skipped"] == 3


def test_kvk_all_source_type_preserves_supported_extensions():
    assert audit.kvk_all_source_type("scan.xlsx") == "discord_upload_xlsx"
    assert audit.kvk_all_source_type("scan.xls") == "discord_upload_xls"
    assert audit.kvk_all_source_type("scan.csv") == "discord_upload_csv"
