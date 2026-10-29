"""Fence a completed import for read-only capture under both SQL session guards."""

from contextlib import contextmanager
import json

from kvk.dal.new_source_import_dal import SourceConflict, one
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.legacy_export_snapshot_dal import PreparationClaim


class ImportCaptureRecoveryDAL:
    def __init__(self, outcomes, *, stats_execution=True):
        self.outcomes = outcomes
        self.stats_execution = stats_execution

    def guards(self, preparation_id):
        return ("k98-legacy-output-snapshot",) + (
            ("S11:stats-import:" + identity(preparation_id),) if self.stats_execution else ()
        )

    @contextmanager
    def session(self, preparation_id):
        connection = self.outcomes.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                # Match producer lock order. Neither elapsed time nor a completed
                # receipt substitutes for exclusion of a still-live SQL session.
                for resource in self.guards(preparation_id):
                    cursor.execute(
                        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,"
                        "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; "
                        "SELECT @r AS LockResult",
                        resource,
                    )
                    result = one(cursor)
                    if not result or result["LockResult"] < 0:
                        from kvk.dal.new_source_import_dal import SourceBusy

                        raise SourceBusy("The original producer is still active. Recheck later.")
                yield connection
            finally:
                # Explicit release also covers drivers which pool closed connections.
                for resource in reversed(self.guards(preparation_id)):
                    cursor.execute(
                        "IF APPLOCK_MODE('public',?,'Session')='Exclusive' "
                        "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'",
                        resource,
                        resource,
                    )
                cursor.close()
        finally:
            connection.close()

    def adopt(self, connection, preparation_id, token, actor, generation_factory):
        """Short atomic CAS; keep both independent guards until capture finishes."""
        preparation_id = identity(preparation_id)
        cursor = connection.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            for resource in self.guards(preparation_id):
                cursor.execute("SELECT APPLOCK_MODE('public',?,'Session') AS Mode", resource)
                if one(cursor)["Mode"] != "Exclusive":
                    raise SourceConflict("All producer recovery session guards are required.")
            _mutex(cursor, "account:" + self.outcomes.account)
            prep, execution, resources = self.outcomes._snapshot(cursor, preparation_id)
            self.outcomes._scope(prep)
            if self.outcomes.action(prep, execution, resources) != "resume_capture":
                raise SourceConflict("Only a completed, retained import can resume capture.")
            previous = json.loads(prep["GenerationJson"]) if prep["GenerationJson"] else {}
            if previous.get("capture_failure") or previous.get("capture_abandoned"):
                raise SourceConflict(
                    "Capture needs a new admin decision; the prior repair cannot resume."
                )
            marker = dict(token=token, actor=actor)
            retained = previous.get("capture_recovery")
            if retained != marker and (
                retained is not None or self.outcomes.token(prep, execution, resources) != token
            ):
                raise SourceConflict("Recovery evidence changed. Review the current incident.")
            generation = generation_factory(prep, execution)
            generation["capture_recovery"] = marker
            resource = resources[0]
            version = _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='committed',GenerationJson=?,"
                "Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version "
                "WHERE PreparationID=? AND OwnerID=? AND Fence=? AND Version=?",
                bounded_json(generation),
                preparation_id,
                prep["OwnerID"],
                prep["Fence"],
                prep["Version"],
            )["Version"]
            resource_version = _cas(
                cursor,
                "UPDATE dbo.ExportResource SET BlockedReason=NULL,Version=Version+1 "
                "OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? "
                "AND OwnerID=? AND Fence=? AND Version=? AND ActiveJobID IS NULL "
                "AND ActiveOutputOperationID IS NULL",
                resource["ResourceKey"],
                preparation_id,
                prep["OwnerID"],
                prep["Fence"],
                resource["Version"],
            )["Version"]
            cursor.execute("COMMIT TRANSACTION")
            return (
                PreparationClaim(
                    preparation_id,
                    self.outcomes.account,
                    identity(prep["OwnerID"]),
                    prep["Fence"],
                    version,
                    ((resource["ResourceKey"], resource_version),),
                ),
                generation,
            )
        except BaseException:
            # An unknown COMMIT leaves a durable marker; the same action reads it
            # on its next attempt. Never infer rollback from this cleanup.
            try:
                cursor.execute("IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
            except Exception:
                pass
            raise
        finally:
            cursor.close()

    def conclude(self, preparation_id, token, actor, reason, generation_factory, *, abandon):
        """Fence an unavailable capture or abandon its export; never undo SQL data."""
        if (
            not isinstance(actor, str)
            or not 1 <= len(actor) <= 128
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise ValueError("Bounded recovery actor and reason required.")
        preparation_id = identity(preparation_id)
        marker = dict(token=token, actor=actor, reason=reason)
        key = "capture_abandoned" if abandon else "capture_failure"
        with self.session(preparation_id) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                _mutex(cursor, "account:" + self.outcomes.account)
                prep, execution, resources = self.outcomes._snapshot(cursor, preparation_id)
                self.outcomes._scope(prep)
                generation = generation_factory(prep, execution)
                if prep["JobID"] is not None:
                    raise SourceConflict("Queued exports require their separate recovery workflow.")
                if generation.get(key) == marker:
                    if abandon and (prep["State"] != "unavailable" or resources):
                        raise SourceConflict("Abandonment receipt differs from its release.")
                    cursor.execute("COMMIT TRANSACTION")
                    return
                if prep["State"] == "unavailable" or generation.get("capture_abandoned"):
                    raise SourceConflict("Capture was already closed by another action.")
                if self.stats_execution and (
                    not execution
                    or execution["State"] != "completed"
                    or execution["Resolution"] is not None
                    or (identity(execution["OwnerID"]), execution["Fence"])
                    != (identity(prep["OwnerID"]), prep["Fence"])
                ):
                    raise SourceConflict("The exact completed SQL execution receipt is required.")
                captured = self.outcomes.capture_completed(prep, execution, resources)
                if (
                    not captured
                    and self.outcomes.action(prep, execution, resources) != "resume_capture"
                ):
                    raise SourceConflict("Only an unqueued committed capture may be closed.")
                # A prepare-side provider stream is outside this SQL-only repair.
                cursor.execute(
                    "SELECT TOP (1) StreamID FROM dbo.ExportExecutionStream WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
                    preparation_id,
                )
                if one(cursor):
                    raise SourceConflict("Provider execution evidence requires separate recovery.")
                current = self.outcomes.token(prep, execution, resources)
                retained = generation.get("capture_recovery")
                if current != token and (abandon or retained != dict(token=token, actor=actor)):
                    raise SourceConflict("Capture evidence changed. Review the current incident.")
                if generation.get("capture_failure") and not abandon:
                    raise SourceConflict("A different failed capture decision is already recorded.")
                generation[key] = marker
                if abandon:
                    for resource in resources:
                        _cas(
                            cursor,
                            "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,Version=Version+1 "
                            "OUTPUT inserted.Version WHERE ResourceKey=? AND Version=? AND OwnerID=? AND Fence=? "
                            "AND ActivePreparationID=? AND ActiveJobID IS NULL AND ActiveOutputOperationID IS NULL",
                            resource["ResourceKey"],
                            resource["Version"],
                            prep["OwnerID"],
                            prep["Fence"],
                            preparation_id,
                        )
                _cas(
                    cursor,
                    "UPDATE dbo.ExportPreparation SET State=?,GenerationJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                    "OUTPUT inserted.Version WHERE PreparationID=? AND Version=? AND OwnerID=? AND Fence=? AND JobID IS NULL",
                    "unavailable" if abandon else prep["State"],
                    bounded_json(generation),
                    preparation_id,
                    prep["Version"],
                    prep["OwnerID"],
                    prep["Fence"],
                )
                cursor.execute("COMMIT TRANSACTION")
            except BaseException:
                try:
                    cursor.execute("IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
                except Exception:
                    pass
                raise
            finally:
                cursor.close()
