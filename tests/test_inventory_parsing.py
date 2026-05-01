import pytest

from inventory.models import InventoryImportType
from inventory.parsing import (
    apply_resource_total_corrections,
    apply_speedup_duration_corrections,
    format_resource_value,
    format_speedup_duration,
    normalize_final_values,
    parse_resource_value,
    parse_speedup_days,
    parse_speedup_minutes,
    speedup_row_from_days,
)


def test_parse_resource_value_expands_suffixes():
    assert parse_resource_value("7.0B") == 7_000_000_000
    assert parse_resource_value("122.2M") == 122_200_000
    assert parse_resource_value("30K") == 30_000
    assert parse_resource_value("30000") == 30_000
    assert parse_resource_value(0) == 0


def test_parse_resource_value_rejects_negative_values():
    with pytest.raises(ValueError, match=r"Invalid resource value|Negative"):
        parse_resource_value("-1")


def test_parse_speedup_minutes_supports_day_hour_minute_tokens():
    assert parse_speedup_minutes("122d 2h 42m") == (122 * 1440) + 120 + 42
    assert parse_speedup_minutes("239d") == 239 * 1440
    assert parse_speedup_minutes("2h 42m") == 162
    assert parse_speedup_minutes("0") == 0


def test_parse_speedup_days_uses_only_day_component():
    assert parse_speedup_days("505d 3h 37m") == 505
    assert parse_speedup_days("505") == 505
    assert parse_speedup_days(505.9) == 505


def test_normalize_final_values_for_speedups_calculates_derived_fields():
    normalized = normalize_final_values(
        InventoryImportType.SPEEDUPS,
        {
            "speedups": {
                "building": {"total_days_decimal": 0},
                "research": {"total_days_decimal": 0},
                "training": {"total_days_decimal": 1},
                "healing": {"total_days_decimal": 0},
                "universal": {"total_days_decimal": 2},
            }
        },
    )

    assert normalized["speedups"]["building"] == speedup_row_from_days(0)
    assert normalized["speedups"]["universal"]["total_days_decimal"] == 2.0


def test_resource_total_corrections_only_change_total_resources():
    values = {
        "resources": {
            "food": {"from_items_value": 10, "total_resources_value": 20},
            "wood": {"from_items_value": 30, "total_resources_value": 40},
            "stone": {"from_items_value": 50, "total_resources_value": 60},
            "gold": {"from_items_value": 70, "total_resources_value": 80},
        }
    }

    corrected = apply_resource_total_corrections(values, {"food": "1.2M", "gold": "90"})

    assert corrected["resources"]["food"]["from_items_value"] == 10
    assert corrected["resources"]["food"]["total_resources_value"] == 1_200_000
    assert corrected["resources"]["gold"]["from_items_value"] == 70
    assert corrected["resources"]["gold"]["total_resources_value"] == 90


def test_speedup_duration_corrections_accept_friendly_text():
    values = {
        "speedups": {
            "building": {"total_minutes": 1},
            "research": {"total_minutes": 2},
            "training": {"total_minutes": 3},
            "healing": {"total_minutes": 4},
            "universal": {"total_minutes": 5},
        }
    }

    corrected = apply_speedup_duration_corrections(values, {"healing": "505d 3h 37m"})

    assert corrected["speedups"]["healing"]["total_minutes"] == 505 * 1440


def test_inventory_display_formatters_are_user_friendly():
    assert format_resource_value(1_200_000) == "1.2M"
    assert format_speedup_duration((505 * 1440) + 180 + 37) == "505d"


def test_format_resource_value_returns_unreadable_on_invalid_input():
    assert format_resource_value(None) == "unreadable"
    assert format_resource_value(-1) == "unreadable"
    assert format_resource_value("not_a_number") == "unreadable"
    assert format_resource_value(1.5) == "unreadable"


def test_format_speedup_duration_returns_unreadable_on_invalid_input():
    assert format_speedup_duration(None) == "unreadable"
    assert format_speedup_duration(-1) == "unreadable"
    assert format_speedup_duration("bad input") == "unreadable"
