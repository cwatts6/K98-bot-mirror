# Offline repair regression tests; no production paths or scheduled tasks touched.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$path=Join-Path $PSScriptRoot 'Upgrade-K98InstalledUpdater.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
foreach($f in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){. ([scriptblock]::Create($f.Extent.Text))}
$passed=0
function Check($v,$m){if(-not $v){throw $m};$script:passed++}
function Reject($call,$pattern){try{& $call;throw 'DID_NOT_REJECT'}catch{if($_.Exception.Message -notlike $pattern){throw};$script:passed++}}
$fixture=Join-Path (Split-Path -Parent $PSScriptRoot) ('.codex_artifacts\upgrade-test-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($fixture)
$script:denied=''
function Assert-Custody([string]$Path){if($Path -ceq $script:denied){throw 'custody denied'}}
$names=@('Update-K98.ps1','K98-SourceUpdate.ps1','Deploy-K98Release.ps1','prepare_k98_update.py','verify_k98_update_pair.py','package_k98_update_tool.py','EmptyGitConfig.txt')
$files=[ordered]@{};$payload=[ordered]@{}
foreach($name in $names){$bytes=[Text.Encoding]::UTF8.GetBytes($name);[IO.File]::WriteAllBytes((Join-Path $fixture $name),$bytes);$files[$name]=Upgrade-Hash $bytes;$payload[$name]=[Convert]::ToBase64String($bytes)}
$manifest=[Text.Encoding]::UTF8.GetBytes((@{version=1;files=$files}|ConvertTo-Json -Depth 5 -Compress))
[IO.File]::WriteAllBytes((Join-Path $fixture 'update-tool.json'),$manifest)
$hash=Upgrade-Hash $manifest
$payload['update-tool.json']=[Convert]::ToBase64String($manifest)
$payloadObject=($payload|ConvertTo-Json -Compress)|ConvertFrom-Json
Assert-UpgradeTool $fixture $hash;Check $true 'valid complete tool'
Reject {Assert-UpgradeTool $fixture ('0'*64)} '*manifest identity*'
$script:denied=Join-Path $fixture 'Update-K98.ps1'
Reject {Assert-UpgradeTool $fixture $hash} '*custody denied*'
$script:denied=''
[IO.File]::WriteAllText((Join-Path $fixture 'unexpected.txt'),'bad')
Reject {Assert-UpgradeTool $fixture $hash} '*Unexpected tool member*'
Remove-Item -LiteralPath (Join-Path $fixture 'unexpected.txt')
[IO.File]::WriteAllText((Join-Path $fixture 'Update-K98.ps1'),'tampered')
Reject {Assert-UpgradeTool $fixture $hash} '*checksum differs*'
Reject {Assert-UpgradePartial $fixture $payloadObject} '*checksum differs*'
Remove-Item -LiteralPath (Join-Path $fixture 'Update-K98.ps1')
Remove-Item -LiteralPath (Join-Path $fixture 'update-tool.json')
Assert-UpgradePartial $fixture $payloadObject;Check $true 'partial tool without manifest can resume'
Reject {Assert-UpgradeTool $fixture $hash} '*manifest missing*'
# Native atomic member staging with substituted ordinary fixture ACLs only.
function New-Acl([bool]$Directory){
 $acl=[Security.AccessControl.FileSecurity]::new()
 $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.WindowsIdentity]::GetCurrent().User,[Security.AccessControl.FileSystemRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow))
 return $acl
}
$work=Join-Path $fixture 'work';$candidate=Join-Path $work 'tool'
$null=[IO.Directory]::CreateDirectory($candidate)
Write-UpgradeMember $candidate $work 'member.txt' ([Text.Encoding]::UTF8.GetBytes('complete'))
Check ([IO.File]::ReadAllText((Join-Path $candidate 'member.txt')) -ceq 'complete') 'atomic member missing'
Write-UpgradeMember $candidate $work 'member.txt' ([Text.Encoding]::UTF8.GetBytes('complete'))
Reject {Write-UpgradeMember $candidate $work 'member.txt' ([byte[]]@(1))} '*Candidate member differs*'
Reject {Write-UpgradeMember $candidate $work '../outside' ([byte[]]@(1))} '*Invalid candidate*'
# A retained interrupted staging write does not become an executable member.
[IO.File]::WriteAllText((Join-Path $work 'pending-fixture'),'partial')
Write-UpgradeMember $candidate $work 'next.txt' ([Text.Encoding]::UTF8.GetBytes('next'))
Check (Test-Path -LiteralPath (Join-Path $work 'pending-fixture')) 'partial staging evidence lost'
# Exercise the actual swap orchestration without accessing production paths.
$body=$ast.EndBlock.Statements[-1].Extent.Text
$root='C:\ProgramData\K98\S11';$tool=Join-Path $root 'updater';$archive=Join-Path $root 'updater-before-custody-cd112e19';$updates=Join-Path $root 'updates'
$work=Join-Path $root 'test-work';$candidate=Join-Path $work 'tool'
$policy=[pscustomobject]@{state_directory='C:\fixture-state'}
$newPayload=$payloadObject
$lock=[pscustomobject]@{};$lock|Add-Member ScriptMethod Dispose {$script:disposed=$true}
$script:busy=$false;$script:rejectOld=$false;$script:rejectCandidate=$false;$script:failSwap=$false
$script:existing=@();$script:moves=@();$script:disposed=$false
function Test-Path([string]$LiteralPath){return $LiteralPath -cin $script:existing}
function Assert-NoUpgradeProcess {if($script:busy){throw 'Other updater process present'}}
function Assert-UpgradeTool([string]$Path,[string]$ManifestHash){
 if($script:rejectOld -and $Path -ceq $tool){throw 'old package drift'}
 if($script:rejectCandidate -and $Path -ceq $candidate){throw 'candidate drift'}
}
function Assert-UpgradePartial([string]$Path,$Payload){}
function Write-UpgradeMember([string]$Directory,[string]$Work,[string]$Name,[byte[]]$Bytes){}
function Move-Item([string]$LiteralPath,[string]$Destination,[string]$ErrorAction){
 if($script:failSwap -and $LiteralPath -ceq $candidate){throw 'injected swap failure'}
 $script:moves+=($LiteralPath+'->'+$Destination)
 $script:existing=@($script:existing | Where-Object {$_ -cne $LiteralPath})+@($Destination)
}
function Reset-Case {$script:existing=@($tool,$work,$candidate);$script:moves=@();$script:disposed=$false}
foreach($marker in @((Join-Path $updates 'active.json'),(Join-Path $policy.state_directory 'deployment-request.json'))) {
 Reset-Case;$script:existing+=$marker
 Reject {& ([scriptblock]::Create($body))} '*exists; tool replacement refused*'
 Check ($moves.Count -eq 0 -and $disposed) 'active update mutated package or leaked lock'
}
Reset-Case;$script:busy=$true
Reject {& ([scriptblock]::Create($body))} '*Other updater process*'
Check ($moves.Count -eq 0 -and $disposed) 'busy process changed package';$script:busy=$false
Reset-Case;$script:rejectOld=$true
Reject {& ([scriptblock]::Create($body))} '*old package drift*'
Check ($moves.Count -eq 0) 'old drift moved package';$script:rejectOld=$false
Reset-Case;$script:rejectCandidate=$true
Reject {& ([scriptblock]::Create($body))} '*candidate drift*'
Check ($moves.Count -eq 0) 'bad candidate moved original';$script:rejectCandidate=$false
Reset-Case;& ([scriptblock]::Create($body))
Check ($moves.Count -eq 2 -and $tool -cin $existing -and $archive -cin $existing -and $disposed) 'complete swap failed'
$script:moves=@();& ([scriptblock]::Create($body))
Check ($moves.Count -eq 0) 'repeat changed installed package'
Reset-Case;$script:failSwap=$true
Reject {& ([scriptblock]::Create($body))} '*injected swap failure*'
Check ($archive -cin $existing -and $tool -cnotin $existing -and $candidate -cin $existing -and $disposed) 'interrupted swap lost original or candidate'
$script:failSwap=$false;$script:moves=@();& ([scriptblock]::Create($body))
Check ($moves.Count -eq 1 -and $tool -cin $existing -and $archive -cin $existing) 'interrupted swap did not resume'
[pscustomobject]@{Status='PASS';Cases=$passed;ProductionTouched=$false;Qualification='Ordinary fixture ACLs and simulated task/control guards; exact manifest checks, native atomic member writes and orchestration exercised.'}|ConvertTo-Json -Compress
