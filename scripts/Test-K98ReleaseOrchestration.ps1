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
foreach($name in @('Get-BytesHash','Read-Pinned','Read-IncarnationIssuer')) {
    $definition=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name},$true)
    if($null -eq $definition){throw ('Missing production function: '+$name)}
    . ([scriptblock]::Create($definition.Extent.Text))
}
function Assert-AdminPath([string]$Path){$script:inspected=$Path}
function Read-Control([string]$Path){$script:issuerReads++;return $Path}
$planPath=Join-Path $root 'pinned-plan.json'
$commitPath=Join-Path $root 'runtime\seed\Commit.json'
$planBytes=[Text.UTF8Encoding]::new($false).GetBytes((@{commit_file=$commitPath}|ConvertTo-Json -Compress))
[IO.File]::WriteAllBytes($planPath,$planBytes)
$policy=[pscustomobject]@{seed_plan=@{path=$planPath;sha256=(Get-BytesHash $planBytes)}}
$nonce=[guid]::NewGuid().ToString()
$expected=Join-Path (Join-Path (Join-Path $root 'runtime') $nonce) 'AutomaticIssuer.json'
foreach($policyLocation in @('runtime\seed\Policy.json','elsewhere\Policy.json')) {
    # A policy's storage location must not select the runtime incarnation root.
    $script:manifest=@{policy=@{path=(Join-Path $root $policyLocation)}}
    $script:issuerReads=0
    $actual=Read-IncarnationIssuer $policy $nonce
    Assert ($actual -ceq $expected) 'Issuer location did not follow pinned commit_file'
    Assert ($script:inspected -ceq $planPath) 'Seed plan ACL was not checked'
    Assert ($script:issuerReads -eq 1) 'Issuer record not read exactly once'
}
[IO.File]::AppendAllText($planPath,' ')
$script:issuerReads=0;$failed=$false
try {$null=Read-IncarnationIssuer $policy $nonce} catch {$failed=$true}
Assert ($failed -and $script:issuerReads -eq 0) 'Altered plan reached issuer lookup'
[pscustomobject]@{Status='PASS';Cases=($cases.Count+3);Evidence=$root;ProductionTouched=$false}|ConvertTo-Json -Compress
