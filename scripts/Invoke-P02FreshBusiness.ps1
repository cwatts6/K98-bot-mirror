#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$SealPath,
      [Management.Automation.Runspaces.PSSession]$Session,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$vmId=[guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
$seal=Get-Content -LiteralPath $SealPath -Raw|ConvertFrom-Json
$root=Split-Path -Parent $SealPath
if($seal.purpose -cnotin @('fresh-db18-release-report-capture','fresh-db18-backup-preflight-continuation','fresh-db18-producer-first-overlap','preserved-db18-index-reader-qualification','preserved-db18-recovery-coexistence','preserved-db18-actor-qualification','preserved-db18-maintenance-continuation','preserved-db18-publisher-baseline','preserved-db18-publisher-orders','preserved-db18-publisher-continuation') -or $seal.production_eligible -ne $false -or $seal.vm_id -cne $vmId.ToString() -or $seal.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or $seal.target_database_id -ne 18){throw 'Exact fresh business qualification seal required'}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.host_sha256 -or (Get-FileHash -LiteralPath $seal.archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.sha256){throw 'Sealed host or packet differs'}
$evidenceRoot='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
if([IO.Path]::GetFullPath((Split-Path -Parent $root)) -ine $evidenceRoot -or (Split-Path -Leaf $root) -cnotmatch '^fresh-business-[0-9]{17}$' -or [IO.Path]::GetFullPath($seal.archive) -ine [IO.Path]::Combine($root,'packet.zip')){throw 'Exact local sealed packet directory required'}
if($ValidateOnly){[pscustomobject]@{outcome='validated';native_actions=0;archive_sha256=$seal.sha256};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated development-host console required'}
if(Test-Path -LiteralPath (Join-Path $root 'launch-result.json')){throw 'Original launch already recorded; do not replay'}
$vm=Get-VM -Id $vmId
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$disks=@(Get-VMHardDiskDrive -VM $vm|Where-Object {$_.ControllerType -eq 'SCSI' -and $_.ControllerNumber -eq 0 -and $_.ControllerLocation -eq 4})
$expectedVhd=Join-Path (Split-Path -Parent $root) 'business-baseline-20261121173848849/business.vhdx'
if($disks.Count -ne 1 -or [IO.Path]::GetFullPath($disks[0].Path) -ine [IO.Path]::GetFullPath($expectedVhd)){throw 'Completed business disk attachment differs'}
$vhd=Get-VHD -Path $disks[0].Path
if([string]$vhd.DiskIdentifier -ine '702186c1-fafe-4eda-95d8-7abb4c6843f2' -or $vhd.Size -ne 128GB -or [string]$vhd.VhdType -cne 'Dynamic'){throw 'Completed business disk identity differs'}
$checkpoint=@(Get-VMSnapshot -VM $vm)
if($checkpoint.Count -ne 1 -or [string]$checkpoint[0].Id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Retained original checkpoint differs'}
if($null -eq $Session){
 $matches=@(Get-PSSession|Where-Object {$_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'})
 if($matches.Count -ne 1){throw 'Pass the existing authenticated lab session'}
 $Session=$matches[0]
}
if($Session.VMId -ne $vmId -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
# Collect only the missing final preservation records. Existing evidence is
# checked, never overwritten; no guest script or SQL is replayed for collection.
$priorRoot=Join-Path (Split-Path -Parent $root) 'business-baseline-20261121181435617'
$priorGuest='Q:\P02Observer\20261121181435617'
$pins=@{'before/receipt.json'='9098b90e82e293d764dfdbfaeb82e4807b935b3ee539e71f7cce565f59b0c19e';'after/receipt.json'='d56edab767d4accdaef1871150cd96479b1aa400484c83abea3878a34d3d9d18'}
foreach($name in @('before/receipt.json','before/entered.json','after/receipt.json','after/entered.json')){
 $remote=[IO.Path]::Combine($priorGuest,$name);$local=Join-Path $priorRoot $name
 if(-not(Test-Path -LiteralPath $local)){Copy-Item -FromSession $Session -LiteralPath $remote -Destination $local}
 if($pins.ContainsKey($name) -and (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant() -cne $pins[$name]){throw 'Original final preservation receipt differs'}
}
$destination=Invoke-Command -Session $Session -ArgumentList $seal.guest_directory -ScriptBlock {
 param($path)
 if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Test-Path -LiteralPath $path)){throw 'Exact guest and fresh packet directory required'}
 $partition=Get-Partition -DriveLetter R
 $disk=Get-Disk -Number $partition.DiskNumber
 $volume=Get-Volume -DriveLetter R
 if($disk.UniqueId -ine '60022480C1862170FEFA7ABB4C6843F2' -or $disk.Size -ne 128GB -or $partition.PartitionNumber -ne 2 -or $partition.Guid.Trim('{}') -ine 'fa4c5920-80fb-4206-ab7d-88f12cb600ff' -or $partition.Size -ne 137421127680 -or $volume.FileSystem -cne 'NTFS' -or $volume.FileSystemLabel -cne 'P02_BUSINESS_20261121180254259'){throw 'Completed guest storage identity differs'}
 if((Get-PSDrive Q).Free -lt 20GB -or (Get-PSDrive R).Free -lt 40GB -or (Get-PSDrive C).Free -lt 1GB){throw 'Preserved snapshot and work reserve required'}
 [void][IO.Directory]::CreateDirectory($path)
 Join-Path $path 'packet.zip'
}
Copy-Item -LiteralPath $seal.archive -Destination $destination -ToSession $Session
$run=Invoke-Command -Session $Session -ArgumentList $seal.guest_directory,$seal.sha256 -ScriptBlock {
 param($path,$digest)
 Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
 $zip=Join-Path $path 'packet.zip'
 if((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Guest sealed archive differs'}
 Expand-Archive -LiteralPath $zip -DestinationPath $path
 $entry=Join-Path $path 'qualification\p02_observer\application.py'
 $child=Start-Process -FilePath 'C:\Program Files\Python311\python.exe' -ArgumentList ('-I -S -B "'+$entry+'"') -WorkingDirectory $path -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $path 'stdout.txt') -RedirectStandardError (Join-Path $path 'stderr.txt')
 $null=$child.Handle
 $global:P02FreshBusinessProcess=$child
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while(-not $child.WaitForExit(10000)){
  Write-Host ('Grouped fresh qualification: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original claim and fixtures retained.')
  if($watch.Elapsed.TotalSeconds -ge 1200){return [pscustomobject]@{state='retained-running';pid=$child.Id;path=$path}}
 }
 $child.WaitForExit()
 [pscustomobject]@{state='exited';pid=$child.Id;exitCode=$child.ExitCode;path=$path}
}
$run|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'launch-result.json') -Encoding UTF8
# A fixed evidence inventory, excluding credentials and all spool/report data.
$names=@('receipt.json','progress.json','entered.json','stdout.txt','stderr.txt','handover.json',
 'before-restore-reader.json','after-restore-reader.json','fresh-contract-observation.json','fresh-runtime.json','fresh-backups.json')
$names+=@(1..10|ForEach-Object {'stage-'+$_+'.json'})
foreach($operation in @('Status','Preflight','Apply','Verify')){foreach($stream in @('stdout','stderr')){$names+=($operation+'.'+$stream+'.txt')}}
foreach($role in @('producer','reader','consumer')){foreach($index in @(1,2)){foreach($suffix in @('entered.json','progress.json','ready.json','go.json','abort.json','stdout.txt','stderr.txt','complete-observation.json')){$names+=($role+'-'+$index+'.'+$suffix)}}}
$available=@(Invoke-Command -Session $Session -ArgumentList $seal.guest_directory,$names -ScriptBlock {
 param($path,$names)
 foreach($name in $names){if(Test-Path -LiteralPath (Join-Path $path $name)){$name}}
})
foreach($name in $available){
 $local=Join-Path $root $name
 if(Test-Path -LiteralPath $local){throw 'Existing collected evidence must not be overwritten'}
 Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($seal.guest_directory,$name)) -Destination $local
}
$run|Format-List
$receipt=Join-Path $root 'receipt.json'
if(Test-Path -LiteralPath $receipt){Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json|Select-Object outcome,stage,original_preserved,login_disabled,physical_custody_retained,first_failure|Format-List}
Write-Host ('Evidence saved: '+$root)
Write-Host 'Completed storage, original setup, migrations and claim are retained. Do not rerun this packet.'
