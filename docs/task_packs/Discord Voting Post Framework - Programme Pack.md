# Discord Voting Post Framework - Programme Pack

> Living programme pack for SQL-backed, button-driven Discord vote posts with live Pillow result
> cards, restart-safe scheduling, and guided admin/player workflows.

## 1. Programme Header

- Programme name: `Discord Voting Post Framework`
- Date: `2026-07-01`
- Owner/context: `KD98 Discord bot / leadership and admin voting workflow`
- Programme type: `Product UX | Discord command architecture | SQL/data | visual output | operations`
- One-pass approved: `no`
- Current status: `Phase 1 complete; Phase 2 prepared`
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

## 4. Current Product Feedback

Phase 1 works, but smoke testing showed the admin UX needs a guided second phase.

Feedback to preserve:

- Pipe-separated `options` input is clunky and error-prone.
- Option character limits are discovered too late, after the admin has already filled the command.
- Creation should use individual option fields:
  - `Option 1` required
  - `Option 2` required
  - `Option 3` optional
  - `Option 4` optional
  - `Option 5` optional
  - `Option 6` optional
- Option count should increase to a maximum of 6.
- Character limits should be enforced while filling fields where Discord supports this, not only
  after submit.
- `closes_at_utc` as free-text UTC is hard to fill in and should become selector-guided.
- Result bars should become vertical rather than horizontal.
- `/vote_admin update`, `/vote_admin status`, and `/vote_admin close` should not require admins to
  know a raw VotePostID.
- Admin vote selection should use a vote title dropdown or autocomplete selector, with IDs shown
  only as disambiguating metadata.
- `/vote_admin update` with every field optional is confusing; it should guide the admin toward one
  explicit change or a clearer edit flow.
- `/vote_admin status` is good and should be preserved while improving vote selection.
- `/vote_admin close` works, but close output should show the winner clearly.
- Automatic close should also show the winner clearly.
- The final card and close announcement should make the winning option or tie state obvious.

## 5. Target Model

### Current command model

```text
/vote_admin create
/vote_admin update
/vote_admin close
/vote_admin status
```

Phase 1 intentionally used `/vote_admin` as the approved command group.

### Phase 2 target command model

Keep the existing command group and improve the command UX:

```text
/vote_admin create
/vote_admin update
/vote_admin close
/vote_admin status
```

Phase 2 should avoid adding a new top-level command. It may add autocomplete, option fields,
modals, buttons, or selects behind the existing group.

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

Status: prepared.

Deliver:

- Replace pipe-separated create options with individual fields:
  - `option_1` required
  - `option_2` required
  - `option_3` optional
  - `option_4` optional
  - `option_5` optional
  - `option_6` optional
- Raise maximum supported options from 5 to 6 if Discord button layout and card layout remain
  clear.
- Add Discord-supported option length limits where possible so admins get feedback while filling
  the command.
- Keep service-side SQL/card/button validation as the final authority.
- Replace raw UTC close text with a guided close-time flow using the best viable Discord pattern:
  autocomplete, preset choices, select menus, modal fields, or a staged confirm flow.
- Add vote-title autocomplete/select support for update, status, and close so admins do not need
  raw VotePostID values.
- Rework update UX so admins explicitly choose what to change or use a clearer guided edit flow.
- Preserve the useful status output while adding easier vote selection.
- Redesign result card bars from horizontal to vertical.
- Highlight the winner or tie state on final/closed cards.
- Include winner/tie summary in both manual-close and automatic-close announcements.
- Preserve restart safety, SQL source of truth, no broad ping on vote updates, and backend
  validation.

### Phase 3 - Admin Export and Audit Hardening

Status: future candidate.

Deliver:

- Export command for results and voter audit.
- Admin-friendly closed vote summaries.
- Richer audit/status inspection for reminders, close source, and operational failures.
- Permission review for voter identity export.
- Optional CSV and/or embed summary output.

### Phase 4 - Advanced Voting Modes

Status: future candidate.

Deliver:

- Role-restricted voting.
- Governor-linked voting mode.
- Private or hidden-until-close results.
- Multi-select or survey-style vote modes.
- Per-option emoji/icon support.
- Saved templates for recurring vote types.

## 8. Phase 2 Scope Summary

Phase 2 is a UX polish and guided-admin workflow phase. It should not add export, role-restricted
voting, anonymous voting, templates, or survey builder functionality.

Affected areas:

- `commands/vote_admin_cmds.py`
- `voting/service.py`
- `voting/dal.py`
- `voting/models.py`
- `voting/discord_presentation.py`
- `voting/render_service.py`
- `voting/scheduler.py`
- `ui/views/vote_post_view.py`
- `tests/test_vote_admin_cmds.py`
- `tests/test_voting_service.py`
- `tests/test_voting_render_service.py`
- `tests/test_voting_scheduler.py`
- SQL repo only if option count, title lookup, or result-summary needs cannot be satisfied by
  current tables and queries.

## 9. Cross-Programme Constraints

- Do not add another top-level command for Phase 2.
- Keep `/vote_admin` command registration valid: required options must precede optional options.
- Do not rely on Discord UI limits alone; service validation must remain authoritative.
- Validate any SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Preserve all Phase 1 smoke-tested behavior.
- Do not introduce repeated `@everyone` pings on vote updates.
- Preserve persistent view restart behavior and scheduler idempotency.
- Do not edit vote options after votes exist unless the task explicitly defines safe rules.

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
- [ ] Admin creation is guided and avoids pipe-separated option syntax.
- [ ] Admin close time input is guided.
- [ ] Admin update/status/close do not require raw VotePostID lookup.
- [ ] Closed votes visibly highlight the winner or tie state.
- [ ] Result cards meet the vertical-bar visual direction.
- [ ] Export/audit workflow is delivered or intentionally deferred to Phase 3.

## 12. Suggested Next Action

```text
Start Discord Voting Post Framework Phase 2: Guided Admin UX and Results Polish using the
prepared task pack and chat starter.
```

## 13. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| 2026-07-01 | Initial programme pack created | Captured SQL-backed live voting, buttons, Pillow card, reminders, and close handling. |
| 2026-07-01 | Phase 1 marked complete | SQL deployed, bot smoke test successful, mirror/prod review fixes completed. |
| 2026-07-01 | Phase 2 scope prepared | Preserved smoke-test feedback for guided create UX, vote selectors, vertical bars, and winner callout. |
