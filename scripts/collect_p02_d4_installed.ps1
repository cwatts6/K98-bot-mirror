#requires -Version 5.1
<##
Fixed metadata-only D4 collection on the installed machine. No application
imports, business procedures, backup requests, migration, or configuration writes.
Run in Windows PowerShell 5.1 under the operator's existing integrated identity.
Output contains private definitions and principal names: never commit or publish it.
##>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputFile
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ine 'MINI_AMD') { throw 'This collector requires MINI_AMD.' }
if ($PSVersionTable.PSEdition -ne 'Desktop') { throw 'Use Windows PowerShell 5.1.' }
$outputPath = [IO.Path]::GetFullPath($OutputFile)
if (-not [IO.Directory]::Exists([IO.Path]::GetDirectoryName($outputPath))) {
    throw 'Output parent must already exist.'
}
# CreateNew and an explicit protected ACL apply before the first evidence byte.
$acl = New-Object Security.AccessControl.FileSecurity
$acl.SetAccessRuleProtection($true, $false)
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
$acl.SetOwner($identity)
foreach ($sid in @($identity, (New-Object Security.Principal.SecurityIdentifier 'S-1-5-18'))) {
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule(
        $sid, [Security.AccessControl.FileSystemRights]::FullControl,
        [Security.AccessControl.AccessControlType]::Allow)))
}
$output = New-Object IO.FileStream($outputPath, [IO.FileMode]::CreateNew,
    [Security.AccessControl.FileSystemRights]::Write, [IO.FileShare]::None,
    4096, [IO.FileOptions]::None, $acl)
$timer = [Diagnostics.Stopwatch]::StartNew()
$script:cellsBytes = 0L
$record = [ordered]@{
    version=2; kind='p02_d4_installed_metadata'; phase='collecting'
    startedUtc=[DateTime]::UtcNow.ToString('o'); computer=$env:COMPUTERNAME
    collectorSHA256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    sections=@(); limitations=@(
        'Metadata only; no procedure or application workload was invoked.',
        'Collector identity is not proof of effective runtime-principal rights.',
        'Manual, external, dynamic and Windows scheduled consumers require separate disposition.',
        'Missing or hidden metadata is unresolved, never proof of retirement.',
        'Creation/alteration dates are not execution dates; cached activity is not lifetime history.',
        'Query Store observations cover retained statements, not a complete procedure invocation audit.',
        'Definitions and principal names are private; do not commit this receipt.'
    )
}
function Read-Metadata([Data.SqlClient.SqlConnection]$Connection, [string]$Sql) {
    if ($timer.Elapsed.TotalSeconds -ge 60) { throw 'total_time_bound' }
    $command = $Connection.CreateCommand()
    $command.CommandTimeout = 3
    $command.CommandText = $Sql
    $reader = $null
    $rows = New-Object 'Collections.Generic.List[object]'
    try {
        $reader = $command.ExecuteReader()
        while ($reader.Read()) {
            if ($rows.Count -ge 512) { throw 'row_bound' }
            if ($timer.Elapsed.TotalSeconds -ge 60) { throw 'total_time_bound' }
            $row = [ordered]@{}
            for ($i=0; $i -lt $reader.FieldCount; $i++) {
                $value = if ($reader.IsDBNull($i)) { $null } else { $reader.GetValue($i) }
                if ($null -ne $value) {
                    $size = [Text.Encoding]::UTF8.GetByteCount([string]$value)
                    if ($size -gt 1MB) { throw 'cell_bound' }
                    $script:cellsBytes += $size
                    if ($script:cellsBytes -gt 4MB) { throw 'total_byte_bound' }
                }
                $row[$reader.GetName($i)] = $value
            }
            $rows.Add([pscustomobject]$row)
        }
        if ($reader.NextResult()) { throw 'unexpected_result_set' }
        return ,$rows.ToArray()
    } finally {
        if ($null -ne $reader) { $reader.Dispose() }
        $command.Dispose()
    }
}
# All object names below are source-reviewed D4 roots, not an execution allowlist.
$roots = @'
WITH roots(name) AS (
 SELECT name FROM (VALUES
 (N'UPDATE_ALL'),(N'UPDATE_ALL2'),(N'UPDATE_RALLY_DATA'),(N'TEST'),
 (N'KS4_UNO_SEQ'),(N'KingdomScanData4'),(N'CLAIM_KS4_IMPORT_FILE'),
 (N'IMPORT_STAGING_PROC_CORE'),(N'ARCHIVE_IMPORT_STAGING_FILE'),
 (N'SUMMARY_PROC'),(N'SP_Stats_for_Upload'),(N'sp_TARGETS_MASTER'),
 (N'CREATE_DELTA_TABLES'),(N'sp_ExcelOutput_ByKVK'),
 (N'usp_S11CompleteStatsReportsCore'),(N'usp_S11ValidateStatsReportStage'),
 (N'MaintenanceWork'),(N'MaintenanceConfigurationWork'),
 (N'MaintenanceKvkWork'),(N'MaintenanceBackupWork'),(N'usp_update_stats'),
 (N'usp_RunMaintenance'),(N'usp_MaintenanceDue'),(N'usp_MaintenanceConfigurationDue'),
 (N'usp_MaintenanceKvkDue'),(N'usp_MaintenanceImport'),(N'usp_MaintenanceConfiguration'),
 (N'usp_MaintenancePlayerReport'),(N'usp_MaintenanceKvkOutput'),
 (N'usp_MaintenanceFinalStats'),(N'usp_MaintenancePostImport'),
 (N'usp_MaintenanceBackupClaim'),(N'usp_MaintenanceBackupAcknowledge'),
 (N'LogBackupTriggerQueue'),(N'usp_GetPendingLogBackupTriggers'),
 (N'usp_MarkLogBackupTriggerProcessed'),(N'usp_CleanupLogBackupTriggerQueue'),
 (N'usp_start_rok_tracker_log_backup'),(N'sp_Import_Rally_Daily'),
 (N'sp_Import_Rally_AllTime'),(N'IngestionLog')) v(name)
)
'@
$queries = @(
    @{name='objects'; sql=($roots + @'
SELECT TOP(513) r.name AS requested_name,s.name AS schema_name,o.type_desc,
 o.object_id,o.create_date,o.modify_date,USER_NAME(o.principal_id) AS object_owner,
 USER_NAME(s.principal_id) AS schema_owner,m.execute_as_principal_id,
 m.uses_ansi_nulls,m.uses_quoted_identifier,m.is_schema_bound,
 DATALENGTH(m.definition) AS definition_bytes,
 SUBSTRING(m.definition,1,524288) AS definition
FROM roots r LEFT JOIN sys.objects o ON o.name=r.name
 LEFT JOIN sys.schemas s ON s.schema_id=o.schema_id
 LEFT JOIN sys.sql_modules m ON m.object_id=o.object_id
ORDER BY r.name,s.name;
'@)},
    @{name='sequence'; sql=@'
SELECT TOP(513) s.name AS schema_name,q.name,TYPE_NAME(q.user_type_id) AS type_name,
 CONVERT(nvarchar(100),q.start_value) AS start_value,
 CONVERT(nvarchar(100),q.increment) AS increment_value,
 CONVERT(nvarchar(100),q.minimum_value) AS minimum_value,
 CONVERT(nvarchar(100),q.maximum_value) AS maximum_value,
 CONVERT(nvarchar(100),q.current_value) AS current_value,
 q.is_cycling,q.is_cached,q.cache_size,q.is_exhausted
FROM sys.sequences q JOIN sys.schemas s ON s.schema_id=q.schema_id
WHERE q.name=N'KS4_UNO_SEQ';
'@},
    @{name='dependencies'; sql=($roots + @'
SELECT TOP(513) OBJECT_SCHEMA_NAME(d.referencing_id) AS caller_schema,
 OBJECT_NAME(d.referencing_id) AS caller_name,d.referenced_server_name,
 d.referenced_database_name,d.referenced_schema_name,d.referenced_entity_name,
 d.is_caller_dependent,d.is_ambiguous
FROM sys.sql_expression_dependencies d
WHERE EXISTS(SELECT 1 FROM roots r WHERE r.name=OBJECT_NAME(d.referencing_id)
 OR r.name=d.referenced_entity_name)
ORDER BY d.referencing_id,d.referenced_entity_name;
'@)},
    @{name='lexical_callers'; sql=($roots + @'
SELECT TOP(513) s.name AS schema_name,o.name AS module_name,r.name AS root_candidate,
 CONVERT(varchar(64),HASHBYTES('SHA2_256',CONVERT(varbinary(max),m.definition)),2) AS definition_hash
FROM sys.sql_modules m JOIN sys.objects o ON o.object_id=m.object_id
JOIN sys.schemas s ON s.schema_id=o.schema_id
JOIN roots r ON CHARINDEX(LOWER(r.name),LOWER(m.definition))>0
ORDER BY o.object_id,r.name;
'@)},
    @{name='grants'; sql=($roots + @'
SELECT TOP(513) p.class_desc,p.major_id,p.minor_id,
 USER_NAME(p.grantee_principal_id) AS grantee,
 USER_NAME(p.grantor_principal_id) AS grantor,p.permission_name,p.state_desc,
 CASE WHEN p.class=1 THEN OBJECT_SCHEMA_NAME(p.major_id) END AS schema_name,
 CASE WHEN p.class=1 THEN OBJECT_NAME(p.major_id) END AS object_name
FROM sys.database_permissions p
WHERE p.class IN(0,3) OR (p.class=1 AND EXISTS(
 SELECT 1 FROM roots r WHERE r.name=OBJECT_NAME(p.major_id)))
ORDER BY p.class,p.major_id,p.grantee_principal_id,p.permission_name,p.minor_id;
'@)},
    @{name='roles'; sql=@'
SELECT TOP(513) USER_NAME(role_principal_id) AS role_name,
 USER_NAME(member_principal_id) AS member_name
FROM sys.database_role_members ORDER BY role_principal_id,member_principal_id;
'@},
    @{name='signatures'; sql=($roots + @'
SELECT TOP(513) OBJECT_SCHEMA_NAME(cp.major_id) AS schema_name,
 OBJECT_NAME(cp.major_id) AS module_name,cp.crypt_type_desc,
 CONVERT(varchar(128),cp.thumbprint,2) AS thumbprint
FROM sys.crypt_properties cp
WHERE cp.class=1 AND EXISTS(SELECT 1 FROM roots r WHERE r.name=OBJECT_NAME(cp.major_id))
ORDER BY cp.major_id,cp.thumbprint;
'@)},
    @{name='procedure_activity'; sql=($roots + @'
SELECT TOP(513) OBJECT_SCHEMA_NAME(p.object_id) AS schema_name,
 OBJECT_NAME(p.object_id) AS module_name,p.cached_time,p.last_execution_time,
 p.execution_count
FROM sys.dm_exec_procedure_stats p
WHERE p.database_id=DB_ID() AND EXISTS(
 SELECT 1 FROM roots r WHERE r.name=OBJECT_NAME(p.object_id))
ORDER BY p.object_id,p.cached_time;
'@)},
    @{name='server_start'; sql=@'
SELECT TOP(513) sqlserver_start_time FROM sys.dm_os_sys_info;
'@},
    @{name='query_store_options'; sql=@'
SELECT TOP(513) actual_state_desc,desired_state_desc,query_capture_mode_desc,
 stale_query_threshold_days,interval_length_minutes
FROM sys.database_query_store_options;
'@},
    @{name='query_store_activity'; sql=($roots + @'
SELECT TOP(513) OBJECT_SCHEMA_NAME(q.object_id) AS schema_name,
 OBJECT_NAME(q.object_id) AS module_name,
 MIN(s.first_execution_time) AS first_retained_statement_execution,
 MAX(s.last_execution_time) AS last_retained_statement_execution,
 SUM(CONVERT(bigint,s.count_executions)) AS retained_statement_executions,
 s.execution_type_desc
FROM sys.query_store_query q
JOIN sys.query_store_plan p ON p.query_id=q.query_id
JOIN sys.query_store_runtime_stats s ON s.plan_id=p.plan_id
WHERE EXISTS(SELECT 1 FROM roots r WHERE r.name=OBJECT_NAME(q.object_id))
GROUP BY q.object_id,s.execution_type_desc
ORDER BY q.object_id,s.execution_type_desc;
'@)},
    @{name='synonyms'; sql=@'
SELECT TOP(513) SCHEMA_NAME(schema_id) AS schema_name,name,base_object_name
FROM sys.synonyms ORDER BY schema_id,name;
'@}
)
$jobs = $roots + @'
SELECT TOP(513) CONVERT(varchar(36),j.job_id) AS job_id,
 j.name AS job_name,j.enabled,j.start_step_id,SUSER_SNAME(j.owner_sid) AS owner_name,
 st.step_id,st.step_name,st.subsystem,st.database_name,st.proxy_id,
 CONVERT(varchar(64),HASHBYTES('SHA2_256',CONVERT(varbinary(max),st.command)),2) AS command_hash,
 r.name AS root_candidate
FROM dbo.sysjobs j LEFT JOIN dbo.sysjobsteps st ON st.job_id=j.job_id
LEFT JOIN roots r ON CHARINDEX(LOWER(r.name),LOWER(st.command))>0
-- Include every bounded step: wrappers may address jobs only by GUID, and
-- jobs running in master may contain no D4 root name. Bodies stay private.
ORDER BY j.job_id,st.step_id,r.name;
'@
$connection = $null
try {
    foreach ($database in @('ROK_TRACKER','msdb')) {
        $connection = New-Object Data.SqlClient.SqlConnection (
            'Data Source=lpc:localhost;Initial Catalog=' + $database +
            ';Integrated Security=True;Connect Timeout=5;Pooling=False;Application Name=P02D4Metadata')
        $connection.Open()
        $who = Read-Metadata $connection @'
SELECT @@SERVERNAME AS server_name,DB_NAME() AS database_name,
 ORIGINAL_LOGIN() AS original_login,USER_NAME() AS database_user,
 IS_SRVROLEMEMBER('sysadmin') AS is_sysadmin,
 HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','VIEW DEFINITION') AS can_view_definition;
'@
        if ($who.Count -ne 1 -or $who[0].server_name -ine 'MINI_AMD' -or
            $who[0].database_name -cne $database) { throw 'wrong_sql_target' }
        $record.sections += @{database=$database; name='identity'; status='complete'; rows=$who}
        $setup = $connection.CreateCommand()
        try {
            $setup.CommandTimeout=3
            $setup.CommandText='SET LOCK_TIMEOUT 0; SET DEADLOCK_PRIORITY LOW;'
            [void]$setup.ExecuteNonQuery()
        } finally { $setup.Dispose() }
        $selected = if ($database -eq 'msdb') {
            @($queries[0],$queries[4],$queries[5],$queries[6],$queries[7],$queries[8],@{name='jobs';sql=$jobs})
        } else { $queries }
        foreach ($query in $selected) {
            try {
                $rows = Read-Metadata $connection $query.sql
                if ($query.name -eq 'objects' -and @($rows | Where-Object { $_.definition_bytes -gt 1048576 }).Count) {
                    throw 'definition_bound'
                }
                $record.sections += @{database=$database;name=$query.name;status='complete';rows=$rows}
            } catch {
                $record.sections += @{database=$database;name=$query.name;status='unavailable';
                    errorType=$_.Exception.GetType().Name}
            }
        }
        $connection.Dispose(); $connection=$null
    }
    $record.phase = 'metadata_collected_requires_review'
} catch {
    $record.phase = 'incomplete_requires_review'
    $record.errorType = $_.Exception.GetType().Name
} finally {
    if ($null -ne $connection) { $connection.Dispose() }
    $record.finishedUtc=[DateTime]::UtcNow.ToString('o')
    $record.elapsedSeconds=$timer.Elapsed.TotalSeconds
    try {
        $json=$record | ConvertTo-Json -Depth 12
        $bytes=[Text.Encoding]::UTF8.GetBytes($json)
        if ($bytes.Length -gt 8MB) { throw 'Output byte bound exceeded; empty receipt retained.' }
        $output.Write($bytes,0,$bytes.Length)
        $output.Flush($true)
    } finally { $output.Dispose() }
}
Write-Host ('D4 metadata receipt version 2 saved: ' + $outputPath)
Write-Host 'Manual/external consumers and effective runtime permissions remain unqualified.'
