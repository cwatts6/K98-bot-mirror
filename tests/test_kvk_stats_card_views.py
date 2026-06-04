from __future__ import annotations

from dataclasses import replace

from kvk.models.kvk_stats_card import KvkStatsCardPayload, KvkTargetProgress
from ui.views.kvk_stats_card_views import build_history_embed, build_more_stats_embed


def _payload() -> KvkStatsCardPayload:
    return KvkStatsCardPayload(
        governor_id="123",
        governor_name="Card Tester",
        kvk_no=54,
        kvk_name="Tides of War",
        kingdom=1978,
        camp_name="Wind",
        last_refresh=None,
        status="INCLUDED",
        kvk_rank=12,
        matchmaking_power=100_000_000,
        kp_gain=500_000_000,
        kills_gain=300_000_000,
        kill_target=400_000_000,
        kill_progress=KvkTargetProgress(
            current=300_000_000,
            target=400_000_000,
            percent=75.0,
            color_hex="#2ecc71",
            quote="Fight more, still time!",
        ),
        deads=20_000_000,
        dead_target=20_000_000,
        dead_target_percent=100.0,
        power_loss=-5_000_000,
        healed=10_000_000,
        kp_loss=200_000_000,
        tanking_score_percent=40.0,
        playstyle="Sniping Kills",
        acclaim=10,
        dkp=25_000_000,
        dkp_target=50_000_000,
        dkp_target_percent=50.0,
        pass_stats={"Pass 4 Kills": 1_000},
        prekvk_rank=7,
        prekvk_points=123_456,
        honor_rank=9,
        honor_points=654_321,
        history_summary={"KVK Played": 3},
        personal_bests={"Most Kills": 900_000_000},
        last_kvk_summary={
            "KVK_NO": 53,
            "Kills": 250_000_000,
            "Kill Target": 300_000_000,
            "Kill Percent": 83.3,
            "Deads": 10_000_000,
            "Dead Target": 12_000_000,
            "Dead Percent": 83.3,
            "DKP": 11_000_000,
            "DKP Target": 12_000_000,
            "DKP Percent": 91.6,
            "KP": 400_000_000,
            "Acclaim": 8,
        },
        matchmaking_snapshot={"MM KP": 100_000_000},
    )


def test_more_stats_embed_uses_payload_context():
    embed = build_more_stats_embed(_payload())

    assert embed.title == "More KVK Stats - Card Tester"
    assert embed.description == "KVK 54 | Tides of War"
    assert any(field.name == "Passes" for field in embed.fields)


def test_history_embed_includes_last_kvk_summary():
    embed = build_history_embed(_payload())

    assert embed.title == "Historic KVK Data - Card Tester"
    assert any(field.name == "Last KVK Summary - KVK 53" for field in embed.fields)


def test_history_embed_filters_zero_summary_and_personal_best_rows():
    payload = replace(
        _payload(),
        history_summary={"Autarch": 0, "KVK Played": 0, "Highest Acclaim": 0},
        personal_bests={"Most Kills": 0, "Most Deads": 0, "Most Heal": 0},
        last_kvk_summary={},
        matchmaking_snapshot={"MM KP": 0, "MM Kills": 0, "MM Deads": None},
    )

    embed = build_history_embed(payload)
    field_names = [field.name for field in embed.fields]

    assert "Summary" not in field_names
    assert "Personal Bests" not in field_names
    assert "Matchmaking Snapshot" not in field_names
    assert field_names == ["Last KVK Summary"]
