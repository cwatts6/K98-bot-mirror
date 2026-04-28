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
git fetch origin
git switch <branch-name>
git pull origin <branch-name>
git status
git log --oneline -5
```

### Step 2 - Run Local Validation

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
git diff --check
git status
```

`pytest` should target `tests`, not the whole repository, so archived legacy tests are not included by accident.

### Step 3 - Merge Mirror PR

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

### Step 4 - Confirm Production Remote

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

### Step 5 - Promote to Production

```powershell
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
- runs `pre_commit`, `pytest -q tests`, and `git diff --check`
- pushes `prod/<branch-name>` to `production`

If validation modifies files, review the changes, commit the correct mirror fix, and rerun the promotion.

### Step 6 - Open Production PR

Open a PR in GitHub:

```text
K98-bot: prod/<branch-name> -> main
```

GitHub should allow a normal comparison because the branch is based on `K98-bot/main`.

### Step 7 - Merge Production PR

In GitHub, merge:

```text
K98-bot PR -> main
```

### Step 8 - Deploy on Bot Machine Only

```powershell
cd C:\discord_file_downloader
git switch main
git pull origin main
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The bot machine must deploy only from `K98-bot/main`, never from `K98-bot-mirror`.

### Step 9 - Cleanup

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
