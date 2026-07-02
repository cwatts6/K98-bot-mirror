# Codex Task Pack - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 5 hidden-until-close results smoke test`
- Task type: `audit | product scope | SQL-backed voting design | Discord interaction UX`
- One-pass approved: `no`
- Status: `prepared - not started`

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

- [ ] Current vote SQL contract is validated against `C:\K98-bot-SQL-Server`.
- [ ] Multi-select-only and survey-style candidates are compared in a decision matrix.
- [ ] The first implementation slice is recommended with rationale.
- [ ] SQL contract options and migration order are documented.
- [ ] Permission/privacy and result-visibility behavior is documented.
- [ ] Command/view UX is documented.
- [ ] Export and audit implications are documented.
- [ ] Automated tests and manual smoke plan are documented.
- [ ] Deferred optimisation backlog is updated so no survey, emoji, or reporting work is lost.
- [ ] No runtime voting behavior changes in this audit slice.
- [ ] Required docs validators pass.

## 14. PR Summary Template

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
