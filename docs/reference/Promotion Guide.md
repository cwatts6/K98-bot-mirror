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

## Codex Skills

Use the local Codex skills as promotion guardrails:

- `k98-pr-review`: use before merge to confirm the mirror change is ready for handoff.
- `k98-test-selection`: use before promotion to verify the focused and broad validation plan.
- `k98-sql-validation`: use when SQL-facing bot changes, SQL repo changes, `ProcConfig`, DAL
  assumptions, staging/output tables, imports, exports, or SQL-backed caches are involved.
- `k98-promotion-check`: use before creating the production branch or PR, and again before bot
  machine deployment when SQL, config, dependency, startup, scheduler, persistence, or cache risks
  exist.
- `k98-deferred-optimisation-capture`: use when promotion review finds out-of-scope cleanup or
  follow-up work that should not be mixed into the active promotion.

## Standard Process

### 1. Validate Mirror Branch

Before running the branch checks, use `k98-pr-review` for merge readiness and `k98-test-selection`
to confirm the validation plan. If SQL-facing work is present, use `k98-sql-validation` and keep the
SQL repo evidence with the promotion notes.

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1

git fetch origin
git switch codex/<branch-name>
git pull origin codex/<branch-name>
git status
git log --oneline origin/main..HEAD
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD

cd C:\K98-bot-SQL-Server
git pull
git status
git log --oneline -5
```

or if required as there are SQL differences use:
```powershell
cd C:\K98-bot-SQL-Server
git restore .
git pull
```

### 2. Run Local Validation

Use `k98-test-selection` to choose focused tests in addition to the baseline gates below. Document
any skipped validation with a reason before promotion.

Use targeted validation for small changes and full validation before production promotion:

```powershell
cd C:\discord_file_downloader
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
git diff --check
git status
```

if pre-commit triggers files reformat or changes:
```powershell
git commit -a
git push
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

Before creating the production branch, use `k98-promotion-check` to verify remotes, branch state,
validation evidence, SQL/config sequencing, bot-machine readiness, and rollback notes. Do not
promote if it reports blocking issues.

```powershell
cd C:\discord_file_downloader
git config core.quotePath false

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

Include the `k98-promotion-check` verdict, validation summary, SQL/config notes, and rollback notes
in the production PR body.

Open:

```text
K98-bot: prod/<branch-name> -> main
```

### 6. Test on local BOT Machine before merge

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
git merge --quit
git switch main
git fetch
git switch prod/<branch-name>
git pull
```

GitHub should allow a normal comparison because the branch is based on `K98-bot/main`.

# If needed to push again 

1. 
```powershell
git switch main
git branch -D prod/<branch-name>
```

2. 
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1

git fetch origin
git switch codex/<branch-name>
git pull origin codex/<branch-name>

.\scripts\promote-to-production.ps1 `
  -SourceBranch codex/<branch-name> `
  -ProductionBranch prod/<branch-name>
```

3. (on the bot machine)
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1

git merge --abort 2>$null
git fetch origin
git switch prod/<branch-name>
git reset --hard origin/prod/<branch-name>
git clean -fd
git status
git log --oneline -5
```




### 7. Merge And Deploy

Before bot-machine deployment, rerun or refresh `k98-promotion-check` when the change includes SQL,
config, dependency, startup, scheduler, persistence, rehydration, or cache implications.

1. Merge the mirror PR into `K98-bot-mirror/main`.
Then update local mirror main:
```powershell
git switch main
git pull origin main
git status
```

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

```powershell
git commit -a
git push
```

### 8. Post-Production Sync & Alignment (NEW)

```powershell
cd C:\discord_file_downloader
git fetch origin
git fetch production
git switch main
git reset --hard origin/main
git clean -fd

cd C:\K98-bot-SQL-Server
git pull
```


### 9. Cleanup

```powershell
cd C:\discord_file_downloader
git switch main
git pull origin main
git branch --delete codex/<branch-name>
git branch --delete prod/<branch-name>
git fetch origin --prune
git fetch production --prune

cd C:\K98-bot-SQL-Server
git switch main
git pull
git status
git fetch origin --prune
```

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
