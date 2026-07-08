# Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design`
- Date: `2026-07-08`
- Owner/context: `Follow-up after Phase 19 delivered the compact private leadership engagement dashboard`
- Task type: `audit | private leadership reporting product scope | privacy review | private CSV export implementation | SQL/data compatibility review`
- One-pass approved: `no`
- Status: `implementation approved and delivered locally; awaiting review, Codex Security sign-off, and operator smoke before archive`

## 2. Objective

Audit and design the richer private per-user engagement breakdown that was intentionally kept out of
the Phase 19 embed.

Phase 19 gave leadership the top-level private dashboard view: total polls, total users,
participation levels, monthly snapshots, and best/worst single poll across a selected time window
and role filter. During smoke testing, the long per-user list proved too large for an embed.

The approved Phase 20 delivery is a private CSV-only first slice under a separate
`/vote_admin engagement` subcommand. Engagement is removed from `/vote_admin dashboard`, which
returns to individual vote/survey inspection only. `/vote_admin engagement` uses private
dropdown/select controls for the time window and role filter, and exports all eligible users sorted
highest engagement first.

Paged Discord lists, workbook output, graph/image output, public reporting, retention/redaction
changes, SQL-native combined reporting, command aliases, top-level commands, and raw/per-answer
detail remain out of scope unless separately approved.

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
- Area: `voting/engagement_export_service.py`, `voting/reporting_service.py`, `/vote_admin engagement`, future private engagement graphs
- Type: architecture
- Description: Phase 20 delivers the approved private per-user CSV engagement export. It intentionally avoids a paged Discord list, workbook output, and graph/image output in this slice. Candidate future graph questions remain separate follow-up work after leadership reviews the CSV data.
- Suggested Fix: Implemented as a separate `/vote_admin engagement` subcommand with select-driven private controls and CSV export. Keep the future graph candidate deferred until leadership confirms whether a later chart should show combined participation, separate vote/survey series, lowest participation, or a distribution summary.
- Impact: medium
- Risk: high
- Dependencies: Phase 19 private engagement dashboard delivered and smoke/regression tested; Phase 20 CSV export scope approved by the operator; SQL validation in `C:\K98-bot-SQL-Server`; privacy approval for private Discord-name participation/non-participation reporting; Codex Security review before runtime PR handoff because implementation touches private exports/files, Discord interactions, SQL-backed data, and user-controlled Discord display/role names.

## 6. Candidate Phase 20 Scope To Confirm

### Approved Implementation Scope

- Output ownership:
  - private CSV export only;
  - separate `/vote_admin engagement` subcommand under the existing `/vote_admin` group;
  - no engagement mode inside `/vote_admin dashboard`;
  - no private paged/scrollable Discord list;
  - no workbook output;
  - no graph/image output in this slice.
- Controls:
  - use dropdown/select controls for window and role filters where possible;
  - keep command options out of the first flow except the slash subcommand itself.
- Per-user fields:
  - Discord user ID, stored/exported as spreadsheet-safe text if exported;
  - Discord display name;
  - role names and selected role/filter context;
  - eligible opportunity count;
  - vote participation count;
  - survey participation count;
  - participation count;
  - missed count;
  - engagement rate;
  - last participation date.
- Export semantics:
  - sort highest engagement first by default;
  - include role/window labels and generation timestamp;
  - include all eligible users even when participation is zero;
  - avoid row duplication when a Discord user has multiple governor IDs or multiple roles.
- Phase 19 filter inheritance:
  - last month, last 3 months, last 6 months;
  - expected roles;
  - all non-bot members;
  - individual Discord roles such as `Kingdom Leadership`;
  - members with no expected role excluded when expected-role filtering is active.
- Counting rules:
  - one closed published vote or survey item is one opportunity;
  - one multi-question survey is one opportunity;
  - one single-question multi-select vote is one opportunity;
  - vote changes and survey response changes do not multiply participation;
  - unsubmitted survey drafts are excluded;
  - raw text/detail answers are excluded.
- Privacy boundaries:
  - private admin/leadership delivery only;
  - no public export/list/graph;
  - Discord identity allowed only in the approved private per-user profile;
  - no raw text/detail answers;
  - no per-answer response detail;
  - no non-leadership distribution of non-participation lists;
  - clear operator expectations for leadership follow-up based on non-participation inference.
- SQL posture:
  - Phase 19 bot-side DAL/service contracts are enough for this slice;
  - additive service/export code is enough;
  - no SQL-native views/procedures or schema changes are approved.
- Tests, Codex Security review, deployment order, rollback posture, smoke checks, and deferred
  follow-up work remain required before handoff.

### Explicitly Out Of Scope Unless Separately Approved

- Public engagement exports, public graphs, public dashboards, or public voter-level/detail output.
- Raw text/detail answer reporting.
- Per-answer response detail.
- Existing export/report-bundle CSV schema changes.
- Single-survey workbook output or cross-survey aggregate workbook output from Phase 18.
- Phase 20 workbook output.
- Phase 20 paged/scrollable Discord list output.
- Phase 20 graph/image output.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless explicitly approved.
- New voting or survey answer types.
- `/vote_admin` command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 7. Approved Design Decisions

The operator approved:

- CSV export only for this slice.
- No paged Discord list.
- Graph output deferred until leadership can assess the exported data and identify one or two key
  graph questions.
- Include role names and vote/survey split columns.
- Include all eligible users by default, sorted highest engagement first.
- Split the leadership engagement flow into `/vote_admin engagement` rather than extending
  `/vote_admin dashboard`.
- Remove engagement from `/vote_admin dashboard` entirely.
- Prefer dropdown/select-list controls instead of command options wherever possible.

## 8. Recommended Starting Posture

Implemented first-slice design posture:

- Use `/vote_admin engagement` as the ownership surface.
- Reuse Phase 19 window and role-filter eligibility semantics.
- Deliver private CSV export first because leadership needs the full per-user list and Discord
  embeds are too limited for this data shape.
- Consider a graph as a later staged output only after leadership confirms the exact graph question.
- Keep raw answers and per-answer detail excluded.
- Keep implementation bot-side with no SQL schema or SQL-native reporting changes.
- Require Codex Security review before runtime handoff because private files, Discord interactions,
  SQL-backed reporting, permissions, and user-controlled Discord display/role names are involved.

## 9. Test Strategy

For this implementation slice, run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

- `tests/test_voting_reporting_service.py` for per-user counting, window and role-filter
  inheritance, zero-participation inclusion, one-Discord-user de-duplication, and no raw-answer
  leakage;
- export tests for schema, spreadsheet-safe Discord ID handling, formula-injection protection,
  sorted rows, generation metadata, and empty/large result sets if file output is approved;
- `tests/test_vote_admin_engagement_view.py` for private owner-only select-driven controls and file
  delivery;
- `tests/test_vote_admin_dashboard_view.py` for removing engagement mode without regressing the
  vote/survey dashboard;
- command-registration tests for the new `/vote_admin engagement` subcommand;
- graph tests only in a later approved graph slice.

## 10. Rollout / Rollback / Smoke Direction

For the approved bot-side CSV export implementation with no SQL migration:

- deploy bot-only after tests and Codex Security review;
- rollback by reverting the bot PR;
- no database rollback needed;
- smoke with an admin/leadership account: open `/vote_admin engagement`, select window and role
  filter, generate the CSV, verify private delivery, verify row counts against the top-level
  engagement summary, confirm zero-participation users appear when expected, confirm role filters
  match Phase 19, confirm raw answers are absent, and confirm `/vote_admin dashboard` still opens
  vote/survey inspection pages without engagement controls.

If SQL-native reporting is later approved:

- deploy SQL objects first;
- validate SQL deployment against a representative database;
- deploy bot after SQL validation;
- rollback by disabling bot usage first, then leaving additive SQL objects in place unless a
  separate destructive cleanup is approved.
