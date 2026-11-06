# S10D closeout and S10E documentation handoff

## Current delivery and next phase — 2026-09-25

S11 Bot mirror #281, SQL #89 and production Bot #588 are merged. See the
[source closeout and exact manifest](s11_closeout_and_g4_handoff.md) for delivered behavior, review
corrections, source pins and the mirror publication repair follow-up. Production deployment,
SQL installation, provider behavior and G5 acceptance are not established by these merges.

Next: **G4 plan development only**, using the [new task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md) and
[chat starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20G4%20Release%20Planning%20Controlled%20Rollout%20and%20G5%20Acceptance.md). Controlled rollout executes only specifically approved
operations; G5 remains operator-owned. Earlier dated checkpoints below retain their original
scope/status as historical evidence, including headings used by existing links. They do not
reopen implementation or authorize live operations. Preserve S6/S8 gates, uncertainties and data.

## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## Current delivery and next step — 2026-09-15

**S10D SQL authoring/review/repository delivery is complete.** [SQL PR #87](https://github.com/cwatts6/K98-bot-SQL-Server/pull/87)
merged at **10:57:04 UTC** as `80353a6280e523f30c27e724f71e7b47dadadd16`; final head
`0eb5494976627bcb6efaea40e11adcb0cf231344`. Local SQL main/origin main match that merge.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. The operator confirms **no changes have been pulled
to the bot machine**. No SQL installation, execution, provider/Discord operation, deployment or
activation follows from this source merge. S10C SQL installation remains unproven too.

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
No implementation, publication, predecessor rerun or automatic task is authorized by this closeout.

## Exact delivered SQL content

Every GitHub filename AND previous_filename was checked: exactly the eleven approved paths below,
no renamed entries. Each blob matches final PR head, merge commit, local main and origin/main.
The resolved migration creation date/free ordinal was checked before authoring; it is never renamed.
Both pending SQL documents were included. No Bot PR/runtime delta was manufactured for S10D.

| Action | Exact SQL path | Delivered blob |
|---|---|---|
| added | `deploy/Test-OutputPoolRolloverContracts.ps1` | `085eb6d6264fdb5d5e3ebfb5441abbfcfa9ecef1` |
| modified | `docs/SQL_DELIVERY_LOG.md` | `b5563baf1dd8a5c7f0c292317cdda2b0f865c42b` |
| added | `migrations/20260915_001_kvk_output_pool_rollover.sql` | `2870d6903e1f2cd9ac8e1c31897224fe3676c416` |
| modified | `migrations/README.md` | `3410ec7934da61ca89375344065d2048d700f6ff` |
| added | `sql_schema/KVK.SourceOutputDisposition.Table.sql` | `ca69ab1055e4492b58927849278887b5090bd4ab` |
| added | `sql_schema/KVK.SourceOutputFile.Table.sql` | `6a03de5dc838b66cd4a9beed60480bbfc3125c62` |
| added | `sql_schema/KVK.SourceOutputPool.Table.sql` | `6074b4baad7ae085e955f26c467962125d09477d` |
| added | `sql_schema/KVK.SourceOutputSlot.Table.sql` | `84ea5a8a7691afa8b91cefbe9d626f56ac1acd11` |
| modified | `sql_schema/dbo.ExportAttempt.Table.sql` | `104d906c2b8c65b7fd77d67de982d3ec02b44ebb` |
| modified | `sql_schema/dbo.ExportAttemptPart.Table.sql` | `3898eeab2ae011b07a9e854e68821e0e3f20cddd` |
| added | `validation/kvk_source/s10_output_pool_rollover.sql` | `265c36e3513612aaf7c992d67ae84017f994b541` |


## Delivered contract and evidence limits

Four new tables separate global typed physical-file identity, registered pools, current slots and
retained disposition history. Scope-correct FKs bind account/season/job/attempt/part/resource membership
and explicit historical deliveries; two additive attempt reference keys enable exact references.
Current pool epoch/season is not the historical event FK target. Pool/slot bounds remain 8/16.
S10D establishes static shape/identity/scope only. S10E owns temporal owner/fence/version CAS,
monotonic lifecycle, append-only writer APIs, complete P/Q/R/cell/receipt preflight and provider proof.
Privileged DML is not made append-only by CHECKs. Receipt bytes and uncertain claims stay intact.
No metadata sealing of observed drift, backfill, receipt guessing, lease/job-state release or rollback
that drops populated history. Constant additive DDL follows exact inherited guards; forward fix only.

Final offline results: 463 contract assertions, 101 TSQL parse inputs and 11 rejected mutated variants.
SQL repository validation passed in isolated source; 15 warnings belonged to older migrations.
Ninety fixture cases/seven modes remain authored and unexecuted. No backup/actual-restore or live
transaction result is inferred. Initial review corrected three expected-index targets to temporary
tables and strengthened checker regression guards. Corrected Changes scan
`eddcf7bb-ba2f-48c2-a995-b4371f9ce3ac`, Deep off, completed with zero findings and full source coverage.
Initial scan `a582a43f-c6df-4ec3-98be-2dc100f8fa0a` remains retained history, not final-target evidence.
Reviewed migration SHA256 `fd5344ec9d1080fe7ee824801ccb4f03910b71d83e85c6e42d48cbc90f2f0852`;
checker `e34fd0498c601e0d40e3683844d41d72e2621c436084a5c27a77b917521cb9b1`.

CI first misread Bot carry-forward paths as SQL-local paths. Documentation-only commit 0eb5494
separated Bot directory/relative path; all 50 identities/actions remained exact. Both replacement
SQL validation runs 34960113322 and34960108335 passed, including advisory lint. Copilot generated
zero inline comments and COMMENTED rather than formally approved; operator confirmed human reviews
complete. GitHub CLEAN/MERGEABLE and zero review threads were verified before merge. Later evidence/
CI documentation edits had a precise documentation-only security skip; implementation hashes stayed fixed.

## Recovery of overwritten pending Bot documentation

At this closeout entry, Bot main was clean at its unchanged base and the previously pending 50
identities were absent/reverted. The operator reported they were probably overwritten accidentally.
The original closeout generator and three documentation patches were recovered from retained local
task artifacts, replayed only into a temporary copy, and checked against the pre-reset per-file SHA256
manifest. **All 50 original path/action/content identities matched exactly before restoration.**
The recovered S10C closeout SHA256 was
`a8e1bdd9ac5646eb33ea37252bd487741217bb015ae151a268ed8570a40e6514`.
A recovery archive retains those exact earlier bytes before this new closeout updates their status:
C:/Users/cwatt/AppData/Local/Temp/k98-s10d-implementation-20260915/recovery/recovered-bot-docs-before-s10d-closeout.zip.
No retained databases, provider files or runtime code were restored, changed or deleted.
Current docs below intentionally advance status from those recovered bytes; do not compare their
new hashes to old hashes and misclassify the authored closeout changes as loss.

## Archive identity proof

S10C tracked source deletions and destinations are still pending, with source blobs at both recorded
Bot/production bases: starter `0393a3f54067a37f587a69051f5450bae2564246`, pack
`58f0bd559488e34fdcf60cf9c50ba415455d3951`. Both S10C archive destinations were absent at those bases.
S10D active pack/starter were never committed at either base. Their two archive sources therefore
cannot appear as Git deletions/previous_filename in a future PR. Preserve this explicit absence proof
and the recovered source-byte hashes; require both archive destinations in S10E. No invented rename.

| Source absent at Bot/production base | Required archived destination | Source SHA256 before move |
|---|---|---|
| `docs/task_packs/Codex Chat Starter - KVK Source Migration S10D Output Pool and Rollover SQL Foundation.md` | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10D Output Pool and Rollover SQL Foundation.md` | `01f72d880fefd936ed7a874a649f743df08fe6d7130110cb9a27b3ea7c6164d6` |
| `docs/task_packs/Codex Task Pack - KVK Source Migration S10D Output Pool and Rollover SQL Foundation.md` | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10D Output Pool and Rollover SQL Foundation.md` | `323461fc9327e2c97978c870021e73a9b2e88274303cf617b897b296809a7127` |

Only completed S10D pack/starter moved in this closeout. S10C moves were restored exactly first.
All retained contracts, closeouts, runbooks, S6/S8 evidence, databases and files remain available.

## Exact pending Bot documentation manifest

Exactly **54 pending Git path identities** at this closeout; every row must be reconciled individually.

| Action | Exact Bot path | Delivery |
|---|---|---|
| Modify | `README-DEV.md` | S10E Bot implementation PR |
| Modify | `docs/reference/ENV_REFERENCE.md` | S10E Bot implementation PR |
| Modify | `docs/reference/README.md` | S10E Bot implementation PR |
| Modify | `docs/reference/canonical_command_reference.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md` | S10E Bot implementation PR |
| Modify | `docs/reference/local_sql_development.md` | S10E Bot implementation PR |
| Modify | `docs/reference/runbook_diagnostics.md` | S10E Bot implementation PR |
| Modify | `docs/reference/runbook_shutdown.md` | S10E Bot implementation PR |
| Modify | `docs/reference/runbook_startup.md` | S10E Bot implementation PR |
| Delete (S10C archive source) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10C Legacy and Scan Export Adapters.md` | S10E Bot implementation PR |
| Delete (S10C archive source) | `docs/task_packs/Codex Task Pack - KVK Source Migration S10C Legacy and Scan Export Adapters.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/README.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10E Bot implementation PR |
| Modify | `docs/task_packs/archive/README.md` | S10E Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s10c_closeout_and_s10d_handoff.md` | S10E Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s10d_closeout_and_s10e_handoff.md` | S10E Bot implementation PR |
| Create | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10E Export Operator UX and Rollover.md` | S10E Bot implementation PR |
| Create | `docs/task_packs/Codex Task Pack - KVK Source Migration S10E Export Operator UX and Rollover.md` | S10E Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10C Legacy and Scan Export Adapters.md` | S10E Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10D Output Pool and Rollover SQL Foundation.md` | S10E Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10C Legacy and Scan Export Adapters.md` | S10E Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10D Output Pool and Rollover SQL Foundation.md` | S10E Bot implementation PR |

This manifest is mandatory in the eventual authorized S10E Bot implementation PR, together with
any new implementation/test/documentation paths approved during scope. Verify every filename AND
previous_filename, or exact merged/content/absent-at-base proof at head, merge and promotion.
Counts alone do not establish delivery. Do not reopen accepted grouping, create a standalone docs
PR, combine repositories or create unrelated runtime work just to deliver documentation.

## Separate pending SQL documentation

| Action | SQL path | Delivery |
|---|---|---|
| Modify | `docs/SQL_DELIVERY_LOG.md` | Next genuine authorized SQL implementation PR |
| Modify | `migrations/README.md` | Next genuine authorized SQL implementation PR |

These new merge/closeout edits are separate from the versions already delivered in #87. S10E is
Bot scope by default; inspect any actual SQL gap before approving another SQL target. If it needs
one, carry both docs in that SQL PR. Otherwise retain them for the next actual SQL implementation.
Never copy SQL docs into the Bot PR or open a standalone docs PR. No SQL delta is manufactured.

## Retained invariants and next gates

The S10E pack retains fixed source/independent consumers, supplied overall/B0, authoritative
aggregate/DKP, exact endpoint chain, sealed inputs/CAS and matched UpdateID/counterpart attestation.
Preserve immutable running A, eligible pending-only coalescing, daily order/history, account fairness,
registration-aware intent lifecycle and one-period compaction. Preserve S10C immutable complete
outputs/config/header/provenance, durable spool/owner evidence, nested owners, UPDATE_ALL2 ownership,
server-UTC SDK pacing and uncertainty retention. Shutdown stops admission and drains owned delivery.
No SQL transaction over waits/provider requests, mutable-generation relabeling or lease/job-state release.
Rollover requires closing/drain/reconcile, terminated-old-writer proof, private ACL/complete clear/
readback and audited retirement. Preserve 9,000,000-cell ceiling and P/Q/R with 8/16 bounds.

S6-OPS01/PERF01/CAP01 remain open; preserve uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c` plus all retained data.
S8A six scripts/VERIFYONLY, S8B 50 cases/actual restore plus separate offline history, and S8C seven
local checks are distinct. S10C 4,514 passed/67 skipped remains historical Bot evidence, not a new test run.
S11 later exact-target operational acceptance remains separate; none is new live Discord/deployment proof.

## Closeout validation

- Current pending content: 54 exact Bot Git path identities (52 extant Markdown files and two
  tracked S10C source deletions); two modified SQL Markdown documents. No staged or runtime edits.
- All 749 checked relative Markdown links resolve. Both repositories pass `git diff --check`.
  The SQL CI documentation-path check passes after the new closeout edits.
- Architecture validator passed (zero Python files affected); deferred-item validator passed
  (52 Markdown files); security-routing validator passed with zero errors/warnings.
- `scripts/select_tests.py` completed. Its unconditional smoke-import and command-registration
  suggestions are skipped: only Markdown status, handoff, manifest and archive content changed;
  no Python, command registration, dependencies, configuration or runtime behavior changed.
  Pytest/full suite, SQL fixtures, predecessor checks and all operational execution were not rerun.
- Security routing: documented skip for the exact Bot uncommitted Markdown manifest above and
  SQL uncommitted `docs/SQL_DELIVERY_LOG.md` / `migrations/README.md` at their recorded bases.
  These edits describe existing evidence and future scope; no permission, data-access, persistence,
  deployment or executable change exists. S10E implementation requires its own Changes review,
  Deep off; this skip does not replace that gate.
- The original recovery archive retains all extant pre-reset file hashes and deletion identities.
  A second snapshot, `s10d-closeout-pending-documents.zip`, alongside that recovery directory under
  the retained temporary task artifacts, preserves the updated Bot/SQL files and per-path SHA256/action
  manifest. These backups are local recovery evidence, not Git publication or deployment.
