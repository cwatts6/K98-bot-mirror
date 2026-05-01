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


@pytest.mark.asyncio
async def test_myinventory_uses_picker_for_multiple_governors(monkeypatch):
    sent = {}

    class _Followup:
        async def send(self, content=None, **kwargs):
            sent["content"] = content
            sent.update(kwargs)

    ctx = type(
        "_Ctx",
        (),
        {
            "user": type("_User", (), {"id": 42, "display_name": "Tester"})(),
            "followup": _Followup(),
        },
    )()

    async def _resolve(**_kwargs):
        return None

    async def _governors(_user_id):
        return [
            RegisteredGovernor(111, "MainGov", "Main"),
            RegisteredGovernor(222, "AltGov", "Alt 1"),
        ]

    monkeypatch.setattr(
        inventory_report_views.reporting_service,
        "resolve_governor_for_report",
        _resolve,
    )
    monkeypatch.setattr(
        inventory_report_views.reporting_service,
        "get_registered_governors_for_user",
        _governors,
    )

    await inventory_report_views.start_myinventory_command(
        ctx=ctx,
        governor_id=None,
        report_view=InventoryReportView.ALL,
        range_key=InventoryReportRange.ONE_MONTH,
        visibility=inventory_report_views.InventoryReportVisibility.ONLY_ME,
    )

    assert sent["content"] == "Select which governor inventory report to view:"
    assert sent["ephemeral"] is True
    assert sent["view"].children[0].placeholder == "Select Governor"
