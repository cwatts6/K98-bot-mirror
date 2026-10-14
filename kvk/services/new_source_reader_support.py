"""Readable support reports from pinned inputs; no source lookup or provider IO."""

from collections import defaultdict
from decimal import Decimal

from kvk.models.new_source_history import safe_basename
from kvk.models.new_source_reader import ReaderLink, no_fight as is_no_fight
from kvk.rendering.new_source_reader import columns_for, utc_time
from kvk.services.new_source_reader_service import REASONS, _issue, _sheet


def build_support(periods, reports, issues, history_rows, *, checkpoints=None):
    by_period = {s.period_id: (s, snapshot) for s, snapshot in periods}
    uses, targets = defaultdict(list), defaultdict(list)
    windows = {}
    # A selected period's own publication wins over another period's older config.
    ordered = sorted(
        periods,
        key=lambda p: (p[1]["metadata"]["configs"]["selected"]["WindowSeq"], p[0].period_id),
    )
    for selection, snapshot in ordered:
        for window in snapshot["reader_context"]["windows"]:
            windows[window["PeriodID"]] = window
    for selection, snapshot in ordered:
        config = snapshot["metadata"]["configs"]["selected"]
        windows[selection.period_id] = dict(config, PeriodID=selection.period_id)
        period = "Overall" if config["PeriodKind"] == "overall" else config["WindowName"]
        for role, revision in snapshot["reader_context"]["revisions"].items():
            if revision is None:
                continue
            label = (
                "Baseline"
                if role == "baseline"
                else period
                + {"start": " start", "end": " end", "aggregate": " kingdoms and camps"}[role]
            )
            if label not in uses[revision]:
                uses[revision].append(label)
            wanted = ("kingdom", "camp") if role == "aggregate" else ("player",)
            targets[revision].extend(
                r.key for r in reports if r.key in {selection.period_id + ":" + k for k in wanted}
            )
            for checkpoint in checkpoints or ():
                if any(
                    m.period_id == selection.period_id and m.status == "selected"
                    for m in checkpoint.members
                ):
                    cumulative = [
                        k
                        for k in checkpoint.sheet_keys
                        if ":cumulative:" in k and k.rsplit(":", 1)[-1] in wanted
                    ]
                    if cumulative:
                        label = "Fights to " + checkpoint.name
                        if label not in uses[revision]:
                            uses[revision].append(label)
                        targets[revision].extend(cumulative)
    scans, weights, scan_links = [], [], []
    for window in sorted(
        windows.values(),
        key=lambda w: (w["PeriodKind"] == "overall", w["WindowSeq"], w["PeriodID"]),
    ):
        period = "Overall" if window["PeriodKind"] == "overall" else window["WindowName"]
        selected = by_period.get(window["PeriodID"])
        no_fight = window["PeriodKind"] != "overall" and is_no_fight(window)
        row = {
            "Period": period,
            "Start Scan": window["StartScanID"],
            "End Scan": window["EndScanID"],
            "Status": "No fight" if no_fight else "Not published",
            "Selection Notes": window.get("Notes")
            or "Configured endpoints; no published selection yet.",
        }
        if no_fight:
            row["Selection Notes"] = (
                "Configured as no fight; no fighting export."
                if window["PeriodKind"] == "no_fight"
                else "Start and end scans are the same; no fighting export."
            )
        if selected:
            selection, snapshot = selected
            pub, meta = snapshot["envelope"]["publication"], snapshot["metadata"]
            row.update(
                {
                    "Start Scan": pub["StartScanID"],
                    "End Scan": pub["EndScanID"],
                    "Start (UTC)": (meta["endpoints"]["start"] or {}).get("ScanStartUTC"),
                    "End (UTC)": (meta["endpoints"]["end"] or {}).get("ScanStartUTC"),
                }
            )
            if not no_fight:
                row["Status"] = (
                    "Update pending"
                    if not snapshot["envelope"]["is_current"]
                    else REASONS.get(pub["PeriodState"], "Unavailable")
                )
                row["Selection Notes"] = (
                    window.get("Notes")
                    or "Selected endpoints from this publication's configuration."
                )
                if not snapshot["envelope"]["is_current"]:
                    row[
                        "Selection Notes"
                    ] += " Showing the published selection; a requested update is pending."
                aggregate = meta.get("aggregate") or {}
                pairs = (
                    (aggregate.get("CoverageStartUTC"), row.get("Start (UTC)")),
                    (aggregate.get("CoverageEndUTC"), row.get("End (UTC)")),
                )
                if any(
                    a is not None and b is not None and utc_time(a) != utc_time(b) for a, b in pairs
                ):
                    row[
                        "Selection Notes"
                    ] += " Aggregate coverage differs from selected scans; see audit."
                    issues.append(
                        _issue(
                            period,
                            "Scans",
                            {},
                            "Source coverage",
                            "Aggregate coverage differs from selected scans",
                            "Player and aggregate reports retain their own source authority; review audit coverage.",
                        )
                    )
                weights.append(
                    {
                        "Period": period,
                        **{
                            label: (
                                Decimal(snapshot["weights"][key])
                                if snapshot.get("weights")
                                and snapshot["weights"].get(key) is not None
                                else None
                            )
                            for label, key in (
                                ("T4 Kill Weight", "WeightT4XSource"),
                                ("T5 Kill Weight", "WeightT5YSource"),
                                ("Deads Weight", "WeightDeadsZSource"),
                            )
                        },
                        "Applies To": "Players only; kingdom and camp DKP comes from supplied reports.",
                    }
                )
            for report in reports:
                if report.key.startswith(selection.period_id + ":"):
                    scan_links.append(ReaderLink(len(scans), 0, report.key))
        scans.append(row)
    source_records, source_links = [], []
    for fact in history_rows:
        revision = fact["observation_revision_id"] or fact["aggregate_revision_id"]
        counts = (
            [fact["player_records"]]
            if fact["observation_revision_id"]
            else (
                [fact["kingdom_records"], fact["camp_records"]]
                if fact["aggregate_revision_id"]
                else [None]
            )
        )
        count = sum(counts) if all(v is not None for v in counts) else None
        notes = list(fact["notes"])
        if fact["aggregate_revision_id"] and count is not None:
            notes.append(f"{counts[0]} kingdom rows; {counts[1]} camp rows.")
        source_records.append(
            {
                "Scan": fact["scan"],
                "Source File": safe_basename(fact["source_file"]),
                "Data Included": fact["data_included"] or "Unknown",
                "Data Time (UTC)": fact["data_time_utc"],
                "Imported (UTC)": fact["imported_utc"],
                "Records": count,
                "Import Status": fact["import_status"],
                "Used In": "; ".join(uses[revision]) or "Not used",
                "Notes": " ".join(notes),
            }
        )
        source_links.extend(
            ReaderLink(len(source_records) - 1, 7, target)
            for target in dict.fromkeys(targets[revision])
        )
    support = [
        _sheet(
            issues,
            key="scans",
            title="Scans",
            period="All periods",
            purpose="Selected scan endpoints and configured no-fight windows",
            availability="Available",
            columns=columns_for("scans"),
            records=scans,
            links=scan_links,
        ),
        _sheet(
            issues,
            key="weights",
            title="DKP Weights",
            period="All periods",
            purpose="Frozen player scoring coefficients",
            availability="Available",
            columns=columns_for("weights"),
            records=weights,
        ),
        _sheet(
            issues,
            key="sources",
            title="Source Files",
            period="All periods",
            purpose="Every recorded import in the authorised season and guild",
            availability="Available",
            columns=columns_for("sources"),
            records=source_records,
            links=source_links,
            notes=(
                "Includes unused imports and duplicates. Duplicate files do not add another contribution.",
                "Import outcomes and selected revision uses are frozen for this export; receipt time is not data time.",
            ),
        ),
    ]
    # Link by report title only when unambiguous; logical targets never contain a URL/formula.
    title_targets = defaultdict(list)
    for report in reports + support:
        title_targets[report.title].append(report.key)
    issue_links = [
        ReaderLink(i, 1, title_targets[row["Report"]][0])
        for i, row in enumerate(issues)
        if len(title_targets[row["Report"]]) == 1
    ]
    issue_sheet = _sheet(
        [],
        key="issues",
        title="Data Issues",
        period="All periods",
        purpose="Grouped gaps and their effect on reader values",
        availability="Available",
        columns=columns_for("issues"),
        records=issues,
        links=issue_links,
        notes=(
            "Negative power changes are valid. Unsupported audit-only metrics are not reader errors.",
        ),
    )
    support.append(issue_sheet)
    guide_records = [
        {
            "Report": s.title,
            "Purpose": s.purpose,
            "Period": s.period,
            "Availability": s.availability,
        }
        for s in reports + support
    ]
    if checkpoints is not None:
        guide_records.extend(
            {
                "Report": w["WindowName"],
                "Purpose": "No fight; no fighting export",
                "Period": w["WindowName"],
                "Availability": "No fight",
            }
            for w in windows.values()
            if w["PeriodKind"] != "overall" and is_no_fight(w)
        )
    guide = _sheet(
        [],
        key="guide",
        title="Report Guide",
        period="All periods",
        purpose="Report directory and scoring definitions",
        availability="Available",
        columns=columns_for("guide"),
        records=guide_records,
        links=tuple(ReaderLink(i, 0, s.key) for i, s in enumerate(reports + support)),
        notes=(
            "Only T4+T5 KP counts. Player KP = 10 × T4 kills + 20 × T5 kills. T1–T3 kills remain audit-only.",
            "KP Loss = Healed Troops × 20. Tanking Score = T4+T5 KP / (KP Loss + Deads), shown as a percentage once; healed troops must be positive.",
            "Baseline Power is the fixed baseline. Fight-start Power is the selected fight endpoint. DKP / Baseline Power is a multiplier.",
            "Kingdom and camp DKP and tier KP use supplied report values, not player totals. Their displayed precision does not imply more precise measurements.",
            "Overall uses its independently selected publication. An unpublished Overall remains empty.",
            "Exact values and source metadata remain in the authorised audit; reader blanks are distinct from valid zero.",
            "No fight is shown in Scans for explicit no-fight periods or equal start and end scans; it has no fighting report.",
        ),
    )
    return [guide, *support]
