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


class _MaterialVisionClient(_VisionClient):
    async def analyse_image(
        self, image_bytes, *, filename=None, content_type=None, import_type_hint=None
    ):
        result = _VisionResult()
        result.detected_image_type = "materials"
        result.values = {
            "materials": {
                "choice_chests": {
                    "normal": 0,
                    "advanced": 0,
                    "elite": 0,
                    "epic": 4,
                    "legendary": 1,
                },
                "animal_bone": {},
                "leather": {},
                "ebony": {},
                "iron_ore": {},
            }
        }
        result.raw_json = {
            "detected_image_type": "materials",
            "values": result.values,
            "warnings": [],
        }
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
    async def _summary(_discord_user_id):
        return inventory_service.governor_account_service.summarize_accounts(
            {
                "Main": {"GovernorID": "111", "GovernorName": "MainGov"},
                "Alt 1": {"GovernorID": "222", "GovernorName": "AltGov"},
            }
        )

    monkeypatch.setattr(
        inventory_service.governor_account_service,
        "get_account_summary_for_user",
        _summary,
    )

    governors = await inventory_service.get_registered_governors_for_user(123)

    assert [item.governor_id for item in governors] == [111, 222]
    assert governors[0].account_type == "Main"


async def test_get_registered_governors_preserves_legacy_name_fallbacks(monkeypatch):
    async def _summary(_discord_user_id):
        return inventory_service.governor_account_service.summarize_accounts(
            {
                "Main": {"GovernorID": "111", "Governor": "LegacyGov"},
                "Alt 1": {"GovernorID": "222", "GovernorName": ""},
            }
        )

    monkeypatch.setattr(
        inventory_service.governor_account_service,
        "get_account_summary_for_user",
        _summary,
    )

    governors = await inventory_service.get_registered_governors_for_user(123)

    assert governors[0].governor_name == "LegacyGov"
    assert governors[1].governor_name == "222"


async def test_user_can_import_for_governor_uses_shared_registered_governors(monkeypatch):
    async def _summary(_discord_user_id):
        return inventory_service.governor_account_service.summarize_accounts(
            {"Alt 1": {"GovernorID": "222", "GovernorName": "AltGov"}}
        )

    monkeypatch.setattr(
        inventory_service.governor_account_service,
        "get_account_summary_for_user",
        _summary,
    )

    assert (
        await inventory_service.user_can_import_for_governor(discord_user_id=123, governor_id=222)
        is True
    )
    assert (
        await inventory_service.user_can_import_for_governor(discord_user_id=123, governor_id=999)
        is False
    )


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


async def test_additional_material_image_does_not_update_batch_when_not_material(monkeypatch):
    def _update(**_kwargs):
        raise AssertionError("non-material additional screenshots must not overwrite the batch")

    monkeypatch.setattr(inventory_service.inventory_dal, "update_batch_analysis", _update)

    summary = await inventory_service.analyse_additional_material_image(
        import_batch_id=42,
        existing_detected_json={"values": {"materials": {"choice_chests": {"legendary": 1}}}},
        payload=InventoryImagePayload(image_bytes=b"cat", filename="cat.png"),
        vision_client=_LowConfidenceVisionClient(),
    )

    assert summary.import_type == InventoryImportType.UNKNOWN
    assert summary.ok is False
    assert summary.error is not None


async def test_additional_material_image_rejects_high_confidence_non_material(monkeypatch):
    """High-confidence Resources/Speedups image must not be merged into a materials batch."""

    class _ResourcesVisionClient(_VisionClient):
        async def analyse_image(
            self, image_bytes, *, filename=None, content_type=None, import_type_hint=None
        ):
            result = _VisionResult()
            result.detected_image_type = "resources"
            result.confidence_score = 0.95
            result.ok = True
            return result

    def _update(**_kwargs):
        raise AssertionError("non-material additional screenshots must not overwrite the batch")

    monkeypatch.setattr(inventory_service.inventory_dal, "update_batch_analysis", _update)

    summary = await inventory_service.analyse_additional_material_image(
        import_batch_id=42,
        existing_detected_json={"values": {"materials": {"choice_chests": {"legendary": 1}}}},
        payload=InventoryImagePayload(image_bytes=b"resources", filename="resources.png"),
        vision_client=_ResourcesVisionClient(),
    )

    assert summary.ok is False
    assert summary.import_type == InventoryImportType.RESOURCES
    assert summary.error is not None


async def test_additional_material_image_merges_and_persists_materials(monkeypatch):
    captured = {}

    def _update(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(inventory_service.inventory_dal, "update_batch_analysis", _update)

    summary = await inventory_service.analyse_additional_material_image(
        import_batch_id=42,
        existing_detected_json={
            "detected_image_type": "materials",
            "values": {"materials": {"animal_bone": {"epic": 4}}},
            "warnings": [],
        },
        payload=InventoryImagePayload(image_bytes=b"materials", filename="materials.png"),
        vision_client=_MaterialVisionClient(),
    )

    assert summary.import_type == InventoryImportType.MATERIALS
    assert summary.values["materials"]["animal_bone"]["epic"] == 4
    assert summary.values["materials"]["choice_chests"]["legendary"] == 1
    assert captured["status"] == InventoryImportStatus.ANALYSED


async def test_decide_analysis_outcome_allows_materials_review():
    result = _VisionResult()
    result.detected_image_type = "materials"
    result.values = {"materials": {}}

    decision = inventory_service.decide_analysis_outcome(
        inventory_service._summary_from_vision_result(result)
    )

    assert decision.action == "review"
    assert decision.debug_status is None
    assert decision.error is None


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


async def test_resource_significant_change_requires_confirmation(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_resource_values",
        lambda governor_id: {
            "food": {"from_items_value": 0, "total_resources_value": 100},
            "wood": {"from_items_value": 0, "total_resources_value": 100},
            "stone": {"from_items_value": 0, "total_resources_value": 100},
            "gold": {"from_items_value": 0, "total_resources_value": 100},
        },
    )
    values = {
        "resources": {
            "food": {"from_items_value": 0, "total_resources_value": 175},
            "wood": {"from_items_value": 0, "total_resources_value": 101},
            "stone": {"from_items_value": 0, "total_resources_value": 99},
            "gold": {"from_items_value": 0, "total_resources_value": 100},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.RESOURCES,
        values=values,
    )

    assert assessment.requires_confirmation is True
    assert any("Food" in warning for warning in assessment.warnings)


async def test_resource_significant_change_triggers_at_exactly_50_percent(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_resource_values",
        lambda governor_id: {
            "food": {"from_items_value": 0, "total_resources_value": 100},
            "wood": {"from_items_value": 0, "total_resources_value": 100},
            "stone": {"from_items_value": 0, "total_resources_value": 100},
            "gold": {"from_items_value": 0, "total_resources_value": 100},
        },
    )
    values = {
        "resources": {
            "food": {"from_items_value": 0, "total_resources_value": 100},
            "wood": {"from_items_value": 0, "total_resources_value": 100},
            "stone": {"from_items_value": 0, "total_resources_value": 100},
            "gold": {"from_items_value": 0, "total_resources_value": 150},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.RESOURCES,
        values=values,
    )

    assert assessment.requires_confirmation is True
    assert any("Gold changed by 50% or more" in warning for warning in assessment.warnings)


async def test_resource_correction_significant_change_checks_detected_values(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_resource_values",
        lambda governor_id: {
            "food": {"from_items_value": 0, "total_resources_value": 3_900_000_000},
            "wood": {"from_items_value": 0, "total_resources_value": 4_000_000_000},
            "stone": {"from_items_value": 0, "total_resources_value": 3_200_000_000},
            "gold": {"from_items_value": 0, "total_resources_value": 4_200_000_000},
        },
    )
    detected_values = {
        "resources": {
            "food": {"from_items_value": 2_900_000_000, "total_resources_value": 3_900_000_000},
            "wood": {"from_items_value": 3_000_000_000, "total_resources_value": 4_000_000_000},
            "stone": {"from_items_value": 1_900_000_000, "total_resources_value": 3_200_000_000},
            "gold": {"from_items_value": 769_200_000, "total_resources_value": 2_200_000_000},
        }
    }
    corrected_values = {
        "resources": {
            "food": {"from_items_value": 2_900_000_000, "total_resources_value": 3_900_000_000},
            "wood": {"from_items_value": 3_000_000_000, "total_resources_value": 4_000_000_000},
            "stone": {"from_items_value": 1_900_000_000, "total_resources_value": 3_200_000_000},
            "gold": {"from_items_value": 769_200_000, "total_resources_value": 6_200_000_000},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.RESOURCES,
        values=corrected_values,
        baseline_values=detected_values,
    )

    assert assessment.requires_confirmation is True
    assert any(
        "Gold correction from detected value changed by 50% or more" in warning
        for warning in assessment.warnings
    )


async def test_speedup_significant_change_triggers_at_exactly_50_percent(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_speedup_values",
        lambda governor_id: {
            speedup_type: {
                "total_minutes": 100 * 1440,
                "total_hours": 2400,
                "total_days_decimal": 100,
            }
            for speedup_type in ("building", "research", "training", "healing", "universal")
        },
    )
    values = {
        "speedups": {
            "building": {"total_days_decimal": 100},
            "research": {"total_days_decimal": 100},
            "training": {"total_days_decimal": 150},
            "healing": {"total_days_decimal": 100},
            "universal": {"total_days_decimal": 100},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.SPEEDUPS,
        values=values,
    )

    assert assessment.requires_confirmation is True
    assert any(
        "Training speedups changed by 50% or more" in warning for warning in assessment.warnings
    )


async def test_speedup_significant_change_requires_confirmation(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_speedup_values",
        lambda governor_id: {
            "building": {
                "total_minutes": 100 * 1440,
                "total_hours": 2400,
                "total_days_decimal": 100,
            },
            "research": {
                "total_minutes": 100 * 1440,
                "total_hours": 2400,
                "total_days_decimal": 100,
            },
            "training": {
                "total_minutes": 100 * 1440,
                "total_hours": 2400,
                "total_days_decimal": 100,
            },
            "healing": {
                "total_minutes": 100 * 1440,
                "total_hours": 2400,
                "total_days_decimal": 100,
            },
            "universal": {
                "total_minutes": 100 * 1440,
                "total_hours": 2400,
                "total_days_decimal": 100,
            },
        },
    )
    values = {
        "speedups": {
            "building": {"total_minutes": 100 * 1440},
            "research": {"total_minutes": 100 * 1440},
            "training": {"total_minutes": 151 * 1440},
            "healing": {"total_minutes": 100 * 1440},
            "universal": {"total_minutes": 100 * 1440},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.SPEEDUPS,
        values=values,
    )

    assert assessment.requires_confirmation is True
    assert any("Training" in warning for warning in assessment.warnings)


async def test_material_significant_change_checks_each_element_and_total(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_material_dal,
        "fetch_latest_approved_material_values",
        lambda governor_id: {
            "choice_chests": {"legendary": 100},
            "animal_bone": {"legendary": 20},
            "leather": {"legendary": 20},
            "ebony": {"legendary": 20},
            "iron_ore": {"legendary": 20},
        },
    )
    values = {
        "materials": {
            "choice_chests": {"legendary": 400},
            "animal_bone": {"legendary": 20},
            "leather": {"legendary": 20},
            "ebony": {"legendary": 20},
            "iron_ore": {"legendary": 20},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.MATERIALS,
        values=values,
    )

    assert assessment.requires_confirmation is True
    assert any(
        "Choice Chests materials changed by 50% or more" in warning
        for warning in assessment.warnings
    )
    assert any(
        "Total materials changed by 50% or more" in warning for warning in assessment.warnings
    )


async def test_material_correction_significant_change_checks_detected_values(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_material_dal,
        "fetch_latest_approved_material_values",
        lambda governor_id: {},
    )
    detected_values = {
        "materials": {
            "choice_chests": {"legendary": 100},
            "animal_bone": {"legendary": 1},
            "leather": {"legendary": 1},
            "ebony": {"legendary": 1},
            "iron_ore": {"legendary": 1},
        }
    }
    corrected_values = {
        "materials": {
            "choice_chests": {"legendary": 100},
            "animal_bone": {"legendary": 3},
            "leather": {"legendary": 1},
            "ebony": {"legendary": 1},
            "iron_ore": {"legendary": 1},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.MATERIALS,
        values=corrected_values,
        baseline_values=detected_values,
    )

    assert assessment.requires_confirmation is True
    assert any(
        "Materials correction from detected value: Bone materials changed by 50% or more" in warning
        for warning in assessment.warnings
    )


async def test_significant_change_allows_small_delta(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_resource_values",
        lambda governor_id: {
            "food": {"from_items_value": 0, "total_resources_value": 100},
            "wood": {"from_items_value": 0, "total_resources_value": 100},
            "stone": {"from_items_value": 0, "total_resources_value": 100},
            "gold": {"from_items_value": 0, "total_resources_value": 100},
        },
    )
    values = {
        "resources": {
            "food": {"from_items_value": 0, "total_resources_value": 125},
            "wood": {"from_items_value": 0, "total_resources_value": 100},
            "stone": {"from_items_value": 0, "total_resources_value": 100},
            "gold": {"from_items_value": 0, "total_resources_value": 100},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.RESOURCES,
        values=values,
    )

    assert assessment.requires_confirmation is False
    assert assessment.warnings == []


async def test_significant_change_skips_when_no_previous_import(monkeypatch):
    monkeypatch.setattr(
        inventory_service.inventory_dal,
        "fetch_latest_approved_speedup_values",
        lambda governor_id: {},
    )
    values = {
        "speedups": {
            "building": {"total_minutes": 100 * 1440},
            "research": {"total_minutes": 100 * 1440},
            "training": {"total_minutes": 100 * 1440},
            "healing": {"total_minutes": 100 * 1440},
            "universal": {"total_minutes": 100 * 1440},
        }
    }

    assessment = await inventory_service.assess_significant_change(
        governor_id=111,
        import_type=InventoryImportType.SPEEDUPS,
        values=values,
    )

    assert assessment.requires_confirmation is False
