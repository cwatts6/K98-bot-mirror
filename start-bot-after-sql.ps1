# start-bot-after-sql.ps1
param(
  [string]$SqlServiceName = 'MSSQLSERVER',
  [int]$SqlPort = 1433,
  [int]$MaxWaitSeconds = 300,
  [int]$PollIntervalSeconds = 5,
  [string]$PythonExe = 'C:\discord_file_downloader\venv\Scripts\python.exe',
  [string]$BotScript = 'C:\discord_file_downloader\run_bot.py',
  [string]$WorkingDir = 'C:\discord_file_downloader',
  [string]$LogFile = 'C:\discord_file_downloader\logs\start-bot-wrapper.log',
  [string]$Database = 'ROK_TRACKER',
  [double]$WarnThreshold = 85.0
)

function Log($m) {
  $t = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  $line = "$t $m"
  # Ensure directory exists
  $dir = Split-Path $LogFile -Parent
  if (-not (Test-Path $dir)) {
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
  }
  # Append to file, swallow any IO exceptions but write to host for interactive runs
  try {
    $line | Out-File -FilePath $LogFile -Append -Encoding utf8
  } catch {
    Write-Host ("Failed to write to log {0}: {1}" -f $LogFile, $_)
  }
  Write-Host $line
}

try {
  Log "Wrapper started. Waiting for service '$SqlServiceName' and port $SqlPort."

  # Wait for service
  $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $svc = Get-Service -Name $SqlServiceName -ErrorAction Stop
      if ($svc.Status -eq 'Running') {
        Log "SQL service $SqlServiceName is Running."
        break
      }
      Log ("SQL service {0} is {1}. Sleeping {2} s..." -f $SqlServiceName, $($svc.Status), $PollIntervalSeconds)
    } catch {
      Log ("Get-Service error for {0}: {1}" -f $SqlServiceName, $_)
    }
    Start-Sleep -Seconds $PollIntervalSeconds
  }
  if ((Get-Date) -ge $deadline) { Log "Timeout waiting for SQL service. Aborting."; exit 2 }

  # Wait for TCP port
  $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
  while ((Get-Date) -lt $deadline) {
    $t = Test-NetConnection -ComputerName 'localhost' -Port $SqlPort -WarningAction SilentlyContinue
    if ($t.TcpTestSucceeded) {
      Log "TCP port $SqlPort is open."
      break
    }
    Log ("TCP {0} not open yet. Sleeping {1} s..." -f $SqlPort, $PollIntervalSeconds)
    Start-Sleep -Seconds $PollIntervalSeconds
  }
  if ((Get-Date) -ge $deadline) { Log "Timeout waiting for TCP port. Aborting."; exit 3 }

  # DNS checks - warn only
  try {
    $d = Resolve-DnsName discord.com -ErrorAction Stop
    Log ("DNS discord.com OK: {0}" -f $($d[0].IPAddress))
  } catch {
    Log ("WARNING DNS discord.com failed: {0}" -f $_)
  }
  try {
    $s = Resolve-DnsName sheets.googleapis.com -ErrorAction Stop
    Log ("DNS sheets.googleapis.com OK: {0}" -f $($s[0].IPAddress))
  } catch {
    Log ("WARNING DNS sheets.googleapis.com failed: {0}" -f $_)
  }

  # --- NEW: SQL log health check (using sqlcmd if available) ---
  try {
    if (Get-Command -Name sqlcmd -ErrorAction SilentlyContinue) {
      Log "Running SQL log health check for database '$Database' (threshold ${WarnThreshold}%) using sqlcmd."

      $q1 = "SET NOCOUNT ON; SELECT CAST(used_log_space_in_percent AS float) FROM sys.dm_db_log_space_usage WHERE DB_NAME(database_id) = '$Database';"
      $q2 = "SET NOCOUNT ON; SELECT log_reuse_wait_desc FROM sys.databases WHERE name = '$Database';"

      # Use Windows auth (-E). If your environment needs SQL auth, modify this wrapper to pass -U/-P.
      $used_raw = sqlcmd -S "localhost,$SqlPort" -E -Q $q1 -h -1 -W 2>$null
      $reuse_raw = sqlcmd -S "localhost,$SqlPort" -E -Q $q2 -h -1 -W 2>$null

      if (-not $used_raw) {
        Log "WARNING: SQL health check returned no data for used_log_space_percent."
      } else {
        $used = [double]($used_raw.Trim())
        $reuse = ($reuse_raw -as [string]).Trim()
        Log ("SQL log usage for {0}: {1}% (reuse_wait: {2})" -f $Database, $used, $reuse)

        if ($used -ge $WarnThreshold) {
          Log ("ERROR: SQL log usage {0}% >= threshold {1}%. Aborting startup." -f $used, $WarnThreshold)
          exit 5
        }
        if ($reuse -eq "LOG_BACKUP") {
          Log ("ERROR: SQL reuse_wait_desc = LOG_BACKUP (requires full+log backups). Aborting startup.")
          exit 6
        }
      }
    } else {
      Log "sqlcmd not found on PATH; skipping SQL log health check (consider installing sqlcmd to enable this guard)."
    }
  } catch {
    Log ("WARNING: SQL log health check failed: {0}" -f $_)
    # Do NOT abort startup on unexpected sqlcmd failure; the wrapper should not block bootstrapping.
  }

  # Verify Python exists
  if (-not (Test-Path $PythonExe)) {
    Log ("ERROR: Python executable not found at {0}. Aborting." -f $PythonExe)
    exit 4
  }

  Log ("Starting bot: {0} {1} (cwd: {2})" -f $PythonExe, $BotScript, $WorkingDir)
  # Start the bot and capture PID
  $proc = Start-Process -FilePath $PythonExe -ArgumentList $BotScript -WorkingDirectory $WorkingDir -PassThru
  Log ("Bot started with PID {0}. Wrapper exiting." -f $($proc.Id))
  exit 0

} catch {
  Log ("Unhandled exception in wrapper: {0}" -f $_)
  exit 10
}