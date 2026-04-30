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
