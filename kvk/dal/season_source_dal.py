"""Fixed choices and lifecycle CAS. No ordinary source replacement or deletion."""

import json
from uuid import uuid4

from kvk.models.source_integration import SEASON_STATES, SOURCES, bounded_text


def audit_json(value):
    from kvk.dal.new_source_import_dal import canonical

    if not isinstance(value, dict):
        raise ValueError("Audit provenance must be a JSON object.")
    json.dumps(value, allow_nan=False)
    result = canonical(value)
    if len(result.encode("utf-16-le")) > 65536:
        raise ValueError("Audit provenance exceeds SQL capacity.")
    return result


def lock_season(cursor, kvk_no, *, read=True):
    """Called immediately after the common transaction application mutex."""
    from kvk.dal.new_source_import_dal import one

    cursor.execute("SELECT * FROM KVK.SeasonSource WITH (UPDLOCK,HOLDLOCK) WHERE KVK_NO=?", kvk_no)
    if not read:
        cursor.fetchall()
        return None
    return one(cursor)


def require_source(cursor, kvk_no, source_key, *, expected_version=None, onboarding=False):
    from kvk.dal.new_source_import_dal import SourceConflict

    choice = lock_season(cursor, kvk_no)
    if choice is None:
        raise SourceConflict("Season source setup is required before admission.")
    if source_key not in SOURCES or choice["SourceKey"] != source_key:
        raise SourceConflict("The fixed season source conflicts with this operation.")
    allowed = ("planned", "open") if onboarding else ("open",)
    if choice["SeasonState"] not in allowed:
        raise SourceConflict("Season lifecycle does not permit this operation.")
    if expected_version is not None and choice["SeasonVersion"] != expected_version:
        raise SourceConflict("Season lifecycle CAS lost.")
    return choice


class SeasonSourceDAL:
    def __init__(self, connect):
        self.connect = connect

    def choose(self, kvk_no, source_key, *, actor, reason, provenance, authorized):
        from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, one, transaction

        if authorized is not True:
            raise PermissionError("Explicit season-source authority is required.")
        if source_key not in SOURCES:
            raise ValueError("Unknown season source.")
        bounded_text(actor, 128)
        bounded_text(reason, 1024)
        evidence = audit_json(provenance)
        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            previous = lock_season(cursor, kvk_no)
            if previous:
                if previous["SourceKey"] != source_key:
                    raise SourceConflict("A different source is already fixed for this season.")
                return previous
            cursor.execute(
                "INSERT KVK.SeasonSource (KVK_NO,SourceKey,ChoiceID,ChosenBy,ChosenUTC,Reason,ProvenanceJson,SeasonState,SeasonVersion) "
                "VALUES (?,?,?,?,SYSUTCDATETIME(),?,?,'planned',1)",
                kvk_no,
                source_key,
                str(uuid4()),
                actor,
                reason,
                evidence,
            )
            cursor.execute("SELECT * FROM KVK.SeasonSource WHERE KVK_NO=?", kvk_no)
            return one(cursor)

    def read(self, kvk_no):
        from kvk.dal.new_source_import_dal import lock_scope, transaction

        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            return lock_season(cursor, kvk_no)

    def transition(self, kvk_no, state, *, expected_version, actor, reason, authorized):
        from kvk.dal.new_source_import_dal import SourceConflict, lock_scope, one, transaction

        if authorized is not True:
            raise PermissionError("Explicit lifecycle authority is required.")
        bounded_text(actor, 128)
        bounded_text(reason, 1024)
        if state not in SEASON_STATES:
            raise ValueError("Unknown lifecycle state.")
        with transaction(self.connect) as cursor:
            lock_scope(cursor, kvk_no)
            row = lock_season(cursor, kvk_no)
            if not row or row["SeasonVersion"] != expected_version:
                raise SourceConflict("Season lifecycle CAS lost.")
            if SEASON_STATES.index(state) != SEASON_STATES.index(row["SeasonState"]) + 1:
                raise SourceConflict("Lifecycle transitions must advance one state.")
            evidence = json.loads(row["ProvenanceJson"])
            history = evidence.setdefault("lifecycle", [])
            if not isinstance(history, list):
                raise SourceConflict("Invalid retained lifecycle audit.")
            cursor.execute("SELECT SYSUTCDATETIME() AS utc")
            utc = one(cursor)["utc"]
            history.append(
                dict(
                    actor=actor,
                    reason=reason,
                    old=row["SeasonState"],
                    new=state,
                    version=expected_version + 1,
                    utc=utc.isoformat(),
                )
            )
            cursor.execute(
                "UPDATE KVK.SeasonSource SET SeasonState=?,SeasonVersion=SeasonVersion+1,ProvenanceJson=? "
                "OUTPUT inserted.* WHERE KVK_NO=? AND SeasonVersion=?",
                state,
                audit_json(evidence),
                kvk_no,
                expected_version,
            )
            result = one(cursor)
            if result is None:
                raise SourceConflict("Season lifecycle CAS lost.")
            return result
