"""Explicit operator-approved legacy direct permissions; never a signing fallback."""

import json
from pathlib import Path
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest

DIRECT_SOURCE_HASH = "c018e31d759239840e6f43679c9e05d5f9bddfdad166e9d299d76e3c6b1799e6"
DIRECT_MIGRATION = "20261003_001_export_legacy_direct_permissions"
APPLICATION_GRANT_PLAN_HASH = "da0546c5d7abbe94ae782894183f097ca821dee61e2c7a9915eab5c8180a11bc"


def application_grant_rows():
    """Expected direct user rights derive only from the reviewed source plan."""
    plan = json.loads(
        (Path(__file__).resolve().parents[1] / "deploy/s11_application_grants.json").read_bytes()
    )
    if digest(plan).hex() != APPLICATION_GRANT_PLAN_HASH:
        raise SourceConflict("Reviewed application grant source differs.")
    entries = [
        ("ROK_TRACKER", "DATABASE", "ROK_TRACKER", p, None) for p in plan["database_permissions"]
    ]
    entries += [
        ("ROK_TRACKER", "OBJECT", g["object"], g["permission"], g.get("column"))
        for g in plan["grants"]
    ]
    entries += [
        ("master", "DATABASE", "master", p, None) for p in plan["master_database_permissions"]
    ]
    entries += [
        ("master", "OBJECT", g["object"], g["permission"], None)
        for g in plan["master_object_permissions"]
    ]
    return [
        dict(
            DatabaseName=db,
            SecurableClass=kind,
            TargetName=target,
            PermissionName=right,
            GrantState="G",
            ColumnName=column,
        )
        for db, kind, target, right, column in entries
    ]


def validate_contract(approved):
    fields = {
        "version",
        "server",
        "database",
        "principal",
        "login_sid",
        "source",
        "migration_hash",
        "metadata_hash",
    }
    if (
        not isinstance(approved, dict)
        or set(approved) != fields
        or type(approved["version"]) is not int
        or approved["version"] != 2
        or approved["database"] != "ROK_TRACKER"
        or any(
            not isinstance(approved[k], str)
            or not 1 <= len(approved[k]) <= 128
            or approved[k] != approved[k].strip()
            for k in ("server", "principal")
        )
        or not re.fullmatch(r"[0-9a-f]{32,170}", str(approved["login_sid"]))
        or len(approved["login_sid"]) % 2
        or any(
            not re.fullmatch(r"[0-9a-f]{64}", str(approved[k]))
            for k in ("migration_hash", "metadata_hash")
        )
        or digest(approved["source"]).hex() != DIRECT_SOURCE_HASH
    ):
        raise SourceConflict("Complete reviewed direct-permission SQL contract required.")


def queries(base, source):
    """Reuse exact source/body reads, replace signing observations explicitly."""
    result = {
        k: base[k]
        for k in (
            "target",
            "modules",
            "capabilities",
            "module_permissions",
            "ownership",
        )
    }
    target, params = result["target"]
    result["target"] = (
        target.replace(
            "USER_NAME() AS Principal,",
            "USER_NAME() AS Principal,ORIGINAL_LOGIN() AS LoginName,"
            "LOWER(CONVERT(varchar(170),SUSER_SID(),2)) AS LoginSID,",
        ),
        params,
    )
    capability_input = json.loads(result["capabilities"][1][0])
    capability_input += [dict(kind="DATABASE", target="ROK_TRACKER", permission="CHECKPOINT")]
    result["capabilities"] = (result["capabilities"][0], (json.dumps(capability_input),))
    result["grants"] = (
        """SELECT DB_NAME() COLLATE Latin1_General_100_BIN2 AS DatabaseName,
        CASE WHEN u.name=USER_NAME() THEN '$application' ELSE u.name END COLLATE Latin1_General_100_BIN2 AS PrincipalName,
        CASE p.class WHEN 1 THEN 'OBJECT' ELSE p.class_desc END COLLATE Latin1_General_100_BIN2 AS SecurableClass,
        CASE p.class WHEN 0 THEN DB_NAME() WHEN 3 THEN SCHEMA_NAME(p.major_id)
        WHEN 1 THEN OBJECT_SCHEMA_NAME(p.major_id)+'.'+OBJECT_NAME(p.major_id) ELSE 'UNSUPPORTED' END COLLATE Latin1_General_100_BIN2 AS TargetName,
        p.permission_name COLLATE Latin1_General_100_BIN2 AS PermissionName,p.state COLLATE Latin1_General_100_BIN2 AS GrantState,p.minor_id AS MinorID
        FROM sys.database_permissions p JOIN sys.database_principals u ON u.principal_id=p.grantee_principal_id
        WHERE u.name='ExportLegacyEntryReader'
        UNION ALL SELECT 'master','$application',CASE p.class WHEN 1 THEN 'OBJECT' ELSE p.class_desc END,
        CASE p.class WHEN 1 THEN 'dbo.'+OBJECT_NAME(p.major_id,DB_ID('master')) ELSE 'UNSUPPORTED' END,p.permission_name,p.state,p.minor_id
        FROM master.sys.database_permissions p JOIN master.sys.database_principals u ON u.principal_id=p.grantee_principal_id
        WHERE u.sid=SUSER_SID() AND p.class=1
        UNION ALL SELECT 'master','$application','SERVER','',p.permission_name,p.state,0
        FROM sys.server_permissions p JOIN sys.server_principals u ON u.principal_id=p.grantee_principal_id
        WHERE u.sid=SUSER_SID() AND NOT(p.class=100 AND p.major_id=0 AND p.permission_name='CONNECT SQL' AND p.state='G')""",
        (),
    )
    result["memberships"] = (
        """SELECT u.name COLLATE Latin1_General_100_BIN2 AS PrincipalName,
        r.name COLLATE Latin1_General_100_BIN2 AS RoleName
        FROM sys.database_role_members m JOIN sys.database_principals u ON u.principal_id=m.member_principal_id
        JOIN sys.database_principals r ON r.principal_id=m.role_principal_id
        WHERE u.name=USER_NAME() OR u.name='ExportLegacyEntryReader'
        UNION ALL SELECT '$master' COLLATE Latin1_General_100_BIN2,r.name COLLATE Latin1_General_100_BIN2 FROM master.sys.database_role_members m
        JOIN master.sys.database_principals u ON u.principal_id=m.member_principal_id
        JOIN master.sys.database_principals r ON r.principal_id=m.role_principal_id WHERE u.sid=SUSER_SID()
        UNION ALL SELECT '$server' COLLATE Latin1_General_100_BIN2,r.name COLLATE Latin1_General_100_BIN2 FROM sys.server_role_members m
        JOIN sys.server_principals u ON u.principal_id=m.member_principal_id
        JOIN sys.server_principals r ON r.principal_id=m.role_principal_id WHERE u.sid=SUSER_SID()""",
        (),
    )
    result["application_grants"] = (
        """SELECT DB_NAME() COLLATE Latin1_General_100_BIN2 AS DatabaseName,
        CASE p.class WHEN 1 THEN 'OBJECT' ELSE p.class_desc END COLLATE Latin1_General_100_BIN2 AS SecurableClass,
        CASE p.class WHEN 0 THEN DB_NAME() WHEN 3 THEN SCHEMA_NAME(p.major_id)
        WHEN 1 THEN OBJECT_SCHEMA_NAME(p.major_id)+'.'+OBJECT_NAME(p.major_id) ELSE 'UNSUPPORTED' END COLLATE Latin1_General_100_BIN2 AS TargetName,
        p.permission_name COLLATE Latin1_General_100_BIN2 AS PermissionName,p.state COLLATE Latin1_General_100_BIN2 AS GrantState,
        CASE WHEN p.class=1 AND p.minor_id>0 THEN COL_NAME(p.major_id,p.minor_id) END COLLATE Latin1_General_100_BIN2 AS ColumnName
        FROM sys.database_permissions p JOIN sys.database_principals u ON u.principal_id=p.grantee_principal_id
        WHERE u.principal_id=USER_ID()
        UNION ALL SELECT 'master',CASE p.class WHEN 1 THEN 'OBJECT' ELSE p.class_desc END,
        CASE p.class WHEN 0 THEN 'master' WHEN 3 THEN (SELECT name FROM master.sys.schemas WHERE schema_id=p.major_id)
        WHEN 1 THEN CASE WHEN p.major_id IN(OBJECT_ID('master.dbo.xp_cmdshell'),OBJECT_ID('master.dbo.xp_fileexist')) THEN 'dbo'
        ELSE (SELECT s.name FROM master.sys.objects o JOIN master.sys.schemas s ON s.schema_id=o.schema_id WHERE o.object_id=p.major_id) END+'.'+OBJECT_NAME(p.major_id,DB_ID('master')) ELSE 'UNSUPPORTED' END,
        p.permission_name,p.state,
        CASE WHEN p.class=1 AND p.minor_id>0 THEN (SELECT name FROM master.sys.columns WHERE object_id=p.major_id AND column_id=p.minor_id) END
        FROM master.sys.database_permissions p JOIN master.sys.database_principals u ON u.principal_id=p.grantee_principal_id
        WHERE u.sid=SUSER_SID()""",
        (),
    )
    result["token_grants"] = (
        """SELECT p.class_desc COLLATE Latin1_General_100_BIN2 AS SecurableClass,
        CASE p.class WHEN 0 THEN DB_NAME() WHEN 3 THEN SCHEMA_NAME(p.major_id)
        WHEN 1 THEN OBJECT_SCHEMA_NAME(p.major_id)+'.'+OBJECT_NAME(p.major_id) ELSE 'UNSUPPORTED' END COLLATE Latin1_General_100_BIN2 AS TargetName,
        p.permission_name COLLATE Latin1_General_100_BIN2 AS PermissionName,p.state COLLATE Latin1_General_100_BIN2 AS GrantState
        FROM sys.database_permissions p JOIN sys.user_token t ON t.principal_id=p.grantee_principal_id
        WHERE p.state IN('G','W') AND (p.state='W' OR p.permission_name='TAKE OWNERSHIP' OR p.permission_name LIKE 'ALTER%'
        OR p.permission_name LIKE 'CREATE%' OR p.permission_name LIKE 'CONTROL%' OR p.permission_name LIKE 'IMPERSONATE%')
        UNION ALL SELECT p.class_desc,'',p.permission_name,p.state FROM sys.server_permissions p
        JOIN sys.login_token t ON t.principal_id=p.grantee_principal_id WHERE p.state IN('G','W') AND
        (p.state='W' OR p.permission_name='TAKE OWNERSHIP' OR p.permission_name LIKE 'ALTER%' OR p.permission_name LIKE 'CREATE%'
        OR p.permission_name LIKE 'CONTROL%' OR p.permission_name LIKE 'IMPERSONATE%')""",
        (),
    )
    result["migration"] = (base["migration"][0], (DIRECT_MIGRATION,))
    return result


def _exact(actual, expected):
    return sorted(json.dumps(r, sort_keys=True) for r in actual) == sorted(
        json.dumps(r, sort_keys=True) for r in expected
    )


def verify(observed, approved, *, profile):
    from services.export_execution_dal import legacy_definition_hash, legacy_permission_queries

    validate_contract(approved)
    if profile != "application":
        raise SourceConflict("Direct privileges require the explicit shared application profile.")
    source = approved["source"]
    query_set = legacy_permission_queries(source)
    if (
        not isinstance(observed, dict)
        or set(observed) != {"version", *query_set}
        or type(observed["version"]) is not int
        or observed["version"] != 2
        or any(
            not isinstance(observed[k], list) or any(not isinstance(r, dict) for r in observed[k])
            for k in query_set
        )
    ):
        raise SourceConflict("Complete direct-permission observation required.")
    expected_target = dict(
        ServerName=approved["server"],
        DatabaseName="ROK_TRACKER",
        Principal=approved["principal"],
        LoginName=approved["principal"],
        LoginSID=approved["login_sid"],
        DefaultSchema="dbo",
        MajorVersion=16,
        Sysadmin=0,
        DatabaseOwner=0,
        ViewDefinition=1,
        EntryRole=1,
        ReaderRole=0,
        AuthorityRole=1,
        ImpersonateUser=0,
        ImpersonateLogin=0,
    )
    if observed["target"] != [expected_target]:
        raise SourceConflict("Direct application target/login/SID or roles differ.")
    modules = {m["name"]: m for m in source["modules"]}
    if len(observed["modules"]) != len(modules) or {
        m.get("ObjectName") for m in observed["modules"]
    } != set(modules):
        raise SourceConflict("Exact reviewed legacy module closure required.")
    for row in observed["modules"]:
        m = modules[row["ObjectName"]]
        if (
            set(row)
            != {
                "ObjectName",
                "ObjectType",
                "ModuleDefinition",
                "AnsiNulls",
                "QuotedIdentifier",
                "ExecuteAsPrincipal",
                "OwnerName",
            }
            or row["ObjectType"] != m["object_type"]
            or row["OwnerName"] != "dbo"
            or row["ExecuteAsPrincipal"] != m["execute_as"]
            or type(row["AnsiNulls"]) is not int
            or row["AnsiNulls"] != 1
            or type(row["QuotedIdentifier"]) is not int
            or row["QuotedIdentifier"] != 1
            or legacy_definition_hash(row["ModuleDefinition"])
            not in (m["definition_sha256"], *m.get("compatible_definition_sha256", []))
        ):
            raise SourceConflict("Direct legacy module source/context/owner differs.")
    grants = source["grants"]
    expected_grants = [
        dict(
            DatabaseName=g["database"],
            PrincipalName=g["principal"],
            SecurableClass=g["securable_class"],
            TargetName=g["target"],
            PermissionName=g["permission"],
            GrantState="G",
            MinorID=0,
        )
        for g in grants
    ]
    allowed = {(g["securable_class"], g["target"], g["permission"]) for g in grants}
    caps = json.loads(query_set["capabilities"][1][0])
    expected_caps = [
        dict(
            SecurableClass=c["kind"],
            TargetName=c["target"],
            PermissionName=c["permission"],
            Allowed=int((c["kind"], c["target"] or "", c["permission"]) in allowed),
        )
        for c in caps
    ]
    expected_module_rights = [
        dict(
            ObjectName=n,
            PermissionName=right,
            Allowed=int(
                (right == "EXECUTE" and n in source["roots"])
                or (right == "ALTER" and n.startswith("dbo."))
            ),
        )
        for n in modules
        for right in ("EXECUTE", "ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    expected_token = [
        dict(
            SecurableClass=(
                "OBJECT_OR_COLUMN" if g["securable_class"] == "OBJECT" else g["securable_class"]
            ),
            TargetName=g["target"],
            PermissionName=g["permission"],
            GrantState="G",
        )
        for g in grants
        if g["database"] == "ROK_TRACKER" and g["permission"].startswith(("ALTER", "CREATE"))
    ]
    expected_memberships = [
        dict(PrincipalName=approved["principal"], RoleName=r)
        for r in ("ExportExecutionAuthority", "ExportLegacyEntryReader")
    ]
    if (
        not _exact(observed["grants"], expected_grants)
        or not _exact(observed["application_grants"], application_grant_rows())
        or not _exact(observed["capabilities"], expected_caps)
        or not _exact(observed["module_permissions"], expected_module_rights)
        or not _exact(observed["token_grants"], expected_token)
        or not _exact(observed["memberships"], expected_memberships)
        or not _exact(
            observed["ownership"],
            [dict(OwnedSchemas=0, OwnedObjects=0, OwnedPrincipals=0, OwnedServerPrincipals=0)],
        )
    ):
        raise SourceConflict("Direct privileges differ from the exact reviewed grant plan.")
    if not _exact(
        observed["migration"],
        [
            dict(
                MigrationId=DIRECT_MIGRATION,
                ChecksumSha256=approved["migration_hash"],
                Status="Applied",
            )
        ],
    ):
        raise SourceConflict("Exact direct-permission migration receipt required.")
    if digest(observed).hex() != approved["metadata_hash"]:
        raise SourceConflict(
            "Direct permission metadata differs from protected approved fingerprint."
        )
    return digest(observed).hex()
