"""Explicit operator-approved legacy direct permissions; never a signing fallback."""

import json
from pathlib import Path
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest

DIRECT_SOURCE_HASH = "31d158bce8d33440eafb5e12ad4d38d6e55b01d0a090f67051444ba2b48e6a55"
DIRECT_MIGRATION = "20261003_001_export_legacy_direct_permissions"
APPLICATION_GRANT_PLAN_HASH = "932a98e47066943408781d6aa29bd7cba08acc16d0e3e8e6a1318021f3eaabb7"
FILE_VISIBILITY_MIGRATION = "20261008_001_sql_auth_import_file_visibility"
FILE_VISIBILITY_CHECKSUM = "dde9189ac05cb699b2114775eef5769b7ab7e629b63d4c1681427d53ed3c5aaf"
STATS_OUTCOME_MIGRATION = "20261009_001_stats_import_outcomes"
STATS_OUTCOME_CHECKSUM = "6e0bb2c04a5fe4e8e4eb67e821b3d7c490f474b5188a59c5892c25c68e5a885c"
# Canonical UTF-16LE definition hashes of the reviewed migration's exact
# postimages. This is a behavior amendment, not a compatibility spelling.
FILE_VISIBILITY_MODULE_HASHES = {
    "dbo.ARCHIVE_IMPORT_STAGING_FILE": "38728ea3d84bc6ab29b285b25c8b8ecfd68b3bef60efa056839c8a1333838a19",
    "dbo.CLAIM_KS4_IMPORT_FILE": "9c943af3c4cb0de499177a4144a962ee8049defda8dfcb6cc52077899d85516a",
    "dbo.IMPORT_STAGING_PROC_CORE": "5ee53d89a555d6e44c3953d92acafe67ad832c9523dc0b7cdd594f9152fe4bfb",
}


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
    amended = isinstance(approved, dict) and "module_amendment" in approved
    if amended:
        fields.add("module_amendment")
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
        or (
            amended
            and (
                approved["module_amendment"] != FILE_VISIBILITY_MIGRATION
                or not set(FILE_VISIBILITY_MODULE_HASHES)
                <= {m["name"] for m in approved["source"]["modules"]}
            )
        )
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
        WHERE u.sid=SUSER_SID() AND NOT(p.class=100 AND p.major_id=0 AND p.permission_name='CONNECT SQL' AND p.state='G')
        ORDER BY DatabaseName,PrincipalName,SecurableClass,TargetName,PermissionName,GrantState,MinorID""",
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
        JOIN sys.server_principals r ON r.principal_id=m.role_principal_id WHERE u.sid=SUSER_SID()
        ORDER BY PrincipalName,RoleName""",
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
        WHERE u.sid=SUSER_SID()
        ORDER BY DatabaseName,SecurableClass,TargetName,PermissionName,GrantState,ColumnName""",
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
        OR p.permission_name LIKE 'CONTROL%' OR p.permission_name LIKE 'IMPERSONATE%')
        ORDER BY SecurableClass,TargetName,PermissionName,GrantState""",
        (),
    )
    # The new source pin requires the outcome migration. Historical migration
    # receipts remain separate; no installed hash can select its own contract.
    result["migration"] = (
        base["migration"][0].replace(
            "WHERE MigrationId=?", "WHERE MigrationId IN (?,?,?) ORDER BY MigrationId"
        ),
        (DIRECT_MIGRATION, FILE_VISIBILITY_MIGRATION, STATS_OUTCOME_MIGRATION),
    )
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
    amended = approved.get("module_amendment") == FILE_VISIBILITY_MIGRATION
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
        expected_definitions = (
            (FILE_VISIBILITY_MODULE_HASHES[row["ObjectName"]],)
            if amended and row["ObjectName"] in FILE_VISIBILITY_MODULE_HASHES
            else (m["definition_sha256"], *m.get("compatible_definition_sha256", []))
        )
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
            or legacy_definition_hash(row["ModuleDefinition"]) not in expected_definitions
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
    expected_migrations = [
        dict(
            MigrationId=DIRECT_MIGRATION,
            ChecksumSha256=approved["migration_hash"],
            Status="Applied",
        ),
        dict(
            MigrationId=STATS_OUTCOME_MIGRATION,
            ChecksumSha256=STATS_OUTCOME_CHECKSUM,
            Status="Applied",
        ),
    ]
    if amended:
        expected_migrations.append(
            dict(
                MigrationId=FILE_VISIBILITY_MIGRATION,
                ChecksumSha256=FILE_VISIBILITY_CHECKSUM,
                Status="Applied",
            )
        )
    if not _exact(observed["migration"], expected_migrations):
        raise SourceConflict("Exact direct-permission migration receipt required.")
    if digest(observed).hex() != approved["metadata_hash"]:
        raise SourceConflict(
            "Direct permission metadata differs from protected approved fingerprint."
        )
    return digest(observed).hex()
