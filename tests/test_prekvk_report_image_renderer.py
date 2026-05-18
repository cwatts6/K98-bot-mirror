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
        ],
    )

    rendered = render_prekvk_report(payload)

    assert rendered is not None
    assert rendered.image_bytes.getvalue().startswith(b"\x89PNG")
    assert report_image_renderer._clean_text(fox, 28) == fox
    assert report_image_renderer._text_clusters(astronaut)[5:] == ["\U0001f469\u200d\U0001f680"]
    assert report_image_renderer._text_clusters(flag)[4:] == ["\U0001f1ec\U0001f1e7"]
    assert report_image_renderer._text_clusters(thumbs_up)[5:] == ["\U0001f44d\U0001f3fd"]
    assert any(
        candidate.endswith("seguiemj.ttf")
        for candidate in report_image_renderer._font_candidates_for_char("\U0001f98a")
    )
    assert any(
        candidate.endswith("YuGothM.ttc")
        for candidate in report_image_renderer._font_candidates_for_char("\u3010")
    )


def test_render_prekvk_report_empty_payload_returns_none():
    payload = PreKvkReportPayload(
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
        rows=[],
    )

    assert render_prekvk_report(payload) is None
