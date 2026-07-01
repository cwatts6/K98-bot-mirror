# Codex Task Pack — Discord Voting Post Framework Phase 1 SQL-Backed Live Voting

> First implementation task pack for building the MVP of the K98 Discord voting post framework.

## 1. Task Header

- Task name: `Discord Voting Post Framework Phase 1 — SQL-Backed Live Voting`
- Date: `2026-07-01`
- Owner/context: `KD98 Discord bot / admin-created voting posts with live Pillow result card`
- Task type: `feature`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`. Do not add every reference document to the task pack by default.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

Also inspect current examples for:

- persistent Discord views/buttons that survive restart
- admin command grouping and permission decorators
- background scheduler loops/tasks
- Pillow card generation and asset loading
- SQL DAL/repository patterns
- command registration validation expectations
- deployment/promotion guidance for SQL and bot changes

## 3. Objective

Build the first working version of a SQL-backed Discord voting post framework. Admins must be able to create a vote with buttons, a close date/time, configured reminder behaviour, and a live Pillow-generated result card. Players must be able to vote once per Discord user, optionally change their vote before close, and see the original vote post update without any repeated `@everyone` pings.

The system must be robust: SQL is the source of truth, persistent button views survive restart, a scheduler posts reminders and closes votes automatically, buttons are disabled after close, and backend validation rejects late votes.

## 4. Background

The requested feature is a premium replacement for simple Discord polls/reaction voting. Required behaviour discussed and approved for inclusion:

- Discord embed/message with voting buttons.
- Pillow-generated live results image/card with counts, percentages, and progress bars.
- One vote per Discord user.
- Prefer vote changes allowed until close, implemented as update of the existing vote row.
- Vote end date/time setting.
- Automatic lock at close time.
- Disable buttons after close.
- Optional reminder post before close, such as closing in X hours.
- Launch post may include `@everyone`.
- Reminder post may include `@everyone`.
- Closing post may include `@everyone`.
- Vote-result updates after individual votes must not include `@everyone`.
- Admin controls to create, update, close early, and eventually status/export.
- All voting records and operational state must be SQL-backed.
- A background asset will be supplied before build and used for the Pillow card.

This task is Phase 1 and should deliver the live voting MVP plus the foundations needed for later admin-management/export enhancements.

## 5. Scope

### In Scope

- Audit the current command, view, scheduler, SQL, DAL, and Pillow rendering patterns before implementation.
- Decide the safest command location, preferring grouped admin commands such as `/admin vote create` and `/admin vote close` if compatible with the existing command architecture.
- Add SQL-backed persistence for vote posts, options, votes, reminders, and close state.
- Add one-vote-per-user enforcement using service validation and SQL constraints.
- Add persistent Discord button views for vote options.
- Add create workflow for admins with required fields:
  - title
  - description
  - options
  - target channel
  - close date/time
  - reminder offsets or reminder setting
  - launch/reminder/close mention behaviour
  - allow vote changes setting, defaulting to allowed unless product decision says otherwise
- Generate and attach a Pillow live results card using the supplied background asset.
- Edit the original vote message after votes without `@everyone` or broad pings.
- Send launch post with optional `@everyone`.
- Send reminder post(s) with optional `@everyone`.
- Send closing post with optional `@everyone`.
- Add automatic close job that disables buttons and refreshes final card.
- Add admin close-early command.
- Add update support at least for safe fields before close:
  - title/description
  - close time
  - reminder offsets/mention settings
  - launch/close text if implemented
- Add focused unit tests and integration-style tests where existing test patterns support them.
- Update docs and canonical command reference where command surface changes.
- Add logging for create, vote recorded, vote changed, reminder sent, close, close early, render failure, and message edit failure.
- Capture any out-of-scope improvements as deferred optimisations.

### Out of Scope

- Full website integration.
- Complex survey builder.
- Ranked-choice voting.
- Anonymous-from-admin votes.
- Multi-select voting unless implementation is trivial and separately approved.
- Hidden-results-until-close mode unless separately approved.
- Role-restricted voting unless needed by the first production use case.
- Editing option labels after votes exist, unless a safe and audited rule is approved.
- Full result dashboard.
- Recurring vote templates.

## 6. Source Deferred Items

Not applicable. This is new feature work rather than a captured deferred optimisation, although audit findings must still be captured structurally if discovered.

## 7. Codex Skills To Use

| Skill | Use when |
|---|---|
| `k98-architecture-scope` | Use before implementation to identify affected layers, SQL/persistence implications, refactor triggers, conditional docs, tests, and approval checkpoints. |
| `k98-discord-command-feature` | Use because this changes slash commands, Discord views/buttons, interaction callbacks, command registration, permissions, and user-facing bot flows. |
| `k98-sql-validation` | Use because this adds SQL schema and SQL-backed persistence/DAL contracts. |
| `k98-test-selection` | Use before validation to combine `scripts/select_tests.py` with risk-based coverage decisions. |
| `k98-deferred-optimisation-capture` | Use because audit/implementation may find restart-safety, duplicate helper, direct SQL, scheduler, or rendering debt. |
| `k98-pr-review` | Use before PR handoff. |
| `k98-promotion-check` | Use before production promotion and SQL deployment sequencing. |
| `codex-security:security-scan` | Use because permissions, SQL/data access, user-controlled input, persistent Discord interactions, file/assets, and scheduled jobs are touched. |

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Required to define command location, service/DAL boundaries, scheduler impact, and SQL contract. |
| `k98-discord-command-feature` | `use` | Buttons, views, admin commands, message edits, and interaction responses are central to the task. |
| `k98-sql-validation` | `use` | SQL tables/constraints/views/procs and DAL methods are required. |
| `k98-test-selection` | `use` | Needed to select focused tests plus broader command/architecture validation. |
| `k98-deferred-optimisation-capture` | `use` | Required for any audit findings outside Phase 1. |
| `k98-pr-review` | `use` | Required before merge/handoff. |
| `k98-promotion-check` | `use` | Required because bot and SQL deployment sequencing are involved. |
| `codex-security:security-scan` | `use` | Required due to permissioned admin actions, mentions, SQL writes, and user input. |

## 8. Mandatory Workflow

Default workflow:

1. Audit / scope review, then stop for approval.
2. Architecture validation, then stop for approval.
3. Implementation plan, then stop for approval.
4. Implementation after approval.
5. Validation and final review.
6. Codex Security review.

Proceed in one pass only if the operator explicitly approves one-pass execution.

Approval checkpoint must specifically confirm:

- command location and naming
- background asset path/dimensions
- default reminder offsets
- default `@everyone` behaviour
- whether vote changes are allowed by default
- maximum option count for Phase 1

## 9. Audit Requirements

Review the touched area for:

- existing admin command grouping and whether `/admin vote ...` is possible
- current permission decorators for admin/leadership-only workflows
- persistent view registration and startup rehydration patterns
- button callback patterns and interaction defer/respond patterns
- existing Pillow card services/renderers/assets
- existing scheduler/background task patterns
- existing SQL repository/DAL style
- direct SQL in commands or views
- business logic in interaction layers
- duplicate helpers or near-duplicates
- cache and persistence safety
- restart safety
- command registration implications
- tests for command inventory, persistent views, schedulers, and SQL-backed services

Map the likely:

- commands
- services
- repositories / DAL modules
- SQL objects/contracts
- views or modals
- scheduler/background task hooks
- cache/persisted state
- startup registration path
- docs to update

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Existing admin command module if possible; otherwise `commands/vote_admin_cmds.py` with explicit command-governance approval. |
| Views / modals | `ui/views/vote_post_view.py` or equivalent subsystem path. |
| Services / business logic | `services/voting/vote_service.py`, `services/voting/vote_scheduler.py`, `services/voting/vote_render_service.py` or equivalent established package convention. |
| Repository / DAL | `dal/voting_dal.py`, `repositories/voting_repository.py`, or the repo's established SQL access layer pattern. |
| Shared helpers | Existing datetime, permission, asset, logging, message-link, and Discord formatting helpers where practical. |
| Operational tooling | Existing scheduler/startup registration paths. |
| Documentation | `docs/` and `docs/reference/canonical_command_reference.md` as required. |
| SQL schema | SQL repo `sql_schema/dbo.*.Table.sql`, plus indexes/constraints/views/procs using repo standards. |
| Tests | `tests/` focused on services, DAL contract mocks, view callbacks, scheduler logic, command registration, and rendering output shape. |

## 11. Likely Files

### Review

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/canonical_command_reference.md`
- existing admin command modules
- existing leadership/MGE/Ark interactive view modules
- existing startup/persistent view registration modules
- existing scheduler/background task modules
- existing Pillow renderers/card builders
- existing DAL/repository modules
- existing SQL repo schema/proc conventions in `C:\K98-bot-SQL-Server`

### Modify

- Existing admin command module or command registration module.
- Startup/persistent view registration module.
- Scheduler/background task startup module.
- Documentation and command reference.
- Test selection/fixtures only where needed.

### Create

- `ui/views/vote_post_view.py` or equivalent.
- `services/voting/vote_service.py` or equivalent.
- `services/voting/vote_render_service.py` or equivalent.
- `services/voting/vote_scheduler.py` or equivalent.
- `dal/voting_dal.py` or equivalent.
- SQL schema files for voting tables, constraints, indexes, and optional views/procs.
- Focused test files for voting service, voting view, voting scheduler, and render service.
- Documentation page or operator note for the voting workflow.

## 12. Implementation Requirements

- Keep commands and views thin.
- Move business logic into voting services.
- Move data access into repository/DAL code.
- Avoid new direct SQL in commands or views.
- Reuse existing helpers where practical.
- Preserve restart safety.
- Add meaningful structured logging.
- Add or update tests.
- Capture new out-of-scope findings as deferred optimisations.

### Functional Requirements

#### Vote creation

- Admin can create a vote with:
  - title
  - description
  - 2-5 options unless another limit is approved
  - close date/time
  - target channel
  - reminder settings
  - launch mention setting
  - reminder mention setting
  - close mention setting
  - allow vote changes setting
- Validate:
  - close time must be in the future
  - options must be unique after trimming/case normalisation
  - option labels must fit button and card constraints
  - bot has permission to post, attach files, edit message, and use allowed mentions in target channel
  - `@everyone` must only be sent through explicit configured allowed mentions

#### Public vote post

- Post a public vote message with:
  - embed metadata
  - Pillow result card attachment
  - option buttons
  - close/deadline text
- Launch post may include `@everyone` if configured.
- Store Discord `GuildID`, `ChannelID`, `MessageID`, and attachment/render metadata in SQL.

#### Voting interaction

- A player clicks an option button.
- Bot validates the vote exists and is open.
- Bot validates the close time has not passed.
- Bot records the vote in SQL.
- Enforce one active vote per `(VotePostID, DiscordUserID)`.
- If the user previously voted:
  - update their existing vote if changes are allowed
  - otherwise respond ephemerally that they have already voted
- Respond ephemerally with a clear confirmation.
- Regenerate the Pillow card and edit the original message.
- Vote update edits must not include `@everyone`, role pings, or broad mentions.

#### Pillow result card

- Use the supplied background asset.
- Show:
  - vote title
  - status: open/closing soon/closed
  - close date/time and/or time remaining
  - option label
  - count
  - percentage
  - horizontal progress bar
  - total votes
  - last updated timestamp
  - final/closed state when applicable
- Use safe truncation/wrapping for long labels.
- Handle zero-vote state cleanly.
- If rendering fails, log and fall back safely without corrupting the message or losing votes.

#### Reminders

- Scheduler checks for due reminders.
- Reminder offset(s) are stored in SQL.
- Reminder sends once and records sent timestamp.
- Reminder may include `@everyone` if configured.
- Reminder includes:
  - vote title
  - time remaining
  - close deadline
  - link/reference to the vote post
- Reminder must not duplicate after restart.

#### Closing

- Scheduler closes votes when close time is due.
- Admin can close early.
- Close action must:
  - mark vote closed in SQL
  - set closed timestamp and closed reason/source
  - disable buttons on the vote message
  - regenerate final result card
  - post closing announcement if configured
  - include `@everyone` in closing announcement only if configured
- Backend must reject late interactions even if a stale button view is still presented by Discord.

#### Admin update

For Phase 1, implement safe update capability where practical:

- title/description before close
- close time before close
- reminder offsets before they are sent
- mention settings for future reminders/closing

Restrict or defer:

- option edits after votes exist
- target channel changes after launch
- destructive changes without audit trail

#### Restart safety

- Persistent button views must be registered at startup.
- Open votes must be discoverable from SQL on startup.
- Scheduler must recover due reminders and overdue closes.
- If a vote is overdue at startup, close it promptly and idempotently.
- Avoid relying on in-memory state for correctness.

### Command Surface Governance

- [ ] State whether the task changes top-level command count, grouped subcommand count, or neither.
- [ ] Prefer grouped admin commands.
- [ ] If a new top-level command is required, document why an existing group is not suitable, record operator approval, update `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`, update `docs/reference/canonical_command_reference.md`, update relevant user/operator docs and smoke references, and run command registration validation.
- [ ] Preserve or explicitly update `@versioned()`, `@safe_command`, `@track_usage()`, permission decorators, response visibility, autocomplete/options, usage-log identity, and command-cache behavior.
- [ ] Run or justify skipping `scripts/validate_command_registration.py`, `tests/test_validate_command_registration.py`, `tests/test_command_inventory.py`, and `tests/test_command_registration_smoke.py`.

## 13. SQL Requirements

Design exact names to match repo conventions, but the logical model should cover:

### `dbo.VotePosts`

Suggested fields:

```text
VotePostID bigint identity primary key
GuildID bigint not null
ChannelID bigint not null
MessageID bigint null until posted
CreatedByDiscordUserID bigint not null
Title nvarchar(...)
Description nvarchar(max) null
Status varchar(20) not null -- Draft/Open/Closed/Cancelled if needed
AllowVoteChange bit not null default 1
LaunchMentionEveryone bit not null default 0
ReminderMentionEveryone bit not null default 0
CloseMentionEveryone bit not null default 0
OpensAtUtc datetime2 null
ClosesAtUtc datetime2 not null
ClosedAtUtc datetime2 null
ClosedByDiscordUserID bigint null
ClosedReason nvarchar(...) null
BackgroundAssetKey/path nvarchar(...) null if useful
CreatedAtUtc datetime2 not null
UpdatedAtUtc datetime2 not null
```

### `dbo.VotePostOptions`

Suggested fields:

```text
OptionID bigint identity primary key
VotePostID bigint not null
OptionKey varchar(...) not null
Label nvarchar(...)
SortOrder int not null
ButtonStyle varchar(...) null
CreatedAtUtc datetime2 not null
```

### `dbo.VotePostVotes`

Suggested fields:

```text
VotePostID bigint not null
DiscordUserID bigint not null
OptionID bigint not null
GovernorID bigint null
CreatedAtUtc datetime2 not null
UpdatedAtUtc datetime2 not null
OriginalOptionID bigint null if tracking changes separately is desired
```

Required constraint:

```text
unique (VotePostID, DiscordUserID)
```

### `dbo.VotePostReminders`

Suggested fields:

```text
ReminderID bigint identity primary key
VotePostID bigint not null
OffsetMinutesBeforeClose int not null
DueAtUtc datetime2 not null
SentAtUtc datetime2 null
MessageID bigint null
CreatedAtUtc datetime2 not null
```

Required idempotency:

- Reminder send must be guarded by SQL state so restart does not duplicate posts.

### `dbo.VotePostAudit` or equivalent

Capture at least meaningful audit events through either a dedicated table or structured existing logging:

```text
Created
Updated
VoteRecorded
VoteChanged
ReminderSent
ClosedAutomatically
ClosedEarly
RenderFailed
MessageEditFailed
```

### SQL access pattern

- Prefer stored procedures/views only where consistent with project standards.
- Otherwise use parameterised DAL methods following existing repository style.
- No direct SQL in command or view layers.

## 14. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Command location cannot fit existing admin group | `fix now or approval required` | Avoid unnecessary top-level command growth. |
| Existing persistent view registration is duplicated/fragile | `fix now if blocking, otherwise defer` | Restart safety is mandatory for voting; broader cleanup can be deferred. |
| Existing scheduler loop has no reusable due-job pattern | `fix now minimally` | Reminder/close idempotency needs a safe scheduler integration. |
| Existing Pillow helpers can be reused | `fix now` | Avoid duplicating visual/rendering primitives. |
| Option editing after votes exist is complex | `defer` | Requires stronger audit and user-facing rules. |

Deferred items must use the structured format from `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 15. Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path vote creation
- invalid close time
- duplicate/invalid options
- permission boundary for admin-only create/update/close
- player vote record
- player vote change
- duplicate vote blocked when vote changes disabled
- closed vote rejects interaction
- automatic close disables buttons
- early close disables buttons
- reminder sends once
- reminder does not duplicate after simulated restart/idempotent rerun
- vote update edit does not include `@everyone` or broad allowed mentions
- launch/reminder/close mention behaviour is explicit and controlled
- SQL uniqueness for `(VotePostID, DiscordUserID)`
- restart/persistence re-registration path
- render zero-vote state
- render multi-option state
- render closed/final state
- render failure fallback/logging
- message edit failure handling
- command registration validation

Suggested baseline commands:

```powershell
.\.venv\Scripts\python.exe scriptsalidate_architecture_boundaries.py
.\.venv\Scripts\python.exe scriptsalidate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For broader/runtime changes, also consider:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scriptsalidate_command_registration.py
```

Add focused pytest commands after test files are identified, for example:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_voting_service.py tests/test_voting_view.py tests/test_voting_scheduler.py tests/test_voting_render_service.py
```

Before PR handoff, run Codex Security review.

## 16. Acceptance Criteria

- [ ] Admin can create a SQL-backed vote post.
- [ ] Vote post contains buttons and a Pillow-generated results card.
- [ ] Launch post can include `@everyone` when configured.
- [ ] Individual vote updates never include `@everyone`.
- [ ] Each Discord user can have only one active vote per vote post.
- [ ] Vote change behaviour follows the configured setting.
- [ ] Vote counts, percentages, total votes, and bars are accurate after each vote.
- [ ] Close date/time is stored and displayed.
- [ ] Scheduler posts due reminders once only.
- [ ] Reminder posts can include `@everyone` when configured.
- [ ] Vote closes automatically at the configured deadline.
- [ ] Admin can close early.
- [ ] Closing disables buttons.
- [ ] Closing post can include `@everyone` when configured.
- [ ] Late/stale interactions are rejected by backend validation.
- [ ] SQL schema includes appropriate constraints/indexes for durability and one-vote-per-user enforcement.
- [ ] Persistent views and due jobs are restart-safe.
- [ ] Commands/views remain thin with no direct SQL.
- [ ] Logging is adequate for operational diagnosis.
- [ ] Tests were added/updated or justified.
- [ ] Quality gates were run or documented.
- [ ] Codex Security review was run.
- [ ] Deferred optimisations are captured structurally.

## 17. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. AI Review Gates
10. Deployment Steps
11. Deferred Optimisations

Include the exact SQL deployment order and bot deployment order. Note any manual Discord smoke test steps.

## 18. Manual Discord Smoke Test Script

After deployment to a safe test channel:

1. Create a test vote with 3 options, close time 10-15 minutes in the future, and a 5-minute reminder if supported.
2. Confirm launch post appears in the selected channel and uses `@everyone` only if configured.
3. Vote as user A.
4. Confirm ephemeral vote confirmation.
5. Confirm live card updates and no new `@everyone` ping occurs.
6. Change vote as user A if vote changes are enabled.
7. Confirm SQL still has one active vote row for user A.
8. Vote as user B.
9. Confirm totals/percentages are correct.
10. Confirm reminder posts once and uses configured mention behaviour.
11. Close early on a second test vote and confirm buttons disable.
12. Let one vote close automatically and confirm final card/buttons/closing post.
13. Attempt late vote and confirm ephemeral rejection.
14. Restart bot during an open vote and confirm buttons/scheduler continue working.
15. Review logs for create/vote/change/reminder/close/render/edit events.

## 19. PR Summary Template

```md
## Summary

- Added SQL-backed Discord voting posts with live Pillow result cards.
- Added one-vote-per-user button voting with restart-safe persistent views.
- Added reminder and automatic close handling with controlled @everyone behaviour.

## Changes

- <change item>

## Tests

- <test command or verification>

## AI Review Gates

- Codex Security: run

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: new SQL-backed Discord interaction workflow with scheduled jobs and message edits.
- Rollback: disable voting command registration/scheduler, retain SQL records, and revert bot deployment. SQL rollback should follow the generated SQL deployment notes.
```

## 20. Chat Starter for Codex

```text
We need to implement Phase 1 of the Discord Voting Post Framework using the attached task pack.

Start with audit/scope only and stop for approval before implementation.

Key outcomes:
- SQL-backed vote posts/options/votes/reminders.
- Admin create/update/close controls, preferring /admin vote ... if command architecture supports it.
- Button-based voting with one active vote per Discord user.
- Vote changes allowed until close unless audit recommends otherwise.
- Pillow live results card using the supplied background asset.
- Launch/reminder/close may @everyone when configured.
- Per-vote updates must never @everyone.
- Automatic close disables buttons and backend rejects late votes.
- Persistent views and scheduler must be restart-safe.

First confirm:
1. Best command location and command-surface impact.
2. Exact SQL schema/procedure approach based on repo conventions.
3. Existing persistent view and scheduler patterns to reuse.
4. Background asset dimensions and render layout assumptions.
5. Test plan and approval checkpoints.
```
