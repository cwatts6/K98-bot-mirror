# dev.ps1 — repo-local env for Windows (safe to commit)
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path

# Local pre-commit cache to avoid AV locking
$env:PRE_COMMIT_HOME = Join-Path $repo ".pre-commit-home"

# Keep temp files inside the repo to reduce AV interference
$env:TEMP = Join-Path $env:PRE_COMMIT_HOME "tmp"
$env:TMP  = $env:TEMP

# UTF-8 everywhere (prevents encoding issues)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
try {
  chcp 65001 | Out-Null
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

# Ensure folders exist
New-Item -ItemType Directory -Force $env:PRE_COMMIT_HOME,$env:TEMP | Out-Null

Write-Host "[dev] PRE_COMMIT_HOME: $env:PRE_COMMIT_HOME"
Write-Host "[dev] TEMP/TMP:       $env:TEMP"
Write-Host "[dev] UTF-8 enabled"
