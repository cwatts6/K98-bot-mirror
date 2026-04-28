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

function Get-RemoteRepositoryName {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl
  )

  $normalized = $RemoteUrl.Trim().TrimEnd("/")
  if ($normalized.EndsWith(".git", [System.StringComparison]::OrdinalIgnoreCase)) {
    $normalized = $normalized.Substring(0, $normalized.Length - 4)
  }

  $parts = $normalized -split "[:/\\]"
  return $parts[$parts.Count - 1]
}

function Assert-RemoteRepositoryName {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteName,

    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedRepositoryName
  )

  $actualRepositoryName = Get-RemoteRepositoryName -RemoteUrl $RemoteUrl
  if ($actualRepositoryName -ne $ExpectedRepositoryName) {
    throw "Remote '$RemoteName' must point to '$ExpectedRepositoryName'. Current URL: $RemoteUrl"
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
    [string]$ResolvedPython
  )

  Write-Host "Running pre-commit validation..."
  Invoke-Native -FilePath $ResolvedPython -Arguments @("-m", "pre_commit", "run", "-a")
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
  Assert-RemoteRepositoryName -RemoteName "origin" -RemoteUrl $originUrl -ExpectedRepositoryName "K98-bot-mirror"
  Assert-RemoteRepositoryName -RemoteName "production" -RemoteUrl $productionUrl -ExpectedRepositoryName "K98-bot"
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

  $changedFiles = git diff --name-only "origin/main..origin/$SourceBranch"
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
  Invoke-Native -FilePath "git" -Arguments @("switch", "-C", $ProductionBranch, "production/main")

  Write-Host "Applying mirror file delta onto production branch..."
  try {
    Invoke-Native -FilePath "git" -Arguments @("apply", "--index", $patchPath)
  }
  catch {
    throw "Patch failed to apply cleanly to production/main. Resolve the file conflict in the mirror branch or production base, then rerun promotion. $($_.Exception.Message)"
  }

  Write-Host "Committing production promotion patch..."
  Invoke-Native -FilePath "git" -Arguments @("commit", "-m", "Promote $SourceBranch to production")

  $resolvedPython = Resolve-PythonExecutable -RequestedPythonExe $PythonExe -RepoRoot $repoRoot
  Write-Host "Python: $resolvedPython"
  Invoke-ValidationAndEnsureClean -ResolvedPython $resolvedPython

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
