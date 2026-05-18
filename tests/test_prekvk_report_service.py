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


def test_build_scheduled_top_blocks_uses_report_rows_for_all_compact_blocks():
    blocks = report_service.build_scheduled_top_blocks_from_rows(_rows(), limit=1)

    assert [(entry.name, entry.points) for entry in blocks.overall] == [("Bravo", 70)]
    assert [(entry.name, entry.points) for entry in blocks.p1] == [("Bravo", 40)]
    assert [(entry.name, entry.points) for entry in blocks.p2] == [("Alpha", 30)]
    assert [(entry.name, entry.points) for entry in blocks.p3] == [("Bravo", 20)]


def test_build_scheduled_top_blocks_omits_legacy_empty_stage_blocks():
    blocks = report_service.build_scheduled_top_blocks_from_rows(
        [
            {
                "GovernorID": 1,
                "GovernorName": "Legacy",
                "Power": None,
                "OverallPoints": 50,
            }
        ]
    )

    assert [(entry.name, entry.points) for entry in blocks.overall] == [("Legacy", 50)]
    assert blocks.p1 == []
    assert blocks.p2 == []
    assert blocks.p3 == []


def test_build_prekvk_scheduled_summary_fetches_current_and_previous_once(monkeypatch):
    calls = []

    def fake_fetch(kvk_no):
        calls.append(kvk_no)
        if kvk_no == 15:
            return _rows()
        return [
            {
                "GovernorID": 3,
                "GovernorName": "Previous",
                "Power": 90_000_000,
                "Stage1Points": 9,
                "Stage2Points": 8,
                "Stage3Points": 7,
                "OverallPoints": 24,
            }
        ]

    monkeypatch.setattr(report_service.report_dal, "fetch_latest_prekvk_report_rows", fake_fetch)

    summary = report_service.build_prekvk_scheduled_summary_sync(
        kvk_no=15,
        previous_kvk_no=14,
        current_limit=3,
        previous_limit=1,
    )

    assert calls == [15, 14]
    assert summary.kvk_no == 15
    assert summary.previous_kvk_no == 14
    assert summary.current.overall[0].name == "Bravo"
    assert summary.previous.overall[0].name == "Previous"
