# Execute the real v4 orchestration with deterministic external outcomes.
# No production paths, SQL, scheduled tasks or Bot processes are used here.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Deploy-K98Release.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
$f=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-ReleaseSteps'},$true)
. ([scriptblock]::Create($f.Extent.Text))
function Write-NewRecord([string]$Path,$Value){[IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Compress))}
function Read-Control([string]$Path){Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}
function Assert($Value,$Message){if(-not $Value){throw $Message}}
function Invoke-ReleaseScript($Call) {
 $script:events.Add($Call.name)
 if($script:failAt -and $Call.name -ceq $script:failAt){throw 'Simulated process loss before outer acknowledgement'}
 if($Call.name.EndsWith('-verify')){return $script:states[$Call.name].Dequeue()}
 return 0
}
$root=Join-Path ([IO.Path]::GetTempPath()) ('k98-combined-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($root)
$steps=@('sql','source','seed','start','readiness')|ForEach-Object {[pscustomobject]@{id=$_;kind=$_;verify=@{name=($_+'-verify')};apply=@{name=($_+'-apply')}}}
$cases=0
foreach($interruption in @('sql','source','seed','start','readiness')) {
 $directory=Join-Path $root $interruption;$null=[IO.Directory]::CreateDirectory($directory)
 $script:events=[Collections.Generic.List[string]]::new();$script:states=@{}
 foreach($s in $steps){$q=[Collections.Generic.Queue[int]]::new();$q.Enqueue(10);$q.Enqueue(0);$script:states[$s.id+'-verify']=$q}
 $script:failAt=$interruption+'-apply'
 $failed=$false;try{Invoke-ReleaseSteps $steps $directory 'release' 4}catch{$failed=$true}
 Assert $failed 'Interruption was not exercised'
 Assert (Test-Path (Join-Path $directory ($interruption+'.intent.json'))) 'Missing durable intent before effect'
 Assert (-not(Test-Path (Join-Path $directory ($interruption+'.complete.json')))) 'Interrupted effect acknowledged'
 $firstEvents=@($events)
 $script:failAt=$null;$script:events.Clear();$passed=$false
 foreach($s in $steps){
  $q=[Collections.Generic.Queue[int]]::new()
  # The interruption happened after the external effect, before its acknowledgement.
  if(-not $passed){$q.Enqueue(0)}else{$q.Enqueue(10);$q.Enqueue(0)}
  if($s.id -ceq $interruption){$passed=$true}
  $script:states[$s.id+'-verify']=$q
 }
 Invoke-ReleaseSteps $steps $directory 'release' 4
 foreach($s in $steps){Assert (@(@($firstEvents)+@($events)|Where-Object {$_ -ceq ($s.id+'-apply')}).Count -eq 1) ('Effect repeated or skipped: '+$s.id)}
 # A further resume verifies every completed effect without applying any stage.
 $script:events.Clear()
 foreach($s in $steps){$q=[Collections.Generic.Queue[int]]::new();$q.Enqueue(0);$script:states[$s.id+'-verify']=$q}
 Invoke-ReleaseSteps $steps $directory 'release' 4
 Assert (@($events|Where-Object {$_ -like '*-apply'}).Count -eq 0) 'Completed release repeated'
 $cases++
}
foreach($damage in @('release','step','stage')) {
 $directory=Join-Path $root ('receipt-'+$damage);$null=[IO.Directory]::CreateDirectory($directory)
 $record=@{stage='starting';release_id='release';step='sql'}
 if($damage -eq 'release'){$record.release_id='other'}else{$record[$damage]='other'}
 Write-NewRecord (Join-Path $directory 'sql.intent.json') $record
 $script:events.Clear();$failed=$false
 try{Invoke-ReleaseSteps @($steps[0]) $directory 'release' 4}catch{$failed=$true}
 Assert $failed 'Damaged receipt accepted';Assert ($events.Count -eq 0) 'Damaged receipt reached external verifier';$cases++
}
foreach($kind in @('sql','source','seed','readiness','start')) {
 $directory=Join-Path $root ('safe-'+$kind);$null=[IO.Directory]::CreateDirectory($directory)
 $script:events=[Collections.Generic.List[string]]::new();$script:states=@{}
 $q=[Collections.Generic.Queue[int]]::new();$q.Enqueue(11);$q.Enqueue(0);$script:states[$kind+'-verify']=$q
 Write-NewRecord (Join-Path $directory ($kind+'.intent.json')) @{stage='starting';release_id='release';step=$kind}
 $failed=$false
 try {Invoke-ReleaseSteps @($steps|Where-Object {$_.id -ceq $kind}) $directory 'release' 4}catch{$failed=$true}
 Assert ($failed -eq ($kind -ceq 'start')) 'Safe continuation/start outcome differs'
 Assert (@($events|Where-Object {$_ -like '*-apply'}).Count -eq $(if($kind -ceq 'start'){0}else{1})) 'Unexpected continuation count'
 $cases++
}
foreach($observed in @(10,20)) {
 $directory=Join-Path $root ('unknown-'+$observed);$null=[IO.Directory]::CreateDirectory($directory)
 $script:events=[Collections.Generic.List[string]]::new();$script:states=@{}
 $q=[Collections.Generic.Queue[int]]::new();$q.Enqueue($observed);$script:states['sql-verify']=$q
 Write-NewRecord (Join-Path $directory 'sql.intent.json') @{stage='starting';release_id='release';step='sql'}
 $failed=$false;try{Invoke-ReleaseSteps @($steps[0]) $directory 'release' 4}catch{$failed=$true}
 Assert $failed 'Unknown SQL outcome replayed';Assert ($events.Count -eq 1) 'Unknown SQL reached apply';$cases++
}
[pscustomobject]@{Status='PASS';Cases=$cases;Evidence=$root;ProductionTouched=$false}|ConvertTo-Json -Compress
