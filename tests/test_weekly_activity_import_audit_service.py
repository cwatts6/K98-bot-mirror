from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services import weekly_activity_import_audit_service as audit
from stats.dal.import_audit_dal import ImportAuditBatchRef


def test_weekly_activity_external_batch_id_uses_snapshot_id():
    assert audit.weekly_activity_external_batch_id(42) == "42"


def test_audit_duration_ms_accepts_naive_utc_timestamp():
    started = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


def test_audit_duration_ms_accepts_aware_utc_timestamp():
    started = datetime.now(UTC) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


@pytest.mark.asyncio
async def test_start_weekly_activity_audit_batch_populates_generic_taxonomy(monkeypatch):
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

    context = audit.WeeklyActivityImportAuditContext(
        source_filename="1198_alliance_activity.xlsx",
        source_message_id=123,
        source_channel_id=456,
        actor_discord_id=789,
    )

    ref = await audit.start_weekly_activity_audit_batch(
        context=context,
        xlsx_bytes=b"weekly activity workbook",
        audit_runner=inline_runner,
    )

    assert ref == ImportAuditBatchRef(12, "cid")
    assert seen["import_kind"] == audit.WEEKLY_ACTIVITY_AUDIT_IMPORT_KIND
    assert seen["source_type"] == audit.WEEKLY_ACTIVITY_AUDIT_SOURCE_TYPE
    assert seen["source_filename"] == "1198_alliance_activity.xlsx"
    assert seen["source_message_id"] == 123
    assert seen["source_channel_id"] == 456
    assert seen["actor_discord_id"] == 789
    assert len(seen["source_file_hash_sha256"]) == 64
    assert seen["details"] == {"entry_point": "weekly_activity_upload"}


@pytest.mark.asyncio
async def test_complete_weekly_activity_audit_batch_sets_snapshot_external_table(monkeypatch):
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

    await audit.complete_weekly_activity_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        rows_in_source=4,
        rows_staged=4,
        rows_written=4,
        external_batch_id="42",
        audit_runner=inline_runner,
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] == audit.WEEKLY_ACTIVITY_AUDIT_EXTERNAL_TABLE
    assert seen["external_batch_id"] == "42"
    assert seen["rows_in_source"] == 4
    assert seen["rows_staged"] == 4
    assert seen["rows_written"] == 4


@pytest.mark.asyncio
async def test_fail_weekly_activity_audit_batch_leaves_uncorrelated_without_snapshot(monkeypatch):
    seen = {}

    def fake_fail_batch_best_effort(batch_ref, **kwargs):
        seen["batch_ref"] = batch_ref
        seen.update(kwargs)

    async def inline_runner(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(
        audit.import_audit_service,
        "fail_batch_best_effort",
        fake_fail_batch_best_effort,
    )

    await audit.fail_weekly_activity_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        error_type="ValueError",
        error_text="bad workbook",
        audit_runner=inline_runner,
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["external_batch_table"] is None
    assert seen["external_batch_id"] is None
    assert seen["error_type"] == "ValueError"
    assert seen["error_text"] == "bad workbook"
