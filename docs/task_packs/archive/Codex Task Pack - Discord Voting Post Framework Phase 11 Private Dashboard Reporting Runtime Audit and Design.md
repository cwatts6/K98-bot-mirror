# Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design`
- Date: `2026-07-05`
- Owner/context: `Completed follow-up after Phase 10 Survey Export v2 report bundle, SQL reporting views, and smoke test`
- Task type: `audit | product scope | privacy review | dashboard/reporting contract design | SQL reporting design`
- One-pass approved: `no`
- Status: `delivered, smoke tested, regression tested, and archived`

## 2. Objective

Audit and design the next reporting slice: private dashboard/reporting runtime readiness for the
Discord Voting Post Framework.

Phase 10 delivered a private single-survey report bundle and SQL survey aggregate reporting
contract. Phase 11 defined and delivered private dashboard/reporting runtime data for
admin/leadership consumers without building a public website, exposing raw answers publicly, or
reshaping `/vote_admin` broadly.

Phase 11 started with audit/scope confirmation and operator approval for admin/leadership
aggregate dashboard-safe reporting only. It did not implement dashboard UI, new commands, combined
SQL views/procedures, cross-survey exports, workbook exports, retention/redaction behavior, or
command reshaping.

## 2A. Delivery Closeout

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#206`
- Production PR: `cwatts6/k98-bot#513`
- Bot smoke/regression confirmation: `2026-07-06`

Delivered:

- Private admin/leadership reporting runtime contract for aggregate dashboard-safe vote and survey
  summaries.
- `voting/reporting_models.py`, `voting/reporting_dal.py`, and `voting/reporting_service.py`.
- Vote summary, vote option summary, survey summary, survey question summary, and survey option
  summary payloads.
- Combined dashboard payload assembly that supports participation, response/vote counts, open and
  closed states, PublicLive/HiddenUntilClose result visibility, vote modes, survey answer types,
  required/optional dimensions, rating aggregates, and ranking aggregates.
- Dashboard-safe privacy boundary that excludes Discord identity, per-user rows, raw text answers,
  and choice details from aggregate reporting summaries.
- Existing private export profiles remain the approved place for Discord IDs, Discord names, raw
  text answers, detail text, and response-level review.
- Batched survey reporting DAL reads that preserve caller survey order.

Validation and smoke evidence:

- Focused reporting DAL/service and survey DAL tests passed.
- Full bot test suite passed with `2323 passed, 2 skipped`.
- Architecture, deferred, selected-test, smoke-import, command-registration, pre-commit, and Codex
  Security review gates passed.
- Operator smoke testing and regression testing completed successfully on 2026-07-06.

Explicitly not delivered in Phase 11:

- Dashboard UI, public website, or public dashboard.
- New Discord commands or `/vote_admin` reshaping.
- Combined SQL views/procedures or SQL-native cross-survey reporting objects.
- Cross-survey exports, workbook exports, or longitudinal reports.
- Retention/redaction behavior changes.
- Public raw text/detail, voter-level, or response-detail posting.
- Draft/resume, rating-scale extensions, emoji/icon support, role-restricted voting,
  governor-linked reporting, saved templates, or public detail exports.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 10 are complete and smoke tested. The voting framework now supports:

- SQL-backed vote posts, one-choice voting, single-question multi-select voting, and SQL-backed
  multi-question surveys.
- Choice, text, detail, optional, fixed 1-5 rating, and complete ranking survey questions.
- One ballot/response per Discord user with response changes when enabled.
- Scheduler reminders, automatic close, manual close, disabled controls after close, and
  restart-safe public openers.
- Guided vote creation and guided survey builder controls.
- PublicLive and HiddenUntilClose result visibility.
- Aggregate-only public survey results, including text counts, rating summaries, and ranking
  summaries.
- Private admin/leadership live status.
- Private closed-only vote totals, voter audit, survey totals, survey response-detail, and Phase
  10 survey report-bundle CSV exports.
- SQL survey reporting views/procedure for aggregate question and option summaries.
- Spreadsheet-safe Discord IDs and CSV formula safety.
- Audit metadata that records counts/status rather than full answer payloads.

Phase 10 smoke testing on 2026-07-05 confirmed that the report bundle creates a private multi-CSV
bundle, opens cleanly, contains expected rows, and preserves existing regression behavior.

## 5. Source Deferred Items

Phase 11 promotes the active dashboard/reporting runtime deferred item.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin status`, SQL repo vote reporting views/procedures
- Type: architecture
- Description: Dashboard/reporting readiness remains required follow-up work after Phase 10. Phase 10 created survey aggregate reporting views and a report-bundle export, but no combined private vote/survey dashboard runtime contract exists yet for participation, outcomes/top selections, result visibility, answer-type dimensions, export/audit history, or redaction policy.
- Suggested Fix: Prepare Phase 11 as contract and runtime design for private dashboard/reporting consumers. Define combined vote/survey summaries, participation, outcomes/top selections, export/audit history, result visibility, mode dimensions, text/detail exclusion or redaction policy, optional/rating/ranking dimensions, and approved long-form reporting variants. Keep public website work out of scope unless separately approved.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 result visibility, Phase 6 vote-mode/cardinality SQL, Phase 7 survey SQL, Phase 8 text/details, Phase 9A optional questions, Phase 9B fixed 1-5 rating questions, Phase 9C complete ranking questions, and Phase 10 report bundle plus SQL survey reporting views are delivered and smoke tested; operator approval for private versus public reporting consumers.

## 6. Proposed Phase 11 Scope

### In Scope For Audit/Design

- Confirm private dashboard/reporting consumers: admins, leadership, operators, or future internal
  reporting tools.
- Define the first dashboard/reporting runtime contract:
  - vote summary dimensions,
  - survey summary dimensions,
  - participation/response counts,
  - result visibility,
  - vote mode and survey answer-type dimensions,
  - top selections/outcomes,
  - rating/ranking aggregate dimensions,
  - text/detail exclusion or redaction policy,
  - export/audit history indicators if approved.
- Decide whether Phase 11 should use existing service/DAL snapshots, new service-owned reporting
  queries, SQL views/procedures, or a hybrid.
- Validate all SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Decide whether a first runtime slice should be:
  - contract-only service/DAL functions,
  - a private admin/leadership dashboard summary command,
  - a private CSV/report bundle extension,
  - a non-Discord internal reporting contract,
  - or no runtime implementation until a later phase.
- Confirm privacy and permission boundaries for raw text/detail, per-user answers, Discord IDs,
  Discord names, hidden-until-close open results, closed-only reporting, and admin/leadership
  access.
- Confirm retention/redaction boundaries and whether Phase 11 should change no retention behavior.
- Define migration order, rollback posture, deployment sequencing, and guards if SQL reporting
  objects are recommended.
- Define tests, smoke plan, Codex Security requirement, and promotion gates.
- Update deferred optimisation status so cross-survey/workbook exports, draft/resume,
  rating-scale extensions, emoji/icon support, and `/vote_admin` reshaping remain visible but
  separate.

### Candidate Implementation Scope If Approved Later

Implementation is not pre-approved. Possible later slices after the audit may include:

- Private dashboard/reporting summary service and DAL contract for combined vote/survey summaries.
- SQL reporting views/procedures for vote summary facts if existing snapshots are insufficient.
- Private admin/leadership Discord summary command or existing `/vote_admin` status/report
  extension if command-surface review approves it.
- Export/reporting history summary if existing audit rows can support it safely.
- Dashboard-safe private reporting payload that a later UI or dashboard can consume.

### Explicitly Out Of Scope Unless Separately Approved

- Public dashboard or public website implementation.
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Exposing raw text/detail or per-user rows in aggregate dashboard views.
- Cross-survey workbook exports.
- Retention/redaction behavior changes.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Survey Draft/Resume runtime implementation.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- `/vote_admin` rename/removal or broad command reshaping.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/detail/optional/rating/ranking survey behavior except as approved
  for reporting compatibility.

These remain required but separate follow-up slices:

- Survey Draft/Resume.
- Rating Scale Extensions.
- Emoji/Icon Support.
- `/vote_admin` Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.

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
| `k98-sql-validation` | Required for reporting view/procedure/query/index/export assumptions. |
| `k98-test-selection` | Required to select reporting, export, permission, privacy, and regression validation. |
| `k98-deferred-optimisation-capture` | Required to keep export redesign, draft/resume, rating scales, emoji/icon, command reshaping, and not-required policy work visible. |
| `k98-discord-command-feature` | Required if command/status/export controls or admin interactions are changed after approval. |
| `k98-pr-review` | Required before runtime PR handoff if implementation is approved. |
| `k98-promotion-check` | Required before production promotion if implementation is approved. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff if implementation touches permissions, Discord interactions, SQL/data access, generated reports, private data, user-controlled text, or restart-sensitive flows. |

## 8. Architecture Questions To Answer

- Should dashboard/reporting runtime data be owned by survey/vote services, a new reporting
  service, SQL views/procedures, or a hybrid?
- Should vote and survey summaries share a common reporting model or remain separate payloads with
  a thin aggregation boundary?
- What is the dashboard-safe minimum contract for Phase 11?
- Are Phase 10 survey aggregate views sufficient for survey dashboard data?
- Are new vote reporting views/procedures needed, or are current vote snapshots/DAL queries enough?
- Should export/audit history be part of Phase 11 or a later reporting-history slice?
- What migration guards are needed if SQL reporting objects are deployed before or after bot code?

## 9. Privacy And UX Questions To Answer

- Who may access private dashboard/reporting output: admin, leadership, operator, or a narrower
  role?
- Should dashboard/reporting be available only for closed votes/surveys, or can private
  admin/leadership open-state reporting reuse current status permissions?
- Should Discord names appear in dashboard summaries, or only in private detail/export profiles?
- How should raw text/detail be represented: excluded, counted, redacted, or linked only to
  existing private response-detail export?
- Should hidden-until-close open results remain hidden from public outputs while still visible to
  admin/leadership private reporting?
- Should the first UX be a Discord command, generated file, internal contract, or docs-only
  contract?

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

Run full pytest before production promotion if implementation changes shared survey/vote DAL,
reporting services, command modes, generated files, or SQL-facing reporting contracts.

## 11. Manual Smoke Plan To Design

The audit should produce a smoke plan covering:

- an admin/leadership user accessing private dashboard/reporting output successfully,
- a normal user being denied,
- at least one closed one-choice vote,
- at least one closed multi-select vote,
- one closed mixed survey with choice, text, detail, optional, rating, and ranking questions,
- HiddenUntilClose behavior that remains private while open and aggregate-only when closed,
- raw text/detail exclusion from aggregate dashboard summaries,
- private response-detail export remaining the raw/detail access path,
- existing `/vote_admin status` and `/vote_admin survey_export` behavior staying compatible.

## 12. Approval Needed

Before implementation, confirm:

- Whether Phase 11 should remain audit/design only or include a first private dashboard/reporting
  runtime slice after scope approval.
- Whether the first runtime output should be a service/DAL contract, Discord command, generated
  file, or internal reporting contract.
- Whether SQL vote reporting views/procedures are approved if current snapshots are insufficient.
- Which private consumers need the output and what privacy profile each consumer may see.
- Whether export/audit history summaries belong in Phase 11 or a later slice.
- Whether any `/vote_admin status`, `/vote_admin survey_status`, or export command changes are
  approved.
