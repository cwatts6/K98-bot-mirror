"""Explicit V2 consumer facade over one S3B publication snapshot.

Legacy callers never enter this facade implicitly. No cache, source activation,
calculation replay, SQL writes or publication selection occurs here.
"""

from datetime import UTC, datetime
from decimal import Decimal, localcontext
import json

from kvk.dal import kvk_admin_dal, new_source_reporting_dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.schemas.new_source_schema import SOURCE_KEY

BLOCK_KEYS = (
    "players_by_kills",
    "players_by_deads",
    "players_by_dkp",
    "kingdoms_by_kills",
    "kingdoms_by_deads",
    "kingdoms_by_dkp",
    "camps_by_kills",
    "camps_by_deads",
    "camps_by_dkp",
    "our_top_players",
    "our_kingdom",
    "our_camp",
)
FIELDS = {
    "deads": "dead",
    "dkp": "dkp",
    "kp_gain": "total_kill_points",
    "tier_kp": "kp_t4_t5",
    "healed_troops": "healed",
    "acclaim_gain": "acclaim",
}


def _utc(value):
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise SourceConflict("Invalid stored source timestamp.")
    # SQL datetime2 columns explicitly store UTC, not local or upload time.
    return (
        value.replace(tzinfo=UTC).isoformat()
        if value.tzinfo is None
        else value.astimezone(UTC).isoformat()
    )


def _number(value):
    if value is None:
        return None
    if type(value) not in (int, Decimal) or not Decimal(value).is_finite():
        raise SourceConflict("Source metrics require exact finite numbers.")
    return Decimal(value)


def _row(raw, *, aggregate=False):
    states = {} if aggregate else json.loads(raw["FieldStatusJson"])
    row = {
        "governor_id": raw.get("GovernorID"),
        "name": raw.get("name"),
        "kingdom": raw.get("Kingdom") if aggregate else raw["b0_kingdom"],
        "camp_id": raw["CampID"],
        "camp_name": raw.get("CampLabel"),
        "states": {},
        "reported": {},
    }
    for target, source in FIELDS.items():
        state = (
            ("unsupported" if source == "total_kill_points" else "available")
            if aggregate
            else states[source]
        )
        value = None if state != "available" else _number(raw.get(source))
        if (state == "available") != (value is not None):
            raise SourceConflict("Metric value and availability disagree.")
        row[target] = value
        row["states"][target] = state
        if aggregate and state == "available":
            row["reported"][target] = {
                "raw": raw[source + "_raw"],
                "unit": _number(raw[source + "_unit"]),
                "precision": raw[source + "_precision"],
            }
    tier_states = ["available" if aggregate else states[k] for k in ("t4_kills", "t5_kills")]
    row["states"]["kills_gain"] = next((s for s in tier_states if s != "available"), "available")
    with localcontext() as context:
        context.prec = 100
        row["kills_gain"] = (
            _number(raw["t4_kills"]) + _number(raw["t5_kills"])
            if all(s == "available" for s in tier_states)
            else None
        )
    if aggregate:
        row["reported"]["kills_gain"] = {
            "raw": f"{raw['t4_kills_raw']} + {raw['t5_kills_raw']}",
            "precision": "reported_tier_sum",
            "units": (raw["t4_kills_unit"], raw["t5_kills_unit"]),
        }
    return row


def _ranked(rows, metric, identity, *, no_fight=False):
    usable = [r for r in rows if r[metric] is not None]
    ordered = sorted(usable, key=lambda r: (r[metric].copy_negate(), r[identity]))
    # No-fight scores remain visible, but there is no combat competition/rank.
    return [
        dict(r, rank=None if no_fight else i, population=None if no_fight else len(ordered))
        for i, r in enumerate(ordered, 1)
    ]


def load_report_v2(
    *, connect, kvk_no, period_id, our_kingdom, publication_id=None, snapshot_loader=None
):
    """Load one requested period; a pinned preview fails closed after reselection.

    A changed selection requires a new preview session, never silent retargeting.
    Missing publications return a V2 unavailable envelope, never legacy data.
    """
    if type(kvk_no) is not int or not 1 <= kvk_no <= 2147483647 or not period_id:
        raise ValueError("Explicit source season and period are required.")
    loader = snapshot_loader or new_source_reporting_dal.load_snapshot
    envelope = loader(connect=connect, kvk_no=kvk_no, period_id=period_id)
    if (
        envelope["source_key"] != SOURCE_KEY
        or envelope["kvk_no"] != kvk_no
        or str(envelope["period_id"]) != str(period_id)
    ):
        raise SourceConflict("Source snapshot scope mismatch.")
    publication = envelope.get("publication")
    if publication_id is not None and (
        not publication or str(publication["PublicationID"]) != str(publication_id)
    ):
        raise SourceConflict(
            "Preview publication changed; retain this session and create a new one."
        )
    report = dict(
        schema_version=2,
        source_key=SOURCE_KEY,
        kvk_no=kvk_no,
        period_id=str(period_id),
        publication_id=None,
        is_current=False,
        current_period_state="not_received",
        player_state="not_received",
        aggregate_state="not_received",
        blocks={k: [] for k in BLOCK_KEYS},
    )
    if not publication:
        return report
    meta = kvk_admin_dal.fetch_source_report_metadata(connect, envelope)
    selected, requested = meta["configs"]["selected"], meta["configs"]["requested"]
    for config in (selected, requested):
        if (
            config["SourceKey"] != SOURCE_KEY
            or config["KVK_NO"] != kvk_no
            or config["PeriodKey"] != publication["PeriodKey"]
        ):
            raise SourceConflict("Source configuration scope mismatch.")
    no_fight = (
        selected["StartScanID"] is not None and selected["StartScanID"] == selected["EndScanID"]
    )
    report.update(
        publication_id=str(publication["PublicationID"]),
        generation=publication["Generation"],
        selection_version=envelope["selection"]["SelectionVersion"],
        period_key=publication["PeriodKey"],
        period_kind=selected["PeriodKind"],
        period_label=selected["WindowName"],
        requested_config_id=str(envelope["desired_config_id"]),
        selected_config_id=str(publication["ConfigVersionID"]),
        requested_start_scan_id=requested["StartScanID"],
        requested_end_scan_id=requested["EndScanID"],
        selected_start_scan_id=publication["StartScanID"],
        selected_end_scan_id=publication["EndScanID"],
        is_current=envelope["is_current"],
        current_period_state=envelope["current_period_state"],
        selected_period_state=publication["PeriodState"],
        player_state=publication["PlayerState"],
        aggregate_state=publication["AggregateState"],
        eligible_count=publication["EligibleCount"],
        roster_id=str(publication["RosterID"]),
        calculation_version=publication["CalculationVersion"],
        endpoint_pending=not envelope["is_current"]
        or publication["EndScanID"] != requested["EndScanID"]
        or requested["EndScanID"] is None,
        player_start_utc=_utc((meta["endpoints"]["start"] or {}).get("ScanStartUTC")),
        player_end_utc=_utc((meta["endpoints"]["end"] or {}).get("ScanStartUTC")),
        aggregate_coverage_start_utc=_utc((meta["aggregate"] or {}).get("CoverageStartUTC")),
        aggregate_coverage_end_utc=_utc((meta["aggregate"] or {}).get("CoverageEndUTC")),
        aggregate_as_of_utc=_utc((meta["aggregate"] or {}).get("AsOfUTC")),
        aggregate_revision_id=(
            str(publication["AggregateRevisionID"]) if publication["AggregateRevisionID"] else None
        ),
        final_unavailable_reason=publication.get("FinalUnavailableReason"),
    )
    if no_fight and (
        publication["AggregateRevisionID"] or publication["AggregateState"] != "not_applicable"
    ):
        raise SourceConflict("No-fight aggregates are not applicable.")
    players = [_row(r) for r in envelope["players"]]
    kingdoms = [_row(r, aggregate=True) for r in envelope["aggregates"]["SourceKingdomReportRow"]]
    camps = [_row(r, aggregate=True) for r in envelope["aggregates"]["SourceCampReportRow"]]
    mapping = {r["Kingdom"]: r for r in meta["camps"]}
    for player in players:
        player["camp_name"] = mapping[player["kingdom"]]["CampName"]
    blocks = report["blocks"]
    for family, rows, identity in (
        ("players", players, "governor_id"),
        ("kingdoms", kingdoms, "kingdom"),
        ("camps", camps, "camp_id"),
    ):
        for suffix, metric in (("kills", "kills_gain"), ("deads", "deads"), ("dkp", "dkp")):
            blocks[f"{family}_by_{suffix}"] = _ranked(rows, metric, identity, no_fight=no_fight)
    blocks["our_top_players"] = _ranked(
        [p for p in players if p["kingdom"] == our_kingdom],
        "kills_gain",
        "governor_id",
        no_fight=no_fight,
    )
    blocks["our_kingdom"] = [r for r in kingdoms if r["kingdom"] == our_kingdom]
    our_camp = mapping.get(our_kingdom, {}).get("CampID")
    blocks["our_camp"] = [r for r in camps if r["camp_id"] == our_camp]
    report["players"] = players  # Includes unavailable B0 members, independent of leaderboards.
    report["overall_ranks"] = (
        {}
        if no_fight
        else {
            r["governor_id"]: (r["rank"], r["population"])
            for r in _ranked(players, "tier_kp", "governor_id")
        }
    )
    return report


def card_context(report, governor_id):
    """Whole-KVK context only; the independent KS4 numerator is never read here."""
    if report.get("schema_version") != 2 or report.get("period_kind") != "overall":
        raise ValueError("Card context requires an explicit V2 overall report.")
    rank = report.get("overall_ranks", {}).get(int(governor_id))
    if not report["is_current"] or rank is None:
        return {"source_context": {"available": False, "source_key": SOURCE_KEY}}
    return {
        "source_context": {
            "available": True,
            "source_key": SOURCE_KEY,
            "period": "overall",
            "publication_id": report["publication_id"],
            "rank": rank[0],
            "population": rank[1],
            "basis": "T4/T5 KP; usable frozen B0 cohort",
            "as_of_utc": report["player_end_utc"],
            "start_utc": report["player_start_utc"],
            "state": report["player_state"],
        }
    }
