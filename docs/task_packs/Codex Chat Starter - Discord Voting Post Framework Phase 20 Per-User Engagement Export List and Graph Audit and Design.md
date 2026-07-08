# Codex Chat Starter - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design

Use this to start the Phase 20 audit/design slice.

```text
Codex, start Discord Voting Post Framework Phase 20: Per-User Engagement Export List and Graph
Audit and Design.

Phase 1 through Phase 19 are complete or audit-closed. Phase 19 delivered the compact private
leadership engagement dashboard in /vote_admin dashboard, including Total Polls, Total Users,
Participation levels, Monthly Snapshots, best/worst single poll, fixed rolling windows, role-based
eligibility filters such as Expected roles and Kingdom Leadership, one-Discord-user counting even
when a player has multiple governor IDs, raw-answer exclusion, and graceful timeout handling.

Phase 20 objective:
Audit and design the richer private per-user engagement breakdown that was intentionally kept out
of the Phase 19 embed because there are too many users to list usefully in Discord embed text.
Candidate outputs include a private export, a private scrollable/paged list, a private graph, or a
staged combination. Candidate fields include Discord user identity, selected role/role context,
eligible opportunities, participation count, missed count, engagement rate, last participation
date, and optional vote/survey count splits. Confirm whether graphing should show survey-only
counts by user, combined vote/survey participation, separate vote/survey series, a lowest
participation chart, or a distribution summary.

Start with audit/scope confirmation. Do not implement new export files, workbook generation,
graph/image generation, dashboard pages, command options, SQL/DAL changes, file handling,
identity joins, public reporting, retention/redaction behavior, or SQL-native combined reporting
until I approve the product scope, privacy model, data contract, compatibility, documentation,
tests, rollout, rollback, and operator communication plan.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/Discord Voting Post Framework - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 20 Per-User Engagement Export List and Graph Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation because this audit depends on SQL-backed vote/survey participation data,
  role-filtered eligibility, identity fields, and any SQL-native reporting contracts proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated exports/graphs, private data, file handling,
  user-controlled input, or restart-sensitive flows

Candidate Phase 20 audit scope to confirm:
- Confirm output ownership:
  - private CSV export
  - private workbook export
  - private scrollable/paged dashboard list
  - private attached graph/image
  - staged combination and delivery order
- Confirm whether output should live inside the existing /vote_admin dashboard engagement flow or
  under a new existing-/vote_admin subcommand only if dashboard extension is unsuitable.
- Confirm per-user fields:
  - Discord user ID, spreadsheet-safe if exported
  - Discord display name
  - role names or selected role context
  - eligible opportunities
  - participation count
  - missed count
  - engagement rate
  - last participation date
  - optional vote and survey count split
- Confirm graph semantics:
  - survey-only counts by user
  - combined vote/survey participation by user
  - separate vote and survey series
  - lowest-participation chart
  - participation distribution summary
  - graph limits for large user counts
- Confirm Phase 19 filter inheritance:
  - last month
  - last 3 months
  - last 6 months
  - Expected roles
  - All non-bot members
  - individual Discord roles such as Kingdom Leadership
  - members with no expected role excluded when Expected roles is selected
- Confirm counting rules:
  - one closed published vote or survey item is one opportunity
  - one multi-question survey is one opportunity
  - one single-question multi-select vote is one opportunity
  - vote changes and survey response changes do not multiply participation
  - unsubmitted survey drafts are excluded
  - raw text/detail answers are excluded
- Confirm privacy boundaries:
  - private admin/leadership delivery only
  - no public export/list/graph
  - Discord identity allowed only in the approved private per-user profile
  - no raw text/detail answers
  - no per-answer response detail
  - no non-leadership distribution of non-participation lists
  - leadership follow-up expectations for non-participation inference
- Confirm SQL posture:
  - whether Phase 19 bot-side DAL/service contracts are enough
  - whether additive bot-side DAL reads are enough
  - whether SQL-native views/procedures are justified by performance or consumer needs
  - exact SQL objects and indexes to validate before implementation
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

Do not include in Phase 20 unless separately approved:
- Public engagement exports, public graphs, public dashboards, or public voter-level/detail output.
- Raw text/detail answer reporting.
- Per-answer response detail.
- Existing export/report-bundle CSV schema changes.
- Single-survey workbook output or cross-survey aggregate workbook output.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless explicitly approved.
- New voting or survey answer types.
- /vote_admin command reshaping, command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

Expected validation for the audit/docs portion:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py

Stop after the audit/scope packet unless I explicitly approve implementation.
```
