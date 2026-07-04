# Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design`
- Date: `2026-07-04`
- Owner/context: `Follow-up after Phase 9C complete ranking survey questions were delivered, SQL deployed, and smoke tested`
- Task type: `audit | product scope | privacy review | SQL reporting design | export/reporting UX design`
- One-pass approved: `no`
- Status: `active next-slice audit/design starter; implementation requires explicit approval`

## 2. Objective

Audit and design the next voting-framework slice: private survey export v2 and reporting
readiness now that the survey answer model includes choice, text, details, optional questions,
fixed 1-5 ratings, and complete rankings.

Phase 10 should decide what richer private exports, SQL reporting views/procedures, and dashboard
readiness should look like without changing current public result behavior or implementing a
dashboard prematurely.

Start with audit/scope confirmation. Do not implement SQL reporting views/procedures, workbook
exports, cross-survey exports, dashboard/reporting UI, command changes, export shape changes, or
retention/redaction behavior until the architecture, product scope, privacy, SQL, permissions, UX,
tests, smoke plan, migration order, rollback posture, and deferred-scope direction are approved.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9C Ranking Survey Questions.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 9C are complete and smoke tested. The framework now supports:

- SQL-backed one-choice vote posts.
- Single-question multi-select vote posts.
- SQL-backed multi-question surveys.
- Choice, text, detail, optional, fixed 1-5 rating, and complete ranking survey questions.
- One ballot/response per Discord user with changes when enabled.
- Scheduler reminders, automatic close, manual close, disabled controls after close, and
  restart-safe public openers.
- Guided vote creation and guided survey builder controls.
- PublicLive and HiddenUntilClose result visibility.
- Aggregate-only public survey results, including rating and ranking summaries.
- Private admin/leadership live totals/status.
- Private closed-only totals CSV, voter-level vote audit CSV, and survey response-detail CSV.
- Spreadsheet-safe Discord IDs and CSV formula safety.
- Audit metadata that records counts/status rather than full answer payloads.

Phase 9C smoke testing on 2026-07-04 confirmed ranking survey creation, required ranking response
flow, optional ranking skip/clear behavior, ranking update/regression behavior, public aggregate
ranking cards, and compatibility for existing choice/text/detail/optional/rating surveys,
multi-select votes, and one-choice votes.

## 5. Source Deferred Items

Phase 10 promotes the active required follow-up items for richer exports and reporting readiness.

### Deferred Optimisation
- Area: `voting/export_service.py`, future survey export services, SQL repo survey reporting views/procedures
- Type: architecture
- Description: First-slice survey exports are private, closed-only, and single-survey focused. Phase 8 added text/detail rows, Phase 9A added skipped optional semantics, Phase 9B added rating values, and Phase 9C added ranked-option rows, but cross-survey exports, workbook-style exports, private reporting views/procedures, and dashboard-ready reporting contracts are still undefined.
- Suggested Fix: Run Phase 10 as an audit/design slice. Validate current export consumers, define private export v2 goals, decide whether SQL views/procedures or service-owned queries should back reporting, preserve private delivery by default, define retention/redaction boundaries, and prepare implementation slices only after approval.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 survey data model; Phase 8 text/detail exports; Phase 9A optional answer semantics; Phase 9B fixed 1-5 rating exports; Phase 9C ranking exports; SQL repo validation; operator approval for consumers and output formats.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin status`, SQL repo vote/survey reporting views/procedures
- Type: architecture
- Description: Dashboard/reporting readiness is required follow-up work, but no private reporting contract exists for combined vote/survey summaries, participation, outcomes, result visibility, answer-type dimensions, export/audit history, or redaction policy.
- Suggested Fix: Include dashboard/reporting readiness in Phase 10 audit/design. Define private reporting consumers, SQL or service reporting boundaries, dashboard-safe data shapes, redaction/exclusion rules for raw text/detail and per-user answers, and a phased implementation plan without building dashboard UI in the audit slice.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 result visibility; Phase 6 vote modes; Phase 7 survey model; Phase 8 text/details; Phase 9A optional questions; Phase 9B rating; Phase 9C ranking; SQL repo validation; operator approval for reporting consumers.

## 6. Proposed Phase 10 Scope

### In Scope For Audit/Design

- Inventory current private export surfaces and columns for vote totals, voter audit, survey
  totals, and survey response detail.
- Confirm private export v2 product value and users: admin, leadership, operator, reporting, and
  dashboard consumers.
- Decide whether Phase 10 should later implement:
  - richer single-survey exports,
  - cross-survey exports,
  - workbook-style exports,
  - SQL reporting views/procedures,
  - service-owned reporting queries,
  - dashboard-ready private summary contracts,
  - export audit/history summaries.
- Confirm privacy boundaries for raw text/detail, per-user answers, Discord IDs, names, result
  visibility, closed-only export, and leadership/admin-only access.
- Confirm retention/redaction rules and whether raw answer data should be included, summarized,
  omitted, or split into separate private/export-only profiles.
- Validate all SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Identify migration order, rollback posture, deployment sequencing, and migration guards if SQL
  views/procedures/tables are proposed.
- Confirm command/builder/admin UX direction if `/vote_admin export` or `/vote_admin status` needs
  new modes.
- Define tests, smoke plan, Codex Security requirement, and promotion gates.
- Update deferred optimisation status so draft/resume, rating-scale extensions, emoji/icon support,
  and `/vote_admin` reshaping remain visible but separate.

### Candidate Implementation Scope If Approved Later

Implementation is not pre-approved. Possible later slices after the audit may include:

- Private export v2 output profile for closed surveys.
- Private cross-survey summary export.
- Private workbook-style export with separate totals/detail/audit sheets.
- SQL reporting views/procedures for survey and vote summary facts.
- Private dashboard-ready data contract without public website work.
- `/vote_admin export` mode additions or admin status refinements if the command-surface review
  approves them.

### Explicitly Out Of Scope Unless Separately Approved

- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public dashboard or website implementation.
- Draft/resume runtime implementation.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- `/vote_admin` rename/removal or broad command reshaping.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/rating/ranking survey behavior except as approved
  for reporting/export compatibility.

These are required but separate follow-up slices:

- Survey Draft/Resume.
- Rating Scale Extensions.
- Emoji/Icon Support.
- `/vote_admin` Reshaping.

These are definitely not required and should remain excluded unless a later operator decision
reverses that status:

- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 7. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before implementation. |
| `k98-sql-validation` | Required for SQL views/procedures, reporting facts, indexes, migration order, and rollback assumptions. |
| `k98-test-selection` | Required to select export/reporting/status/permission/privacy validation. |
| `k98-deferred-optimisation-capture` | Required to keep draft/resume, rating scales, emoji/icon, command reshaping, and not-required policy work visible. |
| `k98-discord-command-feature` | Required if command modes, status views, export controls, or admin interactions are changed after approval. |
| `k98-pr-review` | Required before runtime PR handoff if implementation is approved. |
| `k98-promotion-check` | Required before production promotion if implementation is approved. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff if export/reporting implementation touches permissions, Discord interactions, SQL/data access, file generation, user-controlled text, or private data surfaces. |

## 8. SQL And Reporting Questions To Answer

- Are current DAL/service queries enough for reporting, or should the SQL repo own reporting
  views/procedures?
- Should reporting use stable fact-like views for:
  - vote posts and options,
  - vote responses,
  - survey posts and questions,
  - survey choice answers,
  - text/detail answer counts,
  - rating aggregates,
  - ranking aggregates,
  - export/audit events?
- Should raw text/detail answers remain service/export-only, or be excluded from SQL reporting
  views by default?
- What indexes are needed for cross-survey reporting without slowing response submission?
- What migration guards are needed if bot code can deploy before SQL reporting objects?
- What rollback posture is safe for reporting-only views/procedures versus persisted export
  history tables?

## 9. UX And Export Questions To Answer

- Should `/vote_admin export` remain a simple CSV command, gain new export modes, or defer command
  changes until `/vote_admin` reshaping?
- Should export v2 be one CSV, multiple CSVs, or an XLSX workbook?
- Should response-detail export remain one survey at a time?
- How should export profiles communicate raw-answer privacy to admins?
- Should status/live totals and export outputs share the same aggregate model?
- How should oversized exports be delivered or blocked?
- What smoke data set is needed to cover choice, text, detail, optional, rating, and ranking
  questions in one reporting fixture?

## 10. Test Strategy

Expected audit/docs validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Expected implementation validation if a runtime slice is approved:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_survey_export_service.py tests\test_survey_dal.py tests\test_vote_admin_cmds.py
```

Run full pytest before production promotion if implementation changes shared survey DAL, export
services, command modes, generated files, or SQL-facing reporting contracts.

## 11. Manual Smoke Plan To Design

The audit should produce a smoke plan using one closed survey that includes:

- required single-choice,
- required multi-select,
- required text,
- optional skipped text/detail,
- required rating,
- optional skipped rating,
- required ranking,
- optional skipped or cleared ranking.

Smoke should confirm private delivery, closed-only enforcement, formula safety, spreadsheet-safe
Discord IDs, raw text/detail privacy, rank/rating aggregate correctness, export row counts, and no
public detail exposure.

## 12. Approval Needed

Before implementation, confirm:

- Whether Phase 10 should remain audit/design only or include a first export/reporting runtime
  slice after scope approval.
- Which export v2 formats are approved.
- Whether SQL reporting views/procedures are approved.
- Whether dashboard readiness means data-contract design only or a private dashboard prototype.
- Whether any `/vote_admin export` or `/vote_admin status` command changes are approved.
- Which private consumers need the output and what privacy profile each consumer may see.
