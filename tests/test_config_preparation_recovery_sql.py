"""Opt-in real SQL, exclusively session-local #tables in the approved fixture.

No permanent DDL/DML, provider calls, retained-data changes or database creation.
The authoritative column/check definitions are reused; FKs to absent fixture
dependencies are omitted. This proves queries/CAS/rollback, not production rights
or multi-session contention on permanent objects.
"""

from dataclasses import replace
from datetime import datetime
import os
from pathlib import Path
import re
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.config_preparation_recovery_dal import ConfigPreparationRecoveryDAL
from services.export_execution_dal import ExportExecutionDAL
from tests.test_config_preparation_recovery import fixture

pytestmark = pytest.mark.skipif(
    os.environ.get("K98_CONFIG_RECOVERY_SQL") != "1",
    reason="explicit local temporary-table SQL fixture",
)
TABLES = (
    "ExportPreparation",
    "ExportPreparationResource",
    "ExportResource",
    "ExportExecutionStream",
    "ExportProviderRequest",
    "ExportProviderRequestEvent",
    "ExportContainedTarget",
)
SERVER = r"localhost\K98DEV"
DATABASE = "master"
SQL_SOURCE = Path(os.environ.get("K98_CONFIG_RECOVERY_SQL_SOURCE", "C:/K98-bot-SQL-Server"))


def local_sql(sql):
    for name in sorted(TABLES, key=len, reverse=True):
        sql = re.sub(r"\bdbo\." + name + r"\b", "#" + name, sql)
    return sql


@pytest.fixture
def sql_fixture():
    import pyodbc

    native = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER="
        + SERVER
        + ";DATABASE="
        + DATABASE
        + ";Trusted_Connection=yes;TrustServerCertificate=yes",
        autocommit=True,
        timeout=5,
    )
    try:
        server_identity, database_identity = tuple(
            native.execute(
                "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()"
            ).fetchone()
        )
        assert database_identity == DATABASE
        for name in TABLES:
            raw = (SQL_SOURCE / "sql_schema" / f"dbo.{name}.Table.sql").read_text(
                encoding="utf-8-sig"
            )
            raw = "\n".join(line for line in raw.splitlines() if "FOREIGN KEY" not in line)
            raw = re.sub(r",\s*\);", "\n);", raw)
            native.execute(local_sql(raw))

        class Cursor:
            def __init__(self):
                self.inner = native.cursor()

            def execute(self, sql, *args):
                self.inner.execute(local_sql(sql), *args)
                return self

            def __getattr__(self, name):
                return getattr(self.inner, name)

        class Connection:
            @property
            def autocommit(self):
                return native.autocommit

            @autocommit.setter
            def autocommit(self, value):
                native.autocommit = value

            def cursor(self):
                return Cursor()

            def commit(self):
                native.commit()

            def rollback(self):
                native.rollback()

            def close(self):
                pass  # Test owns the session-local tables until teardown.

        def connect():
            native.autocommit = False
            return Connection()

        service, snapshot, stream, _ = fixture()
        read_reference = service.verifier.store.read_reference
        service.verifier.store.read_reference = lambda ref, sha: read_reference(
            str(ref).lower(), sha
        )
        service.target = replace(service.target, server=server_identity, database=DATABASE)
        snapshot["preparation"].update(
            EnqueueSequence=10,
            Actor="test",
            Reason="temporary fixture",
            CreatedUTC=datetime(2026, 10, 15),
            UpdatedUTC=datetime(2026, 10, 15),
        )
        stream.update(
            SessionID=str(uuid4()),
            SnapshotHash=b"s" * 32,
            CreatedUTC=datetime(2026, 10, 15),
            ClosedUTC=datetime(2026, 10, 15),
        )
        binary = {
            "RequestHash",
            "RegistrationHash",
            "SnapshotHash",
            "ClosureHash",
            "EventDigest",
            "SpoolHash",
        }

        def insert(name, row):
            cols = list(row)
            values = [
                bytes.fromhex(row[k]) if k in binary and isinstance(row[k], str) else row[k]
                for k in cols
            ]
            placeholders = ["CAST(? AS binary(32))" if k in binary else "?" for k in cols]
            native.execute(
                f"INSERT INTO #{name} ({','.join(cols)}) VALUES ({','.join(placeholders)})", *values
            )

        insert("ExportPreparation", snapshot["preparation"])
        for row in snapshot["resources"]:
            insert("ExportResource", row | {"ResourceKind": row["ResourceKey"].split(":")[0]})
            insert(
                "ExportPreparationResource",
                dict(PreparationID=service.target.preparation_id, ResourceKey=row["ResourceKey"]),
            )
        insert("ExportExecutionStream", stream)
        service.dal = ConfigPreparationRecoveryDAL(connect)
        service.execution = service.verifier.dal = ExportExecutionDAL(connect)
        yield service, native
    finally:
        native.close()  # SQL Server removes only this session's temporary tables.


def test_real_sql_settlement_preserves_stream_and_membership(sql_fixture):
    service, sql = sql_fixture
    assert service.dal.pending_recovery(account="account-a", storage_owner="fixture") == [
        service.target.preparation_id
    ]
    data = service.dal.target_data(
        service.target.preparation_id, account="account-a", storage_owner="fixture"
    )
    assert len(data["resources"]) == 2
    assert data["stream_ids"] == list(service.target.stream_ids)
    with pytest.raises(SourceConflict):
        service.dal.target_data(
            service.target.preparation_id, account="other", storage_owner="fixture"
        )
    report = service.inspect()
    service.apply(
        approved_snapshot_sha256=report["snapshot_sha256"], actor="test", reason="verified"
    )
    assert tuple(sql.execute("SELECT State,Version FROM #ExportPreparation").fetchone()) == (
        "unavailable",
        4,
    )
    assert (
        sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL OR BlockedReason IS NOT NULL"
        ).fetchval()
        == 0
    )
    assert sql.execute("SELECT COUNT(*) FROM #ExportPreparationResource").fetchval() == 2
    assert sql.execute("SELECT State FROM #ExportExecutionStream").fetchval() == "closed"
    assert sql.execute("SELECT COUNT(*) FROM #ExportProviderRequest").fetchval() == 0
    assert service.dal.pending_recovery(account="account-a", storage_owner="fixture") == []
    assert (
        service.dal.target_data(
            service.target.preparation_id, account="account-a", storage_owner="fixture"
        )["resources"]
        == []
    )


@pytest.mark.parametrize(
    "purpose,kind,terminal,fresh,rejected",
    [
        ("probe", "read", "unknown", False, False),
        ("probe", "read", "unknown", True, True),
        ("mutation", "mutation", "unknown", False, True),
        ("probe", "mutation", "unknown", False, True),
        ("mutation", "read", "unknown", False, True),
        # Historical read-only prefixes are admissible after the separate closed
        # membership gate; they never substitute for a successful fresh probe.
        ("probe", "read", "prepared", False, False),
        ("probe", "read", "dispatch_intent", False, False),
        ("probe", "read", "prepared", True, True),
        ("probe", "read", "dispatch_intent", True, True),
        ("probe", "read", None, False, True),
        ("probe", "mutation", "prepared", False, True),
        ("probe", "mutation", "dispatch_intent", False, True),
        ("mutation", "read", "prepared", False, True),
        ("mutation", "read", "dispatch_intent", False, True),
        ("probe", "read", "succeeded", True, False),
        ("mutation", "mutation", "not_sent", False, False),
    ],
)
def test_real_sql_history_gate_distinguishes_failed_reads_from_writes(
    sql_fixture, purpose, kind, terminal, fresh, rejected
):
    _, sql = sql_fixture
    source = (
        SQL_SOURCE / "sql_schema/dbo.usp_ExportReconciliationProofIssue.StoredProcedure.sql"
    ).read_text(encoding="utf-8-sig")
    start = " IF EXISTS (SELECT 1 FROM @Members m JOIN dbo.ExportProviderRequest r ON r.StreamID=m.StreamID"
    gate = source[source.index(start) :].split("  THROW 51700,'Request gaps", 1)[0].strip()
    expression = gate.removeprefix("IF ")
    for name in ("ExportExecutionStream", "ExportProviderRequestEvent", "ExportProviderRequest"):
        expression = expression.replace("dbo." + name, name)
    expression = expression.replace("@Members", "Members")
    identifier = str(uuid4())
    statement = """
        DECLARE @ProbeID uniqueidentifier=?;
        WITH Members AS (SELECT CAST(? AS uniqueidentifier) AS StreamID),
        ExportExecutionStream AS (SELECT StreamID,CAST(? AS varchar(16)) AS Purpose FROM Members),
        ExportProviderRequest AS (SELECT StreamID,1 AS RequestID,CAST(? AS varchar(16)) AS RequestKind FROM Members),
        ExportProviderRequestEvent AS (SELECT 1 AS RequestID,CAST(? AS varchar(32)) AS State)
        SELECT CASE WHEN """ + expression + " THEN 1 ELSE 0 END"
    result = sql.execute(
        statement, identifier if fresh else str(uuid4()), identifier, purpose, kind, terminal
    ).fetchval()
    assert bool(result) is rejected


def test_real_sql_changed_snapshot_refuses_without_release(sql_fixture):
    service, sql = sql_fixture
    report = service.inspect()
    sql.execute("UPDATE #ExportResource SET Version=Version+1 WHERE ResourceKind='destination'")
    sql.commit()
    with pytest.raises(SourceConflict):
        service.dal.settle(service.target, report["snapshot"], {"actor": "test", "reason": "race"})
    assert (
        sql.execute("SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL").fetchval()
        == 2
    )
    assert sql.execute("SELECT State FROM #ExportPreparation").fetchval() == "uncertain"


def test_real_sql_partial_cas_failure_rolls_back_every_release(sql_fixture, monkeypatch):
    import services.config_preparation_recovery_dal as module

    service, sql = sql_fixture
    report = service.inspect()
    original = module._cas
    calls = []

    def fail_last(cursor, statement, *args):
        calls.append(statement)
        if len(calls) == 3:
            raise SourceConflict("injected final resource race")
        return original(cursor, statement, *args)

    monkeypatch.setattr(module, "_cas", fail_last)
    with pytest.raises(SourceConflict):
        service.dal.settle(
            service.target, report["snapshot"], {"actor": "test", "reason": "rollback"}
        )
    assert tuple(sql.execute("SELECT State,Version FROM #ExportPreparation").fetchone()) == (
        "uncertain",
        3,
    )
    assert (
        sql.execute(
            "SELECT COUNT(*) FROM #ExportResource WHERE OwnerID IS NOT NULL AND BlockedReason IS NOT NULL"
        ).fetchval()
        == 2
    )
