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
    SUMMARY_METRIC_LAYOUT,
    _last3_display_rows,
    _summary_display_value,
    build_last3_text_fallback,
    render_kvk_history_last3_card,
    render_kvk_history_summary_card,
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
            "Most Heals": 36_800_000,
            "Most DKP": 300_000_000,
            "Lowest Tanking Score": 0.85,
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
            "Most Heals": KvkHistorySummaryMetric(36_800_000, 15, 6),
            "Most DKP": KvkHistorySummaryMetric(300_000_000, 15, 7),
            "Lowest Tanking Score": KvkHistorySummaryMetric(0.85, 15, 8),
            "Most Pre-KVK": KvkHistorySummaryMetric(900_000, 15, 10),
            "Most Honor": KvkHistorySummaryMetric(800_000, 15, 11),
        },
        trends={"kills": KvkHistoryTrend(metric="kills", average=125_000_000, direction="up")},
    )


def test_history_background_assets_are_used():
    assert HISTORY_LAST3_BACKGROUND.name == "history_card1.PNG"
    assert HISTORY_SUMMARY_BACKGROUND.name == "history_card2.PNG"


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


def test_history_summary_tanking_score_displays_as_percent():
    assert _summary_display_value(0.85, "score") == "85%"


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
        "Most Heals",
        "Most DKP",
        "Lowest Tanking Score",
        "Most Pre-KVK",
        "Most Honor",
    ]


def test_last3_text_fallback_preserves_missing_acclaim():
    text = build_last3_text_fallback(_payload())

    assert "KVK 14: no row found" in text
    assert "Acclaim Missing" in text
