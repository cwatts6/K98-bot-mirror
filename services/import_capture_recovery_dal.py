"""Fence a completed import for read-only capture under both SQL session guards."""

from contextlib import contextmanager
import json

from kvk.dal.new_source_import_dal import SourceConflict, one
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.legacy_export_snapshot_dal import PreparationClaim


class ImportCaptureRecoveryDAL:
    def __init__(self, outcomes):
        self.outcomes = outcomes

    @contextmanager
    def session(self, preparation_id):
        connection = self.outcomes.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                # Match producer lock order. Neither elapsed time nor a completed
                # receipt substitutes for exclusion of a still-live SQL session.
                for resource in (
                    "k98-legacy-output-snapshot",
                    "S11:stats-import:" + identity(preparation_id),
                ):
                    cursor.execute(
                        "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,"
                        "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; "
                        "SELECT @r AS LockResult",
                        resource,
                    )
                    result = one(cursor)
                    if not result or result["LockResult"] < 0:
                        raise SourceConflict(
                            "The original producer is still active. Recheck later."
                        )
                yield connection
            finally:
                # Explicit release also covers drivers which pool closed connections.
                for resource in (
                    "S11:stats-import:" + identity(preparation_id),
                    "k98-legacy-output-snapshot",
                ):
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
            for resource in (
                "k98-legacy-output-snapshot",
                "S11:stats-import:" + preparation_id,
            ):
                cursor.execute("SELECT APPLOCK_MODE('public',?,'Session') AS Mode", resource)
                if one(cursor)["Mode"] != "Exclusive":
                    raise SourceConflict("Both recovery session guards are required.")
            _mutex(cursor, "account:" + self.outcomes.account)
            prep, execution, resources = self.outcomes._snapshot(cursor, preparation_id)
            self.outcomes._scope(prep)
            if self.outcomes.action(prep, execution, resources) != "resume_capture":
                raise SourceConflict("Only a completed, retained import can resume capture.")
            previous = json.loads(prep["GenerationJson"]) if prep["GenerationJson"] else {}
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
