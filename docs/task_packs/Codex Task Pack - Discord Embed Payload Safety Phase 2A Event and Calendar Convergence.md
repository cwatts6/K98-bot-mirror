# Codex Task Pack - Discord Embed Payload Safety Phase 2A Event and Calendar Convergence

## 1. Task Header

- Task name: `Discord Embed Payload Safety Phase 2A Event and Calendar Convergence`
- Date: `2026-09-02`
- Owner/context: `Chris Watts / follow-up to mirror PR #251 and production PR #558`
- Task type: `deferred optimisation batch / payload reliability`
- One-pass approved: `no`
- Status: `approved implementation and automated validation complete; production promotion/smoke pending`
- Repository: `K98-bot-mirror` bot repository only

## 2. Required Reading

Before work, read the current versions of:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- every core reference required by that index
- `docs/reference/REVIEW_HELPERS.md`
- `docs/reference/events_and_dm_reminders.md`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_diagnostics.md`
- `docs/reference/deferred_optimisations.md`
- root and applicable nested `SECURITY.md` files
- `docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`
- `core/discord_embed_limits.py` and its focused tests

Use the current `k98-architecture-scope`, `k98-discord-command-feature`, `k98-test-selection`,
`k98-deferred-optimisation-capture`, `k98-pr-review`, `k98-promotion-check`, and
`k98-security-review-routing` skills when their stage is reached.

Revalidate current `main`, the Phase 1 merge state, and current Discord hard limits before relying
on this preparation record. Do not assume the PR preparation commit is still the repository head.

## 3. Objective

Make the live event and calendar embed families consistently obey the canonical Discord payload
contract introduced in Phase 1, including final validation before sends and edits. Preserve the
meaning and cardinality of event/reminder output through complete-item packing, explicit compaction,
or truthful omission markers selected by the owning renderer.

This phase must not redesign commands, visibility, event selection, reminders, pings, persisted
state, rehydration, or scheduler behavior.

## 4. Delivered Prerequisite And Smoke Baseline

Phase 1 delivered:

- dependency-light canonical ownership in `core/discord_embed_limits.py`;
- the exact 1,029-character Pre-KVK regression and complete-event packing;
- final Pre-KVK validation before send/edit;
- repaired `embed_utils.send_embed_safe()` overflow planning;
- sole Pre-KVK ownership of the post-success `prekvk_daily` claim;
- `40 passed` focused validation and `3059 passed, 2 skipped` full/log-noise validation;
- two Changes-only, Deep-off reviews with full coverage and no reportable findings.

On 2026-09-02 the operator successfully exercised `/ops test_embed` against KVK 16 in `DRAFT`:

```text
[PREKVK] Embed payload validated fields=13 chars=1847 max_field_value=530
         event_fields=1 compacted_events=0 omitted_events=0
[PREKVK] Edited existing message id=1544617668999381044
         in channel=1209532242506813540
[/ops test_embed] success (kvk=True, dur=1.33s)
```

The persisted `prekvk_msg_id` matched `1544617668999381044`, and the observed
`prekvk_daily` count was `1`. This proves the canonical validator and same-day edit path were
accepted by Discord without a duplicate post or `50035` rejection.

Important interpretation: test mode bypasses the daily guards. The command edited because the
same-day `prekvk_msg_id` was valid; the daily guard controls a fresh normal production send only
when no editable current message exists. A scheduled fresh-send ping and post-success claim remain
a natural operational observation, not evidence supplied by this test command.

Mirror PR #251 and production PR #558 remain the delivery records. Recheck their final state before
starting Phase 2A.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `event_embed_manager.py`, `event_scheduler.py`, `event_calendar/reminders.py`, `daily_KVK_overview_embed.py`, `ui/views/calendar.py`, and focused event/calendar payload tests
- Type: consistency
- Description: Event and calendar outputs use several local title, description, field-value, field-count, footer, and soft-aggregate policies. Sheet-controlled names and descriptions can reach public reminders, DMs, persistent calendar edits, and interaction pages without one complete final Discord payload check. This is separate from the deferred public calendar command/visibility redesign.
- Suggested Fix: Use `core/discord_embed_limits.py` as the hard-limit owner. Preserve event selection, reminder eligibility, pings, visibility, persistence, commands, and view cardinality while defining complete-event chunking, explicit compaction, or omission markers at each renderer boundary. Add pathological Sheet-value, DM, public-reminder, pinned-edit, pagination, and restart/deduplication regression coverage.
- Impact: high
- Risk: medium
- Dependencies: Phase 1 delivered and operator edit-path smoke accepted; separate Phase 2A audit/scope approval; no command or public/ephemeral redesign.

## 6. Batch Selection And Exclusions

Priority score uses `(Impact + Frequency + Risk Reduction) - Effort`, each scored 1-5.

| Candidate | Impact | Frequency | Risk reduction | Effort | Score | Decision |
|---|---:|---:|---:|---:|---:|---|
| Event/calendar convergence | 5 | 5 | 5 | 4 | 11 | Phase 2A; prioritise now |
| Ark payload hardening | 4 | 3 | 4 | 4 | 7 | Separate evidence-led Phase 2B |
| Rankings/history | 3 | 3 | 3 | 4 | 5 | Later product-policy slice |
| Operator diagnostics | 3 | 3 | 3 | 3 | 6 | Later independent slice |
| Atomic Pre-KVK reservation | 4 | 2 | 4 | 5 | 5 | Separate high-risk reliability design |

Only the first row belongs in this task. The score does not override the distinct persistence and
product decisions required by the excluded candidates.

## 7. Scope

### In Scope

- Functionally map and test live payloads owned by:
  - `event_embed_manager.py` live countdown sends, edits, and rehydrated views;
  - `event_scheduler.py` public reminders, reminder refresh edits, and legacy subscription DMs;
  - `event_calendar/reminders.py` calendar reminder DMs and text fallback;
  - `daily_KVK_overview_embed.py` pinned send/edit and local-time view;
  - `ui/views/calendar.py` pinned calendar, next-event, pagination, and interaction edits.
- Reuse `core/discord_embed_limits.py` as the sole hard-limit model.
- Measure normal, boundary, and pathological payloads from Sheet/cache-controlled names,
  descriptions, variants, emoji, links, channel IDs, dates, footer metadata, and list cardinality.
- Define a product-specific policy per output: preserve complete logical event blocks; compact only
  bounded text segments; paginate where the current view already paginates; use truthful omission
  markers when the owning output cannot show every selected item.
- Validate every final changed embed before send/edit/DM delivery.
- Preserve text fallback reliability on the existing calendar reminder DM route.
- Add structural logging for payload size and overflow action without logging event/user content.
- Add focused regression tests and complete selector-driven broad validation.
- Update the durable findings, task status, and deferred records after implementation.

### Out Of Scope

- Pre-KVK rendering, guard ownership, `prekvk_msg_id`, or claim behavior already delivered in
  Phase 1, except compatibility verification of the canonical helper.
- Ark, MGE, rankings/history, player reports, or operator diagnostic remediation.
- Atomic Pre-KVK reserve/commit/release or any guard persistence redesign.
- Command additions, moves, renames, retirements, command registration, or command resync.
- Changes to permission, public/ephemeral/DM visibility, mention/ping timing, allowed mentions,
  event selection, reminder eligibility, date windows, event caps, ordering, or source data.
- SQL objects, queries, DAL contracts, cache schemas, tracker formats, scheduler task names/timing,
  startup ordering, sent-key semantics, deduplication rules, or rehydration behavior.
- Editing Sheet values as a safety control.
- A public calendar/KVK-calendar UX redesign.
- A global discord.py monkeypatch, mechanical rewrite of every builder, or a new competing limit
  helper.
- A standard or deep Codex Security codebase scan.

## 8. Skills And Security Routing

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | First response must map flows, ownership, persistence implications, policies, tests, and approval questions. |
| `k98-discord-command-feature` | use | Embeds, DMs, message edits, interaction edits, persistent views, and visibility contracts are affected; command surface remains unchanged. |
| `k98-sql-validation` | not applicable | No SQL or DAL contract is expected; stop if audit proves otherwise. |
| `k98-test-selection` | use | Combine selector output with payload, scheduler, DM, interaction, restart, and deduplication risks. |
| `k98-deferred-optimisation-capture` | use | Capture product redesign or separate subsystem findings without widening Phase 2A. |
| `k98-pr-review` | use after implementation | Review final architecture, Discord behavior, tests, and deferrals before merge handoff. |
| `k98-promotion-check` | use before production promotion | Promotion and deployment are separate approvals. |
| `k98-security-review-routing` | use | Route implementation to a Changes-only bot diff review with Deep off. |

### Security Review Decision

| Repository | Decision | Target | Expected setup | Evidence |
|---|---|---|---|---|
| Bot | Changes review | Final approved Phase 2A base..head | Changes + Deep off | Pending implementation; retain scan ID, manifest, coverage, findings, and base/head. |
| SQL | Documented skip | `C:\K98-bot-SQL-Server` | Not applicable | Confirm no SQL diff, query, schema, data-access, deployment, or persistence-contract change. |

No standard or deep codebase scan is authorised. The functional payload audit is engineering scope,
not permission for broader security discovery.

## 9. Mandatory First Response

Start with audit/scope and architecture planning only. Do not change runtime code or tests before
operator approval. The first response must:

1. Report current branch, head, working tree, Phase 1 merge state, and whether work remains bot-only.
2. Reconfirm canonical helper behavior/import dependencies and current Discord limits.
3. Map every listed builder to send/edit/DM/fallback/view/rehydration paths, visibility, mentions,
   persisted message IDs or sent state, and current tests.
4. Record current dynamic inputs and cardinality for each renderer.
5. Calculate normal, exact-boundary, one-over, and realistic pathological payload sizes, including
   title, description, fields, footer, author, field count, embed count, and aggregate text.
6. Identify where local 1,024/25/5,800 policies conflict with or omit the canonical contract.
7. Produce a findings matrix with `safe`, `fix now`, `defer`, or `not runtime` dispositions.
8. Propose the exact complete-item compaction/chunking/omission behavior for each `fix now` output,
   including a pathological single event and field/aggregate exhaustion.
9. Prove how event selection, reminders, pings, state writes, deduplication, restart/rehydration,
   message identity, visibility, and text fallback remain unchanged.
10. Name the exact runtime/test/documentation files proposed for modification.
11. Give selector output plus the risk-based validation, smoke, security, and rollback plan.
12. List open product decisions and stop for approval.

## 10. Architecture Direction

- `core/discord_embed_limits.py` remains the dependency-light hard-limit owner.
- Each renderer owns its output policy and produces a valid final embed; the canonical primitive
  validates and measures but does not decide product truncation, pagination, or omission priority.
- Existing send/edit/DM/view owners remain in place. Do not force these routes through
  `send_embed_safe()`.
- Shared logical-event packing may be extracted only when at least two Phase 2A consumers have an
  identical tested representation. Do not create a generic event framework from superficial
  similarity.
- Scheduler/reminder services retain eligibility, dispatch, sent-state, retry, and deduplication
  ownership. Views retain interaction routing only.
- Persistent tracker and reminder state formats remain byte-compatible unless a separately approved
  task changes them.

## 11. Likely Files

### Review

- `core/discord_embed_limits.py`
- `embed_utils.py`
- `event_embed_manager.py`
- `event_scheduler.py`
- `event_calendar/reminders.py`
- `daily_KVK_overview_embed.py`
- `ui/views/calendar.py`
- directly supporting cache, tracker, scheduler, startup, and command call paths
- related tests under `tests/`

### Modify After Approval

Expected runtime candidates, subject to the first response:

- `event_embed_manager.py`
- `event_scheduler.py`
- `event_calendar/reminders.py`
- `daily_KVK_overview_embed.py`
- `ui/views/calendar.py`

Do not change `core/discord_embed_limits.py` or `embed_utils.py` unless the audit proves a canonical
contract defect or a narrowly reusable Phase 2A primitive and the operator approves that expansion.

Expected focused test candidates:

- `tests/test_calendar_reminders.py`
- `tests/test_calendar_reminders_dispatch.py`
- `tests/test_calendar_pinned_embed.py`
- `tests/test_calendar_view_pagination.py`
- `tests/test_calendar_views.py`
- `tests/test_daily_kvk_overview_lifecycle.py`
- `tests/test_event_scheduler_subscription_matching.py`
- `tests/test_event_scheduler_at_start_projection.py`
- a focused live-event/embed-manager payload test if no current file provides the correct home

### Documentation

- this task pack and its chat starter
- `README-DEV.md`
- `docs/task_packs/README.md`
- `docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`
- `docs/reference/deferred_optimisations.md`
- `docs/reference/archive/deferred_optimisations_resolved.md` after completion

## 12. Implementation Requirements

For every approved output:

- preserve meaningful complete event blocks and valid Markdown, links, mentions, custom emoji, and
  Discord timestamp tokens;
- bound dynamic title, description, field name/value, footer, author, field count, embed count, and
  all-embed aggregate through the canonical constants;
- never silently discard selected events; use an explicit count-bearing marker;
- compact a pathological single event by changing only approved free-text segments and retaining
  its identity, timing, and action link where present;
- reserve budget for fixed trailing fields/footer before filling dynamic lists;
- validate the final payload immediately before every changed send/edit/DM call;
- retain existing text fallback and mark reminder state only after the existing successful delivery
  boundary;
- retain current local-time views, custom IDs, message IDs, trackers, pin behavior, timeouts,
  ownership guards, mentions, and allowed-mention behavior;
- log only renderer, route, field count, aggregate, maximum component sizes, and overflow action;
  never log full Sheet text, DM content, user data, or protected links.

## 13. Refactor Decisions

| Issue | Initial decision | Reason |
|---|---|---|
| Local 25/1,024/5,800 calendar policy | audit/fix now where invalid | It does not account for every final component and duplicates canonical hard-limit ownership. |
| Live event title/description bounds | audit/fix now if reproduced | Sheet-controlled content reaches public send/edit paths. |
| Legacy reminder public/DM bounds | audit/fix now if reproduced | Same payload root cause across scheduled/DM delivery. |
| Daily overview line-by-line clipping | audit/fix now | It can cut logical blocks and does not validate aggregate/footer. |
| Calendar command/visibility redesign | defer | Product and command-surface decision, explicitly outside payload convergence. |
| Reminder state or scheduler redesign | defer | No behavior defect requires persistence/lifecycle expansion in this phase. |
| Ark/rankings/diagnostics | defer | Separate scored batches with different product policies. |

New deferrals must use the repository's exact Deferred Optimisation format.

## 14. Test And Validation Plan

The path selector currently recommends:

```powershell
python -m pytest -q tests/test_calendar_*.py
python -m pytest -q tests/test_ui_imports.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

Risk-based focused coverage must additionally prove:

- normal, exact-limit, and one-over dynamic title/description/name/value/footer/aggregate cases;
- multiple-event field/page packing, field-slot exhaustion, aggregate exhaustion, and a single
  pathological Sheet-controlled event;
- stable event order, selection count, timestamps, links, emoji, local-time controls, and omission
  counts;
- public send and same-message edit output equivalence;
- calendar DM embed success, existing HTTP fallback to text, and no sent-state write after complete
  delivery failure;
- public reminder mention timing and allowed-mention behavior unchanged;
- pinned/live/daily message IDs, tracker writes, missing-message recreation, and rehydrated views
  remain compatible;
- pagination owner guard, timeout/button behavior, and page cardinality remain unchanged;
- no command-registration or visibility change;
- structural logs contain metrics but not event or user content.

After implementation, run in order:

```powershell
.\.venv\Scripts\python.exe -m pytest -q <approved focused files>
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\validate_codex_security_routing.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Fix only task-related failures. Document unrelated failures without widening scope.

## 15. Acceptance Criteria

- [x] Audit/scope first response is approved before runtime/test edits.
- [x] Current main, Phase 1 prerequisite, and actual runtime flows are revalidated.
- [x] Each changed event/calendar payload satisfies the full canonical contract.
- [x] Meaningful event lists retain complete items or a truthful count-bearing marker.
- [x] Pathological single items retain valid Markdown/timestamps/links and explicit compaction.
- [x] Final validation occurs before every changed send/edit/DM boundary.
- [x] Event selection, ordering, caps, reminder eligibility, pings, visibility, and fallback behavior
      are preserved.
- [x] Message IDs, tracker/state formats, sent-state semantics, deduplication, and rehydration remain
      compatible.
- [x] No SQL, command, permission, config, source-data, cache-schema, or scheduler contract changes.
- [ ] Focused, selector, validator, pre-commit, full pytest, and log-noise gates pass or are
      explicitly documented.
- [ ] Final bot diff receives a Changes-only security review with Deep off; SQL has a documented
      no-diff skip.
- [ ] Production smoke is separately approved and recorded before final acceptance.
- [ ] Ark, rankings/history, diagnostics, and atomic Pre-KVK reservation remain separate.

## 16. Production Smoke And Rollback

Production promotion/deployment requires the normal separate workflow. Smoke should begin with
non-pinging/admin-safe paths and must avoid generating duplicate public reminders or unsolicited
DMs.

After approval, verify representative examples of:

- an existing live event or pinned calendar message edited in place;
- calendar pagination/local-time interaction;
- daily KVK overview edit or a safely controlled builder equivalent;
- one calendar reminder DM to an approved test recipient, including fallback only if safely
  inducible;
- one public reminder only at an approved time, confirming unchanged mention behavior;
- payload metric logs with no `50035`, state duplication, or content leakage.

Rollback is to revert the Phase 2A bot PR and redeploy the prior bot revision. There is no SQL,
Sheet, data, cache-schema, or state migration rollback. Existing tracker/message IDs should remain
usable by the prior revision.

## 17. Required Delivery Output

Provide:

1. Summary and exact file manifest.
2. Runtime flow and payload-policy matrix.
3. Helpers reused and any approved extraction.
4. SQL/persistence/restart statement.
5. Refactor and deferred decisions.
6. Focused and broad test results.
7. Changes-only security evidence and SQL skip.
8. Production smoke evidence or precise pending items.
9. Rollback and the next separately gated phase.

## 18. Implementation Record

The operator approved the review-first scope on 2026-09-02. The implementation uses
`core/discord_embed_limits.py` without changing it, adds a narrowly opt-in complete-event mode to
`LocalTimeToggleView`, and enables that mode only for Phase 2A live-event, reminder, daily-overview,
and calendar consumers. Pre-KVK keeps the default compatibility mode.

Daily overview and local-time fields split only between events. Pinned calendar output uses date
continuations and a count-bearing `/calendar` marker. Calendar command pages retain eight logical
source items per page and omit only whole trailing items with an exact page-local marker when the
canonical aggregate cannot fit all eight. Valid source links up to the SQL/cache contract of 500
characters remain intact; over-contract links receive an explicit link-omitted marker rather than a
broken truncated URL.

The implementation changes no command, permission, visibility, mention, event selection/order/cap,
reminder eligibility, source contract, SQL, cache/state schema, tracker format, scheduler timing/task
name, startup order, message identity, pinning, deduplication, sent-state boundary, fallback, or
rehydration semantics. Focused Phase 2A and lifecycle coverage passed `74`; the calendar selector
equivalent passed `157`; the full suite passed `3077 passed, 2 skipped`. The isolated
`tests/test_ui_imports.py` selector command still exposes an unrelated pre-existing test-stub gap for
`constants.PLAYER_STATS_LAST_CACHE`; the full suite passes that test under normal collection order.
