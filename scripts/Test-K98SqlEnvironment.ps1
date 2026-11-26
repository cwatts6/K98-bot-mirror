# Offline PowerShell-to-JSON contract test. Never connects to SQL or runs updater entrypoints.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$FixturePath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Parse-Script([string]$Name) {
 $tokens=$null;$errors=$null
 $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $Name),[ref]$tokens,[ref]$errors)
 if($errors.Count){throw 'Script parse failure'}
 return $ast
}
$entry=Parse-Script 'Update-K98.ps1'
$library=Parse-Script 'K98-SourceUpdate.ps1'
$assignments=@($entry.FindAll({param($n) $n -is [Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -ceq '$sqlEnvironment'},$true))
$guards=@($entry.FindAll({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Extent.Text.StartsWith('if($sqlEnvironment.Count')},$true))
$bindings=@($entry.FindAll({param($n) $n -is [Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -ceq '$bindings'},$true))
$rowsFunction=$library.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Rows'},$false)
$returns=@($rowsFunction.FindAll({param($n) $n -is [Management.Automation.Language.ReturnStatementAst]},$true))
if($assignments.Count -ne 1 -or $guards.Count -ne 1 -or $bindings.Count -ne 1 -or $returns.Count -ne 1){throw 'Observation source shape differs'}
$table=$bindings[0].Find({param($n) $n -is [Management.Automation.Language.HashtableAst]},$true)
$value=@($table.KeyValuePairs | Where-Object {$_.Item1.Extent.Text -ceq 'sql_environment'})
if($value.Count -ne 1){throw 'SQL environment binding missing'}
$script:Fixture=[IO.File]::ReadAllText($FixturePath)|ConvertFrom-Json
# Preserve the real Rows return expression, including its array-enumeration semantics.
$stub='function Rows([string]$Query) {$rows=@($script:Fixture.rows);'+$returns[0].Extent.Text+'}'
. ([scriptblock]::Create($stub))
. ([scriptblock]::Create($assignments[0].Extent.Text))
. ([scriptblock]::Create($guards[0].Extent.Text))
$serialize='$observation=@{bindings=@{sql_environment='+$value[0].Item2.Extent.Text+'}}; $observation|ConvertTo-Json -Depth 20 -Compress'
. ([scriptblock]::Create($serialize))
