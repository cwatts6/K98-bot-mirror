"""Read retained plans for measured catalogue queries in the isolated D5e DB.

No catalogue test replay, cache clearing, SHOWPLAN grant, SQL object/data change
or production connection. An absent/evicted plan is reported, never recreated.
"""

from contextlib import closing
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

sys.path.append(r"C:\discord_file_downloader\venv\Lib\site-packages")
import pyodbc

PLAN_SQL = """WITH selected AS (
    SELECT TOP (96) qs.plan_handle,qs.statement_start_offset,qs.statement_end_offset,
        qs.creation_time,qs.last_execution_time,qs.execution_count,qs.plan_generation_num,
        qs.last_worker_time,qs.last_elapsed_time,qs.last_logical_reads,qs.last_logical_writes,
        qs.last_physical_reads,qs.last_rows,st.text AS BatchText
    FROM sys.dm_exec_query_stats qs
    CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
    CROSS APPLY sys.dm_exec_plan_attributes(qs.plan_handle) pa
    WHERE pa.attribute=N'dbid' AND CONVERT(int,pa.value)=DB_ID()
        AND st.objectid IS NULL
        AND st.text NOT LIKE N'%sys.dm_exec_query_stats%'
        AND ((st.text LIKE N'%WITH selected AS (%'
              AND (st.text LIKE N'%AS visible_position,t.max_column_id_used,c.is_computed%'
                   OR st.text LIKE N'%AS column_name,name,is_system_named,definition FROM sys.default_constraints%'
                   OR st.text LIKE N'%AS candidate_column_name,i.name AS candidate_index_name%'))
             OR (st.text LIKE N'%AS visible_position,%'
                 AND st.text LIKE N'%WHERE c.object_id IN (OBJECT_ID(%')
             OR (st.text LIKE N'%sys.fn_my_permissions%'
              AND st.text LIKE N'%FROM sys.objects o%')
             OR (st.text LIKE N'%HAS_PERMS_BY_NAME%'
                 AND st.text LIKE N'%FROM sys.objects o JOIN sys.columns c%')
             OR (st.text LIKE N'%NativeObjectID%'
              AND st.text LIKE N'%c.default_object_id AS NativeDefaultID%'
              AND st.text LIKE N'%WHERE c.object_id IN (OBJECT_ID(%')
             OR (st.text LIKE N'%DECLARE @required TABLE(object_id int NOT NULL PRIMARY KEY)%'
              AND (st.text LIKE N'%i.name AS IndexName,i.type AS IndexType%'
                   OR st.text LIKE N'%c.name AS ConstraintName,c.definition AS Definition%'
                   OR st.text LIKE N'%AS visible_position,%'
                   OR st.text LIKE N'%d.name,d.is_system_named,d.definition%'
                   OR st.text LIKE N'%AS candidate_column_name,%'
                   OR st.text LIKE N'%c.column_id AS Ordinal,c.name AS ColumnName%'
                   OR st.text LIKE N'%AS object_name,i.index_id,i.name,i.type_desc%'
                   OR st.text LIKE N'%AS NativeDefaultID,name AS DefaultName%'
                   OR st.text LIKE N'%definition AS ComputedDefinition,is_persisted AS ComputedPersisted%'
                   OR st.text LIKE N'%CONVERT(nvarchar(128),seed_value) AS IdentitySeed%'))
             OR (st.text LIKE N'%WITH required AS (%'
                 AND st.text LIKE N'%name AS ConstraintName,definition AS Definition%'
                 AND st.text LIKE N'%FROM sys.check_constraints WHERE%'))
    ORDER BY qs.last_execution_time DESC,qs.statement_start_offset
)
SELECT LOWER(CONVERT(varchar(130),s.plan_handle,2)) AS PlanHandle,
    s.statement_start_offset,s.statement_end_offset,s.creation_time,s.last_execution_time,
    s.execution_count,s.plan_generation_num,s.last_worker_time,s.last_elapsed_time,
    s.last_logical_reads,s.last_logical_writes,s.last_physical_reads,s.last_rows,s.BatchText,
    p.query_plan AS PlanText
FROM selected s
OUTER APPLY sys.dm_exec_text_query_plan(s.plan_handle,s.statement_start_offset,s.statement_end_offset) p
ORDER BY s.last_execution_time DESC,s.statement_start_offset"""


def read(connection, statement):
    with closing(connection.cursor()) as cursor:
        cursor.execute(statement)
        columns = [item[0] for item in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(97) if cursor.description else []
        if len(rows) > 96:
            raise ValueError("Plan diagnostic exceeded its row bound")
        result = [dict(zip(columns, row, strict=True)) for row in rows]
        while cursor.nextset():
            if cursor.description:
                raise ValueError("Unexpected plan diagnostic result")
        return result


def main(destination):
    if os.environ.get("COMPUTERNAME") != "MINI_AMD":
        raise RuntimeError("Exact isolated qualification guest required")
    pyodbc.pooling = False
    receipt: dict[str, Any] = dict(
        schema="p02-observer-query-plans/1",
        utc=datetime.now(UTC).isoformat(),
        sql_mutations=0,
        catalogue_replays=0,
        connections_closed=0,
    )
    connection = None
    try:
        connection = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;DATABASE=K98_P025_D5e_Cost_20261115",
            autocommit=True,
            timeout=5,
        )
        connection.timeout = 3
        read(connection, "SET LOCK_TIMEOUT 0; SET DEADLOCK_PRIORITY LOW")
        receipt["target"] = read(
            connection, "SELECT DB_NAME() AS DatabaseName,DB_ID() AS DatabaseID"
        )
        assert receipt["target"] == [dict(DatabaseName="K98_P025_D5e_Cost_20261115", DatabaseID=11)]
        receipt["sequence"] = read(
            connection,
            "SELECT object_id,create_date,modify_date,CONVERT(bigint,current_value) AS Generation FROM sys.sequences WHERE name=N'P02ObservationGeneration' AND schema_id=SCHEMA_ID(N'dbo')",
        )
        receipt["plans"] = read(connection, PLAN_SQL)
        receipt["possibly_truncated"] = len(receipt["plans"]) == 96
        receipt["outcome"] = "observed" if receipt["plans"] else "no-matching-retained-plans"
    except Exception as error:
        receipt["outcome"] = "failed"
        receipt["failure"] = dict(type=type(error).__name__, detail=str(error)[:2000])
    finally:
        if connection is not None:
            try:
                connection.close()
                receipt["connections_closed"] += 1
            except Exception as error:
                receipt["outcome"] = "cleanup-unknown"
                receipt["cleanup_failure"] = str(error)[:1000]
        receipt["finished"] = datetime.now(UTC).isoformat()
        with Path(destination).open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, default=str)
    print(receipt["outcome"], flush=True)
    return 0 if receipt["outcome"] in {"observed", "no-matching-retained-plans"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
