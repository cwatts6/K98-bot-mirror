from decimal import Decimal
import json
from types import SimpleNamespace
from uuid import uuid4

import pandas as pd
import pytest

from core.export_numeric import sql_output_frame
import gsheet_module as gm
from services.export_output_dal import read_export_frame
from services.legacy_export_snapshot_dal import LegacySnapshotDAL
from services.legacy_export_snapshot_service import (
    LegacySnapshot,
    OutputSection,
    configuration_digest,
    output_digest,
)


def scope():
    return dict(
        consumer="scan_data",
        spreadsheets={"Book": "file-a"},
        exports=[
            dict(
                query="SELECT * FROM dbo.SUMMARY_CHANGE_EXPORT",
                sheet="Book",
                tab="Summary",
                sort=0,
            )
        ],
        grid_ids={"file-a": {"Summary": 7}},
    )


class Cursor:
    def __init__(self, rows, columns):
        self.rows = rows
        self.description = [(c,) for c in columns]
        self.closed = False
        self.queries = []

    def execute(self, query):
        self.queries.append(query)
        return self

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, cursor):
        self.current = cursor
        self.closed = False

    def cursor(self):
        return self.current

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    "value", [0, -(2**63), 2**31, 2**53 - 1, 2**53, 2**53 + 1, 2**63 - 1]
)
def test_nullable_sql_int_is_exact_before_sheet_conversion(value):
    frame = sql_output_frame([(1, value), (2, None)], ["GovernorID", "Power"])
    assert int(frame["Power"].iloc[0]) == value
    sections, plan = gm.plan_legacy_outputs(scope(), frames=[frame])
    expected = str(value) if abs(value) > 2**53 else value
    assert sections[0].rows == ((1, expected), (2, ""))
    assert sections[0].columns == ("GovernorID", "Power")
    assert len(plan["outputs"][0]["format_requests"]) == 2


def test_sql_capture_and_direct_reader_preserve_values_and_close(monkeypatch, tmp_path):
    raw = [(9007199254740993, 9223372036854775807, "=literal"), (3, None, "last")]
    columns = ["GovernorID", "Power", "GovernorName"]
    config = tmp_path / "config.json"
    config.write_text(json.dumps(scope()["exports"]), encoding="utf-8")
    monkeypatch.setattr("constants.CONFIG_FILE", str(config))
    cursor = Cursor(raw, columns)
    sections, _ = LegacySnapshotDAL.capture_outputs(Connection(cursor), scope())
    assert cursor.closed
    assert sections[0].rows == (
        (3, "", "last"),
        ("9007199254740993", "9223372036854775807", "=literal"),
    )
    cursor2 = Cursor(raw, columns)
    connection = Connection(cursor2)
    frame = read_export_frame(
        SimpleNamespace(raw_connection=lambda: connection),
        scope()["exports"][0]["query"],
    )
    direct, _ = gm.plan_legacy_outputs(scope(), frames=[frame])
    assert direct == sections
    assert cursor2.closed and connection.closed


def test_decimal_blanks_boolean_and_dates_remain_explicit():
    assert (
        gm._coerce_cell_for_sheet(Decimal("12.34567890123456789"))
        == "12.34567890123456789"
    )
    assert gm._coerce_cell_for_sheet(Decimal("2.50")) == "2.50"
    assert gm._coerce_cell_for_sheet(True) is True
    assert gm._coerce_cell_for_sheet(pd.NA) == ""
    assert gm._coerce_cell_for_sheet(None) == ""
    assert gm._coerce_cell_for_sheet(3.5) == 3.5
    assert gm._coerce_cell_for_sheet(3.0) == 3
    frame = sql_output_frame([(1, Decimal("2.50")), (2, None)], ["ID", "Weight"])
    assert frame["Weight"].iloc[0] == Decimal("2.50")


def test_direct_export_uses_raw_text_and_tuple_rows(monkeypatch):
    events = []
    ws = SimpleNamespace(
        title="Summary",
        id=7,
        spreadsheet=SimpleNamespace(id="file-a", title="Book"),
        clear=lambda: events.append("clear"),
        update=lambda values, **kw: events.append((values, kw)),
    )
    monkeypatch.setattr(gm, "_retry_gspread_call", lambda action, **kw: action())
    monkeypatch.setattr(gm.time, "sleep", lambda seconds: None)
    # Numeric-only mixed columns used to make iterrows coerce the integer to float.
    frame = sql_output_frame([(9007199254740993, 1.25), (None, 2.5)], ["ID", "Ratio"])
    gm.export_dataframe_to_sheet(ws, frame)
    assert events == [
        "clear",
        (
            [["ID", "Ratio"], ["9007199254740993", 1.25], ["", 2.5]],
            {"value_input_option": "RAW"},
        ),
    ]


def test_unsafe_approximate_value_stops_before_direct_clear(monkeypatch):
    ws = SimpleNamespace(
        clear=lambda: pytest.fail("Invalid numeric input cleared provider output")
    )
    with pytest.raises(ValueError, match="approximate"):
        gm.export_dataframe_to_sheet(ws, sql_output_frame([(float(2**54),)], ["Power"]))


def test_old_and_new_immutable_payloads_round_trip_without_regeneration():
    for cells in [((1.0, 123.0),), ((1, "9223372036854775807"),)]:
        sections = (OutputSection("file-a:Summary", ("GovernorID", "Power"), cells),)
        config = dict(outputs=[], destinations=["file-a"])
        original = LegacySnapshot.capture(
            consumer="scan_data",
            preparation_id=str(uuid4()),
            generation=dict(
                completion="committed",
                commit_identity="retained",
                output_sha256=output_digest(sections),
                config_sha256=configuration_digest(config),
            ),
            config=config,
            provenance={},
            sections=sections,
        )
        loaded = LegacySnapshot.load(original.payload)
        assert loaded.payload == original.payload


def test_empty_output_preserves_headers_and_decimal_sort_is_numeric():
    sections, _ = gm.plan_legacy_outputs(
        scope(), frames=[sql_output_frame([], ["GovernorID", "Power"])]
    )
    assert sections[0].rows == () and sections[0].columns == ("GovernorID", "Power")
    frame = sql_output_frame([(Decimal("10.5"),), (Decimal("2.5"),)], ["Weight"])
    sections, _ = gm.plan_legacy_outputs(scope(), frames=[frame])
    assert sections[0].rows == (("2.5",), ("10.5",))


def test_direct_reader_failure_closes_both_handles():
    cursor = Cursor([], [])
    cursor.fetchall = lambda: (_ for _ in ()).throw(ValueError("read failed"))
    connection = Connection(cursor)
    with pytest.raises(ValueError, match="read failed"):
        read_export_frame(
            SimpleNamespace(raw_connection=lambda: connection), "reviewed"
        )
    assert cursor.closed and connection.closed


def test_direct_reader_preserves_read_error_when_cleanup_also_fails():
    cursor = Cursor([], [])
    cursor.fetchall = lambda: (_ for _ in ()).throw(ValueError("first read failure"))
    cursor.close = lambda: (_ for _ in ()).throw(RuntimeError("later close failure"))
    connection = Connection(cursor)
    with pytest.raises(ValueError, match="first read failure"):
        read_export_frame(
            SimpleNamespace(raw_connection=lambda: connection), "reviewed"
        )
    assert connection.closed
