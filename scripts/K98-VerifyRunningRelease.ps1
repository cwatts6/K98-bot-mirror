# Definitions loaded only from a separately sealed verification packet.
# Reuse the reviewed custody/source/native primitives; never call retirement,
# source installation, task execution, the release runner or recovery adapters.
function Assert-RunningReleaseEvidence($Profile) {
 $active=Read-RetirementJson 'C:\ProgramData\K98\S11\updates\active.json' $Profile.active_sha256
 if($active.release_id -cne $Profile.release_id -or $active.directory -cne $Profile.work){throw 'Active release differs'}
 $bindingsPath=Join-Path $Profile.stage 'ReleaseBindings.json'
 $script:c=Read-RetirementJson $bindingsPath $Profile.bindings_sha256
 $null=Read-RetirementBytes (Join-Path $Profile.work 'package\ReleaseBindings.json') $Profile.bindings_sha256
 $manifest=Read-RetirementJson (Join-Path $Profile.work 'package\release.json') $Profile.manifest_sha256
 $null=Read-RetirementBytes (Join-Path $Profile.stage '.release.json') $Profile.manifest_sha256 65536
 if($c.release_id -cne $Profile.release_id -or $c.target -cne $Profile.target -or $c.sid -cne $Profile.sid -or
    $c.host -cne $Profile.host -or $c.root -cne 'C:\discord_file_downloader' -or
    $Profile.stage -cne (Join-Path $c.old_policy.StateDirectory ('release-'+$Profile.release_id)) -or
    $manifest.version -ne 4 -or $manifest.release_id -cne $Profile.release_id -or
    (@($manifest.steps.id) -join ',') -cne 'source,seed,start,readiness' -or
    (@($manifest.steps.kind) -join ',') -cne 'source,seed,start,readiness'){throw 'Pinned source-only release differs'}
 $receiptRoot=Join-Path $Profile.stage '.receipts'
 $names=@(Get-ChildItem -LiteralPath $receiptRoot -Force | Select-Object -First 7 | Sort-Object Name)
 if($names.Count -ne 5 -or @($names|Where-Object {$_.PSIsContainer}).Count -or
    (($names.Name) -join ',') -cne 'seed.complete.json,seed.intent.json,source.complete.json,source.intent.json,start.intent.json'){throw 'Original stage boundary differs'}
 foreach($entry in $Profile.receipts.PSObject.Properties) {
  $record=Read-RetirementJson (Join-Path $receiptRoot $entry.Name) $entry.Value
  $parts=$entry.Name.Split('.');$expected=if($parts[1] -ceq 'complete'){'verified'}else{'starting'}
  if($record.release_id -cne $Profile.release_id -or $record.step -cne $parts[0] -or $record.stage -cne $expected){throw 'Historical receipt differs'}
 }
 foreach($path in @((Join-Path $Profile.stage '.amendment-selected.json'),(Join-Path $Profile.stage 'readiness-status.json'),(Join-Path $c.new_state_directory 'deployment-request.json'))) {
  if(Test-Path -LiteralPath $path){throw 'Release selection or readiness advanced; preserve evidence'}
 }
 $null=Read-RetirementBytes (Join-Path $Profile.stage 'start-requested.json') $Profile.start_sha256
 $retired=Read-RetirementJson $Profile.original_retirement_path $Profile.original_retirement_sha256
 if($retired.kind -cne 'retired_without_verified_readiness'){throw 'Original retirement differs'}
 # The original protected drain binds the terminated predecessor and release.
 $requestPath=Join-Path $c.old_policy.StateDirectory 'deployment-request.json'
 $request=Read-RetirementJson $requestPath
 $drain=Read-RetirementJson (Join-Path $c.old_policy.StateDirectory ('deployment-drained-'+$c.release_id+'.json'))
 if($request.release_id -cne $c.release_id -or $request.policy_sha256 -cne $c.old_policy.SHA256 -or
    $request.sequence -ne $c.old_journal.Record.sequence -or -not(Same $request.publication $c.old_journal.Record.publication) -or
    $drain.stage -cne 'deployment_drained' -or $drain.release_id -cne $c.release_id -or
    $drain.request_sha256 -cne (Hash (Read-RetirementBytes $requestPath)) -or
    -not(Same $drain.previous $c.old_journal.Record)){throw 'Original physical drain evidence differs'}
 $script:newGate=Join-Path $c.new_seed_directory 'Start-ReviewedAutomaticStartup.ps1'
 if(-not(Seed-Complete)){throw 'Successor seed/task differs'}
 $context=[pscustomobject]@{profile=$Profile;bindings=$c;prepared=[pscustomobject]@{target=$Profile.target}}
 $runtime=Get-RetirementRuntime $context
 Assert-RetirementSource $context $runtime.policy
 return $runtime
}

function Read-RunningStartupText($Profile,[string]$ProfileHash,[string]$Directory,$Start) {
 if($Profile.version -ne 2 -or $Start.release_id -cne $Profile.release_id -or
    [long]$Start.log_offset -ne [long]$Profile.startup_log_anchor.offset){throw 'Original startup log anchor differs'}
 $reader=Join-Path $Directory 'Read-StartupEvidence.py'
 $null=Read-RetirementBytes $reader $Profile.members.'Read-StartupEvidence.py' 1MB
 $profilePath=Join-Path $Directory 'profile.json'
 $null=Read-RetirementBytes $profilePath $ProfileHash 65536
 $null=Read-RetirementBytes $c.venv.path $c.venv.sha256 4MB
 $output=@(& $c.venv.path -I -B $reader --profile $profilePath --sha256 $ProfileHash)
 $code=$LASTEXITCODE
 $record=$null
 if($output.Count -eq 1){try{$record=$output[0]|ConvertFrom-Json}catch{$record=$null}}
 $evidence=$null;$failure='invalid_response'
 if($null -ne $record -and $null -ne $record.PSObject.Properties['evidence']){$evidence=$record.evidence}
 if($null -ne $record -and $null -ne $record.PSObject.Properties['failure_type']){$failure=$record.failure_type}
 $text=$null
 try {
  if($code -ne 0 -or $null -eq $record -or $record.stage -cne 'STARTUP_HISTORY_CAPTURED'){throw 'Capture refused'}
  $bytes=[Convert]::FromBase64String($record.raw_base64)
  if($bytes.Length -gt 8MB -or $bytes.Length -ne $evidence.interval_bytes -or (Hash $bytes) -cne $evidence.interval_sha256){throw 'Capture result differs'}
  $text=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
  $failure=$null
 } catch {if($failure -ceq 'invalid_response'){$failure=$_.Exception.GetType().Name}}
 $observation=[ordered]@{version=1;release_id=$Profile.release_id;profile_sha256=$ProfileHash;observed_utc=[datetime]::UtcNow.ToString('o');exit_code=$code;evidence=$evidence;failure_type=$failure}
 $path=Join-Path $Directory ('startup-observation-'+[guid]::NewGuid().ToString()+'.json')
 Write-RetirementBytes $path (Retirement-Bytes $observation)
 if($null -ne $failure){
  throw 'Startup history capture refused; preserve its observation and obtain review. No retry or acceptance.'
 }
 $script:runningStartupObservationHash=Hash (Read-RetirementBytes $path)
 return $text
}

function Invoke-RunningReleaseVerification($Profile,[string]$ProfileHash,[string]$Directory) {
 $updates='C:\ProgramData\K98\S11\updates'
 $lockPath=Join-Path $updates 'operator.lock'
 $null=Read-RetirementBytes $lockPath '' 4096
 $operatorLock=[IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
 $releaseLock=$null;$processes=$null
 try {
  $execution=Join-Path (Split-Path -Parent $Profile.stage) ('deployment-'+$Profile.release_id+'.lock')
  $null=Read-RetirementBytes $execution '' 4096
  $releaseLock=[IO.File]::Open($execution,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
  $runtime=Assert-RunningReleaseEvidence $Profile
  $processes=Open-RetirementProcesses $runtime.processes
  $complete=Join-Path $Profile.work 'verified.json'
  if(Test-Path -LiteralPath $complete) {
   $prior=Read-RetirementJson $complete
   if($prior.release_id -cne $Profile.release_id -or $prior.target -cne $Profile.target -or
      $prior.closeout_kind -cne 'running_release_verification_v1' -or $prior.profile_sha256 -cne $ProfileHash){throw 'Different acceptance exists; preserve evidence'}
   Assert-RetirementProcesses $processes
   Write-Host 'HISTORICAL VERIFICATION RECORDED. No SQL repeated. Active selection and original receipts retained. Obtain review before finalizing the pointer.'
   return
  }
  Write-Host 'The exact original receipts and running process identities match. No restart or business action will run.'
  Write-Host 'Confirm the current /ops dl_bot_status response is online. This does not certify import/export or provider delivery.'
  $answer=Read-Host 'Type CONFIRM ONLINE to perform one bounded verification and record acceptance, or press Enter to leave it pending'
  if($answer -cne 'CONFIRM ONLINE'){Write-Host 'No SQL observation or acceptance performed.';return}
  $null=Assert-RunningReleaseEvidence $Profile
  Assert-RetirementProcesses $processes
  $start=Read-RetirementJson (Join-Path $Profile.stage 'start-requested.json') $Profile.start_sha256
  $startupText=Read-RunningStartupText $Profile $ProfileHash $Directory $start
  $health=Import-ExportStatus $startupText
  if($startupText -notmatch '\[BOOT\] full_startup_sequence completed successfully' -or
     $startupText -notmatch 'Logged in as' -or $health.reason -ceq 'runtime_admission_unavailable') {
   throw 'Startup/readiness evidence remains unconfirmed; no verification or acceptance'
  }
  foreach($entry in $Profile.members.PSObject.Properties) {
   $null=Read-RetirementBytes (Join-Path $Directory $entry.Name) $entry.Value 4MB
  }
  $profilePath=Join-Path $Directory 'profile.json'
  $null=Read-RetirementBytes $profilePath $ProfileHash 65536
  $null=Read-RetirementBytes $c.venv.path $c.venv.sha256 4MB
  $output=@(& $c.venv.path -I -B (Join-Path $Directory 'Verify-RunningRelease.py') --profile $profilePath --sha256 $ProfileHash)
  $code=$LASTEXITCODE
  $attempt=[ordered]@{version=1;release_id=$Profile.release_id;profile_sha256=$ProfileHash;observed_utc=[datetime]::UtcNow.ToString('o');exit_code=$code;output=@($output)}
  $attemptPath=Join-Path $Directory ('attempt-'+[guid]::NewGuid().ToString()+'.json')
  Write-RetirementBytes $attemptPath (Retirement-Bytes $attempt)
  $output | Out-Host
  if($code -eq 12){Write-Host 'VERIFICATION PENDING: acknowledged schema contention. No retry, start or acceptance. Preserve this attempt and obtain review.';return}
  if($code -ne 0 -or $output.Count -eq 0){throw 'Verification refused; original failures and this attempt retained'}
  $proof=$output[-1]|ConvertFrom-Json
  if($proof.stage -cne 'RUNNING_RELEASE_VERIFIED' -or $proof.release_id -cne $Profile.release_id -or
     $proof.target -cne $Profile.target -or $proof.sequence -ne $runtime.journal.sequence -or
     $proof.provider_delivery_verified -ne $false -or $proof.retry -ne $false){throw 'Verification proof differs'}
  $null=Assert-RunningReleaseEvidence $Profile
  Assert-RetirementProcesses $processes
  if((Import-ExportStatus (Read-RunningStartupText $Profile $ProfileHash $Directory $start)).reason -ceq 'runtime_admission_unavailable'){throw 'Runtime admission failure appeared; no acceptance'}
  $acceptance=[ordered]@{version=1;release_id=$Profile.release_id;target=$Profile.target;verified_utc=[datetime]::UtcNow.ToString('o');
   closeout_kind='running_release_verification_v1';profile_sha256=$ProfileHash;actor_sid=$Profile.sid;
   failure_evidence_sha256=$Profile.failure_evidence_sha256;attempt_sha256=(Hash (Read-RetirementBytes $attemptPath));
   final_startup_observation_sha256=$script:runningStartupObservationHash;
   current_successor=$proof;readiness=@{discord_status='operator_confirmed_online';import_export=@{status='degraded';provider_delivery_verified=$false};original_start='unconfirmed_preserved';original_readiness='unstarted_preserved'}}
  Assert-RetirementProcesses $processes
  $null=Assert-RunningReleaseEvidence $Profile
  # Publish only after every fallible verification check has passed. This is
  # point-in-time acceptance, not a promise that the processes cannot exit later.
  Write-RetirementBytes $complete (Retirement-Bytes $acceptance)
  Write-Host 'VERIFICATION RECORDED. Original start/readiness receipts and both failure histories are preserved. Runtime unchanged; no restart or replay. Run only -Status next and obtain review before clearing the active pointer.'
 } finally {
  if($null -ne $processes){foreach($process in $processes){$process.Dispose()}}
  if($null -ne $releaseLock){$releaseLock.Dispose()}
  $operatorLock.Dispose()
 }
}
