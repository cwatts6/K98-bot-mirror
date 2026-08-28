from __future__ import annotations

from io import BytesIO

from PIL import Image

from kvk.models.kvk_history_payload import (
    KvkHistoryPayload,
    KvkHistoryRow,
    KvkHistorySummaryMetric,
    KvkHistoryTrend,
)
from kvk.rendering.kvk_history_renderer import (
    HISTORY_LAST3_BACKGROUND,
    HISTORY_SUMMARY_BACKGROUND,
    HISTORY_TRENDS_BACKGROUND,
    SUMMARY_METRIC_LAYOUT,
    TREND_METRIC_LAYOUT,
    _last3_display_rows,
    _summary_display_value,
    _trend_detail,
    _trend_history_count,
    _trend_label,
    _trend_text,
    _trend_value,
    build_last3_text_fallback,
    render_kvk_history_last3_card,
    render_kvk_history_summary_card,
    render_kvk_history_trends_card,
)


def _payload() -> KvkHistoryPayload:
    rows = (
        KvkHistoryRow(
            kvk_no=13,
            row_present=True,
            kvk_rank=10,
            kills=100_000_000,
            kill_target_percent=80.0,
            deads=1_000_000,
            dead_target_percent=50.0,
            dkp=200_000_000,
            dkp_target_percent=70.0,
            acclaim=None,
            heals=None,
            kill_points=44_000_000,
            tanking_score=None,
        ),
        KvkHistoryRow(kvk_no=14, row_present=False),
        KvkHistoryRow(
            kvk_no=15,
            row_present=True,
            kvk_rank=5,
            kills=150_000_000,
            kill_target_percent=120.0,
            deads=2_000_000,
            dead_target_percent=100.0,
            dkp=300_000_000,
            dkp_target_percent=110.0,
            acclaim=12_000,
            heals=36_800_000,
            kill_points=55_000_000,
            tanking_score=85.0,
        ),
    )
    return KvkHistoryPayload(
        governor_id="2441482",
        governor_name="Tester",
        started_kvks=(13, 14, 15),
        last3_kvks=(13, 14, 15),
        rows=rows,
        last3_rows=rows,
        history_summary={
            "Highest Rank": 5,
            "Autarchs": 2,
            "KVK Played": 3,
            "Highest Acclaim": 12_000,
            "Most Kills": 150_000_000,
            "Most KillPoints": 55_000_000,
            "Most Deads": 2_000_000,
            "Lowest Healed": 36_800_000,
            "Most DKP": 300_000_000,
            "Highest Tanking Score": 85.0,
            "Most Pre-KVK": 900_000,
            "Most Honor": 800_000,
        },
        history_summary_metrics={
            "Highest Rank": KvkHistorySummaryMetric(5, 15),
            "Autarchs": KvkHistorySummaryMetric(2, 15),
            "KVK Played": KvkHistorySummaryMetric(3, 15),
            "Highest Acclaim": KvkHistorySummaryMetric(12_000, 15, 9),
            "Most Kills": KvkHistorySummaryMetric(150_000_000, 15, 3),
            "Most KillPoints": KvkHistorySummaryMetric(55_000_000, 15, 4),
            "Most Deads": KvkHistorySummaryMetric(2_000_000, 15, 5),
            "Lowest Healed": KvkHistorySummaryMetric(36_800_000, 15, 6),
            "Most DKP": KvkHistorySummaryMetric(300_000_000, 15, 7),
            "Highest Tanking Score": KvkHistorySummaryMetric(85.0, 15, 8),
            "Most Pre-KVK": KvkHistorySummaryMetric(900_000, 15, 10),
            "Most Honor": KvkHistorySummaryMetric(800_000, 15, 11),
        },
        trends={
            "rank": KvkHistoryTrend("rank", 7.5, "up", 10, 5, 2),
            "last3_kills": KvkHistoryTrend(
                "last3_kills", 125_000_000, "up", 100_000_000, 150_000_000, 2
            ),
            "kills": KvkHistoryTrend("kills", 125_000_000, "down", 200_000_000, 150_000_000, 2),
            "kill_target_percent": KvkHistoryTrend(
                "kill_target_percent", 100.0, "up", 80.0, 120.0, 2
            ),
            "deads": KvkHistoryTrend("deads", 1_500_000, "down", 1_000_000, 2_000_000, 2),
            "dead_target_percent": KvkHistoryTrend(
                "dead_target_percent", 75.0, "down", 50.0, 100.0, 2
            ),
            "heals": KvkHistoryTrend(
                "heals", 36_800_000, "insufficient", 36_800_000, 36_800_000, 1
            ),
            "dkp": KvkHistoryTrend("dkp", 250_000_000, "up", 200_000_000, 300_000_000, 2),
            "dkp_target_percent": KvkHistoryTrend("dkp_target_percent", 90.0, "up", 70.0, 110.0, 2),
            "acclaim": KvkHistoryTrend("acclaim", 12_000, "insufficient", 12_000, 12_000, 1),
            "kill_points": KvkHistoryTrend(
                "kill_points", 49_500_000, "up", 44_000_000, 55_000_000, 2
            ),
            "tanking_score": KvkHistoryTrend("tanking_score", 0.85, "insufficient", 0.85, 0.85, 1),
        },
    )


def test_history_background_assets_are_used():
    assert HISTORY_LAST3_BACKGROUND.name == "history_card1.PNG"
    assert HISTORY_SUMMARY_BACKGROUND.name == "history_card2.PNG"
    assert HISTORY_TRENDS_BACKGROUND.name == "history_card3.PNG"


def test_history_last3_card_renders_png():
    rendered = render_kvk_history_last3_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_history_last3_2441482.png"
    image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
    assert image.format == "PNG"
    assert image.size == (1180, 640)


def test_history_last3_display_rows_are_descending():
    assert [row.kvk_no for row in _last3_display_rows(_payload())] == [15, 14, 13]


def test_history_summary_card_renders_png():
    rendered = render_kvk_history_summary_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_history_summary_2441482.png"
    assert Image.open(BytesIO(rendered.image_bytes.getvalue())).size == (1180, 640)


def test_history_trends_card_renders_png():
    rendered = render_kvk_history_trends_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_history_trends_2441482.png"
    assert Image.open(BytesIO(rendered.image_bytes.getvalue())).size == (1180, 640)


def test_history_summary_tanking_score_displays_as_percent():
    assert _summary_display_value(85.0, "score") == "85%"


def test_history_summary_layout_matches_requested_metric_order():
    labels = [title for row in SUMMARY_METRIC_LAYOUT for title, _key, _color, _kind in row]

    assert labels == [
        "Highest Rank",
        "Autarchs",
        "KVK Played",
        "Highest Acclaim",
        "Most Kills",
        "Most KillPoints",
        "Most Deads",
        "Lowest Healed",
        "Most DKP",
        "Highest Tanking Score",
        "Most Pre-KVK",
        "Most Honor",
    ]


def test_history_trends_layout_includes_phase_4biii_metrics():
    labels = [title for title, _key, _color, _kind in TREND_METRIC_LAYOUT]

    assert labels == [
        "Rank",
        "Kills",
        "Deads",
        "Healed",
        "DKP",
        "Acclaim",
        "KillPoints",
        "Tanking Score",
    ]


def test_history_header_uses_last3_kills_trend_when_all_history_differs():
    label, _color = _trend_label(_payload())

    assert label == "Up"


def test_history_trend_down_copy_is_performance_oriented():
    assert _trend_text("down") == "Declined"


def test_history_trend_rank_average_rounds_instead_of_truncating():
    assert _trend_value(7.9, "rank") == "#8"


def test_history_trend_rank_average_rounds_half_up():
    assert _trend_value(6.5, "rank") == "#7"


def test_history_trend_detail_uses_readable_two_line_copy():
    trend = KvkHistoryTrend("rank", 4.4, "up", 6, 3, 3)

    assert _trend_detail(trend, "rank") == "#6 to #3, Avg #4"


def test_history_trend_history_count_uses_present_rows():
    assert _trend_history_count(_payload()) == 2


def test_last3_text_fallback_preserves_missing_acclaim():
    text = build_last3_text_fallback(_payload())

    assert "KVK 14: no row found" in text
    assert "Acclaim Missing" in text
