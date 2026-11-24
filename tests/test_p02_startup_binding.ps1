param([Parameter(Mandatory=$true)][string]$RepoRoot,[Parameter(Mandatory=$true)][string]$TemporaryRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$script:passed=0
function Check([bool]$Value,[string]$Message){if(-not $Value){throw $Message};$script:passed++}
function Parse([string]$Path){$t=$null;$e=$null;$a=[Management.Automation.Language.Parser]::ParseFile($Path,[ref]$t,[ref]$e);if($e.Count){throw ($e|Out-String)};return $a}
$guestAst=Parse (Join-Path $RepoRoot 'scripts/Read-P02StartupBinding.ps1')
$hostAst=Parse (Join-Path $RepoRoot 'scripts/Invoke-P02StartupBinding.ps1')
$libraryAst=Parse (Join-Path $RepoRoot 'scripts/K98-SourceUpdate.ps1')
foreach($name in @('Hash')){
 $f=$libraryAst.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 . ([scriptblock]::Create($f.Extent.Text))
}
foreach($f in @($guestAst.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst]},$true))){. ([scriptblock]::Create($f.Extent.Text))}
function StartupAction([string]$Arguments,[string]$Executable='powershell.exe'){[pscustomobject]@{Arguments=$Arguments;Execute=$Executable;WorkingDirectory='C:\discord_file_downloader'}}
$legacy='-NoProfile -ExecutionPolicy Bypass -File "C:\discord_file_downloader\scripts\start-bot-after-sql.ps1"'
$x=Get-P02StartupAction (StartupAction $legacy)
Check ($x.recognized -and $x.safe_arguments -ceq $legacy) 'Legacy startup action not identified'
$gate='C:\ProgramData\K98\S11\runtime\11111111-1111-1111-1111-111111111111\Start-ReviewedAutomaticStartup.ps1'
$x=Get-P02StartupAction (StartupAction ('-NonInteractive -NoProfile -File "'+$gate+'"'))
Check ($x.recognized -and $x.script_path -ceq $gate) 'Reviewed gate not identified'
foreach($argumentValue in @(
 '-File "C:\private\secrets.ps1"',
 '-File "\\server\share\start.ps1"',
 '-File "C:\discord_file_downloader\scripts\..\secrets.ps1"',
 ($legacy+' -Password hidden-secret'),
 '-EncodedCommand c2VjcmV0',
 '-Command "secret"',
 '-File "C:\discord_file_downloader\scripts\start-bot-after-sql.ps1" & evil',
 ('x'*8192)
)){
 $x=Get-P02StartupAction (StartupAction $argumentValue)
 Check (-not $x.recognized -and $null -eq $x.safe_arguments -and $null -eq $x.script_path -and -not (($x|ConvertTo-Json).Contains('hidden-secret'))) 'Unsafe task details escaped redaction'
}
$x=Get-P02StartupAction (StartupAction $legacy 'C:\evil\powershell.exe')
Check (-not $x.recognized) 'Unreviewed executable accepted'
try{Get-P02StartupAction (StartupAction ('x'*8193));throw 'Missing length refusal'}catch{Check ($_.Exception.Message -ceq 'Startup arguments exceed metadata bound') 'Wrong length refusal'}
# Actual owner-read orchestration, with named external task/filesystem substitutes.
$script:currentName=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$script:currentSid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$script:xml='<Task>retained-private-original</Task>'
$script:exportCount=0;$script:enabled=$false;$script:drift=$false;$script:manifestFailure=$false;$script:writes=@();$script:reads=@();$script:directories=0
function Get-ScheduledTask { [pscustomobject]@{Settings=[pscustomobject]@{Enabled=$script:enabled};State='Disabled';Principal=[pscustomobject]@{UserId=$script:currentName};Actions=@(StartupAction $legacy)} }
function Export-ScheduledTask {$script:exportCount++;if($script:drift -and $script:exportCount -gt 1){return '<Task>changed</Task>'};return $script:xml}
function Write-New([string]$Path,[byte[]]$Bytes){$script:writes+=,@{path=$Path;raw=[Text.Encoding]::UTF8.GetString($Bytes)}}
function Read-Bytes([string]$Path,[string]$Expected,[long]$Limit){$script:reads+=,$Path;if($script:manifestFailure){throw 'fixture secret text must not escape'};return ,[Text.Encoding]::UTF8.GetBytes('{}')}
# Retain the actual metadata function for separate below-boundary tests.
function Get-P02BindingFact([string]$Path,[switch]$Directory){[pscustomobject]@{path=$Path;exists=$true;protected=$true;sha256=('a'*64)}}
function Get-P02StartupPolicy([string]$Path){[pscustomobject]@{file=[pscustomobject]@{path=$Path};binding_read=$true}}
function Test-Path([string]$LiteralPath){return $false}
function Get-ChildItem([string]$LiteralPath,[switch]$Directory,[switch]$Force){
 for($i=0;$i -lt $script:directories;$i++){[pscustomobject]@{Name=('00000000-0000-0000-0000-'+$i.ToString('000000000000'));FullName=($LiteralPath+'\00000000-0000-0000-0000-'+$i.ToString('000000000000'));Attributes=[IO.FileAttributes]::Directory}}
}
$plan=[pscustomobject]@{task_xml_sha256=(Hash ([Text.Encoding]::UTF8.GetBytes($script:xml)));task_principal_sid=$script:currentSid;updater_manifest_sha256=('a'*64)}
$r=Invoke-P02StartupBindingRead $plan $script:currentSid 'C:\fixture'
Check ($r.outcome -ceq 'passed' -and $r.task.operator_matches_task) 'Complete same-account read failed'
Check ($r.sql_connections_opened -eq 0 -and $r.startup_actions -eq 0 -and $r.installation_changes -eq 0) 'Read claimed native actions'
Check ($script:writes.Count -eq 1 -and $script:writes[0].path.EndsWith('original-task.xml')) 'Original XML not confined to guest evidence'
Check (-not (($r|ConvertTo-Json -Depth 20).Contains('retained-private-original'))) 'Raw task XML escaped receipt'
$script:exportCount=0;$r=Invoke-P02StartupBindingRead $plan 'S-1-5-18' 'C:\fixture'
Check ($r.outcome -ceq 'passed' -and -not $r.task.operator_matches_task) 'Different operator identity was hidden'
$script:enabled=$true;$script:reads=@();$script:writes=@();$r=Invoke-P02StartupBindingRead $plan $script:currentSid 'C:\fixture'
Check ($r.outcome -ceq 'failed' -and $script:reads.Count -eq 0 -and $script:writes.Count -eq 0) 'Enabled task reached file inspection'
$script:enabled=$false;$plan.task_principal_sid='S-1-5-18';$r=Invoke-P02StartupBindingRead $plan $script:currentSid 'C:\fixture'
Check ($r.outcome -ceq 'failed' -and $script:reads.Count -eq 0) 'Changed principal reached file inspection'
$plan.task_principal_sid=$script:currentSid;$script:manifestFailure=$true;$script:exportCount=0;$r=Invoke-P02StartupBindingRead $plan $script:currentSid 'C:\fixture'
Check ($r.outcome -ceq 'failed' -and $r.stage -ceq 'updater identity' -and -not (($r|ConvertTo-Json -Depth 20).Contains('fixture secret'))) 'Read failure or secret suppression differs'
$script:manifestFailure=$false;$script:directories=17;$script:exportCount=0;$r=Invoke-P02StartupBindingRead $plan $script:currentSid 'C:\fixture'
Check ($r.outcome -ceq 'passed' -and $r.runtime_inventory_truncated -and $r.policies.Count -eq 17) 'Policy inventory did not preserve truncation'
$script:drift=$true;$script:exportCount=0;$r=Invoke-P02StartupBindingRead $plan $script:currentSid 'C:\fixture'
Check ($r.outcome -ceq 'failed' -and $r.stage -ceq 'final preservation') 'Late task change was accepted'
$script:drift=$false
# Exercise the actual policy projection: unsafe paths cannot expand the read scope.
$policyFunction=$guestAst.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Get-P02StartupPolicy'},$true)
. ([scriptblock]::Create($policyFunction.Extent.Text))
$script:policyText='{"state_directory":"C:\\private\\secrets","seed_plan":{"path":"C:\\private\\credentials.json","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"secret":"do-not-export"}'
function Read-Bytes([string]$Path,[string]$Expected,[long]$Limit){$script:reads+=,$Path;return ,[Text.Encoding]::UTF8.GetBytes($script:policyText)}
$script:reads=@();$r=Get-P02StartupPolicy 'C:\ProgramData\K98\S11\AutomaticStartupPolicy.json'
Check ($r.state_path_supported -eq $false -and $r.seed_path_supported -eq $false -and $script:reads.Count -eq 1) 'Policy expanded to arbitrary paths'
Check (-not (($r|ConvertTo-Json -Depth 10).Contains('do-not-export'))) 'Unknown policy fields escaped projection'
$script:policyText='{"state_directory":"C:\\ProgramData\\K98\\S11\\history\\11111111-1111-1111-1111-111111111111","seed_plan":{"path":"C:\\ProgramData\\K98\\S11\\runtime\\11111111-1111-1111-1111-111111111111\\ManualProcessPairPlan-CANDIDATE.json","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}'
$r=Get-P02StartupPolicy 'C:\ProgramData\K98\S11\AutomaticStartupPolicy.json'
Check ($r.binding_read -and $r.seed_matches_policy -and $r.state.path.StartsWith('C:\ProgramData\K98\S11\history\')) 'Supported policy binding was lost'

# Exact launch block: actual Restricted policy, real bounded bytes, substituted custody.
Check ((Get-ExecutionPolicy) -ceq 'Restricted') 'Launch regression requires real Restricted policy'
$policies=Get-ExecutionPolicy -List|ConvertTo-Json -Compress
$null=[IO.Directory]::CreateDirectory($TemporaryRoot)
$probe='param($Action,$PacketRoot,$PlanSHA256) $global:P02BindingTestDispatch++;[pscustomobject]@{action=$Action;root=$PacketRoot;plan=$PlanSHA256}'
$entry=Join-Path $TemporaryRoot 'Read-P02StartupBinding.ps1'
[IO.File]::WriteAllText($entry,$probe,[Text.UTF8Encoding]::new($false))
$entryHash=Hash ([IO.File]::ReadAllBytes($entry))
$planPath=Join-Path $TemporaryRoot 'plan.json'
[IO.File]::WriteAllText($planPath,(@{files=@{'Read-P02StartupBinding.ps1'=$entryHash}}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$planHash=Hash ([IO.File]::ReadAllBytes($planPath))
$blocks=@($hostAst.FindAll({param($n)$n -is [Management.Automation.Language.ScriptBlockExpressionAst] -and $n.Extent.Text.Contains('$entry=Read-Bytes')},$true))
Check ($blocks.Count -eq 1) 'Exact native launch not found'
$launch=$blocks[0].ScriptBlock.GetScriptBlock()
$helpers='function Assert-Protected($Path){if($global:P02BindingTestCustody){throw "custody refused"}}'
foreach($name in @('Hash','Read-Bytes')){$f=$libraryAst.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true);$helpers+=[Environment]::NewLine+$f.Extent.Text}
$global:P02BindingTestDispatch=0;$global:P02BindingTestCustody=$false
$r=& $launch $TemporaryRoot $planHash $helpers
Check ($r.action -ceq 'Run' -and $r.root -ceq $TemporaryRoot -and $global:P02BindingTestDispatch -eq 1) 'Restricted text launch did not run exact verified body'
$global:P02BindingTestDispatch=0
foreach($fault in @('plan','entry','custody')){
 if($fault -ceq 'entry'){[IO.File]::AppendAllText($entry,' ')}
 if($fault -ceq 'custody'){$global:P02BindingTestCustody=$true}
 try{& $launch $TemporaryRoot $(if($fault -ceq 'plan'){'0'*64}else{$planHash}) $helpers;throw 'Expected launch refusal'}catch{Check (-not $_.Exception.Message.Contains('Expected launch refusal')) 'Launch accepted tampering'}
}
Check ($global:P02BindingTestDispatch -eq 0) 'Refused launch executed the body'
Check ((Get-ExecutionPolicy -List|ConvertTo-Json -Compress) -ceq $policies) 'Policy changed'
Write-Output ('PASS: '+$script:passed+' startup binding checks; actual PS5.1 Restricted launch, explicit task/filesystem/custody substitutes, no VM or SQL contact')
