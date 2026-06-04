from __future__ import annotations

from io import BytesIO

from PIL import Image

from kvk.models.kvk_stats_card import (
    KvkStatsCardPayload,
    KvkTargetProgress,
)
from kvk.rendering.kvk_stats_card_renderer import _pct, _progress_scale, render_kvk_stats_card


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


def test_progress_scale_expands_to_next_useful_cap():
    assert _progress_scale(95) == [0, 25, 50, 75, 100]
    assert _progress_scale(126) == [0, 25, 50, 75, 100, 125, 150]
