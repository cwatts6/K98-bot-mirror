# Local function-level Windows regression tests. No task, SQL or production calls.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Update adapter parse failure'}
$definitions=$ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)
foreach($definition in $definitions){. ([scriptblock]::Create($definition.Extent.Text.Replace('$PSScriptRoot',("'"+$PSScriptRoot.Replace("'","''")+"'"))))}
$passed=0
function Check([bool]$value,[string]$message){if(-not $value){throw $message};$script:passed++}
function Reject([scriptblock]$call,[string]$pattern){try{& $call;throw 'TEST_DID_NOT_REJECT'}catch{if($_.Exception.Message -notlike $pattern){throw};$script:passed++}}
$fixture=Join-Path (Split-Path -Parent $PSScriptRoot) ('.codex_artifacts\update-test-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory((Join-Path $fixture 'docs\reference'))
$file=Join-Path $fixture 'docs\reference\note.md'
[IO.File]::WriteAllText($file,'fixture')
$trusted=[Security.AccessControl.DirectorySecurity]::new()
$trusted.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
$untrusted=[Security.AccessControl.DirectorySecurity]::new()
$untrusted.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-545'))
$script:deny='';$script:visited=[Collections.Generic.List[string]]::new()
function Get-Acl([string]$LiteralPath){$script:visited.Add($LiteralPath);if($LiteralPath -ceq $script:deny){return $script:untrusted};return $script:trusted}
Check (Test-UpdateCanRefresh $fixture 'no-deployment' -PrepareOnly) 'Unstaged preparation must remain refreshable'
foreach($marker in @('deployment-request.json','deployment-drained-test.json','release-test')) {
 $state=Join-Path $fixture ([guid]::NewGuid().ToString('N'))
 $null=[IO.Directory]::CreateDirectory($state)
 $path=Join-Path $state $marker
 if($marker -eq 'release-test'){$null=[IO.Directory]::CreateDirectory($path);[IO.File]::WriteAllText((Join-Path $path '.release.json'),'{}')}else{[IO.File]::WriteAllText($path,'{}')}
 Check (-not(Test-UpdateCanRefresh $state 'test')) 'Started deployment must retain its active release'
 Reject {Test-UpdateCanRefresh $state 'test' -PrepareOnly} '*without -PrepareOnly*'
 Check (Test-Path -LiteralPath $path) 'Resume classification must preserve existing evidence'
}
$emptyState=Join-Path $fixture 'empty-stage-state'
$emptyStage=Join-Path $emptyState 'release-test'
$null=[IO.Directory]::CreateDirectory($emptyStage)
Check (Test-UpdateCanRefresh $emptyState 'test' -PrepareOnly) 'Empty pre-manifest stage must permit fresh preparation'
Check (Test-Path -LiteralPath $emptyStage) 'Empty historical stage must not be deleted'
$script:deny=$emptyStage
Reject {Test-UpdateCanRefresh $emptyState 'test'} '*Protected owner differs*'
$script:deny=''
[IO.File]::WriteAllText((Join-Path $emptyStage 'unexpected.bin'),'partial')
Check (-not(Test-UpdateCanRefresh $emptyState 'test')) 'Missing manifest alone must not allow refresh'
Reject {Test-UpdateCanRefresh $emptyState 'test' -PrepareOnly} '*without -PrepareOnly*'
Assert-Protected $file
Check ($visited.Contains((Join-Path $fixture 'docs'))) 'Ancestor traversal skipped docs'
Check ($visited.Contains([IO.Path]::GetPathRoot($file))) 'Ancestor traversal did not reach volume root'
$script:deny=Join-Path $fixture 'docs'
Reject {Assert-Protected $file} ('*Protected owner differs: '+$deny+'*')
$c=[pscustomobject]@{root=$fixture;source_members=@([pscustomobject]@{path='docs/reference/note.md';deleted=$false;added=$false})}
Reject {Assert-UpdatePaths} ('*Protected owner differs: '+$deny+'*')
$script:deny=''
$c.source_members=@([pscustomobject]@{path='new/deep/file.py';deleted=$false;added=$true})
Assert-UpdatePaths;$passed++
$null=[IO.Directory]::CreateDirectory((Join-Path $fixture 'corex'))
[IO.File]::WriteAllText((Join-Path $fixture 'corex\note.txt'),'untracked fixture')
$c.source_members=@([pscustomobject]@{path='CoreX/helper.py';deleted=$false;added=$true})
Reject {Assert-UpdatePaths} '*Live parent spelling differs*'
$c.source_members=@([pscustomobject]@{path='corex/helper.py';deleted=$false;added=$true})
Assert-UpdatePaths;$passed++
$c.source_members=@([pscustomobject]@{path='docs/reference/note.md';deleted=$false;added=$true})
Reject {Assert-UpdatePaths} '*New tracked path already exists*'
$c.source_members=@([pscustomobject]@{path='docs/reference';deleted=$false;added=$true})
Reject {Assert-UpdatePaths} '*New tracked path already exists*'
$c.source_members=@([pscustomobject]@{path='docs/reference/note.md/child.py';deleted=$false;added=$true})
Reject {Assert-UpdatePaths} '*Source parent is not a directory*'
$c.source_members=@([pscustomobject]@{path='../outside.py';deleted=$false})
Reject {Assert-UpdatePaths} '*Unsafe source member*'

# Isolate Git config validation from custody, which was exercised above.
function Assert-Protected([string]$Path) {}
function Read-Bytes([string]$Path,[string]$Expected='', [long]$Limit=1MB){return ,([byte[]]@(1))}
function Get-Item {return [pscustomobject]@{PSIsContainer=$true}}
function Test-Path {return $false}
$script:gitMetadataChecked=$true
$script:settings="core.quotepath`nfalse`0core.bare`nfalse`0"
$script:calls=[Collections.Generic.List[string]]::new()
function Invoke-GitWorker([string]$Arguments){$script:calls.Add($Arguments);if($Arguments -eq 'config --local --no-includes --null --list'){return $script:settings};return 'EXPECTED'}
Check ((Git 'rev-parse HEAD') -ceq 'EXPECTED') 'core.quotepath blocked routine update'
foreach($key in @('include.path','core.sshcommand','filter.x.smudge','credential.helper')) {
 $script:settings=$key+"`nunsafe`0";$calls.Clear()
 Reject {Git 'rev-parse HEAD'} '*outside reviewed non-executable allowlist*'
 Check ($calls.Count -eq 1) 'Unsafe config reached Git operation'
}

# A base interpreter without win32file must never be selected by the verifier.
function Fake-Venv {$script:venvCalls++;$script:verifyArgs=@($args);$global:LASTEXITCODE=0}
function Fake-Base {throw 'BASE_PYTHON_SELECTED'}
$script:venvCalls=0
$c=[pscustomobject]@{venv=@{path='Fake-Venv';sha256='a'*64};old_plan=@{Python='Fake-Base'};extra_members=@([pscustomobject]@{name='Verify-NewPair.py';sha256='b'*64})}
$ExpectedBindingsSHA256='c'*64
Verify-Native
Check ($venvCalls -eq 1) 'Native verifier did not use installed venv'
Check ('--preflight' -notin $verifyArgs) 'Successor verification selected predecessor'
Verify-Native -Preflight
Check ('--preflight' -in $verifyArgs) 'Preflight did not select complete predecessor source check'

# Retained cohorts may gain new captures, but an existing held/captured row
# cannot disappear or change during deployment.
$c=[pscustomobject]@{expected_preparation=@([pscustomobject]@{PreparationID='old';State='captured';Version=6});expected_resources=@();account='fixture'}
$script:retained=@($c.expected_preparation)+@([pscustomobject]@{PreparationID='new';State='captured';Version=6})
function Retained-Preparations {return ,$script:retained}
function Rows([string]$Query){return ,@()}
Assert-Held;$passed++
$script:retained=@()
Reject {Assert-Held} '*Retained preparation changed*'
$script:retained=@([pscustomobject]@{PreparationID='old';State='unavailable';Version=7})
Reject {Assert-Held} '*Retained preparation changed*'
$script:retained=$c.expected_preparation
$script:streams=@([pscustomobject]@{StreamID='stream';SessionID='new-session'})
function Rows([string]$Query){return ,$script:streams}
function New-Journal {return @{publication='verified-by-separate-test'}}
function Assert-NewSession($Journal) {}
function Sessions {return ,@([pscustomobject]@{SessionID='new-session'})}
Reject {Assert-Held} '*Open provider stream blocks release*'
Assert-Held -SuccessorRunning;$passed++
$script:streams=@([pscustomobject]@{StreamID='stream';SessionID='old-session'})
Reject {Assert-Held -SuccessorRunning} '*unexpected session*'
# Online markers and a successful SQL/native check do not prove import/export health.
$online="[BOOT] full_startup_sequence completed successfully`nLogged in as bot"
$health=Import-ExportStatus $online
Check ($health.status -ceq 'degraded') 'Startup-only evidence was treated as healthy'
Check ($health.reason -ceq 'fresh_import_export_health_evidence_unavailable') 'Missing evidence not explicit'
Check (-not $health.provider_delivery_verified) 'Provider delivery incorrectly certified'
foreach($failure in @('S11 export admission remains closed','Export admission disabled:','Export coordinator unavailable')) {
 $health=Import-ExportStatus ($online+"`n"+$failure)
 Check ($health.reason -ceq 'runtime_admission_unavailable') 'Runtime failure not classified'
}
# Exercise the full readiness gate with a real temporary log and stub only the
# separately tested native/SQL/source boundaries. Old log markers are excluded.
$null=[IO.Directory]::CreateDirectory((Join-Path $fixture 'logs'))
$logPath=Join-Path $fixture 'logs\log.txt'
$oldText=$online+"`n"
[IO.File]::WriteAllText($logPath,$oldText,[Text.UTF8Encoding]::new($false))
$script:offset=([Text.Encoding]::UTF8.GetByteCount($oldText))
$c=[pscustomobject]@{root=$fixture;target='b'*40;release_id='fixture-release';new_pins=@{}}
$script:statusRecord=$null
function Assert-Drained {param([switch]$SuccessorRunning)}
function Assert-Source($Pins,$Commit) {}
function Seed-Complete {return $true}
function Verify-Native {}
function Read-Json([string]$Path,[string]$Expected='') {
 if($Path.EndsWith('start-requested.json')){return @{log_offset=$script:offset}}
 return $script:statusRecord
}
function Test-Path {param([string]$LiteralPath);return $null -ne $script:statusRecord}
function Write-Record([string]$Path,$Value){$script:statusRecord=$Value}
Check (-not(Check-Readiness)) 'Old startup markers satisfied new readiness'
Check ($null -eq $statusRecord) 'Incomplete startup wrote a readiness status'
[IO.File]::AppendAllText($logPath,$online)
Check (Check-Readiness) 'Online successor did not produce explicit degraded readiness'
Check ($statusRecord.import_export.status -ceq 'degraded') 'Status receipt omitted degradation'
Check ($statusRecord.release_id -ceq 'fixture-release') 'Status receipt not release-bound'
Check (Check-Readiness) 'Repeated verification did not retain matching status'
[IO.File]::AppendAllText($logPath,"`nExport coordinator unavailable")
Reject {Check-Readiness} '*Readiness classification changed*'
[pscustomobject]@{Status='PASS';Cases=$passed;Evidence=$fixture;ProductionTouched=$false}|ConvertTo-Json -Compress
