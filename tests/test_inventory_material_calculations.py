import pytest

from inventory.material_calculations import (
    choice_chest_total,
    fixed_material_total,
    legendary_equivalent,
    merge_material_value_sets,
    normalize_material_kind,
    normalize_material_rarity,
    normalize_material_values,
    parse_material_quantity,
    total_legendary_equivalent,
)


def test_material_normalization_accepts_expected_aliases():
    assert normalize_material_kind("Bone") == "animal_bone"
    assert normalize_material_kind("Iron Ore") == "iron_ore"
    assert normalize_material_kind("choice chest") == "choice_chests"
    assert normalize_material_rarity("grey") == "normal"
    assert normalize_material_rarity("orange") == "legendary"


def test_parse_material_quantity_accepts_commas_and_rejects_invalid_values():
    assert parse_material_quantity("1,409") == 1409
    assert parse_material_quantity("") == 0
    assert parse_material_quantity(None) == 0
    with pytest.raises(ValueError):
        parse_material_quantity("-1")
    with pytest.raises(ValueError):
        parse_material_quantity("1.5")


def test_legendary_equivalent_formula_by_rarity():
    assert legendary_equivalent(256, "normal") == 1
    assert legendary_equivalent(64, "advanced") == 1
    assert legendary_equivalent(16, "elite") == 1
    assert legendary_equivalent(4, "epic") == 1
    assert legendary_equivalent(1, "legendary") == 1


def test_choice_chests_remain_separate_from_fixed_material_total():
    values = normalize_material_values(
        {
            "materials": {
                "choice_chests": {"legendary": 2},
                "animal_bone": {"epic": 4},
                "leather": {"legendary": 1},
                "ebony": {},
                "iron_ore": {},
            }
        }
    )

    assert fixed_material_total(values) == 2
    assert choice_chest_total(values) == 2
    assert total_legendary_equivalent(values) == 4


def test_merge_material_value_sets_warns_for_duplicates_and_blocks_conflicts():
    first = normalize_material_values({"materials": {"animal_bone": {"epic": 4}}})
    duplicate = normalize_material_values({"materials": {"animal_bone": {"epic": 4}}})
    conflict = normalize_material_values({"materials": {"animal_bone": {"epic": 8}}})

    duplicate_result = merge_material_value_sets([first, duplicate])
    conflict_result = merge_material_value_sets([first, conflict])

    assert duplicate_result.conflicts == []
    assert duplicate_result.warnings == ["Duplicate animal_bone/epic value detected; kept 4."]
    assert conflict_result.conflicts
    assert conflict_result.conflicts == [
        "Conflicting animal_bone/epic values detected; kept 4 and ignored 8."
    ]
    assert conflict_result.can_approve is False
