"""Exact SQL import receipts and evidence-gated metadata settlement. Never replay SQL."""

from __future__ import annotations

import hashlib
import json
import re

from core.sql_observation import observation
from kvk.dal.new_source_import_dal import SourceBusy, SourceConflict, one, rows, transaction
from services.export_coordination_dal import _cas, _mutex, identity


class ImportExecutionActive(SourceBusy):
    """An execution still owns its SQL session guard; not an abandoned import."""


class StatsImportOutcomeDAL:
    def __init__(self, connect, *, account, storage_owner):
        self.connect = connect
        self.account = account
        self.storage_owner = storage_owner

    def _scope(self, prep):
        if not prep or (prep["AccountKey"], prep["StorageOwner"], prep["ConsumerKind"]) != (
            self.account,
            self.storage_owner,
            "scan_data",
        ):
            raise SourceConflict(
                "Exact runtime account, storage owner and scan preparation required."
            )

    def prepare(self, claim, completed_filename):
        if claim.account != self.account:
            raise SourceConflict("Import receipt belongs to another runtime account.")
        if re.fullmatch(r"stats_[0-9a-f]{32}\.ready\.csv", completed_filename) is None:
            raise ValueError("Exact immutable input identity required.")
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + claim.account)
            _cas(
                cursor,
                "INSERT dbo.StatsImportExecution (PreparationID,CompletedFileName,OwnerID,Fence,State) "
                "OUTPUT inserted.PreparationID "
                "SELECT PreparationID,?,OwnerID,Fence,'prepared' FROM dbo.ExportPreparation "
                "WHERE PreparationID=? AND OwnerID=? AND Fence=? AND Version=? AND State='writing' "
                "AND ConsumerKind='scan_data' AND JobID IS NULL AND SpoolKey IS NULL "
                "AND AccountKey=? AND StorageOwner=?",
                completed_filename,
                claim.preparation_id,
                claim.owner,
                claim.fence,
                claim.version,
                self.account,
                self.storage_owner,
            )

    @staticmethod
    def _idle(cursor, preparation_id):
        # The SQL wrapper holds this session lock for its entire execution.
        # A transaction lock conflicts with it, including a late running SQL request.
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',"
            "@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult",
            "S11:stats-import:" + identity(preparation_id),
        )
        result = one(cursor)
        if not result or result["LockResult"] < 0:
            raise ImportExecutionActive(
                "SQL execution is still active; wait and check status again."
            )

    def read(self, preparation_id):
        with transaction(self.connect) as cursor:
            self._idle(cursor, preparation_id)
            cursor.execute(
                "SELECT AccountKey,StorageOwner,ConsumerKind FROM dbo.ExportPreparation WHERE PreparationID=?",
                identity(preparation_id),
            )
            self._scope(one(cursor))
            cursor.execute(
                "SELECT * FROM dbo.StatsImportExecution WHERE PreparationID=?",
                identity(preparation_id),
            )
            return one(cursor)

    @staticmethod
    def _snapshot(cursor, preparation_id):
        cursor.execute(
            "SELECT * FROM dbo.ExportPreparation WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
            preparation_id,
        )
        prep = one(cursor)
        cursor.execute(
            "SELECT * FROM dbo.StatsImportExecution WITH (UPDLOCK,HOLDLOCK) WHERE PreparationID=?",
            preparation_id,
        )
        execution = one(cursor)
        cursor.execute(
            "SELECT * FROM dbo.ExportResource WITH (UPDLOCK,HOLDLOCK) WHERE ActivePreparationID=? ORDER BY ResourceKey",
            preparation_id,
        )
        resources = rows(cursor)
        return prep, execution, resources

    @staticmethod
    def token(prep, execution, resources):
        # Bind confirmation to exact evidence, ownership and versions, not display text.
        document = [prep, execution, resources]
        return hashlib.sha256(
            json.dumps(document, sort_keys=True, default=str).encode()
        ).hexdigest()

    @staticmethod
    def action(prep, execution, resources):
        if not prep or not execution:
            raise SourceConflict(
                "No exact execution receipt. Retain this preparation and collect its SQL execution evidence; historical work is not automatically adopted."
            )
        if execution["Resolution"] is not None:
            return "resolved"
        if (identity(prep["OwnerID"]), prep["Fence"]) != (
            identity(execution["OwnerID"]),
            execution["Fence"],
        ):
            raise SourceConflict(
                "Execution and preparation ownership differ; preserve both records for investigation."
            )
        if (
            prep["JobID"] is not None
            or prep["SpoolKey"] is not None
            or prep["State"] not in {"writing", "committed", "uncertain"}
        ):
            raise SourceConflict(
                "Captured or exported work cannot be discarded through import resolution."
            )
        if len(resources) != 1 or resources[0]["ResourceKey"] != "sql_snapshot:legacy_outputs":
            raise SourceConflict(
                "Exact snapshot resource ownership required; no blanket resource release."
            )
        r = resources[0]
        if (identity(r["OwnerID"]), r["Fence"], r["ActiveJobID"], r["ActiveOutputOperationID"]) != (
            identity(prep["OwnerID"]),
            prep["Fence"],
            None,
            None,
        ):
            raise SourceConflict("Snapshot ownership differs; retain work for investigation.")
        state = execution["State"]
        if state in {"prepared", "rolled_back", "partial"} and prep["GenerationJson"] is not None:
            raise SourceConflict(
                "Preparation already has generation evidence; preserve it for inspection."
            )
        if state in {"prepared", "rolled_back"}:
            return "release_failure"
        if state == "partial":
            return "supersede_partial"
        if state == "completed":
            return "resume_capture"
        raise SourceConflict(
            "SQL outcome is unproven. Obtain the exact execution/transaction evidence; absence of a running process is insufficient."
        )

    def inspect(self, preparation_id):
        preparation_id = identity(preparation_id)
        with observation(), transaction(self.connect) as cursor:
            self._observe_idle(cursor, self.account)
            self._idle(cursor, preparation_id)
            prep, execution, resources = self._snapshot(cursor, preparation_id)
            self._scope(prep)
            explanation = None
            try:
                action = self.action(prep, execution, resources)
            except SourceConflict as exc:
                action, explanation = "hold", str(exc)
            return dict(
                action=action,
                token=self.token(prep, execution, resources),
                preparation=prep,
                execution=execution,
                resources=resources,
                explanation=explanation,
                captured=self.capture_completed(prep, execution, resources),
            )

    @staticmethod
    def _observe_idle(cursor, account):
        """Admit recovery reads before any row locks, including checkpoint gaps.

        The global producer guard spans SQL completion through capture. The
        account mutex also serializes admission/teardown before that guard exists.
        Every acquisition is nonblocking: observers never retain row locks while
        waiting for a producer or a different account's shared snapshot resource.
        """
        cursor.execute("SET LOCK_TIMEOUT 0;")
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock "
            "@Resource=N'k98-legacy-output-snapshot',@LockMode='Exclusive',"
            "@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult"
        )
        result = one(cursor)
        if not result or result["LockResult"] < 0:
            raise ImportExecutionActive("A SQL producer or capture is still active.")
        _mutex(cursor, "account:" + account)

    @staticmethod
    def capture_completed(prep, execution, resources):
        """SQL completion plus released snapshot and durable capture; not export success."""
        return bool(
            prep
            and execution
            and not resources
            and execution["State"] == "completed"
            and execution["Resolution"] is None
            and prep["State"] in {"captured", "materialized"}
            and prep["SpoolKey"]
            and prep["SpoolHash"]
            and prep["SpoolBytes"] > 0
            and (identity(prep["OwnerID"]), prep["Fence"])
            == (identity(execution["OwnerID"]), execution["Fence"])
        )

    def pending_failures(self, limit=16, *, after=None):
        if type(limit) is not int or not 1 <= limit <= 32:
            raise ValueError("Bounded outcome discovery required.")
        after = identity(after) if after is not None else None
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) e.PreparationID FROM dbo.StatsImportExecution e JOIN dbo.ExportPreparation p ON p.PreparationID=e.PreparationID WHERE e.Resolution IS NULL AND e.State IN ('prepared','rolled_back') AND p.State IN ('writing','uncertain') AND p.JobID IS NULL AND p.SpoolKey IS NULL AND p.AccountKey=? AND p.StorageOwner=? AND p.ConsumerKind='scan_data' ORDER BY CASE WHEN e.PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,e.PreparationID",
                limit,
                self.account,
                self.storage_owner,
                after,
            )
            return [identity(r["PreparationID"]) for r in rows(cursor)]

    def pending_recovery(self, *, after=None, limit=20):
        """Discover held/partial imports without requiring the next processing job."""
        if type(limit) is not int or not 1 <= limit <= 25:
            raise ValueError("Bounded recovery discovery required.")
        after = identity(after) if after else None
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT TOP (?) p.PreparationID FROM dbo.ExportPreparation p "
                "LEFT JOIN dbo.StatsImportExecution e ON e.PreparationID=p.PreparationID "
                "WHERE p.AccountKey=? AND p.StorageOwner=? AND p.ConsumerKind='scan_data' "
                "AND p.State IN ('writing','committed','uncertain','captured') AND p.JobID IS NULL "
                "AND e.Resolution IS NULL AND p.UpdatedUTC<DATEADD(second,-120,SYSUTCDATETIME()) "
                "AND COALESCE(JSON_VALUE(p.RequestJson,'$.request.producer.kind'),'')NOT IN ('player_stats_report','configuration_import') "
                "ORDER BY CASE WHEN p.PreparationID>CAST(? AS uniqueidentifier) THEN 0 ELSE 1 END,p.PreparationID",
                limit,
                self.account,
                self.storage_owner,
                after,
            )
            return [identity(r["PreparationID"]) for r in rows(cursor)]

    def settle(self, preparation_id, *, token, actor, reason, allow_partial=False):
        if (
            not isinstance(actor, str)
            or not 1 <= len(actor) <= 128
            or not isinstance(reason, str)
            or not 1 <= len(reason.strip()) <= 512
        ):
            raise ValueError("Bounded actor and resolution reason required.")
        preparation_id = identity(preparation_id)
        with transaction(self.connect) as cursor:
            _mutex(cursor, "account:" + self.account)
            self._idle(cursor, preparation_id)
            # A live producer's independent session guard must also have ended.
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'k98-legacy-output-snapshot',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=0; SELECT @r AS LockResult"
            )
            locked = one(cursor)
            if not locked or locked["LockResult"] < 0:
                raise SourceConflict("Producer/capture is still active; no settlement.")
            prep, execution, resources = self._snapshot(cursor, preparation_id)
            self._scope(prep)
            action = self.action(prep, execution, resources)
            if action == "resolved":
                return action
            if action not in {"release_failure", "supersede_partial"}:
                raise SourceConflict(
                    "Completed imports must finish capture, not release their output."
                )
            if token != self.token(prep, execution, resources):
                raise SourceConflict("Evidence changed since preview; inspect and preview again.")
            if action == "supersede_partial" and not allow_partial:
                raise SourceConflict(
                    "Imported data is committed but reporting is unfinished. Admin must explicitly accept retaining that partial outcome before its exact reservation can be released."
                )
            _cas(
                cursor,
                "UPDATE dbo.ExportPreparation SET State='unavailable',Version=Version+1,UpdatedUTC=SYSUTCDATETIME() OUTPUT inserted.Version WHERE PreparationID=? AND Version=?",
                preparation_id,
                prep["Version"],
            )
            r = resources[0]
            _cas(
                cursor,
                "UPDATE dbo.ExportResource SET ActivePreparationID=NULL,OwnerID=NULL,BlockedReason=NULL,Version=Version+1 OUTPUT inserted.Version WHERE ResourceKey=? AND ActivePreparationID=? AND OwnerID=? AND Fence=? AND Version=? AND ActiveJobID IS NULL AND ActiveOutputOperationID IS NULL",
                r["ResourceKey"],
                preparation_id,
                prep["OwnerID"],
                prep["Fence"],
                r["Version"],
            )
            _cas(
                cursor,
                "UPDATE dbo.StatsImportExecution SET Resolution=?,ResolvedBy=?,ResolutionReason=?,ResolvedUTC=SYSUTCDATETIME(),UpdatedUTC=SYSUTCDATETIME(),Version=Version+1 OUTPUT inserted.Version WHERE PreparationID=? AND Version=? AND Resolution IS NULL",
                action,
                actor,
                reason.strip(),
                preparation_id,
                execution["Version"],
            )
            return action
