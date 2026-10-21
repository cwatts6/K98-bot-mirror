param([Parameter(Mandatory=$true)][string]$Collector)
$ErrorActionPreference='Stop'
. $Collector
$sample="2026-10-21 06:25:00,000 UTC publication_verification_phase phase=retained_history completed=True duration_ms=300`n"+
 "2026-10-21 06:30:00,123 UTC publication_verification_phase phase=provider_readback completed=False duration_ms=123456`r`n"+
 "2026-10-21 06:39:00,000 UTC publication_verification_phase phase=sealed_history completed=True duration_ms=3`n"+
 "2026-10-21 06:30:00,000 UTC private_credentials=never-export-this`n"+
 "2026-10-21 06:30:00,000 UTC publication_verification_phase phase=foreign_phase completed=True duration_ms=3`n"+
 "2026-10-21 06:31:00,000 UTC publication_verification_phase phase=sealed_history completed=True duration_ms=3"
$rows=@(Select-PublicationPhases $sample)
if($rows.Count -ne 2 -or $rows[0].phase -cne 'retained_history' -or -not $rows[0].completed -or $rows[1].completed -or $rows[1].duration_ms -ne 123456){throw 'Exact redacted phase parsing failed'}
if(($rows|ConvertTo-Json) -match 'private_credentials|never-export|foreign_phase'){throw 'Private content leaked'}
# Temporary fixture bypasses custody only in this disposable test process.
function Assert-TimingPath([string]$Path) {}
$path=Join-Path ([IO.Path]::GetTempPath()) ('k98-timing-test-'+[guid]::NewGuid().ToString('N')+'.log')
$writer=$null
try {
 $writer=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite)
 $bytes=[Text.Encoding]::UTF8.GetBytes($sample)
 $writer.Write($bytes,0,$bytes.Length);$writer.Flush()
 $result=Read-TimingBytes $path '' 262144
 if((Timing-Hash $result) -cne (Timing-Hash $bytes)){throw 'Shared read differs'}
 $rejected=$false
 try{$null=Read-TimingBytes $path '' 5}catch{$rejected=$true}
 if(-not $rejected){throw 'Size limit not enforced'}
 $rejected=$false
 try{$null=Read-TimingBytes $path ('0'*64)}catch{$rejected=$true}
 if(-not $rejected){throw 'Hash mismatch not rejected'}
} finally {
 if($null -ne $writer){$writer.Dispose()}
 if(Test-Path -LiteralPath $path){Remove-Item -LiteralPath $path}
}
'PASS: redaction, window, partial record, shared active-file read, bounds, hash mismatch'

$start=[DateTimeOffset]::Parse('2026-10-22T10:00:00Z')
$end=$start.AddMinutes(30)
$detail="2026-10-22 10:05:00,000 UTC publication_verification_detail step=provider_child count=8 failed=0 duration_ms=1200`n"+
 "2026-10-22 10:05:00,001 UTC publication_verification_detail step=private-secret count=1 failed=0 duration_ms=1`n"+
 "2026-10-22 10:05:00,002 UTC publication_verification_detail step=budget_wait count=1 failed=2 duration_ms=1`n"+
 "2026-10-22 10:05:00,003 UTC publication_verification_detail step=budget_sql count=0 failed=0 duration_ms=1`n"+
 "2026-10-22 10:31:00,004 UTC publication_verification_detail step=budget_sql count=1 failed=0 duration_ms=1`n"+
 "2026-10-22 10:05:00,005 UTC publication_verification_detail step=budget_complete count=1 failed=0 duration_ms=1"
$parsed=@(Select-PublicationDetails $detail $start $end)
if($parsed.Count -ne 1 -or $parsed[0].step -cne 'provider_child' -or $parsed[0].count -ne 8 -or $parsed[0].duration_ms -ne 1200){throw 'Bounded detail parsing failed'}
foreach($bad in @($start,$start.AddSeconds(-1),$start.AddHours(25))) {
 $refused=$false
 try{$null=Select-PublicationDetails $detail $start $bad}catch{$refused=$true}
 if(-not $refused){throw 'Invalid window accepted'}
}
'PASS: explicit window, detail redaction, malformed count, partial line and 24-hour bound'
