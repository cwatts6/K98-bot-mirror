[CmdletBinding()]
param(
    [ValidateSet('localhost', '.', '(local)')]
    [string]$ServerName = 'localhost',

    [ValidateSet('ROK_TRACKER_BACKUP_TEST_KS4_PHASE3_REHEARSAL')]
    [string]$DatabaseName = 'ROK_TRACKER_BACKUP_TEST_KS4_PHASE3_REHEARSAL',

    [ValidateSet('C:\discord_file_downloader\downloads_test_phase5_rehearsal')]
    [string]$TestRoot = 'C:\discord_file_downloader\downloads_test_phase5_rehearsal',

    [ValidateSet('C:\K98-bot-SQL-Server')]
    [string]$SqlRepoRoot = 'C:\K98-bot-SQL-Server',

    [ValidateSet(
        'C:\discord_file_downloader',
        'C:\K98-bot-SQL-Server\reports\phase51-bot-worktree'
    )]
    [string]$BotRepoRoot = 'C:\K98-bot-SQL-Server\reports\phase51-bot-worktree',

    [Parameter(Mandatory = $true)]
    [int]$BotProcessId,

    [Parameter(Mandatory = $true)]
    [switch]$ConfirmIsolatedTarget,

    [Parameter(Mandatory = $true)]
    [switch]$ConfirmCurrentTokenIsBot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedMachine = 'MINI_AMD'
$expectedSqlCommit = '2e0f228f399bcc7b8bd3d6a758b059466c0474ac'
$resolvedRoot = [IO.Path]::GetFullPath($TestRoot).TrimEnd('\')
$readyRoot = Join-Path $resolvedRoot 'Import_Ready'
$claimedRoot = Join-Path $resolvedRoot 'Import_Claimed'
$archiveRoot = Join-Path $resolvedRoot 'Import_Archive'
$evidenceRoot = Join-Path $resolvedRoot 'evidence'
$runId = 'phase5_1_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$runRoot = Join-Path $evidenceRoot $runId
$receiptPath = Join-Path $runRoot 'receipt.json'
$transcriptPath = Join-Path $runRoot 'transcript.log'

if (-not $ConfirmIsolatedTarget.IsPresent) {
    throw 'Pass -ConfirmIsolatedTarget only after confirming the pinned isolated database.'
}
if (-not $ConfirmCurrentTokenIsBot.IsPresent) {
    throw 'Pass -ConfirmCurrentTokenIsBot only when this shell uses the real bot token.'
}
if ($env:COMPUTERNAME -ine $expectedMachine) {
    throw "Run locally on $expectedMachine. Current host: $env:COMPUTERNAME"
}
if ($DatabaseName -ceq 'ROK_TRACKER') {
    throw 'Phase 5.1 evidence refuses the production database.'
}
if ($resolvedRoot -cne 'C:\discord_file_downloader\downloads_test_phase5_rehearsal') {
    throw 'Phase 5.1 evidence refuses an unreviewed filesystem root.'
}

foreach ($directory in @($readyRoot, $claimedRoot, $archiveRoot, $evidenceRoot)) {
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        throw "Required isolated directory is missing: $directory"
    }
}
if (Test-Path -LiteralPath $runRoot) {
    throw "Evidence directory already exists: $runRoot"
}
New-Item -ItemType Directory -Path $runRoot | Out-Null
Start-Transcript -LiteralPath $transcriptPath | Out-Null

function Invoke-EvidenceSql {
    param([Parameter(Mandatory = $true)][string]$Query)

    Invoke-Sqlcmd `
        -ServerInstance $ServerName `
        -Database $DatabaseName `
        -Query $Query `
        -AbortOnError `
        -TrustServerCertificate `
        -ErrorAction Stop
}

function Invoke-DeniedMutation {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Operation
    )

    try {
        & $Operation
        return [pscustomobject]@{
            Name = $Name
            Denied = $false
            ErrorType = $null
            ErrorText = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Name = $Name
            Denied = $true
            ErrorType = $_.Exception.GetType().FullName
            ErrorText = $_.Exception.Message
        }
    }
}

try {
    $databaseGuard = Invoke-EvidenceSql -Query @"
SELECT DB_NAME() AS DatabaseName,
       @@SERVERNAME AS ServerName,
       CASE WHEN DB_NAME() = N'ROK_TRACKER' THEN 0 ELSE 1 END AS IsIsolated;
"@
    if ([int]$databaseGuard.IsIsolated -ne 1) {
        throw 'Database guard did not prove an isolated target.'
    }

    $currentIdentity = (& whoami).Trim()
    $currentToken = @(& whoami /all)
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $BotProcessId"
    if ($null -eq $process) {
        throw "Bot process $BotProcessId was not found."
    }
    $ownerResult = Invoke-CimMethod -InputObject $process -MethodName GetOwner
    $processOwner = "$($ownerResult.Domain)\$($ownerResult.User)"
    if ($processOwner -ine $currentIdentity) {
        throw "Current identity $currentIdentity does not match bot process owner $processOwner."
    }

    $serviceRows = Invoke-EvidenceSql -Query @"
SELECT servicename, service_account, status_desc
FROM sys.dm_server_services
WHERE servicename LIKE N'SQL Server (%';
"@
    $xpIdentityRows = Invoke-EvidenceSql -Query "EXEC master.dbo.xp_cmdshell 'whoami';"

    $roots = @($readyRoot, $claimedRoot, $archiveRoot)
    $rootDrives = @($roots | ForEach-Object { [IO.Path]::GetPathRoot($_) } | Select-Object -Unique)
    if ($rootDrives.Count -ne 1) {
        throw 'Ready, Claimed and Archive are not on one volume.'
    }
    $driveLetter = $rootDrives[0].Substring(0, 1)
    $volume = Get-Volume -DriveLetter $driveLetter
    if ($volume.FileSystemType -cne 'NTFS') {
        throw "Immutable handoff requires NTFS; found $($volume.FileSystemType)."
    }
    $logicalDisk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID = '$driveLetter`:'"

    $aclEvidence = [ordered]@{}
    foreach ($path in $roots) {
        $aclEvidence[$path] = @(& icacls $path)
    }

    $sqlCommit = (& git -C $SqlRepoRoot rev-parse HEAD).Trim()
    if ($sqlCommit -cne $expectedSqlCommit) {
        throw "SQL repository is not frozen at $expectedSqlCommit; found $sqlCommit."
    }
    $botCommit = (& git -C $BotRepoRoot rev-parse HEAD).Trim()

    $token = [Guid]::NewGuid().ToString('N')
    $completedFileName = "stats_$token.ready.csv"
    $temporaryPath = Join-Path $readyRoot ".stats_$token.tmp"
    $readyPath = Join-Path $readyRoot $completedFileName
    $claimedPath = Join-Path $claimedRoot $completedFileName
    $archivePath = Join-Path $archiveRoot $completedFileName
    foreach ($path in @($temporaryPath, $readyPath, $claimedPath, $archivePath)) {
        if (Test-Path -LiteralPath $path) {
            throw "Generated immutable identity unexpectedly exists: $path"
        }
    }

    $fixturePath = Join-Path $SqlRepoRoot (
        'performance_remediation\kingdomscandata4\phase5\fixtures\valid_minimal.csv'
    )
    $fixtureText = Get-Content -Raw -LiteralPath $fixturePath
    $fixtureText = $fixtureText.Replace('Phase Five Minimal', "Phase Five $($token.Substring(0, 8))")
    $utf8Bom = [Text.UTF8Encoding]::new($true)
    $stream = [IO.FileStream]::new(
        $temporaryPath,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write,
        [IO.FileShare]::None
    )
    try {
        $bytes = $utf8Bom.GetBytes($fixtureText)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }
    [IO.File]::Move($temporaryPath, $readyPath)
    if (-not (Test-Path -LiteralPath $readyPath -PathType Leaf)) {
        throw 'Bot-positive atomic publication did not produce the Ready file.'
    }
    $readyDigest = (Get-FileHash -LiteralPath $readyPath -Algorithm SHA256).Hash

    $claimResult = Invoke-EvidenceSql -Query @"
DECLARE @Digest binary(32), @Claimed nvarchar(4000), @Archive nvarchar(4000);
EXEC dbo.CLAIM_KS4_IMPORT_FILE
    @CompletedFileName = N'$completedFileName',
    @FileDigest = @Digest OUTPUT,
    @ClaimedPath = @Claimed OUTPUT,
    @ArchivePath = @Archive OUTPUT;
SELECT CONVERT(varchar(64), @Digest, 2) AS ClaimDigest,
       @Claimed AS ClaimedPath,
       @Archive AS ArchivePath;
"@
    if (-not (Test-Path -LiteralPath $claimedPath -PathType Leaf)) {
        throw 'SQL-positive claim did not produce the exact Claimed identity.'
    }

    $replacementPath = Join-Path $readyRoot ".replacement_$token.tmp"
    $mutationAttempts = @(
        Invoke-DeniedMutation -Name 'overwrite' -Operation {
            [IO.File]::WriteAllText($claimedPath, 'overwrite')
        }
        Invoke-DeniedMutation -Name 'replacement' -Operation {
            [IO.File]::WriteAllText($replacementPath, 'replacement')
            Move-Item -LiteralPath $replacementPath -Destination $claimedPath -Force -ErrorAction Stop
        }
        Invoke-DeniedMutation -Name 'rename' -Operation {
            [IO.File]::Move($claimedPath, "$claimedPath.renamed")
        }
        Invoke-DeniedMutation -Name 'delete' -Operation {
            [IO.File]::Delete($claimedPath)
            if (Test-Path -LiteralPath $claimedPath) {
                throw [UnauthorizedAccessException]::new('Delete did not remove the claimed file.')
            }
        }
        Invoke-DeniedMutation -Name 'in_place_modify' -Operation {
            $handle = [IO.File]::Open($claimedPath, [IO.FileMode]::Open, [IO.FileAccess]::Write)
            $handle.Dispose()
        }
    )
    Remove-Item -LiteralPath $replacementPath -ErrorAction SilentlyContinue
    if (@($mutationAttempts | Where-Object { -not $_.Denied }).Count -ne 0) {
        throw 'The real bot token retained a mutation path after SQL claim.'
    }

    Invoke-EvidenceSql -Query @"
EXEC dbo.UPDATE_ALL2
    @param1 = NULL,
    @param2 = NULL,
    @CompletedFileName = N'$completedFileName';
"@ | Out-Null

    $ledger = Invoke-EvidenceSql -Query @"
SELECT claim.CompletedFileName,
       claim.ClaimStatus,
       CONVERT(varchar(64), claim.FileDigest, 2) AS ClaimDigest,
       claim.ReadyPath,
       claim.ClaimedPath,
       claim.ArchivePath,
       claim.ClaimRequestedAtUtc,
       claim.ClaimedAtUtc,
       claim.ImportCommittedAtUtc,
       claim.ArchivedAtUtc,
       receipt.ScanOrder,
       receipt.[RowCount],
       receipt.ArchiveStatus,
       receipt.DatabaseCommittedAtUtc
FROM dbo.KS4_ImportFileClaim AS claim
LEFT JOIN dbo.KS4_ImportFileReceipt AS receipt
  ON receipt.FileDigest = claim.FileDigest
WHERE claim.CompletedFileName = N'$completedFileName';
"@
    if ($ledger.ClaimStatus -cne 'archived' -or $ledger.ArchiveStatus -cne 'archived') {
        throw 'SQL did not reach the receipt-backed archived terminal state.'
    }

    $archiveDigestRow = Invoke-EvidenceSql -Query @"
DECLARE @Digest binary(32);
EXEC dbo.HASH_KS4_IMPORT_ARCHIVE_FILE
    @ApprovedPath = N'$archivePath',
    @FileDigest = @Digest OUTPUT;
SELECT CONVERT(varchar(64), @Digest, 2) AS ArchiveDigest;
"@
    if ($readyDigest -ine $ledger.ClaimDigest -or $ledger.ClaimDigest -ine $archiveDigestRow.ArchiveDigest) {
        throw 'Ready, claim and archive SHA-256 digests do not match.'
    }

    $receipt = [ordered]@{
        EvidenceVersion = 1
        RunId = $runId
        CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
        Machine = $env:COMPUTERNAME
        ServerName = [string]$databaseGuard.ServerName
        DatabaseName = [string]$databaseGuard.DatabaseName
        BotCommit = $botCommit
        SqlCommit = $sqlCommit
        CurrentBotIdentity = $currentIdentity
        BotProcessId = $BotProcessId
        BotProcessOwner = $processOwner
        BotCommandLine = $process.CommandLine
        CurrentToken = $currentToken
        SqlServices = @($serviceRows)
        XpCmdShellIdentity = @($xpIdentityRows)
        Paths = $roots
        DriveLetter = $driveLetter
        FileSystem = $volume.FileSystemType
        VolumeUniqueId = $volume.UniqueId
        VolumeSerialNumber = $logicalDisk.VolumeSerialNumber
        AclEvidence = $aclEvidence
        CompletedFileName = $completedFileName
        ReadyDigest = $readyDigest
        ClaimResult = $claimResult
        MutationAttempts = $mutationAttempts
        Ledger = $ledger
        ArchiveDigest = [string]$archiveDigestRow.ArchiveDigest
        StableFindingIds = @(
            'csf_1a1c440452b02cdb787fa7c3',
            'csf_3cb54318733d3a216dd91e9b'
        )
        Status = 'PASS'
    }
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    Write-Host "Phase 5.1 immutable handoff evidence passed: $receiptPath"
}
finally {
    Stop-Transcript | Out-Null
}
