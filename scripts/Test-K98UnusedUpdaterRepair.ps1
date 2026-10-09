# Offline repair regression tests; no production paths or scheduled tasks touched.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'Repair-K98UnusedUpdater.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
foreach($f in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){. ([scriptblock]::Create($f.Extent.Text))}
$passed=0
function Check($v,$m){if(-not $v){throw $m};$script:passed++}
function Reject($call,$pattern){try{& $call;throw 'DID_NOT_REJECT'}catch{if($_.Exception.Message -notlike $pattern){throw};$script:passed++}}
$fixture=Join-Path (Split-Path -Parent $PSScriptRoot) ('.codex_artifacts\repair-test-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($fixture)
$script:denied=''
function Assert-Custody([string]$Path){if($Path -ceq $script:denied){throw 'custody denied'}}
$names=@('Update-K98.ps1','K98-SourceUpdate.ps1','Deploy-K98Release.ps1','prepare_k98_update.py','verify_k98_update_pair.py','package_k98_update_tool.py','EmptyGitConfig.txt')
$files=[ordered]@{};$payload=[ordered]@{}
foreach($name in $names){$bytes=[Text.Encoding]::UTF8.GetBytes($name);[IO.File]::WriteAllBytes((Join-Path $fixture $name),$bytes);$files[$name]=Repair-Hash $bytes;$payload[$name]=[Convert]::ToBase64String($bytes)}
$manifest=[Text.Encoding]::UTF8.GetBytes((@{version=1;files=$files}|ConvertTo-Json -Depth 5 -Compress))
[IO.File]::WriteAllBytes((Join-Path $fixture 'update-tool.json'),$manifest)
$hash=Repair-Hash $manifest
$payload['update-tool.json']=[Convert]::ToBase64String($manifest)
$payloadObject=($payload|ConvertTo-Json -Compress)|ConvertFrom-Json
Assert-RepairTool $fixture $hash;Check $true 'valid complete tool'
Reject {Assert-RepairTool $fixture ('0'*64)} '*manifest identity*'
$script:denied=Join-Path $fixture 'Update-K98.ps1'
Reject {Assert-RepairTool $fixture $hash} '*custody denied*'
$script:denied=''
[IO.File]::WriteAllText((Join-Path $fixture 'unexpected.txt'),'bad')
Reject {Assert-RepairTool $fixture $hash} '*Unexpected tool member*'
Remove-Item -LiteralPath (Join-Path $fixture 'unexpected.txt')
[IO.File]::WriteAllText((Join-Path $fixture 'Update-K98.ps1'),'tampered')
Reject {Assert-RepairTool $fixture $hash} '*checksum differs*'
Reject {Assert-RepairPartial $fixture $payloadObject} '*checksum differs*'
Remove-Item -LiteralPath (Join-Path $fixture 'Update-K98.ps1')
Remove-Item -LiteralPath (Join-Path $fixture 'update-tool.json')
Assert-RepairPartial $fixture $payloadObject;Check $true 'partial tool without manifest can resume'
Reject {Assert-RepairTool $fixture $hash} '*manifest missing*'
# Exercise production orchestration with all filesystem/control effects replaced.
$body=$ast.EndBlock.Statements[-1].Extent.Text
$root='C:\ProgramData\K98\S11';$tool=Join-Path $root 'updater';$archive=Join-Path $root 'updater-before-ucrt-d9704e51';$updates=Join-Path $root 'updates'
$policy=[pscustomobject]@{state_directory='C:\fixture-state'}
$newPayload=$payloadObject
$lock=[pscustomobject]@{};$lock|Add-Member ScriptMethod Dispose {$script:disposed=$true}
$script:existing=@();$script:moved=$false;$script:installed=$false;$script:disposed=$false;$script:partial=$false
function Test-Path([string]$LiteralPath){return $LiteralPath -cin $script:existing}
function Assert-RepairTool([string]$Path,[string]$ManifestHash){}
function Assert-RepairPartial([string]$Path,$Payload){$script:partial=$true}
function Move-Item([string]$LiteralPath,[string]$Destination,[string]$ErrorAction){$script:moved=$true}
$installerText='$script:installed=$true'
foreach($marker in @((Join-Path $updates 'active.json'),(Join-Path $policy.state_directory 'deployment-request.json'))) {
 $script:existing=@($marker);$script:moved=$false;$script:installed=$false
 Reject {& ([scriptblock]::Create($body))} '*exists; tool replacement refused*'
 Check (-not $moved -and -not $installed -and $disposed) 'refusal mutated tool or leaked lock'
}
$script:existing=@();& ([scriptblock]::Create($body));Check ($moved -and $installed) 'initial replacement failed'
$script:existing=@($archive,$tool);$script:moved=$false;$script:installed=$false
& ([scriptblock]::Create($body));Check (-not $moved -and $installed -and $partial) 'partial retry moved archive or failed install'
$script:existing=@($archive);$script:installed=$false
& ([scriptblock]::Create($body));Check $installed 'archive-only interruption did not resume'
[pscustomobject]@{Status='PASS';Cases=$passed;ProductionTouched=$false}|ConvertTo-Json -Compress
