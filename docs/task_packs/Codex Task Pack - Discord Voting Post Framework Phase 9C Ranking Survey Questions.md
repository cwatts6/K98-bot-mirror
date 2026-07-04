# Codex Task Pack - Discord Voting Post Framework Phase 9C Ranking Survey Questions

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 9C Ranking Survey Questions`
- Date: `2026-07-04`
- Owner/context: `Follow-up after successful Phase 9B fixed 1-5 rating delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | privacy/export review`
- One-pass approved: `no`
- Status: `active next-slice audit/design starter; implementation requires explicit approval`

## 2. Objective

Audit and design the next advanced survey slice: ranking survey questions.

Phase 9B delivered fixed 1-5 rating questions. Phase 9C should decide whether and how to add a
small, predictable ranking question type without changing existing one-choice votes, multi-select
votes, choice/text/rating surveys, optional-question semantics, exports, or close/restart behavior.

The safest candidate slice is a complete-ranking question over the existing survey option model:
players rank all options for a ranking question using unique ranks. Required ranking questions must
be fully ranked before submit; optional ranking questions may be skipped entirely, but partial
rankings should remain out of the first slice unless the audit explicitly proves a safe UX and
storage contract.

Start with audit/scope confirmation. Do not implement SQL migrations, ranking runtime storage,
response UI, export shape changes, dashboard/reporting implementation, or command changes until
the Phase 9C architecture, product scope, privacy, SQL, permissions, and UX direction are approved.

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
- `docs/reference/ENV_REFERENCE.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`
- `docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md`
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 9C Ranking Survey Questions.md`

## 4. Delivered Baseline

Phase 1 through Phase 9B are complete and smoke tested. The voting framework supports SQL-backed
vote posts, one-choice voting, single-question multi-select voting, SQL-backed choice/text/rating
multi-question surveys, one ballot/response per Discord user, response changes when enabled,
scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
public controls, guided vote/survey creation, PublicLive and HiddenUntilClose result visibility,
private admin live totals, private totals/voter-audit/survey-detail CSV exports, required and
optional choice/text/rating survey questions, required free-text survey questions, one optional
details capture per choice question, fixed 1-5 rating aggregates, formula-safe text/detail/export
cells, aggregate text-question totals rows, answered/skipped optional export/status semantics, and
no public raw text/detail/per-user rating exposure.

Phase 9B smoke testing on 2026-07-04 confirmed rating-question creation, disabled option/detail
controls for rating questions, required and optional rating submission, optional rating skip
behavior, average-rating public display, and compatibility for existing choice/text/detail/optional
surveys, multi-select votes, and one-choice votes.

## 5. Source Deferred Item

This task promotes the ranking half of the active advanced survey question-types deferred item.

### Deferred Optimisation
- Area: `voting/`, future survey ranking question types, SQL repo survey answer tables
- Type: architecture
- Description: Ranking questions remain outside Phase 9B. They need a dedicated ranked-option answer contract, duplicate-rank prevention, clear Discord entry/edit UX, conservative public aggregate semantics, and private response-detail export representation.
- Suggested Fix: Prepare Phase 9C ranking questions using existing `SurveyQuestionOptions` plus a dedicated SQL ranking answer contract, likely `dbo.SurveyRankingAnswers`, with uniqueness constraints for rank and option per response/question after source-of-truth SQL validation. Keep public output aggregate-only and private response-detail exports closed-only/admin-leadership-only.
- Impact: high
- Risk: high
- Dependencies: Phase 9A optional-question semantics delivered and smoke tested; Phase 9B fixed 1-5 rating questions delivered and smoke tested; SQL repo migration approval for ranking; export shape approval; focused service/DAL/view/export tests; Discord smoke testing for prefill/update/close/restart behavior.

## 6. Proposed Phase 9C Scope

### In Scope For Audit/Design

- Confirm product value for complete ranking questions over 2-6 existing survey options.
- Confirm whether required ranking means every option receives one unique rank.
- Confirm optional ranking semantics: skipped entirely or fully ranked in the first slice.
- Confirm builder UX without free-typed question-type values.
- Confirm player UX for entering, reviewing, editing, clearing/skipping optional rankings, and
  submitting ranking answers without Discord drag/drop support.
- Confirm PublicLive and HiddenUntilClose aggregate-only behavior for ranking results.
- Confirm private admin/leadership live status behavior.
- Confirm private closed-only totals and response-detail export shape for ranked options and
  skipped optional ranking questions.
- Preserve formula safety and spreadsheet-safe Discord ID behavior.
- Define audit metadata without storing full answer payloads in audit JSON.
- Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
- Select tests, smoke plan, migration order, rollback posture, and deferred follow-up work.

### Candidate Implementation Scope If Approved

- Add `QuestionType = Ranking`.
- Reuse `SurveyQuestionOptions` for rankable choices.
- Add dedicated SQL-backed submitted ranking answer storage.
- Add service validation for unique ranks, complete required rankings, optional skip, and stale
  option rejection.
- Add private player controls for rank assignment/editing with submitted-answer prefill.
- Add aggregate-only public result rendering.
- Add private status/export representation.
- Preserve all Phase 1 through Phase 9B behavior.

### Out Of Scope Unless Separately Approved

- Partial top-N rankings.
- Ties, weighted scoring variants, pairwise voting, Condorcet/IRV/STV logic, or winner election
  algorithms beyond conservative aggregate ranking summaries.
- Ranking comments.
- Custom rating scales, 1-10 scales, rating labels, or rating comments.
- Persisted partial player response drafts or resume.
- Per-option emoji/icon support.
- Dashboard/reporting implementation.
- Cross-survey export/workbook redesign.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Renaming/removing `/vote_admin`.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/rating/optional survey behavior except as explicitly approved for
  ranking compatibility.

## 7. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before coding. |
| `k98-discord-command-feature` | Required because builder/player/status/export UX uses Discord interactions, modals, buttons, selects, and private panels. |
| `k98-sql-validation` | Required for ranking schema, constraints, indexes, migration order, DAL queries, and export assumptions. |
| `k98-test-selection` | Required to select focused service/DAL/view/export/scheduler/regression tests. |
| `k98-deferred-optimisation-capture` | Required to keep drafts, rating scale polish, reporting, export, emoji/icon, policy, and template work visible. |
| `k98-pr-review` | Required before implementation handoff if a runtime slice is approved. |
| `k98-promotion-check` | Required before production promotion if implementation is approved. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff because ranking answers touch Discord interactions, permissions/privacy, user input, SQL persistence, result aggregation, generated exports, and restart-sensitive response flows. |

## 8. Architecture Direction To Confirm

- Preserve the separate SQL-backed survey model; do not fold surveys back into `VotePosts`.
- Add `QuestionType = Ranking` through SQL and service validation, not a free-text builder value.
- Reuse existing survey question options for rankable choices.
- Use a dedicated submitted-answer table instead of overloading choice, text, or rating answers.
- Store one row per ranked option for each response/question.
- Enforce one rank per option and one option per rank for a submitted response/question.
- Keep required/optional completion semantics aligned with Phase 9A.
- Prefer complete rankings for the first slice; defer partial ranking unless explicitly approved.
- Keep all service validation authoritative; do not rely on Discord component limits alone.
- Keep public outputs aggregate-only. Per-user ranked rows are private export only.
- Keep private response-detail exports admin/leadership-gated and closed-only.
- Keep audit JSON to operational metadata, not full answer payloads.
- Preserve no persisted partial player drafts unless a separate draft/resume slice is approved.

## 9. SQL Contract To Validate

Validate against `C:\K98-bot-SQL-Server` before implementation:

- Expand `CK_SurveyQuestions_Type` to allow `Ranking`.
- Reuse `dbo.SurveyQuestionOptions` for ranking options.
- Add dedicated ranking answer storage, expected candidate shape:
  - `SurveyRankingAnswerID bigint IDENTITY`
  - `SurveyResponseID bigint NOT NULL`
  - `SurveyID bigint NOT NULL`
  - `SurveyQuestionID bigint NOT NULL`
  - `SurveyQuestionOptionID bigint NOT NULL`
  - `DiscordUserID decimal(20,0) NOT NULL` or the existing Discord ID type used by survey tables
  - `RankValue tinyint NOT NULL`
  - `CreatedAtUtc datetime2 NOT NULL`
  - `UpdatedAtUtc datetime2 NOT NULL`
- Add foreign keys to survey response/question/option tables using existing cascade/delete posture.
- Add uniqueness so one response ranks each option at most once for a ranking question.
- Add uniqueness so one response assigns each rank at most once for a ranking question.
- Add constraints or service validation for valid rank bounds based on option count.
- Add export/status indexes by `SurveyID`, `SurveyQuestionID`, response, option, and rank where
  justified.
- Confirm migration compatibility guards for bot/schema deployment ordering.
- Confirm rollback posture before submitted ranking rows exist.

## 10. UX Direction To Confirm

Builder:

- Add `Ranking` to the existing question type selector only after SQL/runtime approval.
- Require 2-6 options using the existing survey option controls.
- Keep required as the default and reuse the Phase 9A required/optional toggle.
- Disable rating-scale-only controls and details controls where they do not apply.
- Make complete-ranking expectations clear in the builder review.

Player response panel:

- Pick a Discord-native entry pattern during audit, such as rank-by-rank select menus, option-by-
  option rank selects, or compact reorder buttons.
- Show required missing, complete, invalid duplicate, and optional skipped states consistently.
- Keep Submit disabled only while required questions are missing or invalid.
- Allow optional rankings to be skipped/cleared.
- Preserve prefilled editing for submitted responses when response changes are allowed.
- After successful submit, preserve Phase 8/9A/9B closeout behavior by clearing/closing private
  controls.

Public presentation:

- PublicLive may show aggregate-only ranking summaries such as average rank per option, first-place
  counts, and rank distribution per option if approved.
- HiddenUntilClose should hide ranking aggregates while open and reveal aggregate-only ranking
  results at close.
- Public outputs must not show per-user ranking rows.

## 11. Export And Audit Direction

Totals export:

- Preserve existing columns where possible.
- Add ranking aggregate rows/fields only after approval, likely average rank, first-place count,
  rank distribution, answered count, and skipped count.
- Keep text/detail answers aggregate-only in totals export.

Response-detail export:

- Preserve one row per response/question/option ranking entry or define a deterministic compact
  representation if one row per response/question is approved instead.
- Include `QuestionType = Ranking`, `IsRequired`, `AnswerStatus`, option label, rank value, and
  skipped optional representation.
- If response changes are enabled and original-answer reporting is already available for that
  export path, define original-rank and changed semantics.
- Keep `DiscordUserID` spreadsheet-safe and all user-controlled strings formula-safe.

Audit:

- Submission/change audit may record required count, optional answered count, optional skipped
  count, ranking answer count, invalid/duplicate rejection counts, and changed flag.
- Export audit may record column profile, row count, byte count, oversized status, and delivery
  status.
- Do not store full answer payloads in audit JSON.

## 12. Test Strategy

Expected focused coverage:

- `tests/test_survey_service.py`: ranking validation, duplicate-rank rejection, missing required
  ranking enforcement, optional ranking skip/clear, stale option rejection, response changes
  allowed/blocked, and existing choice/text/rating optional regressions.
- `tests/test_survey_dal.py`: ranking answer persistence, replacement semantics, snapshot loading,
  export row mapping, missing-migration compatibility guards, and transaction rollback behavior.
- `tests/test_survey_post_view.py`: builder ranking controls, player ranking entry/edit/prefill,
  submit gating, optional clear/skip, timeout/stale behavior, and owner-only panels.
- `tests/test_survey_export_service.py`: ranking totals, response-detail ranking columns,
  formula safety, spreadsheet-safe Discord IDs, closed-only enforcement, and oversized audit
  metadata.
- Survey presentation/render tests for PublicLive and HiddenUntilClose ranking aggregates.
- `tests/test_vote_admin_cmds.py` and command registration validation if command wiring changes.

Baseline audit/docs validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Recommended validation before runtime PR handoff:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_survey_service.py tests\test_survey_dal.py tests\test_survey_post_view.py tests\test_survey_export_service.py tests\test_voting_scheduler.py tests\test_vote_admin_cmds.py
```

Run full pytest before production promotion if runtime implementation touches shared survey DAL,
service, views, scheduler, exports, or command wiring.

## 13. Manual Smoke Plan

1. Create a required ranking survey with 2-6 options and submit a complete unique ranking.
2. Confirm Submit is blocked when a required ranking is missing or incomplete.
3. Confirm duplicate ranks or duplicate options are rejected or prevented by the UI and service.
4. Create a mixed required/optional survey with choice, text, rating, and ranking questions.
5. Confirm Submit succeeds when an optional ranking is skipped and all required questions are
   answered.
6. Reopen a submitted response and confirm the ranking is prefilled.
7. Change a ranking when response changes are allowed; confirm the update is recorded.
8. Attempt a change when response changes are blocked; confirm rejection.
9. Confirm PublicLive shows aggregate ranking summaries only.
10. Confirm HiddenUntilClose hides open aggregates and reveals aggregate-only ranking results at
    close.
11. Confirm private admin status shows ranking answered/skipped counts.
12. Close manually and by scheduler; confirm disabled controls and restart-safe survey opener
    behavior.
13. Export totals and response detail privately; confirm ranking values, skipped optional rankings,
    spreadsheet-safe Discord IDs, formula safety, and closed-only enforcement.
14. Regression smoke existing one-choice vote, multi-select vote, choice/text/details survey,
    optional question survey, and rating survey behavior.

## 14. Deferred Follow-Up Work

Keep these separate unless explicitly approved:

- Survey Draft/Resume: SQL-backed partial drafts, resume after timeout/restart, cleanup/expiry,
  privacy approval, and export exclusion for unsubmitted drafts.
- Rating Scale Extensions: custom rating scales, 1-10 scales, scale labels, rating comments, and
  backward compatibility for delivered fixed 1-5 ratings.
- Survey Export v2 / Reporting Readiness: cross-survey exports, workbook outputs, private
  reporting views/procedures, retention/redaction policy, and dashboard/reporting decisions.
- Emoji/Icon Support: option metadata, Discord button/select rendering, export representation, and
  generated-card glyph QA.
- Voting Identity/Policy Work: role-restricted voting, governor-linked voting/reporting, saved
  templates, public detail exports, and `/vote_admin` command reshaping.

## 15. Approval Needed

Before implementation, confirm:

- Whether complete rankings over existing 2-6 survey options are approved for Phase 9C.
- Whether optional ranking questions should be skipped entirely or require a complete ranking when
  answered.
- Which Discord-native ranking entry UX should be used.
- Which public aggregate ranking metrics are approved.
- Which response-detail export shape is approved.
- Whether partial/top-N ranking remains deferred after the first ranking slice.
