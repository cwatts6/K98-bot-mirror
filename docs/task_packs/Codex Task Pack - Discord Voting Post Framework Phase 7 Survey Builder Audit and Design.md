# Codex Task Pack - Discord Voting Post Framework Phase 7 Survey Builder Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 7 Survey Builder Audit and Design`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 6 single-question MultiSelect delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey design | Discord interaction UX | privacy review | approved first-slice implementation`
- One-pass approved: `no`
- Status: `audit approved; choice-only first implementation slice in progress`

## 2. Objective

Audit and design the next advanced voting slice: multi-question survey-style voting.

Phase 6 delivered the safest cardinality change first: single-question `MultiSelect` voting under
the existing `/vote_admin` workflow. Phase 7 should decide whether and how to add a broader survey
builder without disturbing the now-smoke-tested vote-post framework.

The audit/scope pass was completed first. The operator then approved the safest first
implementation slice: choice-only multi-question surveys. Free-text questions and choice-question
`Add details` are confirmed as the next phase, and submitted text/detail data must be included in
private admin/leadership exports when that phase is implemented.

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

Conditionally read:

- `docs/reference/Promotion Guide.md` before production promotion.
- SQL repo `C:\K98-bot-SQL-Server` before recommending any survey object, column, index,
  migration, stored procedure, view, constraint, or audit event shape.

## 4. Delivered Baseline

Phase 1 through Phase 6 are complete and smoke tested.

The voting framework now supports:

- SQL-backed vote posts, options, votes, reminders, and audit rows.
- `OneChoice` votes as the default mode with one selected option per Discord user.
- `MultiSelect` votes with SQL-backed min/max selection rules and one ballot per Discord user.
- Vote changes before close when enabled, including multi-select selection-set replacement.
- Previously selected multi-select options displayed when reopening the private selector.
- Scheduler reminders and automatic close.
- Manual close.
- Disabled controls after close.
- Restart-safe open vote controls for one-choice buttons and multi-select opener buttons.
- Guided create option fields and guided close durations.
- Autocomplete vote lookup for status, update, close, and export.
- Guided update target selection.
- Vertical result bars with mode-aware outcome wording.
- Private totals-only CSV export for one closed vote at a time.
- Private voter-level audit CSV export for one closed vote at a time.
- Hidden-until-close result visibility with public close reveal.
- Private admin/leadership status with live totals.

Phase 6 smoke testing confirmed:

- Multi-select create/vote/update/close/status paths work.
- Vote changes allowed and blocked behavior works.
- Selection limits work.
- Restart-safe opener behavior works.
- Previously selected options display when reopening the selector and can be amended.
- One-choice regression behavior remains compatible.

Do not regress these behaviours.

## 5. Source Deferred Items

This task promotes the active full survey-builder deferred optimisation into an audit/design slice.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin`, future survey builder UI, SQL repo vote/survey framework
- Type: architecture
- Description: Full multi-question survey-style voting remains valuable for richer KD98 feedback, event planning, rankings, and structured questionnaires, but it is intentionally separate from the Phase 6 single-question MultiSelect implementation. It requires question modeling, per-question options, response envelopes, partial/private response UX, broader export design, and question-level privacy/reporting decisions that are not needed for single-question MultiSelect.
- Suggested Fix: Prepare a separate survey-builder audit/task pack. Define survey question types, create/edit builder UX, private response flow, partial submission/restart behavior, SQL tables for questions/options/responses/answers, PublicLive versus HiddenUntilClose summary rules, closed-only private export shapes, audit events, and migration/rollback order. Do not bundle survey builder with emoji/icon polish or dashboard/reporting implementation.
- Impact: high
- Risk: high
- Dependencies: Phase 6 MultiSelect production smoke evidence; SQL repo validation in `C:\K98-bot-SQL-Server`; privacy review for question-level responses; focused builder/response/export/restart tests.

Phase 7 should either resolve this item by producing an approved survey-builder implementation
scope, or refine it into smaller future slices if a full builder remains too large.

## 6. Scope

### In Scope

- Define the KD98 product value for multi-question surveys.
- Decide whether surveys belong under `/vote_admin`, a new subgroup, or a new approved command
  group.
- Define survey ownership and permissions: create/manage/close/export by admin/leadership, public
  response by eligible Discord users unless a later task explicitly approves restrictions.
- Define question types for the first implementation candidate.
- Define minimum viable survey shape:
  - title/description
  - multiple ordered questions
  - per-question options
  - one response envelope per Discord user
  - submitted/updated timestamps
  - close status and result visibility
- Define whether partial responses are allowed, saved, resumable, or rejected until complete.
- Define whether response changes are allowed before close and how existing answers are shown.
- Define PublicLive and HiddenUntilClose summary rules for survey results.
- Define closed outcome/summary rules where surveys do not have one winner.
- Define private response-panel UX, paging, confirmation, timeout, and restart behavior.
- Define closed-only private export shapes for summary and voter-audit/detail exports.
- Define audit event needs for create, update, response submit/change, close, and export.
- Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
- Propose SQL contract options, indexes, constraints, migration order, and rollback posture.
- Define automated tests and manual smoke plan.
- Update deferred optimisation status so survey, emoji/icon, reporting, and any new export/report
  work remain tracked.

### Out of Scope

- Implementing survey voting.
- SQL migrations or schema files.
- Per-option emoji/icon implementation.
- Dashboard/reporting implementation.
- Long-form public reporting pages.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote/survey templates.
- Public voter-level export posting.
- Renaming or removing `/vote_admin`.
- Changing existing one-choice vote button behavior.
- Changing existing multi-select opener/panel behavior.
- Changing existing totals-only or voter-audit export behavior for one-choice or multi-select.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required for affected layers, command shape, persistence, restart safety, and survey boundary decisions. |
| `k98-discord-command-feature` | use | Surveys affect slash command UX, guided builders, private response panels, interaction privacy, and response sequencing. |
| `k98-sql-validation` | use | Required before recommending survey tables, constraints, indexes, views, procedures, or audit contracts. |
| `k98-test-selection` | use | Required to define focused tests for a later implementation slice. |
| `k98-deferred-optimisation-capture` | use | Required to resolve/refine the survey deferred item and preserve reporting/emoji work. |
| `k98-pr-review` | use | Use before handoff if the audit edits docs/backlog/task packs. |
| `k98-promotion-check` | conditional | Use before production promotion if docs are pushed to production branches. |
| `codex-security:security-diff-scan` | conditional | Required before any runtime implementation touching Discord interactions, permissions/privacy, SQL/data access, exports, user input, or restart-sensitive persistence. Usually skipped for audit-only docs with explicit justification. |

## 8. Mandatory Workflow

1. Audit current Phase 1 through Phase 6 behavior and SQL contracts.
2. Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
3. Compare possible survey shapes:
   - simple single-page multi-question survey
   - paged private survey response flow
   - staged builder plus response confirmation
   - full builder with edit/resume support
4. Produce a decision matrix covering product value, privacy, permissions, SQL shape, UX, exports,
   tests, smoke plan, and rollout risk.
5. Recommend the first survey implementation slice.
6. Split larger survey/reporting/export work into future task-pack outlines or structured deferred
   items.
7. Update the deferred optimisation backlog.
8. Stop for operator approval before implementation.

## 8A. Phase 7 Audit Result

Audit date: `2026-07-02`

Verdict: implement surveys as a separate SQL-backed survey-post model under the existing
`/vote_admin` command group, not as another `VoteMode` bolted onto the current single-question
`VotePosts` option model.

Operator sequencing confirmed:

- First implementation step is multiple-choice only: `SingleChoice` and per-question
  `MultiSelect`.
- Second implementation slice should add free-text questions and optional choice-question
  `Add details` text.
- Free-text and `Add details` response data must be included in private admin/leadership exports
  when that second slice is implemented.
- Admin/leadership visibility should match the current vote results model: private live/admin
  visibility for authorized users, public aggregate output only where the result-visibility mode
  allows it, and no public voter-level/detail export.

Recommended first implementation slice: choice-only multi-question surveys with a staged guided
admin builder, a persistent public `Answer survey` entry button, a private paged player response
flow, all questions required, no persisted partial drafts, submitted-response prefill, optional
response changes before close, `PublicLive` and `HiddenUntilClose` aggregate visibility, manual and
scheduled close, and closed-only private summary/detail CSV exports.

Do not proceed to implementation until the operator approves this product, privacy, SQL,
permissions, and UX direction.

## 8B. Current Contract Audit

Current bot contract reviewed:

- `/vote_admin create`, `update`, `close`, `status`, and `export` live under
  `commands/vote_admin_cmds.py`.
- `VoteSnapshot` currently represents one public post with one ordered option set.
- `VotePostView` renders either one-choice option buttons or one multi-select opener button.
- Multi-select uses a private user-specific selector panel with existing-selection prefill.
- `voting/service.py` owns validation and orchestration; `voting/dal.py` owns SQL execution;
  `ui/views/vote_post_view.py` owns interaction routing.
- Existing exports are closed-only, private, and one vote at a time.
- Existing scheduler/rehydration behaviour depends on SQL-backed message IDs, close times,
  reminders, and stable persistent custom IDs.

Authoritative SQL checked in `C:\K98-bot-SQL-Server`:

- `migrations/20260701_002_add_vote_post_framework.sql` defines `dbo.VotePosts`,
  `dbo.VotePostOptions`, `dbo.VotePostVotes`, `dbo.VotePostReminders`, and `dbo.VotePostAudit`.
- `migrations/20260702_001_add_vote_post_result_visibility.sql` adds
  `VotePosts.ResultVisibility` constrained to `PublicLive` and `HiddenUntilClose`.
- `migrations/20260702_002_add_vote_post_multi_select.sql` adds `VotePosts.VoteMode`,
  `MinSelections`, `MaxSelections`, `dbo.VotePostMultiSelectVotes`, and
  `dbo.VotePostMultiSelectSelections`.
- Search found no existing authoritative survey tables, question tables, response envelopes,
  answer tables, survey stored procedures, or survey reporting views.

SQL implication: Phase 7 implementation needs a new additive SQL contract. It should not infer
survey objects from Python naming and should not overload `dbo.VotePostVotes.OptionID`,
`dbo.VotePostMultiSelectSelections`, or `VotePostOptions` with multi-question data.

## 8C. Survey Shape Decision Matrix

| Candidate shape | Product value | Permission/privacy model | SQL contract needs | Command/builder/view UX | Tests and smoke needs | Verdict |
|---|---|---|---|---|---|---|
| Extend `/vote_admin create` with more fields | Low to medium. It looks familiar, but Discord slash options are already dense and the current command is tuned for one question. | Admin/leadership would remain correct, but players would need a separate private flow anyway. Privacy rules become confusing if a `Survey` mode shares current vote exports/status. | Would require adding `Survey` to vote-mode checks or adding post kind branching to `VotePosts`; high risk of existing one-choice/multi-select code treating survey as multi-select. | Bad fit. Dynamic question counts cannot be expressed cleanly in slash-command options. | Heavy regression coverage across every existing vote path because the central command and mode normalization would change. | Reject for first slice. Too much regression risk and poor admin UX. |
| Simple single-page private survey panel | Medium. Useful for 2-3 small surveys. | Public post can stay simple; responses stay private. Without paging, Discord component limits cap usefulness. | Needs survey/question/option/response tables, but could avoid drafts. | One `Answer survey` button opens one private view with all selects. This breaks down on mobile and with more than a few questions. | View tests for component limits, privacy, stale panels, close rejection, exports, and hidden-results leak prevention. | Defer as too constrained. It is simpler but would likely be replaced quickly. |
| Linked survey object plus paged private response flow | High. Supports event planning, availability, preference ranking, and structured KD98 feedback without public noise. | Admin/leadership creates/manages/exports. Any Discord user can respond unless a later task adds restrictions. No public voter-level detail. HiddenUntilClose hides all public aggregates until close. | New additive survey tables for posts, questions, options, submitted response envelopes, and answer selections. Existing vote tables remain untouched except shared naming/docs if approved. | New `/vote_admin survey_create` launches a guided builder. Public survey post has persistent opener. Player flow is private, paged, confirm-before-submit, and prefilled from submitted answers when editing. | Focused service/DAL/view/export/scheduler tests plus one-choice and multi-select regression tests. Smoke covers create, answer, change allowed/blocked, restart, hidden close reveal, exports. | Recommended first implementation slice. Best balance of value and containment. |
| Staged builder with SQL draft persistence and response resume | High for long surveys and interrupted admin/player flows. | More durable, but draft responses may contain sensitive unsubmitted intent. Needs explicit retention and cleanup policy. | Adds draft status, partial answers, expiry/cleanup fields, and likely more indexes/procedures. | Admin and player flows survive restart mid-build/mid-response. More states, stale actions, and cleanup rules. | Adds draft lifecycle, expiry, resume, cleanup, and restart tests. | Defer. Useful later, but too many states for the first survey slice. |
| Full builder with free text, rating, optional questions, edit/resume, reporting | Very high long-term value. | Highest privacy risk, especially free text and detail exports. Needs retention, moderation, and operator-facing access rules. | Adds answer-value columns or type-specific answer tables, reporting views/procs, optional-answer semantics, and possibly full-text/export safeguards. | Rich builder and richer private response UI. More export/report variants. | Broad test and security surface: injection/formula safety, free-text privacy, report permissions, mobile UX, restart, migration. | Defer into future task packs. Too large and security-sensitive for first implementation. |

## 8D. Recommended First Survey Slice

Scope name: `Phase 8 - Choice-Only Survey Posts`.

Product scope:

- Survey title and optional description.
- Two to five ordered questions.
- Each question is `SingleChoice` or `MultiSelect`.
- Each question has two to six ordered options.
- All questions are required in the first slice.
- Per-question multi-select supports `MinSelections` and `MaxSelections` within that question.
- One submitted response envelope per Discord user per survey.
- Response changes are controlled by `AllowResponseChange` before close.
- No free-text, rating, optional questions, role restrictions, governor linking, templates,
  emoji/icon support, dashboards, or public voter-level exports.

Partial/resume/change rules:

- Do not persist partial player answers in the first slice.
- If a private response panel times out or the bot restarts before submit, the player reopens the
  public `Answer survey` button and starts again.
- A response is persisted only after the final confirmation step validates all required questions.
- Submitted responses can be reopened and prefilled from SQL while the survey is open.
- If response changes are disabled, a submitted response can be viewed privately but not replaced.
- If response changes are enabled, resubmission replaces the current answer set in one DAL
  transaction and records an audit event.

Result visibility:

- `PublicLive`: public open post may show aggregate response count and per-question aggregate
  selections/top selections. It never shows voter names or individual response rows.
- `HiddenUntilClose`: public open post shows survey metadata and close time but hides response
  count, per-question counts, percentages, and top selections. Private admin status may show live
  aggregates.
- On close, public reveal shows a compact per-question summary. Survey copy should avoid
  `winner`; use `Top selection(s)` or `No responses`.
- Closed survey exports remain private and one survey at a time.

Permissions and privacy:

- Create, status, close, update-like management if later approved, and export stay
  admin/leadership-gated under `/vote_admin`.
- Player response entry is public on the post, but the response flow and confirmation are private.
- Detail export includes Discord user ID and resolved Discord name only, matching Phase 4 privacy.
- No governor identity, role eligibility, or public detail posting in the first slice.
- When the second text/details slice is approved, private admin/leadership detail exports must
  include free-text answers and per-choice detail notes with CSV formula-safety handling.
- Export audit rows should log requester, mode, row count, byte count, columns, oversized flag, and
  delivery status, but not store voter lists or full answer payloads in audit JSON.

## 8E. SQL Contract Direction

Recommended SQL model: separate additive `dbo.Survey*` tables rather than adding `Survey` to
`VotePosts.VoteMode`.

Rationale:

- Current `VotePosts` and `VoteSnapshot` are single-question and option-set oriented.
- Existing code often treats any non-`OneChoice` vote mode as multi-select; adding `Survey` there
  would create regression traps.
- Separate survey tables isolate Phase 1 through Phase 6 behaviour and let survey aggregation,
  exports, and response privacy evolve without breaking one-choice or multi-select exports.

Proposed first-slice tables:

- `dbo.SurveyPosts`: survey shell with guild/channel/message IDs, creator, title, description,
  status, result visibility, response-change flag, mention flags, open/close timestamps, close
  metadata, created/updated timestamps.
- `dbo.SurveyQuestions`: ordered question definitions with prompt, question type, required flag,
  min/max selections, and timestamps.
- `dbo.SurveyQuestionOptions`: ordered choice options per question.
- `dbo.SurveyResponses`: one submitted response envelope per survey and Discord user, with
  created/submitted/updated timestamps and optional original-answer metadata if approved for audit.
- `dbo.SurveyResponseSelections`: normalized selected options keyed by survey, Discord user,
  question, and option.
- `dbo.SurveyReminders`: reminder offsets, due/claim/sent timestamps, and reminder message IDs.
- `dbo.SurveyAudit`: create/publish/update/response/close/export audit events with JSON metadata
  constrained by `ISJSON`.

Recommended constraints and indexes:

- `SurveyPosts.Status IN ('Open', 'Closed', 'Cancelled')`.
- `SurveyPosts.ResultVisibility IN ('PublicLive', 'HiddenUntilClose')`.
- `SurveyQuestions.QuestionType IN ('SingleChoice', 'MultiSelect')`.
- `SurveyQuestions.IsRequired = 1` for the first slice, enforced by service and optionally a check
  constraint until optional questions are approved.
- Unique question sort/key per survey.
- Unique option sort/key per question.
- Unique submitted response per `(SurveyID, DiscordUserID)`.
- Selection FKs must ensure selected options belong to the selected question/survey.
- Index open due closes by `(Status, ClosesAtUtc)` and reminder claims by `(SentAtUtc, DueAtUtc)`.
- Index response aggregation by `(SurveyID, QuestionID, OptionID)` or equivalent selection table
  key order.

Migration order:

1. Add survey shell, question, option, response, selection, reminder, and audit tables.
2. Add defaults, check constraints, FKs, and uniqueness constraints.
3. Add aggregation/lookup indexes.
4. Deploy bot code that can create and operate surveys.
5. Keep rollback as disabling survey command creation first, then leaving additive empty/compatible
   SQL objects in place unless a destructive cleanup is separately approved.

SQL objects explicitly not recommended for the first slice:

- Stored procedures or reporting views for dashboards.
- Free-text answer tables/columns.
- Per-choice `Add details` answer tables/columns.
- Governor-linked response columns.
- Role eligibility tables.
- Template tables.
- Public report/export tables.

## 8F. Command, Builder, And View UX Direction

Command placement:

- Keep the existing top-level `/vote_admin` group.
- Add survey-specific subcommands only after approval, starting with `/vote_admin survey_create`.
- Later implementation may add `/vote_admin survey_status`, `/vote_admin survey_close`, and
  `/vote_admin survey_export` if separate survey tables are approved. Do not overload existing
  vote autocomplete lists unless the implementation explicitly makes vote and survey lookup
  mode-aware.
- Any new subcommand must update `docs/reference/canonical_command_reference.md`,
  command-registration validation, and command inventory tests.

Admin builder:

- Slash command should collect only stable launch fields: title, target channel, close duration,
  result visibility, allow response changes, and mention/reminder policy.
- A private builder view should collect questions one at a time through modals/selects.
- Builder limits should be visible through enabled/disabled controls, not long instructional copy.
- Draft builder state can be in memory for the first slice because no public post or submitted
  data exists until `Publish`. If the builder times out or the bot restarts, the admin restarts the
  builder.
- SQL write should happen only at publish, in one service/DAL transaction.

Player response flow:

- Public post contains a persistent `Answer survey` button.
- Button opens a private paged response panel owned by that Discord user.
- Each page shows one question with a select control.
- Back/Next controls navigate pages; final page opens a review/submit step.
- Existing submitted answers are prefilled when the player reopens the panel.
- Unauthorized users cannot use another user's private panel.
- Closed, stale, deleted-message, and permission failure paths return private safe errors.

Public post/card:

- Keep public open survey posts compact on mobile.
- Use survey-specific wording: `Survey open`, `Responses`, `Questions`, `Closes`.
- Avoid a single overall winner. Closed survey summaries should present one compact row/section per
  question and label top selections per question.

## 8G. Export And Audit Direction

First-slice closed-only private exports:

- Summary export: one row per question option, including survey metadata, question ID/key/prompt,
  question type, option ID/key/label, response count, selection count, percent of submitted
  responses, top-selection flag, close metadata, message link, and reminder metadata.
- Detail/audit export: one row per respondent-question, with spreadsheet-safe Discord user ID,
  resolved Discord name, question ID/key/prompt, selected option IDs/keys/labels joined with
  semicolons, response created/submitted/updated timestamps, and response-changed flag.

Export rules:

- Only closed surveys can be exported.
- Delivery is ephemeral/private.
- Oversized exports are blocked from Discord upload with operator guidance.
- CSV formula-safety and spreadsheet-safe Discord ID handling must match existing vote exports.
- Existing one-choice and multi-select export headers and behavior remain unchanged.

Audit events:

- `SurveyCreated`
- `SurveyPublished`
- `SurveyResponseSubmitted`
- `SurveyResponseChanged`
- `SurveyClosedEarly`
- `SurveyClosedAutomatically`
- `SurveySummaryExported`
- `SurveyDetailExported`
- `SurveyMessageEditFailed`

Audit JSON should contain operational metadata, not full voter lists or full answer payloads.

## 8H. Test Strategy For Approved Implementation

New focused tests to add:

- `tests/test_survey_service.py`: builder validation, question/option limits, all-required
  enforcement, response change allowed/blocked, closed rejection, result visibility summary rules.
- `tests/test_survey_dal.py`: transactional publish, submitted response replacement, aggregation
  mapping, audit rows, missing/stale SQL state.
- `tests/test_survey_views.py`: public opener, private owner-only panel, paging, submit
  confirmation, existing-answer prefill, stale/closed rejection, timeout/reopen behavior.
- `tests/test_survey_export_service.py`: summary/detail CSV headers, formula safety, Discord ID
  text formatting, closed-only enforcement, oversized handling, export audit metadata.
- `tests/test_survey_discord_presentation.py`: PublicLive aggregate summary, HiddenUntilClose leak
  prevention, closed reveal wording, no overall-winner wording.
- `tests/test_survey_scheduler.py`: due reminders, due close, duplicate claim protection, manual
  and automatic close parity.
- `tests/test_vote_admin_cmds.py`: new survey command permission/defer/service handoff and
  command option ordering.

Regression tests to keep running:

- `tests/test_voting_service.py`
- `tests/test_voting_dal.py`
- `tests/test_vote_post_view.py`
- `tests/test_voting_export_service.py`
- `tests/test_voting_discord_presentation.py`
- `tests/test_voting_render_service.py`
- `tests/test_voting_scheduler.py`
- `tests/test_vote_admin_cmds.py`

Recommended validation commands for implementation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_survey_service.py tests\test_survey_dal.py tests\test_survey_views.py tests\test_survey_export_service.py tests\test_survey_discord_presentation.py tests\test_survey_scheduler.py tests\test_vote_admin_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_voting_service.py tests\test_voting_dal.py tests\test_vote_post_view.py tests\test_voting_export_service.py tests\test_voting_discord_presentation.py tests\test_voting_render_service.py tests\test_voting_scheduler.py
```

Run full pytest before PR handoff or production promotion if the implementation touches shared
presentation, scheduler, command registration, or SQL/DAL helpers broadly.

Codex Security review is required before runtime PR handoff because the implementation will touch
Discord interactions, permissions/privacy, user input, SQL-backed persistence, exports, and
restart-sensitive public buttons.

## 8I. Manual Smoke Plan For First Implementation Slice

1. Create and answer a default one-choice vote to prove Phase 1-5 regression safety.
2. Create and answer a multi-select vote to prove Phase 6 remains stable.
3. Create a choice-only survey with at least two questions, one single-choice and one multi-select.
4. Submit a complete response from one Discord user.
5. Submit a complete response from a second Discord user.
6. Reopen the survey as the first user and confirm existing answers are prefilled.
7. Change the response when changes are enabled.
8. Create a second survey with changes disabled and confirm repeat submission is blocked.
9. Restart the bot with an open survey and confirm the public `Answer survey` button still opens a
   private response flow.
10. Confirm `HiddenUntilClose` hides public response counts, question totals, percentages, and top
    selections while open.
11. Close manually and confirm public close reveal uses per-question `Top selection(s)` wording.
12. Let a survey close by scheduler and confirm controls disable and close announcement matches
    manual close behavior.
13. Export summary CSV privately for one closed survey.
14. Export detail/audit CSV privately for one closed survey.
15. Confirm no public voter-level detail is posted and existing one-choice/multi-select export
    behavior is unchanged.

## 8J. Future Task-Pack Outlines / Deferred Work

Future survey slices after the recommended first implementation:

- `Phase 9 - Survey Draft Resume And Optional Questions`: SQL-backed draft responses, partial
  resume, optional questions, expiry/cleanup policy, and admin/player restart recovery.
- `Phase 10 - Survey Advanced Question Types`: rating questions and free-text questions after a
  separate privacy and retention review. This slice is operator-confirmed to include both
  free-text questions and optional choice-question `Add details` text. Private admin/leadership
  exports must include the submitted text/detail data with formula safety, retention, moderation,
  and audit rules defined before implementation.
- `Phase 11 - Survey Reporting Readiness`: private SQL views/procedures for survey participation,
  aggregate results, export history, and trend reporting. Keep dashboards/public reporting out of
  scope until separately approved.
- `Survey Export v2`: richer workbook or multi-file exports, cross-survey export, and reporting
  consumer contracts after the first CSV shapes have production evidence.

Tracked out-of-scope voting slices preserved outside Phase 7:

- Per-option emoji/icon support remains a separate polish slice.
- Dashboard/reporting readiness remains a separate private reporting slice after survey SQL shape
  approval.
- Role-restricted voting, governor-linked voting, saved templates, and public voter-level export
  posting remain out of active scope unless the operator reopens them.

## 9. Design Questions To Answer

1. Is a survey still a vote post, or a separate survey object linked to a post?
2. Should `/vote_admin create` grow survey fields, or should surveys use a guided builder command?
3. What is the smallest useful first survey: fixed number of questions, question builder, or
   import-like text syntax?
4. Which question types are approved first: single choice, multi-select, free text, rating, or only
   choice-based questions?
5. How many questions and options should the first slice allow?
6. Can users submit partial responses?
7. Can users resume or change submitted responses before close?
8. How are existing answers shown privately when editing a response?
9. How does HiddenUntilClose apply across multiple questions?
10. What does a public open survey post show without becoming noisy?
11. What does a public close reveal show when there are many questions?
12. What should private admin status show for open surveys?
13. What should summary export contain?
14. What should voter-audit/detail export contain?
15. What SQL tables, columns, indexes, constraints, and audit events are needed?
16. What state must survive restart?
17. What is the migration and rollback path?
18. Which pieces should remain deferred?

## 10. Likely Files

### Review

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/export_service.py`
- `voting/discord_presentation.py`
- `voting/render_service.py`
- `voting/outcomes.py`
- `voting/scheduler.py`
- `voting/rehydration.py`
- `ui/views/vote_post_view.py`
- potential new survey service/DAL/view modules under `voting/` or `ui/views/`
- `tests/test_vote_admin_cmds.py`
- `tests/test_vote_post_view.py`
- `tests/test_voting_service.py`
- `tests/test_voting_dal.py`
- `tests/test_voting_export_service.py`
- `tests/test_voting_discord_presentation.py`
- `tests/test_voting_render_service.py`
- `tests/test_voting_scheduler.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- SQL repo `C:\K98-bot-SQL-Server`

### Modify In Audit Slice

- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/reference/deferred_optimisations.md`
- future task packs or starters created from the audit

### Modify Only In Later Implementation Slices

- Runtime Python under `commands/`, `voting/`, and `ui/views/`
- focused tests
- SQL repo migrations, schema files, constraints, indexes, stored procedures, or views

## 11. Architecture Requirements

- Preserve `OneChoice` and `MultiSelect` behavior exactly unless a later implementation task
  explicitly changes it.
- Keep SQL as the source of truth for survey definitions and submitted responses.
- Do not store response state only in Discord view instances.
- Keep commands thin; services/DAL own validation, survey state, response persistence,
  aggregation, and audit behavior.
- Keep views focused on interaction flow and private response sequencing.
- Do not add direct SQL to commands or views.
- Preserve private/ephemeral export behavior by default.
- Preserve `PublicLive` and `HiddenUntilClose` semantics, with survey-specific summary rules.
- Treat free-text answers, if approved, as higher privacy risk than choice answers and design
  retention/export/audit rules explicitly.
- Avoid adding survey dashboards or reports until the survey data model is stable.

## 12. Testing Requirements For Future Implementation

The audit should define exact tests for the approved implementation. Likely categories:

- command registration and option ordering
- builder validation and command permission checks
- service validation for question count, option count, required answers, and response changes
- DAL transaction and row-mapping behavior
- response submission, update, duplicate, stale, and closed-survey rejection behavior
- private confirmation and existing-answer prefill behavior
- PublicLive survey summary behavior
- HiddenUntilClose leak prevention across all questions
- close reveal behavior
- export shape and privacy regression
- audit-event metadata without storing voter lists in export audit JSON
- restart-safe public entry point and private response restart/reopen behavior
- scheduler/manual close compatibility
- Codex Security review before PR handoff

Baseline validation for this audit/docs slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 13. Manual Smoke Plan To Define

The audit should produce a final smoke plan for the selected implementation slice. At minimum, it
should include:

1. Create and answer a default one-choice vote to prove regression safety.
2. Create and answer a multi-select vote to prove Phase 6 remains stable.
3. Create the simplest approved survey.
4. Submit a complete response from one user.
5. Submit a response from another user.
6. Change a response when changes are allowed.
7. Confirm changes are blocked when disabled.
8. Restart the bot with an open survey and confirm the public entry point still works.
9. Test HiddenUntilClose for survey summaries.
10. Close manually and by scheduler.
11. Export closed survey summary and detail/audit files privately.
12. Confirm no public voter-level detail is posted.

## 14. Acceptance Criteria

- [ ] Current vote and multi-select SQL contracts are validated against `C:\K98-bot-SQL-Server`.
- [x] Survey shape candidates are compared in a decision matrix.
- [x] The first survey implementation slice is recommended with rationale.
- [x] SQL contract options and migration order are documented.
- [x] Permission/privacy and result-visibility behavior is documented.
- [x] Command/builder/view UX is documented.
- [x] Export and audit implications are documented.
- [x] Automated tests and manual smoke plan are documented.
- [x] Deferred optimisation backlog is updated so no survey, emoji, reporting, or export work is lost.
- [x] Audit-only constraint satisfied before implementation approval.
- [ ] Required docs validators pass after implementation updates.

## 15. PR Summary Template

```md
## Summary

- Audited survey-style voting after Phase 6 MultiSelect delivery.
- Recommended the safest first survey-builder implementation slice.
- Updated deferred voting backlog and preserved remaining voting polish/reporting work.

## Tests

- <commands run>

## Risk / Rollback

- Risk: documentation/scope only unless implementation is separately approved.
- Rollback: revert docs/backlog/task-pack changes.
```
