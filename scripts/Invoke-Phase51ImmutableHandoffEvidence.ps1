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
    [string]$BotRepoRoot = 'C:\discord_file_downloader',

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$ExpectedSqlCommit,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$ExpectedBotCommit,

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
$resolvedRoot = [IO.Path]::GetFullPath($TestRoot).TrimEnd('\')
$readyRoot = Join-Path $resolvedRoot 'Import_Ready'
$claimedRoot = Join-Path $resolvedRoot 'Import_Claimed'
$archiveRoot = Join-Path $resolvedRoot 'Import_Archive'
$evidenceRoot = Join-Path $resolvedRoot 'evidence'
$runId = 'phase5_1_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$runRoot = Join-Path $evidenceRoot $runId
$receiptPath = Join-Path $runRoot 'receipt.json'
$failureReceiptPath = Join-Path $runRoot 'receipt.failed.json'
$transcriptPath = Join-Path $runRoot 'transcript.log'
$mutationAttempts = [System.Collections.Generic.List[object]]::new()
$currentIdentity = $null
$processOwner = $null
$process = $null
$sqlCommit = $null
$botCommit = $null
$completedFileName = $null
$claimResult = $null
$claimEvidenceRows = @()
$claimedFileAcl = $null
$ledger = $null
$ledgerEvidenceRows = @()
$updateAll2DurationMs = $null
$archiveDigestDurationMs = $null

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

function Convert-EvidenceSqlRows {
    param([AllowNull()][object[]]$Rows)

    foreach ($row in @($Rows)) {
        if ($null -eq $row) {
            continue
        }

        $dataRow = if ($row -is [System.Data.DataRow]) {
            $row
        }
        elseif ($row.PSObject.BaseObject -is [System.Data.DataRow]) {
            $row.PSObject.BaseObject
        }
        else {
            throw "Evidence SQL returned an unexpected row type: $($row.GetType().FullName)"
        }

        $evidenceRow = [ordered]@{}
        foreach ($column in $dataRow.Table.Columns) {
            $value = $dataRow[$column]
            if ($value -is [DBNull]) {
                $value = $null
            }
            elseif (
                $null -ne $value -and
                $value -isnot [string] -and
                $value -isnot [ValueType]
            ) {
                $value = [string]$value
            }
            $evidenceRow[[string]$column.ColumnName] = $value
        }
        [pscustomobject]$evidenceRow
    }
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
        $exception = $_.Exception
        $accessDenied = $false
        while ($null -ne $exception) {
            if (
                $exception -is [UnauthorizedAccessException] -or
                $exception.HResult -eq -2147024891 -or
                (
                    $exception.PSObject.Properties.Name -contains 'NativeErrorCode' -and
                    [int]$exception.NativeErrorCode -eq 5
                )
            ) {
                $accessDenied = $true
                break
            }
            $exception = $exception.InnerException
        }

        return [pscustomobject]@{
            Name = $Name
            Denied = $accessDenied
            ErrorType = $_.Exception.GetType().FullName
            ErrorText = $_.Exception.Message
        }
    }
}

function Invoke-UpdateAll2Evidence {
    param(
        [Parameter(Mandatory = $true)]
        [ValidatePattern('^stats_[0-9a-f]{32}\.ready\.csv$')]
        [string]$CompletedFileName
    )

    $connectionBuilder = [System.Data.SqlClient.SqlConnectionStringBuilder]::new()
    $connectionBuilder['Data Source'] = $ServerName
    $connectionBuilder['Initial Catalog'] = $DatabaseName
    $connectionBuilder['Integrated Security'] = $true
    $connectionBuilder['TrustServerCertificate'] = $true
    $connectionBuilder['Connect Timeout'] = 15
    $connectionBuilder['Application Name'] = 'K98 Phase 5.1 Immutable Handoff Evidence'

    $connection = [System.Data.SqlClient.SqlConnection]::new(
        $connectionBuilder.ToString()
    )
    $command = $connection.CreateCommand()
    $command.CommandText = @'
EXEC dbo.UPDATE_ALL2
    @param1 = NULL,
    @param2 = NULL,
    @CompletedFileName = @CompletedFileName;
'@
    $command.CommandTimeout = 900
    $completedFileParameter = $command.Parameters.Add(
        '@CompletedFileName',
        [System.Data.SqlDbType]::NVarChar,
        260
    )
    $completedFileParameter.Value = $CompletedFileName

    try {
        $connection.Open()
        [void]$command.ExecuteNonQuery()
    }
    finally {
        $command.Dispose()
        $connection.Dispose()
    }
}

function Get-ArchiveDigestEvidence {
    param(
        [Parameter(Mandatory = $true)]
        [ValidatePattern('\\Import_Archive\\stats_[0-9a-f]{32}\.ready\.csv$')]
        [string]$ApprovedPath
    )

    $connectionBuilder = [System.Data.SqlClient.SqlConnectionStringBuilder]::new()
    $connectionBuilder['Data Source'] = $ServerName
    $connectionBuilder['Initial Catalog'] = $DatabaseName
    $connectionBuilder['Integrated Security'] = $true
    $connectionBuilder['TrustServerCertificate'] = $true
    $connectionBuilder['Connect Timeout'] = 15
    $connectionBuilder['Application Name'] = 'K98 Phase 5.1 Archive Digest Evidence'

    $connection = [System.Data.SqlClient.SqlConnection]::new(
        $connectionBuilder.ToString()
    )
    $command = $connection.CreateCommand()
    $command.CommandText = @'
DECLARE @Digest binary(32);
EXEC dbo.HASH_KS4_IMPORT_ARCHIVE_FILE
    @ApprovedPath = @ApprovedPath,
    @FileDigest = @Digest OUTPUT;
SELECT CONVERT(varchar(64), @Digest, 2);
'@
    $command.CommandTimeout = 120
    $approvedPathParameter = $command.Parameters.Add(
        '@ApprovedPath',
        [System.Data.SqlDbType]::NVarChar,
        4000
    )
    $approvedPathParameter.Value = $ApprovedPath

    try {
        $connection.Open()
        $digest = $command.ExecuteScalar()
        if ($null -eq $digest -or $digest -is [DBNull]) {
            throw 'Archive digest query did not return a digest.'
        }
        return [string]$digest
    }
    finally {
        $command.Dispose()
        $connection.Dispose()
    }
}

function Assert-TrackedWorktreeClean {
    param(
        [Parameter(Mandatory = $true)][string]$RepositoryRoot,
        [Parameter(Mandatory = $true)][string]$RepositoryLabel
    )

    & git -C $RepositoryRoot diff --quiet --exit-code --
    if ($LASTEXITCODE -ne 0) {
        throw "$RepositoryLabel repository has unstaged tracked changes."
    }

    & git -C $RepositoryRoot diff --cached --quiet --exit-code --
    if ($LASTEXITCODE -ne 0) {
        throw "$RepositoryLabel repository has staged but uncommitted changes."
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
    if ([string]$process.CommandLine -notmatch '(?i)\\DL_bot\.py(?:\s|$|\")') {
        throw "Process $BotProcessId is not a live DL_bot.py process."
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
    $serviceEvidenceRows = @(Convert-EvidenceSqlRows -Rows @($serviceRows))
    $xpIdentityRows = Invoke-EvidenceSql -Query "EXEC master.dbo.xp_cmdshell 'whoami';"
    $xpIdentityEvidenceRows = @(Convert-EvidenceSqlRows -Rows @($xpIdentityRows))

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
    if ($sqlCommit -cne $ExpectedSqlCommit) {
        throw "SQL repository is not frozen at $ExpectedSqlCommit; found $sqlCommit."
    }
    Assert-TrackedWorktreeClean -RepositoryRoot $SqlRepoRoot -RepositoryLabel 'SQL'
    $botCommit = (& git -C $BotRepoRoot rev-parse HEAD).Trim()
    if ($botCommit -cne $ExpectedBotCommit) {
        throw "Bot repository is not frozen at $ExpectedBotCommit; found $botCommit."
    }
    Assert-TrackedWorktreeClean -RepositoryRoot $BotRepoRoot -RepositoryLabel 'Bot'

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
       @Archive AS ArchivePath,
       claim.AclHardenedAtUtc,
       claim.AclOwnerIdentity
FROM dbo.KS4_ImportFileClaim AS claim
WHERE claim.CompletedFileName = N'$completedFileName';
"@
    $claimEvidenceRows = @(Convert-EvidenceSqlRows -Rows @($claimResult))
    if (-not (Test-Path -LiteralPath $claimedPath -PathType Leaf)) {
        throw 'SQL-positive claim did not produce the exact Claimed identity.'
    }

    $claimedAcl = Get-Acl -LiteralPath $claimedPath
    $claimedFileAcl = [ordered]@{
        Owner = $claimedAcl.Owner
        Sddl = $claimedAcl.GetSecurityDescriptorSddlForm(
            [Security.AccessControl.AccessControlSections]::All
        )
        Icacls = @(& icacls $claimedPath)
    }
    if ([string]::IsNullOrWhiteSpace([string]$claimResult.AclOwnerIdentity)) {
        throw 'SQL claim did not persist the ACL owner identity.'
    }
    if ($claimedAcl.Owner -ine [string]$claimResult.AclOwnerIdentity) {
        throw "Claimed file owner $($claimedAcl.Owner) does not match SQL evidence $($claimResult.AclOwnerIdentity)."
    }

    $replacementPath = Join-Path $readyRoot ".replacement_$token.tmp"
    $mutationOperations = @(
        [pscustomobject]@{ Name = 'overwrite'; Operation = {
            [IO.File]::WriteAllText($claimedPath, 'overwrite')
        } }
        [pscustomobject]@{ Name = 'replacement'; Operation = {
            [IO.File]::WriteAllText($replacementPath, 'replacement')
            Move-Item -LiteralPath $replacementPath -Destination $claimedPath -Force -ErrorAction Stop
        } }
        [pscustomobject]@{ Name = 'rename'; Operation = {
            [IO.File]::Move($claimedPath, "$claimedPath.renamed")
        } }
        [pscustomobject]@{ Name = 'delete'; Operation = {
            [IO.File]::Delete($claimedPath)
            if (Test-Path -LiteralPath $claimedPath) {
                throw [InvalidOperationException]::new(
                    'Delete returned without access denial but the claimed file remains.'
                )
            }
        } }
        [pscustomobject]@{ Name = 'in_place_modify'; Operation = {
            $handle = [IO.File]::Open($claimedPath, [IO.FileMode]::Open, [IO.FileAccess]::Write)
            $handle.Dispose()
        } }
    )

    foreach ($mutationOperation in $mutationOperations) {
        $attempt = Invoke-DeniedMutation `
            -Name $mutationOperation.Name `
            -Operation $mutationOperation.Operation
        $mutationAttempts.Add($attempt)
        if (-not $attempt.Denied) {
            break
        }
    }
    Remove-Item -LiteralPath $replacementPath -ErrorAction SilentlyContinue
    if (@($mutationAttempts | Where-Object { -not $_.Denied }).Count -ne 0) {
        throw 'The real bot token retained a mutation path after SQL claim.'
    }

    Write-Host 'Phase 5.1 evidence: all five bot-token mutation attempts were denied.'
    Write-Host 'Phase 5.1 evidence: starting UPDATE_ALL2 without materializing result rows.'
    $updateAll2Stopwatch = [Diagnostics.Stopwatch]::StartNew()
    try {
        Invoke-UpdateAll2Evidence -CompletedFileName $completedFileName
    }
    finally {
        $updateAll2Stopwatch.Stop()
        $updateAll2DurationMs = $updateAll2Stopwatch.ElapsedMilliseconds
    }
    Write-Host "Phase 5.1 evidence: UPDATE_ALL2 completed in $updateAll2DurationMs ms."

    Write-Host 'Phase 5.1 evidence: validating the terminal SQL ledger.'
    $ledger = Invoke-EvidenceSql -Query @"
SELECT claim.CompletedFileName,
       claim.ClaimStatus,
       CONVERT(varchar(64), claim.FileDigest, 2) AS ClaimDigest,
       claim.ReadyPath,
       claim.ClaimedPath,
       claim.ArchivePath,
       claim.ClaimRequestedAtUtc,
       claim.ClaimedAtUtc,
       claim.AclHardenedAtUtc,
       claim.AclOwnerIdentity,
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
    $ledgerEvidenceRows = @(Convert-EvidenceSqlRows -Rows @($ledger))
    if ($ledger.ClaimStatus -cne 'archived' -or $ledger.ArchiveStatus -cne 'archived') {
        throw 'SQL did not reach the receipt-backed archived terminal state.'
    }

    Write-Host 'Phase 5.1 evidence: validating the archived file digest with a bounded command.'
    $archiveDigestStopwatch = [Diagnostics.Stopwatch]::StartNew()
    try {
        $archiveDigest = Get-ArchiveDigestEvidence -ApprovedPath $archivePath
    }
    finally {
        $archiveDigestStopwatch.Stop()
        $archiveDigestDurationMs = $archiveDigestStopwatch.ElapsedMilliseconds
    }
    Write-Host "Phase 5.1 evidence: archive digest completed in $archiveDigestDurationMs ms."
    if ($readyDigest -ine $ledger.ClaimDigest -or $ledger.ClaimDigest -ine $archiveDigest) {
        throw 'Ready, claim and archive SHA-256 digests do not match.'
    }

    Write-Host 'Phase 5.1 evidence: writing the normalized JSON receipt.'
    $receipt = [ordered]@{
        EvidenceVersion = 2
        RunId = $runId
        CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
        Machine = $env:COMPUTERNAME
        ServerName = [string]$databaseGuard.ServerName
        DatabaseName = [string]$databaseGuard.DatabaseName
        BotCommit = $botCommit
        SqlCommit = $sqlCommit
        ExpectedBotCommit = $ExpectedBotCommit
        ExpectedSqlCommit = $ExpectedSqlCommit
        CurrentBotIdentity = $currentIdentity
        BotProcessId = $BotProcessId
        BotProcessOwner = $processOwner
        BotCommandLine = [string]$process.CommandLine
        CurrentToken = @($currentToken | ForEach-Object { [string]$_ })
        SqlServices = $serviceEvidenceRows
        XpCmdShellIdentity = $xpIdentityEvidenceRows
        Paths = @($roots | ForEach-Object { [string]$_ })
        DriveLetter = $driveLetter
        FileSystem = [string]$volume.FileSystemType
        VolumeUniqueId = [string]$volume.UniqueId
        VolumeSerialNumber = [string]$logicalDisk.VolumeSerialNumber
        AclEvidence = $aclEvidence
        CompletedFileName = $completedFileName
        ReadyDigest = $readyDigest
        ClaimResult = $claimEvidenceRows
        ClaimedFileAcl = $claimedFileAcl
        MutationAttempts = @($mutationAttempts)
        UpdateAll2DurationMs = $updateAll2DurationMs
        ArchiveDigestDurationMs = $archiveDigestDurationMs
        Ledger = $ledgerEvidenceRows
        ArchiveDigest = $archiveDigest
        StableFindingIds = @(
            'csf_1a1c440452b02cdb787fa7c3',
            'csf_3cb54318733d3a216dd91e9b'
        )
        Status = 'PASS'
    }
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
    Write-Host "Phase 5.1 immutable handoff evidence passed: $receiptPath"
}
catch {
    $failureReceipt = [ordered]@{
        EvidenceVersion = 2
        RunId = $runId
        CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
        Machine = $env:COMPUTERNAME
        DatabaseName = $DatabaseName
        BotCommit = $botCommit
        SqlCommit = $sqlCommit
        ExpectedBotCommit = $ExpectedBotCommit
        ExpectedSqlCommit = $ExpectedSqlCommit
        CurrentBotIdentity = $currentIdentity
        BotProcessOwner = $processOwner
        CompletedFileName = $completedFileName
        ClaimResult = $claimEvidenceRows
        ClaimedFileAcl = $claimedFileAcl
        MutationAttempts = @($mutationAttempts)
        UpdateAll2DurationMs = $updateAll2DurationMs
        ArchiveDigestDurationMs = $archiveDigestDurationMs
        ErrorType = $_.Exception.GetType().FullName
        ErrorText = $_.Exception.Message
        Status = 'FAIL'
    }
    $failureReceipt |
        ConvertTo-Json -Depth 12 |
        Set-Content -LiteralPath $failureReceiptPath -Encoding UTF8
    throw
}
finally {
    Stop-Transcript | Out-Null
}
