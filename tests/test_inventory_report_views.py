import pytest

from inventory.models import InventoryReportRange, InventoryReportView, RegisteredGovernor
from ui.views import inventory_report_views
from ui.views.inventory_report_views import InventoryRangeView


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

    async def _resolve(**_kwargs):
        return None

    async def _get_governors(_user_id):
        return _two_governors()

    monkeypatch.setattr(
        inventory_report_views.reporting_service,
        "resolve_governor_for_report",
        _resolve,
    )
    monkeypatch.setattr(
        inventory_report_views.reporting_service,
        "get_registered_governors_for_user",
        _get_governors,
    )

    await inventory_report_views.start_myinventory_command(
        ctx=ctx,
        governor_id=None,
        report_view=InventoryReportView.ALL,
        range_key=InventoryReportRange.ONE_MONTH,
        visibility=inventory_report_views.InventoryReportVisibility.ONLY_ME,
    )

    return ctx, followup, followup.sent["view"]


@pytest.mark.asyncio
async def test_myinventory_uses_picker_for_multiple_governors(monkeypatch):
    _ctx, followup, view = await _start_and_get_picker(monkeypatch)

    assert followup.sent["content"] == "Select which governor inventory report to view:"
    assert followup.sent["ephemeral"] is True
    assert view.children[0].placeholder == "Select Governor"


@pytest.mark.asyncio
async def test_on_select_rejects_wrong_user(monkeypatch):
    """_on_select must refuse interactions from users other than the command invoker."""
    _ctx, _followup, picker_view = await _start_and_get_picker(monkeypatch, user_id=42)
    on_select = picker_view._on_select_governor

    rejected = {}

    class _Followup2:
        async def send(self, content=None, **kwargs):
            rejected["content"] = content
            rejected.update(kwargs)

    intruder_interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 999})(),
            "followup": _Followup2(),
        },
    )()

    await on_select(intruder_interaction, "111", True)  # ephemeral=True (picker is ephemeral)

    assert "not for you" in rejected.get("content", "")
    assert rejected.get("ephemeral") is True


@pytest.mark.asyncio
async def test_on_select_rejects_stale_governor(monkeypatch):
    """_on_select must handle a governor_id that was removed after the picker was shown."""
    _ctx, _followup, picker_view = await _start_and_get_picker(monkeypatch, user_id=42)
    on_select = picker_view._on_select_governor

    stale_response = {}

    class _Followup3:
        async def send(self, content=None, **kwargs):
            stale_response["content"] = content
            stale_response.update(kwargs)

    valid_interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 42})(),
            "followup": _Followup3(),
        },
    )()

    await on_select(valid_interaction, "9999", True)  # ephemeral=True (picker is ephemeral)

    assert "no longer available" in stale_response.get("content", "")
    assert stale_response.get("ephemeral") is True


@pytest.mark.asyncio
async def test_on_select_sends_report_for_valid_governor(monkeypatch):
    """_on_select must hand off to _send_inventory_report_message with the selected governor."""
    _ctx, _followup, picker_view = await _start_and_get_picker(monkeypatch, user_id=42)
    on_select = picker_view._on_select_governor

    captured = {}

    async def _mock_send_report(*, send, user, requester_id, governor, **kwargs):
        captured["governor"] = governor
        captured["requester_id"] = requester_id

    monkeypatch.setattr(
        inventory_report_views,
        "_send_inventory_report_message",
        _mock_send_report,
    )

    class _Followup4:
        async def send(self, content=None, **kwargs):
            pass

    valid_interaction = type(
        "_Interaction",
        (),
        {
            "user": type("_User", (), {"id": 42, "display_name": "Tester"})(),
            "followup": _Followup4(),
        },
    )()

    await on_select(valid_interaction, "222", True)  # ephemeral=True (picker is ephemeral)

    assert captured["governor"].governor_id == 222
    assert captured["requester_id"] == 42
