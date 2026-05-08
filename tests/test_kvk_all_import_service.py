from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from kvk.schemas.kvk_all_schema import EXPECTED_FULL_DATA_COLUMNS, SCHEMA_VERSION
from kvk.services import kvk_all_import_service as service


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


def test_prepare_maps_full_data_columns_and_metadata() -> None:
    full_data = _full_data_df()
    full_data.loc[0, "rank"] = 7
    full_data.loc[0, "minkill_points"] = 111
    full_data.loc[0, "maxkill_points"] = 222
    full_data.loc[0, "max_contribute_min"] = 333
    full_data.loc[0, "cur_contribute_diff"] = 444

    prepared = service.prepare_kvk_all_import(_xlsx_bytes({"Full Data": full_data}), "kvk.xlsx")
    row = prepared.dataframe.iloc[0]

    assert prepared.sheet_name == "Full Data"
    assert prepared.staged_rows == 1
    assert row["rank"] == 7
    assert row["min_kill_points"] == 111
    assert row["max_kill_points"] == 222
    assert row["min_max_contribute"] == 333
    assert row["cur_contribute_diff"] == 444
    assert row["schema_version"] == SCHEMA_VERSION
    assert row["source_sheet_name"] == "Full Data"
    assert row["source_column_count"] == len(EXPECTED_FULL_DATA_COLUMNS)
    assert prepared.schema_metadata["unknown_columns"] == []


def test_read_full_data_workbook_preserves_unknown_column_reporting() -> None:
    full_data = _full_data_df()
    full_data["future_metric"] = 99

    df, sheet_name, schema = service.read_full_data_workbook(
        _xlsx_bytes({"Full Data": full_data}),
        "kvk.xlsx",
    )

    assert sheet_name == "Full Data"
    assert "future_metric" in df.columns
    assert schema["unknown_columns"] == ["future_metric"]


def test_prepare_wraps_coercion_failures_with_sheet_and_schema() -> None:
    full_data = _full_data_df()
    full_data.loc[0, "governor_id"] = None

    with pytest.raises(service.KvkAllImportPreparationError) as exc:
        service.prepare_kvk_all_import(_xlsx_bytes({"Full Data": full_data}), "kvk.xlsx")

    assert str(exc.value) == "One or more rows missing governor_id or kingdom after coercion."
    assert exc.value.sheet_name == "Full Data"
    assert exc.value.schema_metadata["schema_version"] == SCHEMA_VERSION
