"""Read the preserved ROK_TRACKER lab predecessor before caller qualification.

No credentials, password hashes, provider data or business rows are read. This
does not install the candidate, create an account, or issue a release contract.
"""

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys

QUERIES = {
    "target": """SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS ServerName,
DB_NAME() AS DatabaseName,DB_ID() AS DatabaseID,d.create_date,d.state_desc,
d.is_read_only,d.snapshot_isolation_state_desc,d.is_read_committed_snapshot_on,
d.source_database_id,CONVERT(int,SERVERPROPERTY('IsIntegratedSecurityOnly')) AS WindowsOnly
FROM sys.databases d WHERE d.database_id=DB_ID()""",
    "history": """SELECT MigrationId,MigrationFile,ChecksumSha256,AppliedAtUtc,
GitCommit,DeploymentId,Status FROM dbo.SchemaMigrationHistory ORDER BY MigrationId""",
    "predecessor_bodies": """SELECT SCHEMA_NAME(o.schema_id)+'.'+o.name AS ObjectName,
o.object_id,o.type,o.create_date,o.modify_date,m.uses_ansi_nulls,m.uses_quoted_identifier,
m.execute_as_principal_id,USER_NAME(COALESCE(o.principal_id,s.principal_id)) AS OwnerName,
LOWER(CONVERT(varchar(64),HASHBYTES('SHA2_256',REPLACE(m.definition,NCHAR(13)+NCHAR(10),NCHAR(10))),2)) AS DefinitionSHA256
FROM sys.objects o JOIN sys.schemas s ON s.schema_id=o.schema_id
JOIN sys.sql_modules m ON m.object_id=o.object_id
WHERE o.object_id IN (OBJECT_ID('dbo.sp_ExcelOutput_ByKVK'),
OBJECT_ID('dbo.usp_RunMaintenance'),OBJECT_ID('dbo.usp_S11ValidateStatsReportStage'))
ORDER BY ObjectName""",
    "observer_objects": """SELECT name,type_desc FROM sys.objects
WHERE name IN ('P02ObservationGeneration','usp_P02BeginCatalogueMutation',
'usp_P02EndCatalogueMutation','usp_P02ReadObservationBoundary')
UNION ALL SELECT name,type_desc FROM sys.triggers WHERE name LIKE 'tr_P02%Observation%'
ORDER BY name""",
    "lab_principals": """SELECT p.name,p.type_desc,p.default_schema_name,
LOWER(CONVERT(varchar(170),p.sid,2)) AS LoginSID,r.name AS RoleName
FROM sys.database_principals p
LEFT JOIN sys.database_role_members rm ON rm.member_principal_id=p.principal_id
LEFT JOIN sys.database_principals r ON r.principal_id=rm.role_principal_id
WHERE p.name IN ('S11_ExportApplication_P02Qual','S11_ExportApplication_P02ObserverQual',
'ExportLegacyEntryReader') ORDER BY p.name,r.name""",
    "lab_logins": """SELECT name,type_desc,is_disabled,default_database_name,
is_policy_checked,is_expiration_checked FROM sys.sql_logins
WHERE name IN ('S11_ExportApplication_P02Qual','S11_ExportApplication_P02ObserverQual')
ORDER BY name""",
    "lifecycle_permissions": """SELECT p.name AS Principal,dp.state_desc,dp.permission_name,
OBJECT_SCHEMA_NAME(dp.major_id)+'.'+OBJECT_NAME(dp.major_id) AS ObjectName,dp.minor_id
FROM sys.database_permissions dp JOIN sys.database_principals p ON p.principal_id=dp.grantee_principal_id
WHERE dp.class=1 AND dp.major_id IN (OBJECT_ID('dbo.KVKFinalReportHeader'),
OBJECT_ID('dbo.MaintenanceKvkWork'),OBJECT_ID('dbo.MaintenanceWork'))
AND dp.permission_name='ALTER' ORDER BY Principal,ObjectName,dp.minor_id""",
    "dynamic_outputs": """SELECT SCHEMA_NAME(o.schema_id)+'.'+o.name AS ObjectName,
o.object_id,o.type,o.create_date,o.modify_date FROM sys.objects o
WHERE o.object_id IN (OBJECT_ID('dbo.EXCEL_EXPORT_KVK_TARGETS_16'),
OBJECT_ID('dbo.EXCEL_FOR_KVK_16'),OBJECT_ID('dbo.EXCEL_OUTPUT_KVK_TARGETS_16'),
OBJECT_ID('dbo.TARGETS_16')) ORDER BY ObjectName""",
    "files": """SELECT file_id,name,type_desc,physical_name,
CONVERT(bigint,size)*8192 AS BytesAllocated,
CONVERT(bigint,FILEPROPERTY(name,'SpaceUsed'))*8192 AS BytesUsed FROM sys.database_files
ORDER BY file_id""",
    "active_sessions": """SELECT s.session_id,s.login_name,s.host_name,s.program_name,
s.status,s.open_transaction_count,r.command,r.blocking_session_id
FROM sys.dm_exec_sessions s LEFT JOIN sys.dm_exec_requests r ON r.session_id=s.session_id
WHERE s.is_user_process=1 AND s.session_id<>@@SPID
AND (s.database_id=DB_ID() OR r.database_id=DB_ID()) ORDER BY s.session_id""",
}


def main(output):
    if os.environ.get("COMPUTERNAME") != "MINI_AMD":
        raise RuntimeError("Exact isolated qualification guest required")
    sys.path.append(r"C:\discord_file_downloader\venv\Lib\site-packages")
    import pyodbc

    pyodbc.pooling = False
    receipt = dict(
        schema="p02-observer-release-prerequisites/1",
        utc=datetime.now(UTC).isoformat(),
        sql_mutations=0,
        connection_closed=False,
        reads={},
    )
    connection = None
    failed = False
    try:
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;"
            "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
            "DATABASE=ROK_TRACKER;APP=P02ObserverReleaseInventory",
            autocommit=True,
            timeout=5,
        )
        connection.timeout = 3
        with connection.cursor() as cursor:
            cursor.execute("SET LOCK_TIMEOUT 0; SET DEADLOCK_PRIORITY LOW")
        for name, statement in QUERIES.items():
            with connection.cursor() as cursor:
                cursor.execute(statement)
                columns = [item[0] for item in cursor.description]
                rows = cursor.fetchmany(501)
                if len(rows) > 500:
                    raise ValueError("Read-only prerequisite row bound exceeded")
                values = [dict(zip(columns, row, strict=True)) for row in rows]
                if cursor.nextset():
                    raise ValueError("Unexpected prerequisite result set")
            receipt["reads"][name] = values
            if name == "target" and (
                len(values) != 1
                or values[0]["ServerName"].upper() != "MINI_AMD"
                or values[0]["DatabaseName"] != "ROK_TRACKER"
                or values[0]["DatabaseID"] != 12
                or str(values[0]["create_date"]) != "2026-11-17 17:34:47.357000"
                or values[0]["source_database_id"] is not None
            ):
                raise ValueError("Preserved lab predecessor incarnation changed")
    except Exception as error:
        failed = True
        receipt["failure"] = dict(type=type(error).__name__, detail=str(error)[:2000])
    finally:
        if connection is not None:
            try:
                connection.close()
                receipt["connection_closed"] = True
            except Exception as error:
                failed = True
                receipt["cleanup_failure"] = type(error).__name__
        receipt["finished"] = datetime.now(UTC).isoformat()
        with Path(output).open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, default=str)
    print("Read-only release prerequisite evidence saved", flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
