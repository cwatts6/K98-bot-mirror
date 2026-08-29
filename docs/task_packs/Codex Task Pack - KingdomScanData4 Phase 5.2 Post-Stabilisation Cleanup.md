# Codex Task Pack - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup

> Cross-machine audit, retention, removal, Git cleanup, and closeout pack for the completed KingdomScanData4 Phase 5.2 production programme.
> This pack is **not one-pass approved**. Begin with a read-only audit, present an exact retain/archive/quarantine/delete manifest, and stop for operator approval before any destructive action.

## 1. Task Header

- Task name: `KingdomScanData4 Phase 5.2 post-stabilisation cleanup`
- Date: `2026-08-28`
- Owner/context: `Chris Watts / completed Phase 5.2 production go-live and one-week stability period`
- Task type: `deferred optimisation batch`
- One-pass approved: `no`
- Local SQL repository: `C:\K98-bot-SQL-Server`
- Local bot repository: `C:\discord_file_downloader`
- Production machine: `MINI_AMD`
- Production bot worktree: `C:\discord_file_downloader`
- Production SQL instance/database: `MINI_AMD / ROK_TRACKER`
- Recommended mirror branch: `codex/phase52-post-stabilisation-cleanup`
- RDP and `\\tsclient` shared-drive access to `MINI_AMD` are authorised for the audit and approved cleanup workflow.

## 2. Required Reading

Before beginning, read the current versions of:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- the core standards routed by `docs/reference/README.md`
- `docs/reference/Promotion Guide.md`
- `docs/reference/runbook_devops.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/singleton_lock.md`
- `docs/reference/runbook_diagnostics.md`
- root and applicable nested `SECURITY.md` files

For SQL and database work, treat `C:\K98-bot-SQL-Server` and the live `MINI_AMD` SQL metadata as the sources of truth. Do not infer attached databases, backup chains, file paths, job dependencies, or retention requirements from filenames alone.

## 3. Objective

Safely close the KingdomScanData4 Phase 5.2 programme after sustained successful production imports. Inventory and remove obsolete rehearsal databases, redundant backups, generated build/review workspaces, one-off launchers, test fixtures, stale Git branches/stashes, and other programme debris from the local machine and `MINI_AMD`, while retaining the canonical production evidence, current recovery capability, unrelated runtime data, and every file required by the follow-up to production PR #552.

Leave both repositories and the production machine in an explained, supportable state with a deletion receipt, before/after capacity evidence, clean Git status apart from intentional PR changes, and no effect on the live bot or `ROK_TRACKER`.

## 4. Background

- KingdomScanData4 Phase 5.2 production go-live completed on 2026-08-24.
- Fresh production Checkpoint C receipt SHA-256: `A57B827C6F533599E52882F8F2FFF93BA81BDE65FDA55D6830FDF53A83B8642E`.
- Guarded finalizer execution receipt SHA-256: `8BB6B10E829A587CFA43F4AC44689580F8178D33AA18C3AAB618C5541598A1E2`.
- Post-SQL recovery completion receipt SHA-256: `F23022EE4E2A06DF38B649BBF53E252C0B9558639000DEA405F29C45DCA47632`.
- The first fully fresh post-fix import used immutable identity `stats_2b8b7c14b46be2bdd16310ca8067c325.ready.csv`, imported 416 rows into both `KingdomScanData4` and `KingdomScanData5`, advanced the expected counter to 914, rebuilt both caches, completed `dbo.usp_update_stats`, and completed ProcConfig refresh without error.
- The operator now reports a week of numerous successful imports without error. This satisfies the stability prerequisite for cleanup.
- Production PR #552 (`Promote codex/kvk-post-pass4-provenance-safe-refresh`) merged on 2026-08-28. Local follow-up documentation changes from that delivery are not disposable cleanup debris and must be included in the PR created by this task.

### Protected PR #552 Follow-up Changes

Preserve exactly these existing local bot-repository changes before any Git cleanup:

1. `README-DEV.md` — 27-line post-delivery closeout addition.
2. Deletion of `docs/task_packs/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md` from the active task-pack folder.
3. Addition of `docs/task_packs/archive/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md`.

The archived file is materially updated relative to the PR #552 copy, not a byte-identical move: the observed comparison was 114 insertions and 38 deletions. Do not restore, overwrite, regenerate, discard, or classify it as disposable. These changes, this cleanup task pack, and its chat starter must be retained for the cleanup PR.

## 5. Scope

### In Scope

- Full read-only inventory of Phase 5.2-related artifacts on the local machine and `MINI_AMD`.
- Classification of every candidate as `RETAIN`, `COMMIT`, `ARCHIVE`, `QUARANTINE`, or `DELETE`.
- Cleanup of confirmed obsolete untracked files and directories in both repositories/worktrees.
- Cleanup of generated packages, extracted package duplicates, build directories, review workspaces, scan workspaces, temporary validation outputs, `__pycache__`, and obsolete one-off Phase 5.2 operator launchers after exact classification.
- Inventory and approved removal of obsolete rehearsal/test databases, detached database files, and their redundant backups.
- Backup-chain and retention review before deleting any `.bak`, `.trn`, `.dif`, `.mdf`, `.ndf`, or `.ldf` file.
- Inventory and approved cleanup of Phase 5.2 evidence copies while retaining one canonical closeout bundle and its hashes.
- Audit and cleanup of stale Git branches, worktrees, and stashes on `MINI_AMD` and locally.
- Preservation and PR inclusion of the protected PR #552 follow-up changes.
- Creation of a cleanup evidence manifest and before/after disk-capacity report.
- Creation of a focused mirror PR for tracked documentation, ignore-rule, or operational-tool changes that survive the audit.
- Production repository promotion only if the final tracked change genuinely needs production alignment; do not deploy or restart the bot merely for documentation-only cleanup.

### Out of Scope

- Any change to production bot behaviour, commands, SQL schema, stored procedures, tables, views, indexes, permissions, migrations, import contracts, cache formats, or scheduler behaviour.
- Dropping, restoring, replacing, renaming, detaching, or otherwise mutating `ROK_TRACKER`.
- Deleting system databases or SQL Server files belonging to an attached retained database.
- Deleting current production credentials, `.env` files, service-account files, `venv`, active logs, current cache/state files, bot locks, queue state, or current import/archive data.
- Deleting unrelated CrystalTech, KVK, GovernorOS, MGE, inventory, logs, diagnostics, or user data merely because it is untracked.
- Broad Git history rewriting, `git reset --hard`, or indiscriminate `git clean -fdx`.
- Deleting canonical production go-live receipts or the only remaining copy of any audit evidence.
- Creating replacement rehearsal databases to make cleanup evidence easier.
- Running full pytest against the live bot worktree.

## 6. Source Deferred Items

```md
### Deferred Optimisation
- Area: `KingdomScanData4 Phase 5.2 local and production operational artifacts`
- Type: cleanup
- Description: The completed programme left numerous untracked build/review directories, generated packages, one-off launchers, rehearsal fixtures, evidence copies, rehearsal databases, backups, and Git branch/stash state across the local machine and `MINI_AMD`.
- Suggested Fix: Perform a manifest-driven two-machine audit, preserve canonical evidence and PR-bound files, remove only approved obsolete items, and record exact before/after state and recoverability.
- Impact: high
- Risk: high
- Dependencies: Sustained successful production imports; live SQL metadata and backup-chain review; exact operator approval of the destructive manifest.
```

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required to separate audit, retention, destructive execution, Git/PR work, database work, and runtime safety. |
| `k98-discord-command-feature` | not applicable | No command, view, permission, interaction, or command-registration change is intended. |
| `k98-sql-validation` | use | Required for attached-database inventory, backup-chain validation, SQL Agent dependency checks, and safe database/backup removal. |
| `k98-test-selection` | use | Required to select documentation/tooling validation and safe dry-run tests without running full pytest on the live bot worktree. |
| `k98-deferred-optimisation-capture` | use | This is a cleanup batch; newly discovered unrelated debt must be captured without expanding deletion scope. |
| `k98-pr-review` | use | Required before handing off the cleanup mirror PR. |
| `k98-promotion-check` | use if production promotion is needed | Required only if tracked changes must be promoted to the private production repository or deployed. |
| `k98-security-review-routing` | use | Required to record separate bot and SQL repository decisions; do not start a standard or deep scan. |

### Security Review Decision

| Repository | Decision | Target | Expected setup / execution | Evidence |
|---|---|---|---|---|
| `K98-bot-mirror` | Changes review | final `origin/main..HEAD` cleanup branch | `Changes`, Deep off | Required if the PR contains an executable cleanup tool, `.gitignore`/configuration change, or any runtime-affecting file. If final diff proves documentation/archive-only, the routing skill may replace this with a precise documented skip naming every file. |
| `K98-bot-SQL-Server` | documented skip | final tracked SQL repository state | Not applicable | No tracked SQL/schema/tool change is planned. Direct live cleanup is governed by the approved manifest, SQL validation, readback, and cleanup receipt. If tracked SQL tooling is added, change this to a separate SQL Changes review with Deep off. |

No repository-wide Codebase scan and no Deep scan are authorised by this task pack.

## 8. Mandatory Workflow

### Phase 1 — Read-Only Audit And Protection

1. Confirm local and `MINI_AMD` machine identity, repository roots, current branches, remotes, HEADs, worktrees, status, stashes, running bot/worker processes, scheduled tasks, and free disk capacity.
2. Capture the protected PR #552 follow-up files and hashes in the audit manifest before any cleanup.
3. Inventory all candidate files/directories, databases, database files, backups, evidence bundles, branches, worktrees, and stashes.
4. Resolve ownership, origin, last modification, size, duplication, Git reachability, database attachment, backup-chain relevance, current process use, and evidence value.
5. Produce an exact proposed manifest with one row per file or safe directory root and one row per database/backup/stash/branch.
6. Stop for operator approval. Do not delete, drop, detach, overwrite, prune, stash-drop, branch-delete, stop the bot, restart services, or create the PR during Phase 1.

### Phase 2 — Approval And Execution Plan

1. Incorporate operator changes to the manifest.
2. State exact commands or scripts, execution order, rollback/recovery method, estimated space reclaimed, runtime impact, and whether a bot shutdown is genuinely required.
3. Resolve every `UNKNOWN` item. Unresolved items default to `RETAIN`.
4. Obtain explicit approval for the exact destructive manifest and execution batches.

### Phase 3 — Protected Git/PR Work

1. Preserve the dirty local bot working tree; do not reset or clean it.
2. Create the approved `codex/phase52-post-stabilisation-cleanup` branch from the correct mirror base while retaining the protected changes.
3. Include the PR #552 follow-up set, this task pack/chat starter, and only audit-approved tracked changes.
4. Do not add generated evidence, credentials, production logs, database backups, build workspaces, or broad machine-specific paths to Git.
5. Do not add broad ignore rules that could conceal future source/evidence files. Any `.gitignore` change must enumerate narrow, justified patterns and receive review.

### Phase 4 — Approved Cleanup

Execute in separately verifiable batches:

1. Local generated workspaces and duplicate packages.
2. Local obsolete launchers and temporary tooling.
3. `MINI_AMD` bot-worktree rehearsal/test artifacts.
4. Git worktree/branch/stash cleanup after content preservation and reachability proof.
5. Rehearsal/test database removal after exact SQL checks.
6. Redundant backup and detached-file removal after backup retention approval.
7. Optional evidence compaction/archive after the canonical bundle is verified.

After every batch, capture success/failure, remaining targets, disk capacity, Git state, SQL state where applicable, and rollback/recovery information. Stop on a material path, identity, permissions, lock, database, backup-chain, capacity, security, or runtime discrepancy.

### Phase 5 — Verification And Handoff

1. Prove `ROK_TRACKER` is online, unchanged in identity, and accessible.
2. Prove the bot process/scheduler remains healthy; if it was never stopped, state that explicitly.
3. Confirm no active import/offload/SQL transaction was interrupted.
4. Confirm both Git repositories contain only intended tracked/untracked state.
5. Verify every retained evidence artifact and PR-bound file still exists with its expected hash.
6. Produce the final cleanup receipt and before/after capacity report.
7. Run the selected local validation and PR review gates.
8. Open the mirror PR only after the retained file manifest is correct.

## 9. Audit Requirements

### 9.1 Evidence Manifest

Create machine-readable JSON or CSV plus a concise Markdown summary. Each candidate must record:

- machine and resolved absolute path/object name;
- item type;
- originating phase/task/PR when known;
- size and last-write UTC;
- Git tracked/untracked/ignored status where applicable;
- database attached/online state where applicable;
- backup type, database, first/last LSN, checkpoint/database-backup LSN, finish time and verification state where applicable;
- duplication/canonical-copy relationship;
- current process/job/scheduler reference;
- classification: `RETAIN`, `COMMIT`, `ARCHIVE`, `QUARANTINE`, or `DELETE`;
- reason;
- recovery method;
- approval state;
- execution result and UTC timestamp.

Hash small scripts, manifests, receipts, task packs, and final evidence. For multi-gigabyte backup/database files, metadata and SQL backup-header evidence are sufficient unless hashing is specifically useful.

### 9.2 Local SQL Repository Audit

Start with the current untracked inventory and expand it rather than assuming it is complete. Known families include:

- `.phase52_*_build/`, `.phase52_*_review/`, `.phase52_*_security_review/`, and `.phase52_*_security_scan/`;
- `_phase52_packages/`, `_phase52_scan_work/`, `_phase52_scan_workspaces/`, `_phase52_security_scans/`, `_phase52_validation/`, and `_phase52_verify_extract/`;
- `.codex-isolated/` and `__pycache__/`;
- Phase 5.2 generated ZIPs and their extracted duplicate directories;
- `Check-*`, `Complete-*`, `Diagnose-*`, `Export-*`, `Repair-*`, and `Run-Phase52-*` one-off launchers;
- `tools/`, which must be inspected and must not be deleted merely because it is untracked.

Group only when every descendant has the same provenance and disposition. Before recursive removal, resolve and record every absolute target root and prove it remains inside `C:\K98-bot-SQL-Server` or another explicitly approved cleanup root.

### 9.3 Local Bot Repository Audit

- Preserve the protected PR #552 follow-up changes.
- Inventory all other tracked, untracked, ignored, stashed, and worktree state.
- Distinguish source/task-pack files from runtime output, smoke artifacts, logs, virtual environments, credentials, and caches.
- Do not use `git clean` as the inventory mechanism or deletion mechanism.

### 9.4 `MINI_AMD` Bot Worktree Audit

Use RDP/shared access and capture complete `git status --porcelain=v2 --untracked-files=all`, ignored-state inventory where useful, branch/remotes/HEAD, worktree list, stash list, and relevant process/scheduled-task state.

Known candidates from the supplied log include:

- `Invoke-Phase52CheckpointBReadOnlyProbe.ps1`;
- `Test-Phase52DriveDSuitability.ps1`;
- `downloads_test/` rehearsal SQL, PowerShell tools, manifests, and evidence;
- `downloads_test_phase5_rehearsal/` fixtures and evidence.

Known item that defaults to `RETAIN` pending separate evidence:

- `data/crystaltech_archives/arch_20260825T144732Z.crystaltech_progress.json` — appears unrelated to Phase 5.2 and may be a legitimate runtime archive.

Also inspect, without assuming disposal:

- `C:\K98_release_evidence\kingdomscandata4\...`;
- `C:\sql_backup\ROK_TRACKER\...` and any other SQL backup roots;
- Phase 5.2 payload copies under production evidence directories;
- old `.codex_pytest_audit.log`, diagnostic exports, download staging, import Ready/Archive state, lock/marker files, and offload registry entries;
- scheduled tasks or startup helpers created or modified during the go-live.

Never delete live `downloads`, `data`, `logs`, credentials, environment files, `venv`, watchdog/bot locks, current queue state, or import archives solely based on age or untracked status.

### 9.5 Git Branch, Worktree, And Stash Audit

For each local and `MINI_AMD` repository:

- record current branch/HEAD/remotes and `git worktree list --porcelain`;
- list local and remote branches with upstream/merged status;
- list stashes with date and commit identity;
- inspect each stash with stat, name-status, and patch, including untracked content where present;
- compare stash/branch content to merged mirror and production commits;
- identify whether any content is unique, already merged, superseded, or required by the protected PR #552 follow-up;
- export a patch/bundle or copy unique content to the canonical evidence location before dropping a stash or deleting a branch;
- retain the stash commit ID and exported artifact hash in the cleanup receipt.

Do not delete `main`, the current branch, an unmerged branch, a branch containing unique commits, or any stash until the manifest proves its content is preserved or redundant. Do not rewrite history.

### 9.6 Database Audit

Query live SQL metadata for all databases and record:

- exact name, database ID, state, recovery model, creation date, owner, compatibility level, and source database ID;
- physical data/log file paths and sizes from `sys.master_files`;
- active sessions, requests, open transactions, locks, SQL Agent/job-step references, synonyms, linked-server dependencies, and backup recency;
- Phase 5.2 migration-history state and whether the database is a rehearsal/test clone;
- whether any bot config, scheduled task, script, connection string, or evidence manifest references it.

Never classify by name alone. Known naming families to investigate include `ROK_TRACKER_BACKUP_TEST_KS4*`, `*_PHASE52*`, `*_REAPPLY*`, `*_ROLLBACK*`, `*_FORWARD*`, `*_FINALIZER*`, and `*_RECOVERY*`. The exact live `sys.databases` result is authoritative.

Before proposing `DROP DATABASE`, prove all of the following:

- it is not `ROK_TRACKER` or a system database;
- it is an obsolete Phase 5.2 rehearsal/test database;
- it has no active request, transaction, job, user, or runtime dependency;
- its evidence value is preserved;
- its required backup/restore evidence is preserved or deliberately retired;
- the associated physical files are identified;
- the exact database name is approved.

### 9.7 Backup And Database-File Audit

Inventory SQL backup history from `msdb` and filesystem metadata together. For each candidate:

- identify database, type, dates, copy-only flag, first/last LSN, database-backup LSN, checkpoint LSN, family/device path, size and verification history;
- determine whether it participates in the current production recovery chain;
- identify whether it is the only remaining backup for a rehearsal outcome or rollback proof;
- run safe header/verify checks where required before retention/deletion decisions;
- retain the current production backup set required by the operator's normal retention and disaster-recovery policy.

The known `ROK_TRACKER_KS4_PHASE2_PRECHANGE_86A94B02CF604B968F97E55B8EB5B01B.bak` is a candidate for review, not automatic deletion. No production full/differential/log backup may be deleted until its recovery-chain role is explicitly resolved.

After an approved database drop, separately confirm whether its `.mdf`/`.ndf`/`.ldf` files remain and remove only the exact orphaned paths included in the manifest. Never recursively delete a database-file directory.

### 9.8 Evidence Retention

Retain at minimum one canonical Phase 5.2 closeout bundle containing:

- production read-only preflight and fresh-backup receipts;
- final filesystem ACL evidence;
- migration success/failure history necessary to explain the final state;
- the accepted fresh Checkpoint C receipt and SHA-256;
- guarded finalizer and post-finalization evidence;
- the post-SQL recovery completion receipt;
- successful fresh-import evidence and the week-stability operator attestation;
- frozen heads/PR identifiers and final production revisions;
- database/backup cleanup manifest and final receipt.

Redundant build directories, duplicate extracted packages, failed-attempt copies, and superseded payload copies may be proposed for deletion only after the canonical bundle is complete and readable. Prefer archiving/compressing unique evidence over deleting the only copy.

## 10. Classification Rules

| Classification | Meaning |
|---|---|
| `RETAIN` | Required production/runtime data, canonical evidence, current recovery capability, unrelated data, or unresolved ownership. |
| `COMMIT` | Intended tracked source/docs/tooling, including the protected PR #552 follow-up set and this pack/starter. |
| `ARCHIVE` | Unique historical evidence worth preserving outside active worktrees. |
| `QUARANTINE` | Candidate believed obsolete but retained temporarily because provenance or recovery confidence is incomplete. |
| `DELETE` | Proven obsolete, redundant, unreferenced, approved, and recoverable or intentionally irrecoverable. |

Default rules:

- Unknown means `RETAIN`, never `DELETE`.
- Untracked does not mean disposable.
- Old does not mean disposable.
- A matching filename does not prove identical content.
- A database-looking backup filename does not prove a valid or redundant backup.
- A merged PR does not prove every local branch/stash file is represented in the merge.

## 11. Destructive Execution Requirements

- Use exact absolute paths and `-LiteralPath`; do not pass unresolved environment variables, globs, repository roots, drive roots, or broad parent directories to recursive removal.
- Verify resolved targets are within the intended cleanup roots immediately before execution.
- Keep one shell end-to-end for discovery and deletion; on Windows use native PowerShell filesystem operations.
- Prefer quarantine or recycle-bin movement when practical. State when deletion is immediate and unrecoverable.
- Do not combine database drop, backup deletion, stash drop, branch deletion, and filesystem deletion into one opaque script/run.
- Require a separate result/receipt for each destructive batch.
- Do not stop or restart the bot unless an approved target is locked/in use and shutdown is materially required. If shutdown becomes necessary, stop and obtain explicit approval with the expected downtime and restart verification.
- Do not interrupt an import, offload, SQL request, backup, or scheduled maintenance operation.
- Do not create replacement databases to resolve evidence-wrapper discrepancies.
- Stop on a material state, identity, integrity, permissions, lock, capacity, security, backup-chain, SQL, scheduler, or runtime discrepancy.

## 12. Architecture Targets

| Concern | Target |
|---|---|
| Audit/cleanup orchestration, if retained | `scripts/` in the appropriate repository |
| Machine-readable cleanup manifest | external canonical evidence directory; do not commit production paths/data |
| Operator-facing closeout documentation | `docs/task_packs/` then `docs/task_packs/archive/` at completion |
| Narrow generated-artifact ignore rules, if justified | repository `.gitignore` |
| SQL schema | no change planned |
| Bot runtime code | no change planned |
| Tests | focused tooling tests only if reusable cleanup tooling is added |

## 13. Likely Files

### Review

- Local SQL repository untracked inventory listed in the supplied task context.
- Local bot repository current dirty state and all untracked/ignored items.
- `MINI_AMD` bot worktree untracked inventory listed in the supplied task context.
- `C:\K98_release_evidence\kingdomscandata4\...`
- `C:\sql_backup\ROK_TRACKER\...`
- SQL `sys.databases`, `sys.master_files`, `msdb` backup history, SQL Agent job steps, sessions, requests and transactions.
- Local and `MINI_AMD` Git branches, worktrees, reflogs as needed, and stashes.

### Preserve And Include In PR

- `README-DEV.md`
- deletion of `docs/task_packs/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md`
- `docs/task_packs/archive/Codex Task Pack - KVK Post-Pass-4 Healed Troops and Provenance-Safe Stats Refresh.md`
- `docs/task_packs/Codex Task Pack - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup.md`
- `docs/task_packs/Codex Chat Starter - KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup.md`

### Modify Or Create Only If Audit Justifies It

- `.gitignore` with narrow patterns for reproducible transient artifacts.
- A narrowly named `scripts/` cleanup or audit tool plus tests/dry-run behavior.
- cleanup receipt and evidence outside Git.

### SQL Changes

- None planned. Database and backup removal are approved operational cleanup, not schema evolution.

## 14. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Phase 5.2 generated build/review workspaces | fix now after manifest approval | Core cleanup objective and generally recoverable from Git/package sources. |
| Duplicate packages and extracted copies | fix now after hash/provenance check | Reclaim space while retaining the canonical source/evidence copy. |
| One-off local and MINI_AMD launchers | fix now after reference check | Remove obsolete operator clutter without removing current recovery tooling still needed. |
| Rehearsal/test databases and redundant backups | fix now after SQL/backup approval | High-value capacity cleanup with high destructive risk. |
| Stale branches/worktrees/stashes | fix now after reachability/content preservation | Explicit operator request; must not lose unique work. |
| PR #552 closeout files | commit | Required follow-up and explicitly protected by the operator. |
| Unrelated CrystalTech runtime archive | not applicable / retain | Not established as Phase 5.2 debris. |
| Broad ignore rules | defer unless narrow evidence supports them | Avoid hiding future source or evidence files. |
| General backup-retention redesign | defer | Separate operational policy task unless required to classify these exact backups. |
| Runtime/code refactor discovered during cleanup | defer | No bot or SQL behavior change is authorised here. |

## 15. Testing Requirements

Use `k98-test-selection` after the final tracked file list is known.

### Audit/cleanup validation

- Validate audit scripts in read-only/dry-run mode first.
- If a reusable deletion tool is created, test it only against temporary fixture directories/databases, including containment rejection, unknown-item retention, exact-path behavior, partial failure, idempotent rerun, and receipt generation.
- Never test destructive behavior against `ROK_TRACKER`, the live bot worktree, or current backup chain.
- Validate JSON/CSV/Markdown manifests parse and agree on counts/bytes.
- Compare before/after Git status, SQL database list, filesystem list, capacity, and retained hashes.

### Bot repository baseline

For a docs-only PR, run or justify:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
git diff --check
```

Runtime pytest, smoke imports, command registration, dependency installation, bot restart, and deployment are not required for a documentation/archive-only diff. If executable tooling, config, or runtime code is added, expand validation proportionately and run the selected focused tests locally—not full pytest on the live bot worktree.

### SQL validation

- Confirm `ROK_TRACKER` online and unchanged before and after cleanup.
- Confirm final `sys.databases`/`sys.master_files` matches the approved retained list.
- Confirm no active request, open transaction, job dependency, or bot connection targets a removed database.
- Confirm retained production backup chain and canonical evidence remain available.
- No SQL schema migration or repository validation is required unless tracked SQL files change.

## 16. Acceptance Criteria

- [ ] Phase 1 completed read-only and produced exact machine/file/database/backup/Git manifests.
- [ ] Protected PR #552 follow-up files were hashed and preserved before cleanup.
- [ ] Every candidate received one explicit classification and reason.
- [ ] Every destructive target received exact operator approval.
- [ ] No unknown/unresolved item was deleted.
- [ ] `ROK_TRACKER`, system databases, production backup requirements, bot runtime data, credentials, logs/state, and unrelated artifacts were retained.
- [ ] Canonical Phase 5.2 evidence and receipt hashes were retained and readable.
- [ ] Approved rehearsal/test databases were removed and read back as absent.
- [ ] Approved redundant backups/orphaned database files were removed and read back as absent.
- [ ] Approved local and `MINI_AMD` artifacts were removed with exact-path containment checks.
- [ ] Stashes/branches/worktrees were removed only after unique-content and reachability checks plus preservation evidence.
- [ ] Before/after capacity and cleanup receipts were produced.
- [ ] Local SQL repository has no unintended tracked or untracked Phase 5.2 debris.
- [ ] `MINI_AMD` bot worktree has no unintended Phase 5.2 debris and retains unrelated runtime data.
- [ ] Protected PR #552 follow-up changes, this pack, and the chat starter are included in the cleanup PR.
- [ ] Security routing was finalized separately for bot and SQL repositories.
- [ ] Required local validators and PR review passed or precise skips were recorded.
- [ ] Bot remained healthy, or any approved shutdown/restart was verified through normal startup evidence.

## 17. Required Delivery Output

1. Executive summary and final verdict.
2. Local machine before/after inventory.
3. `MINI_AMD` before/after inventory.
4. Protected/committed file manifest.
5. Retained canonical evidence manifest and hashes.
6. Deleted/quarantined/archived file manifest with reclaimed bytes.
7. Database before/after manifest.
8. Backup and database-file before/after manifest.
9. Git branch/worktree/stash cleanup manifest.
10. Scheduled-task/process/runtime verification.
11. SQL validation and backup-chain evidence.
12. Test/validator results.
13. Security review decision and evidence per repository.
14. Mirror PR summary and URL.
15. Production alignment/deployment decision.
16. Residual risks and deferred optimisations.
17. Recovery instructions for any quarantined or archived item.

## 18. PR Summary Template

```md
## Summary

- Close out KingdomScanData4 Phase 5.2 after sustained successful production imports.
- Preserve and commit the post-PR #552 delivery documentation.
- Record the approved two-machine cleanup and retained canonical evidence.

## Changes

- Archive the completed KVK post-Pass-4 task pack and update `README-DEV.md`.
- Add/archive the Phase 5.2 post-stabilisation cleanup pack and evidence summary.
- Add only narrowly justified ignore rules or reusable audit tooling, if any.

## Tests

- `[record the validators and focused tooling tests actually run]`
- Runtime tests skipped if documentation/archive-only: no bot behavior changed.

## Security Review

- Bot decision: `[record Changes review with Deep off or the precise documentation-only skip]`
- Bot target/evidence: `[record origin/main..HEAD or the named files and skip reason]`
- SQL decision: `documented skip` unless tracked SQL tooling changed
- SQL evidence: no schema/procedure/runtime SQL repository diff; live cleanup validated separately

## Cleanup Evidence

- Manifest: `[record path and SHA-256]`
- Reclaimed capacity: `[record local bytes and MINI_AMD bytes]`
- Removed databases/backups: `[record approved identifiers]`
- Retained canonical evidence: `[record path and hash summary]`

## Deferred Optimisations

- `[record none or structured items]`

## Risk / Rollback

- Cleanup used exact approved targets and retained recovery evidence.
- `[record quarantine/archive recovery instructions]`
```

## Appendix A — First Response Required From The New Task

The new task's first substantive response must:

1. Confirm it has read this task pack and applicable current standards.
2. State that Phase 1 is read-only and that no destructive action is yet authorised.
3. Identify the local and `MINI_AMD` access paths it will use.
4. Repeat the protected PR #552 follow-up file set.
5. Present the proposed audit commands/queries and evidence output location.
6. Confirm that `ROK_TRACKER`, system databases, current production backup requirements, bot runtime state, credentials, canonical evidence, and unrelated CrystalTech data default to retain.
7. Begin the read-only audit efficiently.
8. Stop after delivering the exact proposed manifest and approval request.
