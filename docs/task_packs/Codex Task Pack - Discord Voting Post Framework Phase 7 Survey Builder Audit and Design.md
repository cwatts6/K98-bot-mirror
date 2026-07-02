# Codex Task Pack - Discord Voting Post Framework Phase 7 Survey Builder Audit and Design

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 7 Survey Builder Audit and Design`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 6 single-question MultiSelect delivery and smoke test`
- Task type: `audit | product scope | SQL-backed survey design | Discord interaction UX | privacy review`
- One-pass approved: `no`
- Status: `prepared - not started`

## 2. Objective

Audit and design the next advanced voting slice: multi-question survey-style voting.

Phase 6 delivered the safest cardinality change first: single-question `MultiSelect` voting under
the existing `/vote_admin` workflow. Phase 7 should decide whether and how to add a broader survey
builder without disturbing the now-smoke-tested vote-post framework.

Start with audit/scope only. Do not implement SQL migrations, survey tables, question builder UI,
response flows, command changes, export changes, dashboard/reporting changes, or new Discord views
until the operator approves the architecture, product scope, privacy, SQL, permissions, and UX
direction.

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
- [ ] Survey shape candidates are compared in a decision matrix.
- [ ] The first survey implementation slice is recommended with rationale.
- [ ] SQL contract options and migration order are documented.
- [ ] Permission/privacy and result-visibility behavior is documented.
- [ ] Command/builder/view UX is documented.
- [ ] Export and audit implications are documented.
- [ ] Automated tests and manual smoke plan are documented.
- [ ] Deferred optimisation backlog is updated so no survey, emoji, reporting, or export work is lost.
- [ ] No runtime voting behavior changes in this audit slice.
- [ ] Required docs validators pass.

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
