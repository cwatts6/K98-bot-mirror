# Elevated disposable qualification of the current source adapter's real ACL and
# atomic publication primitives. No production paths, SQL or bot/task startup.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ResultPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -cne '9SX2VF4'){throw 'Exact development host required'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if($identity.Owner.Value -cne 'S-1-5-32-544'){throw 'Elevated development token required'}
$resultFile=[IO.Path]::GetFullPath($ResultPath)
if(-not $resultFile.StartsWith('C:\discord_file_downloader\.codex_artifacts\p0a-', [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($resultFile) -cne '.json'){throw 'Disposable evidence output required'}
if(Test-Path -LiteralPath $resultFile){throw 'Evidence already exists'}
. (Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1') -Action Library
$script:c=[pscustomobject]@{sid=$identity.User.Value}
$fixture='C:\ProgramData\K98-P0a-Qualification-'+[guid]::NewGuid().ToString('N')
$checks=[Collections.Generic.List[string]]::new()
function Check($condition,$name){if(-not $condition){throw $name};$checks.Add($name)}
$result=@{status='RUNNING';fixture=$fixture;production_changed=$false;checks=@();error=$null}
try {
 # Bootstrap the unique fixture with its explicit administrative ACL. The
 # production helper then operates only beneath that protected fixture root.
 $null=[IO.Directory]::CreateDirectory($fixture,(New-Acl $true))
 Assert-Protected $fixture
 $partial=Join-Path $fixture 'partial'
 New-Directory $partial
 $pending=Join-Path $partial 'seed.json'
 $bytes=[Text.Encoding]::UTF8.GetBytes('{"fixture":"p0a","stage":"verified"}')
 Write-New $pending $bytes
 $expected=Hash $bytes
 Check ((Hash (Read-Bytes $pending $expected)) -ceq $expected) 'Protected CreateNew readback'
 $before=(Get-Acl -LiteralPath $pending).GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::All)
 $published=Join-Path $fixture 'verified-seed'
 [IO.Directory]::Move($partial,$published)
 $final=Join-Path $published 'seed.json'
 Assert-Protected $final
 Check ((Hash (Read-Bytes $final $expected)) -ceq $expected) 'Atomic directory publication preserves verified bytes'
 Check ((Get-Acl -LiteralPath $final).GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::All) -ceq $before) 'Atomic publication preserves exact ACL'
 $failed=$false;try{Write-New $final ([byte[]]@(1))}catch{$failed=$true}
 Check $failed 'Existing evidence cannot be overwritten'
 Check ((Hash (Read-Bytes $final $expected)) -ceq $expected) 'Refused overwrite preserves evidence'
 $failed=$false;try{$null=Read-Bytes $final ('0'*64)}catch{$failed=$true}
 Check $failed 'Changed expected hash is rejected'
 $lock=Join-Path $fixture 'execution.lock';Write-New $lock ([byte[]]@(1))
 $handle=[IO.File]::Open($lock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
 try{
  $failed=$false;try{$other=[IO.File]::Open($lock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None);$other.Dispose()}catch{$failed=$true}
  Check $failed 'Concurrent operator excluded by actual native handle'
 }finally{$handle.Dispose()}
 $result.status='PASS'
}catch{$result.status='FAIL';$result.error=$_.Exception.Message}
$result.checks=@($checks.ToArray())
[IO.File]::WriteAllText($resultFile,($result|ConvertTo-Json -Depth 5))
if($result.status -cne 'PASS'){exit 1}
