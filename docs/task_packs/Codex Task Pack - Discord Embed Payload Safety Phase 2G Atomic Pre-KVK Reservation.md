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
