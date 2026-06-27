# Codex Task Pack - Player Self-Service Command Centre Phase 13 Legacy Redirect Planning

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 13 Legacy Redirect Planning`
- Date: `2026-06-27`
- Owner/context: Player Self-Service Command Centre programme after Phase 12B Discord User
  Preference Profile Store was delivered in mirror PR #177, SQL PR #20, and production PR #485,
  and smoke tested successfully by the operator on 2026-06-27
- Task type: `Discord command audit | legacy rollout planning | player communication | command-surface cleanup`
- One-pass approved: `partial - approved redirect slice only`
- Status: `approved redirect slice implemented - awaiting validation and handoff`

## 2. Required Reading

Before implementation or rollout decisions, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Player Self-Service Command Centre - Programme Pack.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read:

- `docs/reference/Promotion Guide.md` only for production promotion or deployment sequencing.
- SQL repo docs only if usage evidence or rollout tooling depends on SQL-backed usage data.
- Existing command tests for any legacy command path included in an approved redirect or removal.

## 3. Objective

Plan the safe rollout for remaining legacy player self-service command paths now that `/me`
dashboard, accounts, reminders, preferences, inventory, and exports have been delivered and smoke
tested.

Phase 13 started with audit and recommendation only. After reviewing the classifications and updated usage evidence, the operator explicitly approved a lightweight redirect slice for selected legacy paths. This slice keeps command registrations in place, does not remove commands from Discord, and defers final command removal until player communication plus a no-feedback monitoring window are complete.

## 4. Delivered Context

The `/me` command centre now provides:

- `/me dashboard` as the private player home
- `/me accounts` for account review, lookup, registration, replacement, and removal
- `/me reminders` for KVK and calendar reminder management
- `/me preferences` for Inventory visibility, Inventory VIP handoff, and SQL-backed profile
  preferences for timezone, location country, and preferred language
- `/me inventory` for private latest-approved Inventory summary and report handoff
- `/me exports` for guided Stats and Inventory export option windows

Approved legacy paths remain registered for compatibility; selected paths now return private redirect guidance to the matching `/me` centre.

## 5. Legacy Paths To Audit

Audit at least:

```text
/register_governor
/modify_registration
/my_registrations
/mygovernorid
/subscribe
/modify_subscription
/unsubscribe
/calendar_reminder_config
/inventory_preferences
/my_stats_export
/export_inventory
```

Also review related still-live personal paths that should likely be preserved rather than
redirected in Phase 13:

```text
/myinventory
/my_stats
/mykvkcrystaltech
/player_profile
```

## 6. In Scope

- Audit current behavior, ownership, permissions, public/private response behavior, command
  registration status, and player-facing copy for each legacy path.
- Review available command usage signals before recommending redirects or removals.
- Classify each command as:
  - preserve
  - prefer `/me` but keep live
  - redirect/help response candidate
  - no-feedback-window removal candidate
  - out of Phase 13
- Propose player briefing and operator communication for any redirect/deprecation path.
- Define a no-feedback monitoring window before final removal.
- Preserve compatibility unless operator approval explicitly changes the path.
- Update docs, canonical command reference, deferred backlog, and tests for any approved rollout
  design or implementation.

## 6A. Audit Findings - 2026-06-27

Phase 13 started with audit/scope only. After the operator reviewed the classifications, the approved implementation slice changed selected runtime handlers to private redirect-only responses. No command registration has been removed.

### Usage Evidence Review

Available usage signals were reviewed before classification. Evidence sources:

- All candidate paths use `@track_usage()` and are therefore eligible for command usage review.
- Usage events are written through `usage_tracker.py` to local `data/command_usage_*.jsonl` files
  and flushed to SQL through `telemetry/dal/command_usage_dal.py`.
- SQL source-of-truth validation confirms `dbo.BotCommandUsage` exists in
  `C:\K98-bot-SQL-Server\sql_schema\dbo.BotCommandUsage.Table.sql` with indexes on
  `CommandName`, `ExecutedAtUtc`, `UserId`, and app context.
- The operator-provided SQL extract
  `C:\Users\cwatt\OneDrive\Documents\ROK\BotCommandUsage extract.csv` was parsed read-only. It
  contains 14,605 rows from `dbo.BotCommandUsage`.
- The operator-provided dated JSONL files from 2026-06-19 through 2026-06-27 were parsed
  read-only. They contain 1,138 operational usage events with reliable UTC dates.
- The SQL extract is treated as the broad usage signal. The dated JSONL files are treated as a
  recent-window signal and are not added to the SQL extract totals because flushed events may
  overlap.

Provided evidence shows nonzero broad usage for every audited legacy and related personal command.
Recent JSONL evidence also shows live direct usage of reminders, calendar reminder configuration,
inventory preferences, stats and inventory exports, `/myinventory`, `/my_stats`,
`/mykvkcrystaltech`, and `/player_profile`. `/me` usage exists in the recent JSONL window, but it
is concentrated in one user and matches the Phase 12B smoke-test period, so it should be treated as
operator/smoke adoption evidence rather than broad player migration evidence.

Usage evidence summary:

| Path | SQL extract uses / users / failures | Recent JSONL uses / users | Evidence note |
|---|---:|---:|---|
| `/register_governor` | 30 / 8 / 1 | 0 / 0 | Broad usage exists; no recent JSONL hit in supplied window. |
| `/modify_registration` | 4 / 2 / 0 | 0 / 0 | Low broad usage, but still used historically. |
| `/my_registrations` | 42 / 4 / 0 | 0 / 0 | Broad review/action usage exists. |
| `/mygovernorid` | 17 / 3 / 0 | 0 / 0 | Broad direct lookup usage exists and command is referenced by fallback copy. |
| `/subscribe` | 26 / 11 / 0 | 1 / 1 | Broad and recent direct signup usage exists. |
| `/modify_subscription` | 25 / 4 / 3 | 1 / 1 | Broad and recent edit usage exists; historical failures were command/runtime errors. |
| `/unsubscribe` | 1 / 1 / 0 | 0 / 0 | Low usage; remove-all/unsubscribe is now covered by `/me reminders` confirmation. |
| `/calendar_reminder_config` | 20 / 1 / 0 | 2 / 1 | Broad and recent direct calendar reminder usage exists. |
| `/inventory_preferences` | 12 / 3 / 0 | 3 / 2 | Broad and recent direct preference usage exists. |
| `/my_stats_export` | 49 / 2 / 8 | 3 / 1 | Broad and recent export usage exists; preserve pending export-specific review. |
| `/export_inventory` | 2 / 1 / 0 | 1 / 1 | Low but recent export usage exists; preserve pending export-specific review. |
| `/myinventory` | 60 / 2 / 0 | 6 / 2 | Broad and recent detailed inventory report usage exists. |
| `/my_stats` | 197 / 23 / 20 | 2 / 1 | High broad personal stats usage exists. |
| `/mykvkcrystaltech` | 252 / 12 / 0 | 1 / 1 | High broad CrystalTech usage exists. |
| `/player_profile` | 52 / 1 / 1 | 2 / 1 | Leadership profile usage exists; out of Phase 13. |
| `/me dashboard` | 56 / 1 / 0 | 56 / 1 | Recent smoke/operator-heavy use. |
| `/me accounts` | 3 / 1 / 0 | 3 / 1 | Recent smoke/operator-heavy use. |
| `/me reminders` | 6 / 1 / 0 | 6 / 1 | Recent smoke/operator-heavy use. |
| `/me preferences` | 3 / 1 / 0 | 3 / 1 | Recent smoke/operator-heavy use. |
| `/me inventory` | 6 / 1 / 0 | 6 / 1 | Recent smoke/operator-heavy use. |
| `/me exports` | 7 / 1 / 0 | 7 / 1 | Recent smoke/operator-heavy use. |

Before any final command-registration removal is approved, collect a fresh production usage snapshot after the player briefing has been posted. The supplied evidence proves there is current and historical dependency on direct legacy paths; the approved redirect slice intentionally keeps old paths discoverable while steering users to `/me`.

Suggested SQL shape for future production monitoring:

```sql
SELECT
    CommandName,
    COUNT(*) AS Uses,
    COUNT(DISTINCT UserId) AS UniqueUsers,
    SUM(CASE WHEN Success = 1 THEN 0 ELSE 1 END) AS Failures,
    MIN(ExecutedAtUtc) AS FirstSeen,
    MAX(ExecutedAtUtc) AS LastSeen
FROM dbo.BotCommandUsage
WHERE ExecutedAtUtc >= DATEADD(day, -30, SYSUTCDATETIME())
  AND CommandName IN (
      'register_governor',
      'modify_registration',
      'my_registrations',
      'mygovernorid',
      'subscribe',
      'modify_subscription',
      'unsubscribe',
      'calendar_reminder_config',
      'inventory_preferences',
      'my_stats_export',
      'export_inventory',
      'myinventory',
      'my_stats',
      'mykvkcrystaltech',
      'player_profile',
      'me dashboard',
      'me accounts',
      'me reminders',
      'me preferences',
      'me inventory',
      'me exports'
  )
GROUP BY CommandName
ORDER BY Uses DESC, CommandName ASC;
```

### Candidate Classification

| Path | Owner module | Current behavior and visibility | Classification | Rationale / recommendation |
|---|---|---|---|---|
| `/register_governor` | `commands/registry_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me accounts`. Legacy validation/view code was removed from the command handler; registration remains so old invocations receive guidance during monitoring. |
| `/modify_registration` | `commands/registry_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me accounts`. Legacy modify/remove view code was removed from the command handler; registration remains so old invocations receive guidance during monitoring. |
| `/my_registrations` | `commands/registry_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me accounts`. The old summary/embed/action helper path was removed from the command module; registration remains so old invocations receive guidance during monitoring. |
| `/mygovernorid` | `commands/telemetry_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me accounts`. Lookup and account linking now live in the private account centre; registration remains so old invocations receive guidance during monitoring. |
| `/subscribe` | `commands/subscriptions_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me reminders`. The old subscription setup view code was removed from the command handler. |
| `/modify_subscription` | `commands/subscriptions_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me reminders`. The old edit view code was removed from the command handler. |
| `/unsubscribe` | `commands/subscriptions_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me reminders`. The old direct unsubscribe cleanup path was removed from the command handler because `/me reminders` owns confirmed remove-all/unsubscribe. |
| `/calendar_reminder_config` | `commands/calendar_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me reminders`. The old calendar reminder panel wiring was removed from this command handler. |
| `/inventory_preferences` | `commands/inventory_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance. | Redirect/help response implemented | Redirects to `/me preferences`. The old direct preference prompt entry point was removed from this command handler; `/myinventory` still uses the prompt when needed. |
| `/my_stats_export` | `commands/stats_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance while retaining old options for compatibility. | Redirect/help response implemented | Redirects to `/me exports` under explicit operator approval. Export service/schema/file behavior remains available through `/me exports`; registration remains during monitoring. |
| `/export_inventory` | `commands/inventory_cmds.py` | Public command-level access; defers ephemeral; sends private redirect guidance while retaining old options for compatibility. | Redirect/help response implemented | Redirects to `/me exports` under explicit operator approval. Export service/schema/file behavior remains available through `/me exports`; registration remains during monitoring. |

### Related Personal Path Classification

| Path | Owner module | Classification | Rationale / recommendation |
|---|---|---|---|
| `/myinventory` | `commands/inventory_cmds.py` | Preserve; v2 alignment candidate | `/me inventory` intentionally hands off to this detailed report journey through Open Report. It remains valuable, but command-group alignment belongs in the Player Self-Service v2 programme pack. |
| `/my_stats` | `commands/stats_cmds.py` | Preserve; v2 programme candidate | This command remains the personal stats report journey with KVK stats-channel rules. It was too large for this programme pack and should be modernised in Player Self-Service v2. |
| `/mykvkcrystaltech` | `commands/telemetry_cmds.py` | Preserve | CrystalTech has its own channel and user-selectable visibility rules. It is a related personal path, but not replaced by `/me` and should stay out of Phase 13 redirect scope. |
| `/player_profile` | `commands/telemetry_cmds.py` | Preserve; v2 programme candidate | This is an admin/leadership profile lookup with allowed-channel gating. It should be considered with `/stats player` and `/my_stats` in the v2 modernisation pack rather than Phase 13 redirects. |

### Rollout Recommendation

Approved first rollout is redirect-first for the explicit operator-approved slice, while preserving registrations and deferring final removal:

1. Keep old command registrations in place so players receive guidance instead of command-not-found errors.
2. Redirect only the approved paths to `/me accounts`, `/me reminders`, `/me preferences`, or `/me exports`.
3. Remove command-local legacy view/export wiring that is no longer reachable from those flat commands, while preserving shared services and `/me` behavior.
4. Publish player/operator communication that the older direct commands now point to `/me`, and keep `/myinventory`, `/my_stats`, `/mykvkcrystaltech`, `/player_profile`, and `/stats player` live.
5. Use a no-feedback monitoring window before any command-registration removal.

No Phase 13 candidate should be moved straight from live behavior to command-registration removal.

### Player Briefing Draft

```text
Personal setup is moving to /me dashboard.

Use /me dashboard as your private starting point for accounts, reminders, preferences, inventory,
and exports. The older account, reminder, preference, and export direct commands now point you to /me, which is the preferred place to manage personal setup:

- /me accounts for account lookup, registration, replacement, and removal
- /me reminders for KVK and calendar reminder settings
- /me preferences for inventory visibility, VIP, timezone, location, and language
- /me inventory for your latest approved inventory summary
- /me exports for private stats and inventory exports

No command has been removed from Discord yet. Please report anything you still need from an older command before final cleanup.
```

### Operator Communication Draft

```text
Phase 13 has an approved lightweight redirect rollout.

The selected legacy player self-service commands remain registered but now return private guidance to the matching `/me` centre. No command has been removed from Discord. The next decision is whether, after player communication and monitoring, any redirect-only registrations can be removed.

Before approving command behavior changes, collect 30-day usage for:
/register_governor, /modify_registration, /my_registrations, /mygovernorid,
/subscribe, /modify_subscription, /unsubscribe, /calendar_reminder_config,
/inventory_preferences, /my_stats_export, /export_inventory, /myinventory,
/my_stats, /mykvkcrystaltech, /player_profile, and the /me subcommands.

/myinventory, /my_stats, CrystalTech, /stats player, and leadership profile lookup should remain live. `/my_stats_export` and `/export_inventory` now redirect to `/me exports`, but export schemas/services remain unchanged.
```

### No-Feedback Monitoring Plan

Before final removal of any command path, require all of the following:

- Operator approval for the exact command path and final user-facing copy.
- Player briefing posted with a concrete timestamp and channel.
- Production usage evidence collected for at least a 30-day lookback before the change.
- A private help/redirect or deprecation slice deployed first, unless the operator explicitly
  approves skipping that step for a path with no production usage.
- A minimum 30 consecutive days after the redirect/deprecation production deploy with:
  - no actionable player complaints or support requests tied to the command path
  - no meaningful successful usage of the old command beyond testing/operator checks
  - no increase in failures for the preferred `/me` replacement
  - operator sign-off recorded before command-registration removal

For `/my_stats_export` and `/export_inventory`, use a separate export-specific approval and
monitoring decision. Do not include them in a general legacy cleanup removal batch.

## 7. Out of Scope

- Immediate removal of legacy command registrations without a separate approval after the redirect monitoring window.
- Export schema or file-format redesign; Phase 13 only redirects old export entry points to `/me exports`.
- Full `/my_stats`, `/stats player`, `/myinventory`, `/mykvkcrystaltech`, or `/player_profile` redesign; stats/profile/inventory alignment is deferred to Player Self-Service v2.
- Public calendar/KVK calendar redesign.
- New SQL schema unless separately approved.
- Website or external settings dashboard work.

## 8. Architecture Direction

- Redirected commands remain thin and return clear private redirect/help copy.
- Do not add direct SQL to command or view modules.
- Keep any usage-data access in service/DAL helpers if usage evidence is pulled from SQL.
- Preserve decorators, command registration governance, tracking, and response visibility.
- Treat removal as a later cleanup after player communication and no-feedback monitoring.

## 9. Suggested Validation

For audit-only scope, run or justify skipping:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

For the approved redirect/help implementation, add focused tests for the touched command modules and run:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_me_cmds.py tests\test_player_self_service_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_validate_command_registration.py
```

Run broader tests when command registration, shared decorators, or multiple legacy command modules
change.

## 10. Manual Smoke

For any approved redirect/deprecation implementation:

- `/me dashboard`, `/me accounts`, `/me reminders`, `/me preferences`, `/me inventory`, and
  `/me exports` remain private and behavior-compatible.
- Each changed legacy command returns the approved private guidance or redirect behavior.
- Commands classified as preserve still behave as before.
- Command registration remains stable.
- No public/private response behavior changes without explicit approval.
- Player communication copy is clear and does not imply a command has disappeared before it has.

## 11. Acceptance Criteria

- Phase 13 begins with audit/scope.
- Every candidate legacy path has a documented classification and rationale.
- Redirect/removal recommendations are backed by behavior review and available usage evidence.
- No command is removed without explicit operator approval, player communication, and a
  no-feedback monitoring plan.
- Export legacy commands are not redirected or removed without explicit approval.
- Docs, canonical command reference, and deferred backlog are updated to match the approved plan.
- Focused tests and standard validators pass for any implemented rollout slice.
