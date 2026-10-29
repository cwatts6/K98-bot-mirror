param([Parameter(Mandatory=$true)][string]$Collector)
$ErrorActionPreference='Stop'
. $Collector
$root='C:\ProgramData\K98\S11\evidence'
$log=$root+'\publication-timing.log'
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$other='S-1-5-21-111-222-333-444'
$grantPath=$root;$grantSid=$sid;$ownerSid='S-1-5-18';$reparse=$false
$checked=[Collections.Generic.List[string]]::new()
# Native filesystem types with synthetic metadata: no installed paths or ACLs are changed.
function New-TestDirectory([string]$Path) {
 $node=[IO.DirectoryInfo]::new($Path)
 $parent=if($node.Parent){New-TestDirectory $node.Parent.FullName}else{$null}
 $node|Add-Member -Force NoteProperty Parent $parent
 $node|Add-Member -Force NoteProperty Attributes ([IO.FileAttributes]::Directory)
 $node|Add-Member -Force NoteProperty PSIsContainer $true
 return $node
}
function Get-Item([string]$LiteralPath,[switch]$Force) {
 if($LiteralPath -ceq $log) {
  $node=[IO.FileInfo]::new($LiteralPath)
  $node|Add-Member -Force NoteProperty Directory (New-TestDirectory $root)
  $node|Add-Member -Force NoteProperty Attributes ([IO.FileAttributes]::Normal)
  $node|Add-Member -Force NoteProperty PSIsContainer $false
 } else {$node=New-TestDirectory $LiteralPath}
 if($reparse){$node|Add-Member -Force NoteProperty Attributes ([IO.FileAttributes]::ReparsePoint)}
 return $node
}
function Get-Acl([string]$LiteralPath) {
 $checked.Add($LiteralPath)
 $acl=[Security.AccessControl.DirectorySecurity]::new()
 $owner=if($LiteralPath -ceq $grantPath){$ownerSid}else{'S-1-5-18'}
 $grant=if($LiteralPath -ceq $grantPath){$grantSid}else{'S-1-5-18'}
 $acl.SetSecurityDescriptorSddlForm('O:'+$owner+'G:SYD:(A;;FA;;;'+$grant+')')
 return $acl
}
function Expect-Refusal([scriptblock]$Action,[string]$Message) {
 $failure=$null
 try{& $Action}catch{$failure=$_.Exception.Message}
 if($failure -cne $Message){throw ('Expected refusal: '+$Message+'; got: '+$failure)}
}
Expect-Refusal {Assert-TimingPath $root} 'Untrusted write access'
Assert-TimingPath $root $sid
$checked.Clear()
Assert-TimingPath $log $sid
if($checked.Count -ne 6 -or $checked[-1] -cne 'C:\'){throw 'Ancestor traversal incomplete'}
$grantPath=$log;$ownerSid=$sid
Assert-TimingPath $log $sid
$ownerSid='S-1-5-18';$grantPath='C:\ProgramData\K98\S11'
Expect-Refusal {Assert-TimingPath $log $sid} 'Untrusted write access'
$grantPath=$root;$grantSid=$other
Expect-Refusal {Assert-TimingPath $root $sid} 'Untrusted write access'
$grantSid=$sid;$ownerSid=$other
Expect-Refusal {Assert-TimingPath $root $sid} 'Protected owner differs'
$ownerSid='S-1-5-18';$reparse=$true
Expect-Refusal {Assert-TimingPath $root $sid} 'Reparse path refused'
$reparse=$false
Expect-Refusal {Assert-TimingPath $root $other} 'Evidence identity or path differs'
Expect-Refusal {Assert-TimingPath ($root+'\private.json') $sid} 'Evidence identity or path differs'
Expect-Refusal {Assert-TimingPath ($root+'\..\publication-timing.log') $sid} 'Evidence identity or path differs'
Expect-Refusal {Assert-TimingPath 'C:\ProgramData\K98\S11' $sid} 'Evidence identity or path differs'
'PASS: evidence writer and owner accepted only on fixed targets; ancestors, foreign writers/owners, reparse points, identity and path escapes refused.'
