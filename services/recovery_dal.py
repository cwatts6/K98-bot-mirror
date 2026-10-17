"""Durable scoped incidents and at-most-one dispatch per evidence revision.

An action intent is committed before a domain call. A lost commit acknowledgement
never authorises dispatch. Pending actions are reconciled, not claimed again.
"""

import hashlib
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, canonical, one, rows, transaction
from services.export_coordination_dal import identity


def document(value, *, export_incident=False):
    encoded = canonical(value)
    if len(encoded.encode("utf-16-le")) > (1048576 if export_incident else 32768):
        raise ValueError("Recovery evidence exceeds its bound.")
    return encoded


def input_document(value):
    encoded = canonical(value)
    if len(encoded.encode("utf-16-le")) > 1048576:
        raise SourceConflict("Guided recovery input exceeds its bound.")
    return encoded


class RecoveryDAL:
    def __init__(self, connect, *, account, storage_owner, guild_id):
        self.connect = connect
        self.scope = hashlib.sha256(
            canonical([account, storage_owner, int(guild_id)]).encode()
        ).hexdigest()

    def _get(self, cursor, incident_id, *, lock=False):
        hint = " WITH (UPDLOCK,HOLDLOCK)" if lock else ""
        cursor.execute(
            "SELECT * FROM dbo.RecoveryIncident" + hint + " WHERE IncidentID=? AND ScopeKey=?",
            identity(incident_id),
            self.scope,
        )
        row = one(cursor)
        if not row:
            raise SourceConflict("This incident is unavailable in the current recovery scope.")
        row["IncidentID"] = identity(row["IncidentID"])
        row["evidence"] = json.loads(row["EvidenceJson"])
        return row

    def get(self, incident_id):
        with transaction(self.connect) as cursor:
            return self._get(cursor, incident_id)

    def observe(self, kind, source_id, evidence, evidence_hash, *, resolved=False):
        if not isinstance(kind, str) or not 1 <= len(kind) <= 64:
            raise ValueError("Bounded recovery kind required.")
        source_id = identity(source_id)
        if len(evidence_hash) != 64 or any(c not in "0123456789abcdef" for c in evidence_hash):
            raise ValueError("Exact evidence digest required.")
        encoded = document(evidence, export_incident=kind == "export_job")
        state = "resolved" if resolved else "open"
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.RecoveryIncident WITH (UPDLOCK,HOLDLOCK) "
                "WHERE ScopeKey=? AND SourceKind=? AND SourceID=?",
                self.scope,
                kind,
                source_id,
            )
            row = one(cursor)
            if row:
                incident_id = identity(row["IncidentID"])
                changed = (
                    row["EvidenceHash"] != evidence_hash
                    or row["State"] != state
                    or row["EvidenceJson"] != encoded
                )
                cursor.execute(
                    "UPDATE dbo.RecoveryIncident SET EvidenceJson=?,EvidenceHash=?,State=?,"
                    "Revision=Revision+?,LastSeenUTC=SYSUTCDATETIME() WHERE IncidentID=? AND ScopeKey=?",
                    encoded,
                    evidence_hash,
                    state,
                    int(changed),
                    incident_id,
                    self.scope,
                )
            else:
                incident_id = str(uuid4())
                cursor.execute(
                    "INSERT dbo.RecoveryIncident (IncidentID,ScopeKey,SourceKind,SourceID,State,EvidenceHash,EvidenceJson) "
                    "VALUES (?,?,?,?,?,?,?)",
                    incident_id,
                    self.scope,
                    kind,
                    source_id,
                    state,
                    evidence_hash,
                    encoded,
                )
            return self._get(cursor, incident_id)

    def list_open(self, *, after=None, limit=20, non_evidence=False, queues_only=False):
        if type(limit) is not int or not 1 <= limit <= 25:
            raise ValueError("Bounded incident page required.")
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) * FROM dbo.RecoveryIncident WHERE ScopeKey=? AND State='open' "
                "AND SourceKind<>'recovery_overview' "
                + ("AND SourceKind<>'private_evidence' " if non_evidence else "")
                + ("AND SourceKind='queue_admission' " if queues_only else "")
                + "AND (? IS NULL OR IncidentID>CAST(? AS uniqueidentifier)) ORDER BY IncidentID",
                limit,
                self.scope,
                after,
                after,
            )
            result = rows(cursor)
            for row in result:
                row["IncidentID"] = identity(row["IncidentID"])
                row["evidence"] = json.loads(row["EvidenceJson"])
            return result

    def count_open(self):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT COUNT_BIG(*) AS Total FROM dbo.RecoveryIncident "
                "WHERE ScopeKey=? AND State='open' AND SourceKind<>'recovery_overview'",
                self.scope,
            )
            return one(cursor)["Total"]

    def check_failed(self, incident_id, error_type):
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id, lock=True)
            if row["evidence"].get("check_unavailable") == error_type:
                return
            evidence = dict(row["evidence"], check_unavailable=error_type)
            cursor.execute(
                "UPDATE dbo.RecoveryIncident SET EvidenceJson=?,Revision=Revision+1 WHERE IncidentID=? AND ScopeKey=?",
                document(evidence, export_incident=row["SourceKind"] == "export_job"),
                row["IncidentID"],
                self.scope,
            )

    def report_page(self, *, after=None, through=None):
        """Read all states in bounded pages; never inspect, reconcile or dispatch."""
        after = identity(after) if after is not None else None
        with transaction(self.connect) as cursor:
            if through is None:
                # Match FirstSeenUTC precision, including its millisecond rounding.
                cursor.execute("SELECT CONVERT(datetime2(3),SYSUTCDATETIME()) AS ThroughUTC")
                through = one(cursor)["ThroughUTC"]
            cursor.execute(
                "SELECT COUNT_BIG(*) AS Total FROM dbo.RecoveryIncident "
                "WHERE ScopeKey=? AND FirstSeenUTC<=?",
                self.scope,
                through,
            )
            total = one(cursor)["Total"]
            cursor.execute(
                "SELECT TOP (101) i.*, a.State AS PendingActionState, "
                "a.ActionKind AS PendingActionKind FROM dbo.RecoveryIncident i "
                "OUTER APPLY (SELECT TOP (1) State,ActionKind FROM dbo.RecoveryAction "
                "WHERE IncidentID=i.IncidentID AND State IN ('dispatched','unknown') "
                "ORDER BY CreatedUTC,ActionID) a WHERE i.ScopeKey=? "
                "AND i.FirstSeenUTC<=? AND (? IS NULL OR i.IncidentID>CAST(? AS uniqueidentifier)) "
                "ORDER BY i.IncidentID",
                self.scope,
                through,
                after,
                after,
            )
            result = rows(cursor)
            more = len(result) > 100
            result = result[:100]
            for row in result:
                row["IncidentID"] = identity(row["IncidentID"])
                row["evidence"] = json.loads(row["EvidenceJson"])
                row["pending_action"] = (
                    {"state": row["PendingActionState"], "kind": row["PendingActionKind"]}
                    if row["PendingActionState"] is not None
                    else None
                )
            return dict(rows=result, through=through, total=total, more=more)

    def has_failed_checks(self):
        """Include failures outside the current discovery page and across restarts."""
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) IncidentID FROM dbo.RecoveryIncident WHERE ScopeKey=? "
                "AND State='open' AND JSON_VALUE(EvidenceJson,'$.check_unavailable') IS NOT NULL",
                self.scope,
            )
            return one(cursor) is not None

    def touch_pending(self, incident_id):
        """Fair retry scheduling only; never marks a repair successful."""
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id)
            cursor.execute(
                "UPDATE dbo.RecoveryAction SET UpdatedUTC=SYSUTCDATETIME() WHERE IncidentID=? "
                "AND State IN ('dispatched','unknown')",
                row["IncidentID"],
            )

    def alerts_due(self):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (1) IncidentID FROM dbo.RecoveryIncident WHERE ScopeKey=? "
                "AND SourceKind='recovery_overview' AND (State='open' OR AlertedRevision<Revision) "
                "AND (AlertCheckedUTC IS NULL OR AlertCheckedUTC<DATEADD(minute,-5,SYSUTCDATETIME())) "
                "ORDER BY COALESCE(AlertCheckedUTC,CONVERT(datetime2,'19000101')),IncidentID",
                self.scope,
            )
            return [identity(r["IncidentID"]) for r in rows(cursor)]

    def alert_sent(self, incident_id, revision, channel_id, message_id):
        with transaction(self.connect) as cursor:
            self._get(cursor, incident_id, lock=True)
            cursor.execute(
                "UPDATE dbo.RecoveryIncident SET AlertChannelID=?,AlertMessageID=?,AlertedRevision=?,"
                "AlertCheckedUTC=SYSUTCDATETIME(),AlertAttemptUTC=NULL WHERE IncidentID=? AND ScopeKey=? AND Revision>=?",
                int(channel_id),
                int(message_id),
                int(revision),
                identity(incident_id),
                self.scope,
                int(revision),
            )

    def claim_alert(self, incident_id):
        """Lease only notification delivery, never resource or business ownership."""
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id, lock=True)
            cursor.execute(
                "UPDATE dbo.RecoveryIncident SET AlertAttemptUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.IncidentID WHERE IncidentID=? AND ScopeKey=? "
                "AND (AlertAttemptUTC IS NULL OR AlertAttemptUTC<DATEADD(minute,-5,SYSUTCDATETIME()))",
                row["IncidentID"],
                self.scope,
            )
            return one(cursor) is not None

    def claim(
        self,
        incident_id,
        revision,
        evidence_hash,
        kind,
        actor,
        reason,
        *,
        payload=None,
        draft_version=None,
    ):
        if not (
            1 <= len(actor) <= 128 and 1 <= len(reason.strip()) <= 512 and 1 <= len(kind) <= 64
        ):
            raise ValueError("Bounded action, actor and reason required.")
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id, lock=True)
            cursor.execute(
                "SELECT TOP (1) ActionID FROM dbo.RecoveryAction WHERE IncidentID=? "
                "AND (State IN ('dispatched','unknown') OR IncidentRevision=?)",
                row["IncidentID"],
                revision,
            )
            existing = one(cursor)
            if existing:
                return identity(existing["ActionID"]), False
            if row["State"] != "open" or (row["Revision"], row["EvidenceHash"]) != (
                revision,
                evidence_hash,
            ):
                raise SourceConflict(
                    "The evidence changed. Review the refreshed incident before confirming."
                )
            action_id = str(uuid4())
            if payload is not None:
                draft = self._input_draft(cursor, row, kind, lock=True)
                if draft["version"] != draft_version or draft["input"] != payload:
                    raise SourceConflict(
                        "The replacement choices changed. Review them again before confirming."
                    )
            cursor.execute(
                "INSERT dbo.RecoveryAction (ActionID,IncidentID,IncidentRevision,ActionKind,EvidenceHash,Actor,Reason,State) "
                "VALUES (?,?,?,?,?,?,?,'dispatched')",
                action_id,
                row["IncidentID"],
                revision,
                kind,
                evidence_hash,
                actor,
                reason.strip(),
            )
            if payload is not None:
                cursor.execute(
                    "UPDATE dbo.RecoveryAction SET InputJson=? WHERE ActionID=?",
                    input_document(payload),
                    action_id,
                )
            return action_id, True

    def _input_draft(self, cursor, row, action, *, lock=False):
        hint = " WITH(UPDLOCK,HOLDLOCK)" if lock else ""
        cursor.execute(
            "SELECT * FROM dbo.RecoveryInputDraft"
            + hint
            + " WHERE IncidentID=? AND IncidentRevision=? AND ActionKind=?",
            row["IncidentID"],
            row["Revision"],
            action,
        )
        draft = one(cursor)
        if draft is None:
            return dict(version=0, input={})
        if draft["EvidenceHash"] != row["EvidenceHash"]:
            raise SourceConflict("Saved input belongs to different recovery evidence.")
        return dict(version=draft["Version"], input=json.loads(draft["InputJson"]))

    def input_draft(self, incident_id, action):
        with transaction(self.connect) as cursor:
            return self._input_draft(cursor, self._get(cursor, incident_id), action)

    def save_input(self, incident_id, revision, token, action, version, values, actor):
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id, lock=True)
            if row["State"] != "open" or (row["Revision"], row["EvidenceHash"]) != (
                revision,
                token,
            ):
                raise SourceConflict("Recovery evidence changed. Reopen the guided form.")
            cursor.execute(
                "SELECT TOP (1) ActionID FROM dbo.RecoveryAction WHERE IncidentID=? AND "
                "(State IN ('dispatched','unknown') OR IncidentRevision=?)",
                row["IncidentID"],
                revision,
            )
            if one(cursor):
                raise SourceConflict(
                    "A confirmed action already owns this evidence; recheck its result."
                )
            draft = self._input_draft(cursor, row, action, lock=True)
            if draft["version"] != version:
                raise SourceConflict("Another form saved newer choices. Reopen this page.")
            payload = draft["input"] | values
            encoded = input_document(payload)
            if version == 0:
                cursor.execute(
                    "INSERT dbo.RecoveryInputDraft(IncidentID,IncidentRevision,ActionKind,EvidenceHash,Version,InputJson,Actor,UpdatedUTC) "
                    "VALUES(?,?,?,?,1,?,?,SYSUTCDATETIME())",
                    row["IncidentID"],
                    revision,
                    action,
                    token,
                    encoded,
                    actor,
                )
            else:
                cursor.execute(
                    "UPDATE dbo.RecoveryInputDraft SET Version=Version+1,InputJson=?,Actor=?,UpdatedUTC=SYSUTCDATETIME() "
                    "WHERE IncidentID=? AND IncidentRevision=? AND ActionKind=? AND Version=?",
                    encoded,
                    actor,
                    row["IncidentID"],
                    revision,
                    action,
                    version,
                )
            return dict(version=version + 1, input=payload)

    def pending_actions(self, incident_id):
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id)
            cursor.execute(
                "SELECT * FROM dbo.RecoveryAction WHERE IncidentID=? AND State IN ('dispatched','unknown') ORDER BY CreatedUTC",
                row["IncidentID"],
            )
            return rows(cursor)

    def finish(self, incident_id, action_id, state, result):
        if state not in {"verified", "unknown", "not_applied"}:
            raise ValueError("Unsupported recovery result.")
        with transaction(self.connect) as cursor:
            row = self._get(cursor, incident_id, lock=True)
            cursor.execute(
                "UPDATE dbo.RecoveryAction SET State=?,ResultJson=?,UpdatedUTC=SYSUTCDATETIME() "
                "WHERE ActionID=? AND IncidentID=? AND State IN ('dispatched','unknown')",
                state,
                document(result),
                identity(action_id),
                row["IncidentID"],
            )
