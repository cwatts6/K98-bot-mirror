#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[Management.Automation.Runspaces.PSSession]$Session,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$p=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
$base='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
$continuing=($null -ne $p.PSObject.Properties['resume_storage'] -and $p.resume_storage -eq $true)
$directoryContinuing=($null -ne $p.PSObject.Properties['resume_directory'] -and $p.resume_directory -eq $true)
if($directoryContinuing -and -not $continuing){throw 'Formatted continuation must retain original disk ownership'}
$fixtureStamp=if($directoryContinuing){'20261121180254259'}else{Split-Path -Leaf $p.guest_directory}
$priorRoot=Join-Path $base $(if($directoryContinuing){'business-baseline-20261121180254259'}else{'business-baseline-20261121173848849'})
$priorHostHash=if($directoryContinuing){'cb6b65a6983a33b124d161f54ca76ce581fe9e08349c834a2226fcc1250c012b'}else{'93952713873b9a30791d7362addafea995a0f9a0035535d3619b1b7b456bf659'}
$expectedVhd=if($continuing){Join-Path (Join-Path $base 'business-baseline-20261121173848849') 'business.vhdx'}else{Join-Path $root 'business.vhdx'}
if($continuing){
 $priorReceipt=Join-Path $priorRoot 'host-receipt.json'
 if((Get-FileHash -LiteralPath $priorReceipt -Algorithm SHA256).Hash.ToLowerInvariant() -cne $priorHostHash){throw 'Exact original settled host failure required'}
 $original=Get-Content -LiteralPath $priorReceipt -Raw|ConvertFrom-Json
}
if($root -cnotmatch ('^'+[regex]::Escape($base)+'\\business-baseline-[0-9]{17}$') -or $p.schema -cne 'p02-business-baseline-host/1' -or $p.production_eligible -ne $false -or $p.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $p.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or $p.fresh_database -cne ('K98_P02Business_'+$fixtureStamp) -or $p.host_vhd -cne $expectedVhd -or $p.new_disk_bytes -ne 128GB -or $p.controller_location -ne 4){throw 'Exact fresh business baseline plan required'}
foreach($item in @(@{path=$PSCommandPath;hash=$p.host_sha256},@{path=$p.archive;hash=$p.archive_sha256},@{path=(Join-Path $root 'host-inventory.json');hash=$p.inventory_sha256})){
 $info=Get-Item -LiteralPath $item.path -Force
 if($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -or (Get-FileHash -LiteralPath $info.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.hash){throw 'Sealed host member differs'}
}
if($p.archive -cne (Join-Path $root 'packet.zip') -or $p.inventory_sha256 -cne '42eb5d74466027c98c1cb99399eaf87d30b5adf673a9161ea4fbf6ab82e5e6a6'){throw 'Exact completed inventory and packet required'}
$cursor=$root
while($cursor.Length -ge $base.Length){
 $info=Get-Item -LiteralPath $cursor -Force
 if(-not $info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Ordinary authorized evidence directories required'}
 if($cursor -ceq $base){break}
 $cursor=Split-Path -Parent $cursor
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead($p.archive)
try{
 if($zip.Entries.Count -gt 128){throw 'Bounded sealed inventory required'}
 $entry=$zip.GetEntry('manifest.json')
 if($null -eq $entry -or $entry.Length -gt 1MB){throw 'Bounded manifest required'}
 $reader=[IO.StreamReader]::new($entry.Open(),[Text.UTF8Encoding]::new($false,$true))
 try{$manifest=$reader.ReadToEnd()|ConvertFrom-Json}finally{$reader.Dispose()}
 if($manifest.purpose -cne 'fresh-business-baseline-restore' -or $manifest.production_eligible -ne $false -or $manifest.vm_id -cne $p.vm_id -or $manifest.guest_directory -cne $p.guest_directory -or $manifest.fresh_database -cne $p.fresh_database -or $manifest.new_disk_bytes -ne 128GB -or $manifest.drive_letter -cne 'R' -or $manifest.data_directory -cne ('R:\'+$p.fresh_database) -or $manifest.volume_label -cne ('P02_BUSINESS_'+$fixtureStamp)){throw 'Sealed archive and host plan disagree'}
 if($continuing -ne ($null -ne $manifest.PSObject.Properties['resume_storage'] -and $manifest.resume_storage -eq $true)){throw 'Host and guest continuation mode differs'}
 if($directoryContinuing -ne ($null -ne $manifest.PSObject.Properties['resume_directory'] -and $manifest.resume_directory -eq $true)){throw 'Host and guest formatted continuation mode differs'}
 if($zip.Entries.Count -ne @($manifest.files.PSObject.Properties).Count+1){throw 'Exact archive inventory required'}
 $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($member in $zip.Entries){
  if(-not $seen.Add($member.FullName) -or $member.Length -gt 1MB -or $member.FullName -match '[:\\\\]' -or $member.FullName.StartsWith('/') -or @($member.FullName.Split('/')|Where-Object {$_ -in @('','.','..')}).Count){throw 'Unsafe or duplicated archive member'}
  if($member.FullName -ceq 'manifest.json'){continue}
  $property=$manifest.files.PSObject.Properties[$member.FullName]
  if($null -eq $property){throw 'Unexpected archive member'}
  $stream=$member.Open();$algorithm=[Security.Cryptography.SHA256]::Create()
  try{$digest=([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}finally{$algorithm.Dispose();$stream.Dispose()}
  if($digest -cne $property.Value){throw 'Sealed archive member differs'}
 }
}finally{$zip.Dispose()}
if($ValidateOnly){[pscustomobject]@{validated=$true;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$p.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running network-isolated VM required'}
if($null -eq $Session){$sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($sessions.Count -ne 1){throw 'One authenticated lab session required'};$Session=$sessions[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$inventory=Get-Content -LiteralPath (Join-Path $root 'host-inventory.json') -Raw|ConvertFrom-Json
$receiptPath=Join-Path $root 'host-receipt.json'
if((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath (Join-Path $root 'host-stage-1.json')) -or (-not $continuing -and (Test-Path -LiteralPath $p.host_vhd))){throw 'Existing attempt or disk retained; do not rerun'}
$r=[ordered]@{schema='p02-business-baseline-host/1';outcome='running';stage='verify retained VM storage';started=[datetime]::UtcNow.ToString('o');vm_id=$p.vm_id;actions=@();new_disk=$null;guest_before=$null;storage=$null;restore=$null;first_failure=$null;collection_failure=$null;production_operations=0;existing_disks_changed=0}
$journal=@{number=0}
function Write-NewHost([string]$Path,[object]$Value){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 16));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
function Save-Host {$journal.number++;if($journal.number -gt 16){throw 'Host stage limit'};Write-NewHost (Join-Path $root ('host-stage-'+$journal.number+'.json')) $r}
function Assert-RetainedDisks([bool]$WithNew){
 $drives=@(Get-VMHardDiskDrive -VM $vm)
 if($drives.Count -ne (2+[int]$WithNew)){throw 'Unexpected VM attachment count'}
 foreach($expected in $inventory.disks){
  $found=@($drives|Where-Object {$_.Path -ieq $expected.path})
  if($found.Count -ne 1 -or [string]$found[0].ControllerType -cne $expected.controller_type -or $found[0].ControllerNumber -ne $expected.controller_number -or $found[0].ControllerLocation -ne $expected.controller_location){throw 'Original VM attachment changed'}
  $vhd=Get-VHD -Path $found[0].Path
  if([string]$vhd.DiskIdentifier -ine $expected.disk_id -or $vhd.Size -ne $expected.virtual_bytes -or [string]$vhd.VhdType -cne $expected.type -or $vhd.ParentPath -ine $expected.parent_path){throw 'Original disk/checkpoint chain changed'}
 }
 $checkpoints=@(Get-VMSnapshot -VM $vm)
 if($checkpoints.Count -ne 1 -or [string]$checkpoints[0].Id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Original checkpoint must remain retained'}
 if($WithNew){
  $new=@($drives|Where-Object {$_.Path -ieq $p.host_vhd})
  if($new.Count -ne 1 -or [string]$new[0].ControllerType -cne 'SCSI' -or $new[0].ControllerNumber -ne 0 -or $new[0].ControllerLocation -ne 4){throw 'New disk attachment differs'}
 }elseif(@($drives|Where-Object {[string]$_.ControllerType -eq 'SCSI' -and $_.ControllerNumber -eq 0 -and $_.ControllerLocation -eq 4}).Count){throw 'Fresh SCSI slot already occupied'}
}
function Receive-OwnedStage($Job,[int]$Seconds,[string]$Label){
 $watch=[Diagnostics.Stopwatch]::StartNew()
 while($Job.State -in @('NotStarted','Running') -and $watch.Elapsed.TotalSeconds -lt $Seconds){$null=Wait-Job -Job $Job -Timeout 10;Write-Host ($Label+': '+[int]$watch.Elapsed.TotalSeconds+' seconds; original fixtures and checkpoint retained.')}
 $r.job_state=[string]$Job.State
 if($Job.State -ne 'Completed'){
  $r.job_errors=@($Job.ChildJobs|ForEach-Object {[pscustomobject]@{state=[string]$_.State;reason=[string]$_.JobStateInfo.Reason;errors=@($_.Error|ForEach-Object {$_.Exception.Message})}})
  throw 'Guest stage is unresolved; retain job/session and do not rerun'
 }
 $received=@(Receive-Job -Job $Job -Keep)
 if($Job.ChildJobs.Count -ne 1 -or $Job.ChildJobs[0].Error.Count -ne 0 -or $received.Count -ne 1){throw 'Unexpected guest result; retain original stage'}
 return $received[0]
}
Save-Host
try{
 Assert-RetainedDisks $continuing
 if($continuing){
  $retained=Get-VHD -Path $p.host_vhd
  if([string]$retained.DiskIdentifier -ine '702186c1-fafe-4eda-95d8-7abb4c6843f2' -or $retained.Size -ne 128GB -or [string]$retained.VhdType -cne 'Dynamic' -or $retained.ParentPath -or -not $retained.Attached){throw 'Exact retained new VHD must remain attached'}
  $r.new_disk=$original.new_disk;$r.original_host_receipt_sha256=$priorHostHash
  $r.actions+=@([ordered]@{operation='reuse original created and attached disk';acknowledged=$true})
 }
 if((Get-PSDrive C).Free -lt 160GB){throw 'Host reserve for the new disk is unavailable'}
 $r.guest_before=Invoke-Command -Session $Session -ArgumentList $continuing,$directoryContinuing -ScriptBlock {
  param($continuing,$directoryContinuing)
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'MINI_AMD\K98LabAdmin'){throw 'Exact guest identity required'}
  $disks=@(Get-Disk|Select-Object UniqueId,Size,IsBoot,IsSystem,PartitionStyle)
  if($disks.Count -ne (2+[int]$continuing) -or @($disks|Where-Object {$_.UniqueId -ceq '60022480FF55AB6D02F41EDBFA5D57E1' -and $_.Size -eq 120GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480F18852E666A58D834543C4BC' -and $_.Size -eq 416GB}).Count -ne 1 -or (-not $directoryContinuing -and (Test-Path -LiteralPath 'R:\'))){throw 'Original disk identities and expected R drive state required'}
  if($continuing -and @($disks|Where-Object {$_.UniqueId -ceq '60022480C1862170FEFA7ABB4C6843F2' -and $_.Size -eq 128GB}).Count -ne 1){throw 'Exact retained guest disk missing'}
  $disks
 }
 $r.stage='copy sealed fresh restore packet';Save-Host
 $destination=Invoke-Command -Session $Session -ArgumentList $p.guest_directory -ScriptBlock {
  param($path)
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or $path -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or (Test-Path -LiteralPath $path) -or (Get-PSDrive Q).Free -lt 1GB){throw 'Fresh bounded packet directory required'}
  [void][IO.Directory]::CreateDirectory($path)
  [IO.Path]::Combine($path,'packet.zip')
 }
 Copy-Item -LiteralPath $p.archive -Destination $destination -ToSession $Session
 Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$p.archive_sha256 -ScriptBlock {
  param($path,$digest)
  $archive=[IO.Path]::Combine($path,'packet.zip')
  if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -cne $digest){throw 'Guest archive differs'}
  Expand-Archive -LiteralPath $archive -DestinationPath $path
 }
 if(-not $continuing){
 $r.stage='create new 128 GiB disk';$r.actions+=@([ordered]@{operation='create new disk';acknowledged=$false});Save-Host
 $new=New-VHD -Path $p.host_vhd -Dynamic -SizeBytes 128GB
 if($new.Size -ne 128GB -or [string]$new.VhdType -cne 'Dynamic' -or [string]$new.VhdFormat -cne 'VHDX' -or $new.ParentPath){throw 'New VHD acknowledgement differs'}
 $r.new_disk=[ordered]@{path=$new.Path;id=[string]$new.DiskIdentifier;bytes=$new.Size}
 $r.actions[-1].acknowledged=$true;Save-Host
 $r.stage='attach only new disk';$r.actions+=@([ordered]@{operation='attach SCSI 0/4';acknowledged=$false});Save-Host
 Add-VMHardDiskDrive -VM $vm -ControllerType SCSI -ControllerNumber 0 -ControllerLocation 4 -Path $p.host_vhd
 Assert-RetainedDisks $true
 $attached=Get-VHD -Path $p.host_vhd
 if([string]$attached.DiskIdentifier -ine $r.new_disk.id -or $attached.Size -ne 128GB -or -not $attached.Attached){throw 'New attached disk identity differs'}
 $r.actions[-1].acknowledged=$true;Save-Host
 }
 $r.stage=if($continuing){'reconcile and complete retained fresh disk'}else{'initialize only fresh guest disk'};Save-Host
 $global:P02BusinessStorageJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,@('60022480FF55AB6D02F41EDBFA5D57E1','60022480F18852E666A58D834543C4BC') -AsJob -ScriptBlock {
  param($path,$ids)
  $manifest=Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw|ConvertFrom-Json
  $name='qualification/p02_observer/Initialize-P02BusinessDisk.ps1';$entry=Join-Path $path $name
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifest.files.$name){throw 'Sealed storage script differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path -PreviousIds $ids
 }
 $r.storage=Receive-OwnedStage $global:P02BusinessStorageJob 120 'Fresh lab storage'
 Save-Host
 if($r.storage.outcome -cne 'passed'){throw 'Storage stage stopped; retain created disk and do not replay'}
 $r.stage='verify backup and restore only fresh restricted baseline';Save-Host
 $global:P02BusinessRestoreJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$r.storage.sha256 -AsJob -ScriptBlock {
  param($path,$storageHash)
  $manifest=Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw|ConvertFrom-Json
  $name='qualification/p02_observer/Restore-P02BusinessBaseline.ps1';$entry=Join-Path $path $name
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifest.files.$name){throw 'Sealed restore script differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path -StorageSHA256 $storageHash
 }
 $r.restore=Receive-OwnedStage $global:P02BusinessRestoreJob 1200 'Fresh restricted baseline'
 Save-Host
 if($r.restore.outcome -cne 'passed'){throw 'Restore stage stopped; preserve all acknowledged stages without rerunning'}
 Assert-RetainedDisks $true
 $r.outcome='passed';$r.stage='new restricted business fixture ready; original setup, claim and checkpoint preserved'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{
 try{
  if($Session.State -eq 'Opened' -and $Session.Availability -eq 'Available'){
   $files=@(Invoke-Command -Session $Session -ArgumentList $p.guest_directory -ScriptBlock {
    param($path)
    $names=@('storage-receipt.json','guest-receipt.json','before.stdout.txt','before.stderr.txt','after.stdout.txt','after.stderr.txt')
    $names+=@(1..12|ForEach-Object {'storage-stage-'+$_+'.json'})
    $names+=@(1..20|ForEach-Object {'restore-stage-'+$_+'.json'})
    foreach($phase in @('before','after')){$names+=@(($phase+'/receipt.json'),($phase+'/entered.json'));$names+=@(1..10|ForEach-Object {$phase+'/stage-'+$_+'.json'})}
    foreach($name in $names){if(Test-Path -LiteralPath ([IO.Path]::Combine($path,$name))){$name}}
   })
   foreach($group in @('','before/','after/')){
    $selected=@($files|Where-Object {if($group -eq ''){$_ -notmatch '/'}else{$_.StartsWith($group,[StringComparison]::Ordinal)}})
    if($selected.Count){
     $destination=if($group){Join-Path $root $group.TrimEnd('/')}else{$root}
     [void][IO.Directory]::CreateDirectory($destination)
     foreach($name in $selected){if(Test-Path -LiteralPath (Join-Path $root $name)){throw 'Existing collected evidence must not be overwritten'}}
     $remote=@($selected|ForEach-Object {[IO.Path]::Combine($p.guest_directory,$_ )})
     Copy-Item -LiteralPath $remote -FromSession $Session -Destination $destination
    }
   }
  }else{$r.collection_failure='Session unavailable; retained job/session must be reconciled before collection';$r.outcome='failed'}
 }catch{$r.collection_failure=$_.Exception.Message;$r.outcome='failed'}
 $r.finished=[datetime]::UtcNow.ToString('o')
 Write-NewHost $receiptPath $r
}
[pscustomobject]$r|Select-Object outcome,stage,first_failure,collection_failure|Format-List
Write-Host ('Evidence saved: '+$root)
