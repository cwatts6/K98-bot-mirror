<#
Reviewed filesystem installation only. Preview is the default. No SQL, provider,
Bot, task, dependency installation, recursive delete or automatic rollback.
The operator approves an independently sealed, factual plan before -Apply.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PlanPath,
    [Parameter(Mandatory=$true)][string]$ExpectedPlanSHA256,
    [switch]$Apply,
    [switch]$OperatorHoldConfirmed,
    [switch]$BotStopped,
    [switch]$Worker,
    [string]$WorkerProgressPath
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function InvokeBoundedWorker([string]$Command,[string]$ProgressPath,[string]$ReceiptPath,[int]$TimeoutMs=60000) {
    $start=[Diagnostics.ProcessStartInfo]::new()
    $start.FileName='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
    $workerCommand='$ErrorActionPreference=''Stop'';$ProgressPreference=''SilentlyContinue'';'+$Command
    $start.Arguments='-NoProfile -NonInteractive -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($workerCommand))
    $start.UseShellExecute=$false; $start.CreateNoWindow=$true
    $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
    $process=[Diagnostics.Process]::new();$process.StartInfo=$start
    $journal=[IO.StreamWriter]::new([IO.File]::Open($ReceiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read))
    $bytes=[long]0;$clock=[Diagnostics.Stopwatch]::StartNew();$lastProgress=[long]0;$stamp=[datetime]::MinValue;$started=$false
    try {
        if(-not $process.Start()){throw 'Worker launch failed'}
        $started=$true
        $lineTask=$process.StandardOutput.ReadLineAsync();$errorTask=$process.StandardError.ReadToEndAsync()
        while($true) {
            if(Test-Path -LiteralPath $ProgressPath){$next=(Get-Item -LiteralPath $ProgressPath).LastWriteTimeUtc;if($next -ne $stamp){$stamp=$next;$lastProgress=$clock.ElapsedMilliseconds}}
            if($clock.ElapsedMilliseconds-$lastProgress -gt $TimeoutMs){throw 'Owned installation operation timeout; retain partial state'}
            if($lineTask.IsCompleted){
                $line=$lineTask.GetAwaiter().GetResult()
                if($null -eq $line){break}
                $bytes+=[Text.Encoding]::UTF8.GetByteCount($line)+2
                if($bytes -gt 20MB-4096){throw 'Installation receipt output limit; retain partial state'}
                $journal.WriteLine($line);$journal.Flush();Write-Output $line
                $lineTask=$process.StandardOutput.ReadLineAsync()
            } else {Start-Sleep -Milliseconds 10}
        }
        $remaining=[Math]::Max(1,$TimeoutMs-($clock.ElapsedMilliseconds-$lastProgress))
        if(-not $process.WaitForExit([int]$remaining)){throw 'Worker exit timeout'}
        if($process.ExitCode -ne 0 -or $errorTask.GetAwaiter().GetResult()){throw 'Worker stopped; retain partial receipts'}
    } catch {
        if($started -and -not $process.HasExited){$process.Kill();$null=$process.WaitForExit(5000)}
        $stop=@{Stage='STOP_INCOMPLETE_SUPERVISOR';FailureType=$_.Exception.GetType().FullName;Receipt=$ReceiptPath;Progress=$ProgressPath;Next='Retain partial actions; reconcile before retry or start'}|ConvertTo-Json -Compress
        $journal.WriteLine($stop);$journal.Flush();Write-Output $stop
        throw 'STOP_INCOMPLETE: retain supervised installation receipt'
    } finally {$journal.Dispose();$process.Dispose()}
}
function BeginOperation {
    if($script:progressPath){[IO.File]::WriteAllText($script:progressPath,[guid]::NewGuid().ToString('N'))}
}

# The public entry point supervises only its own child. A fresh progress file
# resets the deadline before each finite operation, never extending a stalled one.
if(-not $Worker){
    $receiptPath=Join-Path $PSScriptRoot ('source-boundary-receipt-'+[guid]::NewGuid().ToString('N')+'.jsonl')
    $progressPath=$receiptPath+'.progress'
    $null=[IO.File]::Open($progressPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read).Dispose()
    $command="& '"+$PSCommandPath.Replace("'","''")+"' -Worker -WorkerProgressPath '"+$progressPath.Replace("'","''")+"' -PlanPath '"+$PlanPath.Replace("'","''")+"' -ExpectedPlanSHA256 '"+$ExpectedPlanSHA256.Replace("'","''")+"'"
    if($Apply){$command+=' -Apply'};if($OperatorHoldConfirmed){$command+=' -OperatorHoldConfirmed'};if($BotStopped){$command+=' -BotStopped'}
    InvokeBoundedWorker $command $progressPath $receiptPath
    return
}
$progressPath=$WorkerProgressPath
if(-not $progressPath -or -not (Test-Path -LiteralPath $progressPath)){throw 'Supervised worker required'}
BeginOperation

function CanonicalPath([string]$Path) {
    if ($Path -cnotmatch '^[A-Za-z]:\\' -or $Path.Substring(2).Contains(':')) { throw 'Canonical local absolute path required' }
    $absolute=[IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($absolute.Length -lt 3 -or $absolute -cne $Path.TrimEnd('\')) { throw 'Noncanonical or root target refused' }
    return $absolute
}
function Inside([string]$Path,[string]$Root) {
    return $Path.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)
}
function CheckedItem([string]$Path) {
    $cursor=$Path
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item=Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse path refused' }
        }
        $cursor=[IO.Path]::GetDirectoryName($cursor)
    }
    return Get-Item -LiteralPath $Path -Force
}
function VerifyStateDirectories([string]$Root) {
    foreach($name in @('logs','data','downloads')) {
        $item=CheckedItem (Join-Path $Root $name)
        if(-not $item.PSIsContainer){throw 'Application state directory required'}
    }
}
function FileDigest([string]$Path) {
    BeginOperation
    $item=CheckedItem $Path
    if ($item.PSIsContainer -or $item.Length -gt 16MB) { throw 'Bounded file required' }
    $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $sha=[Security.Cryptography.SHA256]::Create()
    try {
        if($stream.Length -gt 16MB){throw 'Bounded file required'}
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()
    } finally {$sha.Dispose();$stream.Dispose()}
}
function VerifySourceDirectory([string]$Path,$KnownPaths,$MovePaths,[string]$SourceRoot) {
    BeginOperation
    $entries=@(Get-ChildItem -LiteralPath $Path -Force | Select-Object -First 1001)
    if($entries.Count -gt 1000){throw 'Source directory metadata bound exceeded'}
    # Match the runtime source-only exclusions without walking state or tooling.
    $excluded=@('.git','.pytest_cache','.ruff_cache','.codex_artifacts','.codex_security_scans','.pre-commit-home','tests','data','downloads','artifacts','docs','logs','smoke_artifacts','sql','assets')
    foreach($entry in $entries){
        if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Source reparse member refused'}
        if($entry.PSIsContainer){
            if($KnownPaths.Contains($entry.FullName) -or $MovePaths.Contains($entry.FullName) -or $excluded -ccontains $entry.Name -or ($Path -ceq $SourceRoot -and $entry.Name -ceq 'venv')){continue}
            throw 'Unreviewed source directory refused'
        }
        $extension=$entry.Extension.ToLowerInvariant()
        if($extension -ceq '.py'){
            if(-not $KnownPaths.Contains($entry.FullName)){throw 'Unreviewed Python source refused'}
        } elseif(@('.pyw','.pyc','.pyo','.pyd','.so') -ccontains $extension){throw 'Non-source executable module refused'}
        elseif(@('.exe','.com','.cmd','.bat','.ps1','.psm1','.psd1','.vbs','.vbe','.js','.jse','.wsf','.wsh','.hta','.dll','.scr','.cpl','.msi','.msp','.lnk','.reg') -ccontains $extension){
            if(-not $KnownPaths.Contains($entry.FullName)){throw 'Unreviewed executable/script refused'}
        }
    }
}
function ReadBoundedGit([string]$Arguments) {
    BeginOperation
    $start=[Diagnostics.ProcessStartInfo]::new()
    $start.FileName=$script:git
    $start.Arguments='-C "'+$script:root+'" '+$Arguments
    $start.UseShellExecute=$false; $start.CreateNoWindow=$true
    $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
    $process=[Diagnostics.Process]::new(); $process.StartInfo=$start
    try {
        if(-not $process.Start()){throw 'Git process failed'}
        $output=$process.StandardOutput.ReadToEndAsync(); $errorOutput=$process.StandardError.ReadToEndAsync()
        if(-not $process.WaitForExit(55000)){ $process.Kill(); throw 'Owned Git operation timeout; reconcile' }
        $text=$output.GetAwaiter().GetResult(); $errorText=$errorOutput.GetAwaiter().GetResult()
        if($process.ExitCode -ne 0 -or $errorText -or [Text.Encoding]::UTF8.GetByteCount($text) -gt 20MB){throw 'Git operation failed/output exceeded'}
        return $text.TrimEnd("`r","`n")
    } finally {$process.Dispose()}
}
function WriteReceipt($Value) {
    $line=$Value | ConvertTo-Json -Compress -Depth 6
    $script:receiptBytes+=[Text.Encoding]::UTF8.GetByteCount($line)+2
    if ($script:receiptBytes -gt 20MB) { throw 'Receipt output budget exceeded' }
    [Console]::WriteLine($line)
}
function PathId([string]$Path) {
    if(-not $script:pathIds.ContainsKey($Path)){$id=$script:pathIds.Count;$script:pathIds[$Path]=$id;WriteReceipt @{Stage='path';Id=$id;Value=$Path}}
    return $script:pathIds[$Path]
}
function AclId([string]$SDDL) {
    if(-not $script:aclIds.ContainsKey($SDDL)){$id=$script:aclIds.Count;$script:aclIds[$SDDL]=$id;WriteReceipt @{Stage='sddl';Id=$id;Value=$SDDL}}
    return $script:aclIds[$SDDL]
}
function SetProtection([string]$Path,[string]$SDDL) {
    BeginOperation
    $item=CheckedItem $Path
    $before=Get-Acl -LiteralPath $Path
    $pathId=PathId $Path;$priorId=AclId $before.Sddl;$nextId=AclId $SDDL
    WriteReceipt @{Stage='acl_intent';PathId=$pathId;PriorAclId=$priorId;ProposedAclId=$nextId}
    $clock=[Diagnostics.Stopwatch]::StartNew()
    if ($item.PSIsContainer) { $acl=[Security.AccessControl.DirectorySecurity]::new() }
    else { $acl=[Security.AccessControl.FileSecurity]::new() }
    $acl.SetSecurityDescriptorSddlForm($SDDL)
    Set-Acl -LiteralPath $Path -AclObject $acl
    $actual=Get-Acl -LiteralPath $Path
    if ($actual.GetOwner([Security.Principal.SecurityIdentifier]).Value -cne 'S-1-5-32-544' -or -not $actual.AreAccessRulesProtected) { throw 'Applied protection mismatch' }
    $desiredRules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | ForEach-Object {"$($_.IdentityReference.Value):$([int]$_.FileSystemRights):$([int]$_.InheritanceFlags):$([int]$_.PropagationFlags):$([int]$_.AccessControlType):$($_.IsInherited)"} | Sort-Object)
    $actualRules=@($actual.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | ForEach-Object {"$($_.IdentityReference.Value):$([int]$_.FileSystemRights):$([int]$_.InheritanceFlags):$([int]$_.PropagationFlags):$([int]$_.AccessControlType):$($_.IsInherited)"} | Sort-Object)
    if(($desiredRules -join "`n") -cne ($actualRules -join "`n")){throw 'Applied DACL rights mismatch'}
    if ($clock.ElapsedMilliseconds -gt 60000) { throw 'ACL operation budget exceeded; reconcile' }
    $actualId=AclId $actual.Sddl
    WriteReceipt @{Stage='acl_completed';PathId=$pathId;ObservedAclId=$actualId;ElapsedMs=$clock.ElapsedMilliseconds}
}
function NewProtectedDirectory([string]$Path,[string]$SDDL) {
    BeginOperation
    if (Test-Path -LiteralPath $Path) { throw 'Fresh installation directory required' }
    $parent=[IO.Path]::GetDirectoryName($Path)
    $null=CheckedItem $parent
    WriteReceipt @{Stage='directory_intent';Path=$Path}
    $null=New-Item -ItemType Directory -Path $Path
    SetProtection $Path $SDDL
}

$stage='plan'; $receiptBytes=[long]0;$pathIds=@{};$aclIds=@{}
try {
    $planItem=CheckedItem (CanonicalPath $PlanPath)
    if ($planItem.PSIsContainer -or $planItem.Length -gt 4MB -or $ExpectedPlanSHA256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Bounded sealed plan required' }
    # Parse exactly the bytes hashed, without reopening a mutable plan.
    $raw=[IO.File]::ReadAllBytes($planItem.FullName)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $digest=([BitConverter]::ToString($sha.ComputeHash($raw))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
    if ($digest -cne $ExpectedPlanSHA256) { throw 'Plan hash mismatch' }
    $plan=[Text.Encoding]::UTF8.GetString($raw).TrimStart([char]0xfeff) | ConvertFrom-Json
    if ($plan.status -cne 'REVIEWED_SOURCE_BOUNDARY_INSTALLATION_V1' -or $plan.source_root -cne 'C:\discord_file_downloader' -or $plan.proposed_control_root -cne 'C:\ProgramData\K98\S11') { throw 'Reviewed installation plan required' }
    $root=CanonicalPath $plan.source_root
    $control=CanonicalPath $plan.proposed_control_root
    $sid=$plan.application_sid
    if ($sid -cnotmatch '^S-1-5-21-[0-9-]+$' -or $plan.source_head -cnotmatch '^[0-9a-f]{40}$') { throw 'Exact application/source bindings required' }
    $installation=[guid]::ParseExact($plan.installation_id,'D').ToString()
    $preserve=$control+'\preserved\'+$installation
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    if ($env:COMPUTERNAME -cne $plan.computer_name -or $identity.User.Value -cne $sid -or (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Cryptography' -Name MachineGuid).MachineGuid -cne $plan.machine_guid) { throw 'Installation observer mismatch' }
    if ($Apply -and (-not $OperatorHoldConfirmed -or -not $BotStopped -or -not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))) { throw 'Apply requires administrative operator, actual hold and stopped Bot' }
    $stage='all_preflight'
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $immutable=@($plan.immutable_source_files)+@($plan.immutable_config_and_existing_key)
    if ($immutable.Count -lt 3 -or $immutable.Count -gt 4096 -or $plan.immutable_source_directories.Count -gt 1000 -or $plan.preserve_moves.Count -gt 1000) { throw 'Plan row bounds exceeded' }
    foreach($row in $immutable) {
        BeginOperation
        $path=CanonicalPath $row.path
        if (-not (Inside $path $root) -or (Inside $path ($root+'\.git')) -or (Inside $path ($root+'\venv')) -or -not $seen.Add($path)) { throw 'Immutable source path outside scope or duplicated' }
        $expected=if($row.PSObject.Properties['expected_reviewed_sha256']){$row.expected_reviewed_sha256}else{$row.digest}
        if ($expected -cnotmatch '^[0-9a-f]{64}$' -or (FileDigest $path) -cne $expected -or (Get-Acl -LiteralPath $path).Sddl -cne $row.prior_acl) { throw 'Immutable source/content/ACL drift' }
    }
    foreach($row in $plan.immutable_source_directories) {
        BeginOperation
        $path=CanonicalPath $row.path
        if (($path -cne $root -and -not (Inside $path $root)) -or (Inside $path ($root+'\.git')) -or (Inside $path ($root+'\venv')) -or -not $seen.Add($path) -or -not (CheckedItem $path).PSIsContainer -or (Get-Acl -LiteralPath $path).Sddl -cne $row.prior_acl) { throw 'Source directory drift/scope mismatch' }
    }
    if (-not $seen.Contains($root)) { throw 'Source root protection required' }
    $envPath=$root+'\.env'
    if ($plan.existing_environment.path -cne $envPath -or (FileDigest $envPath) -cne $plan.existing_environment.observed_sha256 -or (Get-Acl -LiteralPath $envPath).Sddl -cne $plan.existing_environment.prior_acl) { throw 'Private environment drift' }
    $moveSeen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach($row in $plan.preserve_moves) {
        BeginOperation
        $from=CanonicalPath $row.source; $to=CanonicalPath $row.destination
        if (-not (Inside $from $root) -or -not (Inside $to $preserve) -or -not $moveSeen.Add($from) -or (Test-Path -LiteralPath $to) -or -not (CheckedItem $from).PSIsContainer -or (Get-Acl -LiteralPath $from).Sddl -cne $row.prior_acl) { throw 'Preservation path/ACL conflict' }
        $null=CheckedItem ([IO.Path]::GetDirectoryName($to).Substring(0,3))
        if ($row.kind -ceq 'operator_confirmed_unused_legacy_directory') {
            if ([IO.Path]::GetDirectoryName($from) -cne $root -or @('Archive','botenv','downloads_test_phase3','downloads_test_phase3_rehearsal','exports','tools') -cnotcontains [IO.Path]::GetFileName($from) -or $to -cne ($preserve+'\legacy-root\'+[IO.Path]::GetFileName($from))) { throw 'Legacy move allowlist mismatch' }
        } elseif ($row.kind -ceq 'source_bytecode_cache') {
            $parent=[IO.Path]::GetDirectoryName($from)
            if (-not $seen.Contains($parent) -or [IO.Path]::GetFileName($from) -cne '__pycache__' -or $to -cne ($preserve+'\bytecode\'+$from.Substring($root.Length+1))) { throw 'Cache move scope mismatch' }
            $entries=@(Get-ChildItem -LiteralPath $from -Force | Select-Object -First 1001)
            if ($entries.Count -gt 1000 -or @($entries | Where-Object {$_.PSIsContainer -or ($_.Attributes -band [IO.FileAttributes]::ReparsePoint)}).Count -or (@($entries.Name | Sort-Object) -join "`n") -cne (@($row.expected_names | Sort-Object) -join "`n")) { throw 'Cache membership drift' }
        } else { throw 'Unknown preservation category' }
    }
    # Reject unreviewed executable files/directories before sealing any source.
    # Read only immediate entries in the finite reviewed import-directory list.
    foreach($row in $plan.immutable_source_directories){VerifySourceDirectory $row.path $seen $moveSeen $root}
    # Complete bounded metadata closure only under the explicitly approved existing venv.
    # No package contents, keys, business data or other filesystem trees are collected.
    $venv=$root+'\venv'; $stack=[Collections.Generic.Stack[string]]::new(); $stack.Push($venv)
    $dependencyPaths=[Collections.Generic.List[string]]::new()
    while($stack.Count) {
        BeginOperation
        $directory=$stack.Pop(); $null=CheckedItem $directory; $dependencyPaths.Add($directory)
        $entries=@(Get-ChildItem -LiteralPath $directory -Force | Select-Object -First 1001)
        if ($entries.Count -gt 1000) { throw 'Venv per-directory row bound exceeded' }
        foreach($entry in $entries) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Venv reparse member refused' }
            if($entry.PSIsContainer){$stack.Push($entry.FullName)}else{$dependencyPaths.Add($entry.FullName)}
            if($dependencyPaths.Count+$stack.Count -gt 50000){throw 'Venv metadata closure bound exceeded'}
        }
    }
    if ((FileDigest ($venv+'\Scripts\python.exe')) -cne $plan.venv_python_sha256 -or (FileDigest ($venv+'\pyvenv.cfg')) -cne $plan.venv_config_sha256) { throw 'Venv identity drift' }
    foreach($row in $plan.base_interpreter_observations) {
        BeginOperation
        $path=CanonicalPath $row.Path
        if ($path -cne 'C:\Program Files' -and $path -cne 'C:\Program Files\Python311' -and -not (Inside $path 'C:\Program Files\Python311')) { throw 'Base verification scope mismatch' }
        if($row.Present){$null=CheckedItem $path;if((Get-Acl -LiteralPath $path).Sddl -cne $row.SDDL){throw 'Base interpreter ACL drift'};if($row.PSObject.Properties['SHA256'] -and (FileDigest $path) -cne $row.SHA256){throw 'Base interpreter content drift'}}
        elseif(Test-Path -LiteralPath $path){throw 'Base optional path changed'}
    }
    $git='C:\Program Files\Git\cmd\git.exe'
    if ((FileDigest $git) -cne $plan.git_sha256) { throw 'Git pin mismatch' }
    if((ReadBoundedGit 'rev-parse HEAD') -cne $plan.source_head){throw 'Installed source mismatch'}
    if((ReadBoundedGit 'branch --show-current') -cne 'main'){throw 'Private main required'}
    if((ReadBoundedGit 'status --porcelain --untracked-files=no') -cne ''){throw 'Tracked source drift'}
    VerifyStateDirectories $root
    if((Test-Path -LiteralPath $control) -or (Test-Path -LiteralPath 'C:\ProgramData\K98')){throw 'Fresh control parent/root required; reconcile existing state'}
    WriteReceipt @{Stage='preflight_completed';ImmutableFiles=$immutable.Count;VenvMembers=$dependencyPaths.Count;PreserveMoves=$plan.preserve_moves.Count;Apply=[bool]$Apply}
    if(-not $Apply){WriteReceipt @{Stage='COMPLETED_PREVIEW_ONLY';ProductionWritten=$false};return}
    $stage='installation'
    $fileAcl="O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;0x1200a9;;;$sid)"
    $dirAcl="O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1200a9;;;$sid)"
    $privateDir="O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;$sid)"
    WriteReceipt @{Stage='installation_started';PlanSHA256=$digest;InstallationId=$installation}
    # Capture the full mutable interpreter ACL closure before any parent can
    # propagate permissions. Stop before effects if the receipt budget is exceeded.
    foreach($path in $dependencyPaths){BeginOperation;$pathId=PathId $path;$aclId=AclId (Get-Acl -LiteralPath $path).Sddl;WriteReceipt @{Stage='venv_prior_acl';PathId=$pathId;AclId=$aclId}}
    # Reserve worst-case bounded per-member intention/completion records before
    # effects. Interned paths and SDDL retain exact restoration inputs once.
    if($receiptBytes+($dependencyPaths.Count+$immutable.Count+1000)*400+1MB -gt 20MB-4096){throw 'Complete receipt capacity insufficient before effects'}
    $k98='C:\ProgramData\K98'
    if(Test-Path -LiteralPath $k98){throw 'Existing K98 parent requires explicit reconciliation'}
    NewProtectedDirectory $k98 $dirAcl
    NewProtectedDirectory $control $dirAcl
    NewProtectedDirectory ($control+'\preserved') $dirAcl
    NewProtectedDirectory $preserve $dirAcl
    foreach($row in $plan.preserve_moves) {
        $from=CanonicalPath $row.source; $to=CanonicalPath $row.destination
        # Validate final absolute same-volume targets again immediately before moving.
        if(-not (Inside $from $root) -or -not (Inside $to $preserve) -or [IO.Path]::GetPathRoot($from) -cne [IO.Path]::GetPathRoot($to) -or (Test-Path -LiteralPath $to)){throw 'Move guard failed'}
        $null=CheckedItem $from
        $parent=[IO.Path]::GetDirectoryName($to); $missing=[Collections.Generic.Stack[string]]::new()
        while(-not (Test-Path -LiteralPath $parent)){$missing.Push($parent);$parent=[IO.Path]::GetDirectoryName($parent)}
        while($missing.Count){NewProtectedDirectory ($missing.Pop()) $dirAcl}
        $null=CheckedItem ([IO.Path]::GetDirectoryName($to))
        WriteReceipt @{Stage='move_intent';Source=$from;Destination=$to;PriorSDDL=$row.prior_acl}
        BeginOperation;$moveClock=[Diagnostics.Stopwatch]::StartNew(); [IO.Directory]::Move($from,$to)
        if($moveClock.ElapsedMilliseconds -gt 60000){throw 'Move budget exceeded; reconcile'}
        WriteReceipt @{Stage='move_completed';Source=$from;Destination=$to}
    }
    foreach($path in @($dependencyPaths | Sort-Object Length -Descending)) { $item=CheckedItem $path; if($item.PSIsContainer){SetProtection $path $dirAcl}else{SetProtection $path $fileAcl} }
    foreach($row in $immutable){SetProtection $row.path $fileAcl}
    SetProtection $envPath $fileAcl
    foreach($name in @('logs','data','downloads')){SetProtection ($root+'\'+$name) $privateDir}
    # Both startup modes now atomically publish inside the private writable logs
    # directory. Retain any historical root PID leaf without using or rewriting it.
    foreach($row in @($plan.immutable_source_directories | Sort-Object {$_.path.Length} -Descending)){SetProtection $row.path $dirAcl}
    foreach($name in @('evidence','spool')){NewProtectedDirectory ($control+'\'+$name) $privateDir}
    if((FileDigest $envPath) -cne $plan.existing_environment.observed_sha256){throw 'Environment content changed'}
    WriteReceipt @{Stage='COMPLETED_FILESYSTEM_INSTALLATION_ONLY';BotStarted=$false;SqlConnected=$false;DependenciesInstalled=$false;Enrollment=$false;Activation=$false;Next='Return receipts; ordinary operator verification and static runtime installation remain separate'}
} catch {
    WriteReceipt @{Stage='STOP_INCOMPLETE';At=$stage;FailureType=$_.Exception.GetType().FullName;Next='Retain all partial receipts; no retry, automatic rollback, Bot start or activation until reconciled'}
    throw 'STOP_INCOMPLETE: retain filesystem installation receipt'
}
