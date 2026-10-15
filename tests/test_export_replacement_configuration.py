"""Shared configuration replacement: bounded evidence, routing and protected tabs."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_execution_protocol import ProviderRequest
from services.export_replacement_configuration import CONFIGURATION_COLUMNS, CONFIGURATION_TABS
from services.export_replacement_plan import replacement_registration, verified_registration
from services.export_replacement_verification import (
    METADATA,
    ReplacementVerificationPlan,
    discover_replacement,
    replacement_readback,
    verification_plan,
    verification_requests,
)
from services.export_runtime_composition import RuntimeRegistration
from services.legacy_export_snapshot_service import LegacyExportRuntime
from tests.test_export_manual_enrollment import responses
from tests.test_export_replacement_plan import legacy_fixture
from tests.test_export_replacement_verification import value


def configuration_registration():
    v = legacy_fixture()
    v["legacy_configuration"]["config"]["destinations"] = ["legacy-scan_data"]
    return RuntimeRegistration(v)


def configuration_fixture():
    v = value()
    v["version"] = 5
    v["files"][0]["kind"] = "configuration_output"
    plan = ReplacementVerificationPlan(v)
    return plan, configuration_responses(plan, "replacement-file")


def configuration_responses(plan, file_id, *, rows_by_tab=None):
    """Realistic Sheets metadata, cell and FORMULA responses; no provider calls."""
    grids, sheets, replies = [], [], []
    for number, title in enumerate((*CONFIGURATION_TABS, "Sheet1")):
        grid = dict(file_id=file_id, sheet_id=number, title=title, rows=100, columns=26)
        reply = responses(plan, grid)
        reply[2]["sheets"][0]["properties"].update(
            title=title, gridProperties=dict(rowCount=100, columnCount=26)
        )
        reply[3]["valueRanges"][0]["range"] = title + "!A1:Z100"
        sheets.append(deepcopy(reply[2]["sheets"][0]))
        grids.append(grid)
        if title != "Sheet1":
            rows = [list(CONFIGURATION_COLUMNS[title])]
            if title == "ProcConfig":
                rows.append([42, 100, 101, 102, 103, 104, 105, 106, 3, 107])
            if rows_by_tab and title in rows_by_tab:
                rows = [list(CONFIGURATION_COLUMNS[title]), *rows_by_tab[title]]
            reply[3]["valueRanges"][0]["values"] = rows
            reply[2]["sheets"][0]["data"] = [
                dict(
                    rowData=[
                        dict(
                            values=[
                                dict(
                                    userEnteredValue={
                                        "stringValue" if isinstance(v, str) else "numberValue": v
                                    }
                                )
                                for v in row
                            ]
                        )
                        for row in rows
                    ]
                )
            ]
        replies.extend(reply[2:])
    metadata = dict(spreadsheetId=file_id, sheets=sheets)
    return metadata, [*responses(plan, grids[-1])[:2], *replies]


COMPLETE_CONFIGURATION = {
    "ProcConfig": [[42, 100, 101, 102, 103, 104, 105, 106, 3, 107]],
    "KVKTargetBands": [[42, 100000000, 20000000, 10000000, 1000000]],
    "EXEMPT": [[12345, "Example governor", 1, 42]],
    "KVK_Details": [
        [
            42,
            "Season",
            "01/10/2026",
            "15/10/2026",
            "15/12/2026",
            101,
            106,
            43,
            "01/10/2026",
            "15/10/2026",
            102,
        ]
    ],
    "KVK_DKPWeights": [[42, "0.125", "2", "3"]],
    "KVK_Windows": [[42, "Pass 4", 1, 102, 103, "First fight"]],
    "KVK_CampMap": [[42, 1098, 1, "Water"]],
}


def test_complete_populated_configuration_matches_all_import_contracts():
    plan, _ = configuration_fixture()
    metadata, replies = configuration_responses(
        plan, "replacement-file", rows_by_tab=COMPLETE_CONFIGURATION
    )
    policy = plan.value()["files"][0]
    summary = replacement_readback(plan, policy, discover_replacement(policy, metadata), replies)
    assert len(summary) == 7 and all(item["rows"] == 1 for item in summary)


@pytest.mark.parametrize(
    "tab,column,bad",
    [
        ("ProcConfig", "KVK_NO", "1e999999999"),
        ("KVK_CampMap", "CampID", 9),
        ("KVK_CampMap", "CampName", "\U0001f600" * 21),
        ("KVK_Windows", "StartScanID", 0),
        ("KVK_Windows", "EndScanID", 101),
        ("EXEMPT", "KVK_NO", "42.5"),
        ("KVK_DKPWeights", "WeightT4X", "0.1234567890123"),
    ],
)
def test_complete_copy_rejects_values_that_would_fail_after_activation(tab, column, bad):
    data = deepcopy(COMPLETE_CONFIGURATION)
    data[tab][0][CONFIGURATION_COLUMNS[tab].index(column)] = bad
    plan, _ = configuration_fixture()
    metadata, replies = configuration_responses(plan, "replacement-file", rows_by_tab=data)
    policy = plan.value()["files"][0]
    with pytest.raises(SourceConflict):
        replacement_readback(plan, policy, discover_replacement(policy, metadata), replies)


@pytest.mark.parametrize("displayed", ["1,000", "12.5%", "999"])
def test_readback_checks_displayed_numeric_meaning(displayed):
    plan, (metadata, replies) = configuration_fixture()
    offset = 2 + 2 * CONFIGURATION_TABS.index("ProcConfig")
    replies[offset]["sheets"][0]["data"][0]["rowData"][1]["values"][1]["formattedValue"] = displayed
    policy = plan.value()["files"][0]
    with pytest.raises(SourceConflict, match="formatting"):
        replacement_readback(plan, policy, discover_replacement(policy, metadata), replies)


def test_complete_configuration_observation_and_exact_bounded_read_plan():
    plan, (metadata, replies) = configuration_fixture()
    policy = plan.value()["files"][0]
    grid = discover_replacement(policy, metadata)
    summary = replacement_readback(plan, policy, grid, replies)
    assert [s["tab"] for s in summary] == list(CONFIGURATION_TABS)
    assert next(s["rows"] for s in summary if s["tab"] == "ProcConfig") == 1
    requests = [METADATA, *verification_requests(grid)]
    assert len(requests) == plan.verification_request_count == 19
    for operation, arguments in requests:
        request = ProviderRequest.parse(
            dict(
                version=1,
                request_id=str(uuid4()),
                stream_id=str(uuid4()),
                operation=operation,
                target=policy["file_id"],
                arguments=arguments,
            ),
            enrollment=True,
        )
        plan.authorize_request(request, phase="verify", ordinal=1)


@pytest.mark.parametrize(
    "damage",
    [
        "missing_tab",
        "extra_tab",
        "large",
        "formula",
        "mismatch",
        "headers",
        "empty_config",
        "overlap",
        "owner",
        "output_data",
        "wrong_range",
        "duplicate_key",
    ],
)
def test_incomplete_or_unsafe_configuration_copy_is_rejected(damage):
    plan, (metadata, replies) = configuration_fixture()
    offset = 2 + 2 * CONFIGURATION_TABS.index("ProcConfig")
    sheet, cells = replies[offset : offset + 2]
    if damage == "missing_tab":
        metadata["sheets"].pop()
    elif damage == "extra_tab":
        metadata["sheets"].append(deepcopy(metadata["sheets"][0]))
    elif damage == "large":
        metadata["sheets"][0]["properties"]["gridProperties"]["rowCount"] = 100000
    elif damage == "formula":
        sheet["sheets"][0]["data"][0]["rowData"][1]["values"][0]["userEnteredValue"] = dict(
            formulaValue="=42"
        )
    elif damage == "mismatch":
        cells["valueRanges"][0]["values"][1][0] = 99
    elif damage in {"headers", "empty_config", "duplicate_key"}:
        rows = cells["valueRanges"][0]["values"]
        if damage == "headers":
            rows[0][0] = "Wrong"
        elif damage == "empty_config":
            rows.pop()
        else:
            rows.append(deepcopy(rows[1]))
        sheet["sheets"][0]["data"] = [
            dict(
                rowData=[
                    dict(
                        values=[
                            dict(
                                userEnteredValue={
                                    "stringValue" if isinstance(v, str) else "numberValue": v
                                }
                            )
                            for v in row
                        ]
                    )
                    for row in rows
                ]
            )
        ]
    elif damage == "overlap":
        sheet["sheets"][0]["data"].append({})
    elif damage == "owner":
        replies[0]["owners"] = [dict(emailAddress="wrong@example.com")]
    elif damage == "output_data":
        replies[-1]["valueRanges"][0]["values"] = [["old report"]]
    elif damage == "wrong_range":
        cells["valueRanges"][0]["range"] = "ProcConfig!A1:A1"
    with pytest.raises(SourceConflict):
        grid = discover_replacement(plan.value()["files"][0], metadata)
        replacement_readback(plan, plan.value()["files"][0], grid, replies)


@pytest.mark.parametrize(
    "formatted, accepted",
    [("15/10/2026", True), ("15/10/26", True), ("10/15/2026", False), (46310, False)],
)
def test_copied_date_serial_keeps_the_importers_uk_formatted_value(formatted, accepted):
    plan, (metadata, replies) = configuration_fixture()
    offset = 2 + 2 * CONFIGURATION_TABS.index("KVK_Details")
    sheet, cells = replies[offset : offset + 2]
    data = [42, "Season", 46310]
    cells["valueRanges"][0]["values"].append(data)
    entries = [
        dict(userEnteredValue={"stringValue" if isinstance(v, str) else "numberValue": v})
        for v in data
    ]
    entries[2]["formattedValue"] = formatted
    sheet["sheets"][0]["data"][0]["rowData"].append(dict(values=entries))
    policy = plan.value()["files"][0]
    grid = discover_replacement(policy, metadata)
    if accepted:
        assert replacement_readback(plan, policy, grid, replies)
    else:
        with pytest.raises(SourceConflict, match="formatting"):
            replacement_readback(plan, policy, grid, replies)


def test_alias_chain_preserves_inputs_and_reserved_configuration_grid_ids():
    original = configuration_registration()
    first = replacement_registration(
        original,
        targets=["legacy-scan_data"],
        replacements={"legacy-scan_data": "replacement-file"},
        replacement_id=str(uuid4()),
    )
    plan, (metadata, replies) = configuration_fixture()
    grid = discover_replacement(plan.value()["files"][0], metadata)
    first = verified_registration(first, [grid])
    current = RuntimeRegistration(first["registration"])
    scope = current.value()["legacy_configuration"]
    assert scope["config"]["input_aliases"] == {"legacy-scan_data": "replacement-file"}
    assert scope["scan_data"]["preserved_tabs"] == {"replacement-file": list(CONFIGURATION_TABS)}
    assert all(
        scope["scan_data"]["grid_ids"]["replacement-file"][g["title"]] == g["sheet_id"]
        for g in grid["configuration_grids"]
    )
    second = replacement_registration(
        current,
        targets=["replacement-file"],
        replacements={"replacement-file": "second-config-file"},
        replacement_id=str(uuid4()),
    )
    second_metadata = deepcopy(metadata)
    second_metadata["spreadsheetId"] = "second-config-file"
    second_grid = discover_replacement(
        dict(file_id="second-config-file", kind="configuration_output"), second_metadata
    )
    second = verified_registration(second, [second_grid])
    runtime = LegacyExportRuntime.__new__(LegacyExportRuntime)
    runtime.configuration = json.dumps(second["registration"]["legacy_configuration"])
    assert runtime.configuration_destination("legacy-scan_data") == "second-config-file"
    assert runtime.configuration_destination("replacement-file") == "second-config-file"
    assert runtime.configuration_health_destination("legacy-scan_data") == "second-config-file"
    assert original.value()["legacy_configuration"]["config"]["destinations"] == [
        "legacy-scan_data"
    ]


def test_plan_role_comes_from_registration_and_future_import_uses_active_file(monkeypatch):
    registration = configuration_registration()
    proposal = replacement_registration(
        registration,
        targets=["legacy-scan_data"],
        replacements={"legacy-scan_data": "replacement-file"},
        replacement_id=str(uuid4()),
    )
    proposal["owner_email"] = "owner@example.com"
    plan = verification_plan(
        registration,
        proposal,
        verification_id=str(uuid4()),
        manifest_hash="a" * 64,
        profile_hash="b" * 64,
        project_id="example",
    )
    assert plan.value()["version"] == 5
    assert plan.value()["files"][0]["kind"] == "configuration_output"
    import gsheet_module as gm
    import proc_config_import as importer
    from services import (
        export_provider_adapter as provider,
        legacy_export_snapshot_service as legacy,
    )

    runtime = LegacyExportRuntime.__new__(LegacyExportRuntime)
    runtime.configuration = json.dumps(proposal["registration"]["legacy_configuration"])
    monkeypatch.setattr(legacy, "_writer_runtime", lambda: runtime)
    monkeypatch.setattr(provider, "current_provider", lambda: SimpleNamespace(execution=object()))
    read = Mock(return_value=[["KVK_NO"], [42]])
    monkeypatch.setattr(gm, "get_sheet_values", read)
    result = importer._read_sheet_to_df(None, "legacy-scan_data", "ProcConfig!A1:J")
    assert result.iloc[0, 0] == 42
    assert read.call_args.args[0] == "replacement-file"
