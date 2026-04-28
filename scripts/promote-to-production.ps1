[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateNotNullOrEmpty()]
  [string]$BranchName,

  [string]$PythonExe
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

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $scriptDir
$repoRoot = (Resolve-Path -LiteralPath $repoRoot).Path

Set-Location -LiteralPath $repoRoot

Write-Host "Repository: $repoRoot"

Write-Host "Checking git remotes..."
$originUrl = Get-RequiredRemoteUrl -RemoteName "origin"
$productionUrl = Get-RequiredRemoteUrl -RemoteName "production"
Write-Host "origin:     $originUrl"
Write-Host "production: $productionUrl"

Write-Host "Checking current branch..."
$currentBranch = (git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($currentBranch)) {
  throw "Could not determine the current git branch."
}
if ($currentBranch -ne $BranchName) {
  throw "Current branch is '$currentBranch'. Expected '$BranchName'. Switch branches first."
}

Write-Host "Checking working tree..."
$dirty = git status --porcelain
if ($LASTEXITCODE -ne 0) {
  throw "Could not read git status."
}
if ($dirty) {
  throw "Working tree is not clean. Commit or stash changes before promotion."
}

$resolvedPython = Resolve-PythonExecutable -RequestedPythonExe $PythonExe -RepoRoot $repoRoot
Write-Host "Python: $resolvedPython"

Write-Host "Running pre-commit validation..."
Invoke-Native -FilePath $resolvedPython -Arguments @("-m", "pre_commit", "run", "-a")

Write-Host "Re-checking working tree after pre-commit..."
$dirtyAfterPreCommit = git status --porcelain
if ($LASTEXITCODE -ne 0) {
  throw "Could not read git status after pre-commit."
}
if ($dirtyAfterPreCommit) {
  throw "pre-commit modified files. Review, commit, and rerun promotion."
}

Write-Host "Running pytest..."
Invoke-Native -FilePath $resolvedPython -Arguments @("-m", "pytest tests", "-q")

Write-Host "Pushing branch to mirror..."
Invoke-Native -FilePath "git" -Arguments @("push", "-u", "origin", $BranchName)

Write-Host "Pushing branch to production..."
Invoke-Native -FilePath "git" -Arguments @("push", "production", $BranchName)

Write-Host ""
Write-Host "Done. Now open PRs:"
Write-Host "1. K98-bot-mirror: $BranchName -> main"
Write-Host "2. K98-bot:        $BranchName -> main"
