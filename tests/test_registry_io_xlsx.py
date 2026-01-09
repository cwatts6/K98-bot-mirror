# tests/test_registry_io_xlsx.py
import io

import pytest

pytest.importorskip("openpyxl")  # skip these tests if openpyxl isn't installed

from openpyxl import load_workbook

import registry_io


def make_sample_registry():
    return {
        "100": {
            "discord_name": "UserOne#0001",
            "accounts": {
                "Main": {"GovernorID": "100001", "GovernorName": "Alpha"},
                "Alt 1": {"GovernorID": "100002", "GovernorName": "AlphaAlt"},
            },
        },
        "200": {
            "discord_name": "UserTwo#0002",
            "accounts": {
                "Main": {"GovernorID": "200100", "GovernorName": "Beta"},
            },
        },
    }


def test_xlsx_export_parse_roundtrip():
    registry = make_sample_registry()
    xbuf = registry_io.export_registry_to_xlsx_bytes(registry)
    assert isinstance(xbuf, io.BytesIO)
    # parse back
    rows = registry_io.parse_xlsx_bytes(xbuf.getvalue())
    # Expect 3 data rows
    assert len(rows) == 3
    # Now validate via prepare_import_plan
    changes, errors, warnings, error_rows = registry_io.prepare_import_plan(
        rows, existing_registry={}
    )
    assert not errors
    assert len(changes) == 3


def test_export_registration_audit_xlsx_contains_three_sheets():
    registry = make_sample_registry()
    # minimal members_info and sql_rows
    members_info = {
        "100": {"discord_user": "UserOne#0001", "roles": "r1;r2", "top_role": "r1"},
        "200": {"discord_user": "UserTwo#0002", "roles": "r3", "top_role": "r3"},
        "300": {"discord_user": "Someone#0300", "roles": "", "top_role": ""},
    }
    sql_rows = [
        {"GovernorID": 999999, "GovernorName": "Unreg", "Alliance": "A", "PowerRank": 1},
        {"GovernorID": 100001, "GovernorName": "Alpha", "Alliance": "B", "PowerRank": 2},
    ]
    xbuf = registry_io.export_registration_audit_xlsx_bytes(registry, members_info, sql_rows)
    wb = load_workbook(filename=io.BytesIO(xbuf.getvalue()), read_only=True)
    names = [s.title for s in wb.worksheets]
    assert "registered_accounts" in names
    assert "unregistered_current_governors" in names
    assert "members_without_registration" in names
