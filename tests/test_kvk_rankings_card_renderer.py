from __future__ import annotations

from io import BytesIO

from PIL import Image

from kvk.models.kvk_rankings import RankingPayload, RankingRow
from kvk.rendering.kvk_rankings_card_renderer import (
    _records_context_line,
    _records_count_label,
    _records_darkening_overlay,
    _records_total_label,
    _support_text,
    render_hall_of_fame_top10_card,
    render_kvk_rankings_top10_card,
)


def _payload(*, mode: str = "kvk", limit: int = 10, rows: int = 10) -> RankingPayload:
    return RankingPayload(
        mode=mode,
        mode_label="KVK",
        metric="kills",
        metric_label="Kills",
        limit=limit,
        kvk_no=3,
        total_rows=63,
        freshness_label="2026-06-18 12:00 UTC",
        source_note="Current KVK stats cache",
        filters=("STATUS = INCLUDED", "Starting Power >= 40M"),
        rows=[
            RankingRow(
                rank=idx,
                governor_id=1000 + idx,
                governor_name=f"Top Player {idx} With A Very Long Name",
                value=150_000_000 - (idx * 1_250_000),
                supporting_values={
                    "Power": 90_000_000 + idx,
                    "Kills": 150_000_000 - (idx * 1_250_000),
                    "DKP": 115_000_000 - (idx * 900_000),
                    "Acclaim": 10_000_000 - (idx * 10_000),
                    "Tanking Score": 80.0 + idx,
                    "Kill Points": 200_000_000 - (idx * 1_000_000),
                    "Healed": 10_000_000 - (idx * 100_000),
                },
            )
            for idx in range(1, rows + 1)
        ],
    )


def _records_payload(*, mode: str = "records", limit: int = 10, rows: int = 10) -> RankingPayload:
    return RankingPayload(
        mode=mode,
        metric="killpoints",
        metric_label="KillPoints",
        limit=limit,
        source_note="Single-KVK performances across started KVKs",
        rows=[
            RankingRow(
                rank=idx,
                governor_id=2000 + idx,
                governor_name=f"Record Holder {idx} With A Long Name",
                value=225_000_000 - (idx * 2_500_000),
                kvk_no=20 - idx,
                kvk_name="Heroic Anthem",
            )
            for idx in range(1, rows + 1)
        ],
    )


def test_kvk_rankings_top10_card_renders_from_payload_rows():
    rendered = render_kvk_rankings_top10_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_rankings_top10_kills.png"
    image_bytes = rendered.image_bytes.getvalue()
    assert image_bytes.startswith(b"\x89PNG")

    with Image.open(BytesIO(image_bytes)) as image:
        assert image.size == (1180, 640)


def test_kvk_rankings_top10_card_only_handles_current_kvk_top10():
    assert render_kvk_rankings_top10_card(_payload(limit=25)) is None
    assert render_kvk_rankings_top10_card(_payload(mode="honor")) is None
    assert render_kvk_rankings_top10_card(_payload(rows=0)) is None


def test_kvk_rankings_top10_card_metric_support_texts_match_card_copy():
    payload = _payload()
    row = payload.rows[0]

    acclaim_payload = RankingPayload(
        **{**payload.__dict__, "metric": "acclaim", "metric_label": "Acclaim"}
    )
    tanking_payload = RankingPayload(
        **{**payload.__dict__, "metric": "tanking_score", "metric_label": "Tanking Score"}
    )

    assert _support_text(acclaim_payload, row) == "Kills 148.8M  |  Healed 9.9M"
    assert _support_text(tanking_payload, row) == "Kill Points 199M  |  Healed 9.9M"


def test_hall_of_fame_top10_card_renders_from_records_payload_rows():
    rendered = render_hall_of_fame_top10_card(_records_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_hall_of_fame_top10_killpoints.png"
    image_bytes = rendered.image_bytes.getvalue()
    assert image_bytes.startswith(b"\x89PNG")

    with Image.open(BytesIO(image_bytes)) as image:
        assert image.size == (1180, 640)


def test_hall_of_fame_top10_card_only_handles_records_top10():
    assert render_hall_of_fame_top10_card(_records_payload(limit=25)) is None
    assert render_hall_of_fame_top10_card(_records_payload(mode="kvk")) is None
    assert render_hall_of_fame_top10_card(_records_payload(rows=0)) is None


def test_hall_of_fame_top10_card_context_mentions_single_kvk_records():
    payload = _records_payload()

    assert _records_context_line(payload) == "Top 10 all-time single-KVK KillPoints"


def test_hall_of_fame_top10_card_summary_uses_metric_record_denominator():
    payload = RankingPayload(
        mode="records",
        metric="kills",
        metric_label="Kills",
        limit=10,
        total_rows=1234,
        rows=[
            RankingRow(rank=1, governor_id=101, governor_name="One", value=100),
            RankingRow(rank=2, governor_id=101, governor_name="One", value=90),
            RankingRow(rank=3, governor_id=202, governor_name="Two", value=80),
        ],
    )

    assert _records_count_label(payload) == "TOP 10"
    assert _records_total_label(payload) == "from 1,234 records"


def test_hall_of_fame_darkening_overlay_is_cached_and_symmetric():
    overlay = _records_darkening_overlay()

    assert _records_darkening_overlay() is overlay
    width, height = overlay.size
    for y in (0, height // 2, height - 1):
        assert overlay.getpixel((0, y)) == overlay.getpixel((width - 1, y))
        assert overlay.getpixel((1, y)) == overlay.getpixel((width - 2, y))
