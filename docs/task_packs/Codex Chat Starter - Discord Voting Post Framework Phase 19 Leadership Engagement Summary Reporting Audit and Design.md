# Codex Chat Starter - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design

Use this to start the Phase 19 audit/design slice.

```text
Codex, start Discord Voting Post Framework Phase 19: Leadership Engagement Summary Reporting Audit and Design.

Phase 1 through Phase 18 are complete or audit-closed. Phase 18 confirmed that single-survey
workbook output, cross-survey aggregate workbook/report output, and extra export documentation are
not required now because existing private exports and report bundles are understood and sufficient.

Phase 19 objective:
Audit and design whether leadership needs a higher-level private engagement summary/dashboard/report
for vote and survey activity. Candidate measures include number of vote/survey posts published
across a time window, possible participation opportunities, actual participation counts, aggregate
engagement rates, monthly buckets such as June or July, rolling windows such as last month/last 3
months/last 6 months, and private per-Discord-name participation counts so leadership can identify
whether vote/survey volume is appropriate and whether specific players are not engaging.

Start with audit/scope confirmation. Do not implement new dashboard pages, report files, export
modes, command options, SQL/DAL changes, identity joins, public reporting, retention/redaction
behavior, or SQL-native combined reporting until I approve the product scope, privacy model, data
contract, compatibility, documentation, tests, rollout, rollback, and operator communication plan.

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
- docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design.md
- docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design.md

Use these skills as applicable:
- k98-architecture-scope
- k98-sql-validation because this audit depends on SQL-backed vote/survey participation data,
  identity fields, possible reporting queries, and any SQL-native reporting contracts proposed
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before runtime PR handoff if implementation is approved
- k98-promotion-check before production promotion if implementation is approved
- codex-security security review before runtime PR handoff if implementation touches permissions,
  Discord interactions, SQL/data access, generated reports/exports, private data, file handling,
  user-controlled input, or restart-sensitive flows

Candidate Phase 19 audit scope to confirm:
- Inventory current dashboard/reporting data contracts:
  - /vote_admin dashboard
  - voting.reporting_service.build_admin_leadership_dashboard_report
  - voting.reporting_dal vote/survey summary queries
  - vote and survey response/voter tables through SQL repo validation
- Define leadership questions and success criteria:
  - are vote/survey counts too high for the community
  - is engagement healthy over time
  - which users rarely participate and may need follow-up
  - which content types or time windows show low participation
- Confirm time-window options:
  - last month
  - last 3 months
  - last 6 months
  - monthly buckets such as June, July, and later months
  - whether custom date ranges are needed or explicitly out of scope
- Define counting rules:
  - vote post published count
  - survey post published count
  - open versus closed item inclusion
  - possible participation denominator
  - actual participant count
  - engagement rate
  - per-user participation count
  - treatment of vote changes and survey response changes
  - treatment of one multi-question survey as one participation opportunity
  - treatment of single-question multi-select votes as one participation opportunity
  - treatment of unsubmitted survey drafts as excluded
- Confirm whether engagement should include votes only, surveys only, combined vote/survey
  activity, or separate and combined views.
- Confirm privacy boundaries:
  - private admin/leadership delivery only
  - no public engagement dashboard
  - Discord identity allowed only in the approved private participation profile
  - no raw text/detail answers
  - no per-answer response detail unless separately approved
  - non-participation inference and leadership follow-up expectations
  - HiddenUntilClose semantics for currently open items
- Confirm command and UX ownership:
  - extend /vote_admin dashboard with a private engagement page or filter
  - add a new subcommand under existing /vote_admin only if dashboard extension is unsuitable
  - avoid new top-level commands
  - avoid /vote_admin reshaping or aliases
  - decide whether output is dashboard-only, report/export file, or staged combination
- Confirm SQL posture:
  - whether existing bot-side DAL/reporting queries are enough
  - whether additive bot-side DAL reads are enough
  - whether SQL-native views/procedures are justified by performance or consumer needs
  - exact SQL objects and indexes to validate before implementation
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

Do not include in Phase 19 unless separately approved:
- New voting or survey answer types.
- /vote_admin command reshaping, command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- Changing existing export/report-bundle CSV schemas.
- Single-survey workbook output or cross-survey aggregate workbook output.
- Public dashboards, public raw text/detail display, public participation reports, or public
  voter-level/response-detail exports.
- Raw text/detail answer reporting in engagement summaries.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless explicitly approved.
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
