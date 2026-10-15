"""Durable scoped incidents and at-most-one dispatch per evidence revision.

An action intent is committed before a domain call. A lost commit acknowledgement
never authorises dispatch. Pending actions are reconciled, not claimed again.
"""

import hashlib
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, canonical, one, rows, transaction
from services.export_coordination_dal import identity


def document(value):
    encoded = canonical(value)
    if len(encoded.encode("utf-16-le")) > 32768:
        raise ValueError("Recovery evidence exceeds its bound.")
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
        encoded = document(evidence)
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
                changed = row["EvidenceHash"] != evidence_hash or row["State"] != state
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

    def list_open(self, *, after=None, limit=20):
        if type(limit) is not int or not 1 <= limit <= 25:
            raise ValueError("Bounded incident page required.")
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) * FROM dbo.RecoveryIncident WHERE ScopeKey=? AND State='open' "
                "AND (? IS NULL OR IncidentID>CAST(? AS uniqueidentifier)) ORDER BY IncidentID",
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

    def alerts_due(self):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) IncidentID FROM dbo.RecoveryIncident WHERE ScopeKey=? "
                "AND (State='open' OR AlertedRevision<Revision) "
                "AND (AlertCheckedUTC IS NULL OR AlertCheckedUTC<DATEADD(second,-60,SYSUTCDATETIME())) "
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

    def claim(self, incident_id, revision, evidence_hash, kind, actor, reason):
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
            return action_id, True

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
