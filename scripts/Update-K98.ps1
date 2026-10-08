[CmdletBinding()]
param([switch]$PrepareOnly)
# Routine operator entrypoint: run this same script, then the prompted Discord
# restart. No release-specific arguments, packet editing or hash entry.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Use Windows PowerShell 5.1, Run as administrator.'}
if($env:COMPUTERNAME -cne 'MINI_AMD'){throw 'This is the MINI_AMD production updater. Do not run it on the development PC.'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as administrator using the existing bot deployment account.'}
if($identity.Owner.Value -cne 'S-1-5-32-544'){throw 'Administrative default object owner required. No source or task change performed.'}
$root='C:\discord_file_downloader'
$powershell='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
foreach($name in @('PYTHONPATH','PYTHONHOME','PYTHONEXECUTABLE','__PYVENV_LAUNCHER__')){[Environment]::SetEnvironmentVariable($name,$null,'Process')}

# The updater and helper are installed under the same protected source boundary
# as the existing administrative launch gate. Verify custody before dot-sourcing.
function Assert-UpdaterCustody([string]$Path) {
 $item=Get-Item -LiteralPath $Path -Force
 $strict=if($item -is [IO.DirectoryInfo]){0}else{1};$depth=0
 $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
 while($null -ne $item) {
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Updater reparse path: '+$item.FullName)}
  $acl=Get-Acl -LiteralPath $item.FullName
  if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw ('Updater owner differs: '+$item.FullName)}
  $mask=if($depth -le $strict){0x500d0156}else{0x500d0040}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
   if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
      ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and
      $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band $mask) -ne 0){throw ('Updater write access differs: '+$item.FullName)}
  }
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory};$depth++
 }
}
Assert-UpdaterCustody $PSCommandPath
$library=Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'
Assert-UpdaterCustody $library
. $library -Action Library
$script:c=[pscustomobject]@{root=$root;sid=$identity.User.Value;git_path='C:\Program Files\Git\cmd\git.exe';git_sha256=''}
$updates='C:\ProgramData\K98\S11\updates'
if(-not(Test-Path -LiteralPath $updates)){New-Directory $updates}
Assert-Protected $updates
# Prevent two operator windows from preparing or deploying concurrently. The
# file is protected; the exclusive handle is retained for this whole operation.
$lockPath=Join-Path $updates 'operator.lock'
if(-not(Test-Path -LiteralPath $lockPath)){Write-New $lockPath ([byte[]]@(0))}
Assert-Protected $lockPath
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$transcript=Join-Path $updates ('update-'+[datetime]::UtcNow.ToString('yyyyMMddTHHmmssfff')+'.txt')
$null=Start-Transcript -LiteralPath $transcript -NoClobber
try {
 $active=Join-Path $updates 'active.json'
 if(Test-Path -LiteralPath $active) {
  $saved=Read-Json $active
  $work=$saved.directory
  if($work -cnotmatch '^C:\\ProgramData\\K98\\S11\\updates\\[0-9a-f-]{36}$'){throw 'Saved update path differs'}
  $prepared=Read-Json (Join-Path $work 'prepared.json')
  if(Test-Path -LiteralPath (Join-Path $work 'verified.json')) {
   # Only the pointer is removed. All immutable release evidence is retained.
   Remove-Item -LiteralPath $active
   $prepared=$null
  } else {
   $savedManifest=Read-Json $prepared.manifest $prepared.manifest_sha256
   $savedPolicy=Read-Json $savedManifest.policy.path $savedManifest.policy.sha256
   $request=Join-Path $savedPolicy.state_directory 'deployment-request.json'
   $drained=Join-Path $savedPolicy.state_directory ('deployment-drained-'+$savedManifest.release_id+'.json')
   $receipts=Join-Path (Join-Path $savedPolicy.state_directory ('release-'+$savedManifest.release_id)) '.receipts'
   if(-not(Test-Path -LiteralPath $request) -and -not(Test-Path -LiteralPath $drained) -and -not(Test-Path -LiteralPath $receipts)) {
    # Preparation and preflight have not crossed the durable deployment request.
    # Refresh observations automatically: a normal restart since PrepareOnly
    # must not strand the operator with a stale native process/session binding.
    # Retain the unused package; remove only its active pointer.
    Remove-Item -LiteralPath $active
    $prepared=$null
   }
  }
 } else {$prepared=$null}
 if($null -eq $prepared) {
  $clock=[Diagnostics.Stopwatch]::StartNew()
  $task=Task
  $actions=$task.Definition.Actions
  if($actions.Count -ne 1 -or $actions.Item(1).Path -cne $powershell){throw 'Installed startup action differs'}
  $arguments=$actions.Item(1).Arguments
  if($arguments -cnotmatch '^-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "(C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\Start-ReviewedAutomaticStartup.ps1)"$'){throw 'Installed protected startup gate cannot be resolved'}
  $gatePath=$Matches[1]
  $gateBytes=Read-Bytes $gatePath '' 1MB
  $gate=[Text.Encoding]::UTF8.GetString($gateBytes)
  $seedDirectory=Split-Path -Parent $gatePath
  $policyPath=Join-Path $seedDirectory 'AutomaticStartupPolicy.json'
  $policyBytes=Read-Bytes $policyPath '' 1MB
  $policyHash=Hash $policyBytes
  # Literal lookup avoids executing launch-gate code to discover its data.
  if(-not $gate.Contains('$policyHash='''+$policyHash+'''')){throw 'Startup gate policy binding differs'}
  if(-not $gate.Contains('$policy='''+$policyPath+'''')){throw 'Startup gate policy path differs'}
  $policy=[Text.Encoding]::UTF8.GetString($policyBytes)|ConvertFrom-Json
  $plan=Read-Json $policy.seed_plan.path $policy.seed_plan.sha256
  if($plan.application_sid -cne $c.sid){throw 'Use the installed deployment account'}
  if($gate -cnotmatch "Assert-PinnedFile 'C:\\Program Files\\Git\\cmd\\git.exe' '([0-9a-f]{64})'"){throw 'Installed Git executable binding missing'}
  $c.git_sha256=$Matches[1]
  $null=Read-Bytes $c.git_path $c.git_sha256 2MB
  $venvPath=Join-Path $root 'venv\Scripts\python.exe'
  if($gate -cnotmatch "Assert-PinnedFile 'C:\\discord_file_downloader\\venv\\Scripts\\python.exe' '([0-9a-f]{64})'"){throw 'Installed venv binding missing'}
  $venvHash=$Matches[1]
  $null=Read-Bytes $venvPath $venvHash 4MB
  # The shared Git worker reads this empty fixed configuration from scripts.
  $empty=Join-Path $PSScriptRoot 'EmptyGitConfig.txt'
  if(-not(Test-Path -LiteralPath $empty)){Write-New $empty ([byte[]]@())}
  $before=Git 'rev-parse HEAD'
  Assert-Source $policy.source_hashes $before
  $remote=Git 'remote get-url origin'
  if($remote -notmatch '^https://github\.com/cwatts6/K98-bot(?:\.git)?$'){throw 'Production origin must be private cwatts6/K98-bot'}
  # Use Git's installed credential manager, never a helper named by user config.
  $credential='C:\Program Files\Git\mingw64\bin\git-credential-manager.exe'
  Assert-Protected $credential
  Write-Host 'Checking private main and preparing this update automatically...'
  $null=Git ('-c credential.helper= -c credential.helper="C:/Program\ Files/Git/mingw64/bin/git-credential-manager.exe" fetch --no-tags --no-recurse-submodules origin +refs/heads/main:refs/remotes/origin/main')
  $target=Git 'rev-parse refs/remotes/origin/main'
  if($before -ceq $target){Write-Host 'Already current. No restart required.';return}
  $null=Git ('merge-base --is-ancestor '+$before+' '+$target)
  $seed=[ordered]@{}
  foreach($name in @('authority-template.json','bot-template.json','ManualProcessPairPlan-CANDIDATE.json','AutomaticStartupPolicy.json','host_acl.json','bot_identity.json','identity_issuance.json','file_access.json','key_inventory.json','writer_drain.json','sql_installation.json')){$seed[$name]=Read-Json (Join-Path $seedDirectory $name)}
  $account=$seed['authority-template.json'].runtime_registration.account
  $c | Add-Member -NotePropertyName account -NotePropertyValue $account
  if($account -notmatch '^[A-Za-z0-9_.@:-]{1,128}$'){throw 'Invalid installed account'}
  $journals=@(Get-ChildItem -LiteralPath $policy.state_directory -Filter 'incarnation-*.json' -File | Select-Object -First 1001 | Sort-Object Name)
  if($journals.Count -lt 1 -or $journals.Count -gt 1000){throw 'Bounded installed incarnation required'}
  $journalPath=$journals[-1].FullName;$journalRaw=Read-Bytes $journalPath
  $journal=[Text.Encoding]::UTF8.GetString($journalRaw)|ConvertFrom-Json
  if($journals[-1].Name -cnotmatch '^incarnation-[0-9]{20}-([0-9a-f-]{36})\.json$'){throw 'Incarnation filename differs'}
  $issuerPath=Join-Path (Join-Path (Split-Path -Parent (Split-Path -Parent $plan.commit_file)) $Matches[1]) 'AutomaticIssuer.json'
  $issuer=Read-Json $issuerPath
  if($journal.policy_sha256 -cne $policyHash -or $issuer.plan_sha256 -cne $journal.publication.plan_sha256){throw 'Installed publication differs'}
  if(Test-Path -LiteralPath (Join-Path $policy.state_directory 'deployment-request.json')){throw 'An existing deployment request requires same-release reconciliation'}
  $native=@($journal.bindings.authority,$journal.bindings.bot,$issuer.issuer) | ForEach-Object {@{PID=$_.pid;ExpectedCreatedFiletime=$_.created_filetime}}
  $sessions=Sessions
  if($sessions.Count -ne 1 -or $sessions[0].ManifestHash.ToLowerInvariant() -cne $journal.publication.manifests.authority){throw 'Installed SQL session differs'}
  $retained=Retained-Preparations
  $resources=Rows ("SELECT TOP (129) r.ResourceKey,r.ActiveJobID,r.ActivePreparationID,r.ActiveOutputOperationID,r.OwnerID,r.Fence,r.BlockedReason,r.Version FROM dbo.ExportResource r JOIN dbo.ExportPreparation p ON p.PreparationID=r.ActivePreparationID WHERE p.AccountKey='"+$account+"' AND p.State IN ('captured','materialized','uncertain') ORDER BY r.ResourceKey;")
  $bindings=@{
   root=$root;host=$env:COMPUTERNAME;sid=$c.sid;account=$account;before=$before;target=$target
   git_path=$c.git_path;git_sha256=$c.git_sha256;venv=@{path=$venvPath;sha256=$venvHash}
   old_policy=@{Path=$policyPath;SHA256=$policyHash;StateDirectory=$policy.state_directory}
   old_plan=@{Path=$policy.seed_plan.path;SHA256=$policy.seed_plan.sha256;Python=$plan.python;PythonSHA256=$plan.python_sha256}
   old_gate=@{Path=$gatePath;SHA256=(Hash $gateBytes)}
   old_journal=@{Path=$journalPath;SHA256=(Hash $journalRaw);Record=$journal}
   old_native=@($native);old_session=$sessions[0];expected_preparation=@($retained);expected_resources=@($resources)
  }
  $work=Join-Path $updates ([guid]::NewGuid().ToString())
  $observation=Join-Path $updates ('observation-'+[guid]::NewGuid().ToString()+'.json')
  Write-Record $observation @{seed=$seed;gate=$gate;bindings=$bindings}
  $preparer=Join-Path $PSScriptRoot 'prepare_k98_update.py'
  $toolManifestPath=Join-Path $PSScriptRoot 'update-tool.json'
  if(Test-Path -LiteralPath $toolManifestPath) {
   # The one-time reviewed installer places these immutable tool files outside
   # the live checkout. They can prepare the first release containing the tool.
   $toolManifest=Read-Json $toolManifestPath
   if($toolManifest.version -ne 1){throw 'Unsupported installed update tool'}
   $required=@('Update-K98.ps1','K98-SourceUpdate.ps1','Deploy-K98Release.ps1','prepare_k98_update.py','verify_k98_update_pair.py','EmptyGitConfig.txt')
   if(@($toolManifest.files.PSObject.Properties).Count -ne $required.Count){throw 'Exact update tool inventory required'}
   foreach($name in $required){$null=Read-Bytes (Join-Path $PSScriptRoot $name) $toolManifest.files.$name 2MB}
  } else {
   $null=Read-Bytes $preparer $policy.source_hashes.'scripts/prepare_k98_update.py' 2MB
  }
  & $venvPath -I -B $preparer --observation $observation --output $work | Out-Host
  if($LASTEXITCODE -ne 0){throw 'Preparation failed. Bot remains running; no restart requested.'}
  # The generator creates administrative custody atomically, before any bytes.
  Assert-Protected $work
  $prepared=Read-Json (Join-Path $work 'prepared.json')
  Write-Record $active @{directory=$work;release_id=$prepared.release_id}
  Write-Host ('Prepared automatically in '+[math]::Round($clock.Elapsed.TotalSeconds,1)+' seconds. Target '+$target)
 }
 if($PrepareOnly){Write-Host ('Package ready: '+$prepared.manifest+'. Run this same script without -PrepareOnly to deploy.');return}
 $manifest=Read-Json $prepared.manifest $prepared.manifest_sha256
 $runner=Join-Path (Split-Path -Parent $prepared.manifest) 'Deploy-K98Release.ps1'
 $null=Read-Bytes $runner $prepared.runner_sha256 2MB
 $oldPolicy=Read-Json $manifest.policy.path $manifest.policy.sha256
 $stage=Join-Path $oldPolicy.state_directory ('release-'+$manifest.release_id)
 $launch=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$runner,'-ManifestPath',$prepared.manifest,'-ExpectedSHA256',$prepared.manifest_sha256)
 if(Test-Path -LiteralPath $stage){$launch+='-Resume'}
 & $powershell @launch | Out-Host
 if($LASTEXITCODE -ne 0){throw 'Update stopped. Evidence is retained; no automatic second start or source replay.'}
 Write-Record (Join-Path $work 'verified.json') @{release_id=$prepared.release_id;target=$prepared.target;verified_utc=[datetime]::UtcNow.ToString('o')}
 Remove-Item -LiteralPath $active
 Write-Host ('Update verified: '+$prepared.target+'. Check your ordinary Discord command. No package cleanup is needed.')
} finally {
 $null=Stop-Transcript
 $lock.Dispose()
 Write-Host ('Update transcript: '+$transcript)
}
