param([Parameter(Mandatory=$true)][string]$Launcher)
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($Launcher,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Launcher syntax failed'}
# Load only literal function definitions; no host check, staging or recovery runs.
foreach($definition in $ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false)) {
 Invoke-Expression $definition.Extent.Text
}
function Refused([scriptblock]$Action,[string]$Expected) {
 $actual=$null
 try{& $Action}catch{$actual=$_.Exception.Message}
 if($actual -cne $Expected){throw ('Expected '+$Expected+'; received '+$actual)}
}
$sample=[Text.Encoding]::UTF8.GetBytes('retained original evidence')
$file=Join-Path ([IO.Path]::GetTempPath()) ('k98-recovery-fixture-'+[guid]::NewGuid().ToString('N')+'.txt')
try {
 [IO.File]::WriteAllBytes($file,$sample)
 if((Recovery-Hash (Recovery-Read $file (Recovery-Hash $sample))) -cne (Recovery-Hash $sample)){throw 'Packet readback differs'}
 Refused {Recovery-Read $file ('0'*64)} 'Recovery packet member hash differs'
} finally {if(Test-Path -LiteralPath $file){Remove-Item -LiteralPath $file}}
$root='C:\fixture';$owner='S-1-5-32-544';$trustee='S-1-5-32-544';$rights='FA';$link=$false;$nullDacl=$false
function Get-Item([string]$LiteralPath,[switch]$Force) {
 $node=[IO.DirectoryInfo]::new($LiteralPath)
 $attributes=if($link){[IO.FileAttributes]::ReparsePoint}else{[IO.FileAttributes]::Directory}
 $node|Add-Member -Force -MemberType NoteProperty -Name Attributes -Value $attributes
 return $node
}
function Get-Acl([string]$LiteralPath) {
 $acl=[Security.AccessControl.DirectorySecurity]::new()
 if($nullDacl){$acl.SetSecurityDescriptorSddlForm('O:BAG:SYD:NO_ACCESS_CONTROL')}
 else{$acl.SetSecurityDescriptorSddlForm('O:'+$owner+'G:SYD:(A;;'+$rights+';;;'+$trustee+')')}
 return $acl
}
Recovery-AssertProtected $root
$trustee='S-1-5-32-545';$rights='GR'
Refused {Recovery-AssertProtected $root} 'Recovery custody permits untrusted access'
Recovery-AssertProtected $root -AllowRead
$rights='GW'
Refused {Recovery-AssertProtected $root -AllowRead} 'Recovery custody permits untrusted access'
$trustee='S-1-5-32-544';$rights='FA';$owner='S-1-5-32-545'
Refused {Recovery-AssertProtected $root} 'Recovery custody owner differs'
$owner='S-1-5-32-544';$link=$true
Refused {Recovery-AssertProtected $root} 'Protected reparse path refused'
$link=$false;$nullDacl=$true
Refused {Recovery-AssertProtected $root} 'Recovery custody has no protective DACL'
'PASS: 9 packet syntax, exact-byte/hash and custody checks; no production operation'
