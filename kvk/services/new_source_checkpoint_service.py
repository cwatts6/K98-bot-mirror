"""Stage 4 logical season reports and immutable window/cumulative output manifests."""

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.new_source_checkpoints import FightCheckpoint
from kvk.models.new_source_reader import ReaderProjection
from kvk.services.new_source_comparisons import comparison_sheets
from kvk.services.new_source_cumulative import (
    KINDS,
    cumulative_sheet,
    entity_records,
    exact_records,
    members_for,
    no_fight,
)
from kvk.services.new_source_reader_service import build_reader_projection
from kvk.services.new_source_reader_support import build_support


def build_checkpoint_projection(inputs, *, history_snapshot, history_rows):
    inputs, history_rows = tuple(inputs), tuple(history_rows)
    base = build_reader_projection(
        inputs, history_snapshot=history_snapshot, history_rows=history_rows
    )
    by_period = {s.period_id: (s, snap) for s, snap in inputs}
    ordered = sorted(
        inputs, key=lambda p: (p[1]["metadata"]["configs"]["selected"]["WindowSeq"], p[0].period_id)
    )
    reports = {s.key: s for s in base.sheets if s.key.rsplit(":", 1)[-1] in KINDS}
    facts = {}
    for selection, snapshot in inputs:
        for kind in KINDS:
            key = selection.period_id + ":" + kind
            if key in reports:
                facts[selection.period_id, kind] = entity_records(snapshot, reports[key], kind)
    issues = exact_records(next(s for s in base.sheets if s.key == "issues"))
    output, checkpoints, latest_members = [], [], ()
    overall_ids = []
    for selection, snapshot in ordered:
        config = snapshot["metadata"]["configs"]["selected"]
        if config["PeriodKind"] == "overall":
            overall_ids.append(selection.period_id)
            continue
        members = members_for(selection, snapshot, by_period)
        latest_members = members
        if no_fight(config):
            continue
        own = tuple(selection.period_id + ":" + k for k in KINDS)
        output.extend(reports[k] for k in own)
        cumulative = (
            tuple(selection.period_id + ":cumulative:" + k for k in KINDS)
            if sum(m.status != "no_fight" for m in members) > 1
            else ()
        )
        checkpoint = FightCheckpoint(
            selection.period_id, config["WindowName"], members, own + cumulative
        )
        if cumulative:
            output.extend(cumulative_sheet(checkpoint, k, by_period, facts, issues) for k in KINDS)
        checkpoints.append(checkpoint)
    if len(overall_ids) > 1:
        raise SourceConflict("Only one independently selected Overall period is supported.")
    # An Overall-only export still exposes configured expected fights in comparisons.
    if not latest_members and ordered:
        selection, snap = ordered[-1]
        windows = [w for w in snap["reader_context"]["windows"] if w["PeriodKind"] == "fight"]
        if windows:
            from kvk.models.new_source_checkpoints import FightMember

            latest_members = tuple(
                FightMember(
                    w["PeriodID"],
                    w["WindowName"],
                    w["WindowSeq"],
                    w["StartScanID"],
                    w["EndScanID"],
                    "no_fight" if no_fight(w) else "missing",
                )
                for w in sorted(windows, key=lambda w: w["WindowSeq"])
            )
    overall = overall_ids[0] if overall_ids else "overall"
    output.extend(reports[overall + ":" + kind] for kind in KINDS)
    output.extend(comparison_sheets(latest_members, overall, facts, issues, set(reports)))
    support = build_support(ordered, output, issues, history_rows, checkpoints=tuple(checkpoints))
    return ReaderProjection(
        tuple(support[:1] + output + support[1:]),
        base.audit,
        base.history,
        version="snapshot_report_reader_v2",
        checkpoints=tuple(checkpoints),
    )
