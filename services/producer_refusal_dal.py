"""Durable refused-stage discovery using existing immutable preparation inputs."""

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import _cas, _mutex, bounded_json, identity
from services.producer_recovery_intent import validate_inputs

_serialized_source = ContextVar("serialized_refused_producer", default=None)


def unused(attempt):
    if (
        attempt["State"] != "unavailable"
        or attempt["ExecutionState"] is not None
        or attempt["HeldCount"]
        or attempt["StreamCount"]
        or any(attempt[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID"))
    ):
        return False
    request = json.loads(attempt["RequestJson"])["request"]["producer"]
    marker = dict(
        producer_refusal_closed=dict(parent=request["parent"], action=request["operation"])
    )
    return (attempt["GenerationJson"] is None and attempt["Version"] in {2, 4}) or json.loads(
        attempt["GenerationJson"] or "{}"
    ) == marker


class ProducerRefusalDAL:
    def __init__(self, runtime):
        self.runtime, self.connect = runtime, runtime.dal.connect
        self.account, self.storage_owner = runtime.account, runtime.store.storage_owner

    def pending(self, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (100) PreparationID FROM dbo.ExportPreparation p "
                "WHERE AccountKey=? AND StorageOwner=? "
                "AND (State='unavailable' OR (State IN ('pending','preflight','sql_pending','writing','uncertain') "
                "AND UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()))) "
                "AND NOT EXISTS (SELECT 1 FROM dbo.StatsImportExecution e WHERE e.PreparationID=p.PreparationID) "
                "AND (GenerationJson IS NULL OR JSON_VALUE(GenerationJson,'$.producer_admission_closed.action') IS NOT NULL) "
                "AND JSON_VALUE(RequestJson,'$.request.producer.parent') IS NULL "
                "AND JSON_VALUE(RequestJson,'$.request.producer.kind')='stats_import' "
                "ORDER BY CASE WHEN PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,PreparationID",
                self.account,
                self.storage_owner,
                identity(after) if after else None,
            )
            return [identity(r["PreparationID"]) for r in rows(cursor)]

    def snapshot(self, source_id, *, action_id=None):
        source_id = identity(source_id)
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE PreparationID=? AND AccountKey=? AND StorageOwner=?",
                source_id,
                self.account,
                self.storage_owner,
            )
            prep = one(cursor)
            if prep is None:
                raise SourceConflict("Refused stage is outside registered custody.")
            cursor.execute(
                "SELECT ResourceKey FROM dbo.ExportPreparationResource WHERE PreparationID=? ORDER BY ResourceKey",
                source_id,
            )
            membership = [r["ResourceKey"] for r in rows(cursor)]
            cursor.execute(
                "SELECT * FROM dbo.ExportResource WHERE ActivePreparationID=? ORDER BY ResourceKey",
                source_id,
            )
            held = rows(cursor)
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportExecutionStream WHERE PreparationID=?",
                source_id,
            )
            streams = one(cursor)["n"]
            cursor.execute(
                "SELECT * FROM dbo.StatsImportExecution WHERE PreparationID=?",
                source_id,
            )
            execution = one(cursor)
            cursor.execute(
                "SELECT p.*,e.State AS ExecutionState,e.CompletedFileName,e.Resolution,"
                "(SELECT COUNT(*) FROM dbo.ExportResource r WHERE r.ActivePreparationID=p.PreparationID) AS HeldCount,"
                "(SELECT COUNT(*) FROM dbo.ExportExecutionStream s WHERE s.PreparationID=p.PreparationID) AS StreamCount "
                "FROM dbo.ExportPreparation p LEFT JOIN dbo.StatsImportExecution e ON e.PreparationID=p.PreparationID "
                "WHERE p.AccountKey=? AND p.StorageOwner=? "
                "AND JSON_VALUE(p.RequestJson,'$.request.producer.parent')=? ORDER BY p.EnqueueSequence,p.PreparationID",
                self.account,
                self.storage_owner,
                source_id,
            )
            # Stream the entire immutable attempt history into a commitment;
            # retain active work and the requested/latest closed action only.
            # Memory stays bounded without making the 101st refusal unrecoverable.
            attempts, latest_closed, requested = [], None, None
            history, attempt_count = hashlib.sha256(), 0
            document = json.loads(prep["RequestJson"])
            producer = document.get("request", {}).get("producer", {})
            while (attempt := one(cursor)) is not None:
                self._validate_attempt(document, producer, source_id, attempt)
                history.update(digest(_wire(attempt)))
                attempt_count += 1
                operation = json.loads(attempt["RequestJson"])["request"]["operation"]
                if unused(attempt):
                    latest_closed = attempt
                    if action_id is not None and operation == identity(action_id):
                        requested = attempt
                else:
                    attempts.append(attempt)
                    if len(attempts) > 1:
                        raise SourceConflict(
                            "Multiple active continuations require exact receipt recovery."
                        )
            for closed in (latest_closed, requested):
                if closed is not None and closed not in attempts:
                    attempts.append(closed)
            cursor.execute(
                "SELECT r.ResourceKey,r.ActiveJobID,r.ActivePreparationID,r.ActiveOutputOperationID,r.BlockedReason,"
                "p.ConsumerKind,JSON_VALUE(p.RequestJson,'$.request.producer.kind') AS ProducerKind,"
                "JSON_VALUE(p.RequestJson,'$.request.producer.parent') AS ProducerParent,"
                "CASE WHEN e.PreparationID IS NULL THEN 0 ELSE 1 END AS HasImportReceipt,"
                "p.State AS PreparationState,j.State AS JobState,"
                "p.AccountKey AS PreparationAccount,j.AccountKey AS JobAccount,o.AccountKey AS OperationAccount "
                "FROM dbo.ExportResource r LEFT JOIN dbo.ExportPreparation p ON p.PreparationID=r.ActivePreparationID "
                "LEFT JOIN dbo.StatsImportExecution e ON e.PreparationID=p.PreparationID "
                "LEFT JOIN dbo.ExportJob j ON j.JobID=r.ActiveJobID "
                "LEFT JOIN KVK.SourceOutputOperation o ON o.OperationID=r.ActiveOutputOperationID "
                "WHERE r.ResourceKey IN (?,?) AND (r.OwnerID IS NOT NULL OR r.BlockedReason IS NOT NULL)",
                "account:" + self.account,
                "sql_snapshot:legacy_outputs",
            )
            blockers = rows(cursor)
            queued = self._queued_blocker(cursor, source_id)
            if queued:
                blockers.append(queued)
        document = json.loads(prep["RequestJson"])
        producer = document.get("request", {}).get("producer", {})
        validate_inputs(producer.get("inputs"))
        if (
            prep["ConsumerKind"] != "scan_data"
            or (
                not execution
                and any(
                    prep[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID")
                )
            )
            or streams
            or bytes(prep["RequestHash"]) != digest(document)
            or document.get("consumer") != "scan_data"
            or document.get("storage_owner") != self.storage_owner
            or document.get("request", {}).get("kind") != "scan_data"
            or producer.get("kind") != "stats_import"
            or producer.get("parent") is not None
            or producer.get("operation") != document["request"].get("operation")
        ):
            raise SourceConflict("Exact withdrawn stage with no producer execution is required.")
        if execution:
            if execution["CompletedFileName"] != producer["inputs"]["completed_filename"]:
                raise SourceConflict("Registered import differs from the saved input.")
            phase = "execution_registered"
        else:
            phase = self._original_phase(prep, membership, held)
            if phase == "cancelled" and any(not unused(a) for a in attempts):
                raise SourceConflict(
                    "Cancelled input has an active continuation; investigate its receipt."
                )
        identity(producer["operation"])
        # Global SQL contention may belong to another registered account. Do not
        # turn it into a link that adopts another account's recovery authority.
        for blocker in blockers:
            if blocker.pop("PreparationAccount") != self.account:
                blocker["ActivePreparationID"] = None
            if blocker.pop("JobAccount") != self.account:
                blocker["ActiveJobID"] = None
            if blocker.pop("OperationAccount") != self.account:
                blocker["ActiveOutputOperationID"] = None
        return _wire(
            dict(
                preparation=prep,
                producer=producer,
                attempts=attempts,
                attempt_count=attempt_count,
                attempt_history_sha256=history.hexdigest(),
                current_registration=json.loads(self.runtime.configuration)["scan_data"],
                blockers=blockers,
                original_phase=phase,
                original_resources=held,
                original_execution=execution,
            )
        )

    @staticmethod
    def _validate_attempt(document, producer, source_id, attempt):
        child = json.loads(attempt["RequestJson"])
        expected = dict(document)
        expected["request"] = dict(document["request"])
        operation = identity(child["request"]["operation"])
        child_producer = dict(producer, parent=source_id, operation=operation)
        registration = child["request"]["producer"].get("registration_recovery")
        if registration is not None:
            expected_registration = dict(
                original_sha256=digest(document["request"]["config"]).hex(),
                approved_sha256=digest(child["request"]["config"]).hex(),
            )
            if registration != expected_registration:
                raise SourceConflict("The confirmed registration transition does not verify.")
            child_producer["registration_recovery"] = registration
            expected["request"]["config"] = child["request"]["config"]
        expected["request"].update(operation=operation, producer=child_producer)
        if (
            child != expected
            or bytes(attempt["RequestHash"]) != digest(child)
            or attempt["ConsumerKind"] != "scan_data"
            or attempt["KVK_NO"] is not None
            or (
                attempt["ExecutionState"] is not None
                and attempt["CompletedFileName"] != producer["inputs"]["completed_filename"]
            )
        ):
            raise SourceConflict("Recovery attempt differs from the retained producer inputs.")

    def _queued_blocker(self, cursor, source_id):
        from services.export_target_admission_dal import AVAILABLE_JOB_TARGETS_SQL

        # A resumed stage receives a fresh ticket. Show the oldest eligible
        # queued owner even while it has no resource claim, matching admission.
        cursor.execute(
            "SELECT TOP (1) * FROM ("
            "SELECT EnqueueSequence AS Ticket,'job' AS Kind,JobID AS QueuedID FROM dbo.ExportJob WHERE AccountKey=? AND State='ready' "
            + (AVAILABLE_JOB_TARGETS_SQL if self.runtime.dal.execution_evidence else "")
            + "UNION ALL SELECT EnqueueSequence,'preparation',PreparationID FROM dbo.ExportPreparation "
            "WHERE AccountKey=? AND State IN ('pending','sql_pending') AND PreparationID<>? "
            + (
                "UNION ALL SELECT EnqueueSequence,'output_operation',OperationID FROM KVK.SourceOutputOperation WHERE AccountKey=? AND State IN ('closing','ready') "
                if self.runtime.dal.output_operations
                else ""
            )
            + ") q ORDER BY Ticket,Kind,QueuedID",
            self.account,
            self.account,
            source_id,
            *((self.account,) if self.runtime.dal.output_operations else ()),
        )
        queued = one(cursor)
        if not queued:
            return None
        result = dict(
            ResourceKey="queue",
            ActiveJobID=None,
            ActivePreparationID=None,
            ActiveOutputOperationID=None,
            BlockedReason=None,
            ConsumerKind=None,
            ProducerKind=None,
            ProducerParent=None,
            HasImportReceipt=0,
            PreparationState=None,
            JobState=None,
            PreparationAccount=None,
            JobAccount=None,
            OperationAccount=None,
            QueueTicket=queued["Ticket"],
        )
        if queued["Kind"] == "preparation":
            cursor.execute(
                "SELECT p.ConsumerKind,p.State,JSON_VALUE(p.RequestJson,'$.request.producer.kind') AS ProducerKind,"
                "JSON_VALUE(p.RequestJson,'$.request.producer.parent') AS ProducerParent,"
                "CASE WHEN e.PreparationID IS NULL THEN 0 ELSE 1 END AS HasImportReceipt "
                "FROM dbo.ExportPreparation p LEFT JOIN dbo.StatsImportExecution e ON e.PreparationID=p.PreparationID "
                "WHERE p.PreparationID=? AND p.AccountKey=?",
                queued["QueuedID"],
                self.account,
            )
            preparation = one(cursor)
            if not preparation:
                return None
            result.update(
                ActivePreparationID=queued["QueuedID"],
                PreparationAccount=self.account,
                ConsumerKind=preparation["ConsumerKind"],
                PreparationState=preparation["State"],
                ProducerKind=preparation["ProducerKind"],
                ProducerParent=preparation["ProducerParent"],
                HasImportReceipt=preparation["HasImportReceipt"],
            )
        elif queued["Kind"] == "job":
            result.update(ActiveJobID=queued["QueuedID"], JobAccount=self.account, JobState="ready")
        else:
            result.update(ActiveOutputOperationID=queued["QueuedID"], OperationAccount=self.account)
        return result

    def _original_phase(self, prep, membership, resources, *, allow_cancel=True):
        generation = json.loads(prep["GenerationJson"] or "{}")
        cancelled = generation.get("producer_stage_cancelled")
        if cancelled is not None:
            if (
                not allow_cancel
                or set(generation) != {"producer_stage_cancelled"}
                or not isinstance(cancelled, dict)
                or set(cancelled) != {"action", "token", "version", "fence", "prior"}
                or type(cancelled["version"]) is not int
                or type(cancelled["fence"]) is not int
                or prep["Version"] != cancelled["version"] + 1
                or prep["Fence"] != cancelled["fence"] + 1
                or prep["State"] != "unavailable"
                or resources
                or not isinstance(cancelled["token"], str)
                or len(cancelled["token"]) != 64
                or any(c not in "0123456789abcdef" for c in cancelled["token"])
            ):
                raise SourceConflict("Saved-stage cancellation receipt differs.")
            identity(cancelled["action"])
            previous = dict(
                prep,
                Version=cancelled["version"],
                Fence=cancelled["fence"],
                GenerationJson=cancelled["prior"],
            )
            if (
                self._original_phase(previous, membership, resources, allow_cancel=False)
                != "refused"
            ):
                raise SourceConflict("Cancellation requires a proven refused stage.")
            return "cancelled"
        account, sql = "account:" + self.account, "sql_snapshot:legacy_outputs"
        states = {
            "pending": (1, [], []),
            "preflight": (2, [account], [account]),
            "sql_pending": (3, [account], []),
            "writing": (4, [account, sql], [sql]),
            "uncertain": (5, [account, sql], [sql]),
        }
        marker = json.loads(prep["GenerationJson"] or "{}").get("producer_admission_closed")
        if prep["State"] == "unavailable":
            if resources:
                raise SourceConflict("Closed admission still has reservations.")
            if marker is not None:
                previous = states.get(marker.get("state"))
                if (
                    not previous
                    or set(json.loads(prep["GenerationJson"])) != {"producer_admission_closed"}
                    or marker.get("version") != previous[0]
                    or prep["Version"] != previous[0] + 1
                    or membership != previous[1]
                    or prep["Fence"] != marker.get("fence", -2) + 1
                    or set(marker) != {"action", "token", "state", "version", "fence"}
                ):
                    raise SourceConflict("Admission closure checkpoint does not verify.")
                identity(marker["action"])
                if (
                    not isinstance(marker["token"], str)
                    or len(marker["token"]) != 64
                    or any(c not in "0123456789abcdef" for c in marker["token"])
                ):
                    raise SourceConflict("Admission closure token is malformed.")
            elif (
                prep["GenerationJson"] is not None
                or prep["Version"] not in {2, 4, 5}
                or membership != {2: [], 4: [account], 5: [account, sql]}.get(prep["Version"])
            ):
                raise SourceConflict("Refusal checkpoint does not verify.")
            return "refused"
        expected = states.get(prep["State"])
        if (
            not expected
            or prep["GenerationJson"] is not None
            or prep["Version"] != expected[0]
            or membership != expected[1]
            or [r["ResourceKey"] for r in resources] != expected[2]
            or any(
                identity(r["OwnerID"]) != identity(prep["OwnerID"])
                or r["Fence"] != prep["Fence"]
                or r["ActiveJobID"] is not None
                or r["ActiveOutputOperationID"] is not None
                for r in resources
            )
        ):
            raise SourceConflict("Exact unstarted admission ownership is required.")
        return "unstarted"

    def cancel_saved_stage(self, source_id, token, action_id):
        """Close an unwanted, proven refused input; never release other work."""
        self._require_serialized(source_id)
        state = self.snapshot(source_id)
        if (
            digest(state).hex() != token
            or state["original_phase"] != "refused"
            or any(not unused(a) for a in state["attempts"])
        ):
            raise SourceConflict("Only a proven unstarted input can be cancelled.")
        from services.stats_import_outcome_dal import StatsImportOutcomeDAL

        with transaction(self.connect) as cursor:
            StatsImportOutcomeDAL._idle(cursor, source_id)
            _mutex(cursor, "account:" + self.account)
            _mutex(cursor, "sql_snapshot:legacy_outputs")
            prep, execution, resources = StatsImportOutcomeDAL._snapshot(cursor, source_id)
            before = state["preparation"]
            if (
                execution
                or resources
                or not prep
                or prep["State"] != "unavailable"
                or prep["Version"] != before["Version"]
                or prep["Fence"] != before["Fence"]
                or prep["RequestJson"] != before["RequestJson"]
                or prep["GenerationJson"] != before["GenerationJson"]
                or (prep["AccountKey"], prep["StorageOwner"]) != (self.account, self.storage_owner)
                or any(
                    prep[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID")
                )
            ):
                raise SourceConflict("Saved stage changed; review its current execution evidence.")
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportExecutionStream WHERE PreparationID=?",
                source_id,
            )
            if one(cursor)["n"]:
                raise SourceConflict("Provider stream prevents cancellation.")
            marker = dict(
                producer_stage_cancelled=dict(
                    action=identity(action_id),
                    token=token,
                    version=prep["Version"],
                    fence=prep["Fence"],
                    prior=prep["GenerationJson"],
                )
            )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET GenerationJson=?,Version=Version+1,Fence=Fence+1,"
                "UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND Version=? AND State='unavailable'",
                bounded_json(marker),
                identity(source_id),
                prep["Version"],
            )

    def close_admission(self, source_id, token, action_id):
        """Fence an original typed stats admission only before SQL registration."""
        self._require_serialized(source_id)
        state = self.snapshot(source_id)
        if digest(state).hex() != token or state["original_phase"] != "unstarted":
            raise SourceConflict("Admission evidence changed; review the current incident.")
        with transaction(self.connect) as cursor:
            from services.stats_import_outcome_dal import StatsImportOutcomeDAL

            StatsImportOutcomeDAL._idle(cursor, source_id)
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',"
                "@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult"
            )
            if one(cursor)["LockResult"] < 0:
                raise SourceConflict(
                    "The producer is still running; its admission cannot be cancelled."
                )
            _mutex(cursor, "account:" + self.account)
            _mutex(cursor, "sql_snapshot:legacy_outputs")
            prep, execution, resources = StatsImportOutcomeDAL._snapshot(cursor, source_id)
            if (
                not prep
                or execution
                or prep["Version"] != state["preparation"]["Version"]
                or prep["Fence"] != state["preparation"]["Fence"]
                or prep["State"] != state["preparation"]["State"]
                or _wire(resources) != state["original_resources"]
            ):
                raise SourceConflict("SQL registration exists; use its exact receipt recovery.")
            cursor.execute(
                "SELECT ResourceKey FROM dbo.ExportPreparationResource WHERE PreparationID=? ORDER BY ResourceKey",
                source_id,
            )
            membership = [r["ResourceKey"] for r in rows(cursor)]
            if self._original_phase(prep, membership, resources) != "unstarted":
                raise SourceConflict("Admission is already closed.")
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportExecutionStream WHERE PreparationID=?",
                source_id,
            )
            if one(cursor)["n"] or (
                prep["AccountKey"],
                prep["StorageOwner"],
                prep["ConsumerKind"],
            ) != (self.account, self.storage_owner, "scan_data"):
                raise SourceConflict("Original admission scope or execution changed.")
            request = json.loads(prep["RequestJson"])
            producer = request.get("request", {}).get("producer", {})
            validate_inputs(producer.get("inputs"))
            if (
                producer.get("kind") != "stats_import"
                or producer.get("parent")
                or bytes(prep["RequestHash"]) != digest(request)
            ):
                raise SourceConflict("Original typed producer request is required.")
            marker = dict(
                producer_admission_closed=dict(
                    action=identity(action_id),
                    token=token,
                    state=prep["State"],
                    version=prep["Version"],
                    fence=prep["Fence"],
                )
            )
            if any(r["ResourceKey"] == "account:" + self.account for r in resources):
                self.runtime.dal._execution_gate(cursor, self.account)
            for r in resources:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,"
                    "Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? AND Version=?",
                    r["ResourceKey"],
                    source_id,
                    prep["OwnerID"],
                    prep["Fence"],
                    r["Version"],
                )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='unavailable',OwnerID=COALESCE(OwnerID,?),Fence=Fence+1,"
                "Version=Version+1,GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND Version=?",
                identity(action_id),
                bounded_json(marker),
                source_id,
                prep["Version"],
            )

    @contextmanager
    def serialized(self, source_id):
        """Exclude a live recovery dispatcher, including its drained worker threads."""
        connection = self.connect()
        connection.autocommit = True
        cursor = connection.cursor()
        resource = "k98-producer-recovery:" + identity(source_id)
        acquired = False
        try:
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',"
                "@LockOwner='Session',@LockTimeout=0; SELECT @r AS LockResult",
                resource,
            )
            acquired = one(cursor)["LockResult"] >= 0
            if not acquired:
                from services.stats_import_outcome_dal import ImportExecutionActive

                raise ImportExecutionActive("The confirmed continuation is still running.")
            token = _serialized_source.set((self, identity(source_id)))
            try:
                yield
            finally:
                _serialized_source.reset(token)
        finally:
            try:
                if acquired:
                    cursor.execute(
                        "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", resource
                    )
            finally:
                cursor.close()
                connection.close()

    def reserve(self, source_id, action_id, *, use_current_registration=False):
        """A stable request is also a tombstone against late action dispatch."""
        self._require_serialized(source_id)
        state = self.snapshot(source_id, action_id=action_id)
        for attempt in state["attempts"]:
            if json.loads(attempt["RequestJson"])["request"]["operation"] == identity(action_id):
                return identity(attempt["PreparationID"])
        if state["original_phase"] == "cancelled":
            raise SourceConflict("This saved input was permanently cancelled; it cannot resume.")
        document = json.loads(state["preparation"]["RequestJson"])
        request = dict(document["request"])
        request.update(
            operation=identity(action_id),
            producer=dict(
                state["producer"], parent=identity(source_id), operation=identity(action_id)
            ),
        )
        if use_current_registration:
            request["config"] = state["current_registration"]
            request["producer"]["registration_recovery"] = dict(
                original_sha256=digest(document["request"]["config"]).hex(),
                approved_sha256=digest(request["config"]).hex(),
            )
        return self.runtime.dal.request(
            account=self.account,
            consumer="scan_data",
            kvk_no=None,
            request=request,
            storage_owner=self.storage_owner,
            actor="recovery:" + identity(action_id),
            reason="Resume confirmed unstarted SQL stage",
        )

    def close_unused(self, source_id, action_id):
        """Called only under serialized(). Fence an attempt that never registered SQL.

        Both SQL execution guards and exact row ownership are checked in the same
        transaction as release. A receipt, stream or generation excludes this path.
        The durable marker prevents a late dispatcher from reusing this action.
        """
        self._require_serialized(source_id)
        state = self.snapshot(source_id, action_id=action_id)
        candidates = [
            p
            for p in state["attempts"]
            if json.loads(p["RequestJson"])["request"]["operation"] == identity(action_id)
        ]
        if len(candidates) != 1:
            raise SourceConflict("One exact continuation reservation is required.")
        candidate = candidates[0]
        identifier = identity(candidate["PreparationID"])
        marker = dict(
            producer_refusal_closed=dict(parent=identity(source_id), action=identity(action_id))
        )
        with transaction(self.connect) as cursor:
            from services.stats_import_outcome_dal import StatsImportOutcomeDAL

            StatsImportOutcomeDAL._idle(cursor, identifier)
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',"
                "@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult"
            )
            if one(cursor)["LockResult"] < 0:
                raise SourceConflict("A producer still holds the SQL execution guard.")
            _mutex(cursor, "account:" + self.account)
            _mutex(cursor, "sql_snapshot:legacy_outputs")
            prep, execution, resources = StatsImportOutcomeDAL._snapshot(cursor, identifier)
            cursor.execute(
                "SELECT COUNT(*) AS n FROM dbo.ExportExecutionStream WHERE PreparationID=?",
                identifier,
            )
            streams = one(cursor)["n"]
            if (
                not prep
                or prep["Version"] != candidate["Version"]
                or prep["AccountKey"] != self.account
                or prep["StorageOwner"] != self.storage_owner
                or prep["ConsumerKind"] != "scan_data"
                or execution
                or streams
                or any(
                    prep[k] is not None for k in ("SpoolKey", "SpoolBytes", "SpoolHash", "JobID")
                )
            ):
                return False
            if prep["GenerationJson"] is not None:
                return (
                    prep["State"] == "unavailable"
                    and not resources
                    and json.loads(prep["GenerationJson"]) == marker
                )
            if prep["State"] not in {
                "pending",
                "preflight",
                "sql_pending",
                "writing",
                "uncertain",
                "unavailable",
            }:
                return False
            for r in resources:
                if (
                    r["ResourceKey"]
                    not in {"account:" + self.account, "sql_snapshot:legacy_outputs"}
                    or identity(r["OwnerID"]) != identity(prep["OwnerID"])
                    or r["Fence"] != prep["Fence"]
                    or r["ActiveJobID"] is not None
                    or r["ActiveOutputOperationID"] is not None
                ):
                    raise SourceConflict("Continuation ownership changed; release refused.")
            if any(r["ResourceKey"] == "account:" + self.account for r in resources):
                self.runtime.dal._execution_gate(cursor, self.account)
            for r in resources:
                _cas(
                    cursor,
                    "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,"
                    "Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? "
                    "AND OwnerID=? AND Fence=? AND Version=?",
                    r["ResourceKey"],
                    identifier,
                    prep["OwnerID"],
                    prep["Fence"],
                    r["Version"],
                )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='unavailable',OwnerID=COALESCE(OwnerID,?),"
                "Fence=Fence+1,Version=Version+1,GenerationJson=?,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE PreparationID=? AND Version=?",
                identity(action_id),
                bounded_json(marker),
                identifier,
                prep["Version"],
            )
            return True

    def _require_serialized(self, source_id):
        if _serialized_source.get() != (self, identity(source_id)):
            raise SourceConflict("Exact continuation dispatcher exclusion required.")
