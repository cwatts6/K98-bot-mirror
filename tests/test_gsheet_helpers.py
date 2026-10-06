import pandas as pd
import pytest

from gsheet_module import _coerce_date_uk, _coerce_float, _coerce_int, _normalize_headers


def test_direct_table_reader_cannot_bypass_coordinated_capture(monkeypatch):
    import gsheet_module as gm
    from services.legacy_export_snapshot_service import SnapshotUnavailable, use_runtime

    with use_runtime(object()), pytest.raises(SnapshotUnavailable, match="immutable"):
        gm.transfer_and_sort(None, None, None, "SELECT unsafe", "title", "tab")


@pytest.mark.parametrize("consumer", ["scan_data", "all_kvk"])
def test_planner_rejects_logical_destination_aliases_before_reading_frames(consumer):
    from gsheet_module import plan_legacy_outputs
    from services.legacy_export_snapshot_service import SnapshotUnavailable

    class UnreadableFrames:
        def __iter__(self):
            raise AssertionError("Aliased registration reached output planning")

    scope = dict(
        consumer=consumer,
        spreadsheets={"First": "file-a", "Second": "file-a"},
        exports=[dict(sheet="First", tab="One"), dict(sheet="Second", tab="Two")],
    )
    with pytest.raises(SnapshotUnavailable, match="alias"):
        plan_legacy_outputs(scope, frames=UnreadableFrames())


def test_planner_preserves_distinct_registered_destinations():
    from gsheet_module import plan_legacy_outputs

    scope = dict(
        consumer="scan_data",
        spreadsheets={"First": "file-a", "Second": "file-b"},
        exports=[dict(sheet="First", tab="One"), dict(sheet="Second", tab="Two")],
    )
    sections, planned = plan_legacy_outputs(
        scope, frames=[pd.DataFrame({"id": [1]}), pd.DataFrame({"id": [2]})]
    )
    assert planned["destinations"] == ["file-a", "file-b"]
    assert {s.name for s in sections} == {"file-a:One", "file-b:Two"}


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
