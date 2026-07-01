# Discord Voting Post Framework — Programme Pack

> Programme pack for introducing SQL-backed, button-driven voting posts with live Pillow result cards, deadline locking, reminders, and admin controls for the K98 Discord bot.

## 1. Programme Header

- Programme name: `Discord Voting Post Framework`
- Date: `2026-07-01`
- Owner/context: `KD98 Discord bot / leadership and admin voting workflow`
- Programme type: `Product UX | Discord command architecture | SQL/data | visual output | operations`
- One-pass approved: `no`
- Headline: `Premium live voting posts for leadership decisions, event timing, player preferences, and community choices.`

## 2. Programme Vision

The goal is to create a reusable, premium-quality Discord voting framework that allows admins to launch polished vote posts with interactive buttons, SQL-backed vote tracking, one-vote-per-user enforcement, live Pillow-generated result cards, automatic deadline locking, reminder posts, and final close announcements.

When complete, leadership should be able to create a vote that looks and behaves like a proper product feature rather than a simple reaction poll. Players should see a clear, attractive public post with options, deadline, current totals, and live progress bars. Admins should have confidence that every vote is recorded robustly, restart-safe, auditable, and protected from duplicate voting.

This should become a reusable platform capability. The first build should support general leadership/community votes, but the architecture should be strong enough to later support Ark availability checks, event timing polls, commander preference votes, migration choices, survey-style player feedback, officer-only decisions, and website-ready export/reporting.

The standard should match the direction set by the modern KVK and inventory visuals: clean presentation, strong Discord UX, SQL-backed data integrity, thin command/view layers, and reusable services/renderers rather than one-off command logic.

## 3. Why This Programme Exists

Discord has several lightweight ways to collect opinions, including built-in polls and reactions, but they do not provide the level of control required for KD98 leadership workflows. The bot needs more robust behaviour: one vote per Discord user, clear vote deadlines, live result tracking, reminder posts, final close posts, restart safety, admin close/update controls, and records stored in SQL.

A button-based bot workflow also provides a better user experience. Players can vote with a single tap, receive private confirmation, see a smart live results image, and trust that the vote will lock at the published deadline.

This is larger than a single quick feature because it touches Discord commands, persistent views, button callbacks, SQL schema, DAL/services, scheduled background jobs, Pillow rendering, message update behaviour, permissions, operational logging, tests, and documentation. It should therefore be treated as a small programme with a first implementation phase and clearly controlled future enhancements.

## 4. Product / Engineering Goal

Create a SQL-backed voting platform inside the Discord bot that lets admins launch and manage polished live vote posts without manual counting or repeated channel noise.

The programme should answer:

- Can leadership create a vote quickly with title, description, options, close time, and reminder settings?
- Can every eligible Discord user vote once, with optional ability to change their vote before close?
- Can the vote post show a live, premium Pillow-generated result card that updates after each vote?
- Can the bot avoid pinging `@everyone` on every vote update, while still pinging on launch, reminders, and closing where configured?
- Can votes automatically close at the deadline and disable buttons?
- Can admins update, close early, reopen if explicitly supported, and export/audit results?
- Can the system recover cleanly after bot restart without losing button behaviour, reminders, or close jobs?
- Can the data model support future voting/reporting use cases without rework?

## 5. Target Model

### Target command model

Preferred grouped command model:

```text
/admin vote create
/admin vote update
/admin vote close
/admin vote status
/admin vote export
```

Alternative if the current admin group structure does not support this cleanly:

```text
/vote_admin create
/vote_admin update
/vote_admin close
/vote_admin status
/vote_admin export
```

The implementation should avoid adding a new top-level command unless command-surface governance confirms it is necessary and approved.

### Target workflow model

```text
Admin creates vote -> bot posts @everyone launch message with embed + Pillow card + buttons -> players vote -> bot records/updates vote in SQL -> bot edits original message/card without @everyone -> scheduler posts reminder with optional @everyone -> scheduler closes vote at deadline -> bot disables buttons, refreshes final card, posts closing announcement with optional @everyone
```

### Target data/model contract

```text
Discord slash command/modal -> vote service -> vote repository/DAL -> SQL tables/views/procs
SQL vote totals -> result model -> Pillow renderer -> Discord message attachment refresh
Scheduler loop -> due reminders/closures -> vote service -> Discord message updates
Button interaction -> persistent view -> vote service -> SQL -> renderer -> message edit
```

### Legacy or current paths to evaluate

```text
Existing admin command groups
Existing persistent view registration patterns
Existing scheduler/background task patterns
Existing Pillow card renderers
Existing SQL DAL/repository patterns
Existing permission decorators and safe command wrappers
Existing telemetry/usage tracking and logging patterns
```

## 6. Navigation / Workflow Model

Admin complexity should be hidden behind a create workflow. The command should collect the essential vote details and, where Discord option length makes this awkward, use a modal or staged interaction.

Recommended create flow:

1. Admin runs `/admin vote create`.
2. Admin provides title, description, options, close date/time, reminder offsets, and channel.
3. Bot validates the close time, option count, option labels, channel permissions, mention behaviour, and whether the background asset is configured.
4. Bot previews the vote privately/ephemerally where practical.
5. Admin confirms launch.
6. Bot posts the live vote message publicly in the selected channel.
7. Launch post includes `@everyone` only when configured/approved.

Player flow:

- Players click an option button on the public vote post.
- The bot stores or updates their vote in SQL.
- The bot responds ephemerally with confirmation, such as `Vote recorded: 19:00 UTC` or `Vote updated from 18:00 UTC to 19:00 UTC`.
- The bot edits the original message/card with refreshed totals.
- The bot must not include `@everyone` or any broad ping when updating after an individual vote.

Admin management flow:

- `/admin vote status` shows open/closed state, deadline, total votes, reminder status, and message link.
- `/admin vote update` allows controlled edits before close.
- `/admin vote close` closes early, disables buttons, refreshes final card, and optionally posts a closing announcement.
- `/admin vote export` returns CSV or structured output of results and voter records according to permission rules.

Timeout and fallback behaviour:

- Persistent vote buttons should remain usable after bot restart.
- If a button interaction arrives for a closed or unknown vote, respond ephemerally and do not write a vote.
- If image rendering fails, retain the previous card and log the failure; optionally fall back to text totals in the embed.
- If message edit fails because the message/channel is missing, mark the vote operationally degraded and log loudly.

## 7. Target User Journeys

### Journey A — Admin launches a community vote

Should answer:

- Can an admin create a polished vote post without manually editing embeds or counting reactions?
- Can the vote clearly show what is being decided and when voting closes?

Target behaviour:

- Admin creates a vote from a guided command/modal workflow.
- Bot validates required fields and posts a public vote with launch `@everyone` where configured.
- Vote post contains an embed, a Pillow results image, and option buttons.

Success means:

- The vote launches in the correct channel, players understand what to do, and the launch ping happens only once.

### Journey B — Player casts or changes a vote

Should answer:

- Can a player vote in one tap?
- Can the system enforce one active vote per Discord user?

Target behaviour:

- Player clicks one option.
- SQL records one vote for `(VotePostID, DiscordUserID)`.
- If vote changes are enabled, selecting a different option updates the existing row rather than inserting a duplicate.
- Player receives ephemeral confirmation.
- Public result card updates without broad pings.

Success means:

- No duplicate votes exist for the same Discord user and vote post; the live card remains accurate.

### Journey C — Vote closes automatically

Should answer:

- Does the vote lock at the published deadline even after restart?
- Are buttons disabled and late votes blocked?

Target behaviour:

- Scheduler identifies due votes.
- Vote status changes to closed in SQL.
- Buttons are disabled on the public message.
- Final Pillow card is generated.
- Closing announcement posts with optional `@everyone`.
- Backend validation rejects any late interaction.

Success means:

- No late votes are accepted and the final state is clear to players and admins.

### Journey D — Reminder is posted before close

Should answer:

- Can the bot encourage participation without spamming after every vote?
- Can reminders use `@everyone` only at configured reminder points?

Target behaviour:

- Scheduler sends configured reminder posts, such as 24h, 6h, 1h, or custom offsets before close.
- Reminder posts may include `@everyone` when enabled.
- Reminder posts include vote title, time remaining, deadline, and link to the vote post.
- Reminders are sent once and recorded in SQL.

Success means:

- Reminders are not duplicated after restart and normal vote updates never ping everyone.

### Journey E — Admin closes early

Should answer:

- Can leadership end a vote before the scheduled close time?
- Is the final result locked and visible?

Target behaviour:

- Admin runs close command and optionally gives a reason.
- Vote closes immediately.
- Buttons are disabled.
- Final card updates.
- Closing post uses configured mention behaviour.

Success means:

- Early close is auditable and no further votes are accepted.

## 8. Visual / Output Direction

Target direction:

- Premium image-first output using a configurable background asset supplied before implementation.
- Clean live result bars that show option label, count, percentage, and visual progress.
- Clear status treatment for `Open`, `Closing Soon`, and `Closed`.
- Strong readability on mobile and desktop.
- No noisy channel output on vote updates; the original post is edited in place.

Recommended output shape:

```text
Size: Confirm against existing Discord/Pillow card conventions; suggested first target 4:3 or existing card standard if reusable.
Format: PNG generated by Pillow.
Privacy: Public totals by default; voter identity export/admin-only.
Fallback: Text totals in embed if image generation fails.
```

Suggested card sections:

```text
Header: vote title + status pill
Subheader: closes at + time remaining
Main body: option rows with label, bar, count, percentage
Footer: total voters + last updated timestamp + vote ID/reference
Closed state: final result highlight + closed timestamp
```

Reusable visual/output primitives to consider:

- Background image asset with safe overlay area.
- Option progress row component.
- Status pill component.
- Deadline/time remaining component.
- Total votes footer.
- Winner/final result highlight.
- Safe text truncation/wrapping for long option labels.

## 9. Design Principles

1. **One source of truth** — SQL stores vote posts, options, votes, reminders, close state, and audit details.
2. **One active vote per Discord user** — enforce with service validation and a SQL uniqueness constraint.
3. **No accidental spam** — use `@everyone` only on launch, configured reminders, and closing posts; never on per-vote updates.
4. **Buttons are UX, SQL is authority** — disabled buttons are helpful, but backend validation must still reject closed/invalid/late interactions.
5. **Restart-safe by design** — persistent views, due-reminder checks, due-close checks, and message references must recover after restart.
6. **Commands and views stay thin** — interaction layers call services; services call repositories/DAL; rendering is isolated.
7. **Premium visual standard** — the image card should feel like a polished bot product, not a raw table or debug output.
8. **Admin control with auditability** — create, update, close early, export, and reminder behaviour should be logged and attributable.
9. **Future-ready contracts** — data structures should support later private votes, role restrictions, multi-select, and web reporting.

## 10. Programme Phases

### Phase 1 — SQL-Backed Live Voting MVP

Status: proposed.

Deliver:

- SQL schema/tables for vote posts, options, votes, reminder events, and audit fields.
- Admin create command for a vote with title, description, options, close date/time, reminder setting, channel, and mention settings.
- Persistent button view with one-vote-per-Discord-user enforcement.
- Vote change support until close, unless explicitly disabled by setting.
- Pillow result card renderer using configurable background asset.
- Public vote post update after each vote without `@everyone`.
- Scheduler/background loop for reminders and automatic closing.
- Buttons disabled on close and backend late-vote rejection.
- Admin close-early command.
- Focused tests and documentation.

### Phase 2 — Admin Management and Export Hardening

Status: proposed.

Deliver:

- Admin update command for controlled edits before close.
- Admin status command with message link, totals, deadline, reminder state, and operational state.
- Export command for results and voter audit.
- Enhanced error handling and operational logging.
- Permission/role hardening and audit trail improvements.
- Optional reopen only if approved after reviewing risk.

### Phase 3 — Advanced Voting Modes

Status: future candidate.

Deliver:

- Role-restricted voting.
- Governor-linked voting mode.
- Private/anonymous results mode.
- Multi-select/toggle voting mode.
- Hidden results until close.
- Per-option emoji/icon support.
- Richer final result card with winner emphasis.

### Phase 4 — Voting Templates and Reusable Workflows

Status: future candidate.

Deliver:

- Saved vote templates for recurring use cases.
- Ark/event timing templates.
- Leadership-only/officer-only templates.
- Player survey templates.
- Recurring vote setup if genuinely useful.

## 11. In Scope for the Programme

- Admin-controlled vote creation, update, status, close early, and export workflows.
- Public vote post with Discord buttons.
- One active vote per Discord user.
- Optional vote changing before close.
- SQL-backed persistence for posts, options, votes, reminders, and closure state.
- Pillow-generated live result card.
- Configurable background asset for the card.
- Launch/reminder/closing mention behaviour, including optional `@everyone`.
- No `@everyone` on vote update edits after individual votes.
- Automatic scheduled close based on configured date/time.
- Reminder posts at configured offsets before close.
- Disabled buttons after close.
- Restart-safe persistent views and scheduled job recovery.
- Tests, docs, command reference updates, and validation gates.

## 12. Out of Scope for the First Build

- Website voting UI.
- Full survey builder with free-text questions.
- Complex ranked-choice voting.
- Anonymous public voting where even admins cannot audit voters.
- Paid/third-party scheduling services.
- Multi-server productisation beyond current K98 bot needs.
- Advanced role eligibility unless required for the first launch use case.
- Editing vote options after votes have been cast, unless a safe explicit rule is approved.

## 13. Likely Source Commands and Areas

### Commands to audit

```text
/admin existing grouped commands
/resync_commands
/dl_bot_status
```

### Modules to audit

```text
commands/*admin*_cmds.py
commands/*leadership*_cmds.py
ui/views/*
services/*
dal/*
core/*scheduler*
core/*logging*
core/*discord*
```

Likely new areas:

```text
commands/vote_admin_cmds.py or existing admin command module
ui/views/vote_post_view.py
services/voting/vote_service.py
services/voting/vote_render_service.py
services/voting/vote_scheduler.py
repositories/voting_repository.py or dal/voting_dal.py
assets/voting/<background asset>
docs/reference/canonical_command_reference.md
```

### SQL repo areas to validate if needed

```text
C:\K98-bot-SQL-Server
```

Likely SQL-backed contracts:

- `dbo.VotePosts`
- `dbo.VotePostOptions`
- `dbo.VotePostVotes`
- `dbo.VotePostReminders`
- `dbo.VotePostAudit` or audit columns/events
- Optional views/procs for current totals and exports

## 14. Cross-Programme Constraints

- Avoid increasing top-level command count unless explicitly approved.
- Prefer grouped admin commands.
- Preserve command registration governance.
- Keep commands/views thin and avoid direct SQL in interaction layers.
- Validate all SQL objects against the SQL repo.
- Use persistent Discord view registration so buttons survive restart.
- Treat all Discord user input as untrusted.
- Enforce close state in SQL/service logic, not just via disabled buttons.
- Avoid broad pings except configured launch/reminder/closing posts.
- Add meaningful logs for create/update/vote/close/reminder/render failures.
- Capture deferred optimisations structurally.

## 15. Programme-Level Validation Strategy

Each implementation phase should consider:

- command registration validation
- focused command tests
- permission tests
- response visibility tests
- view/button callback tests
- modal validation tests if modals are used
- service/DAL contract tests
- SQL schema and uniqueness validation
- one-vote-per-user tests
- close deadline and late-vote rejection tests
- reminder idempotency tests
- restart/persistence tests
- image renderer output shape tests
- fallback path tests for render/edit failures
- manual Discord smoke testing
- Codex Security review because permissions, user input, SQL, persistent interactions, and scheduled jobs are touched

Baseline commands to consider:

```powershell
.\.venv\Scripts\python.exe scriptsalidate_architecture_boundaries.py
.\.venv\Scripts\python.exe scriptsalidate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scriptsalidate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 16. Programme Acceptance Criteria

The programme is complete when:

- [ ] Admins can create a vote with title, description, options, close date/time, reminder settings, channel, and mention behaviour.
- [ ] Vote launch can include `@everyone` when configured.
- [ ] Reminder posts can include `@everyone` when configured and are sent only once per reminder.
- [ ] Closing post can include `@everyone` when configured.
- [ ] Per-vote message/card updates never include `@everyone` or broad pings.
- [ ] Each Discord user has only one active vote per vote post.
- [ ] Vote changes are handled according to the configured setting.
- [ ] Live Pillow card shows accurate counts, percentages, bars, total votes, deadline/status, and last updated/final state.
- [ ] Automatic close disables buttons and blocks late votes in the backend.
- [ ] Admins can close early.
- [ ] Admin update/status/export controls are delivered or intentionally deferred to the named phase.
- [ ] SQL is the durable source of truth.
- [ ] Persistent views and scheduled jobs recover after restart.
- [ ] Documentation and command references are updated.
- [ ] Command registration validation remains green.
- [ ] No new direct SQL exists in command/view layers.
- [ ] Deferred findings are captured structurally.

## 17. Deferred / Future Opportunities

Do not include these in early phases unless separately approved:

- Role-restricted voting.
- Governor-linked voting and account mapping.
- Anonymous public results.
- Hidden results until close.
- Multi-select voting.
- Ranked-choice voting.
- Saved templates.
- Vote result dashboards.
- Website result export/visualisation.
- Automated post-vote action workflows.
- Per-option images/icons.

## 18. Open Questions / Options to Confirm Before Build

These are the main product choices worth confirming before Codex starts implementation:

1. **Command location** — should this live under `/admin vote ...` if the existing admin group allows it, or as a temporary/new `/vote_admin ...` group?
2. **Vote changes** — default should be `allow changes until close`; confirm whether any votes should be immutable after first click.
3. **Reminder defaults** — suggested defaults are `24h` and `1h` before close, with custom offsets optional.
4. **Mention defaults** — suggested default is: launch `@everyone` enabled, reminders `@everyone` configurable, close `@everyone` configurable, vote updates never ping.
5. **Option count** — suggested first build supports 2-5 options to keep button layout clean; later expand if needed.
6. **Results visibility** — suggested first build shows public totals live; hidden-until-close can be deferred.
7. **Admin update rules** — editing title/description/deadline/reminders should be allowed; editing option labels after votes exist should be restricted or audited carefully.
8. **Card dimensions** — confirm the final background asset dimensions before implementation so Pillow layout is built against the right canvas.
9. **Timezone display** — recommended display should show UTC by default and optionally local friendly text if existing helpers support it.
10. **Export format** — CSV first is probably enough; richer admin summary can follow.

## 19. Suggested Next Action

```text
Use the Phase 1 Codex task pack to audit architecture and implement the SQL-backed live voting MVP once the background asset and command location are confirmed.
```

## 20. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| 2026-07-01 | Initial programme pack created | Captures button voting, Pillow live card, one-vote-per-user, deadline locking, reminders, @everyone rules, admin controls, and SQL persistence. |
