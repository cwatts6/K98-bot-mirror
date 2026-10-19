# Native adapter contract checks with deterministic SQL/helper outcomes.
# No production paths, SQL connection, task or process startup is used.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
foreach($name in @('Resolve-RecoverySeed','Verify-Native','Same','Hash')) {
 $f=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 . ([scriptblock]::Create($f.Extent.Text.Replace('$PSScriptRoot',("'"+$PSScriptRoot.Replace("'","''")+"'"))))
}
$script:checks=0
function Check($v,$m){if(-not $v){throw $m};$script:checks++}
function Reject($call,$pattern){try{& $call;throw 'DID_NOT_REJECT'}catch{if($_.Exception.Message -notlike $pattern){throw};$script:checks++}}
function Assert-Source($Pins,$Target){$script:events.Add('source');if($script:sourceDrift){throw 'source drift'}}
function Read-Bytes([string]$Path,[string]$Expected='', [long]$Limit=1MB){
 $script:events.Add('read:'+([IO.Path]::GetFileName($Path)))
 if($Path.EndsWith('bindings.json')){return ,([Text.Encoding]::UTF8.GetBytes(($script:derived|ConvertTo-Json -Depth 30 -Compress)))}
 return ,([byte[]]@(1))
}
function Fake-VerifiedPython {$script:events.Add('helper');$script:arguments=@($args);$global:LASTEXITCODE=$script:helperCode}
$script:events=[Collections.Generic.List[string]]::new()
$script:sourceDrift=$false;$script:helperCode=0
$ExpectedBindingsSHA256='a'*64
$base=@{
 recovery_seed='live_sql_observation_v1';new_pins=@{source='pinned'};target=('b'*40)
 extra_members=@(@{name='Verify-RecoverySeed.py';sha256=('c'*64)},@{name='Verify-NewPair.py';sha256=('d'*64)})
 venv=@{path='Fake-VerifiedPython';sha256=('e'*64)}
 seed_members=@(@{name='old';sha256=('f'*64)});new_policy=@{seed_plan=@{path='fixed';sha256=('1'*64)}};new_policy_sha256=('2'*64)
 flags=@{recovery=$false};new_seed_directory='C:\fixture\seed';release_id='fixture'
}
function Reset-Case {
 $script:c=($base|ConvertTo-Json -Depth 30 -Compress)|ConvertFrom-Json
 $script:derived=($base|ConvertTo-Json -Depth 30 -Compress)|ConvertFrom-Json
 $script:derived.seed_members=@([pscustomobject]@{name='actual';sha256=('3'*64)})
 $script:derived.new_policy.seed_plan.sha256='4'*64;$script:derived.new_policy_sha256='5'*64
 $script:events.Clear();$script:helperCode=0;$script:sourceDrift=$false
}
foreach($code in @(10,11)) {
 Reset-Case;$script:helperCode=$code
 Check ((Resolve-RecoverySeed) -eq $code) 'Incomplete proof classification lost'
 Check ($script:c.new_policy_sha256 -ceq ('2'*64)) 'Incomplete proof changed active seed'
 Check (-not($script:events.Contains('read:bindings.json'))) 'Incomplete proof read an effective seed'
 Check ('--create' -notin $script:arguments) 'Verification attempted evidence creation'
}
Reset-Case
Check ((Resolve-RecoverySeed -Create) -eq 0) 'Verified SQL did not select derived seed'
Check ($script:events[0] -ceq 'source') 'Helper ran before complete target source authentication'
Check ('--create' -in $script:arguments) 'Apply did not request protected evidence publication'
Check ($script:c.new_policy_sha256 -ceq ('5'*64)) 'Derived policy binding not selected'
Check ($script:activeBindingsHash -ceq (Hash ([Text.Encoding]::UTF8.GetBytes(($script:derived|ConvertTo-Json -Depth 30 -Compress))))) 'Effective binding hash differs'
Verify-Native
Check ($script:activeBindingsPath -cin $script:arguments) 'Native successor verifier did not use derived evidence'
Verify-Native -Preflight
Check ($ExpectedBindingsSHA256 -cin $script:arguments) 'Preflight lost immutable predecessor binding'
foreach($damage in @('target','flags','release_id','extra','missing')) {
 Reset-Case
 switch($damage) {
  'target' {$script:derived.target='f'*40}
  'flags' {$script:derived.flags.recovery=$true}
  'release_id' {$script:derived.release_id='foreign'}
  'extra' {$script:derived|Add-Member -NotePropertyName surprise -NotePropertyValue 1}
  'missing' {$script:derived.PSObject.Properties.Remove('flags')}
 }
 Reject {Resolve-RecoverySeed} '*binding*differ*'
 Check ($script:c.new_policy_sha256 -ceq ('2'*64)) 'Invalid effective binding became active'
}
Reset-Case;$script:helperCode=20
Reject {Resolve-RecoverySeed -Create} '*SQL observation is unverified*'
Check (-not($script:events.Contains('read:bindings.json'))) 'Failed SQL comparison reached derived seed'
Reset-Case;$script:sourceDrift=$true
Reject {Resolve-RecoverySeed} '*source drift*'
Check (-not($script:events.Contains('helper'))) 'Drift reached helper'
Reset-Case;$script:c.recovery_seed='unknown'
Reject {Resolve-RecoverySeed} '*Unknown recovery seed*'
[pscustomobject]@{Status='PASS';Checks=$checks;ProductionTouched=$false;SqlConnected=$false}|ConvertTo-Json -Compress
