"""Atomically link one separately queued export to its original isolated input."""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _job, _mutex, identity
from services.export_replacement_projection import project_destinations


def _queued_mapping(cursor, activation, account):
    """Recheck the authority's projection from immutable SQL activation records."""
    cursor.execute("SELECT * FROM dbo.ExportReplacementActivation WHERE AccountKey=?", account)
    history = rows(cursor)
    current = next(
        (r for r in history if identity(r["ActivationID"]) == activation["activation_id"]), None
    )
    if current is None or (
        bytes(current["RegistrationHash"]) != digest(activation["registration"])
        or json.loads(current["RegistrationJson"]) != activation["registration"]
    ):
        raise SourceConflict("Queued continuation registration differs from its activation.")
    prefix, seen = [], set()
    while current is not None:
        key = identity(current["ActivationID"])
        if key in seen:
            raise SourceConflict("Queued continuation activation history is cyclic.")
        seen.add(key)
        prefix.append(current)
        predecessors = [
            r
            for r in history
            if bytes(r["RegistrationHash"]) == bytes(current["BaseRegistrationHash"])
        ]
        if len(predecessors) > 1:
            raise SourceConflict("Queued continuation activation history is ambiguous.")
        current = predecessors[0] if predecessors else None
    mappings = []
    for row in reversed(prefix):
        cursor.execute(
            "SELECT OldFileID,NewFileID FROM dbo.ExportReplacementTarget WHERE ReplacementID=?",
            row["ReplacementID"],
        )
        mappings.append({r["OldFileID"]: r["NewFileID"] for r in rows(cursor)})
    expected = project_destinations(activation["mapping"], mappings)
    if expected != activation["mapping"]:
        raise SourceConflict("Queued continuation differs from the activated destination history.")
    return expected


class ReplacementDeliveryDAL:
    def __init__(self, connect, coordinator):
        self.connect, self.coordinator = connect, coordinator

    def continuation_anchor(self, job_id, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT ActivationID FROM dbo.ExportReplacementDelivery WHERE OriginalJobID=? AND AccountKey=?",
                identity(job_id),
                account,
            )
            receipts = rows(cursor)
            if len(receipts) > 1:
                raise SourceConflict("Queued export has multiple continuation receipts.")
            return identity(receipts[0]["ActivationID"]) if receipts else None

    def publication_parts(self, job):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT p.* FROM dbo.ExportAttemptPart p JOIN dbo.ExportAttempt a "
                "ON a.AttemptID=p.AttemptID JOIN dbo.ExportJob j ON j.JobID=a.JobID "
                "WHERE j.JobID=? AND j.AccountKey=? AND j.Version=? AND j.State='confirmed' "
                "ORDER BY a.AttemptID,p.PartNo",
                job["JobID"],
                job["AccountKey"],
                job["Version"],
            )
            result = [_wire(r) for r in rows(cursor)]
            if not result:
                raise SourceConflict(
                    "Confirmed replacement publication parts are unavailable or changed."
                )
            return result

    def blocking_jobs(self, job_id, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT DISTINCT c.JobID FROM dbo.ExportJobResource m "
                "JOIN dbo.ExportContainedTarget t ON m.ResourceKey='destination:'+t.FileID "
                "JOIN dbo.ExportTargetContainment c ON c.ContainmentID=t.ContainmentID "
                "WHERE m.JobID=? AND c.AccountKey=? AND c.JobID IS NOT NULL ORDER BY c.JobID",
                identity(job_id),
                account,
            )
            return [identity(r["JobID"]) for r in rows(cursor)]

    def read(self, job_id, activation_id, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportReplacementDelivery WHERE OriginalJobID=? AND ActivationID=? AND AccountKey=?",
                identity(job_id),
                identity(activation_id),
                account,
            )
            row = one(cursor)
            if row is None:
                return None
            result = _wire(row)
            for key in ("ActionID", "OriginalJobID", "ActivationID", "ReplacementJobID"):
                result[key] = identity(result[key])
            return result

    def awaiting_initial_publication(self, account):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT a.NewPoolID FROM dbo.ExportReplacementActivation a "
                "WHERE a.AccountKey=? AND a.NewPoolID IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM dbo.ExportReplacementDelivery d WHERE d.ActivationID=a.ActivationID)",
                account,
            )
            return {identity(r["NewPoolID"]) for r in rows(cursor)}

    def enqueue(self, *, original, activation, spec, actor, reason):
        action_id = identity(actor.removeprefix("recovery:"))
        if actor != "recovery:" + action_id or spec.actor != actor or spec.reason != reason:
            raise SourceConflict("One exact durable replacement delivery decision required.")
        with self.coordinator._account(spec.account) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportReplacementDelivery WITH(UPDLOCK,HOLDLOCK) WHERE OriginalJobID=? AND AccountKey=?",
                original["JobID"],
                spec.account,
            )
            prior = one(cursor)
            if prior is not None:
                if (
                    identity(prior["ActionID"]) != action_id
                    or identity(prior["ActivationID"]) != activation["activation_id"]
                    or prior["Actor"] != actor
                    or prior["Reason"] != reason
                ):
                    raise SourceConflict(
                        "Another decision already queued this replacement delivery."
                    )
                return identity(prior["ReplacementJobID"])
            cursor.execute(
                "SELECT * FROM dbo.ExportReplacementActivation WITH(UPDLOCK,HOLDLOCK) WHERE ActivationID=? AND AccountKey=?",
                activation["activation_id"],
                spec.account,
            )
            activated = one(cursor)
            if (
                activated is None
                or bytes(activated["RegistrationHash"]).hex() != activation["registration_sha256"]
            ):
                raise SourceConflict("The verified replacement activation changed.")
            queued_continuation = activation.get("queued_continuation") is True
            if queued_continuation:
                mapping = _queued_mapping(cursor, activation, spec.account)
            else:
                cursor.execute(
                    "SELECT OldFileID,NewFileID FROM dbo.ExportReplacementTarget WHERE ReplacementID=? ORDER BY OldFileID",
                    activation["replacement_id"],
                )
                mapping = {r["OldFileID"]: r["NewFileID"] for r in rows(cursor)}
            if mapping != activation["mapping"]:
                raise SourceConflict("Activated replacement membership changed.")
            for key in sorted(
                {*("destination:" + f for f in mapping), *spec.resource_keys}
                - {"account:" + spec.account}
            ):
                _mutex(cursor, key)
            job = _job(cursor, original["JobID"])
            if job is None or (
                identity(job["JobID"]),
                job["AccountKey"],
                job["ConsumerKind"],
                job["State"],
                job["Version"],
                bytes(job["InputHash"]).hex(),
            ) != (
                original["JobID"],
                spec.account,
                spec.consumer,
                original["State"],
                original["Version"],
                original["InputHash"],
            ):
                raise SourceConflict("Original retained export changed after review.")
            cursor.execute(
                "SELECT m.ResourceKey,c.FileID FROM dbo.ExportJobResource m LEFT JOIN dbo.ExportContainedTarget c ON m.ResourceKey='destination:'+c.FileID WHERE m.JobID=? AND m.ResourceKey LIKE 'destination:%' ORDER BY m.ResourceKey",
                original["JobID"],
            )
            targets = rows(cursor)
            old_files = [r["ResourceKey"][12:] for r in targets]
            if queued_continuation:
                cursor.execute(
                    "SELECT AttemptID FROM dbo.ExportAttempt WHERE JobID=? UNION ALL "
                    "SELECT StreamID FROM dbo.ExportExecutionStream WHERE JobID=?",
                    original["JobID"],
                    original["JobID"],
                )
                if rows(cursor):
                    raise SourceConflict(
                        "Only an unstarted export may compose replacement destinations."
                    )
                if job["ConsumerKind"] == "new_source" and (
                    set(old_files) != set(mapping)
                    or any(r["FileID"] is None for r in targets)
                    or any(old == new for old, new in mapping.items())
                    or sum(
                        set(spec.destinations) == {p["index_file_id"], *p["slot_file_ids"]}
                        for p in activation["registration"]["pools"]
                    )
                    != 1
                ):
                    raise SourceConflict(
                        "Queued source recovery requires one complete replaced pool."
                    )
            if (
                not old_files
                or not set(old_files) <= set(mapping)
                or {mapping[f] for f in old_files} != set(spec.destinations)
                or not any(r["FileID"] is not None for r in targets)
                or any(
                    r["FileID"] is None
                    and (
                        not queued_continuation
                        or mapping.get(r["ResourceKey"][12:]) != r["ResourceKey"][12:]
                    )
                    for r in targets
                )
            ):
                raise SourceConflict(
                    "Every retired destination must have an activated replacement; unchanged outputs must retain their identity."
                )
            cursor.execute(
                "SELECT ResourceKey FROM dbo.ExportResource WHERE ActiveJobID=?", original["JobID"]
            )
            if rows(cursor):
                raise SourceConflict("The original export still owns reservations.")
            provenance = json.loads(spec.provenance).get("replacement", {})
            if (
                provenance.get("original_job_id") != original["JobID"]
                or provenance.get("activation_id") != activation["activation_id"]
                or provenance.get("original_input_sha256") != original["InputHash"]
            ):
                raise SourceConflict("Replacement delivery lacks exact retained-input lineage.")
            queued = self.coordinator.enqueue(
                spec,
                _cursor=cursor,
                _replacement_original=original if spec.consumer == "new_source" else None,
            )
            if json.loads(queued["ProvenanceJson"]).get("replacement") != provenance:
                raise SourceConflict("An existing queue entry has different replacement lineage.")
            key = identity(queued["JobID"])
            cursor.execute(
                "INSERT dbo.ExportReplacementDelivery(ActionID,OriginalJobID,ActivationID,ReplacementJobID,AccountKey,OriginalInputHash,ReplacementInputHash,Actor,Reason,CreatedUTC) VALUES(?,?,?,?,?,?,?,?,?,SYSUTCDATETIME())",
                action_id,
                original["JobID"],
                activation["activation_id"],
                key,
                spec.account,
                bytes.fromhex(original["InputHash"]),
                spec.input_hash,
                actor,
                reason,
            )
            return key
