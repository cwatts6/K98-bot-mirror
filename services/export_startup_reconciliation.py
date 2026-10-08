"""Narrow restart readiness and old-session closure; no job/provider replay."""

import json

from core.export_startup_windows import TerminatedPair
from kvk.dal.new_source_import_dal import SourceConflict, one, rows
from services.export_execution_dal import ExportExecutionDAL


class StartupReconciler:
    def __init__(self, connect, registration, host):
        self.connect, self.registration, self.host = connect, registration, host

    def _readiness(self, cursor):
        account = self.registration["account"]
        files = set()
        for definition in self.registration["legacy_configuration"].values():
            files.update(definition["destinations"])
        for pool in self.registration["pools"]:
            files.update([pool["index_file_id"], *pool["slot_file_ids"]])
        keys = [
            "account:" + account,
            "sql_snapshot:legacy_outputs",
            *("destination:" + f for f in sorted(files)),
        ]
        if len(keys) > 1024:
            raise SourceConflict("Bounded registered startup scope required.")
        cursor.execute(
            "SELECT COUNT(*) AS Held FROM dbo.ExportResource WHERE ResourceKey IN (SELECT value FROM OPENJSON(?)) AND (ActiveJobID IS NOT NULL OR ActivePreparationID IS NOT NULL OR ActiveOutputOperationID IS NOT NULL OR BlockedReason IS NOT NULL)",
            json.dumps(keys),
        )
        observed = one(cursor)
        if observed is None or type(observed.get("Held")) is not int or observed["Held"] != 0:
            raise SourceConflict(
                "Conflicting or uncertain resources require reconciliation before startup."
            )
        cursor.execute(
            "SELECT COUNT(*) AS Held FROM dbo.ExportExecutionStream WHERE AccountKey=? AND State<>'closed'",
            account,
        )
        observed = one(cursor)
        if observed is None or type(observed.get("Held")) is not int or observed["Held"] != 0:
            raise SourceConflict("Provider stream closure is unproven; no automatic replay.")

    def prepare(self, *, previous_hash=None, termination=None):
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                self._readiness(cursor)
                cursor.execute(
                    "SELECT TOP (33) SessionID,ManifestHash,Version FROM dbo.ExportExecutionSession WHERE AuthorityPrincipal=USER_NAME() AND LOWER(HostIdentity) COLLATE Latin1_General_100_BIN2=? AND State='open' ORDER BY CreatedUTC,SessionID",
                    self.host["hostname"],
                )
                sessions = rows(cursor)
                if sessions:
                    if (
                        len(sessions) != 1
                        or previous_hash is None
                        or not isinstance(termination, TerminatedPair)
                        or bytes(sessions[0]["ManifestHash"]).hex() != previous_hash
                    ):
                        raise SourceConflict(
                            "Unrecognized open authority session requires manual reconciliation."
                        )
                    version = sessions[0]["Version"]
                    if type(version) is not int or version <= 0:
                        raise SourceConflict("Exact prior session version required.")
                    termination.verify()
            finally:
                cursor.close()
        finally:
            connection.close()
        if sessions:
            result = ExportExecutionDAL(self.connect).transition(
                "session",
                SessionID=sessions[0]["SessionID"],
                Action="close",
                ExpectedVersion=sessions[0]["Version"],
            )
            if result["State"] != "closed" or result["Version"] != version + 1:
                raise SourceConflict("Previous-session closure acknowledgment differs.")
        # Recheck after closure, without altering any job, attempt, resource or input.
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                self._readiness(cursor)
                cursor.execute(
                    "SELECT COUNT(*) AS OpenSessions FROM dbo.ExportExecutionSession WHERE AuthorityPrincipal=USER_NAME() AND LOWER(HostIdentity) COLLATE Latin1_General_100_BIN2=? AND State='open'",
                    self.host["hostname"],
                )
                observed = one(cursor)
                if (
                    observed is None
                    or type(observed.get("OpenSessions")) is not int
                    or observed["OpenSessions"] != 0
                ):
                    raise SourceConflict("Authority admission changed; retain state.")
            finally:
                cursor.close()
        finally:
            connection.close()
