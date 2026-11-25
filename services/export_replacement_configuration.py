"""Bounded value-only configuration copies for shared workbook recovery.

Column contracts match the ProcConfig staging and six imported SQL tables.
No query or provider operation comes from the administrator's input.
"""

from copy import deepcopy
from decimal import Decimal, InvalidOperation

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_configuration_values import numeric_value, sql_text, verify_import_values

CONFIGURATION_COLUMNS = {
    "ProcConfig": (
        "KVK_NO",
        "LASTKVKEND",
        "MATCHMAKING_SCAN",
        "PRE_PASS_4_SCAN",
        "PASS4END",
        "PASS6END",
        "PASS7END",
        "KVK_END_SCAN",
        "CURRENTKVK3",
        "DRAFTSCAN",
    ),
    "KVKTargetBands": ("KVKVersion", "MinPower", "KillTarget", "MinKillTarget", "DeadTarget"),
    "EXEMPT": ("GovernorID", "GovernorName", "Exempt", "KVK_NO"),
    "KVK_Details": (
        "KVK_NO",
        "KVK_NAME",
        "KVK_REGISTRATION_DATE",
        "KVK_START_DATE",
        "KVK_END_DATE",
        "MATCHMAKING_SCAN",
        "KVK_END_SCAN",
        "NEXT_KVK_NO",
        "MATCHMAKING_START_DATE",
        "FIGHTING_START_DATE",
        "PASS4_START_SCAN",
    ),
    "KVK_DKPWeights": ("KVK_NO", "WeightT4X", "WeightT5Y", "WeightDeadsZ"),
    "KVK_Windows": ("KVK_NO", "WindowName", "WindowSeq", "StartScanID", "EndScanID", "Notes"),
    "KVK_CampMap": ("KVK_NO", "Kingdom", "CampID", "CampName"),
}
CONFIGURATION_TABS = tuple(sorted(CONFIGURATION_COLUMNS))


def configuration_grids(file_id, response):
    """Require the complete known input set plus one empty output placeholder."""
    from services.export_replacement_verification import discovered_grid

    if response.get("spreadsheetId") != file_id or any(
        response.get(key) for key in ("namedRanges", "developerMetadata", "dataSources")
    ):
        raise SourceConflict("Configuration workbook identity or external metadata differs.")
    sheets = response.get("sheets")
    if not isinstance(sheets, list) or len(sheets) != len(CONFIGURATION_TABS) + 1:
        raise SourceConflict(
            "Copy the seven listed configuration tabs as values and retain one blank Sheet1."
        )
    grids, ids = {}, set()
    for sheet in sheets:
        if not isinstance(sheet, dict) or set(sheet) != {"properties"}:
            raise SourceConflict(
                "Configuration tabs may not contain filters, merges or external metadata."
            )
        props = deepcopy(sheet["properties"])
        name = props.get("title")
        if name not in (*CONFIGURATION_TABS, "Sheet1") or name in grids:
            raise SourceConflict(
                "The configuration copy has missing, duplicate or unexpected tabs."
            )
        shape = props.get("gridProperties", {})
        for key, limit in (("frozenRowCount", "rowCount"), ("frozenColumnCount", "columnCount")):
            count = shape.get(key, 0)
            if type(count) is not int or not 0 <= count <= shape.get(limit, -1):
                raise SourceConflict("Configuration frozen-grid dimensions are invalid.")
            if name != "Sheet1":
                shape.pop(key, None)
        grid = discovered_grid(
            file_id, dict(spreadsheetId=file_id, sheets=[dict(properties=props)])
        )
        if grid["sheet_id"] in ids:
            raise SourceConflict("Configuration grid identities must be distinct.")
        ids.add(grid["sheet_id"])
        grids[name] = grid
    if set(grids) != {*CONFIGURATION_TABS, "Sheet1"}:
        raise SourceConflict("The complete configuration tab set is required.")
    return dict(
        grids["Sheet1"],
        configuration_grids=[grids[name] for name in (*CONFIGURATION_TABS, "Sheet1")],
    )


def configuration_requests(file):
    from services.export_replacement_verification import replacement_requests

    result = list(replacement_requests(file)[:2])
    for grid in file["configuration_grids"]:
        result.extend(replacement_requests(grid)[2:])
    return tuple(result)


def _table_values(name, grid, sheet, cells, *, include_rows=False):
    from services.export_manual_enrollment import _range_suffix

    if (
        sheet.get("spreadsheetId") != grid["file_id"]
        or cells.get("spreadsheetId") != grid["file_id"]
    ):
        raise SourceConflict("Configuration readback belongs to another workbook.")
    tabs = sheet.get("sheets", [])
    selected = [s for s in tabs if s.get("properties", {}).get("sheetId") == grid["sheet_id"]]
    if (
        len(selected) != 1
        or len(tabs) != 1
        or any(sheet.get(k) for k in ("namedRanges", "developerMetadata", "dataSources"))
    ):
        raise SourceConflict("Configuration grid membership changed during verification.")
    tab = selected[0]
    props = tab.get("properties", {})
    shape = props.get("gridProperties", {})
    if (
        (props.get("title"), shape.get("rowCount"), shape.get("columnCount"))
        != (name, grid["rows"], grid["columns"])
        or props.get("hidden", False) is not False
        or props.get("sheetType", "GRID") != "GRID"
        or set(tab) - {"properties", "data"}
    ):
        raise SourceConflict("Configuration grid shape changed during verification.")
    ranges = cells.get("valueRanges", [])
    quoted = "'" + name.replace("'", "''") + "'" + _range_suffix(grid)
    if len(ranges) != 1 or ranges[0].get("range") not in {quoted, name + _range_suffix(grid)}:
        raise SourceConflict("Complete configuration formula readback is required.")
    values = deepcopy(ranges[0].get("values", []))
    if (
        not isinstance(values, list)
        or len(values) > grid["rows"]
        or any(not isinstance(row, list) or len(row) > grid["columns"] for row in values)
    ):
        raise SourceConflict("Configuration values exceed the observed grid.")
    actual, formatted = {}, {}
    blocks = tab.get("data", [])
    if not isinstance(blocks, list) or len(blocks) > 1:
        raise SourceConflict("One complete configuration grid readback is required.")
    for block in blocks:
        if block.get("startRow", 0) != 0 or block.get("startColumn", 0) != 0 or actual:
            raise SourceConflict("Configuration readback has unexpected offsets or overlaps.")
        rows = block.get("rowData", [])
        if len(rows) > grid["rows"]:
            raise SourceConflict("Configuration rows exceed the observed grid.")
        for r, row in enumerate(rows):
            if len(row.get("values", [])) > grid["columns"]:
                raise SourceConflict("Configuration columns exceed the observed grid.")
            for c, cell in enumerate(row.get("values", [])):
                if any(cell.get(k) for k in ("pivotTable", "dataSourceTable", "dataSourceFormula")):
                    raise SourceConflict("Configuration must contain independent copied values.")
                entered = cell.get("userEnteredValue", {})
                if set(entered) - {"stringValue", "numberValue", "boolValue"} or len(entered) > 1:
                    raise SourceConflict(
                        "Copy configuration as values; formulas and errors are not accepted."
                    )
                value = next(iter(entered.values()), "")
                if cell.get("effectiveValue", entered) != entered:
                    raise SourceConflict(
                        "Configuration effective content differs from its entered values."
                    )
                if value not in (None, ""):
                    actual[r, c] = value
                    formatted[r, c] = cell.get("formattedValue", value)
    expected = {
        (r, c): v for r, row in enumerate(values) for c, v in enumerate(row) if v not in (None, "")
    }
    if actual != expected:
        raise SourceConflict("Configuration value and formula readbacks disagree.")
    columns = CONFIGURATION_COLUMNS[name]
    if (
        not values
        or tuple(values[0]) != columns
        or tuple(formatted.get((0, c), "") for c in range(len(columns))) != columns
    ):
        raise SourceConflict(f"{name}: use these headers in order: {', '.join(columns)}.")
    rows = []
    for row_index, source in enumerate(values[1:], 1):
        if not any(v not in (None, "") for v in source):
            continue
        if len(source) > len(columns):
            raise SourceConflict(f"{name}: unexpected values outside the configuration columns.")
        row = dict(zip(columns, [*source, *([None] * (len(columns) - len(source)))], strict=True))
        # Import uses FORMATTED_VALUE for every column. Keep the independent
        # entered/formula comparison above, then validate the actual import text.
        for c, column in enumerate(columns):
            if row[column] not in (None, ""):
                entered = row[column]
                displayed = formatted.get((row_index, c), entered)
                if type(entered) in (int, float) and not column.endswith("_DATE"):
                    try:
                        if Decimal(str(entered)) != Decimal(str(displayed)):
                            raise ValueError("Changed numeric meaning")
                    except (ValueError, InvalidOperation) as exc:
                        raise SourceConflict(
                            f"{name}: {column} formatting changes its imported value. "
                            "Use plain numbers, then check again."
                        ) from exc
                row[column] = str(displayed) if not isinstance(displayed, bool) else displayed
        rows.append(row)
    _validate_rows(name, rows)
    if include_rows:
        return rows
    return dict(tab=name, rows=len(rows), sha256=digest(values).hex())


def _validate_rows(name, rows):
    keys = {
        "ProcConfig": ("KVK_NO",),
        "KVKTargetBands": ("KVKVersion", "MinPower"),
        "EXEMPT": (),
        "KVK_Details": ("KVK_NO",),
        "KVK_DKPWeights": ("KVK_NO",),
        "KVK_Windows": ("KVK_NO", "WindowName"),
        "KVK_CampMap": ("KVK_NO", "Kingdom"),
    }
    text = {"GovernorName": 255, "KVK_NAME": 100, "WindowName": 40, "Notes": 200, "CampName": 40}
    dates = {
        "KVK_REGISTRATION_DATE",
        "KVK_START_DATE",
        "KVK_END_DATE",
        "MATCHMAKING_START_DATE",
        "FIGHTING_START_DATE",
    }
    required = set(keys[name]) | (
        set(CONFIGURATION_COLUMNS[name]) if name in {"KVK_DKPWeights", "KVK_CampMap"} else set()
    )
    if name == "EXEMPT":
        required.add("GovernorID")
    seen = set()
    if name == "ProcConfig" and not rows:
        raise SourceConflict("ProcConfig must contain the retained season configuration.")
    for row in rows:
        normalized = {}
        for column, value in row.items():
            if value in (None, ""):
                if column in required:
                    raise SourceConflict(f"{name}: {column} is required on every data row.")
                continue
            if column in text:
                if not sql_text(value, text[column]):
                    raise SourceConflict(f"{name}: {column} has invalid text.")
                normalized[column] = value.strip().casefold()
            elif column in dates:
                continue  # The actual importer date parser is checked below.
            else:
                normalized[column] = numeric_value(name, column, value)
        if name == "KVK_Windows":
            start, end = normalized.get("StartScanID"), normalized.get("EndScanID")
            if start is not None and end is not None and end < start:
                raise SourceConflict("KVK_Windows: EndScanID must not precede StartScanID.")
        key = tuple(normalized.get(column) for column in keys[name])
        if keys[name] and key in seen:
            raise SourceConflict(f"{name}: duplicate configuration key.")
        seen.add(key)
    verify_import_values(name, rows, text, dates)


def configuration_readback(value, file, responses):
    from services.export_manual_enrollment import verify_blank_workbook

    if len(responses) != 18:
        raise SourceConflict("Complete configuration and blank-output observations required.")
    metadata, _, *observations = responses
    summary = []
    for index, grid in enumerate(file["configuration_grids"]):
        sheet, cells = observations[index * 2 : index * 2 + 2]
        if grid["title"] == "Sheet1":
            # The file owner and metadata are checked here as well.
            verify_blank_workbook(value, grid, metadata, sheet, cells)
        else:
            summary.append(_table_values(grid["title"], grid, sheet, cells))
    return summary
