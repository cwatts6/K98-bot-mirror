# Native disposable fixture only. No production entrypoint, SQL, Git or task calls.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ReportPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
if($env:COMPUTERNAME -ieq 'MINI_AMD'){throw 'Development host only'}
if($ReportPath -cnotmatch '^C:\\discord_file_downloader\\\.codex_artifacts\\documentation-custody-test-[a-z0-9-]+\.json$'){throw 'Fixed test report location required'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Disposable native ACL test requires elevation'}
. (Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1') -Action Library
. (Join-Path $PSScriptRoot 'Repair-K98DocumentationCustody.ps1') -Action Library
$fixture='C:\ProgramData\K98-Documentation-Rehearsal-'+[guid]::NewGuid().ToString('N')
$script:c=[pscustomobject]@{root=$fixture;sid=$identity.User.Value}
$null=[IO.Directory]::CreateDirectory($fixture,(New-Acl $true))
Assert-Protected $fixture
$checks=[Collections.Generic.List[string]]::new()
function Check([bool]$Value,[string]$Name){if(-not $Value){throw $Name};$script:checks.Add($Name)}
function Reject([scriptblock]$Call,[string]$Pattern,[string]$Name){$caught=$false;try{& $Call}catch{if($_.Exception.Message -notlike $Pattern){throw};$caught=$true};Check $caught $Name}
function New-Case {
 $script:caseRoot=Join-Path $fixture ([guid]::NewGuid().ToString('N'))
 New-Directory $caseRoot
 $script:live=Join-Path $caseRoot 'task_packs';$script:state=Join-Path $caseRoot 'repair-state'
 $script:fresh=Join-Path $state 'fresh';$script:backup=Join-Path $state 'original-task-packs'
 $script:plan=[pscustomobject]@{sid=$identity.User.Value;before=('d'*40);root_sddl='';entries=@()}
 $acl=New-RepairAcl $true;$acl.SetOwner([Security.Principal.SecurityIdentifier]::new($plan.sid))
 $null=[IO.Directory]::CreateDirectory($live,$acl)
 $archive=Join-Path $live 'archive';$null=[IO.Directory]::CreateDirectory($archive,$acl)
 [IO.File]::SetAttributes($live,[IO.FileAttributes]::Directory);[IO.File]::SetAttributes($archive,[IO.FileAttributes]::Directory)
 $sections=[Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group -bor [Security.AccessControl.AccessControlSections]::Access
 $plan.root_sddl=(Get-Acl -LiteralPath $live).GetSecurityDescriptorSddlForm($sections)
 $entries=@([pscustomobject]@{path='archive';directory=$true;sddl=(Get-Acl -LiteralPath $archive).GetSecurityDescriptorSddlForm($sections)})
 foreach($name in @('present.md','archive/space & name.md')) {
  $path=Resolve-RepairEntry $live $name;$raw=[Text.Encoding]::UTF8.GetBytes("original $name`r`n")
  $a=New-RepairAcl $false;$a.SetOwner([Security.Principal.SecurityIdentifier]::new($plan.sid))
  Write-SourceCopy $path $raw $a
  [IO.File]::SetAttributes($path,[IO.FileAttributes]::Archive)
  $entries+=[pscustomobject]@{path=$name;directory=$false;sddl=(Get-Acl -LiteralPath $path).GetSecurityDescriptorSddlForm($sections);hashes=@((Hash $raw))}
 }
 $plan.entries=$entries
 $script:planHash=Hash ([Text.Encoding]::UTF8.GetBytes(($plan|ConvertTo-Json -Depth 12 -Compress)))
}
$result=[ordered]@{status='RUNNING';host=$env:COMPUTERNAME;fixture=$fixture;production_changed=$false;actual_administrative_acls=$true;checks=@();error=$null}
try {
 New-Case
 $before=Get-RepairImage $live $false
 Invoke-DocumentationRepair
 $saved=Read-RepairReceipt 'prepared.json'
 $after=Get-RepairImage $live $true $saved
 Check ($before.Count -eq $after.Count -and (Test-Path -LiteralPath $backup)) 'Fresh protected tree and retained original'
 Check ($before[0].sha256 -ceq $after[0].sha256) 'Exact original CRLF bytes preserved'
 $receiptHash=Hash (Read-Bytes (Join-Path $state 'complete.json'))
 Invoke-DocumentationRepair
 Check ((Hash (Read-Bytes (Join-Path $state 'complete.json'))) -ceq $receiptHash) 'Completed repeat changes no receipt'
 [IO.File]::WriteAllText((Join-Path $live 'present.md'),'tamper')
 Reject {Invoke-DocumentationRepair} '*differs from installed Git*' 'Completed repeat detects changed accepted bytes'

 foreach($fault in @('content','extra','missing','acl','ads','hardlink','junction')) {
  New-Case;$path=Join-Path $live 'present.md'
  switch($fault) {
   'content' {[IO.File]::WriteAllText($path,'bad')}
   'extra' {[IO.File]::WriteAllText((Join-Path $live 'extra.txt'),'extra')}
   'missing' {Move-Item -LiteralPath $path -Destination (Join-Path $caseRoot 'retained-missing.md')}
   'acl' {$a=Get-Acl -LiteralPath $path;$a.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new('Everyone','Write','Allow'));Set-Acl -LiteralPath $path -AclObject $a}
   'ads' {Set-Content -LiteralPath $path -Stream unexpected -Value 'extra stream'}
   'hardlink' {$null=New-Item -ItemType HardLink -Path (Join-Path $caseRoot 'outside-link') -Target $path}
   'junction' {$old=Join-Path $caseRoot 'original-archive';Move-Item -LiteralPath (Join-Path $live 'archive') -Destination $old;$null=New-Item -ItemType Junction -Path (Join-Path $live 'archive') -Target $old}
  }
  Reject {Invoke-DocumentationRepair} '*' ($fault+' rejected before swap')
  Check (-not(Test-Path -LiteralPath $backup)) ($fault+' retains original location')
 }
 # Lost acknowledgement at each journal boundary converges from retained state.
 $realRecord=${function:Write-AtomicRecord}
 foreach($recordName in @('prepared.json','swap-intent.json','complete.json')) {
  New-Case;$script:crashRecord=$recordName
  function Write-AtomicRecord([string]$Path,$Value) {& $script:realRecord $Path $Value;if([IO.Path]::GetFileName($Path) -ceq $script:crashRecord){throw 'Synthetic lost record acknowledgement'}}
  Reject {Invoke-DocumentationRepair} '*Synthetic lost record*' ($recordName+' lost acknowledgement')
  Set-Item Function:Write-AtomicRecord $realRecord
  Invoke-DocumentationRepair
  $null=Get-RepairImage $live $true (Read-RepairReceipt 'prepared.json')
  Check (Test-Path -LiteralPath (Join-Path $state 'complete.json')) ($recordName+' reconciles')
 }
 New-Case;New-Directory $state
 $null=[IO.Directory]::CreateDirectory($fresh,(New-RepairAcl $true))
 [IO.File]::SetAttributes($fresh,([IO.FileAttributes]::Directory -bor [IO.FileAttributes]::NotContentIndexed))
 Invoke-DocumentationRepair
 Check (Test-Path -LiteralPath (Join-Path $state 'complete.json')) 'Interrupted initial directory attributes reconcile'
 New-Case
 $realCopy=${function:Write-SourceCopy}
 function Write-SourceCopy([string]$Path,[byte[]]$Bytes,$Acl) {& $script:realCopy $Path $Bytes $Acl;if($Path -like '*\pending-*'){throw 'Synthetic lost fresh write acknowledgement'}}
 Reject {Invoke-DocumentationRepair} '*Synthetic lost fresh write*' 'Interrupted fresh file is not an accepted tree member'
 Set-Item Function:Write-SourceCopy $realCopy
 Invoke-DocumentationRepair
 Check (@(Get-ChildItem -LiteralPath $state -Filter 'pending-*').Count -ge 1) 'Interrupted scratch retained while repair converges'

 # An old WRITE_DAC handle must refer only to the quarantined old object.
 Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class DocumentationOldHandle {
 [StructLayout(LayoutKind.Sequential)] struct Info {public uint Attributes,CreationLow,CreationHigh,AccessLow,AccessHigh,WriteLow,WriteHigh,Volume,SizeHigh,SizeLow,Links,IndexHigh,IndexLow;}
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern SafeFileHandle CreateFileW(string p,uint a,uint s,IntPtr z,uint c,uint f,IntPtr t);
 [DllImport("advapi32.dll")] static extern uint SetSecurityInfo(SafeFileHandle h,uint t,uint s,IntPtr o,IntPtr g,IntPtr d,IntPtr a);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle h,out Info i);
 public static SafeFileHandle Open(string p) {var h=CreateFileW(p,0x40000,7,IntPtr.Zero,3,0x02000000,IntPtr.Zero);if(h.IsInvalid)throw new Win32Exception(Marshal.GetLastWin32Error());return h;}
 public static void ChangeOldDacl(SafeFileHandle h) {uint e=SetSecurityInfo(h,1,4,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);if(e!=0)throw new Win32Exception((int)e);}
 public static string Identity(SafeFileHandle h) {Info i;if(!GetFileInformationByHandle(h,out i))throw new Win32Exception(Marshal.GetLastWin32Error());return i.Volume+":"+i.IndexHigh+":"+i.IndexLow;}
}
'@
 New-Case;$prior=[DocumentationOldHandle]::Open($live)
 try {
  $oldIdentity=[DocumentationOldHandle]::Identity($prior)
  Invoke-DocumentationRepair
  $current=[DocumentationOldHandle]::Open($live)
  try{Check ([DocumentationOldHandle]::Identity($current) -cne $oldIdentity) 'Accepted directory has a new native object identity'}finally{$current.Dispose()}
  try{[DocumentationOldHandle]::ChangeOldDacl($prior);$result.old_handle_mutation='Only original object changed'}
  catch{if($_.Exception.InnerException -isnot [ComponentModel.Win32Exception] -or $_.Exception.InnerException.NativeErrorCode -ne 5){throw};$result.old_handle_mutation='Windows denied mutation through old handle'}
  $null=Get-RepairImage $live $true (Read-RepairReceipt 'prepared.json')
  Check $true 'Previously opened directory security handle cannot change accepted tree'
 }finally{$prior.Dispose()}
 $realMove=${function:Move-RepairTree}
 foreach($point in @('after_original','after_fresh')) {
  New-Case;$script:crashPoint=$point
  function Move-RepairTree([string]$From,[string]$To) {
   & $script:realMove $From $To
   if(($script:crashPoint -ceq 'after_original' -and $To -ceq $backup) -or ($script:crashPoint -ceq 'after_fresh' -and $To -ceq $live)){throw 'Synthetic interruption after move'}
  }
  Reject {Invoke-DocumentationRepair} '*Synthetic interruption*' ($point+' interrupted')
  Set-Item Function:Move-RepairTree $realMove
  Invoke-DocumentationRepair
  $null=Get-RepairImage $live $true (Read-RepairReceipt 'prepared.json')
  Check (Test-Path -LiteralPath (Join-Path $state 'complete.json')) ($point+' resumes and verifies')
 }
 New-Case
 Reject {Resolve-RepairEntry $live '../escape'} '*Unsafe repair*' 'Traversal refused'
 Reject {Move-RepairTree $live (Join-Path $caseRoot 'other')} '*Unrecognized repair move*' 'Unbound move refused'
 # Aggregate checks must continue after one failure, without executing repair.
 $script:readiness=[Collections.Generic.List[object]]::new()
 Invoke-ReadinessGate 'first' {throw 'synthetic first failure'}
 Invoke-ReadinessGate 'second' {'second checked'}
 Check ($readiness.Count -eq 2 -and $readiness[0].status -ceq 'FAIL' -and $readiness[1].status -ceq 'PASS') 'Readiness collects independent failures'
 $result.status='PASS'
}catch{$result.status='FAIL';$result.error=$_.Exception.ToString();$result.stack=$_.ScriptStackTrace}
finally {
 $result.checks=$checks.ToArray()
 $raw=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 12))
 $stream=[IO.File]::Open($ReportPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$stream.Write($raw,0,$raw.Length)}finally{$stream.Dispose()}
}
if($result.status -cne 'PASS'){throw $result.error}
Write-Host ('PASS: '+$checks.Count+' native checks; '+$ReportPath)
