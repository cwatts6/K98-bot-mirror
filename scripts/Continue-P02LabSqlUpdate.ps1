#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
if($plan.schema -cne 'p02-lab-sql-update-correction/1' -or $plan.production_eligible -ne $false -or $plan.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $plan.checkpoint_id -cne '125272d0-20b7-4705-908f-d3debc71bce2' -or $plan.guest_directory -cnotmatch '^Q:\\P02Release\\sql-version-[0-9]{17}$' -or $plan.original_guest_directory -cne 'Q:\P02Release\sql-version-20261120173650657' -or $plan.prior_guest_directory -cne 'Q:\P02Release\sql-version-20261120180225633'){throw 'Exact settled installer-input correction required'}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.entry_sha256){throw 'Sealed continuation entry differs'}
foreach($p in $plan.evidence.PSObject.Properties){if((Get-FileHash -LiteralPath $p.Name -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.Value){throw 'Original stage evidence differs'}}
if((Get-FileHash -LiteralPath (Join-Path $root 'Update-P02LabSql.ps1') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.guest_entry_sha256 -or (Get-FileHash -LiteralPath (Join-Path $root 'update-plan.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.update_plan_sha256){throw 'Corrected guest entry or stage plan differs'}
if((Get-FileHash -LiteralPath $plan.prior_guest_path -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'ec7b52fc21946f38a031642b34724fce776c6e1dd0c49935eab52747d155fef6'){throw 'Exact settled installer-input receipt required'}
$priorText=Get-Content -LiteralPath $plan.prior_guest_path -Raw
if($ValidateOnly){[pscustomobject]@{validated=$true;evidence_files=@($plan.evidence.PSObject.Properties).Count;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$plan.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$checkpoints=@(Get-VMSnapshot -VM $vm|Where-Object {$_.Id -eq [guid]$plan.checkpoint_id})
if($checkpoints.Count -ne 1 -or $checkpoints[0].Name -cne 'P02-before-SQL1220-20261120173650657'){throw 'Retained checkpoint identity changed'}
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
$receiptPath=Join-Path $root 'host-receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Continuation already attempted; retain its result'}
$r=[ordered]@{schema='p02-lab-sql-update-correction-host/1';outcome='running';stage='reconnect exact lab session';started=[datetime]::UtcNow.ToString('o');first_failure=$null;guest=$null;checkpoint_id=$plan.checkpoint_id;preflight_replayed=$false;checkpoint_repeated=$false;production_operations=0}
function Save-Host {[IO.File]::WriteAllText($receiptPath,($r|ConvertTo-Json -Depth 24),[Text.UTF8Encoding]::new($false))}
Save-Host
try{
 $global:P02LabSqlUpdateSession=Get-LabSession ([guid]$plan.vm_id)
 $session=$global:P02LabSqlUpdateSession
 if($session.VMId -ne [guid]$plan.vm_id -or $session.State -ne 'Opened' -or $session.Availability -ne 'Available'){throw 'Reconnected session identity or availability differs'}
 $r.session_instance_id=$session.InstanceId.ToString();Save-Host
 $r.stage='verify settled prior attempt and prepare corrected packet';Save-Host
 $prepared=Invoke-Command -Session $session -ArgumentList $plan,$priorText -ScriptBlock {
  param($plan,$priorText)
  Set-StrictMode -Version Latest
  $ErrorActionPreference='Stop'
  $original=$plan.original_guest_directory;$path=$plan.guest_directory
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Get-FileHash -LiteralPath (Join-Path $original 'plan.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.original_plan_sha256){throw 'Exact original guest packet required'}
  $prior=$priorText|ConvertFrom-Json
  $record=Get-Content -LiteralPath (Join-Path $plan.prior_guest_directory 'guest-receipt.json') -Raw|ConvertFrom-Json
  if(($record|ConvertTo-Json -Depth 20 -Compress) -cne ($prior|ConvertTo-Json -Depth 20 -Compress)){throw 'Original stopped guest receipt differs'}
  if($prior.outcome -cne 'failed' -or $prior.stage -cne 'patch exact lab SQL instance' -or $prior.started -cne '2026-11-20T18:03:59.6444154Z' -or -not $prior.execution_settled -or $prior.connections_closed -ne 1 -or -not $prior.installer_started -or $prior.installer_exit_code -ne -2068578299 -or $null -ne $prior.cleanup_failure -or $prior.first_failure.type -cne 'System.Management.Automation.RuntimeException' -or $prior.first_failure.detail -cne 'Installer failed; preserve checkpoint and setup logs'){throw 'Only the exact settled installer-input refusal may continue'}
  $held=Get-Variable P02LabSqlUpdateHeld -Scope Global -ErrorAction SilentlyContinue
  if($null -eq $held -or -not $held.Value.settled -or $null -ne $held.Value.process -or $null -ne $held.Value.connection -or ($held.Value.receipt|ConvertTo-Json -Depth 20 -Compress|ConvertFrom-Json|ConvertTo-Json -Depth 20 -Compress) -cne ($prior|ConvertTo-Json -Depth 20 -Compress)){throw 'Prior native custody is absent, changed or unresolved'}
  $summary='C:\Program Files\Microsoft SQL Server\160\Setup Bootstrap\Log\Summary.txt'
  if((Get-FileHash -LiteralPath $summary -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.installer_summary_sha256){throw 'Original installer input-validation evidence differs'}
  if(Test-Path -LiteralPath $path){throw 'Correction path already exists; preserve attempt'}
  if(@(Get-CimInstance Win32_Process|Where-Object {$_.Name -ieq 'SQLServer2022-KB5132747-x64.exe' -or $_.Name -ieq 'setup.exe'}).Count){throw 'Installer process exists; no replay'}
  if((Get-FileHash -LiteralPath (Join-Path $original 'preflight\receipt.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'cfcd43be18015f9e0a798924f73d33880f406e7629b0cb09d658c5216056cdf4'){throw 'Original completed media receipt differs'}
  foreach($item in $plan.reused_files.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $original $item.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.Value){throw 'Reused sealed payload differs'}}
  $partition=Get-Partition -DriveLetter Q;$disk=Get-Disk -Number $partition.DiskNumber
  if($partition.Guid -ine '{47cc6080-9e5f-447c-a9e2-dcc007b1e297}' -or $disk.UniqueId -ine '60022480F18852E666A58D834543C4BC' -or $disk.Size -ne 416GB -or (Get-Volume -DriveLetter Q).SizeRemaining -lt 50GB){throw 'Retained lab storage differs'}
  [void][IO.Directory]::CreateDirectory((Join-Path $path 'preflight'))
  foreach($item in $plan.reused_files.PSObject.Properties){[IO.File]::Copy((Join-Path $original $item.Name),(Join-Path $path $item.Name),$false)}
  [IO.File]::Copy((Join-Path $original 'preflight\receipt.json'),(Join-Path $path 'preflight\receipt.json'),$false)
  return $true
 }
 if($prepared -ne $true){throw 'Corrected packet preparation not acknowledged'}
 Copy-Item -ToSession $session -LiteralPath (Join-Path $root 'Update-P02LabSql.ps1') -Destination ([IO.Path]::Combine($plan.guest_directory,'Update-P02LabSql.ps1'))
 Copy-Item -ToSession $session -LiteralPath (Join-Path $root 'update-plan.json') -Destination ([IO.Path]::Combine($plan.guest_directory,'plan.json'))
 $r.stage='run corrected preflight and unfinished SQL update';Save-Host
 $global:P02LabSqlUpdateCorrectedJob=Invoke-Command -Session $session -ArgumentList $plan.guest_directory,$plan.guest_entry_sha256,$plan.update_plan_sha256 -AsJob -ScriptBlock {
  param($path,$digest,$planDigest)
  $entry=Join-Path $path 'Update-P02LabSql.ps1'
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest -or (Get-FileHash -LiteralPath (Join-Path $path 'plan.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $planDigest){throw 'Corrected sealed guest entry or plan differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path
 }
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($global:P02LabSqlUpdateCorrectedJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 1000){$null=Wait-Job -Job $global:P02LabSqlUpdateCorrectedJob -Timeout 10;Write-Host ('Lab SQL update: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original checkpoint retained.')}
 $job=$global:P02LabSqlUpdateCorrectedJob
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
 if($r.guest.outcome -cnotin @('passed','passed_restart_required')){throw 'Corrected update stage refused; inspect guest first failure and retained evidence'}
 if($r.Contains('collection_failure')){throw 'Update result retained but log collection incomplete'}
 $r.outcome=$r.guest.outcome;$r.stage=$r.guest.stage
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{$r.finished=[datetime]::UtcNow.ToString('o');Save-Host}
[pscustomobject]$r|Select-Object outcome,stage,first_failure|Format-List
Write-Host ('Evidence saved: '+$root)
