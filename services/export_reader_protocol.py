"""Narrow typed reader batch contracts at the credential authority boundary."""

import math
import re


def validate_reader_batch(operation, instruction):
    from services.export_execution_protocol import ProtocolError

    def reject():
        raise ProtocolError("Invalid inert reader batch instruction.")

    if operation == "updateDimensionProperties":
        if (
            set(instruction) != {"range", "properties", "fields"}
            or instruction["fields"] != "pixelSize"
            or not isinstance(instruction["properties"], dict)
            or set(instruction["properties"]) != {"pixelSize"}
            or type(instruction["properties"]["pixelSize"]) is not int
            or not 80 <= instruction["properties"]["pixelSize"] <= 480
        ):
            reject()
        grid = instruction["range"]
        if (
            not isinstance(grid, dict)
            or set(grid) != {"sheetId", "dimension", "startIndex", "endIndex"}
            or grid["dimension"] != "COLUMNS"
            or any(type(grid[k]) is not int for k in ("sheetId", "startIndex", "endIndex"))
            or not 0 <= grid["sheetId"] < 2**31
            or not 0 <= grid["startIndex"] < grid["endIndex"] <= 16384
        ):
            reject()
        return

    if operation == "setBasicFilter":
        if (
            set(instruction) != {"filter"}
            or not isinstance(instruction["filter"], dict)
            or set(instruction["filter"]) != {"range"}
        ):
            reject()
        grid = instruction["filter"]["range"]
        if not isinstance(grid, dict) or set(grid) != {
            "sheetId",
            "startRowIndex",
            "endRowIndex",
            "startColumnIndex",
            "endColumnIndex",
        }:
            reject()
        if any(type(v) is not int for v in grid.values()) or not (
            0 <= grid["sheetId"] < 2**31
            and 0 <= grid["startRowIndex"] < grid["endRowIndex"] <= 1_048_576
            and 0 <= grid["startColumnIndex"] < grid["endColumnIndex"] <= 16384
        ):
            reject()
        return
    if set(instruction) != {"start", "rows", "fields"} or instruction["fields"] not in {
        "userEnteredValue",
        "userEnteredValue,userEnteredFormat",
    }:
        reject()
    start = instruction["start"]
    if (
        not isinstance(start, dict)
        or set(start) != {"sheetId", "rowIndex", "columnIndex"}
        or any(type(v) is not int for v in start.values())
    ):
        reject()
    rows = instruction["rows"]
    if (
        not isinstance(rows, list)
        or not rows
        or not (
            0 <= start["sheetId"] < 2**31
            and 0 <= start["rowIndex"] < 1_048_576
            and 0 <= start["columnIndex"] < 16384
        )
    ):
        reject()
    if start["rowIndex"] + len(rows) > 1_048_576:
        reject()
    count = 0
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"values"}
            or not isinstance(row["values"], list)
            or start["columnIndex"] + len(row["values"]) > 16384
        ):
            reject()
        count += len(row["values"])
        for cell in row["values"]:
            if not isinstance(cell, dict) or set(cell) - {"userEnteredValue", "userEnteredFormat"}:
                reject()
            value = cell.get("userEnteredValue", {})
            if (
                not isinstance(value, dict)
                or len(value) > 1
                or set(value) - {"stringValue", "numberValue"}
            ):
                reject()
            if "stringValue" in value and (
                type(value["stringValue"]) is not str or len(value["stringValue"]) > 50_000
            ):
                reject()
            if "numberValue" in value and (
                type(value["numberValue"]) not in (int, float)
                or not math.isfinite(value["numberValue"])
            ):
                reject()
            fmt = cell.get("userEnteredFormat", {})
            if not isinstance(fmt, dict) or set(fmt) - {
                "numberFormat",
                "textFormat",
                "backgroundColor",
                "wrapStrategy",
            }:
                reject()
            number = fmt.get("numberFormat")
            if number is not None and (
                not isinstance(number, dict)
                or set(number) != {"type", "pattern"}
                or number["type"] not in {"TEXT", "NUMBER", "DATE_TIME", "PERCENT"}
                or not isinstance(number["pattern"], str)
                or len(number["pattern"]) > 128
            ):
                reject()
            text = fmt.get("textFormat", {})
            if (
                not isinstance(text, dict)
                or set(text) - {"bold", "link"}
                or ("bold" in text and type(text["bold"]) is not bool)
            ):
                reject()
            if "link" in text and (
                not isinstance(text["link"], dict)
                or set(text["link"]) != {"uri"}
                or not isinstance(text["link"]["uri"], str)
                or not re.fullmatch(
                    r"https://docs\.google\.com/spreadsheets/d/[A-Za-z0-9_-]{3,128}/edit#gid=[0-9]{1,10}",
                    text["link"]["uri"],
                )
            ):
                reject()
            color = fmt.get("backgroundColor")
            if color is not None and (
                not isinstance(color, dict)
                or set(color) != {"red", "green", "blue"}
                or any(type(v) not in (int, float) or not 0 <= v <= 1 for v in color.values())
            ):
                reject()
            if "wrapStrategy" in fmt and fmt["wrapStrategy"] != "WRAP":
                reject()
    if count > 50_000:
        reject()
