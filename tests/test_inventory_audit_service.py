from datetime import UTC, datetime

import pytest

from inventory import audit_service
from inventory.models import InventoryAuditStatus, InventoryImportType


def test_parse_audit_filters():
    assert audit_service.parse_audit_status("rejected") == InventoryAuditStatus.REJECTED
    assert audit_service.parse_audit_import_type("Resources") == InventoryImportType.RESOURCES
    assert audit_service.parse_audit_import_type("All") is None


@pytest.mark.asyncio
async def test_fetch_inventory_audit_maps_debug_reference(monkeypatch):
    def _rows(**kwargs):
        assert kwargs["status"] == "failed"
        return [
            {
                "ImportBatchID": 9,
                "GovernorID": 111,
                "DiscordUserID": 42,
                "ImportType": "unknown",
                "FlowType": "upload_first",
                "Status": "failed",
                "CreatedAtUtc": datetime.now(UTC),
                "ApprovedAtUtc": None,
                "RejectedAtUtc": None,
                "ConfidenceScore": 0.12,
                "VisionModel": "test-model",
                "FallbackUsed": False,
                "AdminDebugChannelID": 555,
                "AdminDebugMessageID": 777,
                "WarningJson": ["low confidence"],
                "DetectedJson": {"detected_image_type": "unknown"},
                "CorrectedJson": None,
                "FinalJson": None,
                "ErrorJson": {"error": "Analysis failed."},
            }
        ]

    monkeypatch.setattr(audit_service.inventory_audit_dal, "fetch_import_audit_rows", _rows)

    records = await audit_service.fetch_inventory_audit(status=InventoryAuditStatus.FAILED)

    assert records[0].debug_reference == "<#555> / `777`"
    assert audit_service.summarize_json_comparison(records[0]) == "detected, error"
