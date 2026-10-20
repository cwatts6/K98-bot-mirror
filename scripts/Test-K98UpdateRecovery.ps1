# Continuation proof checks with real bytes and native atomic file replacement.
# Tasks, Git observations and administrative ACLs are fixture substitutes.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Join-Path ([IO.Path]::GetTempPath()) ('k98-recovery-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory((Join-Path $root '.receipts'))
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'),[ref]$null,[ref]$null)
foreach($f in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
 . ([scriptblock]::Create($f.Extent.Text.Replace('$PSScriptRoot',("'"+$root+"'"))))
}
function Assert-Protected([string]$Path){}
function Assert-Drained{}
function Write-New([string]$Path,[byte[]]$Bytes){[IO.File]::WriteAllBytes($Path,$Bytes)}
function Assert-Source($Pins,[string]$Commit){}
function Assert-Task([string]$Gate,[bool]$Disabled){if(-not $Disabled -or $Gate -cne $script:taskGate){throw 'Task differs'}}
function Task {return $script:task}
function Git([string]$Arguments){switch($Arguments){'rev-parse HEAD'{return $c.target};'branch --show-current'{return 'main'};default{return ''}}}
$script:checks=0
function Reject([scriptblock]$Call,[string]$Pattern){$failed=$false;try{& $Call}catch{if($_.Exception.Message -notlike $Pattern){throw};$failed=$true};if(-not $failed){throw 'Expected refusal'};$script:checks++}
$source=Join-Path $root 'source';$null=[IO.Directory]::CreateDirectory($source)
$before=[Text.Encoding]::UTF8.GetBytes("new`r`n");$after=[Text.Encoding]::UTF8.GetBytes("new`n")
$leaf=Join-Path $source 'example.py';Write-New $leaf $before
Write-New (Join-Path $root 'payload.bin') $after
$script:c=[pscustomobject]@{root=$source;release_id='fixture';target=('a'*40);old_gate=@{Path='old.ps1'};old_pins=[pscustomobject]@{};new_pins=[pscustomobject]@{};source_members=@([pscustomobject]@{path='example.py';deleted=$false;target_sha256=(Hash $after);checkout_sha256=@((Hash $before));payload='payload.bin'});new_seed_directory=(Join-Path $root 'seed');new_state_directory=(Join-Path $root 'state');seed_members=@([pscustomobject]@{name='seed.json';sha256=(Hash $after)})}
$taskGate='old.ps1';$newGate='new.ps1'
Write-Record (Join-Path $root '.receipts\source.intent.json') @{stage='starting';step='source';release_id='fixture'}
Assert-SourceContinuation;Install-TargetSourceBytes;Assert-SourceContinuation
if((Hash ([IO.File]::ReadAllBytes($leaf))) -cne (Hash $after)){throw 'Exact byte continuation failed'};$checks++
Write-New $leaf ([byte[]]@(42));Reject {Assert-SourceContinuation} '*unsupported drift*';Write-New $leaf $after
Write-Record (Join-Path $root 'start-requested.json') @{release_id='fixture'}
Reject {Assert-SourceContinuation} '*forbidden after start intent*'
Remove-Item -LiteralPath (Join-Path $root 'start-requested.json')
Write-Record (Join-Path $root '.receipts\seed.intent.json') @{stage='starting';step='seed';release_id='fixture'}
$action=[pscustomobject]@{Arguments='-File old.ps1'}
$actions=[pscustomobject]@{Action=$action};$actions|Add-Member ScriptMethod Item {param($Index);return $this.Action}
$task=[pscustomobject]@{Definition=[pscustomobject]@{Actions=$actions}}
Assert-PartialSeed;$checks++
$null=[IO.Directory]::CreateDirectory($c.new_seed_directory);$null=[IO.Directory]::CreateDirectory($c.new_state_directory)
Write-New (Join-Path $c.new_seed_directory 'seed.json') $after
Assert-PartialSeed;$checks++
$taskGate=$newGate;$action.Arguments='-File new.ps1';Assert-PartialSeed;$checks++
Write-New (Join-Path $c.new_seed_directory 'unknown.json') $after
Reject {Assert-PartialSeed} '*Unknown partial seed member*'
Remove-Item -LiteralPath (Join-Path $c.new_seed_directory 'unknown.json')
Write-New (Join-Path $c.new_seed_directory 'seed.json') ([byte[]]@(42));Reject {Assert-PartialSeed} '*checksum*'
Write-New (Join-Path $c.new_seed_directory 'seed.json') $after
Write-New (Join-Path $c.new_state_directory 'incarnation.json') $after
Reject {Assert-PartialSeed} '*Nonempty successor history*'
@{status='PASS';checks=$checks;production_touched=$false;fixture=$root}|ConvertTo-Json -Compress
