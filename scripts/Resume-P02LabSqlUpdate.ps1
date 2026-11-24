#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
if($plan.schema -cne 'p02-lab-sql-update-resume/1' -or $plan.production_eligible -ne $false -or $plan.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $plan.checkpoint_id -cne '125272d0-20b7-4705-908f-d3debc71bce2' -or $plan.guest_directory -cne 'Q:\P02Release\sql-version-20261120173650657'){throw 'Exact pre-dispatch continuation required'}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.entry_sha256){throw 'Sealed continuation entry differs'}
foreach($p in $plan.evidence.PSObject.Properties){if((Get-FileHash -LiteralPath $p.Name -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.Value){throw 'Original stage evidence differs'}}
if($ValidateOnly){[pscustomobject]@{validated=$true;evidence_files=@($plan.evidence.PSObject.Properties).Count;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$plan.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$checkpoints=@(Get-VMSnapshot -VM $vm|Where-Object {$_.Id -eq [guid]$plan.checkpoint_id})
if($checkpoints.Count -ne 1 -or $checkpoints[0].Name -cne 'P02-before-SQL1220-20261120173650657'){throw 'Retained checkpoint identity changed'}
function Assert-PredispatchFailure($Job) {
 if($null -eq $Job -or $Job.Id -ne 848 -or $Job.State -ne 'Failed' -or $Job.ChildJobs.Count -ne 1 -or $Job.ChildJobs[0].State -ne 'Failed' -or $Job.ChildJobs[0].Error.Count){throw 'Exact retained pre-dispatch failed job required'}
 $reason=$Job.ChildJobs[0].JobStateInfo.Reason
 if($null -eq $reason -or $reason.GetType().FullName -cne 'System.Management.Automation.Runspaces.InvalidRunspaceStateException' -or -not $reason.Message.Contains('Cannot invoke the pipeline because the runspace is not in the Opened state.') -or -not $reason.Message.Contains("'Broken'")){throw 'Failure is not the recorded pre-dispatch broken runspace'}
}
function Get-LabSession([guid]$VmId) {
 $opened=@(Get-PSSession|Where-Object {$_.VMId -eq $VmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'})
 if($opened.Count -eq 1){return $opened[0]}
 if($opened.Count -gt 1){throw 'Multiple available lab sessions require explicit reconciliation'}
 $previous=@(Get-PSSession|Where-Object {$_.VMId -eq $VmId -and $_.InstanceId -eq [guid]'fb80997e-0146-404e-8757-aeef45f8f1a7'})
 $credential=$null
 if($previous.Count -eq 1){try{$credential=$previous[0].Runspace.ConnectionInfo.Credential}catch{$credential=$null}}
 if($null -eq $credential -or $credential.UserName -in @('',$null)){$credential=Get-Credential -UserName 'MINI_AMD\K98LabAdmin' -Message 'Reconnect to the existing isolated qualification VM. The password is not saved or printed.'}
 if($null -eq $credential -or $credential.UserName -in @('',$null)){throw 'Lab authentication was cancelled'}
 return (New-PSSession -VMId $VmId -Credential $credential)
}
Assert-PredispatchFailure $global:P02LabSqlUpdateJob
$receiptPath=Join-Path $root 'host-receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Continuation already attempted; retain its result'}
$r=[ordered]@{schema='p02-lab-sql-update-resume-host/1';outcome='running';stage='reconnect exact lab session';started=[datetime]::UtcNow.ToString('o');first_failure=$null;guest=$null;checkpoint_id=$plan.checkpoint_id;preflight_replayed=$false;checkpoint_repeated=$false;production_operations=0}
function Save-Host {[IO.File]::WriteAllText($receiptPath,($r|ConvertTo-Json -Depth 24),[Text.UTF8Encoding]::new($false))}
Save-Host
try{
 $global:P02LabSqlUpdateSession=Get-LabSession ([guid]$plan.vm_id)
 $session=$global:P02LabSqlUpdateSession
 if($session.VMId -ne [guid]$plan.vm_id -or $session.State -ne 'Opened' -or $session.Availability -ne 'Available'){throw 'Reconnected session identity or availability differs'}
 $r.session_instance_id=$session.InstanceId.ToString();Save-Host
 $r.stage='verify update has not started';Save-Host
 $notStarted=Invoke-Command -Session $session -ArgumentList $plan.guest_directory,$plan.original_plan_sha256 -ScriptBlock {
  param($path,$planSha)
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Get-FileHash -LiteralPath (Join-Path $path 'plan.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $planSha){throw 'Exact original guest packet required'}
  if(Test-Path -LiteralPath (Join-Path $path 'guest-receipt.json')){throw 'Guest update already entered; inspect it rather than replay'}
  $processes=@(Get-CimInstance Win32_Process|Where-Object {$_.Name -ieq 'SQLServer2022-KB5132747-x64.exe' -or $_.Name -ieq 'setup.exe'})
  if($processes.Count){throw 'An installer process exists; no dispatch is permitted'}
  return $true
 }
 if($notStarted -ne $true){throw 'Pre-dispatch absence was not established'}
 $r.stage='resume original unfinished SQL update';Save-Host
 $global:P02LabSqlUpdateResumeJob=Invoke-Command -Session $session -ArgumentList $plan.guest_directory,$plan.guest_entry_sha256 -AsJob -ScriptBlock {
  param($path,$digest)
  $entry=Join-Path $path 'Update-P02LabSql.ps1'
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Original sealed guest entry differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path
 }
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($global:P02LabSqlUpdateResumeJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 1000){$null=Wait-Job -Job $global:P02LabSqlUpdateResumeJob -Timeout 10;Write-Host ('Lab SQL update continuation: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original checkpoint retained.')}
 $job=$global:P02LabSqlUpdateResumeJob
 $r.job_state=[string]$job.State
 $r.job_diagnostics=@($job.ChildJobs|ForEach-Object {
  $reason=[string]$_.JobStateInfo.Reason;if($reason.Length -gt 8192){$reason=$reason.Substring(0,8192)}
  [pscustomobject]@{state=[string]$_.State;reason=$reason;errors=@($_.Error|Select-Object -First 8|ForEach-Object {$message=$_.Exception.Message;if($message.Length -gt 8192){$message=$message.Substring(0,8192)};$message})}
 })
 Save-Host
 if($job.State -ne 'Completed'){throw 'Guest job did not complete; retain connection/process/job and inspect recorded diagnostics'}
 $received=@(Receive-Job -Job $job -Keep)
 if($job.ChildJobs.Count -ne 1 -or $job.ChildJobs[0].Error.Count -or $received.Count -ne 1 -or $received[0] -isnot [string]){throw 'Unexpected guest result; retained job requires reconciliation'}
 $r.guest=$received[0]|ConvertFrom-Json
 [IO.File]::WriteAllText((Join-Path $root 'guest-receipt.json'),$received[0],[Text.UTF8Encoding]::new($false))
 try{
  foreach($name in @('installer.stdout.txt','installer.stderr.txt')){
   $present=Invoke-Command -Session $session -ArgumentList $plan.guest_directory,$name -ScriptBlock {param($path,$name) Test-Path -LiteralPath (Join-Path $path $name)}
   if($present){Copy-Item -FromSession $session -LiteralPath ([IO.Path]::Combine($plan.guest_directory,$name)) -Destination (Join-Path $root $name)}
  }
  $summary='C:\Program Files\Microsoft SQL Server\160\Setup Bootstrap\Log\Summary.txt'
  $present=Invoke-Command -Session $session -ArgumentList $summary -ScriptBlock {param($path) Test-Path -LiteralPath $path}
  if($present){Copy-Item -FromSession $session -LiteralPath $summary -Destination (Join-Path $root 'sql-setup-summary.txt')}
 }catch{$r.collection_failure=$_.Exception.Message}
 if($r.guest.outcome -cnotin @('passed','passed_restart_required')){throw 'Original update stage refused; inspect guest first failure and retained evidence'}
 if($r.Contains('collection_failure')){throw 'Update result retained but log collection incomplete'}
 $r.outcome=$r.guest.outcome;$r.stage=$r.guest.stage
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{$r.finished=[datetime]::UtcNow.ToString('o');Save-Host}
[pscustomobject]$r|Select-Object outcome,stage,first_failure|Format-List
Write-Host ('Evidence saved: '+$root)
