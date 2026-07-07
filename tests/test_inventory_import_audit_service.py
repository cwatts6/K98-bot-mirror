from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from inventory.models import InventoryAnalysisSummary, InventoryImportType
from services import inventory_import_audit_service as audit
from stats.dal.import_audit_dal import ImportAuditBatchRef


def test_inventory_external_batch_id_uses_import_batch_id():
    assert audit.inventory_external_batch_id(42) == "42"


def test_audit_duration_ms_accepts_naive_utc_timestamp():
    started = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)

    assert audit.audit_duration_ms(started) >= 0


def test_inventory_context_maps_command_source_type():
    context = audit.InventoryImportAuditContext(
        import_batch_id=7,
        governor_id=111,
        flow_type="command",
    )

    assert context.source_type == audit.INVENTORY_AUDIT_COMMAND_SOURCE_TYPE


def test_inventory_row_count_counts_resource_speedup_and_material_rows():
    assert (
        audit.inventory_row_count(
            InventoryImportType.RESOURCES,
            {"resources": {"food": {}, "wood": {}, "stone": {}, "gold": {}}},
        )
        == 4
    )
    assert (
        audit.inventory_row_count(
            InventoryImportType.SPEEDUPS,
            {"speedups": {"building": {}, "research": {}, "training": {}}},
        )
        == 3
    )
    assert (
        audit.inventory_row_count(
            InventoryImportType.MATERIALS,
            {"materials": {"animal_bone": {"legendary": 1}, "leather": {"epic": 2}}},
        )
        == 2
    )


def test_image_count_from_material_summary_uses_screenshot_count():
    summary = InventoryAnalysisSummary(
        ok=True,
        import_type=InventoryImportType.MATERIALS,
        raw_json={"screenshot_count": 3},
    )

    assert audit.image_count_from_summary(summary) == 3


@pytest.mark.asyncio
async def test_start_inventory_audit_batch_populates_generic_taxonomy(monkeypatch):
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

    context = audit.InventoryImportAuditContext(
        import_batch_id=77,
        governor_id=111,
        flow_type="upload_first",
        source_filename="inventory.png",
        source_message_id=123,
        source_channel_id=456,
        actor_discord_id=789,
    )

    ref = await audit.start_inventory_audit_batch(
        context=context,
        image_bytes=b"inventory image",
        audit_runner=inline_runner,
    )

    assert ref == ImportAuditBatchRef(12, "cid")
    assert seen["import_kind"] == audit.INVENTORY_AUDIT_IMPORT_KIND
    assert seen["source_type"] == audit.INVENTORY_AUDIT_UPLOAD_SOURCE_TYPE
    assert seen["source_filename"] == "inventory.png"
    assert seen["source_message_id"] == 123
    assert seen["source_channel_id"] == 456
    assert seen["actor_discord_id"] == 789
    assert seen["external_batch_table"] == audit.INVENTORY_AUDIT_EXTERNAL_TABLE
    assert seen["external_batch_id"] == "77"
    assert len(seen["source_file_hash_sha256"]) == 64
    assert seen["details"]["import_batch_id"] == 77
    assert seen["details"]["governor_id"] == 111


@pytest.mark.asyncio
async def test_fetch_inventory_audit_batch_uses_external_correlation(monkeypatch):
    seen = {}

    def fake_fetch(**kwargs):
        seen.update(kwargs)
        return ImportAuditBatchRef(33, "cid")

    async def inline_runner(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(
        audit.import_audit_service,
        "fetch_batch_by_external_id_best_effort",
        fake_fetch,
    )

    ref = await audit.fetch_inventory_audit_batch(import_batch_id=77, audit_runner=inline_runner)

    assert ref == ImportAuditBatchRef(33, "cid")
    assert seen == {
        "import_kind": audit.INVENTORY_AUDIT_IMPORT_KIND,
        "external_batch_table": audit.INVENTORY_AUDIT_EXTERNAL_TABLE,
        "external_batch_id": "77",
    }


@pytest.mark.asyncio
async def test_complete_inventory_audit_batch_uses_cancelled_status(monkeypatch):
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

    await audit.complete_inventory_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        status="cancelled",
        rows_in_source=1,
        rows_written=0,
        rows_skipped=1,
        audit_runner=inline_runner,
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["status"] == "cancelled"
    assert "external_batch_table" not in seen
    assert "external_batch_id" not in seen
    assert seen["rows_skipped"] == 1


@pytest.mark.asyncio
async def test_fail_inventory_audit_batch_preserves_existing_external_correlation(monkeypatch):
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

    await audit.fail_inventory_audit_batch(
        ImportAuditBatchRef(12, "cid"),
        status="failed",
        error_type="InventoryAnalysisFailed",
        error_text="analysis failed",
        rows_in_source=1,
        rows_written=0,
        rows_skipped=1,
        audit_runner=inline_runner,
    )

    assert seen["batch_ref"] == ImportAuditBatchRef(12, "cid")
    assert seen["status"] == "failed"
    assert seen["error_type"] == "InventoryAnalysisFailed"
    assert "external_batch_table" not in seen
    assert "external_batch_id" not in seen
    assert seen["rows_skipped"] == 1
