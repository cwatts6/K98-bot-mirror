#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[Management.Automation.Runspaces.PSSession]$Session,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$p=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
$base='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
$stamp=Split-Path -Leaf $p.guest_directory
if($root -cnotmatch ('^'+[regex]::Escape($base)+'\\cost-fixtures-resume-[0-9]{17}$') -or (Split-Path -Leaf $root) -cne ('cost-fixtures-resume-'+$stamp) -or $p.schema -cne 'p02-cost-fixtures-resume-host/1' -or $p.production_eligible -ne $false -or $p.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $p.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or $p.databases.Count -ne 2 -or $p.databases[0] -cne 'K98_P02Cost_OFF_20261122130322703' -or $p.databases[1] -cne 'K98_P02Cost_ON_20261122130322703' -or $p.host_vhd -cne (Join-Path (Join-Path $base 'cost-fixtures-20261122130322703') 'cost.vhdx') -or $p.new_disk_bytes -ne 256GB -or $p.controller_location -ne 5){throw 'Exact matching-fixture plan required'}
foreach($item in @(@{path=$PSCommandPath;hash=$p.host_sha256},@{path=$p.archive;hash=$p.archive_sha256},@{path=(Join-Path $root 'host-inventory.json');hash=$p.inventory_sha256})){
 $info=Get-Item -LiteralPath $item.path -Force
 if($info.PSIsContainer -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -or (Get-FileHash -LiteralPath $info.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.hash){throw 'Sealed host member differs'}
}
if($p.archive -cne (Join-Path $root 'packet.zip')){throw 'Exact packet archive required'}
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
 if($zip.Entries.Count -gt 1024 -or ($zip.Entries|Measure-Object Length -Sum).Sum -gt 64MB){throw 'Bounded sealed inventory required'}
 $entry=$zip.GetEntry('manifest.json')
 if($null -eq $entry -or $entry.Length -gt 1MB){throw 'Bounded manifest required'}
 $reader=[IO.StreamReader]::new($entry.Open(),[Text.UTF8Encoding]::new($false,$true))
 try{$manifest=$reader.ReadToEnd()|ConvertFrom-Json}finally{$reader.Dispose()}
 if($manifest.purpose -cne 'p02-complete-matching-cost-fixtures' -or $manifest.fixture_stamp -cne '20261122130322703' -or $manifest.production_eligible -ne $false -or $manifest.vm_id -cne $p.vm_id -or $manifest.guest_directory -cne $p.guest_directory -or ($manifest.databases -join '|') -cne ($p.databases -join '|') -or $manifest.new_disk_bytes -ne 256GB -or $manifest.drive_letter -cne 'S' -or $manifest.data_directory -cne 'S:\P02Cost_20261122130322703' -or $manifest.volume_label -cne 'P02_COST_20261122130322703'){throw 'Sealed archive and host plan disagree'}
 if($zip.Entries.Count -ne @($manifest.files.PSObject.Properties).Count+1){throw 'Exact archive inventory required'}
 $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($member in $zip.Entries){
  if(-not $seen.Add($member.FullName) -or $member.Length -gt 16MB -or $member.FullName -match '[:\\\\]' -or $member.FullName.StartsWith('/') -or @($member.FullName.Split('/')|Where-Object {$_ -in @('','.','..')}).Count){throw 'Unsafe or duplicated archive member'}
  if($member.FullName -ceq 'manifest.json'){continue}
  $property=$manifest.files.PSObject.Properties[$member.FullName]
  if($null -eq $property){throw 'Unexpected archive member'}
  $stream=$member.Open();$algorithm=[Security.Cryptography.SHA256]::Create()
  try{$digest=([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}finally{$algorithm.Dispose();$stream.Dispose()}
  if($digest -cne $property.Value){throw 'Sealed archive member differs'}
 }
}finally{$zip.Dispose()}
if((Get-FileHash -LiteralPath (Join-Path (Join-Path $base 'cost-fixtures-20261122130322703') 'host-receipt.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'de807ba5b693366de372b9a43e2104fadb48e2bc7338636e9aba9387fd8356ac'){throw 'Original settled host receipt changed'}
if($ValidateOnly){[pscustomobject]@{validated=$true;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$p.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running network-isolated VM required'}
if($null -eq $Session){$sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($sessions.Count -ne 1){throw 'One authenticated lab session required'};$Session=$sessions[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$inventory=Get-Content -LiteralPath (Join-Path $root 'host-inventory.json') -Raw|ConvertFrom-Json
$receiptPath=Join-Path $root 'host-receipt.json'
if((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath (Join-Path $root 'host-stage-1.json'))){throw 'Existing attempt or disk retained; do not rerun'}
$r=[ordered]@{schema='p02-cost-fixtures-resume-host/1';outcome='running';stage='verify retained VM storage';started=[datetime]::UtcNow.ToString('o');vm_id=$p.vm_id;actions=@();new_disk=$null;guest_before=$null;storage=$null;restore=$null;first_failure=$null;collection_failure=$null;production_operations=0;existing_disks_changed=0}
$journal=@{number=0}
function Write-NewHost([string]$Path,[object]$Value){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 16));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
function Save-Host {$journal.number++;if($journal.number -gt 16){throw 'Host stage limit'};Write-NewHost (Join-Path $root ('host-stage-'+$journal.number+'.json')) $r}
function Assert-RetainedDisks([bool]$WithNew){
 $drives=@(Get-VMHardDiskDrive -VM $vm)
 if($drives.Count -ne 4){throw 'Unexpected VM attachment count'}
 foreach($expected in $inventory.disks){
  $found=@($drives|Where-Object {$_.Path -ieq $expected.path})
  if($found.Count -ne 1 -or [string]$found[0].ControllerType -cne $expected.controller_type -or $found[0].ControllerNumber -ne $expected.controller_number -or $found[0].ControllerLocation -ne $expected.controller_location){throw 'Original VM attachment changed'}
  $vhd=Get-VHD -Path $found[0].Path
  if([string]$vhd.DiskIdentifier -ine $expected.disk_id -or $vhd.Size -ne $expected.virtual_bytes -or [string]$vhd.VhdType -cne $expected.type -or [string]$vhd.ParentPath -ine [string]$expected.parent_path){throw 'Original disk/checkpoint chain changed'}
 }
 $checkpoints=@(Get-VMSnapshot -VM $vm)
 if($checkpoints.Count -ne 1 -or [string]$checkpoints[0].Id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Original checkpoint must remain retained'}
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
 Assert-RetainedDisks $false
 $r.new_disk=[ordered]@{path=$p.host_vhd;id='C2A94828-D1B5-48D0-873F-6F341979C793';bytes=256GB;reused=$true}
 $r.storage=[ordered]@{outcome='passed';sha256='b81f22701ac7775f0b9890b308f7d5cbf12e68c1025f3dadc84684cdb0a32d4f';reused=$true}
 $r.guest_before=Invoke-Command -Session $Session -ScriptBlock {
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'MINI_AMD\K98LabAdmin'){throw 'Exact guest identity required'}
  $disks=@(Get-Disk|Select-Object UniqueId,Size,IsBoot,IsSystem,PartitionStyle)
  if($disks.Count -ne 4 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480FF55AB6D02F41EDBFA5D57E1' -and $_.Size -eq 120GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480F18852E666A58D834543C4BC' -and $_.Size -eq 416GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480C1862170FEFA7ABB4C6843F2' -and $_.Size -eq 128GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '600224802848A9C2B5D16F341979C793' -and $_.Size -eq 256GB -and $_.PartitionStyle -eq 'GPT' -and -not $_.IsBoot -and -not $_.IsSystem}).Count -ne 1){throw 'Exact four retained guest disks required'}
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
 $r.stage='verify completed OFF copy and restore only unfinished ON copy';Save-Host
 $global:P02CostResumeJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$r.storage.sha256 -AsJob -ScriptBlock {
  param($path,$storageHash)
  $manifest=Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw|ConvertFrom-Json
  $name='qualification/p02_observer/Complete-P02CostFixtures.ps1';$entry=Join-Path $path $name
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifest.files.$name){throw 'Sealed restore script differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path -StorageSHA256 $storageHash
 }
 $r.restore=Receive-OwnedStage $global:P02CostResumeJob 1200 'Matching restricted lab copies'
 Save-Host
 if($r.restore.outcome -cne 'passed'){throw 'Restore stage stopped; preserve acknowledged stages without rerunning'}
 Assert-RetainedDisks $true
 $r.outcome='passed';$r.stage='two matching restricted baselines ready; completed work and claim preserved'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{
 try{
  if($Session.State -eq 'Opened' -and $Session.Availability -eq 'Available'){
   $files=@(Invoke-Command -Session $Session -ArgumentList $p.guest_directory -ScriptBlock {
    param($path)
    $names=@('storage-receipt.json','guest-receipt.json','before.stdout.txt','before.stderr.txt','after.stdout.txt','after.stderr.txt','restore-bindings.json','prior-before.json')
    $names+=@(1..16|ForEach-Object {'storage-stage-'+$_+'.json'})
    $names+=@(1..40|ForEach-Object {'restore-stage-'+$_+'.json'})
    foreach($phase in @('before','after')){$names+=@(($phase+'/receipt.json'),($phase+'/entered.json'),($phase+'/progress.json'));$names+=@(1..10|ForEach-Object {$phase+'/stage-'+$_+'.json'})}
    foreach($name in $names){if(Test-Path -LiteralPath ([IO.Path]::Combine($path,$name))){$name}}
   })
   $r.collected_files=$files
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
   if($r.outcome -ceq 'passed'){foreach($required in @('guest-receipt.json','before/receipt.json','after/receipt.json','prior-before.json','restore-bindings.json')){if($required -cnotin $files){throw ('Required collected evidence missing: '+$required)}}}
  }else{$r.collection_failure='Session unavailable; retained job/session must be reconciled before collection';$r.outcome='failed'}
 }catch{$r.collection_failure=$_.Exception.Message;$r.outcome='failed'}
 $r.finished=[datetime]::UtcNow.ToString('o')
 Write-NewHost $receiptPath $r
}
[pscustomobject]$r|Select-Object outcome,stage,first_failure,collection_failure|Format-List
Write-Host ('Evidence saved: '+$root)
