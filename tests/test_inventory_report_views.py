import pytest

from inventory.models import InventoryReportRange, InventoryReportView, RegisteredGovernor
from ui.views.inventory_report_views import InventoryRangeView


@pytest.mark.asyncio
async def test_inventory_range_view_exposes_only_range_buttons():
    view = InventoryRangeView(
        requester_id=42,
        governor=RegisteredGovernor(111, "Gov", "Main"),
        report_view=InventoryReportView.RESOURCES,
        range_key=InventoryReportRange.ONE_MONTH,
        avatar_bytes=None,
    )

    custom_ids = [item.custom_id for item in view.children]

    assert custom_ids == [
        "inventory_report_range_1m",
        "inventory_report_range_3m",
        "inventory_report_range_6m",
        "inventory_report_range_12m",
    ]
