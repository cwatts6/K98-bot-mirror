"""Human column contract and exact typed projection, with no SQL or provider IO."""

from datetime import UTC, datetime

from kvk.models.new_source_reader import ReaderColumn, ReaderSheet, spreadsheet_number
from kvk.rendering.new_source_export import text_value

PLAYER_COLUMNS = (
    "Governor ID",
    "Player Name",
    "Kingdom",
    "Camp",
    "DKP Rank",
    "Player DKP",
    "DKP / Baseline Power",
    "T4+T5 KP",
    "T4 + T5 Kills",
    "T4 Kills",
    "T5 Kills",
    "Deads",
    "Healed Troops",
    "KP Loss",
    "Tanking Score (%)",
    "Acclaim Gained",
    "Baseline Power",
    "Fight-start Power",
    "End Power",
    "Power Change",
    "Data Status",
)
KINGDOM_COLUMNS = (
    "Kingdom",
    "Camp",
    "DKP",
    "T4+T5 KP",
    "T4 + T5 Kills",
    "T4 Kills",
    "T5 Kills",
    "Deads",
    "T4+T5 Deads",
    "Healed Troops",
    "KP Loss",
    "Tanking Score (%)",
    "Acclaim",
    "Data Status",
)
SUPPORT_COLUMNS = {
    "links": ("Source Sheet", "Source", "Report", "Period"),
    "guide": ("Report", "Purpose", "Period", "Availability"),
    "scans": (
        "Period",
        "Start Scan",
        "Start (UTC)",
        "End Scan",
        "End (UTC)",
        "Status",
        "Selection Notes",
    ),
    "weights": ("Period", "T4 Kill Weight", "T5 Kill Weight", "Deads Weight", "Applies To"),
    "sources": (
        "Scan",
        "Source File",
        "Data Included",
        "Data Time (UTC)",
        "Imported (UTC)",
        "Records",
        "Import Status",
        "Used In",
        "Notes",
    ),
    "issues": (
        "Period",
        "Report",
        "Governor ID",
        "Player Name",
        "Kingdom",
        "Camp",
        "Affected Metric",
        "Issue",
        "Effect on Report",
    ),
}
TEXT_COLUMNS = frozenset(
    (
        "Source Sheet",
        "Source",
        "Governor ID",
        "Player Name",
        "Kingdom",
        "Camp",
        "Data Status",
        "Period",
        "Status",
        "Selection Notes",
        "Applies To",
        "Source File",
        "Data Included",
        "Import Status",
        "Used In",
        "Notes",
        "Report",
        "Purpose",
        "Availability",
        "Affected Metric",
        "Issue",
        "Effect on Report",
    )
)


def columns_for(kind, *, overall=False):
    if kind == "player":
        labels = tuple(c for c in PLAYER_COLUMNS if not overall or c != "Fight-start Power")
    elif kind in ("kingdom", "camp"):
        labels = KINGDOM_COLUMNS if kind == "kingdom" else KINGDOM_COLUMNS[1:]
    else:
        labels = SUPPORT_COLUMNS[kind]
    result = []
    for label in labels:
        if label in TEXT_COLUMNS:
            result.append(ReaderColumn(label))
        elif label.endswith("(UTC)"):
            result.append(ReaderColumn(label, "datetime", "yyyy-mm-dd hh:mm:ss"))
        else:
            fmt = (
                '0.00"×"'
                if label == "DKP / Baseline Power"
                else "0.00%" if label == "Tanking Score (%)" else "#,##0.######"
            )
            result.append(ReaderColumn(label, "number", fmt))
    return tuple(result)


def utc_time(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime):
        raise ValueError("Expected a source UTC timestamp.")
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def project_sheet(
    *, key, title, period, purpose, availability, columns, records, notes=(), links=()
):
    """Return typed sheet and precision notices; never silently round source numbers.

    Every text cell is literal, including formula-like prefixes. A later provider
    adapter must honour that type; this model has no executable formula cell kind.
    """
    rows, exact_rows, notices = [], [], []
    for index, record in enumerate(records):
        row, exact = [], []
        for column in columns:
            value = record.get(column.label)
            if column.kind == "text" and value is not None:
                value = text_value(value)
            elif column.kind == "datetime":
                value = utc_time(value)
            exact.append(text_value(value))
            if column.kind == "number" and value is not None and not spreadsheet_number(value):
                notices.append((index, column.label))
                value = None
            row.append(value)
        rows.append(tuple(row))
        exact_rows.append(tuple(exact))
    return ReaderSheet(
        key,
        title,
        period,
        purpose,
        availability,
        columns,
        tuple(rows),
        tuple(exact_rows),
        tuple(notes),
        tuple(links),
    ), tuple(notices)
