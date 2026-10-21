[CmdletBinding()]
param()
# Read-only collection for the already completed 21 October publication check.
# Never loads application code, starts a process, connects to SQL/provider, or
# changes a task, policy, manifest, journal, cache, receipt or diagnostic file.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

function Assert-TimingPath([string]$Path) {
 if(-not [IO.Path]::IsPathRooted($Path)){throw 'Absolute installed path required'}
 $item=Get-Item -LiteralPath $Path -Force
 $strict=if($item.PSIsContainer){0}else{1};$depth=0
 $trusted=@('S-1-5-18','S-1-5-32-544','S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
 while($null -ne $item) {
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse path refused'}
  $acl=Get-Acl -LiteralPath $item.FullName
  if($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $trusted){throw 'Protected owner differs'}
  $mask=if($depth -le $strict){0x500d0156}else{0x500d0040}
  foreach($ace in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
   if($ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
      ($ace.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0 -and
      $ace.IdentityReference.Value -notin $trusted -and ([long]$ace.FileSystemRights -band $mask) -ne 0){throw 'Untrusted write access'}
  }
  $item=if($item.PSIsContainer){$item.Parent}else{$item.Directory};$depth++
 }
}

function Timing-Hash([byte[]]$Bytes) {
 $hash=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$hash.Dispose()}
}

function Read-TimingBytes([string]$Path,[string]$Expected='', [int]$Limit=1MB) {
 Assert-TimingPath $Path
 $item=Get-Item -LiteralPath $Path -Force
 if($item.PSIsContainer -or $item.Length -gt $Limit){throw 'Bounded file required'}
 # The authority keeps this file open. Shared read/write/delete also tolerates
 # rotation; only bytes present at open are collected and a partial line is ignored.
 $stream=[IO.FileStream]::new($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
 try {
  $length=$stream.Length
  if($length -gt $Limit){throw 'File exceeds bound'}
  $bytes=New-Object byte[] ([int]$length)
  $offset=0
  while($offset -lt $length){$count=$stream.Read($bytes,$offset,$length-$offset);if($count -eq 0){throw 'File changed during collection'};$offset+=$count}
 } finally {$stream.Dispose()}
 if($Expected -and (Timing-Hash $bytes) -cne $Expected){throw 'Pinned file differs'}
 return ,$bytes
}

function Read-TimingJson([string]$Path,[string]$Expected='') {
 [Text.Encoding]::UTF8.GetString((Read-TimingBytes $Path $Expected))|ConvertFrom-Json
}

function Select-PublicationPhases([string]$Text) {
 $pattern='^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) UTC publication_verification_phase phase=(retained_history|provider_readback|sealed_history|sealed_response_replay|final_origin_verification) completed=(True|False) duration_ms=(\d{1,12})\r?$'
 $start=[DateTimeOffset]::Parse('2026-10-21T06:23:54Z')
 $end=[DateTimeOffset]::Parse('2026-10-21T06:38:07Z')
 # Require a terminating newline: an active partial final record is not evidence.
 $lines=$Text.Split([char]10)
 for($i=0;$i -lt $lines.Count-1;$i++) {
  if($lines[$i] -cmatch $pattern) {
   $stamp=[DateTimeOffset]::ParseExact($Matches[1]+' +00:00','yyyy-MM-dd HH:mm:ss,fff zzz',[Globalization.CultureInfo]::InvariantCulture)
   if($stamp -ge $start -and $stamp -le $end) {
    [pscustomobject]@{ended_utc=$stamp.ToString('o');phase=$Matches[2];completed=($Matches[3] -ceq 'True');duration_ms=[long]$Matches[4]}
   }
  }
 }
}

function Get-SavedPublicationTiming {
 if($env:COMPUTERNAME -cne 'MINI_AMD'){throw 'Run on MINI_AMD'}
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
 if(-not([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Administrator read access required'}
 $scheduler=New-Object -ComObject 'Schedule.Service'
 $scheduler.Connect()
 $actions=$scheduler.GetFolder('\').GetTask('StartDLBotAfterSQL').Definition.Actions
 if($actions.Count -ne 1 -or $actions.Item(1).Path -cne 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'){throw 'Startup action differs'}
 if($actions.Item(1).Arguments -cnotmatch '^-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "(C:\\ProgramData\\K98\\S11\\runtime\\[0-9a-f-]{36}\\Start-ReviewedAutomaticStartup.ps1)"$'){throw 'Startup gate differs'}
 $gatePath=$Matches[1]
 $gate=[Text.Encoding]::UTF8.GetString((Read-TimingBytes $gatePath))
 $policyPath=Join-Path (Split-Path -Parent $gatePath) 'AutomaticStartupPolicy.json'
 $policyBytes=Read-TimingBytes $policyPath
 $policyHash=Timing-Hash $policyBytes
 if(-not $gate.Contains('$policyHash='''+$policyHash+'''') -or -not $gate.Contains('$policy='''+$policyPath+'''')){throw 'Policy binding differs'}
 $policy=[Text.Encoding]::UTF8.GetString($policyBytes)|ConvertFrom-Json
 $seed=Read-TimingJson $policy.seed_plan.path $policy.seed_plan.sha256
 if($seed.application_sid -cne $identity.User.Value){throw 'Use the installed deployment account'}
 Assert-TimingPath $policy.state_directory
 $journals=@(Get-ChildItem -LiteralPath $policy.state_directory -Filter 'incarnation-*.json' -File | Select-Object -First 1001 | Sort-Object Name)
 if($journals.Count -lt 1 -or $journals.Count -gt 1000){throw 'Bounded incarnation history required'}
 $journalFile=$journals[-1]
 if($journalFile.Name -cnotmatch '^incarnation-[0-9]{20}-([0-9a-f-]{36})\.json$'){throw 'Incarnation name differs'}
 $live=Join-Path (Split-Path -Parent (Split-Path -Parent $seed.commit_file)) $Matches[1]
 $journal=Read-TimingJson $journalFile.FullName
 if($journal.policy_sha256 -cne $policyHash){throw 'Publication policy differs'}
 $plan=Read-TimingJson (Join-Path $live 'ManualProcessPairPlan-CANDIDATE.json') $journal.publication.plan_sha256
 $authority=Read-TimingJson $plan.manifests.authority $journal.publication.manifests.authority
 Assert-TimingPath $authority.evidence_root
 $rows=@();$absent=0
 foreach($name in @('publication-timing.log.2','publication-timing.log.1','publication-timing.log')) {
  $path=Join-Path $authority.evidence_root $name
  if(-not(Test-Path -LiteralPath $path)){$absent++;continue}
  $raw=Read-TimingBytes $path '' 262144
  $rows+=@(Select-PublicationPhases ([Text.Encoding]::UTF8.GetString($raw)))
 }
 # Revalidate the selected journal: never silently combine two incarnations.
 $again=Read-TimingJson $journalFile.FullName
 if(($again|ConvertTo-Json -Depth 50 -Compress) -cne ($journal|ConvertTo-Json -Depth 50 -Compress)){throw 'Incarnation changed during collection'}
 [pscustomobject]@{version=1;read_only=$true;window_start_utc='2026-10-21T06:23:54Z';window_end_utc='2026-10-21T06:38:07Z';absent_rotations=$absent;records=@($rows|Sort-Object ended_utc,phase -Unique);contains_operational_identifiers=$false}
}

if($MyInvocation.InvocationName -ne '.') {
 try {Get-SavedPublicationTiming | ConvertTo-Json -Depth 5}
 catch {throw ('Read-only timing collection stopped: '+$_.Exception.GetType().Name+'. No application operation was invoked.')}
}
