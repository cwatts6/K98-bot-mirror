# Shared, explicit failed-readiness retirement. Definitions only; callers load
# this from the reviewed tool payload, never from an application-selected path.
# Requires the existing protected-read/write and source-custody primitives.
function Assert-RetirementProfile($Profile) {
 $fields='active_sha256,approved_target,bindings_sha256,drain_sha256,failure_evidence_sha256,host,journal_name,journal_sha256,kind,manifest_sha256,prepared_sha256,receipts,release_id,request_sha256,sid,start_sha256,version,work'
 if((($Profile.PSObject.Properties.Name|Sort-Object) -join ',') -cne $fields -or
    $Profile.version -isnot [int] -or $Profile.version -ne 1 -or $Profile.kind -cne 'failed_readiness_retirement' -or
    $Profile.host -cne 'MINI_AMD' -or $Profile.sid -cnotmatch '^S-1-5-21-(?:[0-9]+-){3}[0-9]+$' -or
    $Profile.release_id -cnotmatch '^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$' -or
    $Profile.work -cnotmatch '^C:\\ProgramData\\K98\\S11\\updates\\[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$' -or
    $Profile.approved_target -cnotmatch '^[a-f0-9]{40}$' -or
    $Profile.journal_name -cnotmatch '^incarnation-[0-9]{20}-[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\.json$') {throw 'Exact reviewed retirement profile required'}
 foreach($name in @('active','bindings','drain','failure_evidence','journal','manifest','prepared','request','start')) {
  if($Profile.($name+'_sha256') -cnotmatch '^[a-f0-9]{64}$'){throw 'Retirement profile digest differs'}
 }
 $expected=@('seed.complete.json','seed.intent.json','source.complete.json','source.intent.json','start.complete.json','start.intent.json')
 if((@($Profile.receipts.PSObject.Properties.Name|Sort-Object) -join ',') -cne ($expected -join ',')){throw 'Only completed source/seed/start retirement is supported'}
 foreach($entry in $Profile.receipts.PSObject.Properties){if($entry.Value -cnotmatch '^[a-f0-9]{64}$'){throw 'Retirement receipt digest differs'}}
}

function Read-RetirementBytes([string]$Path,[string]$Expected='', [long]$Limit=2MB) {
 Assert-Protected $Path
 $item=Get-Item -LiteralPath $Path -Force
 if($item.PSIsContainer -or $item.Length -gt $Limit -or ([long]$item.Attributes -band (-bnot 0x20a6)) -ne 0){throw 'Retirement file type/attributes/bound differs'}
 if(@(Get-Item -LiteralPath $Path -Stream * | Where-Object {$_.Stream -cne ':$DATA'}).Count){throw 'Retirement alternate stream refused'}
 $held=Open-SourceCustodyHandle $Path $false
 try {return ,(Read-Bytes $Path $Expected $Limit)} finally {$held.Dispose()}
}
function Read-RetirementJson([string]$Path,[string]$Expected='') {
 [Text.Encoding]::UTF8.GetString((Read-RetirementBytes $Path $Expected))|ConvertFrom-Json
}
function Assert-RetirementDirectory([string]$Path) {
 Assert-Protected $Path
 $item=Get-Item -LiteralPath $Path -Force
 if(-not $item.PSIsContainer -or ([long]$item.Attributes -band (-bnot 0x2010)) -ne 0){throw 'Retirement directory type/attributes differ'}
 $held=Open-SourceCustodyHandle $Path $true
 $held.Dispose()
}
function Open-RetirementExecution($Context) {
 $null=Read-RetirementBytes $Context.lock '' 4096
 return [IO.File]::Open($Context.lock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
}
function Write-RetirementBytes([string]$Path,[byte[]]$Bytes) {
 Assert-RetirementDirectory (Split-Path -Parent $Path)
 if(-not(Test-Path -LiteralPath $Path)) {
  $pending=Join-Path (Split-Path -Parent $Path) ('pending-'+[guid]::NewGuid().ToString('N'))
  Write-New $pending $Bytes
  $null=Read-RetirementBytes $pending (Hash $Bytes)
  [IO.File]::Move($pending,$Path)
 }
 $null=Read-RetirementBytes $Path (Hash $Bytes)
}
function Retirement-Bytes($Value) {return ,([Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 12 -Compress)))}
function Get-RetirementPaths($Profile) {
 $root='C:\ProgramData\K98\S11\updates\retirements'
 [pscustomobject]@{root=$root;directory=(Join-Path $root $Profile.release_id);active='C:\ProgramData\K98\S11\updates\active.json';work=$Profile.work}
}
function Get-RetirementContext($Profile,[string]$ProfileHash=$script:retirementProfileHash) {
 Assert-RetirementProfile $Profile
 $paths=Get-RetirementPaths $Profile
 $prepared=Read-RetirementJson (Join-Path $Profile.work 'prepared.json') $Profile.prepared_sha256
 $package=Join-Path $Profile.work 'package'
 if($prepared.release_id -cne $Profile.release_id -or $prepared.manifest -cne (Join-Path $package 'release.json') -or
    $prepared.manifest_sha256 -cne $Profile.manifest_sha256 -or $prepared.bindings_sha256 -cne $Profile.bindings_sha256){throw 'Retirement preparation identity differs'}
 $manifest=Read-RetirementJson $prepared.manifest $Profile.manifest_sha256
 $bindings=Read-RetirementJson (Join-Path $package 'ReleaseBindings.json') $Profile.bindings_sha256
 if($manifest.version -ne 4 -or $manifest.release_id -cne $Profile.release_id -or
    $manifest.host -cne $Profile.host -or $manifest.application_sid -cne $Profile.sid -or
    $bindings.release_id -cne $Profile.release_id -or $bindings.host -cne $Profile.host -or $bindings.sid -cne $Profile.sid -or
    $bindings.root -cne 'C:\discord_file_downloader' -or $bindings.target -cne $prepared.target -or
    $prepared.target -cnotmatch '^[a-f0-9]{40}$' -or $prepared.target -ceq $Profile.approved_target){throw 'Retirement installed release identity differs'}
 if(@($manifest.steps).Count -ne 4){throw 'Only source-only releases can be retired'}
 for($i=0;$i -lt 4;$i++) {
  $name=@('source','seed','start','readiness')[$i]
  if($manifest.steps[$i].id -cne $name -or $manifest.steps[$i].kind -cne $name){throw 'Only source-only releases can be retired'}
 }
 foreach($path in @($bindings.old_policy.StateDirectory,$bindings.new_state_directory)) {
  if($path -cnotmatch '^C:\\ProgramData\\K98\\S11\\automatic-startup\\[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$'){throw 'Retirement state path differs'}
 }
 if($bindings.new_state_directory -ceq $bindings.old_policy.StateDirectory -or
    $bindings.new_seed_directory -cnotmatch '^C:\\ProgramData\\K98\\S11\\runtime\\[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$' -or
    $manifest.policy.path -cnotmatch '^C:\\ProgramData\\K98\\S11\\runtime\\[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\\AutomaticStartupPolicy\.json$' -or
    $manifest.policy.path -cne $bindings.old_policy.Path -or $manifest.policy.sha256 -cne $bindings.old_policy.SHA256){throw 'Retirement policy binding differs'}
 $oldPolicy=Read-RetirementJson $manifest.policy.path $manifest.policy.sha256
 if($oldPolicy.state_directory -cne $bindings.old_policy.StateDirectory){throw 'Retirement predecessor policy differs'}
 $stage=Join-Path $bindings.old_policy.StateDirectory ('release-'+$Profile.release_id)
 if($ProfileHash -cnotmatch '^[a-f0-9]{64}$'){throw 'Retirement profile hash required'}
 $marker=[ordered]@{version=1;kind='failed_readiness_retirement';release_id=$Profile.release_id;profile_sha256=$ProfileHash}
 [pscustomobject]@{profile=$Profile;paths=$paths;prepared=$prepared;manifest=$manifest;bindings=$bindings;stage=$stage;
  barrier=(Join-Path $stage '.amendment-selected.json');marker=(Retirement-Bytes $marker);
  lock=(Join-Path $bindings.old_policy.StateDirectory ('deployment-'+$Profile.release_id+'.lock'))}
}
function Assert-RetirementEvidence($Context,[switch]$Archived) {
 $p=$Context.profile;$b=$Context.bindings;$stage=$Context.stage
 $null=Read-RetirementBytes (Join-Path $stage '.release.json') $p.manifest_sha256 65536
 $null=Read-RetirementBytes (Join-Path $stage 'ReleaseBindings.json') $p.bindings_sha256
 $null=Read-RetirementBytes (Join-Path $stage 'start-requested.json') $p.start_sha256
 $request=Read-RetirementJson (Join-Path $b.old_policy.StateDirectory 'deployment-request.json') $p.request_sha256
 $drain=Read-RetirementJson (Join-Path $b.old_policy.StateDirectory ('deployment-drained-'+$p.release_id+'.json')) $p.drain_sha256
 if($request.release_id -cne $p.release_id -or $drain.release_id -cne $p.release_id -or
    $drain.stage -cne 'deployment_drained' -or $drain.request_sha256 -cne $p.request_sha256){throw 'Retirement request/drain identity differs'}
 $receiptRoot=Join-Path $stage '.receipts'
 Assert-RetirementDirectory $receiptRoot
 $items=@(Get-ChildItem -LiteralPath $receiptRoot -Force|Select-Object -First 7)
 if($items.Count -ne 6 -or @($items|Where-Object {$_.PSIsContainer}).Count){throw 'Retirement release has advanced or lacks completed stages'}
 foreach($entry in $p.receipts.PSObject.Properties) {
  $record=Read-RetirementJson (Join-Path $receiptRoot $entry.Name) $entry.Value
  $parts=$entry.Name.Split('.');$expected=if($parts[1] -ceq 'complete'){'verified'}else{'starting'}
  if($record.release_id -cne $p.release_id -or $record.step -cne $parts[0] -or $record.stage -cne $expected){throw 'Retirement stage receipt differs'}
 }
 foreach($path in @((Join-Path $p.work 'verified.json'),(Join-Path $stage 'readiness-status.json'),(Join-Path $b.new_state_directory 'deployment-request.json'))) {
  if(Test-Path -LiteralPath $path){throw 'Retirement readiness or new intent has appeared'}
 }
 if(Test-Path -LiteralPath $Context.barrier){$null=Read-RetirementBytes $Context.barrier (Hash $Context.marker)}
 $activePath=if($Archived){Join-Path $Context.paths.directory 'active.json'}else{$Context.paths.active}
 $active=Read-RetirementJson $activePath $p.active_sha256
 if($active.release_id -cne $p.release_id -or $active.directory -cne $p.work){throw 'Retirement active selection differs'}
 if($Archived -and (Test-Path -LiteralPath $Context.paths.active)){throw 'Another active selection exists during retirement'}
}
function Get-RetirementRuntime($Context) {
 $b=$Context.bindings;$p=$Context.profile
 $gate=Join-Path $b.new_seed_directory 'Start-ReviewedAutomaticStartup.ps1'
 $task=Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
 $taskSid=Get-RetirementTaskSid $task
 $expected='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$gate+'"'
 if($taskSid -cne $p.sid -or @($task.Actions).Count -ne 1 -or
    $task.Actions[0].Execute -cne 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -or
    $task.Actions[0].Arguments -cne $expected){throw 'Retirement installed task differs'}
 foreach($member in $b.seed_members) {
  if($member.name -cnotmatch '^[A-Za-z][A-Za-z0-9_.-]{0,127}$'){throw 'Retirement seed member differs'}
  $null=Read-RetirementBytes (Join-Path $b.new_seed_directory $member.name) $member.sha256
 }
 $policy=Read-RetirementJson (Join-Path $b.new_seed_directory 'AutomaticStartupPolicy.json') $b.new_policy_sha256
 if($policy.state_directory -cne $b.new_state_directory){throw 'Retirement installed state differs'}
 Assert-RetirementDirectory $b.new_state_directory
 $items=@(Get-ChildItem -LiteralPath $b.new_state_directory -Force|Select-Object -First 2)
 if($items.Count -ne 1 -or $items[0].PSIsContainer -or $items[0].Name -cne $p.journal_name){throw 'Retirement successor history changed'}
 $journal=Read-RetirementJson $items[0].FullName $p.journal_sha256
 if($journal.policy_sha256 -cne $b.new_policy_sha256 -or $journal.sequence -ne ($b.old_journal.Record.sequence+1)){throw 'Retirement incarnation differs'}
 $nonce=$p.journal_name.Substring(33,36)
 $live=Join-Path 'C:\ProgramData\K98\S11\runtime' $nonce
 $publication=Read-RetirementJson (Join-Path $live 'commit.json')
 if($publication.version -ne 1 -or $publication.plan_sha256 -cne $journal.publication.plan_sha256 -or
    (@($publication.manifests.PSObject.Properties.Name|Sort-Object) -join ',') -cne 'authority,bot' -or
    (@($journal.bindings.PSObject.Properties.Name|Sort-Object) -join ',') -cne 'authority,bot'){throw 'Retirement publication shape differs'}
 $plan=Read-RetirementJson (Join-Path $live 'ManualProcessPairPlan-CANDIDATE.json') $publication.plan_sha256
 foreach($role in @('authority','bot')) {
  $path=Join-Path $live ($role+'-manifest.json')
  if($plan.manifests.$role -cne $path -or $publication.manifests.$role -cne $journal.publication.manifests.$role){throw 'Retirement publication binding differs'}
  $null=Read-RetirementBytes $path $publication.manifests.$role
 }
 $issuer=Read-RetirementJson (Join-Path $live 'AutomaticIssuer.json')
 if($issuer.version -ne 1 -or $issuer.plan_sha256 -cne $publication.plan_sha256){throw 'Retirement issuer publication differs'}
 $processes=@($journal.bindings.authority,$journal.bindings.bot,$issuer.issuer)
 if(@($processes.pid|Select-Object -Unique).Count -ne 3){throw 'Three distinct retirement process identities required'}
 [pscustomobject]@{policy=$policy;journal=$journal;processes=$processes}
}
function Get-RetirementTaskSid($Task) {
 [Security.Principal.NTAccount]::new($Task.Principal.UserId).Translate([Security.Principal.SecurityIdentifier]).Value
}
function Assert-RetirementSource($Context,$Policy) {
 # Read Git's fixed main ref directly: no Git worker, hooks, SQL or application import.
 $root=$Context.bindings.root
 $head=[Text.Encoding]::UTF8.GetString((Read-RetirementBytes (Join-Path $root '.git\HEAD') '' 4096)).Trim()
 if($head -cne 'ref: refs/heads/main'){throw 'Retirement requires installed private main'}
 $ref=Join-Path $root '.git\refs\heads\main'
 if(Test-Path -LiteralPath $ref) {$commit=[Text.Encoding]::UTF8.GetString((Read-RetirementBytes $ref '' 4096)).Trim()}
 else {
  $packed=[Text.Encoding]::UTF8.GetString((Read-RetirementBytes (Join-Path $root '.git\packed-refs') '' 1MB))
  $matches=@([regex]::Matches($packed,'(?m)^([0-9a-f]{40}) refs/heads/main\r?$'))
  if($matches.Count -ne 1){throw 'Retirement main reference differs'}
  $commit=$matches[0].Groups[1].Value
 }
 if($commit -cne $Context.prepared.target){throw 'Retirement installed source changed'}
 $entries=@($Policy.source_hashes.PSObject.Properties)
 if($entries.Count -lt 1 -or $entries.Count -gt 2048){throw 'Retirement source inventory bound differs'}
 $watch=[Diagnostics.Stopwatch]::StartNew();$bytes=0L
 foreach($entry in $entries) {
  if($watch.Elapsed.TotalSeconds -gt 180 -or $bytes -gt 128MB){throw 'Retirement source inspection bound exceeded'}
  if($entry.Name -cnotmatch '^[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*\.py$' -or
     @($entry.Name.Split('/')|Where-Object {$_.StartsWith('.')}).Count){throw 'Retirement source path differs'}
  $raw=Read-RetirementBytes (Join-Path $root $entry.Name.Replace('/','\')) $entry.Value
  $bytes+=$raw.Length
  if($bytes -gt 128MB){throw 'Retirement source inspection bound exceeded'}
 }
}
function Open-RetirementProcesses($Bindings) {
 $held=[Collections.Generic.List[Diagnostics.Process]]::new()
 try {
  if(@($Bindings).Count -ne 3 -or @($Bindings.pid|Select-Object -Unique).Count -ne 3){throw 'Three retirement native identities required'}
  foreach($binding in $Bindings) {
   $process=Get-Process -Id ([int]$binding.pid) -ErrorAction Stop
   $held.Add($process)
   $null=$process.Handle
   if($process.HasExited -or $process.StartTime.ToFileTimeUtc() -ne [long]$binding.created_filetime -or
      $process.Path -cne $binding.executable){throw 'Retirement native identity differs'}
   $null=Read-RetirementBytes $binding.executable $binding.sha256 16MB
  }
  return ,$held
 } catch {foreach($process in $held){$process.Dispose()};throw}
}
function Assert-RetirementProcesses($Processes) {
 if($Processes.Count -ne 3){throw 'Retirement native handles missing'}
 foreach($process in $Processes){if($process.HasExited){throw 'Retirement process exited; retain state and review'}}
}
function Start-FailedReadinessRetirement($Context,[byte[]]$ProfileBytes,[string]$NewToolHash) {
 Assert-RetirementEvidence $Context -Archived:(Test-Path -LiteralPath (Join-Path $Context.paths.directory 'active.json'))
 # The legacy runner already refuses this selection marker before preflight.
 # Its explicit kind records retirement, never a fictitious successful amendment.
 Write-RetirementBytes $Context.barrier $Context.marker
 foreach($path in @($Context.paths.root,$Context.paths.directory)) {
  if(-not(Test-Path -LiteralPath $path)){New-Directory $path}
  Assert-RetirementDirectory $path
 }
 Write-RetirementBytes (Join-Path $Context.paths.directory 'profile.json') $ProfileBytes
 $intent=Retirement-Bytes ([ordered]@{version=1;kind='failed_readiness_retirement';release_id=$Context.profile.release_id;
  profile_sha256=(Hash $ProfileBytes);installed_target=$Context.prepared.target;approved_target=$Context.profile.approved_target;tool_sha256=$NewToolHash})
 Write-RetirementBytes (Join-Path $Context.paths.directory 'intent.json') $intent
}
function Complete-FailedReadinessRetirement($Context,[string]$NewToolHash) {
 $archive=Join-Path $Context.paths.directory 'active.json'
 if(-not(Test-Path -LiteralPath $archive)) {
  Assert-RetirementEvidence $Context
  [IO.File]::Move($Context.paths.active,$archive)
 }
 Assert-RetirementEvidence $Context -Archived
 $intent=Read-RetirementJson (Join-Path $Context.paths.directory 'intent.json')
 if($intent.profile_sha256 -cne $script:retirementProfileHash -or $intent.tool_sha256 -cne $NewToolHash){throw 'Retirement intent differs'}
 $complete=Retirement-Bytes ([ordered]@{version=1;kind='retired_without_verified_readiness';release_id=$Context.profile.release_id;
  profile_sha256=$script:retirementProfileHash;intent_sha256=(Hash (Read-RetirementBytes (Join-Path $Context.paths.directory 'intent.json')));
  active_sha256=$Context.profile.active_sha256;tool_sha256=$NewToolHash})
 Write-RetirementBytes (Join-Path $Context.paths.directory 'complete.json') $complete
}
function Read-CompletedRetirement([string]$Directory) {
 Assert-RetirementDirectory $Directory
 $intent=Read-RetirementJson (Join-Path $Directory 'intent.json')
 $completePath=Join-Path $Directory 'complete.json'
 if(-not(Test-Path -LiteralPath $completePath)){throw 'Failed-readiness retirement is incomplete; use only its reviewed upgrade helper'}
 $complete=Read-RetirementJson $completePath
 $profile=Read-RetirementJson (Join-Path $Directory 'profile.json') $intent.profile_sha256
 Assert-RetirementProfile $profile
 if((($intent.PSObject.Properties.Name|Sort-Object) -join ',') -cne 'approved_target,installed_target,kind,profile_sha256,release_id,tool_sha256,version' -or
    (($complete.PSObject.Properties.Name|Sort-Object) -join ',') -cne 'active_sha256,intent_sha256,kind,profile_sha256,release_id,tool_sha256,version' -or
    $intent.profile_sha256 -cnotmatch '^[a-f0-9]{64}$' -or $intent.tool_sha256 -cnotmatch '^[a-f0-9]{64}$' -or
    (Split-Path -Leaf $Directory) -cne $profile.release_id -or $intent.version -isnot [int] -or $intent.version -ne 1 -or
    $intent.kind -cne 'failed_readiness_retirement' -or $intent.release_id -cne $profile.release_id -or
    $complete.version -isnot [int] -or $complete.version -ne 1 -or $complete.kind -cne 'retired_without_verified_readiness' -or
    $complete.release_id -cne $profile.release_id -or $complete.profile_sha256 -cne $intent.profile_sha256 -or
    $complete.intent_sha256 -cne (Hash (Read-RetirementBytes (Join-Path $Directory 'intent.json'))) -or
    $complete.active_sha256 -cne $profile.active_sha256 -or $complete.tool_sha256 -cne $intent.tool_sha256 -or
    $intent.approved_target -cne $profile.approved_target -or $intent.installed_target -cnotmatch '^[a-f0-9]{40}$') {throw 'Retirement closeout identity differs'}
 $null=Read-RetirementBytes (Join-Path $Directory 'active.json') $profile.active_sha256
 $context=Get-RetirementContext $profile $intent.profile_sha256
 if($intent.installed_target -cne $context.prepared.target){throw 'Retirement installed target differs'}
 $null=Read-RetirementBytes $context.barrier (Hash $context.marker)
 [pscustomobject]@{profile=$profile;intent=$intent;complete=$complete}
}
function Assert-RetirementUpdates([string]$Before='', [string]$Target='') {
 $root='C:\ProgramData\K98\S11\updates\retirements'
 if(-not(Test-Path -LiteralPath $root)){return}
 Assert-RetirementDirectory $root
 $items=@(Get-ChildItem -LiteralPath $root -Force|Select-Object -First 33)
 if($items.Count -gt 32){throw 'Retirement history bound exceeded'}
 foreach($item in $items) {
  if(-not $item.PSIsContainer -or $item.Name -cnotmatch '^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$'){throw 'Retirement history inventory differs'}
  $record=Read-CompletedRetirement $item.FullName
  if($Before -and $Before -ceq $record.intent.installed_target -and $Target -cne $record.profile.approved_target){throw 'Failed-readiness successor target differs from the reviewed correction'}
 }
}
function Assert-ReleaseNotRetired([string]$ReleaseId) {
 if($ReleaseId -cnotmatch '^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$'){throw 'Canonical release identity required'}
 if(Test-Path -LiteralPath (Join-Path 'C:\ProgramData\K98\S11\updates\retirements' $ReleaseId)) {
  throw 'Release retired without verified readiness; do not resume it. Use the reviewed fresh correction release.'
 }
}
