# Isolated elevated rehearsal for the reviewed source-custody helper.
# No Git, SQL, Task Scheduler, bot imports, live updater or restart calls.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
if($PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Use Windows PowerShell 5.1.'}
if($env:COMPUTERNAME -ieq 'MINI_AMD'){throw 'Run this rehearsal on the development PC, not the production bot machine.'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -or $identity.Owner.Value -cne 'S-1-5-32-544'){throw 'Open Windows PowerShell 5.1 with Run as administrator on the development PC. No test files were created.'}

# Authenticate the exact reviewed library in memory before loading definitions.
# Normalize only checkout line endings; never execute a second path-based read.
$expectedLibrary='9d40718f1343a2e1118523e10dbfd8462ed734531339ea633583faf1f6f46132'
$libraryPath=Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'
$libraryBytes=[IO.File]::ReadAllBytes($libraryPath)
if($libraryBytes.Length -gt 128KB){throw 'Rehearsal library exceeds bound'}
$libraryText=[Text.Encoding]::UTF8.GetString($libraryBytes).Replace("`r`n","`n")
$hasher=[Security.Cryptography.SHA256]::Create()
try{$libraryHash=([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($libraryText)))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
if($libraryHash -cne $expectedLibrary){throw 'Rehearsal library differs from reviewed version; do not substitute another copy.'}
. ([scriptblock]::Create($libraryText)) -Action Library

$fixtureRoot='C:\ProgramData\K98-Updater-Rehearsal-'+[guid]::NewGuid().ToString('N')
$script:c=[pscustomobject]@{root=$fixtureRoot;sid=$identity.User.Value;old_pins=[pscustomobject]@{};source_members=@()}
$checks=[Collections.Generic.List[string]]::new()
$result=[ordered]@{Status='RUNNING';StartedUTC=[datetime]::UtcNow.ToString('o');Host=$env:COMPUTERNAME;Fixture=$fixtureRoot;LibrarySHA256=$libraryHash;AdministrativeAclCreation='Real';ProductionTouched=$false;SqlConnected=$false;Checks=@();Error=$null}
function Check([bool]$Value,[string]$Name){if(-not $Value){throw $Name};$script:checks.Add($Name)}
function Reject([scriptblock]$Call,[string]$Pattern,[string]$Name){
 $rejected=$false
 try{& $Call}catch{if($_.Exception.Message -notlike $Pattern){throw};$rejected=$true}
 Check $rejected $Name
}
function New-ApplicationFile([string]$Name,[byte[]]$Bytes,[bool]$Inherited=$false,[bool]$Writable=$false){
 if($Name -cnotmatch '^[a-z-]+\.(txt|py)$'){throw 'Fixture filename differs'}
 $acl=New-Acl $false
 $acl.SetOwner([Security.Principal.SecurityIdentifier]::new($script:c.sid))
 $acl.SetGroup([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
 if($Writable){$acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($script:c.sid),[Security.AccessControl.FileSystemRights]::Write,[Security.AccessControl.AccessControlType]::Allow))}
 $path=Join-Path $script:c.root $Name
 Write-SourceCopy $path $Bytes $acl
 if($Inherited){
  # A blank FileSecurity creates a protected empty DACL instead of the intended
  # inherited fixture. Enable inheritance explicitly on this synthetic file.
  $inheritedAcl=Get-Acl -LiteralPath $path
  foreach($rule in @($inheritedAcl.GetAccessRules($true,$false,[Security.Principal.SecurityIdentifier]))){$inheritedAcl.RemoveAccessRuleSpecific($rule)}
  $inheritedAcl.SetAccessRuleProtection($false,$false)
  Set-Acl -LiteralPath $path -AclObject $inheritedAcl
 }
 return $path
}
$created=$false
try {
 # ProgramData may permit creating new children. It must not permit replacing
 # protected children or changing ancestor permissions. No ancestor is modified.
 $parent=Get-Item -LiteralPath 'C:\ProgramData' -Force
 $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
 while($null -ne $parent){
  if(-not($parent -is [IO.DirectoryInfo]) -or ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Rehearsal parent type/reparse differs'}
  $acl=Get-Acl -LiteralPath $parent.FullName
  if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw 'Rehearsal parent owner differs; no repair attempted'}
  if($null -eq ([Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)).DiscretionaryAcl){throw 'Rehearsal parent has null DACL'}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){
   if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band 0x500d0040) -ne 0){throw 'Rehearsal parent permissions differ; no repair attempted'}
  }
  $parent=$parent.Parent
 }
 if(Test-Path -LiteralPath $fixtureRoot){throw 'Fresh fixture path already exists'}
 $rootAcl=New-Acl $true;$rootAcl.SetGroup([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
 $null=[IO.Directory]::CreateDirectory($fixtureRoot,$rootAcl);$created=$true
 Assert-Protected $fixtureRoot
 $raw=[Text.Encoding]::UTF8.GetBytes("authenticated fixture`r`n")
 $digest=Hash $raw
 $sections=[Security.AccessControl.AccessControlSections]::Access -bor [Security.AccessControl.AccessControlSections]::Group
 foreach($inherited in @($false,$true)){
  $name=if($inherited){'inherited.txt'}else{'explicit.txt'}
  $path=New-ApplicationFile $name $raw $inherited
  $before=Get-Acl -LiteralPath $path
  Check ($before.GetOwner([Security.Principal.SecurityIdentifier]).Value -ceq $c.sid) ($name+': actual application owner')
  Check ($before.AreAccessRulesProtected -eq (-not $inherited)) ($name+': expected inheritance mode')
  [IO.File]::SetLastWriteTimeUtc($path,[datetime]::Parse('2020-01-02T03:04:05Z').ToUniversalTime())
  $metadata=Get-Item -LiteralPath $path -Force
  $sddl=$before.GetSecurityDescriptorSddlForm($sections)
  Initialize-SourceOwner $path $false @($digest)
  $after=Get-Acl -LiteralPath $path
  Check ($after.GetOwner([Security.Principal.SecurityIdentifier]).Value -ceq 'S-1-5-32-544') ($name+': real Administrators owner')
  Check ($after.GetSecurityDescriptorSddlForm($sections) -ceq $sddl) ($name+': exact DACL and group preserved')
  Check ($after.AreAccessRulesProtected -eq $before.AreAccessRulesProtected) ($name+': inheritance preserved')
  Check ((Hash ([IO.File]::ReadAllBytes($path))) -ceq $digest) ($name+': authenticated bytes preserved')
  $observed=Get-Item -LiteralPath $path -Force
  Check ($observed.LastWriteTimeUtc -eq $metadata.LastWriteTimeUtc -and $observed.CreationTimeUtc -eq $metadata.CreationTimeUtc -and $observed.Attributes -eq $metadata.Attributes) ($name+': ordinary metadata preserved')
  Initialize-SourceOwner $path $false @($digest)
  Assert-Protected $path
  Check ((Hash ([IO.File]::ReadAllBytes($path))) -ceq $digest) ($name+': repeat remains valid')
 }
 $bad=New-ApplicationFile 'altered.txt' ([Text.Encoding]::UTF8.GetBytes('different'))
 Reject {Initialize-SourceOwner $bad $false @($digest)} '*predecessor bytes differ*' 'Altered content refused'
 Check ((Get-Acl -LiteralPath $bad).GetOwner([Security.Principal.SecurityIdentifier]).Value -ceq $c.sid) 'Refused content retains original owner'
 $writable=New-ApplicationFile 'writable.txt' $raw $false $true
 Reject {Initialize-SourceOwner $writable $false @($digest)} '*write access differs*' 'Application write permission refused'
 $runtime=New-ApplicationFile 'runtime.py' $raw
 $c.old_pins=[pscustomobject]@{'runtime.py'=$digest}
 $c.source_members=@([pscustomobject]@{path='runtime.py';added=$false;deleted=$false;before_sha256=@($digest)})
 Reject {Initialize-UpdateCustody} '*Protected owner differs*' 'Application-owned pinned runtime refused'
 $result.Status='PASS'
}catch{$result.Status='FAIL';$result.Error=$_.Exception.Message}
$result.Checks=@($checks.ToArray());$result['FinishedUTC']=[datetime]::UtcNow.ToString('o')
$json=$result|ConvertTo-Json -Depth 5
if($created){
 $evidencePath=Join-Path $fixtureRoot 'result.json'
 Write-New $evidencePath ([Text.UTF8Encoding]::new($false).GetBytes($json))
 Write-Host ('Evidence: '+$evidencePath)
}
Write-Output $json
if($result.Status -cne 'PASS'){exit 1}
