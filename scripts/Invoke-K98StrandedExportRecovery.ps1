[CmdletBinding()]
param(
 [ValidateSet('Inspect','Apply')][string]$Action='Inspect',
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PacketSHA256,
 [ValidatePattern('^[a-f0-9]{64}$')][string]$ReviewToken
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($PSVersionTable.PSEdition -cne 'Desktop'){throw 'Windows PowerShell 5.1 required'}
if($env:COMPUTERNAME -cne 'MINI_AMD'){throw 'Run on MINI_AMD'}
$recoveryIdentity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($recoveryIdentity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Elevated installed deployment account required'}
function Recovery-Hash([byte[]]$Bytes) {
 $hasher=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($hasher.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
}
function Recovery-Read([string]$Path,[string]$Expected) {
 $item=Get-Item -LiteralPath $Path -Force
 if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Length -gt 1MB){throw 'Bounded regular packet member required'}
 $bytes=[IO.File]::ReadAllBytes($Path)
 if((Recovery-Hash $bytes) -cne $Expected){throw 'Recovery packet member hash differs'}
 return ,$bytes
}
function Recovery-AssertProtected([string]$Path,[switch]$AllowRead) {
 $item=Get-Item -LiteralPath $Path -Force
 $depth=0;$strict=if($item.PSIsContainer){0}else{1}
 $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
 while($null -ne $item) {
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Protected reparse path refused'}
  $acl=Get-Acl -LiteralPath $item.FullName
  $descriptor=[Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)
  if($null -eq $descriptor.DiscretionaryAcl){throw 'Recovery custody has no protective DACL'}
  if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw 'Recovery custody owner differs'}
  $mask=if($depth -le $strict){if($AllowRead){0x500d0156}else{0xd00d0157}}else{0x500d0040}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
   if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
      ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and
      $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band $mask) -ne 0){throw 'Recovery custody permits untrusted access'}
  }
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory};$depth++
 }
}
function Recovery-NewDirectory([string]$Path) {
 if(Test-Path -LiteralPath $Path){Recovery-AssertProtected $Path;return}
 Recovery-AssertProtected (Split-Path -Parent $Path) -AllowRead
 $acl=[Security.AccessControl.DirectorySecurity]::new()
 $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
 $acl.SetAccessRuleProtection($true,$false)
 foreach($sid in @('S-1-5-18','S-1-5-32-544')) {
  $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),[Security.AccessControl.FileSystemRights]::FullControl,([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit),[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
 }
 $null=[IO.Directory]::CreateDirectory($Path,$acl)
 Recovery-AssertProtected $Path
}
$packetRaw=Recovery-Read (Join-Path $PSScriptRoot 'recovery-packet.json') $PacketSHA256
$packet=[Text.Encoding]::UTF8.GetString($packetRaw)|ConvertFrom-Json
$names=@('Read-K98PublicationTiming.ps1','recover_stranded_export.py','stranded_export_host.py','stranded_export_recovery.py','recovery-target.json')
if($packet.version -ne 1 -or $packet.packet_id -cnotmatch '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$' -or
   (($packet.members.name|Sort-Object) -join '|') -cne (($names|Sort-Object) -join '|')){throw 'Exact reviewed recovery packet required'}
$payloads=@{}
foreach($member in $packet.members) {
 if($member.sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'Exact member hash required'}
 $payloads[$member.name]=Recovery-Read (Join-Path $PSScriptRoot $member.name) $member.sha256
}
$recoveryBase='C:\ProgramData\K98\S11\recovery'
Recovery-NewDirectory $recoveryBase
$recoveryStage=Join-Path $recoveryBase $packet.packet_id
Recovery-NewDirectory $recoveryStage
foreach($member in $packet.members) {
 $destination=Join-Path $recoveryStage $member.name
 if(-not(Test-Path -LiteralPath $destination)) {
  $output=[IO.FileStream]::new($destination,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$output.Write($payloads[$member.name],0,$payloads[$member.name].Length);$output.Flush($true)}finally{$output.Dispose()}
 }
 Recovery-AssertProtected $destination
 $null=Recovery-Read $destination $member.sha256
}
$recoveryJournal=Join-Path $recoveryStage 'journal'
Recovery-NewDirectory $recoveryJournal
. (Join-Path $recoveryStage 'Read-K98PublicationTiming.ps1')
$binding=Get-VerifiedPublicationAuthority
$authority=$binding.authority
# Reuse the installed startup gate's independent venv launcher pin.
$pythonPath=$authority.python
$startupGate=[Text.Encoding]::UTF8.GetString((Read-TimingBytes $binding.gate_path))
if($pythonPath -cne 'C:\discord_file_downloader\venv\Scripts\python.exe' -or
   $startupGate -cnotmatch "Assert-PinnedFile 'C:\\discord_file_downloader\\venv\\Scripts\\python.exe' '([0-9a-f]{64})'"){throw 'Installed venv binding missing'}
$null=Read-TimingBytes $pythonPath $Matches[1] 4MB
$arguments=@('-I','-B',(Join-Path $recoveryStage 'recover_stranded_export.py'),
 '--action',$Action,'--manifest',$binding.manifest_path,'--manifest-sha256',$binding.manifest_sha256,
 '--target',(Join-Path $recoveryStage 'recovery-target.json'),'--journal',$recoveryJournal)
if($Action -ceq 'Apply') {
 if(-not $ReviewToken){throw 'Inspect first and supply its exact ReviewToken'}
 $arguments+=@('--review-token',$ReviewToken)
}
& $pythonPath @arguments
if($LASTEXITCODE -ne 0){throw ('Recovery stopped. Preserve '+$recoveryStage+' and report the output. Do not restart or clear claims.')}
Write-Host ('Recovery evidence: '+$recoveryStage)
