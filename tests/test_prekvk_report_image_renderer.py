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


def test_render_prekvk_report_empty_payload_returns_none():
    payload = PreKvkReportPayload(
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
        rows=[],
    )

    assert render_prekvk_report(payload) is None
