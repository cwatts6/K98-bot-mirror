# Codex Task Pack - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design`
- Date: `2026-07-07`
- Owner/context: `Follow-up after Phase 17 closed /vote_admin reshaping with no runtime command change`
- Task type: `audit | export/reporting product scope | privacy review | SQL/data compatibility review | documentation planning`
- One-pass approved: `no`
- Status: `complete; audit closed with no runtime export change and no documentation-guidance change`

## 2. Objective

Audit and design whether the voting framework needs cross-survey or workbook-style export
capabilities now that single-vote exports, single-survey totals exports, private response-detail
exports, report-bundle CSV output, and private aggregate dashboard/reporting contracts are all
delivered.

The goal is not to redesign every export because a richer format is possible. The goal is to
confirm whether KD98 admins or leadership have a concrete reporting workflow that is not covered
by the current private CSV exports, report bundle, and `/vote_admin dashboard`, then define the
smallest safe next step if one exists.

Start with audit/scope confirmation. Do not implement new export commands, workbook generation,
cross-survey selectors, SQL/DAL changes, export schema changes, dashboard changes, public
reporting, retention/redaction behavior, or SQL-native combined reporting until the operator
approves product scope, privacy boundaries, data contract, compatibility, documentation, tests,
rollout, rollback, and communication plan.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 17 are complete and smoke tested or audit-closed. The voting framework
supports:

- SQL-backed one-choice votes, single-question multi-select votes, and multi-question surveys.
- Choice, text, detail, optional, configurable rating, and ranking survey questions.
- Configurable rating scales up to 1-10, endpoint labels, named rating choices, and option emoji
  metadata.
- Persisted survey drafts/resume for surveys only, with draft exclusion from result/export/report/
  dashboard surfaces until submit.
- PublicLive and HiddenUntilClose result visibility.
- Scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
  public openers, and one ballot/response per Discord user.
- Private admin/leadership status, export, report-bundle, and `/vote_admin dashboard` surfaces.
- Private totals-only vote CSV export and private voter-level vote audit CSV export.
- Private survey totals CSV export, response-detail CSV export, and report-bundle CSV export.
- Private dashboard-safe aggregate reporting contracts and private aggregate dashboard UI.
- `/vote_admin survey_update` for safe open-survey metadata updates with response-sensitive locks.
- Phase 17 decision to keep `/vote_admin` command paths unchanged and archive the command-surface
  reshaping deferred item.

Phase 17 intentionally did not change runtime command paths, command registration, aliases, help
panels, permissions, autocomplete, usage tracking, SQL, exports, reports, dashboards, or public
rendering.

## 5. Source Deferred Item

### Deferred Optimisation
- Area: `voting/export_service.py`, `voting/survey_export_service.py`, report bundle services, future workbook outputs
- Type: architecture
- Description: Phase 10 delivered private single-survey report-bundle CSV output, Phase 11 delivered dashboard-safe aggregate reporting contracts, and Phase 16 preserved the existing report/export shapes while adding safe survey metadata updates. Cross-survey summaries, workbook-style exports, longitudinal reports, export audit/history summaries, and broader export profile redesign remain outside the delivered single-survey report bundle.
- Suggested Fix: Promoted into this Phase 18 audit/design task pack. Scope a dedicated cross-survey/workbook export redesign only after concrete reporting consumers or operator workflows are identified. Preserve private delivery by default, keep existing CSV profiles backward-compatible unless explicitly versioned, define workbook tabs/columns before implementation, and add output-shape regression tests for every generated file.
- Impact: medium
- Risk: medium
- Dependencies: Phase 10 report bundle delivered and smoke tested; Phase 11 dashboard-safe reporting delivered; Phase 12 draft exclusion delivered; Phase 14 rating-scale export/report compatibility delivered; Phase 16 survey update preserves current export/report schema; Phase 17 keeps command paths stable; reporting consumer requirements; SQL repo validation; no public reporting without separate approval.

## 6. Candidate Phase 18 Scope To Confirm

### In Scope For Audit/Design

- Inventory current vote and survey export/report surfaces:
  - `/vote_admin export mode:totals`
  - `/vote_admin export mode:voter_audit`
  - `/vote_admin survey_export mode:totals`
  - `/vote_admin survey_export mode:response_detail`
  - `/vote_admin survey_export mode:report_bundle`
  - `/vote_admin dashboard`
- Identify the concrete operator or leadership workflow that would justify cross-survey summaries,
  workbook-style output, longitudinal reporting, export audit/history summaries, or a broader
  export profile redesign.
- Decide whether the safest next step is:
  - no runtime export change
  - documentation-only guidance for existing report bundle/dashboard workflows
  - a narrowly scoped private workbook export for one survey
  - a private cross-survey aggregate workbook/report
  - a staged combination with compatibility guarantees
- Confirm whether any existing CSV profile must remain byte/header compatible.
- Confirm whether a new export mode under existing `/vote_admin survey_export` is enough, or
  whether another existing command path is a better fit. Default expectation: keep the existing
  `/vote_admin` group and avoid new top-level commands.
- Confirm privacy boundaries for aggregate-only versus response-detail data, including Discord
  identity, raw text answers, choice details, draft exclusion, and HiddenUntilClose semantics.
- Confirm whether SQL repo changes are needed or whether existing bot-side DAL/reporting
  contracts are sufficient.
- Confirm whether workbook generation needs local temporary files, memory-only streams, file size
  protections, spreadsheet formula safety, and Discord upload fallback behavior.
- Confirm tests, Codex Security requirement, deployment order, rollback posture, smoke checks, and
  deferred follow-up work.

### Candidate Implementation Scope If Approved Later

- Add only the approved private export/report surface.
- Preserve current CSV exports unless an explicitly versioned replacement is approved.
- Preserve private delivery by default.
- Preserve draft exclusion until final submit.
- Preserve dashboard-safe aggregate boundaries where the output is aggregate-only.
- Keep raw text/detail and Discord identity out of aggregate exports unless the approved profile is
  explicitly a private response-detail profile.
- Add output-shape regression tests for every generated file/tab.
- Update canonical command docs, task packs, operator guidance, and smoke references if command
  options or export profiles change.

## 7. Out Of Scope Unless Separately Approved

- New voting or survey answer types.
- `/vote_admin` command reshaping, command aliases, new top-level commands, or help panels.
- Changing submitted vote or survey response semantics.
- Changing Phase 16 survey update locks.
- SQL schema or DAL changes not required by the approved export design.
- Public dashboard, public raw text/detail display, public workbook posting, or public voter-level/
  response-detail exports.
- Retention/redaction policy changes.
- SQL-native combined vote/survey reporting views/procedures unless the Phase 18 audit produces a
  concrete need and the operator approves folding that SQL work into this phase.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Per-rating comments.
- Generated-card custom emoji asset fetching or animation.

## 8. Remaining Separate Follow-Up Slices

- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them and Phase 18 does not explicitly approve them.

Definitely not required unless a later operator decision reverses the status:

- Per-rating comments.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 9. Codex Skills To Use

- `k98-architecture-scope`
- `k98-sql-validation` if SQL objects, DAL queries, export/reporting procedures, workbook source
  data, or SQL-backed reporting contracts are proposed
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before runtime PR handoff if implementation is approved
- `k98-promotion-check` before production promotion if implementation is approved
- `codex-security` security review before runtime PR handoff if implementation touches
  permissions, Discord interactions, SQL/data access, generated reports/exports, private data,
  file handling, user-controlled input, or restart-sensitive flows

## 10. Validation Expectations

For audit/docs-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If implementation is later approved, expected validation areas include:

- existing vote export service tests
- existing survey export service tests
- new workbook/export output-shape regression tests
- formula-safety tests for every string-bearing generated sheet or CSV
- file-size/oversized upload behavior tests
- command registration validation if command options change
- smoke imports
- SQL repo validation if SQL-facing assumptions or SQL objects change
- Codex Security diff scan before runtime PR handoff
- manual Discord smoke testing for private delivery, file attachments, existing CSV profiles, new
  workbook/report output, and oversized fallback behavior

## 11. Audit Packet Acceptance Criteria

The audit/scope packet is ready when it clearly answers:

- Whether a cross-survey/workbook export is needed now.
- Which operator or leadership workflow it serves.
- Which existing export/report/dashboard surfaces already cover the need.
- Which command path and mode would own any approved new export.
- Which files/tabs/columns would be generated and which current CSV profiles remain unchanged.
- Whether output is aggregate-only or response-detail, and which private data fields are allowed.
- How draft exclusion, HiddenUntilClose, raw text/detail boundaries, and Discord identity
  boundaries are preserved.
- Whether SQL changes are required or existing bot-side contracts are enough.
- What tests, smoke checks, deployment order, rollback posture, and security review are required.

Stop after the audit/scope packet unless the operator explicitly approves implementation.

## 12. Phase 18 Audit Outcome

The audit confirmed that cross-survey/workbook export redesign is not needed now.

Operator decision:

- Keep existing private vote and survey CSV exports unchanged.
- Keep the single-survey report bundle unchanged.
- Keep `/vote_admin dashboard` unchanged.
- Do not add a single-survey private workbook export. That option would only repackage the
  already-understood single-survey report bundle into workbook form.
- Do not add a cross-survey private aggregate workbook/report. That is the broader comparison or
  aggregate version, and there is no current leadership workflow requiring it.
- Do not add documentation-only guidance because leadership already understands the delivered
  export/report surfaces.
- Close the active cross-survey/workbook deferred item as not required now rather than carrying it
  in the active deferred backlog. If a future reporting consumer asks for workbook or cross-survey
  comparison output, reintroduce it as a fresh requirement.

Validation completed successfully with no runtime changes:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Command registration remained stable at:

```text
primary=42 grouped_subcommands_detected=97 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=42
/vote_admin: 11 subcommands
```

No SQL validation, Codex Security review, deployment, rollback, or operator retraining is required
for the Phase 18 closeout because no runtime command, permission, Discord interaction, SQL/data,
export/report/dashboard, file-handling, user-input, or restart-sensitive behavior changed.

## 13. Separate Reporting Need Identified

The operator identified a different future reporting need: a higher-level private leadership
summary/dashboard/report for vote and survey engagement.

Candidate scope for a separate audit:

- number of vote/survey posts published across a time window
- possible participation opportunities across those posts
- actual participation counts and engagement rate
- monthly buckets such as June and July
- rolling windows such as last month, last 3 months, and last 6 months
- private per-Discord-name participation counts so leadership can spot players who are not taking
  part and follow up appropriately

This should be scoped separately from workbook export redesign because it touches private identity
reporting, non-participation inference, SQL-backed reporting contracts, dashboard/report
ownership, time-window semantics, tests, Codex Security review, rollout, and rollback.
