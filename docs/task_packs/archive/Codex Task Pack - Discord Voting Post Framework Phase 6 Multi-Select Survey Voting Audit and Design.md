# Codex Task Pack - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 5 hidden-until-close results smoke test`
- Task type: `audit | product scope | SQL-backed voting design | Discord interaction UX`
- One-pass approved: `no`
- Status: `complete and smoke tested`

## 2. Objective

Audit and design the next approved advanced voting slice: multi-select or survey-style voting.

Do not implement multi-select, survey mode, SQL migrations, export shape changes, or Discord
interaction changes in this slice until the operator approves the product scope, SQL contract,
privacy model, permissions, UX, and test plan.

The expected output is a decision packet that confirms whether the first implementation should be:

- a single-question `MultiSelect` vote mode only
- a broader survey-style mode with multiple questions
- or a staged roadmap where `MultiSelect` ships first and full survey builder work remains
  deferred

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
- SQL repo `C:\K98-bot-SQL-Server` before recommending any SQL object, column, index, migration,
  view, stored procedure, constraint, or audit event shape.

## 4. Delivered Baseline

Phase 1 through Phase 5 are complete and smoke tested.

The voting framework now supports:

- SQL-backed vote posts, options, votes, reminders, and audit rows.
- One selected option per Discord user for the current default vote mode.
- Vote changes before close.
- Scheduler reminders and automatic close.
- Manual close.
- Disabled buttons after close.
- Restart-safe open vote buttons.
- Guided create option fields and guided close durations.
- Autocomplete vote lookup for status, update, close, and export.
- Guided update target selection.
- Vertical result bars with winner, tie, and no-vote outcomes.
- Private totals-only CSV export for one closed vote at a time.
- Private voter-level audit CSV export for one closed vote at a time.
- Hidden-until-close result visibility with public open-result hiding and public close reveal.
- Private admin/leadership status with live totals.

Phase 5 smoke testing on `2026-07-02` confirmed hidden-until-close behavior was successful.

Do not regress these behaviours.

## 5. Source Deferred Items

This task promotes the active multi-select/survey deferred optimisation into an audit/design slice.

### Deferred Optimisation
- Area: `voting/`, `ui/views/vote_post_view.py`, `/vote_admin`, SQL repo vote framework
- Type: architecture
- Description: Multi-select and survey-style voting are approved for future scope because they support public availability and preference checks better than one forced choice. Current SQL stores one `OptionID` per `(VotePostID, DiscordUserID)`, current buttons have no selected/unselected multi-state, and current result cards assume one vote per user.
- Suggested Fix: Treat multi-select/survey as a separate high-value design and implementation slice after hidden-results scope. Define vote mode, min/max selection rules, result aggregation, export shape, and restart-safe interaction UX before adding SQL such as a vote-selection child table or survey question tables. Do not bundle with emoji support or dashboard readiness.
- Impact: high
- Risk: high
- Dependencies: Hidden-until-close results delivered and smoke tested; approved product design for cardinality and survey semantics; SQL repo migration design; focused interaction and export regression tests.

Phase 6 should either resolve this item by preparing the exact implementation slice, or split it
into separate active deferred items for `MultiSelect` and full survey-builder work.

## 6. Scope

### In Scope

- Define the product value and target use cases for:
  - single-question multi-select voting
  - survey-style voting with multiple questions
- Recommend the safest first implementation slice and explain why.
- Decide whether Phase 6 should design one combined mode or split `MultiSelect` and full survey
  into separate phases.
- Validate the current SQL contract in `C:\K98-bot-SQL-Server`.
- Propose SQL contract options for multi-selection storage, including additive migration and
  rollback considerations.
- Define command UX under existing `/vote_admin` paths where practical.
- Define player interaction UX, including whether to use select menus, private panels, buttons, or
  a staged confirmation view.
- Define public result behavior for both `PublicLive` and `HiddenUntilClose`.
- Define closed result outcome wording for multi-select votes.
- Define totals-only and voter-audit export shape options.
- Define audit event needs for create/update/vote/export behavior.
- Define automated tests and manual smoke plan.
- Update deferred optimisation status so no remaining survey or reporting work is lost.

### Out of Scope

- Implementing `MultiSelect` or survey voting.
- SQL migrations.
- Public voter-level export posting.
- Role-restricted voting.
- Governor-linked voting or governor-aware reporting.
- Saved vote templates.
- Per-option emoji/icon implementation.
- Dashboard/reporting implementation.
- Renaming or removing `/vote_admin`.
- Changing existing one-choice vote button behavior.
- Changing existing totals-only or voter-audit export behavior.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required for affected layers, cardinality design, command shape, persistence, and restart safety. |
| `k98-discord-command-feature` | use | Multi-select affects slash command options, views, select menus/buttons, interaction privacy, and response sequencing. |
| `k98-sql-validation` | use | Required before recommending vote mode columns, selection tables, constraints, indexes, views, or audit contracts. |
| `k98-test-selection` | use | Required to define focused tests for a later implementation slice. |
| `k98-deferred-optimisation-capture` | use | The active multi-select/survey deferred item must be resolved, refined, or split. |
| `k98-pr-review` | use | Use before handoff if the audit edits docs/backlog/task packs. |
| `k98-promotion-check` | conditional | Use before production promotion if docs are pushed to production branches. |
| `codex-security:security-scan` | conditional | Required before any runtime implementation touching Discord interactions, permissions/privacy, SQL/data access, exports, or user input. Usually skipped for audit-only docs with explicit justification. |

## 8. Mandatory Workflow

1. Audit current Phase 1 through Phase 5 behavior and SQL contracts.
2. Validate authoritative SQL assumptions against `C:\K98-bot-SQL-Server`.
3. Compare multi-select-only versus full survey mode.
4. Produce a decision matrix covering product value, privacy, permissions, SQL shape, UX, exports,
   tests, smoke plan, and rollout risk.
5. Recommend the first implementation slice.
6. Update the deferred optimisation backlog.
7. Stop for operator approval before implementation.

## 9. Design Questions To Answer

For each candidate shape, answer:

1. What KD98 problem does it solve?
2. Is this a public vote, private survey, or both?
3. Who can create/manage it?
4. Who can vote?
5. What are the minimum and maximum selections?
6. Can voters change their selections before close?
7. How does the UI show current selections privately without leaking hidden public results?
8. How does `HiddenUntilClose` interact with multi-select result aggregation?
9. What does "winner" mean when voters can select multiple options?
10. What should totals-only export contain?
11. What should voter-audit export contain?
12. Which SQL tables, columns, indexes, constraints, and audit events are needed?
13. What must survive restart?
14. What is the migration and rollback path?
15. Which pieces should remain deferred?

## 10. Likely Files

### Review

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/export_service.py`
- `voting/discord_presentation.py`
- `voting/render_service.py`
- `voting/card_renderer.py`
- `voting/scheduler.py`
- `ui/views/vote_post_view.py`
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

- Keep the current one-choice `PublicLive` vote mode as the default.
- Keep `/vote_admin` as the preferred command group unless an approved design proves it unsuitable.
- Do not add direct SQL to commands or views.
- Keep SQL as the source of truth for vote mode and selections.
- Keep commands thin; services/DAL own validation, cardinality, aggregation, persistence, and
  audit behavior.
- Preserve restart-safe behavior for open vote interactions.
- Preserve private/ephemeral export behavior by default.
- Treat multi-select as a cardinality and data-contract change, not only a renderer change.
- Do not overload existing one-choice buttons if selected/unselected state cannot be represented
  clearly and restart-safely.

## 12. Testing Requirements For Future Implementation

The audit should define the exact tests for the approved implementation. Likely categories:

- command registration and option ordering
- create validation for mode, minimum selections, maximum selections, and option count
- service cardinality rules
- DAL transaction and row-mapping behavior
- selection update/change behavior
- private confirmation behavior
- public live result aggregation
- hidden-until-close leak prevention
- closed reveal and outcome wording
- export shape regression
- voter-audit privacy regression
- restart-safe interaction rehydration
- scheduler/manual close compatibility
- Codex Security review before PR handoff

Baseline validation for this audit/docs slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 13. Acceptance Criteria

- [x] Current vote SQL contract is validated against `C:\K98-bot-SQL-Server`.
- [x] Multi-select-only and survey-style candidates are compared in a decision matrix.
- [x] The first implementation slice is recommended with rationale.
- [x] SQL contract options and migration order are documented.
- [x] Permission/privacy and result-visibility behavior is documented.
- [x] Command/view UX is documented.
- [x] Export and audit implications are documented.
- [x] Automated tests and manual smoke plan are documented.
- [x] Deferred optimisation backlog is updated so no survey, emoji, or reporting work is lost.
- [x] No runtime voting behavior changes in this audit slice.
- [x] Required docs validators pass.

## 14. Phase 6 Audit / Scope Packet

### Scope Summary

Phase 6 audited the next cardinality-changing voting slice after Phase 5 hidden-until-close
results. The safe recommendation is a staged roadmap:

1. Ship single-question `MultiSelect` first.
2. Defer full multi-question survey builder work into a later task pack.
3. Keep emoji/icon polish and dashboard/reporting readiness as separate future slices.

This keeps the first implementation PR focused on one new vote mode, one public post, one
restart-safe interaction entry point, one result aggregation model, and one additive SQL contract.
It also preserves all Phase 1 through Phase 5 one-choice behavior.

### Current SQL / Persistence Contract

Validated against `C:\K98-bot-SQL-Server`:

- `dbo.VotePosts` stores the post, message IDs, status, reminders/mention flags, close metadata,
  and `ResultVisibility`.
- `dbo.VotePostOptions` stores one flat option list per vote post with unique option key and sort
  order indexes.
- `dbo.VotePostVotes` is keyed by `(VotePostID, DiscordUserID)` and has one non-null `OptionID`.
- `dbo.VotePostReminders` and scheduler close state are vote-post-level, not option-level.
- `dbo.VotePostAudit` has single `OptionID` / `PreviousOptionID` columns plus JSON details.
- No SQL object currently stores `VoteMode`, min/max selection rules, multiple selections per
  Discord user, survey questions, or survey responses.

The existing one-choice model is therefore not sufficient for multi-select without an additive SQL
contract. It should not be stretched by stuffing multiple option IDs into the current
`VotePostVotes.OptionID` column or JSON-only storage.

### Decision Matrix

| Candidate | Product value | Privacy / permissions | SQL contract | Discord UX | Exports / audit | Test and smoke burden | Rollout risk | Verdict |
|---|---|---|---|---|---|---|---|---|
| Single-question `MultiSelect` | High. Directly supports availability checks, "pick all that work", preference shortlists, and lightweight leadership decisions. | Same admin/leadership create/manage model; same public voter access; same private export delivery. Result visibility can reuse `PublicLive` and `HiddenUntilClose`. | Add `VotePosts.VoteMode`, `MinSelections`, `MaxSelections`; add current-selection storage for multiple option IDs per Discord user. Existing one-choice tables remain compatible. | Public post should expose one persistent "Choose options" button for multi-select votes. It opens a private panel/select menu for the acting user, avoiding shared public selected-state confusion. | Totals export becomes option-count based for multi-select. Voter audit needs selection-set output without governor identity. Audit details should store before/after selected option IDs. | Moderate: service cardinality, DAL transactions, public/hidden aggregation, private panel, restart opener, exports, close reveal. | Medium. Cardinality changes are real but bounded to one question and current `/vote_admin` workflow. | Recommended first implementation slice. |
| Full multi-question survey | Very high long-term value for richer feedback, event planning, rankings, and structured forms. | More complex. Some survey answers may be sensitive; question-level visibility and admin-only summaries may be needed. | Needs question tables, per-question options, response headers, response answers, order, question type, probably page/progress state. | Requires a guided survey builder and a multi-step private response flow. Public post becomes a survey entry point, not the full voting UI. | Needs long-form and possibly wide-form CSV choices; voter audit must represent multiple questions and answer types. | High: builder, response flow, restart recovery, partial submissions, exports, renderer/reporting, permission review. | High. Too broad for the first cardinality PR. | Defer to a later survey-builder task pack after MultiSelect proves the selection model. |
| Combined MultiSelect + survey in one implementation | Broad coverage, but mostly theoretical first-release value. | Complex and easier to get privacy defaults wrong. | Requires both selection-set and survey-response schema now. | Mixes public vote UX with private survey form UX. | Export shape likely churns immediately. | Very high. | High. | Do not ship as one slice. |

### Recommended First Slice: Single-Question `MultiSelect`

The first implementation should add one new vote mode:

```text
VoteMode = OneChoice | MultiSelect
```

Default remains `OneChoice`, preserving current button behavior, SQL writes, result cards, status,
close, reminders, exports, and rehydration.

For `MultiSelect`:

- Use the same flat option list, initially keeping the existing two-to-six option create limit.
- Default `MinSelections = 1`.
- Require `MaxSelections` between `MinSelections` and option count.
- Allow vote changes before close only when the existing `AllowVoteChange` flag is true.
- Treat one Discord user as one voter even if they select multiple options.
- Treat option counts as "selection count", not total voters.
- Define the closed outcome as "Top selection" or "Top selections", not "Winner", because voters
  can support more than one option.

### SQL Contract Direction

Recommended additive SQL shape for the first implementation:

1. Add to `dbo.VotePosts`:
   - `VoteMode varchar(30) NOT NULL DEFAULT ('OneChoice')`
   - `MinSelections tinyint NOT NULL DEFAULT (1)`
   - `MaxSelections tinyint NOT NULL DEFAULT (1)`
   - checks for `VoteMode IN ('OneChoice', 'MultiSelect')`
   - checks that `MinSelections >= 1`, `MaxSelections >= MinSelections`, and `MaxSelections <= 6`
2. Preserve `dbo.VotePostVotes` for one-choice votes.
3. Add SQL-backed multi-select current-selection storage, preferably:
   - a per-user multi-select ballot/envelope table keyed by `(VotePostID, DiscordUserID)` with
     created/updated timestamps and optional original-selection JSON, plus
   - a child current-selection table keyed by `(VotePostID, DiscordUserID, OptionID)` with a
     composite FK to the option list.
4. Keep `dbo.VotePostAudit` as the durable action trail and use `DetailsJson` for multi-select
   before/after option ID lists. Do not add voter lists to export audit JSON.

Migration order should be:

1. SQL repo migration with nullable/additive or defaulted columns and new tables.
2. Backfill existing rows to `OneChoice`, `MinSelections=1`, `MaxSelections=1`.
3. Add constraints and indexes after data normalization.
4. Deploy bot code that understands both `OneChoice` and `MultiSelect`.
5. Keep rollback as disabling `MultiSelect` creation first, then leaving additive SQL objects in
   place unless a separate destructive rollback is explicitly approved.

Do not infer these objects from Python. The implementation slice must create matching SQL repo
migrations and re-run SQL validation before bot rollout.

### Command / View UX Direction

Keep `/vote_admin` and the current command group.

For `/vote_admin create`, add optional fields only after existing required option fields:

- `vote_mode`, default `OneChoice`
- `min_selections`, default `1`
- `max_selections`, default `1` for `OneChoice`, required/validated for `MultiSelect`

The service remains authoritative: it must reject `OneChoice` values other than min/max `1`, reject
`MultiSelect` cardinality outside the option count, and reject unsupported modes.

Player UX:

- `OneChoice` continues to use the existing public option buttons.
- `MultiSelect` should use a persistent public opener button such as "Choose options".
- The opener creates a private ephemeral selection panel for the acting user.
- The private panel should show a Discord select menu with `min_values` and `max_values` matching
  SQL-backed rules and should write only through the service/DAL.
- Critical selection state must be SQL-backed after submission. Ephemeral view state can be
  transient because users can reopen the public post after restart.

Do not overload public option buttons for multi-select. Shared public buttons cannot clearly show
per-user selected/unselected state, and they would make hidden-result leak review harder.

### Result Visibility And Outcome Rules

`PublicLive`:

- Open multi-select votes may show total voters, total selections, and per-option selection count.
- Percentages should be "percent of voters who selected this option", so percentages can sum above
  100 percent across options.
- Public wording should avoid implying one exclusive winner.

`HiddenUntilClose`:

- Open public posts must hide total voters, total selections, option counts, percentages, bars, and
  outcome text.
- Private `/vote_admin status` may show live totals to admin/leadership users.
- Closing reveals the final multi-select totals and top-selection outcome publicly, just like Phase
  5 close reveal for one-choice votes.

Closed outcome wording:

- no selections: `No votes were cast.`
- one top option: `Top selection: <label> selected by N voter(s) (P%).`
- tie: `Top selections: <labels> selected by N voter(s) each (P%).`

### Export And Audit Direction

Existing closed-only, private export behavior must remain unchanged for `OneChoice`.

For closed `MultiSelect` votes:

- Totals export should include vote mode, min/max selections, total voters, total selections,
  option selection count, percent of voters, and top-selection flag.
- Voter-audit export should stay private and include Discord ID/name only, not governor identity.
- Prefer one row per voter with semicolon-delimited selected option IDs/keys/labels for the first
  implementation. A later reporting slice may add a long-form row-per-selection export if needed.
- Record export audit metadata with mode, row count, byte count, upload limit, oversized flag,
  delivery status, and column profile, but not the voter list.
- Vote-cast audit events should store previous and new selection IDs in `DetailsJson`.

### Architecture Direction

Layer ownership for a later implementation:

- `commands/vote_admin_cmds.py`: collect optional create fields, permission checks, safe defer,
  service handoff, public/private response rendering.
- `voting/service.py`: mode/cardinality validation, min/max rules, selection-set comparison,
  result/outcome semantics, update orchestration.
- `voting/dal.py`: SQL transactions, row mapping, current-selection persistence, aggregation
  queries, audit inserts.
- `ui/views/vote_post_view.py`: persistent public opener and private select-panel interaction
  routing only.
- `voting/discord_presentation.py`, `voting/render_service.py`, `voting/outcomes.py`: mode-aware
  copy, result visibility, card totals, and top-selection wording.
- `voting/export_service.py`: mode-aware closed export rows while preserving one-choice schemas.
- `voting/rehydration.py`: rehydrate one-choice button views and multi-select opener views from
  SQL snapshots.

No direct SQL belongs in commands or views.

### Test Strategy For The Approved Runtime Slice

Focused tests to add/update:

- `tests/test_voting_service.py`: mode parsing, min/max validation, option-count bounds,
  change-blocked behavior, hidden-result compatibility.
- `tests/test_voting_dal.py`: SQL insert/update transaction shape, current-selection aggregation,
  one-choice compatibility, audit details JSON.
- `tests/test_vote_post_view.py`: multi-select opener, private panel handoff, stale/closed vote
  rejection, public message refresh without broad mentions.
- `tests/test_voting_discord_presentation.py`: PublicLive multi-select totals, HiddenUntilClose
  leak prevention, closed reveal.
- `tests/test_voting_render_service.py`: card labels for total voters/selections and hidden mode.
- `tests/test_voting_export_service.py`: totals and voter-audit CSV shape for multi-select plus
  one-choice regression.
- `tests/test_voting_scheduler.py`: automatic close reveal and disabled/open views remain safe.
- `tests/test_vote_admin_cmds.py`: command option validation, default mode, create handoff, export
  mode compatibility.

Validation gates for implementation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_voting_service.py tests\test_voting_dal.py tests\test_vote_post_view.py tests\test_voting_discord_presentation.py tests\test_voting_render_service.py tests\test_voting_export_service.py tests\test_voting_scheduler.py tests\test_vote_admin_cmds.py
```

Run Codex Security review before PR handoff for any approved runtime implementation because the
slice touches Discord interactions, permissions/privacy, SQL persistence, exports, user input, and
restart-sensitive views.

### Manual Smoke Plan For The Approved Runtime Slice

1. Create a default `OneChoice` vote and confirm existing buttons, live totals, close, and export
   behavior still match Phase 1 through Phase 5.
2. Create a `MultiSelect` `PublicLive` vote with min `1`, max `2`, and at least three options.
3. Select two options from the private panel, confirm public counts update, and confirm total voters
   remains one.
4. Change selections before close and verify old selections are replaced, audit records change, and
   public post refreshes without broad mentions.
5. Try too few and too many selections and confirm private rejection.
6. Create a `MultiSelect` `HiddenUntilClose` vote, vote on it, and confirm the public post leaks no
   open totals, counts, bars, or outcome.
7. Restart the bot while a multi-select vote is open and confirm the public opener still works.
8. Close manually and by scheduler, confirming disabled public controls and top-selection wording.
9. Export totals and voter audit privately for a closed multi-select vote.
10. Confirm one-choice exports remain unchanged.

### Deferred Optimisation Status

The original combined multi-select/survey deferred item has been split:

- `MultiSelect` single-question implementation remains active and is now prepared as the safest
  first implementation slice after operator approval.
- Full multi-question survey builder remains deferred as a separate high-risk architecture item.
- Per-option emoji/icon support remains deferred as its own polish slice.
- Dashboard/reporting readiness remains deferred and should wait for stable mode/cardinality
  dimensions.

### Approval Needed

Before implementation, operator approval is needed for:

- staged roadmap with `MultiSelect` first and survey builder deferred
- `VoteMode` names: `OneChoice` and `MultiSelect`
- min/max defaults and first-slice option cap of six
- public opener plus private selection panel UX
- SQL direction using additive mode/cardinality columns and multi-select selection tables
- export shape for multi-select totals and voter audit
- closed outcome wording using "Top selection(s)" instead of "Winner"

## 15. Implementation Addendum

Operator approval to proceed was given after the audit recommendation. The approved first slice was
implemented locally as single-question `MultiSelect` voting while preserving existing `OneChoice`
behavior as the default.

Delivered locally:

- Added `OneChoice` / `MultiSelect` vote-mode normalization.
- Extended vote snapshots and create requests with `VoteMode`, `MinSelections`, `MaxSelections`,
  and `TotalSelections`.
- Added additive SQL migration `20260702_002_add_vote_post_multi_select.sql` in
  `C:\K98-bot-SQL-Server`.
- Preserved `dbo.VotePostVotes` for one-choice votes.
- Added SQL-backed multi-select ballot/current-selection storage through
  `dbo.VotePostMultiSelectVotes` and `dbo.VotePostMultiSelectSelections`.
- Added `/vote_admin create` optional mode/cardinality fields after the existing required options.
- Kept existing one-choice public option buttons.
- Added a persistent public multi-select opener button and private user-specific selection panel.
- Made public embed/card/result outcome copy mode-aware.
- Reused `PublicLive` and `HiddenUntilClose` result visibility for MultiSelect.
- Kept existing one-choice totals/voter-audit CSV headers unchanged.
- Added mode-aware closed-only private totals and voter-audit CSV shape for MultiSelect.
- Added focused regression coverage across service, DAL, command, view, presentation, renderer,
  export, and scheduler-adjacent behavior.

Remaining out of scope:

- Full multi-question survey builder.
- Per-option emoji/icon support.
- Dashboard/reporting implementation.
- Role-restricted voting, governor-linked voting, saved templates, and public voter-level exports.

## 16. Validation Results

Implementation slice. Runtime Python and SQL migration files changed. SQL PR
`cwatts6/K98-bot-SQL-Server#28` has been merged and successfully deployed to production.

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_voting_service.py tests\test_voting_dal.py tests\test_vote_post_view.py tests\test_voting_discord_presentation.py tests\test_voting_render_service.py tests\test_voting_export_service.py tests\test_voting_scheduler.py tests\test_vote_admin_cmds.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_ui_imports.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

Result: passed on 2026-07-02. Final full pytest result after review hardening and smoke-test UX
polish: `2251 passed, 2 skipped`.

SQL repo validation:

```powershell
.\deploy\Validate-SqlRepo.ps1
```

Result: succeeded on 2026-07-02, with pre-existing warnings on older migrations containing
`DROP TABLE` or `TRUNCATE TABLE`.

Codex Security review was considered before PR handoff because this implementation touches Discord
interactions, SQL persistence, privacy/export surfaces, user input, and restart-safe views. The
full Codex Security workbench was not opened for the final tiny UX follow-up because it required a
manual scan-start step; the security-sensitive surface was reviewed locally. The follow-up only
reads the current caller's existing multi-select option IDs for the current vote and uses them as
private Discord select defaults; it does not change writes, exports, permissions, or public
visibility.

## 17. Smoke Test Results

Operator smoke testing completed successfully on `2026-07-02`.

Confirmed:

- Multi-select create, vote, update, close, and status paths work.
- Vote changes allowed and blocked behavior works.
- Selection limits work.
- Restart-safe multi-select opener behavior works.
- Previously selected options display when reopening the selector and can be amended.
- Updated selections are reflected successfully.
- Existing one-choice regression behavior remains compatible.

Phase 6 delivered:

- Single-question `MultiSelect` voting.
- SQL-backed vote mode and min/max selection rules.
- SQL-backed multi-select ballots and current selections.
- Persistent public opener with private per-user selection panel.
- Private panel preselection of existing choices when changes are allowed.
- PublicLive and HiddenUntilClose result behavior for multi-select.
- Mode-aware status, close outcome, cards, totals export, and voter-audit export.

Remaining out of scope and still tracked:

- Full multi-question survey builder.
- Per-option emoji/icon support.
- Dashboard/reporting readiness.
- Role-restricted voting, governor-linked voting, saved templates, and public voter-level exports.

## 18. PR Summary Template

```md
## Summary

- Audited multi-select and survey-style voting after Phase 5 hidden-results delivery.
- Recommended the safest first cardinality-change implementation slice.
- Updated deferred voting backlog and preserved remaining future voting work.

## Tests

- <commands run>

## Risk / Rollback

- Risk: documentation/scope only unless implementation is separately approved.
- Rollback: revert docs/backlog/task-pack changes.
```
