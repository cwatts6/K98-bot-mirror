"""S11 evidence APIs. Connections are explicit; unknown commits are never retried.

Authority transitions own short SQL transactions. Proof consumption instead uses
the caller's existing settlement transaction under the account/resource locks.
"""

from datetime import datetime
import hashlib
import json
import re
from uuid import UUID

from kvk.dal.new_source_import_dal import SourceConflict, digest, one, rows
from services.export_coordination_dal import bounded_json

_PARAMETERS = {
    "session": (
        "SessionID",
        "Action",
        "ExpectedVersion",
        "HostIdentity",
        "BootID",
        "ExecutableHash",
        "ManifestHash",
    ),
    "stream": (
        "SessionID",
        "StreamID",
        "Action",
        "ExpectedVersion",
        "AccountKey",
        "OwnerKind",
        "ObjectID",
        "OwnerID",
        "Fence",
        "ClaimVersion",
        "NestedToken",
        "RegistrationHash",
        "Epoch",
        "SnapshotHash",
        "ScopeJson",
        "Purpose",
        "ChildIdentity",
        "ClosureHash",
        "ClosureReference",
        "EventDigest",
        "LastSequence",
    ),
    "event": (
        "SessionID",
        "StreamID",
        "AccountKey",
        "ExpectedVersion",
        "RequestID",
        "EventID",
        "State",
        "EvidenceHash",
        "EvidenceReference",
        "Operation",
        "RequestKind",
        "TargetID",
        "PayloadHash",
        "PayloadReference",
    ),
    "proof": (
        "SessionID",
        "ProofID",
        "AccountKey",
        "SnapshotHash",
        "RegistrationHash",
        "ProofKind",
        "Outcome",
        "MembershipJson",
        "EvidenceJson",
    ),
    "enrollment": (
        "SessionID",
        "PreparationID",
        "Action",
        "ExpectedVersion",
        "AccountKey",
        "OwnerID",
        "Fence",
        "ResourcesJson",
        "PlanJson",
        "Actor",
        "Reason",
        "Ordinal",
        "FileID",
        "CreationStreamID",
        "CreationRequestID",
        "ResponseEventID",
        "OriginHash",
        "OriginReference",
        "VerificationStreamID",
        "EligibilityHash",
        "EligibilityReference",
    ),
}
_PROCEDURES = {
    "session": "dbo.usp_ExportExecutionSessionTransition",
    "stream": "dbo.usp_ExportExecutionStreamTransition",
    "event": "dbo.usp_ExportProviderRequestEventAppend",
    "proof": "dbo.usp_ExportReconciliationProofIssue",
    "enrollment": "dbo.usp_ExportOutputEnrollmentTransition",
}

# Source-of-truth: the S10A/C/D/E migrations and the additive S11 migration in
# K98-bot-SQL-Server. An approved contract may not omit one of these dependencies.
INSTALLATION_MIGRATIONS = (
    "20260914_001_shared_export_coordination",
    "20260914_002_legacy_export_preparation",
    "20260915_001_kvk_output_pool_rollover",
    "20260915_002_kvk_output_operation_ownership",
    "20260924_001_export_execution_evidence",
)
EVIDENCE_TABLES = tuple(
    "dbo." + name
    for name in (
        "ExportExecutionSession",
        "ExportExecutionStream",
        "ExportProviderRequest",
        "ExportProviderRequestEvent",
        "ExportReconciliationProof",
        "ExportManagedFileOrigin",
    )
)
INSTALLATION_OBJECTS = {
    **{
        "dbo." + name: "U"
        for name in (
            "ExportJob",
            "ExportResource",
            "ExportJobResource",
            "ExportRequestBudget",
            "ExportAttempt",
            "ExportAttemptPart",
            "ExportPreparation",
            "ExportPreparationResource",
            "ExportExecutionSession",
            "ExportExecutionStream",
            "ExportProviderRequest",
            "ExportProviderRequestEvent",
            "ExportReconciliationProof",
            "ExportManagedFileOrigin",
        )
    },
    **{
        "KVK." + name: "U"
        for name in (
            "SeasonSource",
            "SourceRouting",
            "SourceExportIntent",
            "SourcePublication",
            "SourceDelivery",
            "SourceOutputFile",
            "SourceOutputPool",
            "SourceOutputSlot",
            "SourceOutputDisposition",
            "SourceOutputOperation",
            "SourceOutputOperationResource",
        )
    },
    **{name: "P" for name in _PROCEDURES.values()},
}

# Exact writes used by the existing coordination/pool DALs. The three S8 domain
# entries preserve their existing source-selection/configuration/publication
# callers; they do not authorize activation or invent a new writer.
BOT_COORDINATION_WRITES = {
    "dbo.ExportJob": ("INSERT", "UPDATE"),
    "dbo.ExportResource": ("INSERT", "UPDATE"),
    "dbo.ExportJobResource": ("INSERT",),
    "dbo.ExportRequestBudget": ("INSERT", "UPDATE"),
    "dbo.ExportAttempt": ("INSERT", "UPDATE"),
    "dbo.ExportAttemptPart": ("INSERT", "UPDATE"),
    "dbo.ExportPreparation": ("INSERT", "UPDATE"),
    "dbo.ExportPreparationResource": ("INSERT",),
    "KVK.SeasonSource": ("INSERT", "UPDATE"),
    "KVK.SourceRouting": ("INSERT",),
    "KVK.SourceExportIntent": ("INSERT", "UPDATE"),
    "KVK.SourcePublication": ("INSERT", "UPDATE"),
    "KVK.SourceDelivery": ("INSERT", "UPDATE"),
    "KVK.SourceOutputPool": ("UPDATE",),
    "KVK.SourceOutputSlot": ("UPDATE",),
    "KVK.SourceOutputDisposition": ("INSERT",),
    "KVK.SourceOutputOperation": ("INSERT", "UPDATE"),
    "KVK.SourceOutputOperationResource": ("INSERT",),
}
AUTHORITY_COORDINATION_WRITES = {"dbo.ExportRequestBudget": ("INSERT", "UPDATE")}
LOCK_PROCEDURES = ("sys.sp_getapplock", "sys.sp_releaseapplock")
INSTALLATION_PERMISSIONS = {
    **{
        name: ("SELECT", "INSERT", "UPDATE", "DELETE", "ALTER", "CONTROL", "TAKE OWNERSHIP")
        for name, kind in INSTALLATION_OBJECTS.items()
        if kind == "U"
    },
    **{name: ("EXECUTE", "ALTER", "CONTROL", "TAKE OWNERSHIP") for name in _PROCEDURES.values()},
    **{name: ("EXECUTE",) for name in LOCK_PROCEDURES},
}


def installation_permissions(profile):
    """Fixed object capabilities for this export contract, never caller grants.

    `reader` means evidence-reader plus the Bot's existing coordination writes.
    Other source/import/configuration dependencies require separate readiness;
    this bounded object set is not a whole-application permission certificate.
    """
    if profile not in {"authority", "reader"}:
        raise ValueError("Unknown installation permission profile.")
    writes = AUTHORITY_COORDINATION_WRITES if profile == "authority" else BOT_COORDINATION_WRITES
    return {
        (name, None, permission): int(
            permission == "SELECT"
            or permission in writes.get(name, ())
            or (permission == "EXECUTE" and (profile == "authority" or name in LOCK_PROCEDURES))
        )
        for name, permissions in INSTALLATION_PERMISSIONS.items()
        for permission in permissions
    }


# IDs never leave SQL metadata collection: fingerprints use schema/object/column
# names, definitions and ordered contract fields, not installation-specific IDs.
_METADATA_QUERIES = {
    "objects": """SELECT SCHEMA_NAME(o.schema_id)+'.'+o.name AS ObjectName,
        RTRIM(o.type) AS ObjectType, m.definition AS ModuleDefinition,
        m.uses_ansi_nulls AS AnsiNulls, m.uses_quoted_identifier AS QuotedIdentifier,
        m.execute_as_principal_id AS ExecuteAsPrincipal,
        t.is_memory_optimized AS MemoryOptimized, t.temporal_type AS TemporalType
        FROM sys.objects o LEFT JOIN sys.sql_modules m ON m.object_id=o.object_id
        LEFT JOIN sys.tables t ON t.object_id=o.object_id
        WHERE o.object_id IN (SELECT object_id FROM required)
        ORDER BY SCHEMA_NAME(o.schema_id) COLLATE Latin1_General_100_BIN2,o.name COLLATE Latin1_General_100_BIN2""",
    "columns": """SELECT OBJECT_SCHEMA_NAME(c.object_id)+'.'+OBJECT_NAME(c.object_id) AS ObjectName,
        c.column_id AS Ordinal,c.name AS ColumnName,SCHEMA_NAME(t.schema_id)+'.'+t.name AS TypeName,
        c.max_length AS MaxLength,c.precision AS [Precision],c.scale AS Scale,c.collation_name AS Collation,
        c.is_nullable AS Nullable,c.is_identity AS IsIdentity,c.is_computed AS IsComputed,
        c.is_rowguidcol AS IsRowGuid,c.is_sparse AS IsSparse,c.generated_always_type AS GeneratedAlways,
        d.name AS DefaultName,d.definition AS DefaultDefinition,cc.definition AS ComputedDefinition,
        cc.is_persisted AS ComputedPersisted,CONVERT(nvarchar(128),ic.seed_value) AS IdentitySeed,
        CONVERT(nvarchar(128),ic.increment_value) AS IdentityIncrement
        FROM sys.columns c JOIN sys.types t ON t.user_type_id=c.user_type_id
        LEFT JOIN sys.default_constraints d ON d.object_id=c.default_object_id
        LEFT JOIN sys.computed_columns cc ON cc.object_id=c.object_id AND cc.column_id=c.column_id
        LEFT JOIN sys.identity_columns ic ON ic.object_id=c.object_id AND ic.column_id=c.column_id
        WHERE c.object_id IN (SELECT object_id FROM required)
        ORDER BY OBJECT_SCHEMA_NAME(c.object_id) COLLATE Latin1_General_100_BIN2,OBJECT_NAME(c.object_id) COLLATE Latin1_General_100_BIN2,c.column_id""",
    "indexes": """SELECT OBJECT_SCHEMA_NAME(i.object_id)+'.'+OBJECT_NAME(i.object_id) AS ObjectName,
        i.name AS IndexName,i.type AS IndexType,i.is_unique AS IsUnique,i.is_primary_key AS IsPrimaryKey,
        i.is_unique_constraint AS IsUniqueConstraint,i.is_disabled AS Disabled,
        i.is_hypothetical AS Hypothetical,i.ignore_dup_key AS IgnoreDuplicateKey,
        i.has_filter AS HasFilter,i.filter_definition AS FilterDefinition,
        ic.index_column_id AS Ordinal,c.name AS ColumnName,ic.key_ordinal AS KeyOrdinal,
        ic.partition_ordinal AS PartitionOrdinal,ic.is_descending_key AS DescendingKey,
        ic.is_included_column AS IncludedColumn
        FROM sys.indexes i LEFT JOIN sys.index_columns ic
          ON ic.object_id=i.object_id AND ic.index_id=i.index_id
        LEFT JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
        WHERE i.object_id IN (SELECT object_id FROM required)
        ORDER BY OBJECT_SCHEMA_NAME(i.object_id) COLLATE Latin1_General_100_BIN2,OBJECT_NAME(i.object_id) COLLATE Latin1_General_100_BIN2,i.name COLLATE Latin1_General_100_BIN2,ic.index_column_id""",
    "checks": """SELECT OBJECT_SCHEMA_NAME(parent_object_id)+'.'+OBJECT_NAME(parent_object_id) AS ObjectName,
        name AS ConstraintName,definition AS Definition,is_disabled AS Disabled,
        is_not_trusted AS Untrusted,is_not_for_replication AS NotForReplication
        FROM sys.check_constraints WHERE parent_object_id IN (SELECT object_id FROM required)
        ORDER BY OBJECT_SCHEMA_NAME(parent_object_id) COLLATE Latin1_General_100_BIN2,OBJECT_NAME(parent_object_id) COLLATE Latin1_General_100_BIN2,name COLLATE Latin1_General_100_BIN2""",
    "foreign_keys": """SELECT OBJECT_SCHEMA_NAME(f.parent_object_id)+'.'+OBJECT_NAME(f.parent_object_id) AS ObjectName,
        f.name AS ConstraintName,fc.constraint_column_id AS Ordinal,c.name AS ColumnName,
        OBJECT_SCHEMA_NAME(f.referenced_object_id)+'.'+OBJECT_NAME(f.referenced_object_id) AS ReferencedObject,
        rc.name AS ReferencedColumn,f.delete_referential_action AS DeleteAction,
        f.update_referential_action AS UpdateAction,f.is_disabled AS Disabled,
        f.is_not_trusted AS Untrusted,f.is_not_for_replication AS NotForReplication
        FROM sys.foreign_keys f JOIN sys.foreign_key_columns fc ON fc.constraint_object_id=f.object_id
        JOIN sys.columns c ON c.object_id=f.parent_object_id AND c.column_id=fc.parent_column_id
        JOIN sys.columns rc ON rc.object_id=f.referenced_object_id AND rc.column_id=fc.referenced_column_id
        WHERE f.parent_object_id IN (SELECT object_id FROM required)
        ORDER BY OBJECT_SCHEMA_NAME(f.parent_object_id) COLLATE Latin1_General_100_BIN2,OBJECT_NAME(f.parent_object_id) COLLATE Latin1_General_100_BIN2,f.name COLLATE Latin1_General_100_BIN2,fc.constraint_column_id""",
    "triggers": """SELECT OBJECT_SCHEMA_NAME(t.parent_id)+'.'+OBJECT_NAME(t.parent_id) AS ObjectName,
        t.name AS TriggerName,t.is_disabled AS Disabled,t.is_instead_of_trigger AS InsteadOf,
        t.is_not_for_replication AS NotForReplication,m.definition AS ModuleDefinition,
        m.uses_ansi_nulls AS AnsiNulls,m.uses_quoted_identifier AS QuotedIdentifier,
        m.execute_as_principal_id AS ExecuteAsPrincipal
        FROM sys.triggers t LEFT JOIN sys.sql_modules m ON m.object_id=t.object_id
        WHERE t.parent_id IN (SELECT object_id FROM required)
        ORDER BY OBJECT_SCHEMA_NAME(t.parent_id) COLLATE Latin1_General_100_BIN2,OBJECT_NAME(t.parent_id) COLLATE Latin1_General_100_BIN2,t.name COLLATE Latin1_General_100_BIN2""",
}
INSTALLATION_METADATA = frozenset(_METADATA_QUERIES)


class EvidenceCommitUnknown(SourceConflict):
    """Read immutable identity; do not resend a provider operation after this error."""


def _proof_request(values):
    """Validate persistence inputs, without attesting provider truth or coverage."""
    from services.export_execution_protocol import decode, proof_membership, uuid_text

    if set(values) != set(_PARAMETERS["proof"]):
        raise ValueError("Complete immutable proof identity required.")
    values = dict(values)
    for name in ("SessionID", "ProofID"):
        uuid_text(values[name])
    account = values["AccountKey"]
    if not isinstance(account, str) or not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", account):
        raise ValueError("Exact proof account required.")
    for name in ("SnapshotHash", "RegistrationHash"):
        value = values[name]
        if not isinstance(value, (bytes, bytearray, memoryview)) or len(bytes(value)) != 32:
            raise ValueError("Exact proof hash required.")
        values[name] = bytes(value)
    allowed = {
        "publication": ("confirmed", "absent", "damaged"),
        "retirement": ("confirmed",),
        "retirement_recovery": ("confirmed",),
        "rollover_drain": ("confirmed",),
        "rollover_complete": ("completed",),
    }
    kind, outcome = values["ProofKind"], values["Outcome"]
    if not isinstance(kind, str) or outcome not in allowed.get(kind, ()):
        raise ValueError("Supported proof kind/outcome required.")
    proof_membership(values["MembershipJson"])
    raw = values["EvidenceJson"]
    if not isinstance(raw, str) or len(raw.encode("utf-16-le")) > 65536:
        raise ValueError("Bounded proof evidence required.")
    evidence = decode(raw.encode("utf-8"))
    if (
        evidence.get("state") != outcome
        or evidence.get("snapshot_hash") != values["SnapshotHash"].hex()
    ):
        raise ValueError("Proof evidence differs from immutable outcome/snapshot.")
    # Keep the original JSON text: receipts and the SQL membership hash bind it.
    return values


def _proof_acknowledgment(values, result, columns):
    """Accept only the exact issued row, after the procedure batch has completed."""
    from services.export_execution_protocol import uuid_text

    expected = set(_PARAMETERS["proof"]) | {"MembershipHash", "CreatedUTC"}
    if len(columns) != len(expected) or set(columns) != expected:
        raise EvidenceCommitUnknown("Proof acknowledgment shape differs.")
    result = dict(result)
    for name in ("SessionID", "ProofID"):
        value = result[name]
        if not isinstance(value, (str, UUID)):
            raise EvidenceCommitUnknown("Proof acknowledgment identity differs.")
        # SQL uniqueidentifier may arrive as uppercase text or a native UUID.
        result[name] = uuid_text(str(value).lower())
    for name in ("SnapshotHash", "RegistrationHash", "MembershipHash"):
        value = result[name]
        if not isinstance(value, (bytes, bytearray, memoryview)) or len(bytes(value)) != 32:
            raise EvidenceCommitUnknown("Proof acknowledgment hash differs.")
        result[name] = bytes(value)
    if (
        any(result[name] != value for name, value in values.items())
        or result["MembershipHash"]
        != hashlib.sha256(values["MembershipJson"].encode("utf-16-le")).digest()
        or not isinstance(result["CreatedUTC"], datetime)
    ):
        raise EvidenceCommitUnknown("Proof acknowledgment differs from the exact request.")
    return result


# S11 source-manifest pin is generated from the separately reviewed SQL delivery.
# It is not learned from the installed database or accepted from a Bot IPC caller.
LEGACY_PERMISSION_SOURCE_HASH = "d7a5c11769acc6427a5fa1bf2fb00b9b6d4e3bbdc840f34455aaabd8040ed3de"
# Canonical path/name/type/raw-file hashes for all 538 current authoritative
# sql_schema scripts, including the separate uninstalled S11 delivery. This is
# source identity, not an observed installation or permission allowlist.
APPLICATION_SCHEMA_SOURCE_HASH = "0fcc6360f17cc6017801b074117b6b7d6fb8ebb0bd808d686971511b350a27d2"
LEGACY_PERMISSION_MIGRATION = "20260924_002_export_legacy_module_permissions"
LEGACY_DATABASE_CAPABILITIES = (
    "CONTROL",
    "ALTER ANY ROLE",
    "ALTER ANY USER",
    "IMPERSONATE ANY USER",
    "ALTER ANY SCHEMA",
    "ALTER ANY CERTIFICATE",
    "ALTER ANY ASYMMETRIC KEY",
    "ALTER ANY ASSEMBLY",
    "ALTER ANY DATABASE DDL TRIGGER",
    "CREATE TABLE",
    "CREATE VIEW",
    "CREATE PROCEDURE",
    "CREATE FUNCTION",
    "CREATE SYNONYM",
    "CREATE SCHEMA",
    "CREATE ASSEMBLY",
    "CREATE TYPE",
    "CREATE CERTIFICATE",
)
LEGACY_SERVER_CAPABILITIES = (
    "CONTROL SERVER",
    "IMPERSONATE ANY LOGIN",
    "ALTER ANY LOGIN",
    "ALTER ANY SERVER ROLE",
    "ALTER ANY DATABASE",
    "ALTER SETTINGS",
    "CREATE ANY DATABASE",
    "EXTERNAL ACCESS ASSEMBLY",
    "UNSAFE ASSEMBLY",
    "ADMINISTER BULK OPERATIONS",
)


def legacy_definition_hash(definition):
    """Compare source bodies; exported signatures still require exact installed bytes."""
    if not isinstance(definition, str) or not definition.strip():
        raise SourceConflict("Visible legacy module definition required.")
    canonical = definition.replace("\r\n", "\n").strip(" \t\r\n")
    canonical = re.sub(r"^(?:ALTER|CREATE OR ALTER)\b", "CREATE", canonical)
    return hashlib.sha256(canonical.encode("utf-16-le")).hexdigest()


def validate_legacy_permission_source(source):
    try:
        if not isinstance(source, dict) or digest(source).hex() != LEGACY_PERMISSION_SOURCE_HASH:
            raise SourceConflict("Exact reviewed legacy SQL source manifest required.")
    except (TypeError, ValueError, OverflowError) as exc:
        raise SourceConflict("Exact reviewed legacy SQL source manifest required.") from exc


def legacy_permission_queries(source):
    """Fixed, read-only batches; the pinned manifest supplies names, never SQL text."""
    validate_legacy_permission_source(source)
    modules = json.dumps([m["name"] for m in source["modules"]])
    certificates = json.dumps(sorted({s["certificate"] for s in source["signatures"]}))
    capabilities = [
        dict(kind="DATABASE", target=source["database"], permission=p)
        for p in LEGACY_DATABASE_CAPABILITIES
    ] + [dict(kind="SERVER", target=None, permission=p) for p in LEGACY_SERVER_CAPABILITIES]
    capabilities += [
        dict(kind="SCHEMA", target=s, permission=p)
        for s in ("dbo", "KVK")
        for p in ("ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    capabilities += [
        dict(kind="CERTIFICATE", target=c, permission=p)
        for c in json.loads(certificates)
        for p in ("ALTER", "CONTROL", "TAKE OWNERSHIP")
    ]
    return {
        "target": (
            """SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS ServerName,
            DB_NAME() AS DatabaseName,USER_NAME() AS Principal,SCHEMA_NAME() AS DefaultSchema,
            CONVERT(int,SERVERPROPERTY('ProductMajorVersion')) AS MajorVersion,
            IS_SRVROLEMEMBER('sysadmin') AS Sysadmin,IS_MEMBER('db_owner') AS DatabaseOwner,
            HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','VIEW DEFINITION') AS ViewDefinition,
            IS_ROLEMEMBER('ExportLegacyEntryReader') AS EntryRole,
            IS_ROLEMEMBER('ExportExecutionReader') AS ReaderRole,
            IS_ROLEMEMBER('ExportExecutionAuthority') AS AuthorityRole""",
            (),
        ),
        "modules": (
            """SELECT r.value AS ObjectName,RTRIM(o.type) AS ObjectType,m.definition AS ModuleDefinition,
            CONVERT(int,m.uses_ansi_nulls) AS AnsiNulls,CONVERT(int,m.uses_quoted_identifier) AS QuotedIdentifier,
            m.execute_as_principal_id AS ExecuteAsPrincipal,
            USER_NAME(COALESCE(o.principal_id,s.principal_id)) AS OwnerName
            FROM OPENJSON(?) r LEFT JOIN sys.objects o ON o.object_id=OBJECT_ID(r.value)
            LEFT JOIN sys.schemas s ON s.schema_id=o.schema_id
            LEFT JOIN sys.sql_modules m ON m.object_id=o.object_id ORDER BY r.value COLLATE Latin1_General_100_BIN2""",
            (modules,),
        ),
        "signatures": (
            """SELECT OBJECT_SCHEMA_NAME(p.major_id)+'.'+OBJECT_NAME(p.major_id) AS ObjectName,
            c.name AS CertificateName,p.crypt_type AS CryptType,LOWER(CONVERT(varchar(64),p.thumbprint,2)) AS Thumbprint,
            LOWER(CONVERT(varchar(64),HASHBYTES('SHA2_256',p.crypt_property),2)) AS SignatureHash,
            f.is_signed AS IsSigned,f.is_signature_valid AS IsValid
            FROM sys.crypt_properties p LEFT JOIN sys.certificates c ON c.thumbprint=p.thumbprint
            OUTER APPLY (SELECT is_signed,is_signature_valid FROM sys.fn_check_object_signatures('certificate',c.thumbprint)
                WHERE entity_id=p.major_id) f
            WHERE p.class=1 AND (p.major_id IN (SELECT OBJECT_ID(value) FROM OPENJSON(?))
                OR c.name IN (SELECT value FROM OPENJSON(?)))
            ORDER BY ObjectName COLLATE Latin1_General_100_BIN2,CertificateName COLLATE Latin1_General_100_BIN2,CryptType""",
            (modules, certificates),
        ),
        "certificates": (
            """SELECT DB_NAME() AS DatabaseName,c.name AS CertificateName,USER_NAME(c.principal_id) AS OwnerName,
            c.pvt_key_encryption_type AS PrivateKeyType,LOWER(CONVERT(varchar(64),c.thumbprint,2)) AS Thumbprint,
            LOWER(CONVERT(varchar(64),HASHBYTES('SHA2_256',CERTENCODED(c.certificate_id)),2)) AS PublicKeyHash
            FROM sys.certificates c WHERE c.name IN (SELECT value FROM OPENJSON(?))
            ORDER BY DatabaseName,CertificateName""",
            (certificates,),
        ),
        "master_certificates": (
            """EXEC master.sys.sp_executesql N'SELECT DB_NAME() AS DatabaseName,name AS CertificateName,
            USER_NAME(principal_id) AS OwnerName,pvt_key_encryption_type AS PrivateKeyType,
            LOWER(CONVERT(varchar(64),thumbprint,2)) AS Thumbprint,
            LOWER(CONVERT(varchar(64),HASHBYTES(''SHA2_256'',CERTENCODED(certificate_id)),2)) AS PublicKeyHash
            FROM sys.certificates WHERE name=N''S11LegacyImport''';""",
            (),
        ),
        "grants": (
            """SELECT DB_NAME() COLLATE Latin1_General_100_BIN2 AS DatabaseName,u.name COLLATE Latin1_General_100_BIN2 AS PrincipalName,
            CASE p.class WHEN 1 THEN 'OBJECT' ELSE p.class_desc END COLLATE Latin1_General_100_BIN2 AS SecurableClass,
            CASE p.class WHEN 0 THEN DB_NAME() WHEN 3 THEN SCHEMA_NAME(p.major_id)
            WHEN 1 THEN OBJECT_SCHEMA_NAME(p.major_id)+'.'+OBJECT_NAME(p.major_id) ELSE 'UNSUPPORTED' END COLLATE Latin1_General_100_BIN2 AS TargetName,
            p.permission_name COLLATE Latin1_General_100_BIN2 AS PermissionName,p.state COLLATE Latin1_General_100_BIN2 AS GrantState,p.minor_id AS MinorID
            FROM sys.database_permissions p JOIN sys.database_principals u ON u.principal_id=p.grantee_principal_id
            WHERE u.name IN ('S11LegacyImportUser','S11LegacyTargetsUser','S11LegacyStatsUser','ExportLegacyEntryReader')
            UNION ALL SELECT 'master',u.name,CASE p.class WHEN 1 THEN 'OBJECT' ELSE p.class_desc END,
            CASE p.class WHEN 1 THEN 'dbo.'+OBJECT_NAME(p.major_id,DB_ID('master')) ELSE 'UNSUPPORTED' END,p.permission_name,p.state,p.minor_id
            FROM master.sys.database_permissions p JOIN master.sys.database_principals u ON u.principal_id=p.grantee_principal_id
            WHERE u.name='S11LegacyImportUser'
            UNION ALL SELECT 'master',u.name,'SERVER','',p.permission_name,p.state,0
            FROM sys.server_permissions p JOIN sys.server_principals u ON u.principal_id=p.grantee_principal_id
            WHERE u.name='S11LegacyImportLogin'
            ORDER BY DatabaseName,PrincipalName,SecurableClass,TargetName,PermissionName""",
            (),
        ),
        "principals": (
            """SELECT DB_NAME() COLLATE Latin1_General_100_BIN2 AS DatabaseName,u.name COLLATE Latin1_General_100_BIN2 AS PrincipalName,u.type COLLATE Latin1_General_100_BIN2 AS PrincipalType,
            LOWER(CONVERT(varchar(170),u.sid,2)) COLLATE Latin1_General_100_BIN2 AS PrincipalSID,LOWER(CONVERT(varchar(170),c.sid,2)) COLLATE Latin1_General_100_BIN2 AS CertificateSID,
            c.name COLLATE Latin1_General_100_BIN2 AS CertificateName
            FROM sys.database_principals u LEFT JOIN sys.certificates c ON c.sid=u.sid
            WHERE u.name IN ('S11LegacyImportUser','S11LegacyTargetsUser','S11LegacyStatsUser')
            UNION ALL SELECT 'master',u.name,u.type,LOWER(CONVERT(varchar(170),u.sid,2)),LOWER(CONVERT(varchar(170),c.sid,2)),c.name
            FROM master.sys.database_principals u LEFT JOIN master.sys.certificates c ON c.sid=u.sid WHERE u.name='S11LegacyImportUser'
            UNION ALL SELECT 'server',u.name,u.type,LOWER(CONVERT(varchar(170),u.sid,2)),LOWER(CONVERT(varchar(170),c.sid,2)),c.name
            FROM sys.server_principals u LEFT JOIN master.sys.certificates c ON c.sid=u.sid WHERE u.name='S11LegacyImportLogin'
            ORDER BY DatabaseName,PrincipalName""",
            (),
        ),
        "memberships": (
            """SELECT DB_NAME() COLLATE Latin1_General_100_BIN2 AS DatabaseName,u.name COLLATE Latin1_General_100_BIN2 AS PrincipalName,r.name COLLATE Latin1_General_100_BIN2 AS RoleName
            FROM sys.database_role_members m JOIN sys.database_principals u ON u.principal_id=m.member_principal_id
            JOIN sys.database_principals r ON r.principal_id=m.role_principal_id
            WHERE u.name IN ('S11LegacyImportUser','S11LegacyTargetsUser','S11LegacyStatsUser','ExportLegacyEntryReader')
            UNION ALL SELECT 'master',u.name,r.name FROM master.sys.database_role_members m
            JOIN master.sys.database_principals u ON u.principal_id=m.member_principal_id
            JOIN master.sys.database_principals r ON r.principal_id=m.role_principal_id WHERE u.name='S11LegacyImportUser'
            UNION ALL SELECT 'server',u.name,r.name FROM sys.server_role_members m
            JOIN sys.server_principals u ON u.principal_id=m.member_principal_id
            JOIN sys.server_principals r ON r.principal_id=m.role_principal_id WHERE u.name='S11LegacyImportLogin'""",
            (),
        ),
        "capabilities": (
            """SELECT SecurableClass,TargetName,PermissionName,
            HAS_PERMS_BY_NAME(TargetName,SecurableClass,PermissionName) AS Allowed
            FROM OPENJSON(?) WITH (SecurableClass nvarchar(32) '$.kind',TargetName nvarchar(257) '$.target',PermissionName nvarchar(128) '$.permission')
            ORDER BY SecurableClass,TargetName,PermissionName""",
            (json.dumps(capabilities),),
        ),
        "module_permissions": (
            """SELECT r.value AS ObjectName,p.PermissionName,
            HAS_PERMS_BY_NAME(r.value,'OBJECT',p.PermissionName) AS Allowed FROM OPENJSON(?) r
            CROSS JOIN (VALUES('EXECUTE'),('ALTER'),('CONTROL'),('TAKE OWNERSHIP')) p(PermissionName)
            ORDER BY r.value COLLATE Latin1_General_100_BIN2,p.PermissionName""",
            (modules,),
        ),
        "token_grants": (
            """SELECT p.class_desc COLLATE Latin1_General_100_BIN2 AS SecurableClass,p.permission_name COLLATE Latin1_General_100_BIN2 AS PermissionName,p.state COLLATE Latin1_General_100_BIN2 AS GrantState
            FROM sys.database_permissions p JOIN sys.user_token t ON t.principal_id=p.grantee_principal_id
            WHERE p.state IN ('G','W') AND (p.state='W' OR p.permission_name='TAKE OWNERSHIP'
                OR p.permission_name LIKE 'ALTER%' OR p.permission_name LIKE 'CREATE%'
                OR p.permission_name LIKE 'CONTROL%' OR p.permission_name LIKE 'IMPERSONATE%')
            UNION ALL SELECT p.class_desc,p.permission_name,p.state
            FROM sys.server_permissions p JOIN sys.login_token t ON t.principal_id=p.grantee_principal_id
            WHERE p.state IN ('G','W') AND (p.state='W' OR p.permission_name='TAKE OWNERSHIP'
                OR p.permission_name LIKE 'ALTER%' OR p.permission_name LIKE 'CREATE%'
                OR p.permission_name LIKE 'CONTROL%' OR p.permission_name LIKE 'IMPERSONATE%')
            ORDER BY SecurableClass,PermissionName,GrantState""",
            (),
        ),
        "ownership": (
            """SELECT
            (SELECT COUNT(*) FROM sys.schemas s JOIN sys.user_token t ON s.principal_id=t.principal_id) AS OwnedSchemas,
            (SELECT COUNT(*) FROM sys.objects o JOIN sys.user_token t ON o.principal_id=t.principal_id) AS OwnedObjects,
            (SELECT COUNT(*) FROM sys.database_principals p JOIN sys.user_token t ON p.owning_principal_id=t.principal_id) AS OwnedPrincipals,
            (SELECT COUNT(*) FROM sys.server_principals p JOIN sys.login_token t ON p.owning_principal_id=t.principal_id) AS OwnedServerPrincipals""",
            (),
        ),
        "migration": (
            """SELECT MigrationId,LOWER(ChecksumSha256) AS ChecksumSha256,Status FROM dbo.SchemaMigrationHistory WHERE MigrationId=?""",
            (LEGACY_PERMISSION_MIGRATION,),
        ),
    }


def legacy_installation_snapshot(cursor, source):
    """Observe this producer's own connection; no commit, grant, root call or retry."""
    from services.export_execution_protocol import encode

    result = {"version": 1}
    for name, (query, parameters) in legacy_permission_queries(source).items():
        cursor.execute(query, *parameters)
        result[name] = rows(cursor)
        if name == "target" and (
            len(result[name]) != 1
            or result[name][0].get("DatabaseName") != "ROK_TRACKER"
            or result[name][0].get("DefaultSchema") != "dbo"
        ):
            raise SourceConflict("Legacy SQL database/default-schema resolution differs.")
    encode(result)
    return result


def application_installation_snapshot(cursor):
    """Read complete application metadata/permissions on the caller's session.

    No business query/procedure, transaction transition, DDL or data import runs.
    Expected metadata comes from an independently reviewed G4 source comparison,
    never from these observations. Dynamic outputs and external dependencies are
    included in that comparison and cannot disappear behind the fixed 30-object
    coordination contract or the 38-module signing contract.
    """
    from services.export_execution_protocol import encode

    result = {"version": 1, "metadata": {}}
    cursor.execute(
        "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS ServerName,"
        "DB_NAME() AS DatabaseName,USER_NAME() AS Principal,"
        "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','VIEW DEFINITION') AS ViewDefinition"
    )
    result["target"] = one(cursor)
    if result["target"] is None or result["target"]["ViewDefinition"] != 1:
        raise SourceConflict("Whole application metadata must be visible.")
    for name, query in _METADATA_QUERIES.items():
        cursor.execute(
            "WITH required AS (SELECT object_id FROM sys.objects WHERE is_ms_shipped=0 "
            "AND type IN ('U','V','P','FN','IF','TF')) " + query
        )
        result["metadata"][name] = rows(cursor)
    cursor.execute(
        "SELECT SCHEMA_NAME(t.schema_id)+'.'+t.name AS TypeName,c.column_id AS Ordinal,"
        "c.name AS ColumnName,SCHEMA_NAME(st.schema_id)+'.'+st.name AS ColumnType,"
        "c.max_length AS MaxLength,c.precision AS [Precision],c.scale AS Scale,"
        "c.is_nullable AS Nullable,c.collation_name AS Collation "
        "FROM sys.table_types t JOIN sys.columns c ON c.object_id=t.type_table_object_id "
        "JOIN sys.types st ON st.user_type_id=c.user_type_id "
        "ORDER BY TypeName COLLATE Latin1_General_100_BIN2,c.column_id"
    )
    result["metadata"]["table_types"] = rows(cursor)
    cursor.execute(
        "SELECT OBJECT_SCHEMA_NAME(d.referencing_id)+'.'+OBJECT_NAME(d.referencing_id) AS ObjectName,"
        "d.referencing_minor_id AS MinorID,d.referenced_server_name AS ServerName,"
        "d.referenced_database_name AS DatabaseName,d.referenced_schema_name AS SchemaName,"
        "d.referenced_entity_name AS EntityName,d.referenced_minor_id AS ReferencedMinorID,"
        "d.is_schema_bound_reference AS SchemaBound,d.is_caller_dependent AS CallerDependent,"
        "d.is_ambiguous AS Ambiguous FROM sys.sql_expression_dependencies d "
        "JOIN sys.objects o ON o.object_id=d.referencing_id WHERE o.is_ms_shipped=0 "
        "ORDER BY ObjectName COLLATE Latin1_General_100_BIN2,MinorID,ServerName,DatabaseName,"
        "SchemaName,EntityName,ReferencedMinorID"
    )
    result["metadata"]["dependencies"] = rows(cursor)
    cursor.execute(
        "SELECT SCHEMA_NAME(schema_id)+'.'+name AS ObjectName,base_object_name AS Target "
        "FROM sys.synonyms ORDER BY ObjectName COLLATE Latin1_General_100_BIN2"
    )
    result["metadata"]["synonyms"] = rows(cursor)
    cursor.execute(
        "SELECT t.name AS TriggerName,t.is_disabled AS Disabled,m.definition AS ModuleDefinition,"
        "m.execute_as_principal_id AS ExecuteAsPrincipal FROM sys.triggers t "
        "LEFT JOIN sys.sql_modules m ON m.object_id=t.object_id WHERE t.parent_class=0 "
        "ORDER BY t.name COLLATE Latin1_General_100_BIN2"
    )
    result["metadata"]["database_triggers"] = rows(cursor)
    cursor.execute(
        "SELECT s.name AS SchemaName,p.permission_name AS PermissionName,p.subentity_name AS Subentity "
        "FROM sys.schemas s CROSS APPLY sys.fn_my_permissions(QUOTENAME(s.name),'SCHEMA') p "
        "WHERE s.name NOT IN ('sys','INFORMATION_SCHEMA') "
        "ORDER BY s.name COLLATE Latin1_General_100_BIN2,p.permission_name,p.subentity_name"
    )
    result["schema_permissions"] = rows(cursor)
    cursor.execute(
        "SELECT SCHEMA_NAME(o.schema_id)+'.'+o.name AS ObjectName,"
        "p.permission_name AS PermissionName,p.subentity_name AS Subentity "
        "FROM sys.objects o CROSS APPLY sys.fn_my_permissions(QUOTENAME(SCHEMA_NAME(o.schema_id))+'.'+QUOTENAME(o.name),'OBJECT') p "
        "WHERE o.is_ms_shipped=0 AND o.type IN ('U','V','P','FN','IF','TF') "
        "ORDER BY ObjectName COLLATE Latin1_General_100_BIN2,p.permission_name,p.subentity_name"
    )
    result["object_permissions"] = rows(cursor)
    cursor.execute(
        "SELECT SCHEMA_NAME(o.schema_id)+'.'+o.name AS ObjectName,c.name AS ColumnName,"
        "p.PermissionName,HAS_PERMS_BY_NAME(QUOTENAME(SCHEMA_NAME(o.schema_id))+'.'+QUOTENAME(o.name),'OBJECT',p.PermissionName,c.name,'COLUMN') AS Allowed "
        "FROM sys.objects o JOIN sys.columns c ON c.object_id=o.object_id "
        "CROSS JOIN (VALUES ('SELECT'),('UPDATE'),('REFERENCES')) p(PermissionName) "
        "WHERE o.is_ms_shipped=0 AND o.type IN ('U','V','IF','TF') "
        "ORDER BY ObjectName COLLATE Latin1_General_100_BIN2,c.name COLLATE Latin1_General_100_BIN2,p.PermissionName"
    )
    result["column_permissions"] = rows(cursor)
    encode(result)
    return result


class ExportExecutionDAL:
    def __init__(self, connect):
        self.connect = connect

    def installation_snapshot(self):
        """Read the actual target's contract metadata, never execute installation SQL.

        Only an explicitly composed readiness path may call this method. It does
        not establish permissions outside the fixed export object set, external-
        writer exclusion or provider finality. A protected version-2 contract must match
        these observations; migration history alone cannot authorize startup.
        """
        from services.export_execution_protocol import encode

        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')) AS ServerName,"
                    "DB_NAME() AS DatabaseName,CONVERT(nvarchar(128),DATABASEPROPERTYEX(DB_NAME(),'Collation')) AS DatabaseCollation,"
                    "USER_NAME() AS Principal,IS_SRVROLEMEMBER('sysadmin') AS Sysadmin,"
                    "IS_MEMBER('db_owner') AS DatabaseOwner,"
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','VIEW DEFINITION') AS ViewDefinition,"
                    "IS_ROLEMEMBER('ExportExecutionAuthority') AS AuthorityRole,"
                    "IS_ROLEMEMBER('ExportExecutionReader') AS ReaderRole,"
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','CONTROL') AS ControlDatabase,"
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','ALTER ANY ROLE') AS AlterRole,"
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','ALTER ANY USER') AS AlterUser,"
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','IMPERSONATE ANY USER') AS ImpersonateUser"
                )
                target = one(cursor)
                if target is None or target["ViewDefinition"] != 1:
                    raise SourceConflict("Complete installation metadata is not visible.")
                cursor.execute(
                    "SELECT MigrationId,ChecksumSha256,Status FROM dbo.SchemaMigrationHistory "
                    "WHERE MigrationId IN (SELECT value FROM OPENJSON(?)) "
                    "ORDER BY MigrationId COLLATE Latin1_General_100_BIN2",
                    json.dumps(INSTALLATION_MIGRATIONS),
                )
                migrations = rows(cursor)
                metadata = {}
                for name, query in _METADATA_QUERIES.items():
                    cursor.execute(
                        "WITH required AS (SELECT OBJECT_ID(value) AS object_id FROM OPENJSON(?)) "
                        + query,
                        json.dumps(sorted(INSTALLATION_OBJECTS)),
                    )
                    metadata[name] = rows(cursor)
                cursor.execute(
                    "WITH permission_scope AS (SELECT ObjectName,PermissionName "
                    "FROM OPENJSON(?) WITH (ObjectName nvarchar(256) '$.object',PermissionName nvarchar(128) '$.permission')) "
                    "SELECT r.ObjectName,CAST(NULL AS sysname) AS ColumnName,r.PermissionName,"
                    "HAS_PERMS_BY_NAME(r.ObjectName,'OBJECT',r.PermissionName) AS Allowed "
                    "FROM permission_scope r UNION ALL "
                    "SELECT r.ObjectName,c.name AS ColumnName,r.PermissionName,"
                    "HAS_PERMS_BY_NAME(r.ObjectName,'OBJECT',r.PermissionName,c.name,'COLUMN') AS Allowed "
                    "FROM permission_scope r JOIN sys.columns c ON c.object_id=OBJECT_ID(r.ObjectName) "
                    "WHERE r.PermissionName IN ('SELECT','UPDATE') "
                    "ORDER BY ObjectName,ColumnName,PermissionName",
                    json.dumps(
                        [
                            dict(object=name, permission=permission)
                            for name, permissions in INSTALLATION_PERMISSIONS.items()
                            for permission in permissions
                        ]
                    ),
                )
                permissions = rows(cursor)
                result = dict(
                    version=2,
                    target=target,
                    migrations=migrations,
                    metadata=metadata,
                    permissions=permissions,
                )
                encode(result)  # Bound the complete observation; never truncate it.
                return result
            finally:
                cursor.close()
        finally:
            connection.close()

    def transition(self, kind, **values):
        names = _PARAMETERS[kind]
        if not values or not set(values) <= set(names):
            raise ValueError("Unknown evidence procedure parameter.")
        if kind == "proof":
            values = _proof_request(values)
        selected = [name for name in names if name in values]
        sql = "EXEC " + _PROCEDURES[kind] + " " + ",".join("@" + name + "=?" for name in selected)
        connection = self.connect()
        try:
            # The dedicated authority connection is fresh. Procedures explicitly
            # reject ambient transactions; no helper silently commits caller work.
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(sql, *(values[name] for name in selected))
                columns = tuple(column[0] for column in (cursor.description or ()))
                result = one(cursor)
                if result is None:
                    raise EvidenceCommitUnknown("Evidence transition acknowledgment missing.")
                # Procedure SELECT precedes COMMIT. Consume the entire batch:
                # a later commit/error token must arrive before dispatch escapes.
                if cursor.fetchall():
                    raise EvidenceCommitUnknown("Unexpected evidence result cardinality.")
                while cursor.nextset():
                    if cursor.description is not None and cursor.fetchall():
                        raise EvidenceCommitUnknown("Unexpected additional evidence results.")
                if kind == "proof":
                    result = _proof_acknowledgment(values, result, columns)
                return result
            except Exception as exc:
                raise EvidenceCommitUnknown(
                    "Evidence transition unresolved; read exact identity."
                ) from exc
            finally:
                cursor.close()
        finally:
            connection.close()

    def read_request(self, request_id):
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT * FROM dbo.ExportProviderRequest WHERE RequestID=?", request_id
                )
                request = one(cursor)
                cursor.execute(
                    "SELECT * FROM dbo.ExportProviderRequestEvent WHERE RequestID=? ORDER BY EventSequence",
                    request_id,
                )
                return request, rows(cursor)
            finally:
                cursor.close()
        finally:
            connection.close()

    def read_stream(self, stream_id):
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT * FROM dbo.ExportExecutionStream WHERE StreamID=?", stream_id
                )
                return one(cursor)
            finally:
                cursor.close()
        finally:
            connection.close()

    def read_session(self, session_id):
        """Read the immutable authority/host/build identity behind retained evidence."""
        from services.export_execution_protocol import uuid_text

        uuid_text(session_id)
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT * FROM dbo.ExportExecutionSession WHERE SessionID=?", session_id
                )
                return one(cursor)
            finally:
                cursor.close()
        finally:
            connection.close()

    def read_proof(self, proof_id):
        """Read immutable historical evidence; this does not grant settlement authority."""
        from services.export_execution_protocol import uuid_text

        uuid_text(proof_id)
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT * FROM dbo.ExportReconciliationProof WHERE ProofID=?", proof_id
                )
                return one(cursor)
            finally:
                cursor.close()
        finally:
            connection.close()

    @staticmethod
    def proof_targets(snapshot):
        """Derive the full registered pool scope from the locked domain snapshot."""
        context = snapshot["pool"] if "pool" in snapshot["pool"] else snapshot
        pool, slots = context["pool"], context["slots"]
        targets = [pool["IndexFileID"], *(slot["FileID"] for slot in slots)]
        if not 2 <= len(slots) <= 16 or len(targets) != len(set(targets)):
            raise SourceConflict("Complete unique registered pool membership required.")
        return sorted(targets)

    @staticmethod
    def _catalogue_query(*, locked=False, paged=False):
        # Match every former job/preparation/operation with any registered file,
        # including old nested owners and other participating shared writers.
        return (
            "WITH catalogue_scope AS (SELECT CAST(? AS varchar(128)) AS AccountKey, "
            "CAST(? AS nvarchar(max)) AS TargetsJson) SELECT "
            + ("TOP (256) " if paged else "")
            + "s.* FROM dbo.ExportExecutionStream s"
            + (" WITH (UPDLOCK,HOLDLOCK)" if locked else "")
            + " CROSS JOIN catalogue_scope c WHERE s.AccountKey=c.AccountKey AND (EXISTS (SELECT 1 FROM OPENJSON(s.ScopeJson,'$.resources') "
            "WITH (ResourceKey varchar(256) '$.key') r JOIN OPENJSON(c.TargetsJson) "
            "WITH (FileID varchar(128) '$') f ON r.ResourceKey COLLATE Latin1_General_100_BIN2="
            "('destination:'+f.FileID) COLLATE Latin1_General_100_BIN2) "
            "OR EXISTS(SELECT 1 FROM dbo.ExportManagedFileOrigin o JOIN OPENJSON(c.TargetsJson) "
            "WITH (FileID varchar(128) '$') f ON f.FileID COLLATE Latin1_General_100_BIN2=o.FileID "
            "WHERE o.PreparationID=s.PreparationID AND o.Stage='created'))"
            + (
                " AND LOWER(CONVERT(varchar(36),s.StreamID)) COLLATE Latin1_General_100_BIN2>?"
                if paged
                else ""
            )
            + " ORDER BY LOWER(CONVERT(varchar(36),s.StreamID)) COLLATE Latin1_General_100_BIN2"
        )

    @staticmethod
    def _origin_query():
        return (
            "SELECT o.*,p.AccountKey,p.RequestJson,p.RequestHash,p.GenerationJson,p.State AS PreparationState "
            "FROM dbo.ExportManagedFileOrigin o JOIN dbo.ExportPreparation p ON p.PreparationID=o.PreparationID "
            "JOIN OPENJSON(?) WITH(FileID varchar(128) '$') t ON t.FileID COLLATE Latin1_General_100_BIN2=o.FileID "
            "WHERE p.AccountKey=? ORDER BY o.FileID,o.Stage"
        )

    def read_origins(self, account, targets):
        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(self._origin_query(), json.dumps(targets), account)
                return rows(cursor)
            finally:
                cursor.close()
        finally:
            connection.close()

    @staticmethod
    def assert_eligible_origins(cursor, account, targets):
        """Repeat origin membership within the existing settlement transaction."""
        cursor.execute(ExportExecutionDAL._origin_query(), json.dumps(targets), account)
        origins = rows(cursor)
        eligible = [
            o["FileID"]
            for o in origins
            if o["Stage"] == "eligible" and o["PreparationState"] == "completed"
        ]
        if sorted(eligible) != targets:
            raise SourceConflict("Complete authenticated managed-file origins required.")

    def read_catalogue(self, account, targets):
        """Keyset-read bounded batches; close SQL before private evidence is read.

        This inventory is provisional: proof issue/consumption recheck the entire
        catalogue under the account lock, catching inserts before a prior page.
        """
        after = ""
        while True:
            connection = self.connect()
            try:
                connection.autocommit = True
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        self._catalogue_query(paged=True), account, json.dumps(targets), after
                    )
                    batch = rows(cursor)
                finally:
                    cursor.close()
            finally:
                connection.close()
            if not batch:
                return
            for row in batch:
                identifier = str(row["StreamID"]).lower()
                if identifier <= after:
                    raise SourceConflict("Stream catalogue ordering changed.")
                after = identifier
                yield row

    @staticmethod
    def assert_proof_catalogue(cursor, proof, *, snapshot, account):
        from services.export_execution_protocol import (
            CATALOGUE_SEED,
            catalogue_step,
            proof_membership,
        )

        raw = proof["MembershipJson"]
        try:
            membership = proof_membership(raw)
        except ValueError as exc:
            raise SourceConflict("Trusted proof catalogue is malformed.") from exc
        if hashlib.sha256(raw.encode("utf-16-le")).digest() != bytes(
            proof["MembershipHash"]
        ) or membership["targets"] != ExportExecutionDAL.proof_targets(snapshot):
            raise SourceConflict("Proof catalogue hash or registered membership differs.")
        ExportExecutionDAL.assert_eligible_origins(cursor, account, membership["targets"])
        cursor.execute(
            ExportExecutionDAL._catalogue_query(locked=True),
            account,
            json.dumps(membership["targets"]),
        )
        names = [column[0] for column in cursor.description]
        count, previous, root, probe = 0, "", CATALOGUE_SEED, None
        while batch := cursor.fetchmany(256):
            for values in batch:
                stream = dict(zip(names, values, strict=True))
                identifier = str(stream["StreamID"]).lower()
                if (
                    identifier <= previous
                    or stream["State"] != "closed"
                    or stream["ActiveAccountKey"] is not None
                    or stream["AccountKey"] != account
                    or stream["ClosureHash"] is None
                    or stream["EventDigest"] is None
                ):
                    raise SourceConflict("Proof catalogue contains an unclosed or changed writer.")
                previous = identifier
                if identifier == membership["probe"]["stream_id"]:
                    probe = stream
                else:
                    root = catalogue_step(
                        root, identifier, stream["Version"], bytes(stream["EventDigest"])
                    )
                    count += 1
        if (
            {"count": count, "sha256": root.hex()} != membership["history"]
            or probe is None
            or probe["Purpose"] != "probe"
            or probe["Version"] != membership["probe"]["version"]
            or bytes(probe["SnapshotHash"]) != digest(snapshot)
            or bytes(probe["RegistrationHash"]) != bytes(proof["RegistrationHash"])
        ):
            raise SourceConflict("Writer catalogue changed after the fresh proof probe.")

    def request_ids(self, stream_id):
        """Read a closed stream in pages without holding SQL across private I/O."""
        after = 0
        while True:
            connection = self.connect()
            try:
                connection.autocommit = True
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        "SELECT TOP (256) Sequence,RequestID FROM dbo.ExportProviderRequest "
                        "WHERE StreamID=? AND Sequence>? ORDER BY Sequence",
                        stream_id,
                        after,
                    )
                    batch = cursor.fetchall()
                finally:
                    cursor.close()
            finally:
                connection.close()
            if not batch:
                return
            for sequence, identifier in batch:
                if sequence != after + 1:
                    raise SourceConflict("Closed request membership has a gap.")
                after = sequence
                yield str(identifier).lower()

    def stream_digest(self, stream_id):
        """Bounded-memory digest of immutable request/event membership after freeze."""
        from services.export_execution_protocol import encode

        connection = self.connect()
        try:
            connection.autocommit = True
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT r.Sequence,CONVERT(varchar(36),r.RequestID),r.Operation,r.RequestKind,r.TargetID,"
                    "r.PayloadHash,CONVERT(varchar(36),r.PayloadReference),e.EventSequence,e.State,"
                    "CONVERT(varchar(36),e.EventID),e.EvidenceHash,CONVERT(varchar(36),e.EvidenceReference) "
                    "FROM dbo.ExportProviderRequest r LEFT JOIN dbo.ExportProviderRequestEvent e ON e.RequestID=r.RequestID "
                    "WHERE r.StreamID=? ORDER BY r.Sequence,e.EventSequence",
                    stream_id,
                )
                hasher = hashlib.sha256()
                last_request = last_event = 0
                while batch := cursor.fetchmany(256):
                    for row in batch:
                        sequence, event_sequence = row[0], row[7]
                        if event_sequence is None:
                            raise SourceConflict("Request event membership is incomplete.")
                        if sequence == last_request:
                            if event_sequence != last_event + 1:
                                raise SourceConflict("Request event sequence has a gap.")
                        elif sequence != last_request + 1 or event_sequence != 1:
                            raise SourceConflict("Request membership sequence has a gap.")
                        last_request, last_event = sequence, event_sequence
                        values = [
                            (bytes(v).hex() if isinstance(v, (bytes, bytearray, memoryview)) else v)
                            for v in row
                        ]
                        hasher.update(encode(values) + b"\n")
                return last_request, hasher.digest()
            finally:
                cursor.close()
        finally:
            connection.close()

    @staticmethod
    def assert_no_active_stream(cursor, account, *, probe_only=False):
        """Call under the existing account lock before any new claim/release."""
        cursor.execute(
            "SELECT StreamID FROM dbo.ExportExecutionStream WITH (UPDLOCK,HOLDLOCK) WHERE ActiveAccountKey=?"
            + (" AND Purpose='probe'" if probe_only else ""),
            account,
        )
        if one(cursor) is not None:
            raise SourceConflict("Provider writer/probe still owns account admission.")

    @staticmethod
    def settlement_proof(cursor, reference, *, snapshot, account, kind):
        """Resolve only after the caller has compared its locked snapshot exactly."""
        pool = snapshot.get("pool", {})
        pool = pool.get("pool", pool)
        registration = pool.get("RegistrationHash")
        try:
            registration = (
                bytes.fromhex(registration)
                if isinstance(registration, str)
                else bytes(registration)
            )
        except (TypeError, ValueError) as exc:
            raise SourceConflict("Exact registered proof scope is unavailable.") from exc
        if len(registration) != 32:
            raise SourceConflict("Exact registered proof scope is unavailable.")
        return ExportExecutionDAL.load_proof(
            cursor,
            reference,
            snapshot=snapshot,
            account=account,
            kind=kind,
            registration_hash=registration,
        )

    @staticmethod
    def load_proof(cursor, reference, *, snapshot, account, kind, registration_hash=None):
        """Resolve a sole ProofID within the existing exact-snapshot settlement CAS."""
        from services.export_execution_protocol import uuid_text

        if not isinstance(reference, dict) or "proof_id" not in reference:
            raise SourceConflict("A trusted ProofID is required, not caller-built proof flags.")
        # Extra view fields may support an operator preview but never authorize
        # settlement. Replace all of them with the immutable SQL-issued body.
        try:
            identifier = uuid_text(reference["proof_id"])
        except ValueError as exc:
            raise SourceConflict("Canonical trusted ProofID required.") from exc
        cursor.execute("SELECT * FROM dbo.ExportReconciliationProof WHERE ProofID=?", identifier)
        proof = one(cursor)
        if (
            proof is None
            or proof["AccountKey"] != account
            or proof["ProofKind"] != kind
            or bytes(proof["SnapshotHash"]) != digest(snapshot)
            or (
                registration_hash is not None
                and bytes(proof["RegistrationHash"]) != registration_hash
            )
        ):
            raise SourceConflict("Proof scope or snapshot differs.")
        ExportExecutionDAL.assert_no_active_stream(cursor, account)
        ExportExecutionDAL.assert_proof_catalogue(cursor, proof, snapshot=snapshot, account=account)
        evidence = json.loads(proof["EvidenceJson"])
        if (
            not isinstance(evidence, dict)
            or evidence.get("snapshot_hash") != digest(snapshot).hex()
            or evidence.get("state") != proof["Outcome"]
        ):
            raise SourceConflict("Stored proof body differs from its immutable identity.")
        # Preserve this association verbatim in the existing append-only audit.
        evidence["proof_id"] = identifier
        bounded_json(evidence)
        return evidence
