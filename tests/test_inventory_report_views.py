import pytest

from inventory.models import (
    InventoryReportRange,
    InventoryReportView,
    InventoryReportVisibility,
    RegisteredGovernor,
)
from ui.views import inventory_report_views
from ui.views.inventory_report_views import (
    InventoryPreferenceView,
    InventoryRangeView,
    InventoryReportSelectionView,
)


@pytest.mark.asyncio
async def test_inventory_range_view_exposes_range_and_export_buttons():
    view = InventoryRangeView(
        requester_id=42,
        governor=RegisteredGovernor(111, "Gov", "Main"),
        report_view=InventoryReportView.RESOURCES,
        range_key=InventoryReportRange.ONE_MONTH,
        avatar_bytes=None,
    )

    custom_ids = [item.custom_id for item in view.children]

    assert custom_ids[:4] == [
        "inventory_report_range_1m",
        "inventory_report_range_3m",
        "inventory_report_range_6m",
        "inventory_report_range_12m",
    ]
    assert custom_ids[4:] == [
        "inventory_report_export_excel",
        "inventory_report_export_csv",
        "inventory_report_export_google_sheets",
    ]


def _make_ctx(user_id=42):
    class _Followup:
        def __init__(self):
            self.sent = {}

        async def send(self, content=None, **kwargs):
            self.sent["content"] = content
            self.sent.update(kwargs)

    followup = _Followup()
    ctx = type(
        "_Ctx",
        (),
        {
            "user": type("_User", (), {"id": user_id, "display_name": "Tester"})(),
            "followup": followup,
        },
    )()
    return ctx, followup


def _two_governors():
    return [
        RegisteredGovernor(111, "MainGov", "Main"),
        RegisteredGovernor(222, "AltGov", "Alt 1"),
    ]


async def _start_and_get_picker(monkeypatch, user_id=42):
    ctx, followup = _make_ctx(user_id=user_id)

    async def _get_governors(_user_id):
        return _two_governors()

    monkeypatch.setattr(
        inventory_report_views.reporting_service,
        "get_registered_governors_for_user",
        _get_governors,
    )

    await inventory_report_views.start_myinventory_command(
        ctx=ctx,
        visibility=InventoryReportVisibility.ONLY_ME,
    )

    return ctx, followup, followup.sent["view"]


@pytest.mark.asyncio
async def test_myinventory_uses_picker_for_multiple_governors(monkeypatch):
    _ctx, followup, view = await _start_and_get_picker(monkeypatch)

    assert followup.sent["content"] == "Choose the inventory report to view:"
    assert followup.sent["ephemeral"] is True
    placeholders = [getattr(item, "placeholder", None) for item in view.children]
    assert "Select Governor" in placeholders
    assert "Select Output" in placeholders


@pytest.mark.asyncio
async def test_on_select_rejects_wrong_user(monkeypatch):
    """_on_select must refuse interactions from users other than the command invoker."""
    _ctx, _followup, picker_view = await _start_and_get_picker(monkeypatch, user_id=42)
    rejected = {}

    class _Response:
        async def send_message(self, content=None, **kwargs):
            rejected["content"] = content
            rejected.update(kwargs)

    intruder_interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 999})(),
            "response": _Response(),
        },
    )()

    await picker_view.send_report(intruder_interaction)

    assert "not for you" in rejected.get("content", "")
    assert rejected.get("ephemeral") is True


@pytest.mark.asyncio
async def test_show_report_requires_governor_selection(monkeypatch):
    _ctx, _followup, picker_view = await _start_and_get_picker(monkeypatch, user_id=42)
    picker_view.selected_governor_id = None

    response = {}

    class _Response:
        async def send_message(self, content=None, **kwargs):
            response["content"] = content
            response.update(kwargs)

    valid_interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 42})(),
            "response": _Response(),
        },
    )()

    await picker_view.send_report(valid_interaction)

    assert "Choose a governor" in response.get("content", "")
    assert response.get("ephemeral") is True


@pytest.mark.asyncio
async def test_show_report_sends_report_for_selected_governor_and_output(monkeypatch):
    _ctx, _followup, picker_view = await _start_and_get_picker(monkeypatch, user_id=42)
    picker_view.selected_governor_id = 222
    picker_view.selected_view = InventoryReportView.SPEEDUPS
    captured = {}

    async def _mock_send_report(*, send, user, requester_id, governor, **kwargs):
        captured["governor"] = governor
        captured["requester_id"] = requester_id
        captured.update(kwargs)

    monkeypatch.setattr(
        inventory_report_views,
        "_send_inventory_report_message",
        _mock_send_report,
    )

    class _Response:
        async def defer(self, **kwargs):
            captured["defer"] = kwargs

    class _Followup:
        async def send(self, content=None, **kwargs):
            pass

    valid_interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 42, "display_name": "Tester"})(),
            "response": _Response(),
            "followup": _Followup(),
        },
    )()

    await picker_view.send_report(valid_interaction)

    assert captured["governor"].governor_id == 222
    assert captured["requester_id"] == 42
    assert captured["report_view"] == InventoryReportView.SPEEDUPS


@pytest.mark.asyncio
async def test_preference_view_saves_visibility(monkeypatch):
    saved = {}

    async def _resolve_visibility(**kwargs):
        saved.update(kwargs)

    monkeypatch.setattr(
        inventory_report_views.reporting_service,
        "resolve_visibility",
        _resolve_visibility,
    )
    view = InventoryPreferenceView(requester_id=42)

    class _Response:
        async def defer(self, **_kwargs):
            return None

    class _Followup:
        async def send(self, content=None, **kwargs):
            saved["content"] = content
            saved.update(kwargs)

    interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 42})(),
            "response": _Response(),
            "followup": _Followup(),
            "edit_original_response": lambda self, **_kwargs: None,
        },
    )()

    await view._save(interaction, InventoryReportVisibility.PUBLIC)

    assert saved["discord_user_id"] == 42
    assert saved["selected_visibility"] == InventoryReportVisibility.PUBLIC


@pytest.mark.asyncio
async def test_report_selection_view_single_governor_only_shows_output_select():
    ctx, _followup = _make_ctx()
    view = InventoryReportSelectionView(
        ctx=ctx,
        governors=[RegisteredGovernor(111, "MainGov", "Main")],
        visibility=InventoryReportVisibility.ONLY_ME,
    )

    placeholders = [getattr(item, "placeholder", None) for item in view.children]

    assert "Select Governor" not in placeholders
    assert "Select Output" in placeholders
