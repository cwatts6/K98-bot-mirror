from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from kvk.schemas.kvk_all_schema import (
    EXPECTED_FULL_DATA_COLUMNS,
    FULL_DATA_SHEET_NAME,
    SCHEMA_VERSION,
    KvkAllSchemaValidationError,
    validate_full_data_columns,
)
import kvk_all_importer as importer


def _xlsx_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return bio.getvalue()


def _full_data_df() -> pd.DataFrame:
    row = {column: 1 for column in EXPECTED_FULL_DATA_COLUMNS}
    row.update(
        {
            "name": "Test Governor",
            "first_updateUTC": "2026-05-08 01:00:00",
            "last_updateUTC": "2026-05-08 02:00:00",
        }
    )
    return pd.DataFrame([row], columns=list(EXPECTED_FULL_DATA_COLUMNS))


def _basic_data_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rank": 1,
                "governor_id": 123,
                "name": "Basic Governor",
                "kingdom": 98,
                "campid": 4,
                "min_points": 10,
                "max_points": 20,
                "points_difference": 10,
                "min_power": 100,
                "max_power": 200,
                "power_difference": 100,
                "first_update": "2026-05-08 01:00:00",
                "last_update": "2026-05-08 02:00:00",
                "latest_power": 200,
            }
        ]
    )


def test_validate_full_data_columns_accepts_expected_schema() -> None:
    """Passing all EXPECTED_FULL_DATA_COLUMNS directly returns a successful result."""
    result = validate_full_data_columns(EXPECTED_FULL_DATA_COLUMNS, sheet_name=FULL_DATA_SHEET_NAME)

    assert result.schema_version == SCHEMA_VERSION
    assert result.actual_columns == EXPECTED_FULL_DATA_COLUMNS
    assert result.unknown_columns == ()


def test_read_excel_uses_full_data_and_ignores_basic_data() -> None:
    content = _xlsx_bytes(
        {
            "Basic Data": _basic_data_df(),
            "Full Data": _full_data_df(),
        }
    )

    df, sheet_name, schema = importer._read_excel(content, "kvk.xlsx")

    assert sheet_name == "Full Data"
    assert schema["schema_version"] == SCHEMA_VERSION
    assert schema["column_count"] == len(EXPECTED_FULL_DATA_COLUMNS)
    assert df.loc[0, "name"] == "Test Governor"
    assert "first_updateUTC" in df.columns


def test_read_excel_rejects_missing_full_data_without_sheet_fallback() -> None:
    content = _xlsx_bytes(
        {
            "Basic Data": _basic_data_df(),
            "Summary": pd.DataFrame([{"kingdom": 98}]),
        }
    )

    with pytest.raises(KvkAllSchemaValidationError) as exc:
        importer._read_excel(content, "kvk.xlsx")

    error = exc.value.to_dict()
    assert error["code"] == "missing_full_data_sheet"
    assert error["available_sheets"] == ["Basic Data", "Summary"]


def test_read_excel_rejects_missing_required_full_data_columns() -> None:
    full_data = _full_data_df().drop(columns=["cur_contribute_diff", "healed_troops"])
    content = _xlsx_bytes({"Full Data": full_data})

    with pytest.raises(KvkAllSchemaValidationError) as exc:
        importer._read_excel(content, "kvk.xlsx")

    error = exc.value.to_dict()
    assert error["code"] == "missing_required_full_data_columns"
    assert error["sheet_name"] == "Full Data"
    assert error["missing_columns"] == ["cur_contribute_diff", "healed_troops"]


def test_read_excel_rejects_csv_source_filename() -> None:
    with pytest.raises(KvkAllSchemaValidationError) as exc:
        importer._read_excel(b"rank,governor_id\n1,2\n", "kvk.csv")

    error = exc.value.to_dict()
    assert error["code"] == "unsupported_kvk_all_file_type"


def test_read_excel_missing_columns_reports_actual_sheet_name() -> None:
    full_data = _full_data_df().drop(columns=["cur_contribute_diff"])
    content = _xlsx_bytes({" full_data ": full_data})

    with pytest.raises(KvkAllSchemaValidationError) as exc:
        importer._read_excel(content, "kvk.xlsx")

    error = exc.value.to_dict()
    assert error["code"] == "missing_required_full_data_columns"
    assert error["sheet_name"] == " full_data "


def test_ingest_returns_structured_schema_error_for_missing_full_data() -> None:
    content = _xlsx_bytes({"Basic Data": _basic_data_df()})

    result = importer.ingest_kvk_all_excel(
        content=content,
        source_filename="kvk.xlsx",
        uploader_id=123,
        scan_ts_utc=pd.Timestamp("2026-05-08T01:00:00Z").to_pydatetime(),
        server="unused",
        database="unused",
        username="unused",
        password="unused",
    )

    assert result["success"] is False
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["validation_error"]["code"] == "missing_full_data_sheet"
