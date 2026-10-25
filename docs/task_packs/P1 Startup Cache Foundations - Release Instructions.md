# P1 Startup Cache Foundations — release instructions

25 October 2026. This document prepares repository delivery and a future operator
deployment. It does not authorize or record a merge, updater installation, restart,
SQL/provider operation or activation change. Final PR heads and CI/review results
belong in the accompanying local release handoff.

## Release contents and prerequisites

The [implementation and acceptance pack](P1%20Startup%20Cache%20Foundations%20-%20Implementation%20and%20Acceptance.md)
defines the runtime change and separate residuals. There is no SQL migration,
ProcConfig change, dependency install, environment change or cache format migration.
The private branch must be patch-promoted from the mirror onto private main; never
push mirror history to production. Merge mirror first, then its equivalent private
PR only after final review, required CI and zero unresolved actionable threads.

The last verified installed Bot source is
`35d8b7e58a5c248c22552b8ae506e1d03ccc6afe`. Its prior event-cache transition remains
delivered and must not be reapplied. This release adds `startup_cache_foundations_v1`
as the 42nd exact transition: 13 startup/cache implementation members, authenticated
predecessor/target bytes, complete membership and existing bounds. It does not admit
arbitrary future edits. The original 41 transitions remain unchanged.

The candidate updater differs only in `prepare_k98_update.py` and
`k98_update_transitions.json`. A package upgrade is required before source deployment.
The previous updater manifest is the retained package from the verified 25 October
deployment, SHA256 `c7bfad26766d7db65cdde3a62b0509e5d366b4316e962c9fdac98e606c751c53`.
This is retained evidence, not a fresh live inventory; the installer must verify the
actual installed package. A mismatch stops the operation for reconciliation.

Before deployment, validate the final merged private-main target from the installed
commit with both retained installed and candidate manifests. The former must report
`UPDATER_UPGRADE_REQUIRED`; the candidate must report `ROUTINE_COMPATIBLE` with zero
blockers. A check against mirror history is not a production compatibility result:
scrubbing intentionally changes unrelated private configuration files.

```powershell
# Development PC, reviewed private checkout and its own interpreter; read-only.
& .\.venv\Scripts\python.exe -m scripts.validate_k98_update_compatibility `
  --base 35d8b7e58a5c248c22552b8ae506e1d03ccc6afe `
  --head production/main `
  --installed-tool-manifest '<release-folder>\candidate-update-tool.json'
```

Replace only the release-folder path with the supplied local handoff path. Run after
fetching the merged private main. Additional changes require renewed assessment.
This checker does not attest live custody or execute target source.

## Install the supplied updater package

Transfer the two supplied scripts together to
`C:\Users\cwatt\Downloads\P1-startup-foundations-release\package` on MINI_AMD.
Close other updater windows. Use **Windows PowerShell 5.1, Run as administrator**,
under the reviewed deployment account. Do not activate a development environment.
Run only after merge and the final compatibility gate above:

```powershell
$ErrorActionPreference = 'Stop'
$packageDirectory = 'C:\Users\cwatt\Downloads\P1-startup-foundations-release\package'
$expectedHashes = @{
    'Install-K98UpdateTool.ps1' = 'c32614cee88844a9008e37542fee91e6940352d3f496fce9257b4bd1d95e3d28'
    'Upgrade-K98InstalledUpdater.ps1' = 'a41a631edd4df43025d599b431370fe02dd27aee9c81c3ec5ff66ff9215adf1d'
}
foreach ($member in $expectedHashes.Keys) {
    $memberPath = Join-Path $packageDirectory $member
    if ((Get-FileHash -LiteralPath $memberPath -Algorithm SHA256).Hash -ne $expectedHashes[$member]) {
        throw "Package checksum mismatch: $member"
    }
}
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& (Join-Path $packageDirectory 'Upgrade-K98InstalledUpdater.ps1')
```

Use the upgrade helper, not Install directly over an existing updater. It verifies
the exact old/new pair, custody, account, operator lock and absence of active release;
it retains the previous package and supports resuming that same pair. Expected:
`UPGRADE COMPLETE`. The installed `update-tool.json` SHA256 must then be
`544eacb530595866474388124b12ea31a1a5325246ded5e7c65805a288a7bc11`.

## Deploy and verify

In the same elevated Windows PowerShell 5.1 window:

```powershell
& 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'
```

The updater selects private `K98-bot/main`. Confirm its printed target matches the
reviewed merged commit. Request `/ops graceful_restart` once in Discord **only when
prompted**, and leave PowerShell open. The runner owns drain, protected source/policy
installation, successor start and verification. Already-current requires no restart.

Retain transcript, readiness-status.json and verified.json. Confirm exact source,
seed, start and readiness evidence, then inspect `/ops show_command_versions` and a
complete recovery report. Review `monitor.cache_outcomes_v1` and
`monitor.admission_observations_v1` alongside the original startup observer states.
Execution, availability, persistence and readback are separate facts; process-local
generations and correlation IDs are not SQL/provider receipts.

Confirm profile/name startup observes its original work after a deadline, retained
cache availability remains truthful after failure, and main/last-KVK composition
does not enter the nested last-KVK operation twice. Where naturally exercised,
verify Location private acknowledgement, requested result visibility and selector
callbacks. Local tests establish these paths; live acceptance still needs evidence.

Keep SQL 51400 admission refusal separate from singleton locking and the historical
profile completion/reporting discrepancy. The requesting SQL session does not name
the blocker. Scan 1193 dated `2026-09-29 14:44:00` is expected off-season data.
Do not force a cache refresh, import, provider call, repost or rollover to obtain proof.

## Failure, rollback and remaining acceptance

On failure preserve the exact stage, source bindings and receipts. Resume only via
the supported helper/runner after reconciling uncertainty. No manual live pull,
reset/clean, task start, owner/ACL rewrite or control-file deletion. Do not repeat a
drain/start already evidenced. A bot rollback needs a reviewed reverse release from
the actually installed source; the forward-only transition does not authorize a
manual checkout or automatic downgrade. No cache deletion or SQL rollback is required
by this change, and retained business evidence must remain intact.

Natural empty-to-populated event restoration, eligible original-message controls and
safe private callback, exact Daily KVK Overview disposition, all three P1 families,
every WS1–WS6 residual, P0 natural rollover and final every-row F01–F05 reconciliation
remain separate. Preserve accepted scan/import/export receipts and the scan1233
eleven-sheet visual confirmation. Startup verification alone does not accept them.
