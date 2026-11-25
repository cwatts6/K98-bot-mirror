#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedSHA256,[Management.Automation.Runspaces.PSSession]$Session,[Management.Automation.Job]$PreviousJob,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$base='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
function Read-P02Sealed([string]$Path,[string]$Hash,[long]$Bound=2MB){
 $item=Get-Item -LiteralPath $Path -Force
 if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt $Bound){throw 'Ordinary bounded packet file required'}
 if((Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Hash){throw 'Sealed packet bytes differ'}
}
function Assert-P02PriorReadJob($Job) {
 $entry='C:\Program Files\K98-P02-Readiness-20261123214834251\release_readiness_read.ps1'
 if($null -eq $Job -or $Job.Id -ne 644 -or $Job.State -ne 'Failed' -or $Job.ChildJobs.Count -ne 1 -or $Job.ChildJobs[0].Id -ne 645 -or $Job.ChildJobs[0].State -ne 'Failed'){throw 'Exact retained failed read job required'}
 $reason=[string]$Job.ChildJobs[0].JobStateInfo.Reason
 if(-not $reason.Contains($entry) -or -not $reason.Contains('running scripts is disabled on this system')){throw 'Prior job is not the recorded script-load refusal'}
}
function Get-P02ReadJobDiagnostics($Job) {
 return @($Job.ChildJobs|Select-Object -First 4|ForEach-Object {
  $reason=[string]$_.JobStateInfo.Reason;if($reason.Length -gt 8192){$reason=$reason.Substring(0,8192)}
  [pscustomobject]@{id=$_.Id;state=[string]$_.State;reason=$reason;errors=@($_.Error|Select-Object -First 8|ForEach-Object {$message=$_.Exception.Message;if($message.Length -gt 8192){$message=$message.Substring(0,8192)};$message})}
 })
}
Read-P02Sealed $PlanPath $ExpectedSHA256
$p=Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8|ConvertFrom-Json
if($root -cnotmatch ('^'+[regex]::Escape($base)+'\\release-readiness-[0-9]{17}$') -or $p.schema -cne 'p02-release-readiness-read/2' -or $p.production_eligible -ne $false -or $p.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $p.guest_directory -cnotmatch '^C:\\Program Files\\K98-P02-Readiness-[0-9]{17}$' -or (Split-Path -Leaf $root) -cne ('release-readiness-'+$p.guest_directory.Substring($p.guest_directory.Length-17))){throw 'Exact read-only VM plan required'}
$expectedNames=@('release_readiness_read.ps1','legacy-kvk-census.json','return.before.sql','host-inventory.json','K98-SourceUpdate.ps1')
if((@($p.files.PSObject.Properties.Name|Sort-Object) -join '|') -cne (@($expectedNames|Sort-Object) -join '|')){throw 'Exact read group members required'}
Read-P02Sealed $PSCommandPath $p.host_sha256
foreach($item in $p.files.PSObject.Properties){Read-P02Sealed (Join-Path $root $item.Name) $item.Value}
$priorRoot=Join-Path $base 'release-readiness-20261123214834251'
if($p.previous.directory -cne $priorRoot -or $p.previous.plan_sha256 -cne '1cf0d9a55c36c74b781af9f59db2ab0c140e31b9eabc6392c4459f54a45ff462'){throw 'Exact failed predecessor packet required'}
Read-P02Sealed (Join-Path $priorRoot 'plan.json') $p.previous.plan_sha256
Read-P02Sealed (Join-Path $priorRoot 'host-intent.json') $p.previous.intent_sha256
Read-P02Sealed (Join-Path $priorRoot 'host-failure.json') $p.previous.failure_sha256
$cursor=$root
while($cursor.Length -ge $base.Length){
 $item=Get-Item -LiteralPath $cursor -Force
 if(-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Ordinary evidence ancestry required'}
 if($cursor -ceq $base){break};$cursor=Split-Path -Parent $cursor
}
$supportTokens=$null;$supportErrors=$null
$supportAst=[Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'K98-SourceUpdate.ps1'),[ref]$supportTokens,[ref]$supportErrors)
$functions=@($supportAst.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-Protected'},$true))
if($supportErrors.Count -or $functions.Count -ne 1){throw 'Exact existing custody primitive required'}
$custodyCode=$functions[0].Extent.Text
if($ValidateOnly){[pscustomobject]@{validated=$true;vm_contacted=$false;packet=$root};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop'){throw 'Exact host Windows PowerShell 5.1 required'}
$who=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($who)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Use the retained elevated Hyper-V PowerShell session'}
if($null -eq $Session -or $Session.State -cne 'Opened' -or $Session.Availability -cne 'Available' -or $Session.VMId.ToString() -cne $p.vm_id){throw 'Retain the exact opened VM session'}
$vm=Get-VM -Id ([guid]$p.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or $vm.State -ne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$inventory=Get-Content -LiteralPath (Join-Path $root 'host-inventory.json') -Raw -Encoding UTF8|ConvertFrom-Json
$disks=@(Get-VMHardDiskDrive -VM $vm)
if($disks.Count -ne $inventory.disks.Count){throw 'VM disk attachment inventory changed'}
foreach($item in $inventory.disks){
 $disk=@($disks|Where-Object {$_.Path -ieq $item.path})
 if($disk.Count -ne 1 -or [string]$disk[0].ControllerType -cne $item.controller_type -or $disk[0].ControllerNumber -ne $item.controller_number -or $disk[0].ControllerLocation -ne $item.controller_location){throw 'Retained disk attachment changed'}
 # Hyper-V metadata only. Never read, copy or hash virtual disk contents.
 $vhd=Get-VHD -Path $disk[0].Path
 if([string]$vhd.DiskIdentifier -ine $item.disk_id -or $vhd.Size -ne $item.virtual_bytes -or [string]$vhd.ParentPath -ine [string]$item.parent_path){throw 'Retained disk identity changed'}
}
$checkpoints=@(Get-VMSnapshot -VM $vm)
if($checkpoints.Count -ne 1 -or $checkpoints[0].Id.ToString() -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Retained checkpoint differs'}
Assert-P02PriorReadJob $PreviousJob
$global:P02ReadinessPriorJob=$PreviousJob
$intent=Join-Path $root 'host-intent.json'
$stream=[IO.FileStream]::new($intent,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$raw=[Text.UTF8Encoding]::new($false).GetBytes((@{plan_sha256=$ExpectedSHA256;started_utc=[datetime]::UtcNow.ToString('o');vm_id=$p.vm_id}|ConvertTo-Json));$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
$ownedJob=$null;$hostStage='verify original read never entered'
try {
$prior=Invoke-Command -Session $Session -ArgumentList 'C:\Program Files\K98-P02-Readiness-20261123214834251',$p.previous.plan_sha256,$custodyCode -ScriptBlock {
 param($directory,$digest,$custody)
 . ([scriptblock]::Create($custody))
 if($env:COMPUTERNAME -cne 'MINI_AMD' -or $directory -cne 'C:\Program Files\K98-P02-Readiness-20261123214834251'){throw 'Exact original guest packet required'}
 Assert-Protected $directory
 $plan=Join-Path $directory 'plan.json';Assert-Protected $plan
 if((Get-FileHash -LiteralPath $plan -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Original guest plan changed'}
 $original=Get-Content -LiteralPath $plan -Raw -Encoding UTF8|ConvertFrom-Json
 foreach($item in $original.files.PSObject.Properties){
  if($item.Name -cnotmatch '^[A-Za-z0-9_.-]+$'){throw 'Original member name differs'}
  $path=Join-Path $directory $item.Name;Assert-Protected $path
  if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.Value){throw 'Original guest member changed'}
 }
 foreach($name in @('guest-intent.json','receipt.json')){if(Test-Path -LiteralPath (Join-Path $directory $name)){throw 'Prior read execution marker exists; inspect original owner'}}
 foreach($name in @('P02ReadinessConnection','P02ReadinessCommand','P02ReadinessReader')){
  $owner=Get-Variable -Name $name -Scope Global -ErrorAction SilentlyContinue
  if($null -ne $owner -and $null -ne $owner.Value){throw 'Prior physical read owner is retained'}
 }
 [pscustomobject]@{entry_not_started=$true;plan_sha256=$digest}
}
if($prior.entry_not_started -ne $true -or $prior.plan_sha256 -cne $p.previous.plan_sha256){throw 'Original read non-entry was not established'}
$proofPath=Join-Path $root 'predecessor-nonentry.json'
$stream=[IO.FileStream]::new($proofPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$raw=[Text.UTF8Encoding]::new($false).GetBytes((@{entry_not_started=$true;plan_sha256=$prior.plan_sha256;prior_job_id=$PreviousJob.Id;child_job_id=$PreviousJob.ChildJobs[0].Id;checked_utc=[datetime]::UtcNow.ToString('o')}|ConvertTo-Json));$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
$hostStage='create protected guest evidence'
Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$custodyCode -ScriptBlock {
 param($destination,$custody)
 . ([scriptblock]::Create($custody))
 if($env:COMPUTERNAME -cne 'MINI_AMD' -or $destination -cnotmatch '^C:\\Program Files\\K98-P02-Readiness-[0-9]{17}$' -or (Test-Path -LiteralPath $destination)){throw 'Exact fresh guest evidence directory required'}
 $id=[Security.Principal.WindowsIdentity]::GetCurrent()
 if($id.Name -cne 'MINI_AMD\K98LabAdmin' -or $id.Owner.Value -cne 'S-1-5-32-544'){throw 'Administrative lab owner required'}
 Assert-Protected (Split-Path -Parent $destination)
 $parent=Get-Item -LiteralPath (Split-Path -Parent $destination) -Force
 if(-not $parent.PSIsContainer -or ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Ordinary retained evidence parent required'}
 $acl=[Security.AccessControl.DirectorySecurity]::new()
 $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'));$acl.SetAccessRuleProtection($true,$false)
 foreach($sid in @('S-1-5-18','S-1-5-32-544')){$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),[Security.AccessControl.FileSystemRights]::FullControl,([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit),[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))}
 $null=[IO.Directory]::CreateDirectory($destination,$acl)
 Assert-Protected $destination
}
$hostStage='copy sealed evidence'
foreach($name in @('plan.json')+$expectedNames){Copy-Item -LiteralPath (Join-Path $root $name) -Destination (Join-Path $p.guest_directory $name) -ToSession $Session -ErrorAction Stop}
$hostStage='owned guest read'
$global:P02ReadinessJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$ExpectedSHA256,$custodyCode -AsJob -ScriptBlock {
 param($directory,$hash,$custody)
 . ([scriptblock]::Create($custody))
 Assert-Protected $directory
 $plan=Join-Path $directory 'plan.json'
 Assert-Protected $plan
 if((Get-FileHash -LiteralPath $plan -Algorithm SHA256).Hash.ToLowerInvariant() -cne $hash){throw 'Copied plan differs'}
 $p=Get-Content -LiteralPath $plan -Raw -Encoding UTF8|ConvertFrom-Json
 $entry=Join-Path $directory 'release_readiness_read.ps1'
 Assert-Protected $entry
 if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.files.'release_readiness_read.ps1'){throw 'Copied read runner differs'}
 & ([scriptblock]::Create([IO.File]::ReadAllText($entry,[Text.Encoding]::UTF8))) -Action Run -PlanSHA256 $hash -PacketRoot $directory
}
$ownedJob=$global:P02ReadinessJob
$watch=[Diagnostics.Stopwatch]::StartNew()
while($global:P02ReadinessJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 420){
 $null=Wait-Job -Job $global:P02ReadinessJob -Timeout 10
 Write-Host ('Read-only VM checks: '+[int]$watch.Elapsed.TotalSeconds+' seconds; existing fixtures retained.')
}
if($global:P02ReadinessJob.State -cne 'Completed'){throw 'Original guest read is unresolved. Retain P02ReadinessJob and P02LabSession; do not rerun'}
$result=@(Receive-Job -Job $global:P02ReadinessJob -Keep)
if($global:P02ReadinessJob.ChildJobs.Count -ne 1 -or $global:P02ReadinessJob.ChildJobs[0].Error.Count -ne 0 -or $result.Count -ne 1){throw 'Guest result incomplete; retain original job and session'}
$hostStage='collect original guest receipt'
Copy-Item -LiteralPath (Join-Path $p.guest_directory 'receipt.json') -Destination (Join-Path $root 'receipt.json') -FromSession $Session -ErrorAction Stop
Read-P02Sealed (Join-Path $root 'receipt.json') $result[0].receipt_sha256 4MB
$result[0]|Select-Object outcome,receipt_sha256,connection_closed,physical_custody_retained
Write-Host ('Evidence: '+(Join-Path $root 'receipt.json'))
if($result[0].outcome -cne 'passed' -or $result[0].physical_custody_retained -or -not $result[0].connection_closed){throw 'Read group stopped; preserve first failure and owner. No successor or replay.'}

}catch{
 $first=$_
 $failure=[ordered]@{outcome='failed';stage=$hostStage;plan_sha256=$ExpectedSHA256;first_failure=@{type=$first.Exception.GetType().FullName;message=$first.Exception.Message};job_id=$null;job_state=$null;session_retained=$true;rerun_allowed=$false}
 if($null -ne $ownedJob){$failure.job_id=$ownedJob.Id;$failure.job_state=[string]$ownedJob.State;$failure.job_diagnostics=Get-P02ReadJobDiagnostics $ownedJob}
 try {
  $stream=[IO.FileStream]::new((Join-Path $root 'host-failure.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
  try{$raw=[Text.UTF8Encoding]::new($false).GetBytes(($failure|ConvertTo-Json -Depth 8));$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 }catch{Write-Warning 'Host failure receipt could not be saved; retain this console and original job/session.'}
 if($null -ne $ownedJob){foreach($item in $failure.job_diagnostics){if($item.reason){Write-Warning $item.reason};foreach($message in $item.errors){Write-Warning $message}}}
 throw $first
}
