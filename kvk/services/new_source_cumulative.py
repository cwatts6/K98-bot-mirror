"""Cumulative fighting arithmetic using exact Stage 3 facts and frozen membership."""

from dataclasses import replace
from decimal import Decimal, localcontext

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.new_source_checkpoints import FightMember
from kvk.models.new_source_reporting import CalculatedMetric, fits_decimal
from kvk.rendering.new_source_reader import columns_for, utc_time
from kvk.schemas.new_source_schema import MetricState
from kvk.services.new_source_calculation import _ratio
from kvk.services.new_source_reader_service import _issue, _sheet

KINDS = {"player": "Players", "kingdom": "Kingdoms", "camp": "Camps"}


def exact_records(sheet):
    return [
        {
            c.label: (Decimal(v) if c.kind == "number" and v else None if not v else v)
            for c, v in zip(sheet.columns, row, strict=True)
        }
        for row in sheet.exact_rows
    ]


def entity_records(snapshot, sheet, kind):
    records = exact_records(sheet)
    if kind != "camp":
        label = "Governor ID" if kind == "player" else "Kingdom"
        result = {int(r[label]): r for r in records}
        if kind == "player":
            for source in snapshot["envelope"]["players"]:
                result[source["GovernorID"]]["_camp_id"] = source["CampID"]
        return result
    rows = sorted(
        snapshot["envelope"]["aggregates"]["SourceCampReportRow"], key=lambda r: r["CampID"]
    )
    rows.sort(key=lambda r: (r["dkp"] is not None, r["dkp"] or Decimal(0)), reverse=True)
    return {r["CampID"]: record for r, record in zip(rows, records, strict=True)}


def no_fight(window):
    return window["StartScanID"] is not None and window["StartScanID"] == window["EndScanID"]


def members_for(selection, snapshot, by_period):
    config = snapshot["metadata"]["configs"]["selected"]
    windows = {w["PeriodID"]: w for w in snapshot["reader_context"]["windows"]}
    if len(windows) != len(snapshot["reader_context"]["windows"]):
        raise SourceConflict("Duplicate configured fighting period.")
    windows[selection.period_id] = dict(config, PeriodID=selection.period_id)
    fights = [w for w in windows.values() if w["PeriodKind"] == "fight"]
    if len({w["WindowSeq"] for w in fights}) != len(fights):
        raise SourceConflict("Fighting order must be unambiguous.")
    members = []
    for w in sorted(fights, key=lambda w: w["WindowSeq"]):
        if w["WindowSeq"] > config["WindowSeq"]:
            continue
        status = "no_fight" if no_fight(w) else "missing"
        pins = {}
        if w["PeriodID"] in by_period:
            selected, snap = by_period[w["PeriodID"]]
            own = snap["metadata"]["configs"]["selected"]
            if own["PeriodKind"] != "fight" or (own["StartScanID"], own["EndScanID"]) != (
                w["StartScanID"],
                w["EndScanID"],
            ):
                raise SourceConflict(
                    "Checkpoint configuration differs from selected fight endpoints."
                )
            pub = snap["envelope"]["publication"]
            pins = dict(
                publication_id=selected.publication_id,
                selection_version=selected.selection_version,
                calculation_version=pub["CalculationVersion"],
                config_id=pub["ConfigVersionID"],
                roster_id=pub["RosterID"],
                revisions=tuple(sorted(snap["reader_context"]["revisions"].items())),
            )
            if status != "no_fight":
                status = "selected"
        members.append(
            FightMember(
                w["PeriodID"],
                w["WindowName"],
                w["WindowSeq"],
                w["StartScanID"],
                w["EndScanID"],
                status,
                **pins,
            )
        )
    return tuple(members)


def coverage_issues(members, by_period, *, aggregate):
    """Only disjoint effective fight intervals are additive; adjacent boundaries are valid."""
    problems, intervals, revisions = {}, [], set()
    for m in members:
        if m.status == "no_fight":
            continue
        if m.status == "missing":
            problems[m.period_id] = "not published"
            continue
        _, snap = by_period[m.period_id]
        meta, pub = snap["metadata"], snap["envelope"]["publication"]
        times = tuple(
            utc_time((meta["endpoints"][r] or {}).get("ScanStartUTC")) for r in ("start", "end")
        )
        if None in times or times[0] >= times[1]:
            problems[m.period_id] = "effective fight coverage unavailable"
            continue
        if aggregate:
            data = meta.get("aggregate") or {}
            coverage = tuple(utc_time(data.get(k)) for k in ("CoverageStartUTC", "CoverageEndUTC"))
            revision = pub["AggregateRevisionID"]
            if revision is None or coverage != times or revision in revisions:
                problems[m.period_id] = "window-only aggregate coverage not established"
                continue
            revisions.add(revision)
        for old, start, end in intervals:
            if times[0] < end and start < times[1]:
                problems[m.period_id] = problems[old] = "overlapping fighting coverage"
        intervals.append((m.period_id, *times))
    return problems


def ratio(numerator, denominator):
    if numerator is None or denominator is None:
        return None
    return _ratio(
        CalculatedMetric(numerator, MetricState.AVAILABLE),
        CalculatedMetric(denominator, MetricState.AVAILABLE),
    ).value


def cumulative_sheet(checkpoint, kind, by_period, facts, issues):
    members = [m for m in checkpoint.members if m.status != "no_fight"]
    available = [m for m in members if m.status == "selected"]
    columns = tuple(
        replace(c, label="Fighting Power Change") if c.label == "Power Change" else c
        for c in columns_for(kind)
        if c.label not in ("Fight-start Power", "End Power")
    )
    metric_labels = [
        c.label
        for c in columns
        if c.kind == "number"
        and c.label
        not in ("DKP Rank", "DKP / Baseline Power", "Tanking Score (%)", "Baseline Power")
    ]
    problems = coverage_issues(checkpoint.members, by_period, aggregate=kind != "player")
    tables = {m.period_id: facts.get((m.period_id, kind), {}) for m in available}
    identities = sorted(set().union(*(set(t) for t in tables.values())))
    if kind == "player":
        if len({(m.roster_id, dict(m.revisions)["baseline"]) for m in available}) != 1:
            raise SourceConflict("Cumulative players require one pinned baseline roster.")
    title = "Fights to " + checkpoint.name + " " + KINDS[kind]
    output = []
    incomplete, provisional = bool(problems), False
    with localcontext() as ctx:
        ctx.prec = 100
        for identity in identities:
            present = [
                tables[m.period_id][identity] for m in available if identity in tables[m.period_id]
            ]
            row = {c.label: present[-1].get(c.label) for c in columns if c.kind == "text"}
            missing = {}
            for label in metric_labels:
                source = "Power Change" if label == "Fighting Power Change" else label
                bad = [
                    m.name + ": " + (problems.get(m.period_id) or "metric unavailable")
                    for m in members
                    if m.period_id in problems
                    or tables.get(m.period_id, {}).get(identity, {}).get(source) is None
                ]
                value = (
                    None
                    if bad
                    else sum((tables[m.period_id][identity][source] for m in members), Decimal(0))
                )
                if value is not None and not fits_decimal(value, 6):
                    bad = ["cumulative numeric overflow"]
                    value = None
                row[label] = value
                if bad:
                    missing[label] = "; ".join(bad)
            if kind == "player":
                if len({(r["Kingdom"], r["_camp_id"], r["Baseline Power"]) for r in present}) != 1:
                    raise SourceConflict("Cumulative baseline power or attribution changed.")
                row["Baseline Power"] = present[0]["Baseline Power"]
                row["DKP / Baseline Power"] = ratio(row["Player DKP"], row["Baseline Power"])
                if row["DKP / Baseline Power"] is None:
                    missing["DKP / Baseline Power"] = (
                        "complete DKP and positive baseline power required"
                    )
            healed, loss, deads = row["Healed Troops"], row["KP Loss"], row["Deads"]
            row["Tanking Score (%)"] = (
                ratio(row["T4+T5 KP"], loss + deads)
                if healed is not None and healed > 0 and loss is not None and deads is not None
                else None
            )
            if row["Tanking Score (%)"] is None:
                missing["Tanking Score (%)"] = (
                    "No healed troops; score not applicable"
                    if healed == 0
                    and loss is not None
                    and deads is not None
                    and row["T4+T5 KP"] is not None
                    else "complete KP, KP Loss, Deads and positive healed troops required"
                )
            incomplete |= any(
                reason != "No healed troops; score not applicable" for reason in missing.values()
            )
            live = any(
                by_period[m.period_id][1]["envelope"]["publication"][
                    "PlayerState" if kind == "player" else "AggregateState"
                ]
                == "live"
                for m in available
            )
            provisional |= live
            row["Data Status"] = (
                "; ".join(
                    (["Live — provisional"] if live else []) + list(dict.fromkeys(missing.values()))
                )
                or "Available"
            )
            for reason in dict.fromkeys(missing.values()):
                labels = [label for label, why in missing.items() if why == reason]
                issues.append(
                    _issue(
                        checkpoint.name,
                        title,
                        row,
                        ", ".join(labels),
                        reason,
                        "Cumulative value is blank; independent complete metrics remain available.",
                    )
                )
            output.append(row)
        dkp = "Player DKP" if kind == "player" else "DKP"
        output.sort(
            key=lambda r: (r[dkp] is not None, r[dkp] if r[dkp] is not None else Decimal(0)),
            reverse=True,
        )
        if kind == "player":
            rank = 0
            for row in output:
                if row[dkp] is not None:
                    rank += 1
                row["DKP Rank"] = rank if row[dkp] is not None else None
    included = ", ".join(m.name for m in members)
    skipped = ", ".join(m.name for m in checkpoint.members if m.status == "no_fight") or "None"
    population = (
        f"DKP ranked population: {sum(r['DKP Rank'] is not None for r in output)}; baseline roster: {len(output)}."
        if kind == "player"
        else "Supplied entity rows retain their stable identifiers."
    )
    return _sheet(
        issues,
        key=checkpoint.period_id + ":cumulative:" + kind,
        title=title,
        period=checkpoint.name,
        purpose="All fighting through this checkpoint",
        availability=(
            "Incomplete" if incomplete else "Live — provisional" if provisional else "Available"
        ),
        columns=columns,
        records=output,
        notes=(
            f"Included fighting windows: {included}. Skipped (no fight): {skipped}.",
            "Totals require every contribution. Baseline power is counted once; ratios and ranks are recalculated. Fighting Power Change excludes gaps between fights.",
            "Kingdom and camp totals sum compatible supplied fight reports; they are not player totals.",
            population,
        ),
    )
