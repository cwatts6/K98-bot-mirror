# Codex Task Pack - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 4 voter-level audit export smoke test`
- Task type: `audit | product scope | Discord command workflow | SQL-backed voting design`
- One-pass approved: `no`
- Status: `audit drafted - awaiting operator approval`

## 2. Objective

Audit the remaining advanced voting-mode ideas and split them into safe, PR-sized future slices.
Do not implement a new voting mode in Phase 5 unless the operator explicitly approves a follow-up
implementation slice after this audit.

Phase 5 should decide which advanced modes are worth building, what each mode's privacy,
permission, SQL, UX, testing, and deployment model must be, and which deferred optimisation items
will be resolved by each future slice.

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
- SQL repo `C:\K98-bot-SQL-Server` before any SQL object, column, index, migration, view, or audit
  contract decision.

## 4. Delivered Baseline

Phase 1 through Phase 4 are complete and smoke tested.

The voting framework now supports:

- SQL-backed vote posts, options, votes, reminders, and audit rows.
- One vote per Discord user.
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
- Admin/leadership-only voter audit export with spreadsheet-safe Discord ID text, Discord name,
  option/original-option fields, vote timestamps, and change flag.
- SQL `VotePostAudit` event `VoterAuditExported` with requester ID and export metadata.

Phase 4 smoke testing on `2026-07-02` confirmed:

- Private/ephemeral voter-audit export response.
- CSV includes `DiscordUserID` and `DiscordName`.
- `DiscordUserID` remains a full spreadsheet-safe snowflake in Excel/Sheets.
- Governor identity is excluded.
- `VoteChanged` is correct.
- `VoterAuditExported` audit row is written with requester ID and expected metadata.
- Regression tests passed.

Do not regress these behaviours.

## 5. Source Deferred Items

This task promotes the remaining active voting deferred optimisation into an audit/scope slice.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin`, future voting programme phases
- Type: architecture
- Description: Discord Voting Post Framework Phase 4 delivered private voter-level audit export without adding advanced voting modes. Role-restricted voting, anonymous or hidden-until-close results, governor-linked voting, multi-select/survey modes, saved templates, public dashboard reporting, and public voter-level export posting remain outside the delivered Phase 4 scope because each changes permissions, data visibility, SQL contracts, or player expectations.
- Suggested Fix: Prepare an advanced voting modes audit that separately evaluates product need, permission/privacy model, SQL schema changes, command/view UX, migration and rollback plan, and focused tests for each candidate mode before implementation.
- Impact: medium
- Risk: high
- Dependencies: Discord Voting Post Framework Phase 1 through Phase 4 complete; operator approval before any advanced-mode implementation.

Phase 5 should either resolve this deferred item by splitting it into specific approved future
slices, or update the backlog with the exact items that remain deferred after audit.

## 6. Scope

### In Scope

- Audit product value and implementation risk for the original candidate set, then retain only
  operator-approved future scope:
  - hidden-until-close result visibility
  - multi-select or survey-style voting
  - per-option emoji/icon support
  - dashboard/reporting readiness
- Define the safest command shape for any future modes under existing `/vote_admin` where practical.
- Identify SQL schema/index/audit changes each mode would need.
- Identify privacy and permission boundaries for each candidate mode.
- Confirm which future slice should be first, and why.
- Produce future task-pack outlines or backlog entries for each approved remaining slice.
- Update `docs/reference/deferred_optimisations.md` to remove, split, or refine the advanced modes
  deferred item based on the audit result.
- Preserve Phase 1 through Phase 4 behavior and docs.

### Out of Scope

- Implementing hidden/anonymous results.
- Implementing multi-select or survey voting.
- Implementing per-option emoji/icon support.
- Implementing website/dashboard reporting.
- Renaming or removing `/vote_admin`.
- Changing player vote button behavior.
- Changing existing totals-only or voter-audit export behavior.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required for affected layers, command shape, SQL/persistence implications, and slice planning. |
| `k98-discord-command-feature` | use | Candidate modes affect slash commands, buttons, interaction UX, permissions, and response visibility. |
| `k98-sql-validation` | use | Candidate modes likely need SQL schema/index/audit contract decisions. |
| `k98-test-selection` | use | Required to define focused tests for each future implementation slice. |
| `k98-deferred-optimisation-capture` | use | Phase 5 is promoted from an active deferred optimisation and must update the backlog. |
| `k98-pr-review` | use | Use before handoff if the audit edits docs/backlog/task packs. |
| `k98-promotion-check` | use | Use before production promotion if docs are pushed to production branches. |
| `codex-security:security-scan` | conditional | Required for any implementation that touches permissions/privacy/SQL/export files; usually skipped for audit-only docs with explicit justification. |

## 8. Mandatory Workflow

1. Audit current Phase 1 through Phase 4 behavior and SQL contracts.
2. Produce a mode-by-mode decision matrix.
3. Stop for operator approval before creating implementation work.
4. If approved, prepare the next implementation slice task pack only; do not implement in Phase 5.
5. Update deferred optimisation status so no advanced-mode item is lost.

## 9. Audit Requirements

For each candidate mode, answer:

1. What user/operator problem does it solve?
2. Who can create/manage the mode?
3. Who can vote?
4. Who can see interim results?
5. Who can export results or voter-level audit rows?
6. Does the mode change vote cardinality, option shape, identity model, or close semantics?
7. Which SQL tables, columns, indexes, constraints, or audit events are required?
8. Can it reuse existing vote buttons and result cards?
9. What are the manual smoke tests?
10. What automated tests are required?
11. Is this a first implementation candidate, later candidate, or explicit non-goal?

## 10. Likely Files

### Review

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/export_service.py`
- `voting/discord_presentation.py`
- `voting/card_renderer.py`
- `voting/scheduler.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_service.py`
- `tests/test_voting_dal.py`
- `tests/test_voting_export_service.py`
- `tests/test_voting_discord_presentation.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- SQL repo `C:\K98-bot-SQL-Server`

### Modify In Audit Slice

- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/reference/deferred_optimisations.md`
- future task packs or starters created from the audit

### Modify Only In Later Implementation Slices

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/export_service.py`
- `voting/discord_presentation.py`
- `voting/card_renderer.py`
- `voting/scheduler.py`
- focused tests
- SQL repo migrations, if required

## 11. Architecture Requirements

- Keep `/vote_admin` as the preferred admin command group unless a later task explicitly approves a
  new command group.
- Do not add direct SQL to commands or views.
- Keep SQL as the source of truth.
- Keep commands thin and services/DAL responsible for rule enforcement and persistence.
- Preserve restart-safe open vote buttons.
- Preserve private/ephemeral export behavior by default.
- Treat hidden/private results as permission/privacy features, not just UI toggles.
- Keep role-restricted voting, governor-linked voting, saved templates, and public voter-level
  export posting out of active scope unless a future task explicitly re-opens them.

## 12. Testing Requirements For Future Implementation Slices

The Phase 5 audit should define the exact tests for each future slice. Likely categories:

- command registration and option ordering
- permission boundary and denied-user paths
- vote cardinality rules
- hidden/result visibility behavior
- button interaction behavior
- restart-safe view rehydration
- scheduler close/reminder compatibility
- SQL/DAL contract tests
- export and audit regression tests
- result card rendering tests
- manual Discord smoke tests
- Codex Security review for any implementation slice

Baseline validation for the audit/docs slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## 13. Acceptance Criteria

- [ ] Phase 5 produces a mode-by-mode advanced voting audit matrix.
- [ ] No advanced voting mode is implemented without follow-up approval.
- [ ] The first future implementation slice is recommended with rationale.
- [ ] Remaining candidate modes are either assigned to future task packs or explicitly left
      deferred with structured backlog entries.
- [ ] SQL schema/index/audit implications are documented per candidate mode.
- [ ] Privacy and permission boundaries are documented per candidate mode.
- [ ] Phase 1 through Phase 4 behavior remains preserved.
- [ ] Deferred optimisation backlog is updated.
- [ ] Required docs validators pass.

## 14. PR Summary Template

```md
## Summary

- Audited advanced voting-mode candidates after Phase 4 smoke success.
- Split remaining voting work into approved future slices or structured deferred items.
- Preserved Phase 1 through Phase 4 behavior and documentation.

## Tests

- <commands run>

## Risk / Rollback

- Risk: documentation/scope only unless implementation is separately approved.
- Rollback: revert docs/backlog/task-pack changes.
```

## 15. Phase 5 Audit Packet

### Scope Summary

Phase 5 is audit and slice planning only. No runtime Python, SQL migration, Discord command
registration, player vote behavior, export behavior, or `/vote_admin` command shape should change
until the operator approves a follow-up implementation slice.

The current voting framework remains:

- one selected option per Discord user per vote
- public live result card
- admin/leadership create, update, status, close, and private export workflows under `/vote_admin`
- SQL-backed posts, options, votes, reminders, audit rows, scheduler close/reminders, and persistent
  button rehydration
- private totals-only and private voter-level audit CSV exports for one closed vote at a time

### Current Architecture And SQL Contract

Bot ownership is already aligned with the target architecture:

- command surface: `commands/vote_admin_cmds.py`
- business rules: `voting/service.py`
- SQL/DAL: `voting/dal.py`
- exports: `voting/export_service.py`
- Discord presentation/card rendering: `voting/discord_presentation.py`,
  `voting/render_service.py`
- persistent vote buttons: `ui/views/vote_post_view.py`
- scheduler and rehydration: `voting/scheduler.py`, `voting/rehydration.py`

SQL validation against `C:\K98-bot-SQL-Server` confirmed the current authoritative vote migration is
`migrations/20260701_002_add_vote_post_framework.sql`. Current vote tables are:

- `dbo.VotePosts`: post metadata, status, mention flags, open/close timestamps, message IDs, and
  close metadata.
- `dbo.VotePostOptions`: option key, label, sort order, and nullable `ButtonStyle`.
- `dbo.VotePostVotes`: primary key `(VotePostID, DiscordUserID)`, current `OptionID`, nullable
  `GovernorID`, nullable `OriginalOptionID`, and vote timestamps.
- `dbo.VotePostReminders`: reminder offsets, due/claimed/sent timestamps, and reminder message ID.
- `dbo.VotePostAudit`: actor, action type, option IDs, details JSON, and audit timestamp.

Current schema does not include vote mode, result visibility, multi-select selection rows, option
emoji/icon fields, or dashboard/reporting views. `VotePostVotes.GovernorID` exists but is not
currently populated by bot code and was intentionally excluded from Phase 4 voter-audit export;
Phase 5 operator review removed governor-linked voting from active scope.

Operator scope decision after review: do not progress role-restricted voting, governor-linked
voting, saved vote templates, or public voter-level export posting. Those ideas should not be
implemented or kept as active deferred voting work unless they are explicitly re-opened in a new
future task.

### Mode Decision Matrix

| Candidate | Product Value | Permission / Privacy Model | SQL Contract Needs | Command / View UX | Tests And Smoke Plan | Decision |
|---|---|---|---|---|---|---|
| Role-restricted voting | Would limit voting to members with a chosen Discord role. | Not useful for KD98's current goal because leadership is small and the voting framework is meant to broaden public participation. | Would require role restriction SQL, but no SQL shape should be pursued now. | No UX work approved. | No tests or smoke needed unless re-opened later. | Removed from active scope by operator review. |
| Hidden-until-close result visibility | Reduces bandwagon effects and supports public votes where interim totals should not influence voters. | Admin/leadership creates and manages. Players vote publicly through the post, but interim public card hides option totals. Admin status can privately show live totals. Closed result card should reveal publicly unless a later slice explicitly chooses a stricter policy. Exports stay private and closed-only. | Add result visibility to `VotePosts`, for example `ResultVisibility` constrained to `PublicLive` and `HiddenUntilClose`. Existing vote rows can stay unchanged. Audit visibility changes. Consider an index only if visibility becomes a reporting filter. | Add create/update visibility control under `/vote_admin`. Renderer must produce an open hidden-results card and closed normal card. Status should clearly distinguish public hidden state from private admin totals. | Renderer tests for open hidden card and closed reveal, service/DAL mapping tests, status tests, export regression tests, close/scheduler tests. Smoke: open hidden vote shows no totals publicly, votes update without leaking totals, status privately shows totals, close reveals outcome. | Approved safest first implementation slice. |
| Governor-linked voting or governor-aware audit/reporting | Would connect Discord voters to registered game identity. | Not needed for this voting framework; many governors per Discord user adds complexity without enough KD98 value for public votes. | `VotePostVotes.GovernorID` exists but should remain unused by voting until a separate future need is approved. | No UX work approved. | No tests or smoke needed unless re-opened later. | Removed from active scope by operator review. |
| Multi-select or survey-style voting | Supports availability and preference surveys where players can choose every option that works, not only one favorite. | Admin/leadership creates/manages. Voters need private confirmation of all selected choices. Results may be public or hidden depending on result visibility mode. Exports likely need one row per user-option selection or one row per question. | Current `VotePostVotes` stores one `OptionID` per Discord user. Multi-select requires a new mode column plus either `dbo.VotePostVoteSelections` or a redesigned vote table. Need max/min selections, possibly question/group tables for survey mode, and new constraints/indexes. | Buttons alone become awkward for selected/unselected state and persistence. Prefer a select menu or private survey panel rather than overloading current buttons. Existing result card may need grouped bars. | Service cardinality tests, DAL transaction tests, selection toggle tests, export shape tests, renderer tests, restart/view tests, and manual smoke for min/max selections and changes. | Approved high-value future slice; likely second after hidden results. |
| Saved vote templates | Would let admins reuse common vote setups. | Removed because current KD98 value is unclear and vote modes are still settling. | No template SQL should be added now. | No UX work approved. | No tests or smoke needed unless re-opened later. | Removed from active scope by operator review. |
| Per-option emoji/icon support | Improves scanability and polish for small public votes. | Admin/leadership controls emoji/icon values. Players see emoji on buttons/cards. No new voter privacy impact if limited to option presentation. | Current `VotePostOptions` has nullable `ButtonStyle` but no emoji/icon field. Add `EmojiText` or `EmojiID`/`EmojiName` depending on supported scope. Renderer needs Unicode/font validation for card output. | Add optional emoji fields or a guided option-polish panel. Buttons can use Discord emoji support rather than stuffing emoji into labels where possible. Cards need glyph fallback validation. | Validation tests for Unicode/custom emoji format, button construction tests, renderer visual/sample tests, export regression tests. Smoke with Unicode emoji, no emoji, and long labels near the configured limit. | Approved future polish slice. |
| Dashboard/reporting readiness | Enables leadership to review vote participation, outcomes, export history, and trends over time. | Admin/leadership/operator reporting first. Public dashboards should be separate product approval. Voter identity must remain private by default. | Current tables can support basic closed-vote summaries, but durable reporting likely needs views or stored procedures over posts/options/votes/audit. Approved mode columns should be represented as reporting dimensions where practical. | Do not add a website/dashboard in Phase 5. A future slice may add SQL views and private `/vote_admin status` or export summary enhancements first. | SQL view/proc contract tests, export/report shape tests, permissions tests, and smoke for private report generation. | Approved required future slice. |
| Public voter-level export posting policy | Would publicly post who voted for what. | Removed because it undermines broad public participation and current Phase 4 policy keeps voter-level audit private/ephemeral. | No public posting SQL/audit shape should be pursued now. | No UX work approved. | No tests or smoke needed unless re-opened later. | Removed from active scope by operator review. |

### Recommended First Implementation Slice

Recommended first slice: hidden-until-close result visibility.

Rationale:

- It directly supports KD98's public-participation goal while reducing bandwagon effects.
- It preserves the current one-vote-per-Discord-user model, button behavior, scheduler behavior,
  close behavior, and private exports.
- It is lower risk than multi-select/survey because it does not change vote cardinality or export
  row shape.
- It creates a useful visibility setting that later multi-select/survey votes can reuse.
- It has straightforward manual smoke coverage: vote publicly, hide interim totals, reveal at close.

Minimum approved first-slice scope should be:

- admin/leadership create/manage only
- public post remains visible to everyone in the channel, but open hidden-result votes do not show
  option totals or winning state publicly
- admin/leadership status can privately show live totals
- closed vote card and close announcement reveal the outcome publicly
- existing totals-only and voter-audit exports remain private and unchanged
- SQL migration for additive result visibility storage plus audit details
- no role restrictions, governor identity, multi-select, templates, emoji, dashboard, or public
  voter export posting in the same PR

### Future Slice Outlines

1. Phase 6 candidate: hidden-until-close results.
   - SQL: add `ResultVisibility` to `dbo.VotePosts`.
   - Bot: renderer/status/update behavior for hidden open results and revealed closed results.
   - Tests: renderer leak prevention, status private totals, close reveal, export regression.
   - Smoke: open public card hides totals; close reveals winner/tie/no-vote correctly.

2. Phase 7 candidate: multi-select/survey voting.
   - SQL: design vote mode and selection storage, likely `dbo.VotePostVoteSelections` or survey
     question tables.
   - Bot: select-menu or private survey-panel interaction model, min/max selection rules, result
     aggregation, and export shape.
   - Tests: cardinality, DAL transactions, selection updates, export rows, restart/view behavior.
   - Smoke: choose multiple options, change selections, close, and export.

3. Phase 8 candidate: per-option emoji/icon support.
   - SQL: add approved emoji/icon metadata to `dbo.VotePostOptions`.
   - Bot: button emoji support, card rendering, validation, and export regression.
   - Tests: Unicode/custom emoji validation, button construction, renderer visual sample, export
     compatibility.
   - Smoke: emoji and no-emoji votes with labels near the configured limit.

4. Phase 9 candidate: dashboard/reporting readiness.
   - SQL: define private reporting views or procedures for vote summaries, participation, outcomes,
     export/audit history, and approved mode dimensions.
   - Bot: private admin/leadership/operator reporting entry point or export enhancement under
     `/vote_admin`.
   - Tests: SQL/result shape, permission boundaries, report/export format, and smoke validation.

Removed from active voting scope after operator review: role-restricted voting, governor-linked
voting/governor-aware audit, saved vote templates, and public voter-level export posting.

### SQL Validation Verdict

Current Phase 1-4 SQL is adequate for existing behavior and private exports. The current schema is
not adequate to implement the approved future scope for result visibility, multi-select/survey,
emoji/icon metadata, or dashboard reporting views without SQL repo changes. Removed candidates
should not drive SQL migrations.

Recommended SQL deployment posture for future implementation slices:

1. Add nullable or additive tables/columns first.
2. Keep old rows and current bot code compatible.
3. Deploy SQL before bot code when bot code writes new fields.
4. Preserve private export behavior as the rollback baseline.
5. Add new audit events in bot code only after the storage contract is deployed.

### Refactor Triggers

- Direct SQL in command/view layers: not found in the inspected voting command/view path; voting SQL
  is in `voting/dal.py`.
- Business logic in command/view layers: current command/view paths are thin enough for the
  delivered phases. Future hidden-result and multi-select behavior should keep visibility,
  cardinality, and result aggregation rules in service/DAL/rendering layers rather than command or
  view callbacks.
- Fragile restart/persistence: existing open vote buttons are SQL-backed and rehydrated. Future mode
  state must be persisted in SQL so rehydrated buttons enforce the same rules after restart.
- Deferred work: the broad advanced-mode backlog item is split into structured deferred items in
  `docs/reference/deferred_optimisations.md`.

### Test Selection For Future Runtime Slices

Every implementation slice should run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Likely focused pytest files:

- `tests/test_vote_admin_cmds.py`
- `tests/test_vote_post_view.py`
- `tests/test_vote_admin_update_view.py`
- `tests/test_voting_service.py`
- `tests/test_voting_dal.py`
- `tests/test_voting_export_service.py`
- `tests/test_voting_discord_presentation.py`
- `tests/test_voting_render_service.py`
- `tests/test_voting_scheduler.py`
- `tests/test_voting_outcomes.py`

Run a Codex Security review before PR handoff for any runtime implementation because advanced modes
touch Discord interactions, permissions/privacy, user-controlled input, SQL-backed persistence, and
export/report surfaces. For this documentation-only audit slice, the security review can be skipped
with the explicit reason that no runtime code, SQL migration, permission check, export behavior, or
Discord interaction behavior changed.

### Audit Slice Validation

Validation run for this documentation/backlog audit slice:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Result: passed. Runtime pytest was skipped because this slice changed only documentation/backlog
planning files and did not change bot code, SQL, tests, command registration, exports, or Discord
interaction behavior.

### Approval Needed

Operator approval is needed before any follow-up implementation. Specific decisions to approve:

- approval to prepare the hidden-until-close implementation task pack as the next slice
- confirmation that hidden results should reveal publicly at close
- confirmation that multi-select/survey, emoji/icon support, and dashboard/reporting readiness stay
  in future scope
- confirmation that role-restricted voting, governor-linked voting, saved templates, and public
  voter-level export posting are removed from active voting scope
