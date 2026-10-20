"""Atomic, scoped approvals for explicitly selected historical exports."""

import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.export_coordination_dal import identity
from services.historical_import_recovery_service import ACTION
from services.recovery_backlog_dal import RecoveryBacklogDAL, group_reason
from services.recovery_dal import document


class HistoricalRetirementGroupDAL(RecoveryBacklogDAL):
    def __init__(self, store):
        super().__init__(store, group_kind="historical_batch")

    @staticmethod
    def selection_key(preview, members, actor):
        return digest(
            dict(
                actor=actor,
                configuration=preview["configuration"],
                members=sorted(members, key=lambda m: m["id"]),
            )
        ).hex()

    def _lock(self, cursor):
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',"
            "@LockOwner='Transaction',@LockTimeout=3000; SELECT @r AS Result",
            "k98-historical-group:" + self.store.scope,
        )
        if one(cursor)["Result"] < 0:
            raise SourceConflict(
                "Another historical approval is still being saved. Retry this confirmation to check its progress."
            )

    def _existing(self, cursor, preview, members, actor):
        selection_key = self.selection_key(preview, members, actor)
        cursor.execute(
            "SELECT IncidentID FROM dbo.RecoveryIncident WHERE ScopeKey=? "
            "AND SourceKind='historical_batch' "
            "AND JSON_VALUE(EvidenceJson,'$.selection_key')=?",
            self.store.scope,
            selection_key,
        )
        found = rows(cursor)
        if len(found) > 1:
            raise SourceConflict("The saved group approval is ambiguous; retain it for review.")
        if found:
            return identity(found[0]["IncidentID"])
        return self._legacy_approval(cursor, preview, members, actor)

    def _legacy_approval(self, cursor, preview, members, actor):
        # Old groups have no digest. Locate by an exact original member action,
        # then prove the entire saved selection and every action's author.
        first = members[0]
        cursor.execute(
            "SELECT TOP (2) i.IncidentID,i.EvidenceJson FROM dbo.RecoveryIncident i "
            "JOIN dbo.RecoveryAction a ON a.Reason='Historical group '+"
            "CONVERT(nvarchar(36),i.IncidentID)+': admin retired selected obsolete exports; SQL outcome unproven' "
            "WHERE i.ScopeKey=? AND i.SourceKind='historical_batch' "
            "AND JSON_VALUE(i.EvidenceJson,'$.selection_key') IS NULL "
            "AND a.IncidentID=? AND a.IncidentRevision=? AND a.EvidenceHash=? "
            "AND a.ActionKind=? AND a.Actor=?",
            self.store.scope,
            first["id"],
            first["revision"],
            first["token"],
            ACTION,
            actor,
        )
        candidates = rows(cursor)
        if len(candidates) > 1:
            raise SourceConflict("The saved group approval is ambiguous; retain it for review.")
        for candidate in candidates:
            group = identity(candidate["IncidentID"])
            evidence = json.loads(candidate["EvidenceJson"])
            if (
                evidence.get("group_id") != group
                or evidence.get("approved_count") != len(members)
                or evidence.get("configuration") != preview["configuration"]
                or sorted(evidence.get("members", []), key=lambda m: m["id"])
                != sorted(members, key=lambda m: m["id"])
            ):
                continue
            cursor.execute(
                "SELECT a.IncidentID,a.IncidentRevision,a.EvidenceHash,a.Actor,a.ActionKind "
                "FROM dbo.RecoveryAction a JOIN dbo.RecoveryIncident i ON i.IncidentID=a.IncidentID "
                "WHERE i.ScopeKey=? AND i.SourceKind='stats_import' AND a.Reason=?",
                self.store.scope,
                group_reason(group, self.group_kind),
            )
            actions = rows(cursor)
            expected = {(m["id"], m["revision"], m["token"], actor, ACTION) for m in members}
            observed = {
                (
                    identity(a["IncidentID"]),
                    a["IncidentRevision"],
                    a["EvidenceHash"],
                    a["Actor"],
                    a["ActionKind"],
                )
                for a in actions
            }
            if len(actions) == len(members) and observed == expected:
                return group
        return None

    def existing_approval(self, preview, members, actor):
        with transaction(self.store.connect) as cursor:
            self._lock(cursor)
            return self._existing(cursor, preview, members, actor)

    def candidates(self, after=None):
        with transaction(self.store.connect) as cursor:
            boundary = self.store._get(cursor, after) if after else None
            cursor.execute(
                "SELECT TOP (25) i.IncidentID FROM dbo.RecoveryIncident i WHERE i.ScopeKey=? "
                "AND i.SourceKind='stats_import' AND i.State='open' "
                "AND JSON_VALUE(i.EvidenceJson,'$.actions.retire_historical_export.label') IS NOT NULL "
                "AND NOT EXISTS(SELECT 1 FROM dbo.RecoveryAction a WHERE a.IncidentID=i.IncidentID "
                "AND (a.State IN ('dispatched','unknown') OR a.IncidentRevision=i.Revision)) "
                + (
                    "AND (i.FirstSeenUTC>? OR (i.FirstSeenUTC=? AND i.IncidentID>CAST(? AS uniqueidentifier))) "
                    if boundary
                    else ""
                )
                + "ORDER BY i.FirstSeenUTC,i.IncidentID",
                self.store.scope,
                *(
                    (boundary["FirstSeenUTC"], boundary["FirstSeenUTC"], boundary["IncidentID"])
                    if boundary
                    else ()
                ),
            )
            return [identity(r["IncidentID"]) for r in rows(cursor)]

    def approve_selected(self, preview, members, actor):
        """Commit every selected intent before any domain repair can start."""
        if not 1 <= len(members) <= 25 or len({m["id"] for m in members}) != len(members):
            raise SourceConflict("Select between one and 25 distinct historical exports.")
        group = str(uuid4())
        selection_key = self.selection_key(preview, members, actor)
        with transaction(self.store.connect) as cursor:
            self._lock(cursor)
            existing = self._existing(cursor, preview, members, actor)
            if existing:
                return existing
            for member in sorted(members, key=lambda m: m["id"]):
                row = self.store._get(cursor, member["id"], lock=True)
                if (
                    row["SourceKind"] != "stats_import"
                    or row["State"] != "open"
                    or (row["Revision"], row["EvidenceHash"])
                    != (member["revision"], member["token"])
                    or ACTION not in row["evidence"].get("actions", {})
                    or row["evidence"].get("check_unavailable")
                ):
                    raise SourceConflict(
                        "A selected export changed. Reopen the group; none were approved."
                    )
                cursor.execute(
                    "SELECT TOP (1) ActionID FROM dbo.RecoveryAction WITH (UPDLOCK,HOLDLOCK) "
                    "WHERE IncidentID=? AND (State IN ('dispatched','unknown') OR IncidentRevision=?)",
                    row["IncidentID"],
                    row["Revision"],
                )
                if one(cursor):
                    raise SourceConflict(
                        "A selected export already has a decision. Reopen the group."
                    )
            evidence = dict(
                selection_key=selection_key,
                title="Grouped historical retirement",
                actions={},
                outcome="queued",
                group_id=group,
                approved_count=len(members),
                members=members,
                configuration=preview["configuration"],
                explanation="Selected obsolete exports approved. Each retirement is independently verified; SQL outcomes remain unknown.",
            )
            cursor.execute(
                "INSERT dbo.RecoveryIncident (IncidentID,ScopeKey,SourceKind,SourceID,State,EvidenceHash,EvidenceJson) "
                "VALUES (?,?,'historical_batch',?,'open',?,?)",
                group,
                self.store.scope,
                group,
                digest(evidence).hex(),
                document(evidence),
            )
            for member in members:
                cursor.execute(
                    "INSERT dbo.RecoveryAction (ActionID,IncidentID,IncidentRevision,ActionKind,EvidenceHash,Actor,Reason,State) "
                    "VALUES (?,?,?,?,?,?,?,'dispatched')",
                    str(uuid4()),
                    member["id"],
                    member["revision"],
                    ACTION,
                    member["token"],
                    actor,
                    group_reason(group, self.group_kind),
                )
        return group
