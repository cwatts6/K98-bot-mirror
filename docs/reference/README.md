# K98 Bot Reference Docs

## Current status — S8A implemented; PR review in progress, 2026-09-12

S7's contract and manifests are approved; settled decisions remain closed. S8A SQL
files are implemented in [SQL PR #80](https://github.com/cwatts6/K98-bot-SQL-Server/pull/80).
Static validation and the separately approved six-script disposable checks passed.
The subsequent deployment-runner input fix passed offline checks and its exact
Changes security review; that new runner path has not been executed against SQL Server.

**Next: finish S8A review and repository promotion/merge checks, then separately scope S8B.**
Do not repeat S7 planning or request the already-granted S8A file-implementation approval.
The [S8A pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8A%20SQL%20Foundation.md) retains its original implementation scope and gates as history.
Any further SQL execution requires separate exact target, backup/row-preview and operation
approval. Bot runtime/config work, S8B implementation, deployment and activation remain gated.
SourceRouting.Enabled alone does not implement public routing.

Preserve all 27 Bot carry-forward paths, including both S6 archive move sides and both S7
outputs. Bot mirror PR #273 and production PR #580 are separate from SQL PR #80; verify
actual Files changed, including previous_filename, before merge. S1–S6 evidence remains
accepted; retain S6-OPS01/PERF01/CAP01, both uncertain publications and all retained databases
and files. Local deployment is operator-attested, not production runtime deployment or a
fresh post-merge smoke. Earlier dated blocks are historical and do not select the next task.

## Historical delivery — 2026-09-12 post-S6 closeout

**S6 evidence/rehearsal delivered, accepted and merged; feature activation remains blocked.**
Mirror [#272](https://github.com/cwatts6/K98-bot-mirror/pull/272) merged at
19:20:50 UTC as `016df1e61c8017556a7e8ba8374d31375aebfb74`; production-repository
[#579](https://github.com/cwatts6/k98-bot/pull/579) merged at 19:21:34 UTC as
`a8c9c515066ca6ef079120b76dd160e3389badab` (reviewed/final head
`b9c84751d3cc1deaba0a5772ab45d89263fcb398`). Mirror review fix `fa1f4733` records
the missing public routing consumer. Bot local main/origin main is
`a2f148fa9bd4fb367fd46d0500a768c14fee915b`; SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both were clean at this update's entry.

Operator reports merged and deployed locally, with nothing pushed to production.
GitHub confirms the production-repository merge above; **no production runtime or
bot-machine deployment, source activation, or fresh post-merge smoke is claimed**.
Local deployment is operator-attested; exact running process/config was not checked.

All preceding slices remain accepted. S6-OPS01/PERF01/CAP01 retain their open
operational components; accepted measured evidence is not pending reapproval.
The newly agreed requirements are fixed source per KVK for all affected outputs,
matched-pair public publication, confirmed reuse of an unchanged correction
counterpart, import-triggered serialized/latest-pending exports, export-only
recovery, retained input/publication history and safe output reuse after each KVK.
These are requirements, not claims of implemented behavior.

**S7 planning is complete and approved; S8A is implemented and under review.**
Follow the current status above; do not rerun predecessors or start later implementation packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](kvk_source_migration/post_s6_integration_requirements.md); [handoff and exact manifest](kvk_source_migration/post_s6_handoff_log.md); [S7 pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

> **2026-09-12 S6 authenticated rehearsal update:** The operator restored the ignored
> local credential and approved the 5,806-player × ten-period synthetic benchmark,
> confirming both other importers would remain idle. Actual Google write/readback
> and local K98DEV rehearsal evidence now supersedes the earlier credential blocker.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN for operator acceptance and the exact
> unresolved operational gates recorded in the latest appendix of both release
> documents and the S6 pack. No production activation or G5 acceptance is claimed.


> **2026-09-12 S6 output-provisioning update:** Separate S6 output creation was
> approved and completed: one private index and eight private slots, owner and
> service-account Editor metadata verified. Operator expectation is 2–3 exports/day,
> with no fixed maximum duration. Code review found no common lock across S6,
> all-KVK export and scan-data import. Runtime Google rehearsal is currently blocked
> by the missing configured local service-account key; no provider interruption or
> representative-load pass is claimed. All three S6 gates remain OPEN. See the latest
> provisioning appendix in the two release documents and S6 pack.


> **2026-09-12 S6 rehearsal update:** Chris Watts subsequently approved a local
> K98DEV database and beginning rehearsal. Synthetic local SQL/process checks passed
> in `K98_S6_Disposable_20260912`; no production activation occurred.
> S6-OPS01, S6-PERF01 and S6-CAP01 remain OPEN pending provider evidence and operator
> acceptance. Earlier G3-only/no-rehearsal statements below describe the retained
> preparation checkpoint, not the subsequent local rehearsal. See the dated
> rehearsal appendix in both S6 release documents for exact outcomes and gaps.


## Current S6 evidence preparation - 2026-09-12

**S6 G3 approved for documentation/evidence preparation only; stopped at G4.**
All preceding slices remain accepted; S5B-REC01 is closed. S6-OPS01, S6-PERF01 and
S6-CAP01 remain OPEN until separately authorized measurements and Chris Watts's acceptance.
G4 exact-operation approval and G5 acceptance remain operator-owned. No rehearsal, bot-machine
update, SQL operation, real import/export, Discord action, restart, deployment or activation.
The exact 18-path S6 documentation delivery includes all 16 pending closeout paths and both
S5B archive move sides. Eventual PR Files changed verification and promotion remain separately
authorized gates. Historical status blocks below retain their original dated evidence;
their pending/next-slice wording does not reopen accepted slices or authorize execution.

[Readiness and rollback](kvk_source_migration/release_readiness_and_rollback.md); [Canonical S6 evidence and delivery](kvk_source_migration/release_evidence_log.md).


## Current KVK delivery status - S5B closeout, 2026-09-12

**S5B is complete, operator accepted, successfully smoke tested and merged.**
Mirror [#271](https://github.com/cwatts6/K98-bot-mirror/pull/271) merged at 13:49:41 UTC as
`65c535dce831d0840f1a047b9c58f29c562df3df`; production
[#578](https://github.com/cwatts6/k98-bot/pull/578) merged at 13:50:14 UTC as
`c7e063f02ebe8287a584d0054ea14f91a0c0ecc6` on 2026-09-12, including final fix `e5bbd8f7`.
Local mirror main/origin main is `85f303f6bd82bdc9a5cfc2d713da5480e1fa694a`, synchronized from
that production merge; the final recovery fix and tests match production/main. This closes the
prior mirror synchronization handover item. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry. Local pulls are complete. The operator confirms
**no changes have been pulled to the bot machine**; repository merge is not runtime deployment.

Smoke acceptance is operator-reported and supported by recorded local import smoke and synthetic
recovery/transaction checks, not a fresh post-merge or bot-machine smoke. Final review-fix evidence:
186 focused tests passed, including five disposable SQL cases on local K98DEV database
`K98_S5B_Disposable_20260912`; split full suite 4,084 passed / 39 skipped, operational logs unchanged.
Imports, registration (36 top-level / 101 grouped), architecture, deferred-items, routing, lint/type
and staged secret checks passed. Production CI passed. Exact Changes review, Deep off,
`cf5a25c1-f9c6-431b-a2c6-fa9dba1716a7` completed with zero findings; earlier exact-slice evidence is
retained in the archived S5B pack. Historical results are not fresh tests of this closeout patch.

**Next: S6 Release Readiness and Controlled Activation in a new chat, after explicit S6 G3.**
All preceding slices remain accepted; S5B-REC01 is closed by accepted caller/lifecycle and disposable
SQL recovery evidence. S6 prepares documentation only and stops for separate G4 operational approval.
S6-OPS01, S6-PERF01 and S6-CAP01 remain open pre-activation evidence gates. G5 acceptance remains
operator-owned. The prepared S6 pack/starter require every pending closeout documentation change,
both S5B archive move sides and repaired links in the eventual separately authorized S6 PR.
No S6 execution or new chat is started by this closeout. Preserve all retained synthetic databases
and review evidence. Source routing and intake/recovery defaults remain disabled; no bot-machine
update, restart, production SQL, real import/export, Discord action, deployment or activation here.

## Historical KVK delivery status - S5A closeout, 2026-09-12

**S5A is complete, operator accepted, successfully smoke tested (operator reported) and merged.**
Mirror [#270](https://github.com/cwatts6/K98-bot-mirror/pull/270) merged at 08:53:35 UTC as
`c78823d5ae6852b251b2ea6dbc35fa2b4af7e42c`; private bot [#577](https://github.com/cwatts6/k98-bot/pull/577)
merged at 08:54:15 UTC as `dd69666a04daa47d6d596e694aff024a02417144` on 2026-09-12.
Local mirror main/origin main is `90aea74c93c6aad2c890d1783ff53f109cc7bf8a` (synchronized from that private merge);
local production/main matches the private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. **No changes have been pulled
to the bot machine**, as explicitly confirmed by the operator. Repository promotion is not deployment.

Successful S5A smoke is operator-attested; its detailed environment, commands and transcript were not
supplied in this closeout. Do not infer live SQL, real provider/Discord execution or a bot-machine smoke.
Recorded deterministic evidence remains 162 focused tests and 4,033 full tests passed / 34 skipped,
operational logs unchanged, import smoke passed, and registration 36 top-level / 101 grouped.
Every command group is <=25 children (kvk_admin 8; largest ops 24). Exact Changes review, Deep off,
scan `541665eb-2d37-4e14-8ce9-038329bf9653` has complete coverage and zero findings. Earlier gaps
remain historical in the archived S5A delivery; these tests/reviews are not fresh closeout reruns.

**Next: S5B Endpoint Config and Recovery Integration in a new chat, after explicit S5B G3 approval.**
S3B/S4B/S5A prerequisites are accepted. The S5B pack/starter are prepared; no S5B implementation or new
chat is started by this closeout. Recheck both repos and preserve the exact pending documentation
carry-forward manifest in S5B, including both S5A archive move sides and repaired links.
Use mocks/fake destinations until an exact disposable SQL target and operations are explicitly
authorized. S5B's required transaction/recovery SQL evidence remains a separate execution prerequisite;
full S5B acceptance cannot substitute mocks for that requirement. Preserve all retained databases.

S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open. S5A smoke does not close them. Source routing remains
disabled; intake/recovery defaults remain false. No bot-machine action, deployment or activation is
performed here. Historical statuses below are dated evidence, not instructions to rerun accepted slices.

## Historical S4B closeout - 2026-09-11

**S4B is complete, operator accepted, successfully synthetic-smoke tested and merged.**
Mirror [#269](https://github.com/cwatts6/K98-bot-mirror/pull/269) merged at 21:06:11 UTC as
`39c93df39485d796fd66881e47562da112886da1`; private bot [#576](https://github.com/cwatts6/k98-bot/pull/576)
merged at 21:06:38 UTC as `63fcb392385fd2ccad78801cbd4f8bd70f426cc3` on 2026-09-11.
Local mirror main/origin main is `64f6b058c224e749ece334d66cdf0efc81bd983d` (synchronized from the private merge);
local production/main matches that private merge. SQL main remains `44afa315dd6cbfe9fec101f2a39a62e534f5b583`.
Both repositories were clean at closeout entry; local pulls are complete. The operator confirms **no bot-machine pull**.

The archived S4B pack retains actual real-SDK/disposable-SQL synthetic smoke: private recovery,
public Viewer publication, fresh-client reconciliation/deduplication and retired-slot reuse succeeded.
These are historical bounded smoke results, not a post-merge live rerun. Final review-fix validation:
150 focused tests passed; full suites passed in both checkouts with 3,940 passed / 34 skipped
(production 166.93s, mirror 168.50s), operational logs unchanged. Imports and registration 36/100 passed.
Separate exact Changes reviews, Deep off, completed with zero findings; both review comments were resolved.
Production quality and secret CI passed. Earlier incomplete smoke attempts remain historical evidence.

**Next: S5A Private Intake and Admin Controls in a new chat, after explicit S5A G3 approval.**
S1/S3B/S4A/S4B prerequisites are accepted. Start with fresh repo/contract checks and preserve this pending
closeout documentation. The S5A pack requires its exact documentation carry-forward manifest, both sides
of both S4B archive moves, repaired links and this evidence in its eventual separately authorized PR.
No S5A implementation or new chat was started by this closeout.

S4B-MP01 is complete. S5B-REC01 and S6-OPS01/PERF01/CAP01 remain open under their named gates;
they do not block mocked S5A development and are not closed by S4B smoke. Source routing remains disabled.
No bot-machine update/restart, deployment, production SQL, real import/export or Discord action is authorized.
Use mocks/fake destinations; any disposable SQL target and exact operations require explicit authorization.
Preserve all retained predecessor and S4B disposable databases. Historical prerequisite wording below is
retained as history; accepted slices stay closed and S5A/S5B/S6 retain separate approval gates.



This folder contains active project standards, operating runbooks, and domain references.
Do not read every file for every task. Use the tiers below.

## Required For Every Repo Task

Read these before implementation work:

- `../../README-DEV.md`
- `K98 Bot - Project Engineering Standards.md`
- `K98 Bot - Coding Execution Guidelines.md`
- `K98 Bot - Testing Standards.md`
- `K98 Bot - Skills & Refactor Triggers.md`
- `K98 Bot - Deferred Optimisation Framework.md`

Read the task brief, issue, or task pack before these documents when one exists.

## Conditional References

| Area | Reference |
|------|-----------|
| Deferred optimisation backlog | `deferred_optimisations.md` |
| Deferred optimisation batching/scoring | `K98 Bot Deferred Optimisation Scoring Model.md` |
| Command reference and command-surface governance | `canonical_command_reference.md` |
| Promotion or deployment | `Promotion Guide.md`, `runbook_devops.md` |
| Environment variables or runtime config | `ENV_REFERENCE.md` |
| Local SQL setup or disposable integration testing | `local_sql_development.md` |
| Startup lifecycle | `runbook_startup.md`, `singleton_lock.md` |
| Shutdown/recovery lifecycle | `runbook_shutdown.md`, `singleton_lock.md` |
| Diagnostics, telemetry, offloads, queue recovery | `runbook_diagnostics.md` |
| Repo navigation | `runbook_structure.md` |
| Helper or shared utility changes | `REVIEW_HELPERS.md` |
| MGE work | `mge_reference_model.md` plus SQL repo validation |
| Honor ingestion | `honor_scan.md` |
| Event reminders and calendar reminders | `events_and_dm_reminders.md` |
| Weekly activity import | `weekly_activity_importer.md` |
| Security-sensitive work or Codex Security routing | root/applicable `SECURITY.md`, `AGENTS.md`, and the K98 security routing skill |

## Archive

Historical or consolidated notes live in `archive/`. Do not use archived files as active guidance.
Current standards and runbooks override archive content.

Archived examples include:

- historical quality automation task spec
- superseded helper standards note
- old rehydrate test note
- old operations note
- resolved deferred optimisation history

## Templates Live Elsewhere

Reusable task and initiation templates live in `../templates/`. Do not treat template generator
docs as mandatory reading unless the task is to create or update a task pack.

## SQL Source Of Truth

For SQL-facing work, validate object names, columns, procedures, views, indexes, and `ProcConfig`
usage against:

`C:\K98-bot-SQL-Server`

The SQL repo overrides inferred schema assumptions from Python code.

## KVK Source Migration audit

For migration work, read the [decision/evidence register](kvk_source_migration/decision_and_evidence_register.md)
and [Phase 1 audit](kvk_source_migration/phase_1_audit.md). The audit links the dependency and field
matrices, proposed next slice and validation log. Delivered 2026-09-09 for operator review;
B0/deployed-state/aggregate-period limits remain explicit. No implementation is approved.


## KVK Source Migration — Phase 2A architecture review

The 2026-09-09 bounded design pass is delivered: [contract and architecture](kvk_source_migration/phase_2_contract_and_architecture.md),
[synthetic acceptance scenarios](kvk_source_migration/phase_2_acceptance_scenarios.md), and
[evidence/validation](kvk_source_migration/phase_2_evidence_and_validation_log.md).
Latest B0, per-fight/final-overall and Pass-4 evidence supersedes earlier missing-input wording.
G2 awaits operator review; no implementation or Phase 2B packs approved. Local SQL/config parity
is operator-attested; independent live rows/jobs remain later readiness evidence.


KVK Phase 2A clarification (2026-09-09): authorized EndScanID changes are explicit player-window
corrections through normal configuration processing, without a separate correction command.
The contract and scenarios T68-T70 now cover interim scans, revised finals and pending endpoints.
G2 remains pending; no Phase 2B packs or implementation started.


## Phase 2B delivery and G2 approval — 2026-09-09

Chris Watts explicitly approved: **“G2 approved, please proceed”.** G2 is approved, including
the EndScanID clarification and scenarios T68–T70. This supersedes earlier G2-pending/no-pack
statements as current status; their historical evidence remains intact. Phase 2B planning is
delivered in the [implementation plan](kvk_source_migration/phase_2_implementation_plan.md)
and [planning evidence log](kvk_source_migration/phase_2b_evidence_and_validation_log.md).
Ten bounded task packs and matching starters are prepared. **G3 remains pending per slice; S1 is
the recommended first approval.** No implementation, SQL change, live action, PR or deployment
is authorized by this delivery. S6 prepares readiness evidence and stops at separate G4 approval.


## Historical S4B validation follow-up - 2026-09-11

S4B is accepted and merged; the current closeout record and archived pack supersede historical review-pending text. The remaining synthetic multi-period component test is complete. Track the [named follow-up register](kvk_source_migration/phase_2_implementation_plan.md#s4b-follow-ups) for S5B integration and S6 operational interruption, shared-quota throughput and capacity gates. These remain explicit acceptance work, not permission to execute future packs or activate routing.

## Post-S6 active navigation

- [Settled integration requirements](kvk_source_migration/post_s6_integration_requirements.md)
- [Closeout and next-slice carry-forward manifest](kvk_source_migration/post_s6_handoff_log.md)
- [S7 task pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md)
- [S7 starter](../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md)
- [Archived S6 evidence pack](../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md)
