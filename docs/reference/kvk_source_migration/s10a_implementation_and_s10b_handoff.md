# S10A local implementation and S10B carry-forward

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

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

## S10B implementation checkpoint — 2026-09-14

The operator approved scope and implementation in this task. The historical scope-only and predecessor closeout statements below remain evidence of their original authorization boundary; this checkpoint supersedes them for local S10B code and tests only. No Git publication, SQL/provider/Discord execution, real imports/exports, bot-machine pull/restart/deployment or activation is authorized. S10C/D/E/S11 remain separate.

The exact S7 S10B source/test manifest and the mandatory pending documentation manifest remain one eventual Bot implementation PR. SQL stays at merged #85, 3776dfa6b0892a8800d236fdf111c4d2f93c3813, with no SQL delta. No predecessor rerun or automatic new task occurred.


> Current checkpoint — 2026-09-14: S10A results accepted; SQL #85 merged at
> `3776dfa6b0892a8800d236fdf111c4d2f93c3813` and local main/origin main synchronized.
> No changes have been pulled to the bot machine. S10A pack/starter are archived; next is
> S10B initial review/scope only. The final closeout manifest below supersedes earlier lists.

## Authority and current boundary â€” 2026-09-14

The operator approved the S10A scope and requested closure of its physical-design gaps.
Local SQL authoring, offline validation and SQL Changes review are authorized. SQL execution,
including disposable fixtures, provider/Discord operations, imports/exports, Git staging/commit/
publication, bot-machine pull/restart/deployment and activation are not authorized.
No S10B/C worker/adapters, S10D pool schema, S10E recovery/rollover or S11 implementation.
This handoff records preparation for S10B; it does not start or authorize that slice.

Bot HEAD/origin main: `8e60e78d850a92b6ff84c6b870b8f0c6c5254806`;
production/main: `289bc87e1379941fd6ddafe1a18bb5e7a993d09d`;
SQL HEAD/origin main: `d0916f742f9c88743b97107dfca1f3acbcb32c2e`.
These remain comparison anchors, never reset instructions. Both indexes remain empty.

## Exact SQL implementation manifest

All paths below belong only to `C:/K98-bot-SQL-Server`. The migration reservation
20260912_002 was replaced by the approved actual-date/free-sequence name 20260914_001.
No merged migration was renamed. Both pending SQL documentation files are mandatory in
its eventual SQL implementation PR; never a standalone documentation PR.

| Action | Exact SQL path |
|---|---|
| Create | `migrations/20260914_001_shared_export_coordination.sql` |
| Create | `sql_schema/dbo.ExportJob.Table.sql` |
| Create | `sql_schema/dbo.ExportJobResource.Table.sql` |
| Create | `sql_schema/dbo.ExportResource.Table.sql` |
| Create | `sql_schema/dbo.ExportRequestBudget.Table.sql` |
| Create | `sql_schema/dbo.ExportAttempt.Table.sql` |
| Create | `sql_schema/dbo.ExportAttemptPart.Table.sql` |
| Create | `validation/kvk_source/s10_export_coordination.sql` |
| Modify | `docs/SQL_DELIVERY_LOG.md` |
| Modify | `migrations/README.md` |

## Closed design gaps and remaining implementation ownership

The two SQL documents contain the complete field/state/bounds/FK/index contract.
Spool/storage keys use explicit 128-character bounds; spool keys are opaque generated tokens.
New JSON evidence is bounded at 65536 bytes; file manifests at 1024 rows including the index
when represented. These are storage safety limits, not provider quotas or promised pool capacity.
BudgetKind is google_request across both clients; millisecond precision retains 2100ms spacing.
Roles are index/generation/output, ACL states pending/private/public_viewer/failed/uncertain,
and quarantine none/quarantined. Existing SourceDelivery receipt bytes/limits are unchanged.

SQL retains job replay/repair identity, scoped intent references, resource membership/ownership,
budget state and normalized attempt/part evidence. Exact NULL replay tuples remain unique.
A partial schema or incompatible rerun fails closed; a complete rerun verifies catalog shape.
The migration creates no application rows, grants or activation settings. Rollback is disabled
admission and forward correction, retaining all historical state.

S10B/C must implement atomic CAS/admission, matching owner/fence tuples, immutable inputs and
resource membership, exact manifest cardinality/hashes, source/vector eligibility, original
fairness tickets, and provider waits outside SQL transactions. Receipt-to-pinned-vector
membership must be verified by the later DAL even when the receipt's scoped FK is valid.
Old attempts must remain independent of mutable current ownership. Preserve running A while
new B/C arrive; coalesce only eligible pending new-source work, never daily SCANORDER history.
No lease expiry or callback failure proves an uncertain resource is free. Existing Bot
publication_gate/latest-selection behavior remains unchanged until its authorized S10B/C work.

No unrelated helper refactor or new deferred optimisation was introduced. These later
coordinator/adapter obligations are the approved programme boundaries, not hidden debt.

## Validation checkpoint

76 offline static checks and 85 T-SQL parse inputs passed. The fixture authors 76 structural
cases and four guarded modes; none has executed. SQL repository validation succeeded with
15 pre-existing historical migration warnings, none from S10A. No SQL Server catalog,
transaction/concurrency or provider acceptance result is claimed by static validation.
Offline evidence: `C:/Users/cwatt/AppData/Local/Temp/k98-s10a-implementation-20260914`.
The completed Changes scan result and final exact-manifest checks are recorded below.
Bot runtime pytest/import/registration execution is skipped: no Bot runtime/test/config changed.

## Exact mandatory Bot carry-forward to S10B


**39 physical Bot documentation paths** after the approved S10A implementation handoff; exact paths, not the count, control delivery.

| Action | Exact Bot path | Delivery |
|---|---|---|
| Modify | `README-DEV.md` | S10B Bot implementation PR |
| Modify | `docs/reference/README.md` | S10B Bot implementation PR |
| Modify | `docs/reference/canonical_command_reference.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md` | S10B Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md` | S10B Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/local_sql_development.md` | S10B Bot implementation PR |
| Create | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10B Bot implementation PR |
| Delete (archive origin) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Create | `docs/task_packs/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10B Bot implementation PR |
| Delete (archive origin) | `docs/task_packs/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/README.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` | S10B Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` | S10B Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/README.md` | S10B Bot implementation PR |



This set includes the S10A pack/starter, S9B closeout, this handoff, and both the old and new
paths of each S9B archive move. Keep all of it in the next Bot implementation PR, S10B.
At future publication compare provider filename AND previous_filename against every path,
or provide exact already-merged commit/content proof. No pending path has an exemption.
The retained provider records for #277/#584/SQL #84 were checked against local HEAD blobs
and deleted origins; those delivered S9A archive moves are distinct from these pending moves.
No S10A PR exists, so future provider coverage is not claimed complete by local path checks.

## Retained contracts and evidence

Preserve fixed season source, supplied overall/B0, independent stats/targets/publication/roster/
history/daily consumers, authoritative aggregates/DKP, UTC starts, daily SCANORDER, unused scans,
movable within-season windows, exact 11-10/12-10/final13-10/authorized14-10 chain, sealed inputs/CAS,
durable matched UpdateID, explicit counterpart attestation and admission locks. No mixed source,
summed-fight overall, silent legacy fallback or SourceRouting.Enabled-only activation.

S6-OPS01/PERF01/CAP01 remain open. Preserve both uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`, all retained
databases/backups/files and exact receipt/owner/fence evidence. No mapping, repair or reclaim.
S8B accepted smoke/50-case/actual-restore evidence remains distinct from offline runner history,
S8A six-script/VERIFYONLY evidence and S8C disposable/operator evidence. Seven local S8C checks
PASS is not live Discord acceptance. No predecessor evidence was rerun or relabelled.

## Final local review checkpoint â€” 2026-09-14

SQL Changes review completed with Deep off: scan `42f1d097-f2fd-4653-b330-8fde764e8e1d`,
base/head `d0916f742f9c88743b97107dfca1f3acbcb32c2e`, working-patch digest
`codex-security-snapshot/v1:sha256:7d5b7461a9fb392be24b7cfff5cf90068182100daf5ca4d1fdad5af70349d714`.
All eight source files reviewed, both delivery documents assessed, zero reportable findings.
Preflight passed; Daybreak advisory reported granted. No SQL source changed after snapshot.
Canonical sealed report is retained under
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-lvLOmc/K98-bot-SQL-Server/d0916f742f9c88743b97107dfca1f3acbcb32c2e_20260914T145806Z_wvyeqtls/report.md`.
Workbench measured usage: 4,289,534 total tokens, including 4,104,064 cached input tokens;
this is the tool's rollout accounting across three threads, not a standalone billing estimate.

Bot documentation was assessed independently: documented Changes-scan skip because only
Markdown scope, evidence, manifests and archive documentation changed; no executable code,
configuration, permissions or data-access behavior changed. The SQL scan does not cover Bot.
Architecture, deferred-item and security-routing validators passed; test selection completed.
SQL repository validation and offline target-publication contract checks passed. PowerShell
deployment scripts parsed without errors. Both repositories passed git diff --check; local
Markdown destinations and SQL documentation references passed. SQLFluff reported 223 advisory
alias/layout/style warnings in the migration; syntax parsing passed. These are not runtime tests.

Exact ten SQL paths and 39 Bot paths match the manifests. Both archive destination filename
and origin previous_filename obligations are retained explicitly. The other 35 original pending
Bot paths remain byte-identical (including absent origins); only the closeout, pack and starter
received the approved status additions, plus this new handoff. Both pending SQL document
prefixes were preserved. Git anchors and empty indexes remain unchanged.

Remaining gates: separately authorized SQL Server install/rerun/drift/rollback evidence,
later worker/DAL concurrency and provider acceptance, and eventual exact provider PR-path
coverage. No Git publication, SQL execution, deployment or activation occurred.

## Authorized SQL PR publication â€” 2026-09-14

The operator reviewed the local result and then approved SQL PR publication. Earlier
no-publication statements are historical checkpoints; merge and SQL execution remain gated.
[SQL PR #85](https://github.com/cwatts6/K98-bot-SQL-Server/pull/85) is open from
`codex/s10a-shared-export-coordination`, head `e417e5f8bb33ab3e66d3f14ca97ad78e7cb2e430`,
against main `d0916f742f9c88743b97107dfca1f3acbcb32c2e`.

The exact provider filename AND previous_filename union equals all ten SQL manifest paths;
no renames or extra paths. Every provider file blob matches that published head, including
both mandatory SQL documents. SQL working tree is clean. Evidence is retained in
`C:/Users/cwatt/AppData/Local/Temp/k98-s10a-implementation-20260914/publication-evidence.json`.

Staged validation found and removed one extra terminal newline from the new ExportRequestBudget
snapshot. Byte comparison proved this was the sole post-scan change; all SQL statements and
the other nine files were unchanged. The prior unstaged whitespace check did not inspect
untracked files. Staged git diff --check now passes. Security routing records a whitespace-only
skip for this one-byte delta; the completed Changes review remains the behavioral evidence.

All 39 exact Bot documentation paths remain pending for S10B; this update uses the already
manifested handoff path. Neither S9B archive move has been published by this SQL PR. No Bot Git
mutation, SQL execution, provider operation, merge, deployment or activation occurred.

Final hosted static CI passed for both the branch push and PR at this exact head:
[push run](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34861285870) and
[PR run](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34861301638).
Repository validation, target-publication contract, PowerShell parsing, credential-pattern,
documentation-path and nightly-retention checks passed. SQLFluff remains an advisory step;
hosted CI does not execute the S10A SQL fixture or establish deployment acceptance.

## PR #85 review fixes â€” 2026-09-14

The operator authorized action, replies and resolution of all three review comments.
Published correction `5ed6f91e00c8066407cac27ff9d97d8f50335547` updates both SQL current
banners and makes migration/fixture preflight reject non-table name conflicts explicitly
before counting user tables. A fifth guarded mode, type_conflict, creates a synthetic view
inside the fixture transaction and requires the migration's error number/message prefix,
view preservation and no new export tables. Final rollback verification still counts all
object types to detect a surviving view. Five modes/76 structural cases remain unexecuted.

Focused guard/banner assertions and 86 T-SQL parse inputs passed. Repository validation
passed with the same 15 historical warnings. Correction Changes scan
`f982d5d6-2947-4af6-814b-b020c6cf2a90`, Deep off, completed with zero reportable findings
for the four-path delta from `e417e5f8bb33ab3e66d3f14ca97ad78e7cb2e430` at digest
`codex-security-snapshot/v1:sha256:3a89e610905d99de7ab230dffcd9e60a5ee39e65f305243981b451bac8273448`.
Measured scan rollout usage: 1,880,988 total tokens, including 1,842,304 cached input tokens.
Report retained under the security scan directory
`e417e5f8bb33ab3e66d3f14ca97ad78e7cb2e430_20260914T153050Z_r_zw4v2m`.

All three review threads received replies identifying the fix and unexecuted SQL boundary.
The ten SQL paths and 39 Bot carry-forward paths remain unchanged; this entry adds no path.
Bot documentation has an independent documentation-only security skip. No SQL execution,
merge, deployment, activation or Bot Git mutation occurred.

## PR #85 collation review correction â€” 2026-09-14

Further P1 review feedback identified temporary text columns inheriting tempdb collation
instead of the application database default. Commit `0cdf9efcc6f625580a84f57449c5c103e74d8268`
adds COLLATE DATABASE_DEFAULT to all seven affected temporary reason/JSON columns. Permanent
DDL and explicit BIN2 identity columns are unchanged. Static regression checks compare all
29 character-column pairs; all pass, along with 86 parser inputs and repository validation
(the same 15 historical warnings). The existing fixture now documents separately approved
install/constraints runs with database collation different from tempdb; those remain unexecuted.

Correction Changes scan `9e7ceb96-1211-4155-8301-3da7788cf727`, Deep off, completed with zero
reportable findings for the delta from `5ed6f91e00c8066407cac27ff9d97d8f50335547`, digest
`codex-security-snapshot/v1:sha256:7746719833f60cb0b7b38cc15bd7f1e7dcfcdda89cf6c4ea770c889ca0261122`.
Measured rollout usage: 2,260,431 total tokens, including 2,223,616 cached input tokens.
Canonical report retained in scan directory
`5ed6f91e00c8066407cac27ff9d97d8f50335547_20260914T154941Z_b_iz2btz`.
The P1 thread received a reply with the commit, validation and explicit execution boundary.
The exact ten SQL/39 Bot manifests are unchanged; all earlier evidence is retained. No SQL
execution, Bot Git mutation, merge, deployment or activation occurred.

Collation-fix CI passed for [push](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34865107102)
and [PR](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34865112501) at `0cdf9ef`.
The P1 thread was resolved after those checks; GitHub readback confirms all PR85 threads
resolved. Exact filename/previous_filename coverage and every provider blob match the ten-path
manifest at that head. A transient GitHub diff HTTP 500 cleared on read-only retry.
Reply/resolution evidence is retained as collation-reply.json and collation-resolution.json.

## Proposed exact disposable validation plan â€” 2026-09-14

The operator approved preparing this plan after code review completed. This is the concrete
execution-approval checkpoint; no SQL connection, database creation, backup or restore has run.
SQL source remains clean at `0cdf9efcc6f625580a84f57449c5c103e74d8268` on PR #85.
This plan uses the existing handoff path, so the exact Bot manifest remains 39 paths.

### Exact proposed targets and files

| Item | Proposed value |
|---|---|
| Server identity | `9SX2VF4\K98DEV` |
| Connection | `lpc:localhost\K98DEV`, Windows authentication; no production/default target |
| Primary database | `K98_S10A_Disposable_20260914_validation` |
| Actual-restore database | `K98_S10A_Disposable_20260914_validation_restore` |
| Primary/restore collation | `Latin1_General_CI_AS` |
| Expected tempdb/server collation | `SQL_Latin1_General_CP1_CI_AS`, from retained evidence; freshly verify |
| Compatibility | 160 |
| Primary data | `C:/Program Files/Microsoft SQL Server/MSSQL16.K98DEV/MSSQL/DATA/K98_S10A_Disposable_20260914_validation.mdf` |
| Primary log | `C:/Program Files/Microsoft SQL Server/MSSQL16.K98DEV/MSSQL/DATA/K98_S10A_Disposable_20260914_validation_log.ldf` |
| Baseline backup | `C:/Program Files/Microsoft SQL Server/MSSQL16.K98DEV/MSSQL/Backup/K98_S10A_Disposable_20260914_validation_prerequisite.bak` |
| Restore data | `C:/Program Files/Microsoft SQL Server/MSSQL16.K98DEV/MSSQL/DATA/K98_S10A_Disposable_20260914_validation_restore.mdf` |
| Restore log | `C:/Program Files/Microsoft SQL Server/MSSQL16.K98DEV/MSSQL/DATA/K98_S10A_Disposable_20260914_validation_restore_log.ldf` |

The five filesystem paths were absent during offline preparation. Database-name availability,
current service state, server identity/version/collation and SQL permissions are not yet checked.
If any target/file exists or identity differs, stop; do not overwrite, rename the target silently,
start services automatically, use RESTORE WITH REPLACE or substitute an existing database.

### Pinned source and preparation evidence

Manifest: `C:/Users/cwatt/AppData/Local/Temp/k98-s10a-implementation-20260914/s10a-disposable-plan-manifest.json`
SHA256: `1f83efbd5ed044b07cfaf198862f8fe2645e0f210da8642c957eee67ed6c4d4c`.
It contains each of the 19 prerequisite source paths, SHA256 values and FK dependencies,
exact target/file names, operations, exclusions and the following execution inputs.

| Input | File SHA256 |
|---|---|
| `migrations/20260914_001_shared_export_coordination.sql` | `30b214e5c04c32e8985f4802cd78e592ea5ee9e3bfac7d0131fafab53257bd34` |
| `validation/kvk_source/s10_export_coordination.sql` | `92805636b8618000277fea8ea56925fea9397394aa4ef8746f6a81203a2d7883` |
| Prepared `s10a-empty-prerequisites.sql` in the same scratch directory | `027d6b5ea12150290417c58a1c425ea0bdf66ffbe7c763a8e94109f6be31baa7` |

The migration's bound SQL-text UTF-16LE hash is
`97b1d7cd7ab2a8153189b391c83d72fef5fd96af96dd947b5e733c6bfff1a4f6`.
The manifest separately records the fixture's SQL-text hash. File-byte hashes and bound-text
hashes are distinct and must not be interchanged. Recheck all hashes before execution.

The prepared prerequisite SQL creates 19 empty current snapshot tables and 50 trusted FKs,
deferring FK creation until all tables exist. It contains no source data or predecessor
migration invocation. It passed offline T-SQL parsing and checks for complete FK deferral,
exact table count and absence of application DML. Its target/session/empty-schema guard is
specific to the primary database above. This is fixture construction, not predecessor rerun.

Exact prerequisite tables: KVK.SeasonSource, SourceAggregateReport, SourceAggregateRevision,
SourceArtifact, SourceCompleteSelection, SourceConfigRequest, SourceConfigVersion, SourceDelivery,
SourceExportIntent, SourceExportIntentPublication, SourceLogicalScan, SourceObservation,
SourceObservationRevision, SourcePeriod, SourcePublication, SourceRoster, SourceScanBinding,
SourceUpdate and SourceWindowConfig. Their source definitions are authoritative SQL at the
pinned head; no S8B seed packet, existing database backup or production data is reused.

### Proposed operation sequence

1. Read-only preflight against local master: verify exact server identity, SQL Server 2022,
   compatibility support, expected instance directories, server/tempdb collations, both absent
   database names and all five absent file paths. Capture current database-name inventory so
   later evidence can demonstrate that retained databases were not targeted. Stop on mismatch.
2. Create only the named primary database with explicit Latin1_General_CI_AS and compatibility
   160. Assert its collation differs from tempdb. Run the hash-pinned empty prerequisite SQL
   after setting the exact session authorization; capture all 19 empty tables, trusted keys/FKs
   and schema metadata as the baseline. No application rows are seeded outside fixture rollback.
3. Back up only this new prerequisite database with COPY_ONLY and CHECKSUM to the absent backup
   file; run VERIFYONLY and FILELISTONLY. Perform an actual RESTORE to the absent restore database
   using the two explicit restore paths, CHECKSUM and RECOVERY, never REPLACE. Compare restored
   schema/constraints/collation and zero-row counts with the primary baseline. Record successful
   actual restore separately from VERIFYONLY; retain both databases and backup.
4. On the primary, run fixture modes install, partial and type_conflict in fresh sessions.
   Each session sets exact S10A_SERVER/DATABASE/AUTHORIZED/CASE and supplies one bound
   #S10AMigrationInput row with reviewed text/hash and actual backup/restore evidence references.
   The install mode covers migration/rerun and 76 structural cases in rollback; other modes
   require the expected rejection and preserve the original empty prerequisite-only baseline.
5. Execute the exact S10A migration directly on the primary in a session without an ambient
   transaction, then rerun its raw SQL in another fresh session. This tests its own-transaction
   install and rerun, beyond the fixture's ambient-transaction path. Expect six empty export
   tables, trusted constraints and no changes to the 19 prerequisite tables. Record script hash,
   timestamps and success/failure; do not claim production deployment or manually alter history.
6. Run constraints and drift fixture modes on that installed primary, again with exact bound
   inputs and fresh sessions. Constraints reruns the same 76 unique structural cases; report
   the two passes separately, not as 152 distinct cases. Drift must reject the disabled/untrusted
   constraint and restore its trusted baseline on rollback. Verify no synthetic rows survive.
7. Record final primary (25 empty tables) and restore (19 empty tables) metadata, application
   and tempdb collations, per-mode outputs, rollback results, hashes and retained artifact paths.
   Preserve both databases and all files. Stop on any unexpected error; no automatic repair,
   predecessor rerun, retry with weakened guards, cleanup or false PASS.

The proposed run uses explicit same-session bound inputs for the fixture. It does not invoke
the generic deployment runner with production defaults, sweep pending migrations, modify
SchemaMigrationHistory manually or establish deployment-runner acceptance. No new Bot command,
worker or adapter is introduced. The direct migration run is disposable SQL validation only.

### Approval and remaining boundaries

Execution approval would cover only the targets, files and sequence above, including backup
and actual restore of the newly created prerequisite database. All retained S6/S8 databases,
both uncertain publications, provider/Discord state, bot-machine state and operational evidence
remain outside the run. Security review of the actual execution orchestration must precede
execution; no source change may silently reuse a stale hash. Capture any required amendment
before running changed bytes. Merge, local synchronization, deployment, activation and S10B
implementation remain separate subsequent work.

## Approved execution results and stop â€” 2026-09-14

The operator explicitly approved execution of the exact plan above. Executed against
`9SX2VF4\K98DEV` at SQL head `0cdf9efcc6f625580a84f57449c5c103e74d8268`, using approved
manifest `1f83efbd5ed044b07cfaf198862f8fe2645e0f210da8642c957eee67ed6c4d4c`.
The same-session harness SHA256 was
`22d3178b4ab1df70a074ba0a18c5ce6374596f691265b1dfd1e237786341faba`.
Nine offline fake-driver authorization/target/collision guard scenarios passed before use.
Execution-orchestration safety review covered hash binding, exact connection allowlist,
non-overwriting create/backup/restore, bound fixture inputs and stop-on-error behavior. It is
recorded as a manual safety review, not a new Codex Security scan or replacement for the three
existing SQL Changes scans. SQL repository source remained unchanged throughout this run.

Read-only preflight confirmed SQL Server 16.0.1200.5, both server and tempdb collations
SQL_Latin1_General_CP1_CI_AS, the approved data/log/backup directories, both absent database
names and all five absent file paths. The initial catalog inventory contained 19 databases.

| Operation | Actual result |
|---|---|
| Exact source/manifest/target preflight | PASS |
| New primary with Latin1_General_CI_AS, compatibility 160 | PASS |
| 19 empty current prerequisite tables, 50 trusted FKs | PASS |
| COPY_ONLY/CHECKSUM backup | PASS, 16:14:58 UTC |
| RESTORE VERIFYONLY | PASS, distinct from actual restore |
| Actual restore into the new named restore database | PASS, 16:14:59 UTC; schema, constraints, settings and zero-row baseline match |
| Fixture install (ambient transaction), including migration reruns | PASS, 16:15:01 UTC; application collation differs from tempdb |
| Structural cases within install mode | 76/76 PASS; one pass, not 152 distinct cases |
| Install-mode rollback and baseline preservation | PASS |
| Fixture partial mode | FAILED/STOPPED, 16:15:01 UTC: SQL error 207, Invalid column name 'IntentID' |
| Type-conflict mode | NOT RUN |
| Direct own-transaction migration apply/raw rerun | NOT RUN |
| Installed constraints/drift modes | NOT RUN |

The execution receipt status is failed_stopped_no_automatic_retry. A separate read-only audit
confirmed BOTH databases exactly match the prerequisite baseline: 19 tables, zero rows,
Latin1_General_CI_AS, compatibility 160, unchanged column/index/check/FK metadata and trusted
constraints. All original database names/IDs remain unchanged. The database files remain in
SQL's file catalog and the backup exists. An OS stat of active database files was denied;
the audit used SQL metadata instead, with no ACL changes. No test was retried or repaired.

Evidence under `C:/Users/cwatt/AppData/Local/Temp/k98-s10a-implementation-20260914`:

- `s10a-preflight-receipt.json`
- `s10a-execution-receipt.json`
- `s10a-stopped-state-audit.json`
- `execute_disposable.py`
- `test_execution_guards.py` and `execution-guard-tests.json`
- `execution-safety-review.json`
- The unchanged approved manifest and prerequisite bootstrap SQL.

All five newly created data/log/backup files and both databases are retained. No predecessor
database, uncertain publication, provider/Discord resource, bot-machine state or operational
evidence was targeted. No merge, deployment, activation, Git publication or SQL source change
occurred during this execution task. This existing handoff remains within the exact 39 Bot
documentation paths carried to S10B; no additional Bot path was authored.

### Proposed correction and continuation amendment â€” not implemented or executed

Source-grounded diagnosis: partial mode intentionally creates dbo.ExportJob with only JobID.
The migration's same-batch permanent CREATE INDEX IX_ExportJob_Intent references IntentID
before SQL Server reaches the runtime @S10AExisting partial-state rejection. The observed
error is compilation/binding failure rather than the expected 51000 partial-install error.
No additional reproduction was executed after the stop.

Proposed fix: move only the permanent six-table CREATE TABLE/INDEX/FK installation block into
one constant sp_executesql batch, invoked only after prerequisite/type/count guards pass and
@S10AExisting = 0. Preserve exact permanent DDL, the existing transaction/application lock,
temporary catalog-verification logic, trusted constraints and all historical state. This defers
binding of permanent-table column references until installation is actually admitted, allowing
partial and wrong-type states to reach their intended errors. Keep the strict fixture expectation;
do not accept error 207 as a passing partial-install test.

After approval to fix: validate offline, run a focused Changes review with Deep off, publish
the correction and updated SQL delivery documentation within PR #85, then prepare new hashes
and a separately explicit continuation targeting the retained, verified-empty primary database.
Do not rerun database creation, bootstrap, backup/restore or use the original one-run harness
against now-existing targets. Preserve original receipts and successful restore evidence.
Continuation must cover the failed/pending modes and the corrected migration install/rerun;
the completed cross-collation result stays tied to its original hash, not relabelled as a new run.

Final review-fix CI passed for [push](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34863048730)
and [PR](https://github.com/cwatts6/K98-bot-SQL-Server/actions/runs/34863055926) at `5ed6f91`.
All three addressed threads were resolved after passing CI; GitHub readback confirms zero
unresolved threads. Every provider blob matches the final head, with exact filename and
previous_filename coverage of all ten SQL paths. Resolution/reply evidence is retained in
the scratch evidence directory as review-resolution-evidence.json and review-replies.json.

## Compilation fix and continuation approval — 2026-09-14

The operator explicitly approved implementation of the error-207 compilation-boundary fix
and rerunning the plan once complete. This supersedes the preceding proposed/not-authorized
checkpoint for this correction and the exact retained disposable continuation only.
The fixed constant DDL decodes identically to `0cdf9ef`; 87 parse inputs pass, including the
decoded inner batch, and guard prefix/exact-verification suffix are unchanged. Existing
partial/type_conflict/drift fixtures keep their strict 51000 expectations. Eight offline
continuation preflight cases pass. Bot architecture/deferred/test-selector/security-routing
validators pass; runtime Bot tests/imports/registration are skipped because no Bot code changes.

The new continuation runner and receipt use distinct names under the existing scratch root.
They bind revised source hashes and original evidence, recheck both database identities,
files, collations and complete empty baselines, and stop on unexpected results. They contain
no database creation, bootstrap, backup or restore operations. All original evidence remains.
No new repository path is added: the exact 39-path Bot carry-forward and ten-path SQL manifest
remain the delivery boundary, including both sides of both S9B archive moves.

## Compilation fix delivered; continuation01 stopped — 2026-09-14

Fix commit `b8e19f8f03683eec0d6c2563d732fb5303ba04dd`; evidence docs/current PR head
`dbaab083db57e400845f701b453fb4ff6d158dab`. Exact filename AND previous_filename coverage
matches all ten SQL paths and every provider blob matches local HEAD. SQL checkout clean;
no main synchronization/merge. Both SQL documentation paths report actual outcomes.

Completed sealed Changes scan `0a151f59-3c5d-4dfc-a5dc-81852a5782d0`, Deep off, zero findings;
base `0cdf9efcc6f625580a84f57449c5c103e74d8268`, digest
`3f1701d12151a1b24203a15c0ff20d97af003d6decd54b224520028dc2447a7e`.
Measured usage: 2,025,103 total tokens, including 1,940,096 cached input tokens.
Subsequent evidence-only SQL documentation changes were inspected independently: no runtime
or source effect, so a precise documentation-only security skip applies to that delta.

Approved continuation01 passed read-only preflight, install/76 cases, strict partial rejection
and strict type_conflict rejection. Direct own-transaction migration committed six empty
export tables. Python then compared SQL CI ORDER BY with Python case-sensitive sorting,
rejecting the same exact 25 names in different order. No automatic runtime retry occurred.
Corrected read-only audit verifies 25 empty primary tables; unchanged 19-table restore and
prerequisite metadata; enabled/trusted constraints; unchanged original database inventory;
backup retained. Original backup/actual restore and both stopped receipts remain immutable.

## Exact remaining continuation02 — prepared, not executed

Target remains `9SX2VF4\K98DEV`, primary `K98_S10A_Disposable_20260914_validation`, restore
`K98_S10A_Disposable_20260914_validation_restore`, with the exact original file paths above.
SQL source head is `dbaab083db57e400845f701b453fb4ff6d158dab`; migration/fixture bytes unchanged
from executed `b8e19f8`. Primary starts with 25 audited empty tables; restore with the original
19-table empty baseline. Only direct migration rerun, rollback-only constraints (76 cases),
rollback-only drift and final baseline/inventory audit remain. No install, bootstrap, backup
or restore will repeat. Exact head/source/evidence hashes, server identity, database IDs,
file catalog, collations and both full baselines are checked first. Stop on unexpected results.

The new harness sorts both exact table lists before comparison. Offline regression reproduces
the old false failure and rejects missing, extra and duplicate names. Approval after this new
unexpected stop is required before continuation02; no execution is claimed. This is a harness
verification fix, not a second SQL migration defect.

Exact new evidence outputs under `C:/Users/cwatt/AppData/Local/Temp/k98-s10a-implementation-20260914`:

- `compilation-static-results.json` — SHA256 `bcd8ff02d90128ecfce8e55613391d7d2970e60e7c51736b7cd2db58a3355360`.
- `compilation-preflight.json` — SHA256 `9fde462644e2612bbed06029e7121315290f3da8b881b00952f2d5e9ac120923`.
- `compilation-threat.json` — SHA256 `7f8ace327532cabed5111bcb5a580e1adec2d77cebc8801de7842df22877b0d0`.
- `continuation-guard-tests.json` — SHA256 `ca1afde1a3250f5afbc28b720d47bbff6d066985c15139d5daf25ae0454c4bb1`.
- `continuation-safety-review.json` — SHA256 `edb3ba8b59f468dd03e59dcce35106e13b6bc6960dca73d8d419c877daf07def`.
- `s10a-continuation-01-manifest.json` — SHA256 `705ce96f3ef40907c059a30c118dedfb8835e40a66adb7370bc31b1bd146c3b7`.
- `execute_continuation_01.py` — SHA256 `3e4cbc7765369e57caa4c5dfb8dae7e7947769d0f385349532513bc0314bb9a4`.
- `s10a-continuation-01-preflight.json` — SHA256 `336750ed921a3e5df17546451498a662c508b78da9426932521ef5db5df4b45c`.
- `s10a-continuation-01-receipt.json` — SHA256 `f6c2032f99605225eef146853594f5135f355663a92c45966d5474328e0408f0`.
- `s10a-continuation-01-stopped-audit.json` — SHA256 `da790f81ae10b7182bf3e032a4e36587932f5cc98a59e01912c517771677b14d`.
- `continuation-ordering-regression.json` — SHA256 `a1ec7510d897dad775ab6286bff467e2d6b004ddbf6ff01702283ba269062369`.
- `s10a-continuation-02-manifest.json` — SHA256 `170493741737c899caeaebb98d8e0e93f00d54ba4e3d0347bc04420f2c4e7b50`.
- `execute_continuation_02.py` — SHA256 `d742b3c1b2b30c8f282355bbf8fb0a1a20c26f54010b3c83a0cb99db6b0f20ba`.

These evidence references are in the existing manifested handoff; no repository paths added.
Exact Bot carry-forward remains all 39 paths above, including both sides of both S9B archive
moves; Bot index empty, no Git mutation. Historical hash differences outside this handoff are
only the three earlier approved S9B closeout/S10A pack/starter status updates. All other pending
content is intact. S6 open gates, both uncertain publications, all databases/files, and distinct
S8A/S8B/S8C evidence remain preserved. No production/provider/Discord/bot-machine activity.

Continuation02 read-only preflight passed against the retained primary25/restore19 baselines.
No migration or fixture executed. Additional retained output: `s10a-continuation-02-preflight.json`, SHA256
`3fe139d3729f8e394663ee9b9c38fd6bc7374e1ec2ec6e44327a18593e9fa4f2`.

Final head `dbaab083` CI: push run34869455171 and PR run34869458368 both SUCCESS.
Exact filename/previous_filename union and all provider blob IDs verified again at final head.

## S10A disposable validation complete — 2026-09-14

The operator approved continuation02 and it passed at 16:39:18–16:39:22 UTC on
`9SX2VF4\K98DEV`, using retained `K98_S10A_Disposable_20260914_validation` and
`K98_S10A_Disposable_20260914_validation_restore`. Direct migration rerun preserved the
installed baseline; constraints passed all 76 cases; drift rejection passed; final baseline
and database inventory checks passed. Primary retains 25 empty tables, restore retains the
unchanged 19-table prerequisite baseline, with enabled/trusted constraints.

Together with the retained original backup/actual-restore proof and continuation01 install,
partial/type-conflict and direct-apply evidence, all five fixture modes and direct apply/rerun
are now complete. Install and constraints each passed the same 76 structural cases; these
are 76 unique cases, not 152 different cases. Cross-collation application/default-tempdb
behavior passed. No database recreation, bootstrap, backup overwrite or restore repeat occurred.

Executed SQL head: `dbaab083db57e400845f701b453fb4ff6d158dab`; migration/fixture unchanged
from security-reviewed fix `b8e19f8`. Manifest SHA256
`170493741737c899caeaebb98d8e0e93f00d54ba4e3d0347bc04420f2c4e7b50`.
Receipt `s10a-continuation-02-receipt.json`, SHA256
`71be461a0ab4db270c49664c97a8d89a376a3bbb958b65c165f3edd160254713`, retained under
`C:/Users/cwatt/AppData/Local/Temp/k98-s10a-implementation-20260914` with every prior receipt.
The manifest's pending-approval wording is its immutable preparation checkpoint; subsequent
operator approval and this executed receipt supersede it without rewriting evidence.

This is sequential disposable SQL evidence, not worker concurrency, provider truth or live
Discord acceptance. All retained operational gates and uncertain publications remain intact.
No production/bot-machine deployment, activation, merge or later-slice implementation occurred.
This update changes only delivery evidence; SQL source bytes remain unchanged, so the existing
Changes security review applies and a precise documentation-only skip covers this delta.

SQL evidence-only publication head: `02a584b3dd562bb1cc6d9c16c2712021d85e2af2`.
The successful receipt is added to this existing exact-manifest handoff; no new Bot path.
Earlier pending-approval/unexecuted checkpoints above are historical and superseded.

Final `02a584b3` CI: push34870120371 and PR34870124514 both SUCCESS.
Exact ten-path filename/previous_filename union and provider blob identity reverified at this head.
Approved execution work complete; operator acceptance/merge authorization remains the next gate.

## S10A final closeout and S10B delivery manifest — 2026-09-14

Operator accepted all results, merged SQL PR #85 and updated locally. GitHub confirms merge
at 17:12:47 UTC, merge commit `3776dfa6b0892a8800d236fdf111c4d2f93c3813`; final PR head
`02a584b3dd562bb1cc6d9c16c2712021d85e2af2`. SQL HEAD/main/origin main match the merge and
checkout is clean. Both required SQL docs are delivered in the ten-file merged SQL manifest.
No post-merge SQL execution or bot-machine smoke is claimed. User confirms no bot-machine pull.
Bot main/origin main and production/main remain the comparison anchors above, never reset targets.

The completed S10A pack/starter move to archive, preserving their historical requirements.
Existing evidence/reference documents remain available; no retained database, backup or receipt
is deleted. S9B archives remain mandatory. S10B pack/starter are prepared for review/scope only.
No code, SQL changes, Git publication, deployment, activation or automatic new task is authorized.

### Exact current pending Bot paths — mandatory S10B implementation PR

This table supersedes earlier 39-path preparation inventories. It contains 41 physical pending
paths: the original39 minus two never-committed S10A source paths, plus their two archive destinations
and two new S10B pack/starter paths. The two historical S10A source identities remain in the explicit
exception table below, yielding43 path identities across pending delivery and archive provenance.
Do not use counts as proof. Check every filename AND previous_filename in the S10B PR; prove any
specific path already merged before excluding it. Include newly authored handoff outputs. No
standalone documentation PR, no repository mixing, no re-asking the settled grouping.

| Working-tree action | Exact Bot path | Required delivery |
|---|---|---|
| Modify | `README-DEV.md` | S10B Bot implementation PR |
| Modify | `docs/reference/README.md` | S10B Bot implementation PR |
| Modify | `docs/reference/canonical_command_reference.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` | S10B Bot implementation PR |
| Add | `docs/reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` | S10B Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md` | S10B Bot implementation PR |
| Add | `docs/reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md` | S10B Bot implementation PR |
| Modify | `docs/reference/local_sql_development.md` | S10B Bot implementation PR |
| Add | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10B Bot implementation PR |
| Delete source (archive move) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Add | `docs/task_packs/Codex Task Pack - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10B Bot implementation PR |
| Delete source (archive move) | `docs/task_packs/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/README.md` | S10B Bot implementation PR |
| Add | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` | S10B Bot implementation PR |
| Add | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Add | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` | S10B Bot implementation PR |
| Add | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10B Bot implementation PR |
| Modify | `docs/task_packs/archive/README.md` | S10B Bot implementation PR |

### Archive source exceptions: exact absent-at-base proof

These two source files were untracked, absent from Bot HEAD `8e60e78d850a92b6ff84c6b870b8f0c6c5254806`
and never delivered by a Bot PR. `git cat-file -e HEAD:<exact path>` fails for each; the source
is absent on disk after the move. Git cannot emit deletion/previous_filename for a never-tracked
source. Require its archived destination in the PR and inspect its preserved content; do not
misreport these source deletions as missing PR coverage or as already merged paths.

| Historical source path | Required archived destination | Proof |
|---|---|---|
| `docs/task_packs/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | Absent in named Bot base; destination retained |
| `docs/task_packs/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | Absent in named Bot base; destination retained |

The S9B source paths are tracked deletions and their archive destinations are pending additions:
require both sides through filename/previous_filename coverage (or explicit added/deleted entries).
The exact table includes the S9B closeout, this S10A handoff, all earlier pending reference updates,
both archived S10A documents and both active S10B documents. Keep the same grouping through
separately authorized Bot production promotion; SQL history remains separate.

### Validation and remaining boundary

Documentation-only closeout: no runtime/config/permission/data-access effect. Security routing
records a documentation-only skip; no new scan. Existing source Changes reviews remain retained.
Runtime tests/imports/command registration are unnecessary for this Markdown-only change;
architecture/deferred/test-selection/security-routing and link/manifest checks are the closeout gates.
S10B must independently validate its exact source manifest and temporal DAL/worker guarantees
against merged SQL before implementation approval. No deployment/activation is implied by merge.

Closeout verification PASS: all ten SQL PR filename/previous_filename identities and merged blobs
match, including both required SQL documents. SQL main remains clean. Bot exact41 pending paths
match the current manifest, with two explicit absent-source exceptions and empty index. All local
Markdown links in pending files resolve. Architecture, deferred-item, test-selection and security-routing
validators and whitespace checks pass. Runtime tests/imports/registration skipped: Markdown only.
Evidence outputs `s10a-final-bot-carry-forward.json` and `s10a-merged-path-proof.json` are retained
in the existing temporary evidence directory; this handoff is their already-manifested repository record.


## S10B local implementation evidence — 2026-09-14

The approved S7 nineteen-path source/test manifest is implemented locally. It remains grouped with every path in the exact mandatory pending Bot documentation table above. No standalone documentation PR or SQL repository change was made. The index remains empty; Git publication is not authorized.

The coordinator discovers committed immutable intents, preserves running A, and coalesces only eligible unattempted pending work while retaining ticket age. Ordered account/destination resource claims use durable owner/fence/version CAS. Replay preserves immutable input/storage identity. Explicit pre-attempt retry audits actor, reason, server UTC and prior owner/fence/version without replacing the job or ticket; attempted/uncertain work cannot use that path.

Pinned intent loading validates the full publication vector and fixed season choice, then uses immutable result/config/roster snapshots. The coordinated Sheets path persists the complete attempt/part manifest before mutation, rechecks ownership after pacing, writes RAW values, verifies private content/ACLs, and confirms only exact publication readback. Existing scoped legacy receipts are retained. No SQL transaction spans a provider request.

Request reservations and cooldowns use server UTC. A delayed-dispatch regression found during review was corrected by persisting a full policy interval after actual request completion. The checkpoint runs after both successful and failed provider requests. It never shortens existing cooldown or reserved queue tail. If the checkpoint is uncertain, the account/resource claims remain blocked even if the request was read-only. This deliberately adds completion-to-next-request spacing; it favors safe pacing over throughput.

The worker checks shutdown before discovery and requests, retains uncertain attempts/parts and resources, and awaits its offloaded thread through repeated cancellation. Registered spool bytes use exclusive creation, fsync/readback and owner/length/SHA256 validation. Private host ACLs remain a provisioning obligation. Production startup remains closed even with EXPORT_COORDINATION_ENABLED=true: shared S10C adapter composition and later deployment gates do not exist in this slice. New-source pool reuse and operator reconciliation/repair are still S10D/E responsibilities.

### Exact delivery/provenance verification

The union of the exact S7 S10B manifest and the mandatory pending documentation table matches the working tree path by path, with no missing or unexpected paths. Both tracked S9B source deletions and their archive additions are present. At Bot base 8e60e78d850a92b6ff84c6b870b8f0c6c5254806 their source blobs are d00332e532a2982d95cb089ba7bcd9d196581586 (starter) and df7412d3501da466b7c82bf1efe1452f8bd13358 (pack). Both S10A source paths are absent at that exact base and on disk; both archived destinations exist. No PR exists, so provider filename/previous_filename readback remains a mandatory publication-time gate, not a claimed result from local counts.

SQL remains clean at merged #85 / 3776dfa6b0892a8800d236fdf111c4d2f93c3813. Its earlier ten-path merged-blob proof remains retained above. SQL assessment is independent: no SQL delta was required, so there is no new SQL diff security target.

### Validation boundary

Offline regression coverage includes immutable A while B arrives, pending coalescing/ticket inheritance, replay/input bounds, durable server-time budgets and delayed-request completion, cooldown monotonicity, uncertain completion claim retention, stale CAS, attempt/part cardinality and quarantine, spool integrity/affinity, private/public synthetic provider readback, default-closed startup and repeated cancellation. Four opt-in SQL tests require separate authorization for their exact disposable database operations and remain unexecuted. They do not establish live cross-process or provider timing evidence.

Required architecture, deferred-items, security-routing, test-selection, smoke-import and command-registration checks passed before the pacing correction and are repeated for final handoff. Black and Ruff cover the changed Python manifest. Pyright on its configured changed target bot_config.py reported zero errors and one unresolved dotenv import warning; no dependency installation or unrelated typing expansion was performed. All 542 local Markdown links resolved.

Security routing is Changes, Deep off, on the Bot working-tree target. Initial scan 24ec757d-7665-4c4f-afdc-b1f095a8a9a8 completed after correcting a rejected draft-tool argument. Its non-security pacing observation prompted the correction above. A final review of the corrected exact snapshot is required; the original scan does not attest later bytes.

S6 open gates, publications e19c89ac-7977-5f28-ae4c-031807cd1728 and 54a2480a-26fb-5bad-a3f5-9321525a731c, and all retained databases/files remain untouched. S8A six scripts/VERIFYONLY, S8B fifty-case actual-restore evidence, the offline runner and S8C seven local checks retain their distinct evidence boundaries. No predecessor rerun, live SQL/provider/Discord operation, import/export, bot-machine pull/restart/deployment, activation or new task occurred.


### Final S10B local validation result

Final focused run: 230 passed, 4 SQL tests skipped (9.95 s). Final full offline suite through analyse_pytest_log_noise.py: 4,420 passed, 66 skipped (167.75 s); production operational logs unchanged. Architecture (16 Python paths), deferred-items (42 Markdown paths), security-routing (zero errors/warnings), smoke imports and command registration passed. The top-level command surface remains 36 with no drift. Ruff passed and Black left all sixteen changed Python files unchanged. Test selection prescribed the full suite, imports and registration checks, all completed.

Final Codex Security scan 6c3284aa-7c5f-4647-9299-de5feb5771c0 completed and its sealed result was read back: Changes, Deep off, Bot base/head 8e60e78d850a92b6ff84c6b870b8f0c6c5254806, working-tree content digest codex-security-snapshot/v1:sha256:8dcfbe540da05838ffbc7576161309b250ce19e3d939d937124123e4d71978fe. All eleven inventoried changed source files were covered; no security findings or deferred candidates. The earlier pacing observation was verified corrected. Preflight passed without configuration changes; Daybreak status granted, program Daybreak Blue. The scan is static/offline evidence, not live concurrency, deployment or activation evidence.

This final evidence paragraph was appended after sealing. It changes documentation only; executable source/test bytes remain those reviewed in the final scan. Security routing for this result-only append is a documented documentation-only skip. The entire mandatory documentation grouping remains required in the eventual implementation PR, including provider filename/previous_filename verification at that time. No publication or deployment is authorized by this result.


### PR #278 review follow-up

Review comments on commit 70185b646375592875b45962f276b0de7aee7bd9 identified missing SourceExportIntent status transitions and host-clock interpretation of HTTP-date Retry-After, plus a historical handoff spacing typo. All three were accepted for correction within S10B.

Job materialization, pending coalescing and confirmation now synchronize their source intent in the same SQL transaction, using the existing state/supersession fields as CAS expectations. Intent mutexes serialize cross-account status writers; aggregation preserves materialized state while another registered job is still running and records a coalesced successor only when the registered jobs agree. Immutable vector/publication fields are unchanged. Discovery filters already represented registrations rather than scanning every materialized historical intent, while retaining missing registration work after a partial fan-out/restart. Claim identity includes the immutable intent identity.

HTTP-date Retry-After values are parsed to absolute UTC and bounded only against SQL server UTC in the DAL. Numeric delays retain their prior bounds; existing longer cooldowns remain monotonic. Uncertain provider-cooldown checkpoints use the same retained-claim path as uncertain completion checkpoints, including read-only requests. No host wall-clock duration is used. The historical 39-path prose spacing is corrected without changing its retained manifest.

These fixes require no SQL schema delta. Offline regression tests cover intent state CAS/aggregation, coalesced successor retention, registration-aware discovery, terminal synchronization, SQL-clock date bounds and unconfirmed cooldown handling. Live SQL/provider/Discord validation and deployment remain unauthorized; the existing evidence and later-slice gates remain unchanged.

Review-fix validation: full offline suite 4,431 passed, 66 skipped (175.24 s), production logs unchanged; final coordinator regressions 74 passed. Architecture, deferred-items, security-routing, smoke imports, command registration, Ruff, Black and whitespace checks passed. Incremental Changes/Deep-off scan 42cd2d95-a259-4596-9dc7-1786b83314d6 against reviewed PR head 70185b646375592875b45962f276b0de7aee7bd9 completed with no findings or deferred candidates across all three changed source files. This result-only post-scan documentation append has a documentation-only routing skip; code bytes are unchanged. Live SQL/provider tests remain unexecuted and human merge/deployment review remains a separate gate.

### Production PR #585 review follow-up

The review of production head `611ef8dced9bf4f78911989c36ca2b1f944a798a` identified eager loading and long-form expansion of the entire intent vector. The correction loads one pinned publication at a time, compacts it and releases its raw envelope before the next read. Both intent and explicit-selection Sheets loaders reuse the same compact-period merge, preserving deterministic output and independent supplied overall data. The input digest is checked before payload loading; all database transactions close before iteration/compaction and all periods finish before provider mutation. Final compact output memory still scales with export size; this is not a new live memory benchmark or closure of S6-PERF01/CAP01.

Two ten-period regressions verify raw-envelope release, compaction-before-next-read, reversed-vector output/hash parity, supplied or missing overall, transaction boundaries and digest rejection before payload reads. Focused export/delivery tests: **135 passed**. Full offline suite: **4,433 passed, 66 skipped (179.64 s)**; production operational logs unchanged. Architecture, deferred-items, security-routing, test selection, smoke imports, command registration (36 top-level commands, no drift), Ruff, Black and whitespace checks passed.

Incremental Codex Security scan `ad6fa8fd-01f6-4d6c-a387-d1c0b64692dc` completed and its sealed result was read back: Changes, Deep off, exact production head above to the correction, both changed source files covered, no findings or deferred candidates. This result-only documentation append follows sealing and has a documentation-only routing skip. The separate SQL repository remains clean at `3776dfa6b0892a8800d236fdf111c4d2f93c3813`; the existing weight query matches authoritative schema and no SQL delta is required.

Production base `289bc87e1379941fd6ddafe1a18bb5e7a993d09d` and head were verified against GitHub. Exact server filenames match the local Git diff; both S9B archive rename source/destination identities and base blobs match the manifest. Both untracked S10A source paths are absent at this exact production base, with archive destinations present. All 60 physical manifest identities remain represented, rather than relying on the 58-file count. The mirror branch and SQL work remain untouched. No live SQL/provider/Discord operation, real import/export, bot-machine pull/restart/deployment, activation or predecessor rerun occurred; all retained evidence and open gates above remain unchanged.
