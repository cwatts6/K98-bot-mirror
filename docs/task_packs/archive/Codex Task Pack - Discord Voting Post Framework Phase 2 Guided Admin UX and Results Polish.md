# Codex Task Pack - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish`
- Date: `2026-07-01`
- Owner/context: `Follow-up after successful Phase 1 SQL-backed voting smoke test`
- Task type: `feature | UX polish | Discord command workflow | visual output`
- One-pass approved: `no`
- Status: `complete - archived`

## 2. Objective

Make Phase 1 voting simple, guided, and visually clearer. Replace clunky admin inputs with
Discord-friendly guided controls, remove the need to know raw VotePostID values, improve the result
card visual layout, and make final winners obvious on both manual and automatic close.

Phase 2 should preserve the working SQL-backed Phase 1 behavior while improving the admin and
player-facing experience.

Completion note: Phase 2 was delivered through mirror PR `cwatts6/K98-bot-mirror#194` and
production PR `cwatts6/k98-bot#502`. Operator smoke testing on 2026-07-01 confirmed guided create,
configurable 20-character option labels, autocomplete vote lookup for status/update/close, the
guided update follow-up menu, clear manual close results, disabled buttons after close, and
restart-safe open vote buttons.

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
- `docs/task_packs/Discord Voting Post Framework - Programme Pack.md`
- `docs/reference/deferred_optimisations.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` before production promotion.
- SQL repo `C:\K98-bot-SQL-Server` if any SQL-facing query, table, index, or schema contract
  changes are needed.

## 4. Phase 1 Baseline

Phase 1 is complete and smoke tested.

Confirmed behavior:

- Vote creation works.
- Voting buttons work.
- Vote changes record correctly.
- SQL records reflect vote created, vote recorded, and vote changed.
- `@everyone` launch behavior works as configured.
- Manual close works.
- Timer close works.
- Buttons disable after close.
- Persistent restart-safe voting and scheduler behavior were implemented.

Do not regress these behaviors.

## 5. User Feedback To Preserve

Smoke-test feedback that must not be lost:

- `options` is too clunky as a pipe-separated string.
- Option character limits are applied too late; failing after filling the whole command is annoying.
- Creation should use one field per option:
  - `option_1` mandatory
  - `option_2` mandatory
  - `option_3` optional
  - `option_4` optional
  - `option_5` optional
  - `option_6` optional
- Maximum options should become 6.
- Where Discord supports it, character limits should be enforced while the field is being filled.
- `closes_at_utc` as free text is hard to fill in and should become selector-guided.
- Vote bars should be vertical rather than horizontal.
- `/vote_admin update`, `/vote_admin status`, and `/vote_admin close` should not require admins to
  know the raw VoteID.
- Vote selection should be by vote title dropdown/autocomplete, with ID shown only as
  disambiguating metadata.
- `/vote_admin update` having all optional fields is confusing; admins should choose what they are
  updating or use a guided edit flow.
- `/vote_admin status` looks good and should be preserved.
- `/vote_admin close` works, but closing should show what the winner was.
- Automatic timer close should also show what the winner was.
- Overall product direction: make it simple, make it guided, and make it look great.

## 6. In Scope

### Create UX

- Replace pipe-separated `options` with individual slash-command options or an equivalent guided
  modal/select flow.
- Require `option_1` and `option_2`.
- Allow `option_3` through `option_6` as optional.
- Validate uniqueness after trimming/case folding.
- Preserve service-side option validation.
- Use Discord option `max_length` where supported by the installed Pycord version.
- Keep command option ordering valid for Discord sync: all required options before optional options.
- Add regression coverage for required-before-optional ordering if command signature changes.

### Close Time UX

- Replace or supplement free-text `closes_at_utc` with a guided close-time flow.
- Evaluate the safest Discord UX pattern before implementation:
  - autocomplete presets,
  - preset duration choices,
  - date plus hour/minute modal,
  - staged selector flow,
  - or another pattern supported by the installed Discord library.
- Keep UTC persistence.
- Display UTC clearly in the resulting embed/card.
- Reject past close times in the service.

### Vote Selection UX

- Add admin-friendly vote lookup for `update`, `status`, and `close`.
- Prefer autocomplete or select-style lookup by vote title.
- Show enough metadata to disambiguate duplicate titles:
  - VotePostID
  - status
  - close time
  - channel, if useful
- Ensure backend still receives and validates a durable vote identifier.
- Do not rely only on title as a unique key.

### Update UX

- Make update flow less confusing than "all fields optional".
- Preferred patterns to evaluate:
  - explicit `field` selector plus `value`,
  - button/select-driven edit menu,
  - targeted subcommands,
  - modal for title/description/deadline edits.
- Preserve safe update rules from Phase 1.
- Do not allow unsafe option editing after votes exist unless separately approved.

### Result Card Polish

- Convert option bars from horizontal to vertical if the layout remains readable for 2-6 options.
- Preserve title, description, status, close time, total votes, last updated timestamp, and vote ID.
- Preserve zero-vote and multi-option handling.
- Add final winner/tie treatment for closed votes.
- Make the winning option visually obvious on the card.
- Preserve mobile readability.

### Close Output

- Manual close should include a winner/tie summary.
- Automatic close should include a winner/tie summary.
- The close embed and final card should not require players to infer the winner from raw bars.
- Tie cases must be explicit.
- Zero-vote close should be explicit, for example "No votes were cast."

## 7. Out of Scope

- Export command and voter audit export. Keep for Phase 3.
- Role-restricted voting.
- Anonymous or hidden-results voting.
- Governor-linked voting.
- Multi-select or survey voting.
- Saved templates.
- Website dashboard/reporting.
- Removing or renaming `/vote_admin`.
- Editing option labels after votes exist unless a safe, separately approved rule is added.
- SQL schema changes unless the implementation cannot meet Phase 2 requirements with current
  tables and indexed queries.

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to confirm command, view, service, DAL, render, scheduler, and SQL impact. |
| `k98-discord-command-feature` | use | Slash command options, autocomplete/select/modal UX, embeds/cards, and close announcements are central. |
| `k98-sql-validation` | use if needed | Use if vote lookup, option count, winner summary, or query performance requires SQL contract changes or new queries. |
| `k98-test-selection` | use | Select focused voting tests plus command registration and full-suite needs. |
| `k98-deferred-optimisation-capture` | use | Capture any advanced modes/export/template ideas found during audit. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | use | Required before production promotion. |
| `codex-security:security-scan` | use | Discord interactions, permissions, user input, SQL-backed persistence, and scheduled close behavior are security-sensitive. |

## 9. Mandatory Workflow

Start with audit/scope only and stop for approval before implementation.

The audit must confirm:

1. Whether the installed Pycord version supports slash option `max_length` for string options.
2. Whether autocomplete is viable for vote-title selection in the current command pattern.
3. Whether close-time selector UX should be slash choices, autocomplete, select/menu, modal, or a
   staged flow.
4. Whether six buttons fit the current persistent view and Discord layout safely.
5. Whether six vertical bars fit the current card dimensions.
6. Whether any SQL query/index changes are needed for vote lookup by title/status.
7. The exact test plan before code changes.

## 10. Likely Files

### Review

- `commands/vote_admin_cmds.py`
- `ui/views/vote_post_view.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/discord_presentation.py`
- `voting/render_service.py`
- `voting/scheduler.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_vote_post_view.py`
- `tests/test_voting_service.py`
- `tests/test_voting_render_service.py`
- `tests/test_voting_scheduler.py`
- `scripts/validate_command_registration.py`
- `docs/reference/canonical_command_reference.md`

### Likely Modify

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/discord_presentation.py`
- `voting/render_service.py`
- `voting/scheduler.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_service.py`
- `tests/test_voting_render_service.py`
- `tests/test_voting_scheduler.py`
- `docs/reference/canonical_command_reference.md`

### Create If Needed

- Additional admin workflow view/modal tests.
- A small helper/service for winner/tie summary if it materially simplifies close/card rendering.
- SQL repo migration/schema updates only if audit proves current schema/query shape is insufficient.

## 11. Architecture Requirements

- Commands stay thin and collect Discord-facing inputs.
- Services own validation, option normalization, close-time parsing, winner/tie calculation, and
  update rules.
- DAL owns SQL queries and snapshot loading.
- Render service owns visual layout.
- Scheduler uses service/renderer output and does not duplicate winner logic.
- No direct SQL in commands or views.
- Persist UTC only.
- Preserve restart safety.
- Preserve mention safety.

## 12. Testing Requirements

Add or update tests for:

- create command required options before optional options
- individual option fields normalize to service options
- optional option gaps are rejected or normalized by a clear rule
- six-option max behavior
- option label length validation and/or Discord max-length metadata if supported
- duplicate option rejection
- close-time guided parser/selector behavior
- vote-title lookup/autocomplete returns useful choices
- duplicate titles remain disambiguated by ID/status/close time
- update flow requires an explicit change target or produces clear guidance
- vertical result card renders 2, 5, and 6 options
- closed card winner highlight
- tie state
- zero-vote closed state
- manual close winner announcement
- automatic close winner announcement
- no broad mentions on vote update edits
- command registration validation

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_vote_admin_cmds.py tests/test_voting_service.py tests/test_voting_render_service.py tests/test_voting_scheduler.py tests/test_vote_post_view.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 13. Manual Discord Smoke Test

After implementation:

1. Create a vote using individual option fields with only two options.
2. Create a vote using six options.
3. Try too-long option labels and confirm the admin gets early/clear feedback.
4. Create a vote using the new guided close-time flow.
5. Vote as one player and change vote.
6. Confirm SQL still has one row per Discord user per vote.
7. Use status lookup by vote title rather than raw VotePostID.
8. Use update lookup by vote title and make one explicit update.
9. Use close lookup by vote title and close manually.
10. Confirm manual close announcement and card show the winner/tie/no-vote state clearly.
11. Let a vote close automatically and confirm the winner/tie/no-vote state is clear.
12. Confirm no repeated `@everyone` ping on vote updates.
13. Restart during an open vote and confirm buttons and scheduler continue working.

## 14. Acceptance Criteria

- [x] Admins no longer need pipe-separated option input.
- [x] Option 1 and Option 2 are required; Options 3-6 are optional.
- [x] Maximum option count is 6, or audit documents why 6 is unsafe and preserves a smaller limit.
- [x] Option label limits are enforced as early as Discord supports and again in service validation.
- [x] Close-time input is guided and less error-prone than raw UTC free text.
- [x] Update/status/close can select votes by title/autocomplete/dropdown-style lookup.
- [x] Raw VotePostID remains available as metadata but is not the main admin burden.
- [x] Update UX clearly requires or guides a specific change.
- [x] Result card uses vertical bars or audit-approved visual equivalent.
- [x] Closed votes show winner, tie, or no-vote outcome clearly.
- [x] Manual and automatic close announcements include winner/tie/no-vote summary.
- [x] Phase 1 SQL-backed voting, reminder, close, restart, and mention safety behavior is preserved.
- [x] Command registration validation passes.
- [x] Focused and broad tests pass or skips are justified.
- [x] Codex Security review is run or explicitly justified if skipped.

## 15. PR Summary Template

```md
## Summary

- Reworked vote creation into guided option fields and close-time UX.
- Added vote-title lookup for admin status/update/close flows.
- Polished closed vote output with winner/tie summaries and vertical result-card bars.

## Tests

- <commands run>

## Manual Smoke

- <Discord smoke summary>

## Risk / Rollback

- Risk: Discord command option/schema changes and voting card layout changes.
- Rollback: revert bot PR; SQL schema unchanged unless explicitly included by implementation.
```
