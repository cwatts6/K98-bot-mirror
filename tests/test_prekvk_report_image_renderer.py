from pathlib import Path

from prekvk import report_image_renderer
from prekvk.models import PreKvkReportPayload, PreKvkReportRow, PreKvkReportSort
from prekvk.report_image_renderer import render_prekvk_report


def test_render_prekvk_report_returns_png():
    payload = PreKvkReportPayload(
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
        rows=[
            PreKvkReportRow(
                rank=1,
                governor_id=1,
                governor_name="Alpha",
                power=100_000_000,
                stage1_points=10,
                stage2_points=20,
                stage3_points=30,
                overall_points=60,
            )
        ],
        scan_id=7,
        source_filename="PreKvK_Rankings.xlsx",
    )

    rendered = render_prekvk_report(payload)

    assert rendered is not None
    assert rendered.filename == "prekvk_report_kvk15_overall_top10.png"
    assert rendered.image_bytes.getvalue().startswith(b"\x89PNG")


def test_render_prekvk_report_handles_symbol_names():
    fox = "Fox\U0001f98a"
    bracketed = "\u3010 Laki \u3011"
    astronaut = "Orbit\U0001f469\u200d\U0001f680"
    flag = "Flag\U0001f1ec\U0001f1e7"
    thumbs_up = "Boost\U0001f44d\U0001f3fd"
    laki = "\u30c5 Laki \u0e5b"
    fox_yi = "Fox\u4e49"
    viper = "\u4e49V\u00ecper\u4e49"
    fart = "\u30c5 Fart \u0e5b"
    payload = PreKvkReportPayload(
        kvk_no=15,
        sort_by=PreKvkReportSort.STAGE3,
        limit=10,
        rows=[
            PreKvkReportRow(
                rank=1,
                governor_id=1,
                governor_name=fox,
                power=100_000_000,
                stage1_points=10,
                stage2_points=20,
                stage3_points=30,
                overall_points=60,
            ),
            PreKvkReportRow(
                rank=2,
                governor_id=2,
                governor_name=bracketed,
                power=90_000_000,
                stage1_points=9,
                stage2_points=19,
                stage3_points=29,
                overall_points=57,
            ),
            PreKvkReportRow(
                rank=3,
                governor_id=3,
                governor_name=astronaut,
                power=80_000_000,
                stage1_points=8,
                stage2_points=18,
                stage3_points=28,
                overall_points=54,
            ),
            PreKvkReportRow(
                rank=4,
                governor_id=4,
                governor_name=flag,
                power=70_000_000,
                stage1_points=7,
                stage2_points=17,
                stage3_points=27,
                overall_points=51,
            ),
            PreKvkReportRow(
                rank=5,
                governor_id=5,
                governor_name=thumbs_up,
                power=60_000_000,
                stage1_points=6,
                stage2_points=16,
                stage3_points=26,
                overall_points=48,
            ),
            PreKvkReportRow(
                rank=6,
                governor_id=6,
                governor_name=laki,
                power=50_000_000,
                stage1_points=5,
                stage2_points=15,
                stage3_points=25,
                overall_points=45,
            ),
            PreKvkReportRow(
                rank=7,
                governor_id=7,
                governor_name=fox_yi,
                power=40_000_000,
                stage1_points=4,
                stage2_points=14,
                stage3_points=24,
                overall_points=42,
            ),
            PreKvkReportRow(
                rank=8,
                governor_id=8,
                governor_name=viper,
                power=30_000_000,
                stage1_points=3,
                stage2_points=13,
                stage3_points=23,
                overall_points=39,
            ),
            PreKvkReportRow(
                rank=9,
                governor_id=9,
                governor_name=fart,
                power=20_000_000,
                stage1_points=2,
                stage2_points=12,
                stage3_points=22,
                overall_points=36,
            ),
        ],
    )

    rendered = render_prekvk_report(payload)

    assert rendered is not None
    assert rendered.image_bytes.getvalue().startswith(b"\x89PNG")
    assert report_image_renderer._clean_text(fox, 28) == fox
    assert report_image_renderer._clean_text(viper, 28) == viper
    assert report_image_renderer._text_clusters(astronaut)[5:] == ["\U0001f469\u200d\U0001f680"]
    assert report_image_renderer._text_clusters(flag)[4:] == ["\U0001f1ec\U0001f1e7"]
    assert report_image_renderer._text_clusters(thumbs_up)[5:] == ["\U0001f44d\U0001f3fd"]
    assert any(
        candidate.endswith("seguiemj.ttf")
        for candidate in report_image_renderer._font_candidates_for_char("\U0001f98a")
    )
    assert any(
        candidate.endswith("msyh.ttc")
        for candidate in report_image_renderer._font_candidates_for_char("\u3010")
    )
    assert any(
        candidate.endswith("LeelawUI.ttf")
        for candidate in report_image_renderer._font_candidates_for_char("\u0e5b")
    )
    assert any(
        candidate.endswith("msyh.ttc")
        for candidate in report_image_renderer._font_candidates_for_char("\u4e49")
    )
    assert any(
        candidate.endswith("msyh.ttc")
        for candidate in report_image_renderer._font_candidates_for_char("\u3400")
    )
    msyh = Path("C:/Windows/Fonts/msyh.ttc")
    if msyh.exists():
        assert report_image_renderer._font_supports_text(str(msyh), "\u4e49")
    leelaw = Path("C:/Windows/Fonts/LeelawUI.ttf")
    if leelaw.exists():
        assert report_image_renderer._font_supports_text(str(leelaw), "\u0e5b")
    assert report_image_renderer._cluster_font_size("\u30c5", 18) == 22
    assert report_image_renderer._cluster_font_size("\u0e5b", 18) == 22


def test_font_for_text_skips_unsupported_candidate(monkeypatch):
    report_image_renderer._font_for_text.cache_clear()
    used_paths = []

    monkeypatch.setattr(
        report_image_renderer,
        "_font_candidates_for_text",
        lambda text, *, bold=False: ["unsupported.ttf", "supported.ttf"],
    )
    monkeypatch.setattr(
        report_image_renderer,
        "_font_supports_text",
        lambda path, text: path == "supported.ttf",
    )

    def _fake_truetype(path, *, size):
        used_paths.append(path)
        return object()

    monkeypatch.setattr(report_image_renderer.ImageFont, "truetype", _fake_truetype)

    assert report_image_renderer._font_for_text("\u4e49", 18) is not None
    assert used_paths == ["supported.ttf"]
    report_image_renderer._font_for_text.cache_clear()


def test_font_supports_text_reuses_cached_coverage():
    report_image_renderer._font_coverage.cache_clear()
    report_image_renderer._font_supports_text.cache_clear()

    path = "C:/Windows/Fonts/definitely_missing_test_font.ttf"

    assert report_image_renderer._font_supports_text(path, "A") is False
    assert report_image_renderer._font_supports_text(path, "B") is False
    assert report_image_renderer._font_coverage.cache_info().misses == 1
    assert report_image_renderer._font_coverage.cache_info().hits == 1


def test_fit_text_to_width_truncates_by_rendered_width():
    image = report_image_renderer.Image.new("RGBA", (420, 80))
    draw = report_image_renderer.ImageDraw.Draw(image)
    font = report_image_renderer._font(18)
    text = "\u30c5" * 80

    fitted = report_image_renderer._fit_text_to_width(draw, text, width=120, font=font)

    assert fitted.endswith(".")
    assert report_image_renderer._text_width(draw, fitted, font=font) <= 120


def test_render_prekvk_report_empty_payload_returns_none():
    payload = PreKvkReportPayload(
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
        rows=[],
    )

    assert render_prekvk_report(payload) is None
