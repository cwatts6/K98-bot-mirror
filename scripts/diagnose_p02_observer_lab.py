"""Read-only native values from the retained first observer fixture."""

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

sys.path.append(r"C:\discord_file_downloader\venv\Lib\site-packages")
import pyodbc

DATABASE = "K98_P02Observer_20261119175737420"
if os.environ.get("COMPUTERNAME") != "MINI_AMD":
    raise RuntimeError("Isolated qualification guest required")
pyodbc.pooling = False
receipt = {
    "schema": "p02-observer-native-diagnostic/1",
    "database": DATABASE,
    "utc": datetime.now(UTC).isoformat(),
    "sql_mutations": 0,
}
connection = None
cursor: Any = None
try:
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=lpc:localhost;"
        "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;DATABASE=" + DATABASE,
        autocommit=True,
        timeout=5,
    )
    connection.timeout = 3
    cursor = connection.cursor()
    cursor.execute("EXEC dbo.usp_P02ReadObservationBoundary")
    names = [item[0] for item in cursor.description]
    row = cursor.fetchone()
    receipt["boundary"] = [
        {"name": name, "type": type(value).__name__, "value": value}
        for name, value in zip(names, row, strict=True)
        if name != "ContractHealth"
    ]
    health = json.loads(row[-1]) if row[-1] is not None else None
    if health is not None:
        for module in health:
            body = module.pop("definition")
            module["definition_sha256_utf8"] = (
                hashlib.sha256(body.encode()).hexdigest() if body else None
            )
    receipt["health"] = health
    receipt["extra_row"] = cursor.fetchone() is not None
    receipt["extra_result"] = bool(cursor.nextset())
    cursor.execute(
        "SELECT object_id,system_type_id,user_type_id,CONVERT(nvarchar(100),current_value) AS CurrentValue,"
        "CONVERT(nvarchar(100),start_value) AS StartValue,CONVERT(nvarchar(100),increment) AS IncrementValue,"
        "CONVERT(nvarchar(100),minimum_value) AS MinimumValue,CONVERT(nvarchar(100),maximum_value) AS MaximumValue,"
        "is_cycling,is_cached,is_exhausted,create_date,modify_date FROM sys.sequences "
        "WHERE name='P02ObservationGeneration' AND schema_id=SCHEMA_ID('dbo')"
    )
    receipt["sequence"] = dict(
        zip([item[0] for item in cursor.description], cursor.fetchone(), strict=True)
    )
    cursor.execute(
        "SELECT @@TRANCOUNT AS TransactionCount,XACT_STATE() AS TransactionState,APPLOCK_TEST('public','K98:catalogue-mutation:v1','Exclusive','Session') AS WriterAbsent"
    )
    receipt["direct_state"] = dict(
        zip([item[0] for item in cursor.description], cursor.fetchone(), strict=True)
    )
    if len(sys.argv) == 3 and sys.argv[2] == "permissions":
        cursor.execute(
            "SELECT p.name,dp.state_desc,dp.permission_name,dp.class_desc,"
            "OBJECT_SCHEMA_NAME(dp.major_id) AS ObjectSchema,OBJECT_NAME(dp.major_id) AS ObjectName "
            "FROM sys.database_permissions dp JOIN sys.database_principals p "
            "ON p.principal_id=dp.grantee_principal_id "
            "WHERE p.name IN ('P02ObserverApplication','ExportLegacyEntryReader') "
            "ORDER BY p.name,dp.class,dp.major_id,dp.permission_name"
        )
        receipt["database_permissions"] = [
            dict(zip([item[0] for item in cursor.description], row, strict=True))
            for row in cursor.fetchall()
        ]
        cursor.execute(
            "SELECT sp.state_desc,sp.permission_name FROM sys.server_permissions sp "
            "WHERE sp.grantee_principal_id=SUSER_ID('S11_ExportApplication_P02Qual') "
            "ORDER BY sp.permission_name"
        )
        receipt["server_permissions"] = [list(row) for row in cursor.fetchall()]
        cursor.execute("EXECUTE AS LOGIN='S11_ExportApplication_P02Qual'")
        try:
            cursor.execute(
                "SELECT USER_NAME() AS PrincipalName,SUSER_SNAME() AS LoginName,DB_ID() AS DatabaseID,"
                "IS_SRVROLEMEMBER('sysadmin') AS IsSysadmin,IS_ROLEMEMBER('db_owner') AS IsDbOwner,"
                "HAS_PERMS_BY_NAME(NULL,NULL,'ADMINISTER BULK OPERATIONS') AS CanBulk,"
                "HAS_PERMS_BY_NAME('dbo.KVKFinalReportHeader','OBJECT','ALTER') AS HeaderAlter,"
                "HAS_PERMS_BY_NAME('dbo.MaintenanceKvkWork','OBJECT','ALTER') AS KvkWorkAlter,"
                "HAS_PERMS_BY_NAME('dbo.MaintenanceWork','OBJECT','ALTER') AS MaintenanceAlter,"
                "HAS_PERMS_BY_NAME('dbo.P02DirectDDL','OBJECT','ALTER') AS OtherTableAlter"
            )
            receipt["actual_actor"] = [
                {"name": name, "type": type(value).__name__, "value": value}
                for name, value in zip(
                    [item[0] for item in cursor.description], cursor.fetchone(), strict=True
                )
            ]
        finally:
            cursor.execute("REVERT")
        cursor.execute("SELECT SUSER_SNAME(),ORIGINAL_LOGIN()")
        row = cursor.fetchone()
        receipt["impersonation_reverted"] = row[0] == row[1]
    receipt["outcome"] = "observed"
except BaseException as error:
    receipt["outcome"] = "failed"
    receipt["failure"] = {"type": type(error).__name__, "detail": str(error)[:2000]}
finally:
    try:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
        receipt["cleanup"] = "closed"
    except BaseException as error:
        receipt["cleanup"] = "unknown"
        receipt["cleanup_failure"] = type(error).__name__
    with Path(sys.argv[1]).open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, default=str)
print(receipt["outcome"], flush=True)
