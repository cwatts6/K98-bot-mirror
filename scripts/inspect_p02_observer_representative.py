"""Read existing isolated-VM fixtures before selecting representative qualification.

Fixed local databases only. No DDL, DML, recovery, maintenance, backup, grants,
impersonation or business procedure dispatch. Each statement has a three-second
timeout and zero row-lock wait. Failures are preserved as evidence, not retried.
"""

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

sys.path.append(r"C:\discord_file_downloader\venv\Lib\site-packages")
import pyodbc

DATABASES = ("ROK_TRACKER", "K98_P025_D5e_Cost_20261115")
if os.environ.get("COMPUTERNAME") != "MINI_AMD":
    raise RuntimeError("Exact isolated qualification guest required")
pyodbc.pooling = False
receipt: dict[str, Any] = dict(
    schema="p02-observer-representative-inventory/1",
    utc=datetime.now(UTC).isoformat(),
    sql_mutations=0,
    databases=[],
    connections_closed=0,
)


def sql(connection, statement):
    cursor = connection.cursor()
    try:
        cursor.execute(statement)
        columns = [item[0] for item in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(2001) if cursor.description else []
        if len(rows) > 2000:
            raise ValueError("Read-only inventory exceeded its row bound")
        result = [dict(zip(columns, row, strict=True)) for row in rows]
        while cursor.nextset():
            if cursor.description:
                raise ValueError("Unexpected extra inventory result")
        return result
    except Exception as error:
        return dict(error=type(error).__name__, detail=str(error)[:2000])
    finally:
        cursor.close()


for database in DATABASES:
    connection = None
    observed = dict(database=database)
    receipt["databases"].append(observed)
    try:
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;DATABASE="
            + database,
            autocommit=True,
            timeout=5,
        )
        connection.timeout = 3
        observed["session_settings"] = sql(
            connection, "SET LOCK_TIMEOUT 0; SET DEADLOCK_PRIORITY LOW"
        )
        observed["target"] = sql(
            connection,
            "SELECT DB_NAME() AS DatabaseName,DB_ID() AS DatabaseID,CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) AS Edition,CONVERT(nvarchar(128),SERVERPROPERTY('ProductVersion')) AS ProductVersion,d.create_date,d.collation_name,d.compatibility_level,d.state_desc,d.is_read_only,d.snapshot_isolation_state_desc,d.is_read_committed_snapshot_on,d.source_database_id FROM sys.databases d WHERE d.database_id=DB_ID()",
        )
        observed["files"] = sql(
            connection,
            "SELECT file_id,name,type_desc,physical_name,CONVERT(bigint,size)*8192 AS BytesAllocated,CONVERT(bigint,FILEPROPERTY(name,'SpaceUsed'))*8192 AS BytesUsed,max_size,growth,is_percent_growth FROM sys.database_files ORDER BY file_id",
        )
        observed["selected_modules"] = sql(
            connection,
            "SELECT SCHEMA_NAME(o.schema_id)+'.'+o.name AS ObjectName,o.type,o.object_id,o.create_date,o.modify_date,m.definition,m.uses_ansi_nulls,m.uses_quoted_identifier,m.execute_as_principal_id FROM sys.objects o JOIN sys.sql_modules m ON m.object_id=o.object_id WHERE o.name IN ('sp_ExcelOutput_ByKVK','usp_RunMaintenance','usp_S11ValidateStatsReportStage','sp_TARGETS_MASTER','usp_ApplyReportGovernorNames','v_ReportGovernorNames') ORDER BY o.name",
        )
        observed["observer_objects"] = sql(
            connection,
            "SELECT o.name,o.type_desc FROM sys.objects o WHERE o.name LIKE '%P02%Observation%' OR o.name IN ('usp_P02BeginCatalogueMutation','usp_P02EndCatalogueMutation') UNION ALL SELECT name,type_desc FROM sys.triggers WHERE parent_class=0 AND name LIKE '%P02%Observation%' ORDER BY name",
        )
        observed["table_sizes"] = sql(
            connection,
            "SELECT SCHEMA_NAME(t.schema_id)+'.'+t.name AS ObjectName,SUM(p.rows) AS ApproximateRows FROM sys.tables t JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN(0,1) WHERE t.is_ms_shipped=0 GROUP BY t.schema_id,t.name ORDER BY ObjectName",
        )
        observed["active_sessions"] = sql(
            connection,
            "SELECT s.session_id,s.login_name,s.host_name,s.program_name,s.status,s.open_transaction_count,r.command,r.blocking_session_id FROM sys.dm_exec_sessions s LEFT JOIN sys.dm_exec_requests r ON r.session_id=s.session_id WHERE s.is_user_process=1 AND s.session_id<>@@SPID AND (s.database_id=DB_ID() OR r.database_id=DB_ID()) ORDER BY s.session_id",
        )
        observed["lab_actor"] = sql(
            connection,
            "SELECT p.name,p.type_desc,p.default_schema_name,LOWER(CONVERT(varchar(170),p.sid,2)) AS LoginSID,r.name AS RoleName FROM sys.database_principals p LEFT JOIN sys.database_role_members rm ON rm.member_principal_id=p.principal_id LEFT JOIN sys.database_principals r ON r.principal_id=rm.role_principal_id WHERE p.sid=SUSER_SID('S11_ExportApplication_P02Qual') ORDER BY p.name,r.name",
        )
        observed["maintenance"] = sql(
            connection,
            "SELECT Kind,State,DueGeneration,CompletedGeneration FROM dbo.MaintenanceWork ORDER BY Kind",
        )
        observed["kvk_work"] = sql(
            connection,
            "SELECT KVKNo,State,DueGeneration,CompletedGeneration,DueObjectID,DueHeaderRevision FROM dbo.MaintenanceKvkWork ORDER BY KVKNo",
        )
        observed["preparation_states"] = sql(
            connection,
            "SELECT State,COUNT_BIG(*) AS [RowCount] FROM dbo.ExportPreparation GROUP BY State ORDER BY State",
        )
        observed["import_states"] = sql(
            connection,
            "SELECT State,COUNT_BIG(*) AS [RowCount] FROM dbo.StatsImportExecution GROUP BY State ORDER BY State",
        )
    except Exception as error:
        observed["failure"] = dict(type=type(error).__name__, detail=str(error)[:2000])
    finally:
        if connection is not None:
            try:
                connection.close()
                receipt["connections_closed"] += 1
            except Exception as error:
                observed["cleanup_failure"] = type(error).__name__
receipt["finished"] = datetime.now(UTC).isoformat()
with Path(sys.argv[1]).open("x", encoding="utf-8") as handle:
    json.dump(receipt, handle, indent=2, default=str)
print("Read-only representative fixture inventory saved", flush=True)
