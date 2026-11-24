param([Parameter(Mandatory=$true)][string]$RepoRoot,[Parameter(Mandatory=$true)][string]$OriginalHostPath,[Parameter(Mandatory=$true)][string]$TemporaryRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$script:passed=0
function Check([bool]$Value,[string]$Message){if(-not $Value){throw $Message};$script:passed++}
function Parse([string]$Path){$tokens=$null;$errors=$null;$a=[Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors);if($errors.Count){throw ($errors|Out-String)};return $a}
function Block($Ast,[string]$Marker){
 $found=@($Ast.FindAll({param($n) $n -is [Management.Automation.Language.ScriptBlockExpressionAst] -and $n.Extent.Text.Contains($Marker)},$true))
 if($found.Count -ne 1){throw ('Expected one actual block: '+$Marker)}
 return $found[0].ScriptBlock.GetScriptBlock()
}
function Reject([scriptblock]$Call,[string]$Message){
 try{& $Call;throw 'Expected refusal did not occur'}catch{Check ($_.Exception.Message.Contains($Message)) ('Wrong refusal: '+$_.Exception.Message)}
}
Check ((Get-ExecutionPolicy) -ceq 'Restricted') 'This regression must run under actual Restricted policy'
$policies=Get-ExecutionPolicy -List|ConvertTo-Json -Compress
$ast=Parse (Join-Path $RepoRoot 'scripts/Invoke-P02ReleaseReadiness.ps1')
$old=Parse $OriginalHostPath
foreach($name in @('Assert-P02PriorReadJob','Get-P02ReadJobDiagnostics')){
 $f=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true))
 Check ($f.Count -eq 1) ('Missing actual helper '+$name)
 . ([scriptblock]::Create($f[0].Extent.Text))
}
$newLaunch=Block $ast 'Copied read runner differs'
$oldLaunch=Block $old 'Copied read runner differs'
$null=[IO.Directory]::CreateDirectory($TemporaryRoot)
$entry=Join-Path $TemporaryRoot 'release_readiness_read.ps1'
$probe='param([string]$Action,[string]$PlanSHA256,[string]$PacketRoot) $global:P02TestDispatch++;[pscustomobject]@{action=$Action;root=$PacketRoot;plan=$PlanSHA256}'
[IO.File]::WriteAllText($entry,$probe,[Text.UTF8Encoding]::new($false))
$entryHash=(Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant()
$plan=Join-Path $TemporaryRoot 'plan.json'
[IO.File]::WriteAllText($plan,(@{files=@{'release_readiness_read.ps1'=$entryHash}}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$planHash=(Get-FileHash -LiteralPath $plan -Algorithm SHA256).Hash.ToLowerInvariant()
$custody='function Assert-Protected([string]$Path){if($global:P02TestCustodyFailure){throw "surrogate custody refused"}}'
$global:P02TestCustodyFailure=$false;$global:P02TestDispatch=0
Reject {& $oldLaunch $TemporaryRoot $planHash $custody} 'running scripts is disabled'
Check ($global:P02TestDispatch -eq 0) 'Old file launch entered the body'
$result=& $newLaunch $TemporaryRoot $planHash $custody
Check ($result.action -ceq 'Run' -and $result.root -ceq $TemporaryRoot -and $result.plan -ceq $planHash -and $global:P02TestDispatch -eq 1) 'Authenticated text did not receive its exact root/plan'
Check ((Get-ExecutionPolicy -List|ConvertTo-Json -Compress) -ceq $policies) 'Execution policy changed'
$global:P02TestDispatch=0
Reject {& $newLaunch $TemporaryRoot ('0'*64) $custody} 'Copied plan differs'
[IO.File]::AppendAllText($entry,' ')
Reject {& $newLaunch $TemporaryRoot $planHash $custody} 'Copied read runner differs'
$global:P02TestCustodyFailure=$true
Reject {& $newLaunch $TemporaryRoot $planHash $custody} 'surrogate custody refused'
Check ($global:P02TestDispatch -eq 0) 'Refused launch entered the body'
$global:P02TestCustodyFailure=$false
$priorPath='C:\Program Files\K98-P02-Readiness-20261123214834251'
$reason=[Management.Automation.PSSecurityException]::new(('File '+$priorPath+'\release_readiness_read.ps1 cannot be loaded because running scripts is disabled on this system.'))
$child=[pscustomobject]@{Id=645;State='Failed';JobStateInfo=[pscustomobject]@{Reason=$reason};Error=@()}
$job=[pscustomobject]@{Id=644;State='Failed';ChildJobs=@($child)}
Assert-P02PriorReadJob $job
Check ($job.ChildJobs[0].State -ceq 'Failed') 'Original job mutated'
$job.Id=643;Reject {Assert-P02PriorReadJob $job} 'Exact retained failed read job';$job.Id=644
$child.JobStateInfo.Reason=[Exception]::new('other failure');Reject {Assert-P02PriorReadJob $job} 'recorded script-load refusal'
$child.JobStateInfo.Reason=$reason
$diagnostic=Get-P02ReadJobDiagnostics $job
Check ($diagnostic[0].reason.Contains('running scripts is disabled')) 'Original error hidden'
$long=[Exception]::new(('x'*9000));$record=[pscustomobject]@{Exception=$long}
$bounded=Get-P02ReadJobDiagnostics ([pscustomobject]@{ChildJobs=@(1..6|ForEach-Object {[pscustomobject]@{Id=$_;State='Failed';JobStateInfo=[pscustomobject]@{Reason=$long};Error=@(1..10|ForEach-Object {$record})}})})
Check ($bounded.Count -eq 4 -and $bounded[0].reason.Length -eq 8192 -and $bounded[0].errors.Count -eq 8 -and $bounded[0].errors[0].Length -eq 8192) 'Diagnostic bounds differ'
# Run the actual predecessor block with explicit filesystem/identity substitutes.
$priorBlock=Block $ast 'Prior read execution marker exists'
$env:COMPUTERNAME='MINI_AMD'
$script:marker='';$script:hashDrift=$false
function Get-FileHash([string]$LiteralPath,[string]$Algorithm){[pscustomobject]@{Hash=$(if($script:hashDrift){'0'*64}else{'a'*64})}}
function Get-Content([string]$LiteralPath,[switch]$Raw,[string]$Encoding){'{"files":{"probe.ps1":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}'}
function Test-Path([string]$LiteralPath){return ($script:marker -and $LiteralPath.EndsWith($script:marker))}
$result=& $priorBlock $priorPath ('a'*64) $custody
Check ($result.entry_not_started -eq $true) 'Valid non-entry evidence refused'
foreach($marker in @('guest-intent.json','receipt.json')){
 $script:marker=$marker
 Reject {& $priorBlock $priorPath ('a'*64) $custody} 'Prior read execution marker exists'
}
$script:marker=''
foreach($ownerName in @('P02ReadinessConnection','P02ReadinessCommand','P02ReadinessReader')){
 Set-Variable -Name $ownerName -Scope Global -Value ([object]::new())
 Reject {& $priorBlock $priorPath ('a'*64) $custody} 'Prior physical read owner is retained'
 Set-Variable -Name $ownerName -Scope Global -Value $null
}
$script:hashDrift=$true
Reject {& $priorBlock $priorPath ('a'*64) $custody} 'Original guest plan changed'
Check ((Get-ExecutionPolicy -List|ConvertTo-Json -Compress) -ceq $policies) 'Policy changed during refusal checks'
Write-Output ('PASS: '+$passed+' actual launch/predecessor/diagnostic checks; Restricted policy real, guest identity/custody/filesystem and SQL external boundaries substituted; no VM activity')
