# Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection

Status: completed and operator accepted on 2026-07-15. This is an archived execution starter and
must not be reused as an active task.

```text
Codex, implement Player Self-Service Command Centre v2 Phase 5D.1: Authoritative Next Scheduled Alert Projection.

Approval state:
- Phase 5D Premium Reminders Summary Card is complete and operator accepted
- Phase 5D.1 is the agreed next GovernorOS slice before Phase 5E Preferences
- the objective is to complete the existing Reminders hero using authoritative scheduler/event semantics
- preserve the accepted Phase 5D card, Manage journey, privacy, navigation, avatar, fallback, timeout,
  attachment, and footer presentation
- operator Discord smoke is the final post-implementation gate

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md
- docs/player_self_service_command_centre_briefing.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/reference/events_and_dm_reminders.md

Use these skills/workflows:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review
- k98-promotion-check before production promotion
- codex-security:security-diff-scan after implementation

Use k98-sql-validation only if repository evidence unexpectedly proves the implementation is
SQL-facing. No SQL, new persistence, or new event source is approved.

Before editing, inspect and report one concise implementation map:
1. the Phase 5D /me reminders payload, service, view, renderer, fallback, attachment, Manage refresh,
   author gate, timeout, and selected-Dashboard return paths;
2. /calendar_next_event, /next_kvk_event, and /next_kvk_fight, their bulk cache readers, ordering,
   filtering, health/stale behavior, and player-facing labels;
3. KVK scheduler eligibility including subscription matching, 48-hour horizon, alert offsets,
   passed-window/immediate behavior, sent and scheduled trackers, retry, task registry, and rehydration;
4. Calendar dispatcher eligibility including enabled/all/specific event preferences, offsets, grace,
   sent keys, retry, event types, and runtime-cache health;
5. the exact pure helper boundary that both live dispatch and read-only projection will use;
6. proof that source/config/tracker state can be bulk-loaded once per request without N+1 reads;
7. exact files to change and focused tests selected.

Existing-command evidence:
- /calendar_next_event already uses the Calendar runtime-cache next-event/filter path
- /next_kvk_event and /next_kvk_fight already use the KVK upcoming-event cache
- reuse those authoritative reader paths where appropriate
- do not assume these commands provide reminder eligibility: they do not combine player settings,
  alert offsets, KVK's 48-hour horizon, duplicate state, Calendar grace, or sent-key rules
- do not alter, redirect, remove, or re-register any of the three commands

Locked projection rules:
- extract narrow pure scheduler-domain candidate helpers and make live dispatch consume the same
  semantics; do not recreate scheduler rules inside Player Self-Service
- accept an injected timezone-aware UTC clock and already-loaded occurrences/preferences/state
- perform no jobs, tasks, DMs, acknowledgements, tracker writes, persistence writes, cache refreshes,
  network calls, or other side effects
- preserve KVK subscription matching, 48-hour horizon, late/immediate behavior, sent markers,
  scheduled-task/rehydration ownership, retries, and at-start semantics
- preserve Calendar enabled/all/specific event settings, offsets, grace, sent-key behavior, retries,
  and at-start semantics
- a sent KVK alert is excluded; a genuine future alert already represented by the scheduled tracker
  remains a pending candidate and must never be described as delivered
- choose the earliest future candidate across KVK and Calendar with a deterministic tie-break
- use absolute UTC timestamps and friendly authoritative labels; never expose raw keys or countdowns
- never show a past timestamp as the next alert

Locked hero decision:
1. NEXT SCHEDULED ALERT when an authoritative future candidate exists;
2. NO UPCOMING ALERT when both required projections are healthy and no future candidate exists;
3. SCHEDULE UNAVAILABLE when a normally available required source/projection fails for this request;
4. REMINDER COVERAGE only if a task-pack escalation gate prevents safe parity implementation.

The ACTIVE/REVIEW/OFF configuration rules do not change. A temporary source failure must not turn a
valid saved configuration into REVIEW. Never imply Discord delivery success.

Preserve exactly:
- current KVK and Calendar event types, sources, alert-time choices, labels, ordering, and persistence
- KVK autosave/update wording and confirmation DM behavior
- Calendar Settings handoff
- Remove All confirmation and current-state revalidation
- scheduled/sent cleanup, unsubscribe, retry, restart/rehydration, duplicate-send prevention, and dispatch
- private/ephemeral author-gated Discord-user scope and return-only selected Dashboard context
- no Change Governor and no Inventory navigation
- invoking-user avatar, duplicate-safe identity, 1702x924 card, stable filename, full UTC footer,
  component rows, existing Manage action, graceful timeout, fallback, replacement, and stream cleanup
- legacy redirects, command registration, privacy, logging, and service ownership

Do not add or change:
- scheduler cadence or behavior, jobs, dispatch, retries, event sources/types, lead times, grace,
  DM policy, Calendar semantics, SQL, schema, persistence, defaults, presets, history, telemetry,
  favourite/popularity inference, public output, another /me page, or a broad framework

Implementation and validation:
- keep commands/views thin and eligibility in narrow scheduler-domain pure helpers
- build one typed cross-system projection that maps into the existing same-payload Reminders contract
- prove parity with live KVK and Calendar eligibility using deterministic-clock fixtures
- cover sent versus scheduled state, passed windows, at-start, retries, restart/rehydration,
  healthy-empty versus unavailable sources, all/specific Calendar prefs, tie-breaking, and unknown selections
- prove no tasks, DMs, acknowledgements, writes, refreshes, network calls, or N+1 occurrence reads
- preserve Manage mutation/restart/dispatch and the three existing next-event command regressions
- cover direct entry, Dashboard return, fallback, render/edit/send failures, timeout, foreign/stale/
  forged/concurrent interactions, attachment replacement, and stream cleanup
- render original 1702x924, Discord desktop, and mobile samples for NEXT, NO UPCOMING,
  SCHEDULE UNAVAILABLE, long/Unicode, and fallback states
- run architecture, deferred-item, selected-test, smoke-import, registration, pre-commit, focused/full
  pytest, log-noise, scheduler deterministic-clock, K98 PR review, promotion, and Codex Security gates
- update programme, briefing, canonical reference, task status, and deferred evidence
- do not mark operator smoke complete until the operator performs it

Stop and ask only for section 16 blockers in the task pack. In particular, stop if healthy-empty
versus unavailable KVK source state requires a new source/persistence contract, or exact parity
requires changing scheduler behavior rather than extracting it. Do not silently copy scheduler
logic, omit a system, expose raw keys, or widen the phase.
```
