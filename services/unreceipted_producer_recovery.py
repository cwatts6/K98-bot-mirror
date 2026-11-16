"""Explicit disposition of legacy partial SQL work whose outcome remains unknown.

This never proves rollback, reconstructs a checkpoint, or dispatches a producer.
Exact ownership and independent worker exclusion permit only the reviewed hold's
closure. A fresh configuration is a separate, typed, confirmed operation.
"""

import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.import_capture_recovery_dal import ImportCaptureRecoveryDAL
from services.stats_import_outcome_dal import StatsImportOutcomeDAL

MARKER = "unconfirmed_producer_disposition"


def retained_unknown(prep, execution, resources):
    generation = json.loads(prep.get("GenerationJson") or "{}")
    marker = generation.get(MARKER)
    if marker is None:
        return False
    if (
        execution
        or resources
        or prep["State"] != "unavailable"
        or prep["JobID"]
        or prep["SpoolKey"]
        or not isinstance(marker, dict)
        or set(marker)
        != {"action", "token", "reason", "original_fence", "original_version", "request_sha256"}
        or marker["request_sha256"] != bytes(prep["RequestHash"]).hex()
        or type(marker["original_fence"]) is not int
        or prep["Fence"] != marker["original_fence"] + 1
        or type(marker["original_version"]) is not int
        or prep["Version"] <= marker["original_version"]
        or not isinstance(marker["token"], str)
        or re.fullmatch(r"[0-9a-f]{64}", marker["token"]) is None
    ):
        raise SourceConflict(
            "The unknown-outcome disposition does not verify its exact fence and release."
        )
    identity(marker["action"])
    return True


class UnreceiptedProducerDAL(StatsImportOutcomeDAL):
    @staticmethod
    def action(prep, execution, resources):
        request = json.loads(prep["RequestJson"])
        if bytes(prep["RequestHash"]) != digest(request) or (
            request.get("consumer"),
            request.get("storage_owner"),
            request.get("kvk_no"),
            request.get("request", {}).get("kind"),
            prep["KVK_NO"],
        ) != ("scan_data", prep["StorageOwner"], None, "scan_data", None):
            raise SourceConflict("The original immutable producer request cannot be verified.")
        producer = request.get("request", {}).get("producer", {})
        if not isinstance(producer, dict):
            raise SourceConflict("Legacy producer metadata is malformed.")
        if (
            execution
            or producer.get("kind") == "stats_import"
            or producer.get("atomic_checkpoint") == 1
        ):
            raise SourceConflict("This typed producer has a stronger existing recovery contract.")
        if retained_unknown(prep, execution, resources):
            return "retained_unknown"
        generation = json.loads(prep["GenerationJson"] or "{}")
        if generation.get("completion") == "committed" or any(
            prep[k] is not None for k in ("JobID", "SpoolKey", "SpoolHash", "SpoolBytes")
        ):
            raise SourceConflict("Committed or captured output needs its own outcome verification.")
        if prep["State"] not in {"writing", "uncertain"} or len(resources) != 1:
            raise SourceConflict("Only an exact retained legacy SQL hold can be disposed.")
        resource = resources[0]
        if (
            resource["ResourceKey"],
            identity(resource["ActivePreparationID"]),
            identity(resource["OwnerID"]),
            resource["Fence"],
            resource["ActiveJobID"],
            resource["ActiveOutputOperationID"],
        ) != (
            "sql_snapshot:legacy_outputs",
            identity(prep["PreparationID"]),
            identity(prep["OwnerID"]),
            prep["Fence"],
            None,
            None,
        ):
            raise SourceConflict("Foreign or changed reservation ownership must be preserved.")
        return "retain_unknown"

    def pending_recovery(self, *, after=None, limit=20):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) p.PreparationID FROM dbo.ExportPreparation p "
                "WHERE AccountKey=? AND StorageOwner=? AND ConsumerKind='scan_data' "
                "AND State IN ('writing','uncertain') AND JobID IS NULL AND SpoolKey IS NULL "
                "AND COALESCE(JSON_VALUE(RequestJson,'$.request.producer.kind'),'')<>'stats_import' "
                "AND COALESCE(JSON_VALUE(RequestJson,'$.request.producer.atomic_checkpoint'),'')<>'1' "
                "AND NOT EXISTS(SELECT 1 FROM dbo.StatsImportExecution e WHERE e.PreparationID=p.PreparationID) "
                "ORDER BY CASE WHEN p.PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,p.PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["PreparationID"]) for row in rows(cursor)]

    def close(self, source_id, token, action_id, reason):
        if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 512:
            raise SourceConflict("A bounded explicit disposition reason is required.")
        with ImportCaptureRecoveryDAL(self).session(source_id) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("BEGIN TRANSACTION")
                _mutex(cursor, "account:" + self.account)
                prep, execution, resources = self._snapshot(cursor, identity(source_id))
                self._scope(prep)
                if (
                    self.action(prep, execution, resources) != "retain_unknown"
                    or self.token(prep, execution, resources) != token
                ):
                    raise SourceConflict(
                        "Legacy producer evidence changed; review its current outcome."
                    )
                cursor.execute(
                    "SELECT TOP (1) StreamID FROM dbo.ExportExecutionStream WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
                    identity(source_id),
                )
                if one(cursor):
                    raise SourceConflict(
                        "Provider execution must remain in its own recovery workflow."
                    )
                generation = json.loads(prep["GenerationJson"] or "{}")
                generation[MARKER] = dict(
                    action=identity(action_id),
                    token=token,
                    reason=reason.strip(),
                    original_fence=prep["Fence"],
                    original_version=prep["Version"],
                    request_sha256=bytes(prep["RequestHash"]).hex(),
                )
                resource = resources[0]
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,Version=Version+1 "
                    "OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? AND Version=? "
                    "AND ActiveJobID IS NULL AND ActiveOutputOperationID IS NULL",
                    resource["ResourceKey"],
                    identity(source_id),
                    prep["OwnerID"],
                    prep["Fence"],
                    resource["Version"],
                )
                _cas(
                    cursor,
                    "UPDATE dbo.ExportPreparation SET State='unavailable',Fence=Fence+1,Version=Version+1,"
                    "GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version "
                    "WHERE PreparationID=? AND Version=? AND Fence=? AND JobID IS NULL AND SpoolKey IS NULL",
                    bounded_json(generation),
                    identity(source_id),
                    prep["Version"],
                    prep["Fence"],
                )
                cursor.execute("COMMIT TRANSACTION")
            except BaseException:
                try:
                    cursor.execute("IF @@TRANCOUNT>0 ROLLBACK")
                except Exception:
                    pass
                raise
            finally:
                cursor.close()


class UnreceiptedProducerRecovery:
    kind = "unreceipted_producer"

    def __init__(self, dal, *, configuration=None):
        self.dal = dal
        self.configuration = configuration

    def pending_recovery(self, *, after=None):
        return self.dal.pending_recovery(after=after)

    def inspect(self, source_id):
        preview = self.dal.inspect(source_id)
        resolved = preview["action"] == "retained_unknown"
        actions = {}
        if preview["action"] == "retain_unknown":
            actions["retain_unknown"] = dict(
                label="Preserve unknown result & release",
                review_details=True,
                review_title="Review the legacy request and current outputs",
                review_description="The original transaction outcome is unknown. Review the retained request and output registration before choosing an explicit disposition.",
                check="Confirm the legacy producer's original result cannot be established and should remain explicitly unknown. Any partial SQL changes are retained. This does not verify configuration, reports or caches.",
                effect="Exclude both original producer/import sessions, reject provider streams and foreign ownership, fence this exact obsolete preparation and release only its SQL snapshot hold. A fresh configuration requires a separate reviewed decision.",
            )
        evidence = dict(
            title="Legacy producer without a completion receipt",
            outcome="unknown_result_retained" if resolved else "outcome_unconfirmed",
            explanation=(
                "The explicit unknown-outcome disposition and exact release verify. Original SQL effects remain unknown and intact; no operation was replayed."
                if resolved
                else preview["explanation"]
                or "The original request survives but has no atomic outcome contract. Collect its input, SQL transaction logs and configuration history if available, or explicitly retain its unknown result below."
            ),
            original_request_sha256=bytes(preview["preparation"]["RequestHash"]).hex(),
            original_partial_result_recorded=bool(preview["preparation"]["GenerationJson"]),
            actions=actions,
        )
        if resolved:
            evidence["recovery_links"] = [
                dict(
                    label="Review fresh configuration decision",
                    kind="legacy_configuration_continuation",
                    source_id=source_id,
                )
            ]
        return evidence, preview["token"], resolved

    def review_details(self, source_id, action, token):
        from services.producer_recovery_review import registration_review

        preview = self.dal.inspect(source_id)
        if action != "retain_unknown" or preview["action"] != action or preview["token"] != token:
            raise SourceConflict("Legacy producer review changed; reopen the incident.")
        if self.configuration is None:
            raise SourceConflict("Current authenticated registration is required for review.")
        return registration_review(
            dict(
                preparation=preview["preparation"],
                current_registration=json.loads(self.configuration)["scan_data"],
                producer={"inputs": {"operation": "Preserve unknown result; no producer replay"}},
            )
        )

    def execute(self, source_id, action, token, actor, reason):
        if action != "retain_unknown" or not actor.startswith("recovery:"):
            raise SourceConflict("Confirmed unknown-outcome disposition required.")
        self.dal.close(source_id, token, actor.removeprefix("recovery:"), reason)

    def reconcile(self, source_id, action):
        preview = self.dal.inspect(source_id)
        marker = json.loads(preview["preparation"]["GenerationJson"] or "{}").get(MARKER)
        if (
            preview["action"] == "retained_unknown"
            and marker["action"] == identity(action["ActionID"])
            and marker["token"] == action["EvidenceHash"]
        ):
            return "verified"
        if preview["token"] != action["EvidenceHash"]:
            return "not_applied"
        self.execute(
            source_id,
            action["ActionKind"],
            action["EvidenceHash"],
            "recovery:" + identity(action["ActionID"]),
            action["Reason"],
        )
        return "verified" if self.dal.inspect(source_id)["action"] == "retained_unknown" else None
