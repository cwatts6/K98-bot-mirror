#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$ValidateOnly,[Management.Automation.Runspaces.PSSession]$Session)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
if($plan.schema -cne 'p02-lab-sql-update/1' -or $plan.production_eligible -ne $false -or $plan.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $plan.guest_directory -cnotmatch '^Q:\\P02Release\\sql-version-[0-9]{17}$' -or $plan.from_version -cne '16.0.1210.3' -or $plan.to_version -cne '16.0.1220.3'){throw 'Exact isolated SQL version plan required'}
$names=@('Invoke-P02LabSqlUpdate.ps1','Update-P02LabSql.ps1','preflight.zip','SQLServer2022-KB5132747-x64.exe')
if(@($plan.files.PSObject.Properties).Count -ne $names.Count){throw 'Exact packet inventory required'}
foreach($p in $plan.files.PSObject.Properties){
 $file=Join-Path $root $p.Name
 if($p.Name -cnotin $names -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -cne $p.Value){throw 'Sealed member differs'}
}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.files.'Invoke-P02LabSqlUpdate.ps1' -or $plan.files.'SQLServer2022-KB5132747-x64.exe' -cne 'b566f09a461ae4a563a11ff65fd6385993088437a0f3243aa114a90af5b71a79'){throw 'Exact sealed host and Microsoft package required'}
if($ValidateOnly){[pscustomobject]@{validated=$true;members=4;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$plan.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running network-isolated VM required'}
if((Get-PSDrive C).Free -lt 20GB){throw 'Host checkpoint reserve unavailable'}
if($null -eq $Session){$available=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($available.Count -ne 1){throw 'One existing authenticated lab session required'};$Session=$available[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$receiptPath=Join-Path $root 'host-receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Existing attempt retained; inspect before continuation'}
$r=[ordered]@{schema='p02-lab-sql-update-host/1';outcome='running';stage='copy sealed packet';started=[datetime]::UtcNow.ToString('o');first_failure=$null;checkpoint=$null;guest=$null;production_operations=0}
function Save-Host {[IO.File]::WriteAllText($receiptPath,($r|ConvertTo-Json -Depth 24),[Text.UTF8Encoding]::new($false))}
Save-Host
try{
 Invoke-Command -Session $Session -ArgumentList $plan.guest_directory -ScriptBlock {
  param($path)
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Test-Path -LiteralPath $path)){throw 'Exact guest and fresh packet path required'}
  foreach($name in @('P02PrerequisiteHeld','P02FreshBaselineHeld','P02LabSqlUpdateHeld')){
   $held=Get-Variable -Name $name -Scope Global -ErrorAction SilentlyContinue
   if($held -and (-not $held.Value.ContainsKey('settled') -or -not $held.Value.settled)){throw ('Unresolved native owner remains: '+$name)}
  }
  $partition=Get-Partition -DriveLetter Q;$disk=Get-Disk -Number $partition.DiskNumber;$volume=Get-Volume -DriveLetter Q
  if($partition.Guid -ine '{47cc6080-9e5f-447c-a9e2-dcc007b1e297}' -or $disk.UniqueId -ine '60022480F18852E666A58D834543C4BC' -or $disk.Size -ne 416GB -or $volume.FileSystemLabel -cne 'K98_D5B_QUALIFICATION' -or $volume.SizeRemaining -lt 50GB){throw 'Exact expanded lab disk and reserve required'}
  [void][IO.Directory]::CreateDirectory($path)
 }
 foreach($name in @('plan.json')+$names){Copy-Item -LiteralPath (Join-Path $root $name) -Destination ([IO.Path]::Combine($plan.guest_directory,$name)) -ToSession $Session}
 $r.stage='complete backup and lab preflight';Save-Host
 $preflight=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$plan.files.'preflight.zip' -ScriptBlock {
  param($path,$digest)
  $archive=Join-Path $path 'preflight.zip'
  if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Preflight archive differs'}
  $folder=Join-Path $path 'preflight'
  if(Test-Path -LiteralPath $folder){throw 'Preflight already exists; no replay'}
  Expand-Archive -LiteralPath $archive -DestinationPath $folder
  $entry=Join-Path $folder 'qualification/p02_observer/msdb_source_read.ps1'
  $child=Start-Process -FilePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -ArgumentList ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$entry+'"') -WorkingDirectory $folder -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $folder 'stdout.txt') -RedirectStandardError (Join-Path $folder 'stderr.txt')
  $null=$child.Handle;$watch=[Diagnostics.Stopwatch]::StartNew()
  while(-not $child.WaitForExit(1000) -and $watch.Elapsed.TotalSeconds -lt 180){}
  if(-not $child.HasExited){$global:P02MsdbPreflightProcess=$child;throw 'Preflight remains active; retain process and do not rerun'}
  $child.WaitForExit();$code=$child.ExitCode;$child.Dispose()
  $raw=[IO.File]::ReadAllText((Join-Path $folder 'receipt.json'))
  return [pscustomobject]@{exit_code=$code;receipt=$raw}
 }
 [IO.File]::WriteAllText((Join-Path $root 'preflight-receipt.json'),$preflight.receipt,[Text.UTF8Encoding]::new($false))
 $read=$preflight.receipt|ConvertFrom-Json
 if($preflight.exit_code -ne 0 -or $read.outcome -cne 'passed' -or $read.connections_closed -ne 1 -or -not $read.checksum_verification_completed -or $read.engine[0].product_version -cne $plan.from_version -or $read.backup_engine_build -cne '16.0.1220'){throw 'Completed media and exact-version preflight required'}
 $r.stage='preserve VM checkpoint';Save-Host
 if(@(Get-VMSnapshot -VM $vm|Where-Object {$_.Name -ceq $plan.checkpoint_name}).Count){throw 'Named checkpoint already exists; no replay'}
 $checkpoint=Checkpoint-VM -VM $vm -SnapshotName $plan.checkpoint_name -Passthru
 if($null -eq $checkpoint -or $checkpoint.Name -cne $plan.checkpoint_name -or $checkpoint.VMId -ne $vm.Id){throw 'Exact checkpoint acknowledgement required'}
 $r.checkpoint=[ordered]@{id=$checkpoint.Id.ToString();name=$checkpoint.Name;vm_id=$checkpoint.VMId.ToString()}
 Save-Host
 $r.stage='update isolated SQL instance';Save-Host
 $global:P02LabSqlUpdateJob=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$plan.files.'Update-P02LabSql.ps1' -AsJob -ScriptBlock {
  param($path,$digest)
  $entry=Join-Path $path 'Update-P02LabSql.ps1'
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Guest update entry differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path
 }
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($global:P02LabSqlUpdateJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 1000){$null=Wait-Job -Job $global:P02LabSqlUpdateJob -Timeout 10;Write-Host ('Lab SQL version update: '+[int]$watch.Elapsed.TotalSeconds+' seconds; checkpoint retained.')}
 $r.job_state=[string]$global:P02LabSqlUpdateJob.State
 $r.job_diagnostics=@($global:P02LabSqlUpdateJob.ChildJobs|ForEach-Object {
  $reason=[string]$_.JobStateInfo.Reason
  if($reason.Length -gt 8192){$reason=$reason.Substring(0,8192)}
  [pscustomobject]@{state=[string]$_.State;reason=$reason;errors=@($_.Error|Select-Object -First 8|ForEach-Object {$message=$_.Exception.Message;if($message.Length -gt 8192){$message=$message.Substring(0,8192)};$message})}
 })
 Save-Host
 if($global:P02LabSqlUpdateJob.State -ne 'Completed'){throw 'Guest job did not complete; inspect retained job/session/process and do not rerun'}
 $received=@(Receive-Job -Job $global:P02LabSqlUpdateJob -Keep)
 if($global:P02LabSqlUpdateJob.ChildJobs.Count -ne 1 -or $global:P02LabSqlUpdateJob.ChildJobs[0].Error.Count -or $received.Count -ne 1 -or $received[0] -isnot [string]){throw 'Unexpected native update output; original job retained'}
 $r.guest=$received[0]|ConvertFrom-Json
 [IO.File]::WriteAllText((Join-Path $root 'guest-receipt.json'),$received[0],[Text.UTF8Encoding]::new($false))
 try{
 foreach($name in @('installer.stdout.txt','installer.stderr.txt')){
  $present=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$name -ScriptBlock {param($path,$name) Test-Path -LiteralPath (Join-Path $path $name)}
  if($present){Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($plan.guest_directory,$name)) -Destination (Join-Path $root $name)}
 }
 $summary='C:\Program Files\Microsoft SQL Server\160\Setup Bootstrap\Log\Summary.txt'
 $present=Invoke-Command -Session $Session -ArgumentList $summary -ScriptBlock {param($path) Test-Path -LiteralPath $path}
 if($present){Copy-Item -FromSession $Session -LiteralPath $summary -Destination (Join-Path $root 'sql-setup-summary.txt')}
 }catch{$r.collection_failure=$_.Exception.Message}

 if($r.guest.outcome -cnotin @('passed','passed_restart_required')){throw 'Native SQL update stopped; preserve checkpoint and diagnostics'}
 if($r.Contains('collection_failure')){throw 'Update result retained but log collection incomplete'}
 $r.outcome=$r.guest.outcome;$r.stage=$r.guest.stage
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{$r.finished=[datetime]::UtcNow.ToString('o');Save-Host}
[pscustomobject]$r|Select-Object outcome,stage,checkpoint,first_failure|Format-List
Write-Host ('Evidence saved: '+$root)
