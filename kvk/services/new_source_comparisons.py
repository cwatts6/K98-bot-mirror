"""One metric per comparison, with independent fight and Overall columns."""

from collections import Counter
from decimal import Decimal

from kvk.models.new_source_reader import ReaderColumn, ReaderLink
from kvk.services.new_source_cumulative import KINDS
from kvk.services.new_source_reader_service import _sheet

COMPARISON_METRICS = (
    ("DKP", "DKP"),
    ("T4+T5 KP", "T4+T5 KP"),
    ("T4+T5 Kills", "T4 + T5 Kills"),
    ("T4 Kills", "T4 Kills"),
    ("T5 Kills", "T5 Kills"),
    ("Deads", "Deads"),
    ("KP Loss", "KP Loss"),
    ("Tanking Score", "Tanking Score (%)"),
    ("Healed Troops", "Healed Troops"),
)


def comparison_sheets(members, overall_id, facts, issues, report_keys, *, unavailable=()):
    active = [m for m in members if m.status != "no_fight"]
    names = Counter(m.name for m in active)
    reserved = {"Overall", "Data Notes", "Governor ID", "Player Name", "Kingdom", "Camp"}
    labels, used = [], set(reserved)
    for m in active:
        label = (
            m.name if names[m.name] == 1 and m.name not in used else f"{m.name} (fight {m.order})"
        )
        while label in used:
            label += " · fight"
        used.add(label)
        labels.append(label)
    periods = [(m.period_id, label) for m, label in zip(active, labels, strict=True)] + [
        (overall_id, "Overall")
    ]
    output = []
    for kind, plural in KINDS.items():
        identity_labels = {
            "player": ("Governor ID", "Player Name", "Kingdom", "Camp"),
            "kingdom": ("Kingdom", "Camp"),
            "camp": ("Camp",),
        }[kind]
        tables = [facts.get((pid, kind), {}) for pid, _ in periods]
        identities = sorted(set().union(*(set(t) for t in tables)))
        for title, metric in COMPARISON_METRICS:
            if metric == "DKP" and kind == "player":
                metric = "Player DKP"
            records, links = [], []
            for identity in identities:
                latest = next(t[identity] for t in reversed(tables) if identity in t)
                row = {label: latest.get(label) for label in identity_labels}
                missing = []
                for (pid, label), table in zip(periods, tables, strict=True):
                    terminal = (pid, kind) in unavailable
                    row[label] = None if terminal else table.get(identity, {}).get(metric)
                    if row[label] is None:
                        missing.append(
                            label + (": final unavailable" if terminal else ": unavailable")
                        )
                    if "Live" in (table.get(identity, {}).get("Data Status") or ""):
                        missing.append(label + ": Live — provisional")
                row["Data Notes"] = "; ".join(missing)
                records.append(row)
            # Newest fight is the common comparison basis, independent of Overall availability.
            sort_label = labels[-1] if labels else "Overall"
            records.sort(
                key=lambda r: (
                    r[sort_label] is not None,
                    r[sort_label] if r[sort_label] is not None else Decimal(0),
                ),
                reverse=True,
            )
            for i, row in enumerate(records):
                for j, (pid, label) in enumerate(periods, len(identity_labels)):
                    target = str(pid) + ":" + kind
                    if target in report_keys:
                        links.append(ReaderLink(i, j, target))
            fmt = "0.00%" if metric == "Tanking Score (%)" else "#,##0.######"
            columns = (
                tuple(ReaderColumn(label) for label in identity_labels)
                + tuple(ReaderColumn(label, "number", fmt) for _, label in periods)
                + (ReaderColumn("Data Notes"),)
            )
            output.append(
                _sheet(
                    issues,
                    key=f"comparison:{kind}:{title}",
                    title=plural + " " + title,
                    period="Fights and Overall",
                    purpose="Compare this metric across individual fights",
                    availability="Available",
                    columns=columns,
                    records=records,
                    links=links,
                    notes=(
                        "One column per occurring or expected fight. Overall is independently published; it is never a sum of fights.",
                        "Missing values remain blank. Rows sort by the latest fight, then stable entity ID. No-fight windows are omitted; see Scans.",
                    ),
                )
            )
    return output
