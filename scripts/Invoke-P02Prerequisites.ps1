#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$ValidateOnly,[Management.Automation.Runspaces.PSSession]$Session)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
if($plan.schema -cne 'p02-prerequisite-plan/1' -or $plan.production_eligible -ne $false -or $plan.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $plan.sql_commit -cne '73b004d4a834f87fe3e559480d99dd597995fd91' -or $plan.guest_directory -cnotmatch '^Q:\\P02Release\\prerequisites-[0-9]{17}$'){throw 'Exact isolated prerequisite plan required'}
$names=@($plan.files.PSObject.Properties.Name)
if($names.Count -ne 5 -or @($names|Where-Object {$_ -cnotin @('Invoke-P02Prerequisites.ps1','Continue-P02Prerequisites.ps1','source.bundle','baseline-receipt.json','prior-guest-receipt.json')}).Count){throw 'Exact sealed prerequisite inventory required'}
foreach($name in $names){$path=Join-Path $root $name;$item=Get-Item -LiteralPath $path -Force;if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt 64MB -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.files.$name){throw ('Sealed prerequisite member differs: '+$name)}}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.files.'Invoke-P02Prerequisites.ps1' -or $plan.files.'baseline-receipt.json' -cne '39d80a0112d8c79851b03dfe048f559192033cac772ba41fac5ece24fc18d21b' -or $plan.files.'prior-guest-receipt.json' -cne '372d0aaba182fb7a328e665131ca222a22bc0106a1642a6f807c348875c3b8d1'){throw 'Execute sealed entry against exact completed baseline'}
foreach($id in @($plan.phase1_release_id,$plan.d4_release_id)){if(([guid]$id).ToString() -cne $id){throw 'Exact native release identity required'}}
if($ValidateOnly){[pscustomobject]@{validated=$true;members=5;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$plan.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
if($null -eq $Session){$sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($sessions.Count -ne 1){throw 'One existing authenticated lab session required'};$Session=$sessions[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available VM session required'}
$receiptPath=Join-Path $root 'host-receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Prior prerequisite attempt retained; inspect before continuation'}
$r=[ordered]@{schema='p02-prerequisite-host/1';started=[DateTime]::UtcNow.ToString('o');outcome='running';stage='copy sealed packet';guest=$null;first_failure=$null;production_operations=0;business_operations=0}
function Save-HostReceipt {[IO.File]::WriteAllText($receiptPath,($r|ConvertTo-Json -Depth 28),[Text.UTF8Encoding]::new($false))}
Save-HostReceipt
try {
 Invoke-Command -Session $Session -ArgumentList $plan.guest_directory -ScriptBlock {
  param($root)
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Test-Path -LiteralPath $root)){throw 'Exact guest and fresh packet directory required'}
  $partition=Get-Partition -DriveLetter Q;$disk=Get-Disk -Number $partition.DiskNumber;$volume=Get-Volume -DriveLetter Q
  if($partition.Guid -ine '{47cc6080-9e5f-447c-a9e2-dcc007b1e297}' -or $disk.UniqueId -ine '60022480F18852E666A58D834543C4BC' -or $disk.Size -ne 416GB -or $volume.FileSystemLabel -cne 'K98_D5B_QUALIFICATION' -or $volume.SizeRemaining -lt 50GB){throw 'Exact expanded lab volume and reserve required'}
  [void][IO.Directory]::CreateDirectory($root)
 }
 foreach($name in @('plan.json')+$names){Copy-Item -LiteralPath (Join-Path $root $name) -Destination ([IO.Path]::Combine($plan.guest_directory,$name)) -ToSession $Session}
 $r.stage='guest prerequisite stages';Save-HostReceipt
 $global:P02PrerequisiteJob=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$plan.files.'Continue-P02Prerequisites.ps1' -AsJob -ScriptBlock {
  param($root,$sha)
  $entry=Join-Path $root 'Continue-P02Prerequisites.ps1'
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha){throw 'Guest entry differs'}
  $script=[ScriptBlock]::Create([IO.File]::ReadAllText($entry));& $script -PacketRoot $root
 }
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($global:P02PrerequisiteJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 1200){$null=Wait-Job -Job $global:P02PrerequisiteJob -Timeout 10;Write-Host ('Prerequisite fixture: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original fixtures retained.')}
 if($global:P02PrerequisiteJob.State -ne 'Completed'){throw 'Guest job unresolved; retain session/job and do not rerun'}
 $received=@(Receive-Job -Job $global:P02PrerequisiteJob -Keep)
 if($global:P02PrerequisiteJob.ChildJobs.Count -ne 1 -or $global:P02PrerequisiteJob.ChildJobs[0].Error.Count -or $received.Count -ne 1 -or $received[0] -isnot [string]){throw 'Unexpected guest result; original job retained'}
 $r.guest=$received[0]|ConvertFrom-Json
 [IO.File]::WriteAllText((Join-Path $root 'guest-receipt.json'),$received[0],[Text.UTF8Encoding]::new($false))
 $logs=@('20261106_001_personal_stats_daily_read_plan','20261109_001_p02_phase1_sql_exports','20261111_001_p02_d4_combined')|ForEach-Object {$_+'.stdout.txt';$_+'.stderr.txt'}
 foreach($name in $logs){$present=Invoke-Command -Session $Session -ArgumentList $plan.guest_directory,$name -ScriptBlock {param($root,$name) Test-Path -LiteralPath (Join-Path $root $name)};if($present){Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($plan.guest_directory,$name)) -Destination (Join-Path $root $name)}}
 if($r.guest.outcome -cne 'passed'){throw 'Guest prerequisite stage stopped; preserve completed stages and first failure'}
 $r.outcome='passed';$r.stage='genuine prerequisites committed'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{$r.finished=[DateTime]::UtcNow.ToString('o');Save-HostReceipt}
[pscustomobject]$r|Select-Object outcome,stage,first_failure|Format-List
Write-Host ('Evidence saved: '+$root)
