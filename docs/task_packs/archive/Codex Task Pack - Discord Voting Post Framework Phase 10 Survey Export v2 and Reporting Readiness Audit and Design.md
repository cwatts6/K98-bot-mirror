# Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design`
- Date: `2026-07-04`
- Owner/context: `Follow-up after Phase 9C complete ranking survey questions were delivered, SQL deployed, and smoke tested`
- Task type: `audit | product scope | privacy review | SQL reporting design | export/reporting UX design | implementation closeout`
- One-pass approved: `yes, after architecture/product/privacy/SQL/UX direction was approved`
- Status: `complete; SQL deployed; bot runtime smoke tested; archived as delivery record`

## 2. Objective

Audit and design the next voting-framework slice: private survey export v2 and reporting
readiness now that the survey answer model includes choice, text, details, optional questions,
fixed 1-5 ratings, and complete rankings.

Phase 10 should decide what richer private exports, SQL reporting views/procedures, and dashboard
readiness should look like without changing current public result behavior or implementing a
dashboard prematurely.

The audit/scope packet was completed first, then the first approved runtime slice was delivered:
private single-survey Survey Export v2 as a report bundle plus SQL survey reporting views/procedure.
Workbook exports, cross-survey exports, dashboard/reporting UI, retention/redaction changes,
public detail exports, and broad `/vote_admin` reshaping were not included.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md`

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

## 4A. Phase 10 Delivered Closeout

Operator approval on 2026-07-05 confirmed the first Phase 10 runtime slice should include:

- Private admin/leadership reporting exports.
- Richer CSV or multiple CSVs, with multiple CSVs preferred if one file is limiting.
- SQL reporting views/procedures.
- Dashboard readiness as a contract only; dashboard runtime implementation moves to the next
  phase.
- Discord names included where appropriate because report visibility is limited to admin and
  leadership.

Delivered through:

- Bot mirror PR: `cwatts6/K98-bot-mirror#205`
- Bot production PR: `cwatts6/k98-bot#512`
- SQL PR: `cwatts6/K98-bot-SQL-Server#35`
- SQL deployment: `2026-07-05`
- Bot smoke test: `2026-07-05`

Delivered scope:

- Added `dbo.v_SurveyReportingQuestionSummary` and `dbo.v_SurveyReportingOptionSummary` as
  aggregate, dashboard-safe reporting views that exclude raw text/detail answers, per-user rows,
  Discord IDs, and Discord names.
- Added `dbo.usp_SurveyReporting_ExportV2` as a SQL helper procedure for direct private reporting
  consumers.
- Added `/vote_admin survey_export mode:report_bundle` under the existing command group.
- Report bundle produces separate private CSV files for summary, question aggregates, option
  aggregates, and response detail.
- Response-detail bundle output reuses the existing private raw/detail profile and includes
  spreadsheet-safe Discord IDs plus resolved Discord names.
- Existing `totals` and `response_detail` survey export modes remain compatible.
- Cross-survey exports, workbook exports, dashboard UI/runtime implementation, retention/redaction
  behavior changes, `/vote_admin` reshaping, and public detail exports remain out of scope.

Validation evidence:

- Focused survey/export command tests: `49 passed`.
- Full bot test suite after review fixes: `2315 passed, 2 skipped`.
- Architecture validator passed.
- Deferred optimisation validator passed.
- Selected-test review passed.
- Smoke imports passed.
- Command registration validation passed.
- Pre-commit file pass passed.
- Codex Security diff scan completed with 0 findings before PR handoff.
- SQL repo validation passed for the reporting views/procedure before SQL deployment.

Review hardening:

- Report-bundle command tests were changed from raw source-text substring checks to AST validation
  of the command constant and `discord.OptionChoice` registration.
- Unused reporting row fields were removed from the bot model and DAL mapping:
  `selection_rate_of_responses` and survey-level timestamp/closure fields on
  `SurveyReportingQuestionRow`.

Operator smoke evidence:

- Report bundle creates a private multi-CSV bundle.
- The generated CSV files open cleanly.
- The bundle contains expected rows.
- Regression tests were successful.

## 5. Source Deferred Items

Phase 10 promoted and completed the first approved single-survey export/reporting runtime slice.
The remaining export/reporting and dashboard work stays split into later approval-gated slices.

### Deferred Optimisation
- Area: `voting/export_service.py`, future survey export services, SQL repo survey reporting views/procedures
- Type: architecture
- Description: First-slice survey exports were private, closed-only, and single-survey focused. Phase 8 added text/detail rows, Phase 9A added skipped optional semantics, Phase 9B added rating values, and Phase 9C added ranked-option rows. Phase 10 added a private single-survey report bundle plus SQL survey reporting views/procedure, but cross-survey exports, workbook-style exports, longitudinal reporting, retention/redaction changes, and broader export profile redesign remain outside this delivery.
- Suggested Fix: Keep remaining export/reporting improvements as explicit later slices. Candidate slices include cross-survey summaries, workbook outputs, longitudinal reports, export audit/history summaries, and retention/redaction policy. Preserve private delivery by default and add output-shape regression tests before changing existing export formats.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 survey data model; Phase 8 text/detail exports; Phase 9A optional answer semantics; Phase 9B fixed 1-5 rating exports; Phase 9C ranking exports; SQL repo validation; operator approval for consumers and output formats.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin status`, SQL repo vote/survey reporting views/procedures
- Type: architecture
- Description: Dashboard/reporting readiness remains required follow-up work after Phase 10. Phase 10 created survey aggregate reporting views and a report-bundle export, but no combined private vote/survey dashboard runtime contract exists yet for participation, outcomes/top selections, result visibility, answer-type dimensions, export/audit history, or redaction policy.
- Suggested Fix: Promote this into Phase 11. Define private reporting consumers, SQL or service reporting boundaries, dashboard-safe data shapes, redaction/exclusion rules for raw text/detail and per-user answers, and a phased implementation plan without building a public website.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 result visibility; Phase 6 vote modes; Phase 7 survey model; Phase 8 text/details; Phase 9A optional questions; Phase 9B rating; Phase 9C ranking; SQL repo validation; operator approval for reporting consumers.

## 6. Delivered Phase 10 Scope

### Delivered In Scope

- Inventory current private export surfaces and columns for vote totals, voter audit, survey
  totals, and survey response detail.
- Confirm private export v2 product value and users: admin, leadership, operator, reporting, and
  dashboard consumers.
- Deliver the approved richer single-survey private report bundle as multiple CSV files.
- Deliver approved SQL survey reporting views/procedure.
- Preserve dashboard readiness as a contract boundary only; move dashboard runtime to Phase 11.
- Confirm privacy boundaries for raw text/detail, per-user answers, Discord IDs, names, result
  visibility, closed-only export, and leadership/admin-only access.
- Keep retention/redaction behavior unchanged.
- Validate all SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Identify migration order, rollback posture, deployment sequencing, and migration guards if SQL
  views/procedures/tables are proposed.
- Add `/vote_admin survey_export mode:report_bundle` under the existing grouped command.
- Define tests, smoke plan, Codex Security requirement, and promotion gates.
- Update deferred optimisation status so draft/resume, rating-scale extensions, emoji/icon support,
  and `/vote_admin` reshaping remain visible but separate.

### Remaining Candidate Scope After Phase 10

Possible later slices after Phase 10 include:

- Private cross-survey summary export.
- Private workbook-style export with separate totals/detail/audit sheets.
- SQL reporting views/procedures for combined vote summary facts if Phase 11 proves they are
  needed beyond current vote snapshots.
- Private dashboard/reporting runtime contract without public website work.
- Export audit/history summaries.
- Retention/redaction policy changes, only after explicit privacy approval.
- `/vote_admin status` or reporting UX refinements if the command-surface review approves them.

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

These remain required but separate follow-up slices:

- Private Dashboard/Reporting Runtime Readiness: Phase 11.
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

## 12. Phase 10 Closeout

Phase 10 is complete and archived. It delivered the approved private multi-CSV report bundle and
SQL survey reporting contract, preserved existing totals/response-detail exports, preserved public
aggregate-only result behavior, and left dashboard runtime implementation for Phase 11.

Next active voting slice:

```text
Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design
```
