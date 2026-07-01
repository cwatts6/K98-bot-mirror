# Codex Task Pack - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening`
- Date: `2026-07-01`
- Owner/context: `Follow-up after successful Phase 2 guided admin UX smoke test`
- Task type: `feature | reporting | Discord command workflow | SQL-backed audit`
- One-pass approved: `no`
- Status: `prepared - not started`

## 2. Objective

Add a guided admin workflow for retrieving completed vote results and exporting vote audit data.
Phase 3 should make closed votes easy to find after the Discord message has moved out of view,
provide reviewable result output, and prepare a safe voter-audit export path without changing
player voting behaviour.

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
- SQL repo `C:\K98-bot-SQL-Server` before any query, schema, index, or export contract change.

## 4. Phase 2 Baseline

Phase 2 is complete and smoke tested.

Confirmed behavior:

- `/vote_admin create` uses individual option fields.
- Option 1 and Option 2 are required; Options 3-6 are optional.
- `VOTE_OPTION_LABEL_MAX_LENGTH=20` works for the configured option label limit.
- `/vote_admin status`, `/vote_admin close`, and `/vote_admin update` provide vote lookup choices.
- `/vote_admin update` opens the guided six-choice update panel.
- `/vote_admin close` shows a clear result and disables buttons.
- Open vote buttons still work after bot restart.

Do not regress these behaviours.

## 5. Confirmed Phase 3 Scope

Phase 3 should focus on admin result retrieval and audit export:

- Add a guided `/vote_admin export` subcommand, or an equivalent approved `/vote_admin` reporting
  workflow, for completed vote results.
- Let admins select closed votes by title/autocomplete with VotePostID, status, close time, and
  channel metadata for disambiguation.
- Export final option totals in a reviewable CSV file.
- Include voter-level audit rows only after confirming the permission and privacy model.
- Add an admin-friendly closed-vote history/list lookup if it materially improves export selection.
- Reuse existing SQL-backed vote tables as the source of truth.
- Include close source, close time, total voters, winner/tie/no-vote result, and reminder delivery
  metadata where current SQL data supports it.
- Keep responses private/ephemeral by default.

## 6. Out Of Scope

- Role-restricted voting.
- Anonymous or hidden-results voting.
- Governor-linked voting.
- Multi-select or survey voting.
- Saved vote templates.
- Website/dashboard reporting.
- Public voter-level export posting.
- Renaming or removing `/vote_admin`.
- Editing vote options after votes exist.
- Changing player vote button behaviour.

## 7. Audit/Scope Requirements

Start with audit/scope only and stop for approval before implementation.

The audit must confirm:

1. Whether `/vote_admin export` is the best command shape or whether export should be reached from
   status/history controls.
2. Whether voter-level export is allowed for admin/leadership users or should be totals-only in the
   first implementation.
3. Whether closed-vote lookup can use existing DAL queries efficiently or needs a new query/index.
4. Whether export should support only one vote at a time or a date/status-filtered batch.
5. Whether CSV is enough for Phase 3 or whether embed-only summary output should also be included.
6. Which SQL objects and columns from `C:\K98-bot-SQL-Server` are authoritative for vote posts,
   options, votes, reminders, and audit events.
7. The exact test plan before code changes.

## 8. Likely Files

### Review

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/discord_presentation.py`
- `voting/scheduler.py`
- `ui/views/vote_admin_update_view.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_service.py`
- `tests/test_voting_discord_presentation.py`
- `tests/test_voting_scheduler.py`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

### Likely Modify

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/discord_presentation.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_service.py`
- `tests/test_voting_discord_presentation.py`
- `docs/reference/canonical_command_reference.md`

### Create If Needed

- `voting/export_service.py`
- `tests/test_voting_export_service.py`
- Export/history select or modal tests if a guided view is added.
- SQL repo migration only if audit proves current schema/query shape is insufficient.

## 9. Architecture Requirements

- Commands stay thin and collect Discord-facing inputs.
- Services own export validation, vote selection rules, privacy decisions, and output shaping.
- DAL owns SQL queries and row mapping.
- Export generation must avoid direct SQL in commands or views.
- Keep UTC persistence and display UTC clearly.
- Preserve restart safety for open votes and scheduler state.
- Keep export responses private unless explicitly approved otherwise.
- Avoid adding new top-level commands.

## 10. Testing Requirements

Add or update tests for:

- export command registration and required/optional option ordering
- closed vote autocomplete or selection metadata
- duplicate title disambiguation
- totals-only CSV output
- voter-level export permission/privacy decision if included
- zero-vote, tie, and winner export summaries
- closed-only export rules or explicit open-vote handling
- missing/deleted original message handling where relevant
- no repeated `@everyone` pings
- no player vote behaviour regression

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_vote_admin_cmds.py tests/test_voting_service.py tests/test_voting_discord_presentation.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

Run Codex Security review before PR handoff because Phase 3 touches Discord interactions,
permissions/privacy, user-controlled export selection, SQL-backed persistence, and generated file
output.

## 11. Manual Discord Smoke Test

After implementation:

1. Close at least one vote with a winner.
2. Close at least one tied vote.
3. Close at least one zero-vote vote.
4. Use the guided lookup to select each closed vote without entering a raw VotePostID.
5. Export totals and confirm the file contents match the public result card.
6. If voter-level export is approved, confirm only permitted users can receive it.
7. Confirm export responses are private by default.
8. Confirm open vote buttons and restart-safe voting still work.
9. Confirm no broad mention is sent during export/history lookup.

## 12. Acceptance Criteria

- [ ] Phase 3 begins with audit/scope and approval before implementation.
- [ ] Admins can find closed votes without raw SQL or scrolling Discord history.
- [ ] Export selection is guided and disambiguates duplicate titles.
- [ ] Final option totals export correctly.
- [ ] Winner, tie, and no-vote outcomes are represented in export output.
- [ ] Voter-level export is either safely permissioned or intentionally deferred.
- [ ] Existing Phase 1 and Phase 2 voting behaviour is preserved.
- [ ] SQL assumptions are validated against `C:\K98-bot-SQL-Server`.
- [ ] Command registration validation passes.
- [ ] Focused and broad tests pass or skips are justified.
- [ ] Codex Security review is run or explicitly justified if skipped.

## 13. PR Summary Template

```md
## Summary

- Added guided closed-vote lookup/export for vote results.
- Added CSV result output for completed votes.
- Preserved existing vote creation, voting, close, scheduler, and restart behavior.

## Tests

- <commands run>

## Manual Smoke

- <Discord smoke summary>

## Risk / Rollback

- Risk: Generated export output and voter-audit privacy decisions.
- Rollback: revert bot PR; SQL schema unchanged unless explicitly included by implementation.
```
