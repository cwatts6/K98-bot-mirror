# Codex Task Pack - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation

## 1. Task Header
- Date: 2026-09-07
- Owner: Chris Watts
- Task type: evidence-gated restart/persistence reliability design
- One-pass approved: no
- Status: prepared; audit/scope only first, then stop for approval
- Repository: K98-bot-mirror first; SQL separately gated

## 2. Prerequisites And Reading
Phase 2F candidate delivery and operator smoke were accepted through mirror PR #257 and production
PR #564. Both PRs were OPEN at preparation; manual merges and final production-main verification
are operator-owned and pending. Do not infer either from candidate smoke.

Before implementation, revalidate both PR states, live base/head, branch, worktree, intended mirror
base, Phase 1-2F source presence, and final production-main/bot-machine verification evidence.
If prerequisite merges or final verification remain incomplete, report the gap and limit work to
read-only audit/planning. Never develop from the production PR branch.

Read AGENTS.md, README-DEV.md, docs/reference/README.md and all indexed required core standards.
Conditional references: events_and_dm_reminders.md, REVIEW_HELPERS.md, runbook_startup.md,
runbook_shutdown.md, singleton_lock.md, deferred_optimisations.md, the deferred scoring model,
and root/applicable SECURITY.md. Read Promotion Guide.md only for promotion work.
Historical inputs: archived Phase 2F task pack and Discord Embed Payload Safety Audit Findings.md.
Use docs/templates/Codex Task Pack Template.md as the pack structure reference.

## 3. Objective And Evidence
Determine whether an atomic Pre-KVK dispatch reservation is justified, then propose the smallest
approved design that prevents overlapping fresh sends without losing legitimate reminders after
failure or restart. No implementation is approved by this preparation.

Observed code: stats_alerts/embeds/prekvk.py checks sent_today_any and sent_today before a fresh
send, then records prekvk_daily through claim_send after success. stats_alerts/guard.py locks
the claim operation, not the whole check/send/commit sequence. A duplicate production send from
this overlap has not been established. A deterministic overlap reproduction is acceptable evidence;
do not manufacture production duplicates or mentions.

The singleton metadata helper is not an exclusive acquisition primitive. Do not use it as proof
that concurrent processes are impossible. Unique-temp atomic JSON publication also does not merge
snapshots or reserve dispatch ownership.

## 4. Scope And Invariants
Audit every scheduled/manual/test entry point, guard caller, off-season mutual exclusion, CSV
reader/migrator/writer, message-state load/save, edit/fresh-send fallback, exception and offload.
Map coroutines, threads, processes, lock acquisition/release, shutdown and restart.

Preserve Phase 1-2F payload policy, event selection/order, daily limits, existing edit behavior,
message/view IDs, mentions, commands, permissions, visibility, requester ownership, eligibility,
calendar meaning, scheduler timing, and executor once-only semantics. Test-mode guard bypass must
remain explicitly modelled; an ops test_embed edit is not evidence of a guarded scheduled send.

Only separately approved reservation semantics may change. Preserve existing CSV path/header,
date/time/kind meanings, accepted legacy forms, log readers and state contracts unless the operator
explicitly approves a specific compatibility or migration decision. No silent sidecar/schema change.

Out of scope: broad JSON consolidation, DM redesign, active-reminder persistence reopening,
general singleton repair, public reminder child-task redesign, Stats/KVK History executor audits,
Ark retention/draft transactions, SQL/config/dependency changes without separate approval.

## 5. Source Deferred Item And Priority
- Area: stats_alerts/guard.py, stats_alerts/embeds/prekvk.py, stats-alert state and concurrency tests
- Type: architecture
- Description: Check/send/post-success claim permits a theoretical overlapping fresh dispatch.
- Suggested Fix: First prove overlap and design reserve/commit/release with uncertainty and recovery.
- Impact: medium
- Risk: high
- Dependencies: Evidence, explicit persistence-contract approval, deterministic restart/recovery tests.

Provisional scoring (revalidate during audit): impact 3 + frequency 2 + risk reduction 4 - effort 5
= 4, evidence/design-gated backlog candidate. Programme ordering selects this focused audit next;
the score does not authorize implementation or override security severity.

## 6. Architecture Decision Required
Compare leaving the post-success guard unchanged, in-process coordination, existing file-lock
primitives, a narrowly scoped durable reservation store, and SQL-backed coordination only if
evidence justifies separately scoped SQL. Do not select a sidecar or SQL merely because it exists.

Provide a state-transition table for available/reserved/committed/released/uncertain/recovery states:
- Exact reservation key: UTC day/kind and any channel/guild/event scope, supported by current meaning.
- Atomic owner acquisition across the actual coroutine/thread/process model; owner-checked
  commit/release, contention policy, lock duration and stale ownership detection.
- Known pre-send failure versus accepted Discord send, timeout/cancellation with uncertain outcome,
  process death after send but before state/claim, and commit failure after successful delivery.
- Reconciliation evidence and conservative retry policy; never promise exactly-once Discord
  delivery without a supported idempotency/reconciliation mechanism.
- Existing off-season mutual exclusion and all shared guard consumers; explain both directions
  of overlap rather than fixing only the Pre-KVK caller.
- UTC midnight rollover, restart, stale reservation recovery, unreadable/malformed state,
  migration, format/Unicode compatibility, durability, cleanup and rollback.
- Ordering of Discord publication, message-state persistence and legacy successful-send count.
  A reservation must not silently become a completed-send log entry.
- Executor call shapes/results/exceptions stay once-only; no retry through a second backend
  after the first may have started work.

If the design depends on exclusive singleton ownership, stop and propose that prerequisite as a
separate task. Prefer self-contained coordination when justified; do not fold lifecycle repair
into this PR.

## 7. Candidate File Manifest (Audit Must Make Exact)
Inspect stats_alerts/embeds/prekvk.py, stats_alerts/guard.py, stats_alerts/interface.py,
stats_alerts/state.py, stats_alerts/formatters.py, constants.py, file_utils.py and actual dispatcher
callers found by repository search. Inspect singleton_lock.py and lifecycle paths only as supporting
evidence. These are not blanket modification permissions.

Candidate runtime changes after approval: prekvk.py/guard.py and a narrowly scoped persistence
module only if the design proves it necessary. State/interface edits require exact justification.
Candidate tests: tests/test_prekvk_embed.py, tests/test_stats_alerts_state.py and a proposed focused
tests/test_prekvk_reservation.py if approved. Select actual shared guard/caller tests from search.
Documentation: this pack/starter, README-DEV.md, task-pack indexes, event reminder reference,
audit findings and active/resolved debt registers as applicable.
SQL files: none currently approved. Name exact separately gated SQL files before any SQL work,
validated against C:\K98-bot-SQL-Server.

## 8. Required First Response And Approval Questions
1. Confirm prerequisites, both PR merge states, production-main verification, branch/head/worktree,
   intended base and bot/SQL scope.
2. Map source-to-send-to-state/claim boundaries and prove actual concurrency; distinguish deployment
   assumptions from enforced controls.
3. Present evidence/reproduction plan and a safe/fix now/defer/not runtime findings matrix.
4. Compare alternatives and recommend an architecture with the explicit state machine above.
5. Name exact runtime/test/documentation and separately gated SQL files.
6. Explain preserved behavior and every proposed persistence/uncertainty-policy change.
7. Give selector/risk-based tests, security routing, natural smoke, rollback and dependencies.
8. Ask approval for evidence sufficiency, selected reservation/uncertain-send policy, persistence
   path/schema/migration, exact manifest, and any genuinely required separate prerequisite.
9. Stop. Do not edit runtime code or tests in the first response.

## 9. Tests And Validation After Approval
Use k98-test-selection and scripts/select_tests.py. Test overlapping same-key and distinct-key
calls; threads/processes when reachable; one winner; owner mismatch; lock timeout; stale owner;
known Discord failure/release; uncertain timeout/cancel; accepted send/commit failure; restart at
each transition; UTC rollover; corrupt/missing state; legacy CSV reads/counts; unchanged test/edit
paths, off-season guards, mentions, message IDs and executor invocation counts. Use isolated state,
mocked Discord, deterministic barriers/clocks and no production logs/state.

Run or justify architecture/deferred/security-routing validators, selector, smoke imports,
registration validation, focused tests, pre-commit and full pytest/log-noise before promotion.
No live duplicate/mention or failure-injection test.

## 10. Security And SQL Routing
Use k98-security-review-routing before any scan. After implementation: bot Scan type Changes,
exact immutable approved base/head, Deep off, security-diff-scan. Do not run Standard/Codebase or
Deep scans. SQL is a no-diff skip only if repository, schema/migrations/procedures/DAL contracts
remain unchanged; otherwise stop for SQL validation/approval and a separate SQL Changes target.

Record ordinary progress only through scan progress counters. coverage.deferred is for actual
unresolved review work, not progress placeholders. Check canonical completeness and deferred items
before sealing, and verify sealed readback before declaring the review gate passed.
This documentation preparation is a precise security skip: no executable/config/dependency change.

## 11. Delivery, Smoke And Rollback
Mirror PR first, patch-based production promotion after validation, separate Git histories,
operator merges and final deployment from K98-bot/main. Preserve immutable reviewed targets.
Observe a natural eligible fresh dispatch and subsequent normal no-duplicate guard behavior;
inspect identity and committed state/count. Do not use a bypassing test command as proof.
Rollback must specify compatibility of any new reservation store with old code and safe handling
of in-flight/uncertain reservations. Reverting code alone is not assumed safe for a new state model.

## 12. Remaining Programme And Ownership
Owner for all gates: Chris Watts; audit must refresh priorities, not silently expand scope.
- Phase 1 and 2A-2E: accepted prerequisite behavior; do not reopen.
- Phase 2F: candidate delivered/tested and archived; operator merges/final verification pending.
  Restart evidence is concrete; next natural public save remains an observation, not an inferred test.
- Phase 2G: next named phase, this evidence/design-gated reservation audit.
- Follow-up reliability task A: exclusive singleton ownership and owner-checked release. Suggested
  after 2G, or earlier only if 2G demonstrates a hard dependency. Separate approval and PR.
- Follow-up reliability task B: public child-task supervision/cancellation and send/delete/expiry
  interleavings. Suggested after ownership scope is settled, separate approval and PR.
  Neither item is automatically assigned a new Phase 2 letter or bundled into reservation work.
- Separate Stats/KVK History executor audits retain existing owners/gates. Ark transaction/retention
  follow-ups retain their existing independent scope.
- The smoke log's generic tracked-view 10-second timeout is an observation for lifecycle triage,
  not a proven Phase 2F regression or authorization to change rehydration.

## 13. Acceptance
- Audit and explicit implementation approval recorded.
- Actual overlap and failure boundaries proved; chosen contract and rollback approved.
- No unrelated behavior change; all selected tests/validators and complete Changes review pass.
- Production/source verification, natural smoke and residual uncertainty recorded honestly.

## 14. Preparation Validation
This handoff and Phase 2F closure change Markdown only. Architecture, deferred-item and security
routing validators, diff checks and applicable pre-commit hooks are the delivery gates. The selector
also includes the existing implementation branch and recommends full pytest/import/registration;
those already passed for identical Python blobs (3240 passed, 2 skipped; 114 focused). Repeating
runtime tests or a Changes scan solely for this inspected documentation delta is a documented skip.
Mirror and production receive the same documentation patch, preserving separate Git histories.


## 15. Approved Implementation Record — 2026-09-08

This record supersedes preparation-only status above. The operator approved proceeding after
review/scope and approved the versioned local reservation sidecar and exact manifest. No SQL,
config, dependency, singleton, public-child lifecycle or general executor redesign is included.

Prerequisites revalidated: mirror PR #257 merged as `bf3a4d326a5009fa1610b05b9f43979813b4aadc`;
production PR #564 merged as `d9321328507add3b06704c25db2c6e59fe7352f6`. Both merge states and
production main were read from GitHub. All 912 mirror Python blobs matched production main.
The clean mirror base was `55bcfd4f6fe7934a6d9a87fc8a0bc6e6e7429dfd`; implementation branch is
`codex/discord-embed-payload-safety-phase-2g`. The operator answered “Yes deployed and restarted
successfully” to the production-head prerequisite question. This is operator attestation, not
independently collected bot-machine logs. The next natural public reminder atomic save remains
unobserved; archived candidate acceptance alone is not deployment evidence.

### Evidence and scope decisions

| Classification | Evidence / disposition |
|---|---|
| Fix now | Isolated execution of the real Pre-KVK fresh-send suffix and threaded CSV functions produced two mocked sends and one CSV row. Post-success claim cannot own the preceding network await. No production duplicate is asserted. |
| Fix now | Shared legacy CSV migration/read/append could race; serialize the whole operation. Existing O_EXCL lock helper leaves its pathname when the body throws; use the already pinned OS-backed FileLock locally. |
| Fix now | Coordinate active Pre-KVK and off-season attempts, durable positive receipts, compare-and-set message updates and fighting-generation invalidation. A renderer returning without sending must not create a success claim. |
| Safe | Canonical Phase 1–2F payload construction, edit/test paths, permissions, visibility, ordering, eligibility, mentions and public reminder persistence retain their contracts. |
| Defer | Two isolated processes passed the real singleton metadata check concurrently. Exclusive singleton acquisition/release remains separate; this protocol does not depend on it. Public child-task lifecycle, DM redesign, broad JSON consolidation and Stats/KVK History executor audits remain separate. |
| Defer | Stats-alert interface/database offload fallback can retry after callable entry; reservation I/O uses the existing once-only backend directly. Audit those other callers separately. |
| Not runtime | Archived acceptance/preparation text is historical evidence, not a deployment control or singleton guarantee. |

Successful processing through admin_helpers dispatches Kingdom Summary first, then fighting KVK
or Pre-KVK. Honor/Pre-KVK fast upload routes can overlap outside the queued processing lock.
No separate timed Pre-KVK loop was found: the daily key is a guard, not a scheduler. Manual
`/ops test_embed` and `/kvk_admin test_embed post_here=False` use the existing test bypass;
`post_here=True` takes the direct KVK route. Same-day Pre-KVK references edit without daily
reservation; missing/yesterday/fetch-or-edit failure selects fresh publication. Fighting clears the
reference and fences late receipts. Payload preparation completes before fresh publication.
Off-season daily precedes Monday weekly; their completed self-key guards remain independent.
Completed off-season blocks Pre-KVK; completed Pre-KVK still does not block off-season. Active
Pre-KVK attempts block both off-season kinds in both directions. Kingdom Summary ping claims
retain their pre-send meaning and do not become delivery receipts.

Coroutine overlap occurs at network awaits and offloaded I/O; separate dispatcher threads and
processes share the filesystem protocol. A short OS lock covers only journal/CSV/state transitions,
never Discord awaits. Lock order is dispatch then message-state, with no reverse acquisition.
Cancellation waits for a started filesystem operation exactly once before cleanup; it does not
retry through another executor. Shutdown may still kill the process, so durable phases rather
than a successful graceful drain determine restart recovery. The 5-second acquisition bound does
not bound filesystem completion time. Separate hosts/filesystems and mixed versions are excluded.

### Selected persistence and state machine

The prior post-success claim and an in-memory lock cannot coordinate restart/process overlap.
Holding a file lock across Discord I/O would serialize network stalls without retaining ambiguous
outcomes. A CSV schema extension would mix ownership with legacy success/ping meanings. SQL would
require a separate schema, deployment and review gate. The approved choice is a narrow version-1
`<STATS_ALERT_LOG>.dispatch.json` journal and `<STATS_ALERT_LOG>.dispatch.lck` OS lock, reusing
existing `filelock==3.20.0` and atomic JSON helper. Message JSON stays in its legacy shape with
`<STATE_PATH>.lck`; legacy CSV headers/rows/count APIs remain compatible. No historical CSV rows
are imported as pending attempts; the journal is initialized on first reserve. Invalid journal
content is preserved and fails closed. Never delete .lck pathnames while writers may exist.

Each attempt records opaque token, kind, PID plus process creation time, UTC reserved day/time,
channel and message generation. Start persists `sending` plus start time immediately before the
Discord call. A positive message ID persists `accepted` plus receipt time before legacy message
state/CSV projections, then becomes `committed`. Token matching owns transitions. A pre-invocation
failure releases `reserved`; cancellation during start can release because the Discord caller has
not been entered. Once the send callable is entered, exceptions/cancellation become `uncertain`.
Even final HTTP 400/401/403/404 cannot prove non-delivery: the inspected Discord client can retry
after an earlier ambiguous response. No exception-status retry or exactly-once claim is made.

Recovery runs under the same lock at reservation admission. A provably dead reserved PID/create-time
owner releases; a dead sending owner becomes uncertain; unknown/live ownership remains blocked.
Accepted receipts replay projections idempotently. Uncertain attempts never expire or get stolen.
UTC start rechecks current-day eligibility; accepted receipt day owns the CSV count. Active attempts
block conflicts across midnight. Old-day recovered receipts cannot become today's editable message.
Fighting/stale-reference clears advance a journal generation so late receipts cannot resurrect the
cleared ID. Compare-and-set prevents a stale failure clearing a newer ID. Unrelated JSON keys and
Unicode remain intact. Positive receipts retain authority if a CSV is later missing.

`ReservationStore.reconcile_receipt` is a local operator recovery API, not a Discord command or
automatic history search. Verify token, channel, bot author, exact payload/message identity and
publication time from positive evidence before using it. It records the receipt and replays
projections. Missing search results are not proof of non-delivery. With no conclusive evidence,
leave the attempt blocked and escalate to an explicit operator recovery decision; do not delete
or TTL-reset it. Receipt persistence failures log token/message ID for that investigation. Journal
history is retained without automatic pruning; retention needs separate evidence/design approval.

### Exact approved manifest

Runtime: `stats_alerts/dispatch_reservations.py`, `stats_alerts/guard.py`, `stats_alerts/state.py`,
`stats_alerts/interface.py`, `stats_alerts/embeds/prekvk.py`, `stats_alerts/embeds/offseason.py`,
`embed_offseason_stats.py`. The interface/state changes are required to fence fighting clears and
patch only the message reference; off-season participation closes the shared admission race.

Tests: `tests/test_prekvk_reservation.py`, `tests/test_stats_alerts_guard.py`,
`tests/test_stats_alerts_offseason_flow.py`, `tests/test_prekvk_embed.py`,
`tests/test_stats_alerts_state.py`, `tests/test_stats_alerts_fighting_lifecycle.py`,
`tests/test_embed_offseason_stats.py`.

Docs: this pack and matching starter; `README-DEV.md`; `docs/task_packs/README.md`;
`docs/task_packs/archive/README.md`; archived Phase 2F pack (prerequisite update only);
`docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`;
`docs/reference/events_and_dm_reminders.md`; `docs/reference/deferred_optimisations.md`.
No resolved-debt archive change until acceptance is earned.

SQL manifest: **empty, separately gated**. Authoritative SQL repository remains clean main at
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`; no schema, migration, procedure, query or DAL contract
changes. SQL Changes scan is a no-diff skip only while these conditions remain true.

### Validation, delivery and remaining gates

Deterministic tests use temporary files, mocked Discord, barriers and controlled clocks: same and
distinct keys, threads/processes/coroutines, token mismatch, lock timeout, stale/unknown owner,
pre/post-send cancellation, UTC rollover, receipt/state/CSV failures, recovery, corrupt files,
legacy migration/quota and unchanged edit/test/mention paths. No live duplicates or mentions were
forced. All 81 focused tests passed. Full pytest passed **3304 passed, 2 skipped** with production
operational log-noise validation passing. Tests used isolated pinned filelock 3.20.0; the development
venv has 3.29.0, and neither the venv nor requirements were modified. Selector requested full tests,
smoke imports and command registration; imports and registration passed (36 primary/100 grouped).
Architecture validation passed; final hooks, deferred/security-routing validation and immutable
Changes-only/Deep-off bot review remain delivery gates, recorded in the PR/final handoff.

Natural smoke remains pending: after approved mirror/production merge and deployment from
production main, observe an eligible production fresh dispatch; verify one intended message,
unchanged payload/mentions, matching receipt/channel/message-state and one CSV success row. Observe
normal later edit/guard behavior and a restart with committed receipt intact. A bypass test command
cannot establish production admission. Observe uncertainty only if it occurs naturally; do not
inject live failures. Also retain the separate Phase 2F next-natural-save observation.

Rollout and rollback require all bot writers stopped, legacy startup migration settled, and backups
of CSV, message JSON and journal together. Never run mixed old/new writers. Inspect and reconcile
accepted/uncertain attempts before restarting old code: old code ignores this journal, so reverting
alone can duplicate a previously accepted send. Keep a consistent success CSV/reference and retain
the journal backup; if uncertainty remains, keep dispatch stopped pending the operator's explicit
recovery decision. Do not delete locks under live writers or blindly restore stale snapshots.
No singleton repair, public child-task lifecycle or SQL work is a hard implementation dependency;
exclusive operational stop during version changes is a deployment requirement.


## 16. Local Windows validation follow-up - 2026-09-08

The operator's local full suite failed in test_process_contenders_have_one_owner: one child hit
WinError 32 replacing alerts.csv.tmp before any reservation was written. The other child obtained
ownership. This is evidence of pre-send CSV availability failure, not two successful owners; the
original external handle owner is unknown. Twelve local reruns did not reproduce the transient
holder. The strict process test remains unchanged and is not skipped or relaxed.

The follow-up narrowly extends the runtime manifest with `file_utils.py::atomic_write_csv`:
optional replacement-attempt count defaults to one for unchanged callers. Stats guard creation,
migration and append opt into five attempts while retaining the existing coordination lock.
Only os.replace is retried for the existing WinError32 classification; row iteration, CSV writing,
fsync, executor entry and Discord sends are not repeated. Backoff uses the existing JSON-helper
20ms exponential/full-jitter convention capped at 250ms per delay. Exhaustion/other errors still
propagate, preserving the old destination and blocking reservation admission. This is not a fix
for persistent external file locks or permission errors, and it makes no new delivery guarantee.

Changed tests are `tests/test_stats_alerts_guard.py` and `tests/test_prekvk_reservation.py`.
Deterministic injected sharing violations cover initialization/migration/append recovery, unchanged
temp bytes and one fsync, lock ownership throughout retries, exhaustion, non-sharing failures,
legacy single-attempt defaults and no reservation on exhausted CSV creation. Pinned filelock 3.20.0
focused validation passed 88 tests. Full local-version validation and a new immutable bot
Changes-only/Deep-off review are recorded in the PR handoff. No SQL/config/dependency change.


## 17. Production review follow-up - async invalidation

Production PR #565 correctly identified that the synchronous fighting-open clear could wait for
its filesystem lock on the Discord event loop. `clear_prekvk_message` now wraps the existing store
transition through the once-only cancellation-draining `_io` boundary. The interface and all
Pre-KVK stale/fetch/edit-failure clears await it; the synchronous store API, compare-and-set,
generation fence and lock ordering remain unchanged. Errors retain existing caller logging, while
cancellation propagates after any started filesystem operation completes. No alternate executor
fallback, new retry, timing policy, permission or SQL change is introduced.

Runtime delta: stats_alerts/dispatch_reservations.py, stats_alerts/interface.py and
stats_alerts/embeds/prekvk.py. Test delta: tests/test_prekvk_reservation.py,
tests/test_stats_alerts_fighting_lifecycle.py and tests/test_prekvk_embed.py. Tests verify off-loop
execution, responsiveness during a blocked clear, once-only error propagation, cancellation drain,
and existing generation fencing. Pinned focused validation passed 91 tests; final full-suite,
separate mirror/production Changes-only review and patch-promotion evidence are retained in PRs.
