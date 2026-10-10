[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ManifestPath,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSHA256,
    [ValidateRange(30,3600)][int]$WaitSeconds=900,
    [switch]$Resume,
    [switch]$AlreadyStopped
)
# A reviewed release supplies SQL/source/seed/apply/readiness scripts and their
# authoritative probes. The Bot can request a restart, never choose executable code.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($PSVersionTable.PSEdition -cne 'Desktop'){throw 'Run with Windows PowerShell 5.1 for atomic Windows ACL creation'}
$powershell='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
# Resolve administrative commands only from Windows, never a caller's module path.
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
$env:PATHEXT='.EXE;.COM'
$env:SystemRoot='C:\Windows';$env:windir='C:\Windows';$env:ComSpec='C:\Windows\System32\cmd.exe'
foreach($name in @('PYTHONPATH','PYTHONHOME','PYTHONEXECUTABLE','__PYVENV_LAUNCHER__')){[Environment]::SetEnvironmentVariable($name,$null,'Process')}

function Get-BytesHash([byte[]]$Bytes) {
    $hash=[Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() }
    finally { $hash.Dispose() }
}
function Read-Pinned([string]$Path,[string]$Hash,[long]$Limit) {
    $item=Get-Item -LiteralPath $Path -Force
    if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt $Limit){throw 'Invalid bounded release member'}
    $bytes=[IO.File]::ReadAllBytes($item.FullName)
    if($bytes.Length -gt $Limit -or (Get-BytesHash $bytes) -cne $Hash.ToLowerInvariant()){throw 'Release checksum mismatch'}
    return ,$bytes
}
function Assert-AdminPath([string]$Path) {
    $item=Get-Item -LiteralPath $Path -Force
    $depth=0
    $leafDepth=if($item.PSIsContainer){0}else{1}
    while($null -ne $item) {
        if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Protected path reparse point refused'}
        $acl=Get-Acl -LiteralPath $item.FullName
        $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
        if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw 'Protected path owner differs'}
        $mask=if($depth -le $leafDepth){0x500d0156}else{0x500d0040}
        foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
            if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
               ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and
               $ace.IdentityReference.Value -notin $trusted -and
               ([long]$ace.FileSystemRights -band $mask) -ne 0){throw 'Untrusted write access to deployment control'}
        }
        $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory}
        $depth++
    }
}
function New-ControlAcl([bool]$Directory) {
    $acl=if($Directory){[Security.AccessControl.DirectorySecurity]::new()}else{[Security.AccessControl.FileSecurity]::new()}
    $inherit=if($Directory){[Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit}else{[Security.AccessControl.InheritanceFlags]::None}
    $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
    $acl.SetAccessRuleProtection($true,$false)
    foreach($sid in @('S-1-5-18','S-1-5-32-544',$manifest.application_sid)) {
        $rights=if($sid -ceq $manifest.application_sid){[Security.AccessControl.FileSystemRights]::ReadAndExecute}else{[Security.AccessControl.FileSystemRights]::FullControl}
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),$rights,$inherit,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
    }
    return $acl
}
function Write-NewBytes([string]$Path,[byte[]]$Bytes) {
    Assert-AdminPath (Split-Path -Parent $Path)
    $stream=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,(New-ControlAcl $false))
    try { $stream.Write($Bytes,0,$Bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    Assert-AdminPath $Path
}
function Write-NewRecord([string]$Path,$Value) {
    Write-NewBytes $Path ([Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 30 -Compress)))
}
function Read-Control([string]$Path) {
    Assert-AdminPath $Path
    if((Get-Item -LiteralPath $Path).Length -gt 65536){throw 'Control record exceeds bound'}
    Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}
function Read-IncarnationIssuer($Policy,[string]$Incarnation) {
    Assert-AdminPath $Policy.seed_plan.path
    $planRaw=Read-Pinned $Policy.seed_plan.path $Policy.seed_plan.sha256 1MB
    $plan=[Text.Encoding]::UTF8.GetString($planRaw)|ConvertFrom-Json
    if(-not [IO.Path]::IsPathRooted($plan.commit_file)){throw 'Absolute pinned plan commit path required'}
    $runtimeRoot=Split-Path -Parent (Split-Path -Parent $plan.commit_file)
    Read-Control (Join-Path (Join-Path $runtimeRoot $Incarnation) 'AutomaticIssuer.json')
}
function Invoke-ReleaseScript($Invocation) {
    $member=@($script:manifest.members|Where-Object {$_.name -ceq $Invocation.file})
    if($member.Count -ne 1 -or $Invocation.file -notmatch '\.ps1$'){throw 'Unlisted release script'}
    $path=Join-Path $script:staged $Invocation.file
    Assert-AdminPath $path
    $null=Read-Pinned $path $member[0].sha256 16MB
    $arguments=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$path)
    foreach($property in $Invocation.arguments.PSObject.Properties) {
        if($property.Name -notmatch '^[A-Za-z][A-Za-z0-9]*$' -or $property.Value -isnot [string]){throw 'Only explicit string parameters supported'}
        $arguments+=('-'+$property.Name)
        $arguments+=$property.Value
    }
    & $powershell @arguments | Out-Host
    return $LASTEXITCODE
}

function Invoke-ReleaseSteps($Steps,[string]$Receipts,[string]$ReleaseId) {
    foreach($step in $steps) {
        $intent=Join-Path $receipts ($step.id+'.intent.json')
        $done=Join-Path $receipts ($step.id+'.complete.json')
        $observed=Invoke-ReleaseScript $step.verify
        if($observed -eq 0) {
            if(-not(Test-Path -LiteralPath $done)){Write-NewRecord $done @{stage='verified';release_id=$releaseId;step=$step.id}}
            continue
        }
        if($observed -ne 10){throw ('Outcome unresolved at '+$step.id+'; no later step executed')}
        if((Test-Path -LiteralPath $intent) -or (Test-Path -LiteralPath $done)){throw ('Previously observed '+$step.id+' has no confirmed current result; retained for outcome review, not automatically replayed')}
        Write-NewRecord $intent @{stage='starting';release_id=$releaseId;step=$step.id}
        if((Invoke-ReleaseScript $step.apply) -ne 0){throw ('Apply failed at '+$step.id+'; retain evidence and resume only through verification')}
        if((Invoke-ReleaseScript $step.verify) -ne 0){throw ('Postcondition unconfirmed at '+$step.id+'; later steps remain stopped')}
        Write-NewRecord $done @{stage='verified';release_id=$releaseId;step=$step.id}
    }
}

function Assert-AmendmentSelection([string]$Path,$Current,[string]$Hash) {
    $selected=Read-Control $Path
    if($selected.amendment_id -cne $Current.amendment.id -or $selected.manifest_sha256 -cne $Hash.ToLowerInvariant() -or $selected.release_id -cne $Current.release_id){throw 'Another amendment is selected; preserve its outcome'}
}

function Assert-ReleaseAmendment($Current,[string]$BaseStage) {
    # One explicit amendment of a drained version-one release before any step
    # completed. SQL reconciliation belongs to the reviewed new preflight.
    $a=$Current.amendment
    if((($a.PSObject.Properties.Name|Sort-Object) -join ',') -cne 'base_manifest_sha256,failed_step_id,id' -or
       ([guid]$a.id).ToString() -cne $a.id -or $a.base_manifest_sha256 -cnotmatch '^[a-f0-9]{64}$' -or
       $a.failed_step_id -cnotmatch '^[a-z0-9-]{1,60}$'){throw 'Exact release amendment reference required'}
    Assert-AdminPath $BaseStage
    $baseFile=Join-Path $BaseStage '.release.json';Assert-AdminPath $baseFile
    $base=[Text.Encoding]::UTF8.GetString((Read-Pinned $baseFile $a.base_manifest_sha256 65536))|ConvertFrom-Json
    if($base.version -ne 1){throw 'Only an original version-one release can be amended'}
    foreach($field in @('release_id','host','application_sid','repository')) {
        if($base.$field -cne $Current.$field){throw ('Amendment changes original '+$field)}
    }
    foreach($field in @('policy','issuer_launcher')) {
        if($base.$field.path -cne $Current.$field.path -or $base.$field.sha256 -cne $Current.$field.sha256){throw ('Amendment changes original '+$field)}
    }
    if($base.steps[0].kind -cne 'sql' -or $base.steps[0].id -cne $a.failed_step_id){throw 'Amendment requires the original first SQL step'}
    if(@($Current.steps).Count -eq 0 -or $Current.steps[0].kind -cne 'sql' -or $Current.steps[0].id -ceq $a.failed_step_id){throw 'Amendment must begin with a distinct corrective SQL step'}
    $oldApply=@($base.members|Where-Object {$_.name -ceq $base.steps[0].apply.file})
    $newApply=@($Current.members|Where-Object {$_.name -ceq $Current.steps[0].apply.file})
    # A new directory or renamed copy cannot turn the failed executable into
    # a fresh operation. The different corrective script still needs review.
    if($oldApply.Count -ne 1 -or $newApply.Count -ne 1 -or
       $oldApply[0].sha256 -cnotmatch '^[a-f0-9]{64}$' -or $newApply[0].sha256 -cnotmatch '^[a-f0-9]{64}$' -or
       $oldApply[0].sha256 -ceq $newApply[0].sha256){throw 'Amendment requires a different pinned corrective SQL apply script; failed-script replay is prohibited'}
    $directory=Join-Path $BaseStage '.receipts';Assert-AdminPath $directory
    $entries=@(Get-ChildItem -LiteralPath $directory -Force)
    $expected=$a.failed_step_id+'.intent.json'
    if($entries.Count -ne 1 -or $entries[0].PSIsContainer -or $entries[0].Name -cne $expected){throw 'Original release progressed beyond its first SQL intent; amendment refused'}
    $intent=Read-Control $entries[0].FullName
    if($intent.stage -cne 'starting' -or $intent.release_id -cne $Current.release_id -or $intent.step -cne $a.failed_step_id){throw 'Original SQL intent differs'}
    if(Test-Path -LiteralPath (Join-Path $BaseStage 'start-requested.json')){throw 'An original start request prohibits amendment'}
}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run the release script in an administrative PowerShell'}
$raw=Read-Pinned $ManifestPath $ExpectedSHA256 65536
$script:manifest=[Text.Encoding]::UTF8.GetString($raw)|ConvertFrom-Json
if($manifest.version -notin @(1,2) -or $manifest.host -cne $env:COMPUTERNAME -or $manifest.application_sid -cne $identity.User.Value){throw 'Release host or identity differs'}
if(($manifest.version -eq 2) -ne ($manifest.PSObject.Properties.Name -ccontains 'amendment')){throw 'Release version and amendment fields differ'}
$releaseId=([guid]$manifest.release_id).ToString()
if($releaseId -cne $manifest.release_id){throw 'Canonical release ID required'}
Assert-AdminPath $manifest.policy.path
$policyRaw=Read-Pinned $manifest.policy.path $manifest.policy.sha256 1MB
$policy=[Text.Encoding]::UTF8.GetString($policyRaw)|ConvertFrom-Json
Assert-AdminPath $policy.state_directory
Assert-AdminPath $powershell
$script:staged=Join-Path $policy.state_directory ('release-'+$releaseId)
$amendmentSelection=$null
if($manifest.version -eq 2) {
    Assert-ReleaseAmendment $manifest $staged
    if(-not(Test-Path -LiteralPath (Join-Path $policy.state_directory ('deployment-drained-'+$releaseId+'.json')))){throw 'Existing protected drain required before amendment'}
    $amendmentSelection=Join-Path $staged '.amendment-selected.json'
    if(Test-Path -LiteralPath $amendmentSelection) {
        Assert-AmendmentSelection $amendmentSelection $manifest $ExpectedSHA256
    }
    $script:staged=Join-Path $staged ('amendment-'+$manifest.amendment.id)
}
$members=@($manifest.members)
if($members.Count -lt 1 -or $members.Count -gt 128){throw 'Bounded release member inventory required'}
$seen=@{}
foreach($member in $members) {
    if($member.name -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,120}$' -or $member.name.EndsWith('.') -or $member.name -match '^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)' -or $seen.ContainsKey($member.name)){throw 'Unique flat release member required'}
    $seen[$member.name]=$true
}
$steps=@($manifest.steps)
if($steps.Count -lt 2 -or $steps.Count -gt 32 -or $steps[-1].kind -cne 'readiness'){throw 'Bounded deployment steps ending in readiness required'}
$rank=@{sql=1;source=2;seed=3;start=4;readiness=5};$last=0;$stepNames=@{}
foreach($step in $steps) {
    if(-not $rank.ContainsKey($step.kind) -or $rank[$step.kind] -lt $last -or $step.id -notmatch '^[a-z0-9-]{1,60}$' -or $stepNames.ContainsKey($step.id)){throw 'Release order or step identity differs'}
    $last=$rank[$step.kind];$stepNames[$step.id]=$true
    foreach($invocation in @($step.apply,$step.verify)) {
        if(-not $seen.ContainsKey($invocation.file) -or $invocation.file -notmatch '\.ps1$'){throw 'Each step needs listed apply and verify scripts'}
    }
}
foreach($kind in @('seed','start','readiness')) {
    if(@($steps|Where-Object {$_.kind -ceq $kind}).Count -ne 1){throw 'One seed installation, start and readiness step required'}
}
if(-not $seen.ContainsKey($manifest.preflight.file)){throw 'A listed release preflight is required'}
if(-not (Test-Path -LiteralPath $staged)) {
    if($Resume){throw 'No staged release to resume'}
    # The protected seed directory already denies application write access.
    $null=[IO.Directory]::CreateDirectory($staged,(New-ControlAcl $true))
    Assert-AdminPath $staged
    Write-NewBytes (Join-Path $staged '.release.json') $raw
} else {
    if(-not $Resume){throw 'Release already staged; use -Resume with the same manifest'}
    Assert-AdminPath $staged
    $null=Read-Pinned (Join-Path $staged '.release.json') $ExpectedSHA256 65536
}
$source=Split-Path -Parent (Get-Item -LiteralPath $ManifestPath).FullName
foreach($member in $members) {
    $destination=Join-Path $staged $member.name
    if(-not(Test-Path -LiteralPath $destination)) {
        $bytes=Read-Pinned (Join-Path $source $member.name) $member.sha256 16MB
        Write-NewBytes $destination $bytes
    }
    Assert-AdminPath $destination
    $null=Read-Pinned $destination $member.sha256 16MB
}
if((Invoke-ReleaseScript $manifest.preflight) -ne 0){throw 'Release preflight failed; no restart requested'}
if($null -ne $amendmentSelection) {
    if(-not(Test-Path -LiteralPath $amendmentSelection)) {
        Write-NewRecord $amendmentSelection @{amendment_id=$manifest.amendment.id;manifest_sha256=$ExpectedSHA256.ToLowerInvariant();release_id=$releaseId}
    }
    # Another launcher may have selected a manifest while preflight ran.
    # CreateNew is exclusive; any observed selection must still match ours.
    Assert-AmendmentSelection $amendmentSelection $manifest $ExpectedSHA256
}
$journals=@(Get-ChildItem -LiteralPath $policy.state_directory -Filter 'incarnation-*.json' -File|Sort-Object Name)
if($journals.Count -lt 1 -or $journals.Count -gt 1000){throw 'Existing reviewed incarnation required; bootstrap is separate'}
$previous=Read-Control $journals[-1].FullName
if($previous.policy_sha256 -cne $manifest.policy.sha256){throw 'Current incarnation policy differs'}
if($journals[-1].Name -notmatch '^incarnation-[0-9]{20}-([0-9a-f-]{36})\.json$'){throw 'Invalid incarnation filename'}
$incarnation=$Matches[1]
$issuerRecord=Read-IncarnationIssuer $policy $incarnation
if($issuerRecord.plan_sha256 -cne $previous.publication.plan_sha256){throw 'Issuer publication differs'}
$issuerProcess=$null
try {
    $candidate=[Diagnostics.Process]::GetProcessById([int]$issuerRecord.issuer.pid)
    $null=$candidate.Handle # Retain the native process identity across PID reuse.
    if($candidate.StartTime.ToFileTimeUtc() -eq [long]$issuerRecord.issuer.created_filetime){$issuerProcess=$candidate}else{$candidate.Dispose()}
} catch [ArgumentException] {
    # An absent issuer is usable only with its protected completed-drain receipt below.
}
$requestPath=Join-Path $policy.state_directory 'deployment-request.json'
$receiptPath=Join-Path $policy.state_directory ('deployment-drained-'+$releaseId+'.json')
if(-not(Test-Path -LiteralPath $receiptPath)) {
    $gate=Join-Path (Split-Path -Parent $manifest.policy.path) 'Start-ReviewedAutomaticStartup.ps1'
    $task=Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
    $actions=@($task.Actions)
    $expectedArguments='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$gate+'"'
    if($actions.Count -ne 1 -or $actions[0].Execute -cne $powershell -or $actions[0].Arguments -cne $expectedArguments){throw 'Installed startup action differs from this release predecessor'}
    $null=Disable-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
    if((Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL').Settings.Enabled){throw 'Scheduled launch exclusion failed'}
}
if(Test-Path -LiteralPath $requestPath) {
    $request=Read-Control $requestPath
    if($request.release_id -cne $releaseId -or $request.policy_sha256 -cne $manifest.policy.sha256 -or $request.sequence -ne $previous.sequence){throw 'Another or stale release request exists'}
} else {
    Write-NewRecord $requestPath ([ordered]@{version=1;release_id=$releaseId;policy_sha256=$manifest.policy.sha256;sequence=$previous.sequence;publication=$previous.publication})
}
$requestHash=(Get-FileHash -LiteralPath $requestPath -Algorithm SHA256).Hash.ToLowerInvariant()
if($AlreadyStopped -and -not(Test-Path -LiteralPath $receiptPath)) {
    if($null -ne $issuerProcess -and -not $issuerProcess.HasExited){throw 'Issuer is still running; use graceful restart for the staged release'}
    Assert-AdminPath $manifest.issuer_launcher.path
    $null=Read-Pinned $manifest.issuer_launcher.path $manifest.issuer_launcher.sha256 4MB
    $issuerScript=Join-Path $manifest.repository 'scripts\run_export_startup_issuer.py'
    Assert-AdminPath $issuerScript
    $null=Read-Pinned $issuerScript $policy.source_hashes.'scripts/run_export_startup_issuer.py' 2MB
    & $manifest.issuer_launcher.path -I -B $issuerScript --policy $manifest.policy.path --drain-only
    if($LASTEXITCODE -ne 0){throw 'Stopped-release drain could not be verified; no source changes applied'}
} elseif(-not(Test-Path -LiteralPath $receiptPath)) {
    Write-Host 'Release staged. Run /ops graceful_restart in Discord. Waiting for protected drain receipt.'
} else {
    Write-Host 'Protected drain already verified. Continuing this release; do not restart again.'
}
$clock=[Diagnostics.Stopwatch]::StartNew()
while(-not(Test-Path -LiteralPath $receiptPath)) {
    if($clock.Elapsed.TotalSeconds -ge $WaitSeconds){throw 'No drain receipt yet; release retained. Resume the same manifest, do not restart repeatedly.'}
    Start-Sleep -Seconds 1
}
$receipt=Read-Control $receiptPath
if($receipt.stage -cne 'deployment_drained' -or $receipt.release_id -cne $releaseId -or $receipt.request_sha256 -cne $requestHash){throw 'Deployment drain receipt differs'}
if($null -ne $issuerProcess) {
    try {
        if(-not $issuerProcess.WaitForExit(30000)){throw 'Old issuer has not exited; source remains unchanged'}
    } finally {$issuerProcess.Dispose()}
}
$receipts=Join-Path $staged '.receipts'
if(-not(Test-Path -LiteralPath $receipts)){$null=[IO.Directory]::CreateDirectory($receipts,(New-ControlAcl $true))}
Assert-AdminPath $receipts
Invoke-ReleaseSteps $steps $receipts $releaseId
Write-Host ('Release verified: '+$releaseId)
