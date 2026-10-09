# K98 promotion and deployment — operator runbook

Use this sequence for the protected S11 runtime. A merge or development-PC pull does not deploy the bot. The [S11 deployment and restart contract](S11%20Deployment%20and%20Restart%20Contract.md) defines the protected release protocol.

## Current release — 8 October 2026

**Stats-cache recovery succeeded at 20:18 UTC.** After the recorded manual
supersession and exact ticket 405 withdrawal, a normal
`/kvk_admin refresh_stats_cache` was admitted on its first attempt, acknowledged
the durable SQL checkpoint and snapshot capture, and rebuilt the 415-record KVK16
cache with `status=refreshed` in 31.1 seconds. Last-KVK cache also succeeded.
Do not repeat either recovery script or restart for this completed recovery.

The source date remains 29 September because it records source-scan provenance,
not the cache-build time. This result proves the normal stats SQL/cache path
works; it does not prove newer data ingestion or provider/export delivery.
Intake/recovery flags remain false. The historical SQL outcome remains recorded
as unknown in the supersession audit.

PR616 source and startup seed are installed; bot startup, independent successor
native verification and matching SQL session are observed. The generic release
runner still lacks a successful final release receipt and is **not live accepted**.
A successful manual recovery does not close that separate deployment-tooling gap.

### What happens next

No further incident recovery action is required for the accepted stats-cache run.
Next engineering work is acceptance of the simplified updater, followed immediately
by prevention/reconciliation of orphan queue entries. Routine patches use a fixed-command
workflow without bespoke operator-authored packets, or the coordinated startup
source policy must be reconsidered. Broader S11/provider acceptance remains
separate; do not change activation flags on the strength of this cache result.

The operator's local S11 handover retains the exact receipts, logs and completed
recovery commands as history. It is local-only evidence, excluded from Git, at
`.codex_artifacts/s11-runtime-contracts-20261004/S11-GoLive-Handover-20261008.md`
on the development PC; it is not a repository document or deployment input.

### Why not just git pull?

Git still supplies the application source. The protected S11 startup also pins
the approved source-file hashes and startup policy. Updating the checkout alone
does not update that matching policy or coordinate shutdown and one successor start.
It can leave the installed source inconsistent with the approved startup contract.

The release folder contains the instructions and checks for that coordinated
update: stop/drain, install the exact private-main source, install its matching
startup policy, start and verify. It is not a replacement source-control system.
A reviewed source step may use Git; an uncoordinated pull in the live checkout is
not the complete deployment operation.

The reusable updater now implements automatic package creation locally. Native
elevated rehearsal and the first successful real release remain acceptance gates.
The earlier generic-runner attempt reached a running successor but failed its
final verification. Local tests do not close that live-acceptance gap.

**Required tooling outcome:** a manual update must be
as straightforward as the previous `git pull` workflow. A stable script may
prepare and deploy the release, but the operator must not handcraft manifests,
adapters, hashes or commands for each patch. If the source-policy design cannot
support that workflow, review redesign/removal of the coordinated source-policy
update requirement. This is an unresolved usability requirement, not optional
polish. The updater is the first priority, immediately followed by the orphan-queue fix.
That fix must be the first real release used for live acceptance. Changing the
source-policy requirement remains a separate reviewed decision.

**How often:** use this path when actually installing runtime changes, including
small fixes. Several compatible PRs can share one deployment. Documentation and
test-only merges do not require a bot restart/deployment unless they change
installed operational material. A source-only release has no SQL migration step.
The requirement is coordinated source/policy installation, not a fresh manual
design exercise or a repeat of prior recovery for each patch.

For future releases, the updater obtains and validates fresh bindings automatically;
no operator copies commit, seed or receipt values from a previous release.

## Machine and shell

| Work | Machine | Window |
| --- | --- | --- |
| Code, tests, PRs and local pulls | Development PC | Normal PowerShell; development Python is `.venv\Scripts\python.exe` |
| Install the reviewed updater once | MINI_AMD | Supplied installer outside the live repository |
| Automatic preparation and deployment | MINI_AMD | **Windows PowerShell 5.1, Run as administrator**, under the reviewed deployment account |
| Restart request and command checks | Discord | Operator account |

Deployment requires **Windows PowerShell**, not PowerShell 7 (`pwsh`). Do not activate the bot virtual environment or run `dev.ps1` for deployment.

On MINI_AMD, do not manually pull/switch the live checkout, install packages, run formatters, reset/clean Git, start the task or restart ahead of the runner. The packet owns changes after the old process pair drains. Tests belong on the development PC or a separately reviewed isolated checkout.

## Step 1 — Validate and prepare both PRs

**Where:** Codex on the development PC. Skip if both PRs are already merged.

Copy this prompt into the implementation chat:

```text
Prepare this K98 change for merge. Read AGENTS.md and required references. Use
k98-pr-review, k98-test-selection, applicable SQL validation, security routing and
k98-promotion-check. Validate the mirror change, then patch-promote its file delta
onto private production/main and open the private PR. Do not push mirror history
to production. Address, reply to and resolve review comments appropriately; request
another review and verify final-head CI and zero unresolved threads. Report both
exact heads and readiness. Do not merge or deploy. Preserve activation flags and
retained uncertain work. Do not repeat successful operational evidence.
```

Codex uses `scripts/promote-to-production.ps1` to create the initial private PR branch from `production/main`, apply the validated mirror delta, validate, commit and push. That is repository promotion, not deployment. Corrections must remain equivalent between PRs.

**Continue when:** both final heads have completed review and required checks, zero unresolved threads and a recorded promotion-readiness verdict.

## Step 2 — Merge and update the development PC

**Where:** GitHub, then normal PowerShell on the **development PC only**.

1. Merge the mirror PR into `K98-bot-mirror/main`.
2. Merge the private PR into `K98-bot/main`.
3. If the development PC is not already updated, paste:

```powershell
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'C:\discord_file_downloader'
$changes = @(git status --porcelain)
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Git status.' }
if ($changes.Count -ne 0) { throw 'Local changes exist. Return the output to Codex; do not reset or clean.' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Mirror fetch failed.' }
git fetch production
if ($LASTEXITCODE -ne 0) { throw 'Private production fetch failed.' }
git switch main
if ($LASTEXITCODE -ne 0) { throw 'Switch to main failed.' }
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'Fast-forward pull failed. Return the output to Codex.' }
git status --short
git log -1 --oneline
git rev-parse production/main
```

**Expected:** clean local main and the refreshed private-main SHA. Mirror/private hashes may differ because their Git histories differ. Do not rerun branch promotion after merging to deploy the same delta.

## Step 3 — Run the fixed updater on MINI_AMD

**Implementation status:** the reusable updater is under local validation and review.
It is not installed or live-accepted yet. Do not run a draft copy against production.
The orphan-queue fix is the first real release intended to accept this workflow.

After the reviewed tool is installed once, every routine source-only release uses
this same block in **Windows PowerShell 5.1, Run as administrator**, on MINI_AMD:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'
```

The updater fetches private production `main`, checks the running installation,
prepares the release and matching startup policy automatically, and stages the
protected handoff. It prints the selected commit. If already current, it exits
without requesting a restart. No release ID, commit, manifest, hash or adapter is
entered or edited by the operator. No Codex chat or development-PC package transfer
is required for each routine update.

If only package preparation is wanted, the same command accepts `-PrepareOnly`.
Later run the normal command above. It refreshes unused preparation automatically
so an intervening normal restart cannot leave stale process/session bindings.
After deployment intent is recorded, it retains and resumes that exact release.

## Step 4 — Restart once when prompted

In Discord, run `/ops graceful_restart` **only when the updater prompts**. Leave
PowerShell open. The updater verifies drain, installs the pinned source and matching
policy, starts one successor and verifies its native/SQL/startup evidence. It saves
its transcript and release receipts automatically. Check `/ops show_command_versions`
after success. Deployment success does not certify provider/import health.

These are the two routine operator actions: **run the unchanged update script;
request the prompted restart**. Small patches use exactly the same path as larger
source-only releases. Package preparation is part of the script, not another task.

On interruption, retain the output and receipts. The same command finds the saved
release and verifies completed steps before continuing. It must not request another
restart once the drain receipt exists, rerun an uncertain apply, or issue another
start after lost acknowledgement. An unresolved outcome remains stopped for precise
reconciliation; do not delete control files, manually pull, or start the task.

## Deployment completion status

The completion message distinguishes source/startup verification from functional
health. The current read-only verifier classifies import/export as **degraded**
when fresh functional evidence is unavailable, and identifies observed runtime
admission failures separately. It never infers healthy import/export from startup
markers, cached data or a live SQL session. The protected `readiness-status.json`,
final `verified.json` and transcript retain that classification. A degraded result
does not request another restart or repeat an import/export; check the affected
feature before accepting its functional health. This implements the release
contract's explicit healthy/degraded reporting, not a provider-delivery test.

## One-time updater installation

The reviewed implementation supplies one automatically built
`Install-K98UpdateTool.ps1`. Its preparation command on the development PC is
`python -m scripts.package_k98_update_tool`; the operator does not write a tool
manifest. The release handoff supplies the exact reviewed installer and checksum.
Installing it on MINI_AMD creates the protected tool directory only: it does not
change running source, startup policy, task configuration, SQL or activation flags.
It can therefore prepare the first release containing the updater without modifying
the live checkout first. This installation is not repeated for ordinary releases.

## Release boundaries and exceptional changes

Normal bot and SQL changes go through their Git repositories and review first.
The source-only updater selects private `K98-bot/main`; it does not deploy mirror
history, uncommitted live edits, dependencies, configuration or SQL migrations.
A release requiring SQL uses explicit reviewed migration IDs and the correct
SQL-before-bot order where needed, with outcome receipts and no blind replay.

A rare emergency should normally be a small Git hotfix through this same routine
path. A direct-code emergency mode is a separate future design: explicit invocation,
exact patch/before-state capture, minimum validation, matching source-policy update,
controlled restart and mandatory reconciliation back into Git. It is not implemented
or implicitly enabled by this updater. Ordinary restart cannot legitimize uncommitted
changes to pinned source.

## Ordinary restart — no deployment

Run `/ops graceful_restart` once in Discord. It restarts the **installed** release; it does not pull source or run migrations. No deployment packet is needed. Do not repeat the accepted normal-restart test merely because another change merged.

## Repository and validation rules

- `origin` is the scrubbed mirror; `production` is private `K98-bot`. Never push mirror history to production.
- Deploy only an exact reviewed private-main commit. Review SQL-facing contracts against `C:\K98-bot-SQL-Server`.
- Use the K98 review, test-selection, SQL-validation, security-routing and promotion-check skills as applicable. Preserve exact diff review and test evidence.
- Run or justify architecture, deferred-item, test-selection, security-routing, smoke-import, registration, lint and appropriate pytest/log-hygiene checks before promotion. Runtime changes require appropriate focused/full validation; deployment is not the place to auto-format source.
- Never discover and execute all pending migration files. Include only required reviewed migration IDs and retain successful receipts.
- Cleanup is optional development maintenance after evidence retention, not a deployment step. No blanket reset/clean, SQL `git restore .`, or live-checkout branch testing belongs in this runbook.
- Merge, deployment, recovery and activation are different outcomes. No automatic merge or activation is implied.
