"""Entirely synthetic XLSX bytes; never read or copy a private source workbook."""

from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook

from kvk.models.new_source_observation import CampMapping, MetadataConfirmation, SourceScope
from kvk.schemas.new_source_schema import (
    CAMP_HEADERS,
    CAMP_SHEET,
    KINGDOM_HEADERS,
    KINGDOM_SHEET,
    PLAYER_HEADERS,
    PLAYER_SHEET,
)
from kvk.services.new_source_metadata import parse_filename_metadata, validate_source_metadata

SCOPE = SourceScope(16, (101, 102), ("fight:pass4", "overall", "no_fight:baseline"))
MAPPING = CampMapping(((101, 1, "North Camp"), (102, 2, "South Camp")))
CONFIRMATION = MetadataConfirmation(
    actor="synthetic-operator", confirmed_at_utc=datetime(2026, 9, 9, tzinfo=UTC)
)


def metadata(*, aggregate=False):
    name = (
        "kvk16_pass4_totals_live_20260906T1304Z.xlsx"
        if aggregate
        else ("kvk16_players_20260905T1526Z.xlsx")
    )
    confirmation = CONFIRMATION
    if aggregate:
        confirmation = MetadataConfirmation(
            values=(
                ("coverage_start_utc", datetime(2026, 9, 5, 15, 26, tzinfo=UTC)),
                ("coverage_end_utc", datetime(2026, 9, 6, 13, 4, tzinfo=UTC)),
                ("as_of_utc", datetime(2026, 9, 6, 13, 4, tzinfo=UTC)),
            ),
            actor=CONFIRMATION.actor,
            confirmed_at_utc=CONFIRMATION.confirmed_at_utc,
        )
    return validate_source_metadata(parse_filename_metadata(name), confirmation, SCOPE)


def player_row(governor=1001, kingdom=101, **changes):
    row = dict.fromkeys(PLAYER_HEADERS, 1)
    row.update(
        {
            "Governor ID": governor,
            "Kingdom": kingdom,
            "Name": "Synthetic Governor",
            "Alliance": "Synthetic",
            "Civilization": "Synthetic",
            "VIP": 0,
        }
    )
    row.update(changes)
    return row


def workbook_bytes(sheets, *, edit=None):
    workbook = Workbook()
    workbook.remove(workbook.active)
    try:
        for title, rows in sheets:
            sheet = workbook.create_sheet(title)
            for row in rows:
                sheet.append(row)
        if edit:
            edit(workbook)
        with BytesIO() as output:
            workbook.save(output)
            return output.getvalue()
    finally:
        workbook.close()


def player_bytes(rows=None, *, headers=PLAYER_HEADERS, edit=None):
    if rows is None:
        rows = [player_row(), player_row(1002, 102)]
    return workbook_bytes(
        [(PLAYER_SHEET, [headers, *[[row.get(header) for header in headers] for row in rows]])],
        edit=edit,
    )


def aggregate_bytes(*, token="25.3M", edit=None, reverse_sheets=False):
    sheets = [
        (
            KINGDOM_SHEET,
            [
                KINGDOM_HEADERS,
                ["North Camp", 101, *([token] * 8)],
                ["South Camp", 102, *([token] * 8)],
            ],
        ),
        (
            CAMP_SHEET,
            [CAMP_HEADERS, ["North Camp", *(["4.779B"] * 8)], ["South Camp", *(["1.20M"] * 8)]],
        ),
    ]
    return workbook_bytes(list(reversed(sheets)) if reverse_sheets else sheets, edit=edit)


def rewrite_zip(content, transform=None, *, additions=(), compression=ZIP_DEFLATED):
    with BytesIO(content) as source, ZipFile(source) as old, BytesIO() as output:
        with ZipFile(output, "w", compression=compression) as new:
            new.comment = b"synthetic re-export metadata"
            for entry in old.infolist():
                data = old.read(entry.filename)
                if transform:
                    data = transform(entry.filename, data)
                if data is not None:
                    new.writestr(entry.filename, data)
            for name, data in additions:
                new.writestr(name, data)
        return output.getvalue()


def calculation_event(scan_id=10, *, rows=None, day=5, periods=("fight:pass4", "overall")):
    """S3A revision-pinned synthetic observation, using the accepted S1 parser."""
    from dataclasses import replace

    from kvk.models.new_source_reporting import ObservationInput
    from kvk.services.new_source_parser import parse_player_workbook

    meta = metadata()
    meta = replace(
        meta,
        candidate=replace(
            meta.candidate, scan_start_utc=datetime(2026, 9, day, 15, 26, tzinfo=UTC)
        ),
    )
    prepared = parse_player_workbook(player_bytes(rows), meta)
    return ObservationInput(
        scan_id, f"observation-{scan_id}", f"revision-{scan_id}", prepared, periods
    )


def calculation_config(**changes):
    """10/20/40 are synthetic coefficients, never production configuration evidence."""
    from dataclasses import replace

    from kvk.models.new_source_reporting import FrozenWeights, PeriodKind, WindowConfig

    return replace(
        WindowConfig(
            "config-1",
            16,
            "period-pass4",
            "fight:pass4",
            PeriodKind.FIGHT,
            "Pass 4",
            10,
            13,
            "roster-1",
            "revision-1",
            "map-1",
            MAPPING,
            FrozenWeights("weights-1", "10", "20", "40", datetime(2026, 9, 1, tzinfo=UTC)),
        ),
        **changes,
    )


def worked_calculation_inputs():
    """T21-T30: four B0 members, one outsider, different endpoint coverage."""
    b0 = calculation_event(
        1,
        day=1,
        rows=[
            player_row(1001, Power=100_000_000),
            player_row(1002),
            player_row(1003),
            player_row(1004),
        ],
    )
    start = calculation_event(
        10,
        rows=[
            player_row(
                1001,
                **{
                    "T4 Kills": 100,
                    "T5 Kills": 200,
                    "Dead": 50,
                    "Total Kill Points": 6000,
                    "Power": 100_000_000,
                },
            ),
            player_row(1002),
            player_row(1004),
            player_row(9999),
        ],
    )
    middle = calculation_event(
        11,
        day=6,
        rows=[
            player_row(
                1001,
                **{
                    "T4 Kills": 120,
                    "T5 Kills": 230,
                    "Dead": 55,
                    "Total Kill Points": 6850,
                    "Power": 99_000_000,
                },
            ),
            player_row(1002),
            player_row(1003),
            player_row(9999),
        ],
    )
    end = calculation_event(
        13,
        day=7,
        rows=[
            player_row(
                1001,
                **{
                    "T4 Kills": 140,
                    "T5 Kills": 250,
                    "Dead": 60,
                    "Total Kill Points": 7500,
                    "Power": 98_000_000,
                },
            ),
            player_row(1002),
            player_row(1003),
            player_row(1004),
            player_row(9999, **{"T4 Kills": 999_999}),
        ],
    )
    return b0, start, middle, end
