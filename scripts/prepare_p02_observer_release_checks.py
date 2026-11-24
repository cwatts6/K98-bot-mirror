"""Source-derived release checks; no connections or native expected-hash adoption."""

import hashlib

from services.catalogue_observation_dal import canonical_module


def release_checks(before, definitions, grants):
    before = """IF DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader') IS NULL
 THROW 51973,'Reviewed application role is missing.',1;
""" + before
    after = ["DECLARE @id int,@body nvarchar(max);\n"]
    parents = {
        "tr_P02HeaderObservation": "dbo.KVKFinalReportHeader",
        "tr_P02KvkWorkObservation": "dbo.MaintenanceKvkWork",
        "tr_P02MaintenanceObservation": "dbo.MaintenanceWork",
    }
    for name, body in sorted(definitions.items()):
        trigger = name.startswith("tr_")
        database_trigger = name == "tr_P02CatalogueObservation"
        kind = "TRIGGER" if trigger else "PROCEDURE"
        expected = hashlib.sha256(canonical_module(body).encode("utf-16-le")).hexdigest()
        lookup = (
            f"(SELECT object_id FROM sys.triggers WHERE parent_class=0 AND name=N'{name}')"
            if database_trigger
            else f"OBJECT_ID(N'{('dbo.' if trigger else '') + name}')"
        )
        after.append(f"""SET @id={lookup};
SET @body=REPLACE(OBJECT_DEFINITION(@id),NCHAR(13)+NCHAR(10),NCHAR(10));
SET @body=CASE
 WHEN @body LIKE N'CREATE OR ALTER {kind} %' THEN STUFF(@body,1,LEN(N'CREATE OR ALTER {kind}'),N'{kind}')
 WHEN @body LIKE N'CREATE   {kind} %' THEN STUFF(@body,1,LEN(N'CREATE   {kind}'),N'{kind}')
 WHEN @body LIKE N'CREATE {kind} %' THEN STUFF(@body,1,LEN(N'CREATE {kind}'),N'{kind}')
 WHEN @body LIKE N'ALTER {kind} %' THEN STUFF(@body,1,LEN(N'ALTER {kind}'),N'{kind}')
 ELSE NULL END;
IF @id IS NULL OR @body IS NULL OR LOWER(CONVERT(varchar(64),HASHBYTES('SHA2_256',@body),2))<>'{expected}'
 OR NOT EXISTS(SELECT 1 FROM sys.sql_modules WHERE object_id=@id AND uses_ansi_nulls=1 AND uses_quoted_identifier=1
   AND execute_as_principal_id IS NULL AND is_schema_bound=0)
 OR EXISTS(SELECT 1 FROM sys.crypt_properties WHERE class=1 AND major_id=@id)
 THROW 51973,'Observer module postimage differs: {name}.',1;
""")
        if trigger:
            parent = "0" if database_trigger else f"OBJECT_ID(N'{parents[name]}')"
            after.append(
                f"""IF NOT EXISTS(SELECT 1 FROM sys.triggers WHERE object_id=@id AND type='TR'
 AND parent_class={0 if database_trigger else 1} AND parent_id={parent} AND is_disabled=0 AND is_not_for_replication=0
 AND is_instead_of_trigger=0)
 THROW 51973,'Observer trigger state differs: {name}.',1;
"""
            )
        if not database_trigger:
            after.append(
                f"""IF NOT EXISTS(SELECT 1 FROM sys.objects o JOIN sys.schemas s ON s.schema_id=o.schema_id
 WHERE o.object_id=@id AND o.type='{('TR' if trigger else 'P')}' AND s.name=N'dbo'
 AND USER_NAME(COALESCE(o.principal_id,s.principal_id))=N'dbo')
 THROW 51973,'Observer object owner/type differs: {name}.',1;
"""
            )
    after.append(
        """IF NOT EXISTS(SELECT 1 FROM sys.sequences s JOIN sys.schemas sc ON sc.schema_id=s.schema_id
 WHERE sc.name=N'dbo' AND s.name=N'P02ObservationGeneration' AND TYPE_NAME(s.user_type_id)=N'bigint'
 AND s.user_type_id=s.system_type_id AND CONVERT(bigint,s.start_value)=1 AND CONVERT(bigint,s.increment)=1
 AND CONVERT(bigint,s.minimum_value)=1 AND CONVERT(bigint,s.maximum_value)=9223372036854775807
 AND s.is_cycling=0 AND s.is_cached=0 AND s.cache_size IS NULL AND s.is_exhausted=0
 AND CONVERT(bigint,s.current_value)>=1 AND CONVERT(bigint,s.current_value)<9223372036854775807
 AND s.create_date=s.modify_date AND USER_NAME(COALESCE(s.principal_id,sc.principal_id))=N'dbo')
 THROW 51973,'Observer sequence structure/state differs.',1;
"""
    )
    for grant in grants:
        target, permission = grant["target"], grant["permission"]
        state = grant.get("state", "G")
        after.append(f"""IF (SELECT COUNT(*) FROM sys.database_permissions
 WHERE class=1 AND major_id=OBJECT_ID(N'{target}') AND minor_id=0
 AND grantee_principal_id=DATABASE_PRINCIPAL_ID(N'ExportLegacyEntryReader')
 AND grantor_principal_id=DATABASE_PRINCIPAL_ID(N'dbo') AND permission_name='{permission}' AND state='{state}')<>1
 THROW 51973,'Observer permission postimage differs: {target}/{permission}.',1;
""")
    return before, "\n".join(after)
