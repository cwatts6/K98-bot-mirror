from __future__ import annotations

from io import BytesIO

from PIL import Image

from kvk.models.kvk_history_payload import KvkHistoryPayload, KvkHistoryRow, KvkHistoryTrend
from kvk.rendering.kvk_history_renderer import (
    HISTORY_LAST3_BACKGROUND,
    HISTORY_SUMMARY_BACKGROUND,
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
            "KVK Played": 3,
            "Highest Acclaim": 12_000,
            "Most Kills": 150_000_000,
            "Most Deads": 2_000_000,
            "Most Heal": None,
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


def test_history_summary_card_renders_png():
    rendered = render_kvk_history_summary_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_history_summary_2441482.png"
    assert Image.open(BytesIO(rendered.image_bytes.getvalue())).size == (1180, 640)


def test_last3_text_fallback_preserves_missing_acclaim():
    text = build_last3_text_fallback(_payload())

    assert "KVK 14: no row found" in text
    assert "Acclaim Missing" in text
