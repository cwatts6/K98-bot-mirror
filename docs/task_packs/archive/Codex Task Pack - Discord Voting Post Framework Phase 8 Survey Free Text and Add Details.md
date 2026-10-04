# Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 8 Survey Free Text and Add Details`
- Date: `2026-07-03`
- Owner/context: `Follow-up after successful Phase 7 choice-only survey delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey extension design | Discord interaction UX | privacy/export review | implementation`
- One-pass approved: `no`
- Status: `delivered; SQL deployed; operator smoke tested; archived`

## 2. Objective

Audit, design, and deliver the approved second survey slice: free-text survey questions and
optional choice-question `Add details` text.

Phase 7 delivered choice-only multi-question surveys. Phase 8 should extend that model carefully
for text-bearing responses, including privacy, SQL shape, UI, exports, and moderation/retention
considerations. Runtime implementation was intentionally blocked until the architecture, product
scope, privacy, SQL, permissions, and UX direction were approved. Operator approval was recorded
on 2026-07-03, after the audit/scope packet was prepared.

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
- `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` before production promotion.
- SQL repo `C:\K98-bot-SQL-Server` before recommending any answer table, column, index,
  migration, view, stored procedure, constraint, or audit shape.

## 4. Delivered Baseline

Phase 1 through Phase 7 are complete and smoke tested.

The voting framework now supports:

- SQL-backed one-choice votes.
- SQL-backed single-question multi-select votes.
- SQL-backed choice-only multi-question surveys under `/vote_admin survey_*`.
- Guided admin survey builder with question/option modals, min/max dropdowns, visible limits, and
  graceful timeout for unpublished drafts.
- Persistent public `Answer survey` buttons.
- Private paged survey response panels.
- Submitted-answer prefill and response-change allowed/blocked behavior.
- PublicLive and HiddenUntilClose survey aggregate visibility.
- Manual and automatic survey close.
- Private admin/leadership live survey status.
- Private closed-only survey totals and response-detail CSV exports.
- Restart-safe public survey opener behavior.

Phase 7 smoke testing confirmed:

- Survey creation works for single-choice and multi-select questions.
- Response submission and response update work.
- PublicLive and HiddenUntilClose survey results work as required.
- Manual and automatic close work.
- Builder UX polish is acceptable after button/label/limit/timeout refinements.
- Unpublished survey drafts intentionally do not survive bot restart.

## 5. Source Deferred Items

This task promotes the active survey text/details deferred item into the next prepared voting
slice.

### Deferred Optimisation
- Area: `voting/`, future survey question model, survey exports
- Type: architecture
- Description: Free-text and other non-choice survey question types were intentionally excluded from the first choice-only survey slice. Operator follow-up confirmed the second survey slice should add free-text questions and optional choice-question `Add details` text, and that submitted text/detail data must be included in private admin/leadership exports. Text responses increase privacy, moderation, CSV formula-safety, retention, and export risks beyond choice-only aggregate voting.
- Suggested Fix: Define free-text questions, per-choice `Add details` text, SQL storage shape, retention/redaction rules, private export columns containing submitted text/detail data, formula-safety handling, private admin/leadership detail access matching current vote results visibility, and public aggregate behavior before any SQL or runtime implementation.
- Impact: high
- Risk: high
- Dependencies: Phase 7 choice-only survey model delivered and smoke tested; Codex Security review before runtime PR handoff; SQL schema design for type-specific answers and per-choice detail notes; export regression tests.

## 6. Scope

### In Scope

- Confirm the exact product value for:
  - full free-text questions
  - optional `Add details` text attached to a selected choice
- Decide whether Phase 8 should include both text features in one implementation slice or split
  them into smaller sub-slices.
- Define text answer limits, validation copy, empty/whitespace handling, editing rules, and
  response-change behavior.
- Define whether `Add details` is globally enabled per survey, per question, or per option.
- Define the player UX for entering text in Discord without making the flow frustrating.
- Define admin builder UX changes for adding a free-text question or enabling details on a choice
  question.
- Define PublicLive and HiddenUntilClose behavior for text-bearing surveys.
- Define private admin/leadership live status behavior for text-bearing surveys.
- Define summary and response-detail export changes, including formula-safety and text inclusion.
- Define audit metadata for text/detail response submission, change, export, and oversized export
  handling without storing full text payloads in audit JSON.
- Validate SQL options against `C:\K98-bot-SQL-Server`.
- Preserve Phase 1 through Phase 7 behavior.
- Update deferred optimisation status so draft/resume, optional questions, rating questions,
  emoji/icon, dashboard/reporting, and richer exports remain tracked.

### Out of Scope

- Implementing survey free-text or `Add details` runtime behavior before approval.
- SQL migrations before approval.
- Persisted partial player response drafts.
- Admin draft persistence across bot restart.
- Optional survey questions.
- Rating/ranking questions.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level/detail export posting.
- Dashboard/reporting implementation.
- Cross-survey exports or workbook-style export redesign.
- Per-option emoji/icon support.
- Renaming/removing `/vote_admin`.
- Changing existing one-choice, single-question multi-select, or choice-only survey behavior.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required for survey extension boundaries, command/view placement, persistence, privacy, and tests. |
| `k98-discord-command-feature` | use | Text/details affect slash command builder UX, modals, private response panels, and stale/timeout behavior. |
| `k98-sql-validation` | use | Required before recommending answer columns/tables, constraints, indexes, migrations, or reporting views. |
| `k98-test-selection` | use | Required to select focused survey service/DAL/view/export/scheduler/regression tests. |
| `k98-deferred-optimisation-capture` | use | Required to update active deferred items and keep later survey/reporting/export work visible. |
| `k98-pr-review` | use | Use before handoff to check docs, SQL direction, test plan, and privacy boundaries. |
| `k98-promotion-check` | conditional | Use before production promotion if docs or runtime branches are promoted. |
| `codex-security:security-diff-scan` | conditional | Required before runtime implementation because text responses touch privacy, user input, SQL persistence, exports, and Discord interactions. Usually skipped for audit-only docs with explicit justification. |

## 8. Mandatory Workflow

1. Audit the delivered Phase 7 survey model and SQL contract.
2. Validate SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
3. Compare text/detail storage options:
   - add nullable text columns to `dbo.SurveyAnswers`
   - add a normalized text answer table
   - add a separate detail-note table keyed to response/question/option
   - use a single answer-value table with typed answer kinds
4. Compare Discord UX options for text entry:
   - modal per free-text question
   - modal opened from a question page
   - details modal attached to a selected option
   - separate review/edit page
5. Produce a decision matrix covering product value, privacy, permissions, SQL, UX, exports,
   tests, smoke plan, rollout risk, and rollback posture.
6. Recommend the safest first implementation slice.
7. Split larger text/detail/reporting/export work into future task-pack outlines or structured
   deferred items.
8. Stop for operator approval before implementation.

## 9. Architecture Direction To Validate

Initial preferred direction, subject to audit:

- Keep surveys as separate `dbo.Survey*` SQL objects.
- Preserve `dbo.SurveyAnswers` for choice selections.
- Add text/detail persistence additively rather than overloading option IDs.
- Keep response submit/change service-owned and transactional.
- Keep Discord views focused on interaction flow; services validate text limits and answer rules.
- Keep public posts aggregate-only. Never render raw text answers publicly.
- Keep response-detail export private/admin-leadership only.
- Keep text/detail audit JSON to operational metadata, not full answer payloads.

## 10. SQL Questions To Answer

- Should free-text answers live in `dbo.SurveyAnswers`, a new `dbo.SurveyTextAnswers`, or a more
  general typed answer table?
- Should `Add details` text attach to:
  - a response/question pair
  - a response/question/option selection
  - the whole response envelope
- What max length should SQL enforce for text answers and detail notes?
- Should text/detail values have created/updated timestamps separate from the response envelope?
- How should deleted/replaced text be handled when response changes are enabled?
- What indexes are needed for detail export without creating dashboard/reporting scope?
- What constraints prevent text answers on choice-only questions or details on unselected options?
- What migration rollback posture is acceptable for additive text tables/columns?

## 11. UX Questions To Answer

- How does an admin add a free-text question in the current guided builder without reintroducing
  brittle free-typed question-type input?
- Does `Add details` appear as a per-question toggle, per-option toggle, or always-available
  optional text after selecting choices?
- Should players enter text immediately on the question page, through a modal, or through an
  explicit `Add details` button?
- How is existing text/detail prefilled when a player reopens a submitted response?
- What happens when response changes are disabled?
- How does a timed-out private response panel behave if text has been entered but not submitted?
- What copy makes text length limits clear without turning the panel into instructions?

## 12. Export And Privacy Requirements

- Summary exports should remain aggregate and should not include raw text answers unless a
  separate text-summary design is approved.
- Response-detail exports must include submitted free-text answers and `Add details` notes.
- Text values must be CSV formula-safe.
- Discord user ID must remain spreadsheet-safe text.
- Discord names may be resolved at export time as in current voter/detail exports.
- Governor identity remains excluded unless a later governor-linked voting task is reopened.
- Export audit should include requester, export mode, row count, byte count, column profile,
  oversized flag, and delivery status, but not full text/detail payloads.
- Oversized exports must fail privately with operator guidance.

## 13. Test Strategy To Define

Likely focused tests:

- `tests/test_survey_service.py`: free-text validation, detail-note validation, response change,
  closed rejection, required-answer enforcement, stale/invalid text payloads.
- `tests/test_survey_dal.py`: transactional text/detail persistence, replacement semantics,
  export row mapping, constraints, and missing/stale SQL state.
- `tests/test_survey_post_view.py`: builder controls, text/detail modal flow, owner-only private
  panel behavior, prefill, timeout, and closed/stale rejection.
- `tests/test_survey_export_service.py`: response-detail text columns, formula safety, Discord ID
  text handling, closed-only enforcement, oversized handling, audit metadata.
- `tests/test_survey_presentation.py` or current presentation tests: PublicLive/HiddenUntilClose
  leak prevention for text-bearing surveys.
- `tests/test_vote_admin_cmds.py`: command handoff, option ordering, permission/defer behavior,
  and canonical command registration if command surfaces change.

Regression tests to keep running:

- Existing survey service/view/export/scheduler tests.
- Existing one-choice and multi-select vote tests.
- Command registration validation.
- Full pytest before runtime PR handoff if implementation touches shared survey services,
  scheduler, exports, or command registration.

Baseline validation for this audit/docs slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 14. Manual Smoke Plan To Define

At minimum, the eventual implementation smoke plan should cover:

1. Create a choice-only survey to prove Phase 7 regression safety.
2. Create a survey with one free-text question.
3. Create a survey with one choice question that allows optional details.
4. Submit a complete response with text/details.
5. Reopen and confirm text/details prefill.
6. Change text/details when response changes are enabled.
7. Confirm changes are blocked when disabled.
8. Confirm HiddenUntilClose does not expose text/detail data publicly while open.
9. Close manually and by scheduler.
10. Export response detail privately and confirm text/details are included and formula-safe.
11. Confirm summary export stays aggregate unless explicitly changed.
12. Confirm existing one-choice vote, multi-select vote, and choice-only survey behavior remains
    compatible.

## 15. Acceptance Criteria

- [ ] Phase 7 survey SQL and runtime contracts are audited.
- [ ] Survey text/detail candidate shapes are compared in a decision matrix.
- [ ] The safest first text/detail implementation slice is recommended with rationale.
- [ ] SQL contract options, constraints, indexes, migration order, and rollback posture are
      documented.
- [ ] Permission/privacy and result-visibility behavior is documented.
- [ ] Builder/player view UX is documented.
- [ ] Export and audit implications are documented, including private text/detail export.
- [ ] Automated tests and manual smoke plan are documented.
- [ ] Deferred optimisation backlog is updated so no draft/resume, optional question, emoji,
      reporting, or export work is lost.
- [ ] Audit-only constraint is satisfied before implementation approval.
- [ ] Required docs validators pass.

## 16. PR Summary Template

```md
## Summary

- Audited free-text survey questions and optional choice-question Add details after Phase 7.
- Recommended the safest first text/detail implementation slice.
- Updated deferred voting backlog and preserved later survey/reporting/export work.

## Tests

- <commands run>

## Risk / Rollback

- Risk: documentation/scope only unless implementation is separately approved.
- Rollback: revert docs/backlog/task-pack changes.
```

## 17. Audit / Scope Packet - Drafted 2026-07-03

### Scope Summary

Phase 8 should extend the delivered Phase 7 survey model with text-bearing submitted answers while
preserving the existing choice-only survey behavior. The audit recommends a split implementation:

1. Recommended first implementation slice: add required free-text survey questions plus optional
   per-choice selected-option details for choice questions.
2. Later slices: persisted draft/resume, optional questions, rating/ranking questions, richer
   export/reporting surfaces, emoji/icon support, and dashboard/reporting readiness.

The first slice should not change existing one-choice votes, single-question multi-select votes,
choice-only survey creation, existing choice-only response submission, survey reminders/closes,
PublicLive/HiddenUntilClose aggregate behavior, or existing export modes except for adding approved
text/detail columns to private response-detail export rows.

### Current Phase 7 Contract Confirmed

- Bot code stores survey definitions and answers in `voting/survey_*`, `ui/views/survey_post_view.py`,
  and `/vote_admin survey_*` in `commands/vote_admin_cmds.py`.
- `SurveyQuestions.QuestionType` currently supports only `SingleChoice` and `MultiSelect`.
- `SurveyQuestionOptions` is required for all current questions.
- `SurveyResponses` enforces one response envelope per survey/Discord user.
- `SurveyAnswers` stores normalized selected option IDs keyed by survey, response, Discord user,
  question, and option.
- `SurveyResponses.OriginalAnswersJson` currently stores original option ID lists for response
  change comparison.
- Public survey cards and embeds show aggregate option counts only; response-detail export is
  private and closed-only.
- SQL source-of-truth validation found the Phase 7 survey objects in
  `C:\K98-bot-SQL-Server\migrations\20260702_003_add_survey_post_framework.sql`. No separate
  `sql_schema` survey object files were found in the SQL repo during this audit.

### Decision Matrix

| Candidate | Product value | Privacy / permissions | SQL contract | Player UX | Builder UX | Export impact | Tests / smoke | Rollback posture | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Free-text questions only | High for open feedback, explanations, nominations, and availability notes. | Raw text is sensitive; never public. Admin/leadership private status may show counts only; closed response-detail export includes text. | Add `Text` question type plus a dedicated `dbo.SurveyTextAnswers` table keyed to `ResponseID`, `SurveyID`, `DiscordUserID`, and `SurveyQuestionID`. Keep `dbo.SurveyAnswers` choice-only. | Modal per text question from the private response panel, with prefilled value on reopen. Required non-whitespace answer. | Add an explicit question-type control, not free-typed type input. Text questions do not need options or min/max. | Add `TextAnswer` and original/current text change metadata to response-detail export only. Summary export remains aggregate and excludes raw text. | Service validation, DAL transaction, view modal, export formula safety, PublicLive/HiddenUntilClose leak prevention, manual smoke. | Additive SQL table and `QuestionType` constraint expansion; rollback can drop the new table/constraint if no runtime code depends on it. | Good, but less useful alone than pairing with details after the same privacy/storage work. |
| Choice-question `Add details` only | Medium-high for explaining selected choices without changing survey question types. | Raw details are sensitive; details should attach only to selected options and stay private/export-only. | Add details enablement metadata to choice questions or options plus `dbo.SurveyAnswerDetails` keyed to selected answer identity. Keep `dbo.SurveyAnswers` as the selected-option authority. | Optional modal attached to selected choice or selected choices; prefilled on reopen; empty means no detail. | Per-question toggle is safest first; per-option enablement is more granular but harder to build and explain. | Add detail columns to response-detail export; summary export still excludes raw detail text. | Tests for detail allowed/blocked, details only on selected options, updates, CSV safety, and stale close rejection. | Additive metadata plus detail table; details can be ignored by old code if bot rollback happens before SQL rollback. | Valuable, but implementing it without free-text creates nearly the same storage/privacy work. |
| Free-text + per-question details in one slice | Highest near-term KD98 value: freeform answers and explanations for selected choices share modal, validation, export, privacy, and audit patterns. | Same admin/leadership model as current private status/export. No public raw text. No public detail export. No governor identity. Audit JSON stores metadata only. | Expand `SurveyQuestions.QuestionType` to include `Text`; add `AllowDetails` or `DetailsMode` on choice questions; add `dbo.SurveyTextAnswers`; add `dbo.SurveyAnswerDetails`; optionally add original text/detail JSON metadata without full payloads. | Private response panel pages show answer status. Text/details are edited through modals. Submit persists all answers transactionally. No persisted partial drafts. | Add a question type segmented/dropdown-like control and an `Allow details` toggle for choice questions. Save question validates mode-specific fields. | Response-detail export includes text/detail columns and formula-safes every text cell; totals export remains aggregate. | Broad but coherent: service, DAL, view, export, presentation leak prevention, command registration, smoke for choice-only regression and text/detail flows. | Additive SQL first, bot second. Bot rollback can ignore new columns/tables; SQL rollback is manual only if data removal is accepted. | Recommended safest first implementation slice, with per-question details not per-option details. |
| Per-option details | Fine-grained control, but less important than the first text slice. | Slightly easier to avoid irrelevant details, but users/admins must understand which options allow notes. | Requires per-option metadata and constraints around selected option detail rows. | More UI branching and more edge cases when a user changes selected options. | Admin must configure details per option, increasing builder complexity. | Same response-detail export impact, with extra option-level metadata columns. | More matrix coverage across selected/unselected/removed options. | Additive but higher migration/UI risk. | Defer until the per-question details model has production evidence. |
| Whole-response details | Low clarity; becomes a generic comment box detached from a specific question/choice. | Higher accidental disclosure/confusion risk because exported notes are not anchored to a selected option. | Simpler table, but weaker relational integrity. | Easy to enter, harder to review against choices. | Survey-level toggle is simple. | Export consumers must infer what the comment explains. | Lower implementation cost but weaker product fit. | Additive. | Do not use for Phase 8. |
| Single generic typed answer table | Flexible for future ratings/rankings, but broadens the model before those types are approved. | One table can mix sensitive answer types and becomes a reporting magnet. | Replaces/duplicates choice answer semantics and risks disturbing Phase 7 aggregation. | No direct UX benefit. | No direct builder benefit. | Requires wider export remapping. | High regression risk around existing choice-only surveys. | Harder to rollback because it touches the core answer model. | Defer; not the safest first slice. |
| Nullable text columns on `SurveyAnswers` | Quick for selected-choice details, poor fit for text questions with no option. | Couples raw text to aggregate choice rows. | Pollutes choice-selection table and cannot represent a text question cleanly without fake options. | No UX benefit. | No UX benefit. | Export mapping becomes ambiguous. | Risks choice-only regressions. | Column rollback is additive but semantically messy. | Reject. |

### Recommended First Implementation Slice

Implement required free-text survey questions and optional per-question `Add details` for choice
questions together, after approval.

Recommended product rules:

- Free-text questions are required in Phase 8 because all Phase 7 survey questions are required.
- Optional questions remain out of scope.
- Text answers and detail notes are trimmed; empty or whitespace-only text is invalid for
  required free-text answers and treated as absent for optional details.
- Recommended first limits: 500 characters for free-text answers and 300 characters for per-choice
  detail notes. These fit comfortably inside Discord modal inputs and private review copy while
  keeping exports manageable.
- Add details is enabled per choice question, not per survey and not per option, for the first
  implementation slice.
- Details are tied to selected option rows. If a user changes a selection and removes an option,
  detail text for the removed option is deleted on submit.
- No partial player drafts are persisted. Text entered into a modal but not submitted with the
  final response is intentionally lost on panel timeout/restart.
- Response changes follow the existing survey-level `AllowResponseChange` flag. If changes are
  disabled, existing submitted text/details cannot be edited through the player flow.

### Architecture Direction

- Models: add a `Text` question type and explicit text/detail fields to survey request/answer DTOs.
- DAL: keep `dbo.SurveyAnswers` as the normalized choice-selection table. Add dedicated text/detail
  persistence and query helpers; submit/update remains one service-owned transaction.
- Service: validate question type, mode-specific required fields, text/detail limits, empty rules,
  response-change rules, close/stale rules, and export/audit metadata. Services should not depend
  on Discord objects.
- Commands: keep `/vote_admin survey_create`, `/vote_admin survey_status`, `/vote_admin survey_close`,
  and `/vote_admin survey_export`. No new top-level command.
- Views: keep the public persistent `Answer survey` opener. Private response panels own modals and
  routing only; service owns validation and persistence.
- Presentation: public cards/embeds never render raw text/detail data. Text questions may show
  response counts only if needed; choice aggregates keep existing PublicLive/HiddenUntilClose rules.
- Exports: only private closed response-detail export gains raw text/detail columns. Totals export
  remains aggregate and includes count-only rows for text questions.
- Audit: record action type, question counts, text-answer count, detail-note count, changed flag,
  row/byte counts, column profile, oversized status, and delivery status. Do not store full
  submitted text/detail payloads in audit JSON.

### SQL / Persistence Direction

Subject to approval, the additive SQL shape should be:

- Expand `CK_SurveyQuestions_Type` to allow `Text`.
- Add nullable/defaulted choice-detail enablement metadata on `dbo.SurveyQuestions`, such as
  `AllowDetails bit NOT NULL DEFAULT 0`, constrained so `Text` questions cannot allow details.
- Add `dbo.SurveyTextAnswers` with:
  - `SurveyID bigint NOT NULL`
  - `ResponseID bigint NOT NULL`
  - `DiscordUserID bigint NOT NULL`
  - `SurveyQuestionID bigint NOT NULL`
  - `AnswerText nvarchar(500) NOT NULL`
  - `CreatedAtUtc datetime2(0) NOT NULL`
  - `UpdatedAtUtc datetime2(0) NOT NULL`
  - primary key on `(SurveyID, DiscordUserID, SurveyQuestionID)`
  - FK to `SurveyResponses(ResponseID, SurveyID, DiscordUserID)`
  - FK to `SurveyQuestions(SurveyID, SurveyQuestionID)`
- Add `dbo.SurveyAnswerDetails` with:
  - `SurveyID bigint NOT NULL`
  - `ResponseID bigint NOT NULL`
  - `DiscordUserID bigint NOT NULL`
  - `SurveyQuestionID bigint NOT NULL`
  - `SurveyOptionID bigint NOT NULL`
  - `DetailText nvarchar(300) NOT NULL`
  - `CreatedAtUtc datetime2(0) NOT NULL`
  - `UpdatedAtUtc datetime2(0) NOT NULL`
  - primary key on `(SurveyID, DiscordUserID, SurveyQuestionID, SurveyOptionID)`
  - FK to `SurveyAnswers(SurveyID, DiscordUserID, SurveyQuestionID, SurveyOptionID)` so details
    cannot exist for unselected options
  - FK to `SurveyResponses(ResponseID, SurveyID, DiscordUserID)`
- Add export-oriented indexes only where the response-detail query needs them; avoid reporting
  views/procedures in Phase 8.
- Add a new SQL migration before bot rollout. Rollback is manual because text/detail tables can
  contain user-submitted data; bot rollback should remain compatible by ignoring new objects.

### Permission And Privacy Model

- Admin/leadership permissions remain command-level through existing `/vote_admin` decorators.
- Player entry remains public post button plus private response panel.
- PublicLive shows only choice aggregates and response counts. It never shows raw free-text answers
  or detail notes while open.
- HiddenUntilClose hides choice aggregates while open as today and still never reveals raw text
  publicly at close.
- `/vote_admin survey_status` remains private. It should show counts/totals for text-bearing
  questions, not raw text payloads.
- `/vote_admin survey_export mode:response_detail` remains private, closed-only, and
  admin/leadership-gated; it is the approved surface for raw submitted text/detail data.
- Public voter-level/detail posting remains out of scope.

### UX Direction

Builder:

- Add a question type selector/control with `Choice` and `Text`; do not reintroduce free-typed
  question-type values.
- For choice questions, preserve the current prompt/options/min/max builder flow and add an
  `Allow details` toggle.
- For text questions, hide option and min/max controls, show the text-answer limit, and save once
  the prompt is valid.
- Keep unpublished survey builder drafts in memory only. Timeout behavior remains graceful and
  unpublished drafts do not survive restart.

Player:

- Keep one private paged response panel.
- Choice questions keep dropdown selection; if details are enabled, the question gets one
  `Add details` / `Edit details` modal path for the overall question response.
- Text questions use a modal launched from the question page, with current text prefilled when
  reopening a submitted response.
- The review panel should indicate whether the current question has a saved text/detail value
  without printing long raw text into the panel.
- Submit persists the complete response. Unsaved modal/panel state is not durable until submit.

### Export Shape Direction

Totals export:

- Preserve current aggregate columns and exclude raw text/detail values.
- Text questions emit aggregate count-only rows so all-text surveys still show question metadata
  and response counts without exposing raw submitted text.

Response-detail export:

- Preserve `DiscordUserID` as spreadsheet-safe text and continue resolving `DiscordName`.
- Add columns such as `TextAnswer`, `OriginalTextAnswer`, `TextAnswerChanged`,
  `SelectedOptionDetailNotes`, and/or detail-per-option rows. Exact column layout should be
  finalized during implementation, but every raw text/detail cell must use the existing
  formula-safety helper.
- Keep closed-only enforcement and oversized-private-failure behavior.
- Include export audit metadata with the updated column profile, row count, byte count, oversized
  flag, delivery status, and no raw text payload.

### Test Strategy

Implementation should add or update:

- `tests/test_survey_service.py`: text/detail validation, required free-text enforcement,
  whitespace rules, response-change allowed/blocked behavior, closed rejection, invalid question
  type rules.
- `tests/test_survey_dal.py` or equivalent DAL contract tests: transactional create/submit/update,
  delete/replacement semantics, details only for selected options, export row mapping, original
  answer metadata.
- `tests/test_survey_post_view.py`: builder type controls, details toggle, text modal/detail modal,
  owner-only private panel, prefill, timeout/stale behavior.
- `tests/test_survey_export_service.py`: response-detail text/detail columns, formula safety,
  spreadsheet-safe Discord IDs, oversized audit metadata, closed-only enforcement.
- Survey presentation/render tests: text/detail leak prevention for PublicLive and
  HiddenUntilClose.
- `tests/test_vote_admin_cmds.py` and command registration validation if command option ordering or
  subcommand wiring changes.
- Existing vote and survey regression tests, including one-choice, single-question multi-select,
  choice-only surveys, scheduler close/reminders, and rehydration.

Required validation before runtime PR handoff:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_survey_service.py tests\test_survey_post_view.py tests\test_survey_export_service.py tests\test_voting_scheduler.py tests\test_vote_admin_cmds.py
```

Run full pytest before production promotion if runtime implementation touches shared survey DAL,
service, views, scheduler, exports, or command wiring.

### Manual Smoke Plan

1. Create an existing choice-only survey and submit/update a response to confirm Phase 7 regression
   safety.
2. Create a survey with at least one free-text question.
3. Create a survey with a choice question that enables details.
4. Submit a response with choice selections, free text, and details.
5. Reopen and confirm selected options, text, and details prefill.
6. Change text/details when response changes are enabled.
7. Confirm changes are blocked when response changes are disabled.
8. Confirm PublicLive never exposes raw text/details publicly.
9. Confirm HiddenUntilClose hides aggregates while open and still never exposes raw text/details at
   close.
10. Close manually and by scheduler.
11. Export response detail privately and confirm text/details are present, formula-safe, and
    Discord IDs remain spreadsheet-safe.
12. Confirm totals export remains aggregate, includes text-question count rows, and existing vote
    exports remain unchanged.

### Future Task-Pack / Deferred Outlines

- Survey Draft/Resume: SQL-backed partial drafts, resume after timeout/restart, cleanup/expiry,
  privacy approval, and export exclusion for unsubmitted drafts.
- Survey Optional Questions: allow optional questions after required text/detail behavior is stable;
  revisit `SurveyQuestions.IsRequired` constraints, validation copy, missing-answer export shape,
  and public count semantics.
- Survey Rating/Ranking Questions: separate question types with dedicated validation/storage and
  no overloading of choice/text tables.
- Survey Export v2 / Reporting Readiness: cross-survey exports, workbook outputs, private reporting
  views/procedures, retention/redaction policy, and dashboard/reporting decisions.
- Emoji/Icon Support: option metadata, Discord button/select rendering, export representation, and
  generated-card glyph QA.

### Approval And Delivery Status

Approved and delivered first implementation slice:

- Combined first slice: required free-text questions plus per-choice-question optional details.
- Per-question details rather than per-survey or per-option enablement.
- Text/detail limits of 500 and 300 characters.
- Dedicated `SurveyTextAnswers` and `SurveyAnswerDetails` SQL tables.
- Private/export-only raw text visibility.
- No persisted partial player drafts.
- Totals export remains aggregate and includes text-question count rows; response-detail export
  receives raw text/detail columns.

Remaining outside this slice:

- Persisted partial player drafts/resume.
- Optional survey questions.
- Rating/ranking questions.
- Per-option emoji/icon support.
- Survey Export v2, dashboard, and reporting implementation.
