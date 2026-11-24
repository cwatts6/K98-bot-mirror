param([string]$Source,[string]$Case,[string]$Trace,[string]$Fixture)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($Source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Packaged source does not parse in Windows PowerShell 5.1'}
$action=if($Case -like 'verify_*'){'VerifyStart'}else{'ApplyStart'}
$switch=$ast.FindAll({param($n) $n -is [Management.Automation.Language.SwitchStatementAst] -and $n.Condition.Extent.Text -ceq '$Action'},$true)
if($switch.Count -ne 1){throw 'Exact source action switch required'}
$clause=@($switch[0].Clauses | Where-Object {$_.Item1.Value -ceq $action})
if($clause.Count -ne 1){throw 'Exact action required'}
$body=$clause[0].Item2.Extent.Text
$body=$body.Substring(1,$body.Length-2).Replace('[Diagnostics.Stopwatch]::StartNew()','(New-TestWatch)').Replace('$PSScriptRoot','$Fixture')
function Note([string]$Value){[IO.File]::AppendAllText($Trace,$Value+"`n")}
$script:watch=[pscustomobject]@{Elapsed=[pscustomobject]@{TotalSeconds=0}}
function New-TestWatch {return $script:watch}
function Start-Sleep {param($Seconds);$script:watch.Elapsed.TotalSeconds+=60;Note 'wait'}
function Assert-Drained {}
function Assert-Source {}
function Seed-Complete {return $true}
function Assert-Task {
 $task=[pscustomobject]@{Enabled=$false}
 $task|Add-Member ScriptMethod Run {param($unused);Note 'start'}
 return $task
}
function Write-Record {param($Path,$Value);Note 'start_request'}
function Get-Item {param($LiteralPath);return @{Length=0}}
function Get-ChildItem {
 param($LiteralPath,$Filter,[switch]$File)
 if($Filter -and $Case -ne 'verify_fresh'){return [pscustomobject]@{FullName='journal'}}
}
function Test-Path {param($LiteralPath);return $Case -ne 'verify_fresh'}
function New-Journal {Note 'journal';return @{}}
function Assert-NewSession {param($Journal);Note 'session'}
$script:checks=0
function Verify-Native {
 $script:checks++;Note 'verify'
 if($Case -eq 'hard_failure'){throw 'fixture SQL failure after admission'}
 if($Case -in @('timeout','verify_pending')){return $false}
 if($Case -eq 'pending_success' -and $script:checks -eq 1){return $false}
 return $true
}
$c=[pscustomobject]@{root=$Fixture;new_state_directory=$Fixture;new_pins=@{};target='fixture';release_id='fixture'}
$newGate='fixture'
try {. ([scriptblock]::Create($body))}catch{Note ('failure: '+$_.Exception.Message);exit 1}
