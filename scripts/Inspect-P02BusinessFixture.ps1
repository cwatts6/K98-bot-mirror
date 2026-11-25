#requires -Version 5.1
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$SealPath,
 [Management.Automation.Runspaces.PSSession]$Session,
 [switch]$ValidateOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($SealPath))
$seal=Get-Content -LiteralPath $SealPath -Raw|ConvertFrom-Json
$vmId=[guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
$runner='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\scripts\Invoke-P02ObserverLab.ps1'
if($seal.purpose -cne 'retained-business-fixture-preflight' -or $seal.stage -cne 'observer-release-preflight-read' -or $seal.database -cne 'ROK_TRACKER' -or $seal.vm_id -cne [string]$vmId -or $seal.production_eligible -ne $false){throw 'Exact read-only fixture preflight required'}
foreach($item in @(@{path=$seal.archive;hash=$seal.sha256},@{path=$PSCommandPath;hash=$seal.inspector_sha256},@{path=$runner;hash=$seal.runner_sha256})){
 $file=Get-Item -LiteralPath $item.path -Force
 if($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.hash){throw 'Sealed preflight file differs'}
}
if($ValidateOnly){[pscustomobject]@{validated=$true;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id $vmId
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
if($null -eq $Session){
 $sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'})
 if($sessions.Count -ne 1){throw 'One authenticated lab session required'}
 $Session=$sessions[0]
}
if($Session.VMId -ne $vmId -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$path=Join-Path $root 'host-inventory.json'
if(Test-Path -LiteralPath $path){throw 'Prior inventory retained; do not rerun'}
$r=[ordered]@{schema='p02-business-fixture-host-inventory/1';outcome='running';stage='read host storage';started=[DateTime]::UtcNow.ToString('o');vm_id=[string]$vmId;host_free_bytes=(Get-PSDrive C).Free;disks=@();checkpoints=@();guest=$null;first_failure=$null;storage_changes=0;database_operations=0;production_operations=0}
try{
 $drives=@(Get-VMHardDiskDrive -VM $vm)
 if($drives.Count -gt 8){throw 'Bounded lab disk inventory required'}
 foreach($drive in $drives){
  $vhd=Get-VHD -Path $drive.Path
  $r.disks+=@([ordered]@{path=$drive.Path;controller_type=[string]$drive.ControllerType;controller_number=$drive.ControllerNumber;controller_location=$drive.ControllerLocation;virtual_bytes=$vhd.Size;file_bytes=$vhd.FileSize;format=[string]$vhd.VhdFormat;type=[string]$vhd.VhdType;parent_path=$vhd.ParentPath;disk_id=[string]$vhd.DiskIdentifier})
 }
 $r.checkpoints=@(Get-VMSnapshot -VM $vm|Select-Object @{n='id';e={[string]$_.Id}},Name,CreationTime)
 if(@($r.checkpoints|Where-Object {$_.id -eq '125272d0-20b7-4705-908f-d3debc71bce2'}).Count -ne 1){throw 'Original SQL-update checkpoint must remain retained'}
 $r.stage='read guest storage'
 $r.guest=Invoke-Command -Session $Session -ScriptBlock {
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'MINI_AMD\K98LabAdmin'){throw 'Exact Windows lab guest identity required'}
  $disks=@(Get-Disk|Select-Object Number,UniqueId,SerialNumber,Size,PartitionStyle,IsOffline,IsReadOnly,IsBoot,IsSystem)
  $volumes=@(Get-Volume|Where-Object {$null -ne $_.DriveLetter}|Select-Object DriveLetter,FileSystemLabel,FileSystem,Size,SizeRemaining)
  if($disks.Count -gt 8 -or $volumes.Count -gt 16){throw 'Bounded guest storage inventory required'}
  [pscustomobject]@{disks=$disks;volumes=$volumes}
 }
 $r.outcome='passed';$r.stage='host and guest inventory collected'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{
 $r.finished=[DateTime]::UtcNow.ToString('o')
 $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($r|ConvertTo-Json -Depth 12));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
if($r.outcome -cne 'passed'){throw 'Storage inventory stopped; preserve its receipt without rerunning'}
& $runner -SealPath $SealPath -Session $Session
