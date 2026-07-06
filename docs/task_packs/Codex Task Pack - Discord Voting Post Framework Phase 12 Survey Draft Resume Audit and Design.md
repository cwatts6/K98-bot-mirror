# Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design`
- Date: `2026-07-06`
- Owner/context: `Follow-up after Phase 11 private dashboard/reporting runtime contract, smoke testing, and regression testing`
- Task type: `audit | product scope | privacy review | SQL persistence design | Discord interaction design`
- One-pass approved: `no`
- Status: `prepared as the next voting-framework slice`

## 2. Objective

Audit and design persisted survey draft/resume readiness for the Discord Voting Post Framework.

Phase 11 delivered private admin/leadership aggregate dashboard-safe reporting contracts. Phase 12
should now decide whether and how survey respondents can save or recover in-progress survey
answers after timeout, restart, interruption, or intentional pause, without leaking unsubmitted
answers into public results, dashboards, status summaries, or exports.

Start with audit/scope confirmation. Do not implement persisted drafts, new SQL tables,
new commands, command reshaping, retention/redaction behavior changes, or Discord interaction
runtime changes until the product scope, privacy, SQL, permissions, UX direction, tests, smoke
plan, deployment order, rollback posture, and deferred-scope direction are approved.

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
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 11 are complete and smoke tested. The voting framework now supports:

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
- Private closed-only vote totals, voter audit, survey totals, survey response-detail, and survey
  report-bundle CSV exports.
- Private admin/leadership aggregate dashboard-safe reporting contract for vote/survey summaries.
- Dashboard-safe exclusion of Discord identity, per-user rows, raw text answers, and choice
  details.
- Spreadsheet-safe Discord IDs and CSV formula safety in existing private export profiles.
- Audit metadata that records counts/status rather than full answer payloads.

Phase 11 smoke and regression testing on 2026-07-06 confirmed the private aggregate reporting
runtime contract and preserved regressions.

## 5. Source Deferred Item

Phase 12 promotes the active survey draft/resume deferred item.

### Deferred Optimisation
- Area: `voting/`, future survey response UX, SQL repo survey response tables
- Type: architecture
- Description: Phase 7 delivered choice-only surveys without persisted partial player response drafts. This keeps privacy and restart behavior simple, but longer surveys may eventually need SQL-backed draft responses, resume after timeout/restart, expiry/cleanup rules, and clearer abandoned-draft retention. Phase 9A delivered optional-question completion semantics, Phase 9B delivered rating questions, Phase 9C delivered ranking questions, Phase 10 delivered report-bundle exports, and Phase 11 delivered dashboard-safe aggregate reporting contracts without adding persisted drafts.
- Suggested Fix: Keep Phase 12 audit/design first and do not implement persisted draft runtime until product scope, privacy, SQL, permissions, UX, tests, smoke plan, deployment order, rollback posture, and deferred boundaries are approved. Add explicit draft status, partial answer storage, cleanup/expiry policy, resume UX, optional-question interaction rules using the delivered Phase 9A semantics, answer-type handling for choice/text/detail/rating/ranking, and tests for restart, timeout, close, stale draft, and export/dashboard exclusion behavior.
- Impact: medium
- Risk: high
- Dependencies: Phase 7 choice-only surveys; Phase 8 text/details; Phase 9A optional semantics; Phase 9B fixed 1-5 ratings; Phase 9C rankings; Phase 10 report bundle; Phase 11 private aggregate reporting contract; privacy approval for storing unsubmitted answers; SQL repo validation; restart and cleanup tests.

## 6. Proposed Phase 12 Scope

### In Scope For Audit/Design

- Confirm whether survey draft/resume applies only to surveys, not one-choice or multi-select
  vote posts.
- Confirm product value and target user journeys:
  - survey panel timeout,
  - modal interruption,
  - Discord restart/deploy interruption,
  - voluntary save-and-return,
  - accidental close/cancel,
  - reopening an unfinished survey response.
- Define whether drafts are automatic, explicit, or both.
- Define the draft identity key, likely `SurveyID` plus Discord user ID, without Discord names or
  governor identity unless separately approved.
- Define how drafts coexist with the existing one-submitted-response-per-Discord-user model.
- Define draft behavior when response changes are enabled or disabled after a final submission.
- Define answer-type handling for:
  - `SingleChoice`,
  - `MultiSelect`,
  - `Text`,
  - optional choice details,
  - optional questions,
  - fixed 1-5 ratings,
  - complete rankings.
- Define completion rules:
  - required answers are validated at final submit,
  - optional answers may remain skipped,
  - partial rankings remain invalid unless a future slice approves them,
  - duplicate ranking positions remain invalid.
- Confirm privacy boundaries for unsubmitted answers:
  - no public results,
  - no PublicLive or HiddenUntilClose aggregate counts,
  - no private dashboard-safe aggregate summaries,
  - no existing totals/detail/report-bundle exports,
  - no raw text/detail exposure outside the active respondent flow unless explicitly approved.
- Confirm whether admins/leadership can see draft counts only, and whether even draft counts should
  be deferred.
- Confirm close behavior:
  - drafts cannot be submitted after survey close,
  - close should not reveal draft content,
  - draft cleanup after close should be defined or deferred as a retention-policy follow-up.
- Confirm restart behavior, stale interaction handling, duplicate in-flight sessions, and
  idempotency.
- Decide whether Phase 12 needs new SQL tables/procedures, service/DAL-only queries, or no runtime
  implementation until a later phase.
- Validate all SQL-facing assumptions against `C:\K98-bot-SQL-Server` before implementation.
- Define migration order, rollback posture, deployment sequencing, and guards if SQL persistence is
  recommended.
- Define tests, smoke plan, Codex Security requirement, and promotion gates.
- Update deferred optimisation status so rating-scale extensions, emoji/icon support,
  `/vote_admin` reshaping, cross-survey/workbook exports, retention/redaction policy changes, and
  SQL-native combined reporting remain visible but separate.

### Candidate Implementation Scope If Approved Later

Implementation is not pre-approved. Possible later runtime work may include:

- SQL-backed draft response and draft answer persistence.
- Service/DAL APIs for saving, loading, clearing, expiring, and submitting drafts.
- Private respondent resume UX from the existing public `Answer survey` opener.
- Clear/discard draft controls.
- Draft exclusion from public cards, private dashboard summaries, and all current export profiles.
- Focused cleanup/expiry behavior if explicitly approved as part of this slice.

## 7. Out Of Scope Unless Separately Approved

- Dashboard UI, public website, or public dashboard.
- New top-level commands or broad `/vote_admin` reshaping.
- Public raw text/detail export posting.
- Public voter-level/detail export posting.
- Cross-survey workbook exports.
- Retention/redaction policy changes beyond documenting a draft posture.
- Rating-scale extensions or custom rating scales.
- Per-option emoji/icon support.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- SQL-native combined vote/survey reporting views/procedures unless a later reporting slice
  approves them.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing submitted survey behavior except as approved for draft compatibility.

## 8. Required Separate Follow-Up Slices

- Rating Scale Extensions.
- Emoji/Icon Support.
- `/vote_admin` Reshaping.
- Cross-survey/workbook export redesign.
- Retention/redaction policy changes.
- Optional SQL-native combined reporting views/procedures if reporting consumers or performance
  needs justify them.

Definitely not required unless a later operator decision reverses the status:

- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.

## 9. Validation Expectations

For the audit/docs portion:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

If runtime implementation is later approved, select focused tests after the design is approved.
Likely areas include survey service, survey DAL, survey post views, export/reporting exclusion,
scheduler/close behavior, restart/idempotency, command registration, smoke imports, full pytest,
SQL validation, and Codex Security review.

## 10. Stop Point

Stop after the audit/scope packet unless implementation is explicitly approved.
