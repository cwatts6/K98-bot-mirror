$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'Deploy-K98Release.ps1'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Release script does not parse'}
$function=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-ReleaseSteps'},$true)
if($null -eq $function){throw 'Missing production orchestration function'}
. ([scriptblock]::Create($function.Extent.Text))

function Assert($condition,[string]$message){if(-not $condition){throw $message}}
function Write-NewRecord([string]$Path,$Value){$Value|ConvertTo-Json -Compress|Set-Content -LiteralPath $Path}
function Invoke-ReleaseScript($invocation) {
    $script:events.Add($invocation.name)
    if($invocation.name -eq 'verify') {return $script:outcomes.Dequeue()}
    return $script:applyResult
}
$root=Join-Path ([IO.Path]::GetTempPath()) ('k98-release-test-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $root
$step=[pscustomobject]@{id='source';apply=@{name='apply'};verify=@{name='verify'}}
$cases=@(
    @{name='success';states=@(10,0);apply=0;intent=$false;expected='verify,apply,verify';fails=$false},
    @{name='already-applied';states=@(0);apply=0;intent=$false;expected='verify';fails=$false},
    @{name='unknown';states=@(20);apply=0;intent=$false;expected='verify';fails=$true},
    @{name='apply-fails';states=@(10);apply=1;intent=$false;expected='verify,apply';fails=$true},
    @{name='ack-lost';states=@(10,20);apply=0;intent=$false;expected='verify,apply,verify';fails=$true},
    @{name='interrupted-pending';states=@(10);apply=0;intent=$true;expected='verify';fails=$true},
    @{name='interrupted-applied';states=@(0);apply=0;intent=$true;expected='verify';fails=$false}
    @{name='previously-verified-now-missing';states=@(10);apply=0;intent=$false;complete=$true;expected='verify';fails=$true}
)
foreach($case in $cases) {
    $directory=Join-Path $root $case.name
    $null=New-Item -ItemType Directory -Path $directory
    $script:events=[Collections.Generic.List[string]]::new()
    $script:outcomes=[Collections.Generic.Queue[int]]::new()
    foreach($value in $case.states){$script:outcomes.Enqueue($value)}
    $script:applyResult=$case.apply
    if($case.intent){Write-NewRecord (Join-Path $directory 'source.intent.json') @{stage='starting'}}
    if($case.complete){Write-NewRecord (Join-Path $directory 'source.complete.json') @{stage='verified'}}
    $failed=$false
    try {Invoke-ReleaseSteps @($step) $directory 'fixture-release'} catch {$failed=$true}
    Assert ($failed -eq $case.fails) ('Wrong outcome: '+$case.name)
    Assert (($script:events -join ',') -ceq $case.expected) ('Unexpected replay/order: '+$case.name)
    Assert ((Test-Path (Join-Path $directory 'source.complete.json')) -eq ((-not $case.fails) -or [bool]$case.complete)) ('Wrong completion: '+$case.name)
}
[pscustomobject]@{Status='PASS';Cases=$cases.Count;Evidence=$root;ProductionTouched=$false}|ConvertTo-Json -Compress
