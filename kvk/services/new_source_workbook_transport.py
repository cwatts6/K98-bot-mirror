"""Opt-in reader delivery with immutable grid IDs and typed, inert cell values.

Names are presentation only. Every write uses a persisted grid ID. Fresh IDs
increase above the remaining blank grid; retirement already replaces all grids
with max(ID)+1. Uncertain requests keep the existing durable ownership hold.
"""

from copy import deepcopy
import json

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.rendering.new_source_workbook import (
    DIRECTORY,
    WORKBOOK_VERSION,
    WorkbookGeneration,
    cell_value,
    column_layout,
    partition_workbook,
    payload_hash,
)
from kvk.services.new_source_export_service import GoogleSheetsTransport


class ReaderSheetsTransport(GoogleSheetsTransport):
    """Explicitly composed reader version; legacy callers retain their transport."""

    @classmethod
    def validate_observation(cls, generation, files):
        """Select only a complete persisted reader attempt, never provider metadata."""
        try:
            cls._validate_manifest(generation["tables"])
            layout = cls.partition_manifest(generation["tables"])
            bindings = generation["reader_bindings"]
            index_id = generation["reader_index_id"]
            if type(index_id) is not int or not 0 <= index_id < 2**31:
                raise ValueError("Invalid index ID")
            if set(bindings) != set(files[1:]) or len(layout) != len(files) - 1:
                raise ValueError("Invalid binding membership")
            for part, (file_id, pieces) in enumerate(zip(files[1:], layout, strict=True)):
                titles = ([DIRECTORY] if part == 0 else []) + [p["name"] for p in pieces]
                bound = bindings[file_id]
                if (
                    set(bound) != set(titles)
                    or any(type(v) is not int or not 0 <= v < 2**31 for v in bound.values())
                    or len(set(bound.values())) != len(bound)
                ):
                    raise ValueError("Invalid grid bindings")
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise SourceConflict("Complete persisted reader bindings required.") from exc

    def prepare_generation(self, generation):
        if not isinstance(generation, WorkbookGeneration):
            raise ValueError("Versioned reader generation required.")
        super().prepare_generation(generation.projection.audit)
        # Historical/final readers remain retained, including their source history.
        self._retained[generation.key] = True
        return generation

    @staticmethod
    def _validate_manifest(manifest):
        if not manifest or any(s.get("version") != WORKBOOK_VERSION for s in manifest.values()):
            raise ValueError("Versioned reader manifest required.")
        partition_workbook(manifest)

    @classmethod
    def partition_manifest(cls, manifest):
        return partition_workbook(manifest, max_cells=cls.MAX_CELLS)

    @staticmethod
    def _tab(key, name):
        return DIRECTORY if name == "DIRECTORY" else name

    def _get(self, file_id):
        file = super()._get(file_id)
        if file.get("description"):
            parsed = json.loads(file["description"])
            if parsed.get("reader_version") == WORKBOOK_VERSION:
                expected = getattr(self, "observation_bindings", None)
                if expected is not None and (
                    file_id not in expected
                    or parsed.get("bindings") != expected[file_id]
                    or parsed.get("index_id") != self.observation_index_id
                ):
                    raise SourceConflict("Reader identity differs from the persisted attempt.")
                file["reader_bindings"] = parsed["bindings"]
                file["reader_index_id"] = parsed["index_id"]
                file["description"] = json.dumps(parsed["manifest"], sort_keys=True)
        return file

    def _bind(self, destination, key, file, role, manifest, part=0):
        if role == "index":
            return super()._bind(destination, key, file, role, manifest, part)
        binding = self.reader_bindings[file["id"]]
        self._mutate(
            self.drive.files().update(
                fileId=file["id"],
                fields="id",
                body=dict(
                    appProperties=dict(
                        k98Destination=self._identity(destination, key),
                        k98Role=role,
                        k98Generation=key,
                        k98Retain="True",
                        k98Part=str(part),
                        k98Previous="blank",
                        k98Stage="preparing",
                    ),
                    description=json.dumps(
                        dict(
                            reader_version=WORKBOOK_VERSION,
                            manifest=manifest,
                            bindings=binding,
                            index_id=self.reader_index_id,
                        ),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
        )

    def _properties(self, file_id):
        return self._execute(
            self.sheets.spreadsheets().get(spreadsheetId=file_id, fields="sheets.properties")
        )["sheets"]

    def ensure_private(self, destination, key, manifest):
        callback = self._plan_callback
        # Never relabel an old generation. Reuse requires completed owned retirement
        # and its higher-ID blank grid, through the existing output-pool workflow.
        self.reuse_guard = lambda *_: False

        def plan(index, files, layout, specifications):
            props = self._properties(index["id"])
            if len(props) != 1 or props[0]["properties"]["title"] != "Sheet1":
                raise SourceConflict("Exact single-grid index required.")
            self.reader_index_id = props[0]["properties"]["sheetId"]
            self.reader_bindings = {}
            for part, (file, pieces) in enumerate(zip(files, layout, strict=True)):
                titles = ([DIRECTORY] if part == 0 else []) + [p["name"] for p in pieces]
                bindings = file.get("reader_bindings")
                if bindings is None:
                    grids = self._properties(file["id"])
                    if len(grids) != 1 or grids[0]["properties"]["title"] != "Sheet1":
                        raise SourceConflict(
                            "Fresh reader allocation requires a retired blank grid."
                        )
                    floor = grids[0]["properties"]["sheetId"]
                    if floor + len(titles) >= 2**31:
                        raise SourceConflict("Sheet identity exhausted; retire this file.")
                    bindings = {title: floor + i + 1 for i, title in enumerate(titles)}
                if set(bindings) != set(titles) or len(set(bindings.values())) != len(titles):
                    raise SourceConflict("Persisted reader bindings differ from the layout.")
                if file.get("reader_index_id", self.reader_index_id) != self.reader_index_id:
                    raise SourceConflict("Index grid was retired; old generation cannot publish.")
                self.reader_bindings[file["id"]] = bindings
            if callback is not None:
                callback(index, files, layout, specifications)

        self._plan_callback = plan
        try:
            index, files, layout, _ = self._prepare_files(destination, key, manifest)
        finally:
            self._plan_callback = callback
        for part, (file, pieces) in enumerate(zip(files, layout, strict=True)):
            self._staging_file(self._get(file["id"]))
            existing = {
                s["properties"]["title"]: s["properties"] for s in self._properties(file["id"])
            }
            binding = self.reader_bindings[file["id"]]
            specs = [
                (p["name"], p["rows"], p["columns"], manifest[p["table"]]["frozen_columns"])
                for p in pieces
            ]
            if part == 0:
                specs.insert(0, (DIRECTORY, sum(map(len, layout)), 5, 1))
            expected = {
                name: dict(
                    sheetId=binding[name],
                    title=name,
                    index=i,
                    gridProperties=dict(
                        rowCount=max(7, count + 6),
                        columnCount=width,
                        frozenRowCount=6,
                        frozenColumnCount=frozen,
                    ),
                )
                for i, (name, count, width, frozen) in enumerate(specs)
            }
            if set(existing) != set(expected):
                if (
                    set(existing) != {"Sheet1"}
                    or file["appProperties"].get("k98Stage") != "preparing"
                ):
                    raise SourceConflict("Unexpected reader grids require reconciliation.")
                blank = existing["Sheet1"]
                if any(sid <= blank["sheetId"] for sid in binding.values()):
                    raise SourceConflict("Reader grid IDs must increase after retirement.")
                requests = [
                    dict(
                        updateSheetProperties=dict(
                            properties=dict(
                                sheetId=blank["sheetId"],
                                gridProperties=dict(frozenRowCount=0, frozenColumnCount=0),
                            ),
                            fields="gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
                        )
                    ),
                    dict(
                        updateSheetProperties=dict(
                            properties=dict(
                                sheetId=blank["sheetId"],
                                gridProperties=dict(rowCount=1, columnCount=1),
                            ),
                            fields="gridProperties.rowCount,gridProperties.columnCount",
                        )
                    ),
                ]
                requests += [dict(addSheet=dict(properties=p)) for p in expected.values()]
                requests += [dict(deleteSheet=dict(sheetId=blank["sheetId"]))]
                self._mutate(
                    self.sheets.spreadsheets().batchUpdate(
                        spreadsheetId=file["id"], body=dict(requests=requests)
                    )
                )
            elif any(existing[name]["sheetId"] != binding[name] for name in expected):
                raise SourceConflict("Readable name points to another immutable grid.")
            self._mutate(
                self.drive.files().update(
                    fileId=file["id"], fields="id", body=dict(appProperties=dict(k98Stage="built"))
                )
            )
        if not any(k.startswith("k98") for k in index.get("appProperties", {})):
            self._bind(destination, key, index, "index", {})
        directory = self._reader_directory(files, layout)
        self._write_cells(
            files[0]["id"], self.reader_bindings[files[0]["id"]][DIRECTORY], directory, 5
        )

    def _targets(self, files, layout):
        targets = {}
        for file, pieces in zip(files, layout, strict=True):
            for piece in pieces:
                sid = file["reader_bindings"][piece["name"]]
                targets.setdefault(
                    piece["table"],
                    f"https://docs.google.com/spreadsheets/d/{file['id']}/edit#gid={sid}",
                )
        return targets

    def _reader_directory(self, files, layout):
        rows = [
            [{"userEnteredValue": cell_value(DIRECTORY)}, {}, {}, {}, {}],
            *[[{} for _ in range(5)] for _ in range(4)],
        ]
        rows.append(
            [
                {"userEnteredValue": cell_value(v)}
                for v in ("Report", "Workbook", "First data row", "Rows", "Open report")
            ]
        )
        for i, (file, pieces) in enumerate(zip(files, layout, strict=True)):
            for p in pieces:
                url = f"https://docs.google.com/spreadsheets/d/{file['id']}/edit#gid={file['reader_bindings'][p['name']]}"
                row = [
                    {"userEnteredValue": cell_value(v)}
                    for v in (p["table"], i + 1, p["offset"] + 1, p["rows"], p["name"])
                ]
                row[-1]["userEnteredFormat"] = {"textFormat": {"link": {"uri": url}}}
                for cell, (_, wrap) in zip(
                    row,
                    column_layout(("Report", "Workbook", "First data row", "Rows", "Open report")),
                    strict=True,
                ):
                    if wrap:
                        cell.setdefault("userEnteredFormat", {})["wrapStrategy"] = "WRAP"
                rows.append(row)
        for cell in rows[5]:
            cell["userEnteredFormat"] = {"wrapStrategy": "WRAP", "textFormat": {"bold": True}}
        return rows

    def _write_cells(self, file_id, sheet_id, values, width):
        self._mutate(
            self.sheets.spreadsheets().batchUpdate(
                spreadsheetId=file_id,
                body=dict(
                    requests=[
                        dict(
                            updateDimensionProperties=dict(
                                range=dict(
                                    sheetId=sheet_id,
                                    dimension="COLUMNS",
                                    startIndex=i,
                                    endIndex=i + 1,
                                ),
                                properties=dict(pixelSize=pixels),
                                fields="pixelSize",
                            )
                        )
                        for i, (pixels, _) in enumerate(
                            column_layout(
                                c.get("userEnteredValue", {}).get("stringValue", "")
                                for c in values[5]
                            )
                        )
                    ]
                ),
            )
        )
        step = min(self.batch_rows, max(1, 50_000 // width))
        for start in range(0, len(values), step):
            self._mutate(
                self.sheets.spreadsheets().batchUpdate(
                    spreadsheetId=file_id,
                    body=dict(
                        requests=[
                            dict(
                                updateCells=dict(
                                    start=dict(sheetId=sheet_id, rowIndex=start, columnIndex=0),
                                    rows=[dict(values=r) for r in values[start : start + step]],
                                    fields="userEnteredValue,userEnteredFormat",
                                )
                            )
                        ]
                    ),
                )
            )
        self._mutate(
            self.sheets.spreadsheets().batchUpdate(
                spreadsheetId=file_id,
                body=dict(
                    requests=[
                        dict(
                            setBasicFilter=dict(
                                filter=dict(
                                    range=dict(
                                        sheetId=sheet_id,
                                        startRowIndex=5,
                                        endRowIndex=max(7, len(values)),
                                        startColumnIndex=0,
                                        endColumnIndex=width,
                                    )
                                )
                            )
                        )
                    ]
                ),
            )
        )

    def write_range(self, destination, key, name, cell, values, *, value_input_option):
        files = self._files(destination, key)
        manifest = json.loads(files[0]["description"])
        if (
            cell != "A1"
            or value_input_option != "RAW"
            or name not in manifest
            or payload_hash(values) != manifest[name]["sha256"]
        ):
            raise SourceConflict("Typed write differs from its immutable reader manifest.")
        layout = self.partition_manifest(manifest)
        targets = self._targets(files, layout)
        for file, pieces in zip(files, layout, strict=True):
            if file["id"] in self.quarantined or (
                not self.preserve_public_staging
                and any(p.get("type") == "anyone" for p in file["permissions"])
            ):
                raise SourceConflict("Reader writes require the admitted staging audience.")
            for p in pieces:
                if p["table"] != name:
                    continue
                rows = deepcopy(values[:6] + values[6 + p["offset"] : 6 + p["offset"] + p["rows"]])
                for row in rows:
                    for value in row:
                        if "readerLink" in value:
                            target = value.pop("readerLink")
                            value.setdefault("userEnteredFormat", {})["textFormat"] = {
                                "link": {"uri": targets[target]}
                            }
                self._write_cells(
                    file["id"], file["reader_bindings"][p["name"]], rows, p["columns"]
                )

    def _read_cells(self, file_id, title, count, width, sheet_id):
        result = []
        column_pixels = None
        requested_count = count
        count = max(7, count)
        step = min(self.batch_rows, max(1, 50_000 // width))
        for start in range(0, count, step):
            end = min(count, start + step)
            escaped = title.replace("'", "''")
            response = self._execute(
                self.sheets.spreadsheets().get(
                    spreadsheetId=file_id,
                    ranges=[f"'{escaped}'!A{start+1}:{self._column(width)}{end}"],
                    fields="sheets(properties,data(startRow,startColumn,columnMetadata(pixelSize),rowData(values(userEnteredValue,userEnteredFormat,hyperlink,textFormatRuns))),basicFilter)",
                )
            )
            sheets = response.get("sheets", [])
            if (
                len(sheets) != 1
                or sheets[0]["properties"]["title"] != title
                or sheets[0]["properties"]["sheetId"] != sheet_id
            ):
                raise SourceConflict("Reader readback returned another grid.")
            expected_filter = dict(
                sheetId=sheet_id,
                startRowIndex=5,
                endRowIndex=count,
                startColumnIndex=0,
                endColumnIndex=width,
            )
            if sheets[0].get("basicFilter", {}).get("range") != expected_filter:
                raise SourceConflict("Reader filter differs from the complete data range.")
            blocks = sheets[0].get("data", [])
            if len(blocks) > 1 or (
                blocks
                and (blocks[0].get("startRow", 0) != start or blocks[0].get("startColumn", 0) != 0)
            ):
                raise SourceConflict("Reader readback offsets differ.")
            rows = blocks[0].get("rowData", []) if blocks else []
            pixels = (
                [c.get("pixelSize") for c in blocks[0].get("columnMetadata", [])] if blocks else []
            )
            if len(pixels) != width or (column_pixels is not None and pixels != column_pixels):
                raise SourceConflict("Reader column widths are missing or changed during readback.")
            column_pixels = pixels
            if len(rows) > end - start or any(len(r.get("values", [])) > width for r in rows):
                raise SourceConflict("Reader readback exceeds the pinned rectangle.")
            for row in rows:
                values = row.get("values", [])
                for value in values:
                    fmt = value.get("userEnteredFormat", {})
                    color = fmt.get("backgroundColor")
                    style = fmt.pop("backgroundColorStyle", None)
                    if style is not None and style != {"rgbColor": color}:
                        raise SourceConflict("Reader background color representations disagree.")
                    # The provider truncates our header palette to 8-bit RGB,
                    # then returns float32 components and a duplicate style.
                    header = {"red": 0.85, "green": 0.9, "blue": 0.96}
                    if (
                        color is not None
                        and set(color) == set(header)
                        and all(
                            abs(color[k] - int(v * 255) / 255) < 0.0000001
                            for k, v in header.items()
                        )
                    ):
                        fmt["backgroundColor"] = header
                    # Sheets can return a whole-cell link only as the read-only
                    # hyperlink field, omitting the written textFormat.link.
                    # Preserve exact target verification after normalization.
                    if value.get("textFormatRuns"):
                        raise SourceConflict("Unexpected rich-text runs in reader cells.")
                    value.pop("textFormatRuns", None)
                    link = value.pop("hyperlink", None)
                    if link:
                        text = value.setdefault("userEnteredFormat", {}).setdefault(
                            "textFormat", {}
                        )
                        if "link" in text and text["link"] != {"uri": link}:
                            raise SourceConflict("Reader hyperlink representations disagree.")
                        text["link"] = {"uri": link}
                result.append([*values, *({} for _ in range(width - len(values)))])
            result.extend([[{} for _ in range(width)] for _ in range(end - start - len(rows))])
        if any(any(cell for cell in row) for row in result[requested_count:]):
            raise SourceConflict("Unexpected data in an empty reader sheet.")
        expected_pixels = [
            p
            for p, _ in column_layout(
                c.get("userEnteredValue", {}).get("stringValue", "") for c in result[5]
            )
        ]
        if column_pixels != expected_pixels:
            raise SourceConflict("Reader column widths differ from the readable layout.")
        return result[:requested_count]

    def verify(self, destination, key):
        return self._read_verified_manifest(destination, key, require_match=True)

    def _assess_contents(self, destination, key):
        return self._read_verified_manifest(destination, key, require_match=False)

    def _read_verified_manifest(self, destination, key, *, require_match):
        self._verified.discard(key)
        if hasattr(self, "observation_index_id"):
            grids = self._properties(self.registration.index_file_id)
            if len(grids) != 1 or grids[0]["properties"]["sheetId"] != self.observation_index_id:
                raise SourceConflict("Reader index identity differs from the persisted attempt.")
        files = self._files(destination, key)
        manifest = json.loads(files[0]["description"])
        layout = self.partition_manifest(manifest)
        targets = {url: name for name, url in self._targets(files, layout).items()}
        combined = {name: [] for name in manifest}
        for part, (file, pieces) in enumerate(zip(files, layout, strict=True)):
            actual = {
                s["properties"]["title"]: s["properties"] for s in self._properties(file["id"])
            }
            if set(actual) != set(file["reader_bindings"]):
                raise SourceConflict("Reader grid inventory differs.")
            for title, sid in file["reader_bindings"].items():
                if actual[title]["sheetId"] != sid:
                    raise SourceConflict("Reader grid identity differs.")
            if part == 0:
                expected_directory = self._reader_directory(files, layout)
                directory_grid = actual[DIRECTORY]
                if directory_grid.get("index") != 0 or any(
                    directory_grid["gridProperties"].get(k) != v
                    for k, v in dict(
                        rowCount=len(expected_directory),
                        columnCount=5,
                        frozenRowCount=6,
                        frozenColumnCount=1,
                    ).items()
                ):
                    raise SourceConflict("Reader directory dimensions or order differ.")
                if payload_hash(
                    self._read_cells(
                        file["id"],
                        DIRECTORY,
                        len(expected_directory),
                        5,
                        file["reader_bindings"][DIRECTORY],
                    )
                ) != payload_hash(expected_directory):
                    raise SourceConflict("Reader directory differs.")
            for p in pieces:
                spec = manifest[p["table"]]
                grid = actual[p["name"]]["gridProperties"]
                if any(
                    grid.get(k) != v
                    for k, v in dict(
                        rowCount=max(7, p["rows"] + 6),
                        columnCount=p["columns"],
                        frozenRowCount=6,
                        frozenColumnCount=spec["frozen_columns"],
                    ).items()
                ):
                    raise SourceConflict("Reader grid dimensions or frozen panes differ.")
                rows = self._read_cells(
                    file["id"],
                    p["name"],
                    6 + p["rows"],
                    p["columns"],
                    file["reader_bindings"][p["name"]],
                )
                for row in rows:
                    for value in row:
                        fmt = value.get("userEnteredFormat", {})
                        link = fmt.get("textFormat", {}).get("link")
                        if link:
                            if link.get("uri") not in targets:
                                raise SourceConflict("Reader navigation escapes its generation.")
                            value["readerLink"] = targets[link["uri"]]
                            text = fmt["textFormat"]
                            text.pop("link")
                            if not text:
                                fmt.pop("textFormat")
                        if "formulaValue" in value.get("userEnteredValue", {}):
                            raise SourceConflict("Reader contains an executable formula.")
                prior = combined[p["table"]]
                if prior and prior[:6] != rows[:6]:
                    raise SourceConflict("Reader partition headers differ.")
                prior.extend(rows if not prior else rows[6:])
        observed = {
            name: dict(spec, sha256=payload_hash(combined[name])) for name, spec in manifest.items()
        }
        if require_match and observed != manifest:
            raise SourceConflict("Typed reader contents differ from the generation.")
        if observed == manifest:
            self._verified.add(key)
        return observed

    def publish_current(self, destination, key, fence):
        if key not in self._verified or type(fence) is not int or fence <= 0:
            raise SourceConflict("Verified reader and positive fence required.")
        files, index = self._files(destination, key), self._index(destination, key)
        current = self._pointer(index)
        if current and (
            len(current) != 1
            or len(current[0]) != 3
            or not current[0][1].isdecimal()
            or int(current[0][1]) > fence
            or (int(current[0][1]) == fence and current[0][0] != key)
        ):
            raise SourceConflict("A conflicting publication fence is current.")
        sid = files[0]["reader_bindings"][DIRECTORY]
        url = f"https://docs.google.com/spreadsheets/d/{files[0]['id']}/edit#gid={sid}"
        index_id = files[0]["reader_index_id"]
        if any(f["reader_index_id"] != index_id for f in files):
            raise SourceConflict("Reader parts disagree on index identity.")
        if self.registration.audience == "public_viewer":
            for file in files:
                self._public_file(file)
        # A1:C1 stays machine compatible, but this request cannot address a
        # replacement Sheet1 after season rollover: it uses the original ID.
        self._mutate(
            self.sheets.spreadsheets().batchUpdate(
                spreadsheetId=index["id"],
                body=dict(
                    requests=[
                        dict(
                            updateCells=dict(
                                start=dict(sheetId=index_id, rowIndex=0, columnIndex=0),
                                rows=[
                                    dict(
                                        values=[
                                            dict(userEnteredValue=cell_value(v))
                                            for v in (key, str(fence), url)
                                        ]
                                    )
                                ],
                                fields="userEnteredValue",
                            )
                        )
                    ]
                ),
            )
        )
        if self.registration.audience == "public_viewer":
            self._public_file(self._get(index["id"]))
        return url
