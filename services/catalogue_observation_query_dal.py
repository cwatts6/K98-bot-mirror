"""Scope-first catalogue reads for the opt-in, bounded observer only.

The representative plans scanned broad catalogue ranges before membership
filtering. Start with the small declared object set, keeping all projections,
outer joins and ordering. The hints affect these four reads only; native row
parity and measured cost must qualify them before runtime selection.
"""

_SCOPE = """SET NOCOUNT ON;
DECLARE @required TABLE(object_id int NOT NULL PRIMARY KEY);
INSERT @required SELECT DISTINCT OBJECT_ID(value) FROM OPENJSON(?) WHERE OBJECT_ID(value) IS NOT NULL;
"""

_OPTIONS = "\nOPTION (FORCE ORDER, LOOP JOIN)"

CATALOGUE_BATCH_QUERIES = {
    "metadata.indexes": _SCOPE
    + """SELECT s.name+'.'+o.name AS ObjectName,
        i.name AS IndexName,i.type AS IndexType,i.is_unique AS IsUnique,i.is_primary_key AS IsPrimaryKey,
        i.is_unique_constraint AS IsUniqueConstraint,i.is_disabled AS Disabled,
        i.is_hypothetical AS Hypothetical,i.ignore_dup_key AS IgnoreDuplicateKey,
        i.has_filter AS HasFilter,i.filter_definition AS FilterDefinition,
        ic.index_column_id AS Ordinal,c.name AS ColumnName,ic.key_ordinal AS KeyOrdinal,
        ic.partition_ordinal AS PartitionOrdinal,ic.is_descending_key AS DescendingKey,
        ic.is_included_column AS IncludedColumn
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.indexes i ON i.object_id=r.object_id
        LEFT JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
        LEFT JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
        ORDER BY s.name COLLATE Latin1_General_100_BIN2,o.name COLLATE Latin1_General_100_BIN2,i.name COLLATE Latin1_General_100_BIN2,ic.index_column_id"""
    + _OPTIONS,
    "identity.indexes": _SCOPE
    + """SELECT s.name+'.'+o.name AS object_name,i.index_id,i.name,i.type_desc,
        i.is_unique,i.is_primary_key,i.is_unique_constraint,i.is_disabled,i.has_filter,i.filter_definition
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.indexes i ON i.object_id=r.object_id
        ORDER BY object_name,i.index_id"""
    + _OPTIONS,
    "metadata.checks": _SCOPE
    + """SELECT s.name+'.'+o.name AS ObjectName,
        c.name AS ConstraintName,c.definition AS Definition,c.is_disabled AS Disabled,
        c.is_not_trusted AS Untrusted,c.is_not_for_replication AS NotForReplication
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.check_constraints c ON c.parent_object_id=r.object_id
        ORDER BY s.name COLLATE Latin1_General_100_BIN2,o.name COLLATE Latin1_General_100_BIN2,c.name COLLATE Latin1_General_100_BIN2"""
    + _OPTIONS,
}

# Preserve every projection/visibility rule for the measured trigger and
# dependency categories. Foreign keys keep the already-qualified unhinted
# materialized query: forced order regressed its expanded catalogue-view joins.
CATALOGUE_BATCH_QUERIES.update(
    {
        "metadata.triggers": _SCOPE
        + """SELECT s.name+'.'+o.name AS ObjectName,
        t.name AS TriggerName,t.is_disabled AS Disabled,t.is_instead_of_trigger AS InsteadOf,
        t.is_not_for_replication AS NotForReplication,m.definition AS ModuleDefinition,
        m.uses_ansi_nulls AS AnsiNulls,m.uses_quoted_identifier AS QuotedIdentifier,
        m.execute_as_principal_id AS ExecuteAsPrincipal
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.triggers t ON t.parent_id=r.object_id
        LEFT JOIN sys.sql_modules m ON m.object_id=t.object_id
        ORDER BY s.name COLLATE Latin1_General_100_BIN2,o.name COLLATE Latin1_General_100_BIN2,t.name COLLATE Latin1_General_100_BIN2"""
        + _OPTIONS,
        "metadata.dependencies": _SCOPE
        + """SELECT s.name+'.'+o.name AS ObjectName,
        d.referencing_minor_id AS MinorID,d.referenced_server_name AS ServerName,
        d.referenced_database_name AS DatabaseName,d.referenced_schema_name AS SchemaName,
        d.referenced_entity_name AS EntityName,d.referenced_minor_id AS ReferencedMinorID,
        d.is_schema_bound_reference AS SchemaBound,d.is_caller_dependent AS CallerDependent,
        d.is_ambiguous AS Ambiguous
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.sql_expression_dependencies d ON d.referencing_id=r.object_id
        WHERE o.is_ms_shipped=0
        ORDER BY (s.name+'.'+o.name) COLLATE Latin1_General_100_BIN2,MinorID,ServerName,DatabaseName,
        SchemaName,EntityName,ReferencedMinorID"""
        + _OPTIONS,
    }
)

# Keep each identity projection intact. Defaults/dependencies resolve their
# owning object/schema from the fixed scope. The column template uses direct
# bound object lookups; its caller supplies only a finite placeholder list.
# Retain COL_NAME where its nullable lookup is part of the existing contract.
IDENTITY_BATCH_QUERIES = {
    "identity.columns": """SELECT s.name+'.'+o.name AS object_name,c.column_id,c.name AS column_name,
        ROW_NUMBER() OVER(PARTITION BY c.object_id ORDER BY c.column_id) AS visible_position,
        t.max_column_id_used,c.is_computed
        FROM sys.columns c JOIN sys.objects o ON o.object_id=c.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        LEFT JOIN sys.tables t ON t.object_id=c.object_id
        WHERE c.object_id IN (__IDENTITY_OBJECT_IDS__)
        ORDER BY object_name,c.column_id""",
    "identity.default_constraints": _SCOPE
    + """SELECT s.name+'.'+o.name AS object_name,
        COL_NAME(d.parent_object_id,d.parent_column_id) AS column_name,
        d.name,d.is_system_named,d.definition
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.default_constraints d ON d.parent_object_id=r.object_id
        ORDER BY object_name,d.parent_column_id"""
    + _OPTIONS,
    "identity.dependencies": _SCOPE
    + """SELECT s.name+'.'+o.name AS object_name,d.referencing_minor_id,
        d.referencing_class,d.referencing_class_desc,
        COL_NAME(d.referencing_id,d.referencing_minor_id) AS candidate_column_name,
        i.name AS candidate_index_name,i.has_filter AS candidate_index_filtered,
        i.filter_definition AS candidate_index_filter,
        st.name AS candidate_statistics_name,st.has_filter AS candidate_statistics_filtered,
        st.filter_definition AS candidate_statistics_filter,
        d.referenced_class,d.referenced_class_desc,d.referenced_server_name,
        d.referenced_database_name,d.referenced_schema_name,d.referenced_entity_name,
        d.referenced_minor_id,COL_NAME(d.referenced_id,d.referenced_minor_id) AS referenced_column_name,
        d.is_schema_bound_reference,d.is_caller_dependent,d.is_ambiguous
        FROM @required r JOIN sys.objects o ON o.object_id=r.object_id
        JOIN sys.schemas s ON s.schema_id=o.schema_id
        JOIN sys.sql_expression_dependencies d ON d.referencing_id=r.object_id
        LEFT JOIN sys.indexes i ON i.object_id=d.referencing_id AND i.index_id=d.referencing_minor_id
        LEFT JOIN sys.stats st ON st.object_id=d.referencing_id AND st.stats_id=d.referencing_minor_id
        ORDER BY object_name,d.referencing_class,d.referencing_minor_id,d.referenced_entity_name,d.referenced_minor_id"""
    + _OPTIONS,
}
