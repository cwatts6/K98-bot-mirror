[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^stats_[0-9a-f]{32}\.ready\.csv$')]
    [string]$CompletedFilename
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot 'venv\Scripts\python.exe'
$recoveryScript = Join-Path $PSScriptRoot 'retry_phase52_stats_import.py'

if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw "Production virtualenv Python was not found: $pythonExe"
}

Push-Location $repoRoot
try {
    & $pythonExe $recoveryScript `
        --completed-filename $CompletedFilename
    if ($LASTEXITCODE -ne 0) {
        throw "Phase 5.2 stats import recovery failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'COMPLETE - return the output to Codex for row-count and receipt validation.'
