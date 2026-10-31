# One-time repair for the first updater's UCRT lookup failure, before preparation.
# Close all other updater PowerShell windows before running this reviewed helper.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
if($env:COMPUTERNAME -cne 'MINI_AMD' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Use MINI_AMD Windows PowerShell 5.1'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as administrator under the deployment account'}

function Repair-Hash([byte[]]$Bytes) {
 $h=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($h.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
}
function Assert-RepairTool([string]$Path,[string]$ManifestHash) {
 Assert-Custody $Path
 $manifestPath=Join-Path $Path 'update-tool.json'
 if(-not(Test-Path -LiteralPath $manifestPath)){throw 'Tool manifest missing'}
 Assert-Custody $manifestPath
 $bytes=[IO.File]::ReadAllBytes($manifestPath)
 if((Repair-Hash $bytes) -cne $ManifestHash){throw 'Tool manifest identity differs'}
 $manifest=[Text.Encoding]::UTF8.GetString($bytes)|ConvertFrom-Json
 $names=@('Update-K98.ps1','K98-SourceUpdate.ps1','Deploy-K98Release.ps1','prepare_k98_update.py','verify_k98_update_pair.py','package_k98_update_tool.py','EmptyGitConfig.txt')
 if($manifest.version -ne 1 -or @($manifest.files.PSObject.Properties).Count -ne $names.Count){throw 'Tool manifest shape differs'}
 foreach($name in $names){if($null -eq $manifest.files.PSObject.Properties[$name]){throw 'Tool member missing from manifest'}}
 $items=@(Get-ChildItem -LiteralPath $Path -Force)
 foreach($item in $items) {
  if($item.PSIsContainer -or $item.Name -cnotin ($names+@('update-tool.json'))){throw 'Unexpected tool member'}
  Assert-Custody $item.FullName
  if($item.Name -cne 'update-tool.json' -and (Repair-Hash ([IO.File]::ReadAllBytes($item.FullName))) -cne $manifest.files.($item.Name)){throw 'Tool member checksum differs'}
 }
 if($items.Count -ne ($names.Count+1)){throw 'Incomplete tool'}
}
function Assert-RepairPartial([string]$Path,$Payload) {
 Assert-Custody $Path
 foreach($item in @(Get-ChildItem -LiteralPath $Path -Force)) {
  $member=$Payload.PSObject.Properties[$item.Name]
  if($item.PSIsContainer -or $null -eq $member -or $item.Name -cne $member.Name){throw 'Unexpected partial tool member'}
  Assert-Custody $item.FullName
  if((Repair-Hash ([IO.File]::ReadAllBytes($item.FullName))) -cne (Repair-Hash ([Convert]::FromBase64String($member.Value)))){throw 'Partial tool checksum differs'}
 }
}

# Authenticate before executing installer code; retain these exact bytes in memory.
$installer=Join-Path $PSScriptRoot 'Install-K98UpdateTool.ps1'
$installerBytes=[IO.File]::ReadAllBytes($installer)
if((Repair-Hash $installerBytes) -cne 'c8c06bf756e5668cff846dd492a32a40d6a97cbac2d49bf76885a10827402cf3'){throw 'Reviewed installer checksum differs'}
$installerText=[Text.Encoding]::UTF8.GetString($installerBytes)
if($installerText -cnotmatch "\`$encoded='([A-Za-z0-9+/=]+)'"){throw 'Installer payload missing'}
$newPayload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Matches[1]))|ConvertFrom-Json
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($installerText,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Installer parse failure'}
$custody=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-Custody'},$true)
if($null -eq $custody){throw 'Installer custody check missing'}
. ([scriptblock]::Create($custody.Extent.Text))
$root='C:\ProgramData\K98\S11'
$tool=Join-Path $root 'updater'
$archive=Join-Path $root 'updater-before-ucrt-d9704e51'
$updates=Join-Path $root 'updates'
Assert-Custody $root
Assert-Custody $updates
$task=Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
$taskSid=[Security.Principal.NTAccount]::new($task.Principal.UserId).Translate([Security.Principal.SecurityIdentifier]).Value
if($identity.User.Value -cne $taskSid){throw 'Use the installed deployment account'}
if(@($task.Actions).Count -ne 1 -or $task.Actions[0].Arguments -cnotmatch '-File "(C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\Start-ReviewedAutomaticStartup.ps1)"$'){throw 'Installed startup action differs'}
$policyPath=Join-Path (Split-Path -Parent $Matches[1]) 'AutomaticStartupPolicy.json'
Assert-Custody $policyPath
$policy=[IO.File]::ReadAllText($policyPath)|ConvertFrom-Json
Assert-Custody $policy.state_directory
$lockPath=Join-Path $updates 'operator.lock'
Assert-Custody $lockPath
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
 if(Test-Path -LiteralPath (Join-Path $updates 'active.json')){throw 'Active release exists; tool replacement refused'}
 if(Test-Path -LiteralPath (Join-Path $policy.state_directory 'deployment-request.json')){throw 'Deployment request exists; tool replacement refused'}
 # Only the exact failed pre-fetch tool is eligible. Never replace arbitrary tools.
 $oldHash='acd6a7a938284b6712790579d45cf5593a4a39eee234590bbc29460ae47624b8'
 $newHash='cd112e1912ec04318a463a48d8df20e88d6dae4dd20c45368f517deadc318871'
 if(Test-Path -LiteralPath $archive) {
  Assert-RepairTool $archive $oldHash
  if(Test-Path -LiteralPath $tool){Assert-RepairPartial $tool $newPayload}
 } else {
  Assert-RepairTool $tool $oldHash
  # Both literal targets are direct children of the checked protected S11 root.
  if([IO.Path]::GetFullPath($tool) -cne 'C:\ProgramData\K98\S11\updater' -or [IO.Path]::GetFullPath($archive) -cne 'C:\ProgramData\K98\S11\updater-before-ucrt-d9704e51'){throw 'Repair paths differ'}
  Move-Item -LiteralPath $tool -Destination $archive -ErrorAction Stop
 }
 & ([scriptblock]::Create($installerText))
 Assert-RepairTool $tool $newHash
 Write-Host 'REPAIR COMPLETE. Old updater retained; bot source, task, startup policy and SQL unchanged.'
 Write-Host "Next: & 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'"
} finally {$lock.Dispose()}
