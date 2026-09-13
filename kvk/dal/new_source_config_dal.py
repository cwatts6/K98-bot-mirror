"""Caller-owned endpoint snapshots. Never commits or rolls back the caller cursor."""

from datetime import datetime
from decimal import Decimal
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, canonical, digest, lock_scope, one, rows
from kvk.models.new_source_reporting import require_utc
from kvk.schemas.new_source_schema import INT_MAX, SOURCE_KEY

UNCHANGED_START = object()


def locked_period(cursor, kvk_no, period_id):
    lock_scope(cursor, kvk_no)
    # All writers take the same season mutex before the documented row lock order.
    cursor.execute("SELECT * FROM KVK.SourceRouting WITH (UPDLOCK,HOLDLOCK) WHERE KVK_NO=?", kvk_no)
    routing = one(cursor)
    cursor.execute(
        "SELECT * FROM KVK.SourceSelection WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
        SOURCE_KEY,
        kvk_no,
    )
    selections = rows(cursor)
    selection = next((r for r in selections if str(r["PeriodID"]) == str(period_id)), None)
    cursor.execute(
        "SELECT * FROM KVK.SourceCompleteSelection WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? ORDER BY PeriodID",
        SOURCE_KEY,
        kvk_no,
    )
    cursor.fetchall()
    cursor.execute(
        "SELECT r.*,c.ConfigVersion FROM KVK.SourceConfigRequest r WITH (UPDLOCK,HOLDLOCK) JOIN KVK.SourceConfigVersion c ON c.ConfigVersionID=r.DesiredConfigVersionID WHERE r.SourceKey=? AND r.KVK_NO=? AND r.PeriodID=? AND r.RequestState<>'rejected' ORDER BY c.ConfigVersion DESC",
        SOURCE_KEY,
        kvk_no,
        period_id,
    )
    requests = rows(cursor)
    return routing, selection, requests


def desired_config(cursor, selection, requests):
    if selection:
        cursor.execute(
            "SELECT p.ConfigVersionID,c.ConfigVersion FROM KVK.SourcePublication p JOIN KVK.SourceConfigVersion c ON c.ConfigVersionID=p.ConfigVersionID WHERE p.PublicationID=?",
            selection["PublicationID"],
        )
        selected = one(cursor)
        if not requests or selected["ConfigVersion"] > requests[0]["ConfigVersion"]:
            return str(selected["ConfigVersionID"])
    if requests:
        return str(requests[0]["DesiredConfigVersionID"])
    return None


def snapshot_endpoint_request(
    cursor,
    *,
    kvk_no: int,
    period_id: str,
    base_config_id: str,
    new_end_scan_id: int | None,
    actor: str,
    reason: str,
    requested_utc: datetime,
    origin: str,
    provenance: dict,
    new_start_scan_id=UNCHANGED_START,
    reviewed_configuration=None,
    review_id=None,
):
    require_utc(requested_utc)
    if (
        origin not in ("authorized_import", "admin", "system")
        or not actor.strip()
        or len(actor) > 128
        or not reason.strip()
        or len(reason) > 1024
    ):
        raise ValueError("Authorized endpoint provenance is required.")
    if new_end_scan_id is not None and (
        type(new_end_scan_id) is not int or not 1 <= new_end_scan_id <= INT_MAX
    ):
        raise ValueError("Invalid desired endpoint.")
    cursor.execute("SELECT @@TRANCOUNT")
    if cursor.fetchone()[0] < 1:
        raise ValueError("Endpoint requests require the caller's active transaction.")
    _, selection, requests = locked_period(cursor, kvk_no, period_id)
    from kvk.dal.season_source_dal import require_source

    require_source(cursor, kvk_no, SOURCE_KEY)
    if reviewed_configuration is not None:
        cursor.execute(
            "SELECT PayloadJson,ActorID,ReviewKind,ReviewState FROM KVK.SourceAdminReview WHERE ReviewID=? AND KVK_NO=?",
            review_id,
            kvk_no,
        )
        review = one(cursor)
        if (
            not review
            or review["ActorID"] != actor
            or review["ReviewKind"] != "configuration"
            or review["ReviewState"] != "pending"
            or json.loads(review["PayloadJson"]).get("snapshot") != reviewed_configuration
        ):
            raise SourceConflict(
                "Configuration correction requires its exact pending admin review."
            )
    cursor.execute(
        "SELECT c.*,w.StartScanID,w.EndScanID,p.PeriodKind,p.PeriodKey FROM KVK.SourceConfigVersion c JOIN KVK.SourceWindowConfig w ON w.ConfigVersionID=c.ConfigVersionID JOIN KVK.SourcePeriod p ON p.SourceKey=w.SourceKey AND p.KVK_NO=w.KVK_NO AND p.PeriodKey=w.PeriodKey WHERE c.SourceKey=? AND c.KVK_NO=? AND c.ConfigVersionID=? AND p.PeriodID=?",
        SOURCE_KEY,
        kvk_no,
        base_config_id,
        period_id,
    )
    base = one(cursor)
    if not base:
        raise SourceConflict("Missing approved base configuration.")
    old_start = base["StartScanID"]
    start = old_start if new_start_scan_id is UNCHANGED_START else new_start_scan_id
    if start is not None and (type(start) is not int or not 1 <= start <= INT_MAX):
        raise ValueError("Invalid desired start endpoint.")
    if new_end_scan_id is not None and start is not None:
        if new_end_scan_id < start:
            raise SourceConflict("EndScanID must be greater than or equal to StartScanID.")
    if base["PeriodKind"] == "no_fight" and start != new_end_scan_id:
        raise SourceConflict("Baseline no-fight endpoints must remain identical.")
    # The transition hash includes the base: 13 -> 14 -> 13 is a distinct request.
    content = {"base": base_config_id, "period": period_id, "start": start, "end": new_end_scan_id}
    if reviewed_configuration is not None:
        content["configuration"] = reviewed_configuration
    content_hash = digest(content)
    cursor.execute(
        "SELECT * FROM KVK.SourceConfigRequest WHERE SourceKey=? AND KVK_NO=? AND PeriodID=? AND BaseConfigVersionID=? AND ConfigContentHash=?",
        SOURCE_KEY,
        kvk_no,
        period_id,
        base_config_id,
        content_hash,
    )
    existing = one(cursor)
    if existing:
        return existing
    current = desired_config(cursor, selection, requests)
    if current is not None and current != base_config_id:
        raise SourceConflict("Endpoint request base is stale.")
    if (
        base["EndScanID"] == new_end_scan_id
        and old_start == start
        and reviewed_configuration is None
    ):
        return None
    if start is not None and new_end_scan_id is not None:
        cursor.execute(
            "SELECT LogicalScanID,ScanStartUTC FROM KVK.SourceLogicalScan s JOIN KVK.SourceObservation o ON o.ObservationID=s.ObservationID WHERE s.SourceKey=? AND s.KVK_NO=? AND s.LogicalScanID IN (?,?)",
            SOURCE_KEY,
            kvk_no,
            start,
            new_end_scan_id,
        )
        times = {r["LogicalScanID"]: r["ScanStartUTC"] for r in rows(cursor)}
        if (
            start in times
            and new_end_scan_id in times
            and start != new_end_scan_id
            and times[new_end_scan_id] <= times[start]
        ):
            raise SourceConflict("Endpoint event UTC must increase.")
    config_id, request_id = str(uuid4()), str(uuid4())
    roster_id = base["RosterID"]
    if reviewed_configuration is not None:
        roster_id = _configuration_roster(
            cursor, base, reviewed_configuration, actor, reason, requested_utc
        )
    cursor.execute(
        "SELECT ISNULL(MAX(ConfigVersion),0)+1 AS n FROM KVK.SourceConfigVersion WITH (UPDLOCK,HOLDLOCK) WHERE SourceKey=? AND KVK_NO=?",
        SOURCE_KEY,
        kvk_no,
    )
    number = one(cursor)["n"]
    utc = requested_utc.replace(tzinfo=None)
    cursor.execute(
        "INSERT KVK.SourceConfigVersion (ConfigVersionID,SourceKey,KVK_NO,ConfigVersion,RosterID,ConfigContentHash,WindowDigest,MappingDigest,WeightDigest,ApprovedUTC,ApprovedBy,Reason,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        config_id,
        SOURCE_KEY,
        kvk_no,
        number,
        roster_id,
        content_hash,
        digest(
            {
                "prior": bytes(base["WindowDigest"]).hex(),
                "period": period_id,
                "start": start,
                "end": new_end_scan_id,
            }
        ),
        (
            digest({"entries": reviewed_configuration["mapping"]})
            if reviewed_configuration is not None
            else base["MappingDigest"]
        ),
        (
            digest([*reviewed_configuration["weights"], reviewed_configuration["effective"]])
            if reviewed_configuration is not None
            else base["WeightDigest"]
        ),
        utc,
        actor,
        reason,
        canonical(provenance),
    )
    cursor.execute(
        "INSERT KVK.SourceWindowConfig (ConfigVersionID,SourceKey,KVK_NO,WindowName,WindowSeq,StartScanID,EndScanID,Notes,UpdatedAtUTC,PeriodKey) SELECT ?,SourceKey,KVK_NO,WindowName,WindowSeq,CASE WHEN PeriodKey=? THEN ? ELSE StartScanID END,CASE WHEN PeriodKey=? THEN ? ELSE EndScanID END,Notes,?,PeriodKey FROM KVK.SourceWindowConfig WHERE ConfigVersionID=?",
        config_id,
        base["PeriodKey"],
        start,
        base["PeriodKey"],
        new_end_scan_id,
        utc,
        base_config_id,
    )
    cursor.execute(
        "INSERT KVK.SourceCampConfig (ConfigVersionID,SourceKey,KVK_NO,Kingdom,CampID,CampName,CampKey) SELECT ?,SourceKey,KVK_NO,Kingdom,CampID,CampName,CampKey FROM KVK.SourceCampConfig WHERE ConfigVersionID=?",
        config_id,
        base_config_id,
    )
    cursor.execute(
        "INSERT KVK.SourceWeightConfig (ConfigVersionID,SourceKey,KVK_NO,WeightT4X,WeightT5Y,WeightDeadsZ,WeightT4XSource,WeightT5YSource,WeightDeadsZSource,EffectiveFromUTC) SELECT ?,SourceKey,KVK_NO,WeightT4X,WeightT5Y,WeightDeadsZ,WeightT4XSource,WeightT5YSource,WeightDeadsZSource,EffectiveFromUTC FROM KVK.SourceWeightConfig WHERE ConfigVersionID=?",
        config_id,
        base_config_id,
    )
    cursor.execute(
        "INSERT KVK.SourceScanBinding (ConfigVersionID,SourceKey,KVK_NO,LogicalScanID) SELECT ?,SourceKey,KVK_NO,LogicalScanID FROM KVK.SourceScanBinding WHERE ConfigVersionID=?",
        config_id,
        base_config_id,
    )
    if reviewed_configuration is not None:
        # These rows belong to the newly allocated, uncommitted version only.
        cursor.execute("DELETE FROM KVK.SourceCampConfig WHERE ConfigVersionID=?", config_id)
        cursor.execute("DELETE FROM KVK.SourceWeightConfig WHERE ConfigVersionID=?", config_id)
        for kingdom, camp, name in reviewed_configuration["mapping"]:
            cursor.execute(
                "INSERT KVK.SourceCampConfig (ConfigVersionID,SourceKey,KVK_NO,Kingdom,CampID,CampName,CampKey) VALUES (?,?,?,?,?,?,?)",
                config_id,
                SOURCE_KEY,
                kvk_no,
                kingdom,
                camp,
                name,
                " ".join(name.split()).casefold(),
            )
        x, y, z = reviewed_configuration["weights"]
        cursor.execute(
            "INSERT KVK.SourceWeightConfig (ConfigVersionID,SourceKey,KVK_NO,WeightT4X,WeightT5Y,WeightDeadsZ,WeightT4XSource,WeightT5YSource,WeightDeadsZSource,EffectiveFromUTC) VALUES (?,?,?,?,?,?,?,?,?,?)",
            config_id,
            SOURCE_KEY,
            kvk_no,
            Decimal(x),
            Decimal(y),
            Decimal(z),
            x,
            y,
            z,
            datetime.fromisoformat(reviewed_configuration["effective"]).replace(tzinfo=None),
        )
    cursor.execute(
        "INSERT KVK.SourceConfigRequest (RequestID,SourceKey,KVK_NO,PeriodID,PeriodKey,BaseConfigVersionID,DesiredConfigVersionID,ConfigContentHash,OldStartScanID,OldEndScanID,NewStartScanID,NewEndScanID,Origin,Actor,RequestedUTC,RequestState,Reason,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)",
        request_id,
        SOURCE_KEY,
        kvk_no,
        period_id,
        base["PeriodKey"],
        base_config_id,
        config_id,
        content_hash,
        old_start,
        base["EndScanID"],
        start,
        new_end_scan_id,
        origin,
        actor,
        utc,
        reason,
        canonical(provenance),
    )
    cursor.execute("SELECT * FROM KVK.SourceConfigRequest WHERE RequestID=?", request_id)
    return one(cursor)


def _configuration_roster(cursor, base, snapshot, actor, reason, utc):
    """A scope correction can only select membership present in the original B0."""
    cursor.execute("SELECT B0RevisionID FROM KVK.SourceRoster WHERE RosterID=?", base["RosterID"])
    b0 = one(cursor)["B0RevisionID"]
    cursor.execute(
        "SELECT GovernorID,kingdom,power FROM KVK.SourcePlayerSnapshot WHERE RevisionID=? ORDER BY GovernorID",
        b0,
    )
    original = rows(cursor)
    scope = {k for k, _, _ in snapshot["mapping"]}
    cursor.execute("SELECT MetadataJson FROM KVK.SourceObservationRevision WHERE RevisionID=?", b0)
    baseline_scope = set(json.loads(one(cursor)["MetadataJson"])["scope"]["kingdoms"])
    if not scope.issubset(baseline_scope):
        raise SourceConflict("The corrected kingdom scope lacks original B0 evidence.")
    members = [r for r in original if r["kingdom"] in scope]
    if not members:
        raise SourceConflict("Corrected roster cannot be empty.")
    cursor.execute(
        "SELECT GovernorID,b0_kingdom FROM KVK.SourceRosterMember WHERE RosterID=? ORDER BY GovernorID",
        base["RosterID"],
    )
    current = [(r["GovernorID"], r["b0_kingdom"]) for r in rows(cursor)]
    if current == [(r["GovernorID"], r["kingdom"]) for r in members]:
        return base["RosterID"]
    roster = str(uuid4())
    cursor.execute(
        "SELECT ISNULL(MAX(RosterVersion),0)+1 AS n FROM KVK.SourceRoster WHERE SourceKey=? AND KVK_NO=?",
        SOURCE_KEY,
        base["KVK_NO"],
    )
    version = one(cursor)["n"]
    cursor.execute(
        "INSERT KVK.SourceRoster (RosterID,SourceKey,KVK_NO,RosterVersion,B0RevisionID,ScopeDigest,MemberDigest,MemberCount,ApprovedUTC,ApprovedBy,Reason,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        roster,
        SOURCE_KEY,
        base["KVK_NO"],
        version,
        b0,
        digest(snapshot["mapping"]),
        digest(members),
        len(members),
        utc.replace(tzinfo=None),
        actor,
        reason,
        canonical({"base_roster": base["RosterID"], "original_b0": b0}),
    )
    for member in members:
        cursor.execute(
            "INSERT KVK.SourceRosterMember (RosterID,SourceKey,KVK_NO,GovernorID,b0_kingdom,b0_power) VALUES (?,?,?,?,?,?)",
            roster,
            SOURCE_KEY,
            base["KVK_NO"],
            member["GovernorID"],
            member["kingdom"],
            member["power"],
        )
    return roster
