#requires -Version 5.1
[CmdletBinding()]
param([ValidateSet('Library','Run')][string]$Action='Library',[string]$PacketRoot,[string]$PlanSHA256)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function Get-P02StartupAction($Action) {
 $arguments=[string]$Action.Arguments
 if($arguments.Length -gt 8192){throw 'Startup arguments exceed metadata bound'}
 $result=[ordered]@{arguments_sha256=(Hash ([Text.Encoding]::UTF8.GetBytes($arguments)));recognized=$false;script_path=$null;execute=$null;safe_arguments=$null;working_directory=$null}
 $executables=@('C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','powershell.exe')
 if([string]$Action.Execute -notin $executables){return [pscustomobject]$result}
 $pattern='^(?:(?:-NoProfile|-NonInteractive|-NoLogo)\s+|(?:-ExecutionPolicy)\s+(?:Bypass|RemoteSigned|AllSigned|Restricted)\s+)*-File\s+(?:"(?<file>C:\\[^"\r\n]+\.ps1)"|(?<file>C:\\[^ "\r\n]+\.ps1))\s*$'
 $match=[regex]::Match($arguments,$pattern,[Text.RegularExpressions.RegexOptions]::IgnoreCase)
 if(-not $match.Success){return [pscustomobject]$result}
 $path=$match.Groups['file'].Value
 $legacy=@('C:\discord_file_downloader\start-bot-after-sql.ps1','C:\discord_file_downloader\scripts\start-bot-after-sql.ps1')
 if($path -notin $legacy -and $path -notmatch '^C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\Start-ReviewedAutomaticStartup\.ps1$'){return [pscustomobject]$result}
 $result.recognized=$true;$result.script_path=$path;$result.execute=[string]$Action.Execute;$result.safe_arguments=$arguments
 if([string]$Action.WorkingDirectory -in @('','C:\discord_file_downloader','C:\Windows\System32')){$result.working_directory=[string]$Action.WorkingDirectory}
 return [pscustomobject]$result
}
function Get-P02BindingFact([string]$Path,[switch]$Directory) {
 $fact=[ordered]@{path=$Path;exists=(Test-Path -LiteralPath $Path);protected=$false}
 if(-not $fact.exists){return [pscustomobject]$fact}
 $item=Get-Item -LiteralPath $Path -Force
 $fact.attributes=[int]$item.Attributes
 if([bool]$item.PSIsContainer -ne [bool]$Directory -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Startup evidence object type/reparse differs'}
 $acl=Get-Acl -LiteralPath $Path
 $fact.owner_sid=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
 $fact.sddl=$acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access -bor [Security.AccessControl.AccessControlSections]::Owner)
 try{Assert-Protected $Path;$fact.protected=$true}catch{$fact.custody_failure_type=$_.Exception.GetType().FullName;return [pscustomobject]$fact}
 if(-not $Directory){$raw=Read-Bytes $Path '' 1MB;$fact.bytes=$raw.Length;$fact.sha256=Hash $raw}
 return [pscustomobject]$fact
}
function Get-P02StartupPolicy([string]$Path) {
 $fact=Get-P02BindingFact $Path
 $result=[ordered]@{file=$fact;binding_read=$false}
 if(-not $fact.exists -or -not $fact.protected){return [pscustomobject]$result}
 $policy=[Text.Encoding]::UTF8.GetString((Read-Bytes $Path $fact.sha256 1MB))|ConvertFrom-Json
 # Only reviewed structural fields leave the guest. No config, tokens or keys.
 if($null -ne $policy.PSObject.Properties['state_directory']){
  $state=[string]$policy.state_directory
  if($state -match '^C:\\ProgramData\\K98\\S11\\[A-Za-z0-9_\\-]+$' -and [IO.Path]::GetFullPath($state) -ceq $state){
   $result.state=Get-P02BindingFact $state -Directory
   $result.deployment_request_exists=Test-Path -LiteralPath (Join-Path $state 'deployment-request.json')
  }else{$result.state_path_supported=$false}
 }
 if($null -ne $policy.PSObject.Properties['seed_plan']){
  $seed=$policy.seed_plan
  if($null -ne $seed.PSObject.Properties['path'] -and $null -ne $seed.PSObject.Properties['sha256']){
   $pathValue=[string]$seed.path
   if($pathValue -match '^C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\ManualProcessPairPlan-CANDIDATE\.json$' -and [string]$seed.sha256 -cmatch '^[a-f0-9]{64}$'){
    $result.seed=Get-P02BindingFact $pathValue
    $result.seed_matches_policy=$result.seed.exists -and $result.seed.protected -and $result.seed.sha256 -ceq [string]$seed.sha256
   }else{$result.seed_path_supported=$false}
  }
 }
 $result.binding_read=$true
 return [pscustomobject]$result
}
function Invoke-P02StartupBindingRead($Plan,[string]$OperatorSID,[string]$EvidenceRoot) {
 $receipt=[ordered]@{schema='p02-startup-binding-read/1';outcome='failed';stage='initial task';first_failure=$null;sql_connections_opened=0;business_dispatches=0;startup_actions=0;installation_changes=0;physical_custody_retained=$false;qualifies_startup=$false;qualifies_installed_update=$false}
 try {
  $task=Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
  $xml=Export-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
  if([Text.Encoding]::UTF8.GetByteCount($xml) -gt 256KB){throw 'Startup XML exceeds bound'}
  $xmlHash=Hash ([Text.Encoding]::UTF8.GetBytes($xml))
  if($xmlHash -cne $Plan.task_xml_sha256 -or $task.Settings.Enabled -or [string]$task.State -cne 'Disabled' -or @($task.Actions).Count -ne 1){throw 'Accepted disabled startup task changed'}
  $taskSid=([Security.Principal.NTAccount]::new($task.Principal.UserId).Translate([Security.Principal.SecurityIdentifier])).Value
  if($taskSid -cne $Plan.task_principal_sid){throw 'Accepted startup principal changed'}
  # Original XML stays in the protected guest evidence directory, never transported.
  Write-New (Join-Path $EvidenceRoot 'original-task.xml') ([Text.Encoding]::UTF8.GetBytes($xml))
  $action=Get-P02StartupAction $task.Actions[0]
  $receipt.task=[ordered]@{xml_sha256=$xmlHash;principal_sid=$taskSid;operator_sid=$OperatorSID;operator_matches_task=($OperatorSID -ceq $taskSid);enabled=$false;action=$action;original_xml_guest_only=$true}
  $receipt.stage='updater identity'
  $manifest=Read-Bytes 'C:\ProgramData\K98\S11\updater\update-tool.json' $Plan.updater_manifest_sha256 1MB
  $receipt.updater_manifest_sha256=Hash $manifest
  $receipt.stage='bounded startup files'
  $paths=@('C:\ProgramData\K98\S11\AutomaticStartupPolicy.json')
  if($action.recognized){
   $receipt.action_file=Get-P02BindingFact $action.script_path
   if($action.script_path -match '^C:\\ProgramData\\K98\\S11\\runtime\\'){$paths+=Join-Path (Split-Path -Parent $action.script_path) 'AutomaticStartupPolicy.json'}
  }
  $runtime='C:\ProgramData\K98\S11\runtime'
  $receipt.runtime_directory=Get-P02BindingFact $runtime -Directory
  $receipt.runtime_inventory_truncated=$false
  if($receipt.runtime_directory.exists -and $receipt.runtime_directory.protected){
   $items=@(Get-ChildItem -LiteralPath $runtime -Directory -Force|Select-Object -First 17)
   $receipt.runtime_inventory_truncated=$items.Count -gt 16
   foreach($item in @($items|Select-Object -First 16)){
    if($item.Name -cmatch '^[0-9a-f-]{36}$' -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){$paths+=Join-Path $item.FullName 'AutomaticStartupPolicy.json'}
   }
  }
  $receipt.policies=@($paths|Select-Object -Unique|ForEach-Object {Get-P02StartupPolicy $_})
  $receipt.updates_directory=Get-P02BindingFact 'C:\ProgramData\K98\S11\updates' -Directory
  $receipt.active_update_exists=Test-Path -LiteralPath 'C:\ProgramData\K98\S11\updates\active.json'
  $receipt.operator_lock_exists=Test-Path -LiteralPath 'C:\ProgramData\K98\S11\updates\operator.lock'
  $receipt.stage='final preservation'
  $afterTask=Get-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
  $after=Export-ScheduledTask -TaskPath '\' -TaskName 'StartDLBotAfterSQL'
  if((Hash ([Text.Encoding]::UTF8.GetBytes($after))) -cne $xmlHash -or $afterTask.Settings.Enabled -or [string]$afterTask.State -cne 'Disabled'){throw 'Startup task changed during read'}
  $null=Read-Bytes 'C:\ProgramData\K98\S11\updater\update-tool.json' $Plan.updater_manifest_sha256 1MB
  $receipt.outcome='passed'
 }catch{
  # Arbitrary task/policy text cannot enter host error messages.
  $receipt.first_failure=@{stage=$receipt.stage;type=$_.Exception.GetType().FullName;hresult=$_.Exception.HResult}
 }
 return [pscustomobject]$receipt
}
if($Action -ceq 'Library'){return}
if($env:COMPUTERNAME -cne 'MINI_AMD' -or $PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Exact lab Windows PowerShell 5.1 required'}
if($PacketRoot -cnotmatch '^C:\\Program Files\\K98-P02-StartupBinding-[0-9]{17}$'){throw 'Exact fresh packet root required'}
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if($id.Name -cne 'MINI_AMD\K98LabAdmin' -or $id.Owner.Value -cne 'S-1-5-32-544' -or -not ([Security.Principal.WindowsPrincipal]::new($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Retained elevated lab account required'}
$script:c=@{sid=$id.User.Value}
# Functions are injected only by the sealed host launcher, from pinned source.
Assert-Protected $PacketRoot
$plan=[Text.Encoding]::UTF8.GetString((Read-Bytes (Join-Path $PacketRoot 'plan.json') $PlanSHA256 1MB))|ConvertFrom-Json
if($plan.schema -cne 'p02-startup-binding-read/1' -or $plan.guest_directory -cne $PacketRoot -or $plan.production_eligible -ne $false){throw 'Startup binding plan differs'}
$prior='C:\Program Files\K98-P02-Readiness-20261124082204150\receipt.json'
$null=Read-Bytes $prior $plan.accepted_receipt_sha256 1MB
foreach($name in @('P02ReadinessConnection','P02ReadinessCommand','P02ReadinessReader')){
 $owner=Get-Variable -Name $name -Scope Global -ErrorAction SilentlyContinue
 if($null -ne $owner -and $null -ne $owner.Value){throw 'Earlier physical read owner remains retained'}
}
Write-Record (Join-Path $PacketRoot 'guest-intent.json') @{started_utc=[datetime]::UtcNow.ToString('o');plan_sha256=$PlanSHA256}
$receipt=Invoke-P02StartupBindingRead $plan $id.User.Value $PacketRoot
Write-Record (Join-Path $PacketRoot 'receipt.json') $receipt
[pscustomobject]@{outcome=$receipt.outcome;receipt_sha256=(Hash (Read-Bytes (Join-Path $PacketRoot 'receipt.json') '' 1MB));sql_connections_opened=0;startup_actions=0;physical_custody_retained=$receipt.physical_custody_retained}
