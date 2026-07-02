# Codex Task Pack - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 4 voter-level audit export smoke test`
- Task type: `audit | product scope | Discord command workflow | SQL-backed voting design`
- One-pass approved: `no`
- Status: `ready`

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

- Audit product value and implementation risk for:
  - role-restricted voting
  - hidden-until-close or private result visibility
  - governor-linked voting or governor-aware audit/reporting
  - multi-select or survey-style voting
  - saved vote templates
  - per-option emoji/icon support
  - dashboard/reporting readiness
  - public voter-level export posting policy
- Define the safest command shape for any future modes under existing `/vote_admin` where practical.
- Identify SQL schema/index/audit changes each mode would need.
- Identify privacy and permission boundaries for each candidate mode.
- Confirm which future slice should be first, and why.
- Produce future task-pack outlines or backlog entries for each approved remaining slice.
- Update `docs/reference/deferred_optimisations.md` to remove, split, or refine the advanced modes
  deferred item based on the audit result.
- Preserve Phase 1 through Phase 4 behavior and docs.

### Out of Scope

- Implementing role-restricted voting.
- Implementing hidden/anonymous results.
- Implementing governor-linked voting.
- Implementing multi-select or survey voting.
- Implementing templates.
- Implementing website/dashboard reporting.
- Publicly posting voter-level exports.
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
- Treat hidden/private results and role-restricted voting as permission/privacy features, not just
  UI toggles.
- Treat governor-linked voting as an identity-model feature that may require registry review and
  SQL design.

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
