#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$SealPath,
      [Management.Automation.Runspaces.PSSession]$Session,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$vmId=[guid]'2ac1b401-7076-4965-af71-de36ee0f9f9c'
$seal=Get-Content -LiteralPath $SealPath -Raw|ConvertFrom-Json
$root=Split-Path -Parent $SealPath
$evidenceRoot='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
$resuming=$seal.PSObject.Properties.Name -contains 'retained_warmup_receipt_sha256'
if($resuming){
 if($seal.retained_warmup_receipt_sha256 -cne 'c04c8dddf34511b779e77c4f3dfdcab1f9e03febd3f0b7b562b8d21155de0d38' -or $seal.fresh_reports -ne 19 -or $seal.retained_reports -ne 1 -or $seal.total_reports -ne 20){throw 'Exact completed warm-up continuation required'}
}elseif($seal.fresh_reports -ne 20){throw 'Exact original twenty-report workload required'}
if($seal.purpose -cne 'p02-balanced-cost-workload' -or $seal.production_eligible -ne $false -or $seal.vm_id -cne $vmId.ToString() -or $seal.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or $seal.pairs -ne 5){throw 'Exact finite paired workload seal required'}
if([IO.Path]::GetFullPath((Split-Path -Parent $root)) -ine $evidenceRoot -or (Split-Path -Leaf $root) -cnotmatch '^cost-execution-[0-9]{17}$' -or [IO.Path]::GetFullPath($seal.archive) -ine [IO.Path]::Combine($root,'packet.zip')){throw 'Exact local sealed packet directory required'}
if((Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.host_sha256 -or (Get-FileHash -LiteralPath $seal.archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $seal.sha256){throw 'Sealed host or packet differs'}
if($ValidateOnly){[pscustomobject]@{outcome='validated';native_actions=0;archive_sha256=$seal.sha256};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated development-host console required'}
if(Test-Path -LiteralPath (Join-Path $root 'launch-result.json')){throw 'Original launch already recorded; do not replay'}
$vm=Get-VM -Id $vmId
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running isolated VM required'}
$checkpoint=@(Get-VMSnapshot -VM $vm)
if($checkpoint.Count -ne 1 -or [string]$checkpoint[0].Id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Retained original checkpoint differs'}
$diskSpecs=@(
 [pscustomobject]@{location=4;relative='business-baseline-20261121173848849/business.vhdx';id='702186c1-fafe-4eda-95d8-7abb4c6843f2';bytes=128GB},
 [pscustomobject]@{location=5;relative='cost-fixtures-20261122130322703/cost.vhdx';id='c2a94828-d1b5-48d0-873f-6f341979c793';bytes=256GB}
)
foreach($spec in $diskSpecs){
 $disks=@(Get-VMHardDiskDrive -VM $vm|Where-Object {$_.ControllerType -eq 'SCSI' -and $_.ControllerNumber -eq 0 -and $_.ControllerLocation -eq $spec.location})
 $expected=Join-Path $evidenceRoot $spec.relative
 if($disks.Count -ne 1 -or [IO.Path]::GetFullPath($disks[0].Path) -ine [IO.Path]::GetFullPath($expected)){throw 'Completed lab disk attachment differs'}
 $vhd=Get-VHD -Path $disks[0].Path
 if([string]$vhd.DiskIdentifier -ine $spec.id -or $vhd.Size -ne $spec.bytes -or [string]$vhd.VhdType -cne 'Dynamic'){throw 'Completed lab disk identity differs'}
}
if($null -eq $Session){
 $matches=@(Get-PSSession|Where-Object {$_.VMId -eq $vmId -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'})
 if($matches.Count -ne 1){throw 'Pass the existing authenticated lab session'}
 $Session=$matches[0]
}
if($Session.VMId -ne $vmId -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$destination=Invoke-Command -Session $Session -ArgumentList $seal.guest_directory -ScriptBlock {
 param($path)
 Set-StrictMode -Version Latest;$ErrorActionPreference='Stop'
 if($env:COMPUTERNAME -cne 'MINI_AMD' -or (Test-Path -LiteralPath $path)){throw 'Exact guest and fresh packet directory required'}
 $partition=Get-Partition -DriveLetter S
 $disk=Get-Disk -Number $partition.DiskNumber
 $volume=Get-Volume -DriveLetter S
 if($disk.UniqueId -ine '600224802848A9C2B5D16F341979C793' -or $disk.Size -ne 256GB -or $partition.Guid.Trim('{}') -ine 'f22a52c3-25c4-438c-a45e-d928c519006f' -or $volume.FileSystem -cne 'NTFS' -or $volume.FileSystemLabel -cne 'P02_COST_20261122130322703'){throw 'Completed cost storage identity differs'}
 if((Get-PSDrive Q).Free -lt 1GB -or (Get-PSDrive S).Free -lt 40GB -or (Get-PSDrive C).Free -lt 2GB){throw 'Fresh backups, captures and evidence reserve required'}
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
 $entry=Join-Path $path 'qualification\p02_observer\cost_execution.py'
 $child=Start-Process -FilePath 'C:\Program Files\Python311\python.exe' -ArgumentList ('-I -S -B "'+$entry+'"') -WorkingDirectory $path -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $path 'stdout.txt') -RedirectStandardError (Join-Path $path 'stderr.txt')
 $null=$child.Handle
 $global:P02CostComparisonProcess=$child
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while(-not $child.WaitForExit(10000)){
  Write-Host ('Grouped cost comparison: '+[int]$watch.Elapsed.TotalSeconds+' seconds; original claim and fixtures retained.')
  if($watch.Elapsed.TotalSeconds -ge 2400){return [pscustomobject]@{state='retained-running';pid=$child.Id;path=$path}}
 }
 $child.WaitForExit()
 [pscustomobject]@{state='exited';pid=$child.Id;exitCode=$child.ExitCode;path=$path}
}
$run|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'launch-result.json') -Encoding UTF8
$names=@('receipt.json','progress.json','entered.json','stdout.txt','stderr.txt')
foreach($operation in @('Status','Preflight','Apply','Verify')){foreach($stream in @('stdout','stderr')){$names+=($operation+'.'+$stream+'.txt')}}
$available=@(Invoke-Command -Session $Session -ArgumentList $seal.guest_directory,$names -ScriptBlock {
 param($path,$names)
 foreach($name in $names){if(Test-Path -LiteralPath (Join-Path $path $name)){$name}}
})
foreach($name in $available){
 $local=Join-Path $root $name
 if(Test-Path -LiteralPath $local){throw 'Existing collected evidence must not be overwritten'}
 Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($seal.guest_directory,$name)) -Destination $local
}
# Only bounded JSON/text records; no credentials, backup files or private spool.
$records=@(Invoke-Command -Session $Session -ArgumentList $seal.guest_directory -ScriptBlock {
 param($path)
 $dir=Join-Path $path 'cost-evidence'
 if(-not(Test-Path -LiteralPath $dir)){return}
 $files=@(Get-ChildItem -LiteralPath $dir -File -Recurse)
 [long]$totalBytes=0
 foreach($file in $files){$totalBytes+=$file.Length}
 if($files.Count -gt 200 -or $totalBytes -gt 256MB){throw 'Cost evidence exceeds its collection bound'}
 foreach($file in $files){
  $relative=$file.FullName.Substring($path.Length+1)
  if($relative -cnotmatch '^cost-evidence\\(?:[0-9]{2}-(?:OFF|ON)-(?:workload|consumer)\\(?:entered|progress|receipt|contracts|bound-contracts)\.json|[0-9]{2}-(?:OFF|ON)-(?:workload|consumer)\.(?:stdout|stderr)\.txt|captures-[0-9]{2}\.json)$'){throw 'Unexpected cost evidence member'}
  $relative
 }
})
foreach($name in $records){
 $local=Join-Path $root $name
 if(Test-Path -LiteralPath $local){throw 'Existing cost evidence must not be overwritten'}
 [void][IO.Directory]::CreateDirectory((Split-Path -Parent $local))
 Copy-Item -FromSession $Session -LiteralPath ([IO.Path]::Combine($seal.guest_directory,$name)) -Destination $local
}
$run|Format-List
$receipt=Join-Path $root 'receipt.json'
if(Test-Path -LiteralPath $receipt){Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json|Select-Object outcome,stage,original_preserved,original_name_restored,login_disabled,physical_custody_retained,first_failure|Format-List}
Write-Host ('Evidence saved: '+$root)
Write-Host 'Completed original work and claim are retained. Do not rerun this packet.'
