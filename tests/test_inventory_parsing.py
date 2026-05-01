import pytest

from inventory.models import InventoryImportType
from inventory.parsing import (
    normalize_final_values,
    parse_resource_value,
    parse_speedup_minutes,
    speedup_row_from_minutes,
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


def test_normalize_final_values_for_speedups_calculates_derived_fields():
    normalized = normalize_final_values(
        InventoryImportType.SPEEDUPS,
        {
            "speedups": {
                "building": {"total_minutes": 60},
                "research": {"total_minutes": 120},
                "training": {"total_minutes": 1440},
                "healing": {"total_minutes": 0},
                "universal": {"total_minutes": 2880},
            }
        },
    )

    assert normalized["speedups"]["building"] == speedup_row_from_minutes(60)
    assert normalized["speedups"]["universal"]["total_days_decimal"] == 2.0
