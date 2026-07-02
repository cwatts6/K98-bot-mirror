# Discord Voting Post Framework - Programme Pack

> Living programme pack for SQL-backed, button-driven Discord vote posts with live Pillow result
> cards, restart-safe scheduling, and guided admin/player workflows.

## 1. Programme Header

- Programme name: `Discord Voting Post Framework`
- Date: `2026-07-01`
- Owner/context: `KD98 Discord bot / leadership and admin voting workflow`
- Programme type: `Product UX | Discord command architecture | SQL/data | visual output | operations`
- One-pass approved: `no`
- Current status: `Phase 1 complete; Phase 2 complete; Phase 3 complete; Phase 4 complete and smoke tested; Phase 5 prepared`
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
than creating a separate command. Phase 5 should keep using `/vote_admin` unless a later task pack
explicitly approves a different command shape.

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
- Excluded governor names and `GovernorID`; governor-linked voting remains deferred.
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

### Phase 5 - Advanced Voting Modes Audit and Slice Planning

Status: prepared.

Deliver audit/scope before implementation. Phase 5 should produce a mode-by-mode decision matrix
and split the remaining candidate modes into safe implementation slices for:

- Role-restricted voting.
- Hidden-until-close or private result visibility.
- Governor-linked voting or governor-aware audit/reporting.
- Multi-select or survey-style vote modes.
- Per-option emoji/icon support.
- Saved templates for recurring vote types.
- Dashboard/reporting readiness.
- Public voter-level export posting policy.

Do not implement advanced voting modes until the Phase 5 audit approves their product, privacy,
permission, SQL, and UX model and the operator approves a follow-up implementation slice.

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

Phase 5 should audit role restrictions, hidden/anonymous result rules, governor-linked identity,
multi-select/survey semantics, templates, and optional emoji/icon support separately before any
mode is implemented. Each mode may require SQL contract changes, permission/privacy design,
command/view UX, migration/rollback planning, focused tests, manual Discord smoke tests, and
Codex Security review if implementation follows.

Phase 5 must decide:

- which mode, if any, is the safest first implementation slice
- which modes remain explicitly deferred
- which SQL/schema/index/audit changes each future slice needs
- whether existing `/vote_admin` paths remain sufficient
- what manual smoke evidence and automated tests are required per future slice

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
- Do not add advanced voting modes until Phase 5 explicitly approves their product, privacy,
  permissions, SQL, UX, test, and rollout model.

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

## 12. Suggested Next Action

```text
Start Phase 5 Advanced Voting Modes Audit and Slice Planning with audit/scope only.
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
