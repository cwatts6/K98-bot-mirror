# Developer Quickstart

## Windows Setup (per new PowerShell session)
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
. .\dev.ps1
pre-commit autoupdate
pre-commit install --install-hooks
pre-commit run --all-files



1. **Load local dev environment**
# === Session bootstrap (paste this as-is) ===
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create venv if missing, then activate
if (-not (Test-Path .\venv\Scripts\Activate.ps1)) {
  py -m venv venv
}
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Dot-source local dev env (pre-commit cache, UTF-8, etc.)
. .\dev.ps1

# Ensure hooks are installed
pre-commit autoupdate
pre-commit install --install-hooks

# Quick sanity: run all hooks across repo
pre-commit run --all-files
# === end bootstrap ===
