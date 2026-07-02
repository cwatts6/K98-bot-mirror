# Codex Task Pack - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls`
- Date: `2026-07-02`
- Owner/context: `Follow-up after successful Phase 3 totals-only export smoke test`
- Task type: `audit | privacy | Discord command workflow | SQL-backed export`
- One-pass approved: `no`
- Status: `implemented`

## 2. Objective

Decide and, only after approval, implement the safe path for voter-level audit export for completed
Discord vote posts.

Phase 3 delivered private totals-only CSV export for one closed vote at a time. It intentionally
deferred voter-level audit export because that changes the privacy and permission boundary. Phase 4
resolved that decision without changing player voting behavior or adding advanced voting modes.

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
- SQL repo `C:\K98-bot-SQL-Server` before any query, schema, index, or audit/export contract
  change.

## 4. Delivered Baseline

Phase 1, Phase 2, and Phase 3 are complete and smoke tested.

Confirmed Phase 3 behavior:

- `/vote_admin export` exists under the existing `/vote_admin` command group.
- Closed votes can be selected by autocomplete.
- One completed vote exports at a time.
- CSV output is totals-only.
- Export response is private/ephemeral by default.
- CSV includes final option totals, percentages, outcome kind/summary, close metadata, message
  link, reminder metadata, and numeric `IsWinningOption` values.
- Existing open-vote buttons work after restart and deployment.
- No SQL migration was required.

Do not regress these behaviours.

## 5. Confirmed Phase 4 Scope

Start with audit/scope only and stop for approval before implementation.

Phase 4 should decide:

1. Whether voter-level export is allowed at all.
2. Which users may receive it: admin, leadership, a narrower configured role, or nobody yet.
3. Which voter fields are safe to export.
4. Whether Discord user IDs are sufficient or whether display names, governor links, or other
   identity enrichment must be deferred.
5. Whether the export path should be a new option on `/vote_admin export`, a separate
   `/vote_admin audit_export` subcommand, or a guided mode selector behind the existing export path.
6. Whether export delivery remains ephemeral-only or needs an explicit no-public-posting guard.
7. Whether export generation should log an audit event in SQL or only structured bot logs.
8. Whether current SQL tables and indexes support the lookup/export efficiently.

Approved implementation included:

- Voter-level CSV export for one closed vote at a time.
- Private/ephemeral delivery only.
- Admin/leadership permission gate matching the existing `/vote_admin` workflow.
- Discord user ID and resolved Discord name, with governor identity excluded.
- CSV formula escaping for all text fields.
- Tests for permission, privacy, closed-only behavior, field shape, and no totals-export regression.

## 6. Out Of Scope

- Role-restricted voting.
- Anonymous or hidden-results voting.
- Governor-linked voting implementation.
- Multi-select or survey voting.
- Saved vote templates.
- Website/dashboard reporting.
- Public voter-level export posting.
- Renaming or removing `/vote_admin`.
- Changing player vote button behavior.
- Batch/date-filtered exports unless separately approved.

## 7. Deferred Optimisations This Slice Addresses

This slice is expected to resolve or update:

### Deferred Optimisation
- Area: `voting/export_service.py`, `/vote_admin export`, SQL vote/audit tables
- Type: architecture
- Description: Phase 3 delivered totals-only closed-vote CSV export and intentionally deferred voter-level audit export because it exposes individual Discord voter identifiers and changes the privacy/permission model.
- Suggested Fix: Phase 4 should decide the privacy model, allowed recipients, exported fields, audit logging behavior, and SQL query shape before any implementation. If approved, implement a private closed-vote voter audit export with focused permission/privacy tests; otherwise document the continued deferral and keep totals-only export unchanged.
- Impact: high
- Risk: high
- Dependencies: Phase 3 totals-only export delivered and smoke tested; SQL validation in `C:\K98-bot-SQL-Server`; operator approval before implementation.

This slice must not resolve the broader advanced voting modes backlog. Role restriction, hidden
results, governor-linked voting, multi-select/survey modes, templates, and dashboard reporting
remain later slices.

## 8. Likely Files

### Review

- `commands/vote_admin_cmds.py`
- `voting/export_service.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/discord_presentation.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_export_service.py`
- `tests/test_voting_dal.py`
- `tests/test_voting_service.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

### Likely Modify If Approved

- `commands/vote_admin_cmds.py`
- `voting/export_service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/service.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_export_service.py`
- `tests/test_voting_dal.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

### SQL Repo Only If Needed

- New SQL migration only if current `VotePostVotes`, `VotePosts`, `VotePostOptions`,
  `VotePostAudit`, or index contracts cannot support the approved audit export safely.

## 9. Architecture Requirements

- Commands stay thin and own only Discord-facing interaction, validation handoff, permissions,
  deferral, and response rendering.
- Services/export helpers own privacy decisions, export shape, formula escaping, and output
  construction.
- DAL owns SQL query execution and row mapping.
- Do not add direct SQL to commands or views.
- Keep export responses private/ephemeral by default.
- Keep SQL as source of truth.
- Do not change totals-only export behavior except where required to add a clearly separated audit
  mode.

## 10. Audit/Scope Requirements

The audit packet must answer:

1. Is voter-level audit export allowed now?
2. Who can request it?
3. Which columns are allowed, redacted, or explicitly excluded?
4. Should the export include Discord user ID only, or names/governor identity?
5. Does the export need a SQL audit event?
6. Does the SQL repo already expose all needed objects/columns?
7. Is a new query/index needed?
8. Which command shape is safest and most discoverable?
9. What tests are required before implementation?

Stop after the audit/scope packet for approval.

## 11. Testing Requirements If Implementation Is Approved

Add or update tests for:

- command registration and option ordering
- permission boundary for audit export
- denied user path
- closed-vote-only audit export
- no voter-level export for open votes
- CSV field shape and formula escaping
- zero-vote, tie, and winner compatibility
- totals-only export regression
- DAL parameterization and result mapping
- no public posting path

Expected validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_vote_admin_cmds.py tests/test_voting_export_service.py tests/test_voting_dal.py tests/test_voting_service.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run Codex Security review before PR handoff because this slice touches Discord interactions,
permissions/privacy, SQL/data access, generated files, and user-controlled selection.

## 12. Manual Discord Smoke Test If Implemented

1. Use an authorized user to export voter audit rows for a closed vote.
2. Confirm the response is private/ephemeral.
3. Confirm the CSV includes only approved voter/audit columns.
4. Confirm totals-only export still works and remains unchanged.
5. Confirm an unauthorized user cannot receive voter-level export.
6. Confirm an open vote cannot be exported as voter-level audit.
7. Confirm no public channel message or broad mention is sent.
8. Confirm existing open vote buttons still work after restart.

## 13. Acceptance Criteria

- [ ] Phase 4 begins with audit/scope and approval before implementation.
- [ ] Voter-level audit export is either approved with a concrete privacy model or explicitly
      deferred again with rationale.
- [ ] The approved command shape does not add a new top-level command.
- [ ] Export output remains private/ephemeral by default.
- [ ] Current totals-only export remains available.
- [ ] SQL assumptions are validated against `C:\K98-bot-SQL-Server`.
- [ ] Deferred optimisation backlog is updated to show what was resolved, promoted, or still
      deferred.
- [ ] Focused and broad tests pass if implementation is approved.
- [ ] Codex Security review is run or explicitly justified if skipped.

## 14. PR Summary Template

```md
## Summary

- Audited voter-level audit export privacy and permission model.
- <Implemented or deferred voter-level export decision.>
- Preserved totals-only `/vote_admin export` behavior.

## Tests

- <commands run>

## Manual Smoke

- <Discord smoke summary>

## Risk / Rollback

- Risk: voter identifier privacy and generated export files.
- Rollback: revert bot PR; SQL rollback only required if a migration was included.
```
