# rotate-logs.ps1
param(
  [string]$LogFile = 'C:\discord_file_downloader\logs\start-bot-wrapper.log',
  [int]$KeepLines = 1000
)

function Trim-LogFile {
  param($file, $keep)
  if (-not (Test-Path $file)) {
    Write-Output ("rotate-logs: file not found: {0}" -f $file)
    return
  }

  $temp = Join-Path -Path $env:TEMP -ChildPath ("{0}.tmp" -f (Split-Path $file -Leaf))

  try {
    # Write trimmed content to temp file
    Get-Content -Path $file -Tail $keep -ErrorAction Stop | Set-Content -Path $temp -Encoding utf8 -ErrorAction Stop
  } catch {
    Write-Output ("rotate-logs: failed to write temp for {0}: {1}" -f $file, $_)
    return
  }

  # Try to atomically replace the original; fall back if needed
  try {
    Move-Item -Path $temp -Destination $file -Force -ErrorAction Stop
    Write-Output ("rotate-logs: moved temp -> {0}" -f $file)
    return
  } catch {
    Write-Output ("rotate-logs: Move-Item failed for {0}: {1}" -f $file, $_)
  }

  try {
    Copy-Item -Path $temp -Destination $file -Force -ErrorAction Stop
    Remove-Item -Path $temp -Force -ErrorAction SilentlyContinue
    Write-Output ("rotate-logs: copied temp -> {0} (fallback copy)" -f $file)
    return
  } catch {
    Write-Output ("rotate-logs: Copy-Item fallback failed for {0}: {1}" -f $file, $_)
  }

  try {
    $content = Get-Content -Path $temp -Raw -ErrorAction Stop
    Set-Content -Path $file -Value $content -Encoding utf8 -Force -ErrorAction Stop
    Remove-Item -Path $temp -Force -ErrorAction SilentlyContinue
    Write-Output ("rotate-logs: overwritten {0} using Set-Content fallback" -f $file)
    return
  } catch {
    Write-Output ("rotate-logs: final fallback (Set-Content) failed for {0}: {1}" -f $file, $_)
  } finally {
    if (Test-Path $temp) {
      try { Remove-Item -Path $temp -Force -ErrorAction SilentlyContinue } catch {}
    }
  }
}

# Ensure log directory exists
$logDir = Split-Path -Path $LogFile -Parent
if (-not (Test-Path $logDir)) {
  try {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
  } catch {
    Write-Output ("rotate-logs: cannot create {0}: {1}" -f $logDir, $_)
    exit 1
  }
}

# Run rotation on the single target file
Trim-LogFile -file $LogFile -keep $KeepLines