from prekvk import report_service
from prekvk.models import PreKvkReportSort


def _rows():
    return [
        {
            "GovernorID": 1,
            "GovernorName": "Alpha",
            "Power": 100_000_000,
            "Stage1Points": 10,
            "Stage2Points": 30,
            "Stage3Points": 20,
            "OverallPoints": 60,
            "ScanID": 7,
            "SourceFileName": "PreKvK.xlsx",
        },
        {
            "GovernorID": 2,
            "GovernorName": "Bravo",
            "Power": 120_000_000,
            "Stage1Points": 40,
            "Stage2Points": 10,
            "Stage3Points": 20,
            "OverallPoints": 70,
            "ScanID": 7,
            "SourceFileName": "PreKvK.xlsx",
        },
    ]


def test_parse_report_sort_accepts_stage_aliases():
    assert report_service.parse_report_sort("Overall") == PreKvkReportSort.OVERALL
    assert report_service.parse_report_sort("Stage 1") == PreKvkReportSort.STAGE1
    assert report_service.parse_report_sort("stage iii") == PreKvkReportSort.STAGE3


def test_normalize_report_limit_only_allows_buttons():
    assert report_service.normalize_report_limit(25) == 25
    assert report_service.normalize_report_limit(99) == 10


def test_build_report_payload_defaults_overall_and_keeps_scan_metadata():
    payload = report_service.build_report_payload_from_rows(
        15,
        _rows(),
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
    )

    assert payload.kvk_no == 15
    assert payload.scan_id == 7
    assert payload.source_filename == "PreKvK.xlsx"
    assert [row.governor_name for row in payload.rows] == ["Bravo", "Alpha"]
    assert [row.rank for row in payload.rows] == [1, 2]


def test_build_report_payload_sorts_by_stage_and_uses_power_tiebreaker():
    payload = report_service.build_report_payload_from_rows(
        15,
        _rows(),
        sort_by=PreKvkReportSort.STAGE3,
        limit=10,
    )

    assert [row.governor_name for row in payload.rows] == ["Bravo", "Alpha"]
    assert [row.rank for row in payload.rows] == [1, 1]


def test_build_report_payload_handles_legacy_total_only_rows():
    payload = report_service.build_report_payload_from_rows(
        15,
        [
            {
                "GovernorID": 1,
                "GovernorName": "Legacy",
                "Power": None,
                "OverallPoints": 50,
            }
        ],
    )

    assert payload.has_stage_data is False
    assert payload.rows[0].stage1_points is None
    assert payload.rows[0].overall_points == 50
