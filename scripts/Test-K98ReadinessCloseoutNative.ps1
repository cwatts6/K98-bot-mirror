# Disposable native ACL/write rehearsal. No production, SQL, task or process calls.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
if($env:COMPUTERNAME -ieq 'MINI_AMD'){throw 'Development PC rehearsal only'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Elevated Windows PowerShell required'}
$text=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1')).Replace("`r`n","`n")
$hasher=[Security.Cryptography.SHA256]::Create()
try{$sha=([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($text)))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
if($sha -cne '03a00255e5cd53cffb900ba2ebb2fcb59935029d16eac7f819ff4b188520f0ab'){throw 'Reviewed library differs'}
. ([scriptblock]::Create($text)) -Action Library
$fixture='C:\ProgramData\K98-Readiness-Rehearsal-'+[guid]::NewGuid().ToString('N')
if(Test-Path -LiteralPath $fixture){throw 'New fixture required'}
$script:c=[pscustomobject]@{sid=$identity.User.Value}
# Atomic creation with the production ACL; ancestors are read, never changed.
$null=[IO.Directory]::CreateDirectory($fixture,(New-Acl $true))
Assert-Protected $fixture
$result=[ordered]@{status='FAIL';fixture=$fixture;production_touched=$false;sql_connected=$false;native_acl=$true;checks=0;error=$null}
try {
 $intent=Join-Path $fixture 'readiness.intent.json'
 Write-Record $intent @{stage='starting';step='readiness';release_id='disposable'}
 $before=Hash (Read-Bytes $intent)
 $acceptance=@{release_id='disposable';target='fixture';closeout_kind='current_successor_admin_verified_v1';readiness=@{original_readiness='unconfirmed_preserved'}}|ConvertTo-Json -Depth 5|ConvertFrom-Json
 $complete=Join-Path $fixture 'verified.json'
 Write-AtomicRecord $complete $acceptance
 if(-not(Same (Read-Json $complete) $acceptance)){throw 'Native readback differs'}
 $result.checks++
 $refused=$false
 try{Write-AtomicRecord $complete $acceptance}catch{$refused=$true}
 if(-not $refused -or @(Get-ChildItem -LiteralPath $fixture -Filter 'pending-*').Count -ne 1){throw 'Overwrite or interruption evidence failure'}
 $result.checks++
 if((Hash (Read-Bytes $intent)) -cne $before){throw 'Historical intent changed'}
 $result.checks++
 $bad=Join-Path $fixture 'untrusted.json'
 Write-Record $bad $acceptance
 $acl=Get-Acl -LiteralPath $bad
 $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($c.sid),[Security.AccessControl.FileSystemRights]::Write,[Security.AccessControl.AccessControlType]::Allow))
 Set-Acl -LiteralPath $bad -AclObject $acl
 $refused=$false
 try{$null=Read-Json $bad}catch{$refused=$true}
 if(-not $refused){throw 'Application-writable evidence accepted'}
 $result.checks++
 $result.status='PASS'
}catch{$result.error=$_.Exception.Message}
Write-Record (Join-Path $fixture 'result.json') $result
$result|ConvertTo-Json -Compress
if($result.status -cne 'PASS'){exit 1}
