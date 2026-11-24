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
if($root -cnotmatch ('^'+[regex]::Escape($base)+'\\poststate-capture-[0-9]{17}$') -or (Split-Path -Leaf $root) -cne ('poststate-capture-'+$stamp) -or $p.schema -cne 'p02-poststate-capture-continuation-host/1' -or $p.production_eligible -ne $false -or $p.vm_id -cne '2ac1b401-7076-4965-af71-de36ee0f9f9c' -or $p.guest_directory -cnotmatch '^Q:\\P02Observer\\[0-9]{17}$' -or $p.databases.Count -ne 1 -or $p.databases[0] -cne 'K98_P02CaptureChain_20261123150616134' -or $p.host_vhd -cne (Join-Path $base 'poststate-capture-20261123150616134\capture-chain.vhdx') -or $p.new_disk_bytes -ne 0 -or $p.controller_location -ne 6){throw 'Exact matching-fixture plan required'}
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
 if($manifest.continuation -cne 'captured-index-diagnosed-20261123170039650' -or $manifest.capture_route -cne $p.capture_route -or $manifest.purpose -cne 'p02-poststate-capture-chain' -or $manifest.production_eligible -ne $false -or $manifest.vm_id -cne $p.vm_id -or $manifest.guest_directory -cne $p.guest_directory -or ($manifest.databases -join '|') -cne ($p.databases -join '|') -or $manifest.new_disk_bytes -ne 0 -or $manifest.drive_letter -cne 'T' -or $manifest.data_directory -cne 'T:\P02Capture_20261123150616134' -or $manifest.volume_label -cne 'P02_CAPTURE_20261123150616134'){throw 'Sealed archive and host plan disagree'}
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
$prior=Join-Path $base 'poststate-capture-20261123150616134'
foreach($item in @(@{name='host-receipt.json';sha='9d3c07be743b4a329c3a3e59dbf4b06a8957d01be5632fd27306c13e0fd2d642'},@{name='packet.zip';sha='5014ff4672bc2e9066551e787d328c06ea955be1ad1c46dc3120e68499108add'},@{name='integration/receipt.json';sha='bd62aad4691aa1755c8dc2ce3857a23202ef787605387db6a4294d6764a7603e'})){
 if((Get-FileHash -LiteralPath (Join-Path $prior $item.name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha){throw 'Original completed setup evidence changed'}
}
$installed=Join-Path $base 'poststate-capture-20261123160455336'
foreach($item in @(@{name='host-receipt.json';sha='bc0e8ad5fee3162f3b5b82218f84676ed40e04215cbdfd207fd1b591a947fb64'},@{name='packet.zip';sha='d0b8c5ef5eb57f00f00562c1fa011215f61750515223d87634dd81cbc74b60a8'},@{name='integration/receipt.json';sha='024ebf97af740212784cc8a1bd4295f5c471526b99c6adf81a2e718454f490dd'})){
 if((Get-FileHash -LiteralPath (Join-Path $installed $item.name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha){throw 'Original committed observer evidence changed'}
}
$captured=Join-Path $base 'poststate-capture-20261123163556234'
foreach($item in @(@{name='host-receipt.json';sha='439dcdbdd4195e42ebd237da523f484f53f26c19a10136993a2e834a59553dd2'},@{name='packet.zip';sha='2684cd4495c7a64c816d7e2522a2202b4554108f23487e324353e4162852c048'},@{name='integration/receipt.json';sha='ffe605edac43205d5e286c516b1e917e981d2a64276608538d48beb8e6254137'})){
 if((Get-FileHash -LiteralPath (Join-Path $captured $item.name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha){throw 'Completed publication and capture evidence changed'}
}
$diagnostic=Join-Path $base 'poststate-capture-20261123170039650'
foreach($item in @(@{name='host-receipt.json';sha='0c4c47f88a6528c53c2969c1d4976d97a090f60fa7a1e50e188a1ee32783c298'},@{name='packet.zip';sha='c91b2c0c36048705235ac606969300aafef8a90479539fd751b7b6fc25dc59ae'},@{name='integration/receipt.json';sha='0fab868bf606d6f3dc82c0c09a67cf630b19b2242c849072e12ab2088274659e'},@{name='index-diagnostic-before.json';sha='6501d0beeb035dab25d7f11c7857c4dbd2e94530c4ef3e7912fc738ac3965131'})){
 if((Get-FileHash -LiteralPath (Join-Path $diagnostic $item.name) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha){throw 'Original failed diagnostic evidence changed'}
}
if($ValidateOnly){[pscustomobject]@{validated=$true;native_actions=0};return}
if($env:COMPUTERNAME -cne '9SX2VF4' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5 -or -not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Existing elevated Windows PowerShell 5.1 console required'}
$vm=Get-VM -Id ([guid]$p.vm_id)
if($vm.Name -cne 'K98-MGE-Qualification-20261029' -or [string]$vm.State -cne 'Running' -or @(Get-VMNetworkAdapter -VM $vm).Count -ne 0){throw 'Exact running network-isolated VM required'}
if($null -eq $Session){$sessions=@(Get-PSSession|Where-Object {$_.VMId -eq $vm.Id -and $_.State -eq 'Opened' -and $_.Availability -eq 'Available'});if($sessions.Count -ne 1){throw 'One authenticated lab session required'};$Session=$sessions[0]}
if($Session.VMId -ne $vm.Id -or $Session.State -ne 'Opened' -or $Session.Availability -ne 'Available'){throw 'Exact available lab session required'}
$inventory=Get-Content -LiteralPath (Join-Path $root 'host-inventory.json') -Raw|ConvertFrom-Json
$receiptPath=Join-Path $root 'host-receipt.json'
if((Test-Path -LiteralPath $receiptPath) -or (Test-Path -LiteralPath (Join-Path $root 'host-stage-1.json'))){throw 'Existing attempt or disk retained; do not rerun'}
$r=[ordered]@{schema='p02-poststate-capture-continuation-host/1';outcome='running';stage='verify all five retained disks';started=[datetime]::UtcNow.ToString('o');vm_id=$p.vm_id;actions=@();new_disk=$null;guest_before=$null;storage=$null;restore=$null;first_failure=$null;collection_failure=$null;production_operations=0;existing_disks_changed=0}
$journal=@{number=0}
function Write-NewHost([string]$Path,[object]$Value){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 16));$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
function Save-Host {$journal.number++;if($journal.number -gt 24){throw 'Host stage limit'};Write-NewHost (Join-Path $root ('host-stage-'+$journal.number+'.json')) $r}
function Assert-RetainedDisks {
 $drives=@(Get-VMHardDiskDrive -VM $vm)
 if($drives.Count -ne 5 -or $inventory.disks.Count -ne 5){throw 'Exact five retained disks required'}
 foreach($expected in $inventory.disks){
  $found=@($drives|Where-Object {$_.Path -ieq $expected.path})
  if($found.Count -ne 1 -or [string]$found[0].ControllerType -cne $expected.controller_type -or $found[0].ControllerNumber -ne $expected.controller_number -or $found[0].ControllerLocation -ne $expected.controller_location){throw 'Retained VM attachment changed'}
  $vhd=Get-VHD -Path $found[0].Path
  if([string]$vhd.DiskIdentifier -ine $expected.disk_id -or $vhd.Size -ne $expected.virtual_bytes -or [string]$vhd.VhdType -cne $expected.type -or [string]$vhd.ParentPath -ine [string]$expected.parent_path){throw 'Retained disk identity changed'}
 }
 $checkpoints=@(Get-VMSnapshot -VM $vm)
 if($checkpoints.Count -ne 1 -or [string]$checkpoints[0].Id -cne '125272d0-20b7-4705-908f-d3debc71bce2'){throw 'Original checkpoint changed'}
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
 Assert-RetainedDisks
 $r.guest_before=Invoke-Command -Session $Session -ScriptBlock {
  if($env:COMPUTERNAME -cne 'MINI_AMD' -or [Security.Principal.WindowsIdentity]::GetCurrent().Name -ine 'MINI_AMD\K98LabAdmin'){throw 'Exact guest identity required'}
  $disks=@(Get-Disk|Select-Object UniqueId,Size,IsBoot,IsSystem,PartitionStyle)
  if($disks.Count -ne 5 -or @($disks|Where-Object {$_.UniqueId -ceq '60022480DC8C3B8A958A0BBF7B0080C2' -and $_.Size -eq 192GB}).Count -ne 1){throw 'Acknowledged capture disk changed'}
  $partition=Get-Partition -DriveLetter T
  $disk=Get-Disk -Number $partition.DiskNumber
  if($disk.UniqueId -cne '60022480DC8C3B8A958A0BBF7B0080C2' -or -not (Test-Path -LiteralPath 'T:\P02Capture_20261123150616134\CHAIN.mdf')){throw 'Retained capture volume differs'}
  $disks
 }
 $r.stage='copy sealed continuation packet';Save-Host
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
 $r.restore_bindings_sha256='6a1a28edfc2585c42ce316f8a00fd28100107eb29851e2566749d6522bf3bcaa'
 $r.stage='reconcile retained publication and capture, then finish remaining index and capture roles';Save-Host
 $r.integration=Start-OwnedPython 'poststate_chain.py' $r.restore_bindings_sha256 'integration' 2000;Save-Host
 if($r.integration.outcome -cne 'passed'){throw 'Continuation stopped; retain committed stages and original custody without replay'}
 Assert-RetainedDisks
 $r.outcome='passed';$r.stage='capture continuation completed; original work preserved; full release acceptance remains separate'
}catch{$r.outcome='failed';$r.first_failure=[ordered]@{stage=$r.stage;type=$_.Exception.GetType().FullName;detail=$_.Exception.Message}}
finally{
 try{
  if($Session.State -eq 'Opened' -and $Session.Availability -eq 'Available'){
   $files=@(Invoke-Command -Session $Session -ArgumentList $p.guest_directory -ScriptBlock {
    param($path)
    $names=@('captured-resume-before.json','preflight.launch.json','preflight.stdout.txt','preflight.stderr.txt','integration.launch.json','integration.stdout.txt','integration.stderr.txt','chain-initial-contracts.json','publisher-before.json','publisher-after.json','chain-contracts-0.json','chain-contracts-1.json','chain-contracts-2.json','chain-consumer-contracts.json','protected-tool-observation.json','chain-captures.json','chain-bound-contracts.json','chain-workload.stdout.txt','chain-workload.stderr.txt','chain-tool.stdout.txt','chain-tool.stderr.txt','chain-consumer.stdout.txt','chain-consumer.stderr.txt','coordinator-Status.stdout.txt','coordinator-Status.stderr.txt','coordinator-Preflight.stdout.txt','coordinator-Preflight.stderr.txt','coordinator-Apply.stdout.txt','coordinator-Apply.stderr.txt','coordinator-Verify.stdout.txt','coordinator-Verify.stderr.txt','storage-receipt.json','guest-receipt.json','before.stdout.txt','before.stderr.txt','after.stdout.txt','after.stderr.txt','restore-bindings.json')
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
