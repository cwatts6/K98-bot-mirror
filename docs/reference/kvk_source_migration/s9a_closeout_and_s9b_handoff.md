# S9A closeout and S9B handoff

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

> Historical handoff: **S9B repository-delivered; not deployed**. See [S9B closeout / S10A scope and exact documentation carry-forward](s9b_closeout_and_s10a_handoff.md).
> Retained evidence and historical approvals below remain intact; no predecessor rerun or live operation is authorized.

## Delivered state — 2026-09-14

**S9A implementation, review and repository delivery are complete.** The operator reports all
three PRs merged and pulled locally. Read-only GitHub merge/file checks and local Git object checks
confirm the following. Both repositories were on main and clean at documentation-closeout entry.
No changes have been pulled to the bot machine; no deployment or activation is claimed.

| Repository | Merge UTC | Merge commit | Final reviewed head |
|---|---|---|---|
| [Mirror #276](https://github.com/cwatts6/K98-bot-mirror/pull/276) | 2026-09-14 10:13:29 | `59e421cba38c899c7035a7bd3c60968e860c262a` | `964d0806db7353dfc9ecb82abb484d7feddc902f` |
| [Production #583](https://github.com/cwatts6/K98-bot/pull/583) | 2026-09-14 10:14:17 | `a6220dc42d6bb5301afca873e5f1c72e958cd2cd` | `7a0d86ccb2c4ab51025a7d951f22c2835ba6eb30` |
| [SQL #83](https://github.com/cwatts6/K98-bot-SQL-Server/pull/83) | 2026-09-14 10:13:01 | `278b24b48ed075252217a5525ccb751f8e5bf928` | `810ade56faa25f9e0333e0175b753bfa326190dd` |

Comparison anchors, **never reset instructions**: Bot HEAD/main/origin main
`221e1515c3983c3e56f2c11f5742f360b7b10e49`; production/main
`a6220dc42d6bb5301afca873e5f1c72e958cd2cd`; SQL HEAD/main/origin main
`278b24b48ed075252217a5525ccb751f8e5bf928`. Recheck at the next task's entry.

Each Bot PR has 56 GitHub file entries covering the exact **58 physical paths** after including
`previous_filename` for both S8C archive moves. All resulting blobs match the synchronized local
Bot HEAD; old archive origins are absent. This covers all 20 S9A implementation paths and the
approved 38-path S8C carry-forward (36 documentation paths plus the smoke script and its test).
SQL #83 contains exactly `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`; both blobs match
local SQL HEAD. None of that delivered union remains missing. Exact merged-file/blob proof was
retained locally at `C:/Users/cwatt/AppData/Local/Temp/k98-s9a-merged-closeout-proof.json`;
merged PRs and Git objects remain the durable sources for re-verification.

## Delivered behavior and review follow-up

Ordinary reporting callers resolve the fixed season source and matched complete UpdateID/publication,
with capability/availability checks and no silent legacy fallback for a new-source season.
Previous complete context is explicitly labelled during pending configuration. Immutable SeasonRead
and persisted v4 preview identity prevent silent retargeting; final actions recheck freshness.
Heavy result reads run outside the season authority lock; authority/results/metadata use three
connections with subsequent action validation. No report cache was introduced; full identity is
available for consumers. This is structural robustness evidence, not measured production performance.

Authoritative aggregates/DKP/overall, B0, UTC starts, daily SCANORDER, unused retained scans,
movable within-season windows, exact endpoint chain, CAS/sealed inputs, durable UpdateID,
explicit counterpart attestation and admission locks remain preserved. Stats/target card context
and grouped admin dispatch remain S9B; coordinated exports remain S10.

The Bot review's explicit-legacy empty send/claim regression was fixed in `7300de8`; both SQL
comments correcting historical execution/publication wording were addressed in `810ade5`.
All three inline review threads were answered and resolved. SQL CI's cross-repository documentation
reference was corrected in `9b393a7`. The promotion whitespace failure was corrected in `964d0806`
by replacing two Markdown trailing-space breaks in the S8C operator instruction with paragraphs.
The corrected production PR subsequently passed validation and merged; that does not deploy a bot.

## Retained validation and evidence limits

- Final S9A offline suite: **4,290 passed / 62 skipped**, 179.54 seconds; operational logs unchanged.
  Latest focused regression set: **82 passed**. Architecture, deferred-items, security routing,
  test selection, import smoke and registration (36 top-level / 101 grouped) passed, as did the
  applicable pre-commit hooks and strict complete-delta whitespace validation.
- Production #583 Quality passed 2026-09-14 10:10:28 UTC (run 34831284514) and gitleaks passed
  10:04:44 UTC (run 34831284509). SQL #83 static CI passed (runs 34827289716 and 34827284654).
  No hosted mirror checks were reported; do not infer mirror CI from the production checks.
- Bot Changes review `8ef160c4-f5ae-4004-b88e-04e808f38f1b` and incremental review-fix Changes
  `72bb84e5-f375-4bc8-9399-87079602b116` returned zero findings, Deep off. Their exact targets,
  recovery notes and coverage are retained in the archived S9A pack. SQL #83 was documentation-only,
  with an independent documented security skip, not a Bot scan substituted for SQL review.
- These are retained pre-merge results, not newly executed smoke tests in this closeout.
  No fresh SQL/provider/Discord execution, real import/export or predecessor rerun occurred.

See [S8C execution/operator evidence](s8c_folder_intake_smoke_evidence.md) and
[retained operator work instruction](s8c_operator_work_instruction.md): separately approved disposable
SQL and automated folder smoke passed; Chris reported PASS on all seven local operator checks on
2026-09-14, verified against the retained transcript. Synthetic/local actors are not live Discord
acceptance. Preserve the transcript and all inputs, outputs, databases, backups and receipts.
[S8B accepted smoke/50-case and offline runner-history evidence](s8b_closeout_and_s8c_handoff.md)
remain distinct from [S8A six-script evidence](s8a_closeout_and_s8b_handoff.md) and S8C evidence.
Repository merge is not applied SQL or deployed runtime evidence.

S6-OPS01, S6-PERF01 and S6-CAP01 remain open with their existing owners and accepted evidence.
Preserve uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and
`54a2480a-26fb-5bad-a3f5-9321525a731c`; no blind retry, reclaim or cleanup. All retained external
evidence stays local. Only completed S9A task documents are archived; evidence/work instructions,
contracts and operational references remain available. No database or external artifact is archived.

## S9B handoff and mandatory delivery grouping

The operator approved this documentation update/archive on 2026-09-14. S9B starts with review/scope
only using its task pack and starter below. It has exactly **22 approved runtime/test paths**, all
existing at this handoff. Any runtime/test/SQL amendment requires explicit scope approval.
The completed S9A pack/starter retain all historical approvals and execution/review evidence.

The eventual separately authorized S9B Bot PR **must include the complete exact union** of those
22 paths and the pending Bot documentation manifest below, plus approved amendments, or prove
specific paths already merged. Validate actual GitHub `filename` **and** `previous_filename`,
including old/new sides of archive moves; counts alone are insufficient. Do not create a standalone
documentation PR or seek renewed approval for this grouping. Recheck pending work before publication.
These are new post-S9A documentation changes; do not confuse them with the already-delivered S9A58.

Separate SQL carry-forward is exactly `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md`, in a
separate SQL-repository PR during the S9B delivery cycle. They must never enter the Bot PR.
This grouping does not authorize implementation, staging, commit, push, PR creation or SQL execution.

- [S9B task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S9B%20Stats%20Target%20Card%20Context%20and%20Admin%20Dispatch.md)
- [S9B starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S9B%20Stats%20Target%20Card%20Context%20and%20Admin%20Dispatch.md)
- [Archived S9A task pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S9A%20Public%20Routing%20and%20Availability.md)
- [Archived S9A starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S9A%20Public%20Routing%20and%20Availability.md)

### Exact pending Bot documentation manifest

**35 physical Bot documentation paths** after the approved S9B amendment: includes both origins and destinations of the
two S9A archive moves. The amended S9B delivery union is **58 physical Bot paths**
(23 runtime/test + 35 documentation). The original pre-amendment union was 56. SQL's two paths
are separate. This manifest reflects the complete local pending set at this closeout.

| Action | Exact Bot path |
|---|---|
| Modify | `README-DEV.md` |
| Modify | `docs/reference/README.md` |
| Modify (approved S9B amendment) | `docs/reference/canonical_command_reference.md` |
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
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` |
| Modify | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` |
| Modify | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` |
| Modify | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` |
| Add | `docs/reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md` |
| Modify | `docs/reference/local_sql_development.md` |
| Archive origin (remove) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` |
| Add | `docs/task_packs/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` |
| Archive origin (remove) | `docs/task_packs/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` |
| Add | `docs/task_packs/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` |
| Modify | `docs/task_packs/README.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` |
| Archive destination (add) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` |
| Archive destination (add) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` |
| Modify | `docs/task_packs/archive/README.md` |

## Documentation-closeout validation and security decision

This task changes only Markdown status, evidence references, task scope and archive navigation.
Bot and SQL each have a documented security skip via k98-security-review-routing: no executable,
permission/configuration, SQL/data-access or persistence behavior changes. No Changes, Codebase
or Deep scan is launched. Runtime pytest/import/registration and SQL execution are skipped for
this documentation-only task; retained S9A results above must not be relabelled as new execution.
Validation passed on 2026-09-14: architecture (0 Python files), deferred-items (32 existing
Markdown files), security routing (0 errors/warnings), and exact-path test selection. The selector
recommended import/registration checks; both are explicitly skipped because this patch changes
no Python or command registration. All 519 local Markdown links across the changed Bot/SQL
documents resolve. The exact 34-path pending Bot manifest matches Git status; the S9B table matches
all 22 S7 paths, with no overlap, giving a 56-path initial Bot union. SQL has exactly its two
specified Markdown paths. Both archive moves preserve the original S9A text/order except for
added archival headers and relocated links. Strict Git diff whitespace and every added/new-file
line passed; pre-existing untouched README whitespace is outside this delta.

Security skip targets: the exact Bot Markdown working-tree manifest above against
`221e1515c3983c3e56f2c11f5742f360b7b10e49`, and independently the SQL two-document working-tree
patch against `278b24b48ed075252217a5525ccb751f8e5bf928`. Both indexes remain empty. No runtime
code/test, SQL script, config, external evidence, retained database or Git ref was changed.

## S9B implementation authorization — 2026-09-14

The operator approved the initial review and implementation plan with the two exact path
amendments: `commands/kvk_targets_card_posting.py` for send/edit/retry freshness, and
`docs/reference/canonical_command_reference.md` for existing grouped-command semantics.
The original 22 runtime/test paths remain in scope; the amended runtime/test scope is **23**.
The mandatory documentation carry-forward is now **35 physical paths**. The eventual Bot
union is **58 physical paths**, including both sides of both S9A archive moves. This approval
permits local implementation and offline validation/review, not staging, commits, publication,
live operations or activation. The original scope-only starter below is historical.
SQL's two pending documentation paths remain a separate SQL PR in the same delivery cycle.

### S9B scope review and implementation record

Ordinary `/kvk stats` dispatch is `commands/kvk_cmds.py` → personal stats service/select view →
`commands/kvk_stats_card_posting.py` → stats card service/DAL → payload/renderer/transient view.
`commands/stats_cmds.py` owns grouped admin commands and redirects, not the ordinary card entry.
Targets posting → targets service retains independent target DAL/publication metadata, exemption,
last-KVK history and KS4 inputs, adding only shared fixed-source context. No target arithmetic,
roster/history/daily pipeline, source writer, activation or S10 coordinator was changed.

Scope risks: mixed legacy/new camp or rank; selecting the display fight instead of overall;
stale complete selection during render/retry/cached interaction; changing independent numerators
or target provenance; private diagnostics misrepresenting pending matched updates; uncoordinated
exports; admission locks held across expensive work. The implementation uses the unique season
`overall` key, the S9A `SeasonRead` identity and `load_complete_report` (sealed matched UpdateID,
publication/config/roster plus digest validation). Small authority transactions close before heavy
row loading/rendering. Available camp/rank comes from supplied overall and frozen B0. Unavailable
context retains independent values and never invokes a legacy camp/rank fallback. Transient views
pin a copy of the whole payload and reject identity, owner, guild/channel/message, permission or
expiry changes. The view lasts 300 seconds and is not registered as persistent across restarts.

Grouped scans dispatch to the fixed registry and retain unused logical scans/UTC precision.
Window previews are private configuration/complete-selection metadata, explicitly distinct from
public serving acceptance. Same-config pending counterpart updates are labelled. New-source
recompute only inspects metadata; legacy EXEC is inside the source admission transaction. Both
existing export commands reject before invoking either runner, including legacy exports, until
separately scoped coordinator admission exists. No top-level command was added.

Authoritative SQL review used the locally merged schema/migrations at the recorded SQL anchor:
`dbo.KVK_Details`; `KVK.SourcePeriod`, `SourceCompleteSelection`, `SourcePublication`,
`SourceUpdate`, `SourceConfigVersion`, `SourceConfigRequest`, `SourceWindowConfig`,
`SourceObservationRevision`, `SourceObservation`, `SourceLogicalScan`, `SourceCampConfig`;
legacy `KVK_Player_Windowed`, `KVK_CampMap`, `vw_Player_Overall_KVK_Rank`, `KVK_Scan`,
`KVK_Windows` and `sp_KVK_Recompute_Windows`. No missing schema object or SQL runtime
amendment was identified. No SQL was executed. Authoritative aggregates/DKP, exact endpoint
chain, UTC starts/daily SCANORDER, movable within-season windows, unused scans, CAS/sealed
inputs, explicit counterpart attestation and durable UpdateID remain owned by existing code.

Validation is in progress. Newly run evidence will be recorded here; historical S9A/S8/S6 results
above are not evidence for the S9B patch. Required gates are focused/adjacent/full offline tests,
operational-log isolation, architecture/deferred/security-routing validators, exact-path selection,
import/command registration, synthetic stats/target renders, final Bot Changes review (Deep off)
and normal whole-change review. SQL is independently docs-only; its two inspected Markdown
diffs have no runtime/config/schema/security effect and qualify for a documented scan skip.

Delivery coverage is an exact set comparison, not a count assertion. The final Bot manifest is
the original 22-row task-pack table plus `commands/kvk_targets_card_posting.py` plus every row
of the 35-path documentation table above. Both removed S9A origins and both archive destinations
must be included via `filename` and `previous_filename`. No already-merged exemption is claimed.
No PR exists for this work, so provider filename/previous_filename verification remains a gate for
separately authorized publication; local status/path/content evidence cannot substitute for it.


### S9B local validation and review complete — 2026-09-14

Local implementation is complete at the approved 23 runtime/test paths. No staging, commit,
push, PR, SQL execution, provider/Discord operation or bot-machine action occurred. Both indexes
remain empty and all recorded Bot/production/SQL anchors still match. SQL retains exactly its
two pre-existing Markdown changes; no SQL runtime amendment or SQL worktree edit was made.

| Gate | New S9B evidence |
|---|---|
| Focused ten-path card/admin suite | 155 passed in 12.69s at the pre-final checkpoint; operational logs unchanged |
| Final full offline suite | **4,333 passed, 62 skipped**, 157.98s; `RUN_DB_TESTS=0`; operational-log wrapper passed |
| Regressions fixed before final run | Sparse compatibility source provenance no longer crashes renderers; grouped export status retains resolved season wording without claiming a runner started |
| Architecture | 23 Python files checked, passed |
| Deferred-item validator | 33 existing Markdown files checked, passed |
| Security-routing validator | 0 errors, 0 warnings |
| Exact-path test selector | Completed; recommended stats/leadership/mykvkstats/UI imports plus full tests, smoke imports and registration; full suite includes these adjacent tests |
| Imports | Import-only smoke passed with test/no-login/startup guards |
| Command registration | No top-level drift or duplicates; `/kvk_admin` remains 8 children, below 25 |
| Python hygiene | Ruff passed on all 23 changed Python paths; Black formatting applied via API after the Windows CLI stalled; final whitespace check passed |
| Synthetic visual review | Stats main/more and targets, current/missing/stale, Unicode/long names; independent values and target publication labels retained, no clipping of source labels |

S7 mapping: T02 ordinary calls without injected context and capability/unavailability states;
T16 relevant independent stats/target/history/daily regression coverage; T52–T55 complete-identity
and cached-view expiry/change checks; T60–T64 relevant mixed-card, independent-consumer and
permission boundaries. C35–C38, C40, C42–C43, N06 and N11 changes are covered by the scoped
card/admin tests. C41/C53/C54 and the remaining C01–C65/N01–N12 ownership are preserved,
not claimed migrated. The full suite includes retained source pairing, reporting, public routing,
admin, lifecycle and independent-consumer regressions. This is offline evidence, not SQL/live
Discord acceptance or a production performance measurement; S6-PERF01 remains open.

Changes security scan **d9f0f04f-dfd6-4ffe-a5fa-f7194b15cfb6** completed at 11:18:36 UTC with
**zero findings**, complete changed-source coverage, Deep off, and three passed preflight checks.
Base/head: `221e1515c3983c3e56f2c11f5742f360b7b10e49`, working-tree snapshot digest:
`codex-security-snapshot/v1:sha256:ae97e3c1e29bc39e751a6f45fe928f88315cb1998cc362c6bfd538550e6bb842`.
All 13 runtime inventory entries were reviewed, with ten test paths and 35 documentation paths
also inspected. Root SECURITY.md was retained exactly as supplied threat-model context. No
candidate required validation/attack-path follow-up. Workbench usage reports **5,044,610 total
tokens**, including **4,865,792 cached input tokens**, across four threads; this is tool telemetry,
not a production performance or billing estimate. Canonical report and SARIF are retained under:
`C:/Users/cwatt/AppData/Local/Temp/codex-security-scans-rufA55/discord_file_downloader/221e1515c3983c3e56f2c11f5742f360b7b10e49_20260914T111219Z_zw9l1pls/`.

Normal `k98-pr-review` whole-change verdict: **local implementation/review complete; publication
not authorized**. No blocking regression or SQL drift was found. Security review explicitly
considered the independent public fallback: it retains pre-existing public delivery semantics after
stripping source context; it is not a private/source-context permission grant. All cached-view actions
and source-bearing sends revalidate their bound identity and permission. Existing export result
interfaces remain inert behind the S10 rejection boundary; no coordinator was added. No new
out-of-scope refactor or deferred item was introduced. Live acceptance, deployment/configuration
and the retained S6 gates remain separate, and no operational readiness is claimed.

These evidence-only Markdown additions follow the sealed scan. All 23 reviewed Python files
are unchanged, proved by SHA256 of the sorted path-to-file-SHA256 JSON manifest:
`e0a7c3e6badc602b4d0db49b0eae8e8f71bcbdfc3111ba970639017a36b08b4a`.
The post-scan documentation delta has no runtime/config/security effect and is covered by an
explicit documented scan skip; it does not relabel the sealed snapshot as including later text.

Exact final local manifest check: original 22 task-pack paths plus the posting amendment, and
all 35 documentation-table paths, match the complete `git status --porcelain -z` set with
**no missing or unexpected path**. Local proof is retained at
`C:/Users/cwatt/AppData/Local/Temp/k98-s9b-exact-manifest.json` (including every exact path).
There are **no already-merged exemptions**. Both archive pairs were checked individually:

| Archive pair | Origin exists in HEAD / removed locally | Destination local SHA256 |
|---|---|---|
| `docs/task_packs/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` → `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` | HEAD blob `9cb066b662eac4047997523a0b9f4a5929727dcc`; removed | `9221b464dd6ad90b14c8704cdca3d99c28894f9a3a6aa23a0351fc10b129b749` |
| `docs/task_packs/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` → `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` | HEAD blob `816831cba58960d54c35a95135fd932b1baf06fd`; removed | `722a4e66cf05162e1791a57560a1c8f894701fbba11c8f4df3e1e3fb2649388e` |

After separate publication authorization, compare provider `filename` **and** `previous_filename`
against this exact union. The two SQL paths must be in their separate SQL PR in the same cycle.
No standalone documentation PR and no regrouping question is required. Retain both uncertain
publication IDs, all databases/backups/files, S6-OPS01/PERF01/CAP01, S8B smoke/50-case and offline
runner-history distinctions, S8A six-script evidence, and S8C's seven local operator checks without
claiming live Discord acceptance. Final synthetic images are retained under
`C:/Users/cwatt/AppData/Local/Temp/k98-s9b-visual-lk7amm3c/` with `-final.png` suffixes.


### S9B PR publication authorization — 2026-09-14

The operator authorized creation of the Bot mirror PR and separate SQL documentation PR after
local implementation and review completed. This supersedes earlier publication-not-authorized
wording for these two PRs only. The approved exact Bot manifest remains 58 physical paths
(23 runtime/test paths and 35 documentation paths); SQL remains the two documentation paths.
Commit hooks and provider filename/previous_filename coverage are checked during publication
and recorded in the PR descriptions. This evidence-only update has no runtime/security effect;
the reviewed Python hashes remain unchanged. Merge, production promotion, deployment, activation
and all live execution remain outside this authorization.


### S9B PR review follow-up — 2026-09-14

Bot mirror PR #277 review correctly identified incomplete independent stats fallback output.
The follow-up reuses the existing independent three-embed formatter for history, personal bests,
last-KVK summary, matchmaking snapshot and T4/T5 breakdowns. It discards the optional dial file,
image and avatar, adds an explicit suppressed-source notice, and retains existing text-only
fallback transport. The formatter does not consume camp or source overall-rank fields; the
existing independent history cache remains separate from source authority. Regression coverage
exercises disabled rendering, empty/failed rendering, stale selection and failed image send,
with and without the existing fallback chain. No DAL, target or admin behavior changes.

SQL PR #84 review identified missing companion links and stale prospective publication wording;
its two documentation files are updated independently. Both PR manifests retain their exact paths.

The optional banner extraction is deferred because it is a separate consistency refactor; the
current review correction changes text fallback only and does not change the accepted card pixels.

### Deferred Optimisation
- Area: kvk/rendering/kvk_stats_card_renderer.py; kvk/rendering/kvk_targets_card_renderer.py
- Type: refactor
- Description: The three card renderers duplicate the 56px source-context footer composition.
- Suggested Fix: Extract a shared banner compositor in a later focused renderer change and verify all three layouts with pixel/geometry regression checks.
- Impact: low
- Risk: low
- Dependencies: Preserve current provenance labels, font fitting and accepted card geometry.


Follow-up validation: **4,343 passed, 62 skipped**, 180.86 seconds through the full offline
log-noise wrapper; production operational logs unchanged. Architecture/deferred/security-routing
validators and test selection completed; command registration, Ruff, Black, Pyright and staged
secrets checks passed. The hook normalized closeout Markdown line endings only. Local Markdown
links and exact Bot58/SQL2 manifest checks pass; published file coverage is rechecked after push.

Follow-up Changes scan **67b463d9-683c-44c6-951e-ab473a74c743** completed with zero findings,
complete coverage, Deep off, against `e2c8d5f47b6d8d3f4ac552a1ddd28ce72a782e8b` plus the
three-file review patch. Snapshot:
`codex-security-snapshot/v1:sha256:67631f4e8d21b05435e2e3251c4792ae921164750a7c8f8f65d745510b3fae2a`.
The initial S9B scan remains separate evidence for the preceding implementation; the original
all-23-files-unchanged statement describes that earlier checkpoint. The follow-up changes only
the posting module and its test among those Python paths. Their SHA256 values at review are
`1492f321a6a1829d5ead5b1172a904057376793e0cc8e8e59ed9a847a68a695e` and
`ec2ab24b70984490b1ec9858c27fcc6214f3b92abd431936653cfd15aa0b6fda` respectively.
This final evidence paragraph is a documentation-only post-scan delta with no runtime/security
effect and an explicit scan skip. Workbench telemetry reports 1,440,561 total tokens, including
1,392,640 cached input tokens, across two threads; this is not a billing estimate.
SQL review corrections retain the independent two-Markdown-file security skip; staged secrets,
whitespace and local links passed without SQL execution. All prior operational limits remain.


### Production PR #584 review corrections — 2026-09-14

Two production review comments are addressed on the mirror first, then applied as the exact
file patch to the existing production branch. Disabled stats cards now pass an explicit empty
context to the independent payload builder, avoiding source SQL/cohort loading. A guild card
check with a missing/non-permission-capable channel raises PermissionError before member lookup;
existing callers retain unavailable/suppressed output behavior. There is no permissive early return
for malformed guild channels. Focused posting/view tests pass (32 cases), including three disabled
flag values, three unavailable channel shapes, and an unavailable view interaction without edits.
The four Python paths and this closeout already belong to the approved 58-path Bot manifest.
No SQL paths or new command/export-coordinator behavior are introduced. Final validation and exact
mirror/production patch equivalence are recorded in production PR #584 before review resolution.
This is repository review work only; no merge, bot-machine pull, deployment or activation.
