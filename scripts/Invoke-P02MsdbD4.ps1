#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$ValidateOnly,[Management.Automation.Runspaces.PSSession]$Session)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
$names=@('Invoke-P02MsdbD4.ps1','Restore-P02MsdbD4.ps1','accepted-read.json','accepted-update.json','prior-guest-receipt.json')
if($plan.schema -cne 'p02-authentic-msdb-d4/3' -or $plan.production_eligible -ne $false -or $plan.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $plan.guest_directory -cnotmatch '^Q:\\P02Release\\msdb-d4-[0-9]{17}$' -or $plan.checkpoint_id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Exact isolated authentic-msdb/D4 plan required'}
if(@($plan.files.PSObject.Properties).Count -ne $names.Count){throw 'Exact sealed packet inventory required'}
foreach($p in $plan.files.PSObject.Properties){if($p.Name -cnotin $names -or (Get-FileHash -LiteralPath (Join-Path $root $p.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.Value){throw 'Sealed restore/D4 member differs'}}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.files.'Invoke-P02MsdbD4.ps1'){throw 'Sealed host entry differs'}
if($plan.prior_directory -cne 'Q:\P02Release\msdb-d4-20261120184110328' -or $plan.files.'prior-guest-receipt.json' -cne 'e0f4366896ca5f3e344c7e39ec084c437f1e5239485539c7b1af751f1666c63b'){throw 'Exact retained successful-restore receipt required'}
if($ValidateOnly){[pscustomobject]@{validated=$true;members=5;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$plan.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$checkpoints=@(Get-VMSnapshot -VM $vm|Where-Object {$_.Id -eq [guid]$plan.checkpoint_id})
if($checkpoints.Count -ne 1 -or $checkpoints[0].Name -cne 'P02-before-SQL1220-20261120173650657'){throw 'Retained checkpoint identity differs'}
if($null -eq $Session){$available=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($available.Count -ne 1){throw 'One available authenticated lab session required'};$Session=$available[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available session required'}
$receiptPath=Join-Path $root 'host-receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Existing restore/D4 attempt retained; do not rerun'}
$r=[ordered]@{schema='p02-authentic-msdb-d4-host/1';outcome='running';stage='copy sealed packet';started=[datetime]::UtcNow.ToString('o');first_failure=$null;guest=$null;checkpoint_id=$plan.checkpoint_id;production_operations=0}
function Save-Host {[IO.File]::WriteAllText($receiptPath,($r|ConvertTo-Json -Depth 28),[Text.UTF8Encoding]::new($false))}
Save-Host
try{
 Invoke-Command -Session $Session -ArgumentList $plan.guest_directory -ScriptBlock {
  param($path)
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Test-Path -LiteralPath $path)){throw 'Fresh exact guest packet required'}
  $held=Get-Variable P02MsdbD4Held -Scope Global -ErrorAction SilentlyContinue
  if($null -eq $held -or $held.Value -isnot [hashtable] -or -not $held.Value.settled){throw 'Settled previous restore custody required'}
  foreach($name in @('connection','command','pending','process')){if(-not $held.Value.ContainsKey($name) -or $null -ne $held.Value[$name]){throw 'Previous restore physical handles remain'}}
  # The guest authenticates the pinned prior receipt and its actual retained owner
  # before SQL. Preparation only creates the new, separately sealed packet folder.
  foreach($parent in @('Q:\','Q:\P02Release')){
   $item=Get-Item -LiteralPath $parent -Force
   if(-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Ordinary retained lab directories required'}
  }
  [void][IO.Directory]::CreateDirectory($path)
 }
 foreach($name in @('plan.json')+$names){Copy-Item -ToSession $Session -LiteralPath (Join-Path $root $name) -Destination ([IO.Path]::Combine($plan.guest_directory,$name))}
 $r.stage='verify restored dependency and apply only unfinished D4';Save-Host
 $global:P02MsdbD4Job=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$plan.files.'Restore-P02MsdbD4.ps1' -AsJob -ScriptBlock {
  param($path,$digest)
  $entry=Join-Path $path 'Restore-P02MsdbD4.ps1'
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Sealed restore/D4 entry differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path
 }
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($global:P02MsdbD4Job.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 1000){$null=Wait-Job -Job $global:P02MsdbD4Job -Timeout 10;Write-Host ('Lab msdb/D4 stages: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original fixtures and checkpoint retained.')}
 $job=$global:P02MsdbD4Job
 $r.job_state=[string]$job.State
 $r.job_diagnostics=@($job.ChildJobs|ForEach-Object {
  $reason=[string]$_.JobStateInfo.Reason;if($reason.Length -gt 8192){$reason=$reason.Substring(0,8192)}
  [pscustomobject]@{state=[string]$_.State;reason=$reason;errors=@($_.Error|Select-Object -First 8|ForEach-Object {$message=$_.Exception.Message;if($message.Length -gt 8192){$message=$message.Substring(0,8192)};$message})}
 })
 Save-Host
 if($job.State -ne 'Completed'){throw 'Native job incomplete; retain job, session and physical handles; no replay'}
 $received=@(Receive-Job -Job $job -Keep)
 if($job.ChildJobs.Count -ne 1 -or $job.ChildJobs[0].Error.Count -or $received.Count -ne 1 -or $received[0] -isnot [string]){throw 'Unexpected native result; original job retained'}
 $r.guest=$received[0]|ConvertFrom-Json
 [IO.File]::WriteAllText((Join-Path $root 'guest-receipt.json'),$received[0],[Text.UTF8Encoding]::new($false))
 try{
  foreach($name in @('d4.stdout.txt','d4.stderr.txt')){
   $present=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$name -ScriptBlock {param($path,$name) Test-Path -LiteralPath (Join-Path $path $name)}
   if($present){Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($plan.guest_directory,$name)) -Destination (Join-Path $root $name)}
  }
 }catch{$r.collection_failure=$_.Exception.Message}
 if($r.guest.outcome -cne 'passed' -or -not $r.guest.restored -or -not $r.guest.d4_committed -or -not $r.guest.execution_settled -or $r.guest.cleanup_failure){throw 'Restore/D4 stages stopped; inspect exact committed stages before continuation'}
 if($r.Contains('collection_failure')){throw 'Native result retained but child-log collection incomplete'}
 $r.outcome='passed';$r.stage=$r.guest.stage
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{$r.finished=[datetime]::UtcNow.ToString('o');Save-Host}
[pscustomobject]$r|Select-Object outcome,stage,first_failure|Format-List
Write-Host ('Evidence saved: '+$root)
