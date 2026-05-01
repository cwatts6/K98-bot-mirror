import pytest

from inventory.models import InventoryAnalysisSummary, InventoryImportType
from ui.views.inventory_views import (
    InventoryConfirmationView,
    ResourceCorrectionModal,
    SpeedupCorrectionModal,
    _analysis_embed,
)


def _summary(import_type):
    values = {
        "resources": {
            "food": {"from_items_value": 1, "total_resources_value": 2_000_000},
            "wood": {"from_items_value": 3, "total_resources_value": 4_000_000},
            "stone": {"from_items_value": 5, "total_resources_value": 6_000_000},
            "gold": {"from_items_value": 7, "total_resources_value": 8_000_000},
        },
        "speedups": {
            "building": {"total_minutes": 60, "total_hours": 1, "total_days_decimal": 0.0417},
            "research": {"total_minutes": 120, "total_hours": 2, "total_days_decimal": 0.0833},
            "training": {"total_minutes": 1440, "total_hours": 24, "total_days_decimal": 1},
            "healing": {"total_minutes": 2880, "total_hours": 48, "total_days_decimal": 2},
            "universal": {"total_minutes": 4320, "total_hours": 72, "total_days_decimal": 3},
        },
    }
    return InventoryAnalysisSummary(
        ok=True,
        import_type=import_type,
        values=values,
        confidence_score=0.98,
        model="hidden-model",
        fallback_used=True,
    )


def _view(import_type):
    return InventoryConfirmationView(
        bot=object(),
        actor_discord_id=42,
        governor_id=111,
        batch_id=7,
        payload=object(),
        summary=_summary(import_type),
    )


def test_inventory_review_embed_hides_model_and_fallback_details():
    embed = _analysis_embed(governor_id=111, summary=_summary(InventoryImportType.RESOURCES))

    field_names = [field.name for field in embed.fields]

    assert "Model" not in field_names
    assert "Fallback Used" not in field_names
    assert "Detected Values" in field_names


@pytest.mark.asyncio
async def test_resource_correction_modal_only_prompts_total_resources():
    modal = ResourceCorrectionModal(_view(InventoryImportType.RESOURCES))

    labels = [item.label for item in modal.children]

    assert labels == [
        "Food Total Resources",
        "Wood Total Resources",
        "Stone Total Resources",
        "Gold Total Resources",
    ]


@pytest.mark.asyncio
async def test_resource_correction_modal_prefills_exact_integer_values():
    """Pre-fill must use the raw integer string, not the abbreviated format.

    format_resource_value(1_234_567) == "1.2M", which when re-parsed gives
    1_200_000 — silently corrupting an unchanged field on modal submit.
    Using str(int(value)) preserves full precision for round-trips.
    """
    summary = _summary(InventoryImportType.RESOURCES)
    # Override food with a value that abbreviates with precision loss
    summary.values["resources"]["food"]["total_resources_value"] = 1_234_567
    modal = ResourceCorrectionModal(
        InventoryConfirmationView(
            bot=object(),
            actor_discord_id=42,
            governor_id=111,
            batch_id=7,
            payload=object(),
            summary=summary,
        )
    )

    values = {item.label: item.value for item in modal.children}

    assert values["Food Total Resources"] == "1234567"
    # Other fields also use exact integer strings
    assert values["Wood Total Resources"] == "4000000"


@pytest.mark.asyncio
async def test_speedup_correction_modal_prompts_friendly_durations():
    modal = SpeedupCorrectionModal(_view(InventoryImportType.SPEEDUPS))

    labels = [item.label for item in modal.children]
    values = [item.value for item in modal.children]

    assert labels[:3] == [
        "Building Speedup Days",
        "Research Speedup Days",
        "Training Speedup Days",
    ]
    assert values[:3] == ["0d", "0d", "1d"]


@pytest.mark.asyncio
async def test_speedup_correction_updates_original_review_message():
    parent = _view(InventoryImportType.SPEEDUPS)
    edited = {}

    class _Message:
        async def edit(self, **kwargs):
            edited.update(kwargs)

    class _Response:
        async def send_message(self, *args, **kwargs):
            edited["response"] = (args, kwargs)

    parent.message = _Message()
    modal = SpeedupCorrectionModal(parent)
    for item in modal.children:
        if item.label == "Healing Speedup Days":
            item.value = "505d"

    interaction = type(
        "_Interaction",
        (),
        {
            "message": None,
            "response": _Response(),
        },
    )()

    await modal.callback(interaction)

    assert "embed" in edited
    corrected_field = next(
        field for field in edited["embed"].fields if field.name == "Corrected Values"
    )
    assert "Healing: `505d`" in corrected_field.value
