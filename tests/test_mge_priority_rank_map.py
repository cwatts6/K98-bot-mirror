"""Tests for mge_priority_rank_map — options, lookups, and sort_weight ordering."""

from __future__ import annotations

from mge.mge_priority_rank_map import (
    PRIORITY_RANK_OPTIONS,
    PriorityRankOption,
    get_option_by_priority_rank,
    get_option_by_value,
    get_sort_weight,
)


def test_all_four_options_defined() -> None:
    assert len(PRIORITY_RANK_OPTIONS) == 4
    values = {o.value for o in PRIORITY_RANK_OPTIONS}
    assert values == {"high_1_5", "medium_6_10", "low_11_15", "no_preference"}


def test_all_options_have_valid_request_priority() -> None:
    valid = {"High", "Medium", "Low"}
    for opt in PRIORITY_RANK_OPTIONS:
        assert opt.request_priority in valid, f"{opt.value} has invalid priority"


def test_all_options_have_valid_preferred_rank_band() -> None:
    valid = {"1-5", "6-10", "11-15", "no_preference"}
    for opt in PRIORITY_RANK_OPTIONS:
        assert opt.preferred_rank_band in valid, f"{opt.value} has invalid rank band"


def test_sort_weight_ordering_is_high_medium_low_no_preference() -> None:
    weights = [o.sort_weight for o in PRIORITY_RANK_OPTIONS]
    assert weights == sorted(weights), "sort_weights should be in ascending order"
    assert weights[0] == 1   # High
    assert weights[1] == 2   # Medium
    assert weights[2] == 3   # Low
    assert weights[3] == 4   # No preference


def test_get_option_by_value_returns_correct_option() -> None:
    opt = get_option_by_value("high_1_5")
    assert opt is not None
    assert opt.request_priority == "High"
    assert opt.preferred_rank_band == "1-5"
    assert opt.sort_weight == 1


def test_get_option_by_value_returns_none_for_unknown() -> None:
    assert get_option_by_value("totally_unknown") is None


def test_get_option_by_priority_rank_resolves_all_four_combinations() -> None:
    cases = [
        ("High", "1-5", "high_1_5"),
        ("Medium", "6-10", "medium_6_10"),
        ("Low", "11-15", "low_11_15"),
        ("Low", "no_preference", "no_preference"),
    ]
    for priority, rank_band, expected_value in cases:
        opt = get_option_by_priority_rank(priority, rank_band)
        assert opt is not None, f"Expected match for ({priority}, {rank_band})"
        assert opt.value == expected_value


def test_get_option_by_priority_rank_case_insensitive() -> None:
    opt = get_option_by_priority_rank("HIGH", "1-5")
    assert opt is not None
    assert opt.value == "high_1_5"


def test_get_option_by_priority_rank_falls_back_to_no_preference_for_unknown() -> None:
    opt = get_option_by_priority_rank("unknown_priority", "unknown_band")
    assert opt is not None
    assert opt.value == "no_preference"


def test_get_option_by_priority_rank_none_rank_band_falls_back() -> None:
    # None rank_band should fall back gracefully
    opt = get_option_by_priority_rank("High", None)
    # "High" + None -> key ("high", "no_preference") -> no match -> fallback
    assert opt is not None
    assert opt.value == "no_preference"


def test_get_sort_weight_returns_correct_weights() -> None:
    assert get_sort_weight("High", "1-5") == 1
    assert get_sort_weight("Medium", "6-10") == 2
    assert get_sort_weight("Low", "11-15") == 3
    assert get_sort_weight("Low", "no_preference") == 4


def test_get_sort_weight_returns_99_for_unknown() -> None:
    assert get_sort_weight("unknown", "unknown") == 99
    assert get_sort_weight("", None) == 99
