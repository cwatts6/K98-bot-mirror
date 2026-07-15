# Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection

## 1. Task Header

- Task name: `Player Self-Service Command Centre v2 Phase 5D.1 Authoritative Next Scheduled Alert Projection`
- Date: `2026-07-15`
- Owner/context: Follow-on from the completed and operator-accepted Phase 5D Premium Reminders Summary Card.
- Task type: `scheduler-domain extraction | read-only cross-system projection | Reminders hero completion`
- One-pass approved: `No - this pack prepares the next implementation slice; runtime work begins only when the operator starts the implementation task`
- Product direction approved: `Yes - complete the Reminders page before Phase 5E Preferences`
- Runtime implementation approved: `Yes - started by the operator on 2026-07-15`
- Status: `implemented and locally validated - operator Discord smoke pending`
- SQL impact: `None expected or approved`
- Command-surface impact: `None`

### Operator-approved section 16 resolution

Repository audit found that KVK `now` maps to `timedelta(0)` but live dispatch used
`if not delta: continue`, so the saved at-start choice was never scheduled. Calendar `start` was
already eligible. The operator explicitly authorised the narrow KVK correction on 2026-07-15.
Shared KVK eligibility now distinguishes a missing mapping from zero duration, making `now` a
genuine at-start candidate for live dispatch and projection. Existing 48-hour scheduling, delayed
task ownership, sent/scheduled trackers, rehydration, retry, duplicate prevention, unsubscribe,
cleanup, cadence, and DM content remain unchanged.

## 2. Required Reading

Read before implementation:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md`
- this task pack
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5D Premium Reminders Summary Card.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 4 Modern Reminder Centre.md`
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 7 Unified Reminder Centre and Dashboard Card Alignment.md`
- `docs/player_self_service_command_centre_briefing.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/events_and_dm_reminders.md`
- `docs/reference/deferred_optimisations.md`

Use these skills/workflows:

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review`
- `k98-promotion-check` before production promotion
- `codex-security:security-diff-scan` after implementation

Use `k98-sql-validation` only if repository evidence unexpectedly proves that implementation is
SQL-facing. Do not introduce SQL work, a new source, or persistence merely to obtain this hero.

## 3. Objective

Replace the approved Phase 5D `REMINDER COVERAGE` hero with an authoritative read-only projection
of the next eligible KVK or Calendar reminder alert. The projection must use the same eligibility
semantics as live dispatch, choose the earliest genuine future candidate across both systems, and
map that result into the existing typed Phase 5D hero contract without creating work or claiming
delivery.

The finished hero must select exactly one of:

- `NEXT SCHEDULED ALERT` when an authoritative future candidate exists;
- `NO UPCOMING ALERT` when both required projections are healthy and no future candidate exists;
- `SCHEDULE UNAVAILABLE` when a normally available required source/projection fails for this request;
- `REMINDER COVERAGE` only if a proven section-16 escalation gate prevents safe parity delivery.

Use absolute UTC timestamps. Never display a countdown or imply that Discord delivery has succeeded.

## 4. Background And Existing Evidence

Phase 5D deliberately shipped the truthful coverage hero because no single side-effect-free service
exposed exact parity with both reminder engines. The deferred item is now promoted into this task
pack rather than left in the active optimisation backlog.

Three existing commands already demonstrate authoritative bulk occurrence reads:

- `/calendar_next_event` loads the Calendar runtime cache and uses its existing next-event/filter
  semantics, including cache health/staleness presentation;
- `/next_kvk_event` reads the KVK event cache and orders upcoming events;
- `/next_kvk_fight` reads the same KVK cache and applies fight-specific filtering.

These paths are mandatory reuse evidence. They are not, on their own, an alert projection. They do
not combine the player's reminder preferences and offsets with all scheduler eligibility, sent or
scheduled tracker state, Calendar grace rules, or duplicate-send keys. Do not copy their command
presentation logic into Player Self-Service and do not change, redirect, remove, or re-register the
commands in this slice.

## 5. Scope

In scope:

- one typed, side-effect-free candidate contract shared by scheduler-domain code and read-only
  projection;
- narrow pure KVK and Calendar eligibility/candidate helpers extracted from current live behavior;
- one set-based Player Self-Service orchestration read that loads each occurrence/source snapshot
  at most once per request;
- deterministic earliest-candidate selection across KVK and Calendar;
- mapping into the existing Phase 5D hero variants and same-payload fallback;
- explicit healthy-empty versus request-level unavailable source state;
- parity, deterministic-clock, side-effect, restart, duplicate-send, and UI regression coverage;
- documentation and deferred-backlog evidence after delivery.

Out of scope:

- new commands, redirects, command-registration changes, or changes to the three existing next-event commands;
- scheduler cadence, task creation, dispatch, retry, grace, lead-time, event-type, event-source, DM,
  acknowledgement, unsubscribe, or duplicate-send policy changes;
- SQL, schema, persistence format, defaults, presets, history, delivery telemetry, or player comparisons;
- a new occurrence source or per-event N+1 reads;
- a broad scheduler, view, renderer, or service framework;
- Phase 5E Preferences or any other `/me` page.

## 6. Source Deferred Item

- Original area: `player_self_service/reminders_summary.py`, `event_scheduler.py`,
  `event_calendar/reminders.py`, and KVK/Calendar occurrence readers.
- Type: `architecture`
- Problem: exact cross-system projection would drift if KVK's 48-hour candidate window,
  late/immediate rules, tracker exclusions, Calendar grace/per-event settings, and sent-key rules
  were recreated inside the summary service.
- Promoted resolution: extract shared pure eligibility/candidate helpers that accept an injected UTC
  clock and already-loaded inputs, then use those helpers from both live dispatch and projection.
- Score: `8` (`impact 4 + frequency 4 + risk reduction 4 - effort 4`).
- Promotion decision: `approved as Phase 5D.1 on 2026-07-15`; remove the item from the active
  deferred backlog while this task pack is active. It is not marked resolved until implementation
  and parity validation complete.

## 7. Skill Decisions

- `k98-architecture-scope`: required because the work crosses legacy KVK scheduling, Calendar
  dispatch, Player Self-Service, file-backed duplicate state, and Discord presentation.
- `k98-discord-command-feature`: required to preserve privacy, same-payload fallback, author gates,
  attachment replacement, timeout, and Manage behavior while changing hero data.
- `k98-test-selection`: required to select scheduler, reminder, deterministic-clock, registration,
  and Player Self-Service regression gates.
- `k98-deferred-optimisation-capture`: required to close the promoted backlog item accurately and
  record any newly discovered out-of-scope refactor without widening this slice.
- `k98-pr-review`: required before handoff because scheduler parity and restart behavior are high risk.
- `k98-promotion-check`: required before mirror-to-production promotion.
- `codex-security:security-diff-scan`: required because the diff touches Discord interactions,
  user-controlled settings, file-backed sent/scheduled state, restart behavior, and DM eligibility.
- `k98-sql-validation`: not applicable unless the architecture audit unexpectedly finds a SQL-facing
  field; stop before adding SQL because none is approved.

## 8. Implementation Workflow

1. Inspect and report a concise map of the Phase 5D payload/service/view/renderer flow, both live
   reminder engines, occurrence readers, preferences, label maps, trackers, restart/rehydration,
   retry, duplicate-send, and host-refresh paths.
2. Record the exact current eligibility rules and bulk sources for KVK and Calendar before editing.
3. Prove whether KVK cache state can distinguish healthy-empty from unavailable using existing
   read-only state. If this needs a new event source or persistence contract, stop under section 16.
4. Define one narrow typed candidate/result contract with absolute UTC time, system, friendly event
   identity, alert-time label, and source health. It must not contain a delivery-success claim.
5. Extract the smallest pure helpers from scheduler-domain logic and make live dispatch consume the
   same helpers. Keep side effects in the current dispatch owners.
6. Build one set-based cross-system projection using already-loaded inputs and an injected UTC clock.
7. Map the result into the existing Phase 5D hero without changing card hierarchy, renderer size,
   avatar, navigation, Manage, fallback, filename, or timeout behavior.
8. Add focused parity and negative-path tests before running the selected repository gates.
9. Run Codex Security diff review, K98 PR review, and promotion checks.
10. Update the programme, briefing, canonical reference, task status, and deferred evidence; operator
    Discord smoke remains the final external gate.

## 9. Current-State Audit Contract

The pre-edit map must cover:

- `/calendar_next_event`, `/next_kvk_event`, and `/next_kvk_fight`, including their cache readers,
  filters, ordering, health/stale behavior, and why their output is not scheduler parity;
- `event_cache.get_all_upcoming_events()` and Calendar `load_runtime_cache()`/`filter_events()`/
  `next_event()` or their current equivalents;
- KVK subscription matching, the 48-hour scheduling horizon, selected reminder times, passed-window
  immediate behavior, sent and scheduled trackers, task registry, retry, and rehydration;
- Calendar enabled/per-event/global offsets, due/grace evaluation, sent-key state, retry, and source health;
- Player Self-Service config reads, summary construction, hero selection, renderer, fallback, attachment
  cleanup, Manage refresh, selected-Dashboard return, timeout, and author gate;
- exact authoritative event-label and alert-time maps;
- proof that every source/config/tracker collection is loaded in bulk, not once per occurrence.

## 10. Target Architecture

Commands and views remain thin. Player Self-Service orchestrates read-only, already-loaded state and
maps a typed projection result to the existing hero. Scheduler-domain modules own pure candidate
eligibility. Existing live scheduler/dispatcher owners retain task creation, DM sending, state writes,
retry, and acknowledgement.

The pure helper boundary must:

- accept explicit `now_utc` and already-loaded occurrences, preferences, and duplicate state;
- return deterministic candidates or explicit healthy-empty/unavailable state;
- be called by live eligibility and read-only projection so parity cannot drift silently;
- create no task, job, timer, DM, acknowledgement, tracker mutation, persistence write, cache refresh,
  network request, or event-source fetch;
- preserve KVK and Calendar differences rather than forcing them into one false generic scheduler.

### 10.1 Recorded Implementation Map And Evidence

- Phase 5D delivery remains owned by `player_self_service/service.py` and
  `player_self_service/reminders_summary.py`, with the accepted view/render/fallback/attachment/
  Manage/author/timeout/selected-Dashboard paths unchanged in
  `ui/views/player_self_service_views.py`, `player_self_service/reminders_renderer.py`, and
  `ui/views/player_self_service_reminder_views.py`.
- Existing command readers remain unchanged: `/calendar_next_event` uses
  `event_calendar.runtime_cache` filtering/ordering; `/next_kvk_event` and
  `/next_kvk_fight` use the upcoming KVK cache. Those commands expose occurrence order and labels,
  not player reminder eligibility.
- `event_cache.get_upcoming_event_cache_snapshot()` now supplies one locked, deep-copied KVK
  occurrence/health snapshot; `event_scheduler.snapshot_dm_trackers()` supplies one sent/scheduled
  tracker snapshot. Calendar preferences, runtime cache, and sent state are each loaded once by the
  service. No occurrence-level reader is called from either pure evaluator.
- `reminder_domain.kvk_candidates.build_kvk_alert_projection()` is the shared KVK boundary used by
  live scheduling and read-only projection. It owns subscription/fight matching, supported types,
  event identity, the 48-hour horizon, offsets including authorised zero-second at-start, passed-window
  immediate time, sent exclusion, and scheduled-pending representation. Existing scheduler code still
  owns marker writes, retries, task registry, dispatch, cleanup, and rehydration.
- `event_calendar.reminder_candidates` owns the shared Calendar occurrence filter, offset windows,
  enabled/all/specific preference evaluation, known-type and instance checks, grace/expiry, and sent
  keys. `event_calendar/reminders.py` still owns DMs, retries, dry-run behavior, sent writes, the
  operation lock, and persistence.
- `reminder_domain.projection.combine_reminder_projections()` is the typed cross-system selector.
  It accepts the single injected UTC clock and already-loaded source results, fails unavailable when a
  required source fails, rejects past display timestamps, and applies the documented KVK-first
  deterministic tie-break before mapping into the existing hero contract.
- Focused tests are in `tests/test_kvk_reminder_candidates.py`,
  `tests/test_calendar_reminder_candidates.py`, `tests/test_reminder_projection.py`,
  `tests/test_player_self_service_reminder_projection.py`,
  `tests/test_event_scheduler_at_start_projection.py`, and `tests/test_event_cache.py`, alongside
  the existing scheduler, Calendar dispatcher, next-event command, Manage, view, renderer, fallback,
  attachment, timeout, privacy, concurrency, and cleanup regressions selected by the repository.

## 11. Likely Files

Inspect before choosing exact edits:

- `commands/calendar_cmds.py`
- `commands/events_cmds.py`
- `utils.py`
- `event_cache.py`
- `event_scheduler.py`
- `subscription_tracker.py`
- `reminder_task_registry.py`
- `event_calendar/runtime_cache.py`
- `event_calendar/reminders.py`
- `event_calendar/reminder_state.py`
- `event_calendar/reminder_prefs.py`
- `event_calendar/reminder_types.py`
- `player_self_service/service.py`
- `player_self_service/reminders_summary.py`
- current Player Self-Service Reminders view/renderer modules
- focused scheduler, Calendar reminder, command, and Player Self-Service tests
- programme/reference/task-pack/deferred documentation

Do not assume all files need edits. Avoid expanding legacy root modules when a narrow target-domain
module can own the extracted pure contract.

## 12. Implementation Requirements

### KVK parity

- Preserve authoritative subscription matching, event ordering, exact selected offsets, the current
  48-hour occurrence horizon, and current at-start semantics.
- A sent candidate is excluded exactly as live dispatch excludes it.
- A future candidate already represented by the scheduled tracker remains a genuine pending alert
  candidate; projection must not mislabel it as delivered or suppress it merely because a delayed
  task was rehydrated.
- Passed timestamps are never displayed as future. Preserve live late/immediate eligibility in the
  shared helper without causing the read-only path to send immediately.

### Calendar parity

- Preserve enabled state, all-events versus selected-event preferences, global/per-event offsets,
  grace rules, sent-key construction, event-type availability, and at-start semantics.
- A Calendar candidate is excluded exactly when live duplicate state makes it ineligible.
- Projection does not mark sent, acknowledge, refresh the feed, or create a retry.

### Cross-system result

- Compare timezone-aware absolute UTC instants only.
- Use a documented deterministic tie-break when two candidates have the same alert instant.
- Use authoritative friendly labels; never expose raw keys.
- `NEXT SCHEDULED ALERT` states that an alert is scheduled/configured for the shown UTC instant,
  not that delivery has succeeded.
- `NO UPCOMING ALERT` requires healthy projection inputs with no future eligible candidate.
- `SCHEDULE UNAVAILABLE` represents request-level source/projection failure without turning an
  otherwise valid saved configuration into `REVIEW`.
- The existing ACTIVE/REVIEW/OFF configuration rules remain unchanged.

### Discord and delivery preservation

- `/me reminders` stays private, ephemeral, author-gated, and Discord-user scoped.
- Optional Dashboard governor context remains return-only; no Change Governor appears.
- The invoking-user avatar, duplicate-safe identity, `1702x924` backdrop, stable filename, component
  rows without Inventory, existing Manage action, full UTC footer, timeout, replacement, fallback,
  off-loop rendering, and file-stream cleanup remain unchanged.
- Same-payload fallback must not refetch or rerun projection after a render failure.

### Command governance

- Do not add a command, change a command name/description/option, or change registration counts.
- Do not alter `/calendar_next_event`, `/next_kvk_event`, or `/next_kvk_fight` output, privacy,
  filtering, views, or lifecycle merely to share a reader.

## 13. Refactor Decisions

Approved refactor: narrow extraction of pure scheduler-domain candidate eligibility needed to make
live dispatch and read-only projection share semantics.

Not approved: a generic reminder framework, scheduler rewrite, cache redesign, tracker migration,
new persistence abstraction, new event source, broad command cleanup, or renderer/view framework.

If exact parity requires changing behavior, separate the behavioral correction from this projection
and seek approval. Do not encode a known scheduler bug into a new public promise without documenting it.

## 14. Testing And Validation

Focused coverage must prove:

- KVK and Calendar candidate parity with live eligibility across selected offsets, at-start,
  passed windows, late/grace boundaries, healthy-empty, and unavailable-source cases;
- sent versus scheduled tracker semantics, duplicate suppression, retry, restart/rehydration, and
  unsubscribe/Remove All cleanup remain unchanged;
- Calendar all-events and selected-event settings, unavailable saved types, and per-event/global offsets;
- earliest cross-system choice, deterministic equal-time tie-break, and exact timezone-aware UTC output;
- no tasks, jobs, DMs, acknowledgements, tracker writes, persistence writes, refreshes, or network calls;
- each occurrence/config/tracker source is loaded once per request and no N+1 read is introduced;
- ACTIVE/REVIEW/OFF and all hero variants, long/Unicode names, raw-key suppression, and source failure;
- direct entry, selected-Dashboard return, Manage refresh, fallback, render/edit/send failures,
  attachment replacement, concurrent/foreign/stale/forged interactions, timeout, and stream cleanup;
- the three existing next-event commands retain their registration and behavior;
- existing reminder mutation, deterministic-clock, scheduler, Calendar dispatch, retry, and rehydration regressions.

Run or justify skipping:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
pre-commit run -a
pytest -q <selected focused tests>
pytest -q tests
python scripts/analyse_pytest_log_noise.py
```

Also render and inspect representative original `1702x924`, Discord desktop, and mobile samples for
NEXT, NO UPCOMING, UNAVAILABLE, long/Unicode, and fallback states. Run Codex Security diff review
after the implementation tree is final.

## 15. Acceptance Criteria

- [x] The pre-edit implementation map is recorded with exact reader and eligibility owners.
- [x] Live KVK and Calendar dispatch consume the same pure candidate semantics as projection.
- [x] No parallel scheduler logic exists in Player Self-Service.
- [x] The earliest authoritative future candidate produces `NEXT SCHEDULED ALERT` with absolute UTC.
- [x] Healthy inputs with no future candidate produce `NO UPCOMING ALERT`.
- [x] Request-level source/projection failure produces `SCHEDULE UNAVAILABLE` without false `REVIEW`.
- [x] Sent, scheduled, grace, duplicate, retry, restart, and rehydration semantics remain unchanged,
  apart from the separately authorised correction that makes the existing zero-second KVK at-start
  choice genuinely eligible.
- [x] The read-only path performs no task, DM, acknowledgement, refresh, network, or persistence side effect.
- [x] Sources are bulk-read once and deterministic-clock/tie behavior is covered.
- [x] Existing labels, commands, Manage, card, fallback, timeout, attachment, privacy, and navigation contracts remain unchanged.
- [x] No SQL, schema, persistence, event-source, lead-time, event-type, scheduler cadence, or DM policy change is introduced.
- [ ] Focused/full validation, visual evidence, K98 PR review, promotion checks, and Codex Security
  review pass. Automated gates and reviews pass; production promotion remains correctly held until
  commit/mirror PR and operator Discord smoke.
- [x] Programme, briefing, canonical reference, task status, and deferred evidence are updated.
- [ ] Operator Discord smoke is recorded as the final gate.

### 15.1 Delivery Evidence

- Focused selected regression run: `381 passed`; final malformed-runtime projection regression:
  `4 passed`.
- Final full suite: `2586 passed, 2 skipped`; log-noise replay: `2586 passed, 2 skipped` with
  production operational logs unchanged.
- Architecture, deferred-item, test selection, smoke-import, registration
  (`primary=42`, `grouped=101`), pre-commit, and `git diff --check` gates pass.
- Visual evidence contains original `1702x924`, Discord desktop, and mobile samples for NEXT,
  NO UPCOMING, SCHEDULE UNAVAILABLE, long/Unicode, and fallback states under
  `C:\Users\cwatt\.codex\visualizations\2026\07\15\019f652b-ec5a-7b90-a3b2-5a75238a1e5c\phase5d1_next_alert`.
- Final Codex Security report:
  `C:\Users\cwatt\AppData\Local\Temp\codex-security-scans\discord_file_downloader\99039ac9_20260715T114222Z\report.md`.
  Nine source rows were fully reviewed; no reportable finding survived. One production-size Calendar
  sent-state performance question is deferred with evidence in
  `docs/reference/deferred_optimisations.md`.
- K98 PR review: no blocking or non-blocking code finding remains after adding and testing the
  malformed Calendar runtime-source fail-closed guard.
- Promotion-readiness review: do not promote yet. The branch is intentionally uncommitted/unpushed,
  has no mirror PR, and operator Discord smoke is pending. Remotes are correct; SQL/config/dependency
  rollout is not applicable; promotion must later use the patch-based production flow.

## 16. Escalation Gates

Stop and ask only if repository evidence proves one of these:

- exact shared parity requires changing scheduler/dispatcher behavior rather than extracting it;
- healthy-empty versus unavailable KVK source state cannot be represented without a new source or
  persistence contract;
- an authoritative future candidate requires per-occurrence network reads or a new event source;
- current `now` versus `start` semantics are not equivalent and cannot share the approved display label;
- a SQL/schema, persistence format, lead-time, event-type, retry, grace, duplicate-send, or DM-policy
  change is required;
- sharing the helper would break restart/rehydration or scheduled-task ownership;
- the existing typed Phase 5D hero cannot represent the authoritative result without a product-contract change.

Do not silently omit a reminder system, copy scheduler logic into Player Self-Service, display raw
keys, infer popularity or favourites, or show a past timestamp as the next alert.

## 17. Delivery Output And PR Summary

The delivery handoff must include:

- the exact shared helper boundary and live/read-only call sites;
- source-read and no-side-effect proof;
- focused parity results and full validation totals;
- visual evidence for every hero outcome;
- confirmation that the three existing next-event commands and Manage behavior are unchanged;
- Codex Security, K98 PR-review, and promotion evidence;
- any genuinely out-of-scope discovery captured in the deferred framework;
- operator smoke status, without marking it complete before the operator performs it.

Suggested PR headline:

`Complete the Reminders hero with an authoritative, side-effect-free next-alert projection shared with live scheduler eligibility, while preserving every existing reminder and Discord contract.`
