# Isolated updater custody/index regression. Real files, native handles and Git;
# substitute administrative ACL creation and deployment proofs. No task/SQL/bot calls.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$library=Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'
. $library -Action Library
$fixture=Join-Path (Split-Path -Parent $PSScriptRoot) ('.codex_artifacts\update-source-test-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($fixture)
$script:cases=0
function Check([bool]$Value,[string]$Message){if(-not $Value){throw $Message};$script:cases++}
function Reject([scriptblock]$Call,[string]$Pattern){try{& $Call;throw ('TEST_DID_NOT_REJECT: '+$Pattern)}catch{if($_.Exception.Message.StartsWith('TEST_DID_NOT_REJECT') -or $_.Exception.Message -notlike $Pattern){throw};$script:cases++}}
function Acl([string]$Owner) {
 $a=[Security.AccessControl.DirectorySecurity]::new()
 $a.SetOwner([Security.Principal.SecurityIdentifier]::new($Owner))
 $a.SetGroup([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
 return $a
}
$application='S-1-5-21-101-102-103-1001'
$script:trusted=Acl 'S-1-5-32-544'
$script:acls=@{};$script:sealed=[Collections.Generic.List[string]]::new();$script:raced=$false
function Get-Acl([string]$LiteralPath){$a=if($script:acls.ContainsKey($LiteralPath)){$script:acls[$LiteralPath]}else{$script:trusted};$copy=Acl 'S-1-5-32-544';$copy.SetSecurityDescriptorBinaryForm($a.GetSecurityDescriptorBinaryForm());return $copy}
# Real retained handles and atomic object replacement. Substitute only the
# administrative ACL at object creation, unavailable in a non-elevated fixture.
$realOpen=${function:Open-SourceCustodyHandle}
function Open-SourceCustodyHandle([string]$Path,[bool]$Directory) {
 $handle=& $script:realOpen $Path $Directory
 $script:heldPath=$Path
 return $handle
}
function Write-SourceCopy([string]$Path,[byte[]]$Bytes,$Acl) {
 [IO.File]::WriteAllBytes($Path,$Bytes);$script:acls[$Path]=$Acl
 if($script:raced){$script:acls[$script:heldPath].AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new('Everyone','Write','Allow'))}
}
$realInstall=${function:Install-SourceCopy}
function Install-SourceCopy([string]$Fresh,[string]$Path) {
 & $script:realInstall $Fresh $Path
 $script:acls[$Path]=$script:acls[$Fresh];$script:sealed.Add($Path)
}
$c=[pscustomobject]@{root=$fixture;sid=$application;old_pins=[pscustomobject]@{};source_members=@()}
$leaf=Join-Path $fixture 'README-DEV.md'
$raw=[Text.Encoding]::UTF8.GetBytes("before`n")
[IO.File]::WriteAllBytes($leaf,$raw)
$digest=Hash $raw
$acls[$leaf]=Acl $application
Initialize-SourceOwner $leaf $false @($digest)
Check ($sealed.Count -eq 1) 'Known owner-only mismatch was not established'
Check ((Hash ([IO.File]::ReadAllBytes($leaf))) -ceq $digest) 'Ownership changed content'
Initialize-SourceOwner $leaf $false @($digest)
Check ($sealed.Count -eq 1) 'Trusted owner was rewritten on repeat'

$acls[$leaf]=Acl 'S-1-5-32-545'
Reject {Initialize-SourceOwner $leaf $false @($digest)} '*Unrecognized source owner*'
$acls[$leaf]=Acl $application
Reject {Initialize-SourceOwner $leaf $false @('a'*64)} '*predecessor bytes differ*'
Check ($sealed.Count -eq 1) 'Failed preconditions reached ownership write'
$acls[$leaf].AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new('Everyone','Write','Allow'))
Reject {Initialize-SourceOwner $leaf $false @($digest)} '*write access differs*'
$acls[$leaf]=Acl $application;$script:raced=$true
Initialize-SourceOwner $leaf $false @($digest)
Assert-Protected $leaf;$cases++
$script:raced=$false;$acls[$leaf]=Acl 'S-1-5-32-544'
Reject {Open-SourceCustodyHandle $leaf $true} '*type/reparse mismatch*'
# The native handle prevents content writes; protected parent authority controls
# new namespace entries while DELETE sharing permits replacement by the updater.
$hold=Open-SourceCustodyHandle $leaf $false
try {
 Reject {[IO.File]::WriteAllText($leaf,'race')} '*used by another process*'
}finally{$hold.Dispose()}

# Prior security handles must never retain authority over an accepted replacement.
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class CustodyHandleFixture {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern SafeFileHandle CreateFileW(string p,uint a,uint s,IntPtr z,uint c,uint f,IntPtr t);
 [DllImport("advapi32.dll")] static extern uint SetSecurityInfo(SafeFileHandle h,uint t,uint s,IntPtr o,IntPtr g,IntPtr d,IntPtr a);
 public static SafeFileHandle Open(string p) {
  var h=CreateFileW(p,0x40000,7,IntPtr.Zero,3,0x02000000,IntPtr.Zero);
  if(h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error()); return h;
 }
 public static void ClearOldDacl(SafeFileHandle h) {
  uint e=SetSecurityInfo(h,1,4,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero,IntPtr.Zero);
  if(e!=0) throw new Win32Exception((int)e);
 }
}
'@
$prior=[CustodyHandleFixture]::Open($leaf);$acls[$leaf]=Acl $application
try {
 $accepted=$false
 try {Initialize-SourceOwner $leaf $false @($digest);$accepted=$true}
 catch {if($_.Exception.Message -notlike '*Access is denied*' -and $_.Exception.Message -notlike '*used by another process*'){throw}}
 if($accepted) {
  $script:retainedOutcome='FreshObjectUnaffected'
  $sddl=(Microsoft.PowerShell.Security\Get-Acl -LiteralPath $leaf).Sddl
  [CustodyHandleFixture]::ClearOldDacl($prior)
  Check ((Microsoft.PowerShell.Security\Get-Acl -LiteralPath $leaf).Sddl -ceq $sddl) 'Prior handle changed accepted object'
 } else {$script:retainedOutcome='RefusedWhilePriorHandleOpen';Check ((Hash ([IO.File]::ReadAllBytes($leaf))) -ceq $digest) 'Refused replacement altered original'}
}finally{$prior.Dispose()}
Initialize-SourceOwner $leaf $false @($digest)
$acls[$leaf]=Acl $application
Set-Content -LiteralPath $leaf -Stream extra -Value 'retained'
Reject {Initialize-SourceOwner $leaf $false @($digest)} '*alternate streams refused*'
Remove-Item -LiteralPath $leaf -Stream extra
$hardlink=Join-Path $fixture 'hardlink.md'
$null=New-Item -ItemType HardLink -Path $hardlink -Target $leaf
Reject {Initialize-SourceOwner $leaf $false @($digest)} '*hardlinks refused*'
Remove-Item -LiteralPath $hardlink
$acls[$leaf].SetSecurityDescriptorSddlForm('O:BAG:BAD:NO_ACCESS_CONTROL')
Reject {Initialize-SourceOwner $leaf $false @($digest)} '*null DACL refused*'
$acls[$leaf]=$trusted

$docs=Join-Path $fixture 'docs';$reference=Join-Path $docs 'reference'
$null=[IO.Directory]::CreateDirectory($reference)
$junction=Join-Path $fixture 'junction'
$null=New-Item -ItemType Junction -Path $junction -Target $reference
Reject {Open-SourceCustodyHandle $junction $true} '*type/reparse mismatch*'
[IO.Directory]::Delete($junction)
$note=Join-Path $reference 'note.md';[IO.File]::WriteAllBytes($note,$raw)
foreach($path in @($docs,$reference,$note)){$acls[$path]=Acl $application}
$c.source_members=@([pscustomobject]@{path='docs/reference/note.md';added=$false;deleted=$false;before_sha256=@($digest)})
Reject {Initialize-UpdateCustody} '*directory requires established administrative custody*'
$acls[$docs]=$trusted;$acls[$reference]=$trusted
Initialize-UpdateCustody
Check (-not $sealed.Contains($docs) -and -not $sealed.Contains($reference) -and $sealed.Contains($note)) 'Ancestor custody changed or nested file not established'
Assert-UpdatePaths
$cases++
$acls[$docs]=Acl 'S-1-5-32-544'
$acls[$docs].AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($application),[Security.AccessControl.FileSystemRights]::Write,[Security.AccessControl.InheritanceFlags]::ObjectInherit,[Security.AccessControl.PropagationFlags]::InheritOnly,[Security.AccessControl.AccessControlType]::Allow))
Reject {Initialize-UpdateCustody} '*write access differs*'
$acls[$docs]=$trusted
$c.old_pins=[pscustomobject]@{'README-DEV.md'=$digest};$acls[$leaf]=Acl $application
$c.source_members=@([pscustomobject]@{path='README-DEV.md';added=$false;deleted=$false;before_sha256=@($digest)})
Reject {Initialize-UpdateCustody} '*Protected owner differs*'
$c.old_pins=[pscustomobject]@{};$acls[$leaf]=$trusted
$c.source_members=@([pscustomobject]@{path='README-DEV.md';added=$true;deleted=$false;before_sha256=@()})
Reject {Initialize-UpdateCustody} '*New tracked path already exists*'

# Real Git index reproduction, including an interruption between two exact paths.
$repo=Join-Path $fixture 'git';$null=[IO.Directory]::CreateDirectory($repo)
$git='C:\Program Files\Git\cmd\git.exe'
$script:adds=0;$script:failAdd=0
function Git([string]$Arguments) {
 if($Arguments -match ' add --renormalize '){$script:adds++;if($script:adds -eq $script:failAdd){throw 'fixture interrupted index update'}}
 $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$script:git
 $info.Arguments='-c core.hooksPath=NUL -c core.fsmonitor=false -c maintenance.auto=false -c gc.auto=0 -C "'+$script:repo+'" '+$Arguments
 $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 foreach($key in @($info.EnvironmentVariables.Keys)){if(([string]$key).StartsWith('GIT_',[StringComparison]::OrdinalIgnoreCase)){$info.EnvironmentVariables.Remove([string]$key)}}
 $info.EnvironmentVariables['GIT_CONFIG_NOSYSTEM']='1';$info.EnvironmentVariables['GIT_CONFIG_GLOBAL']='NUL'
 $p=[Diagnostics.Process]::new();$p.StartInfo=$info
 try {$null=$p.Start();$stdout=$p.StandardOutput.ReadToEndAsync();$stderr=$p.StandardError.ReadToEndAsync();if(-not $p.WaitForExit(10000)){$p.Kill();throw 'Fixture Git timeout'};$out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult();if($p.ExitCode -ne 0){throw ('Fixture Git failed: '+$err)};return $out.Trim()}finally{$p.Dispose()}
}
$null=Git 'init --initial-branch=main'
$null=Git 'config user.name Fixture';$null=Git 'config user.email fixture@example.invalid'
[IO.File]::WriteAllText((Join-Path $repo '.gitattributes'),"*.ps1 text eol=crlf`n")
[IO.File]::WriteAllText((Join-Path $repo 'unrelated.txt'),"keep`n")
$paths=@('one (space).ps1','two.ps1')
foreach($path in $paths){[IO.File]::WriteAllText((Join-Path $repo $path),"before`r`n")}
$null=Git 'add --all';$null=Git 'commit -m before'
$before=Git 'rev-parse HEAD'
foreach($path in $paths){[IO.File]::WriteAllText((Join-Path $repo $path),"after`r`n")}
$null=Git 'add --all';$null=Git 'commit -m after'
$target=Git 'rev-parse HEAD';$targetRaw=[Text.Encoding]::UTF8.GetBytes("after`n")
$c=[pscustomobject]@{root=$repo;before=$before;target=$target;release_id='fixture';new_pins=[pscustomobject]@{};old_gate=@{Path='fixture'};source_members=@($paths|ForEach-Object {[pscustomobject]@{path=$_;deleted=$false;target_sha256=(Hash $targetRaw)}})}
$script:intent=@{stage='starting';step='source';release_id='fixture'};$script:drain=$true;$script:disabled=$true
function Read-Json([string]$Path,[string]$Expected=''){return $script:intent}
function Assert-Drained {if(-not $script:drain){throw 'fixture drain absent'}}
function Assert-Task([string]$Gate,[bool]$Disabled=$false){if(-not $Disabled -or -not $script:disabled){throw 'fixture task not disabled'}}
foreach($path in $paths){[IO.File]::WriteAllBytes((Join-Path $repo $path),$targetRaw)}
Check ([bool](Git 'status --porcelain --untracked-files=no')) 'CRLF index reproduction missing'
Assert-TargetContents
$script:failAdd=2
Reject {Complete-SourceIndex} '*interrupted index update*'
Check (-not(Git 'diff --cached --name-only --no-ext-diff --')) 'Interrupted normalization staged content'
$script:failAdd=0
Complete-SourceIndex
Check (-not(Git 'status --porcelain --untracked-files=no')) 'Same-release convergence left modified files'
foreach($path in $paths){Check ((Hash ([IO.File]::ReadAllBytes((Join-Path $repo $path)))) -ceq (Hash $targetRaw)) 'Index convergence rewrote authenticated bytes'}
$count=$adds;Complete-SourceIndex;Check ($adds -eq $count) 'Repeated verification rewrote the index'

# Recreate only the stat mismatch, without touching the expected content.
function Dirty {
 foreach($path in $script:paths){[IO.File]::WriteAllText((Join-Path $script:repo $path),"after`r`n")}
 $null=Git 'add --renormalize -- .'
 foreach($path in $script:paths){[IO.File]::WriteAllBytes((Join-Path $script:repo $path),$script:targetRaw)}
}
Dirty
$script:intent.release_id='other';Reject {Complete-SourceIndex} '*Exact source intent required*';$script:intent.release_id='fixture'
$script:drain=$false;Reject {Complete-SourceIndex} '*drain absent*';$script:drain=$true
$script:disabled=$false;Reject {Complete-SourceIndex} '*task not disabled*';$script:disabled=$true
[IO.File]::WriteAllText((Join-Path $repo 'unrelated.txt'),"edit`n")
Reject {Complete-SourceIndex} '*Unrelated modified path*'
$null=Git 'add -- unrelated.txt';Reject {Complete-SourceIndex} '*Staged changes refuse*'
# Restore only this disposable fixture's known bytes and its index.
[IO.File]::WriteAllText((Join-Path $repo 'unrelated.txt'),"keep`n");$null=Git 'add -- unrelated.txt'
[IO.File]::WriteAllText((Join-Path $repo $paths[0]),'tamper')
Reject {Complete-SourceIndex} '*File checksum differs*'
[IO.File]::WriteAllBytes((Join-Path $repo $paths[0]),$targetRaw)
$c.target=$before;Reject {Complete-SourceIndex} '*Target private main differs*';$c.target=$target
Complete-SourceIndex
Check (-not(Git 'status --porcelain --untracked-files=no')) 'Final fixture state differs'
[pscustomobject]@{Status='PASS';Cases=$cases;Evidence=$fixture;ProductionTouched=$false;SqlConnected=$false;AdministrativeAclCreation='Substituted';NativeHandles='Real';AtomicReplacement='Real';RetainedSecurityHandle=$retainedOutcome;Git='Real'}|ConvertTo-Json -Compress
