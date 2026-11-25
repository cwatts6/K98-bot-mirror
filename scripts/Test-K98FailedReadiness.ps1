# Offline Windows PowerShell 5.1 harness. All filesystem writes stay in FixtureRoot.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$FixtureRoot,[Parameter(Mandatory=$true)][string]$ProfilePath,[Parameter(Mandatory=$true)][string]$NativePython)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($PSVersionTable.PSEdition -cne 'Desktop'){throw 'Windows PowerShell 5.1 required'}
$fixture=[IO.Path]::GetFullPath($FixtureRoot)
if(Test-Path -LiteralPath $fixture){throw 'Fresh fixture directory required'}
$null=[IO.Directory]::CreateDirectory($fixture)
$profileBytes=[IO.File]::ReadAllBytes($ProfilePath)
$profile=[Text.Encoding]::UTF8.GetString($profileBytes)|ConvertFrom-Json
$passed=0
function Check($value,[string]$message){if(-not $value){throw $message};$script:passed++}
function Reject([scriptblock]$call,[string]$pattern){try{& $call;throw 'DID_NOT_REJECT'}catch{if($_.Exception.Message -notlike $pattern){throw};$script:passed++}}
# Dot-source only function definitions, not any installed/operational entrypoint.
$library=Join-Path $PSScriptRoot 'K98-SourceUpdate.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($library,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Library parsing failed'}
foreach($name in @('Hash','Read-Bytes','Write-New','New-Directory','Open-SourceCustodyHandle')) {
 $definition=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true)
 if($null -eq $definition){throw ('Required library function missing: '+$name)}
 . ([scriptblock]::Create($definition.Extent.Text))
}
. (Join-Path $PSScriptRoot 'K98-FailedReadiness.ps1')
$script:retirementProfileHash=Hash $profileBytes
Assert-RetirementProfile $profile;Check $true 'valid profile'
foreach($field in @('work','release_id','sid','host','journal_name','approved_target','manifest_sha256')) {
 $copy=$profile|ConvertTo-Json -Depth 8|ConvertFrom-Json
 $copy.$field='invalid'
 Reject {Assert-RetirementProfile $copy} '*retirement*'
}
$copy=$profile|ConvertTo-Json -Depth 8|ConvertFrom-Json
$copy.receipts.PSObject.Properties.Remove('start.complete.json')
Reject {Assert-RetirementProfile $copy} '*completed source/seed/start*'

# Virtual bounded-read adapter exercises the real context/evidence validators.
$realRead=${function:Read-RetirementJson};$realBytes=${function:Read-RetirementBytes}
$script:records=@{};$script:present=@{}
$work=$profile.work;$package=Join-Path $work 'package'
$oldState='C:\ProgramData\K98\S11\automatic-startup\40000000-0000-0000-0000-000000000004'
$newState='C:\ProgramData\K98\S11\automatic-startup\50000000-0000-0000-0000-000000000005'
$seed='C:\ProgramData\K98\S11\runtime\50000000-0000-0000-0000-000000000005'
$policy='C:\ProgramData\K98\S11\runtime\40000000-0000-0000-0000-000000000004\AutomaticStartupPolicy.json'
$stage=Join-Path $oldState ('release-'+$profile.release_id)
$prepared=[pscustomobject]@{release_id=$profile.release_id;manifest=(Join-Path $package 'release.json');manifest_sha256=$profile.manifest_sha256;bindings_sha256=$profile.bindings_sha256;target=('a'*40)}
$manifest=[pscustomobject]@{version=4;release_id=$profile.release_id;host=$profile.host;application_sid=$profile.sid;policy=[pscustomobject]@{path=$policy;sha256=('a'*64)};steps=@(@{id='source';kind='source'},@{id='seed';kind='seed'},@{id='start';kind='start'},@{id='readiness';kind='readiness'})}
$bindings=[pscustomobject]@{release_id=$profile.release_id;host=$profile.host;sid=$profile.sid;root='C:\discord_file_downloader';target=('a'*40);old_policy=[pscustomobject]@{Path=$policy;SHA256=('a'*64);StateDirectory=$oldState};new_state_directory=$newState;new_seed_directory=$seed}
$records[(Join-Path $work 'prepared.json')]=$prepared
$records[$prepared.manifest]=$manifest
$records[(Join-Path $package 'ReleaseBindings.json')]=$bindings
$records[$policy]=[pscustomobject]@{state_directory=$oldState}
$records[(Join-Path $oldState 'deployment-request.json')]=[pscustomobject]@{release_id=$profile.release_id}
$records[(Join-Path $oldState ('deployment-drained-'+$profile.release_id+'.json'))]=[pscustomobject]@{release_id=$profile.release_id;stage='deployment_drained';request_sha256=$profile.request_sha256}
$records['C:\ProgramData\K98\S11\updates\active.json']=[pscustomobject]@{release_id=$profile.release_id;directory=$work}
foreach($entry in $profile.receipts.PSObject.Properties){$parts=$entry.Name.Split('.');$records[(Join-Path (Join-Path $stage '.receipts') $entry.Name)]=[pscustomobject]@{release_id=$profile.release_id;step=$parts[0];stage=$(if($parts[1] -ceq 'complete'){'verified'}else{'starting'})}}
function Read-RetirementJson([string]$Path,[string]$Expected=''){if(-not $records.ContainsKey($Path)){throw ('unexpected read '+$Path)};return $records[$Path]}
function Read-RetirementBytes([string]$Path,[string]$Expected='', [long]$Limit=2MB){return ,([byte[]]@(1))}
function Test-Path([string]$LiteralPath){return $script:present.ContainsKey($LiteralPath)}
$realDirectory=${function:Assert-RetirementDirectory}
function Assert-RetirementDirectory([string]$Path){}
$script:receiptCount=6
function Get-ChildItem([string]$LiteralPath,[switch]$Force){1..$script:receiptCount|ForEach-Object {[pscustomobject]@{PSIsContainer=$false}}}
$context=Get-RetirementContext $profile
Check ($context.stage -ceq $stage) 'stage selection'
Assert-RetirementEvidence $context;Check $true 'complete source-only evidence'
$manifest.steps[1].kind='sql';Reject {Get-RetirementContext $profile} '*source-only*';$manifest.steps[1].kind='seed'
$prepared.target='c'*40;Reject {Get-RetirementContext $profile} '*identity differs*';$prepared.target='a'*40
$manifest.version=3;Reject {Get-RetirementContext $profile} '*identity differs*';$manifest.version=4
$bindings.new_state_directory=$oldState;Reject {Get-RetirementContext $profile} '*policy binding*';$bindings.new_state_directory=$newState
foreach($path in @((Join-Path $work 'verified.json'),(Join-Path $stage 'readiness-status.json'),(Join-Path $newState 'deployment-request.json'))) {
 $script:present[$path]=$true;Reject {Assert-RetirementEvidence $context} '*has appeared*';$script:present.Remove($path)
}
$script:receiptCount=7;Reject {Assert-RetirementEvidence $context} '*advanced*';$script:receiptCount=6
$record=$records[(Join-Path (Join-Path $stage '.receipts') 'start.complete.json')]
$record.stage='starting';Reject {Assert-RetirementEvidence $context} '*receipt differs*';$record.stage='verified'
$records['C:\ProgramData\K98\S11\updates\active.json'].release_id='other'
Reject {Assert-RetirementEvidence $context} '*selection differs*'

# Current runtime checks are read-only observations; virtual task/file adapters
# exercise publication, policy, history and issuer identity rejection branches.
$bindings|Add-Member NoteProperty seed_members @([pscustomobject]@{name='AutomaticStartupPolicy.json';sha256=('a'*64)})
$bindings|Add-Member NoteProperty new_policy_sha256 ('a'*64)
$bindings|Add-Member NoteProperty old_journal ([pscustomobject]@{Record=[pscustomobject]@{sequence=1}})
$installedPolicy=[pscustomobject]@{state_directory=$newState;source_hashes=@{}}
$records[(Join-Path $seed 'AutomaticStartupPolicy.json')]=$installedPolicy
$publication=[pscustomobject]@{version=1;plan_sha256=('d'*64);manifests=[pscustomobject]@{authority=('e'*64);bot=('f'*64)}}
$journal=[pscustomobject]@{sequence=2;policy_sha256=('a'*64);publication=$publication;bindings=[pscustomobject]@{authority=[pscustomobject]@{pid=1};bot=[pscustomobject]@{pid=2}}}
$records[(Join-Path $newState $profile.journal_name)]=$journal
$live=Join-Path 'C:\ProgramData\K98\S11\runtime' $profile.journal_name.Substring(33,36)
$records[(Join-Path $live 'commit.json')]=$publication|ConvertTo-Json -Depth 6|ConvertFrom-Json
$livePlan=[pscustomobject]@{manifests=[pscustomobject]@{authority=(Join-Path $live 'authority-manifest.json');bot=(Join-Path $live 'bot-manifest.json')}}
$records[(Join-Path $live 'ManualProcessPairPlan-CANDIDATE.json')]=$livePlan
$issuer=[pscustomobject]@{version=1;plan_sha256=('d'*64);issuer=[pscustomobject]@{pid=3}}
$records[(Join-Path $live 'AutomaticIssuer.json')]=$issuer
$script:taskSid=$profile.sid;$script:extraHistory=$false
$task=[pscustomobject]@{Actions=@([pscustomobject]@{Execute='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe';Arguments=('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $seed 'Start-ReviewedAutomaticStartup.ps1')+'"')})}
function Get-ScheduledTask([string]$TaskPath,[string]$TaskName){return $script:task}
function Get-RetirementTaskSid($Task){return $script:taskSid}
function Get-ChildItem([string]$LiteralPath,[switch]$Force){
 if($LiteralPath -ceq $newState){
  [pscustomobject]@{PSIsContainer=$false;Name=$profile.journal_name;FullName=(Join-Path $newState $profile.journal_name)}
  if($script:extraHistory){[pscustomobject]@{PSIsContainer=$false;Name='unexpected.json'}}
 } else {1..$script:receiptCount|ForEach-Object {[pscustomobject]@{PSIsContainer=$false}}}
}
$runtime=Get-RetirementRuntime $context;Check ($runtime.processes.Count -eq 3) 'three native bindings'
$script:taskSid='wrong';Reject {Get-RetirementRuntime $context} '*task differs*';$script:taskSid=$profile.sid
$savedArguments=$task.Actions[0].Arguments;$task.Actions[0].Arguments='unexpected';Reject {Get-RetirementRuntime $context} '*task differs*';$task.Actions[0].Arguments=$savedArguments
$script:extraHistory=$true;Reject {Get-RetirementRuntime $context} '*history changed*';$script:extraHistory=$false
$journal.sequence=3;Reject {Get-RetirementRuntime $context} '*incarnation differs*';$journal.sequence=2
$journal.policy_sha256='b'*64;Reject {Get-RetirementRuntime $context} '*incarnation differs*';$journal.policy_sha256='a'*64
$livePlan.manifests.bot='C:\elsewhere';Reject {Get-RetirementRuntime $context} '*publication binding*';$livePlan.manifests.bot=Join-Path $live 'bot-manifest.json'
$issuer.plan_sha256='b'*64;Reject {Get-RetirementRuntime $context} '*issuer publication*';$issuer.plan_sha256='d'*64
$issuer.issuer.pid=1;Reject {Get-RetirementRuntime $context} '*distinct retirement*';$issuer.issuer.pid=3

# Explicit completed-SQL / failed VerifyStart profile. Never synthesize start.complete.
$v2=$profile|ConvertTo-Json -Depth 12|ConvertFrom-Json
$v2.version=2;$v2|Add-Member NoteProperty derived_bindings_sha256 ('d'*64)
$v2.receipts.PSObject.Properties.Remove('start.complete.json')
$v2.receipts|Add-Member NoteProperty 'sql-00.intent.json' ('a'*64)
$v2.receipts|Add-Member NoteProperty 'sql-00.complete.json' ('a'*64)
Assert-RetirementProfile $v2;Check $true 'completed SQL failed-start profile accepted'
$v2.receipts|Add-Member NoteProperty 'start.complete.json' ('a'*64)
Reject {Assert-RetirementProfile $v2} '*completed source/seed/start*'
$v2.receipts.PSObject.Properties.Remove('start.complete.json')
$manifest.steps=@(@{id='sql-00';kind='sql'},@{id='source';kind='source'},@{id='seed';kind='seed'},@{id='start';kind='start'},@{id='readiness';kind='readiness'})
$bindings|Add-Member NoteProperty new_policy ([pscustomobject]@{source_hashes=@{a='b'};flags=@{a=$true};state_directory=$newState;predecessor=@{nonce='same'};seed_plan=@{path='fixed';sha256=('a'*64)}})
$derived=$bindings|ConvertTo-Json -Depth 12|ConvertFrom-Json
$derived.new_policy_sha256='d'*64;$derived.new_policy.seed_plan.sha256='d'*64
$records[(Join-Path $stage 'verified-seed\bindings.json')]=$derived
$context2=Get-RetirementContext $v2
Check ($context2.bindings.new_policy_sha256 -ceq ('d'*64)) 'uses authenticated derived installed seed'
$derived.target='c'*40;Reject {Get-RetirementContext $v2} '*operational binding*';$derived.target='a'*40
$derived.new_policy.flags.a=$false;Reject {Get-RetirementContext $v2} '*operational policy*';$derived.new_policy.flags.a=$true
$derived.new_policy.seed_plan.path='other';Reject {Get-RetirementContext $v2} '*seed location*';$derived.new_policy.seed_plan.path='fixed'
$derived|Add-Member NoteProperty unreviewed $true;Reject {Get-RetirementContext $v2} '*shape differs*';$derived.PSObject.Properties.Remove('unreviewed')
$records['C:\ProgramData\K98\S11\updates\active.json'].release_id=$profile.release_id
$script:receiptCount=7
foreach($entry in $v2.receipts.PSObject.Properties){$parts=$entry.Name.Split('.');$records[(Join-Path (Join-Path $stage '.receipts') $entry.Name)]=[pscustomobject]@{release_id=$v2.release_id;step=$parts[0];stage=$(if($parts[1] -ceq 'complete'){'verified'}else{'starting'})}}
Assert-RetirementEvidence $context2;Check $true 'completed SQL and unacknowledged start remain distinguished'
$sqlReceipt=$records[(Join-Path (Join-Path $stage '.receipts') 'sql-00.complete.json')]
$sqlReceipt.stage='starting';Reject {Assert-RetirementEvidence $context2} '*receipt differs*';$sqlReceipt.stage='verified'
$script:receiptCount=8;Reject {Assert-RetirementEvidence $context2} '*advanced*';$script:receiptCount=7

# Restore real filesystem adapters; keep only custody substituted for an ordinary
# development-account fixture. The native hard-link/stream checks and atomic
# file writes/moves execute unchanged on NTFS.
Set-Item Function:Read-RetirementJson $realRead
Set-Item Function:Read-RetirementBytes $realBytes
Set-Item Function:Assert-RetirementDirectory $realDirectory
Remove-Item Function:Test-Path
Remove-Item Function:Get-ChildItem
function Assert-Protected([string]$Path) {
 if($Path -ceq $NativePython){return} # Read-only interpreter image in native fixture.
 if(-not [IO.Path]::GetFullPath($Path).StartsWith($fixture,[StringComparison]::OrdinalIgnoreCase)){throw 'Fixture escaped'}
}
function New-Acl([bool]$Directory) {
 $acl=if($Directory){[Security.AccessControl.DirectorySecurity]::new()}else{[Security.AccessControl.FileSecurity]::new()}
 $inherit=if($Directory){[Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit}else{[Security.AccessControl.InheritanceFlags]::None}
 $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.WindowsIdentity]::GetCurrent().User,[Security.AccessControl.FileSystemRights]::FullControl,$inherit,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
 return $acl
}
$leaf=Join-Path $fixture 'native.txt';[IO.File]::WriteAllText($leaf,'immutable')
$hash=Hash ([IO.File]::ReadAllBytes($leaf))
$null=Read-RetirementBytes $leaf $hash;Check $true 'native read'
Reject {Read-RetirementBytes $leaf ('f'*64)} '*checksum differs*'
Set-Content -LiteralPath $leaf -Stream alternate -Value 'extra' -NoNewline
Reject {Read-RetirementBytes $leaf $hash} '*alternate stream*'
Remove-Item -LiteralPath $leaf -Stream alternate
$link=Join-Path $fixture 'linked.txt'
$null=New-Item -ItemType HardLink -Path $link -Target $leaf
Reject {Read-RetirementBytes $leaf $hash} '*hardlinks*'
Remove-Item -LiteralPath $link
Write-RetirementBytes $leaf ([IO.File]::ReadAllBytes($leaf));Check $true 'idempotent immutable write'
Reject {Write-RetirementBytes $leaf ([byte[]]@(2))} '*checksum differs*'

# Real distinct native handles, creation-time mismatch, and observed exit. These
# inert children sleep and exit; no application, SQL, scheduled task or VM starts.
$children=@();$handles=$null
try {
 for($i=0;$i -lt 3;$i++) {
  $children+=Start-Process -FilePath $NativePython -ArgumentList @('-I','-B','-c','"import time; time.sleep(5)"') -WindowStyle Hidden -PassThru
 }
 $imageHash=Hash ([IO.File]::ReadAllBytes($NativePython))
 $nativeBindings=@($children|ForEach-Object {[pscustomobject]@{pid=$_.Id;created_filetime=$_.StartTime.ToFileTimeUtc();executable=$_.Path;sha256=$imageHash}})
 Reject {Open-RetirementProcesses @($nativeBindings[0],$nativeBindings[0],$nativeBindings[0])} '*Three retirement*'
 $nativeBindings[0].created_filetime++
 Reject {Open-RetirementProcesses $nativeBindings} '*native identity differs*'
 $nativeBindings[0].created_filetime--
 $handles=Open-RetirementProcesses $nativeBindings
 Assert-RetirementProcesses $handles;Check $true 'live pinned handles'
 foreach($child in $children){if(-not $child.WaitForExit(15000)){throw 'Inert fixture child did not exit'}}
 Reject {Assert-RetirementProcesses $handles} '*process exited*'
} finally {
 if($null -ne $handles){foreach($handle in $handles){$handle.Dispose()}}
 foreach($child in $children){$child.Dispose()}
}

# Source reads use actual files, including loose and packed main references.
$sourceRoot=Join-Path $fixture 'source';$null=[IO.Directory]::CreateDirectory((Join-Path $sourceRoot '.git\refs\heads'))
$sourceContext=[pscustomobject]@{bindings=[pscustomobject]@{root=$sourceRoot};prepared=[pscustomobject]@{target=('a'*40)}}
$sourceFile=Join-Path $sourceRoot 'module.py';[IO.File]::WriteAllText($sourceFile,'# inert source')
$sourcePolicy=[pscustomobject]@{source_hashes=[pscustomobject]@{'module.py'=(Hash ([IO.File]::ReadAllBytes($sourceFile)))}}
$headFile=Join-Path $sourceRoot '.git\HEAD';$mainFile=Join-Path $sourceRoot '.git\refs\heads\main'
[IO.File]::WriteAllText($headFile,'ref: refs/heads/main');[IO.File]::WriteAllText($mainFile,('a'*40))
Assert-RetirementSource $sourceContext $sourcePolicy;Check $true 'source pins and loose main'
[IO.File]::WriteAllText($mainFile,('b'*40));Reject {Assert-RetirementSource $sourceContext $sourcePolicy} '*source changed*'
Remove-Item -LiteralPath $mainFile
[IO.File]::WriteAllText((Join-Path $sourceRoot '.git\packed-refs'),(('a'*40)+' refs/heads/main'))
Assert-RetirementSource $sourceContext $sourcePolicy;Check $true 'packed main'
[IO.File]::WriteAllText($sourceFile,'# changed');Reject {Assert-RetirementSource $sourceContext $sourcePolicy} '*checksum differs*'
[IO.File]::WriteAllText($headFile,'ref: refs/heads/other');Reject {Assert-RetirementSource $sourceContext $sourcePolicy} '*installed private main*'

$realEvidence=${function:Assert-RetirementEvidence}
$script:archiveInterruption=$false
function Assert-RetirementEvidence($Context,[switch]$Archived) {
 $path=if($Archived){Join-Path $Context.paths.directory 'active.json'}else{$Context.paths.active}
 $null=Read-RetirementBytes $path $Context.profile.active_sha256
 if($Archived -and (Test-Path -LiteralPath $Context.paths.active)){throw 'Another active selection exists during retirement'}
 if($Archived -and $script:archiveInterruption){$script:archiveInterruption=$false;throw 'injected interruption after archive move'}
}
function Get-RetirementContext($Profile,[string]$ProfileHash){return $script:context}
$realWrite=${function:Write-RetirementBytes}
$script:cut=0;$script:writes=0
function Write-RetirementBytes([string]$Path,[byte[]]$Bytes) {
 & $realWrite $Path $Bytes
 $script:writes++
 if($script:cut -eq $script:writes){throw 'injected interruption'}
}
foreach($cut in 1..5) {
 $case=Join-Path $fixture ('cut-'+$cut);$null=[IO.Directory]::CreateDirectory($case)
 $p=$profile|ConvertTo-Json -Depth 8|ConvertFrom-Json
 $active=Retirement-Bytes ([ordered]@{release_id=$p.release_id;directory=$p.work})
 $p.active_sha256=Hash $active
 $profileBytes=Retirement-Bytes $p;$script:retirementProfileHash=Hash $profileBytes
 $paths=[pscustomobject]@{root=(Join-Path $case 'retirements');directory=(Join-Path (Join-Path $case 'retirements') $p.release_id);active=(Join-Path $case 'active.json')}
 [IO.File]::WriteAllBytes($paths.active,$active)
 $context=[pscustomobject]@{profile=$p;paths=$paths;prepared=[pscustomobject]@{target=('a'*40)};barrier=(Join-Path $case '.amendment-selected.json');marker=(Retirement-Bytes ([ordered]@{kind='failed_readiness_retirement';profile_sha256=$script:retirementProfileHash}))}
 $script:cut=$cut;$script:writes=0
 $script:archiveInterruption=($cut -eq 5)
 Reject {Start-FailedReadinessRetirement $context $profileBytes ('c'*64);Complete-FailedReadinessRetirement $context ('c'*64)} '*injected interruption*'
 Check (Test-Path -LiteralPath $context.barrier) 'legacy barrier must be first'
 $script:cut=0
 Start-FailedReadinessRetirement $context $profileBytes ('c'*64)
 Complete-FailedReadinessRetirement $context ('c'*64)
 $record=Read-CompletedRetirement $paths.directory
 Check ($record.complete.kind -ceq 'retired_without_verified_readiness') 'false readiness status'
 Check (-not(Test-Path -LiteralPath $paths.active)) 'active pointer remained'
 Check ((Hash ([IO.File]::ReadAllBytes((Join-Path $paths.directory 'active.json')))) -ceq (Hash $active)) 'original selection bytes changed'
 Check (-not(Test-Path -LiteralPath (Join-Path $case 'verified.json'))) 'manufactured success'
}
# The routine updater cannot cross an incomplete retirement, choose another
# first successor, or restore the retired release selection. Route only its
# fixed history root to the fixture; record reads and validation stay real.
$realDirectory=${function:Assert-RetirementDirectory}
$history='C:\ProgramData\K98\S11\updates\retirements'
function Test-Path([string]$LiteralPath) {
 if($LiteralPath -ceq $history){return $true}
 if($LiteralPath -ceq (Join-Path $history $profile.release_id)){return $true}
 Microsoft.PowerShell.Management\Test-Path -LiteralPath $LiteralPath
}
function Assert-RetirementDirectory([string]$Path) {if($Path -ceq $history){& $realDirectory $paths.root}else{& $realDirectory $Path}}
function Get-ChildItem([string]$LiteralPath,[switch]$Force) {Microsoft.PowerShell.Management\Get-ChildItem -LiteralPath $paths.root -Force}
Assert-RetirementUpdates ('a'*40) ('b'*40);Check $true 'reviewed first target'
Reject {Assert-RetirementUpdates ('a'*40) ('c'*40)} '*successor target differs*'
# An additional successor needs its own exact protected approval and the new
# tool manifest. It never edits or replaces the completed retirement record.
$successorFile=Join-Path $paths.directory ('successor-'+('c'*40)+'.json')
$toolFixture=Join-Path $fixture 'successor-tool.json';[IO.File]::WriteAllText($toolFixture,'{"version":1}')
$readSuccessorBytes=${function:Read-RetirementBytes}
function Read-RetirementBytes([string]$Path,[string]$Expected='', [long]$Limit=2MB) {
 if($Path -ceq 'C:\ProgramData\K98\S11\updater\update-tool.json'){$Path=$toolFixture}
 & $readSuccessorBytes $Path $Expected $Limit
}
$unchangedRetirement=@{}
foreach($name in @('profile.json','intent.json','complete.json','active.json')){
 $unchangedRetirement[$name]=Hash ([IO.File]::ReadAllBytes((Join-Path $paths.directory $name)))
}
$approval=[pscustomobject][ordered]@{version=1;kind='failed_readiness_successor_review';release_id=$profile.release_id;
 installed_target=('a'*40);previous_approved_target=('b'*40);approved_target=('c'*40);
 retirement_complete_sha256=$unchangedRetirement['complete.json'];tool_sha256=(Hash ([IO.File]::ReadAllBytes($toolFixture)))}
[IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $approval))
Assert-RetirementUpdates ('a'*40) ('c'*40);Check $true 'exact independently reviewed successor'
Assert-RetirementUpdates ('a'*40) ('b'*40);Check $true 'original successor remains immutable'
Assert-RetirementUpdates;Check $true 'upgrade history read does not select a target'
Reject {Assert-RetirementUpdates ('a'*40) ('f'*40)} '*successor target differs*'
Reject {Assert-RetirementUpdates ('a'*40) '..\elsewhere'} '*Canonical distinct*'
Reject {Assert-RetirementUpdates ('a'*40) ('a'*40)} '*Canonical distinct*'
foreach($field in @('kind','release_id','installed_target','previous_approved_target','approved_target','retirement_complete_sha256','tool_sha256')) {
 $bad=$approval|ConvertTo-Json|ConvertFrom-Json;$bad.$field='invalid'
 [IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $bad))
 Reject {Assert-RetirementUpdates ('a'*40) ('c'*40)} '*successor identity differs*'
 $bad.$field=@($approval.$field)
 [IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $bad))
 Reject {Assert-RetirementUpdates ('a'*40) ('c'*40)} '*field type differs*'
}
foreach($badVersion in @($true,2,'1')) {
 $bad=$approval|ConvertTo-Json|ConvertFrom-Json;$bad.version=$badVersion
 [IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $bad))
 Reject {Assert-RetirementUpdates ('a'*40) ('c'*40)} '*successor identity differs*'
}
$bad=$approval|ConvertTo-Json|ConvertFrom-Json;$bad|Add-Member NoteProperty command 'unreviewed'
[IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $bad))
Reject {Assert-RetirementUpdates ('a'*40) ('c'*40)} '*Exact reviewed*'
foreach($field in @('retirement_complete_sha256','tool_sha256')) {
 $bad=$approval|ConvertTo-Json|ConvertFrom-Json;$bad.$field='f'*64
 [IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $bad))
 Reject {Assert-RetirementUpdates ('a'*40) ('c'*40)} '*checksum differs*'
}
[IO.File]::WriteAllBytes($successorFile,(Retirement-Bytes $approval))
Assert-RetirementUpdates ('a'*40) ('c'*40);Check $true 'exact successor read restored'
foreach($entry in $unchangedRetirement.GetEnumerator()) {
 Check ((Hash ([IO.File]::ReadAllBytes((Join-Path $paths.directory $entry.Key)))) -ceq $entry.Value) 'original retirement bytes changed'
}
Assert-RetirementUpdates ('d'*40) ('e'*40);Check $true 'later ordinary release'
Reject {Assert-ReleaseNotRetired $profile.release_id} '*do not resume*'
$completeFile=Join-Path $paths.directory 'complete.json';$savedComplete=[IO.File]::ReadAllBytes($completeFile)
Remove-Item -LiteralPath $completeFile
Reject {Assert-RetirementUpdates} '*retirement is incomplete*'
[IO.File]::WriteAllBytes($completeFile,$savedComplete)
$altered=[Text.Encoding]::UTF8.GetString($savedComplete)|ConvertFrom-Json;$altered.kind='verified'
[IO.File]::WriteAllBytes($completeFile,(Retirement-Bytes $altered))
Reject {Read-CompletedRetirement $paths.directory} '*closeout identity differs*'
[IO.File]::WriteAllBytes($completeFile,$savedComplete)
[IO.File]::WriteAllText($context.barrier,'changed')
Reject {Read-CompletedRetirement $paths.directory} '*checksum differs*'
[pscustomobject]@{Status='PASS';Cases=$passed;ProductionTouched=$false;Scope='Real profile/evidence validators, native fixture hard-link/stream/immutable writes and interrupted retirement publication; ordinary fixture ACL substitution'}|ConvertTo-Json -Compress
