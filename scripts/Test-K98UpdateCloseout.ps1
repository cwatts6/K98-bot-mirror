# Actual outer closeout statements; disposable files, substituted ACL checks.
# All external deployment operations trap. No live task/process/SQL calls.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1') -Action Library
function Assert-Protected([string]$Path){}
function Write-New([string]$Path,[byte[]]$Bytes){[IO.File]::WriteAllBytes($Path,$Bytes)}
function Unexpected-Runner {throw 'Deployment runner reached during historical closeout'}
$powershell='Unexpected-Runner'
$root=Join-Path ([IO.Path]::GetTempPath()) ('k98-closeout-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($root)
$source=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Update-K98.ps1'),[ref]$null,[ref]$null)
$outer=$source.EndBlock.Statements[-1].Body.Statements
$start=0
for($i=0;$i -lt $outer.Count;$i++){if($outer[$i].Extent.Text -ceq '$manifest=Read-Json $prepared.manifest $prepared.manifest_sha256'){$start=$i;break}}
if(-not $start){throw 'Production closeout statements missing'}
$closeout=[scriptblock]::Create(($outer[$start..($outer.Count-1)]|ForEach-Object {$_.Extent.Text}) -join "`n")
$checks=0
foreach($damage in @('none','wrong-release','missing-stage','wrong-target','amendment','interrupted-write')) {
 $work=Join-Path $root $damage;$null=[IO.Directory]::CreateDirectory($work)
 $stage=Join-Path $work 'release-fixture';$null=[IO.Directory]::CreateDirectory((Join-Path $stage '.receipts'))
 $active=Join-Path $work 'active.json';Write-Record $active @{release_id='fixture'}
 $policyPath=Join-Path $work 'policy.json';Write-Record $policyPath @{state_directory=$work}
 $manifestPath=Join-Path $work 'release.json'
 $manifest=@{release_id='fixture';policy=@{path=$policyPath;sha256=(Hash ([IO.File]::ReadAllBytes($policyPath)))};steps=@(@{id='sql'},@{id='source'},@{id='seed'},@{id='start'},@{id='readiness'})}
 Write-Record $manifestPath $manifest
 $raw=[IO.File]::ReadAllBytes($manifestPath);[IO.File]::WriteAllBytes((Join-Path $stage '.release.json'),$raw)
 $runner=Join-Path $work 'Deploy-K98Release.ps1';Write-New $runner ([byte[]]@(1))
 $prepared=[pscustomobject]@{manifest=$manifestPath;manifest_sha256=(Hash $raw);runner_sha256=(Hash ([byte[]]@(1)));release_id='fixture';target=('a'*40)}
 foreach($s in $manifest.steps){Write-Record (Join-Path $stage ('.receipts\'+$s.id+'.complete.json')) @{stage='verified';release_id='fixture';step=$s.id}}
 $ready=@{release_id='fixture';target=('a'*40);discord_status='online';import_export=@{status='degraded';reason='historical fixture'}}
 if($damage -eq 'wrong-release'){$ready.release_id='other'}
 if($damage -eq 'wrong-target'){$ready.target='b'*40}
 Write-Record (Join-Path $stage 'readiness-status.json') $ready
 if($damage -eq 'missing-stage'){Remove-Item -LiteralPath (Join-Path $stage '.receipts\sql.complete.json')}
 if($damage -eq 'amendment'){Write-Record (Join-Path $stage '.amendment-selected.json') @{amendment_id='other'}}
 $before=@{};Get-ChildItem -LiteralPath $stage -Recurse -File|ForEach-Object {$before[$_.FullName]=Hash ([IO.File]::ReadAllBytes($_.FullName))}
 $realWrite=${function:Write-AtomicRecord}
 if($damage -eq 'interrupted-write'){
  function Write-AtomicRecord([string]$Path,$Value){Write-Record (Join-Path (Split-Path -Parent $Path) 'pending-fixture') $Value;throw 'Simulated lost closeout write'}
 }
 $failed=$false;try{& $closeout}catch{$failed=$true}
 if($failed -ne ($damage -ne 'none')){throw ('Unexpected closeout outcome: '+$damage)}
 if($damage -ne 'none' -and -not(Test-Path $active)){throw 'Failed closeout removed active pointer'}
 if($damage -eq 'interrupted-write'){
  ${function:Write-AtomicRecord}=$realWrite
  & $closeout
  if(-not(Test-Path (Join-Path $work 'pending-fixture'))){throw 'Interrupted evidence removed'}
 }
 if($damage -in @('none','interrupted-write')){
  if((Test-Path $active) -or -not(Test-Path (Join-Path $work 'verified.json'))){throw 'Atomic closeout incomplete'}
 }
 foreach($p in $before.Keys){if((Hash ([IO.File]::ReadAllBytes($p))) -cne $before[$p]){throw 'Historical stage evidence mutated'}}
 $checks++
}
@{status='PASS';checks=$checks;production_touched=$false;fixture=$root}|ConvertTo-Json -Compress
