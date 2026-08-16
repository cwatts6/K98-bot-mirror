[CmdletBinding()]
param(
    [ValidateSet('localhost', '.', '(local)')]
    [string]$ServerName = 'localhost',

    [ValidateSet('ROK_TRACKER_BACKUP_TEST_KS4_PHASE3_REHEARSAL')]
    [string]$DatabaseName = 'ROK_TRACKER_BACKUP_TEST_KS4_PHASE3_REHEARSAL',

    [ValidateSet('C:\discord_file_downloader\downloads_test_phase5_rehearsal')]
    [string]$TestRoot = 'C:\discord_file_downloader\downloads_test_phase5_rehearsal',

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^phase5_1_[0-9]{8}T[0-9]{9}Z$')]
    [string]$FailedRunId,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^stats_[0-9a-f]{32}\.ready\.csv$')]
    [string]$CompletedFileName,

    [Parameter(Mandatory = $true)]
    [switch]$ConfirmDiscardFailedAttempt,

    [Parameter(Mandatory = $true)]
    [switch]$ConfirmWritersStopped
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedMachine = 'MINI_AMD'
$resolvedRoot = [IO.Path]::GetFullPath($TestRoot).TrimEnd('\')
if ($env:COMPUTERNAME -ine $expectedMachine) {
    throw "Run locally on $expectedMachine. Current host: $env:COMPUTERNAME"
}
if (-not $ConfirmDiscardFailedAttempt.IsPresent -or -not $ConfirmWritersStopped.IsPresent) {
    throw 'Reset requires -ConfirmDiscardFailedAttempt and -ConfirmWritersStopped.'
}
if ($DatabaseName -ceq 'ROK_TRACKER') {
    throw 'Phase 5.1 failed-evidence reset refuses the production database.'
}
if ($resolvedRoot -cne 'C:\discord_file_downloader\downloads_test_phase5_rehearsal') {
    throw 'Phase 5.1 failed-evidence reset refuses an unreviewed filesystem root.'
}

$readyRoot = Join-Path $resolvedRoot 'Import_Ready'
$claimedRoot = Join-Path $resolvedRoot 'Import_Claimed'
$archiveRoot = Join-Path $resolvedRoot 'Import_Archive'
$failedRunRoot = Join-Path (Join-Path $resolvedRoot 'evidence') $FailedRunId
$transcriptPath = Join-Path $failedRunRoot 'transcript.log'
$successReceiptPath = Join-Path $failedRunRoot 'receipt.json'
$failedReceiptPath = Join-Path $failedRunRoot 'receipt.failed.json'
$quarantineRoot = Join-Path $failedRunRoot 'failed_work_files'
$resetReceiptPath = Join-Path $quarantineRoot 'reset_receipt.json'

if (-not (Test-Path -LiteralPath $transcriptPath -PathType Leaf)) {
    throw "Failed evidence transcript is missing: $transcriptPath"
}
if (Test-Path -LiteralPath $successReceiptPath -PathType Leaf) {
    throw 'Reset refuses a run that already has a successful receipt.'
}
if (Test-Path -LiteralPath $failedReceiptPath -PathType Leaf) {
    throw 'This reset is only for the retained pre-remediation failure without receipt.failed.json.'
}
if (Test-Path -LiteralPath $resetReceiptPath -PathType Leaf) {
    throw "Reset receipt already exists: $resetReceiptPath"
}

$readyPath = Join-Path $readyRoot $CompletedFileName
$claimedPath = Join-Path $claimedRoot $CompletedFileName
$renamedPath = "$claimedPath.renamed"
$archivePath = Join-Path $archiveRoot $CompletedFileName
$quarantinePath = Join-Path $quarantineRoot "$CompletedFileName.renamed"

foreach ($unexpectedPath in @($readyPath, $claimedPath, $archivePath)) {
    if (Test-Path -LiteralPath $unexpectedPath) {
        throw "Reset found an unexpected protocol file: $unexpectedPath"
    }
}

$renamedExists = Test-Path -LiteralPath $renamedPath -PathType Leaf
$quarantineExists = Test-Path -LiteralPath $quarantinePath -PathType Leaf
if ($renamedExists -eq $quarantineExists) {
    throw 'Reset requires exactly one retained renamed file or one resumable quarantined file.'
}
$retainedPath = if ($renamedExists) { $renamedPath } else { $quarantinePath }
$retainedItem = Get-Item -LiteralPath $retainedPath
$retainedHash = (Get-FileHash -LiteralPath $retainedPath -Algorithm SHA256).Hash
$expectedReplacementHash = '95713E9CBDD1DFCB2D4080C2537F418D43CA0DA25F0D7D6631F4F7C97B89DC47'
if ($retainedItem.Length -ne 11 -or $retainedHash -cne $expectedReplacementHash) {
    throw 'Retained renamed file does not match the exact 11-byte replacement failure shape.'
}

function Invoke-ResetSql {
    param([Parameter(Mandatory = $true)][string]$Query)

    Invoke-Sqlcmd -ServerInstance $ServerName -Database $DatabaseName -Query $Query -AbortOnError -TrustServerCertificate -ErrorAction Stop
}

$databaseGuard = Invoke-ResetSql -Query @"
SELECT DB_NAME() AS DatabaseName,
       @@SERVERNAME AS ServerName,
       CASE WHEN DB_NAME() = N'ROK_TRACKER' THEN 0 ELSE 1 END AS IsIsolated;
"@
if ([int]$databaseGuard.IsIsolated -ne 1) {
    throw 'Database guard did not prove an isolated target.'
}

$claim = Invoke-ResetSql -Query @"
SELECT claim.CompletedFileName,
       claim.ClaimStatus,
       CONVERT(varchar(64), claim.FileDigest, 2) AS FileDigest,
       claim.ReadyPath,
       claim.ClaimedPath,
       claim.ArchivePath,
       claim.ClaimRequestedAtUtc,
       claim.ClaimedAtUtc,
       claim.LastError,
       CASE WHEN receipt.FileDigest IS NULL THEN 0 ELSE 1 END AS HasReceipt
FROM dbo.KS4_ImportFileClaim AS claim
LEFT JOIN dbo.KS4_ImportFileReceipt AS receipt
  ON receipt.FileDigest = claim.FileDigest
WHERE claim.CompletedFileName = N'$CompletedFileName';
"@
if ($null -eq $claim -or $claim.CompletedFileName -cne $CompletedFileName) {
    throw 'Reset did not find exactly the requested failed claim.'
}
if (
    $claim.ClaimStatus -cne 'claimed' -or
    [int]$claim.HasReceipt -ne 0 -or
    $claim.ReadyPath -cne $readyPath -or
    $claim.ClaimedPath -cne $claimedPath -or
    $claim.ArchivePath -cne $archivePath
) {
    throw 'Failed claim does not match the exact retained Phase 5.1 evidence shape.'
}

New-Item -ItemType Directory -Path $quarantineRoot -Force | Out-Null
if ($renamedExists) {
    Move-Item -LiteralPath $renamedPath -Destination $quarantinePath -ErrorAction Stop
}
if (-not (Test-Path -LiteralPath $quarantinePath -PathType Leaf)) {
    throw 'Reset did not quarantine the renamed failure artifact.'
}
if ((Get-FileHash -LiteralPath $quarantinePath -Algorithm SHA256).Hash -cne $retainedHash) {
    throw 'Quarantined failure artifact digest changed.'
}

$deleteResult = Invoke-ResetSql -Query @"
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF EXISTS
(
    SELECT 1
    FROM dbo.KS4_ImportFileReceipt AS receipt
    INNER JOIN dbo.KS4_ImportFileClaim AS claim
      ON claim.FileDigest = receipt.FileDigest
    WHERE claim.CompletedFileName = N'$CompletedFileName'
)
    THROW 52560, 'Reset refuses a claim with a committed receipt.', 1;

DELETE dbo.KS4_ImportFileClaim
WHERE CompletedFileName = N'$CompletedFileName'
  AND ClaimStatus = N'claimed'
  AND ReadyPath = N'$readyPath'
  AND ClaimedPath = N'$claimedPath'
  AND ArchivePath = N'$archivePath';

IF @@ROWCOUNT <> 1
    THROW 52561, 'Reset could not delete exactly one isolated failed claim.', 1;

COMMIT TRANSACTION;
SELECT 1 AS DeletedClaimRows;
"@
if ([int]$deleteResult.DeletedClaimRows -ne 1) {
    throw 'Reset did not confirm deletion of exactly one isolated failed claim.'
}

$receipt = [ordered]@{
    SchemaVersion = 'phase5-1-failed-evidence-reset/v1'
    CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
    Machine = $env:COMPUTERNAME
    ServerName = [string]$databaseGuard.ServerName
    DatabaseName = [string]$databaseGuard.DatabaseName
    FailedRunId = $FailedRunId
    CompletedFileName = $CompletedFileName
    OriginalClaim = $claim
    QuarantinedPath = $quarantinePath
    QuarantinedLength = (Get-Item -LiteralPath $quarantinePath).Length
    QuarantinedSha256 = $retainedHash
    DeletedClaimRows = [int]$deleteResult.DeletedClaimRows
    Status = 'PASS'
}
$receipt | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resetReceiptPath -Encoding UTF8
Write-Host "Phase 5.1 failed evidence reset passed: $resetReceiptPath"
