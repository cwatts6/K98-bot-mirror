"""Scoped backlog queries and atomic group approval on existing recovery receipts.

Each member receives its own durable action before any repair. The ordinary
reconciler validates that member's original hash and records its outcome.
"""

import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.export_coordination_dal import identity

GROUP_REASON = "Evidence group "


def group_reason(identifier, kind="evidence_batch"):
    if kind == "historical_batch":
        return (
            "Historical group "
            + identity(identifier)
            + ": admin retired selected obsolete exports; SQL outcome unproven"
        )
    return GROUP_REASON + identity(identifier) + ": admin approved exact verified-copy repairs"


class RecoveryBacklogDAL:
    def __init__(self, store, *, group_kind="evidence_batch"):
        if group_kind not in {"evidence_batch", "historical_batch"}:
            raise ValueError("Supported recovery group required.")
        self.store = store
        self.group_kind = group_kind

    def summary(self):
        with transaction(self.store.connect) as cursor:
            cursor.execute(
                "SELECT SourceKind,State,JSON_VALUE(EvidenceJson,'$.outcome') AS Outcome,"
                "JSON_VALUE(EvidenceJson,'$.copies.primary') AS PrimaryCopy,"
                "JSON_VALUE(EvidenceJson,'$.copies.replica') AS ReplicaCopy,"
                "CASE WHEN JSON_VALUE(EvidenceJson,'$.check_unavailable') IS NULL THEN 0 ELSE 1 END AS CheckFailed,"
                "COUNT_BIG(*) AS Total,MIN(FirstSeenUTC) AS FirstSeenUTC,MAX(FirstSeenUTC) AS LastFirstSeenUTC "
                "FROM dbo.RecoveryIncident WHERE ScopeKey=? AND SourceKind<>'recovery_overview' "
                "GROUP BY SourceKind,State,JSON_VALUE(EvidenceJson,'$.outcome'),"
                "JSON_VALUE(EvidenceJson,'$.copies.primary'),JSON_VALUE(EvidenceJson,'$.copies.replica'),"
                "CASE WHEN JSON_VALUE(EvidenceJson,'$.check_unavailable') IS NULL THEN 0 ELSE 1 END "
                "ORDER BY SourceKind,State,Outcome,PrimaryCopy,ReplicaCopy,CheckFailed",
                self.store.scope,
            )
            groups = rows(cursor)
            cursor.execute(
                "SELECT a.State,a.ActionKind,COUNT_BIG(*) AS Total FROM dbo.RecoveryAction a "
                "JOIN dbo.RecoveryIncident i ON i.IncidentID=a.IncidentID WHERE i.ScopeKey=? "
                "GROUP BY a.State,a.ActionKind ORDER BY a.State,a.ActionKind",
                self.store.scope,
            )
            actions = rows(cursor)
        return dict(groups=groups, actions=actions)

    def _candidates(self, cursor, through, *, lock=False):
        hint = " WITH (UPDLOCK,HOLDLOCK)" if lock else ""
        cursor.execute(
            "SELECT TOP (100001) i.IncidentID,i.Revision,i.EvidenceHash,CASE WHEN "
            "JSON_VALUE(i.EvidenceJson,'$.copies.primary')='verified' THEN 'protect_evidence' "
            "ELSE 'restore_evidence' END AS ActionKind FROM dbo.RecoveryIncident i" + hint + " "
            "WHERE i.ScopeKey=? AND i.SourceKind='private_evidence' AND i.State='open' "
            "AND i.FirstSeenUTC<=? AND JSON_VALUE(i.EvidenceJson,'$.outcome')='recoverable' "
            "AND JSON_VALUE(i.EvidenceJson,'$.check_unavailable') IS NULL AND "
            "((JSON_VALUE(i.EvidenceJson,'$.copies.primary')='verified' AND "
            "JSON_VALUE(i.EvidenceJson,'$.actions.protect_evidence.label') IS NOT NULL) OR "
            "(JSON_VALUE(i.EvidenceJson,'$.copies.replica')='verified' AND "
            "JSON_VALUE(i.EvidenceJson,'$.actions.restore_evidence.label') IS NOT NULL)) "
            "AND NOT EXISTS(SELECT 1 FROM dbo.RecoveryAction a"
            + hint
            + " WHERE a.IncidentID=i.IncidentID "
            "AND (a.State IN ('dispatched','unknown') OR a.IncidentRevision=i.Revision)) ORDER BY i.IncidentID",
            self.store.scope,
            through,
        )
        result = [dict(r, IncidentID=identity(r["IncidentID"])) for r in rows(cursor)]
        if len(result) > 100000:
            raise SourceConflict(
                "More than 100,000 repairs need review; this group was not approved or truncated."
            )
        return result

    def preview(self):
        with transaction(self.store.connect) as cursor:
            cursor.execute("SELECT CONVERT(datetime2(3),SYSUTCDATETIME()) AS ThroughUTC")
            through = one(cursor)["ThroughUTC"]
            members = self._candidates(cursor, through)
        return dict(through=str(through), count=len(members), token=digest(members).hex())

    def approve(self, preview, actor):
        """The whole reviewed set is claimed or none is; no domain calls here."""
        from services.recovery_dal import document

        group = str(uuid4())
        reason = group_reason(group)
        with transaction(self.store.connect) as cursor:
            # Serialize group approvals in this account/storage/guild. Individual
            # claims share row/action locks and the unique revision constraint.
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',"
                "@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS Result",
                "k98-evidence-group:" + self.store.scope,
            )
            if one(cursor)["Result"] < 0:
                raise SourceConflict("Another group approval is in progress. Reopen the review.")
            members = self._candidates(cursor, preview["through"], lock=True)
            if (
                not members
                or len(members) != preview["count"]
                or digest(members).hex() != preview["token"]
            ):
                raise SourceConflict(
                    "The repair group changed. Review the current group before confirming."
                )
            evidence = dict(
                title="Grouped evidence repairs",
                outcome="queued",
                actions={},
                explanation="Approved repairs are queued. Every copy is independently verified; unavailable or changed evidence stays open.",
                group_id=group,
                approved_count=len(members),
            )
            cursor.execute(
                "INSERT dbo.RecoveryIncident (IncidentID,ScopeKey,SourceKind,SourceID,State,EvidenceHash,EvidenceJson) "
                "VALUES (?,?,'evidence_batch',?,'open',?,?)",
                group,
                self.store.scope,
                group,
                preview["token"],
                document(evidence),
            )
            # SQL insert-select is bounded by the exact locked reviewed membership;
            # one transaction makes a lost acknowledgement safe to reconcile.
            cursor.execute(
                "INSERT dbo.RecoveryAction (ActionID,IncidentID,IncidentRevision,ActionKind,EvidenceHash,Actor,Reason,State) "
                "SELECT NEWID(),i.IncidentID,i.Revision,m.ActionKind,i.EvidenceHash,?,?,'dispatched' "
                "FROM OPENJSON(?) WITH (IncidentID uniqueidentifier '$.IncidentID',"
                "ActionKind varchar(64) '$.ActionKind') m JOIN dbo.RecoveryIncident i ON i.IncidentID=m.IncidentID "
                "WHERE i.ScopeKey=?",
                actor,
                reason,
                json.dumps(members),
                self.store.scope,
            )
        return group

    def group_progress(self, group):
        # Scope is checked even for a guessed group ID.
        row = self.store.get(group)
        if row["SourceKind"] != self.group_kind:
            raise SourceConflict("This is not an evidence repair group.")
        with transaction(self.store.connect) as cursor:
            cursor.execute(
                "SELECT a.State,COUNT_BIG(*) AS Total FROM dbo.RecoveryAction a "
                "JOIN dbo.RecoveryIncident i ON i.IncidentID=a.IncidentID WHERE i.ScopeKey=? AND a.Reason=? "
                "GROUP BY a.State ORDER BY a.State",
                self.store.scope,
                group_reason(group, self.group_kind),
            )
            counts = {r["State"]: r["Total"] for r in rows(cursor)}
        return row, counts

    def pending_groups(self):
        with transaction(self.store.connect) as cursor:
            cursor.execute(
                "SELECT IncidentID FROM dbo.RecoveryIncident WHERE ScopeKey=? AND SourceKind=? AND State='open'",
                self.store.scope,
                self.group_kind,
            )
            return [identity(r["IncidentID"]) for r in rows(cursor)]

    def pending_repairs(self, source_kind="private_evidence"):
        with transaction(self.store.connect) as cursor:
            cursor.execute(
                "SELECT TOP (50) i.IncidentID FROM dbo.RecoveryIncident i JOIN dbo.RecoveryAction a "
                "ON a.IncidentID=i.IncidentID WHERE i.ScopeKey=? AND i.SourceKind=? "
                "AND a.State IN ('dispatched','unknown') "
                "ORDER BY a.UpdatedUTC,a.CreatedUTC,a.ActionID",
                self.store.scope,
                source_kind,
            )
            return [identity(r["IncidentID"]) for r in rows(cursor)]
