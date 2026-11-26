#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ExpectedSHA256,[Management.Automation.Runspaces.PSSession]$Session,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$base='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
# Reuse the accepted bounded file and job-diagnostic functions, never its entrypoint.
$controls=Join-Path $root 'ReadinessControls.ps1'
$controlItem=Get-Item -LiteralPath $controls -Force
if($controlItem.PSIsContainer -or $controlItem.Length -gt 1MB -or ($controlItem.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Bounded ordinary controls required'}
$controlBytes=[IO.File]::ReadAllBytes($controls)
$h=[Security.Cryptography.SHA256]::Create()
try{$controlHash=([BitConverter]::ToString($h.ComputeHash($controlBytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
if($controlBytes.Length -gt 1MB -or $controlHash -cne '9eb91ae7daaa28cb2f1bd7f112eb95835237b2f5bf1af6d0de16a33bdf56e39f'){throw 'Accepted read controls differ'}
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput([Text.Encoding]::UTF8.GetString($controlBytes),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Read control parse failure'}
foreach($name in @('Read-P02Sealed')){
 $found=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true))
 if($found.Count -ne 1){throw 'Exact accepted read function required'}
 . ([scriptblock]::Create($found[0].Extent.Text))
}
Read-P02Sealed $PlanPath $ExpectedSHA256 1MB
$p=Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8|ConvertFrom-Json
if($root -cnotmatch ('^'+[regex]::Escape($base)+'\\startup-binding-[0-9]{17}$') -or $p.schema -cne 'p02-startup-binding-read/1' -or $p.production_eligible -ne $false -or $p.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $p.guest_directory -cnotmatch '^C:\\Program Files\\K98-P02-StartupBinding-[0-9]{17}$' -or (Split-Path -Leaf $root) -cne ('startup-binding-'+$p.guest_directory.Substring($p.guest_directory.Length-17))){throw 'Exact startup-read plan required'}
$names=@('Read-P02StartupBinding.ps1','K98-SourceUpdate.ps1','ReadinessControls.ps1','host-inventory.json')
if((@($p.files.PSObject.Properties.Name|Sort-Object)-join '|') -cne (@($names|Sort-Object)-join '|')){throw 'Exact startup-read members required'}
if($p.accepted_receipt_sha256 -cne '0d3dd5d7b31370463169e53f576dab9e22002d650f02109dba5e5e90a7384b22' -or $p.task_xml_sha256 -cne '9cba57aae5b3b9301dac00c542ada9fde59697257c493dc51ab213f097a99298' -or $p.updater_manifest_sha256 -cne '8dbd0dde860d0e33fd7331698a748ea2ce7f56b5eb20cdf0cdea6566d7ae74b9' -or $p.task_principal_sid -cne 'S-1-5-21-1434108111-1107891387-3488655415-1001'){throw 'Accepted startup baseline differs'}
Read-P02Sealed $PSCommandPath $p.host_sha256
foreach($file in $p.files.PSObject.Properties){Read-P02Sealed (Join-Path $root $file.Name) $file.Value}
Read-P02Sealed (Join-Path $base 'release-readiness-20261124082204150\receipt.json') $p.accepted_receipt_sha256 1MB
$cursor=$root
while($cursor.Length -ge $base.Length){
 $item=Get-Item -LiteralPath $cursor -Force
 if(-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Ordinary evidence ancestry required'}
 if($cursor -ceq $base){break};$cursor=Split-Path -Parent $cursor
}
if($p.files.'K98-SourceUpdate.ps1' -cne '1f25e8fb22f079295c80e25cfdbbdab33d20a1488066839b5bfa11e0d28cbd73'){throw 'Reviewed custody helper differs'}
$supportBytes=[IO.File]::ReadAllBytes((Join-Path $root 'K98-SourceUpdate.ps1'))
$h=[Security.Cryptography.SHA256]::Create()
try{$supportHash=([BitConverter]::ToString($h.ComputeHash($supportBytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
if($supportBytes.Length -gt 2MB -or $supportHash -cne $p.files.'K98-SourceUpdate.ps1'){throw 'Read custody source bytes differ'}
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput([Text.Encoding]::UTF8.GetString($supportBytes),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Custody source parse failure'}
$helperText=''
foreach($name in @('Assert-Protected','Hash','Read-Bytes','New-Acl','New-Directory','Write-New','Write-Record')){
 $found=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true))
 if($found.Count -ne 1){throw 'Exact existing custody function required'}
 $helperText+=$found[0].Extent.Text+[Environment]::NewLine
}
if($ValidateOnly){[pscustomobject]@{validated=$true;vm_contacted=$false;packet=$root};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Exact host Windows PowerShell 5.1 required'}
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not ([Security.Principal.WindowsPrincipal]::new($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Use retained elevated Hyper-V session'}
if($null -eq $Session -or $Session.State -cne 'Opened' -or $Session.Availability -cne 'Available' -or $Session.VMId.ToString() -cne $p.vm_id){throw 'Exact available retained VM session required'}
$vm=Get-VM -Id ([guid]$p.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or $vm.State -ne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$inventory=Get-Content -LiteralPath (Join-Path $root 'host-inventory.json') -Raw -Encoding UTF8|ConvertFrom-Json
$disks=@(Get-VMHardDiskDrive -VM $vm)
if($disks.Count -ne $inventory.disks.Count){throw 'VM attachment inventory changed'}
foreach($expected in $inventory.disks){
 $disk=@($disks|Where-Object {$_.Path -ieq $expected.path})
 if($disk.Count -ne 1 -or [string]$disk[0].ControllerType -cne $expected.controller_type -or $disk[0].ControllerNumber -ne $expected.controller_number -or $disk[0].ControllerLocation -ne $expected.controller_location){throw 'VM attachment changed'}
 $vhd=Get-VHD -Path $disk[0].Path
 if([string]$vhd.DiskIdentifier -ine $expected.disk_id -or $vhd.Size -ne $expected.virtual_bytes -or [string]$vhd.ParentPath -ine [string]$expected.parent_path){throw 'VM disk metadata changed'}
}
$checkpoints=@(Get-VMSnapshot -VM $vm)
if($checkpoints.Count -ne 1 -or $checkpoints[0].Id.ToString() -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Retained checkpoint differs'}
$existing=Get-Variable -Name P02StartupBindingJob -Scope Global -ErrorAction SilentlyContinue
if($null -ne $existing -and $null -ne $existing.Value){throw 'Prior startup-binding job retained; do not replace or rerun'}
$stream=[IO.FileStream]::new((Join-Path $root 'host-intent.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes((@{plan_sha256=$ExpectedSHA256;started_utc=[datetime]::UtcNow.ToString('o')}|ConvertTo-Json));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
$ownedJob=$null;$stage='fresh protected guest evidence'
try {
 Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$helperText -ScriptBlock {
  param($directory,$helpers)
  . ([scriptblock]::Create($helpers))
  $id=[Security.Principal.WindowsIdentity]::GetCurrent()
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or $id.Name -cne 'MINI_AMD\K98LabAdmin' -or $id.Owner.Value -cne 'S-1-5-32-544' -or $directory -cnotmatch '^C:\\Program Files\\K98-P02-StartupBinding-[0-9]{17}$'){throw 'Exact fresh lab evidence context required'}
  $script:c=@{sid=$id.User.Value}
  New-Directory $directory
 }
 foreach($name in @('plan.json')+$names){Copy-Item -LiteralPath (Join-Path $root $name) -Destination (Join-Path $p.guest_directory $name) -ToSession $Session -ErrorAction Stop}
 $stage='owned startup metadata read'
 $global:P02StartupBindingJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$ExpectedSHA256,$helperText -AsJob -ScriptBlock {
  param($directory,$hash,$helpers)
  . ([scriptblock]::Create($helpers))
  Assert-Protected $directory
  $p=[Text.Encoding]::UTF8.GetString((Read-Bytes (Join-Path $directory 'plan.json') $hash 1MB))|ConvertFrom-Json
  $entry=Read-Bytes (Join-Path $directory 'Read-P02StartupBinding.ps1') $p.files.'Read-P02StartupBinding.ps1' 1MB
  & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($entry))) -Action Run -PacketRoot $directory -PlanSHA256 $hash
 }
 $ownedJob=$global:P02StartupBindingJob
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($ownedJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 180){
  $null=Wait-Job -Job $ownedJob -Timeout 10
  Write-Host ('Startup metadata read: '+[int]$watch.Elapsed.TotalSeconds+' seconds; no startup or SQL action.')
 }
 if($ownedJob.State -cne 'Completed'){throw 'Startup read unresolved; retain P02StartupBindingJob and P02LabSession; do not rerun'}
 $result=@(Receive-Job -Job $ownedJob -Keep)
 if($ownedJob.ChildJobs.Count -ne 1 -or $ownedJob.ChildJobs[0].Error.Count -ne 0 -or $result.Count -ne 1){throw 'Incomplete startup read; retain original job/session'}
 $stage='collect original receipt'
 Copy-Item -LiteralPath (Join-Path $p.guest_directory 'receipt.json') -Destination (Join-Path $root 'receipt.json') -FromSession $Session -ErrorAction Stop
 Read-P02Sealed (Join-Path $root 'receipt.json') $result[0].receipt_sha256 1MB
 $result[0]|Select-Object outcome,receipt_sha256,sql_connections_opened,startup_actions,physical_custody_retained
 Write-Host ('Evidence: '+(Join-Path $root 'receipt.json'))
 if($result[0].outcome -cne 'passed' -or $result[0].sql_connections_opened -ne 0 -or $result[0].startup_actions -ne 0 -or $result[0].physical_custody_retained){throw 'Startup metadata read stopped; no successor or replay'}
}catch{
 $first=$_
 $failure=[ordered]@{outcome='failed';stage=$stage;plan_sha256=$ExpectedSHA256;first_failure_type=$first.Exception.GetType().FullName;hresult=$first.Exception.HResult;session_retained=$true;rerun_allowed=$false;job_id=$null;job_state=$null}
 if($null -ne $ownedJob){$failure.job_id=$ownedJob.Id;$failure.job_state=[string]$ownedJob.State}
 $stream=[IO.FileStream]::new((Join-Path $root 'host-failure.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($failure|ConvertTo-Json));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 # Guest arbitrary policy/task text is never reflected in host diagnostics.
 throw ('Startup binding stopped at '+$stage+'. Retain the job/session and protected guest evidence; do not rerun.')
}
