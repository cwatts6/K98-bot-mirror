import pandas as pd
import pytest

from gsheet_module import _coerce_date_uk, _coerce_float, _coerce_int, _normalize_headers


def test_normalize_headers_basic():
    df = pd.DataFrame(columns=[" KV K_No ", "Name", "Other"])
    rename_map = {"KVK_NO": ["KVK_NO", "KV K_No", "kvk_no"], "KVK_NAME": ["Name", "KVK_Name"]}
    df2 = _normalize_headers(df.copy(), rename_map)
    assert "KVK_NO" in df2.columns
    assert "KVK_NAME" in df2.columns


def test_coerce_int_and_float_and_date():
    data = {
        "KVK_NO": ["1", "2", None, "x"],
        "ValFloat": ["1.5", "2.25", "not_a_number", ""],
        "DateUK": ["01/12/2024", "31/01/23", "", None],
    }
    df = pd.DataFrame(data)
    _coerce_int(df, ["KVK_NO"])
    _coerce_float(df, ["ValFloat"])
    _coerce_date_uk(df, ["DateUK"])
    assert df["KVK_NO"].dtype == "Int64"
    assert pytest.approx(float(df["ValFloat"].iloc[0]), 0.001) == 1.5
    # Date columns should be Python date objects for parsed rows
    assert df["DateUK"].iloc[0].day == 1
    assert df["DateUK"].iloc[1].year in (2023, 2023)  # parsed 2-digit year -> 2023
