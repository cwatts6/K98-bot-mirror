from datetime import UTC, datetime, timedelta
from io import BytesIO

from PIL import Image

from core import visual_text
from inventory import report_image_renderer
from inventory.models import (
    InventoryGovernorProfile,
    InventoryMaterialPoint,
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
    InventoryResourcePoint,
    InventorySpeedupPoint,
)
from inventory.report_image_renderer import render_inventory_reports


def test_inventory_renderer_text_helpers_delegate_to_visual_text(monkeypatch):
    image = Image.new("RGBA", (240, 80))
    draw = report_image_renderer.ImageDraw.Draw(image)
    sentinel_font = object()
    calls = {}

    def _font(size, *, bold=False):
        calls["font"] = (size, bold)
        return sentinel_font

    def _text_width(draw_arg, text, *, font, bold=False):
        calls["text_width"] = (text, font, bold)
        return 42

    def _fit_font(draw_arg, text, *, max_width, size, min_size, bold=False):
        calls["fit_font"] = (text, max_width, size, min_size, bold)
        return sentinel_font

    report_image_renderer._font.cache_clear()
    monkeypatch.setattr(report_image_renderer.visual_text, "font", _font)
    monkeypatch.setattr(report_image_renderer.visual_text, "text_width", _text_width)
    monkeypatch.setattr(report_image_renderer.visual_text, "fit_font", _fit_font)

    drawn = {}

    def _draw_text(draw_arg, xy, text, *, fill, font, bold=False):
        drawn.update({"xy": xy, "text": text, "fill": fill, "font": font, "bold": bold})

    monkeypatch.setattr(report_image_renderer.visual_text, "draw_text", _draw_text)

    assert report_image_renderer._font(19, bold=True) is sentinel_font
    assert report_image_renderer._text_width(draw, "義🚀", sentinel_font, bold=True) == 42
    assert (
        report_image_renderer._fit_font(
            draw,
            "Long value",
            max_width=120,
            size=22,
            min_size=12,
            bold=True,
        )
        is sentinel_font
    )
    report_image_renderer._draw_text(
        draw,
        (10.8, 12.2),
        "Gov",
        fill=report_image_renderer.TEXT,
        font=sentinel_font,
        bold=True,
    )

    assert calls["font"] == (19, True)
    assert calls["text_width"] == ("義🚀", sentinel_font, True)
    assert calls["fit_font"] == ("Long value", 120, 22, 12, True)
    assert drawn == {
        "xy": (10, 12),
        "text": "Gov",
        "fill": report_image_renderer.TEXT,
        "font": sentinel_font,
        "bold": True,
    }
    report_image_renderer._font.cache_clear()


def test_inventory_wrap_text_uses_glyph_safe_width():
    image = Image.new("RGBA", (420, 80))
    draw = report_image_renderer.ImageDraw.Draw(image)
    base_font = visual_text.font(18)

    lines = report_image_renderer._wrap_text(
        draw,
        "義" * 50,
        font=base_font,
        max_width=120,
        max_lines=1,
    )

    assert len(lines) == 1
    assert report_image_renderer._text_width(draw, lines[0], base_font) <= 120


def test_inventory_wrap_text_preserves_bold_measurement(monkeypatch):
    image = Image.new("RGBA", (420, 80))
    draw = report_image_renderer.ImageDraw.Draw(image)
    base_font = visual_text.font(18)
    seen_bold_values = []

    def _fake_width(draw_arg, text, *, font, bold=False):
        seen_bold_values.append(bold)
        return 10

    monkeypatch.setattr(report_image_renderer.visual_text, "text_width", _fake_width)

    lines = report_image_renderer._wrap_text(
        draw,
        "bold detail",
        font=base_font,
        max_width=120,
        max_lines=1,
        bold=True,
    )

    assert lines == ["bold detail"]
    assert seen_bold_values
    assert all(seen_bold_values)


def test_inventory_wrap_text_truncates_with_cluster_safe_fit(monkeypatch):
    image = Image.new("RGBA", (420, 80))
    draw = report_image_renderer.ImageDraw.Draw(image)
    base_font = visual_text.font(18)
    calls = {}

    def _fake_fit(draw_arg, text, *, width, base_font, bold=False):
        calls.update({"text": text, "width": width, "base_font": base_font, "bold": bold})
        return "🚀."

    monkeypatch.setattr(report_image_renderer.visual_text, "fit_text_to_width", _fake_fit)
    astronaut = "\U0001f469\u200d\U0001f680"

    lines = report_image_renderer._wrap_text(
        draw,
        astronaut * 20,
        font=base_font,
        max_width=80,
        max_lines=1,
        bold=True,
    )

    assert lines == ["🚀."]
    assert calls == {
        "text": astronaut * 20,
        "width": 80,
        "base_font": base_font,
        "bold": True,
    }


def test_inventory_wrap_text_does_not_split_joined_emoji_clusters():
    image = Image.new("RGBA", (420, 80))
    draw = report_image_renderer.ImageDraw.Draw(image)
    base_font = visual_text.font(18)
    astronaut = "\U0001f469\u200d\U0001f680"

    lines = report_image_renderer._wrap_text(
        draw,
        astronaut * 20,
        font=base_font,
        max_width=80,
        max_lines=1,
        bold=True,
    )

    assert len(lines) == 1
    assert lines[0].endswith(".")
    assert "\u200d." not in lines[0]
    assert report_image_renderer._text_width(draw, lines[0], base_font, bold=True) <= 80


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


def test_render_selected_empty_report_returns_standalone_png_for_each_tab():
    now = datetime.now(UTC)
    expected = {
        InventoryReportView.RESOURCES: "inventory_resources_111_1M.png",
        InventoryReportView.SPEEDUPS: "inventory_speedups_111_1M.png",
        InventoryReportView.MATERIALS: "inventory_materials_111_1M.png",
    }

    for view, filename in expected.items():
        payload = InventoryReportPayload(
            governor_id=111,
            governor_name="Empty Governor",
            view=view,
            range_key=InventoryReportRange.ONE_MONTH,
            generated_at_utc=now,
        )

        rendered = render_inventory_reports(payload)

        assert [item.filename for item in rendered] == [filename]
        image = Image.open(BytesIO(rendered[0].image_bytes.getvalue()))
        assert image.size == (report_image_renderer.WIDTH, report_image_renderer.HEIGHT)


def test_render_all_empty_preserves_legacy_no_report_output():
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Empty Governor",
        view=InventoryReportView.ALL,
        range_key=InventoryReportRange.ONE_MONTH,
        generated_at_utc=datetime.now(UTC),
    )

    assert render_inventory_reports(payload) == []


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


def test_render_inventory_reports_supports_stored_vip_profile():
    now = datetime.now(UTC)
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Gov",
        view=InventoryReportView.ALL,
        range_key=InventoryReportRange.ONE_MONTH,
        governor_profile=InventoryGovernorProfile(
            governor_id=111,
            vip_level_code="VIP_18",
            vip_level_label="VIP 18",
        ),
        resources=[
            InventoryResourcePoint(
                now,
                1_000_000_000,
                1_000_000_000,
                800_000_000,
                800_000_000,
            )
        ],
        speedups=[InventorySpeedupPoint(now, 1, 2, 3, 4, 5)],
        generated_at_utc=now,
    )

    rendered = render_inventory_reports(payload)

    assert [item.filename for item in rendered] == [
        "inventory_resources_111_1M.png",
        "inventory_speedups_111_1M.png",
    ]


def test_render_inventory_reports_returns_materials_png():
    assert (report_image_renderer.ASSET_DIR / "materials_logo.png").exists()
    now = datetime.now(UTC)
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Gov",
        view=InventoryReportView.MATERIALS,
        range_key=InventoryReportRange.ONE_MONTH,
        materials=[
            InventoryMaterialPoint(now - timedelta(days=7), 10, 20, 30, 40, 50),
            InventoryMaterialPoint(now, 20, 30, 40, 50, 60),
        ],
        generated_at_utc=now,
    )

    rendered = render_inventory_reports(payload)

    assert [item.filename for item in rendered] == ["inventory_materials_111_1M.png"]
    assert rendered[0].image_bytes.getvalue().startswith(b"\x89PNG")


def test_render_inventory_reports_handles_special_character_governor_name():
    now = datetime.now(UTC)
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="義【K98】Nunez 🚀",
        view=InventoryReportView.RESOURCES,
        range_key=InventoryReportRange.ONE_MONTH,
        resources=[
            InventoryResourcePoint(now - timedelta(days=7), 100, 200, 300, 400),
            InventoryResourcePoint(now, 200, 300, 400, 500),
        ],
        generated_at_utc=now,
    )

    rendered = render_inventory_reports(payload)

    assert [item.filename for item in rendered] == ["inventory_resources_111_1M.png"]
    image = Image.open(BytesIO(rendered[0].image_bytes.getvalue()))
    assert image.size == (report_image_renderer.WIDTH, report_image_renderer.HEIGHT)
