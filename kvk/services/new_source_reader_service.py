"""Pure publication-pinned reader reports. No provider calls or current reselection."""

from collections import defaultdict
from decimal import Decimal
import json

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.new_source_history import HISTORY_VERSION, HistorySnapshot, encode_fact, hash_row
from kvk.models.new_source_reader import ReaderProjection, no_fight
from kvk.models.new_source_reporting import CalculatedMetric
from kvk.rendering.new_source_reader import columns_for, project_sheet
from kvk.schemas.new_source_schema import SOURCE_KEY, MetricState
from kvk.services.new_source_export_service import build_generation
from kvk.services.new_source_report_metrics import derive_report_metrics

METRICS = {
    "T4+T5 KP": "kp_t4_t5",
    "T4 + T5 Kills": "kills_gain",
    "T4 Kills": "t4_kills",
    "T5 Kills": "t5_kills",
    "Deads": "dead",
    "Healed Troops": "healed",
    "KP Loss": "kp_loss",
    "Tanking Score (%)": "tanking_score",
}
REASONS = {
    "missing_start": "Missing start scan",
    "missing_end": "Missing end scan",
    "invalid_source_value": "Invalid source value",
    "counter_regression": "Counter regression",
    "unsupported": "Not supplied by this source",
    "missing_configuration": "Missing configuration",
    "not_applicable": "Not applicable",
    "not_received": "Not published",
    "final_unavailable": "Unavailable",
    "validation_failed": "Source validation failed",
    "live": "Live — provisional",
    "final": "Published",
    "corrected_final": "Published — corrected",
}


def _issue(period, report, row, metric, reason, effect):
    return {
        "Period": period,
        "Report": report,
        **{c: row.get(c) for c in ("Governor ID", "Player Name", "Kingdom", "Camp")},
        "Affected Metric": metric,
        "Issue": reason,
        "Effect on Report": effect,
    }


def _sheet(issues, *, records, **kwargs):
    sheet, notices = project_sheet(records=records, **kwargs)
    grouped = defaultdict(list)
    for index, label in notices:
        grouped[index].append(label)
    for index, labels in grouped.items():
        issues.append(
            _issue(
                sheet.period,
                sheet.title,
                records[index],
                ", ".join(labels),
                "Spreadsheet precision limit",
                "Numeric cells left blank; exact values retained in audit.",
            )
        )
    if grouped and "Data Status" in [c.label for c in sheet.columns]:
        changed = [dict(r) for r in records]
        for index, labels in grouped.items():
            changed[index]["Data Status"] += (
                "; Precision limit: " + ", ".join(labels) + " (see audit)"
            )
        sheet, _ = project_sheet(records=changed, **kwargs)
    return sheet


def _value(row, metric, *, aggregate=False):
    state = (
        "available" if aggregate else json.loads(row["FieldStatusJson"]).get(metric, "unsupported")
    )
    value = row.get(metric) if state == "available" else None
    if state == "available" and value is None:
        state = "invalid_source_value"
    if value is not None:
        if type(value) not in (int, Decimal):
            raise ValueError("Published metrics must be exact numbers.")
        value = Decimal(value)
    return CalculatedMetric(value, MetricState(state))


def _power(row, role):
    value = row.get(role + "Power")
    statuses = json.loads(row.get(role + "FieldStatusJson") or "{}")
    state = statuses.get("power", statuses.get("Power", "unsupported"))
    if isinstance(state, dict):
        state = state.get("state", "unsupported")
    if state == "invalid_source_value":
        return CalculatedMetric(None, MetricState.INVALID_SOURCE_VALUE)
    if state != "available" or value is None:
        return CalculatedMetric(
            None, MetricState.MISSING_END if role == "End" else MetricState.MISSING_START
        )
    if (
        type(value) not in (int, Decimal)
        or not Decimal(value).is_finite()
        or value < 0
        or value != int(value)
    ):
        return CalculatedMetric(None, MetricState.INVALID_SOURCE_VALUE)
    return CalculatedMetric(Decimal(value), MetricState.AVAILABLE)


def _ranked_players(pub, rows):
    if len(rows) != pub["EligibleCount"]:
        raise SourceConflict("Reader requires the complete published player cohort.")
    ordered = sorted(rows, key=lambda r: r["GovernorID"])
    valid = [r for r in ordered if _value(r, "dkp").value is not None]
    valid.sort(key=lambda r: r["dkp"], reverse=True)
    for rank, row in enumerate(valid, 1):
        if (row.get("dkp_rank"), row.get("dkp_cohort")) != (rank, len(valid)):
            raise SourceConflict("Published ordinal ranking or cohort differs.")
    missing = [r for r in ordered if _value(r, "dkp").value is None]
    if any(r.get("dkp_rank") is not None or r.get("dkp_cohort") is not None for r in missing):
        raise SourceConflict("Unavailable DKP cannot carry a rank.")
    return valid + missing, len(valid)


def _entity_sheet(selection, snapshot, kind, issues):
    context = snapshot["reader_context"]
    pub, meta = context["publication"], context["metadata"]
    overall = meta["configs"]["selected"]["PeriodKind"] == "overall"
    empty_overall = overall and no_fight(meta["configs"]["selected"])
    period = "Overall" if overall else meta["configs"]["selected"]["WindowName"]
    title = period + " " + {"player": "Players", "kingdom": "Kingdoms", "camp": "Camps"}[kind]
    key = selection.period_id + ":" + kind
    camps = {r["CampID"]: r["CampName"] for r in meta["camps"]}
    source_rows = (
        snapshot["envelope"]["players"]
        if kind == "player"
        else snapshot["envelope"]["aggregates"][
            "SourceKingdomReportRow" if kind == "kingdom" else "SourceCampReportRow"
        ]
    )
    terminal = pub["PlayerState" if kind == "player" else "AggregateState"] == "final_unavailable"
    population = None
    if kind == "player":
        if empty_overall:
            if len(source_rows) != pub["EligibleCount"]:
                raise SourceConflict("Reader requires the complete published player cohort.")
        else:
            source_rows, population = _ranked_players(pub, source_rows)
    else:
        if empty_overall and source_rows:
            raise SourceConflict("No-fight Overall cannot contain aggregate rows.")
        source_rows = sorted(
            source_rows, key=lambda r: r["Kingdom" if kind == "kingdom" else "CampID"]
        )
        source_rows.sort(key=lambda r: (r["dkp"] is not None, r["dkp"] or Decimal(0)), reverse=True)
    if terminal:
        identity = {"player": "GovernorID", "kingdom": "Kingdom", "camp": "CampID"}[kind]
        source_rows = sorted(source_rows, key=lambda row: row[identity])
    powers = {r["GovernorID"]: r for r in snapshot["player_powers"]}
    if kind == "player" and (
        len(powers) != len(snapshot["player_powers"])
        or set(powers) != {r["GovernorID"] for r in source_rows}
    ):
        raise SourceConflict("Pinned powers must cover the complete published roster exactly once.")
    output = []
    for row in (() if empty_overall else source_rows):
        derived = derive_report_metrics(
            publication_id=selection.publication_id,
            calculation_version=pub["CalculationVersion"],
            entity_kind=kind,
            row=row,
            aggregate_revision_id=pub["AggregateRevisionID"] if kind != "player" else None,
        )
        facts = dict(METRICS)
        facts.update(
            {
                "Player DKP" if kind == "player" else "DKP": "dkp",
                "Acclaim Gained" if kind == "player" else "Acclaim": "acclaim",
            }
        )
        result = {"Camp": camps.get(row["CampID"], row.get("CampLabel") or f"Camp {row['CampID']}")}
        if kind == "player":
            result.update(
                {
                    "Governor ID": str(row["GovernorID"]),
                    "Player Name": row["name"],
                    "Kingdom": str(row["b0_kingdom"]),
                    "DKP Rank": row["dkp_rank"],
                }
            )
            facts.update({"DKP / Baseline Power": "dkp_power_ratio", "Power Change": "power"})
        elif kind == "kingdom":
            result["Kingdom"] = str(row["Kingdom"])
        if kind != "player":
            facts["T4+T5 Deads"] = "t4_t5_dead"
        unavailable = defaultdict(list)
        for label, metric in facts.items():
            value = (
                derived.metric(metric)
                if metric in dict(derived.metrics)
                else _value(row, metric, aggregate=kind != "player")
            )
            result[label] = value.value
            if value.value is None:
                reason = (
                    "No healed troops; score not applicable"
                    if value.reason == "no_healed_troops"
                    else REASONS.get(value.state.value, "Unavailable")
                )
                unavailable[reason].append(label)
        if kind == "player":
            power = powers[row["GovernorID"]]
            if power["b0_kingdom"] != row["b0_kingdom"]:
                raise SourceConflict("Player power attribution differs from the baseline roster.")
            for label, role in (
                ("Baseline Power", "Baseline"),
                ("Fight-start Power", "Start"),
                ("End Power", "End"),
            ):
                if overall and role == "Start":
                    continue
                value = _power(power, role)
                result[label] = value.value
                if value.value is None:
                    unavailable[
                        (
                            "Invalid "
                            if value.state == MetricState.INVALID_SOURCE_VALUE
                            else "Missing "
                        )
                        + {"Baseline": "baseline", "Start": "start", "End": "end"}[role]
                        + " power"
                    ].append(label)
        for reason, labels in unavailable.items():
            metric = (
                "Fight metrics"
                if reason in ("Missing start scan", "Missing end scan") and len(labels) > 1
                else ", ".join(labels)
            )
            issues.append(
                _issue(
                    period,
                    title,
                    result,
                    metric,
                    reason,
                    "Affected values are blank; available metrics remain valid.",
                )
            )
        state = pub["PlayerState" if kind == "player" else "AggregateState"]
        result["Data Status"] = (
            "; ".join((["Live — provisional"] if state == "live" else []) + list(unavailable))
            or "Available"
        )
        if terminal:
            for column in columns_for(kind, overall=overall):
                if column.kind == "number" and column.label != "Baseline Power":
                    result[column.label] = None
            result["Data Status"] = "Final unavailable"
            issues.append(
                _issue(
                    period,
                    title,
                    result,
                    "Fighting metrics",
                    "Final unavailable",
                    "This stream was finalized as unavailable; retained source values are audit-only.",
                )
            )
        output.append(result)
    authority = (
        "Player DKP uses this publication's frozen weights. Only T4+T5 KP counts."
        if kind == "player"
        else "Kingdom and camp figures use supplied reports, not player totals. DKP and T4+T5 KP retain source authority and resolution."
    )
    notes = [
        authority,
        "KP Loss = Healed Troops × 20. Tanking Score = T4+T5 KP / (KP Loss + Deads); healed troops must be positive.",
    ]
    if population is not None and not terminal:
        notes.append(
            f"DKP ranked population: {population}; baseline roster: {pub['EligibleCount']}. Ordinal ties use Governor ID; valid zeros are included."
        )
    availability = REASONS.get(
        pub["PlayerState" if kind == "player" else "AggregateState"], "Unavailable"
    )
    if empty_overall:
        availability = "Not applicable"
        notes.append("This Overall period has no fighting; no ranked rows are shown.")
    if not output:
        notes.append("No published rows are available for this report.")
    return _sheet(
        issues,
        key=key,
        title=title,
        period=period,
        purpose="Independent Overall report" if overall else "This fighting window only",
        availability=availability,
        columns=columns_for(kind, overall=overall),
        records=output,
        notes=notes,
    )


def build_reader_projection(inputs, *, history_snapshot, history_rows):
    """Pure Stage 3 boundary. Inputs include Stage 2 context and exact player powers.

    Callers authorise the guild/season and supply verified pinned history. All rows
    are consumed and hashes checked before a projection is returned. No writes.
    """
    from kvk.services.new_source_reader_support import build_support

    inputs = tuple(
        sorted(
            inputs,
            key=lambda item: (
                item[1]["metadata"]["configs"]["selected"]["WindowSeq"],
                item[0].period_id,
            ),
        )
    )
    history_rows = tuple(history_rows)
    audit = build_generation(inputs)
    if len({s.kvk_no for s, _ in inputs}) != 1:
        raise SourceConflict("Reader projection requires one authorised season.")
    if not isinstance(history_snapshot, HistorySnapshot) or (
        history_snapshot.source_key,
        history_snapshot.kvk_no,
        history_snapshot.version,
    ) != (SOURCE_KEY, inputs[0][0].kvk_no, HISTORY_VERSION):
        raise SourceConflict("Reader history belongs to another scope.")
    hasher = history_snapshot.hasher()
    for row in history_rows:
        hash_row(hasher, encode_fact(row))
    if (
        len(history_rows) != history_snapshot.row_count
        or hasher.digest() != history_snapshot.content_hash
    ):
        raise SourceConflict("Reader history content differs from its snapshot.")
    periods, sheets, issues = [], [], []
    for selection, snapshot in inputs:
        context, pub = snapshot["reader_context"], snapshot["envelope"]["publication"]
        if context["publication"] != pub or context["metadata"] != snapshot["metadata"]:
            raise SourceConflict("Reader context differs from the selected publication.")
        if any(
            context["revisions"][r] != pub[column]
            for r, column in (
                ("start", "StartRevisionID"),
                ("end", "EndRevisionID"),
                ("aggregate", "AggregateRevisionID"),
            )
        ):
            raise SourceConflict("Reader source revision differs from the publication.")
        config = context["metadata"]["configs"]["selected"]
        periods.append((selection, snapshot))
        if config["PeriodKind"] != "overall" and no_fight(config):
            continue
        sheets.extend(
            _entity_sheet(selection, snapshot, kind, issues)
            for kind in ("player", "kingdom", "camp")
        )
    overall_ids = {
        s.period_id
        for s, snap in periods
        if snap["metadata"]["configs"]["selected"]["PeriodKind"] == "overall"
    }
    if not overall_ids:
        for kind, suffix in (("player", "Players"), ("kingdom", "Kingdoms"), ("camp", "Camps")):
            sheets.append(
                _sheet(
                    issues,
                    key="overall:" + kind,
                    title="Overall " + suffix,
                    period="Overall",
                    purpose="Independent Overall report",
                    availability="Not published",
                    columns=columns_for(kind, overall=True),
                    records=[],
                    notes=(
                        "Overall has not been published. Fighting windows are not substituted or summed.",
                    ),
                )
            )
    # Stable configured order; title collisions are handled by logical keys, not guessed aliases.
    order = {
        s.period_id: snap["metadata"]["configs"]["selected"]["WindowSeq"] for s, snap in periods
    }
    sheets.sort(
        key=lambda s: (
            s.key.split(":")[0] in overall_ids or s.key.startswith("overall:"),
            order.get(s.key.split(":")[0], 0),
            s.key.split(":")[0],
            {"player": 0, "kingdom": 1, "camp": 2}[s.key.rsplit(":", 1)[1]],
        )
    )
    support = build_support(periods, sheets, issues, history_rows)
    return ReaderProjection(tuple(support[:1] + sheets + support[1:]), audit, history_snapshot)


def load_reader_projection(
    *, connect, intent_id, kvk_no, guild_id, expected_hash, with_checkpoints=False
):
    """Optional authorised entry point; no existing provider/delivery caller is changed."""
    from kvk.dal.new_source_delivery_dal import load_reader_export_inputs
    from kvk.dal.new_source_history_dal import iter_history
    from kvk.dal.new_source_report_context_dal import iter_player_powers

    _, history, periods = load_reader_export_inputs(
        connect=connect,
        intent_id=intent_id,
        kvk_no=kvk_no,
        guild_id=guild_id,
        expected_hash=expected_hash,
    )
    if (history.intent_id, history.kvk_no, history.guild_id, history.vector_hash) != (
        intent_id,
        kvk_no,
        guild_id,
        expected_hash,
    ):
        raise SourceConflict("Reader history differs from the authorised request.")
    inputs = [
        (
            selection,
            dict(
                snapshot,
                player_powers=tuple(
                    iter_player_powers(connect=connect, context=snapshot["reader_context"])
                ),
            ),
        )
        for selection, snapshot in periods
    ]
    builder = build_reader_projection
    if with_checkpoints:
        from kvk.services.new_source_checkpoint_service import build_checkpoint_projection

        builder = build_checkpoint_projection
    return builder(
        inputs,
        history_snapshot=history,
        history_rows=iter_history(connect=connect, snapshot=history),
    )
