"""Excel / Google Sheets compatible Account Data workbook builder."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from numbers import Number
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import xlsxwriter
    from xlsxwriter.utility import xl_range_abs
except Exception as exc:  # pragma: no cover - dependency is pinned in production
    raise RuntimeError("XlsxWriter is required for Account Data workbooks.") from exc

from player_self_service.account_data_export_contract import (
    AccountDataExportMetadata,
    AccountDataOutputKind,
    filter_history_window,
    spreadsheet_safe_text,
)
from player_self_service.accounts_export import CSV_COLUMNS, account_row_values
from player_self_service.accounts_models import AccountMetricTotal, AccountsPortfolioPayload
from stats.dal.stats_export_dal import EXPORT_COLUMNS

ALL_DAILY_COLUMNS = tuple(EXPORT_COLUMNS)
FIXED_SHEETS = ("ACCOUNT_SUMMARY", "README", "ALL_DAILY")
_FORBIDDEN_SHEET_CHARS = set("[]:*?/\\")


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_sheet_name(base: str, fallback: str, max_len: int = 31) -> str:
    value = (base or "").strip().strip("'")
    value = "".join(
        character
        for character in value
        if character not in _FORBIDDEN_SHEET_CHARS and ord(character) >= 32
    )
    return (value or fallback)[:max_len]


def _escape_sheet_name_for_reference(sheet_name: str) -> str:
    """Escape an Excel sheet name embedded inside a single-quoted reference."""
    return sheet_name.replace("'", "''")


def _calc_period(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> dict:
    """Summarise snapshots and deltas inside an inclusive period."""
    window = df[(df["AsOfDate"] >= start_date) & (df["AsOfDate"] <= end_date)]
    snapshot = df[df["AsOfDate"] <= end_date].tail(1)

    def colsum(column: str) -> int:
        if column not in window:
            return 0
        return int(pd.to_numeric(window[column], errors="coerce").fillna(0).sum())

    def snapv(column: str) -> int:
        if snapshot.empty or column not in snapshot or pd.isna(snapshot[column].iloc[0]):
            return 0
        return int(snapshot[column].iloc[0])

    return {
        "PowerEnd": snapv("Power"),
        "TroopPowerEnd": snapv("TroopPower"),
        "KillPointsEnd": snapv("KillPoints"),
        "DeadsEnd": snapv("Deads"),
        "RSSGatheredEnd": snapv("RSS_Gathered"),
        "RSSAssistEnd": snapv("RSSAssist"),
        "HelpsEnd": snapv("Helps"),
        "PowerDelta": colsum("PowerDelta"),
        "TroopPowerDelta": colsum("TroopPowerDelta"),
        "KillPointsDelta": colsum("KillPointsDelta"),
        "DeadsDelta": colsum("DeadsDelta"),
        "RSS_GatheredDelta": colsum("RSS_GatheredDelta"),
        "RSSAssistDelta": colsum("RSSAssistDelta"),
        "HelpsDelta": colsum("HelpsDelta"),
        "TechDonationsSum": colsum("TechDonations"),
        "FortsTotalEnd": snapv("FortsTotal"),
        "FortsLaunchedSum": colsum("FortsLaunched"),
        "FortsJoinedSum": colsum("FortsJoined"),
        "AOOJoinedEnd": snapv("AOOJoined"),
        "AOOWonEnd": snapv("AOOWon"),
        "AOOAvgKillEnd": snapv("AOOAvgKill"),
        "AOOAvgDeadEnd": snapv("AOOAvgDead"),
        "AOOAvgHealEnd": snapv("AOOAvgHeal"),
        "T4_KillsEnd": snapv("T4_Kills"),
        "T5_KillsEnd": snapv("T5_Kills"),
        "T4T5_KillsEnd": snapv("T4T5_Kills"),
        "HealedTroopsEnd": snapv("HealedTroops"),
        "RangedPointsEnd": snapv("RangedPoints"),
        "HighestAcclaimEnd": snapv("HighestAcclaim"),
        "AutarchTimesEnd": snapv("AutarchTimes"),
        "T4_KillsDelta": colsum("T4_KillsDelta"),
        "T5_KillsDelta": colsum("T5_KillsDelta"),
        "T4T5_KillsDelta": colsum("T4T5_KillsDelta"),
        "HealedTroopsDelta": colsum("HealedTroopsDelta"),
        "RangedPointsDelta": colsum("RangedPointsDelta"),
    }


def _normalise_history(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy(deep=True)
    for column in ALL_DAILY_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = pd.NA
    prepared = prepared.loc[:, ALL_DAILY_COLUMNS].copy()
    prepared["AsOfDate"] = pd.to_datetime(prepared["AsOfDate"], errors="coerce")
    prepared["GovernorID"] = pd.to_numeric(prepared["GovernorID"], errors="coerce")
    prepared = prepared.loc[prepared["AsOfDate"].notna() & prepared["GovernorID"].notna()].copy()
    if not prepared.empty:
        prepared["GovernorID"] = prepared["GovernorID"].astype("int64")
        prepared = prepared.sort_values(
            ["GovernorID", "AsOfDate"], ascending=[True, False], kind="mergesort"
        ).reset_index(drop=True)
    return prepared


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(result) if isinstance(result, (bool, np.bool_)) else False


def _write_value(worksheet, row: int, column: int, value: Any, formats: dict[str, Any]) -> None:
    if _is_missing(value):
        worksheet.write_blank(row, column, None, formats["body"])
    elif isinstance(value, pd.Timestamp):
        worksheet.write_datetime(row, column, value.to_pydatetime(), formats["date"])
    elif isinstance(value, datetime):
        worksheet.write_datetime(row, column, value, formats["datetime"])
    elif isinstance(value, (Number, Decimal)) and not isinstance(value, bool):
        number = float(value)
        if np.isfinite(number):
            worksheet.write_number(row, column, number, formats["number"])
        else:
            worksheet.write_blank(row, column, None, formats["body"])
    else:
        worksheet.write_string(row, column, spreadsheet_safe_text(value), formats["body"])


def _date_text(value: Any) -> str:
    if value is None:
        return "Not applicable"
    if isinstance(value, datetime):
        stamp = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return stamp.isoformat(timespec="seconds")
    return value.isoformat()


def _governor_display_names(
    portfolio: AccountsPortfolioPayload | None, history: pd.DataFrame
) -> dict[int, str]:
    names: dict[int, str] = {}
    if portfolio is not None:
        for row in portfolio.rows:
            if row.governor_id is not None and row.governor_id not in names:
                names[row.governor_id] = row.display_name
    if not history.empty:
        for governor_id, group in history.groupby("GovernorID", sort=False):
            values = group["GovernorName"].dropna() if "GovernorName" in group else pd.Series()
            if int(governor_id) not in names and not values.empty:
                names[int(governor_id)] = str(values.iloc[0])
    return names


def _build_sheet_names(governor_ids: Iterable[int], names: dict[int, str]) -> dict[int, str]:
    used = {item.casefold() for item in FIXED_SHEETS}
    result: dict[int, str] = {}
    for governor_id in governor_ids:
        gid = int(governor_id)
        suffix = f"-{gid}"
        clean_name = _safe_sheet_name(names.get(gid, "Account"), "Account", max_len=31)
        prefix = clean_name[: max(1, 31 - len(suffix))]
        candidate = f"{prefix}{suffix}"[:31]
        counter = 2
        while candidate.casefold() in used:
            collision_suffix = f"-{gid}-{counter}"
            candidate = f"{clean_name[: max(1, 31 - len(collision_suffix))]}{collision_suffix}"[:31]
            counter += 1
        used.add(candidate.casefold())
        result[gid] = candidate
    return result


def _workbook_formats(workbook) -> dict[str, Any]:
    return {
        "title": workbook.add_format(
            {"bold": True, "font_size": 16, "font_color": "#FFFFFF", "bg_color": "#17365D"}
        ),
        "section": workbook.add_format(
            {"bold": True, "font_color": "#FFFFFF", "bg_color": "#1F4E78"}
        ),
        "header": workbook.add_format(
            {"bold": True, "font_color": "#FFFFFF", "bg_color": "#5B9BD5", "border": 1}
        ),
        "body": workbook.add_format({"border": 1, "valign": "top"}),
        "number": workbook.add_format({"border": 1, "num_format": "#,##0"}),
        "date": workbook.add_format({"border": 1, "num_format": "yyyy-mm-dd"}),
        "datetime": workbook.add_format({"border": 1, "num_format": "yyyy-mm-dd hh:mm:ss"}),
        "link": workbook.add_format({"border": 1, "font_color": "#0563C1", "underline": True}),
        "note": workbook.add_format({"text_wrap": True, "valign": "top"}),
    }


def _write_account_summary(
    workbook,
    portfolio: AccountsPortfolioPayload | None,
    sheet_names: dict[int, str],
    formats: dict[str, Any],
) -> None:
    worksheet = workbook.add_worksheet("ACCOUNT_SUMMARY")
    worksheet.freeze_panes(1, 0)
    worksheet.write_row(0, 0, CSV_COLUMNS, formats["header"])
    rows = portfolio.rows if portfolio is not None else ()
    for row_index, portfolio_row in enumerate(rows, start=1):
        values = account_row_values(portfolio_row)
        for column_index, value in enumerate(values):
            _write_value(worksheet, row_index, column_index, value, formats)
        governor_id = portfolio_row.governor_id
        if governor_id is not None and governor_id in sheet_names:
            link_column = 3 if values[3] else 4
            display = str(spreadsheet_safe_text(values[link_column]))
            escaped_sheet_name = _escape_sheet_name_for_reference(sheet_names[governor_id])
            worksheet.write_url(
                row_index,
                link_column,
                f"internal:'{escaped_sheet_name}'!A1",
                formats["link"],
                display,
            )
    worksheet.autofilter(0, 0, max(1, len(rows)), len(CSV_COLUMNS) - 1)
    worksheet.set_column(0, 3, 20)
    worksheet.set_column(4, 26, 16)
    worksheet.set_column(27, 28, 22)


def _write_readme(workbook, metadata: AccountDataExportMetadata, formats: dict[str, Any]) -> None:
    worksheet = workbook.add_worksheet("README")
    worksheet.set_column(0, 0, 34)
    worksheet.set_column(1, 1, 88)
    worksheet.write(0, 0, "Account Data workbook", formats["title"])
    rows = (
        ("Generated UTC", _date_text(metadata.generated_at_utc)),
        ("Authorised distinct governors", metadata.authorised_governor_count),
        ("Current snapshot rows", metadata.snapshot_row_count),
        ("History rows written", metadata.history_row_count),
        ("Requested history days", metadata.requested_days),
        ("Selected window start", _date_text(metadata.window_start)),
        ("Selected window end", _date_text(metadata.window_end)),
        ("Actual written start", _date_text(metadata.written_start)),
        ("Actual written end", _date_text(metadata.written_end)),
        ("Stats freshness", _date_text(metadata.stats_freshness)),
        ("Governor scan freshness", _date_text(metadata.governor_scan_freshness)),
        ("Inventory oldest", _date_text(metadata.inventory_oldest)),
        ("Inventory latest", _date_text(metadata.inventory_latest)),
        (
            "Inventory coverage",
            (
                f"{metadata.inventory_reporting_count}/{metadata.inventory_expected_count} linked rows"
                if metadata.inventory_reporting_count is not None
                and metadata.inventory_expected_count is not None
                else "Not applicable"
            ),
        ),
    )
    for row_index, (label, value) in enumerate(rows, start=2):
        worksheet.write(row_index, 0, label, formats["header"])
        _write_value(worksheet, row_index, 1, value, formats)
    notes = (
        "ACCOUNT_SUMMARY is the current all-linked account snapshot. ALL_DAILY and each governor "
        "worksheet contain only the selected inclusive Stats history window. Source gaps are not "
        "filled. Current/lifetime snapshots and selected-window deltas are labelled separately.\n\n"
        "This .xlsx file is compatible with Microsoft Excel and Google Sheets. To use Sheets, "
        "upload the downloaded file to Google Drive and open it with Google Sheets; no live Sheet "
        "was created or shared."
    )
    worksheet.merge_range(18, 0, 23, 1, notes, formats["note"])


def _write_all_daily(workbook, history: pd.DataFrame, formats: dict[str, Any]) -> None:
    worksheet = workbook.add_worksheet("ALL_DAILY")
    worksheet.freeze_panes(1, 0)
    worksheet.write_row(0, 0, ALL_DAILY_COLUMNS, formats["header"])
    for row_index, values in enumerate(history.itertuples(index=False, name=None), start=1):
        for column_index, value in enumerate(values):
            _write_value(worksheet, row_index, column_index, value, formats)
    worksheet.autofilter(0, 0, max(1, len(history.index)), len(ALL_DAILY_COLUMNS) - 1)
    worksheet.set_column(0, 2, 18)
    worksheet.set_column(3, 3, 13)
    worksheet.set_column(4, len(ALL_DAILY_COLUMNS) - 1, 16)


def _numeric_sum(frame: pd.DataFrame, column: str) -> int:
    if column not in frame:
        return 0
    return int(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def _write_governor_sheet(
    workbook,
    *,
    sheet_name: str,
    governor_id: int,
    display_name: str,
    history_desc: pd.DataFrame,
    metadata: AccountDataExportMetadata,
    formats: dict[str, Any],
) -> None:
    worksheet = workbook.add_worksheet(sheet_name)
    worksheet.write(
        0, 0, f"{spreadsheet_safe_text(display_name)} ({governor_id})", formats["title"]
    )
    worksheet.write(
        1,
        0,
        f"Selected {metadata.requested_days or 0}-day window: "
        f"{_date_text(metadata.window_start)} to {_date_text(metadata.window_end)}",
        formats["note"],
    )
    if history_desc.empty:
        worksheet.write(3, 0, "No Stats history exists for this governor in the selected window.")
        worksheet.set_column(0, 0, 90)
        return

    history = history_desc.sort_values("AsOfDate", ascending=True, kind="mergesort").reset_index(
        drop=True
    )
    latest_date = pd.Timestamp(history["AsOfDate"].max()).normalize()
    month_start = latest_date.replace(day=1)
    previous_end = month_start - pd.Timedelta(days=1)
    previous_start = previous_end.replace(day=1)
    selected_start = pd.Timestamp(history["AsOfDate"].min()).normalize()
    selected = _calc_period(history, selected_start, latest_date)
    month = _calc_period(history, month_start, latest_date)
    previous = _calc_period(history, previous_start, previous_end)

    worksheet.write_row(
        3,
        0,
        (
            "Metric",
            "Current / lifetime snapshot",
            f"Selected {metadata.requested_days}-day delta",
            "MTD delta within window",
            "Previous-month delta within window",
        ),
        formats["header"],
    )
    metrics = (
        ("Power", "PowerEnd", "PowerDelta"),
        ("Troop Power", "TroopPowerEnd", "TroopPowerDelta"),
        ("Kill Points", "KillPointsEnd", "KillPointsDelta"),
        ("T4+T5 Kills", "T4T5_KillsEnd", "T4T5_KillsDelta"),
        ("Deads", "DeadsEnd", "DeadsDelta"),
        ("Healed Troops", "HealedTroopsEnd", "HealedTroopsDelta"),
        ("RSS Gathered", "RSSGatheredEnd", "RSS_GatheredDelta"),
        ("RSS Assistance", "RSSAssistEnd", "RSSAssistDelta"),
        ("Helps", "HelpsEnd", "HelpsDelta"),
    )
    for row_index, (label, snapshot_key, delta_key) in enumerate(metrics, start=4):
        worksheet.write(row_index, 0, label, formats["body"])
        for column_index, value in enumerate(
            (
                selected[snapshot_key],
                selected[delta_key],
                month[delta_key],
                previous[delta_key],
            ),
            start=1,
        ):
            _write_value(worksheet, row_index, column_index, value, formats)

    forts_row = 14
    worksheet.write_row(
        forts_row,
        0,
        ("Selected-window Forts", "Total", "Launched", "Joined"),
        formats["header"],
    )
    worksheet.write_row(
        forts_row + 1,
        0,
        (
            f"Selected {metadata.requested_days} days",
            _numeric_sum(history, "FortsTotal"),
            _numeric_sum(history, "FortsLaunched"),
            _numeric_sum(history, "FortsJoined"),
        ),
        formats["number"],
    )

    daily_columns = list(ALL_DAILY_COLUMNS) + ["FortsTotal_Cumulative"]
    table_row = 19
    worksheet.write_row(table_row, 0, daily_columns, formats["header"])
    forts = pd.to_numeric(history.get("FortsTotal", 0), errors="coerce").fillna(0).cumsum()
    for offset, values in enumerate(history.itertuples(index=False, name=None), start=1):
        for column_index, value in enumerate(values):
            _write_value(worksheet, table_row + offset, column_index, value, formats)
        _write_value(
            worksheet,
            table_row + offset,
            len(ALL_DAILY_COLUMNS),
            forts.iloc[offset - 1],
            formats,
        )
    worksheet.autofilter(
        table_row,
        0,
        table_row + len(history.index),
        len(daily_columns) - 1,
    )
    worksheet.freeze_panes(table_row + 1, 4)
    worksheet.set_column(0, 0, 18)
    worksheet.set_column(1, 2, 22)
    worksheet.set_column(3, len(daily_columns) - 1, 16)

    first_data_row = table_row + 1
    last_data_row = table_row + len(history.index)
    date_column = daily_columns.index("AsOfDate")

    chart_specs = (
        ("Power and Troop Power", ("Power", "TroopPower"), "G2"),
        ("Kill Points", ("KillPoints",), "G18"),
        ("Resources", ("RSS_Gathered", "RSSAssist"), "O2"),
        ("Combat", ("T4T5_Kills", "Deads", "HealedTroops"), "O18"),
        ("Forts cumulative", ("FortsTotal_Cumulative",), "W2"),
    )
    for title, series_columns, anchor in chart_specs:
        chart = workbook.add_chart({"type": "line"})
        for column_name in series_columns:
            column_index = daily_columns.index(column_name)
            chart.add_series(
                {
                    "name": column_name,
                    "categories": [
                        sheet_name,
                        first_data_row,
                        date_column,
                        last_data_row,
                        date_column,
                    ],
                    "values": [
                        sheet_name,
                        first_data_row,
                        column_index,
                        last_data_row,
                        column_index,
                    ],
                }
            )
        chart.set_title({"name": title})
        chart.set_legend({"position": "bottom"})
        chart.set_size({"width": 520, "height": 280})
        worksheet.insert_chart(anchor, chart)

    sparkline_start = max(first_data_row, last_data_row - 29)
    quoted_sheet = _escape_sheet_name_for_reference(sheet_name)
    worksheet.write(16, 0, "Last 30 source rows", formats["section"])
    for row_index, column_name in enumerate(("Power", "KillPoints", "RSS_Gathered"), start=16):
        worksheet.write(row_index, 1, column_name, formats["body"])
        column_index = daily_columns.index(column_name)
        worksheet.add_sparkline(
            row_index,
            2,
            {
                "range": (
                    f"'{quoted_sheet}'!"
                    f"{xl_range_abs(sparkline_start, column_index, last_data_row, column_index)}"
                ),
                "type": "line",
            },
        )


def build_account_data_workbook(
    history_frame: pd.DataFrame,
    *,
    portfolio: AccountsPortfolioPayload,
    governor_ids: tuple[int, ...],
    metadata: AccountDataExportMetadata,
    out_path: str | Path,
) -> str:
    """Build the locked Account-Summary-first workbook from prefiltered history."""
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    history = _normalise_history(history_frame)
    names = _governor_display_names(portfolio, history)
    sheet_names = _build_sheet_names(governor_ids, names)

    workbook = xlsxwriter.Workbook(
        str(target),
        {"strings_to_formulas": False, "strings_to_urls": False, "constant_memory": False},
    )
    try:
        formats = _workbook_formats(workbook)
        _write_account_summary(workbook, portfolio, sheet_names, formats)
        _write_readme(workbook, metadata, formats)
        _write_all_daily(workbook, history, formats)
        for governor_id in governor_ids:
            group = history.loc[history["GovernorID"] == int(governor_id)].copy()
            _write_governor_sheet(
                workbook,
                sheet_name=sheet_names[int(governor_id)],
                governor_id=int(governor_id),
                display_name=names.get(int(governor_id), f"Governor {governor_id}"),
                history_desc=group,
                metadata=metadata,
                formats=formats,
            )
    finally:
        workbook.close()
    return str(target)


def build_user_stats_excel(
    df_daily: pd.DataFrame,
    _df_targets: pd.DataFrame | None,
    *,
    out_path: str,
    days_for_daily_table: int = 90,
) -> None:
    """Compatibility wrapper; the Account Data service uses build_account_data_workbook."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    window = filter_history_window(df_daily, days_for_daily_table)
    governor_ids = tuple(
        int(value)
        for value in pd.to_numeric(
            window.frame.get("GovernorID", pd.Series(dtype=int)), errors="coerce"
        )
        .dropna()
        .drop_duplicates()
        .tolist()
    )
    metadata = AccountDataExportMetadata(
        output_kind=AccountDataOutputKind.FULL_WORKBOOK,
        generated_at_utc=datetime.now(UTC),
        authorised_governor_count=len(governor_ids),
        snapshot_row_count=0,
        history_row_count=window.row_count,
        requested_days=days_for_daily_table,
        window_start=window.window_start,
        window_end=window.window_end,
        written_start=window.written_start,
        written_end=window.written_end,
        stats_freshness=window.window_end,
        governor_scan_freshness=None,
        inventory_oldest=None,
        inventory_latest=None,
        inventory_reporting_count=None,
        inventory_expected_count=None,
    )
    empty_portfolio = AccountsPortfolioPayload(
        discord_user_id=0,
        state="SETUP",
        rows=(),
        linked_count=0,
        main_row=None,
        role_counts=(),
        power=AccountMetricTotal(value=None, reporting_count=0, expected_count=0),
        troop_power=AccountMetricTotal(value=None, reporting_count=0, expected_count=0),
        t4_t5_kills=AccountMetricTotal(value=None, reporting_count=0, expected_count=0),
        rss_total=AccountMetricTotal(value=None, reporting_count=0, expected_count=0),
        insight="",
        refreshed_at_utc=metadata.generated_at_utc,
    )
    build_account_data_workbook(
        window.frame,
        portfolio=empty_portfolio,
        governor_ids=governor_ids,
        metadata=metadata,
        out_path=out_path,
    )
