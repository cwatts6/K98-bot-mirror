# KingdomScanData4 Phase 5.1 immutable-handoff remediation runbook

This runbook is for the pinned isolated rehearsal only until Phase 5.2 separately authorizes the
production ACL rollout.

## Current release state

- Mirror PR #232 is open.
- Production PR #539 is open.
- MINI_AMD has temporarily exercised PR #539 code.
- PR #539 is not accepted while the immutable-handoff evidence is failing.
- After the corrected production PR is merged, MINI_AMD must be switched back to private
  `K98-bot/main`, pulled, validated and gracefully restarted before Phase 5.2 begins.

## 1. Preserve the failed evidence

Do not edit or delete:

- the failed `phase5_1_*` evidence directory;
- the `Import_Claimed\<completed-name>.renamed` file;
- the matching `dbo.KS4_ImportFileClaim` row.

## 2. Apply the reviewed isolated reset

Stop the bot writer first. Run the reset only with the exact failed run ID and completed filename:

```powershell
Set-Location C:\discord_file_downloader

.\scripts\Reset-Phase51FailedEvidence.ps1 `
  -FailedRunId '<failed-run-id>' `
  -CompletedFileName '<stats_...ready.csv>' `
  -ConfirmDiscardFailedAttempt `
  -ConfirmWritersStopped
```

Require `failed_work_files\reset_receipt.json`. The script quarantines the 11-byte renamed
artifact before deleting exactly one receipt-free isolated claim.

The reset writes `failed_work_files\reset_intent.json` atomically before the SQL delete and bounds
both SQL lock and query waits. If interruption occurs after commit, rerun the same command to
complete the receipt from that intent. The single pre-intent incident from
`phase5_1_20260816T173604288Z` requires the additional explicit
`-ConfirmRecoverLegacyPostCommit` switch; that path accepts only the pinned run, filename,
transcript markers, quarantine digest, absent claim and absent matching receipt.

## 3. Configure isolated directory ACLs

Resolve the real identities first:

```powershell
$phase51BotIdentity = 'MINI_AMD\cwatt'
$phase51SqlIdentity = 'NT SERVICE\MSSQLSERVER'
$phase51AclEvidence = 'C:\discord_file_downloader\downloads_test_phase5_rehearsal\evidence\acl'
```

Then run from an elevated shell:

```powershell
.\scripts\Configure-Phase51ImmutableHandoffAcl.ps1 `
  -RootPath 'C:\discord_file_downloader\downloads_test_phase5_rehearsal' `
  -BotIdentity $phase51BotIdentity `
  -SqlIdentity $phase51SqlIdentity `
  -EvidenceDirectory $phase51AclEvidence `
  -ConfirmIsolatedRoot
```

Require a `phase5_1_acl_*.json` PASS receipt. Ready must give the bot Modify; Claimed and Archive
must give it Read/Execute at most; SQL and SYSTEM receive Full Control; broad inherited mutation
grants must be absent.

## 4. Deploy and verify the SQL remediation

Use the SQL repository preflight, migration and verification in
`performance_remediation\kingdomscandata4\phase5_1_acl`. Deploy SQL before the corrected bot.

## 5. Deploy the corrected test branch

Use the patch-based promotion workflow to update PR #539 only after mirror PR #232 is validated.
For the isolated evidence run, MINI_AMD may test the production PR branch, but that branch is not a
production acceptance point.

Start or restart the bot only through `StartDLBotAfterSQL` / `/ops graceful_restart`, then
resolve the live PID from `bot_pid.txt` and `BOT_LOCK.json`.

## 6. Run real-token evidence

Freeze the exact 40-character SQL and bot commits:

```powershell
.\scripts\Invoke-Phase51ImmutableHandoffEvidence.ps1 `
  -BotProcessId $phase51BotPid `
  -ExpectedSqlCommit '<40-char-sql-commit>' `
  -ExpectedBotCommit '<40-char-bot-commit>' `
  -ConfirmIsolatedTarget `
  -ConfirmCurrentTokenIsBot
```

Require:

- `receipt.json` with `Status=PASS`;
- five denied mutation attempts;
- SQL owner and DACL evidence;
- matching Ready, claim and archive digests;
- archived claim and receipt;
- no `receipt.failed.json`.

## 7. Review, merge and restore MINI_AMD

After both repository Changes reviews and PR reviews pass:

1. Merge mirror PR #232.
2. Refresh PR #539 through the patch-based promotion flow.
3. Merge PR #539.
4. On MINI_AMD, stop using the PR branch and switch to private production `main`.
5. Pull the merged production commit, run pre-commit and full pytest, and gracefully restart.
6. Confirm the running PID, lock files, startup logs and exact production commit.
7. Only then start Phase 5.2.
