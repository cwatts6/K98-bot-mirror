# Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 9B Rating Survey Questions`
- Date: `2026-07-04`
- Owner/context: `Follow-up after successful Phase 9A optional survey-question delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | privacy/export review`
- One-pass approved: `no`
- Status: `implemented locally after operator approval; pending SQL deployment and Discord smoke`

## 2. Objective

Design and, if approved, implement the next advanced survey slice: rating survey questions.

Phase 9A delivered optional questions for existing `SingleChoice`, `MultiSelect`, and `Text`
survey types. Phase 9B should add a small, predictable rating question type without changing
existing vote behavior, choice/text survey behavior, or the optional-question semantics that have
now been smoke tested.

The safest intended slice is a fixed 1-5 numeric rating question type with aggregate-only public
results, private admin/leadership detail export, service-owned validation, SQL-backed persistence,
and no persisted partial player drafts.

Start with audit/scope confirmation. Do not implement SQL migrations, rating runtime storage,
response UI, export shape changes, dashboard/reporting implementation, or command changes until
the Phase 9B architecture, product scope, privacy, SQL, permissions, and UX direction are approved.

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
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md`

## 4. Delivered Baseline

Phase 1 through Phase 9A are complete and smoke tested. The voting framework supports SQL-backed
vote posts, one-choice voting, single-question multi-select voting, SQL-backed choice/text
multi-question surveys, one ballot/response per Discord user, response changes when enabled,
scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
public controls, guided vote/survey creation, PublicLive and HiddenUntilClose result visibility,
private admin live totals, private totals/voter-audit/survey-detail CSV exports, required and
optional choice/text survey questions, required free-text survey questions, one optional details
capture per choice question, formula-safe text/detail export cells, aggregate text-question totals
rows, optional answered/skipped export/status semantics, and no public raw text/detail exposure.

Phase 9A smoke testing on 2026-07-04 confirmed optional questions can be skipped while the response
still submits successfully when all required questions are answered.

## 5. Source Deferred Item

This task promotes the rating half of the active advanced survey question-types deferred item.

### Deferred Optimisation
- Area: `voting/`, future survey rating question type, SQL repo survey answer tables
- Type: architecture
- Description: Rating questions remain outside Phase 9A. They need a dedicated scalar answer contract, aggregate average/distribution behavior, private response-detail export columns, and careful public/private visibility rules.
- Suggested Fix: Add a fixed 1-5 `Rating` question type first, backed by a dedicated `dbo.SurveyRatingAnswers` table and aggregate-only public presentation. Keep ranking questions, custom scale labels, 1-10 scales, comments on ratings, dashboard/reporting, and cross-survey export redesign out of scope unless separately approved.
- Impact: high
- Risk: high
- Dependencies: Phase 9A optional survey questions delivered and smoke tested; SQL repo migration approval; export shape approval; focused service/DAL/view/export tests; Discord smoke testing for prefill/update/close/restart behavior.

## 6. Scope

### In Scope

- Confirm product value and UX for fixed 1-5 rating questions.
- Decide the SQL contract for `Rating` questions and rating answers.
- Define required versus optional rating semantics using the Phase 9A optional-question model.
- Define builder UX without free-typed question-type values.
- Define player UX for entering, reviewing, editing, clearing/skipping optional ratings, and
  submitting responses.
- Define PublicLive and HiddenUntilClose aggregate behavior for rating questions.
- Define private admin/leadership live status behavior for rating questions.
- Define private closed-only totals and response-detail export shape for rating values.
- Preserve formula safety and spreadsheet-safe Discord ID behavior.
- Define audit metadata without storing full answer payloads in audit JSON.
- Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
- Select tests, smoke plan, migration order, rollback posture, and deferred follow-up work.

### Out of Scope Unless Separately Approved

- Ranking questions.
- Custom rating scales, 1-10 scales, scale labels, emoji/icons, or rating comments.
- Persisted partial player response drafts or resume.
- Dashboard/reporting implementation.
- Cross-survey export/workbook redesign.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Renaming/removing `/vote_admin`.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text/optional survey behavior except as explicitly approved for rating
  compatibility.

## 7. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before coding. |
| `k98-discord-command-feature` | Required because builder/player/status/export UX uses Discord interactions, modals, buttons, selects, and private panels. |
| `k98-sql-validation` | Required for rating schema, constraints, indexes, migration order, DAL queries, and export assumptions. |
| `k98-test-selection` | Required to select focused service/DAL/view/export/scheduler/regression tests. |
| `k98-deferred-optimisation-capture` | Required to keep ranking, draft/resume, reporting, export, emoji/icon, policy, and template work visible. |
| `k98-pr-review` | Required before implementation handoff if a runtime slice is approved. |
| `k98-promotion-check` | Required before production promotion if implementation is approved. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff because ratings touch Discord interactions, permissions/privacy, user input, SQL persistence, result aggregation, generated exports, and restart-sensitive response flows. |

## 8. Architecture Direction To Confirm

- Preserve the separate SQL-backed survey model; do not fold surveys back into `VotePosts`.
- Add `QuestionType = Rating` through SQL and service validation, not a free-text builder value.
- Use a dedicated `dbo.SurveyRatingAnswers` table instead of overloading choice or text answer
  tables.
- Store one scalar rating value per response/question.
- Keep fixed 1-5 scale first unless the operator explicitly approves broader scale design.
- Reuse Phase 9A required/optional completion semantics.
- Keep all service validation authoritative; do not rely on Discord component limits alone.
- Keep public outputs aggregate-only: count, average, and distribution are allowed; per-user rating
  rows are private export only.
- Keep private response-detail exports admin/leadership-gated and closed-only.
- Keep audit JSON to operational metadata, not full answer payloads.
- Preserve no persisted partial player drafts unless a separate draft/resume slice is approved.

## 9. SQL Contract To Validate

Validate against `C:\K98-bot-SQL-Server` before implementation:

- Expand `CK_SurveyQuestions_Type` to allow `Rating`.
- Add dedicated `dbo.SurveyRatingAnswers` with a narrow contract, expected shape:
  - `SurveyRatingAnswerID bigint IDENTITY`
  - `SurveyResponseID bigint NOT NULL`
  - `SurveyID bigint NOT NULL`
  - `SurveyQuestionID bigint NOT NULL`
  - `DiscordUserID decimal(20,0) NOT NULL` or the existing Discord ID type used by survey tables
  - `RatingValue tinyint NOT NULL`
  - `CreatedAtUtc datetime2 NOT NULL`
  - `UpdatedAtUtc datetime2 NOT NULL`
- Add a check constraint for the approved scale, initially `RatingValue BETWEEN 1 AND 5`.
- Add foreign keys to survey response/question tables using existing cascade/delete posture.
- Add uniqueness so one response has at most one rating per rating question.
- Add export/status indexes by `SurveyID`, `SurveyQuestionID`, and response where justified.
- Confirm whether original answer metadata is service-derived during response replacement or needs
  extra storage.
- Confirm migration rollback posture before submitted rating rows exist.

## 10. UX Direction To Confirm

Builder:

- Add `Rating` to the existing question type selector only after SQL/runtime approval.
- Keep required as the default and reuse the Phase 9A required/optional toggle.
- For the first rating slice, avoid custom scale text fields.
- Make the rating prompt and required/optional state clear in the builder review.

Player response panel:

- Use Discord-native controls such as a select menu or compact buttons for ratings 1 through 5.
- Show required missing, answered, and optional skipped states consistently with Phase 9A.
- Keep Submit disabled only while required questions are missing.
- Allow optional ratings to be skipped/cleared.
- Preserve prefilled editing for submitted responses when response changes are allowed.
- After successful submit, preserve Phase 8/9A closeout behavior by clearing/closing private
  controls.

Public presentation:

- PublicLive may show rating answered count, average rating, and count distribution.
- HiddenUntilClose should hide rating aggregates while open and reveal aggregate-only results at
  close.
- Public outputs must not show per-user rating values.

## 11. Export And Audit Direction

Totals export:

- Preserve existing columns where possible.
- Add rating aggregate rows/fields for answered count, skipped count, average, minimum, maximum,
  and per-rating distribution where approved.
- Keep text/detail answers aggregate-only in totals export.

Response-detail export:

- Preserve one row per response/question.
- Include `QuestionType = Rating`, `IsRequired`, `AnswerStatus`, and `RatingValue`.
- If response changes are enabled and original-answer reporting is already available for that
  export path, include `OriginalRatingValue` and `RatingChanged` using the established change
  semantics.
- Represent skipped optional ratings distinctly from blank strings.
- Keep `DiscordUserID` spreadsheet-safe and all user-controlled strings formula-safe.

Audit:

- Submission/change audit may record required count, optional answered count, optional skipped
  count, rating answer count, and changed flag.
- Export audit may record column profile, row count, byte count, oversized status, and delivery
  status.
- Do not store full answer payloads in audit JSON.

## 12. Test Strategy

Expected focused coverage:

- `tests/test_survey_service.py`: rating validation, invalid/stale payloads, required rating
  enforcement, optional rating skip/clear, response changes allowed/blocked, and existing
  choice/text optional regressions.
- `tests/test_survey_dal.py`: rating answer persistence, replacement semantics, snapshot loading,
  export row mapping, and transaction rollback behavior.
- `tests/test_survey_post_view.py`: builder rating controls, player rating entry/edit/prefill,
  submit gating, optional clear/skip, timeout/stale behavior, and owner-only panels.
- `tests/test_survey_export_service.py`: rating totals, response-detail rating columns,
  formula safety, spreadsheet-safe Discord IDs, closed-only enforcement, and oversized audit
  metadata.
- Survey presentation/render tests for PublicLive and HiddenUntilClose rating aggregates.
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

1. Create a required rating survey and submit a rating.
2. Create a mixed required/optional survey with choice, text, and rating questions.
3. Confirm Submit is blocked when a required rating is missing.
4. Confirm Submit succeeds when an optional rating is skipped and all required questions are
   answered.
5. Reopen a submitted response and confirm the rating is prefilled.
6. Change a rating when response changes are allowed; confirm the update is recorded.
7. Attempt a change when response changes are blocked; confirm rejection.
8. Confirm PublicLive shows aggregate rating counts/average/distribution only.
9. Confirm HiddenUntilClose hides open aggregates and reveals aggregate-only rating results at
   close.
10. Confirm private admin status shows rating answered/skipped counts.
11. Close manually and by scheduler; confirm disabled controls and restart-safe survey opener
    behavior.
12. Export totals and response detail privately; confirm rating values, skipped optional ratings,
    spreadsheet-safe Discord IDs, formula safety, and closed-only enforcement.
13. Regression smoke an existing required choice/text/details survey and a skipped optional
    Phase 9A survey.

## 14. Deferred Follow-Up Work

Keep these separate unless explicitly approved:

- Phase 9C Ranking Survey Questions: dedicated ranking table, duplicate-rank prevention, clear
  Discord entry/edit UX, conservative public aggregate semantics, and private response-detail
  export shape.
- Survey Draft/Resume: SQL-backed partial drafts, resume after timeout/restart, cleanup/expiry,
  privacy approval, and export exclusion for unsubmitted drafts.
- Survey Export v2 / Reporting Readiness: cross-survey exports, workbook outputs, private
  reporting views/procedures, retention/redaction policy, and dashboard/reporting decisions.
- Emoji/Icon Support: option metadata, Discord button/select rendering, export representation, and
  generated-card glyph QA.
- Voting Identity/Policy Work: role-restricted voting, governor-linked voting/reporting, saved
  templates, public detail exports, and `/vote_admin` command reshaping.

## 15. Approval Needed

Before implementation, confirm:

- Whether to approve fixed 1-5 rating questions as the Phase 9B implementation slice.
- Whether optional ratings should use the Phase 9A skip/clear semantics.
- Whether public rating aggregates should include count, average, min/max, and distribution.
- Whether response-detail export should include `RatingValue`, `OriginalRatingValue`, and
  `RatingChanged`.
- Whether ranking should remain Phase 9C after rating is delivered and smoke tested.

## 16. Phase 9B Local Implementation Record - 2026-07-04

Phase 9B was approved after the audit/scope packet and implemented locally as the fixed 1-5 rating
slice only.

Delivered local scope:

- Added `QuestionType = Rating` as a first-class survey question type.
- Prepared additive SQL migration `20260704_002_add_survey_rating_questions.sql` in the SQL repo.
- Added dedicated `dbo.SurveyRatingAnswers` storage with fixed 1-5 rating constraint, response
  linkage, one rating per response/question, and rating-question FK enforcement.
- Preserved Phase 9A required/optional semantics for rating questions.
- Added private player rating controls with prefilled editing and optional skip/clear behavior.
- Added guided builder `Rating` selection without free-typed question type values.
- Added PublicLive and HiddenUntilClose aggregate-only rating behavior using answered count,
  average, min/max, and 1-5 distribution.
- Added private admin status rating summaries.
- Added private closed-only totals and response-detail export fields for rating values,
  original rating values, changed flags, skipped optional ratings, formula safety, and
  spreadsheet-safe Discord IDs.
- Extended submission/change audit metadata with rating counts without storing full answer
  payloads in audit JSON.
- Preserved existing one-choice votes, multi-select votes, choice/text surveys, optional questions,
  details, reminders, automatic/manual close, restart-safe public openers, and private exports.

Still out of scope:

- Ranking questions.
- Custom scales, 1-10 scales, scale labels, emoji/icons, rating comments.
- Persisted partial drafts/resume.
- Dashboard/reporting, export v2/workbook redesign, role/governor voting, saved templates,
  public detail exports, and `/vote_admin` reshaping.

Local validation:

- Focused survey/voting pytest passed: `69 passed`.

Pending before production rollout:

- SQL deployment from `C:\K98-bot-SQL-Server`.
- Full bot validation gates and Codex Security review before PR handoff.
- Operator Discord smoke covering rating create, submit, update, optional skip, PublicLive,
  HiddenUntilClose close reveal, status, exports, manual/automatic close, restart-safe opener, and
  existing choice/text optional regressions.
