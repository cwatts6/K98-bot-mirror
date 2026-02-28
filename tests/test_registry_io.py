# tests/test_registry_io.py
import io

import registry_io


def make_sample_registry():
    # Two users with numeric GovernorIDs
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


def test_export_parse_roundtrip_and_prepare_plan():
    registry = make_sample_registry()
    buf = registry_io.export_registry_to_csv_bytes(registry)
    assert isinstance(buf, io.BytesIO)
    content = buf.getvalue()
    rows = registry_io.parse_csv_bytes(content)
    assert len(rows) == 3  # 3 account rows exported

    changes, errors, warnings, error_rows = registry_io.prepare_import_plan(
        rows, existing_registry={}
    )
    assert not errors
    assert len(changes) == 3


def test_strip_excel_formula_warning():
    text = "DiscordUserID,AccountType,GovernorID,GovernorName\n123,Main,=123456,ExcelGuy\n"
    content = text.encode("utf-8")
    rows = registry_io.parse_csv_bytes(content)
    changes, errors, warnings, error_rows = registry_io.prepare_import_plan(
        rows, existing_registry={}
    )
    assert not errors
    assert any("formula" in w.lower() for w in warnings)


def test_duplicate_gid_in_import_causes_error():
    text = (
        "DiscordUserID,AccountType,GovernorID,GovernorName\n"
        "111,Main,999999,One\n"
        "222,Main,999999,Two\n"
    )
    rows = registry_io.parse_csv_bytes(text.encode("utf-8"))
    changes, errors, warnings, error_rows = registry_io.prepare_import_plan(
        rows, existing_registry={}
    )
    assert errors
    assert any(
        "assigned to multiple" in e.lower() or "multiple discord" in e.lower() for e in errors
    )


def test_collision_with_existing_registry_blocks_import():
    existing = {
        "500": {
            "discord_name": "Existing#0500",
            "accounts": {"Main": {"GovernorID": "777777", "GovernorName": "Existing"}},
        }
    }
    text = "DiscordUserID,AccountType,GovernorID,GovernorName\n777,Main,777777,NewGuy\n"
    rows = registry_io.parse_csv_bytes(text.encode("utf-8"))
    changes, errors, warnings, error_rows = registry_io.prepare_import_plan(
        rows, existing_registry=existing
    )
    assert errors
    assert any("already registered" in e.lower() for e in errors)


def test_prepare_import_plan_with_valid_ids_blocks_missing_source():
    # If valid_ids provided, missing source-of-truth should cause error
    registry = {}
    text = "DiscordUserID,AccountType,GovernorID,GovernorName\n111,Main,123456,Name\n"
    rows = registry_io.parse_csv_bytes(text.encode("utf-8"))
    valid_ids = {"999999": {"GovernorID": "999999"}}
    changes, errors, warnings, error_rows = registry_io.prepare_import_plan(
        rows, existing_registry=registry, valid_ids=valid_ids
    )
    assert errors
    assert any("not found in source" in e.lower() for e in errors)
