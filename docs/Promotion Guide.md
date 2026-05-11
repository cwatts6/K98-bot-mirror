# Mirror to Production Promotion Guide

## Why This Exists

`K98-bot-mirror` and `K98-bot` may have unrelated Git histories. A branch created in the mirror repository cannot be pushed directly to the production repository and used for a production pull request, because GitHub may not be able to compare it with `K98-bot/main`.

The production pull request branch must always be based on `production/main`. Only the final file changes from the mirror branch are applied to that production branch.

Do not directly promote mirror branch history:

```powershell
git push production <mirror-feature-branch>
```

Use the patch-based promotion script instead.

## Standard Process

### Step 1 - Validate Mirror Branch Locally

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1
git fetch origin
git switch <branch-name>
git pull origin <branch-name>
git status
git log --oneline -5
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
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1
cd C:\K98-bot-SQL-Server
git restore .
git pull
```

### Step 2 - Run Local Validation

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
git diff --check
git status
```

`pytest` should target `tests`, not the whole repository, so archived legacy tests are not included by accident.

if pre-commit triggers files reformat or changes:

```powershell
git commit -a
git push
```

### Step 3 - Confirm Production Remote

```powershell
git remote -v
```

If needed:

```powershell
git remote add production https://github.com/cwatts6/K98-bot.git
git fetch production
```

The expected remotes are:

```text
origin     -> K98-bot-mirror
production -> K98-bot
```

### Step 4 - Promote to Production

```powershell
git config core.quotePath false

.\scripts\promote-to-production.ps1 `
  -SourceBranch <branch-name> `
  -ProductionBranch prod/<branch-name>
```

For backwards compatibility, `-BranchName` can be used in place of `-SourceBranch`.

The script:

- verifies the remotes
- fetches `origin` and `production`
- verifies `origin/<branch-name>` and `production/main`
- creates `prod/<branch-name>` from `production/main`
- applies the file delta from `origin/main..origin/<branch-name>`
- commits the promoted file changes
- runs `pre_commit` against the promoted file list, then `pytest -q tests`, `git diff --check`, and `git diff --cached --check`
- pushes `prod/<branch-name>` to `production`

The script automatically derives the promoted file list from:

```powershell
git diff --name-only origin/main..origin/<branch-name>
```

During promotion, the intended file delta is staged before validation. The script therefore checks for unexpected unstaged changes and unexpected staged files rather than requiring a completely clean working tree before the promotion commit.

If validation modifies promoted files, review the changes, commit the correct mirror fix, and rerun the promotion. Unrelated production baseline formatting should not be mixed into the production promotion branch.


### Step 5 - Open Production PR

Open a PR in GitHub:

```text
K98-bot: prod/<branch-name> -> main
```

### Step 6 - Test on local BOT Machine before merge

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
git merge --quit
git switch main
git fetch
git switch prod/<branch_name>
git pull
```

GitHub should allow a normal comparison because the branch is based on `K98-bot/main`.

# If needed to push again 

1. 
```powershell
git switch main
git branch -D prod/<branch_name>
```

2. 
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1

git fetch origin
git switch <branch_name>
git pull origin <branch_name>

.\scripts\promote-to-production.ps1 `
  -SourceBranch <branch_name> `
  -ProductionBranch prod/<branch_name>
```

3. (on the bot machine)
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1

git merge --abort 2>$null
git fetch origin
git switch prod/<branch_name>
git reset --hard origin/prod/<branch_name>
git clean -fd
git status
git log --oneline -5
```

### Step 7 - Merge Mirror PR

In GitHub, merge:

```text
K98-bot-mirror PR -> main
```

Then update local mirror main:

```powershell
git switch main
git pull origin main
git status
```

### Step 8 - Merge Production PR

In GitHub, merge:

```text
K98-bot PR -> main
```

### Step 9 - Deploy on Bot Machine Only

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

if pre-commit updates any files push again!
```powershell
git commit -a
git push
```

The bot machine must deploy only from `K98-bot/main`, never from `K98-bot-mirror`.

### Step 10 - Post-Production Sync & Alignment (NEW)

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


### Step 11 - Cleanup

```powershell
cd C:\discord_file_downloader
git switch main
git pull origin main
git branch --delete <branch-name>
git branch --delete prod/<branch-name>
git fetch origin --prune
git fetch production --prune
```

## Troubleshooting

Missing `production` remote:

```powershell
git remote add production https://github.com/cwatts6/K98-bot.git
git fetch production
```

Empty patch:

The source branch has no file changes compared with `origin/main`, or the wrong source branch was provided.

Patch conflict:

The file delta from the mirror branch does not apply cleanly to `production/main`. Resolve the production compatibility issue in the mirror branch or update production first, then rerun the promotion.

Archive changes:

The script refuses changes under `archive/` by default. Re-run with `-AllowArchiveChanges` only when those archived files are intentionally part of the promotion.
