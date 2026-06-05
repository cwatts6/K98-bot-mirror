from __future__ import annotations

import pytest

from kvk.models.kvk_stats_card import KvkStatsCardContext
from kvk.services.kvk_stats_card_service import (
    build_kvk_stats_card_payload,
    kill_progress_policy,
)


@pytest.mark.asyncio
async def test_build_payload_includes_kvk_mode_and_camp():
    row = {
        "Gov_ID": "58744139",
        "Governor_Name": "Toraki",
        "Rank": 8,
        "KVK_NO": 54,
        "KVK_RANK": 23,
        "LAST_REFRESH": "2026-06-03T07:53:00+00:00",
        "Starting Power": 146_110_000,
        "Power_Delta": -20_129_000,
        "T4&T5_Kills": 955_512_000,
        "Kill Target": 1_000_000_000,
        "Deads_Delta": 33_000_000,
        "Dead_Target": 30_000_000,
        "DKP_SCORE": 88_000_000,
        "DKP Target": 80_000_000,
        "HealedTroopsDelta": 31_950_650,
        "KillPointsDelta": 955_512_000,
        "Acclaim": 24_500,
        "KvKPlayed": 8,
        "MostKvKKill": 1_200_000_000,
    }
    context = KvkStatsCardContext(
        kvk_name="Tides of War",
        kingdom=1978,
        camp_name="Wind",
        overall_kvk_rank=41,
        overall_kvk_total_governors=8_734,
        overall_kvk_percentile=0.47,
    )

    payload = await build_kvk_stats_card_payload(row, context=context)

    assert payload.display_mode == "Tides of War"
    assert payload.kingdom == 1978
    assert payload.display_camp == "Wind"
    assert payload.kingdom_rank == 8
    assert payload.kvk_rank == 23
    assert payload.overall_kvk_rank == 41
    assert payload.overall_kvk_total_governors == 8_734
    assert payload.overall_kvk_percentile == pytest.approx(0.47)
    assert payload.kp_loss == 639_013_000
    assert payload.playstyle == "Sniping Kills"
    assert payload.kill_progress.percent == pytest.approx(95.5512)
    assert payload.kill_progress.quote == "So close, push now!"


@pytest.mark.asyncio
async def test_build_payload_handles_zero_kp_without_tanking_score():
    payload = await build_kvk_stats_card_payload(
        {
            "GovernorID": "123",
            "GovernorName": "Zero KP",
            "KillPointsDelta": 0,
            "HealedTroopsDelta": 100,
        },
        context=KvkStatsCardContext(kvk_name="Tides of War"),
    )

    assert payload.kp_loss == 2_000
    assert payload.tanking_score_percent is None
    assert payload.playstyle is None


@pytest.mark.asyncio
async def test_build_payload_preserves_zero_healed_value():
    payload = await build_kvk_stats_card_payload(
        {
            "GovernorID": "123",
            "GovernorName": "Zero Heal",
            "KillPointsDelta": 100,
            "HealedTroopsDelta": 0,
        },
        context=KvkStatsCardContext(kvk_name="Tides of War"),
    )

    assert payload.healed == 0
    assert payload.kp_loss == 0
    assert payload.tanking_score_percent == 0
    assert payload.playstyle == "Sniping Kills"


def test_kill_progress_policy_preserves_existing_threshold_quotes():
    assert kill_progress_policy(101) == ("#FFD357", "Smashed it! Don't stop!!")
    assert kill_progress_policy(86) == ("#006400", "So close, push now!")
    assert kill_progress_policy(10) == ("#8B0000", "FIGHT NOW!!")
    assert kill_progress_policy(None, is_exempt=True) == (
        "#666666",
        "No targets assigned this KVK",
    )
