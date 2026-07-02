# Discord Voting Post Framework - Programme Pack

> Living programme pack for SQL-backed, button-driven Discord vote posts with live Pillow result
> cards, restart-safe scheduling, and guided admin/player workflows.

## 1. Programme Header

- Programme name: `Discord Voting Post Framework`
- Date: `2026-07-01`
- Owner/context: `KD98 Discord bot / leadership and admin voting workflow`
- Programme type: `Product UX | Discord command architecture | SQL/data | visual output | operations`
- One-pass approved: `no`
- Current status: `Phase 1 complete; Phase 2 complete; Phase 3 complete; Phase 4 complete; Phase 5 complete; Phase 6 single-question MultiSelect complete and smoke tested; Phase 7 choice-only survey first slice in implementation; free-text and Add details confirmed as the next phase`
- Headline: `Make voting simple, guided, durable, and good-looking.`

## 2. Programme Vision

The voting framework should give KD98 admins a polished way to launch decisions, event-time
choices, player preference checks, and community votes without manual counting, repeated pings, or
fragile restart behavior.

Players should see a clear public vote post, tap a button, receive private confirmation, and trust
that the visible result card reflects the SQL-backed source of truth. Admins should be guided
through vote creation and management rather than needing to remember vote IDs, UTC string formats,
pipe-separated option syntax, or hidden character limits.

The product standard is: make it simple, make it guided, and make it look great. SQL remains the
authority; Discord buttons, embeds, selectors, modals, reminders, and Pillow cards are the UX.

## 3. Phase 1 Delivery Summary

Phase 1 delivered the first working SQL-backed live voting MVP.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#193`
- Production PR: `cwatts6/k98-bot#501`
- SQL PR: `cwatts6/K98-bot-SQL-Server#26`
- SQL deployment: `2026-07-01`
- Bot smoke test: `2026-07-01`

SQL deployment added:

- `dbo.VotePosts`
- `dbo.VotePostOptions`
- `dbo.VotePostVotes`
- `dbo.VotePostReminders`
- `dbo.VotePostAudit`

Smoke test confirmed:

- `/vote_admin create` creates a public vote post.
- Voting buttons work.
- Vote changes record correctly.
- SQL rows reflect vote creation, votes recorded, and votes changed.
- `@everyone` launch behavior works as configured.
- The original vote post updates in place without repeated broad pings.
- Manual close works.
- Timer close works.
- Buttons are disabled after close.

Phase 1 records are archived under:

```text
docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 1 SQL Backed Live Voting.md
```

## 4. Phase 2 Delivery Summary

Phase 2 delivered the guided admin UX and results polish slice.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#194`
- Production PR: `cwatts6/k98-bot#502`
- SQL PR: `not required`
- Bot smoke test: `2026-07-01`

Delivered:

- `/vote_admin create` now uses individual option fields instead of pipe-separated input.
- Option 1 and Option 2 are required; Options 3-6 are optional.
- Vote posts support up to six options.
- Option label validation is configurable with `VOTE_OPTION_LABEL_MAX_LENGTH`, defaulting to 20 and
  allowing values from 1 through 80.
- Close time uses guided duration choices rather than raw UTC free text.
- `/vote_admin update`, `/vote_admin status`, and `/vote_admin close` use autocomplete vote
  selection with title plus status/close-time metadata.
- `/vote_admin update` opens an explicit private update panel so admins choose the field to edit.
- `/vote_admin status` output was preserved.
- Result cards use vertical bars.
- Closed cards and close announcements show winner, tie, or no-vote outcomes clearly.
- Manual close and automatic close both use the same outcome summary.
- Restart-safe open vote buttons continue to work after bot restart.
- Vote updates still avoid repeated `@everyone` pings.

Smoke test confirmed:

- Guided create works.
- The 20-character option label limit works when configured in `.env`.
- Status, close, and update vote selection offer the expected vote list.
- Update opens the six-option guided follow-up menu.
- Manual close disables buttons and shows a clear result.
- Open-vote buttons still work after bot restart.

Phase 2 records are archived under:

```text
docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish.md
docs/task_packs/archive/Codex Chat Starter - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish.md
```

## 5. Target Model

### Current command model

```text
/vote_admin create
/vote_admin update
/vote_admin close
/vote_admin status
```

Phase 1 intentionally used `/vote_admin` as the approved command group.

### Current command model after Phase 4

The existing command group now includes private completed-vote export:

```text
/vote_admin create
/vote_admin update
/vote_admin close
/vote_admin status
/vote_admin export
```

No new top-level command was added. Phase 4 added `mode` selection to `/vote_admin export` rather
than creating a separate command. Future voting slices should keep using `/vote_admin` unless a
later task pack explicitly approves a different command shape.

### Target workflow model

```text
Admin creates guided vote -> bot validates early -> bot posts vote -> players vote -> SQL updates
-> original message/card edits in place -> reminder/close scheduler runs -> final card and close
announcement highlight the winner
```

### Target data/model contract

```text
Discord command/select/modal -> voting service -> voting DAL -> SQL tables
SQL snapshot -> embed/card renderer -> original Discord message update
Scheduler -> due reminders/closes -> voting service -> final card and close announcement
```

## 6. Design Principles

1. **Guided before clever** - Avoid compact syntax when Discord can provide separate fields,
   selectors, autocomplete, or staged forms.
2. **Validate as early as possible** - Use Discord option limits where available, then service
   validation as the authority.
3. **SQL is the source of truth** - Buttons and cards reflect SQL state; they do not define it.
4. **No accidental spam** - Launch, reminders, and close may use configured broad mentions; vote
   updates never do.
5. **Restart-safe by default** - Views, reminders, close jobs, and message IDs must survive restart.
6. **Readable final outcome** - Closed votes should tell players who won without making them infer
   it from bars.
7. **Good visual hierarchy** - Cards should scan well on Discord desktop and mobile, with clear
   status, options, totals, and winner treatment.
8. **Commands stay thin** - Commands collect/validate Discord-facing inputs and call services;
   services and DAL own behavior and persistence.

## 7. Programme Phases

### Phase 1 - SQL-Backed Live Voting MVP

Status: complete.

Delivered:

- SQL schema and deployed tables for vote posts, options, votes, reminders, and audit.
- `/vote_admin create`, `/vote_admin update`, `/vote_admin status`, and `/vote_admin close`.
- Persistent button view and restart-safe rehydration.
- SQL-backed one-vote-per-Discord-user enforcement.
- Optional vote changes before close.
- Live Pillow result card.
- Original vote post updates without repeated `@everyone` pings.
- Scheduler reminders and automatic close.
- Manual close.
- Disabled buttons after close.
- Backend late-vote rejection.
- Review hardening for launch failure cleanup, SQL length validation, close reason validation,
  elapsed-deadline card status, background file-handle handling, reminder mark failure handling,
  and Discord required/optional command option ordering.
- Focused tests, full test suite validation, mirror and production PR promotion.

### Phase 2 - Guided Admin UX and Results Polish

Status: complete.

Delivered:

- Individual create option fields with two required options and four optional options.
- Up to six option buttons and six vertical result bars.
- Configurable option label length via `VOTE_OPTION_LABEL_MAX_LENGTH`, default 20.
- Guided close-duration choices.
- Autocomplete vote lookup for update, status, and close.
- Explicit update target menu.
- Preserved status output.
- Vertical result card bars.
- Winner, tie, and no-vote outcome treatment on closed cards and announcements.
- Preserved SQL source of truth, one vote per Discord user, vote changes, scheduler reminders,
  automatic close, manual close, disabled buttons, backend late-vote rejection, restart safety, and
  mention safety.

### Phase 3 - Admin Export and Audit Hardening

Status: complete.

Delivered:

- Added `/vote_admin export` under the existing `/vote_admin` command group.
- Added closed-vote autocomplete for export lookup.
- Exported one completed vote at a time as a totals-only CSV attachment.
- Kept export delivery private/ephemeral by default.
- Included final option totals, percentages, outcome kind/summary, close metadata, message link,
  reminder metadata, and numeric `IsWinningOption` flags.
- Deferred voter-level audit export pending a separate privacy and access-control slice.
- Preserved Phase 1 and Phase 2 behavior, including restart-safe open vote buttons.
- Required no SQL migration; existing SQL-backed vote snapshots and DAL-owned queries are
  sufficient for the delivered totals export.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#195`
- SQL PR: `not required`
- Bot smoke test: `2026-07-02`

Smoke test confirmed:

- `/vote_admin export` produces the expected CSV.
- Export response posts ephemerally/private as expected.
- Existing vote buttons still work after restart and deployment.

Phase 3 records are archived under:

```text
docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening.md
docs/task_packs/archive/Codex Chat Starter - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening.md
```

### Phase 4 - Voter-Level Audit Export Privacy and Access Controls

Status: complete and smoke tested.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#196`
- Production PR: `cwatts6/K98-bot#504`
- SQL PR: `not required`
- Bot smoke test: `2026-07-02`

Delivered:

- Approved voter-level audit export for admin/leadership users.
- Added private `/vote_admin export mode:voter_audit` for one closed vote at a time.
- Preserved default totals-only `/vote_admin export` behavior.
- Included spreadsheet-safe Discord user ID text, resolved Discord name, selected option, original
  option, vote timestamps, and vote-change flag.
- Excluded governor names and `GovernorID`; Phase 5 later removed governor-linked voting from active
  voting scope.
- Added SQL audit logging through `VotePostAudit` with `ActionType=VoterAuditExported`.
- Logged requester ID plus mode, row count, byte count, upload limit, oversized flag, delivery
  status, and column profile without storing the voter list in audit JSON.
- Preserved private/ephemeral delivery by default.
- Validated all SQL-facing voter/audit columns against `C:\K98-bot-SQL-Server`.

Smoke test confirmed:

- `/vote_admin export mode:voter_audit` produces a private/ephemeral voter-level export.
- Voter-audit CSV includes `DiscordUserID` and `DiscordName`.
- `DiscordUserID` opens in Excel/Sheets as text and preserves the full Discord snowflake.
- Governor names and `GovernorID` are absent.
- `VoteChanged` is correct for a changed vote.
- `VotePostAudit` writes `ActionType=VoterAuditExported` with requester ID and expected metadata.
- Regression tests passed.

Phase 4 records are archived under:

```text
docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls.md
docs/task_packs/archive/Codex Chat Starter - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls.md
```

### Phase 5 - Advanced Voting Modes Audit and Hidden-Until-Close Results

Status: complete and smoke tested.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#197`
- Production PR: `cwatts6/k98-bot#505`
- SQL PR: `cwatts6/K98-bot-SQL-Server#27`
- Bot smoke test: `2026-07-02`

Phase 5 first produced a mode-by-mode decision matrix and split the remaining candidate modes into
approved future slices for:

- Hidden-until-close result visibility.
- Multi-select or survey-style vote modes.
- Per-option emoji/icon support.
- Dashboard/reporting readiness.

Do not implement additional advanced voting modes until the operator separately approves the next
implementation slice.

Operator-reviewed Phase 5 recommendation:

- First implementation candidate: hidden-until-close results, because it improves public vote
  quality without changing vote cardinality, scheduler behavior, exports, or existing button
  semantics.
- Second implementation candidate: multi-select/survey voting, because it has high KD98 value for
  availability and preference checks.
- Later approved candidates: per-option emoji/icon support and dashboard/reporting readiness.
- Removed from active scope: role-restricted voting, governor-linked voting/governor-aware audit,
  saved vote templates, and public voter-level export posting.
- First approved implementation slice delivered: create-time hidden-until-close result visibility
  with public close reveal, private admin live totals, unchanged player vote buttons, and unchanged
  private closed-only exports.

Delivered:

- Added create-time `result_visibility` selection with `PublicLive` as the default and
  `HiddenUntilClose` as the optional mode.
- Added additive SQL-backed `VotePosts.ResultVisibility` storage with a default preserving existing
  Phase 1 through Phase 4 behavior.
- Hid public open-result totals, option counts, percentages, bar fills, total-voter footer, and
  outcome text for hidden-until-close votes.
- Kept player vote buttons and vote-change behavior unchanged.
- Kept private `/vote_admin status` live totals available to admin/leadership users.
- Revealed final totals, bars, and winner/tie/no-vote outcome publicly when the vote closes.
- Preserved private closed-only totals and voter-audit exports.
- Preserved restart-safe open vote buttons and scheduler/manual close behavior.

Smoke test confirmed:

- Hidden-until-close votes can be created and voted on through the normal public vote post.
- Open hidden-result votes do not leak public interim totals or outcome state.
- Closing the vote reveals total votes, option results, and winner/tie/no-vote outcome.
- Result visibility is shown clearly on the public post.
- Existing button, close, and export behavior remains compatible.

Phase 5 records are archived under:

```text
docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning.md
docs/task_packs/archive/Codex Chat Starter - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning.md
```

### Phase 6 - Multi-Select / Survey Voting Audit and Design

Status: complete and smoke tested.

Delivered through:

- Mirror PR: `cwatts6/K98-bot-mirror#198`
- Production PR: `cwatts6/k98-bot#506`
- SQL PR: `cwatts6/K98-bot-SQL-Server#28`
- SQL deployment: `2026-07-02`
- Bot smoke test: `2026-07-02`

Phase 6 first audited multi-select versus full survey-style voting and selected a staged roadmap:
ship single-question `MultiSelect` first, then defer the full survey builder into a later task
pack. This kept the first cardinality change bounded to the existing `/vote_admin` workflow while
preserving all Phase 1 through Phase 5 behavior.

Confirmed Phase 6 direction:

- Focus first on whether KD98 needs a single-question multi-select vote mode before any full
  multi-question survey builder.
- Preserve the existing one-choice `PublicLive`/`HiddenUntilClose` mode as the default behavior.
- Reuse hidden-until-close result visibility where applicable instead of introducing another result
  visibility model.
- Define SQL storage for multiple selections per Discord user before implementation.
- Keep private exports private and closed-only unless a later task explicitly approves a change.
- Keep role-restricted voting, governor-linked voting, saved templates, public voter-level export
  posting, emoji/icon support, and dashboard/reporting implementation out of this slice.

Audit recommendation drafted on `2026-07-02`:

- Use a staged roadmap rather than one combined multi-select/survey implementation.
- First implementation slice: single-question `MultiSelect` under the existing `/vote_admin`
  workflow.
- Preserve current `OneChoice` behavior as the default and keep the current public option buttons
  for that mode.
- Additive SQL direction: `VotePosts.VoteMode`, `MinSelections`, `MaxSelections`, and SQL-backed
  multi-select selection storage; do not overload `VotePostVotes.OptionID` with multiple values.
- Player UX direction: persistent public opener button for multi-select votes, with a private
  user-specific select panel for selection submission.
- Result direction: reuse `PublicLive` and `HiddenUntilClose`; public multi-select percentages are
  percent of voters selecting each option, and closed copy should say `Top selection(s)` rather
  than `Winner`.
- Export direction: keep existing one-choice exports unchanged; add mode-aware closed-only private
  totals and voter-audit shapes for multi-select.
- Full multi-question survey builder remains deferred as a separate high-risk task pack.

Delivered after operator approval:

- Added `OneChoice` / `MultiSelect` vote mode handling with `OneChoice` as the default.
- Added SQL-backed mode/cardinality columns and multi-select current-selection storage in the SQL
  repo migration `20260702_002_add_vote_post_multi_select.sql`.
- Preserved existing one-choice public option buttons and exports.
- Added a persistent public "Choose options" opener button for multi-select votes with a private
  user-specific selection panel.
- Added private panel preselection of existing choices when a user reopens the selector.
- Made status, public embeds, rendered cards, outcomes, and closed-only private exports mode-aware.
- Full pytest passed locally with `2245 passed, 2 skipped`; SQL repo validation succeeded with only
  pre-existing warnings on older migrations.

Final validation and smoke evidence:

- Final full pytest after review hardening and smoke-test UX polish: `2251 passed, 2 skipped`.
- Multi-select create/vote/update/close/status paths work.
- Vote changes allowed and blocked behavior works.
- Selection limits work.
- Restart-safe opener behavior works.
- Previously selected options display when reopening the selector and can be amended.
- Updated selections are reflected successfully.
- Existing one-choice regression behavior remains compatible.

Phase 6 records are archived under:

```text
docs/task_packs/archive/Codex Task Pack - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design.md
docs/task_packs/archive/Codex Chat Starter - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design.md
```

### Phase 7 - Survey Builder Audit and Design

Status: first choice-only implementation slice approved and in implementation.

Phase 7 started with audit/scope because full multi-question survey-style voting changes product
semantics, privacy, SQL shape, private response flow, export shape, and reporting implications
more deeply than Phase 6 single-question `MultiSelect`. The operator approved the safest first
implementation slice: choice-only surveys first, with free-text questions and choice-question
`Add details` confirmed as the next phase.

Audit recommendation drafted on `2026-07-02`:

- Use a separate SQL-backed survey-post model rather than adding `Survey` to
  `VotePosts.VoteMode`, because the current vote-post model and Python snapshot/view/export code
  are intentionally single-question.
- Keep surveys under the existing `/vote_admin` top-level group, beginning with a new
  survey-specific create flow only after operator approval.
- First implementation slice: choice-only surveys with two to five required questions, two to six
  options per question, min/max selection controls that derive single-choice versus multi-select
  behavior, no free text, no optional answers, no role restrictions, no governor linking, and no
  templates.
- Player UX: persistent public `Answer survey` button, private paged response panel, direct
  submit from the private panel, submitted-answer prefill when reopening, no persisted partial
  drafts in the first slice, and SQL-backed submitted responses only.
- Privacy: public aggregate summaries only, no public voter-level detail, `HiddenUntilClose` hides
  public response counts and per-question totals until close, and private closed-only summary/detail
  CSV exports remain admin/leadership-gated.
- SQL direction: additive `dbo.SurveyPosts`, `dbo.SurveyQuestions`,
  `dbo.SurveyQuestionOptions`, `dbo.SurveyResponses`, `dbo.SurveyAnswers`,
  `dbo.SurveyReminders`, and `dbo.SurveyAudit` tables with FKs, uniqueness constraints, JSON audit
  checks, open/due indexes, and aggregation indexes.
- Future slices remain separate for draft/resume support, optional questions, free-text/rating
  types, richer survey exports, emoji/icon support, and private reporting/dashboard readiness.
- Operator follow-up confirmed that the first implementation step should stay multiple-choice
  only. A second survey slice should add free-text questions and optional choice-question
  `Add details` text, and that submitted text/detail data must be included in private
  admin/leadership exports. Admin/leadership visibility should match the current vote results
  model: authorized private live/status/export visibility, public aggregate output only according
  to result visibility, and no public voter-level/detail export.

Prepared scope retained:

- Define the first survey implementation candidate and decide whether it is a simple
  choice-question survey, a paged private response flow, or a fuller guided builder.
- Define question types and first-slice limits.
- Define required/optional answer rules, partial response policy, resume policy, and response
  change behavior.
- Define how existing answers are shown privately when editing a response.
- Define PublicLive and HiddenUntilClose behavior across multiple questions.
- Define summary and detail/voter-audit export shapes.
- Validate SQL options against `C:\K98-bot-SQL-Server`, including survey definitions, questions,
  options, response envelopes, answers, indexes, constraints, and audit events.
- Preserve one-choice and multi-select behavior.
- Keep emoji/icon support and dashboard/reporting implementation out of the first survey audit
  unless separately approved.

## 8. Remaining Slice Scope Summary

### Completed Phase 4 scope summary

Phase 4 was a privacy and access-control slice for voter-level audit export. It did not add new
voting modes or change player voting behavior.

Affected areas:

- `commands/vote_admin_cmds.py`
- `voting/export_service.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/discord_presentation.py` only if admin summary rendering changes
- `ui/views/` only if a guided export mode selector is approved
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_service.py`
- `tests/test_voting_dal.py` or equivalent SQL/DAL contract tests if query shape changes
- `tests/test_voting_export_service.py`
- `tests/test_voting_discord_presentation.py`
- SQL repo only if voter-level export, audit logging, or query performance needs cannot be
  satisfied by current tables and indexed queries.

### Phase 5 advanced-mode scope summary

Phase 5 audited role restrictions, hidden/anonymous result rules, governor-linked identity,
multi-select/survey semantics, templates, optional emoji/icon support, dashboard/reporting
readiness, and public voter-level export posting. Operator review retained hidden-until-close
results, multi-select/survey voting, per-option emoji/icon support, and dashboard/reporting
readiness as active future scope. Hidden-until-close results are now delivered and smoke tested.
Role-restricted voting, governor-linked voting, saved templates, and public voter-level export
posting were removed from active scope.

Phase 5 decided:

- hidden-until-close result visibility was the safest first implementation slice and is now complete
- full survey-builder voting, emoji/icon support, and dashboard/reporting readiness remain active
  future slices after Phase 6 MultiSelect delivery
- role-restricted voting, governor-linked voting, saved vote templates, and public voter-level
  export posting are removed from active scope
- existing `/vote_admin` paths remain sufficient for the approved voting-mode roadmap
- each future slice must define SQL/schema/index/audit, automated tests, and manual smoke evidence
  before implementation

### Phase 6 multi-select scope summary

Phase 6 is complete. It resolved the first half of the combined multi-select/survey deferred item
by delivering single-question `MultiSelect` voting with SQL-backed cardinality and selection
storage.

Delivered scope:

- Staged roadmap selected: `MultiSelect` first, full survey builder deferred.
- Additive SQL delivered: `VotePosts.VoteMode`, `MinSelections`, `MaxSelections`,
  `dbo.VotePostMultiSelectVotes`, and `dbo.VotePostMultiSelectSelections`.
- Existing one-choice vote buttons preserved.
- Multi-select public opener plus private selection panel delivered.
- Existing selections are preselected when a user reopens the panel.
- PublicLive and HiddenUntilClose result behavior works for multi-select.
- Mode-aware status, card, close outcome, totals export, and voter-audit export delivered.
- Restart-safe opener behavior smoke tested.
- One-choice regression behavior smoke tested.

### Phase 7 survey-builder scope summary

Phase 7 should not implement survey voting immediately. It should audit and design the safest first
survey builder slice, then stop for approval.

Prepared scope:

- Define whether survey-style voting should be modeled as a vote mode, a separate survey object,
  or a survey object linked to a public vote post.
- Define command placement under existing `/vote_admin` paths versus a separately approved survey
  command group.
- Define first-slice question types and limits.
- Define partial response, resume, response-change, and existing-answer prefill behavior.
- Validate SQL options against `C:\K98-bot-SQL-Server`, including survey definitions, questions,
  options, response envelopes, answers, constraints, indexes, and audit events.
- Define how public live and hidden-until-close result visibility should work across multiple
  questions.
- Define closed summary, totals export, and voter-audit/detail export shapes before changing any
  export behavior.
- Define automated tests and manual smoke steps for builder UX, response submission/change,
  restart behavior, exports, close reveal, and privacy.

## 9. Cross-Programme Constraints

- Do not add another top-level command for Phase 3.
- Keep `/vote_admin` command registration valid: required options must precede optional options.
- Do not rely on Discord UI limits alone; service validation must remain authoritative.
- Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Preserve all Phase 1 and Phase 2 smoke-tested behavior.
- Do not introduce repeated `@everyone` pings on vote updates.
- Preserve persistent view restart behavior and scheduler idempotency.
- Do not edit vote options after votes exist unless the task explicitly defines safe rules.
- Do not expose voter-level exports publicly without explicit approval.
- Do not add further advanced voting modes until their product, privacy, permissions, SQL, UX,
  test, and rollout model are explicitly approved.
- Do not implement full survey builder, emoji/icon support, dashboard/reporting readiness,
  role-restricted voting, governor-linked voting, saved templates, or public voter-level exports
  as part of Phase 7 unless separately approved.

## 10. Validation Strategy

Every implementation phase should consider:

- command registration validation
- focused command tests
- service validation tests
- view/button interaction tests
- scheduler reminder/close tests
- render output shape tests
- SQL/DAL contract tests where SQL-facing behavior changes
- restart/rehydration tests
- manual Discord smoke testing
- Codex Security review when Discord interactions, SQL/data access, permissions, or persistence are
  touched

Baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 11. Programme Acceptance Criteria

The core programme is successful when:

- [x] Admins can create a SQL-backed vote.
- [x] Players can vote once per Discord user.
- [x] Vote changes can update the existing vote row.
- [x] Launch `@everyone` works when configured.
- [x] Per-vote updates do not repeat `@everyone`.
- [x] Scheduler reminders and closes are SQL-backed.
- [x] Buttons disable after close.
- [x] Backend rejects late votes.
- [x] Persistent views survive restart.
- [x] SQL is the durable source of truth.
- [x] Admin creation is guided and avoids pipe-separated option syntax.
- [x] Admin close time input is guided.
- [x] Admin update/status/close do not require raw VotePostID lookup.
- [x] Closed votes visibly highlight the winner or tie state.
- [x] Result cards meet the vertical-bar visual direction.
- [x] Totals-only completed-vote export workflow is delivered in Phase 3.
- [x] Voter-level audit export is delivered in Phase 4 with admin/leadership private delivery,
      Discord ID/name columns, SQL audit logging, and governor identity deferred.
- [x] Hidden-until-close result visibility is delivered in Phase 5 with public open-result hiding,
      public close reveal, private admin live totals, and unchanged private closed-only exports.
- [x] Single-question multi-select voting is delivered in Phase 6 with SQL-backed mode/cardinality
      storage, restart-safe public opener, private selection panel, existing-selection prefill,
      PublicLive/HiddenUntilClose support, mode-aware status/cards/outcomes/exports, and preserved
      one-choice behavior.

## 12. Suggested Next Action

```text
Start Discord Voting Post Framework Phase 7: Survey Builder Audit and Design.

Begin with audit/scope only. Do not implement SQL migrations, survey tables, question-builder UI,
private response flows, export shape changes, dashboard/reporting implementation, or command
changes until the Phase 7 architecture and product scope are approved.
```

## 13. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| 2026-07-01 | Initial programme pack created | Captured SQL-backed live voting, buttons, Pillow card, reminders, and close handling. |
| 2026-07-01 | Phase 1 marked complete | SQL deployed, bot smoke test successful, mirror/prod review fixes completed. |
| 2026-07-01 | Phase 2 scope prepared | Preserved smoke-test feedback for guided create UX, vote selectors, vertical bars, and winner callout. |
| 2026-07-01 | Phase 2 marked complete | Guided create, vote lookup, update panel, vertical bars, outcome summaries, restart smoke, and configurable option length delivered. |
| 2026-07-01 | Phase 3 scope prepared | Next slice confirmed as admin export, closed-vote history, and audit retrieval under `/vote_admin`. |
| 2026-07-02 | Phase 3 marked complete | Totals-only `/vote_admin export` delivered, smoke tested private/ephemeral export, and restart/deployment vote buttons confirmed. |
| 2026-07-02 | Phase 4 scope prepared | Next slice confirmed as voter-level audit export privacy and access-control audit before advanced voting modes. |
| 2026-07-02 | Phase 4 implemented | Added private voter-level audit export mode with Discord ID/name, option/timestamp/change columns, SQL audit logging, and totals-only export preserved. |
| 2026-07-02 | Phase 4 smoke tested and archived | Smoke confirmed private voter-audit export, Excel-safe Discord ID text, DiscordName, governor identity exclusion, VoteChanged, SQL audit metadata, and regression tests. Phase 4 task pack and starter moved to archive. |
| 2026-07-02 | Phase 5 prepared | Created advanced voting modes audit/slice-planning task pack and starter; active deferred voting item promoted into Phase 5 audit scope. |
| 2026-07-02 | Phase 5 audit drafted | Initial draft recommended role-restricted voting as the safest first implementation slice; split hidden results, governor-aware audit/reporting, multi-select/survey, templates, emoji/icon support, dashboard readiness, and public voter-level export posting into future slices or deferred policy items. |
| 2026-07-02 | Phase 5 operator scope revised | Approved hidden-until-close results, multi-select/survey voting, per-option emoji/icon support, and dashboard/reporting readiness for future slices; removed role-restricted voting, governor-linked voting, saved templates, and public voter-level export posting from active scope. |
| 2026-07-02 | Hidden results slice locally validated | Added create-time `PublicLive`/`HiddenUntilClose` result visibility, SQL `VotePosts.ResultVisibility` migration, public open-result hiding, public close reveal, private admin live totals, focused regression tests, full pytest, SQL validation, and Codex Security review with 0 findings. |
| 2026-07-02 | Hidden results smoke tested and archived | Operator smoke testing confirmed hidden-until-close behavior was successful. Phase 5 audit/starter records were archived, and Phase 6 multi-select/survey audit and design was prepared as the next voting slice. |
| 2026-07-02 | Phase 6 audit drafted | Recommended staged roadmap with single-question `MultiSelect` first, full survey builder deferred, additive SQL mode/cardinality and selection storage, private selection-panel UX, mode-aware result/export behavior, and no runtime changes until operator approval. |
| 2026-07-02 | Phase 6 MultiSelect implemented locally | Added SQL-backed `OneChoice`/`MultiSelect` mode, min/max selections, multi-select ballot/selection storage, persistent public opener with private selection panel, mode-aware status/cards/outcomes/exports, focused tests, full pytest, and SQL repo validation. |
| 2026-07-02 | Phase 6 smoke tested and archived | SQL PR #28 was merged and deployed to production. Smoke testing confirmed multi-select create/vote/update/close/status paths, allowed/blocked changes, selection limits, restart-safe opener behavior, existing-selection prefill, successful amendments, and one-choice regression compatibility. Phase 6 task pack and starter were archived. |
| 2026-07-02 | Phase 7 survey-builder audit prepared | Created the next active survey-builder audit/design task pack and starter; preserved remaining full survey, emoji/icon, dashboard/reporting, and export/reporting follow-up work in deferred optimisation scope. |
| 2026-07-02 | Phase 7 survey-builder audit drafted | Recommended separate SQL-backed choice-only survey posts under `/vote_admin`, with private paged response UX, no partial persisted drafts, hidden-until-close aggregate privacy, closed-only private exports, additive survey SQL tables, and future task-pack outlines for draft/resume, advanced question types, reporting, and export v2. Operator confirmed multiple-choice first, then free-text questions plus choice-question `Add details` in a second slice with submitted text/detail data included in private admin/leadership exports. |
| 2026-07-02 | Phase 7 choice-only survey first slice started | Began implementation of separate SQL-backed choice-only survey posts under `/vote_admin survey_*`, preserving existing one-choice and single-question MultiSelect behavior. Free-text questions and choice-question `Add details` remain the next phase. |
