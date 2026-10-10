# Reusable exact-version upgrade; packaging supplies independently pinned hashes.
# Exact installed package, current startup state and operator lock are revalidated.
# Close all other updater PowerShell windows before running this reviewed helper.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0'
$env:PSModulePath='C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
# Packaging replaces these literals once. Invocation cannot select another package.
Set-Variable -Name PreviousManifestSHA256 -Value 'cd112e1912ec04318a463a48d8df20e88d6dae4dd20c45368f517deadc318871' -Option Constant
Set-Variable -Name InstallerSHA256 -Value 'ab69591f89a88628a729eb35a08eadda4ed0602d7512291075e5ab746017fd30' -Option Constant
Set-Variable -Name TargetManifestSHA256 -Value '6562c4cf8970c8fe5c776d10275aab6f2211fc2e814a9d3a529a56a15c34c50b' -Option Constant
if($env:COMPUTERNAME -cne 'MINI_AMD' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Use MINI_AMD Windows PowerShell 5.1'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if($identity.Owner.Value -cne 'S-1-5-32-544'){throw 'Administrative default object owner required'}
if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run as administrator under the deployment account'}

function Upgrade-Hash([byte[]]$Bytes) {
 $h=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($h.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
}
function Assert-UpgradeTool([string]$Path,[string]$ManifestHash) {
 Assert-Custody $Path
 $manifestPath=Join-Path $Path 'update-tool.json'
 if(-not(Test-Path -LiteralPath $manifestPath)){throw 'Tool manifest missing'}
 Assert-Custody $manifestPath
 $bytes=[IO.File]::ReadAllBytes($manifestPath)
 if((Upgrade-Hash $bytes) -cne $ManifestHash){throw 'Tool manifest identity differs'}
 $manifest=[Text.Encoding]::UTF8.GetString($bytes)|ConvertFrom-Json
 $names=@('Update-K98.ps1','K98-SourceUpdate.ps1','Deploy-K98Release.ps1','prepare_k98_update.py','verify_k98_update_pair.py','package_k98_update_tool.py','EmptyGitConfig.txt')
 if($null -ne $manifest.files.PSObject.Properties['prepare_k98_release.py']){$names+=@('prepare_k98_release.py')}
 if($manifest.version -ne 1 -or @($manifest.files.PSObject.Properties).Count -ne $names.Count){throw 'Tool manifest shape differs'}
 foreach($name in $names){if($null -eq $manifest.files.PSObject.Properties[$name]){throw 'Tool member missing from manifest'}}
 $items=@(Get-ChildItem -LiteralPath $Path -Force)
 foreach($item in $items) {
  if($item.PSIsContainer -or $item.Name -cnotin ($names+@('update-tool.json'))){throw 'Unexpected tool member'}
  Assert-Custody $item.FullName
  if($item.Name -cne 'update-tool.json' -and (Upgrade-Hash ([IO.File]::ReadAllBytes($item.FullName))) -cne $manifest.files.($item.Name)){throw 'Tool member checksum differs'}
 }
 if($items.Count -ne ($names.Count+1)){throw 'Incomplete tool'}
}
function Assert-UpgradePartial([string]$Path,$Payload) {
 Assert-Custody $Path
 foreach($item in @(Get-ChildItem -LiteralPath $Path -Force)) {
  $member=$Payload.PSObject.Properties[$item.Name]
  if($item.PSIsContainer -or $null -eq $member -or $item.Name -cne $member.Name){throw 'Unexpected partial tool member'}
  Assert-Custody $item.FullName
  if((Upgrade-Hash ([IO.File]::ReadAllBytes($item.FullName))) -cne (Upgrade-Hash ([Convert]::FromBase64String($member.Value)))){throw 'Partial tool checksum differs'}
 }
}

function Assert-NoUpgradeProcess {
 # Current entrypoint loads its library before taking operator.lock. Refuse any
 # other observed updater process; the operator must close other updater windows.
 $others=@(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe' OR Name='python.exe'" | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -match '(Update-K98\.ps1|Deploy-K98Release\.ps1|prepare_k98_update\.py|K98-SourceUpdate\.ps1)'})
 if($others.Count){throw 'Other updater process present; close its window first'}
}
function Write-UpgradeMember([string]$Directory,[string]$Work,[string]$Name,[byte[]]$Bytes) {
 if($Name -cnotmatch '^[A-Za-z][A-Za-z0-9_.-]+$'){throw 'Invalid candidate member'}
 $target=Join-Path $Directory $Name
 if(Test-Path -LiteralPath $target) {
  Assert-Custody $target
  if((Upgrade-Hash ([IO.File]::ReadAllBytes($target))) -cne (Upgrade-Hash $Bytes)){throw 'Candidate member differs'}
  return
 }
 # An interrupted write stays outside the executable tool directory. Retain it;
 # the next invocation writes a fresh temporary file and never executes fragments.
 $pending=Join-Path $Work ('pending-'+[guid]::NewGuid().ToString('N'))
 $stream=[IO.FileStream]::new($pending,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,(New-Acl $false))
 try{$stream.Write($Bytes,0,$Bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 Assert-Custody $pending
 if((Upgrade-Hash ([IO.File]::ReadAllBytes($pending))) -cne (Upgrade-Hash $Bytes)){throw 'Candidate write readback differs'}
 Move-Item -LiteralPath $pending -Destination $target -ErrorAction Stop
}

# Authenticate before executing installer code; retain these exact bytes in memory.
$installer=Join-Path $PSScriptRoot 'Install-K98UpdateTool.ps1'
$installerBytes=[IO.File]::ReadAllBytes($installer)
if((Upgrade-Hash $installerBytes) -cne $InstallerSHA256){throw 'Reviewed installer checksum differs'}
$installerText=[Text.Encoding]::UTF8.GetString($installerBytes)
if($installerText -cnotmatch "\`$encoded='([A-Za-z0-9+/=]+)'"){throw 'Installer payload missing'}
$newPayload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Matches[1]))|ConvertFrom-Json
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($installerText,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Installer parse failure'}
$custody=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Assert-Custody'},$true)
if($null -eq $custody){throw 'Installer custody check missing'}
. ([scriptblock]::Create($custody.Extent.Text))
$newAcl=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'New-Acl'},$true)
if($null -eq $newAcl){throw 'Installer ACL builder missing'}
. ([scriptblock]::Create($newAcl.Extent.Text))
$sid=$identity.User.Value
$root='C:\ProgramData\K98\S11'
$tool=Join-Path $root 'updater'
$archive=Join-Path $root ('updater-before-'+$PreviousManifestSHA256)
$updates=Join-Path $root 'updates'
$work=Join-Path $root ('updater-upgrade-'+$TargetManifestSHA256)
$candidate=Join-Path $work 'tool'
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
 # Only the fully inventoried old package or exact completed new package is eligible.
 $oldHash=$PreviousManifestSHA256
 $newHash=$TargetManifestSHA256
 Assert-NoUpgradeProcess
 if(Test-Path -LiteralPath $archive) {
  Assert-UpgradeTool $archive $oldHash
  if(Test-Path -LiteralPath $tool) {
   Assert-UpgradeTool $tool $newHash
   Write-Host 'UPGRADE ALREADY COMPLETE. No changes made.'
   return
  }
 } else {Assert-UpgradeTool $tool $oldHash}
 if(-not(Test-Path -LiteralPath $work)){$null=[IO.Directory]::CreateDirectory($work,(New-Acl $true))}
 Assert-Custody $work
 if(-not(Test-Path -LiteralPath $candidate)){$null=[IO.Directory]::CreateDirectory($candidate,(New-Acl $true))}
 Assert-UpgradePartial $candidate $newPayload
 foreach($member in $newPayload.PSObject.Properties) {
  Write-UpgradeMember $candidate $work $member.Name ([Convert]::FromBase64String($member.Value))
 }
 Assert-UpgradeTool $candidate $newHash
 # Recheck admission after staging; the exclusive operator lock stays held.
 if(Test-Path -LiteralPath (Join-Path $updates 'active.json')){throw 'Active release exists; tool replacement refused'}
 if(Test-Path -LiteralPath (Join-Path $policy.state_directory 'deployment-request.json')){throw 'Deployment request exists; tool replacement refused'}
 Assert-NoUpgradeProcess
 if(-not(Test-Path -LiteralPath $archive)) {
  Assert-UpgradeTool $tool $oldHash
  # Directory moves are confined to literal direct children of the protected root.
  if([IO.Path]::GetFullPath($tool) -cne 'C:\ProgramData\K98\S11\updater' -or [IO.Path]::GetFullPath($archive) -cne (Join-Path $root ('updater-before-'+$oldHash)) -or [IO.Path]::GetFullPath($candidate) -cne (Join-Path (Join-Path $root ('updater-upgrade-'+$newHash)) 'tool')){throw 'Upgrade paths differ'}
  Move-Item -LiteralPath $tool -Destination $archive -ErrorAction Stop
 }
 # Interruption after the backup move resumes here with the verified candidate.
 if(Test-Path -LiteralPath $tool){throw 'Unexpected updater appeared during upgrade'}
 Move-Item -LiteralPath $candidate -Destination $tool -ErrorAction Stop
 Assert-UpgradeTool $archive $oldHash
 Assert-UpgradeTool $tool $newHash
 Write-Host 'UPGRADE COMPLETE. Old updater retained; bot source, task, startup policy and SQL unchanged.'
 Write-Host "Next, after reviewed production promotion: & 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'"
} finally {$lock.Dispose()}
