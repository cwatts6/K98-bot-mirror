from __future__ import annotations

from pathlib import Path

from kvk.services import kvk_reporting_service
from stats_alerts import allkingdoms


def test_reporting_service_preserves_block_keys_and_adds_contribution_fields(monkeypatch) -> None:
    raw_blocks = {
        "players_by_kills": [
            {
                "name": "Alice",
                "kills_gain": 100,
                "kp_gain": 200,
                "deads": 3,
                "dkp": 42,
                "healed_troops": 50,
                "max_contribute_gain": 7,
                "cur_contribute_gain": 8,
            }
        ],
        "kingdoms_by_kills": [{"kingdom": 1198, "kills_gain": 1000}],
        "camps_by_kills": [{"camp_name": "Camp A", "kills_gain": 900}],
    }
    captured = {}

    def fake_fetch(kvk_no: int, our_kingdom: int):
        captured["args"] = (kvk_no, our_kingdom)
        return raw_blocks

    monkeypatch.setattr(
        kvk_reporting_service.kvk_reporting_dal,
        "fetch_allkingdom_reporting_rows",
        fake_fetch,
    )

    blocks = kvk_reporting_service.load_allkingdom_reporting_blocks(12, our_kingdom=1198)

    assert captured["args"] == (12, 1198)
    assert tuple(blocks) == kvk_reporting_service.REPORTING_BLOCK_KEYS
    assert blocks["players_by_kills"][0]["max_contribute_gain"] == 7
    assert blocks["players_by_kills"][0]["cur_contribute_gain"] == 8
    assert blocks["kingdoms_by_kills"][0]["max_contribute_gain"] == 0
    assert blocks["camps_by_kills"][0]["cur_contribute_gain"] == 0
    assert blocks["players_by_deads"] == []
    assert blocks["our_camp"] == []


def test_allkingdoms_wrapper_delegates_to_reporting_service(monkeypatch) -> None:
    expected = {"players_by_kills": [{"name": "Alice"}]}

    def fake_load(kvk_no: int):
        assert kvk_no == 99
        return expected

    monkeypatch.setattr(allkingdoms, "load_allkingdom_reporting_blocks", fake_load)

    assert allkingdoms.load_allkingdom_blocks(99) is expected


def test_reporting_sql_lives_in_dal_not_allkingdoms_wrapper() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper_text = (repo_root / "stats_alerts/allkingdoms.py").read_text(encoding="utf-8")
    dal_text = (repo_root / "kvk/dal/kvk_reporting_dal.py").read_text(encoding="utf-8")

    assert "SELECT TOP" not in wrapper_text
    assert "dbo.fn_KVK_Player_Aggregated" not in wrapper_text
    assert "dbo.fn_KVK_Player_Aggregated" in dal_text
    assert "max_contribute_gain" in dal_text
    assert "cur_contribute_gain" in dal_text
