"""Lab-only SQL-authenticated full application observation and owned reuse.

The original database is snapshotted. Historical migration rows and business
work are preserved. This does not certify the complete production release path.
"""

import base64
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import secrets
import subprocess
import sys
import time
from typing import Any

HISTORY_SQL = """SELECT MigrationId,MigrationFile,ChecksumSha256,AppliedAtUtc,
GitCommit,DeploymentId,Status FROM dbo.SchemaMigrationHistory ORDER BY MigrationId"""
IDENTITY_SQL = """SELECT DB_ID() AS database_id,object_id AS sequence_object_id,
create_date AS sequence_created,modify_date AS sequence_modified,
CONVERT(bigint,current_value) AS generation FROM sys.sequences
WHERE object_id=OBJECT_ID('dbo.P02ObservationGeneration')"""
GUARD_SQL = """IF DB_NAME()<>'ROK_TRACKER' OR DB_ID()<>12 OR NOT EXISTS(
SELECT 1 FROM sys.databases WHERE database_id=12 AND name='ROK_TRACKER'
AND create_date=CONVERT(datetime,'2026-11-17T17:34:47.357',126)
AND state=0 AND is_read_only=0 AND source_database_id IS NULL)
THROW 51973,'Preserved lab incarnation changed.',1;
IF EXISTS(SELECT 1 FROM sys.dm_exec_sessions s LEFT JOIN sys.dm_exec_requests r
ON r.session_id=s.session_id WHERE s.is_user_process=1 AND s.session_id<>@@SPID
AND (s.database_id=12 OR r.database_id=12))
THROW 51973,'Other lab sessions remain; no forced cleanup.',1;"""


def encode(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(connection, statement):
    cursor = connection.cursor()
    try:
        cursor.execute(statement)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchmany(501)
        if len(rows) > 500 or cursor.nextset():
            raise ValueError("Prerequisite query result exceeded its bound")
        return [dict(zip(columns, row, strict=True)) for row in rows]
    finally:
        cursor.close()


def execute(connection, statement, *parameters):
    cursor = connection.cursor()
    try:
        cursor.execute(statement, *parameters)
        while True:
            if cursor.description:
                raise ValueError("Unexpected setup result")
            if not cursor.nextset():
                break
    finally:
        cursor.close()


def protect_credential(password):
    # Current Windows user DPAPI. Plaintext travels only through redirected
    # stdin/stdout memory; it never appears in arguments, files or receipts.
    command = (
        "$ErrorActionPreference='Stop';"
        "[void][Reflection.Assembly]::Load('System.Security, Version=4.0.0.0, "
        "Culture=neutral, PublicKeyToken=b03f5f7f11d50a3a');"
        "[Convert]::ToBase64String([Security.Cryptography.ProtectedData]::Protect("
        "[Text.Encoding]::UTF8.GetBytes([Console]::In.ReadToEnd()),$null,"
        "[Security.Cryptography.DataProtectionScope]::CurrentUser))"
    )
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        input=password,
        capture_output=True,
        text=True,
        timeout=10,
    )
    value = result.stdout.strip()
    if result.returncode or not value:
        raise ValueError("Private lab credential protection failed")
    return base64.b64decode(value, validate=True)


def main():
    packet = Path(__file__).resolve().parents[2]
    manifest = json.loads((packet / "manifest.json").read_bytes())
    if (
        os.environ.get("COMPUTERNAME") != "MINI_AMD"
        or manifest["stage"] != "restored-application-observer"
        or manifest["database"] != "ROK_TRACKER"
        or manifest["principal"] != "S11_ExportApplication_P02ObserverQual"
        or manifest["production_eligible"] is not False
    ):
        raise ValueError("Exact isolated lab-only proof required")
    for name, expected in manifest["files"].items():
        member = (packet / name).resolve()
        if not member.is_relative_to(packet) or sha(member.read_bytes()) != expected:
            raise ValueError("Sealed proof member changed")
    sys.path[:0] = [str(packet / "bot"), r"C:\discord_file_downloader\venv\Lib\site-packages"]
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    import pyodbc

    from services.application_observation_admission import AdmissionBinding, AdmissionMetadata
    from services.catalogue_observation_contract import reviewed_protocol_modules
    from services.catalogue_observation_dal import BOUNDARY_SQL
    from services.export_observer_contract import observation_record

    pyodbc.pooling = False
    budget = runpy.run_path(str(packet / "Verify-RunningRelease.py"))
    receipt: dict[str, Any] = dict(
        schema="p02-observer-application-proof/1",
        started=datetime.now(UTC).isoformat(),
        production_operations=0,
        business_operations=0,
        migration_history_changed=False,
        complete_release_accepted=False,
        stages=[],
        connections_closed=0,
    )

    def save(name, value):
        with (packet / name).open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, default=str)

    def stage(name, **facts):
        receipt["stages"].append(dict(name=name, **facts))
        save("stage-" + str(len(receipt["stages"])) + ".json", receipt["stages"][-1])

    admin, owner, password = None, None, None
    login_attempted = False
    failed = False
    base = (
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;"
        "Encrypt=yes;TrustServerCertificate=yes;DATABASE=ROK_TRACKER;"
    )
    principal = manifest["principal"]
    try:
        # Validate credential protection before any SQL connection or fixture DDL.
        password = "Aa1!" + secrets.token_urlsafe(48)
        encrypted = protect_credential(password)
        with (packet / "lab-credential.dpapi").open("xb") as handle:
            handle.write(encrypted)
        admin = pyodbc.connect(base + "Trusted_Connection=yes", autocommit=True, timeout=5)
        admin.timeout = 10
        execute(admin, "SET NOCOUNT ON; SET LOCK_TIMEOUT 1000; SET XACT_ABORT ON")
        execute(admin, GUARD_SQL)
        history = read(admin, HISTORY_SQL)
        assert sha(encode(history)) == manifest["history_sha256"]
        assert not read(
            admin,
            f"SELECT name FROM sys.server_principals WHERE name='{principal}' OR sid=0x{manifest['login_sid']}",
        )
        assert not read(admin, f"SELECT name FROM sys.database_principals WHERE name='{principal}'")
        assert not read(
            admin, f"SELECT name FROM sys.databases WHERE name='{manifest['snapshot']}'"
        )
        execute(
            admin,
            f"CREATE DATABASE [{manifest['snapshot']}] ON (NAME=[ROK_TRACKER],FILENAME=N'{manifest['snapshot_file']}') AS SNAPSHOT OF [ROK_TRACKER]",
        )
        snapshot = read(
            admin,
            f"SELECT name,source_database_id,state_desc,is_read_only FROM sys.databases WHERE name='{manifest['snapshot']}'",
        )
        assert len(snapshot) == 1 and snapshot[0]["source_database_id"] == 12
        assert snapshot[0]["state_desc"] == "ONLINE" and snapshot[0]["is_read_only"]
        stage("original-database-preserved", snapshot=snapshot, history_sha256=sha(encode(history)))
        login_attempted = True
        execute(
            admin,
            f"""DECLARE @Password nvarchar(128)=?;
DECLARE @Sql nvarchar(max)=N'CREATE LOGIN [{principal}] WITH PASSWORD='
+QUOTENAME(@Password,CHAR(39))+N', SID=0x{manifest['login_sid']},CHECK_POLICY=ON,CHECK_EXPIRATION=OFF,DEFAULT_DATABASE=[ROK_TRACKER];';
BEGIN TRANSACTION;
EXEC sys.sp_executesql @Sql;
ALTER LOGIN [{principal}] DISABLE;
COMMIT TRANSACTION;
SET @Password=NULL; SET @Sql=NULL;""",
            password,
        )
        stage(
            "new-disabled-lab-login",
            principal=principal,
            login_sid=manifest["login_sid"],
            credential_protection="CurrentUser DPAPI",
            credential_sha256=sha(encrypted),
        )
        execute(admin, "BEGIN TRANSACTION")
        try:
            execute(
                admin,
                f"""CREATE USER [{principal}] FOR LOGIN [{principal}] WITH DEFAULT_SCHEMA=[dbo];
ALTER ROLE [ExportLegacyEntryReader] ADD MEMBER [{principal}];
ALTER ROLE [ExportExecutionAuthority] ADD MEMBER [{principal}];
GRANT VIEW DEFINITION TO [{principal}];
GRANT SELECT ON OBJECT::sys.sql_expression_dependencies TO [{principal}];""",
            )
            execute(admin, (packet / "sql/lab-install.sql").read_text(encoding="utf-8"))
            provisional = read(admin, IDENTITY_SQL)
            assert len(provisional) == 1 and provisional[0]["generation"] == 1
            execute(admin, "COMMIT TRANSACTION")
        except BaseException:
            execute(admin, "IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
            raise
        # Receipt the committed stage before any later assertion. A later
        # failure cannot cause the installation to be replayed.
        stage("candidate-commit-acknowledged", provisional=provisional)
        committed = read(admin, IDENTITY_SQL)
        assert committed == provisional
        identity = committed[0]
        binding = dict(
            version=1,
            protocol_sha256=manifest["protocol_sha256"],
            server="MINI_AMD",
            database="ROK_TRACKER",
            database_id=12,
            principal=principal,
            login=principal,
            sequence_object_id=identity["sequence_object_id"],
            sequence_created=identity["sequence_created"].isoformat(timespec="microseconds"),
            sequence_modified=identity["sequence_modified"].isoformat(timespec="microseconds"),
            bootstrap_generation=1,
        )
        save(
            "lab-installation.json",
            dict(
                production_eligible=False,
                binding=binding,
                lineage=sha((packet / "evidence/lab-lineage.json").read_bytes()),
            ),
        )
        execute(admin, f"ALTER LOGIN [{principal}] ENABLE")
        approved = dict(manifest["approved"], observation_installation=binding)
        modules = reviewed_protocol_modules()
        # Read-only admission fixture: no durable claim or business authority is
        # manufactured. Actual DAL/service transfer has separate unit coverage.
        context = AdmissionBinding(
            sha(b"lab-read-only-claim"),
            sha(b"lab-config"),
            sha(b"lab-registration"),
            sha(encode(approved)),
            sha(encode(modules)),
        )
        owner = budget["ObservationConnections"](
            lambda: pyodbc.connect(
                base + f"UID={principal};PWD={{{password}}}", autocommit=True, timeout=5
            )
        )
        with owner:
            owner.observation_phase("application")
            origin = owner().cursor()
            with AdmissionMetadata(
                context, approved=approved, expected_modules=modules
            ) as evidence:
                started = time.perf_counter()
                evidence.collect(origin)
                cold_seconds = time.perf_counter() - started
                cold_end = len(owner.observations)
                stage(
                    "complete-application-observation",
                    seconds=cold_seconds,
                    dispatches=owner.statements,
                    scope_names=487,
                    login_mode="SQL authentication",
                )
                producer = owner().cursor()
                producer.execute("BEGIN TRANSACTION")
                entry_start = len(owner.observations)
                started = time.perf_counter()
                reused = evidence.consume(producer, context)
                reuse_seconds = time.perf_counter() - started
                entry_rows = owner.observations[entry_start:]
                producer.execute("SELECT @@TRANCOUNT,XACT_STATE()")
                assert tuple(producer.fetchone()) == (1, 1)
                producer.execute("ROLLBACK TRANSACTION")
                assert (
                    sum(row["sql_sha256"] == sha(BOUNDARY_SQL.encode()) for row in entry_rows) == 2
                )
                save(
                    "application-observation.json",
                    dict(observation=reused.value, boundary=observation_record(reused)),
                )
                stage(
                    "same-admission-reuse",
                    seconds=reuse_seconds,
                    dispatches=len(entry_rows),
                    boundary_reads=2,
                    borrowed_transaction_preserved=True,
                )
        assert all(connection.closed for connection in owner.connections)
        maximum = max(
            row["execute_seconds"] + row["fetch_seconds"] for row in owner.observations[:cold_end]
        )
        stage(
            "read-cost-and-cleanup",
            cold_seconds=cold_seconds,
            max_batch_seconds=maximum,
            owner_dispatches=owner.statements,
            connections_closed=len(owner.connections),
        )
        assert cold_seconds <= 15 and maximum <= 0.250
        assert sha(encode(read(admin, HISTORY_SQL))) == manifest["history_sha256"]
        receipt["outcome"] = "passed"
    except BaseException as error:
        failed = True
        receipt.update(outcome="failed", failure=budget["sql_error_facts"](error))
    finally:
        if admin is not None:
            if login_attempted:
                try:
                    execute(admin, "IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
                    execute(
                        admin,
                        f"IF EXISTS(SELECT 1 FROM sys.sql_logins WHERE name='{principal}' AND sid=0x{manifest['login_sid']}) ALTER LOGIN [{principal}] DISABLE",
                    )
                    cleanup_login = read(
                        admin,
                        f"SELECT name,is_disabled FROM sys.sql_logins WHERE name='{principal}' AND sid=0x{manifest['login_sid']}",
                    )
                    assert not cleanup_login or (
                        len(cleanup_login) == 1 and cleanup_login[0]["is_disabled"]
                    )
                    receipt["lab_login_cleanup"] = cleanup_login
                except BaseException as error:
                    failed = True
                    receipt["login_cleanup_failure"] = type(error).__name__
            try:
                admin.close()
                receipt["connections_closed"] += 1
            except BaseException as error:
                failed = True
                receipt["admin_cleanup_failure"] = type(error).__name__
        password = None
        if owner is not None:
            receipt["owner"] = owner.evidence()
            receipt["connections_closed"] += sum(c.closed for c in owner.connections)
        receipt["finished"] = datetime.now(UTC).isoformat()
        if failed:
            receipt["outcome"] = "failed"
        save("receipt.json", receipt)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
