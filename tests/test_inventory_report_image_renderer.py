from datetime import UTC, datetime, timedelta

from inventory import report_image_renderer
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


def test_chart_ticks_expand_flat_values():
    ticks = report_image_renderer._chart_ticks(100, 100)

    assert len(ticks) == 5
    assert ticks[0] < 100
    assert ticks[-1] > 100


def test_chart_ticks_start_at_zero_for_report_domain():
    ticks = report_image_renderer._chart_ticks(0, 100)

    assert ticks[0] == 0
    assert ticks[-1] == 100


def test_series_values_flattens_visible_series_for_y_scale():
    values = report_image_renderer._series_values(
        {
            "Food": [10, 20],
            "Wood": [5, 7],
            "Stone": [1, 2],
        }
    )

    assert values == [10, 20, 5, 7, 1, 2]


def test_resource_chart_colours_are_distinct():
    colours = list(report_image_renderer.RESOURCE_CHART_COLORS.values())

    assert len(colours) == 4
    assert len(set(colours)) == 4
    assert (
        report_image_renderer.RESOURCE_CHART_COLORS["Wood"]
        != report_image_renderer.RESOURCE_CHART_COLORS["Gold"]
    )
