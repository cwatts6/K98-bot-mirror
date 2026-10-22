"""Scoped durable pipeline intents, exclusion, observations and explicit decisions."""

from contextlib import contextmanager
import json
from uuid import uuid4

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows, transaction
from services.export_coordination_dal import _cas, bounded_json, identity

STAGES = (
    "import",
    "player_cache",
    "name_cache",
    "maintenance",
    "configuration",
    "target_cache",
    "export",
)


class PipelineReceiptDAL:
    def __init__(self, runtime):
        self.runtime = runtime
        self.connect = runtime.dal.connect

    def create(self, inputs, *, run_id=None):
        run_id = identity(run_id or str(uuid4()))
        with transaction(self.connect) as cursor:
            cursor.execute(
                "INSERT dbo.ProcessingPipelineRun(RunID,AccountKey,StorageOwner,InputsJson,RegistrationJson) VALUES(?,?,?,?,?)",
                run_id,
                self.runtime.account,
                self.runtime.store.storage_owner,
                bounded_json(inputs),
                self.runtime.configuration,
            )
            for stage in STAGES:
                cursor.execute(
                    "INSERT dbo.ProcessingPipelineStage(RunID,Stage,OperationID,State) VALUES(?,?,?,'not_started')",
                    run_id,
                    stage,
                    str(uuid4()),
                )
        return run_id

    def _snapshot(self, cursor, run_id):
        cursor.execute(
            "SELECT * FROM dbo.ProcessingPipelineRun WITH (UPDLOCK,HOLDLOCK) "
            "WHERE RunID=? AND AccountKey=? AND StorageOwner=?",
            identity(run_id),
            self.runtime.account,
            self.runtime.store.storage_owner,
        )
        run = one(cursor)
        if not run:
            raise SourceConflict("Pipeline is unavailable in this account and storage scope.")
        cursor.execute(
            "SELECT * FROM dbo.ProcessingPipelineStage WITH (UPDLOCK,HOLDLOCK) WHERE RunID=? ORDER BY Stage",
            identity(run_id),
        )
        stages = rows(cursor)
        if {row["Stage"] for row in stages} != set(STAGES):
            raise SourceConflict("The complete durable pipeline stage contract is required.")
        return dict(run=run, stages={row["Stage"]: row for row in stages})

    def snapshot(self, run_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, run_id)

    @contextmanager
    def guard(self, run_id):
        """Held through actual work, including cancellation drain; never an age lease."""
        connection = self.connect()
        resource = "k98-pipeline:" + identity(run_id)
        cursor = None
        acquired = False
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',"
                "@LockOwner='Session',@LockTimeout=0; SELECT @r AS LockResult",
                resource,
            )
            locked = one(cursor)
            if not locked or locked["LockResult"] < 0:
                raise SourceConflict("This pipeline still has a live worker; wait for its receipt.")
            acquired = True
            yield connection
        finally:
            try:
                if acquired:
                    cursor.execute(
                        "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", resource
                    )
            finally:
                if cursor is not None:
                    cursor.close()
                connection.close()

    def start(self, run_id, stage, *, action_id=None):
        if stage not in STAGES:
            raise ValueError("Unknown pipeline stage.")
        with transaction(self.connect) as cursor:
            state = self._snapshot(cursor, run_id)
            row = state["stages"][stage]
            if row["State"] != "not_started":
                raise SourceConflict(
                    "This stage already has an intent; inspect its durable outcome."
                )
            decisions = json.loads(row["DecisionJson"] or "[]")
            expected_action = decisions[-1]["action"] if decisions else None
            if expected_action != (identity(action_id) if action_id else None):
                raise SourceConflict("Only the confirmed continuation can dispatch this stage.")
            approved = decisions[-1].get("registration") if decisions else None
            approved = approved or json.loads(state["run"]["RegistrationJson"])
            if approved != json.loads(self.runtime.configuration):
                raise SourceConflict("Pipeline registration changed; review a new decision.")
            _cas(
                cursor,
                "UPDATE dbo.ProcessingPipelineStage SET State='running',Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE RunID=? AND Stage=? AND Version=? AND State='not_started'",
                identity(run_id),
                stage,
                row["Version"],
            )
            return identity(row["OperationID"])

    def observe(self, run_id, stage, operation, evidence, *, verified):
        with transaction(self.connect) as cursor:
            self._snapshot(cursor, run_id)
            _cas(
                cursor,
                "UPDATE dbo.ProcessingPipelineStage SET State=?,EvidenceJson=?,Version=Version+1,UpdatedUTC=SYSUTCDATETIME() "
                "OUTPUT inserted.Version WHERE RunID=? AND Stage=? AND OperationID=? AND State='running'",
                "observed" if verified else "unconfirmed",
                bounded_json(evidence),
                identity(run_id),
                stage,
                identity(operation),
            )

    def preparation(self, operation):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE AccountKey=? AND StorageOwner=? "
                "AND ConsumerKind='scan_data' AND JSON_VALUE(RequestJson,'$.request.producer.operation')=?",
                self.runtime.account,
                self.runtime.store.storage_owner,
                identity(operation),
            )
            found = rows(cursor)
            if len(found) > 1:
                raise SourceConflict("Multiple preparations match the pipeline operation.")
            return found[0] if found else None

    def configuration_read(self, operation):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM dbo.ExportPreparation WHERE AccountKey=? AND StorageOwner=? "
                "AND ConsumerKind='config' AND JSON_VALUE(RequestJson,'$.request.configuration_import.producer.operation')=?",
                self.runtime.account,
                self.runtime.store.storage_owner,
                identity(operation),
            )
            found = rows(cursor)
            if len(found) > 1:
                raise SourceConflict("Multiple configuration reads match the pipeline operation.")
            return found[0] if found else None

    def configuration_result(self, operation):
        """Follow only a verified, separately confirmed continuation association.

        The original operation remains the pipeline identity. A child cannot be
        adopted merely because its reservation was released or its config looks
        similar: the existing continuation DAL verifies its exact saved request.
        """
        from services.configuration_continuation_dal import ConfigurationContinuationDAL
        from services.configuration_producer_recovery import ConfigurationProducerDAL
        from services.configuration_read_continuation_dal import ConfigurationReadContinuationDAL

        original = self.preparation(operation)
        read = self.configuration_read(operation)
        root = original or read
        if root is None or not json.loads(root["GenerationJson"] or "{}").get(
            "configuration_continuation"
        ):
            return original
        outcomes = ConfigurationProducerDAL(
            self.connect,
            account=self.runtime.account,
            storage_owner=self.runtime.store.storage_owner,
        )
        contract = ConfigurationContinuationDAL if original else ConfigurationReadContinuationDAL
        state = contract(self.runtime, outcomes).snapshot(identity(root["PreparationID"]))
        return state["child"] if state["marker"]["choice"] == "retry" else original

    def decide(self, run_id, stage, token, marker, *, disposition=False, evidence=None):
        """Save a separate decision and preserve its predecessor, including unknown work."""
        if stage not in STAGES or (stage == "import" and not disposition and evidence is None):
            raise SourceConflict("The committed import cannot be dispatched by pipeline recovery.")
        with transaction(self.connect) as cursor:
            state = self._snapshot(cursor, run_id)
            if self.token(state) != token:
                raise SourceConflict("Pipeline evidence changed; reopen the confirmation.")
            row = state["stages"][stage]
            history = json.loads(row["DecisionJson"] or "[]")
            history.append(
                dict(
                    marker,
                    previous_operation=identity(row["OperationID"]),
                    previous_state=row["State"],
                    previous_evidence=json.loads(row["EvidenceJson"] or "null"),
                )
            )
            recorded = bounded_json(history)
            outcome = (
                "skipped"
                if disposition
                else ("observed" if evidence is not None else "not_started")
            )
            result = (
                dict(outcome="explicitly_retained_unfinished", original_outcome="unconfirmed")
                if disposition
                else evidence
            )
            _cas(
                cursor,
                "UPDATE dbo.ProcessingPipelineStage SET State=?,OperationID=?,EvidenceJson=?,DecisionJson=?,"
                "Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE RunID=? AND Stage=? AND Version=?",
                outcome,
                (
                    identity(row["OperationID"])
                    if disposition or evidence is not None
                    else identity(marker["action"])
                ),
                bounded_json(result) if result is not None else None,
                recorded,
                identity(run_id),
                stage,
                row["Version"],
            )

    def pending_recovery(self, *, after=None):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (20) r.RunID FROM dbo.ProcessingPipelineRun r WHERE AccountKey=? AND StorageOwner=? "
                "AND EXISTS(SELECT 1 FROM dbo.ProcessingPipelineStage s WHERE s.RunID=r.RunID "
                "AND s.State NOT IN ('observed','skipped')) "
                "ORDER BY CASE WHEN r.RunID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,r.RunID",
                self.runtime.account,
                self.runtime.store.storage_owner,
                identity(after) if after else None,
            )
            return [identity(row["RunID"]) for row in rows(cursor)]

    @staticmethod
    def token(state):
        # SQL datetimes/UUIDs are represented consistently for evidence-bound actions.
        return digest(json.loads(json.dumps(state, sort_keys=True, default=str))).hex()
