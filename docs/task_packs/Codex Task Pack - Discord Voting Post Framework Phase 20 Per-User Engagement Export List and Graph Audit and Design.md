# Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design`
- Date: `2026-07-08`
- Owner/context: `Follow-up after Phase 19 delivered the compact private leadership engagement dashboard`
- Task type: `audit | private leadership reporting product scope | privacy review | export/list/graph design | SQL/data compatibility review`
- One-pass approved: `no`
- Status: `active; audit/scope only until output format, privacy, data contract, file-handling posture, docs, tests, rollout, rollback, and operator communication direction are approved`

## 2. Objective

Audit and design the richer private per-user engagement breakdown that was intentionally kept out of
the Phase 19 embed.

Phase 19 now gives leadership the top-level private dashboard view: total polls, total users,
participation levels, monthly snapshots, and best/worst single poll across a selected time window
and role filter. During smoke testing, the long lowest-participation user list proved too large for
an embed. Phase 20 should decide whether that detail belongs in:

- a private CSV export;
- a private workbook export;
- a private scrollable/paged dashboard list;
- an attached private graph/image;
- or a staged combination, such as export first and graph/list later.

Start with audit/scope confirmation. Do not implement new export files, workbook generation,
graph/image generation, dashboard pages, command options, SQL/DAL changes, file handling,
identity joins, public reporting, retention/redaction behavior, or SQL-native combined reporting
until the operator approves product scope, privacy boundaries, data contract, compatibility,
documentation, tests, rollout, rollback, and communication plan.

## 3. Required Reading

Read first:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design.md`

Use these skills as applicable:

- `k98-architecture-scope`
- `k98-sql-validation` because this audit depends on SQL-backed vote/survey participation data,
  role-filtered eligibility, identity fields, and any proposed SQL-native reporting contract
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if implementation is approved
- `codex-security` security review before runtime PR handoff if implementation touches
  permissions, Discord interactions, SQL/data access, generated exports/graphs, private data,
  file handling, user-controlled input, or restart-sensitive flows

## 4. Delivered Baseline

Phase 1 through Phase 19 are complete and smoke tested or audit-closed. The voting framework
supports:

- SQL-backed one-choice votes, single-question multi-select votes, and multi-question surveys.
- Choice, text, detail, optional, configurable rating, and ranking survey questions.
- Persisted survey drafts/resume for surveys only, with draft exclusion from result/export/report/
  dashboard surfaces until submit.
- PublicLive and HiddenUntilClose result visibility.
- Private admin/leadership status, export, report-bundle, and `/vote_admin dashboard` surfaces.
- Private dashboard-safe aggregate reporting contracts and private aggregate dashboard UI.
- Private Phase 19 engagement dashboard mode with fixed rolling windows, role-filtered eligibility,
  compact top-level metrics, monthly snapshots, best/worst single poll, raw-answer exclusion, and
  one-Discord-user counting regardless of governor IDs.
- Phase 17 decision to keep `/vote_admin` command paths unchanged.
- Phase 18 decision that single-survey workbook output and cross-survey aggregate workbook/report
  output are not required now.

Phase 19 intentionally did not add the richer per-user export/list/graph. It also did not change
existing export/report-bundle CSV schemas, retention/redaction behavior, public reporting,
SQL-native combined reporting objects, governor-linked reporting, or role-restricted voting.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `voting/reporting_service.py`, `voting/reporting_dal.py`, `/vote_admin dashboard`, future private engagement exports/lists/graphs
- Type: architecture
- Description: Phase 19 delivered the compact private leadership engagement dashboard and intentionally removed the long lowest-participation user list from the embed. Leadership still needs an audit/design slice for a richer private per-user engagement breakdown that may be an export, scrollable/paged list, graph, or staged combination. Candidate fields include Discord user identity, role context, eligible opportunities, participation count, missed count, engagement rate, and last participation date, using the Phase 19 time-window and role-filter semantics.
- Suggested Fix: Promoted into this active Phase 20 audit/design task pack. Confirm whether first delivery should be CSV, workbook, private paged/scrollable dashboard list, attached graph/image, or staged combination; whether the graph is survey-only, combined vote/survey, or separate vote/survey series; allowed per-user fields; privacy boundaries for Discord identity and non-participation inference; file-handling/export safety; SQL source contracts; tests; Codex Security review; rollout; and rollback before implementation.
- Impact: medium
- Risk: high
- Dependencies: Phase 19 private engagement dashboard delivered and smoke/regression tested; active Phase 20 audit/design approval; SQL validation in `C:\K98-bot-SQL-Server`; privacy approval for private Discord-name participation/non-participation reporting; Codex Security review before runtime PR handoff if implementation touches private exports/files, Discord interactions, SQL/data access, generated graph artifacts, user-controlled input, or restart-sensitive flows.

## 6. Candidate Phase 20 Scope To Confirm

### In Scope For Audit/Design

- Confirm output ownership:
  - private CSV export;
  - private workbook export;
  - private scrollable/paged dashboard list;
  - private attached graph/image;
  - staged combination and delivery order.
- Confirm whether the first slice should inherit the existing `/vote_admin dashboard` engagement
  controls or add a new sub-action under existing `/vote_admin` only if dashboard extension is
  unsuitable.
- Confirm per-user fields:
  - Discord user ID, stored/exported as spreadsheet-safe text if exported;
  - Discord display name;
  - role names or selected role context;
  - eligible opportunity count;
  - participation count;
  - missed count;
  - engagement rate;
  - last participation date;
  - optional vote count and survey count split.
- Confirm graph semantics:
  - survey-only counts by user;
  - combined vote/survey participation by user;
  - separate vote and survey series;
  - lowest-participation graph, participation distribution graph, or top/bottom user chart;
  - graph limits for large user counts.
- Confirm list/export semantics:
  - sort lowest participation first by default;
  - support zero-participation view;
  - include role/window labels and generation timestamp;
  - include all eligible users even when participation is zero;
  - use newest participation date for tie-breaks where needed;
  - avoid row duplication when a Discord user has multiple governor IDs or multiple roles.
- Confirm Phase 19 filter inheritance:
  - last month, last 3 months, last 6 months;
  - expected roles;
  - all non-bot members;
  - individual Discord roles such as `Kingdom Leadership`;
  - members with no expected role excluded when expected-role filtering is active.
- Confirm counting rules:
  - one closed published vote or survey item is one opportunity;
  - one multi-question survey is one opportunity;
  - one single-question multi-select vote is one opportunity;
  - vote changes and survey response changes do not multiply participation;
  - unsubmitted survey drafts are excluded;
  - raw text/detail answers are excluded.
- Confirm privacy boundaries:
  - private admin/leadership delivery only;
  - no public export/list/graph;
  - Discord identity allowed only in the approved private per-user profile;
  - no raw text/detail answers;
  - no per-answer response detail;
  - no non-leadership distribution of non-participation lists;
  - clear operator expectations for leadership follow-up based on non-participation inference.
- Confirm SQL posture:
  - whether Phase 19 bot-side DAL/service contracts are enough;
  - whether additive bot-side DAL reads are enough;
  - whether SQL-native views/procedures are justified by performance or consumer needs;
  - exact SQL objects and indexes to validate before implementation.
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

### Explicitly Out Of Scope Unless Separately Approved

- Public engagement exports, public graphs, public dashboards, or public voter-level/detail output.
- Raw text/detail answer reporting.
- Per-answer response detail.
- Existing export/report-bundle CSV schema changes.
- Single-survey workbook output or cross-survey aggregate workbook output from Phase 18.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless explicitly approved.
- New voting or survey answer types.
- `/vote_admin` reshaping, command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 7. Initial Design Questions

Implementation must not start until the operator approves these decisions:

- Should the first output be export-only, list-only, graph-only, or staged?
- If export is first, should it be CSV or workbook?
- If graph is first, should it show survey-only counts by user, combined vote/survey counts, or
  separate vote/survey series?
- Should graphs include every eligible user, only the lowest-participation users, or a distribution
  summary that can handle large populations?
- Which per-user identity fields are allowed?
- Should role names be included in row output, or should the selected role/filter label be enough?
- Should the output include all eligible users, only non-participants, or filterable groups?
- Should the output include separate vote and survey participation counts as well as combined?
- Should Phase 20 reuse the Phase 19 engagement mode filters exactly?
- Should generated files use existing private ephemeral response patterns, and how should timeout
  behavior be handled?
- Is additive bot-side DAL reporting approved as the SQL posture, with SQL-native combined
  reporting deferred?
- Is the proposed test, Codex Security, rollout, rollback, and smoke plan approved?

## 8. Recommended Starting Posture

Recommended first-slice design posture:

- Keep `/vote_admin dashboard` as the ownership surface unless the audit proves it is unsuitable.
- Reuse Phase 19 window and role-filter eligibility semantics.
- Prefer private CSV export first if leadership mainly needs the full per-user list, because it is
  easy to inspect, filter, and verify, and avoids overcrowding Discord embeds.
- Consider a graph as a second staged output unless leadership confirms the exact graph question.
- Keep raw answers and per-answer detail excluded.
- Keep implementation bot-side with additive DAL/service reads unless performance evidence or a
  direct SQL consumer justifies SQL-native reporting.
- Require Codex Security review before runtime handoff if any private file, graph artifact, SQL
  query, Discord interaction, permission path, or user-controlled input path changes.

## 9. Test Strategy

For this audit/docs-only slice, run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

If implementation is approved later, add or update:

- `tests/test_voting_reporting_service.py` for per-user counting, window and role-filter
  inheritance, zero-participation inclusion, one-Discord-user de-duplication, and no raw-answer
  leakage;
- `tests/test_voting_reporting_dal.py` for bounded SQL reads, correct vote/survey participant
  sources, and no text/detail answer reads;
- export tests for schema, spreadsheet-safe Discord ID handling, formula-injection protection,
  sorted rows, generation metadata, and empty/large result sets if file output is approved;
- graph tests for deterministic aggregation, large-user limits, and artifact creation/cleanup if
  graph output is approved;
- `tests/test_vote_admin_dashboard_view.py` and presentation tests if a paged list or export action
  is added to the dashboard;
- command-registration tests if any `/vote_admin` option or subcommand changes.

## 10. Rollout / Rollback / Smoke Direction

If bot-side export/list/graph implementation is approved with no SQL migration:

- deploy bot-only after tests and Codex Security review;
- rollback by reverting the bot PR;
- no database rollback needed;
- smoke with an admin/leadership account: open engagement dashboard, select window and role filter,
  generate the per-user output, verify private delivery, verify row/graph counts against the
  top-level dashboard, confirm zero-participation users appear when expected, confirm role filters
  match Phase 19, confirm raw answers are absent, and confirm existing dashboard pages still work.

If SQL-native reporting is later approved:

- deploy SQL objects first;
- validate SQL deployment against a representative database;
- deploy bot after SQL validation;
- rollback by disabling bot usage first, then leaving additive SQL objects in place unless a
  separate destructive cleanup is approved.
