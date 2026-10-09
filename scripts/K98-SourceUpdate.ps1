[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][ValidateSet('Library','Preflight','VerifySource','ApplySource','VerifySeed','ApplySeed','VerifyStart','ApplyStart','VerifyReadiness','AwaitReadiness')][string]$Action,
 [string]$ExpectedBindingsSHA256
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$powershell='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$script:gitMetadataChecked=$false
if($PSVersionTable.PSEdition -cne 'Desktop'){throw 'Windows PowerShell 5.1 required'}

function Assert-Protected([string]$Path) {
 $item=Get-Item -LiteralPath $Path -Force
 $leafDepth=if($item.PSIsContainer){0}else{1};$depth=0
 while($null -ne $item) {
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Protected reparse path refused'}
  $acl=Get-Acl -LiteralPath $item.FullName
  $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
  if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw ('Protected owner differs: '+$item.FullName+' owner='+$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value)}
  $mask=if($depth -le $leafDepth){0x500d0156}else{0x500d0040}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
   if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
      ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and
      $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band $mask) -ne 0){throw 'Untrusted write rights'}
  }
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory};$depth++
 }
}
function Hash([byte[]]$Bytes) {
 $hasher=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($hasher.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
}
function Read-Bytes([string]$Path,[string]$Expected='', [long]$Limit=1MB) {
 Assert-Protected $Path
 $item=Get-Item -LiteralPath $Path -Force
 if($item.PSIsContainer -or $item.Length -gt $Limit){throw 'File size/type differs'}
 $bytes=[IO.File]::ReadAllBytes($Path)
 if($bytes.Length -gt $Limit -or ($Expected -and (Hash $bytes) -cne $Expected)){throw 'File checksum differs'}
 return ,$bytes
}
function Read-Json([string]$Path,[string]$Expected='') {
 [Text.Encoding]::UTF8.GetString((Read-Bytes $Path $Expected)) | ConvertFrom-Json
}
function New-Acl([bool]$Directory) {
 $acl=if($Directory){[Security.AccessControl.DirectorySecurity]::new()}else{[Security.AccessControl.FileSecurity]::new()}
 $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'));$acl.SetAccessRuleProtection($true,$false)
 $inherit=if($Directory){[Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit}else{[Security.AccessControl.InheritanceFlags]::None}
 foreach($sid in @('S-1-5-18','S-1-5-32-544',$script:c.sid)) {
  $rights=if($sid -ceq $script:c.sid){[Security.AccessControl.FileSystemRights]::ReadAndExecute}else{[Security.AccessControl.FileSystemRights]::FullControl}
  $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),$rights,$inherit,[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow))
 }
 return $acl
}
function New-Directory([string]$Path) {
 Assert-Protected (Split-Path -Parent $Path)
 if(Test-Path -LiteralPath $Path){throw 'New directory already exists; preserve partial state'}
 $null=[IO.Directory]::CreateDirectory($Path,(New-Acl $true));Assert-Protected $Path
}
function Write-New([string]$Path,[byte[]]$Bytes) {
 Assert-Protected (Split-Path -Parent $Path)
 $stream=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,(New-Acl $false))
 try{$stream.Write($Bytes,0,$Bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 $null=Read-Bytes $Path (Hash $Bytes) 16MB
}
function Write-Record([string]$Path,$Value) {
 Write-New $Path ([Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 30 -Compress)))
}
function Same($Actual,$Expected) {
 if($null -eq $Actual -or $null -eq $Expected){return ($null -eq $Actual -and $null -eq $Expected)}
 if($Expected -is [array]) {
  $a=@($Actual);if($a.Count -ne $Expected.Count){return $false}
  for($i=0;$i -lt $a.Count;$i++){if(-not(Same $a[$i] $Expected[$i])){return $false}}
  return $true
 }
 if($Expected -is [pscustomobject]) {
  if(@($Actual.PSObject.Properties).Count -ne @($Expected.PSObject.Properties).Count){return $false}
  foreach($p in $Expected.PSObject.Properties){if($null -eq $Actual.PSObject.Properties[$p.Name] -or -not(Same $Actual.($p.Name) $p.Value)){return $false}}
  return $true
 }
 return ([string]$Actual -ceq [string]$Expected)
}
function Invoke-GitWorker([string]$Arguments) {
 $null=Read-Bytes $c.git_path $c.git_sha256 2MB
 $empty=Join-Path $PSScriptRoot 'EmptyGitConfig.txt'
 $null=Read-Bytes $empty 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
 $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$c.git_path
 $info.Arguments='--no-optional-locks -c safe.directory=C:/discord_file_downloader -c core.hooksPath=NUL -c core.fsmonitor=false -c core.attributesFile="'+$empty+'" -c maintenance.auto=false -c gc.auto=0 -C C:\discord_file_downloader '+$Arguments
 $info.WorkingDirectory='C:\Windows\System32'
 $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 foreach($key in @($info.EnvironmentVariables.Keys)){if(([string]$key).StartsWith('GIT_',[StringComparison]::OrdinalIgnoreCase)){$info.EnvironmentVariables.Remove([string]$key)}}
 $info.EnvironmentVariables['GIT_CONFIG_NOSYSTEM']='1';$info.EnvironmentVariables['GIT_CONFIG_GLOBAL']=$empty
 $info.EnvironmentVariables['GIT_ATTR_NOSYSTEM']='1';$info.EnvironmentVariables['GIT_NO_REPLACE_OBJECTS']='1'
 $info.EnvironmentVariables['GIT_TERMINAL_PROMPT']='0';$info.EnvironmentVariables['GCM_INTERACTIVE']='Never'
 $process=[Diagnostics.Process]::new();$process.StartInfo=$info
 try {
  if(-not $process.Start()){throw 'Git worker failed to start'}
  $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
  if(-not $process.WaitForExit(60000)){$process.Kill();throw 'Git timed out; retain intent and verify outcome'}
  $out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult()
  if($process.ExitCode -ne 0 -or $out.Length -gt 1MB -or $err.Length -gt 1MB){throw ('Git failed/bounds exceeded: '+$process.ExitCode)}
  return $out.Trim()
 }finally{$process.Dispose()}
}
function Assert-GitDirectoryInheritance([string]$Path) {
 $acl=Get-Acl -LiteralPath $Path
 $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
 foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
  # InheritOnly does not affect the existing directory but can grant write access
  # to metadata that Git creates later in the same protected operation.
  if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
     $ace.InheritanceFlags -ne [Security.AccessControl.InheritanceFlags]::None -and
     $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band 0x500d0156) -ne 0){throw 'Git metadata may not inherit untrusted write rights'}
 }
}
function Assert-GitMetadata([string]$Path,[int]$MaxItems=20000,[int]$MaxSeconds=60) {
 $watch=[Diagnostics.Stopwatch]::StartNew();$count=0
 Assert-Protected $Path;Assert-GitDirectoryInheritance $Path
 $queue=[Collections.Generic.Queue[IO.DirectoryInfo]]::new()
 $queue.Enqueue([IO.DirectoryInfo]::new($Path))
 while($queue.Count) {
  $directory=$queue.Dequeue()
  foreach($child in $directory.EnumerateFileSystemInfos()) {
   if(++$count -gt $MaxItems -or $watch.Elapsed.TotalSeconds -ge $MaxSeconds){throw 'Git metadata custody inventory exceeded count/time bound'}
   # Existing descendants may have independent ACLs. Inspect before descending;
   # a protected root alone does not authorize privileged metadata reads/writes.
   Assert-Protected $child.FullName
   if($child -is [IO.DirectoryInfo]){Assert-GitDirectoryInheritance $child.FullName;$queue.Enqueue($child)}
  }
 }
}
function Git([string]$Arguments) {
 $metadata=Join-Path $c.root '.git'
 Assert-Protected $metadata
 if(-not(Get-Item -LiteralPath $metadata -Force).PSIsContainer){throw 'Ordinary Git metadata directory required'}
 if(-not $script:gitMetadataChecked){Assert-GitMetadata $metadata;$script:gitMetadataChecked=$true}
 foreach($name in @('commondir','config.worktree','info\grafts','objects\info\alternates')) {
  if(Test-Path -LiteralPath (Join-Path $metadata $name)){throw 'Nonstandard Git indirection requires separate review'}
 }
 $config=Join-Path $metadata 'config'
 $beforeHash=Hash (Read-Bytes $config '' 65536)
 # This first command only parses protected local configuration, without includes;
 # it cannot run checkout/status filters. Global/system/environment config is off.
 $settings=Invoke-GitWorker 'config --local --no-includes --null --list'
 foreach($record in $settings.Split([char]0)) {
  if(-not $record){continue}
  $key=($record -split "`n",2)[0]
  if($key -notmatch '^(core\.(repositoryformatversion|filemode|bare|logallrefupdates|symlinks|ignorecase|autocrlf|safecrlf|eol|longpaths|quotepath)|remote\.[a-zA-Z0-9_-]+\.(url|fetch)|branch\.[a-zA-Z0-9_/-]+\.(remote|merge)|user\.(name|email)|pull\.rebase|fetch\.prune)$'){throw 'Git configuration outside reviewed non-executable allowlist'}
 }
 $null=Read-Bytes $config $beforeHash 65536
 $writes=$Arguments -match '(^| )(fetch|merge|update-ref)( |$)'
 $existing=if($writes){Git-MetadataPaths $metadata}else{$null}
 $result=Invoke-GitWorker $Arguments
 if($writes){Seal-NewGitMetadata $metadata $existing}
 return $result
}
function Git-MetadataPaths([string]$Path) {
 $paths=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 $queue=[Collections.Generic.Queue[IO.DirectoryInfo]]::new();$queue.Enqueue([IO.DirectoryInfo]::new($Path))
 $clock=[Diagnostics.Stopwatch]::StartNew()
 while($queue.Count) {
  foreach($item in $queue.Dequeue().EnumerateFileSystemInfos()) {
   if($paths.Count -ge 20000 -or $clock.Elapsed.TotalSeconds -ge 60){throw 'Git metadata inventory bound exceeded'}
   if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Git metadata reparse path refused'}
   $null=$paths.Add($item.FullName)
   if($item -is [IO.DirectoryInfo]){$queue.Enqueue($item)}
  }
 }
 return ,$paths
}
function Seal-NewGitMetadata([string]$Path,$Existing) {
 # Existing metadata was custody-checked before privileged Git ran. Only new
 # entries created by that bounded worker receive the established control ACL.
 $current=Git-MetadataPaths $Path
 foreach($name in @($current | Sort-Object Length)) {
  if(-not $Existing.Contains($name)) {
   $item=Get-Item -LiteralPath $name -Force
   Set-Acl -LiteralPath $name -AclObject (New-Acl ($item -is [IO.DirectoryInfo]))
   Assert-Protected $name
  }
 }
}
function Assert-Source($Pins,[string]$Head) {
 if((Git 'rev-parse HEAD') -cne $Head -or (Git 'branch --show-current') -cne 'main' -or (Git 'status --porcelain --untracked-files=no')){throw 'Private main source state differs'}
 $watch=[Diagnostics.Stopwatch]::StartNew();$count=0
 foreach($p in $Pins.PSObject.Properties) {
  if(++$count -gt 1000 -or $watch.Elapsed.TotalSeconds -gt 60){throw 'Source verification bound exceeded'}
  $path=[IO.Path]::GetFullPath((Join-Path $c.root $p.Name))
  if(-not $path.StartsWith($c.root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Source path escaped repository'}
  $null=Read-Bytes $path $p.Value 2MB
 }
}
function Assert-UpdatePaths {
 foreach($m in $c.source_members) {
  if($m.path -notmatch '^[A-Za-z0-9_ .()/+-]+$' -or $m.path -match '(^|/)[.]{1,2}(/|$)'){throw 'Unsafe source member path'}
  $path=[IO.Path]::GetFullPath((Join-Path $c.root $m.path))
  if(-not $path.StartsWith($c.root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Source member escaped repository'}
  # Walk to the existing parent for newly added paths. Check every ancestor
  # before stopping the bot; never infer parent type from PSIsContainer.
  $parent=Split-Path -Parent $path
  while(-not(Test-Path -LiteralPath $parent)){$parent=Split-Path -Parent $parent}
  Assert-Protected $parent
  Assert-GitDirectoryInheritance $parent
  if(Test-Path -LiteralPath $path){Assert-Protected $path}
 }
}
function Prepare-SourceParents {
 foreach($m in $c.source_members) {
  if($m.deleted){continue}
  $parent=Split-Path -Parent (Join-Path $c.root $m.path)
  $missing=[Collections.Generic.Stack[string]]::new()
  while(-not(Test-Path -LiteralPath $parent)){$missing.Push($parent);$parent=Split-Path -Parent $parent}
  Assert-Protected $parent
  while($missing.Count){New-Directory $missing.Pop()}
 }
}
function Rows([string]$Query) {
 $connection=[Data.SqlClient.SqlConnection]::new('Server=mini_AMD;Database=ROK_TRACKER;Integrated Security=True;Application Name=K98_Routine_Update;Connect Timeout=5;Encrypt=True;TrustServerCertificate=True;ApplicationIntent=ReadOnly')
 try {
  $connection.Open();$cmd=$connection.CreateCommand();$cmd.CommandTimeout=5;$cmd.CommandText='SET LOCK_TIMEOUT 2000; '+$Query
  $reader=$null;$rows=@()
  try {
   $reader=$cmd.ExecuteReader()
   while($reader.Read()) {
    if($rows.Count -ge 128){throw 'SQL result exceeds exact release scope'}
    $row=[ordered]@{}
    for($i=0;$i -lt $reader.FieldCount;$i++){$v=$reader.GetValue($i);if($v -is [DBNull]){$v=$null};if($v -is [guid]){$v=$v.ToString()};$row[$reader.GetName($i)]=$v}
    $rows+=,[pscustomobject]$row
   }
   return ,$rows
  }finally{if($null -ne $reader){$reader.Dispose()};$cmd.Dispose()}
 }finally{$connection.Dispose()}
}
function Retained-Preparations {
 $account=$c.account
 if($account -notmatch '^[A-Za-z0-9_.@:-]{1,128}$'){throw 'Invalid bound account'}
 return ,(Rows ("SELECT TOP (129) PreparationID,AccountKey,ConsumerKind,State,OwnerID,Fence,Version,JobID,CONVERT(varchar(64),HASHBYTES('SHA2_256',CONVERT(varbinary(max),GenerationJson)),2) AS GenerationHash,SpoolKey,SpoolBytes,CONVERT(varchar(64),SpoolHash,2) AS SpoolHash FROM dbo.ExportPreparation WHERE AccountKey='"+$account+"' AND State IN ('captured','materialized','uncertain') ORDER BY PreparationID;"))
}
function Assert-Held([switch]$SuccessorRunning) {
 $current=Retained-Preparations
 foreach($expected in $c.expected_preparation) {
  $actual=@($current | Where-Object {$_.PreparationID -ceq $expected.PreparationID})
  if($actual.Count -ne 1 -or -not(Same $actual[0] $expected)){throw 'Retained preparation changed; no reconciliation authorized'}
 }
 foreach($expected in $c.expected_resources) {
  $id=([guid]$expected.ActivePreparationID).ToString()
  $actual=Rows ("SELECT ResourceKey,ActiveJobID,ActivePreparationID,ActiveOutputOperationID,OwnerID,Fence,BlockedReason,Version FROM dbo.ExportResource WHERE ActivePreparationID='"+$id+"' ORDER BY ResourceKey;")
  $match=@($actual | Where-Object {$_.ResourceKey -ceq $expected.ResourceKey})
  if($match.Count -ne 1 -or -not(Same $match[0] $expected)){throw 'Retained resource changed'}
 }
 $streams=Rows ("SELECT TOP (129) StreamID,SessionID FROM dbo.ExportExecutionStream WHERE AccountKey='"+$c.account+"' AND State<>'closed';")
 if($streams.Count) {
  if(-not $SuccessorRunning){throw 'Open provider stream blocks release'}
  # The new bot may legitimately perform startup reads. Only its independently
  # verified fresh session may own streams after the single successor start.
  $journal=New-Journal;Assert-NewSession $journal
  $session=(Sessions)[0]
  if(@($streams | Where-Object {$_.SessionID -cne $session.SessionID}).Count){throw 'Stream belongs to an unexpected session'}
 }
}
function Sessions {
 return ,(Rows "SELECT TOP (33) SessionID,AuthorityPrincipal,HostIdentity,CONVERT(varchar(64),ManifestHash,2) AS ManifestHash,State,Version FROM dbo.ExportExecutionSession WHERE HostIdentity='MINI_AMD' COLLATE Latin1_General_100_CI_AS AND State='open' ORDER BY CreatedUTC,SessionID;")
}
function Assert-Predecessor {
 $policy=Read-Json $c.old_policy.Path $c.old_policy.SHA256
 if(-not(Same $policy.flags $c.flags)){throw 'Activation flags differ'}
 $journal=Read-Json $c.old_journal.Path $c.old_journal.SHA256
 if(-not(Same $journal $c.old_journal.Record)){throw 'Predecessor journal differs'}
 $journals=@(Get-ChildItem -LiteralPath $c.old_policy.StateDirectory -Filter 'incarnation-*.json' -File | Select-Object -First 1001 | Sort-Object Name)
 if($journals.Count -gt 1000 -or $journals[-1].FullName -cne $c.old_journal.Path){throw 'Predecessor has advanced; fresh release binding needed'}
 $null=Read-Bytes $c.old_gate.Path $c.old_gate.SHA256
 $null=Read-Bytes $c.old_plan.Python $c.old_plan.PythonSHA256 4MB
}
function Assert-Drained([switch]$SuccessorRunning) {
 Assert-Predecessor
 $requestPath=Join-Path $c.old_policy.StateDirectory 'deployment-request.json'
 $request=Read-Json $requestPath
 if($request.release_id -cne $c.release_id -or $request.policy_sha256 -cne $c.old_policy.SHA256 -or $request.sequence -ne $c.old_journal.Record.sequence -or -not(Same $request.publication $c.old_journal.Record.publication)){throw 'Exact deployment request differs'}
 $receipt=Read-Json $drainPath
 if($receipt.stage -cne 'deployment_drained' -or $receipt.release_id -cne $c.release_id -or $receipt.request_sha256 -cne (Hash (Read-Bytes $requestPath)) -or -not(Same $receipt.previous $c.old_journal.Record)){throw 'Exact protected drain receipt differs'}
 foreach($binding in $c.old_native) {
  $process=$null
  try {$process=[Diagnostics.Process]::GetProcessById([int]$binding.PID);if($process.StartTime.ToFileTimeUtc() -eq [long]$binding.ExpectedCreatedFiletime -and -not $process.HasExited){throw 'Old process still alive'}}
  catch [ArgumentException] { }
  finally {if($null -ne $process){$process.Dispose()}}
 }
 $old=Rows ("SELECT State,Version FROM dbo.ExportExecutionSession WHERE SessionID='"+$c.old_session.SessionID+"';")
 if($old.Count -ne 1 -or $old[0].State -cne 'closed' -or $old[0].Version -ne ($c.old_session.Version+1)){throw 'Prior authority session closure not confirmed'}
 Assert-Held -SuccessorRunning:$SuccessorRunning
}
function Task {
 $service=New-Object -ComObject 'Schedule.Service';$service.Connect();return $service.GetFolder('\').GetTask('StartDLBotAfterSQL')
}
function Assert-Task([string]$Gate,[bool]$Disabled=$false) {
 $task=Task;$d=$task.Definition
 $sid=[Security.Principal.NTAccount]::new($d.Principal.UserId).Translate([Security.Principal.SecurityIdentifier]).Value
 $arguments='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$Gate+'"'
 if($sid -cne $c.sid -or $d.Principal.LogonType -ne 3 -or $d.Principal.RunLevel -ne 1 -or $d.Actions.Count -ne 1 -or $d.Actions.Item(1).Path -cne $powershell -or $d.Actions.Item(1).Arguments -cne $arguments -or $d.Actions.Item(1).WorkingDirectory -cne 'C:\Windows\System32'){throw 'Scheduled action/account differs'}
 if($Disabled -and ($task.Enabled -or $task.GetInstances(0).Count)){throw 'Scheduled launch exclusion required'}
 $security=[Security.AccessControl.RawSecurityDescriptor]::new($task.GetSecurityDescriptor(7))
 if($security.Owner.Value -cne 'S-1-5-32-544' -or -not($security.ControlFlags -band [Security.AccessControl.ControlFlags]::DiscretionaryAclProtected)){throw 'Task protection differs'}
 foreach($ace in $security.DiscretionaryAcl) {
  if($ace.AceQualifier -ne [Security.AccessControl.AceQualifier]::AccessAllowed -or $ace.SecurityIdentifier.Value -notin @('S-1-5-18','S-1-5-32-544',$c.sid)){throw 'Task ACL differs'}
  if($ace.SecurityIdentifier.Value -ceq $c.sid -and $ace.AccessMask -notin @(-1610612736,1179817)){throw 'Application may only read/execute task'}
 }
 return $task
}
function Seed-Complete {
 if(-not(Test-Path -LiteralPath $c.new_seed_directory) -and -not(Test-Path -LiteralPath $c.new_state_directory)){return $false}
 Assert-Protected $c.new_seed_directory;Assert-Protected $c.new_state_directory
 foreach($member in $c.seed_members){$null=Read-Bytes (Join-Path $c.new_seed_directory $member.name) $member.sha256}
 $policy=Read-Json (Join-Path $c.new_seed_directory 'AutomaticStartupPolicy.json') $c.new_policy_sha256
 if(-not(Same $policy $c.new_policy)){throw 'Installed successor policy differs'}
 $null=Assert-Task $newGate
 return $true
}
function Verify-Native {
 $member=@($c.extra_members | Where-Object {$_.name -ceq 'Verify-NewPair.py'})
 if($member.Count -ne 1){throw 'Native verifier not sealed'}
 $script=Join-Path $PSScriptRoot $member[0].name
 $null=Read-Bytes $script $member[0].sha256
 $null=Read-Bytes $c.venv.path $c.venv.sha256 4MB
 & $c.venv.path -I -B $script --bindings (Join-Path $PSScriptRoot 'ReleaseBindings.json') --sha256 $ExpectedBindingsSHA256 | Out-Host
 if($LASTEXITCODE -ne 0){throw 'New native publication not verified'}
}
function New-Journal {
 $journals=@(Get-ChildItem -LiteralPath $c.new_state_directory -Filter 'incarnation-*.json' -File | Select-Object -First 2)
 if($journals.Count -ne 1){throw 'Exactly one successor incarnation required; do not restart'}
 $j=Read-Json $journals[0].FullName
 if($j.sequence -ne ($c.old_journal.Record.sequence+1) -or $j.policy_sha256 -cne $c.new_policy_sha256){throw 'Successor sequence/policy differs'}
 return $j
}
function Assert-NewSession($Journal) {
 $sessions=Sessions
 if($sessions.Count -ne 1 -or $sessions[0].ManifestHash.ToLowerInvariant() -cne $Journal.publication.manifests.authority -or $sessions[0].SessionID -ceq $c.old_session.SessionID -or $sessions[0].AuthorityPrincipal -cne 'S11_ExportApplication' -or $sessions[0].Version -ne 1){throw 'Fresh successor SQL session differs'}
}
function Import-ExportStatus([string]$StartupText) {
 # Only examine the bounded successor log interval. Startup/SQL-session success
 # is not a successful import or provider probe. Missing evidence is degradation,
 # never an inferred healthy result. Do not run business work to test deployment.
 $reason='fresh_import_export_health_evidence_unavailable'
 if($StartupText -match 'S11 export admission remains closed|Export admission disabled:|Export coordinator unavailable') {
  $reason='runtime_admission_unavailable'
 }
 return @{status='degraded';import_status='degraded';export_status='degraded';reason=$reason;provider_delivery_verified=$false}
}
function Check-Readiness {
 Assert-Drained -SuccessorRunning;Assert-Source $c.new_pins $c.target
 if(-not(Seed-Complete)){throw 'Successor seed missing'}
 $journal=New-Journal;Verify-Native;Assert-NewSession $journal
 $start=Read-Json (Join-Path $PSScriptRoot 'start-requested.json')
 $log=Join-Path $c.root 'logs\log.txt'
 $stream=[IO.File]::Open($log,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
 try {
  if($stream.Length -lt [long]$start.log_offset -or $stream.Length-[long]$start.log_offset -gt 8MB){throw 'Startup log rotated/exceeded bound; readiness unresolved'}
  $null=$stream.Seek([long]$start.log_offset,[IO.SeekOrigin]::Begin)
  $reader=[IO.StreamReader]::new($stream);$text=$reader.ReadToEnd()
 }finally{$stream.Dispose()}
 if($text -notmatch '\[BOOT\] full_startup_sequence completed successfully' -or $text -notmatch 'Logged in as'){return $false}
 $health=Import-ExportStatus $text
 $status=@{release_id=$c.release_id;target=$c.target;discord_status='online';import_export=$health}|ConvertTo-Json -Depth 5 -Compress|ConvertFrom-Json
 $statusPath=Join-Path $PSScriptRoot 'readiness-status.json'
 if(Test-Path -LiteralPath $statusPath) {
  $prior=Read-Json $statusPath
  if(-not(Same $prior $status)){throw 'Readiness classification changed; preserve evidence for review'}
 } else {Write-Record $statusPath $status}
 Write-Warning ('DEPLOYED WITH DEGRADED IMPORT/EXPORT STATUS: '+$health.reason+'. No import/export or provider delivery is certified.')
 Write-Host ('READY: Discord online; exact source '+$c.target+'; import=degraded; export=degraded; retained work and activation flags preserved.')
 return $true
}

if($Action -ceq 'Library'){return}
try {
 if($ExpectedBindingsSHA256 -cnotmatch '^[a-f0-9]{64}$'){throw 'Exact bindings hash required'}
 Assert-Protected $PSScriptRoot
 $c=Read-Json (Join-Path $PSScriptRoot 'ReleaseBindings.json') $ExpectedBindingsSHA256
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
 if($env:COMPUTERNAME -cne $c.host -or $identity.User.Value -cne $c.sid -or -not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Release identity differs'}
 if($identity.Owner.Value -cne 'S-1-5-32-544'){throw 'Administrative default object owner required before Git can create source or metadata'}
 $drainPath=Join-Path $c.old_policy.StateDirectory ('deployment-drained-'+$c.release_id+'.json')
 $newGate=Join-Path $c.new_seed_directory 'Start-ReviewedAutomaticStartup.ps1'
 switch($Action) {
  'Preflight' {
   Assert-Predecessor
   if(Test-Path -LiteralPath $drainPath){Assert-Drained -SuccessorRunning:(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'start-requested.json'));exit 0}
   Assert-Held
   Assert-Source $c.old_pins $c.before;Assert-UpdatePaths;$null=Read-Bytes $c.venv.path $c.venv.sha256 4MB;$null=Assert-Task $c.old_gate.Path
   & $c.venv.path -I -B -c 'import win32file, win32api, win32security' | Out-Host
   if($LASTEXITCODE -ne 0){throw 'Installed venv native dependencies unavailable; bot remains running'}
   if((Test-Path -LiteralPath $c.new_seed_directory) -or (Test-Path -LiteralPath $c.new_state_directory)){throw 'Successor state already exists without drain receipt'}
   if(-not(Same (Sessions) @($c.old_session))){throw 'Current authority session differs'}
   foreach($b in $c.old_native){$p=[Diagnostics.Process]::GetProcessById([int]$b.PID);try{if($p.StartTime.ToFileTimeUtc() -ne [long]$b.ExpectedCreatedFiletime -or $p.HasExited){throw 'Current native identity differs'}}finally{$p.Dispose()}}
   Write-Host 'Preflight passed: exact live predecessor, held claim unchanged, no provider stream.';exit 0
  }
  'VerifySource' {
   $head=Git 'rev-parse HEAD'
   if($head -ceq $c.target){Assert-Source $c.new_pins $c.target;foreach($m in $c.source_members){$path=Join-Path $c.root $m.path;if($m.deleted){if(Test-Path -LiteralPath $path){throw 'Deleted member exists'}}else{$null=Read-Bytes $path $m.target_sha256 2MB}};exit 0}
   if($head -ceq $c.before){Assert-Source $c.old_pins $c.before;exit 10}
   throw 'Unrecognized source outcome'
  }
  'ApplySource' {
   Assert-Drained;Assert-Source $c.old_pins $c.before;Assert-UpdatePaths;$null=Read-Bytes $c.venv.path $c.venv.sha256 4MB;$null=Assert-Task $c.old_gate.Path $true
   Assert-UpdatePaths
   Prepare-SourceParents
   if((Git 'rev-parse refs/remotes/origin/main') -cne $c.target){throw 'Acquired private-main target changed'}
   $null=Git ('merge-base --is-ancestor '+$c.before+' '+$c.target)
   $null=Git ('update-ref refs/heads/codex/before-update-'+$c.release_id+' '+$c.before+' 0000000000000000000000000000000000000000')
   $null=Git ('merge --ff-only --no-overwrite-ignore --no-edit '+$c.target)
   foreach($m in $c.source_members) {
    $path=Join-Path $c.root $m.path
    if($m.deleted){if(Test-Path -LiteralPath $path){throw 'Deleted member still exists'};continue}
    # Git creates source under the admin token; apply explicit custody and the
    # authenticated byte convention before any new source is executed.
    Set-Acl -LiteralPath $path -AclObject (New-Acl $false)
    $bytes=Read-Bytes (Join-Path $PSScriptRoot $m.payload) $m.target_sha256 2MB
    [IO.File]::WriteAllBytes($path,$bytes)
    $null=Read-Bytes $path $m.target_sha256 2MB
   }
   Assert-Source $c.new_pins $c.target;exit 0
  }
  'VerifySeed' {
   if(Seed-Complete){exit 0};exit 10
  }
  'ApplySeed' {
   Assert-Drained;Assert-Source $c.new_pins $c.target;$task=Assert-Task $c.old_gate.Path $true
   if((Test-Path -LiteralPath $c.new_seed_directory) -or (Test-Path -LiteralPath $c.new_state_directory)){throw 'Partial seed must not be overwritten'}
   New-Directory $c.new_seed_directory;New-Directory $c.new_state_directory
   foreach($m in $c.seed_members){$bytes=Read-Bytes (Join-Path $PSScriptRoot $m.name) $m.sha256;Write-New (Join-Path $c.new_seed_directory $m.name) $bytes}
   Write-New (Join-Path $PSScriptRoot 'task-before.xml') ([Text.UTF8Encoding]::new($false).GetBytes($task.Xml))
   $d=$task.Definition;$d.Settings.Enabled=$false;$d.Actions.Item(1).Arguments='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$newGate+'"'
   $service=New-Object -ComObject 'Schedule.Service';$service.Connect()
   $sddl='O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;GRGX;;;'+$c.sid+')'
   $null=$service.GetFolder('\').RegisterTaskDefinition('StartDLBotAfterSQL',$d,60,$d.Principal.UserId,$null,3,$sddl)
   $updated=Task;$updated.SetSecurityDescriptor($sddl,16)
   $null=Assert-Task $newGate $true
   if(-not(Seed-Complete)){throw 'Seed installation not verified'};exit 0
  }
  'VerifyStart' {
   if(-not(Seed-Complete)){throw 'Seed missing'}
   $journals=@(Get-ChildItem -LiteralPath $c.new_state_directory -Filter 'incarnation-*.json' -File | Select-Object -First 2)
   if(-not $journals.Count -and -not(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'start-requested.json'))){$null=Assert-Task $newGate $true;exit 10}
   $j=New-Journal;Verify-Native;Assert-NewSession $j;exit 0
  }
  'ApplyStart' {
   Assert-Drained;Assert-Source $c.new_pins $c.target
   if(-not(Seed-Complete)){throw 'Seed missing'}
   $task=Assert-Task $newGate $true
   if(@(Get-ChildItem -LiteralPath $c.new_state_directory -File).Count){throw 'Fresh successor history required'}
   $log=Get-Item -LiteralPath (Join-Path $c.root 'logs\log.txt')
   Write-Record (Join-Path $PSScriptRoot 'start-requested.json') @{release_id=$c.release_id;requested_utc=[datetime]::UtcNow.ToString('o');log_offset=$log.Length}
   $task.Enabled=$true
   $null=$task.Run($null)
   $watch=[Diagnostics.Stopwatch]::StartNew()
   do {
    Start-Sleep -Seconds 2
    $journals=@(Get-ChildItem -LiteralPath $c.new_state_directory -Filter 'incarnation-*.json' -File | Select-Object -First 2)
    if($journals.Count -eq 1){try{$j=New-Journal;Verify-Native;Assert-NewSession $j;exit 0}catch{if($watch.Elapsed.TotalSeconds -ge 120){throw}}}
   }while($watch.Elapsed.TotalSeconds -lt 120)
   throw 'One start requested but not confirmed; do not start again'
  }
  'VerifyReadiness' {if(Check-Readiness){exit 0};exit 10}
  'AwaitReadiness' {
   $watch=[Diagnostics.Stopwatch]::StartNew()
   do {if(Check-Readiness){exit 0};Start-Sleep -Seconds 3}while($watch.Elapsed.TotalSeconds -lt 180)
   throw 'Startup/readiness remains unconfirmed; preserve state'
  }
 }
}catch{
 Write-Error ('Release step '+$Action+' stopped: '+$_.Exception.Message)
 exit 1
}
