import pytest

from inventory import inventory_service
from inventory.models import InventoryImagePayload, InventoryImportStatus, InventoryImportType

pytestmark = pytest.mark.asyncio


class _VisionResult:
    def __init__(self):
        self.ok = True
        self.detected_image_type = "resources"
        self.confidence_score = 0.93
        self.warnings = []
        self.model = "test-model"
        self.prompt_version = "inventory_vision_v1"
        self.fallback_used = False
        self.error = None
        self.values = {
            "resources": {
                "food": {"from_items_value": 1, "total_resources_value": 2},
                "wood": {"from_items_value": 3, "total_resources_value": 4},
                "stone": {"from_items_value": 5, "total_resources_value": 6},
                "gold": {"from_items_value": 7, "total_resources_value": 8},
            }
        }
        self.raw_json = {"detected_image_type": "resources", "values": self.values}


class _VisionClient:
    def __init__(self):
        self.calls = []

    async def analyse_image(
        self, image_bytes, *, filename=None, content_type=None, import_type_hint=None
    ):
        self.calls.append(
            {
                "image_bytes": image_bytes,
                "filename": filename,
                "content_type": content_type,
                "import_type_hint": import_type_hint,
            }
        )
        return _VisionResult()


class _LowConfidenceVisionClient(_VisionClient):
    async def analyse_image(
        self, image_bytes, *, filename=None, content_type=None, import_type_hint=None
    ):
        result = _VisionResult()
        result.ok = True
        result.detected_image_type = "unknown"
        result.confidence_score = 0.12
        result.error = "not an inventory screenshot"
        return result


async def test_analyse_inventory_image_does_not_send_type_hint(monkeypatch):
    captured = {}

    def _update(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(inventory_service.inventory_dal, "update_batch_analysis", _update)

    client = _VisionClient()
    summary = await inventory_service.analyse_inventory_image(
        import_batch_id=42,
        payload=InventoryImagePayload(
            image_bytes=b"img",
            filename="rss.png",
            content_type="image/png",
            source_message_id=10,
            source_channel_id=20,
            image_attachment_url="https://cdn.test/rss.png",
        ),
        vision_client=client,
    )

    assert client.calls[0]["import_type_hint"] is None
    assert summary.import_type == InventoryImportType.RESOURCES
    assert captured["status"] == InventoryImportStatus.ANALYSED
    assert captured["source_message_id"] == 10
    assert captured["image_attachment_url"] == "https://cdn.test/rss.png"


async def test_get_registered_governors_for_user_maps_registry(monkeypatch):
    monkeypatch.setattr(
        inventory_service,
        "load_registry",
        lambda: {
            "123": {
                "accounts": {
                    "Main": {"GovernorID": "111", "GovernorName": "MainGov"},
                    "Alt 1": {"GovernorID": "222", "GovernorName": "AltGov"},
                }
            }
        },
    )

    governors = await inventory_service.get_registered_governors_for_user(123)

    assert [item.governor_id for item in governors] == [111, 222]
    assert governors[0].account_type == "Main"


async def test_analyse_inventory_image_marks_random_image_failed(monkeypatch):
    captured = {}

    def _update(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(inventory_service.inventory_dal, "update_batch_analysis", _update)

    summary = await inventory_service.analyse_inventory_image(
        import_batch_id=42,
        payload=InventoryImagePayload(
            image_bytes=b"cat",
            filename="cat.png",
            content_type="image/png",
        ),
        vision_client=_LowConfidenceVisionClient(),
    )

    assert summary.import_type == InventoryImportType.UNKNOWN
    assert captured["status"] == InventoryImportStatus.FAILED


async def test_approve_import_blocks_duplicate_same_day_for_non_admin(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "has_approved_import_today",
        lambda governor_id, import_type: True,
    )

    summary = inventory_service._summary_from_vision_result(_VisionResult())
    with pytest.raises(ValueError, match="already has an approved import"):
        await inventory_service.approve_import(
            import_batch_id=42,
            governor_id=111,
            summary=summary,
        )


async def test_approve_import_preserves_admin_same_day_override(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "has_approved_import_today",
        lambda governor_id, import_type: True,
    )
    captured = {}

    def _approve_batch(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(inventory_service.inventory_dal, "approve_batch", _approve_batch)

    summary = inventory_service._summary_from_vision_result(_VisionResult())
    await inventory_service.approve_import(
        import_batch_id=42,
        governor_id=111,
        summary=summary,
        is_admin=True,
    )

    assert captured["import_batch_id"] == 42


async def test_speedup_digit_loss_anomaly_adds_warning():
    result = _VisionResult()
    result.detected_image_type = "speedups"
    result.values = {
        "speedups": {
            "building": {"total_minutes": 144_000, "total_hours": 2400, "total_days_decimal": 100},
            "research": {
                "total_minutes": 150_000,
                "total_hours": 2500,
                "total_days_decimal": 104.1667,
            },
            "training": {
                "total_minutes": 160_000,
                "total_hours": 2666.6667,
                "total_days_decimal": 111.1111,
            },
            "healing": {
                "total_minutes": 72_757,
                "total_hours": 1212.6167,
                "total_days_decimal": 50.5257,
            },
            "universal": {
                "total_minutes": 500_000,
                "total_hours": 8333.3333,
                "total_days_decimal": 347.2222,
            },
        }
    }

    summary = inventory_service._summary_from_vision_result(result)

    assert any("Healing" in warning and "missing digit" in warning for warning in summary.warnings)
