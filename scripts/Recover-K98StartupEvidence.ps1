# Template appended to the reviewed installer's trusted Windows bootstrap.
# __PROFILE__ and __PAYLOAD__ are generated constants, never operator expressions.
$profileBytes=[Convert]::FromBase64String('__PROFILE__')
$profile=[Text.Encoding]::UTF8.GetString($profileBytes)|ConvertFrom-Json
$requestedAction=$Action
$payload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__PAYLOAD__'))|ConvertFrom-Json
$library='C:\ProgramData\K98\S11\updater\K98-SourceUpdate.ps1'
Assert-Custody $library
if((Hash ([IO.File]::ReadAllBytes($library))) -cne $profile.library_sha256){throw 'Installed source adapter differs'}
. $library -Action Library
$script:c=Read-Json $profile.bindings $profile.bindings_sha256
$original=$c
if($c.sid -cne $sid -or $c.host -cne 'MINI_AMD' -or $c.root -cne 'C:\discord_file_downloader' -or $c.release_id -cne $profile.release_id -or $c.target -cne $profile.failed_target){throw 'Exact failed deployment identity differs'}
if($identity.Owner.Value -cne 'S-1-5-32-544'){throw 'Administrative default object owner required'}
$updates='C:\ProgramData\K98\S11\updates'
$destination=Join-Path $updates ('startup-correction-'+$profile.recovery_id)
$selection=Join-Path $destination 'selected-plan.json'
$selectedMarker=Join-Path $profile.stage '.amendment-selected.json'
$drainPath=Join-Path $original.old_policy.StateDirectory ('deployment-drained-'+$original.release_id+'.json')
$failedGate=Join-Path $original.new_seed_directory 'Start-ReviewedAutomaticStartup.ps1'
$activePath=Join-Path $updates 'active.json'
$mutex=$null;$mutexOwned=$false;$operatorLock=$null;$releaseLock=$null

function Install-CorrectionFile([string]$Path,[byte[]]$Bytes) {
 if(-not(Test-Path -LiteralPath $Path)){
  $pending=Join-Path (Split-Path -Parent $Path) ('pending-'+[guid]::NewGuid().ToString('N'))
  Write-New $pending $Bytes
  [IO.File]::Move($pending,$Path)
 }
 $null=Read-Bytes $Path (Hash $Bytes) 16MB
}

function Assert-OriginalRecords {
 $null=Read-Bytes $profile.bindings $profile.bindings_sha256
 $null=Read-Bytes (Join-Path $profile.stage '.release.json') $profile.manifest_sha256 65536
 $receipts=Join-Path $profile.stage '.receipts'
 $items=@(Get-ChildItem -LiteralPath $receipts -Force)
 if($items.Count -ne 5 -or @($items|Where-Object {$_.PSIsContainer}).Count){throw 'Original release progressed; correction refused'}
 foreach($entry in $profile.receipts.PSObject.Properties){$null=Read-Bytes (Join-Path $receipts $entry.Name) $entry.Value}
 $start=Read-Json (Join-Path $profile.stage 'start-requested.json')
 if(-not(Same $start $profile.start_request)){throw 'Original start request differs'}
 Assert-Protected $original.new_state_directory
 if(@(Get-ChildItem -LiteralPath $original.new_state_directory -Force).Count){throw 'Failed startup has an incarnation or other history; preserve it'}
 foreach($member in $original.seed_members){$null=Read-Bytes (Join-Path $original.new_seed_directory $member.name) $member.sha256}
 if(Test-Path -LiteralPath (Join-Path $profile.work 'verified.json')){throw 'Original release has a closeout; do not supersede it'}
 if(Test-Path -LiteralPath $activePath){
  $active=Read-Json $activePath
  if($active.release_id -cne $profile.release_id -or $active.directory -cne $profile.work){throw 'Another update is selected'}
 } elseif(-not(Test-Path -LiteralPath (Join-Path $destination 'complete.json'))){throw 'Original active update pointer missing'}
 if(Test-Path -LiteralPath $selectedMarker){
  $marker=Read-Json $selectedMarker
  if($marker.amendment_id -cne $profile.recovery_id -or $marker.manifest_sha256 -cne (Hash $profileBytes) -or $marker.release_id -cne $profile.release_id){throw 'Another continuation is selected'}
 }
}

function Assert-NoStartupProcesses {
 $processes=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
  $_.Name -match '^python(?:w|[0-9.]*)?\.exe$' -or
  $_.ExecutablePath -like 'C:\discord_file_downloader\*' -or
  $_.CommandLine -match 'Start-ReviewedAutomaticStartup\.ps1|start-bot-after-sql\.ps1|run_export_startup_issuer\.py'
 })
 if($processes.Count){throw 'A Python/bot/startup process remains; no process is stopped by this correction'}
}

function Assert-QuietPredecessor {
 $script:c=$original
 Assert-Drained
 if((Sessions).Count){throw 'An open authority session remains; no closure is performed'}
 Assert-NoStartupProcesses
 Assert-OriginalRecords
}

function Enter-StartupExclusion {
 $authority=Read-Json (Join-Path $original.new_seed_directory 'authority-template.json')
 $machine=[string]$authority.deployment_boundary.host.machine_guid
 if(([guid]$machine).ToString() -cne $machine){throw 'Canonical installed machine identity required'}
 $security=[Security.AccessControl.MutexSecurity]::new()
 $security.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
 $security.SetAccessRuleProtection($true,$false)
 foreach($principal in @('S-1-5-18','S-1-5-32-544')){
  $security.AddAccessRule([Security.AccessControl.MutexAccessRule]::new([Security.Principal.SecurityIdentifier]::new($principal),[Security.AccessControl.MutexRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow))
 }
 $created=$false
 $script:mutex=[Threading.Mutex]::new($false,('Global\K98.S11.Startup.'+$machine),[ref]$created,$security)
 $actual=$mutex.GetAccessControl()
 if($actual.GetOwner([Security.Principal.SecurityIdentifier]).Value -cne 'S-1-5-32-544'){throw 'Startup mutex owner differs'}
 foreach($ace in $actual.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){
  if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and $ace.IdentityReference.Value -notin @('S-1-5-18','S-1-5-32-544')){throw 'Startup mutex access differs'}
 }
 try {$script:mutexOwned=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$script:mutexOwned=$true}
 if(-not $mutexOwned){throw 'Another startup supervisor owns the host'}
 Assert-QuietPredecessor
}

function Read-CorrectionPlan {
 $chosen=Read-Json $selection
 if($chosen.profile_sha256 -cne (Hash $profileBytes) -or $chosen.directory -cnotmatch ('^'+[regex]::Escape($destination)+'\\plan-[a-f0-9-]{36}$')){throw 'Selected correction plan differs'}
 $plan=Read-Json (Join-Path $chosen.directory 'correction-plan.json') $chosen.sha256
 if($plan.version -ne 1 -or $plan.kind -cne 'startup_evidence_correction_v1' -or $plan.recovery_id -cne $profile.recovery_id -or $plan.original_release_id -cne $profile.release_id -or $plan.original_bindings_sha256 -cne $profile.bindings_sha256 -or $plan.profile_sha256 -cne (Hash $profileBytes) -or $plan.target -cne $profile.target){throw 'Correction plan identity differs'}
 if($plan.members.Count -gt 256){throw 'Correction member inventory exceeds bound'}
 foreach($member in $plan.members){
  if($member.name -cnotmatch '^[A-Za-z][A-Za-z0-9_.-]{0,127}$'){throw 'Flat correction member required'}
  $null=Read-Bytes (Join-Path $chosen.directory $member.name) $member.sha256 16MB
 }
 $script:correctionDirectory=$chosen.directory;$script:correctionPlan=$plan
 $script:corrected=Read-Json (Join-Path $chosen.directory 'ReleaseBindings.json') $plan.bindings_sha256
}

function Invoke-CorrectionAdapter([string]$Operation) {
 Read-CorrectionPlan
 & $powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $correctionDirectory 'Release-Step.ps1') -Action $Operation -ExpectedBindingsSHA256 $correctionPlan.bindings_sha256 | Out-Host
 return $LASTEXITCODE
}

function Invoke-CorrectionStage([string]$Name,[string]$Verify,[string]$Apply) {
 $receipts=Join-Path $correctionDirectory '.receipts'
 $intent=Join-Path $receipts ($Name+'.intent.json');$done=Join-Path $receipts ($Name+'.complete.json')
 foreach($pair in @(@($intent,'starting'),@($done,'verified'))){
  if(Test-Path -LiteralPath $pair[0]){
   $record=Read-Json $pair[0]
   if($record.release_id -cne $profile.release_id -or $record.step -cne $Name -or $record.stage -cne $pair[1]){throw 'Correction receipt identity differs'}
  }
 }
 $code=Invoke-CorrectionAdapter $Verify
 if($code -eq 0){if(-not(Test-Path -LiteralPath $done)){Write-Record $done @{release_id=$profile.release_id;step=$Name;stage='verified'}};return}
 $safe=$code -eq 11 -and $Name -cne 'start'
 if($code -ne 10 -and -not $safe){throw ('Correction '+$Name+' outcome unconfirmed; retain all evidence')}
 if((Test-Path -LiteralPath $done) -or ((Test-Path -LiteralPath $intent) -and -not $safe)){throw ('Correction '+$Name+' already attempted; no automatic replay')}
 if(-not(Test-Path -LiteralPath $intent)){Write-Record $intent @{release_id=$profile.release_id;step=$Name;stage='starting'}}
 if($Name -ceq 'start'){
  Assert-QuietPredecessor
  if(-not $mutexOwned){throw 'Exclusive pre-start verification was not held'}
  $mutex.ReleaseMutex();$script:mutexOwned=$false;$mutex.Dispose();$script:mutex=$null
 }
 if((Invoke-CorrectionAdapter $Apply) -ne 0 -or (Invoke-CorrectionAdapter $Verify) -ne 0){throw ('Correction '+$Name+' did not verify; no later step or repeated start')}
 Write-Record $done @{release_id=$profile.release_id;step=$Name;stage='verified'}
}

try {
 Assert-Protected $updates
 foreach($path in @((Join-Path $updates 'operator.lock'),(Join-Path $original.old_policy.StateDirectory ('deployment-'+$profile.release_id+'.lock')))){Assert-Protected $path}
 $operatorLock=[IO.File]::Open((Join-Path $updates 'operator.lock'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
 $releaseLock=[IO.File]::Open((Join-Path $original.old_policy.StateDirectory ('deployment-'+$profile.release_id+'.lock')),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
 Assert-OriginalRecords
 if($requestedAction -ceq 'Inspect'){
  if(Test-Path -LiteralPath $selection){Read-CorrectionPlan;Write-Host 'A correction plan already exists. Use Apply to verify its current stage; it never repeats a start.';return}
  Assert-QuietPredecessor;Assert-Source $original.new_pins $original.target
  $null=Assert-Task $failedGate
  Write-Output ('{"stage":"STARTUP_CORRECTION_REVIEW_READY","production_changed":false,"recovery_id":"'+$profile.recovery_id+'"}');return
 }
 if(-not(Test-Path -LiteralPath $destination)){New-Directory $destination}
 foreach($entry in $payload.PSObject.Properties){
  if($entry.Name -cnotmatch '^[A-Za-z][A-Za-z0-9_.-]{0,127}$'){throw 'Flat tool payload required'}
  $raw=[Convert]::FromBase64String($entry.Value);$path=Join-Path $destination $entry.Name
  Install-CorrectionFile $path $raw
 }
 $profilePath=Join-Path $destination 'profile.json'
 Install-CorrectionFile $profilePath $profileBytes
 if(Test-Path -LiteralPath $selection){Read-CorrectionPlan}
 $hasStart=(Test-Path -LiteralPath $selection) -and (Test-Path -LiteralPath (Join-Path $correctionDirectory '.receipts\start.intent.json'))
 if(-not $hasStart){
  Assert-QuietPredecessor
  $gate=if((Test-Path -LiteralPath $selection) -and (Task).Definition.Actions.Item(1).Arguments.Contains($corrected.new_seed_directory)){Join-Path $corrected.new_seed_directory 'Start-ReviewedAutomaticStartup.ps1'}else{$failedGate}
  $task=Assert-Task $gate
  if($task.GetInstances(0).Count){throw 'Scheduled startup action still running'}
  $task.Enabled=$false;$null=Assert-Task $gate $true
  Enter-StartupExclusion
  if(-not(Test-Path -LiteralPath $selection)){
   Assert-Source $original.new_pins $original.target
   $remote=Git 'remote get-url origin'
   if($remote -notmatch '^https://github\.com/cwatts6/K98-bot(?:\.git)?$'){throw 'Private production origin required'}
   $credential=Get-GitCredentialManager;$helper=$credential.Replace('\','/').Replace(' ','\ ')
   $null=Git ('-c credential.helper= -c credential.helper="'+$helper+'" fetch --no-tags --no-recurse-submodules origin +refs/heads/main:refs/remotes/origin/main')
   if((Git 'rev-parse refs/remotes/origin/main') -cne $profile.target){throw 'Exact reviewed private-main target required'}
   $null=Git ('merge-base --is-ancestor '+$original.target+' '+$profile.target)
   $seed=[ordered]@{}
   foreach($member in $original.seed_members){if($member.name.EndsWith('.json')){$seed[$member.name]=Read-Json (Join-Path $original.new_seed_directory $member.name) $member.sha256}}
   $observed=$original|ConvertTo-Json -Depth 40 -Compress|ConvertFrom-Json
   $observed.before=$original.target;$observed.target=$profile.target
   $observed.old_policy=[pscustomobject]@{Path=(Join-Path $original.new_seed_directory 'AutomaticStartupPolicy.json');SHA256=$original.new_policy_sha256;StateDirectory=$original.new_state_directory}
   $gateBytes=Read-Bytes $failedGate
   $observed.old_gate=[pscustomobject]@{Path=$failedGate;SHA256=(Hash $gateBytes)}
   $observation=Join-Path $destination ('observation-'+[guid]::NewGuid().ToString()+'.json')
   Write-Record $observation @{seed=$seed;gate=[Text.Encoding]::UTF8.GetString($gateBytes);bindings=$observed}
   $candidate=Join-Path $destination ('candidate-'+[guid]::NewGuid().ToString())
   & $original.venv.path -I -B (Join-Path $destination 'prepare_k98_update.py') --observation $observation --observation-sha256 (Hash (Read-Bytes $observation '' 4MB)) --output $candidate | Out-Host
   if($LASTEXITCODE -ne 0){throw 'Correction preparation failed; no source or start performed'}
   $prepared=Join-Path $candidate 'prepared.json'
   $planDirectory=Join-Path $destination ('plan-'+[guid]::NewGuid().ToString())
   & $original.venv.path -I -B (Join-Path $destination 'prepare_k98_startup_correction.py') --profile $profilePath --profile-sha256 (Hash $profileBytes) --prepared $prepared --prepared-sha256 (Hash (Read-Bytes $prepared)) --output $planDirectory | Out-Host
   if($LASTEXITCODE -ne 0){throw 'Correction lineage preparation failed; no source or start performed'}
   $planPath=Join-Path $planDirectory 'correction-plan.json'
   Write-AtomicRecord $selection @{profile_sha256=(Hash $profileBytes);directory=$planDirectory;sha256=(Hash (Read-Bytes $planPath))}
   Read-CorrectionPlan
  }
  if(-not(Test-Path -LiteralPath $selectedMarker)){Write-AtomicRecord $selectedMarker @{amendment_id=$profile.recovery_id;manifest_sha256=(Hash $profileBytes);release_id=$profile.release_id}}
  Assert-OriginalRecords
 }
 Read-CorrectionPlan
 $receipts=Join-Path $correctionDirectory '.receipts'
 if(-not(Test-Path -LiteralPath $receipts)){New-Directory $receipts}
 if(-not(Test-Path -LiteralPath (Join-Path $receipts 'source.intent.json')) -and -not $hasStart){
  # The normal runner establishes safe existing source-file custody during its
  # live preflight. This correction starts after drain, so do the same bounded
  # preparation here, while exclusion is held and before any source intent.
  try {
   $script:c=$corrected
   Assert-Source $c.old_pins $c.before
   Initialize-UpdateCustody;Assert-UpdatePaths
  } finally {$script:c=$original}
 }
 Invoke-CorrectionStage 'source' 'VerifySource' 'ApplySource'
 Invoke-CorrectionStage 'seed' 'VerifySeed' 'ApplySeed'
 Invoke-CorrectionStage 'start' 'VerifyStart' 'ApplyStart'
 Invoke-CorrectionStage 'readiness' 'VerifyReadiness' 'AwaitReadiness'
 Assert-OriginalRecords
 $completion=[pscustomobject]@{version=1;stage='STARTUP_CORRECTION_VERIFIED';recovery_id=$profile.recovery_id;original_release_id=$profile.release_id;original_target=$profile.failed_target;target=$profile.target;bindings_sha256=$correctionPlan.bindings_sha256;original_start_intent='preserved';provider_delivery_verified=$false}
 $completePath=Join-Path $destination 'complete.json'
 if(Test-Path -LiteralPath $completePath){if(-not(Same (Read-Json $completePath) $completion)){throw 'Correction closeout differs'}}else{Write-AtomicRecord $completePath $completion}
 if(Test-Path -LiteralPath $activePath){Remove-Item -LiteralPath $activePath}
 $completion|ConvertTo-Json -Compress
 Write-Host ('Recovery evidence: '+$destination)
} finally {
 if($mutexOwned){$mutex.ReleaseMutex()}
 if($null -ne $mutex){$mutex.Dispose()}
 if($null -ne $releaseLock){$releaseLock.Dispose()}
 if($null -ne $operatorLock){$operatorLock.Dispose()}
}
