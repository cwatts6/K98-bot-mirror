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
    [switch]$ConfirmWritersStopped,

    [switch]$ConfirmRecoverLegacyPostCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedMachine = 'MINI_AMD'
$expectedRoot = 'C:\discord_file_downloader\downloads_test_phase5_rehearsal'
$expectedReplacementHash = '95713E9CBDD1DFCB2D4080C2537F418D43CA0DA25F0D7D6631F4F7C97B89DC47'
$legacyPostCommitRunId = 'phase5_1_20260816T173604288Z'
$legacyPostCommitFileName = 'stats_4f3816925f51437fbaba8f5d49c40064.ready.csv'
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
if ($resolvedRoot -cne $expectedRoot) {
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
$resetIntentPath = Join-Path $quarantineRoot 'reset_intent.json'
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
if ($retainedItem.Length -ne 11 -or $retainedHash -cne $expectedReplacementHash) {
    throw 'Retained renamed file does not match the exact 11-byte replacement failure shape.'
}

function Write-JsonAtomically {
    param(
        [Parameter(Mandatory = $true)]$Value,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (Test-Path -LiteralPath $Destination) {
        throw "Refusing to replace existing evidence: $Destination"
    }
    $temporaryPath = "$Destination.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        $Value |
            ConvertTo-Json -Depth 12 |
            Set-Content -LiteralPath $temporaryPath -Encoding UTF8
        [IO.File]::Move($temporaryPath, $Destination)
    }
    finally {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-ResetSql {
    param([Parameter(Mandatory = $true)][string]$Query)

    $boundedQuery = "SET LOCK_TIMEOUT 30000;`r`n$Query"
    Invoke-Sqlcmd `
        -ServerInstance $ServerName `
        -Database $DatabaseName `
        -Query $boundedQuery `
        -QueryTimeout 60 `
        -AbortOnError `
        -TrustServerCertificate `
        -ErrorAction Stop
}

function Get-ReceiptPathCount {
    $result = Invoke-ResetSql -Query @"
SELECT COUNT_BIG(*) AS ReceiptPathCount
FROM dbo.KS4_ImportFileReceipt
WHERE SourcePath IN (N'$readyPath', N'$claimedPath')
   OR ArchivePath = N'$archivePath';
"@
    return [long]$result.ReceiptPathCount
}

function New-ResetReceipt {
    param(
        [Parameter(Mandatory = $true)]$DatabaseGuard,
        [Parameter(Mandatory = $true)]$OriginalClaim,
        [Parameter(Mandatory = $true)][string]$RecoveryMode,
        [Parameter(Mandatory = $true)][string]$EvidenceSource
    )

    return [ordered]@{
        SchemaVersion = 'phase5-1-failed-evidence-reset/v2'
        CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
        Machine = $env:COMPUTERNAME
        ServerName = [string]$DatabaseGuard.ServerName
        DatabaseName = [string]$DatabaseGuard.DatabaseName
        FailedRunId = $FailedRunId
        CompletedFileName = $CompletedFileName
        RecoveryMode = $RecoveryMode
        EvidenceSource = $EvidenceSource
        OriginalClaim = $OriginalClaim
        TranscriptPath = $transcriptPath
        TranscriptSha256 = (Get-FileHash -LiteralPath $transcriptPath -Algorithm SHA256).Hash
        QuarantinedPath = $quarantinePath
        QuarantinedLength = (Get-Item -LiteralPath $quarantinePath).Length
        QuarantinedSha256 = $retainedHash
        DeletedClaimRows = 1
        MatchingReceiptRows = 0
        Status = 'PASS'
    }
}

$databaseGuard = Invoke-ResetSql -Query @"
SELECT DB_NAME() AS DatabaseName,
       @@SERVERNAME AS ServerName,
       CASE WHEN DB_NAME() = N'ROK_TRACKER' THEN 0 ELSE 1 END AS IsIsolated;
"@
if ([int]$databaseGuard.IsIsolated -ne 1) {
    throw 'Database guard did not prove an isolated target.'
}

$claimRows = @(
    Invoke-ResetSql -Query @"
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
)

if ($claimRows.Count -eq 0) {
    if (-not $quarantineExists -or $renamedExists) {
        throw 'Post-commit recovery requires only the exact quarantined failure artifact.'
    }
    if ((Get-ReceiptPathCount) -ne 0) {
        throw 'Post-commit recovery found a matching committed receipt.'
    }

    if (Test-Path -LiteralPath $resetIntentPath -PathType Leaf) {
        $intent = Get-Content -LiteralPath $resetIntentPath -Raw | ConvertFrom-Json
        if (
            $intent.SchemaVersion -cne 'phase5-1-failed-evidence-reset-intent/v1' -or
            $intent.DatabaseName -cne $DatabaseName -or
            $intent.FailedRunId -cne $FailedRunId -or
            $intent.CompletedFileName -cne $CompletedFileName -or
            $intent.QuarantinedSha256 -cne $retainedHash
        ) {
            throw 'Reset intent does not match the requested post-commit recovery.'
        }
        $receipt = New-ResetReceipt `
            -DatabaseGuard $databaseGuard `
            -OriginalClaim $intent.OriginalClaim `
            -RecoveryMode 'PostCommitIntentRecovery' `
            -EvidenceSource $resetIntentPath
        Write-JsonAtomically -Value $receipt -Destination $resetReceiptPath
        Write-Host "Phase 5.1 post-commit intent recovery passed: $resetReceiptPath"
        return
    }

    if (-not $ConfirmRecoverLegacyPostCommit.IsPresent) {
        throw 'Claim deletion committed without a reset intent. Pass -ConfirmRecoverLegacyPostCommit only for the pinned legacy incident.'
    }
    if (
        $FailedRunId -cne $legacyPostCommitRunId -or
        $CompletedFileName -cne $legacyPostCommitFileName
    ) {
        throw 'Legacy post-commit recovery refuses every run except the pinned 2026-08-16 incident.'
    }

    $transcript = Get-Content -LiteralPath $transcriptPath -Raw
    if (
        $transcript -notmatch [regex]::Escape($CompletedFileName) -or
        $transcript -notmatch [regex]::Escape($expectedReplacementHash) -or
        $transcript -notmatch 'ClaimStatus\s+ReadyPath' -or
        $transcript -notmatch 'claimed\s+C:\\discord_file_downloader\\downloads_test_phase5_rehearsal\\Import_Ready'
    ) {
        throw 'Legacy post-commit recovery transcript markers do not match the pinned failed incident.'
    }

    $legacyClaimEvidence = [ordered]@{
        CompletedFileName = $CompletedFileName
        ClaimStatus = 'claimed'
        ReadyPath = $readyPath
        ClaimedPath = $claimedPath
        ArchivePath = $archivePath
        HasReceipt = 0
        RecoveryNote = 'Original row was deleted before the interrupted v1 reset could persist its receipt; exact state is reconstructed from the pinned transcript, paths, and quarantine digest.'
    }
    $receipt = New-ResetReceipt `
        -DatabaseGuard $databaseGuard `
        -OriginalClaim $legacyClaimEvidence `
        -RecoveryMode 'LegacyPostCommitRecovery' `
        -EvidenceSource $transcriptPath
    Write-JsonAtomically -Value $receipt -Destination $resetReceiptPath
    Write-Host "Phase 5.1 pinned legacy post-commit recovery passed: $resetReceiptPath"
    return
}

if ($claimRows.Count -ne 1) {
    throw 'Reset did not find exactly one requested failed claim.'
}
$claim = $claimRows[0]
if (
    $claim.CompletedFileName -cne $CompletedFileName -or
    $claim.ClaimStatus -cne 'claimed' -or
    [int]$claim.HasReceipt -ne 0 -or
    $claim.ReadyPath -cne $readyPath -or
    $claim.ClaimedPath -cne $claimedPath -or
    $claim.ArchivePath -cne $archivePath
) {
    throw 'Failed claim does not match the exact retained Phase 5.1 evidence shape.'
}

New-Item -ItemType Directory -Path $quarantineRoot -Force | Out-Null
if (-not (Test-Path -LiteralPath $resetIntentPath -PathType Leaf)) {
    $intent = [ordered]@{
        SchemaVersion = 'phase5-1-failed-evidence-reset-intent/v1'
        CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
        Machine = $env:COMPUTERNAME
        ServerName = [string]$databaseGuard.ServerName
        DatabaseName = [string]$databaseGuard.DatabaseName
        FailedRunId = $FailedRunId
        CompletedFileName = $CompletedFileName
        OriginalClaim = $claim
        TranscriptPath = $transcriptPath
        TranscriptSha256 = (Get-FileHash -LiteralPath $transcriptPath -Algorithm SHA256).Hash
        QuarantinedPath = $quarantinePath
        QuarantinedSha256 = $retainedHash
        Status = 'PENDING'
    }
    Write-JsonAtomically -Value $intent -Destination $resetIntentPath
}

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

$receipt = New-ResetReceipt `
    -DatabaseGuard $databaseGuard `
    -OriginalClaim $claim `
    -RecoveryMode 'Normal' `
    -EvidenceSource $resetIntentPath
Write-JsonAtomically -Value $receipt -Destination $resetReceiptPath
Write-Host "Phase 5.1 failed evidence reset passed: $resetReceiptPath"
