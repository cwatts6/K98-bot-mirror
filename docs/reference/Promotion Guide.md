# Mirror To Production Promotion Guide

Purpose: promote a validated mirror branch from `K98-bot-mirror` to the private production
repository `K98-bot`.

## Why This Exists

Mirror and production may have unrelated Git histories. Do not push mirror branch history directly
to production. Production PR branches must be based on `production/main`; apply only the file delta
from the mirror branch.

Do not use:

```powershell
git push production <mirror-feature-branch>
```

Use the patch-based promotion script instead.

## Standard Process

### 1. Validate Mirror Branch

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1

git fetch origin
git switch codex/<branch-name>
git pull origin codex/<branch-name>
git status
git log --oneline origin/main..HEAD
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

If SQL changes are involved:

```powershell
cd C:\K98-bot-SQL-Server
git pull
git status
git log --oneline -5
```

### 2. Run Local Validation

Use targeted validation for small changes and full validation before production promotion:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
python -m pytest -q tests
git diff --check
git status
```

### 3. Confirm Remotes

```powershell
git remote -v
```

Expected:

```text
origin     -> K98-bot-mirror
production -> K98-bot
```

Add production if missing:

```powershell
git remote add production https://github.com/cwatts6/K98-bot.git
git fetch production
```

### 4. Promote Branch

```powershell
.\scripts\promote-to-production.ps1 `
  -SourceBranch codex/<branch-name> `
  -ProductionBranch prod/<branch-name>
```

The script:

- verifies remotes
- fetches `origin` and `production`
- creates `prod/<branch-name>` from `production/main`
- applies the file delta from `origin/main..origin/<branch-name>`
- runs validation against the promoted file list
- commits and pushes the promoted branch to `production`

If validation modifies files, review the changes, fix the mirror branch first where appropriate,
and rerun promotion.

### 5. Open Production PR

Open:

```text
K98-bot: prod/<branch-name> -> main
```

### 6. Merge And Deploy

1. Merge the mirror PR into `K98-bot-mirror/main`.
2. Merge the production PR into `K98-bot/main`.
3. Deploy only from `K98-bot/main` on the bot machine.

Deployment machine:

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
git switch main
git pull
Git-CleanupMerged
.\venv\Scripts\python.exe -m pip install -r requirements.txt
pre-commit run -a
pytest -q tests
```

If validation changes files on the production branch, commit and push those intended changes before
deploying.

## Troubleshooting

### Empty Patch

The source branch has no file changes compared with `origin/main`, or the wrong source branch was
provided.

### Patch Conflict

The file delta from the mirror branch does not apply cleanly to `production/main`. Resolve the
compatibility issue in the mirror branch or update production first, then rerun promotion.

### Archive Changes

The script refuses archive changes by default. Use `-AllowArchiveChanges` only when archived files
are intentionally part of the promotion.
