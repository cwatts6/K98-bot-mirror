# S11 — Controlled Release and Acceptance

## Authorization and first step

Prepared after S10E merged/local closeout, 2026-09-15. **Initial review/scope only.**
The operator authorized documentation closeout, archiving completed instructions and preparing this
handoff. This is not approval to implement S11, execute a fixture, install SQL, connect provider
clients, pull/restart the bot machine, activate routing, publish Git changes or create a new task.
Use the [S10E closeout](../reference/kvk_source_migration/s10e_closeout_and_s11_handoff.md) and [S7 exact contracts/manifests](../reference/kvk_source_migration/integration_implementation_manifests.md).
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`. These are comparison anchors, never reset instructions.
**No changes have been pulled to the bot machine.** Recheck both repositories and preserve pending work.

## Objective and scope boundary

Prepare an evidence-based release/acceptance plan for the integrated S8–S10 behavior. Preserve
accepted predecessor decisions and measurements. S7 proposes eight documentation paths below;
start there and add the exact mandatory carry-forward manifest. Do not treat S11 as blanket runtime
implementation approval. Inspect actual factories/callers, trusted termination/reconciliation and
retirement-recovery producers, worker registration, legacy adapters and all participating processes.
Distinguish already authored behavior, disabled composition, missing implementation and unknown
installation/runtime evidence. Any genuine code/SQL gap needs its own bounded manifest and approval;
do not manufacture code to carry documentation or silently broaden S11.

## Required reading

Read current AGENTS, README-DEV, reference index and its five core standards. Read S7 integration
contracts/manifests, architecture/EndScanID amendment, S10A/B/C/D/E closeouts and authoritative SQL
in `C:/K98-bot-SQL-Server`. Read release evidence/rollback, local SQL, startup/shutdown/diagnostics,
source consumer matrix and retained S6/S8 evidence as relevant. Historical status blocks are dated
history. Source merges and CI do not attest deployed schema, running code or provider state.

## Starting eight-path S7 documentation proposal

| Action | Exact Bot path |
|---|---|
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` |
| Modify | `docs/reference/local_sql_development.md` |
| Modify | `README-DEV.md` |
| Modify | `docs/reference/README.md` |

Add every exact pending Bot documentation identity in the [closeout manifest](../reference/kvk_source_migration/s10e_closeout_and_s11_handoff.md),
including this pack/starter, both closeouts, S10E source deletions and archive destinations.

## Review deliverables before approval

1. Exact Bot/SQL branch, base, file/index and deployment inventory; preserve recovered evidence.
2. Actual command → service → worker → DAL/provider ownership map, including every producer/consumer.
3. SQL/static versus disposable transaction versus provider/Discord versus bot-machine evidence matrix.
4. Exact proposed target database/account/file/process identities, versions and operations; backup and
   actual restore plan, isolation, allowed reads/writes, failure handling and retained-data exclusions.
   Do not choose retained S6/S8 databases/files as new test targets or expose credentials in documents.
5. Composition/installation dependency order and explicit disabled defaults. Verify SQL C/D/E schema,
   immutable registration, compatible shared writers and trustworthy proof producers before admission.
6. Focused evidence plan for newly affected interruption/restart, lost acknowledgements, nested recovery,
   fairness/capacity and rollover. Reuse retained predecessor results; rerun only newly affected cases
   after exact authorization. Separate offline tests, actual SQL transactions, provider reads/writes,
   Discord/operator smoke and deployment evidence. Preserve S6-OPS01/PERF01/CAP01 until explicit acceptance.
7. Exact change/test manifests, security routing, rollback, stop conditions and approval checkpoints.
   Return scope, risks, files, evidence matrix, tests and implementation/operation plan; stop for approval.

## Invariants and acceptance boundaries

- Fixed season source; independent consumers; supplied overall/B0; authoritative aggregates/DKP;
  exact endpoint chain (11-10 / 12-10 / final 13-10 / authorized 14-10), sealed inputs/CAS,
  matched UpdateID and explicit counterpart attestation. No mixed source or silent legacy fallback.
- Immutable running A; eligible pending coalescing; daily ordering/history and account fairness;
  registration-aware intent lifecycle, one-period compaction and complete S10C output/config/header/
  provenance. Preserve durable spool/owner evidence, nested owner tokens, UPDATE_ALL2 ownership and
  server-UTC SDK pacing. Shutdown stops admission and drains owned delivery; uncertainty retains claims.
- Exact file/index identity, owner/fence/version CAS, monotonic epochs, append-only assignments and
  dispositions, byte-exact receipts, P/Q/R capacity, 9,000,000-cell parts and 8/16 pool bounds.
- No new top-level command. Existing grouped export/status/reconcile/rebuild and preview/confirm
  rollover retain fresh authority, immutable accepted inputs/registration, zero-provider confirmed
  no-op, explicit RepairID, read-only status and durable/expiring confirmation.
- Rollover closes admission, drains/reconciles, proves old-writer termination, privately clears/reads
  back before audited reuse/retirement. Interrupted in-season retirement uses the explicit journal-
  based recovery path, nested versioned owner, no-delayed-effects proof, read-before-clear and fresh
  publication probe after owner revocation. Uncertain is reconciliation, never blind retry.
- No lease-age/job-state release, guessed receipt mapping, uncertain/quarantined reuse, mutable
  generation relabeling or SQL transaction over waits/provider I/O. Preserve both uncertain publications
  e19c89ac-7977-5f28-ae4c-031807cd1728 and 54a2480a-26fb-5bad-a3f5-9321525a731c and every retained file/database.
- S8A six scripts/VERIFYONLY, S8B 50 cases/actual restore versus offline history, and S8C seven local
  checks are distinct. S10C/D/E authoring/static evidence is not installation or provider proof.

## Approval sequence and rollback

Initial S11 review → operator-approved exact implementation/docs scope if needed → offline gates and
Changes review for each actual runtime diff → exact G4 environment/operations authorization → bounded
execution and evidence → separate operator G5 acceptance. A PR merge, local pull or SourceRouting.Enabled
alone is not activation. Do not infer execution approval from this pack or earlier slice approvals.

Rollback closes new admission and drains/reconciles owners; preserve immutable accepted facts,
receipts, dispositions, pending/uncertain claims and retained data. Use reviewed forward SQL fixes;
never drop populated history or release ownership by age. Pin any allowed publication rollback and
serving version explicitly. No destructive reset/clean commands or automatic bot-machine operation.

## Tests and security routing

For preparation-only Markdown, run architecture/deferred/security-routing validators, exact-path test
selection, diff/relative-link and identity checks. Document skipping runtime pytest/SQL/provider work
because no executable changes occur. For an approved runtime patch select relevant deterministic
regressions and the isolated full-suite/log-noise gate. Use **Changes, Deep off**, exact immutable Bot
base/head/patch; separately assess any actual SQL delta. No inferred Codebase/Deep audit.

## Mandatory documentation delivery

The eventual authorized Bot PR MUST carry EVERY pending Bot path in the closeout manifest, including
all status/reference updates, this pack/starter, S10D and S10E closeouts, both S10E archive move sides
and all later task-produced docs. Reconcile fresh staged/unstaged/untracked/deleted files before
staging and again against GitHub Files changed. Verify `filename` AND `previous_filename`, exact
content at head/merge and explicit absent-at-base proof. Counts alone never prove delivery.

No standalone docs PR, mixed repositories or manufactured runtime work. If S11 stays preparation-only
and no qualifying PR is authorized, retain the whole manifest for the next genuine authorized Bot
implementation PR; do not drop docs or request renewed grouping approval. SQL `docs/SQL_DELIVERY_LOG.md`
and `migrations/README.md` stay separate for the next actual authorized SQL implementation PR. If no SQL
delta exists, retain them pending. Preserve all original recovery ZIPs/hashes and new closeout evidence.
