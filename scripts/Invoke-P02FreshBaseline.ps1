#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$ValidateOnly,[Management.Automation.Runspaces.PSSession]$Session)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
if($plan.schema -cne 'p02-fresh-baseline-plan/1' -or $plan.production_eligible -ne $false -or $plan.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $plan.database -cnotmatch '^K98_P02Release_[0-9]{17}$' -or $plan.disk_before_bytes -ne 288GB -or $plan.disk_after_bytes -ne 416GB){throw 'Exact fresh baseline plan required'}
$names=@($plan.files.PSObject.Properties.Name)
if($names.Count -ne 3 -or @($names|Where-Object {$_ -cnotin @('Invoke-P02FreshBaseline.ps1','Restore-P02FreshBaseline.ps1','backup-inventory.json')}).Count){throw 'Exact sealed baseline inventory required'}
foreach($name in $names){$path=Join-Path $root $name;$info=Get-Item -LiteralPath $path -Force;if($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $info.Length -gt 1MB -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.files.$name){throw ('Sealed baseline member differs: '+$name)}}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.files.'Invoke-P02FreshBaseline.ps1'){throw 'Execute the sealed host entry'}
if($plan.files.'backup-inventory.json' -cne '851e3db25d20ad2d84ceaf1777d02829d7f79dbda5f1f46b24c0de824138c852'){throw 'Exact native backup inventory required'}
if($ValidateOnly){[pscustomobject]@{validated=$true;native_actions=0;members=$names.Count};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$plan.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
if($null -eq $Session){$sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($sessions.Count -ne 1){throw 'One existing authenticated lab session required'};$Session=$sessions[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available VM session required'}
$diskPath='C:\discord_file_downloader\.codex_artifacts\p025\d5b-native\D5b-Qualification-20261111.vhdx'
$vhd=Get-VHD -Path $diskPath
$attachment=@(Get-VMHardDiskDrive -VM $vm|Where-Object {$_.Path -ieq $diskPath})
if($vhd.DiskIdentifier -ine 'E65288F1-A566-46C6-AD4E-8D834543C4BC' -or $vhd.VhdType -ne 'Dynamic' -or $vhd.VhdFormat -ne 'VHDX' -or $vhd.Size -ne 288GB -or $vhd.ParentPath -or -not $vhd.Attached -or $attachment.Count -ne 1 -or $attachment[0].ControllerType -ne 'SCSI' -or @(Get-VMSnapshot -VM $vm).Count){throw 'Unchanged directly attached lab disk without checkpoints required'}
if((Get-PSDrive C).Free -lt 150GB){throw 'Host capacity reserve unavailable'}
$receiptPath=Join-Path $root 'host-receipt.json'
if(Test-Path -LiteralPath $receiptPath){throw 'Prior host attempt retained; inspect before continuation'}
$r=[ordered]@{schema='p02-fresh-baseline-host/1';started=[DateTime]::UtcNow.ToString('o');outcome='running';stage='preflight';actions=@();guest=$null;first_failure=$null;production_operations=0;business_operations=0}
function Save-HostReceipt {[IO.File]::WriteAllText($receiptPath,($r|ConvertTo-Json -Depth 24),[Text.UTF8Encoding]::new($false))}
Save-HostReceipt
try {
 $r.guest_before=Invoke-Command -Session $Session -ScriptBlock {
  if($env:COMPUTERNAME -cne 'MINI_AMD'){throw 'Exact guest required'}
  $p=@(Get-Partition -DriveLetter Q);if($p.Count -ne 1){throw 'One Q partition required'};$d=Get-Disk -Number $p[0].DiskNumber;$v=Get-Volume -DriveLetter Q
  if($p[0].DiskNumber -ne 1 -or $p[0].PartitionNumber -ne 2 -or $p[0].Guid -ine '{47cc6080-9e5f-447c-a9e2-dcc007b1e297}' -or $p[0].Size -ne 309219819520 -or $d.UniqueId -ine '60022480F18852E666A58D834543C4BC' -or $d.Size -ne 288GB -or $d.IsOffline -or $d.IsReadOnly -or $v.FileSystemLabel -cne 'K98_D5B_QUALIFICATION' -or $v.FileSystem -cne 'NTFS'){throw 'Exact qualification volume/partition/disk required'}
  [pscustomobject]@{disk_bytes=$d.Size;disk_id=$d.UniqueId;partition_bytes=$p[0].Size;partition_id=$p[0].Guid;free=$v.SizeRemaining}
 }
 $r.stage='grow lab virtual disk';$r.actions+=@([ordered]@{action='expand existing qualification VHDX 288 to 416 GiB';acknowledged=$false});Save-HostReceipt
 Resize-VHD -Path $diskPath -SizeBytes 416GB
 $after=Get-VHD -Path $diskPath
 if($after.DiskIdentifier -ine $vhd.DiskIdentifier -or $after.Size -ne 416GB -or $after.ParentPath){throw 'Disk expansion acknowledgement differs'}
 $r.actions[-1].acknowledged=$true;Save-HostReceipt
 $r.stage='extend exact Q partition';$r.actions+=@([ordered]@{action='extend existing qualification partition';acknowledged=$false});Save-HostReceipt
 $r.guest_after=Invoke-Command -Session $Session -ScriptBlock {
  Update-HostStorageCache
  $p=@(Get-Partition -DriveLetter Q);if($p.Count -ne 1){throw 'One Q partition required'};$d=Get-Disk -Number $p[0].DiskNumber
  if($p[0].DiskNumber -ne 1 -or $p[0].PartitionNumber -ne 2 -or $p[0].Guid -ine '{47cc6080-9e5f-447c-a9e2-dcc007b1e297}' -or $p[0].Size -ne 309219819520 -or $d.UniqueId -ine '60022480F18852E666A58D834543C4BC' -or $d.Size -ne 416GB -or $d.IsOffline -or $d.IsReadOnly){throw 'Exact expanded disk and unchanged partition required'}
  $limit=Get-PartitionSupportedSize -DiskNumber 1 -PartitionNumber 2
  if($limit.SizeMax -lt ($p[0].Size+127GB) -or $limit.SizeMax -ge 416GB){throw 'Partition expansion bound differs'}
  Resize-Partition -DiskNumber 1 -PartitionNumber 2 -Size $limit.SizeMax
  $p=Get-Partition -DriveLetter Q;$v=Get-Volume -DriveLetter Q
  if($p.Guid -ine '{47cc6080-9e5f-447c-a9e2-dcc007b1e297}' -or $p.Size -ne $limit.SizeMax -or $v.FileSystemLabel -cne 'K98_D5B_QUALIFICATION' -or $v.SizeRemaining -lt 105GB){throw 'Expanded volume acknowledgement/headroom differs'}
  [pscustomobject]@{partition_bytes=$p.Size;partition_id=$p.Guid;free=$v.SizeRemaining}
 }
 $r.actions[-1].acknowledged=$true;Save-HostReceipt
 $r.stage='fresh restore dispatch';Save-HostReceipt
 $guest=[ScriptBlock]::Create([IO.File]::ReadAllText((Join-Path $root 'Restore-P02FreshBaseline.ps1')))
 $global:P02FreshBaselineJob=Invoke-Command -Session $Session -ScriptBlock $guest -ArgumentList $plan.database -AsJob
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($global:P02FreshBaselineJob.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt 600){$null=Wait-Job -Job $global:P02FreshBaselineJob -Timeout 10;Write-Host ('Fresh baseline preparation: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original fixtures retained.')}
 if($global:P02FreshBaselineJob.State -ne 'Completed'){throw 'Guest remains unresolved; retain job/session and do not replay'}
 $received=@(Receive-Job -Job $global:P02FreshBaselineJob -Keep)
 if($global:P02FreshBaselineJob.ChildJobs.Count -ne 1 -or $global:P02FreshBaselineJob.ChildJobs[0].Error.Count -ne 0 -or $received.Count -ne 1 -or $received[0] -isnot [string]){throw 'Unexpected guest result; retain original job'}
 $r.guest=$received[0]|ConvertFrom-Json
 [IO.File]::WriteAllText((Join-Path $root 'guest-receipt.json'),$received[0],[Text.UTF8Encoding]::new($false))
 if($r.guest.outcome -cne 'passed'){throw 'Guest stopped; preserve completed stages and first diagnostic'}
 $r.outcome='passed';$r.stage='fresh baseline observed'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{$r.finished=[DateTime]::UtcNow.ToString('o');Save-HostReceipt}
[pscustomobject]$r|Select-Object outcome,stage,first_failure|Format-List
Write-Host ('Evidence saved: '+$root)
