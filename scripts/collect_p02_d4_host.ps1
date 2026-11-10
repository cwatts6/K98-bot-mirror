#requires -Version 5.1
<##
Read-only D4 host evidence. Run outside the installed application tree, using
Windows PowerShell 5.1 on MINI_AMD. Creates one private receipt; does not import
application code, execute inspected scripts, connect to SQL, or modify tasks.
##>
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$OutputFile)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ine 'MINI_AMD'){throw 'This collector requires MINI_AMD.'}
if($PSVersionTable.PSEdition -ne 'Desktop'){throw 'Use Windows PowerShell 5.1.'}
$outputPath=[IO.Path]::GetFullPath($OutputFile)
if(-not [IO.Directory]::Exists([IO.Path]::GetDirectoryName($outputPath))){throw 'Output parent must already exist.'}
$acl=New-Object Security.AccessControl.FileSecurity
$acl.SetAccessRuleProtection($true,$false)
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$acl.SetOwner($identity.User)
foreach($sid in @($identity.User,(New-Object Security.Principal.SecurityIdentifier 'S-1-5-18'))){
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule(
        $sid,[Security.AccessControl.FileSystemRights]::FullControl,
        [Security.AccessControl.AccessControlType]::Allow)))
}
$output=New-Object IO.FileStream($outputPath,[IO.FileMode]::CreateNew,
    [Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,
    4096,[IO.FileOptions]::None,$acl)
$timer=[Diagnostics.Stopwatch]::StartNew()
$script:readBytes=0L
$script:visited=0
$script:files=New-Object 'Collections.Generic.List[object]'
$script:seen=@{}
$record=[ordered]@{
    version=1;kind='p02_d4_host_metadata';phase='collecting'
    computer=$env:COMPUTERNAME;startedUtc=[DateTime]::UtcNow.ToString('o')
    collectorSHA256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    identitySID=$identity.User.Value
    elevated=([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    sections=@();limitations=@(
        'Private metadata only. Never publish this receipt.',
        'No SQL, business operation, task change, application import or inspected script execution.',
        'File and task snapshots are not atomic and do not establish deployment readiness.',
        'Lexical absence is not proof of no dynamic, remote, service or manual consumers.',
        'Task arguments are hashed, not copied; opaque actions require separate review.',
        'Configuration identities are file observations, not the running process environment or effective SQL rights.',
        'Three-minute budget is cooperative at item boundaries; a filesystem or scheduler read can outlast it.'
    )
}
function Check-Budget {
    if($timer.Elapsed.TotalSeconds -ge 180){throw 'time_bound'}
}
function Hash-Bytes([byte[]]$Bytes){
    $hash=[Security.Cryptography.SHA256]::Create()
    try {([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}
    finally {$hash.Dispose()}
}
function Assert-LocalPath([string]$Path){
    if($Path -notmatch '^[Cc]:\\' -or $Path.Substring(2).Contains(':')){throw 'local_path_required'}
    $full=[IO.Path]::GetFullPath($Path)
    $item=Get-Item -LiteralPath $full -Force
    while($null -ne $item){
        if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'reparse_path'}
        $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory}
    }
    return $full
}
function Read-Bounded([string]$Path,[int]$Limit=2MB){
    Check-Budget
    $full=Assert-LocalPath $Path
    $stream=[IO.File]::Open($full,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        $length=$stream.Length
        if($length -gt $Limit -or $script:readBytes+$length -gt 128MB){throw 'byte_bound'}
        $script:readBytes+=$length
        $raw=New-Object byte[] ([int]$length)
        $offset=0
        while($offset -lt $length){
            Check-Budget
            $count=$stream.Read($raw,$offset,$length-$offset)
            if($count -eq 0){throw 'file_changed'}
            $offset+=$count
        }
        if($stream.Length -ne $length){throw 'file_changed'}
        return ,$raw
    } finally {$stream.Dispose()}
}
function Decode-Text([byte[]]$Raw){
    $stream=[IO.MemoryStream]::new($Raw,$false)
    $reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$true)
    try {$reader.ReadToEnd()} finally {$reader.Dispose();$stream.Dispose()}
}
function Find-Roots([string]$Text){
    foreach($name in @('UPDATE_ALL','UPDATE_ALL2','UPDATE_RALLY_DATA','TEST','rally_data.csv',
        'usp_GetPendingLogBackupTriggers','usp_MarkLogBackupTriggerProcessed','usp_CleanupLogBackupTriggerQueue',
        'usp_start_rok_tracker_log_backup','sp_Import_Rally_Daily','sp_Import_Rally_AllTime')){
        if([regex]::IsMatch($Text,'(?i)(?<![\w])'+[regex]::Escape($name)+'(?![\w])')){$name}
    }
}
function Read-SourceFile([string]$Path){
    $full=Assert-LocalPath $Path
    if($script:seen.ContainsKey($full)){return}
    if($script:files.Count -ge 8192){throw 'file_count_bound'}
    $raw=Read-Bounded $full
    $text=Decode-Text $raw
    $script:files.Add([pscustomobject]@{path=$full;bytes=$raw.Length;sha256=(Hash-Bytes $raw)
        textLF_SHA256=(Hash-Bytes ([Text.Encoding]::UTF8.GetBytes($text.Replace("`r`n","`n"))))
        root_candidates=@(Find-Roots $text)})
    $script:seen[$full]=$true
}
function Read-SourceTree([string]$Path){
    $full=Assert-LocalPath $Path
    foreach($entry in [IO.Directory]::EnumerateFileSystemEntries($full)){
        Check-Budget
        $script:visited++
        if($script:visited -gt 16384){throw 'entry_count_bound'}
        $item=Get-Item -LiteralPath $entry -Force
        if($item.PSIsContainer){
            if($item.Name -in @('.git','.venv','venv','.codex_artifacts','.codex','.agents','.pytest_cache',
                '__pycache__','node_modules','tests','docs','logs','data','backups','local_artifacts','archive')){continue}
            Read-SourceTree $item.FullName
        } elseif($item.Extension -in @('.py','.ps1','.bat','.cmd')){Read-SourceFile $item.FullName}
    }
}
function Read-IdentitySettings([string]$Path){
    $text=Decode-Text (Read-Bounded $Path 256KB)
    $allowed=@('SQL_SERVER','SQL_DATABASE','SQL_USERNAME','S11_SQL_USERNAME','IMPORT_SQL_USERNAME',
        'IMPORT_USERNAME','SQL_MONITOR_SERVER','SQL_MONITOR_USERNAME','SQL_MONITOR_JOB_ID')
    $rows=@()
    foreach($line in $text.Split([char]10)){
        if($line -match '^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$' -and $Matches[1] -cin $allowed){
            $key=$Matches[1];$value=$Matches[2].Trim()
            $value=$value.Trim([char]34,[char]39)
            # Never echo arbitrary text under a misleading key or expand variables.
            $safe=$value -cmatch '^[A-Za-z0-9_\\.@{}:, -]{1,128}$'
            $rows+=@{key=$key;value=$(if($safe){$value}else{$null});status=$(if($safe){'literal'}else{'unresolved'})}
        }
    }
    return @{settings=$rows}
}
function Add-Section([string]$Name,[scriptblock]$Read){
    try {Check-Budget;$value=& $Read;$record.sections+=@{name=$Name;status='complete';value=$value}}
    catch {
        # Only our fixed sentinel codes are public within this private receipt.
        # Never copy arbitrary exception messages, even if they look like tokens.
        $safeCodes=@('time_bound','local_path_required','reparse_path','byte_bound','file_changed',
            'file_count_bound','entry_count_bound','folder_count_bound','task_count_bound',
            'action_count_bound','arguments_bound','updater_count_bound','startup_action_shape',
            'seed_path_shape','ref_shape','ref_unresolved','head_shape')
        $code=if($_.Exception.Message -cin $safeCodes){$_.Exception.Message}else{'read_failed'}
        $record.sections+=@{name=$Name;status='unavailable';error_type=$_.Exception.GetType().Name;error_code=$code}
    }
}
function Read-Tasks {
    $scheduler=New-Object -ComObject 'Schedule.Service'
    $scheduler.Connect()
    $folders=New-Object 'Collections.Generic.Queue[object]'
    $folders.Enqueue($scheduler.GetFolder('\'))
    $rows=New-Object 'Collections.Generic.List[object]'
    $folderCount=0
    while($folders.Count){
        Check-Budget
        if(++$folderCount -gt 512){throw 'folder_count_bound'}
        $folder=$folders.Dequeue()
        # GetFolders flags are reserved and must be zero; hidden TASKS use 1 below.
        foreach($child in $folder.GetFolders(0)){$folders.Enqueue($child)}
        foreach($task in $folder.GetTasks(1)){
            Check-Budget
            if($rows.Count -ge 2048){throw 'task_count_bound'}
            $actions=@()
            foreach($action in $task.Definition.Actions){
                if($actions.Count -ge 32){throw 'action_count_bound'}
                if($action.Type -ne 0){$actions+=@{type=$action.Type;status='opaque'};continue}
                $arguments=[string]$action.Arguments
                if($arguments.Length -gt 32768){throw 'arguments_bound'}
                $actions+=@{type=0;executable=[string]$action.Path;working_directory=[string]$action.WorkingDirectory
                    arguments_sha256=(Hash-Bytes ([Text.Encoding]::UTF8.GetBytes($arguments)))
                    root_candidates=@(Find-Roots $arguments)
                    script_candidates=@([regex]::Matches($arguments,'(?i)"(C:\\[^"\r\n]+\.(?:ps1|cmd|bat|py))"') | ForEach-Object {$_.Groups[1].Value})}
            }
            $rows.Add([pscustomobject]@{path=$task.Path;enabled=$task.Enabled;state=$task.State
                principal=$task.Definition.Principal.UserId;logon_type=$task.Definition.Principal.LogonType
                last_run_local=[string]$task.LastRunTime;last_result=$task.LastTaskResult;actions=$actions})
        }
    }
    return @{tasks=$rows.ToArray();folders=$folderCount}
}
function Read-UpdaterMembers([string]$Directory){
    $members=@()
    foreach($entry in [IO.Directory]::EnumerateFiles((Assert-LocalPath $Directory))){
        if($members.Count -ge 64){throw 'updater_count_bound'}
        $raw=Read-Bounded $entry 8MB
        $members+=@{name=[IO.Path]::GetFileName($entry);sha256=(Hash-Bytes $raw);bytes=$raw.Length}
    }
    return ,$members
}
function Read-ProtectedRelease {
    $scheduler=New-Object -ComObject 'Schedule.Service';$scheduler.Connect()
    $actions=$scheduler.GetFolder('\').GetTask('StartDLBotAfterSQL').Definition.Actions
    if($actions.Count -ne 1 -or $actions.Item(1).Type -ne 0){throw 'startup_action_shape'}
    if($actions.Item(1).Arguments -cnotmatch '^-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "(C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\Start-ReviewedAutomaticStartup.ps1)"$'){throw 'startup_action_shape'}
    $gate=$Matches[1];Read-SourceFile $gate
    $policyPath=Join-Path (Split-Path -Parent $gate) 'AutomaticStartupPolicy.json'
    $policyRaw=Read-Bounded $policyPath
    $policy=(Decode-Text $policyRaw)|ConvertFrom-Json
    $planPath=[string]$policy.seed_plan.path
    if($planPath -cnotmatch '^C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\ManualProcessPairPlan-CANDIDATE\.json$'){throw 'seed_path_shape'}
    $seedDirectory=Split-Path -Parent $planPath
    $members=@()
    foreach($name in @('ManualProcessPairPlan-CANDIDATE.json','authority-template.json','bot-template.json',
        'host_acl.json','bot_identity.json','identity_issuance.json','file_access.json','key_inventory.json','writer_drain.json','sql_installation.json')){
        $path=Join-Path $seedDirectory $name;$raw=Read-Bounded $path
        $members+=@{name=$name;sha256=(Hash-Bytes $raw);bytes=$raw.Length}
    }
    $botRaw=Read-Bounded (Join-Path $seedDirectory 'bot-template.json')
    $bot=(Decode-Text $botRaw)|ConvertFrom-Json
    $updater='C:\ProgramData\K98\S11\updater'
    $updaterFiles=Read-UpdaterMembers $updater
    # Original supported policies have no predecessor; later release policies do.
    $predecessor=if($null -ne $policy.PSObject.Properties['predecessor']){$policy.predecessor}else{$null}
    # Return only known contract fields, never arbitrary template properties.
    return @{gate=$gate;policy_path=$policyPath;policy_sha256=(Hash-Bytes $policyRaw)
        policy=@{version=$policy.version;predecessor=$predecessor;seed_plan=$policy.seed_plan
            source_hashes=$policy.source_hashes;flags=$policy.flags;state_directory=$policy.state_directory}
        seed_directory=$seedDirectory;seed_members=$members;updater=$updaterFiles
        bot_contracts=@{sql_contract=$bot.sql_contract;legacy_sql_contract=$bot.legacy_sql_contract
            application_sql_contract=$bot.application_sql_contract;source_hashes=$bot.source_hashes}}
}
try {
    Add-Section 'scheduled_tasks' {Read-Tasks}
    Add-Section 'protected_release' {Read-ProtectedRelease}
    Add-Section 'bot_source' {Read-SourceTree 'C:\discord_file_downloader';@{scope='code extensions excluding named data/dependency/history directories'}}
    Add-Section 'sql_deploy_source' {Read-SourceTree 'C:\K98-bot-SQL-Server\deploy';@{scope='deployment scripts only'}}
    Add-Section 'identity_settings' {Read-IdentitySettings 'C:\discord_file_downloader\.env'}
    Add-Section 'git_head' {
        $git='C:\discord_file_downloader\.git'
        $head=(Decode-Text (Read-Bounded (Join-Path $git 'HEAD') 1KB)).Trim()
        if($head -match '^[0-9a-f]{40}$'){@{head=$head;kind='detached'}}
        elseif($head -match '^ref: (refs/heads/[A-Za-z0-9_./-]+)$'){
            $ref=$Matches[1]
            if($ref.Contains('..')){throw 'ref_shape'}
            $path=Join-Path $git $ref
            if([IO.File]::Exists($path)){$commit=(Decode-Text (Read-Bounded $path 1KB)).Trim()}
            else {
                $packed=Decode-Text (Read-Bounded (Join-Path $git 'packed-refs'))
                $matchesRef=@([regex]::Matches($packed,'(?m)^([0-9a-f]{40}) '+[regex]::Escape($ref)+'\r?$'))
                if($matchesRef.Count -ne 1){throw 'ref_unresolved'}
                $commit=$matchesRef[0].Groups[1].Value
            }
            if($commit -notmatch '^[0-9a-f]{40}$'){throw 'head_shape'}
            @{head=$commit;ref=$ref;kind='branch'}
        } else {throw 'head_shape'}
    }
    $record.phase='metadata_collected_requires_review'
} finally {
    $record.files=$script:files.ToArray()
    $record.finishedUtc=[DateTime]::UtcNow.ToString('o')
    $record.elapsedSeconds=$timer.Elapsed.TotalSeconds
    $record.readBytes=$script:readBytes
    try {
        $json=$record|ConvertTo-Json -Depth 35
        $bytes=[Text.Encoding]::UTF8.GetBytes($json)
        if($bytes.Length -gt 8MB){throw 'output_byte_bound'}
        $output.Write($bytes,0,$bytes.Length);$output.Flush($true)
    } finally {$output.Dispose()}
}
Write-Host ('D4 host receipt version 1: '+$outputPath)
Write-Host 'Private metadata only; no application, SQL or task changes were made.'
