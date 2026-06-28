from __future__ import annotations

from io import BytesIO

from PIL import Image

from kvk.models.kvk_rankings import RankingPayload, RankingRow
from kvk.rendering.kvk_rankings_card_renderer import (
    _background_path,
    _context_line,
    _current_rankings_overlay,
    _draw_top_card,
    _footer,
    _ranking_background,
    _records_context_line,
    _records_count_label,
    _records_darkening_overlay,
    _records_total_label,
    _support_text,
    can_render_current_rankings_top10_card,
    can_render_kvk_rankings_top10_card,
    render_current_rankings_top10_card,
    render_hall_of_fame_top10_card,
    render_kvk_rankings_top10_card,
)


def _payload(
    *,
    mode: str = "kvk",
    metric: str = "kills",
    metric_label: str = "Kills",
    limit: int = 10,
    rows: int = 10,
) -> RankingPayload:
    mode_label = {"kvk": "KVK", "honor": "Honor", "prekvk": "PreKvK"}.get(mode, "KVK")
    return RankingPayload(
        mode=mode,
        mode_label=mode_label,
        metric=metric,
        metric_label=metric_label,
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
                    "Governor ID": str(1000 + idx),
                    "KVK": 3,
                    "Stage 1": 1_500_000 - (idx * 10_000),
                    "Stage 2": 1_300_000 - (idx * 10_000),
                    "Stage 3": 1_100_000 - (idx * 10_000),
                    "Overall": 3_900_000 - (idx * 30_000),
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
    rendered = render_current_rankings_top10_card(_payload())

    assert rendered is not None
    assert rendered.filename == "kvk_rankings_top10_kills.png"
    image_bytes = rendered.image_bytes.getvalue()
    assert image_bytes.startswith(b"\x89PNG")

    with Image.open(BytesIO(image_bytes)) as image:
        assert image.size == (1180, 640)


def test_current_rankings_top10_card_renders_honor_and_prekvk_modes():
    honor = render_current_rankings_top10_card(
        _payload(mode="honor", metric="honor", metric_label="Honor")
    )
    prekvk = render_current_rankings_top10_card(
        _payload(mode="prekvk", metric="overall", metric_label="Overall")
    )

    assert honor is not None
    assert honor.filename == "kvk_rankings_honor_top10_honor.png"
    assert honor.image_bytes.getvalue().startswith(b"\x89PNG")
    assert prekvk is not None
    assert prekvk.filename == "kvk_rankings_prekvk_top10_overall.png"
    assert prekvk.image_bytes.getvalue().startswith(b"\x89PNG")


def test_kvk_rankings_top10_card_only_handles_current_top10_modes():
    assert render_current_rankings_top10_card(_payload(limit=25)) is None
    assert render_current_rankings_top10_card(_records_payload()) is None
    assert render_current_rankings_top10_card(_payload(rows=0)) is None


def test_kvk_rankings_top10_card_aliases_current_renderer_for_compatibility():
    payload = _payload(mode="honor", metric="honor", metric_label="Honor")

    assert can_render_kvk_rankings_top10_card(payload) is True
    assert can_render_kvk_rankings_top10_card(payload) == can_render_current_rankings_top10_card(
        payload
    )
    rendered = render_kvk_rankings_top10_card(payload)
    assert rendered is not None
    assert rendered.filename == "kvk_rankings_honor_top10_honor.png"


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


def test_current_rankings_top10_card_mode_specific_context_and_support_copy():
    honor_payload = _payload(mode="honor", metric="honor", metric_label="Honor")
    prekvk_payload = _payload(mode="prekvk", metric="overall", metric_label="Overall")

    assert _context_line(honor_payload) == "Top 10  |  KVK 3"
    assert _support_text(honor_payload, honor_payload.rows[0]) == "Governor ID 1001  |  KVK 3"
    assert _context_line(prekvk_payload) == "Top 10  |  KVK 3"
    assert _support_text(prekvk_payload, prekvk_payload.rows[0]) == (
        "Stage 1 1.5M  |  Stage 2 1.3M"
    )


def test_current_rankings_top10_card_honor_and_prekvk_footer_only_shows_freshness():
    honor_payload = _payload(mode="honor", metric="honor", metric_label="Honor")
    prekvk_payload = _payload(mode="prekvk", metric="overall", metric_label="Overall")

    assert _footer(honor_payload) == "Last refreshed 2026-06-18 12:00 UTC"
    assert _footer(prekvk_payload) == "Last refreshed 2026-06-18 12:00 UTC"


def test_current_kvk_top10_podium_uses_centered_text_path(monkeypatch):
    calls = []

    def fake_centered(*_args, **kwargs):
        calls.append(kwargs)

    def fail_legacy(*_args, **_kwargs):
        raise AssertionError("KVK podium should use centered text rendering")

    monkeypatch.setattr(
        "kvk.rendering.kvk_rankings_card_renderer._draw_shadowed_center_fitted",
        fake_centered,
    )
    monkeypatch.setattr("kvk.rendering.kvk_rankings_card_renderer._draw_fitted", fail_legacy)
    monkeypatch.setattr("kvk.rendering.kvk_rankings_card_renderer._draw_text", fail_legacy)

    payload = _payload(mode="kvk", metric="kills", metric_label="Kills", rows=1)
    row = payload.rows[0]
    _draw_top_card(
        object(),
        payload=payload,
        row=row,
        box=(100, 150, 400, 348),
        accent=(255, 255, 0),
    )

    assert [call["text"] for call in calls] == [
        "#1",
        row.governor_name,
        "148.8M",
        "Power 90M  |  DKP 114.1M",
    ]
    assert {call["center_x"] for call in calls} == {250}


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


def test_current_rankings_overlay_is_cached():
    overlay = _current_rankings_overlay()

    assert _current_rankings_overlay() is overlay
    assert overlay.size == (1180, 640)


def test_ranking_background_cache_is_reused_without_mutation():
    _ranking_background.cache_clear()
    payload = _payload()
    background = _background_path(payload.mode)
    assert background is not None

    assert render_current_rankings_top10_card(payload) is not None
    cached_image = _ranking_background(background)
    sampled_pixel = cached_image.getpixel((10, 10))

    cached = _ranking_background.cache_info()
    assert cached.misses == 1
    assert render_current_rankings_top10_card(payload) is not None

    cached = _ranking_background.cache_info()
    assert cached.hits == 2
    assert cached.misses == 1
    assert cached_image.getpixel((10, 10)) == sampled_pixel
