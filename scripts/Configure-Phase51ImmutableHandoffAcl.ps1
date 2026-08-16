[CmdletBinding()]
param(
    [ValidateSet(
        'C:\discord_file_downloader\downloads_test_phase5_rehearsal',
        'C:\discord_file_downloader\downloads'
    )]
    [string]$RootPath = 'C:\discord_file_downloader\downloads_test_phase5_rehearsal',

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BotIdentity,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$SqlIdentity,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$EvidenceDirectory,

    [switch]$ConfirmIsolatedRoot,
    [switch]$ConfirmProductionRoot,
    [switch]$ConfirmWritersStopped
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedMachine = 'MINI_AMD'
$isolatedRoot = 'C:\discord_file_downloader\downloads_test_phase5_rehearsal'
$productionRoot = 'C:\discord_file_downloader\downloads'
$resolvedRoot = [IO.Path]::GetFullPath($RootPath).TrimEnd('\')
$resolvedEvidence = [IO.Path]::GetFullPath($EvidenceDirectory).TrimEnd('\')

if ($env:COMPUTERNAME -ine $expectedMachine) {
    throw "Run locally on $expectedMachine. Current host: $env:COMPUTERNAME"
}
if ($resolvedRoot -ceq $isolatedRoot) {
    if (-not $ConfirmIsolatedRoot.IsPresent) {
        throw 'Pass -ConfirmIsolatedRoot only after confirming the pinned rehearsal root.'
    }
}
elseif ($resolvedRoot -ceq $productionRoot) {
    if (-not $ConfirmProductionRoot.IsPresent -or -not $ConfirmWritersStopped.IsPresent) {
        throw 'Production ACL configuration requires -ConfirmProductionRoot and -ConfirmWritersStopped.'
    }
}
else {
    throw "Immutable handoff ACL configuration refuses unreviewed root: $resolvedRoot"
}

$principal = [Security.Principal.WindowsPrincipal]::new(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Immutable handoff ACL configuration requires an elevated Administrator shell.'
}

function Resolve-IdentitySid {
    param([Parameter(Mandatory = $true)][string]$Identity)

    try {
        return ([Security.Principal.NTAccount]::new($Identity)).Translate(
            [Security.Principal.SecurityIdentifier]
        )
    }
    catch {
        throw "Could not resolve Windows identity '$Identity' to a SID: $($_.Exception.Message)"
    }
}

function Get-AclSnapshot {
    param([Parameter(Mandatory = $true)][string]$Path)

    $acl = Get-Acl -LiteralPath $Path
    $rules = @(
        $acl.GetAccessRules(
            $true,
            $true,
            [Security.Principal.SecurityIdentifier]
        ) | ForEach-Object {
            [ordered]@{
                IdentitySid = $_.IdentityReference.Value
                AccessControlType = $_.AccessControlType.ToString()
                FileSystemRights = $_.FileSystemRights.ToString()
                InheritanceFlags = $_.InheritanceFlags.ToString()
                PropagationFlags = $_.PropagationFlags.ToString()
                IsInherited = $_.IsInherited
            }
        }
    )

    return [ordered]@{
        Path = $Path
        Owner = $acl.Owner
        OwnerSid = (Resolve-IdentitySid -Identity $acl.Owner).Value
        AreAccessRulesProtected = $acl.AreAccessRulesProtected
        Sddl = $acl.GetSecurityDescriptorSddlForm(
            [Security.AccessControl.AccessControlSections]::All
        )
        Rules = $rules
        Icacls = @(& icacls $Path)
    }
}

function Add-AllowRule {
    param(
        [Parameter(Mandatory = $true)]
        [Security.AccessControl.DirectorySecurity]$Acl,

        [Parameter(Mandatory = $true)]
        [Security.Principal.SecurityIdentifier]$Sid,

        [Parameter(Mandatory = $true)]
        [Security.AccessControl.FileSystemRights]$Rights
    )

    $inheritance = (
        [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
        [Security.AccessControl.InheritanceFlags]::ObjectInherit
    )
    $rule = [Security.AccessControl.FileSystemAccessRule]::new(
        $Sid,
        $Rights,
        $inheritance,
        [Security.AccessControl.PropagationFlags]::None,
        [Security.AccessControl.AccessControlType]::Allow
    )
    [void]$Acl.AddAccessRule($rule)
}

function Set-ImmutableDirectoryAcl {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]
        [Security.AccessControl.FileSystemRights]$BotRights,
        [Parameter(Mandatory = $true)]
        [Security.Principal.SecurityIdentifier]$BotSid,
        [Parameter(Mandatory = $true)]
        [Security.Principal.SecurityIdentifier]$SqlSid
    )

    $systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    $administratorsSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true, $false)
    $acl.SetOwner($SqlSid)

    Add-AllowRule -Acl $acl -Sid $systemSid -Rights (
        [Security.AccessControl.FileSystemRights]::FullControl
    )
    if ($SqlSid.Value -cne $systemSid.Value) {
        Add-AllowRule -Acl $acl -Sid $SqlSid -Rights (
            [Security.AccessControl.FileSystemRights]::FullControl
        )
    }
    Add-AllowRule -Acl $acl -Sid $administratorsSid -Rights (
        [Security.AccessControl.FileSystemRights]::ReadAndExecute
    )
    Add-AllowRule -Acl $acl -Sid $BotSid -Rights $BotRights

    Set-Acl -LiteralPath $Path -AclObject $acl
}

$botSid = Resolve-IdentitySid -Identity $BotIdentity
$sqlSid = Resolve-IdentitySid -Identity $SqlIdentity
if ($botSid.Value -ceq $sqlSid.Value) {
    throw 'Bot and SQL identities must be different principals.'
}

$readyRoot = Join-Path $resolvedRoot 'Import_Ready'
$claimedRoot = Join-Path $resolvedRoot 'Import_Claimed'
$archiveRoot = Join-Path $resolvedRoot 'Import_Archive'
$paths = @($readyRoot, $claimedRoot, $archiveRoot)

foreach ($path in $paths) {
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        throw "Required immutable-handoff directory is missing: $path"
    }
}

foreach ($path in @($readyRoot, $claimedRoot)) {
    if (@(Get-ChildItem -LiteralPath $path -Force).Count -ne 0) {
        throw "ACL configuration requires an empty directory: $path"
    }
}

$driveRoots = @(
    $paths |
        ForEach-Object { [IO.Path]::GetPathRoot($_) } |
        Select-Object -Unique
)
if ($driveRoots.Count -ne 1) {
    throw 'Ready, Claimed and Archive must be on one volume.'
}
$driveLetter = $driveRoots[0].Substring(0, 1)
$volume = Get-Volume -DriveLetter $driveLetter
if ($volume.FileSystemType -cne 'NTFS') {
    throw "Immutable handoff requires NTFS; found $($volume.FileSystemType)."
}

New-Item -ItemType Directory -Path $resolvedEvidence -Force | Out-Null
$receiptPath = Join-Path $resolvedEvidence (
    'phase5_1_acl_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '.json'
)
if (Test-Path -LiteralPath $receiptPath) {
    throw "ACL receipt unexpectedly exists: $receiptPath"
}

$before = @($paths | ForEach-Object { Get-AclSnapshot -Path $_ })

Set-ImmutableDirectoryAcl -Path $readyRoot -BotRights ([Security.AccessControl.FileSystemRights]::Modify) -BotSid $botSid -SqlSid $sqlSid
Set-ImmutableDirectoryAcl -Path $claimedRoot -BotRights ([Security.AccessControl.FileSystemRights]::ReadAndExecute) -BotSid $botSid -SqlSid $sqlSid
Set-ImmutableDirectoryAcl -Path $archiveRoot -BotRights ([Security.AccessControl.FileSystemRights]::ReadAndExecute) -BotSid $botSid -SqlSid $sqlSid

$after = @($paths | ForEach-Object { Get-AclSnapshot -Path $_ })
foreach ($snapshot in $after) {
    if (-not [bool]$snapshot.AreAccessRulesProtected) {
        throw "Configured ACL still inherits broad parent permissions: $($snapshot.Path)"
    }
    if ([string]$snapshot.OwnerSid -cne $sqlSid.Value) {
        throw "Configured directory owner is not the SQL identity: $($snapshot.Path)"
    }

    $unexpectedBroadSid = @(
        $snapshot.Rules | Where-Object {
            $_.IdentitySid -in @(
                'S-1-1-0',
                'S-1-5-11',
                'S-1-5-32-545'
            )
        }
    )
    if ($unexpectedBroadSid.Count -ne 0) {
        throw "Configured ACL retained a broad mutable principal: $($snapshot.Path)"
    }
}

$receipt = [ordered]@{
    SchemaVersion = 'phase5-1-acl-configuration/v1'
    CapturedAtUtc = [DateTime]::UtcNow.ToString('o')
    Machine = $env:COMPUTERNAME
    RootPath = $resolvedRoot
    IsProductionRoot = $resolvedRoot -ceq $productionRoot
    BotIdentity = $BotIdentity
    BotSid = $botSid.Value
    SqlIdentity = $SqlIdentity
    SqlSid = $sqlSid.Value
    FileSystem = $volume.FileSystemType
    VolumeUniqueId = $volume.UniqueId
    Before = $before
    After = $after
    Status = 'PASS'
}
$receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
Write-Host "Phase 5.1 immutable-handoff ACL configuration passed: $receiptPath"
