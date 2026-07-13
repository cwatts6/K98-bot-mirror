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


def test_inventory_backdrop_assets_match_runtime_and_master_contract():
    expected_runtime_names = {
        InventoryReportView.RESOURCES: "inventory_resources_governoros_backdrop.png",
        InventoryReportView.SPEEDUPS: "inventory_speedups_governoros_backdrop.png",
        InventoryReportView.MATERIALS: "inventory_materials_governoros_backdrop.png",
    }

    assert set(report_image_renderer.REPORT_BACKDROP_PATHS) == set(expected_runtime_names)
    for view, expected_name in expected_runtime_names.items():
        path = report_image_renderer.REPORT_BACKDROP_PATHS[view]
        assert path.name == expected_name
        assert path.stat().st_size > 0
        assert "_master_2x" not in path.name
        with Image.open(path) as image:
            image.load()
            assert image.format == "PNG"
            assert image.size == (1400, 980)

        master_path = path.with_name(path.stem + "_master_2x.png")
        assert master_path.stat().st_size > 0
        with Image.open(master_path) as master:
            master.load()
            assert master.format == "PNG"
            assert master.size == (2800, 1960)


def test_selected_empty_reports_use_their_report_specific_backdrops():
    now = datetime.now(UTC)
    sample_pixel = (830, 0)

    for view, path in report_image_renderer.REPORT_BACKDROP_PATHS.items():
        payload = InventoryReportPayload(
            governor_id=111,
            governor_name="Backdrop Governor",
            view=view,
            range_key=InventoryReportRange.ONE_MONTH,
            generated_at_utc=now,
        )

        rendered = render_inventory_reports(payload)

        with Image.open(path) as backdrop:
            expected_pixel = backdrop.convert("RGB").getpixel(sample_pixel)
        with Image.open(BytesIO(rendered[0].image_bytes.getvalue())) as output:
            assert output.getpixel(sample_pixel) == expected_pixel
        rendered[0].image_bytes.close()


def test_runtime_renderer_never_loads_master_backdrops(monkeypatch):
    opened_paths = []
    real_open = report_image_renderer.Image.open

    def recording_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(report_image_renderer.Image, "open", recording_open)
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Runtime Governor",
        view=InventoryReportView.SPEEDUPS,
        range_key=InventoryReportRange.ONE_MONTH,
        generated_at_utc=datetime.now(UTC),
    )

    rendered = render_inventory_reports(payload)

    assert any(path.endswith("inventory_speedups_governoros_backdrop.png") for path in opened_paths)
    assert all("_master_2x" not in path for path in opened_paths)
    rendered[0].image_bytes.close()


def test_missing_corrupt_and_wrong_sized_backdrops_use_safe_fallback(tmp_path, monkeypatch):
    view = InventoryReportView.RESOURCES
    candidates = [tmp_path / "missing.png", tmp_path / "corrupt.png", tmp_path / "wrong.png"]
    candidates[1].write_bytes(b"not-a-png")
    Image.new("RGB", (40, 40), (1, 2, 3)).save(candidates[2], format="PNG")
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Fallback Governor",
        view=view,
        range_key=InventoryReportRange.ONE_MONTH,
        generated_at_utc=datetime.now(UTC),
    )

    for path in candidates:
        monkeypatch.setitem(report_image_renderer.REPORT_BACKDROP_PATHS, view, path)
        rendered = render_inventory_reports(payload)

        assert [item.filename for item in rendered] == ["inventory_resources_111_1M.png"]
        with Image.open(BytesIO(rendered[0].image_bytes.getvalue())) as output:
            assert output.size == (1400, 980)
            assert output.getpixel((830, 0)) == report_image_renderer.BG
        rendered[0].image_bytes.close()


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


def test_white_icon_background_cleanup_uses_pillow_11_compatible_pixel_access(monkeypatch):
    def fail_if_newer_api_is_used(_image):
        raise AssertionError("Pillow 11.3 does not provide get_flattened_data")

    monkeypatch.setattr(
        Image.Image,
        "get_flattened_data",
        fail_if_newer_api_is_used,
        raising=False,
    )
    canvas = Image.new("RGBA", (96, 96), (0, 0, 0, 0))

    report_image_renderer._paste_icon(
        canvas,
        report_image_renderer.ASSET_DIR / "speedup_logo.png",
        (8, 8, 88, 88),
    )

    assert canvas.getbbox() is not None
    assert canvas.getpixel((8, 8))[3] == 0


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
        assert item.image_bytes.tell() == 0
        assert not item.image_bytes.closed
        item.image_bytes.close()
        assert item.image_bytes.closed


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


def test_resources_preserve_kpi_values_deltas_chart_series_and_legend(monkeypatch):
    now = datetime.now(UTC)
    points = [
        InventoryResourcePoint(
            now - timedelta(days=7), 1_000_000_000, 2_000_000_000, 3_000_000_000, 4_000_000_000
        ),
        InventoryResourcePoint(now, 1_100_000_000, 2_200_000_000, 3_300_000_000, 4_400_000_000),
    ]
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Gov",
        view=InventoryReportView.RESOURCES,
        range_key=InventoryReportRange.ONE_MONTH,
        resources=points,
        generated_at_utc=now,
    )
    kpis = []
    chart = {}

    monkeypatch.setattr(
        report_image_renderer,
        "_draw_kpi",
        lambda *_args, **kwargs: kpis.append(kwargs),
    )

    def capture_chart(*args, **kwargs):
        chart.update(series=args[3], labels=args[4], colors=args[5], kwargs=kwargs)

    monkeypatch.setattr(report_image_renderer, "_line_chart", capture_chart)

    rendered = report_image_renderer.render_resources_report(payload)

    assert [(item["title"], item["value"], item["delta"]) for item in kpis[:5]] == [
        ("Food", "1.1B", "+100M"),
        ("Wood", "2.2B", "+200M"),
        ("Stone", "3.3B", "+300M"),
        ("Gold", "4.4B", "+400M"),
        ("Total RSS", "11B", "+1B"),
    ]
    assert chart["series"] == {
        "Food": [1_000_000_000.0, 1_100_000_000.0],
        "Wood": [2_000_000_000.0, 2_200_000_000.0],
        "Stone": [3_000_000_000.0, 3_300_000_000.0],
        "Gold": [4_000_000_000.0, 4_400_000_000.0],
    }
    assert chart["colors"] == [
        report_image_renderer.RESOURCE_CHART_COLORS[name] for name in chart["series"]
    ]
    assert chart["kwargs"] == {}
    assert rendered is not None
    rendered.image_bytes.close()


def test_speedups_preserve_days_deltas_chart_series_and_units(monkeypatch):
    now = datetime.now(UTC)
    points = [
        InventorySpeedupPoint(now - timedelta(days=7), 1, 2, 20, 30, 10),
        InventorySpeedupPoint(now, 2, 3, 27, 29, 15),
    ]
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Gov",
        view=InventoryReportView.SPEEDUPS,
        range_key=InventoryReportRange.ONE_MONTH,
        speedups=points,
        generated_at_utc=now,
    )
    kpis = []
    chart = {}
    monkeypatch.setattr(
        report_image_renderer,
        "_draw_kpi",
        lambda *_args, **kwargs: kpis.append(kwargs),
    )

    def capture_chart(*args, **kwargs):
        chart.update(series=args[3], colors=args[5], kwargs=kwargs)

    monkeypatch.setattr(report_image_renderer, "_line_chart", capture_chart)

    rendered = report_image_renderer.render_speedups_report(payload)

    assert [(item["title"], item["value"], item["delta"]) for item in kpis[:3]] == [
        ("Universal", "15d", "+5d"),
        ("Training", "27d", "+7d"),
        ("Healing", "29d", "-1d"),
    ]
    assert chart["series"] == {
        "Universal": [10, 15],
        "Training": [20, 27],
        "Healing": [30, 29],
    }
    assert chart["colors"] == [(250, 204, 21), (96, 165, 250), (248, 113, 113)]
    assert chart["kwargs"] == {"y_suffix": "d"}
    assert rendered is not None
    rendered.image_bytes.close()


def test_materials_preserve_values_deltas_chart_series_and_legend(monkeypatch):
    now = datetime.now(UTC)
    points = [
        InventoryMaterialPoint(now - timedelta(days=7), 10, 20, 30, 40, 50),
        InventoryMaterialPoint(now, 20, 30, 40, 50, 60),
    ]
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name="Gov",
        view=InventoryReportView.MATERIALS,
        range_key=InventoryReportRange.ONE_MONTH,
        materials=points,
        generated_at_utc=now,
    )
    kpis = []
    chart = {}
    monkeypatch.setattr(
        report_image_renderer,
        "_draw_kpi",
        lambda *_args, **kwargs: kpis.append(kwargs),
    )

    def capture_chart(*args, **_kwargs):
        chart.update(series=args[3], colors=args[5])

    monkeypatch.setattr(report_image_renderer, "_line_chart", capture_chart)

    rendered = report_image_renderer.render_materials_report(payload)

    assert [(item["title"], item["value"], item["delta"]) for item in kpis[:5]] == [
        ("Bone", "20.0", "+10"),
        ("Leather", "30.0", "+10"),
        ("Ebony", "40.0", "+10"),
        ("Iron", "50.0", "+10"),
        ("Choice Chests", "60.0", "+10"),
    ]
    assert chart["series"] == {
        "Bone": [10, 20],
        "Leather": [20, 30],
        "Ebony": [30, 40],
        "Iron": [40, 50],
        "Choice Chests": [50, 60],
    }
    assert chart["colors"] == [
        report_image_renderer.MATERIAL_CHART_COLORS[name] for name in chart["series"]
    ]
    assert rendered is not None
    rendered.image_bytes.close()


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


def test_long_unicode_governor_context_uses_header_width_fitting(monkeypatch):
    now = datetime.now(UTC)
    governor_name = ("義【K98】👩‍🚀 กษัตริย์ ") * 10
    payload = InventoryReportPayload(
        governor_id=111,
        governor_name=governor_name,
        view=InventoryReportView.MATERIALS,
        range_key=InventoryReportRange.TWELVE_MONTHS,
        materials=[InventoryMaterialPoint(now, 10, 20, 30, 40, 50)],
        generated_at_utc=now,
    )
    calls = []
    real_fit_font = report_image_renderer._fit_font

    def recording_fit_font(draw, text, **kwargs):
        if text.startswith(governor_name):
            calls.append(kwargs)
        return real_fit_font(draw, text, **kwargs)

    monkeypatch.setattr(report_image_renderer, "_fit_font", recording_fit_font)

    rendered = render_inventory_reports(payload)

    assert calls == [{"max_width": 1210, "size": 20, "min_size": 14}]
    with Image.open(BytesIO(rendered[0].image_bytes.getvalue())) as image:
        assert image.size == (1400, 980)
    rendered[0].image_bytes.close()
