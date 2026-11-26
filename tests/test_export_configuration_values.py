"""Configuration checks agree with SQL bounds and the existing import coercions."""

from decimal import Decimal

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_configuration_values import (
    numeric_value,
    sql_text,
    verify_import_values,
)


@pytest.mark.parametrize(
    "table,column,value",
    [
        ("ProcConfig", "KVK_NO", "1e999999999"),
        ("ProcConfig", "KVK_NO", "1e-999999999"),
        ("ProcConfig", "KVK_NO", "NaN"),
        ("ProcConfig", "KVK_NO", True),
        ("ProcConfig", "MATCHMAKING_SCAN", 0),
        ("ProcConfig", "DRAFTSCAN", 0),
        ("ProcConfig", "DRAFTSCAN", "1e3"),
        ("ProcConfig", "KVK_NO", "42.0"),
        ("ProcConfig", "KVK_NO", "4_2"),
        ("ProcConfig", "KVK_NO", "\u0664\u0662"),
        ("EXEMPT", "KVK_NO", "42.5"),
        ("KVK_CampMap", "CampID", 0),
        ("KVK_CampMap", "CampID", 9),
        ("KVK_Windows", "StartScanID", 0),
        ("KVK_DKPWeights", "WeightT4X", "1e1000"),
        ("KVK_DKPWeights", "WeightT4X", "0.1234567890123"),
        ("KVK_DKPWeights", "KVK_NO", "42.0"),
    ],
)
def test_invalid_values_are_rejected_before_import(table, column, value):
    with pytest.raises(SourceConflict):
        numeric_value(table, column, value)


def test_sql_text_counts_supplementary_characters_as_two_units():
    assert sql_text("\U0001f600" * 20, 40)
    assert not sql_text("\U0001f600" * 21, 40)
    assert not sql_text("\ud800", 40)


@pytest.mark.parametrize("token", ["1,000", "12.5%", "$100", "42.5"])
def test_actual_formatted_integer_tokens_cannot_silently_change(token):
    with pytest.raises(SourceConflict):
        verify_import_values("EXEMPT", [{"GovernorID": token}], {}, {})


def test_mixed_blank_column_cannot_round_a_large_integer():
    with pytest.raises(SourceConflict, match="during import"):
        verify_import_values(
            "EXEMPT", [{"GovernorID": "9007199254740993"}, {"GovernorID": None}], {}, {}
        )


def test_valid_integer_float_and_dates_match_importer():
    verify_import_values("ProcConfig", [{"KVK_NO": "42"}], {}, {})
    verify_import_values("KVK_DKPWeights", [{"WeightT4X": "0.123456789012"}], {}, {})
    verify_import_values("KVK_Details", [{"KVK_START_DATE": "15/10/26"}], {}, {"KVK_START_DATE"})
    assert numeric_value("KVK_CampMap", "CampID", 8) == Decimal(8)
    assert numeric_value("EXEMPT", "KVK_NO", "0") == Decimal(0)
    assert numeric_value("ProcConfig", "MATCHMAKING_SCAN", 101.0) == Decimal(101)


def test_invalid_calendar_date_is_rejected_by_the_import_parser():
    with pytest.raises(SourceConflict, match="during import"):
        verify_import_values(
            "KVK_Details", [{"KVK_START_DATE": "31/02/2026"}], {}, {"KVK_START_DATE"}
        )
