[CmdletBinding()]
param()
# Read-only: reuse verified task/policy/manifest custody; never load bot code.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Read-K98PublicationTiming.ps1')

function Select-AuthorityDiagnostics([string]$Text,[int]$AuthorityProcessId,[DateTimeOffset]$CreatedUtc) {
 $stages=@('AUTHORITY_CAPTURE_READY','AUTHORITY_PROCESS_FAILED','AUTHORITY_SERVING','AUTHORITY_DISPATCH_FAILED','AUTHORITY_CONNECTION_FAILED','AUTHORITY_REQUEST_FAILED','AUTHORITY_REQUEST_COMPLETED','AUTHORITY_STOPPED')
 $steps=@('request_lookup','request_payload','request_prepared','request_budget','request_guard','request_dispatch','provider_child','response_validation','request_result','budget_complete','budget_feedback')
 $reasons=@('sql_snapshot_owned','account_busy','resource_busy','resource_version_conflict','stream_version_conflict','preparation_version_conflict')
 $guidPattern='^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
 $fields=@('stage','observed_utc','diagnostic_id','authority_pid','action','checkpoint','stream_id','object_id','request_id','exception_types','sqlstates','sql_numbers','reason_code','frames')
 $lines=$Text.Split([char]10)
 for($i=0;$i -lt $lines.Count-1;$i++) {
  if($lines[$i].Length -gt 16384){continue}
  try {
   $row=$lines[$i]|ConvertFrom-Json
   if(@($row.PSObject.Properties).Count -ne $fields.Count){continue}
   if(@($row.PSObject.Properties.Name|Where-Object {$_ -cnotin $fields}).Count){continue}
   $valid=$true
   foreach($key in @('stage','observed_utc','diagnostic_id','action')){if($row.$key -isnot [string]){$valid=$false}}
   foreach($key in @('checkpoint','reason_code','stream_id','object_id','request_id')){if($null -ne $row.$key -and $row.$key -isnot [string]){$valid=$false}}
   if(-not $valid -or $row.authority_pid -isnot [int]){continue}
   if($row.stage -cnotin $stages -or $row.authority_pid -ne $AuthorityProcessId){continue}
   $stamp=[DateTimeOffset]::Parse($row.observed_utc)
   if($stamp.Offset -ne [TimeSpan]::Zero -or $stamp -lt $CreatedUtc){continue}
   if($row.diagnostic_id -cnotmatch $guidPattern -or $row.action -cnotin @('invalid','ready','open','execute','close','prove')){continue}
   if($null -ne $row.checkpoint -and $row.checkpoint -cnotin $steps){continue}
   if($null -ne $row.reason_code -and $row.reason_code -cnotin $reasons){continue}
   $valid=$true
   foreach($key in @('stream_id','object_id','request_id')){if($null -ne $row.$key -and $row.$key -cnotmatch $guidPattern){$valid=$false}}
   if(@($row.exception_types).Count -gt 8 -or @($row.sqlstates).Count -gt 4 -or @($row.sql_numbers).Count -gt 8 -or @($row.frames).Count -gt 16){continue}
   foreach($name in $row.exception_types){if($name -isnot [string] -or $name -cnotmatch '^[A-Za-z_][A-Za-z0-9_]{0,63}$'){$valid=$false}}
   foreach($state in $row.sqlstates){if($state -isnot [string] -or $state -cnotmatch '^[A-Z0-9]{5}$'){$valid=$false}}
   foreach($number in $row.sql_numbers){if($number -isnot [int] -and $number -isnot [long]){$valid=$false};if($number -lt 100 -or $number -gt 999999){$valid=$false}}
   foreach($frame in $row.frames){
    if(@($frame.PSObject.Properties).Count -ne 3 -or @($frame.PSObject.Properties.Name|Where-Object {$_ -cnotin @('file','function','line')}).Count){$valid=$false;continue}
    if($frame.file -isnot [string] -or $frame.function -isnot [string] -or $frame.file -cnotmatch '^[A-Za-z0-9_]{1,80}\.py$' -or $frame.function -cnotmatch '^[A-Za-z_][A-Za-z0-9_]{0,79}$' -or $frame.line -isnot [int] -or $frame.line -lt 1){$valid=$false}
   }
   if($valid){$row}
  } catch {continue} # Partial/malformed records are not diagnostic evidence.
 }
}

function Get-SavedAuthorityDiagnostics {
 $binding=Get-VerifiedPublicationAuthority
 $authority=$binding.authority;$identity=$binding.identity;$journal=$binding.journal
 $processId=[int]$journal.bindings.authority.pid
 $created=[DateTimeOffset]::new([DateTime]::FromFileTimeUtc([long]$journal.bindings.authority.created_filetime))
 $rows=@();$absent=0
 foreach($name in @('authority-diagnostics.jsonl.2','authority-diagnostics.jsonl.1','authority-diagnostics.jsonl')) {
  $path=Join-Path $authority.evidence_root $name
  if(-not(Test-Path -LiteralPath $path)){$absent++;continue}
  $raw=Read-TimingBytes $path '' 262144 $identity.User.Value
  $rows+=@(Select-AuthorityDiagnostics ([Text.Encoding]::UTF8.GetString($raw)) $processId $created)
 }
 $again=Read-TimingJson $binding.journalFile.FullName
 if(($again|ConvertTo-Json -Depth 50 -Compress) -cne ($journal|ConvertTo-Json -Depth 50 -Compress)){throw 'Incarnation changed during collection'}
 $rows=@($rows|Sort-Object observed_utc,diagnostic_id -Unique)
 [pscustomobject]@{
  format='k98-authority-diagnostics-v1';read_only=$true;generated_utc=[DateTime]::UtcNow.ToString('o')
  sequence=$journal.sequence;authority_pid=$processId;authority_created_utc=$created.ToString('o')
  capture_ready_observed=(@($rows|Where-Object stage -CEQ 'AUTHORITY_CAPTURE_READY').Count -gt 0)
  serving_observed=(@($rows|Where-Object stage -CEQ 'AUTHORITY_SERVING').Count -gt 0)
  absent_rotations=$absent;contains_operational_identifiers=$true;records=$rows
  qualification='Bounded observations for the pinned incarnation, not receipts or proof of current health. Missing or rotated records do not prove success. No SQL/provider call or application operation.'
 }
}

if($MyInvocation.InvocationName -ne '.') {
 try {Get-SavedAuthorityDiagnostics | ConvertTo-Json -Depth 8}
 catch {throw ('Read-only authority collection stopped: '+$_.Exception.GetType().Name+'. No application operation was invoked.')}
}
