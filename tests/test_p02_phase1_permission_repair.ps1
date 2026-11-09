Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($PSVersionTable.PSEdition -cne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5){throw 'Windows PowerShell 5.1 required'}
$repo=Split-Path -Parent $PSScriptRoot
$asts=@{}
foreach($name in @('K98-SourceUpdate.ps1','Update-K98.ps1','Upgrade-K98InstalledUpdater.ps1')){
 $tokens=$null;$parseErrors=$null
 $asts[$name]=[Management.Automation.Language.Parser]::ParseFile((Join-Path $repo ('scripts\'+$name)),[ref]$tokens,[ref]$parseErrors)
 if(@($parseErrors).Count){throw ($parseErrors|Out-String)}
}
function Function-Text([string]$Name){
 $found=@($asts['K98-SourceUpdate.ps1'].FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $Name},$true))
 if($found.Count -ne 1){throw ('Missing unique function '+$Name)}
 return $found[0].Extent.Text
}
foreach($name in @('Assert-Phase1PermissionRepairState','Hash','Same')){. ([scriptblock]::Create((Function-Text $name)))}
$passed=0
function Require([bool]$Value,[string]$Message){if(-not $Value){throw $Message}}
$release='dad1d06d-f342-40e6-92ee-74676bee7842'
$work='C:\ProgramData\K98\S11\updates\f25b9a13-ee10-4268-9e75-357bde4eac51'
$journal='incarnation-00000000000000000099-0fb4a20c-6798-48c4-a3d6-38a1717b2603.json'
$receiptNames=@('seed.complete.json','seed.intent.json','source.complete.json','source.intent.json','sql-00.complete.json','sql-00.intent.json','start.intent.json')
foreach($case in @('valid','active','manifest','bindings','target','receipt_bytes','extra_receipt','missing_receipt','new_readiness','amendment','second_journal','wrong_journal','deployment_request')){
 $readRecord={param($path,$expected)
  Require ($expected -cmatch '^[0-9a-f]{64}$') 'Every original record must be pinned'
  if($case -ceq 'receipt_bytes' -and $path.EndsWith('source.complete.json')){throw 'Injected byte mismatch'}
  if($path.EndsWith('active.json')){return [pscustomobject]@{release_id=$(if($case -ceq 'active'){'other'}else{$release});directory=$work}}
  if($path.EndsWith('ReleaseBindings.json')){return [pscustomobject]@{release_id=$(if($case -ceq 'bindings'){'other'}else{$release});target=$(if($case -ceq 'target'){'wrong'}else{'5fe2dbdc203c8d7268271b2baccac9d49915d280'})}}
  if($path.EndsWith('release.json')){return [pscustomobject]@{release_id=$(if($case -ceq 'manifest'){'other'}else{$release})}}
  return [pscustomobject]@{}
 }
 $inventory={param($path,$filter)
  if($path.EndsWith('.receipts')){
   if($case -ceq 'extra_receipt'){return $receiptNames+@('start.complete.json')}
   if($case -ceq 'missing_receipt'){return $receiptNames[1..6]}
   return $receiptNames
  }
  if($filter -ceq 'incarnation-*.json'){
   if($case -ceq 'second_journal'){return @($journal,'incarnation-extra.json')}
   if($case -ceq 'wrong_journal'){return @('incarnation-other.json')}
   return @($journal)
  }
  if($filter -ceq 'deployment-request.json'){if($case -ceq 'deployment_request'){return @('deployment-request.json')};return @()}
  if($case -ceq 'new_readiness'){return @('readiness-status.json')}
  if($case -ceq 'amendment'){return @('.amendment-selected.json')}
  return @()
 }
 $accepted=$false
 try{$result=Assert-Phase1PermissionRepairState $readRecord $inventory;$accepted=$true}catch{if($case -ceq 'valid'){throw}}
 Require ($accepted -eq ($case -ceq 'valid')) ('Admission case failed: '+$case)
 $passed++
}

# Execute the real atomic selection logic only within a unique local fixture.
# Custody/native/SQL admission is exercised separately; these callbacks model
# already-verified records and allow deterministic interruption at write points.
$fixtureRoot=Join-Path ([IO.Path]::GetTempPath()) ('K98-phase1-permission-selection-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($fixtureRoot)
$original=[Text.UTF8Encoding]::new($false).GetBytes('{"release_id":"dad1d06d-f342-40e6-92ee-74676bee7842","directory":"C:\\ProgramData\\K98\\S11\\updates\\f25b9a13-ee10-4268-9e75-357bde4eac51"}')
Require ((Hash $original) -ceq '78ad11d814e174620fb0cd59c4e803b917ab2232da87b9e997b9102e6d12e7a2') 'Original pointer fixture identity'
function Read-Bytes([string]$Path,[string]$Expected='',[long]$Limit=1MB){
 if($Path -ceq (Join-Path $candidateWork 'prepared.json')){$raw=$preparedBytes}else{$raw=[IO.File]::ReadAllBytes($Path)}
 if($script:failure -ceq 'after_replace' -and $Path.EndsWith('original-active.json')){$script:failure='';throw 'Injected interruption after replacement'}
 if($raw.Length -gt $Limit -or ($Expected -and (Hash $raw) -cne $Expected)){throw 'Fixture pinned bytes differ'}
 return ,$raw
}
function Read-Json([string]$Path,[string]$Expected=''){[Text.Encoding]::UTF8.GetString((Read-Bytes $Path $Expected))|ConvertFrom-Json}
function Write-New([string]$Path,[byte[]]$Bytes){
 $f=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$f.Write($Bytes,0,$Bytes.Length)}finally{$f.Dispose()}
 if($script:failure -ceq 'after_pending' -and $Path.EndsWith('candidate-active.json')){$script:failure='';throw 'Injected interruption after pending pointer'}
}
function Write-Record([string]$Path,$Value){
 Write-New $Path ([Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 20 -Compress)))
 if($script:failure -ceq 'after_intent' -and $Path.EndsWith('selection.json')){$script:failure='';throw 'Injected interruption after intent'}
}
function Read-Phase1PermissionRepairState {
 Require ((Hash (Read-Bytes (Join-Path $caseRoot 'active.json'))) -ceq (Hash $original)) 'Original active pointer changed'
 return [pscustomobject]@{release_id=$release;active_sha256=(Hash $original)}
}
function Assert-Phase1RepairCandidate($Prepared,[string]$Work){
 $script:preflights++
 if($script:failure -ceq 'preflight'){throw 'Injected preflight refusal'}
 Require ($Work -ceq $candidateWork -and $Prepared.release_id -ceq $candidateId) 'Candidate differs'
}
foreach($case in @('normal','after_intent','after_pending','after_replace','preflight','changed_pending','changed_active','changed_prepared')){
 $caseRoot=Join-Path $fixtureRoot $case;$null=[IO.Directory]::CreateDirectory($caseRoot)
 $text=(Function-Text 'Select-Phase1PermissionRepair').Replace("'C:\ProgramData\K98\S11\updates'",("'"+$caseRoot.Replace("'","''")+"'"))
 . ([scriptblock]::Create($text))
 $candidateWork='C:\ProgramData\K98\S11\updates\01234567-0123-4123-8123-0123456789ab'
 $candidateId='11234567-0123-4123-8123-0123456789ab'
 $prepared=[pscustomobject]@{release_id=$candidateId;before='5fe2dbdc203c8d7268271b2baccac9d49915d280';target=('a'*40);manifest=(Join-Path $candidateWork 'package\release.json')}
 $preparedBytes=[Text.UTF8Encoding]::new($false).GetBytes(($prepared|ConvertTo-Json -Compress))
 [IO.File]::WriteAllBytes((Join-Path $caseRoot 'active.json'),$original)
 $script:preflights=0;$script:failure=if($case -in @('changed_pending','changed_active','changed_prepared')){'after_pending'}elseif($case -ceq 'normal'){''}else{$case}
 $stopped=$false
 try{$result=Select-Phase1PermissionRepair $prepared $candidateWork}catch{$stopped=$true;if($case -ceq 'normal'){throw}}
 if($case -ceq 'preflight'){
  Require $stopped 'Preflight must refuse'
  Require ((Hash (Read-Bytes (Join-Path $caseRoot 'active.json'))) -ceq (Hash $original)) 'Refusal changed active pointer'
  Require (-not(Test-Path -LiteralPath (Join-Path $caseRoot 'phase1-permission-repair-selection.json'))) 'Refusal selected a repair'
 } elseif($case -in @('changed_pending','changed_active','changed_prepared')){
  if($case -ceq 'changed_prepared'){$preparedBytes=[Text.Encoding]::UTF8.GetBytes('{}')}
  else{$name=if($case -ceq 'changed_pending'){'phase1-permission-repair-candidate-active.json'}else{'active.json'};[IO.File]::WriteAllText((Join-Path $caseRoot $name),'{}')}
  $refused=$false;try{$null=Select-Phase1PermissionRepair $null ''}catch{$refused=$true}
  Require $refused ('Changed state must refuse: '+$case)
 } else {
  if($case -cne 'normal'){Require $stopped 'Interruption fixture did not stop';$result=Select-Phase1PermissionRepair $null ''}
  Require ($result.release_id -ceq $candidateId) 'Wrong selected repair'
  Require ((Hash (Read-Bytes (Join-Path $caseRoot 'phase1-permission-repair-original-active.json'))) -ceq (Hash $original)) 'Original pointer not preserved'
  $selected=Read-Json (Join-Path $caseRoot 'active.json');Require ($selected.release_id -ceq $candidateId) 'Active repair differs'
  $completed=Read-Json (Join-Path $caseRoot 'phase1-permission-repair-selected.json')
  Require ($completed.original_readiness -ceq 'unverified' -and -not $completed.sql_replayed) 'Original failure was falsely closed'
  $before=@(Get-ChildItem -LiteralPath $caseRoot -File).Count
  $null=Select-Phase1PermissionRepair $null ''
  Require (@(Get-ChildItem -LiteralPath $caseRoot -File).Count -eq $before) 'Completed selection repeated writes'
 }
 $passed++
}
. ([scriptblock]::Create((Function-Text 'Test-UpdateCanRefresh')))
$refresh=Join-Path $fixtureRoot 'refresh';$null=[IO.Directory]::CreateDirectory($refresh)
Require (Test-UpdateCanRefresh $refresh 'new') 'Ordinary unused preparation can refresh'
Require (-not(Test-UpdateCanRefresh $refresh 'new' -RetainSelectedRepair)) 'Selected repair must not refresh'
Require (-not(Test-UpdateCanRefresh $refresh 'new' -PrepareOnly -RetainSelectedRepair)) 'Prepare-only must preserve selection'
[IO.File]::WriteAllText((Join-Path $refresh 'deployment-request.json'),'{}')
Require (-not(Test-UpdateCanRefresh $refresh 'new' -RetainSelectedRepair)) 'Requested deployment must resume'
$refused=$false;try{$null=Test-UpdateCanRefresh $refresh 'new' -PrepareOnly -RetainSelectedRepair}catch{$refused=$true}
Require $refused 'Preparation after deployment request must refuse'
$passed+=5
Write-Output ('PHASE1_PERMISSION_REPAIR_TESTS_PASSED='+$passed+'; fixture='+$fixtureRoot)
