# Packaged with an exact predecessor inventory; never an arbitrary recursive repair.
[CmdletBinding()]
param([ValidateSet('Check','Repair','Verify','Library')][string]$Action='Check')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function Resolve-RepairEntry([string]$Root,[string]$Name) {
 if($Name -match '[\\:*?"<>|]' -or $Name.StartsWith('/') -or @($Name.Split('/')|Where-Object {$_ -in @('','.','..')}).Count){throw 'Unsafe repair relative path'}
 $result=[IO.Path]::GetFullPath((Join-Path $Root $Name))
 if(-not $result.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Repair entry escaped fixed root'}
 return $result
}
function Assert-RepairAcl([string]$Path,[bool]$Directory,[bool]$Fresh,[string]$Expected='') {
 $item=Get-Item -LiteralPath $Path -Force
 if($item.PSIsContainer -ne $Directory -or [long]$item.Attributes -ne $(if($Directory){16}else{32})){throw ('Repair type/attributes differ: '+$Path)}
 $acl=Get-Acl -LiteralPath $Path
 if($null -eq ([Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)).DiscretionaryAcl){throw 'Null repair DACL'}
 $sections=[Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group -bor [Security.AccessControl.AccessControlSections]::Access
 if(-not $Fresh){if($acl.GetSecurityDescriptorSddlForm($sections) -cne $Expected){throw ('Original repair permissions changed: '+$Path)};return}
 if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -cne 'S-1-5-32-544' -or -not $acl.AreAccessRulesProtected -or $acl.GetGroup([Security.Principal.SecurityIdentifier]).Value -cne $plan.sid){throw 'Fresh repair ownership/protection differs'}
 $rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
 if($rules.Count -ne 3){throw 'Fresh repair ACL inventory differs'}
 foreach($sid in @('S-1-5-18','S-1-5-32-544',$plan.sid)) {
  $rule=@($rules|Where-Object {$_.IdentityReference.Value -ceq $sid})
  $rights=if($sid -ceq $plan.sid){1179817}else{2032127}
  $inherit=if($Directory){3}else{0}
  if($rule.Count -ne 1 -or [long]$rule[0].FileSystemRights -ne $rights -or $rule[0].AccessControlType -ne 'Allow' -or [int]$rule[0].InheritanceFlags -ne $inherit -or [int]$rule[0].PropagationFlags -ne 0 -or $rule[0].IsInherited){throw 'Fresh repair access differs'}
 }
 Assert-Protected $Path
}
function Get-RepairImage([string]$Root,[bool]$Fresh,$Receipt=$null,[switch]$IncludeBytes) {
 Assert-Protected (Split-Path -Parent $Root)
 $handles=[Collections.Generic.List[IDisposable]]::new()
 $rows=[Collections.Generic.List[object]]::new()
 try {
  $handles.Add((Open-SourceCustodyHandle $Root $true))
  Assert-RepairAcl $Root $true $Fresh $plan.root_sddl
  $expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
  foreach($entry in $plan.entries){if(-not $expected.Add($entry.path)){throw 'Duplicate repair entry'}}
  $observed=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
  $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($Root)
  while($queue.Count) {
   $parent=$queue.Dequeue()
   foreach($path in [IO.Directory]::EnumerateFileSystemEntries($parent)) {
    $name=$path.Substring($Root.Length+1).Replace('\','/')
    if(-not $expected.Contains($name) -or -not $observed.Add($name)){throw ('Unexpected repair entry: '+$name)}
    $entry=@($plan.entries|Where-Object {$_.path -ceq $name})[0]
    $handles.Add((Open-SourceCustodyHandle $path ([bool]$entry.directory)))
    Assert-RepairAcl $path ([bool]$entry.directory) $Fresh $entry.sddl
    if($entry.directory){$queue.Enqueue($path);continue}
    if(@(Get-Item -LiteralPath $path -Stream *|Where-Object {$_.Stream -cne ':$DATA'}).Count){throw ('Alternate stream refused: '+$name)}
    $item=Get-Item -LiteralPath $path -Force
    if($item.Length -gt 2MB){throw 'Repair member exceeds bound'}
    $raw=[IO.File]::ReadAllBytes($path);$digest=Hash $raw
    if($digest -cnotin @($entry.hashes)){throw ('Repair source differs from installed Git: '+$name)}
    if($null -ne $Receipt) {
     $saved=@($Receipt.files|Where-Object {$_.path -ceq $name})
     if($saved.Count -ne 1 -or $saved[0].sha256 -cne $digest -or [long]$saved[0].last_write -ne $item.LastWriteTimeUtc.Ticks){throw ('Repair verification differs: '+$name)}
    }
    $row=[ordered]@{path=$name;sha256=$digest;length=$raw.Length;created=$item.CreationTimeUtc.Ticks;last_write=$item.LastWriteTimeUtc.Ticks;last_access=$item.LastAccessTimeUtc.Ticks}
    if($IncludeBytes){$row.bytes=$raw}
    $rows.Add([pscustomobject]$row)
   }
  }
  if($observed.Count -ne $expected.Count){throw 'Missing repair entries'}
  return ,$rows.ToArray()
 }finally{foreach($handle in $handles){$handle.Dispose()}}
}
function New-RepairAcl([bool]$Directory) {
 $acl=New-Acl $Directory
 $acl.SetGroup([Security.Principal.SecurityIdentifier]::new($plan.sid))
 return $acl
}
function Initialize-RepairDirectory([string]$Path) {
 if($Path -cne $fresh -and -not $Path.StartsWith($fresh+'\',[StringComparison]::Ordinal)){throw 'Staging directory escaped repair tree'}
 Assert-Protected (Split-Path -Parent $Path)
 if(-not(Test-Path -LiteralPath $Path)){$null=[IO.Directory]::CreateDirectory($Path,(New-RepairAcl $true))}
 # A crash can occur between native creation and attribute preservation. Resume
 # only the independently protected fresh directory and this known inherited bit.
 Assert-Protected $Path
 if([long](Get-Item -LiteralPath $Path -Force).Attributes -notin @(16,8208)){throw 'Unexpected staging directory attributes'}
 [IO.File]::SetAttributes($Path,[IO.FileAttributes]::Directory)
 Assert-RepairAcl $Path $true $true
}
function Move-RepairTree([string]$From,[string]$To) {
 # Only the two manifest-bound same-volume moves below call this function.
 $allowed=($From -ceq $live -and $To -ceq $backup) -or ($From -ceq $fresh -and $To -ceq $live)
 if(-not $allowed -or [IO.Path]::GetPathRoot($From) -cne [IO.Path]::GetPathRoot($To)){throw 'Unrecognized repair move'}
 Assert-Protected (Split-Path -Parent $From);Assert-Protected (Split-Path -Parent $To)
 if(Test-Path -LiteralPath $To){throw 'Repair move destination already exists'}
 [IO.Directory]::Move($From,$To)
}
function Read-RepairReceipt([string]$Name) {
 $saved=Read-Json (Join-Path $state $Name)
 if($saved.plan_sha256 -cne $planHash -or $saved.before -cne $plan.before){throw 'Repair receipt identity differs'}
 return $saved
}
function Invoke-DocumentationRepair {
 Assert-Protected (Split-Path -Parent $live)
 Assert-Protected (Split-Path -Parent $state)
 if(-not(Test-Path -LiteralPath $state)){New-Directory $state}
 Assert-Protected $state
 $preparedPath=Join-Path $state 'prepared.json';$intentPath=Join-Path $state 'swap-intent.json';$completePath=Join-Path $state 'complete.json'
 if(Test-Path -LiteralPath $completePath) {
  $null=Read-RepairReceipt 'complete.json';$receipt=Read-RepairReceipt 'prepared.json'
  $null=Get-RepairImage $live $true $receipt
  Write-Host 'REPAIR ALREADY VERIFIED. No tree changes.';return
 }
 if(-not(Test-Path -LiteralPath $preparedPath)) {
  if((Test-Path -LiteralPath $backup) -or (Test-Path -LiteralPath $intentPath)){throw 'Repair journal incomplete; preserve all evidence'}
  $rows=Get-RepairImage $live $false -IncludeBytes
  Initialize-RepairDirectory $fresh
  foreach($entry in @($plan.entries|Where-Object {$_.directory}|Sort-Object path)) {
   $path=Resolve-RepairEntry $fresh $entry.path
   Assert-Protected (Split-Path -Parent $path)
   Initialize-RepairDirectory $path
  }
  foreach($row in $rows) {
   $path=Resolve-RepairEntry $fresh $row.path
   if(-not(Test-Path -LiteralPath $path)) {
    $pending=Join-Path $state ('pending-'+[guid]::NewGuid().ToString('N'))
    Write-SourceCopy $pending $row.bytes (New-RepairAcl $false)
    [IO.File]::SetAttributes($pending,[IO.FileAttributes]::Archive)
    [IO.File]::SetCreationTimeUtc($pending,[datetime]::new([long]$row.created,[DateTimeKind]::Utc))
    [IO.File]::SetLastWriteTimeUtc($pending,[datetime]::new([long]$row.last_write,[DateTimeKind]::Utc))
    [IO.File]::SetLastAccessTimeUtc($pending,[datetime]::new([long]$row.last_access,[DateTimeKind]::Utc))
    Assert-RepairAcl $pending $false $true
    $null=Read-Bytes $pending $row.sha256 2MB
    Assert-Protected (Split-Path -Parent $path)
    [IO.File]::Move($pending,$path)
   }
   Assert-RepairAcl $path $false $true
  }
  $receipt=[pscustomobject]@{plan_sha256=$planHash;before=$plan.before;files=@($rows|Select-Object path,sha256,length,created,last_write,last_access)}
  $null=Get-RepairImage $fresh $true $receipt
  Write-AtomicRecord $preparedPath $receipt
 }
 $receipt=Read-RepairReceipt 'prepared.json'
 if(-not(Test-Path -LiteralPath $intentPath)) {
  if(Test-Path -LiteralPath $backup){throw 'Unexpected original archive without swap intent'}
  $null=Get-RepairImage $live $false $receipt
  $null=Get-RepairImage $fresh $true $receipt
  Write-AtomicRecord $intentPath @{plan_sha256=$planHash;before=$plan.before;stage='swap-authorized'}
 }
 $intent=Read-RepairReceipt 'swap-intent.json'
 if($intent.stage -cne 'swap-authorized'){throw 'Unexpected swap stage'}
 if(-not(Test-Path -LiteralPath $backup)) {
  $null=Get-RepairImage $live $false $receipt
  $null=Get-RepairImage $fresh $true $receipt
  Move-RepairTree $live $backup
 }
 # The archive is retained evidence, never a source of trusted repair bytes.
 if(-not(Test-Path -LiteralPath $live)) {
  $null=Get-RepairImage $fresh $true $receipt
  Move-RepairTree $fresh $live
 } elseif(Test-Path -LiteralPath $fresh){throw 'Ambiguous live/staged repair trees; no overwrite permitted'}
 $null=Get-RepairImage $live $true $receipt
 Write-AtomicRecord $completePath @{plan_sha256=$planHash;before=$plan.before;stage='verified';files=$receipt.files.Count;verified_utc=[datetime]::UtcNow.ToString('o')}
 Write-Host 'REPAIR VERIFIED. Exact source bytes retained; original tree archived; no Bot/SQL/restart change.'
}
function Test-DrySourceMember($Member) {
 $path=Source-MemberPath $Member.path
 Assert-ParentSpelling $Member.path
 if($Member.added){if(Test-Path -LiteralPath $path){throw 'New tracked path already exists'};return 'New member path is clear'}
 Assert-Protected (Split-Path -Parent $path)
 $handle=Open-SourceCustodyHandle $path $false
 try {
  Assert-SourcePreimage $path $Member.before_sha256
  $acl=Get-Acl -LiteralPath $path
  $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
  $owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
  if($null -eq ([Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)).DiscretionaryAcl){throw 'Source null DACL'}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
   if($ace.AccessControlType -eq 'Allow' -and $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band 0x500d0156) -ne 0){throw 'Untrusted source write rights'}
  }
  if($owner -in $trusted){Assert-Protected $path;return 'Protected authenticated source'}
  if($owner -cne $c.sid -or $null -ne $c.old_pins.PSObject.Properties[$Member.path]){throw 'Source owner is not eligible for automatic custody'}
  if(@(Get-Item -LiteralPath $path -Stream *|Where-Object {$_.Stream -cne ':$DATA'}).Count -or ([long](Get-Item -LiteralPath $path).Attributes -band (-bnot 0x20a6)) -ne 0){throw 'Source streams/attributes refuse automatic custody'}
  return 'Authenticated file eligible for the existing updater custody step; no change made by this check'
 }finally{$handle.Dispose()}
}
function Invoke-ReadinessGate([string]$Name,[scriptblock]$Check) {
 $row=[ordered]@{name=$Name;status='FAIL';detail=$null}
 try {$detail=& $Check;$row.status='PASS';$row.detail=($detail|Out-String).Trim()}
 catch {$row.detail=$_.Exception.Message}
 $script:readiness.Add([pscustomobject]$row)
}
function Get-DocumentationReadiness {
 $script:readiness=[Collections.Generic.List[object]]::new()
 Invoke-ReadinessGate 'SQL preflight and migration receipts' {$null=Invoke-UpdateSql 'Preflight' ''}
 Invoke-ReadinessGate 'Predecessor policy, flags, journal and gate' {Assert-Predecessor}
 Invoke-ReadinessGate 'Retained preparations, ownership and provider stream closure' {Assert-Held}
 Invoke-ReadinessGate 'Git metadata, clean private main and existing source pins' {Assert-Source $c.old_pins $c.before}
 $parents=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($member in $c.source_members) {
  $parent=Split-Path -Parent (Source-MemberPath $member.path)
  while($parent.StartsWith($c.root,[StringComparison]::OrdinalIgnoreCase)) {
   $null=$parents.Add($parent);if($parent -ceq $c.root){break};$parent=Split-Path -Parent $parent
  }
 }
 foreach($parent in @($parents|Sort-Object)) {
  Invoke-ReadinessGate ('Directory custody: '+$parent) {
   if(Test-Path -LiteralPath $parent){Assert-Protected $parent;Assert-GitDirectoryInheritance $parent}
   else {'Directory absent; the updater will create it beneath a verified parent'}
  }
 }
 foreach($member in $c.source_members){Invoke-ReadinessGate ('Source member: '+$member.path) {Test-DrySourceMember $member}}
 Invoke-ReadinessGate 'Native process identity and SQL startup contracts' {Verify-Native -Preflight}
 Invoke-ReadinessGate 'Pinned Python and required native imports' {
  $null=Read-Bytes $c.venv.path $c.venv.sha256 4MB
  & $c.venv.path -I -B -c 'import win32file, win32api, win32security' | Out-Host
  if($LASTEXITCODE -ne 0){throw 'Installed native dependencies unavailable'}
 }
 Invoke-ReadinessGate 'Scheduled launch configuration and permissions' {$null=Assert-Task $c.old_gate.Path}
 Invoke-ReadinessGate 'No premature successor directories' {if((Test-Path -LiteralPath $c.new_seed_directory) -or (Test-Path -LiteralPath $c.new_state_directory)){throw 'Successor state already exists'}}
 Invoke-ReadinessGate 'Authority SQL session still matches' {if(-not(Same (Sessions) @($c.old_session))){throw 'Current authority session differs'}}
 Invoke-ReadinessGate 'Both predecessor process creation times still match' {
  foreach($binding in $c.old_native){$process=[Diagnostics.Process]::GetProcessById([int]$binding.PID);try{if($process.StartTime.ToFileTimeUtc() -ne [long]$binding.ExpectedCreatedFiletime -or $process.HasExited){throw 'Current native identity differs'}}finally{$process.Dispose()}}
 }
 $failed=@($readiness|Where-Object {$_.status -ceq 'FAIL'})
 return [pscustomobject]@{stage=$(if($failed.Count){'BLOCKERS_FOUND'}else{'READ_ONLY_PREFLIGHT_CHECKS_PASSED'});checked_utc=[datetime]::UtcNow.ToString('o');before=$plan.before;target=$plan.target;gates=$readiness.ToArray();failures=$failed.Count;readiness_checks_are_read_only=$true;free_bytes_c=([IO.DriveInfo]::new('C:\')).AvailableFreeSpace;limits='Snapshot against the authenticated failed packet, not fresh deployment authority. Full PrepareOnly must pass again. Drain, SQL backup/apply, successor publication/start and functional health require actual coordinated execution.'}
}

if($Action -ceq 'Library'){return}
# Packaging replaces only these two digest placeholders. No user-selected paths.
$planHash='__PLAN_SHA256__'
$libraryHash='__LIBRARY_SHA256__'
$requestedAction=$Action
$bundle=$PSScriptRoot
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
if($PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Windows PowerShell 5.1 required'}
function Read-Bundle([string]$Name,[string]$Digest,[long]$Limit) {
 $path=Join-Path $bundle $Name;$item=Get-Item -LiteralPath $path -Force
 if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt $Limit){throw 'Bundle member type/size differs'}
 $bytes=[IO.File]::ReadAllBytes($path);$sha=[Security.Cryptography.SHA256]::Create()
 try{$observed=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
 if($bytes.Length -gt $Limit -or $observed -cne $Digest){throw 'Bundle member identity differs'}
 return ,$bytes
}
$plan=[Text.Encoding]::UTF8.GetString((Read-Bundle 'CustodyRepairPlan.json' $planHash 1MB))|ConvertFrom-Json
$libraryText=[Text.Encoding]::UTF8.GetString((Read-Bundle 'K98-SourceUpdate.ps1' $libraryHash 128KB))
. ([scriptblock]::Create($libraryText)) -Action Library
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if($env:COMPUTERNAME -cne 'MINI_AMD' -or $identity.User.Value -cne $plan.sid -or $identity.Owner.Value -cne 'S-1-5-32-544' -or -not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Use elevated Windows PowerShell on MINI_AMD with the existing deployment account'}
$live='C:\discord_file_downloader\docs\task_packs'
$state='C:\ProgramData\K98\S11\documentation-custody-'+$planHash.Substring(0,16)
$fresh=Join-Path $state 'fresh';$backup=Join-Path $state 'original-task-packs'
$script:c=[pscustomobject]@{root='C:\discord_file_downloader';sid=$plan.sid}
$updates='C:\ProgramData\K98\S11\updates'
Assert-Protected $updates;Assert-Protected (Split-Path -Parent $live)
$operatorLock=Join-Path $updates 'operator.lock';Assert-Protected $operatorLock
$lock=[IO.File]::Open($operatorLock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
 if(Test-Path -LiteralPath (Join-Path $updates 'active.json')){throw 'An update is already active; preserve its evidence and use its status workflow'}
 # Bind repair to the failed, unstarted release and the unchanged R4 installation.
 $tool='C:\ProgramData\K98\S11\updater'
 $null=Read-Bytes (Join-Path $tool 'update-tool.json') $plan.updater_manifest_sha256 64KB
 $package=$plan.failed_package
 $bindings=Read-Json (Join-Path $package 'ReleaseBindings.json') $plan.bindings_sha256
 if($bindings.before -cne $plan.before -or $bindings.target -cne $plan.target -or $bindings.sid -cne $plan.sid){throw 'Failed release bindings differ'}
 foreach($name in @('deployment-request.json',('deployment-drained-'+$bindings.release_id+'.json'))) {
  if(Test-Path -LiteralPath (Join-Path $bindings.old_policy.StateDirectory $name)){throw 'Deployment has started; no standalone documentation repair permitted'}
 }
 # Load the same authenticated definitions from their protected packet location,
 # preserving their PSScriptRoot for pinned SQL/native read-only checks.
 $adapter=Join-Path $package 'Release-Step.ps1'
 $null=Read-Bytes $adapter $libraryHash 128KB
 . $adapter -Action Library -ExpectedBindingsSHA256 $plan.bindings_sha256
 $script:c=$bindings
 if($requestedAction -ceq 'Repair'){Assert-Predecessor;Invoke-DocumentationRepair}
 elseif($requestedAction -ceq 'Verify') {
  $done=Read-RepairReceipt 'complete.json';$receipt=Read-RepairReceipt 'prepared.json'
  if($done.stage -cne 'verified'){throw 'Repair is not complete'}
  $null=Get-RepairImage $live $true $receipt
  Write-Host 'REPAIR VERIFICATION PASSED.'
 }
 $result=Get-DocumentationReadiness
 $reportPath=Join-Path $bundle ('P0a-readiness-'+[guid]::NewGuid().ToString('N')+'.json')
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 12))
 $reportFile=[IO.File]::Open($reportPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$reportFile.Write($bytes,0,$bytes.Length)}finally{$reportFile.Dispose()}
 Write-Host ('Readiness report: '+$reportPath)
 Write-Host ('Checks: '+$result.gates.Count+'; blockers: '+$result.failures)
 foreach($failure in @($result.gates|Where-Object {$_.status -ceq 'FAIL'})){Write-Host ($failure.name+': '+$failure.detail)}
 if($result.failures){throw 'Readiness blockers remain. Keep maintenance enabled; return the report. No drain was requested.'}
 Write-Host "Read-only checks passed. Next run the installed Update-K98.ps1 -PrepareOnly, then the normal updater only after that passes."
}finally{$lock.Dispose()}
