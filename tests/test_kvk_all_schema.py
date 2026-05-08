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
    row: dict[str, object] = {column: 1 for column in EXPECTED_FULL_DATA_COLUMNS}
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


def test_coerce_maps_full_data_v2_columns_to_additive_stage_columns() -> None:
    full_data = _full_data_df()
    full_data.loc[0, "rank"] = 7
    full_data.loc[0, "minkill_points"] = 111
    full_data.loc[0, "maxkill_points"] = 222
    full_data.loc[0, "minpower"] = 333
    full_data.loc[0, "maxpower"] = 444
    full_data.loc[0, "max_contribute_min"] = 555
    full_data.loc[0, "max_contribute_max"] = 666
    full_data.loc[0, "cur_contribute_min"] = 777
    full_data.loc[0, "cur_contribute_max"] = 888
    full_data.loc[0, "max_contribute_diff"] = 999
    full_data.loc[0, "cur_contribute_diff"] = 1000

    coerced = importer._coerce(full_data)

    assert coerced.loc[0, "rank"] == 7
    assert coerced.loc[0, "min_kill_points"] == 111
    assert coerced.loc[0, "max_kill_points"] == 222
    assert coerced.loc[0, "min_power_raw"] == 333
    assert coerced.loc[0, "max_power_raw"] == 444
    assert coerced.loc[0, "min_max_contribute"] == 555
    assert coerced.loc[0, "max_max_contribute"] == 666
    assert coerced.loc[0, "min_cur_contribute"] == 777
    assert coerced.loc[0, "max_cur_contribute"] == 888
    assert coerced.loc[0, "max_contribute_diff"] == 999
    assert coerced.loc[0, "cur_contribute_diff"] == 1000


def test_stage_insert_contract_includes_phase2_columns_and_metadata() -> None:
    required = {
        "rank",
        "min_kill_points",
        "max_kill_points",
        "min_power_raw",
        "max_power_raw",
        "min_dead",
        "max_dead",
        "min_troop_power",
        "max_troop_power",
        "min_units_healed",
        "max_units_healed",
        "min_kills_iv",
        "max_kills_iv",
        "min_kills_v",
        "max_kills_v",
        "min_max_contribute",
        "max_max_contribute",
        "min_cur_contribute",
        "max_cur_contribute",
        "max_contribute_diff",
        "cur_contribute_diff",
        "schema_version",
        "source_sheet_name",
        "source_column_hash",
        "source_column_count",
        "source_row_count",
    }

    assert required.issubset(set(importer.STAGE_COL_ORDER))
    assert importer.STAGE_INSERT_SQL.count("?") == len(importer.STAGE_INSERT_COLUMNS)


def test_rows_for_stage_include_source_metadata_values() -> None:
    schema = validate_full_data_columns(EXPECTED_FULL_DATA_COLUMNS, sheet_name=FULL_DATA_SHEET_NAME)
    coerced = importer._coerce(_full_data_df())
    enriched = importer._with_source_metadata(
        coerced,
        sheet_name=FULL_DATA_SHEET_NAME,
        schema_metadata=schema.to_dict(),
    )

    row = importer._rows_for_stage("token-1", enriched)[0]
    values = dict(zip(["IngestToken", *importer.STAGE_COL_ORDER], row, strict=True))

    assert values["IngestToken"] == "token-1"
    assert values["schema_version"] == SCHEMA_VERSION
    assert values["source_sheet_name"] == FULL_DATA_SHEET_NAME
    assert values["source_column_hash"] == schema.column_hash
    assert values["source_column_count"] == len(EXPECTED_FULL_DATA_COLUMNS)
    assert values["source_row_count"] == 1


def test_ingest_call_contract_passes_phase2_metadata_parameters() -> None:
    for parameter_name in [
        "@SchemaVersion=?",
        "@SourceSheetName=?",
        "@SourceColumnHash=?",
        "@SourceColumnCount=?",
        "@SourceRowCount=?",
    ]:
        assert parameter_name in importer.CALL_INGEST_SQL


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
