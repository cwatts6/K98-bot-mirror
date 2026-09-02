# Codex Task Pack - Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening

## 1. Task Header

- Task name: `Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening`
- Date: `2026-09-02`
- Owner/context: `Chris Watts / follow-up to mirror PR #252 and production PR #559`
- Task type: `deferred optimisation batch / payload reliability`
- One-pass approved: `no`
- Status: `implementation, validation, and Changes security review complete; mirror PR #253 open`
- Repository: `K98-bot-mirror` bot repository only

## 2. Delivery Prerequisites

Phase 1 owns the unchanged canonical contract in `core/discord_embed_limits.py`. Phase 2A event and
calendar convergence is merged through mirror PR #252 and production PR #559. Before starting,
fetch both remotes and revalidate branch/head,
working-tree state, both PR merge states, and that the Phase 1 and Phase 2A commits are present in
the intended base. If either prerequisite is absent from the working base, stop before runtime or
test implementation and report the exact state.

Expected scope is bot-only. SQL is a no-diff expectation, not permission to infer SQL contracts.
If audit discovers a required schema, stored-procedure, DAL query, or persistence change, use
`k98-sql-validation`, revalidate against `C:\K98-bot-SQL-Server`, and stop for a new approval.

## 3. Required Reading

Read current versions of:

- `AGENTS.md`, `README-DEV.md`, and every core reference indexed by
  `docs/reference/README.md`;
- `docs/reference/events_and_dm_reminders.md`, `docs/reference/Promotion Guide.md`, root and
  applicable nested `SECURITY.md` files;
- `docs/task_packs/archive/Discord Embed Payload Safety Audit Findings.md`;
- archived Phase 1 and Phase 2A task packs and implementation records;
- `core/discord_embed_limits.py` and its focused tests;
- the Ark runtime, state, DAL, rehydration, and test paths in this pack.

Use `k98-architecture-scope` for the first response, `k98-test-selection` for deterministic gates,
`k98-deferred-optimisation-capture` for out-of-scope findings, `k98-security-review-routing` before
security review, `k98-pr-review` for merge readiness, and `k98-promotion-check` only after review.
Use `k98-discord-command-feature` only if the approved implementation touches an interaction view;
this task does not authorize command changes.

## 4. Objective

Measure the complete Discord payload contract for Ark registration, confirmation, completed-match,
team publication, reminder, report, and interaction renderers. Classify each live boundary as
`safe`, `fix now`, `defer`, or `not runtime`. After a separately approved scope response, reuse the
canonical helper to fix only builders proven unsafe by current data contracts and deterministic
normal/boundary/pathological evidence.

The slice must preserve meaningful roster/team content as complete logical lines or groups. It must
not silently truncate rosters, notes, updates, results, or player lists. Output-specific choices for
additional embeds, pages, explicit compaction, attachments, or exact count-bearing omission markers
require operator approval before implementation.

## 5. Canonical Discord Contract

Reconfirm current Discord limits against authoritative documentation and the existing helper before
planning a fix. The present repository contract is:

- 10 embeds per message;
- 256 title characters;
- 4,096 description characters;
- 25 fields per embed;
- 256 field-name characters;
- 1,024 field-value characters;
- 2,048 footer characters;
- 256 author-name characters;
- 6,000 total embed-text characters across all embeds in one message.

Reuse `measure_embed_payload()`, `validate_embed_payload()`,
`require_valid_embed_payload()`, and narrowly appropriate canonical constants. Do not add a
competing limit helper, globally monkeypatch Discord, or force every path through
`send_embed_safe()`.

## 6. Architecture And Delivery Map To Revalidate

Map every builder to its final public, ephemeral, DM, edit, and restart boundary. At minimum:

| Area | Builders / responsibilities | Delivery and identity contracts |
|---|---|---|
| `ark/embeds.py` | Registration, locked, cancelled, confirmation, and match-complete embeds; roster splitting | Registration/confirmation public sends and edits; roster names, notes, updates, results, field count, aggregate |
| `ark/registration_messages.py` | Registration and confirmation send/edit/move behavior | Persisted channel/message references, recreation on missing messages, view attachment/removal, `_allowed_mentions(announce)` |
| `ark/registration_flow.py` | Registration refresh, fuzzy results, user/admin interaction responses | Public registration message plus ephemeral selector/status responses and tracker serialization |
| `ark/confirmation_flow.py` | Closed/cancelled/completed selection, check-in and withdrawal flows, team-builder launch | Confirmation message identity and public edit behavior; ephemeral ownership/permissions |
| `ark/ark_scheduler.py` | Registration opening/locking, public reminder embeds, DM reminder embeds | Existing task timing, eligibility/grace, `AllowedMentions`, sent-state writes, registration message IDs |
| `ark/reminders.py` | Cancellation and other DM reminder paths | Per-user delivery, DM failure handling, reminder-key marking and persistence |
| `ark/team_publish.py` | Header and two team embeds; first-publication plain-text mention chunks | Three public message IDs, send-or-edit/recreate behavior, SQL-backed first-publication claim, unchanged `AllowedMentions(users=True)` |
| `commands/ark_cmds.py` | Existing Ark report pages and command-level refresh/cancel boundaries | Public report response/pagination and existing ephemeral/public visibility; no command surface change |
| `ui/views/ark_report_view.py`, `ui/views/ark_fuzzy_select_view.py`, `ui/views/team_builder_views.py` | Page navigation, fuzzy selection, ephemeral team builder | Interaction owner checks, stored webhook/message edits, ephemeral visibility, published-team handoff |
| `ark/state/ark_state.py`, `ark/reminder_state.py`, `ark/team_state.py` | Message identity, deduplication, and local persisted state | Existing paths, shapes, keys, load/save timing, and restart compatibility |
| `ark/dal/ark_dal.py` | SQL-backed match, roster, team, publication, and message-ID contracts | Review-only unless separately approved; preserve `TeamsFirstPublishedAtUtc` semantics |
| `rehydrate_views.py` | Ark persistent registration-view restoration | Same tracker keys, channel/message IDs, fetch/edit/add-view order, prune/failure behavior |

Inventory any other live Ark embed builder found by current searches. Classify test fixtures,
examples, dead code, and non-Discord formatting as `not runtime` rather than widening scope.

## 7. Data Contracts And Measurements

Trace each dynamic value to its current Sheet, SQL, config, cache, state, or Discord source. Include
alliance names; match dates/times/status; registration notes; update history; result and result
notes; player/sub/check-in rosters; governor display-name snapshots; Discord IDs; team assignments;
reminder labels and text; report rows; caps; and configured channel/mention behavior.

For each approved output, record component lengths, field count, embed count, and 6,000-character
aggregate for:

1. empty/minimum and normal production-representative data;
2. every exact hard boundary;
3. one character, field, or embed over each applicable boundary;
4. realistic pathological source values and maximum credible roster cardinality;
5. one pathological indivisible value, including a single governor name, note, update, result note,
   alliance title, or no-Discord-name suffix;
6. combinations that are locally valid but exceed field count or message aggregate;
7. multi-embed team/report messages, measuring the actual single-message grouping used at send;
8. first-publication plain-text mention chunks separately from embed limits, including the full
   header and the final no-Discord-name suffix.

Do not treat the current `_split_lines()` 1,024-character roster policy or
`MENTION_CHUNK_LIMIT=1800` as proof of the complete contract. Compare all local field/page/soft
limits with the canonical final-message contract.

## 8. Findings And Approval Matrix

The first response must provide one row per runtime builder/delivery boundary with:

- source and maximum credible cardinality;
- current local policy;
- measured normal, exact-boundary, one-over, and pathological result;
- public/ephemeral/DM visibility;
- mentions and `AllowedMentions` behavior;
- message ID, state, deduplication, fallback, and rehydration dependencies;
- disposition: `safe`, `fix now`, `defer`, or `not runtime`;
- proposed output behavior and exact files if `fix now`.

Evidence, not subsystem proximity, selects the runtime diff. A safe builder receives tests or
recorded measurements only when needed to prevent a demonstrated regression; it is not rewritten
for consistency alone.

## 9. Output Policy To Propose Before Coding

For each unsafe output, propose an exact, deterministic policy. The proposal must state:

- the complete logical unit: one roster/player line, one update, one result block, or one team;
- whether fields continue only between complete units;
- which free-text components may be explicitly compacted and the visible marker used;
- whether additional embeds or existing report pages are allowed at that delivery boundary;
- whether an attachment is appropriate and whether it changes the existing UX;
- the exact count-bearing omission marker if all complete units cannot fit;
- how field exhaustion, 6,000-character aggregate exhaustion, and 10-embed exhaustion interact;
- handling for a single unit that cannot fit even on an otherwise empty embed;
- final validation immediately before every changed send/edit/DM boundary;
- metric logging that excludes private content and Discord IDs.

Do not silently clip meaningful lists. Do not break Markdown, mention tokens, timestamps, or URLs.
Do not move public content into DMs/ephemeral output, or vice versa, merely to gain space.

## 10. Behavior That Must Remain Unchanged

Phase 2B must not change:

- commands, command names/grouping/registration/sync, permissions, or interaction ownership;
- public, ephemeral, or DM visibility;
- match selection, ordering, status transitions, registration lifecycle, caps, roster membership,
  check-in, withdrawal, or team assignment;
- reminder eligibility, preferences, grace windows, timing, task names, scheduler cadence,
  sent-state boundaries, deduplication keys, retry/failure behavior, or cancellation/reschedule rules;
- mention copy, token ordering, chunk audience, `AllowedMentions`, or the SQL-backed
  first-publication-only ping decision;
- channel/message IDs, registration/confirmation/team publication identity, recreation behavior,
  tracker/state paths or formats, cache schemas, SQL schema/DAL contracts, or audit-log meaning;
- startup order, persistent-view keys, rehydration fetch/edit/add-view semantics, or prune behavior;
- fallback behavior unless a proven payload rejection requires an explicitly approved presentation
  fallback.

The audit must explain how every proposed fix preserves each applicable invariant.

## 11. Hard Boundaries

- Do not reopen Phase 1 Pre-KVK or Phase 2A event/calendar behavior.
- Do not redesign Ark commands or the public calendar UX.
- Do not change SQL, DAL, config, cache/state schemas, tracker formats, or source data.
- Do not alter Ark orchestration, scheduler lifecycle, or restart architecture.
- Do not combine rankings/history, diagnostics, active-reminder atomicity, atomic Pre-KVK
  reservation, or unrelated Ark orchestration extraction.
- Do not change reminder pings or first-team-publication semantics.
- Do not add a generic parallel helper or global sender wrapper.
- Do not run a standard or deep codebase security scan.

Capture credible out-of-scope issues in the deferred backlog using the required framework; do not
fix them in this slice.

## 12. Proposed File Set

The first response must reduce this review set to an exact approved modification manifest.
Candidates to inspect are:

- runtime: `ark/embeds.py`, `ark/registration_messages.py`, `ark/registration_flow.py`,
  `ark/confirmation_flow.py`, `ark/ark_scheduler.py`, `ark/reminders.py`, `ark/team_publish.py`,
  `commands/ark_cmds.py`, selected `ui/views/ark_*.py` and `ui/views/team_builder_views.py`;
- state/restart review only unless separately approved: `ark/state/ark_state.py`,
  `ark/reminder_state.py`, `ark/team_state.py`, `ark/dal/ark_dal.py`, `rehydrate_views.py`;
- canonical helper review/reuse: `core/discord_embed_limits.py`;
- tests: `tests/test_ark_embeds.py`, `tests/test_ark_confirmation_embed.py`,
  `tests/test_ark_confirmation_flow.py`, `tests/test_ark_registration_messages.py`,
  `tests/test_ark_registration_flow.py`, `tests/test_ark_team_publish_mention.py`,
  `tests/test_ark_scheduler.py`, `tests/test_ark_scheduler_reminders.py`,
  `tests/test_ark_scheduler_dm_failures.py`, the `tests/test_ark_reminder_phase_*.py` family,
  `tests/test_ark_reminder_state.py`, `tests/test_ark_team_state.py`,
  `tests/test_ark_confirm_publish_service.py`, applicable report/view/rehydration tests, and any
  narrowly named payload-boundary test file approved after audit;
- documentation: this pack, the audit findings, `README-DEV.md`, task-pack indexes, and deferred
  records as required by the delivered diff.

`core/discord_embed_limits.py` is not expected to change. A proposed canonical-helper change must
identify a real missing Discord contract shared beyond Ark and receive separate approval.

## 13. Test And Validation Plan

Use `scripts/select_tests.py` after the approved diff exists and record its selectors. At minimum,
propose deterministic tests for every changed renderer and boundary:

- normal, exact-boundary, and one-over component lengths;
- field count and aggregate exhaustion, including combinations of rosters, notes, updates, results,
  and checked-in lists;
- complete logical-unit packing and truthful singular/plural omission counts;
- one pathological indivisible source value;
- multi-embed count/aggregate grouping where a send uses `embeds=[...]`;
- unchanged public/ephemeral/DM visibility and `AllowedMentions`;
- unchanged send-versus-edit/recreate message identity and tracker/state writes;
- first-publication ping exactly once, including restart/SQL-backed behavior;
- reminder eligibility, preference, deduplication, failure, and sent-state boundaries;
- persistent-view restart/rehydration compatibility;
- fallback behavior at the same failure boundary;
- Phase 1 and Phase 2A regression selectors.

Before PR handoff, run or justify:

```powershell
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

## 14. Security, SQL, Smoke, And Rollback

After implementation, route a bot `Changes` review over the exact approved base..head with Deep
off. Retain scan ID, base/head, manifest, coverage, and findings. SQL is a documented no-diff skip
only if no SQL repository or bot SQL-facing contract changed. Do not run Standard/Codebase or Deep.

Production smoke requires separate approval. Begin with builder measurements and existing-message
edits that do not ping. Then select only operator-approved examples needed for changed boundaries:
registration/confirmation edit-in-place, a controlled team re-publication that proves message IDs
without re-pinging, an approved test-recipient DM if relevant, report/page navigation if changed,
and restart rehydration. Verify payload metrics, unchanged visibility/mentions/state/message identity,
no duplicate, and no Discord `50035`. Do not force a first-publication ping or production reminder
solely for smoke unless the operator explicitly approves it.

Rollback is to revert the Phase 2B bot PR and redeploy the prior bot revision. There must be no SQL,
Sheet, config, cache-schema, tracker, or state migration rollback. Existing registration,
confirmation, and team publication message IDs must remain usable by the prior revision.

## 15. Required First Response And Stop Gate

The first response must be audit/scope and architecture planning only. It must:

1. confirm branch/head, working tree, Phase 1/2A prerequisite and PR merge state, and bot-only scope;
2. reconfirm the canonical helper and current Discord hard limits;
3. map every Ark builder to public send/edit, ephemeral interaction, DM, state, message identity,
   first-publication ping, reminder, and rehydration boundaries;
4. trace current data contracts and measure normal, exact-boundary, one-over, and realistic
   pathological payloads;
5. compare local roster/mention/page policies with the full canonical contract;
6. provide the complete `safe` / `fix now` / `defer` / `not runtime` findings matrix;
7. propose exact complete-unit packing, compaction, pagination/additional-embed/attachment, and
   omission-marker behavior for each `fix now` output;
8. prove unchanged selection, lifecycle, permissions, visibility, mentions, state, deduplication,
   message identity, restart/rehydration, SQL first-publication, and fallback behavior;
9. name exact runtime, test, and documentation files proposed for modification;
10. give selector-driven and risk-based tests, Changes-only/Deep-off security routing, SQL skip,
    production smoke, and rollback;
11. list every product/output choice requiring approval.

Stop after that response. Do not edit runtime code or tests until the operator explicitly approves
the proposed Phase 2B implementation scope.

## 16. Acceptance Criteria

- [x] Audit/scope first response is complete and explicitly approved.
- [x] Current base contains the accepted Phase 1 and Phase 2A prerequisites.
- [x] Every live Ark payload boundary has a measured, evidence-backed disposition.
- [x] Only proven unsafe builders enter the approved runtime diff.
- [x] Meaningful rosters/teams/updates/results retain complete units or truthful explicit markers.
- [x] Every changed final payload satisfies the canonical full-message contract.
- [x] Visibility, mentions, permissions, selection, lifecycle, reminders, state, SQL, message IDs,
      deduplication, fallback, and rehydration semantics remain unchanged.
- [x] Focused, selector, validator, pre-commit, full pytest, and log-noise gates pass or are
      explicitly documented.
- [x] The bot diff receives a Changes-only security review with Deep off; SQL has a precise no-diff
      skip if applicable.
- [ ] Production smoke is separately approved and recorded.
- [x] Phase 1, Phase 2A, rankings/history, diagnostics, and unrelated reliability work remain
      outside the slice.

## 17. Approved Implementation Progress

The operator approved the complete first-response proposal on 2026-09-02. Implementation uses
branch `codex/discord-embed-payload-safety-phase-2b` from revalidated base `4290b0fc`. Phase 1 and
Phase 2A are both present in that base, mirror PRs #251/#252 and production PRs #558/#559 are
merged, and the SQL repository remains clean with no SQL-facing change.

The implementation reuses the unchanged canonical helper and hardens only the approved Ark
boundaries. It packs complete roster/team/update units, reserves result and status information,
uses visible compaction for over-contract display values, creates character-budgeted report pages
and first-publication mention chunks, emits exact count-bearing omission markers, and validates at
changed send/edit/DM boundaries. Commands, permissions, visibility, `AllowedMentions`, lifecycle,
caps, assignment, reminder timing/preferences/deduplication, message IDs, SQL-backed first
publication, state formats, fallback, startup, and rehydration remain unchanged.

Focused pathological coverage includes 255-character alliances, 45-by-128-character rosters,
1,024/1,025 field boundaries, oversized confirmation update/result combinations, maximum credible
reminder teams, all-unlinked first-publication names, ephemeral team-builder rendering, and
character-budgeted public reports. The Ark family passes `188`; the complete suite passes
`3090 passed, 2 skipped`; UI imports, architecture, deferred-item, security-routing, import-smoke,
command-registration, Ruff, Black, Pyright, full pre-commit, and the log-noise gate pass, with
production operational logs unchanged. Changes-only scan
`79603f53-69f8-4586-9296-760385dd9420` reviewed the exact
`4290b0fcc3d2568fca3a7fb7715f8baa06477f95..fccde886db2589382d279e6e0ef361dba16369af`
bot range with Deep off, complete coverage of all 11 runtime review items, and zero reportable
findings. Its sealed manifest, coverage, findings, Markdown report, and SARIF artifacts are retained
under the scan record. The SQL repository remained clean and is a documented no-diff security
skip. Mirror PR #253 carries the result. The later PR-reference delta changes only these delivery
records and receives a precise incremental security skip: no runtime, test, configuration, SQL,
permission, interaction, persistence, or deployment behavior changed. Separately approved
production smoke remains to be recorded.
