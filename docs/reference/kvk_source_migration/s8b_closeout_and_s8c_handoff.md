# S8B closeout and S8C handoff

## Current status — S10D SQL merged; S10E scope next, 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
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

> Historical handoff: **S9B repository-delivered; not deployed**. See [S9B closeout / S10A scope and exact documentation carry-forward](s9b_closeout_and_s10a_handoff.md).
> Retained evidence and historical approvals below remain intact; no predecessor rerun or live operation is authorized.

> Retained S8B/S8C reference, 2026-09-14: S9B repository delivery is now complete.
> See [S9A closeout / S9B scope and pending documentation delivery](s9a_closeout_and_s9b_handoff.md).
> Historical execution/operator evidence and limits below remain intact; this update does not
> request a rerun or claim live Discord acceptance, bot-machine deployment or activation.


> S8C is now delivered and archived. The [S8C closeout and S9A handoff](s8c_closeout_and_s9a_handoff.md) supersedes the next-slice/status directions below; retain the dated S8B/S8C evidence as history.

## 1. Accepted closeout and verified state — 2026-09-13

**S8B is complete, operator accepted, successfully smoke tested and merged into production.**
The operator confirms local pulls are complete and **no changes have been pulled to the bot
machine**. Smoke acceptance is operator-attested and supported by the retained checks below;
it is not a fresh post-merge SQL run, bot-machine smoke, deployment or activation claim.

| Repository / PR | Verified disposition | Merge UTC / commit | Reviewed final head |
|---|---|---|---|
| Bot production [#581](https://github.com/cwatts6/k98-bot/pull/581) | MERGED | 2026-09-13 10:58:06 / `9bcbe004ecd6174e7343dbbb552410facd2feb32` | `fc600fdba378e62e1aec5486b5480152d5bc090b` |
| SQL [#81](https://github.com/cwatts6/K98-bot-SQL-Server/pull/81) | MERGED | 2026-09-13 10:57:34 / `3983522feb0ff90c96ba56ca11c2dac177f84ca6` | `32d7752f90fba9bbc805d86f80326ce78771924a` |
| Bot mirror [#274](https://github.com/cwatts6/K98-bot-mirror/pull/274) | CLOSED; no merge commit/date returned | Delivered content verified in synchronized mirror main; do not describe this PR as merged | `4068769e90d4633d8183056e204e4a3416966012` |

Bot local main/origin main is `e9114dd62f4f4ee2d8e193bd1f0b9e31b8543486`, synchronized from
production `9bcbe004`; production/main matches that merge. SQL main/origin main is
`3983522feb0ff90c96ba56ca11c2dac177f84ca6`. Both worktrees were clean at closeout entry.
These hashes are comparison anchors, not reset instructions. No pull/fetch/reset was performed.

Fresh GitHub Files changed verification: production #581 has 47 entries covering all 51 physical
S8B paths, counting each `filename` and `previous_filename`. All four S7/S8A archive origins are
absent and their destinations present. Each delivered file blob matches the locally pulled Bot
HEAD. SQL #81 has six entries and all blobs match SQL HEAD. Mirror #274 now returns five entries
after synchronization (it returned 47 before close); all five current entries match local HEAD.
Use production's complete manifest plus content proof for the synchronized snapshot, not mirror
PR state or current file count as a substitute. No S8B implementation carry-forward remains missing.
Proof is retained in `C:\Users\cwatt\AppData\Local\Temp\k98-s8b-merged-content-proof.json`.

## 2. Validation, retained limits and next slice

- Final Bot review fixes keep legacy admission/season lock through ingest and recompute in one
  transaction, roll back a failed generation, reject new closing-season imports, and remove discarded
  sealed endpoint reads. Both production review threads have replies and are resolved.
- Fresh pre-merge follow-up evidence: 43 focused production tests; equivalent mirror full offline
  suite **4,152 passed / 57 skipped in 169.69 seconds**, four operational logs unchanged. Pre-commit,
  type/lint/secrets, architecture, deferred, routing, smoke imports and registration (36 / 101) passed.
  Production Quality and gitleaks checks passed before merge. This closeout does not rerun runtime tests.
- Exact final production Changes review `092cb991-5be6-4be6-86e6-1633413b7342`, Deep off, sealed
  with zero findings and no snapshot warning. Earlier mirror follow-up review
  `3a6bdc33-cf7c-4e41-88d2-bbdab251a8a4` had unchanged runtime bytes but subsequent test formatting;
  the final production review covers the complete applied patch. Earlier Bot/SQL reviews remain retained.
- S8B approved disposable evidence: backup, VERIFYONLY and actual restore; migration preview/apply/
  rerun; **50 SQL cases passed in 25.09 seconds** against their recorded source hashes. Preserve
  `K98_S8B_Disposable_20260913_validation`, `K98_S8B_Disposable_20260913_validation_restore`, backups,
  files, synthetic data and receipts. Later PR fixes are offline/static validated, not a fresh run
  of those SQL cases. The SQL runner's supported input/session/history path is offline-tested only.
- S8A's six disposable scripts and VERIFYONLY evidence are separate historical evidence; S8A did
  not perform an actual restore. S8B's later actual restore does not rewrite the S8A record.
- S6-OPS01/PERF01/CAP01 retain their recorded open operational components. Preserve uncertain
  publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`,
  all predecessor evidence, databases and retained provider files. Acceptance does not authorize
  retrying, cleaning or reconciling them.

Full S8B evidence is in the [archived task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).
The [S7/S8A closeout](s8a_closeout_and_s8b_handoff.md), approved contract/manifests and release
evidence remain active references; only completed S8B task pack/starter are newly archived.

**S8C is ready to start in a new chat for initial review/scope only.** Use the
[S8C task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md)
and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8C%20Intake%20and%20Admin%20Pairing%20UX.md).
Its 13-path S7 boundary includes seven runtime, five test and one command-reference path.
Scope approval is needed before S8C implementation; no new chat or implementation is started here.
S7 decisions and S8B acceptance remain settled. S8C is intake/admin UX; S9 ordinary public routing
and S10 export workers remain outstanding. SourceRouting.Enabled alone cannot activate those paths.
No bot-machine deployment or activation readiness is claimed by readiness to scope S8C.

## 3. Exact documentation carry-forward manifest

Every physical Bot path listed below MUST accompany the eventual separately authorized S8C Bot
PR alongside its 13-path implementation manifest. Include both source deletion and destination
of both S8B archive moves; preserve existing uncommitted documentation when branching. No path
may be omitted merely because it predates implementation. If separately merged first, retain
specific commit/content proof. Verify actual PR `filename` plus `previous_filename` against the
union, including production promotion. Do not require duplicate edits to unchanged S8B paths
already proven delivered in section 1.

30 physical Bot documentation paths:

| Action | Repository-relative path |
|---|---|
| Modify | `README-DEV.md` |
| Modify | `docs/reference/README.md` |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` |
| Create | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` |
| Modify | `docs/reference/local_sql_development.md` |
| Delete (archive origin) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S8B Bot Source and Matched Update Services.md` |
| Create | `docs/task_packs/Codex Chat Starter - KVK Source Migration S8C Intake and Admin Pairing UX.md` |
| Delete (archive origin) | `docs/task_packs/Codex Task Pack - KVK Source Migration S8B Bot Source and Matched Update Services.md` |
| Create | `docs/task_packs/Codex Task Pack - KVK Source Migration S8C Intake and Admin Pairing UX.md` |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` |
| Modify | `docs/task_packs/README.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8B Bot Source and Matched Update Services.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8B Bot Source and Matched Update Services.md` |
| Modify | `docs/task_packs/archive/README.md` |

Separate SQL carry-forward against `3983522feb0ff90c96ba56ca11c2dac177f84ca6` has exactly two
Modify paths in C:\K98-bot-SQL-Server: `docs/SQL_DELIVERY_LOG.md` (closeout append/status) and
`migrations/README.md` (closeout status over the historical authoring checkpoint). These need a
later separate SQL PR or path-specific merged-content proof. The prior complete log is already
merged in #81. Neither SQL document belongs in the Bot PR; no SQL implementation edits are selected.

## 4. Closeout validation and authorization boundary

Documentation-only update: status, evidence, task preparation, archival and relative links. No
runtime/test/config/schema/dependency/permission/persistence behavior changed. Security routing:
documented skip for the exact Bot documentation manifest and separate two-path SQL docs delta. Future
S8C implementation requires Changes at its exact Bot Git target, Deep off, and an independent SQL
decision. No standard/deep scan, runtime smoke or SQL execution is performed for this closeout.

Architecture, deferred, routing, exact-path test selector, whitespace, link and manifest checks
passed: all 30 physical Bot documentation paths match the local delta; all 426 relative Markdown
links resolve; S8C's 13 implementation paths match S7 exactly and exist. Runtime pytest, import
smoke and registration are skipped because no executable files
changed; earlier runtime results above are historical evidence. No unrelated refactor or deferred
item is introduced. All documentation remains local and uncommitted for the required future PRs.
No Git stage/commit/push/PR/merge, SQL connection, provider/Discord action, real import/export,
bot-machine pull, restart, deployment, activation, predecessor operation or new chat is performed.


## 5. Subsequent S8C implementation checkpoint — 2026-09-13

The operator subsequently approved the revised S8C implementation. The historical closeout
and evidence above remain unchanged in meaning. The current exact union is 39 Bot implementation
paths plus the 30 documentation paths in section 3 (69 physical paths), including the directly
affected command-registration regression test. The approved amendment in
[integration_implementation_manifests.md](integration_implementation_manifests.md) enumerates it.
SQL now has the separate six-path authoring union recorded there; its two original documentation
carry-forward paths remain mandatory and must not enter a Bot PR.

Local implementation includes owner-scoped durable setup/configuration reviews, explicit paired
UpdateID confirmation and waiting-side completion, all three attachment entry modes, imported B0
prerequisites, later within-season window assignment, and reviewed configuration corrections.
Supplied kingdom/camp aggregates and DKP remain authoritative. Controls remain default-off.
Offline validation and independent exact-patch security results belong to this implementation
checkpoint and the task's final report, not to retained S8B/S8A evidence. SQL fixtures are authored
but unrun. No deployment, operator smoke, post-merge run, remote PR path verification or external
action is claimed. Eventual PR checks must inspect filename AND previous_filename against the union.


### S8C PR preparation evidence

The operator reviewed the local implementation and authorized separate Bot mirror and SQL PRs,
ready for review. Full offline pytest passed 4,202 tests / 62 skipped in 130.47s; production
operational logs were unchanged. Architecture, deferred-items, security-routing, test selection,
import smoke, command registration (36 top-level / 101 grouped), Ruff and Black checks passed.
Configured Pyright returned zero errors and five environment import warnings. SQL text-only
contract validation passed 13 checks; the disposable SQL fixture and five S8C SQL cases are unrun.

Changes reviews with Deep off completed with zero findings: Bot
`d5641b69-74b3-4241-b7c5-fbc992350b2b` (22 production source paths) and SQL
`00c2caf5-e6ce-4ace-816b-268120f8aabd` (four source paths, plus two documentation paths).
Subsequent PR-preparation changes are documentation/status/evidence and mechanical hook formatting
only; executable review coverage must be rechecked if executable behavior changes.

These results do not replace retained S8B operator acceptance or its 50-case SQL evidence, or
S8A's separate six-script evidence. No S8C SQL execution, Discord/provider operation, production
promotion, bot-machine action, deployment or activation is authorized by PR creation. PR file
verification must cover all 69 Bot physical paths using filename and previous_filename, and the
six separate SQL paths. Runtime SQL and operator journey evidence remain outstanding.

### S8C PR review corrections

Addressed the two Bot review findings: selected_update_id now comes from the retained complete
selection result while update_id preserves the requested identity; weights column validation now
precedes original-token capture, which still runs before coercion. Regression coverage includes
retained-target/no-result outcomes and each missing required weights column. Full offline suite:
4,208 passed / 62 skipped in 135.31s, production operational logs unchanged; focused review/config
checks: 53 passed / 5 skipped. Follow-up Changes security review
43ab3fde-0947-4cec-b320-1200fa1a3e63 completed with zero findings, Deep off, against PR head
54c7f2087c91cae8c2d6fd527487625a180cd77f. Prior full S8C review remains separate evidence.
SQL review fixes align forward-fix-only metadata, NOCOUNT and Unicode fixture literals. Separate
SQL Changes review 1f23bee6-0463-4fa7-9eff-6b11a538270f completed with zero findings, Deep off,
against 2f419bfbee3124e5bb88b6b94c9768164d431c15; 13 SQL text-only checks pass. No SQL executed.
The exact 69-path Bot and 6-path SQL unions remain unchanged; retained S8B/S8A evidence is distinct.
