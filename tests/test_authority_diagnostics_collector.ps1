param([Parameter(Mandatory=$true)][string]$Collector)
$ErrorActionPreference='Stop'
. $Collector
$created=[DateTimeOffset]::Parse('2026-10-23T21:00:00Z')
$record=[ordered]@{
 stage='AUTHORITY_REQUEST_FAILED';observed_utc='2026-10-23T21:01:00+00:00'
 diagnostic_id='00000000-0000-0000-0000-000000000001';authority_pid=1234
 action='execute';checkpoint='request_prepared';stream_id=$null;object_id=$null
 request_id='00000000-0000-0000-0000-000000000002'
 exception_types=@('ProgrammingError');sqlstates=@('42000');sql_numbers=@(51700)
 reason_code='account_busy';frames=@([ordered]@{file='authority.py';function='execute';line=123})
}
function Encode-Record($Value){($Value|ConvertTo-Json -Depth 8 -Compress)+"`n"}
$json=Encode-Record $record
$rows=@(Select-AuthorityDiagnostics $json 1234 $created)
if($rows.Count -ne 1 -or $rows[0].checkpoint -cne 'request_prepared'){throw 'Valid capture missing'}
foreach($bad in @('unknown-stage','secret-field','wrong-pid','old-process','partial','invalid-frame','private-reason','oversized')) {
 $copy=$json|ConvertFrom-Json
 switch($bad) {
  'unknown-stage' {$copy.stage='SECRET'}
  'secret-field' {$copy|Add-Member -NotePropertyName password -NotePropertyValue SECRET}
  'wrong-pid' {$copy.authority_pid=9876}
  'old-process' {$copy.observed_utc='2026-10-23T20:59:00Z'}
  'invalid-frame' {$copy.frames[0].file='C:\secret\authority.py'}
  'private-reason' {$copy.reason_code='SECRET'}
 }
 $fixtureText=Encode-Record $copy
 if($bad -eq 'partial'){$fixtureText=$fixtureText.TrimEnd([char]10)}
 if($bad -eq 'oversized'){$fixtureText=(' '*16385)+$fixtureText}
 if(@(Select-AuthorityDiagnostics $fixtureText 1234 $created).Count){throw ('Unsafe record accepted: '+$bad)}
}
# JSON null/arrays and incomplete lines must not hide subsequent valid rows.
$rows=@(Select-AuthorityDiagnostics ("null`n[]`n{broken`n"+$json) 1234 $created)
if($rows.Count -ne 1){throw 'Malformed record isolation failed'}
'PASS: strict projection, pinned incarnation, redaction, partial and malformed records'

