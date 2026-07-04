# Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design`
- Date: `2026-07-04`
- Owner/context: `Follow-up after successful Phase 8 survey text/details delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | privacy/export review`
- One-pass approved: `no`
- Status: `prepared; audit/scope only until approved`

## 2. Objective

Audit and design the next approved survey slice: optional survey questions plus rating/ranking
question types.

Phase 8 delivered required free-text questions and optional choice-question details. Phase 9 should
decide the safest next implementation shape for advanced survey question types, including
completion semantics, SQL storage, validation, privacy, PublicLive/HiddenUntilClose behavior,
private exports, tests, smoke plan, migration order, rollback posture, and deferred follow-up work.

Do not implement SQL migrations, runtime optional/rating/ranking storage, response UI, export shape
changes, dashboard/reporting implementation, or command changes until the Phase 9 architecture,
product scope, privacy, SQL, permissions, and UX direction are approved.

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
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`

## 4. Delivered Baseline

Phase 1 through Phase 8 are complete and smoke tested. The voting framework supports SQL-backed
vote posts, one-choice voting, single-question multi-select voting, SQL-backed choice/text
multi-question surveys, one ballot/response per Discord user, response changes when enabled,
scheduler reminders, automatic close, manual close, disabled controls after close, restart-safe
public controls, guided vote/survey creation, PublicLive and HiddenUntilClose result visibility,
private admin live totals, private totals/voter-audit/survey-detail CSV exports, required
free-text survey questions, one optional details capture per choice question, formula-safe
text/detail export cells, aggregate text-question totals rows, and no public raw text/detail
exposure.

## 5. Source Deferred Item

This task promotes the active advanced survey question-types deferred item into an audit/design
slice.

### Deferred Optimisation
- Area: `voting/`, future survey question model, survey builder, survey exports
- Type: architecture
- Description: Optional survey questions and rating/ranking question types remain intentionally outside Phase 8; they require changes to `SurveyQuestions.IsRequired`, missing-answer validation, response completion semantics, public count/card behavior, private export shape, and SQL constraints.
- Suggested Fix: Decide optional-answer semantics, rating/ranking storage, validation limits, export columns for missing/rated/ranked answers, PublicLive/HiddenUntilClose aggregate behavior, builder controls, and smoke tests before any implementation.
- Impact: high
- Risk: high
- Dependencies: Phase 8 text/details delivered and smoke tested; SQL repo validation; privacy/export approval for non-choice answers; regression tests for required choice/text surveys.

## 6. Scope

### In Scope

- Produce an advanced survey question-types decision matrix.
- Decide whether optional questions, rating questions, and ranking questions should ship together
  or as separate implementation slices.
- Define optional-question completion semantics:
  - what counts as survey complete
  - how missing optional answers appear in review/status/export
  - how submit gating changes when required and optional questions are mixed
  - how response changes handle newly answered or cleared optional answers
- Define rating-question semantics:
  - supported scale shapes and limits
  - required versus optional behavior
  - aggregate public summaries
  - private response-detail columns
- Define ranking-question semantics:
  - rank cardinality and duplicate prevention
  - whether ranking uses existing options or a separate item model
  - aggregate public summaries
  - private response-detail columns
- Define admin builder UX without free-typed question-type values.
- Define player response UX for entering, reviewing, editing, and submitting advanced answers.
- Define PublicLive and HiddenUntilClose behavior for optional/rating/ranking questions.
- Define private admin/leadership status and export behavior.
- Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
- Update deferred optimisation status so draft/resume, emoji/icon, richer exports, reporting,
  templates, role/gov voting, and public detail export work remain visible.

### Out of Scope

- Runtime implementation before architecture approval.
- SQL migrations before approval.
- Persisted partial player response drafts or resume.
- Dashboard/reporting implementation.
- Cross-survey export/workbook redesign.
- Per-option emoji/icon support.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Renaming/removing `/vote_admin`.
- Changing existing one-choice vote behavior.
- Changing existing multi-select vote behavior.
- Changing existing choice/text survey behavior except where explicitly approved for advanced
  question-type compatibility.

## 7. Codex Skills To Use

| Skill | Use |
|---|---|
| `k98-architecture-scope` | Required for product/architecture boundary decisions before coding. |
| `k98-discord-command-feature` | Required because builder/player/status/export UX uses Discord interactions, modals, buttons, and private panels. |
| `k98-sql-validation` | Required for all SQL-facing schema, constraint, index, export, and migration assumptions. |
| `k98-test-selection` | Required to select focused service/DAL/view/export/scheduler/regression tests. |
| `k98-deferred-optimisation-capture` | Required to update active deferred items and keep later survey/reporting/export work visible. |
| `k98-pr-review` | Required before implementation handoff if a runtime slice is approved later. |
| `k98-promotion-check` | Required before production promotion if a runtime slice is approved later. |
| `codex-security:security-diff-scan` | Required before runtime PR handoff because advanced answers touch permissions/privacy, user input, SQL persistence, generated exports, and restart-sensitive response flows. |

## 8. Mandatory Audit Workflow

1. Read the required documents and Phase 8 archived task pack.
2. Audit current survey service, DAL, models, builder/view, presentation/rendering, scheduler,
   export, and command tests.
3. Validate current survey SQL schema and constraints against `C:\K98-bot-SQL-Server`.
4. Produce a decision matrix for these candidate shapes:
   - optional questions only
   - rating questions only
   - ranking questions only
   - optional + rating first
   - optional + rating + ranking together
5. For each candidate, confirm product value, privacy, permissions, SQL contract, command/builder
   UX, player UX, public result behavior, private status/export behavior, tests, smoke plan,
   migration order, rollback posture, and regression risk.
6. Identify the safest first implementation slice.
7. Split remaining approved work into future task-pack outlines or structured deferred items.
8. Stop after the audit/scope packet for approval.

## 9. Architecture Direction To Validate

- Preserve the separate SQL-backed survey model; do not fold surveys back into `VotePosts`.
- Prefer additive question-type metadata and answer tables over overloading choice/text answer
  rows.
- Keep all service validation authoritative; do not rely on Discord UI limits alone.
- Keep public outputs aggregate-only. Never render raw free text or detail notes publicly.
- Keep private response-detail exports admin/leadership-gated and closed-only.
- Keep audit JSON to operational metadata, not full answer payloads.
- Preserve no persisted partial player drafts unless a separate draft/resume slice is approved.

## 10. SQL Questions To Answer

- Should optionality reuse `SurveyQuestions.IsRequired`, and does the current constraint/default
  support optional choice and text questions safely?
- Do rating answers need a dedicated table, a typed scalar-answer table, or an extension of
  `SurveyTextAnswers`?
- Do ranking answers need a dedicated ranked-item table keyed by option and rank?
- What check constraints prevent rating/ranking data on incompatible question types?
- What indexes support closed-only response-detail export without creating dashboard/reporting
  scope?
- How are original answers represented for response changes?
- What migration order preserves Phase 7 and Phase 8 behavior during rollout?
- What rollback posture is acceptable if advanced answer tables contain user-submitted data?

## 11. UX Questions To Answer

- How does the builder select `Choice`, `Text`, `Rating`, or `Ranking` without free-typed values?
- How does the builder mark a question optional while keeping defaults required?
- How does the player panel communicate "answered", "optional and skipped", and "required missing"?
- Should submit stay disabled until all required questions are complete while optional questions
  remain skippable?
- How are rating scales displayed in Discord components without exceeding option limits?
- How are rankings entered and reviewed without a confusing multi-step flow?
- How are advanced answers prefilled when a player reopens a submitted response?

## 12. Export And Privacy Requirements

- Totals exports should remain aggregate and must not expose raw text/detail data.
- Response-detail exports must represent missing optional answers distinctly from blank strings.
- Rating/ranking export cells must be formula-safe where user-controlled labels can appear.
- Discord user IDs must remain spreadsheet-safe text.
- Export audit should include requester, export mode, row count, byte count, column profile,
  oversized flag, delivery status, and no full answer payloads.
- Public voter-level/detail posting remains out of scope.

## 13. Test Strategy To Define

Select tests after audit, but expect focused coverage around:

- `tests/test_survey_service.py`: optional completion rules, rating/ranking validation, stale
  payloads, response changes, closed rejection, and required-answer enforcement.
- `tests/test_survey_dal.py`: transactional advanced answer persistence, replacement semantics,
  original-answer metadata, and export row mapping.
- `tests/test_survey_post_view.py`: builder controls, player entry/edit/prefill, submit gating,
  timeout/stale behavior, and owner-only panels.
- `tests/test_survey_export_service.py`: aggregate rows, response-detail advanced columns,
  formula safety, closed-only enforcement, and oversized audit metadata.
- Survey presentation/render tests for PublicLive and HiddenUntilClose aggregate behavior.
- `tests/test_vote_admin_cmds.py` and command registration validation if command wiring changes.

Baseline audit/docs validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 14. Manual Smoke Plan To Define

The audit packet should define a smoke plan that covers:

1. Existing choice-only and text/detail survey regression.
2. Optional unanswered question submit behavior.
3. Rating submit/update/export behavior.
4. Ranking submit/update/export behavior.
5. PublicLive aggregate behavior.
6. HiddenUntilClose open/close behavior.
7. Private admin status behavior.
8. Private closed-only exports with spreadsheet-safe IDs and formula safety.
9. Manual close, automatic close, reminders, and restart-safe survey opener behavior.

## 15. Future Task-Pack / Deferred Outlines

Keep these as separate unless the audit explicitly promotes one:

- Survey Draft/Resume: SQL-backed partial drafts, resume after timeout/restart, cleanup/expiry,
  privacy approval, and export exclusion for unsubmitted drafts.
- Survey Export v2 / Reporting Readiness: cross-survey exports, workbook outputs, private
  reporting views/procedures, retention/redaction policy, and dashboard/reporting decisions.
- Emoji/Icon Support: option metadata, Discord button/select rendering, export representation, and
  generated-card glyph QA.
- Voting Identity/Policy Work: role-restricted voting, governor-linked voting/reporting, saved
  templates, public detail exports, and `/vote_admin` command reshaping.

## 16. Audit / Scope Packet - Drafted 2026-07-04

### Scope Summary

Phase 9 should not ship optional questions, rating questions, and ranking questions in one runtime
slice. The safest first implementation slice is:

1. Phase 9A: optional questions for the existing delivered survey question types only
   (`SingleChoice`, `MultiSelect`, and `Text`).
2. Later slice: rating questions, after optional completion/export semantics are stable.
3. Later slice: ranking questions, after rating and optional behavior are proven, because ranking
   has the highest Discord UX and aggregation complexity.

This preserves Phase 1 through Phase 8 behavior by keeping every current survey question required
by default and treating optionality as an explicit builder choice. Existing one-choice votes,
single-question multi-select votes, required choice surveys, required text surveys, Add details,
reminders, close behavior, restart-safe public openers, and private exports should remain
compatible.

### Current Contract Confirmed

- Runtime survey ownership is already in target layers:
  - commands: `commands/vote_admin_cmds.py`
  - views/modals: `ui/views/survey_post_view.py`
  - service: `voting/survey_service.py`
  - DAL: `voting/survey_dal.py`
  - presentation/rendering: `voting/survey_presentation.py` and `voting/survey_render_service.py`
  - exports: `voting/survey_export_service.py`
- Current runtime question types are `SingleChoice`, `MultiSelect`, and `Text`.
- `SurveyQuestionCreateRequest` and `SurveyQuestion` do not yet carry `is_required` in the Python
  model even though SQL has `SurveyQuestions.IsRequired`.
- `voting/survey_dal.py` currently inserts `IsRequired = 1` for all questions.
- `voting/survey_service.validate_response_payload()` currently requires every choice question to
  meet `MinSelections` and every text question to have non-empty text.
- The private response panel currently disables Submit until all questions validate.
- The public survey card currently says all questions are required.
- Existing text/detail answers are not persisted until Submit; no partial response drafts survive
  timeout or restart.
- Response-detail export already emits one row per response/question, which gives Phase 9A a good
  base for representing skipped optional answers without introducing public detail exposure.

### SQL Validation Summary

Validated against `C:\K98-bot-SQL-Server`:

- `migrations/20260702_003_add_survey_post_framework.sql` creates:
  - `dbo.SurveyPosts`
  - `dbo.SurveyQuestions`
  - `dbo.SurveyQuestionOptions`
  - `dbo.SurveyResponses`
  - `dbo.SurveyAnswers`
  - `dbo.SurveyReminders`
  - `dbo.SurveyAudit`
- `SurveyQuestions.IsRequired bit NOT NULL` exists with default `1`.
- `CK_SurveyQuestions_Required` currently enforces `[IsRequired] = 1`; optional questions require
  a SQL migration before bot code can persist them.
- `migrations/20260703_001_add_survey_text_details.sql` adds:
  - `SurveyQuestions.AllowDetails`
  - `QuestionType = Text`
  - `dbo.SurveyTextAnswers`
  - `dbo.SurveyAnswerDetails`
- `CK_SurveyQuestions_Type` currently allows only `SingleChoice`, `MultiSelect`, and `Text`.
- No `SurveyRatingAnswers`, `SurveyRankingAnswers`, rating question metadata, ranking question
  metadata, or SQL schema object files for survey tables were found in `sql_schema/` during this
  audit. The active survey contract is migration-defined.

### Decision Matrix

| Candidate | Product value | Permission / privacy model | SQL contract needs | Builder / command UX | Player view UX | Public result behavior | Private status / export | Tests and smoke | Migration / rollback | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| Optional questions only | High. Lets admins ask useful context questions without blocking the whole response. Unlocks better mixed surveys using existing choice/text/detail types. | Same as Phase 8. Admin/leadership commands and exports stay private. Player panel remains owner-only. Raw text/details remain private/export-only. | Drop/recreate `CK_SurveyQuestions_Required` to allow `0` or `1`; keep default `1`. Add Python `is_required` model/request fields and DAL read/write. No new answer table required. | Add a required/optional toggle in the guided builder, default required. No new slash command or free-typed type value. | Submit is enabled when all required questions are answered. Optional questions can be skipped or cleared. Panel must distinguish `required missing`, `answered`, and `optional skipped`. | PublicLive may show aggregate counts and answered/skipped counts, never raw text/details. HiddenUntilClose hides open aggregates and still never reveals raw text/details. | Status should show answered/skipped per question. Totals export should include answered/skipped counts. Response-detail export should represent missing optional answers distinctly from empty strings. | Focused service/DAL/view/export/presentation tests plus smoke for optional unanswered submit and required-regression behavior. | SQL first, bot second. Bot rollback ignores optional-capable SQL. SQL rollback requires no `IsRequired = 0` rows or a manual conversion to required. | Recommended first slice. It is the smallest semantic unlock and preserves existing default behavior. |
| Rating questions only | Medium-high. Useful for quick sentiment, satisfaction, priority, and readiness scoring. | Aggregate ratings can be public; per-user ratings stay private response detail only. No raw text exposure beyond existing text/detail rules. | Add `QuestionType = Rating`, rating scale metadata, and preferably `dbo.SurveyRatingAnswers` keyed to response/user/question. Optional semantics still need `IsRequired` handling for mixed surveys. | Add `Rating` to question type selector and scale controls. Avoid free-typed scale definitions in the first rating slice. | Private rating selector, prefilled on reopen. Required rating blocks Submit unless answered; optional rating can be skipped after Phase 9A. | PublicLive can show count, average, and distribution; HiddenUntilClose hides while open and reveals aggregate at close. | Response-detail export adds rating value/original rating/changed status. Totals export adds rating aggregate rows. | Needs service validation, DAL transaction, export shape, presentation aggregate, and smoke for submit/update/export. | Additive but broader than optional because it changes type constraints, answer tables, aggregations, exports, and UI. | Defer until optional semantics are approved and stable. Required-only rating is possible but less useful and still broad. |
| Ranking questions only | Medium. Useful for priority ordering and preference ranking, but harder to explain and operate in Discord. | Per-user ranking order is sensitive detail and should stay private export only. Public output must be aggregate only. | Add `QuestionType = Ranking`, use existing `SurveyQuestionOptions` as rankable items, and add `dbo.SurveyRankingAnswers` keyed to option/rank. Need uniqueness constraints for one rank per item and one item per rank. | Add `Ranking` type plus rank-cardinality controls. Builder must make item count and rank count clear. | Discord has no native drag/drop ranking; likely requires staged rank selects or one modal/select per rank. Prefill/edit/clear behavior is more complex. | PublicLive should show aggregate top-ranked counts or average rank; HiddenUntilClose hides open aggregates. | Response-detail export needs ordered rank representation, original ranks, changed flag, and missing optional representation. | Highest view/service/export matrix; smoke must cover duplicate rank prevention, partial rankings, update, export, and close/restart regression. | Additive SQL, but rollback after submitted ranking data is manual. UI rollback risk is higher because partial private-panel state is more complex. | Defer. Do not combine with optional or rating first. |
| Optional + rating first | High. Delivers skippable context plus common numeric scoring in one programme step. | Same privacy model as optional-only plus private per-user rating detail. | Requires optional SQL change plus `Rating` type/table/metadata. | Adds both required toggle and rating scale controls. | Adds skip/clear semantics and rating entry in one UI pass. | Adds answered/skipped counts and rating aggregates. | Adds optional missing markers and rating columns/rows. | Broad but coherent if operator wants one larger PR. | SQL rollback more involved because both optional and rating data may exist. | Viable second choice, but not the safest first slice. Use only if operator prefers one broader implementation. |
| Optional + rating + ranking together | Very high feature coverage, but too much risk for one PR-sized slice. | Combines every advanced privacy/export/aggregation rule at once. | Requires optional constraint change plus rating and ranking answer tables, metadata, constraints, and export mappings. | Builder and player panel become much more complex at once. | Submit gating, skip/clear, rating, ranking, prefill, and stale behavior all change together. | Multiple aggregate types need cards/status/export at the same time. | Response-detail export shape changes substantially. | Requires broad focused tests plus likely full pytest and longer Discord smoke. | Rollback after production data is manual and high-risk. | Reject for Phase 9 implementation. |

### Recommended Phase 9A Implementation Scope

Implement optional questions only for existing survey types:

- Add `is_required` to survey models and create requests, defaulting to `True`.
- Persist `SurveyQuestions.IsRequired` from the builder instead of hardcoding `1`.
- Keep SQL default `DF_SurveyQuestions_IsRequired = 1`.
- Replace `CK_SurveyQuestions_Required` with a constraint that allows `IsRequired IN (0, 1)`.
- Preserve current `MinSelections` and `MaxSelections`; for optional choice questions, an absent
  answer is allowed, but if answered the existing min/max rules apply.
- For optional text questions, absent or whitespace-only text means skipped; if provided, it is
  trimmed and length-validated.
- For optional choice questions with `AllowDetails`, detail notes remain allowed only for selected
  options. Skipping or clearing the answer clears detail notes for that question on submit.
- Submit remains disabled until all required questions are complete. Optional questions do not
  block Submit.
- Response changes keep the existing survey-level `AllowResponseChange` rule. When changes are
  allowed, players can add, edit, skip, or clear optional answers before close.
- No persisted partial drafts. Optional answers in the private panel remain non-durable until
  Submit.

### Rating Direction For Later Approval

Recommended first rating slice after Phase 9A:

- Add `QuestionType = Rating`.
- Start with a fixed 1-5 scale to avoid a large builder-scale design. Custom scale labels and
  1-10 scales can be deferred unless operator value justifies the extra controls.
- Add dedicated `dbo.SurveyRatingAnswers` rather than overloading `SurveyAnswers` or
  `SurveyTextAnswers`.
- Store one `RatingValue tinyint` per response/question, with a SQL check constrained to the
  question scale.
- Public aggregates: answered count, average rating, and count distribution. HiddenUntilClose
  hides open aggregates and reveals them at close.
- Private response-detail export: `RatingValue`, `OriginalRatingValue`, `RatingChanged`, and
  `AnswerStatus`.
- Audit JSON records counts and changed status only, not per-user answer payloads.

### Ranking Direction For Later Approval

Recommended ranking slice after rating:

- Add `QuestionType = Ranking`.
- Reuse `dbo.SurveyQuestionOptions` as the rankable item list.
- Add dedicated `dbo.SurveyRankingAnswers` with one row per ranked option and rank value.
- Use uniqueness constraints to prevent duplicate option ranks and duplicate rank positions within
  one response/question.
- Use `MinSelections` and `MaxSelections` as ranking cardinality only after the service and SQL
  naming are reviewed for clarity.
- Player UX should use explicit rank controls with review/prefill, not a fragile free-text ranking
  string.
- Public aggregates should start with conservative summaries such as first-place counts and
  average rank. Richer ranked-choice methods are reporting scope, not first-slice runtime scope.

### Permission And Privacy Model

- Keep `/vote_admin survey_create`, `survey_status`, `survey_close`, and `survey_export` under the
  existing admin/leadership permission decorators.
- Keep player entry as public `Answer survey` plus private owner-only response panel.
- Keep private status ephemeral and admin/leadership-only.
- Keep response-detail export private, closed-only, and admin/leadership-only.
- PublicLive and HiddenUntilClose may expose only aggregate counts/summaries. They must not expose
  raw text, detail notes, or per-user rating/ranking rows.
- Discord user IDs remain spreadsheet-safe text in exports.
- Formula-safety remains required for all user-controlled export cells, including option labels,
  text, detail notes, Discord names, and future ranking labels.

### SQL / Persistence Direction

Phase 9A migration order:

1. SQL repo migration: drop/recreate `CK_SurveyQuestions_Required` so `IsRequired` can be `0` or
   `1`; keep the default at `1`; do not add rating/ranking tables in this slice.
2. Bot DAL/model rollout: read/write `IsRequired`.
3. Service rollout: optional completion validation and answer clearing semantics.
4. View/export/presentation rollout: builder toggle, skip/clear UX, answered/skipped aggregates,
   and missing optional export markers.

Rollback posture:

- Bot rollback is compatible with optional-capable SQL because existing bot code only creates
  required questions.
- SQL rollback is manual if optional surveys have been created. Either convert optional questions
  to required after operator approval or preserve the relaxed constraint.
- No destructive data removal should be part of the first optional migration.

Rating/ranking migration order, when separately approved:

1. Expand `CK_SurveyQuestions_Type`.
2. Add type-specific metadata columns or tables.
3. Add dedicated answer tables and constraints.
4. Add export indexes only for closed response-detail/export queries.
5. Roll out bot/DAL/service/view/export support after SQL is deployed.

### UX Direction

Builder:

- Extend the current question type selector rather than adding command options or free-typed
  question-type values.
- Add a required/optional toggle with required as the default.
- For Phase 9A, keep `Choice` and `Text` as the only selectable question types.
- Do not add `Rating` or `Ranking` builder options until their SQL/runtime slices are approved.

Player response panel:

- Show each question state as one of `required missing`, `answered`, or `optional skipped`.
- Keep Submit disabled only while required questions are missing.
- Add a clear/skip control for optional questions, because Discord selects cannot always represent
  an empty selection cleanly once a value is chosen.
- Preserve prefilled editing for submitted responses.
- After successful submit, keep the Phase 8 behavior of closing/clearing private response controls.

Public presentation:

- Replace copy that assumes all questions are required.
- For optional questions, show aggregate `answered` counts and optionally `skipped` counts.
- For text/detail questions, continue showing counts only, never raw values.

### Export Shape Direction

Totals export:

- Preserve existing columns where possible.
- Add optional-aware aggregate fields in a compatible way, such as `AnsweredResponses` and
  `SkippedResponses`, or document a row-level representation that does not break existing rows.
- Existing text-question count rows remain aggregate only.

Response-detail export:

- Preserve one row per response/question.
- Add `IsRequired` and `AnswerStatus` (`Answered`, `SkippedOptional`, `MissingRequired` only if
  historical/invalid data is encountered).
- Represent skipped optional answers distinctly from empty text strings.
- Keep `DiscordUserID` spreadsheet-safe and all user-controlled strings formula-safe.

Audit:

- Submission/change audit may record required count, optional answered count, optional skipped
  count, text answer count, detail note count, and changed flag.
- Export audit may record column profile, row count, byte count, oversized status, and delivery
  status.
- Do not store full answer payloads in audit JSON.

### Test Strategy

Phase 9A implementation should add/update:

- `tests/test_survey_service.py`: optional choice/text validation, required regression, skip/clear
  behavior, details cleared when optional choice is skipped, response changes allowed/blocked, and
  closed/stale rejection.
- `tests/test_survey_dal.py`: `IsRequired` row mapping, create persistence, transactional submit,
  optional answer deletion/replacement semantics, and original-answer metadata.
- `tests/test_survey_post_view.py`: builder required toggle, player state copy, skip/clear
  controls, submit gating, prefill, owner-only panel behavior, and timeout/stale paths.
- `tests/test_survey_export_service.py`: missing optional representation, aggregate answered/skipped
  counts, formula safety, spreadsheet-safe Discord IDs, closed-only enforcement, and oversized
  audit metadata.
- Survey presentation/render tests: PublicLive and HiddenUntilClose aggregate behavior with mixed
  required/optional surveys and no raw text/detail leaks.
- `tests/test_vote_admin_cmds.py` and command registration validation only if command wiring or
  slash options change; the preferred Phase 9A design should not add a new command.

Recommended validation for audit/docs only:

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

### Manual Smoke Plan

Phase 9A optional-question smoke:

1. Create an existing required choice/text/details survey and confirm Phase 7/8 regression safety.
2. Create a mixed survey with one required question and one optional choice question.
3. Submit with the optional question skipped; confirm Submit is allowed.
4. Reopen and add the optional answer; confirm prefill and update behavior.
5. Clear the optional answer; confirm any details for that question are removed.
6. Create a survey with an optional text question; submit skipped and then submit answered.
7. Confirm PublicLive shows only aggregate counts and no raw text/details.
8. Confirm HiddenUntilClose hides open aggregates and still never exposes raw text/details at close.
9. Confirm private status shows answered/skipped counts.
10. Close manually and by scheduler; confirm reminders and restart-safe opener behavior.
11. Export totals and response detail privately; confirm missing optional answers are distinct,
    Discord IDs are spreadsheet-safe, and formula safety still applies.

Later rating smoke:

1. Create a rating survey.
2. Submit/update ratings, including optional skipped ratings if Phase 9A is delivered.
3. Confirm PublicLive/HiddenUntilClose aggregate behavior.
4. Confirm private response-detail export includes rating values and change flags.

Later ranking smoke:

1. Create a ranking survey.
2. Submit valid rankings and reject duplicates/missing required ranks.
3. Reopen, prefill, and update rankings.
4. Confirm public aggregate behavior and private export representation.

### Refactor Triggers And Deferred Decisions

- Direct SQL is present in `voting/survey_dal.py`, which is the correct DAL layer for this
  subsystem. No new command/view SQL should be added.
- Business logic currently belongs mostly in `voting/survey_service.py`; Phase 9A should keep
  optional semantics there and avoid moving completion rules into the Discord view.
- The current renderer/card copy assumes required questions. This is in scope for Phase 9A because
  optional questions make that copy incorrect.
- Persisted partial response drafts remain out of scope and should stay deferred.
- Rating and ranking remain designed but deferred after the optional-first recommendation.
- Emoji/icon support, richer exports/reporting, dashboard/reporting, role/governor voting, saved
  templates, public detail exports, and `/vote_admin` reshaping remain separate deferred work.

### Approval Needed

Before implementation, confirm:

- Whether to approve Phase 9A optional questions only as the first implementation slice.
- Whether optional questions should apply to both choice and text questions in Phase 9A.
- Whether response-detail export should add `IsRequired` and `AnswerStatus` columns as proposed.
- Whether totals export should add answered/skipped counts in Phase 9A.
- Whether rating should be the next slice after optional questions, with fixed 1-5 scale first.
