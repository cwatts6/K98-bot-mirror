# Codex Task Pack - Player Self-Service Command Centre Phase 13 Legacy Redirect Planning

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 13 Legacy Redirect Planning`
- Date: `2026-06-27`
- Owner/context: Player Self-Service Command Centre programme after Phase 12B Discord User
  Preference Profile Store was delivered in mirror PR #177, SQL PR #20, and production PR #485,
  and smoke tested successfully by the operator on 2026-06-27
- Task type: `Discord command audit | legacy rollout planning | player communication | command-surface cleanup`
- One-pass approved: `no`
- Status: `ready for audit/scope`

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

Phase 13 must start with audit and recommendation only. Do not redirect, deprecate, or remove
commands until the operator explicitly approves the chosen rollout after reviewing usage,
compatibility, player communication, and no-feedback monitoring needs.

## 4. Delivered Context

The `/me` command centre now provides:

- `/me dashboard` as the private player home
- `/me accounts` for account review, lookup, registration, replacement, and removal
- `/me reminders` for KVK and calendar reminder management
- `/me preferences` for Inventory visibility, Inventory VIP handoff, and SQL-backed profile
  preferences for timezone, location country, and preferred language
- `/me inventory` for private latest-approved Inventory summary and report handoff
- `/me exports` for guided Stats and Inventory export option windows

Legacy commands remain live for compatibility.

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

## 7. Out of Scope

- Immediate removal of legacy commands without a separate approval after audit.
- Export schema or file-format redesign.
- Full `/my_stats`, `/myinventory`, `/mykvkcrystaltech`, or `/player_profile` redesign.
- Public calendar/KVK calendar redesign.
- New SQL schema unless separately approved.
- Website or external settings dashboard work.

## 8. Architecture Direction

- Commands remain thin and should return clear private redirect/help copy if a redirect slice is
  approved.
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

If redirect/help behavior is approved and implemented, add focused tests for the touched command
modules and run:

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
