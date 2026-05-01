from datetime import UTC, datetime, timedelta

from inventory.models import (
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
    InventoryResourcePoint,
    InventorySpeedupPoint,
)
from inventory.report_image_renderer import render_inventory_reports


def test_render_inventory_reports_returns_png_files_for_resources_and_speedups():
    now = datetime.now(UTC)
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Gov",
        view=InventoryReportView.ALL,
        range_key=InventoryReportRange.ONE_MONTH,
        resources=[
            InventoryResourcePoint(now - timedelta(days=7), 100, 200, 300, 400),
            InventoryResourcePoint(now, 200, 300, 400, 500),
        ],
        speedups=[
            InventorySpeedupPoint(now - timedelta(days=7), 1, 2, 3, 4, 5),
            InventorySpeedupPoint(now, 2, 3, 4, 5, 6),
        ],
        generated_at_utc=now,
    )

    rendered = render_inventory_reports(payload)

    assert [item.filename for item in rendered] == [
        "inventory_resources_111_1M.png",
        "inventory_speedups_111_1M.png",
    ]
    for item in rendered:
        assert item.image_bytes.getvalue().startswith(b"\x89PNG")
