# dev.ps1 — repo-local/dev shell setup for Windows
# Usage:
#   . .\dev.ps1             # global pre-commit home in %LOCALAPPDATA% (recommended)
#   . .\dev.ps1 -LocalCache # use repo-local .pre-commit-home (optional)

param(
  [switch]$LocalCache
)

$ErrorActionPreference = 'Stop'

# Resolve repo path (folder containing this script)
$ScriptPath = $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $ScriptPath

# Decide pre-commit home
if ($LocalCache) {
  $preCommitHome = Join-Path $repo ".pre-commit-home"
  $mode = "LOCAL"
} else {
  $preCommitHome = Join-Path $env:LOCALAPPDATA "pre-commit"
  $mode = "GLOBAL"
}

# Keep temp files alongside pre-commit home (reduces AV/indexer interference)
$tempDir = Join-Path $preCommitHome "tmp"

# UTF-8 everywhere (prevents encoding issues with emojis/logs)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try { chcp 65001 | Out-Null } catch {}
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Export environment for this session
$env:PRE_COMMIT_HOME = $preCommitHome
$env:TEMP = $tempDir
$env:TMP  = $tempDir

# Ensure folders exist
New-Item -ItemType Directory -Force -Path $preCommitHome | Out-Null
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Optional: show which Python/venv we're using (PS5-safe)
$python = $null
try {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { $python = $cmd.Source }
} catch {}
$venv = $env:VIRTUAL_ENV

# Banner
Write-Host "[dev] Mode:            $mode" -ForegroundColor Cyan
Write-Host "[dev] PRE_COMMIT_HOME: $preCommitHome"
Write-Host "[dev] TEMP/TMP:        $tempDir"
if ($venv)  { Write-Host "[dev] VENV:            $venv" }
if ($python){ Write-Host "[dev] python.exe:      $python" }
Write-Host "[dev] UTF-8 enabled"
