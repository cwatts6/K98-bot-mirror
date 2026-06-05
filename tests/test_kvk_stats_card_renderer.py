from __future__ import annotations

from dataclasses import replace
from io import BytesIO

from PIL import Image

from kvk.models.kvk_stats_card import (
    KvkStatsCardPayload,
    KvkTargetProgress,
)
from kvk.rendering.kvk_stats_card_renderer import (
    _background_for_mode,
    _compact,
    _history_background,
    _pct,
    _progress_scale,
    render_kvk_history_card,
    render_kvk_more_stats_card,
    render_kvk_stats_card,
)


def _payload() -> KvkStatsCardPayload:
    return KvkStatsCardPayload(
        governor_id="58744139",
        governor_name="Toraki",
        kvk_no=54,
        kvk_name="Tides of War",
        kingdom=1978,
        camp_name="Wind",
        last_refresh="2026-06-03 07:53 UTC",
        status="INCLUDED",
        kvk_rank=23,
        matchmaking_power=146_110_000,
        kp_gain=955_512_000,
        kills_gain=955_512_000,
        kill_target=1_000_000_000,
        kill_progress=KvkTargetProgress(
            current=955_512_000,
            target=1_000_000_000,
            percent=95.5512,
            color_hex="#006400",
            quote="So close, push now!",
        ),
        deads=33_000_000,
        dead_target=30_000_000,
        dead_target_percent=110.0,
        power_loss=-20_129_000,
        healed=31_950_650,
        kp_loss=639_013_000,
        tanking_score_percent=66.877,
        playstyle="Sniping Kills",
        acclaim=24_500,
        dkp=88_000_000,
        dkp_target=80_000_000,
        dkp_target_percent=110.0,
        pass_stats={"Pass 4 Kills": 14_300_000, "Pass 6 Kills": 4_600_000},
        prekvk_rank=22,
        prekvk_points=2_800_000,
        honor_rank=16,
        honor_points=67_200,
        history_summary={"Autarch": 3, "KVK Played": 10, "Highest Acclaim": 10_000_000},
        personal_bests={
            "Most Kills": 53_400_000,
            "Most Deads": 2_000_000,
            "Most Heal": 36_800_000,
        },
        last_kvk_summary={
            "KVK_NO": 53,
            "Kills": 36_300_000,
            "Kill Target": 15_000_000,
            "Kill Percent": 242.0,
            "Deads": 1_900_000,
            "Dead Target": 1_200_000,
            "Dead Percent": 150.0,
            "DKP": 124_000_000,
            "DKP Target": 55_000_000,
            "DKP Percent": 226.0,
            "KP": 696_500_000,
            "Acclaim": 10_000_000,
        },
        matchmaking_snapshot={
            "MM KP": 7_900_000_000,
            "MM Kills": 477_400_000,
            "MM Deads": 25_000_000,
            "MM Healed": 331_800_000,
        },
    )


def test_render_kvk_stats_card_outputs_png_with_expected_size():
    avatar = Image.new("RGB", (128, 128), (30, 90, 180))
    avatar_buf = BytesIO()
    avatar.save(avatar_buf, format="PNG")

    rendered = render_kvk_stats_card(_payload(), avatar_bytes=avatar_buf.getvalue())

    assert rendered is not None
    assert rendered.filename == "kvk_stats_58744139.png"
    assert rendered.image_bytes.getbuffer().nbytes > 10_000

    image = Image.open(BytesIO(rendered.image_bytes.getvalue()))
    assert image.format == "PNG"
    assert image.size == (1180, 640)


def test_pct_formats_compact_whole_percentages():
    assert _pct(95.0) == "95%"
    assert _pct(95.5) == "95.5%"


def test_compact_formats_large_values_to_one_decimal():
    assert _compact(124_135_000) == "124.1M"
    assert _compact(1_135_000_000) == "1.1B"
    assert _compact(18_900) == "18.9K"


def test_progress_scale_expands_to_next_useful_cap():
    assert _progress_scale(95) == [0, 25, 50, 75, 100]
    assert _progress_scale(126) == [0, 25, 50, 75, 100, 125, 150]
    assert _progress_scale(225) == [0, 25, 50, 75, 100, 125, 150, 200, 250]


def test_background_selection_uses_mode_specific_assets_and_default():
    assert _background_for_mode("Tides of War").name == "Tides_Stats_Card.png"
    assert _background_for_mode("heroic_anthem").name == "Heroic_Anthem_Stats_Card.jpg"
    assert _background_for_mode("Storm of Stratagems").name == (
        "Storm_of_Stratagems_Stats_card.png"
    )
    assert _background_for_mode("Songs of Troy").name == "Songs_of_Troy_Stats_card.jpg"
    assert _background_for_mode("Unknown Mode").name == "Default_card.jpg"
    assert _background_for_mode(None).name == "Default_card.jpg"


def test_history_background_uses_history_card_asset():
    assert _history_background().name == "History_stats_card.jpg"


def test_secondary_cards_render_pngs():
    more = render_kvk_more_stats_card(_payload())
    history = render_kvk_history_card(_payload())

    assert more is not None
    assert more.filename == "kvk_more_stats_58744139.png"
    assert Image.open(BytesIO(more.image_bytes.getvalue())).size == (1180, 640)

    assert history is not None
    assert history.filename == "kvk_history_58744139.png"
    assert Image.open(BytesIO(history.image_bytes.getvalue())).size == (1180, 640)


def test_history_card_snapshot_metrics_affect_rendered_output():
    with_snapshot = render_kvk_history_card(_payload())
    without_snapshot = render_kvk_history_card(replace(_payload(), matchmaking_snapshot={}))

    assert with_snapshot is not None
    assert without_snapshot is not None
    assert with_snapshot.image_bytes.getvalue() != without_snapshot.image_bytes.getvalue()
