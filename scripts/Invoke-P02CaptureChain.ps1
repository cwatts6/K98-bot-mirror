#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PlanPath,[Management.Automation.Runspaces.PSSession]$Session,[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$p=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
$base='C:\Users\cwatt\.codex\worktrees\p02-observer-proof\discord_file_downloader\.codex_artifacts\p02-observer-proof-20261119'
$stamp=Split-Path -Leaf $p.guest_directory
if($p.capture_route -cne 'player_report'){throw 'Exact player-report capture group required; legacy KVK remains separate'}
if($root -cnotmatch ('^'+[regex]::Escape($base)+'\\poststate-capture-[0-9]{17}$') -or (Split-Path -Leaf $root) -cne ('poststate-capture-'+$stamp) -or $p.schema -cne 'p02-poststate-capture-host/1' -or $p.production_eligible -ne $false -or $p.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $p.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or $p.databases.Count -ne 1 -or $p.databases[0] -cne ('K98_P02CaptureChain_'+$stamp) -or $p.host_vhd -cne (Join-Path $root 'capture-chain.vhdx') -or $p.new_disk_bytes -ne 192GB -or $p.controller_location -ne 6){throw 'Exact matching-fixture plan required'}
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
 if($manifest.capture_route -cne $p.capture_route -or $manifest.purpose -cne 'p02-poststate-capture-chain' -or $manifest.production_eligible -ne $false -or $manifest.vm_id -cne $p.vm_id -or $manifest.guest_directory -cne $p.guest_directory -or ($manifest.databases -join '|') -cne ($p.databases -join '|') -or $manifest.new_disk_bytes -ne 192GB -or $manifest.drive_letter -cne 'T' -or $manifest.data_directory -cne ('T:\P02Capture_'+$stamp) -or $manifest.volume_label -cne ('P02_CAPTURE_'+$stamp)){throw 'Sealed archive and host plan disagree'}
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
if($ValidateOnly){[pscustomobject]@{validated=$true;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$p.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running network-isolated VM required'}
if($null -eq $Session){$sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($sessions.Count -ne 1){throw 'One authenticated lab session required'};$Session=$sessions[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$inventory=Get-Content -LiteralPath (Join-Path $root 'host-inventory.json') -Raw|ConvertFrom-Json
$receiptPath=Join-Path $root 'host-receipt.json'
if((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath (Join-Path $root 'host-stage-1.json')) -or (Test-Path -LiteralPath $p.host_vhd)){throw 'Existing attempt or disk retained; do not rerun'}
$r=[ordered]@{schema='p02-poststate-capture-host/1';outcome='running';stage='verify retained VM storage';started=[datetime]::UtcNow.ToString('o');vm_id=$p.vm_id;actions=@();new_disk=$null;guest_before=$null;storage=$null;restore=$null;first_failure=$null;collection_failure=$null;production_operations=0;existing_disks_changed=0}
$journal=@{number=0}
function Write-NewHost([string]$Path,[object]$Value){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 16));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
function Save-Host {$journal.number++;if($journal.number -gt 24){throw 'Host stage limit'};Write-NewHost (Join-Path $root ('host-stage-'+$journal.number+'.json')) $r}
function Assert-RetainedDisks([bool]$WithNew){
 $drives=@(Get-VMHardDiskDrive -VM $vm)
 if($drives.Count -ne (4+[int]$WithNew)){throw 'Unexpected VM attachment count'}
 foreach($expected in $inventory.disks){
  $found=@($drives|Where-Object {$_.Path -ieq $expected.path})
  if($found.Count -ne 1 -or [string]$found[0].ControllerType -cne $expected.controller_type -or $found[0].ControllerNumber -ne $expected.controller_number -or $found[0].ControllerLocation -ne $expected.controller_location){throw 'Original VM attachment changed'}
  $vhd=Get-VHD -Path $found[0].Path
  if([string]$vhd.DiskIdentifier -ine $expected.disk_id -or $vhd.Size -ne $expected.virtual_bytes -or [string]$vhd.VhdType -cne $expected.type -or [string]$vhd.ParentPath -ine [string]$expected.parent_path){throw 'Original disk/checkpoint chain changed'}
 }
 $checkpoints=@(Get-VMSnapshot -VM $vm)
 if($checkpoints.Count -ne 1 -or [string]$checkpoints[0].Id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Original checkpoint must remain retained'}
 if($WithNew){
  $new=@($drives|Where-Object {$_.Path -ieq $p.host_vhd})
  if($new.Count -ne 1 -or [string]$new[0].ControllerType -cne 'SCSI' -or $new[0].ControllerNumber -ne 0 -or $new[0].ControllerLocation -ne 6){throw 'New disk attachment differs'}
 }elseif(@($drives|Where-Object {[string]$_.ControllerType -eq 'SCSI' -and $_.ControllerNumber -eq 0 -and $_.ControllerLocation -eq 6}).Count){throw 'Fresh SCSI slot already occupied'}
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
function Start-OwnedPython([string]$Entry,[string]$Argument,[string]$Label,[int]$Seconds){
 $global:P02CaptureChainJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$Entry,$Argument,$Label,$Seconds -AsJob -ScriptBlock {
  param($path,$entryName,$argument,$label,$seconds)
  if($entryName -cnotin @('poststate_preservation.py','poststate_chain.py') -or $label -cnotin @('preflight','integration') -or (Test-Path -LiteralPath (Join-Path $path ($label+'.launch.json')))){throw 'Fresh declared child required'}
  $manifest=Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw|ConvertFrom-Json
  $member='qualification/p02_observer/'+$entryName;$entry=Join-Path $path $member
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifest.files.$member){throw 'Sealed child differs'}
  if(($label -ceq 'preflight' -and $argument -cne 'before') -or ($label -ceq 'integration' -and $argument -cnotmatch '^[0-9a-f]{64}$')){throw 'Exact child argument required'}
  $arguments='-I -S -B "'+$entry+'" '+$argument
  $process=Start-Process -FilePath 'C:\Program Files\Python311\python.exe' -ArgumentList $arguments -WorkingDirectory $path -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $path ($label+'.stdout.txt')) -RedirectStandardError (Join-Path $path ($label+'.stderr.txt'))
  $global:P02CaptureChainHeldProcess=$process;$handle=$process.Handle
  $watch=[Diagnostics.Stopwatch]::StartNew()
  while(-not $process.WaitForExit(1000) -and $watch.Elapsed.TotalSeconds -lt $seconds){}
  $run=[ordered]@{pid=$process.Id;role=$label;settled=$process.HasExited;exit_code=$null;outcome='retained-running';receipt=$null;receipt_sha256=$null}
  if($process.HasExited){
   $process.WaitForExit();$run.exit_code=$process.ExitCode;$process.Dispose();$global:P02CaptureChainHeldProcess=$null
   $relative=if($label -ceq 'preflight'){'before/receipt.json'}else{'integration/receipt.json'}
   $receiptPath=Join-Path $path $relative
   if(Test-Path -LiteralPath $receiptPath){
    $value=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
    $run.receipt=$relative;$run.receipt_sha256=(Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $run.outcome=if($run.exit_code -eq 0 -and $value.outcome -ceq 'passed' -and -not $value.first_failure -and $value.cleanup_failures.Count -eq 0 -and -not $value.physical_custody_retained){'passed'}else{'failed'}
   }else{$run.outcome='failed-no-receipt'}
  }
  [IO.File]::WriteAllText((Join-Path $path ($label+'.launch.json')),($run|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
  [pscustomobject]$run
 }
 return (Receive-OwnedStage $global:P02CaptureChainJob ($Seconds+30) $Label)
}
Save-Host
try{
 Assert-RetainedDisks $false
 if((Get-PSDrive C).Free -lt 256GB){throw 'Host reserve for separate lab storage unavailable'}
 $r.guest_before=Invoke-Command -Session $Session -ScriptBlock {
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'MINI_AMD\K98LabAdmin'){throw 'Exact guest identity required'}
  $disks=@(Get-Disk|Select-Object UniqueId,Size,IsBoot,IsSystem,PartitionStyle)
  if($disks.Count -ne 4 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480FF55AB6D02F41EDBFA5D57E1' -and $_.Size -eq 120GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480F18852E666A58D834543C4BC' -and $_.Size -eq 416GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480C1862170FEFA7ABB4C6843F2' -and $_.Size -eq 128GB}).Count -ne 1 -or @($disks|Where-Object {$_.UniqueId -ceq '600224802848A9C2B5D16F341979C793' -and $_.Size -eq 256GB}).Count -ne 1 -or (Test-Path -LiteralPath 'T:\')){throw 'Exact four retained guest disks and unused T drive required'}
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
 $r.stage='read-only preservation, genuine report source and legacy season census';Save-Host
 $r.preflight=Start-OwnedPython 'poststate_preservation.py' 'before' 'preflight' 180;Save-Host
 if($r.preflight.outcome -cne 'passed'){throw 'Preflight stopped before storage creation; preserve the original result'}
 $r.stage='create new 192 GiB disk';$r.actions+=@([ordered]@{operation='create new disk';acknowledged=$false});Save-Host
 $new=New-VHD -Path $p.host_vhd -Dynamic -SizeBytes 192GB
 if($new.Size -ne 192GB -or [string]$new.VhdType -cne 'Dynamic' -or [string]$new.VhdFormat -cne 'VHDX' -or $new.ParentPath){throw 'New VHD acknowledgement differs'}
 $r.new_disk=[ordered]@{path=$new.Path;id=[string]$new.DiskIdentifier;bytes=$new.Size}
 $r.actions[-1].acknowledged=$true;Save-Host
 $r.stage='attach only new disk';$r.actions+=@([ordered]@{operation='attach SCSI 0/6';acknowledged=$false});Save-Host
 Add-VMHardDiskDrive -VM $vm -ControllerType SCSI -ControllerNumber 0 -ControllerLocation 6 -Path $p.host_vhd
 Assert-RetainedDisks $true
 $attached=Get-VHD -Path $p.host_vhd
 if([string]$attached.DiskIdentifier -ine $r.new_disk.id -or $attached.Size -ne 192GB -or -not $attached.Attached){throw 'New attached disk identity differs'}
 $r.actions[-1].acknowledged=$true;Save-Host
 $r.stage='initialize only new capture-chain disk';Save-Host
 $global:P02CaptureStorageJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,@('60022480FF55AB6D02F41EDBFA5D57E1','60022480F18852E666A58D834543C4BC','60022480C1862170FEFA7ABB4C6843F2','600224802848A9C2B5D16F341979C793') -AsJob -ScriptBlock {
  param($path,$ids)
  $manifest=Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw|ConvertFrom-Json
  $name='qualification/p02_observer/Initialize-P02CaptureDisk.ps1';$entry=Join-Path $path $name
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifest.files.$name){throw 'Sealed storage script differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path -PreviousIds $ids
 }
 $r.storage=Receive-OwnedStage $global:P02CaptureStorageJob 150 'New lab storage'
 Save-Host
 if($r.storage.outcome -cne 'passed'){throw 'Storage stage stopped; retain created disk without replay'}
 $r.stage='verify backup and restore one new restricted fixture';Save-Host
 $global:P02CaptureRestoreJob=Invoke-Command -Session $Session -ArgumentList $p.guest_directory,$r.storage.sha256,$r.preflight.receipt_sha256 -AsJob -ScriptBlock {
  param($path,$storageHash,$beforeHash)
  $manifest=Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw|ConvertFrom-Json
  $name='qualification/p02_observer/Restore-P02CaptureFixture.ps1';$entry=Join-Path $path $name
  if((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifest.files.$name){throw 'Sealed restore script differs'}
  & ([scriptblock]::Create([IO.File]::ReadAllText($entry))) -PacketRoot $path -StorageSHA256 $storageHash -BeforeSHA256 $beforeHash
 }
 $r.restore=Receive-OwnedStage $global:P02CaptureRestoreJob 1200 'New restricted capture fixture'
 Save-Host
 if($r.restore.outcome -cne 'passed'){throw 'Restore stage stopped; preserve acknowledged stages without rerunning'}
 Assert-RetainedDisks $true
 $bindingSHA=Invoke-Command -Session $Session -ArgumentList $p.guest_directory -ScriptBlock {param($path) (Get-FileHash -LiteralPath (Join-Path $path 'restore-bindings.json') -Algorithm SHA256).Hash.ToLowerInvariant()}
 $r.restore_bindings_sha256=$bindingSHA;$r.stage='genuine observer installation and declared capture-chain roles';Save-Host
 $r.integration=Start-OwnedPython 'poststate_chain.py' $bindingSHA 'integration' 2000;Save-Host
 if($r.integration.outcome -cne 'passed'){throw 'Integration stopped; retain all committed stages and original custody without replay'}
 Assert-RetainedDisks $true
 $r.outcome='passed';$r.stage='capture-chain group completed; original work preserved; full release acceptance remains separate'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{
 try{
  if($Session.State -eq 'Opened' -and $Session.Availability -eq 'Available'){
   $files=@(Invoke-Command -Session $Session -ArgumentList $p.guest_directory -ScriptBlock {
    param($path)
    $names=@('preflight.launch.json','preflight.stdout.txt','preflight.stderr.txt','integration.launch.json','integration.stdout.txt','integration.stderr.txt','chain-initial-contracts.json','chain-contracts-0.json','chain-contracts-1.json','chain-contracts-2.json','chain-consumer-contracts.json','protected-tool-observation.json','chain-captures.json','chain-bound-contracts.json','chain-workload.stdout.txt','chain-workload.stderr.txt','chain-tool.stdout.txt','chain-tool.stderr.txt','chain-consumer.stdout.txt','chain-consumer.stderr.txt','coordinator-Status.stdout.txt','coordinator-Status.stderr.txt','coordinator-Preflight.stdout.txt','coordinator-Preflight.stderr.txt','coordinator-Apply.stdout.txt','coordinator-Apply.stderr.txt','coordinator-Verify.stdout.txt','coordinator-Verify.stderr.txt','storage-receipt.json','guest-receipt.json','before.stdout.txt','before.stderr.txt','after.stdout.txt','after.stderr.txt','restore-bindings.json')
    $names+=@(1..16|ForEach-Object {'storage-stage-'+$_+'.json'})
    $names+=@(1..40|ForEach-Object {'restore-stage-'+$_+'.json'})
    foreach($phase in @('before','after','integration','chain-workload','chain-tool','chain-consumer')){$names+=@(($phase+'/receipt.json'),($phase+'/entered.json'),($phase+'/progress.json'));$names+=@(1..10|ForEach-Object {$phase+'/stage-'+$_+'.json'})}
    foreach($name in $names){if(Test-Path -LiteralPath ([IO.Path]::Combine($path,$name))){$name}}
   })
   foreach($group in @('','before/','after/','integration/','chain-workload/','chain-tool/','chain-consumer/')){
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
