# Archived Task Packs

## Current status — S7/S8A complete and merged; S8B next, 2026-09-13

S7's approved contract/manifests and S8A's SQL foundation are complete and merged.
The operator confirms successful smoke acceptance and local pulls; **no changes have
been pulled to the bot machine**. Retained S8A evidence includes six successful disposable
scripts; the later runner input fix has offline validation only. No fresh post-merge
SQL run, production runtime deployment or activation is claimed.

**Next: start S8B Bot Source and Matched Update Services in a new chat, review/scope first.**
Use the [S8B pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).
Read the [canonical closeout, merge evidence and exact S8B carry-forward manifest](../../reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md).
Do not reopen settled S7 decisions or repeat S8A implementation. Further SQL execution
requires exact target/backup/row-preview/operation approval; S8B implementation needs its
own approval after scope review. Public routing remains S9 work; SourceRouting.Enabled
alone does not implement it. S6-OPS01/PERF01/CAP01, both uncertain publications and all
retained databases/files remain preserved. Earlier dated sections are historical evidence.

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

**S7/S8A are complete and merged; S8B is next.**
Follow the current status above; do not rerun predecessors or start later implementation packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](../../reference/kvk_source_migration/post_s6_integration_requirements.md); [handoff and exact manifest](../../reference/kvk_source_migration/post_s6_handoff_log.md); [S7 pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

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

[Readiness and rollback](../../reference/kvk_source_migration/release_readiness_and_rollback.md); [Canonical S6 evidence and delivery](../../reference/kvk_source_migration/release_evidence_log.md).


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



## Programme boundary decision — 2026-09-09

The operator closed the Discord Embed Payload Safety approved implementation scope through
Phase 2K and moved former Phase 2L to **Bot Operational Reliability Workstream 1**.
The [new programme](../Bot%20Operational%20Reliability%20-%20Programme%20Pack.md) owns the proposed reliability workstreams; no implementation
is approved. Priority awaits comparison with the incoming missing-KVK-import and inventory-upload
privacy programme packs. Historical next-phase instructions below are superseded by this decision.
Natural Pre-KVK/off-season and Phase 2F public-save observations remain open independently.

Final Phase 2K closeout, 2026-09-09: mirror #262 merged at 12:06:38 UTC and production
#569 at 12:07:06 UTC. Verified mirror main: `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`;
production main: `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`. Operator supplied the same
production bot HEAD and empty `git status --short`. Associated restart invoked 12:08:56.672,
ready 12:09:10.755, full startup complete 12:09:15.539, new child PID 4800. This closes the
final deployment evidence gap; candidate smoke/test revisions below remain historical evidence.


This folder keeps completed task packs and chat starters for historical reference.

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Operator acceptance: 2026-09-08, Chris Watts. The Phase 2H pack/starter are archived.
Both Phase 2H PRs (#259 mirror / #566 production) await operator merge and final production-main
deployment/restart verification. The detailed receipt, hashes and limits are in the archived
Phase 2H task pack. Phase 2I Fighting-KVK Diagnostic Parity is the next scope-first task;
no Phase 2I implementation is approved. Phase 2F's natural public-save observation stays pending.


Discord Embed Payload Safety Phase 2E Ark Persistence Orchestration and Delivery Observability
completed its audit-first gate, review remediation, automated validation, final
Changes-only/Deep-off security review, candidate delivery, and operator smoke on 2026-09-07.
Focused verification passed `48`, Ark-plus-UI regression passed `204`, and the full suite passed
`3186 passed, 2 skipped`. Final scan `e7f618aa-0ab4-4934-a2d0-2bfb398ebf80` reviewed exact range
`06e34776eacf3c49db4a0b93077d5067069ae88e..cd973007f4b88de33ae50f3c455a42e724ced118`
with Deep off, all four changed runtime files covered, and zero findings. SQL was a no-diff skip.
The operator reported that messages posted and refreshed successfully. Mirror PR #256 and
production PR #563 contain the candidate and await manual merge plus final production-main
verification. The Phase 2E pack/starter and its completed team-builder/registration deferred items
are archived; confirmation-history remains keep-all/deferred. Phase 2F Active Reminder Tracker
Atomic Persistence is prepared as the next audit-first slice, with implementation not approved.

Discord Embed Payload Safety Phase 2D Operator Diagnostics Convergence completed implementation,
review remediation, automated validation, final Changes-only security review, production-candidate
deployment, and operator smoke on 2026-09-03. Focused review verification passed `64`, the complete
suite passed `3172 passed, 2 skipped`, pre-commit passed, and scan
`984d93ff-29b1-4dd3-b681-a9830d01a1c4` covered the exact production runtime range with Deep off,
all 11 runtime files covered, and zero findings. SQL was a no-diff skip. Restart, queue persistence
and rehydration, `/ops logs` and component interactions, `/ops show_logs`,
`/ops view_restart_log`, `/ops last_errors`, and the representative command set passed without
`File.to_dict`, Discord `50035`, traceback, command error, or error/critical entry. Mirror PR #255
and production PR #562 are merged, and final production-main source verification passed. Phase 2E
is archived above as candidate-delivered and operator-smoke accepted.

Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence completed its
evidence-led tests/documentation-only implementation, review, candidate deployment, and operator
smoke on 2026-09-03 through mirror PR #254 and production PR #561. Authoritative contracts proved
every live rankings/history payload safe, so no runtime correction was required. Focused validation
passed `79`; the full suite passed `3104 passed, 2 skipped`; Changes-only scan
`25a90732-3ad2-4ee0-9138-d1f4f11bbf36` covered all nine changed files with Deep off and zero
findings; SQL was a no-diff skip. Both PRs are merged, and final production-main source verification
passed. Phase 2D is archived above as delivered.

Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening completed implementation,
validation, Changes-only security review, production-candidate promotion, and operator candidate
smoke on 2026-09-02. Mirror PR #253's delivered tree is present on mirror `main`; production PR
#560 is merged in production commit `6da1c083`. The full suite passed `3090 passed, 2 skipped`; scan
`79603f53-69f8-4586-9296-760385dd9420` ran over the exact approved bot runtime range with Deep off,
complete coverage, and zero reportable findings; SQL was a no-diff skip. Smoke built a four-field,
346-character registration payload with no compaction/omission, retained `should_announce=False`,
and edited the existing message reference without state/identity change, duplication, or `50035`.
Phase 2C rankings/history is archived above as delivered and operator smoke accepted. Diagnostics,
Ark persistence and delivery observability, active-reminder atomicity, and atomic Pre-KVK
reservation remain assigned to Phases 2D through 2G rather than left unowned.

Discord Embed Payload Safety Phase 2A Event and Calendar Convergence completed implementation,
review, promotion preparation, and representative production smoke on 2026-09-02 through mirror
PR #252 and production PR #559, pending the operator's manual merges. Final automated validation
passed `3078 passed, 2 skipped`; the applicable Changes-only reviews ran with Deep off and found no
reportable issues. Restart smoke rehydrated the persistent pinned view, armed the reminder and
daily-refresh tasks, and edited message `1488086669876920341` in place for 27 events. Payload
metrics were `fields=15`, `chars=4789`, `max_field_value=533`, `compacted_events=0`, and
`omitted_events=0`, with no duplicate or Discord `50035`. Public/DM reminders and an omission marker
were not naturally forced during smoke; their unchanged behavior and boundary cases retain
automated coverage. Phase 2B is now archived above as delivered and candidate-smoke accepted.

Discord Embed Payload Safety Phase 1 completed implementation, review, promotion preparation, and
operator edit-path smoke on 2026-09-02 through mirror PR #251 and production PR #558, pending the
operator's manual merges. It delivered `core/discord_embed_limits.py`, the exact 1,029-character
Pre-KVK regression and complete-event packing, shared-sender overflow repair, and sole Pre-KVK
ownership of `prekvk_daily`. Focused validation passed `40` tests and the full/log-noise suites
passed `3059 passed, 2 skipped`; two Changes-only reviews ran with Deep off and zero reportable
findings. Live smoke validated 13 fields, 1,847 aggregate characters, a 530-character largest
field, and an in-place edit of message `1544617668999381044` with matching persisted state and no
duplicate or `50035`. The archived task pack, starter, and findings record preserve the delivery.
Phase 2A event/calendar convergence and Phase 2B Ark hardening are archived as delivered.
Rankings/history, diagnostics, Ark persistence/observability, active-reminder atomicity, and atomic
Pre-KVK reservation retain the named Phase 2C-2G follow-up sequence.

Pinned Calendar Tracker Atomic Persistence completed implementation, validation, Changes-only
security review, production deployment, and operator restart smoke on 2026-09-01 through mirror
PR #250 and production PR #557. The existing pinned message was rehydrated and edited in place
with unchanged channel/message identity, the tracker remained valid JSON with an advanced
`updated_at_utc`, no duplicate or stale temporary file remained, and the daily refresh scheduled
normally. Its task pack and chat starter are archived here as the completed execution record. No
SQL, config, dependency, command, permission, cache, reminder, scheduler, or user-facing behavior
change was delivered.

DL_bot Offload Callable Once-Only Failure Semantics completed implementation, production review,
automated validation, and operator Discord smoke on 2026-09-01 through mirror PR #248 and
production PR #555, pending manual merge. The smoke confirmed that a duplicate MGE import failed
as expected and that a standard scan import completed successfully with its route unaffected. Its
task pack and chat starter are archived here; upload admission/backpressure and the separate
once-only audits for `stats_module.py` and `ui/views/kvk_history_view.py` remain active deferred
items.

KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup completed through mirror PR #246 without a
runtime or SQL behaviour change. Its task pack and chat starter are archived here. The separate
MINI_AMD transaction-log backup cadence policy question remains active in the deferred register;
it is not unfinished Phase 5.2 work.

GovernorOS Phase 8.1 Leadership Player Review Visual Hierarchy, Presence and Performance completed
and was operator accepted on 2026-07-23. Mirror PR #231 and production PR #538 carry the bot
delivery; SQL PRs #58 and #59 supplied the additive rank and exact-ID existence support. Its task
pack and chat starter are archived here, while representative delivered-path performance evidence
remains separately deferred.

MGE Process Polish Phase 2 completed in mirror PR #75, then was production deployed and smoke
tested through production PR #386. Its initiation/delivery record is archived here as historical
service-boundary evidence; it is not an active MGE implementation pack.

King of All Britain KVK Card Background completed implementation, review, and operator visual smoke
on 2026-08-28 through mirror PR #244 and production PR #551, pending manual merge. Both KVK Stats
and Targets renderers select the pinned `1180 × 640` RGB production backdrop through the existing
normalised fixed mapping and unchanged fallback chain. Focused renderer coverage passes 32 tests,
the mirror and production Changes reviews ran with Deep Off and returned zero findings, and the
operator confirmed the live Stats and Targets cards display the backdrop correctly and look
perfect. Local Stats, More Stats, active Targets, and exempt Targets artifacts are retained under
`smoke_artifacts/king_of_all_britain/`. No SQL, command, payload, publication, permission,
persistence, or registration contract changed; deployment requires only the normal bot rollout and
restart. The archived task pack and starter are the historical completion records.

KVK Target Publication State Separation Phase 1 was deployed and operator accepted on 2026-08-26
through mirror PR #235, production PR #542, and SQL PR #73. The import-path transaction follow-up
was deployed through mirror PR #236 and production PR #543. Production publication metadata,
source-scan, row-count, cache rebuild, and Discord smoke checks passed. Its task pack and chat
starter are archived here.

KVK Targets Quality Phase 2 completed the deferred target-architecture programme through mirror
PRs #237-#242, production PRs #544-#549, and Phase 2A SQL PR #74. The six independently gated
slices delivered immutable typed target rows, one service-owned presentation-input path, a bounded
crash-recoverable target cache repository, explicit fighting-lifecycle terminology, lifecycle DAL
ownership, history rank result-set hardening, and final target interaction cleanup. Phase 2F
production smoke on 2026-08-28 passed history, targets, stats, CrystalTech, and shared account-picker
flows with clear logs. Its task pack and chat starter are archived here; the final follow-up review
found no new Phase 2 requirement or active target-subsystem deferred optimisation.

CrystalTech Path Refresh and Config Corrections completed operator smoke and acceptance on
2026-08-25 in mirror PR #234 and production PR #541, pending manual merge. The archived bundle
records the 404-step source contract, the 11 approved follow-up image/spelling corrections,
focused regression coverage, final security Changes review, clean-rollover/no-extant-progress
precondition, successful validate/reload checks, and two-user progression/reset smoke evidence.

Discord Voting Post Framework Phase 1 through Phase 22 execution records are archived here. The
programme delivered SQL-backed vote posts, button voting, one-vote-per-Discord-user enforcement,
vote changes, live Pillow result cards, scheduler reminders, automatic close, manual close,
persistent views, mention safety, guided admin UX, private totals-only export, private
admin/leadership voter-audit export, hidden-until-close result visibility, single-question
multi-select voting, choice-only multi-question surveys, private survey response-detail export,
SQL audit logging, free-text survey questions, choice-question details, optional survey questions,
fixed 1-5 rating survey questions, rollout-safe rating migration guards, production promotion, and
complete ranking survey questions, plus Phase 10 private Survey Export v2 report-bundle CSV output
and SQL survey reporting views/procedure, and Phase 11 private admin/leadership aggregate
dashboard-safe reporting contracts, and Phase 12 persisted survey drafts/resume with draft
exclusion from public results, private dashboard summaries, status totals, and existing export
profiles until final submit, Phase 13 private aggregate dashboard UI, and Phase 14 configurable
rating scales with fixed 1-5 compatibility, fixed 1-10 ratings, custom min/max scales, endpoint
labels, named rating choices, draft/resume compatibility, and private/public aggregate reporting
compatibility, plus Phase 15 per-option Unicode/custom Discord emoji support, guided option-polish
controls, Discord/status/dashboard emoji display including animated custom emoji, generated-card
custom emoji text fallback, and narrow dense-summary readability polish, plus Phase 16 guided
survey builder review/edit/delete/reorder controls and `/vote_admin survey_update` for safe
open-survey metadata updates with response-sensitive and closed-survey locks, plus Phase 17
`/vote_admin` command-surface audit closure with no runtime command change, plus Phase 18
cross-survey/workbook export redesign audit closure with no runtime export or documentation
guidance change because the current private exports are sufficient and understood, plus Phase 19
private leadership engagement dashboard delivery with compact top-level engagement metrics,
role-filtered eligibility, fixed rolling windows, best/worst single poll, one-Discord-user
counting regardless of governor IDs, raw-answer exclusion, and graceful dashboard timeout handling,
plus Phase 20 private per-user engagement CSV export delivery under `/vote_admin engagement`, and
Phase 21 private engagement graph assessment audit closure with no runtime graph implementation
because the CSV export remains sufficient until leadership defines a concrete graph requirement,
plus Phase 22 final retention/redaction policy and SQL-only admin delete delivery through
`dbo.VoteSurveyDeletionAudit` and `dbo.usp_VoteSurveyAdminDelete` with no bot runtime/UI changes.
Operator smoke/regression testing is complete through 2026-07-08, and SQL-only Phase 22 deployment
and smoke testing completed successfully on 2026-07-09 after SQL PR #39 and follow-up SQL PR #40
were merged and pushed to production.
The closed programme pack remains in `../`.

Player Self-Service Command Centre completed Phase 1 audit/design, Phase 2 `/me` shell
foundation, Phase 3 Modern Account Centre, Phase 4 Modern Reminder Centre, Phase 5 Visual
Dashboard Card and Preferences Hub, Phase 6 Guided Management Cards and Workflow Simplification,
and Phase 7 Unified Reminder Centre and Dashboard Card Alignment execution records are archived
here. The original programme is complete; its closed programme pack remains in `docs/task_packs/`.

Player Self-Service Command Centre v2 / GovernorOS completed Phases 1 through 8. The archived
records cover the dashboard blueprint/data foundation, governor selector and premium dashboard,
direct Inventory reports and visual alignment, Accounts, Reminders, and the authoritative shared
KVK/Calendar next-alert projection. Phase 5D.1 delivered in mirror PR #223 and production PR #530;
operator smoke accepted the final `/me reminders` presentation on 2026-07-15. Phase 5E Preferences
delivered in mirror PR #224 and production PR #531 and was deployed on 2026-07-16; its archived
records capture the accepted top-left-avatar Personal Settings card, local-time/UTC fallback,
regional profile, Inventory privacy flow, one Manage Settings journey, and Accounts-owned Update
VIP migration with no SQL deployment. The active v2 programme pack remains in `docs/task_packs/`.
Phase 5F Inventory Surface Consolidation and Legacy Retirement delivered in mirror PR #225, was
promoted at production-branch commit `89f7da16`, and was operator accepted after final Discord smoke
on 2026-07-16. Its archived records capture retirement of `/me inventory`, `/myinventory`,
`/inventory_preferences`, `/export_inventory`, public/combined Inventory viewing and the combined
export; preservation of the selected-governor reports and their three exports; the profile-first
Personal Settings reflow; final 39 top-level/8 `/me` command baselines; zero SQL change; and the
dormant rollback table. Phase 5G Account Data Export Consolidation completed final review,
deployment/resync, and operator Discord smoke on 2026-07-17 through mirror PR #227 and production
PR #534. Its archived task pack and starter record the canonical Account Summary Download data
journey, retirement of `/me exports` and `/my_stats_export`, the `38 / 7 / 2` command surface, all
three private output contracts, corrected workbook/history semantics, no SQL change, and the Phase 6
interactive Stats handoff. Phase 6 Interactive Period Performance completed final production Discord
smoke on 2026-07-18 through mirror PR #228 and production PR #535 after SQL PRs #43/#44 deployed.
Its archived task pack and starter record private-anywhere `/me stats`, the accepted 1702x924
Overview/Activity/Combat format, opaque paged governor selection plus explicit All Linked, exact
periods and coverage, source-refresh semantics, `/my_stats` retirement, preserved `/stats player`,
the `37 / 100 / 8 / 2` command surface, zero unresolved bot/SQL Changes findings, and final operator
acceptance. Phase 7 completed the retained `/me` visual/content closeout on 2026-07-19 through
mirror PR #229 and production PR #536. Phase 8 completed the one private `/stats player` leadership
journey, global canonical combat alignment, bounded source/audit/history contracts and
`/player_profile` retirement on 2026-07-21 through mirror PR #230 and production PR #537 after the
SQL migration series and merged follow-up SQL PR #53 deployed. Its archived records preserve the
accepted `36 / 100 / 8 / 1 / 2` command surface and production smoke evidence. The living v2
programme pack remains in `docs/task_packs/`; Phase 8.1 is complete and its execution records are
archived here. Phase 9 `/stats kingdom` remains separately proposed and gated.

Archived packs include completed registry/account-resolution, telemetry, stats, pytest
log-isolation and original slow-pytest optimisation, high-priority KVK state, MGE Phase 1 polish,
PreKvK schema standardisation, completed KVK Player Experience Redesign execution phases,
completed KVK_ALL phase initiation statements, the completed KVK_ALL Schema Modernisation
programme pack and supporting metric/source references, and the DL_bot upload-routing and
startup/lifecycle programmes.

KVK_ALL Schema Modernisation is complete through Phase 11. Phase 11 Acclaim Output Contract Polish
closed the final output-contract items by keeping max_contribute_gain internal, exposing
cur_contribute_gain as acclaim_gain in player-facing outputs, preserving the 10-result-set export
contract, preserving Google Sheets spreadsheet and tab names, and leaving Discord embeds unchanged.
Operator smoke evidence confirmed KVK.vw_FightingDataset now exposes acclaim_gain, Google Sheets
exports show acclaim_gain without Highest Acclaim gain, and KVK_ALL imports plus export completed
successfully. Future KVK_ALL work should start from a fresh task pack rather than continuing the
schema modernisation programme as Phase 12.

Import pipeline archives include Task A Import Process Schema Resilience and Shield Time Support,
which delivered fallback `Credit` / `Conduct Score` compatibility, interim auto partial fallback
overlay support, player-location shield timestamp persistence, and the temporary ASCII-safe SQL
bulk CSV hotfix. Task B Unicode Import Contract replaced the temporary ASCII fallback with raw text
SQL staging plus explicit typed conversion. Task C Slice 1 Import Architecture and Service/DAL
Wrappers extracted fallback import file orchestration and DAL helpers while preserving current
route, command, SQL, and import output behavior. Task C Slice 2 Durable Batch Audit Foundation
added SQL-owned durable import batch/phase audit tables and stored procedure writers, bot audit
DAL/service wrappers, and fallback-first audit wiring correlated to `dbo.FallbackImportBatchControl`
without changing route, command, queue, staging, SQL procedure, or import output behavior. Task C
Slice 3 Non-Fallback Audit Adoption mapped location, Honor, PreKvK, weekly activity, MGE, and
inventory import state surfaces, then wired player-location generic audit for the auto
`scan_1198.csv` route and `/location import` command merge path. Task C Slice 3A Import Audit
Batch Counter Normalization added optional `RowsInSource` support to SQL-owned terminal audit
writer procedures, threaded it through bot DAL/service wrappers, and smoke tested normalized
fallback and player-location batch counters without historical backfill.
Task C Slice 4 Honor Import Audit Adoption wired the KVK Honor upload/import path to generic
durable audit with `honor_xlsx_parse`, `honor_sql_ingest`, and `honor_post_import_refresh` phases,
correlated completed batches to `dbo.KVK_Honor_Scan`, preserved user-facing route/import behavior,
and smoke tested a completed Honor batch with 562 source/staged/written rows.
Task C Slice 5 PreKvK Import Audit Adoption wired the PreKvK upload/import path to generic durable
audit with `prekvk_xlsx_parse`, `prekvk_sql_ingest`, and `prekvk_post_import_refresh` phases,
correlated accepted batches to `dbo.PreKvk_Scan`, correlated duplicate/rejected batches to
`dbo.PreKvk_ImportHistory` when available, preserved user-facing route/import behavior, and smoke
tested accepted, duplicate, and rejected PreKvK outcomes.
Task C Slice 6 Weekly Activity Import Audit Adoption wired the weekly activity upload/import path
to generic durable audit with `weekly_activity_xlsx_parse`, `weekly_activity_sql_ingest`, and
`weekly_activity_post_import_backup` phases, correlated accepted batches to
`dbo.AllianceActivitySnapshotHeader`, left duplicate and failed-without-snapshot outcomes
uncorrelated, preserved user-facing route/import behavior, and smoke tested completed and duplicate
weekly activity outcomes.
Task C Slice 7 MGE Results Import Audit Adoption wired the MGE results upload/manual import path
to generic durable audit with `mge_results_xlsx_parse`, `mge_results_sql_ingest`, and
`mge_results_post_import_backup` phases, correlated accepted and post-domain-row failed outcomes
to `dbo.MGE_ResultImports`, left duplicate/pre-domain outcomes uncorrelated, preserved route,
manual overwrite, report, and importer behavior, resolved review hardening feedback, and was
reported smoke tested successfully on 2026-06-30.
Task C Slice 8 Inventory Import Audit Adoption wired inventory image uploads, command-session
imports, additional-material continuation, approval/reject/cancel/timeout/failure outcomes, admin
debug, and original-upload cleanup into generic durable audit while preserving inventory's domain
audit/history model and route UX. Accepted lifecycle outcomes correlate to
`dbo.InventoryImportBatch`. Operator smoke testing on 2026-06-30 confirmed resources, speedups,
materials, failure, and cancel audit outcomes, including a three-file material continuation with
`RowsInSource=3`, `RowsStaged=3`, and `RowsWritten=25`.
Task C Slice 9 KVK_ALL Import Audit Adoption delivered the KVK_ALL half of the split
KVK_ALL/Rally Forts audit-adoption scope in mirror PR #190 and production PR #498. It wired the
KVK_ALL upload route to generic durable audit while preserving route UX, embed text, importer
contracts, SQL ingest/recompute behavior, Google Sheet link behavior, and auto-export scheduling.
Accepted imports correlate to `KVK.KVK_Scan` using `ExternalBatchId=<KVK_NO>:<ScanID>`, and
KVK-details timestamp rejections correlate to `KVK.KVK_Ingest_Diagnostics` when a diagnostic id
exists. Operator smoke testing on 2026-06-30 confirmed completed batch 23 with `ExternalBatchId=15:83`
and 9194 source/staged/written rows, plus failed diagnostic batch 22 with `ExternalBatchId=2` and
9194 staged/skipped rows. Rally Forts was split into Task C Slice 10 and later delivered in
mirror PR #191 and production PR #499.

Task C Slice 10 Rally Forts Import Audit Adoption delivered generic durable audit for Rally Forts
uploads, correlated successful daily/all-time imports to `dbo.IngestionLog/<IngestionID>`, kept
duplicate/no-row/unrecognized/preflight/failure outcomes externally uncorrelated, and was reported
smoke tested successfully on 2026-07-01.

Task C Slice 11 Import Audit Phase Timestamp Normalization normalized generic
`ImportAuditPhase` timestamp handling in bot service and SQL writer boundaries, preserving
duration semantics, audit best-effort behavior, route/importer contracts, batch counters, external
correlation, SQL import behavior, user-facing behavior, and historical rows. Production smoke
testing on 2026-07-01 confirmed new fallback batch 27 and player-location batch 28 phase rows no
longer show `CompletedAtUtc < StartedAtUtc`.

Task C Slice 12 is complete and archived. The active import follow-up is Task C Slice 13, whose
July evidence/object map must be refreshed against the post-August KingdomScanData4 tree before
execution:

`../Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md`.

The DL_bot upload-routing and startup/lifecycle optimisation programme is complete through
Phase 6L:

- `DL_bot.py` remains process-entry, command-registration, signal, and message/upload owner.
- `bot_loader.py` remains bot construction owner.
- `bot_instance.py` remains lifecycle event, startup phase, task-supervision, and bot-side graceful
  teardown owner.

Remaining related work is tracked in `docs/reference/deferred_optimisations.md` as separate future
programmes, including command-surface migration, queue-domain redesign, optional SQL-backed queue
persistence, and disabled secondary command-surface cleanup. Pinned calendar tracker atomic-write
hardening is complete and recorded in `docs/reference/archive/deferred_optimisations_resolved.md`.

Phase 2F pack/starter: candidate delivered and restart smoke accepted via mirror #257 / production
#564; archived with explicit pending operator merges and final production verification.


## Prerequisite refresh — 2026-09-08

Phase 2F mirror #257 and production #564 are merged; production main is
`d9321328507add3b06704c25db2c6e59fe7352f6`. The operator confirmed deployment and successful restart.
This supersedes pending-merge preparation statements below; the next natural public save remains
unobserved. Phase 2G implementation subsequently completed; the closure below supersedes that intermediate status.


## Delivery closure and Phase 2H handoff — 2026-09-08

**Phase 2G is complete as an implementation and bounded-validation delivery, by explicit operator
acceptance. Full live Pre-KVK validation is carried forward to Phase 2H; it is not claimed complete.**
This status supersedes preparation and intermediate status statements in this historical record.

Mirror PR #258 and production PR #565 were both OPEN when this closure was prepared. Reviewed
runtime heads are mirror `bd99ea1421286ddb152f7729e11de664116d7e47` and production
`fea2767f52f345450225bcdf0c1f03f3d5e3dc4c`; their Python trees match. Documentation closeout commits
follow these heads. Operator merges, final production-main source verification and bot-machine
deployed-head verification remain pending. Supplied restart logs contain no immutable Git head;
they cannot prove deployment of the final merged source. Codex has not merged or deployed either PR.

Delivered: durable reserve/start/accept/commit/release, conservative uncertain-send retention,
receipt recovery, off-season coordination, generation/CAS fencing, bounded Windows CSV replacement
retries and off-loop fighting/stale-reference invalidation. Phase 1–2F payload, permission,
visibility, mention, eligibility, edit/test and executor contracts remain preserved.

Final validation: full **3314 passed, 2 skipped**, production log-noise pass; **91** focused tests
with pinned filelock 3.20.0; **67** production focused tests; strengthened lifecycle assertions
passed separately (**3**). Pre-commit, architecture/deferred/security-routing validators, selector,
smoke imports and registration (36 primary / 100 grouped) passed. Full suite evidence transfers
through verified Python-tree identity; it was not independently rerun in production.

Changes-only / Deep-off security: mirror full scan `43cd6ae2-7ea7-40b1-89e2-c916b16b79f1`
through `fd93202f`, mirror delta `90ad6945-fded-4367-b915-ee5964414523` through `bd99ea14`, and
separate production scan `eba7b5b2-73ad-4b39-8e64-263362802657` for `d9321328..fea2767f`
completed with zero reportable findings and no deferred candidates. The final documentation-only
delta changes no executable, configuration, dependency, SQL, permission or persistence control;
an additional security scan and pytest run are skipped for that delta, with documentation/hooks
and routing validators required. SQL manifest remains empty; authoritative repo was clean at
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`.

Operator log evidence, 2026-09-08 09:16:40–09:22:06 (timestamps as supplied):

- Graceful shutdown drained queues, persisted state and cancelled registered tasks. Full startup
  completed at 09:17:05; reminder/live-event views reattached and command registration was unchanged.
- At 09:21:50 the normal fighting KVK route skipped Kingdom Summary (already sent) and KVK
  publication (daily cap). The generic subsequent “sent successfully” line is not a send receipt.
- No `[DISPATCH] Reserved` / `Committed` evidence appears. Fresh Pre-KVK/off-season ownership,
  matching CSV/journal/message references and restart-after-commit remain unobserved live.
- ProcConfig failed at 09:20:17 while restoring `conn.autocommit` with pending SQL results;
  later success reporting masked that failure. This unchanged pipeline is separate work.
- Tracked-view rehydration timed out after 10 seconds; remaining generic tracked views are
  unverified. Google Sheets 503 recovered on retry. Neither is silently counted as a clean pass.

Phase 2H owns an admin-only, mention-neutral, explicitly targeted diagnostic using the real
reservation flow and isolated durable journal/CSV/message state. Existing `is_test=True` bypasses
cannot establish reservation admission and still touch shared message state. The diagnostic must
support receipt inspection, repeat/guard/edit and restart verification without changing production
calendar data or weakening eligibility. Natural production calendar routing stays a distinct gate;
an isolated diagnostic cannot prove every live scheduling, contention or uncertain-send scenario.

Rollout/rollback requirements remain binding: stop all writers; back up CSV, message state and
journal together; no mixed versions; reconcile accepted/uncertain receipts before downgrade and
keep dispatch stopped if outcomes remain unknown. No exactly-once, cross-host or TTL-stealing claim.
The separate Phase 2F next-natural-public-save observation remains pending unless new evidence proves it.

## Phase 2J — accepted delivery, 2026-09-09

Archived [Codex Task Pack - Discord Embed Payload Safety Phase 2J Ops Diagnostic Convergence.md](Codex%20Task%20Pack%20-%20Discord%20Embed%20Payload%20Safety%20Phase%202J%20Ops%20Diagnostic%20Convergence.md) and [chat starter](Codex%20Chat%20Starter%20-%20Discord%20Embed%20Payload%20Safety%20Phase%202J%20Ops%20Diagnostic%20Convergence.md). Operator smoke passed; #261/#568 merges and final main/deployed verification remain pending. The original embed audit now includes a Phase 1–2J disposition reconciliation. Phase 2K audit/design pack is active one directory above.

## KVK S2 closeout — 2026-09-10

S2A and S2B task packs and matching chat starters are archived here after accepted merges.
S2B SQL #79, mirror #265 and private bot #572 are merged; no bot-machine update is claimed.
Retain all delivery, review and disposable-SQL evidence. The active S3A pack/starter in the
parent folder owns the next separately approved implementation; no archived starter is runnable
as a new slice. Architecture, scenarios and local SQL guidance remain active references.


## S3A archived — 2026-09-10

S3A is complete, smoke accepted and merged through mirror #266 and private bot #573.
Retained: [task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3A%20Player%20Window%20Calculations.md)
and [historical starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S3A%20Player%20Window%20Calculations.md).
They contain the exact implementation/review/security/smoke evidence; do not execute them again.
The historical successor was [S3B](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3B%20Acceptance%20and%20Atomic%20Publication.md),
now accepted and archived. S4A subsequently completed; S4B is the current next slice with separate G3. Bot-machine deployment remains absent.


## S3B archived — 2026-09-10

Retained [task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S3B%20Acceptance%20and%20Atomic%20Publication.md) and [historical starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S3B%20Acceptance%20and%20Atomic%20Publication.md).
Mirror #267 and private #574 are merged; operator smoke passed 36 tests in 9.11s.
All implementation/review/security and validation-gap evidence is preserved.
Historical S3B successor (now complete): [S4A pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md) and [starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md), separate G3 pending.
Both S3B archive moves and closeout docs were included in the merged S4A PRs.

## S4A completed and archived — 2026-09-10

[Final task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md) and [historical starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S4A%20Shared%20Reports%20and%20Cards.md) retain implementation, review fixes, security, operator smoke/full-suite and verified merge evidence. Next active slice: [S4B](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S4B%20Versioned%20Exports%20and%20Delivery.md), separate G3 pending.


## S5A archive - 2026-09-12

- [Completed S5A task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5A%20Private%20Intake%20and%20Admin%20Controls.md)
- [Historical S5A starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S5A%20Private%20Intake%20and%20Admin%20Controls.md)

Accepted and merged after operator-reported successful smoke. Continue only through separately
approved S5B; keep historical evidence and retained review worktrees/databases.


## S5B archive closeout - 2026-09-12

Completed S5B task pack and approval starter are retained here as historical records:

- [Codex Task Pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md)
- [Codex Chat Starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S5B%20Endpoint%20Config%20and%20Recovery%20Integration.md)

S6 is the active next pack in the parent directory. Retain all delivery, test and security evidence;
archival does not remove code, databases or worktrees and does not authorize deployment.

## Post-S6 active navigation

- [Settled integration requirements](../../reference/kvk_source_migration/post_s6_integration_requirements.md)
- [Closeout and next-slice carry-forward manifest](../../reference/kvk_source_migration/post_s6_handoff_log.md)
- [S7 task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md)
- [S7 starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md)
- [Archived S6 evidence pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S6%20Release%20Readiness%20and%20Controlled%20Activation.md)


## S7/S8A accepted closeout and S8B active navigation — 2026-09-13

S7 and S8A packs/starters are archived; approved contracts and evidence remain active references.
Next: [S8B task pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md) and [new-chat starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md), review/scope first.
[Merge/smoke limits and exact mandatory carry-forward manifest](../../reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md).
