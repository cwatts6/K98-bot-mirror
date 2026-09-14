from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services import prekvk_import_audit_service as audit
from stats.dal.import_audit_dal import ImportAuditBatchRef


def test_prekvk_scan_external_batch_id_uses_kvk_and_scan_id():
    assert audit.prekvk_scan_external_batch_id(15, 9) == "15:9"


def test_audit_duration_ms_accepts_naive_utc_timestamp():
    started = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


def test_audit_duration_ms_accepts_aware_utc_timestamp():
    started = datetime.now(UTC) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


@pytest.mark.asyncio
async def test_start_prekvk_audit_batch_populates_generic_taxonomy(monkeypatch):
    seen = {}

    def fake_start_batch_best_effort(**kwargs):
        seen.update(kwargs)
        return ImportAuditBatchRef(12, "cid")

    async def inline_runner(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(
        audit.import_audit_service,
        "start_batch_best_effort",
        fake_start_batch_best_effort,
    )

    context = audit.PreKvkImportAuditContext(
        source_filename="1198_prekvk.xlsx",
        source_message_id=123,
        source_channel_id=456,
        actor_discord_id=789,
        kvk_no=15,
    )

    ref = await audit.start_prekvk_audit_batch(
        context=context,
        xlsx_bytes=b"prekvk workbook",
        audit_runner=inline_runner,
    )

    assert ref == ImportAuditBatchRef(12, "cid")
    assert seen["import_kind"] == audit.PREKVK_AUDIT_IMPORT_KIND
    assert seen["source_type"] == audit.PREKVK_AUDIT_SOURCE_TYPE
    assert seen["source_filename"] == "1198_prekvk.xlsx"
    assert seen["source_message_id"] == 123
    assert seen["source_channel_id"] == 456
    assert seen["actor_discord_id"] == 789
    assert len(seen["source_file_hash_sha256"]) == 64
    assert seen["details"] == {"entry_point": "prekvk_upload", "kvk_no": 15}


@pytest.mark.asyncio
async def test_complete_prekvk_audit_batch_forwards_external_table(monkeypatch):
    seen = {}

    def fake_complete_batch_best_effort(batch_ref, **kwargs):
        seen["batch_ref"] = batch_ref
        seen.update(kwargs)

    async def inline_runner(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(
        audit.import_audit_service,
        "complete_batch_best_effort",
        fake_complete_batch_best_effort,
    )

    await audit.complete_prekvk_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        rows_in_source=4,
        rows_staged=4,
        rows_written=4,
        external_batch_table=audit.PREKVK_AUDIT_SCAN_TABLE,
        external_batch_id="15:9",
        audit_runner=inline_runner,
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] == audit.PREKVK_AUDIT_SCAN_TABLE
    assert seen["external_batch_id"] == "15:9"
    assert seen["rows_in_source"] == 4
    assert seen["rows_staged"] == 4
    assert seen["rows_written"] == 4
