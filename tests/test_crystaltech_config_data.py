from datetime import datetime
from pathlib import Path
import re

import pytest

from crystaltech_config import load_and_validate_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "crystaltech_paths.v1.json"
ASSETS_PATH = ROOT / "assets" / "crystaltech"

EXPECTED_PATH_CONTRACT = {
    "f2p_low_infantry": (43, 47_997_500),
    "f2p_low_archers": (42, 47_997_500),
    "f2p_low_cavalry": (44, 53_357_500),
    "f2p_low_siege": (51, 64_189_500),
    "mid_high_infantry": (54, 59_097_500),
    "mid_high_archer": (54, 59_097_500),
    "mid_high_cavalry": (54, 58_001_500),
    "mid_high_siege": (62, 67_726_500),
}

ADDED_STEP_UIDS = {
    "f2p_low_infantry__swift_marching_ii_lv8",
    "f2p_low_infantry__cultural_exchange_lv15",
    "f2p_low_infantry__swift_marching_iii_lv10",
    "f2p_low_infantry__special_concoction_ii_lv3",
    "f2p_low_archer__cultural_exchange_lv15",
    "f2p_low_archer__fleet_of_foot_iii_lv10",
    "f2p_low_archer__special_concoction_ii_lv3",
    "f2p_low_cavalry__cultural_exchange_lv15",
    "f2p_low_cavalry__swift_steeds_iii_lv10",
    "f2p_low_cavalry__special_concoction_ii_lv3",
    "f2p_low_siege__cultural_exchange_lv15",
    "f2p_low_siege__reinforced_axles_iii_lv10",
    "f2p_low_siege__special_concoction_ii_lv3",
    "f2p_low_siege__siege_expert_lv4",
}

EXPECTED_IMAGES = {
    "archer_expert.png",
    "archers_focus.png",
    "barbarian_bounties.png",
    "call_to_arms.png",
    "cavalry_expert.png",
    "crystal_mine.png",
    "cultural_exchange.png",
    "cutting_corners.png",
    "emergency_support.png",
    "fleet_of_foot.png",
    "improved_bows.png",
    "improved_projectiles.png",
    "infantry_expert.png",
    "iron_infantry.png",
    "karaku_reports.png",
    "larger_camps.png",
    "leadership.png",
    "mounted_combat_techniques.png",
    "quenched_blades.png",
    "reinforced_axles.png",
    "research_center.png",
    "riders_resilience.png",
    "siege_expert.png",
    "siege_provisions.png",
    "special_concoctions.png",
    "starmetal_axles.png",
    "starmetal_barding.png",
    "starmetal_bracers.png",
    "starmetal_shields.png",
    "swift_marching.png",
    "swift_steeds.png",
}

EXPECTED_COMMON_BLOCKS = {
    "f2p": [
        {
            "step_uid": "f2p_common_mine_25",
            "type": "building",
            "name": {"en-GB": "Crystal Mine Upgrade"},
            "target_level": 25,
            "crystal_cost": 1_800_000,
            "image": "crystal_mine.png",
        },
        {
            "step_uid": "f2p_common_research_center_21",
            "type": "building",
            "name": {"en-GB": "Research Center Upgrade"},
            "target_level": 21,
            "crystal_cost": 900_000,
            "image": "research_center.png",
        },
    ],
    "mid_high": [
        {
            "step_uid": "mh_common_mine_25",
            "type": "building",
            "name": {"en-GB": "Crystal Mine Upgrade"},
            "target_level": 25,
            "crystal_cost": 1_800_000,
            "image": "crystal_mine.png",
        },
        {
            "step_uid": "mh_common_research_center_25",
            "type": "building",
            "name": {"en-GB": "Research Center Upgrade"},
            "target_level": 25,
            "crystal_cost": 1_800_000,
            "image": "research_center.png",
        },
    ],
}


@pytest.fixture(scope="module")
def production_config():
    config, report = load_and_validate_config(str(CONFIG_PATH), str(ASSETS_PATH))
    issue_details = "\n".join(
        f"[{issue.level}] {issue.code}: {issue.message}" for issue in report.issues
    )
    assert report.ok, f"{report.summary()}\n{issue_details}"
    assert not report.issues, f"Expected a clean validation report:\n{issue_details}"
    return config


def _steps_by_path(config):
    return {path["path_id"]: path["steps"] for path in config["paths"]}


def _step_index(config):
    return {
        step["step_uid"]: step
        for path in config["paths"]
        for step in path["steps"]
    }


def test_production_config_root_and_path_contract(production_config):
    config = production_config

    assert list(config) == ["schema_version", "meta", "locales", "blocks", "paths"]
    assert config["schema_version"] == "1.0"
    assert config["locales"] == ["en-GB"]
    assert config["meta"] == {
        "updated_at_utc": config["meta"]["updated_at_utc"],
        "effective_from_kvk": 14,
        "uid_namespacing": "path_id__<generated>",
        "includes_removed": True,
    }
    datetime.strptime(config["meta"]["updated_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
    assert config["blocks"] == {"common": EXPECTED_COMMON_BLOCKS}
    assert sum(len(steps) for steps in EXPECTED_COMMON_BLOCKS.values()) == 4

    assert [path["path_id"] for path in config["paths"]] == list(EXPECTED_PATH_CONTRACT)
    assert all(path["includes"] == [] for path in config["paths"])


def test_production_config_counts_costs_and_uid_delta(production_config):
    steps_by_path = _steps_by_path(production_config)
    all_steps = [step for steps in steps_by_path.values() for step in steps]
    all_uids = [step["step_uid"] for step in all_steps]

    assert len(all_steps) == 404
    assert len(all_uids) == len(set(all_uids))
    assert {
        path_id: (len(steps), sum(step["crystal_cost"] for step in steps))
        for path_id, steps in steps_by_path.items()
    } == EXPECTED_PATH_CONTRACT
    assert ADDED_STEP_UIDS <= set(all_uids)
    assert "f2p_low_siege__siege_expert_lv2" not in all_uids
    assert {
        step["image"] for step in all_steps
    } == EXPECTED_IMAGES, "The production config must retain the original 31-image contract"


def test_production_config_semantic_corrections(production_config):
    steps_by_path = _steps_by_path(production_config)
    step_index = _step_index(production_config)

    for path_id, steps in steps_by_path.items():
        for step in steps:
            uid = step["step_uid"]
            match = re.search(r"_lv(\d+)$", uid)
            assert match, f"Missing level suffix: {uid}"
            assert int(match.group(1)) == step["target_level"], uid

            if path_id.startswith("f2p_low_") and "karaku_reports" in uid:
                assert step["name"]["en-GB"] == "Karaku Reports"
            if path_id.startswith("f2p_low_") and "iron_infantry" in uid:
                assert step["image"] == "iron_infantry.png"
            if path_id.startswith("f2p_low_") and "special_concoction_ii" in uid:
                assert step["name"]["en-GB"] == "Special Concoction II"

    for uid in (
        "f2p_low_siege__reinforced_axles_i_lv3",
        "f2p_low_siege__reinforced_axles_i_lv5",
    ):
        assert step_index[uid]["name"]["en-GB"] == "Reinforced Axles I"

    assert (
        step_index["mid_high_cavalry__fleet_of_foot_ii_lv10"]["name"]["en-GB"]
        == "Fleet of Foot II"
    )
    assert step_index["mid_high_siege__siege_provisions_lv10"]["target_level"] == 10
    assert step_index["mid_high_siege__reinforced_axles_iii_lv10"]["target_level"] == 10


def test_production_config_regression_sensitive_ordering(production_config):
    steps_by_path = _steps_by_path(production_config)

    archer_uids = [step["step_uid"] for step in steps_by_path["f2p_low_archers"]]
    archer_index = archer_uids.index("f2p_low_archer__cultural_exchange_lv15")
    assert archer_uids[archer_index + 1] == "f2p_low_archer__larger_camps_lv5"

    cavalry_uids = [step["step_uid"] for step in steps_by_path["f2p_low_cavalry"]]
    assert cavalry_uids[31] == "f2p_low_cavalry__cultural_exchange_lv15"

    siege_uids = [step["step_uid"] for step in steps_by_path["f2p_low_siege"]]
    siege_index = siege_uids.index("f2p_low_siege__siege_provisions_lv10")
    assert siege_uids[siege_index + 1] == "f2p_low_siege__reinforced_axles_iii_lv5"


def test_review_only_workbook_fields_do_not_leak(production_config):
    forbidden_keys = {
        "Path_Order",
        "Step_Order",
        "Review_Status",
        "Reviewer_Notes",
        "Duplicate_Count",
        "UID_Level_Check",
    }
    leaked_keys = set()

    def visit(value):
        if isinstance(value, dict):
            leaked_keys.update(forbidden_keys.intersection(value))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(production_config)
    assert not leaked_keys
