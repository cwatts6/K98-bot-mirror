"""Render reviewed object grants; never connects, creates accounts or installs SQL."""

import argparse
import hashlib
import json
from pathlib import Path
import re


def render_login(*, server, principal):
    """Public template: the administrator supplies the secret privately in SSMS."""
    if not re.fullmatch(r"[A-Za-z0-9_\\.-]{1,128}", server):
        raise ValueError("Exact server binding required")
    if not re.fullmatch(r"S11_ExportApplication(?:_[A-Za-z0-9_]+)?", principal):
        raise ValueError("Dedicated S11 principal required")
    return f"""-- Separate approved account provisioning. Never save the filled-in password script.
USE [master];
SET NOCOUNT ON; SET XACT_ABORT ON; SET LOCK_TIMEOUT 1000;
IF CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) COLLATE Latin1_General_100_BIN2<>N'{server}'
 OR SERVERPROPERTY('IsIntegratedSecurityOnly')<>0
 OR COALESCE(IS_SRVROLEMEMBER('sysadmin'),0)<>1
 THROW 52080,'Account provisioning target/access mismatch.',1;
IF SUSER_ID(N'{principal}') IS NOT NULL THROW 52080,'Existing login is not adopted.',1;
DECLARE @Password nvarchar(128)=N'REPLACE_IN_PRIVATE_SSMS';
IF @Password=N'REPLACE_IN_PRIVATE_SSMS' OR LEN(@Password)<24
 THROW 52080,'Supply a new strong password privately; never log it.',1;
DECLARE @Sql nvarchar(max)=N'CREATE LOGIN [{principal}] WITH PASSWORD='
 +QUOTENAME(@Password,CHAR(39))+N', CHECK_POLICY=ON, CHECK_EXPIRATION=OFF, DEFAULT_DATABASE=[ROK_TRACKER];';
BEGIN TRY
 BEGIN TRANSACTION;
 EXEC sys.sp_executesql @Sql;
 ALTER LOGIN [{principal}] DISABLE;
 COMMIT TRANSACTION;
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
 THROW;
END CATCH;
SET @Password=NULL; SET @Sql=NULL;
SELECT name,CONVERT(varchar(172),sid,1) AS ActualLoginSID,is_disabled
 FROM sys.sql_logins WHERE name=N'{principal}';
-- Bind this returned SID to the reviewed grants. Enable only after grants/config validation.
"""


def render(plan, *, server, database, principal, login_sid):
    if not re.fullmatch(r"[A-Za-z0-9_\\.-]{1,128}", server):
        raise ValueError("Exact server binding required")
    if database != "ROK_TRACKER" and not re.fullmatch(
        r"K98_S11_Disposable_[A-Za-z0-9_]+", database
    ):
        raise ValueError("Production or specifically named disposable database required")
    if not re.fullmatch(r"S11_ExportApplication(?:_[A-Za-z0-9_]+)?", principal):
        raise ValueError("Dedicated S11 principal required")
    if not re.fullmatch(r"0x[0-9A-Fa-f]{32,170}", login_sid) or len(login_sid) % 2:
        raise ValueError("Actual reviewed login SID required")
    entries = plan["grants"]
    direct = plan.get("version") == 2
    if plan.get("version") not in (1, 2) or not entries or len(entries) > 500:
        raise ValueError("Reviewed finite grant plan required")
    if direct:
        from services.export_sql_direct_permissions import DIRECT_SOURCE_HASH

        if (
            plan.get("permission_model") != "direct_application_v1"
            or plan.get("legacy_source_sha256") != DIRECT_SOURCE_HASH
            or plan.get("server_permissions")
            != ["ADMINISTER BULK OPERATIONS", "VIEW SERVER PERFORMANCE STATE"]
            or plan.get("master_database_permissions") != ["CONNECT"]
            or plan.get("master_object_permissions")
            != [
                dict(object="dbo.xp_cmdshell", permission="EXECUTE"),
                dict(object="dbo.xp_fileexist", permission="EXECUTE"),
            ]
        ):
            raise ValueError("Exact reviewed direct legacy grant plan required")
    master_statements = []
    if direct:
        master_statements = [
            f"IF USER_ID(N'{principal}') IS NOT NULL OR EXISTS(SELECT 1 FROM sys.database_principals WHERE sid={login_sid}) THROW 52080,'Existing master user is not adopted.',1;",
            f"CREATE USER [{principal}] FOR LOGIN [{principal}] WITH DEFAULT_SCHEMA=[dbo];",
            f"GRANT CONNECT TO [{principal}];",
            f"GRANT EXECUTE ON OBJECT::[dbo].[xp_cmdshell] TO [{principal}];",
            f"GRANT EXECUTE ON OBJECT::[dbo].[xp_fileexist] TO [{principal}];",
            f"GRANT ADMINISTER BULK OPERATIONS TO [{principal}];",
        ]
    seen = set()
    statements = []
    for entry in entries:
        name, permission = entry["object"], entry["permission"]
        column = entry.get("column")
        metadata_catalog = name == "sys.sql_expression_dependencies"
        if metadata_catalog and (permission != "SELECT" or column is not None):
            raise ValueError("Dependency catalog allows only object SELECT")
        if not metadata_catalog and not re.fullmatch(r"(?:dbo|KVK)\.[A-Za-z0-9_]{1,128}", name):
            raise ValueError("Allowlisted object required")
        if permission not in {"SELECT", "INSERT", "UPDATE", "DELETE", "EXECUTE"}:
            raise ValueError("Application object permission required")
        if column is not None and (
            permission != "SELECT" or not re.fullmatch(r"[A-Za-z0-9_]{1,128}", column)
        ):
            raise ValueError("Exact SELECT column required")
        key = (name, permission, column)
        if key in seen:
            raise ValueError("Duplicate grant")
        seen.add(key)
        quoted = ".".join("[" + part + "]" for part in name.split("."))
        statements += [
            f"IF OBJECT_ID(N'{name}') IS NULL THROW 52080,'Required S11 dependency is absent.',1;",
            f"GRANT {permission} ON OBJECT::{quoted}"
            + (f" ([{column}])" if column else "")
            + f" TO [{principal}];",
        ]
    fingerprint = hashlib.sha256(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return "\n".join(
        [
            "-- Prepared grants only. Login provisioning and installation are separate operations.",
            "-- Grant-plan SHA256: " + fingerprint,
            "SET NOCOUNT ON; SET XACT_ABORT ON; SET LOCK_TIMEOUT 1000;",
            f"IF CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) COLLATE Latin1_General_100_BIN2<>N'{server}' OR DB_NAME() COLLATE Latin1_General_100_BIN2<>N'{database}' THROW 52080,'S11 grant target mismatch.',1;",
            f"IF SUSER_SID(N'{principal}') IS NULL OR SUSER_SID(N'{principal}')<>{login_sid} THROW 52080,'S11 login SID mismatch.',1;",
            f"IF COALESCE(IS_SRVROLEMEMBER('sysadmin',N'{principal}'),-1)<>0 THROW 52080,'S11 login is privileged or unknown.',1;",
            f"IF NOT EXISTS(SELECT 1 FROM sys.sql_logins WHERE name=N'{principal}' AND sid={login_sid} AND is_disabled=1) THROW 52080,'Disabled S11 login required during grant installation.',1;",
            f"IF EXISTS(SELECT 1 FROM sys.server_role_members m JOIN sys.server_principals p ON p.principal_id=m.member_principal_id WHERE p.sid={login_sid}) THROW 52080,'S11 login has unexpected server memberships.',1;",
            f"IF EXISTS(SELECT 1 FROM sys.server_permissions g JOIN sys.server_principals p ON p.principal_id=g.grantee_principal_id WHERE p.sid={login_sid} AND NOT(g.class=100 AND g.major_id=0 AND g.permission_name=N'CONNECT SQL' AND g.state=N'G')) THROW 52080,'Existing direct server permissions are not adopted.',1;",
            "BEGIN TRY",
            "BEGIN TRANSACTION;",
            f"IF USER_ID(N'{principal}') IS NOT NULL THROW 52080,'Existing user is not adopted; reconcile first.',1;",
            "IF DATABASE_PRINCIPAL_ID(N'ExportExecutionAuthority') IS NULL OR DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader') IS NULL THROW 52080,'Reviewed S11 roles must be installed first.',1;",
            f"CREATE USER [{principal}] FOR LOGIN [{principal}] WITH DEFAULT_SCHEMA=[dbo];",
            f"GRANT CONNECT, VIEW DEFINITION TO [{principal}];",
            f"ALTER ROLE [ExportExecutionAuthority] ADD MEMBER [{principal}];",
            f"ALTER ROLE [ExportLegacyEntryReader] ADD MEMBER [{principal}];",
            *statements,
            "-- Server grant for the SQL 2022 log DMV belongs to this same transaction:",
            "USE [master];",
            *master_statements,
            f"GRANT VIEW SERVER PERFORMANCE STATE TO [{principal}];",
            f"USE [{database}];",
            "COMMIT TRANSACTION;",
            "END TRY",
            "BEGIN CATCH",
            "IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;",
            "THROW;",
            "END CATCH;",
            (
                "-- Direct legacy role carries reviewed schema/database rights; no certificate required."
                if direct
                else "-- No schema DML/ALTER or bulk/file grants in the signed profile."
            ),
            "-- No db_owner, bulkadmin, SQLAgent role, backup, impersonation, grant option or login enable.",
            "",
        ]
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("plan", "server", "database", "principal", "login-sid", "out"):
        parser.add_argument("--" + option, required=True)
    args = parser.parse_args()
    output = render(
        json.loads(Path(args.plan).read_text(encoding="utf-8-sig")),
        server=args.server,
        database=args.database,
        principal=args.principal,
        login_sid=args.login_sid,
    )
    Path(args.out).write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
