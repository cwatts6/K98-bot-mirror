import pytest

from inventory import inventory_service
from inventory.models import (
    InventoryAnalysisSummary,
    InventoryFlowType,
    InventoryImagePayload,
    InventoryImportType,
)
from ui.views import inventory_views
from ui.views.inventory_views import (
    InventoryConfirmationView,
    ResourceCorrectionModal,
    SpeedupCorrectionModal,
    _analysis_embed,
    _resource_modal_value,
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


class _DoneResponse:
    def __init__(self):
        self.messages = []
        self.deferred = False

    def is_done(self):
        return self.deferred

    async def defer(self, **_kwargs):
        self.deferred = True

    async def send_message(self, content=None, **kwargs):
        self.messages.append((content, kwargs))
        self.deferred = True


class _Followup:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, **kwargs):
        self.sent.append((content, kwargs))


class _Message:
    def __init__(self):
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


class _Interaction:
    def __init__(self, user_id=42):
        self.user = type("_User", (), {"id": user_id})()
        self.response = _DoneResponse()
        self.followup = _Followup()
        self.message = _Message()


def test_inventory_review_embed_hides_model_and_fallback_details():
    embed = _analysis_embed(governor_id=111, summary=_summary(InventoryImportType.RESOURCES))

    field_names = [field.name for field in embed.fields]

    assert "Model" not in field_names
    assert "Fallback Used" not in field_names
    assert "Detected Values" in field_names


@pytest.mark.asyncio
async def test_confirmation_view_uses_explicit_audit_entry_point():
    view = InventoryConfirmationView(
        bot=object(),
        actor_discord_id=42,
        governor_id=111,
        batch_id=7,
        payload=InventoryImagePayload(image_bytes=b"img", filename="materials.png"),
        summary=_summary(InventoryImportType.MATERIALS),
        flow_type=InventoryFlowType.UPLOAD_FIRST.value,
        audit_entry_point="inventory_additional_material_upload",
    )

    assert view._audit_context().entry_point == "inventory_additional_material_upload"


@pytest.mark.asyncio
async def test_inventory_review_uses_single_cancel_button():
    view = _view(InventoryImportType.SPEEDUPS)
    custom_ids = [item.custom_id for item in view.children]

    assert "inventory_import_cancel" in custom_ids
    assert "inventory_import_reject" not in custom_ids


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
    """Pre-fill may use compact text only when it round-trips exactly.

    format_resource_value(1_234_567) == "1.2M", which when re-parsed gives
    1_200_000 — silently corrupting an unchanged field on modal submit.
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
    assert values["Wood Total Resources"] == "4M"


def test_resource_modal_value_uses_compact_text_only_when_exact():
    assert _resource_modal_value(3_800_000_000) == "3.8B"
    assert _resource_modal_value(100_000_000) == "100M"
    assert _resource_modal_value(1_234_567) == "1234567"


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
async def test_speedup_correction_updates_original_review_message(monkeypatch):
    parent = _view(InventoryImportType.SPEEDUPS)
    edited = {}

    async def _state(_batch_id):
        return inventory_service.InventoryReviewActionState(active=True)

    monkeypatch.setattr(inventory_views.inventory_service, "get_review_action_state", _state)

    class _Message:
        async def edit(self, **kwargs):
            edited.update(kwargs)

    class _Response:
        def is_done(self):
            return False

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


@pytest.mark.asyncio
async def test_approve_requires_second_click_for_significant_change(monkeypatch):
    parent = _view(InventoryImportType.RESOURCES)
    interaction = _Interaction()

    async def _state(_batch_id):
        return inventory_service.InventoryReviewActionState(active=True)

    async def _assessment(**_kwargs):
        return inventory_service.InventorySignificantChangeAssessment(
            requires_confirmation=True,
            warnings=["Food changed by more than 50% (100 -> 200)."],
        )

    async def _approve(**_kwargs):
        raise AssertionError("approval should wait for the second confirmation")

    monkeypatch.setattr(inventory_views.inventory_service, "get_review_action_state", _state)
    monkeypatch.setattr(inventory_views.inventory_service, "assess_significant_change", _assessment)
    monkeypatch.setattr(inventory_views.inventory_service, "approve_import", _approve)

    await parent.approve.callback(interaction)

    assert parent._significant_change_confirmed is True
    assert "significantly different" in interaction.followup.sent[0][0]
    assert interaction.message.edits


@pytest.mark.asyncio
async def test_corrected_approve_checks_detected_values_as_baseline(monkeypatch):
    parent = _view(InventoryImportType.RESOURCES)
    parent.corrected_values = {
        "resources": {
            **parent.summary.values["resources"],
            "gold": {"from_items_value": 7, "total_resources_value": 6_200_000_000},
        }
    }
    interaction = _Interaction()
    captured = {}

    async def _assessment(**kwargs):
        captured.update(kwargs)
        return inventory_service.InventorySignificantChangeAssessment()

    monkeypatch.setattr(inventory_views.inventory_service, "assess_significant_change", _assessment)

    requires_second = await parent._requires_second_approve(interaction)

    assert requires_second is False
    assert captured["values"] is parent.corrected_values
    assert captured["baseline_values"] is parent.summary.values


@pytest.mark.asyncio
async def test_stale_click_after_timeout_returns_expired_message(monkeypatch):
    parent = _view(InventoryImportType.RESOURCES)
    parent._expired = True
    parent._terminal = True
    interaction = _Interaction()

    async def _state(_batch_id):
        raise AssertionError("local expired state should short-circuit")

    monkeypatch.setattr(inventory_views.inventory_service, "get_review_action_state", _state)

    denied = await parent._deny_if_not_actor(interaction)

    assert denied is True
    assert "expired" in interaction.response.messages[0][0]


@pytest.mark.asyncio
async def test_review_buttons_reject_non_initiating_user(monkeypatch):
    parent = _view(InventoryImportType.RESOURCES)
    interaction = _Interaction(user_id=999)

    async def _state(_batch_id):
        raise AssertionError("actor check should run before state lookup")

    monkeypatch.setattr(inventory_views.inventory_service, "get_review_action_state", _state)

    denied = await parent._deny_if_not_actor(interaction)

    assert denied is True
    assert "Only the user who started this import" in interaction.response.messages[0][0]


@pytest.mark.asyncio
async def test_correction_modal_rejects_expired_parent():
    parent = _view(InventoryImportType.SPEEDUPS)
    parent._expired = True
    parent._terminal = True
    modal = SpeedupCorrectionModal(parent)
    interaction = _Interaction()

    await modal.callback(interaction)

    assert "expired" in interaction.response.messages[0][0]
