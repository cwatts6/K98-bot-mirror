[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [Alias("BranchName")]
  [ValidateNotNullOrEmpty()]
  [string]$SourceBranch,

  [Parameter(Mandatory = $true)]
  [ValidateNotNullOrEmpty()]
  [string]$ProductionBranch,

  [string]$PythonExe,

  [switch]$AllowArchiveChanges
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Native {
  param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,

    [Parameter()]
    [string[]]$Arguments = @()
  )

  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
  }
}

function Get-RequiredRemoteUrl {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteName
  )

  $url = git remote get-url $RemoteName 2>$null
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($url)) {
    throw "Required git remote '$RemoteName' is not configured."
  }
  return $url.Trim()
}

function Assert-RemoteRepositoryName {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteName,

    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedOwner,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedRepositoryName
  )

  # Validate that the remote points to exactly github.com (anchored to start of URL)
  if ($RemoteUrl -notmatch "^(https?://github\.com[:/]|git@github\.com:)") {
    throw "Remote '$RemoteName' must point to github.com. Current URL: $RemoteUrl"
  }

  # Extract the owner/repo path segment that follows github.com
  $pathMatch = [regex]::Match($RemoteUrl, "(?:github\.com[:/])(.+)")
  if (-not $pathMatch.Success) {
    throw "Remote '$RemoteName' URL could not be parsed to extract owner and repository name. URL: $RemoteUrl"
  }

  $ownerRepo = $pathMatch.Groups[1].Value.TrimEnd("/")
  if ($ownerRepo.EndsWith(".git", [System.StringComparison]::OrdinalIgnoreCase)) {
    $ownerRepo = $ownerRepo.Substring(0, $ownerRepo.Length - 4)
  }

  $parts = $ownerRepo -split "[/\\]"
  if ($parts.Count -lt 2 -or [string]::IsNullOrEmpty($parts[0]) -or [string]::IsNullOrEmpty($parts[1])) {
    throw "Remote '$RemoteName' URL could not be parsed to extract owner and repository name. URL: $RemoteUrl"
  }

  $actualOwner = $parts[0]
  $actualRepo = $parts[1]

  if ($actualOwner -ne $ExpectedOwner -or $actualRepo -ne $ExpectedRepositoryName) {
    throw "Remote '$RemoteName' must point to '$ExpectedOwner/$ExpectedRepositoryName'. Current URL: $RemoteUrl"
  }
}

function Assert-GitRefExists {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RefName,

    [Parameter(Mandatory = $true)]
    [string]$ErrorMessage
  )

  git rev-parse --verify --quiet "$RefName^{commit}" *> $null
  if ($LASTEXITCODE -ne 0) {
    throw $ErrorMessage
  }
}

function Assert-CleanWorkingTree {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Context
  )

  $dirty = git status --porcelain
  if ($LASTEXITCODE -ne 0) {
    throw "Could not read git status while checking $Context."
  }
  if ($dirty) {
    throw "Working tree is not clean during $Context. Review, commit or stash changes, then rerun promotion."
  }
}

function Resolve-PythonExecutable {
  param(
    [string]$RequestedPythonExe,
    [string]$RepoRoot
  )

  $candidates = @()
  if (-not [string]::IsNullOrWhiteSpace($RequestedPythonExe)) {
    $candidates += $RequestedPythonExe
  }
  $candidates += @(
    (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
    (Join-Path $RepoRoot "venv\Scripts\python.exe")
  )

  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return $python.Source
  }

  throw "Could not find Python. Pass -PythonExe or create .venv/venv."
}

function Invoke-ValidationAndEnsureClean {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ResolvedPython,

    [Parameter(Mandatory = $true)]
    [string[]]$PromotedFiles
  )

  $preCommitFiles = @(
    $PromotedFiles |
      Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
      Where-Object { Test-Path -LiteralPath $_ }
  )

  if ($preCommitFiles.Count -gt 0) {
    Write-Host "Running pre-commit validation against promoted files..."
    Write-Host ("Promoted file count: {0}" -f $preCommitFiles.Count)
    Invoke-Native -FilePath $ResolvedPython -Arguments (@("-m", "pre_commit", "run", "--files") + $preCommitFiles)
  }
  else {
    Write-Host "Skipping pre-commit validation because no promoted files exist after patch application."
  }
  Assert-CleanWorkingTree -Context "after pre-commit validation"

  Write-Host "Running pytest validation against tests..."
  Invoke-Native -FilePath $ResolvedPython -Arguments @("-m", "pytest", "-q", "tests")
  Assert-CleanWorkingTree -Context "after pytest validation"

  Write-Host "Running whitespace validation..."
  Invoke-Native -FilePath "git" -Arguments @("diff", "--check")
  Assert-CleanWorkingTree -Context "after git diff --check"
}

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $scriptDir
$repoRoot = (Resolve-Path -LiteralPath $repoRoot).Path
$patchPath = Join-Path ([System.IO.Path]::GetTempPath()) ("k98-production-promotion-{0}.patch" -f ([System.Guid]::NewGuid().ToString("N")))

Set-Location -LiteralPath $repoRoot

try {
  Write-Host "Repository: $repoRoot"
  Write-Host "Source branch: $SourceBranch"
  Write-Host "Production branch: $ProductionBranch"

  Write-Host "Checking working tree..."
  Assert-CleanWorkingTree -Context "before production promotion"

  Write-Host "Checking git remotes..."
  $originUrl = Get-RequiredRemoteUrl -RemoteName "origin"
  $productionUrl = Get-RequiredRemoteUrl -RemoteName "production"
  Assert-RemoteRepositoryName -RemoteName "origin" -RemoteUrl $originUrl -ExpectedOwner "cwatts6" -ExpectedRepositoryName "K98-bot-mirror"
  Assert-RemoteRepositoryName -RemoteName "production" -RemoteUrl $productionUrl -ExpectedOwner "cwatts6" -ExpectedRepositoryName "K98-bot"
  Write-Host "origin:     $originUrl"
  Write-Host "production: $productionUrl"

  Write-Host "Fetching mirror and production remotes..."
  Invoke-Native -FilePath "git" -Arguments @("fetch", "origin")
  Invoke-Native -FilePath "git" -Arguments @("fetch", "production")

  $sourceRef = "refs/remotes/origin/$SourceBranch"
  $mirrorMainRef = "refs/remotes/origin/main"
  $productionMainRef = "refs/remotes/production/main"

  Assert-GitRefExists -RefName $sourceRef -ErrorMessage "Source branch 'origin/$SourceBranch' does not exist. Push the mirror branch first."
  Assert-GitRefExists -RefName $mirrorMainRef -ErrorMessage "Mirror base 'origin/main' does not exist."
  Assert-GitRefExists -RefName $productionMainRef -ErrorMessage "Production base 'production/main' does not exist. Fetch or configure the production remote."

  $changedFiles = @(git diff --name-only "origin/main..origin/$SourceBranch")
  if ($LASTEXITCODE -ne 0) {
    throw "Could not list changed files for origin/main..origin/$SourceBranch."
  }
  $archiveChanges = @($changedFiles | Where-Object { $_ -match '^(archive/|archive\\)' })
  if ($archiveChanges.Count -gt 0 -and -not $AllowArchiveChanges) {
    throw "Promotion includes changes under archive/. Re-run with -AllowArchiveChanges if this is intentional."
  }

  Write-Host "Creating patch from mirror file delta..."
  Invoke-Native -FilePath "git" -Arguments @("diff", "--binary", "origin/main..origin/$SourceBranch", "--output", $patchPath)
  $patchInfo = Get-Item -LiteralPath $patchPath
  if ($patchInfo.Length -eq 0) {
    throw "Patch is empty for origin/main..origin/$SourceBranch. Nothing to promote."
  }

  Write-Host "Creating production PR branch from production/main..."
  Invoke-Native -FilePath "git" -Arguments @("switch", "-c", $ProductionBranch, "production/main")

  Write-Host "Applying mirror file delta onto production branch..."
  try {
    Invoke-Native -FilePath "git" -Arguments @("apply", "--index", $patchPath)
  }
  catch {
    $applyErrorMessage = $_.Exception.Message
    try {
      Write-Host "Patch apply failed. Resetting production branch to production/main..."
      Invoke-Native -FilePath "git" -Arguments @("reset", "--hard", "production/main")
    }
    catch {
      throw "Patch failed to apply cleanly to production/main, and cleanup failed while restoring the repository state. Resolve the file conflict in the mirror branch or production base, then rerun promotion.`nApply error: $applyErrorMessage`nCleanup error: $($_.Exception.Message)"
    }

    throw "Patch failed to apply cleanly to production/main. Repository state was reset to production/main. Resolve the file conflict in the mirror branch or production base, then rerun promotion. $applyErrorMessage"
  }

  $resolvedPython = Resolve-PythonExecutable -RequestedPythonExe $PythonExe -RepoRoot $repoRoot
  Write-Host "Python: $resolvedPython"
  try {
    Invoke-ValidationAndEnsureClean -ResolvedPython $resolvedPython -PromotedFiles $changedFiles
  }
  catch {
    $validationErrorMessage = $_.Exception.Message
    try {
      Write-Host "Validation failed. Resetting production branch to production/main..."
      Invoke-Native -FilePath "git" -Arguments @("reset", "--hard", "production/main")
    }
    catch {
      throw "Validation failed, and cleanup failed while restoring repository state.`nValidation error: $validationErrorMessage`nCleanup error: $($_.Exception.Message)"
    }

    throw "Validation failed. Repository state was reset to production/main. $validationErrorMessage"
  }

  Write-Host "Committing production promotion patch..."
  Invoke-Native -FilePath "git" -Arguments @("commit", "-m", "Promote $SourceBranch to production")

  Write-Host "Pushing production branch..."
  Invoke-Native -FilePath "git" -Arguments @("push", "production", "${ProductionBranch}:refs/heads/${ProductionBranch}", "--force-with-lease")

  Write-Host ""
  Write-Host "Done. Open production PR:"
  Write-Host "K98-bot: $ProductionBranch -> main"
  Write-Host ""
  Write-Host "Mirror history was not pushed to production. Only file changes from origin/main..origin/$SourceBranch were promoted."
}
finally {
  if (Test-Path -LiteralPath $patchPath) {
    Remove-Item -LiteralPath $patchPath -Force
  }
}
