# Codex Task Pack — MGE Process Audit + Polish

## Delivery Status

Phase 1 has been delivered in branch `codex/mge-process-polish`.

### Phase 1 Delivered

* Completed the Step 1 MGE lifecycle audit before implementation.
* Added admin-only `/mge_refresh_award_reminders`.
* Added idempotent award reminder refresh behaviour:

  * updates existing reminder messages when message metadata is present
  * reposts reminders when message metadata is missing or the message was deleted
  * refuses refresh when awards have not been published
  * rebuilds reminder content from the current active default reminder text for the event rule mode, falling back to the stored event reminder text
  * persists reminder message/channel IDs for future refreshes

* Added admin-only `/mge_commanders`.
* Added MGE commander DAL/service/view support for:

  * listing commanders by variant
  * adding commanders
  * updating commander names
  * activating/deactivating commanders
  * reassigning commanders to variants
  * duplicate-name protection
  * cache refresh after commander changes

* Preserved historical stability by continuing to rely on `GovernorNameSnapshot` and `RequestedCommanderName` on signup/award rows for historical display.
* Added focused tests for reminder refresh and commander management.
* Rechecked the MGE validation blocker noted for `tests/test_dl_bot_mge_auto_import.py`; it now passes in the focused MGE validation run.
* Added bot-repo SQL migration mirror:

  * `sql/mge_award_reminder_message_ids_schema.sql`

### SQL Promotion Required

Before production use of award reminder refresh, promote the matching SQL change to the authoritative SQL Server repo:

* `dbo.MGE_Events.AwardRemindersMessageId BIGINT NULL`
* `dbo.MGE_Events.AwardRemindersChannelId BIGINT NULL`

### Deferred To Phase 2

The following items were explicitly deferred because they are broader architecture work, not required for the two operational features delivered in Phase 1:

* MGE signup registry-service alignment:

  * GitHub issue #29: `service misalignment (MGE / stats)`
  * GitHub issue #32: `Service Layer Consolidation Pack`
  * Deferred because it touches shared registry/account lookup behaviour across MGE and stats.

* MGE publish-service Discord IO extraction:

  * `mge_publish_service.py` already mixes publish state orchestration with Discord send/edit/delete operations.
  * Phase 1 reused that existing boundary to avoid broad refactoring of publish, republish, reminders, award DMs, unpublish, and board refresh in the same PR.
  * Captured as a structured deferred optimisation in `docs/deferred_optimisations.md`.

### Phase 1 Validation

Completed validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q (Get-ChildItem tests\test_mge_*.py).FullName tests\test_dl_bot_mge_auto_import.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m ruff check mge commands ui tests
.\.venv\Scripts\python.exe -m black --check mge commands ui tests
git diff --check
.\.venv\Scripts\python.exe -m pytest -q tests
```

Results:

* Focused MGE validation: `278 passed`
* Full suite: `1291 passed, 8 skipped`
* `git diff --check` passed with only a CRLF warning for `commands/mge_cmds.py`

## Goal

Fully audit and polish the MGE process, resolving hidden issues, improving admin control, and adding two missing operational features:

1. Allow admins to update/re-publish MGE award reminders after rules or award text changes.
2. Add an admin-only command to add, update, activate/deactivate, or reassign MGE commanders.

Also review GitHub issues, recent MGE PR history, and `docs/deferred_optimisations.md` for any MGE-related cleanup.

---

# Required Reading

Before changing code, review:

* `AGENTS.md`
* `docs/codex_execution_guidelines.md`
* `docs/K98 Bot — Project Engineering Standards.md`
* `docs/deferred_optimisations.md`
* MGE modules under:

  * `mge/`
  * `commands/`
  * `ui/views/`
  * `tests/test_mge_*.py`

Recent MGE PR context:

* PR #71: fixed MGE open-mode award cleanup ordering
* PR #72: fixed MGE open-mode award audit insert and signup race

STOP after Step 1 with findings before implementing.

---

# Step 1 — Audit Current MGE Process

Map the full MGE lifecycle:

* Event creation
* Signup open/close
* Controlled/fixed mode vs open mode
* Commander selection
* Award allocation
* Award list publish/re-publish
* Award reminder generation/posting
* Rules text storage and editing
* Open-mode switch cleanup/audit behaviour
* Signup/public embed refresh behaviour
* Any scheduled reminder behaviour

Produce a short audit report covering:

* Current command list
* Current DAL/service/view boundaries
* Where rules are read from
* Where award reminder content is generated
* Whether reminders store enough metadata to be safely updated
* Whether current event history relies on commander name snapshots or live commander rows
* Any direct SQL in command handlers
* Any missing tests or weak regression coverage

Do not implement until this audit is complete.

---

# Step 2 — Add Award Reminder Re-Publish / Refresh Support

## Problem

Currently, if admins publish the award list before correcting rules text, they can re-publish the award list but not the related award reminders. This leaves stale reminder messages unless they are manually posted.

## Required Behaviour

Add an admin-only flow to refresh award reminders for an existing MGE event.

Preferred command name:

* `/mge_refresh_award_reminders`

Alternative acceptable if current naming conventions suggest better:

* `/mge_republish_award_reminders`

The command must:

* Be admin-only using the existing admin decorator pattern.
* Select or infer the relevant active/upcoming MGE event.
* Rebuild reminder content from the current stored event rules/award data.
* Update existing reminder messages where possible.
* If message IDs are missing or messages were deleted, repost cleanly.
* Avoid duplicate reminders.
* Log what happened:

  * updated existing reminders
  * reposted missing reminders
  * skipped because no awards published
  * failed due to missing channel/message permissions

## Important Rules

* Do not require manually editing Discord messages.
* Do not reallocate awards.
* Do not alter signups.
* Do not change open/fixed mode.
* Do not touch historical completed MGE events unless explicitly selected by admin.
* Keep idempotent behaviour: running twice should not create duplicates.

## Tests

Add/extend tests for:

* Refresh updates existing reminder messages.
* Refresh reposts missing/deleted reminder messages.
* Refresh does not duplicate reminders.
* Refresh uses latest rules text.
* Refresh refuses when awards are not published.
* Permission/admin guard remains intact.

---

# Step 3 — Add Admin Commander Management Command

## Goal

Add an admin-only Discord command to manage `MGE_Commanders`.

Suggested command:

* `/mge_commanders`

The UI should use Discord components:

1. Dropdown: select variant.
2. Dropdown: `Add New Commander` or select existing commander.
3. Modal for fields:

   * Commander name
   * Active status
   * Linked variant
   * Optional display/order field if the table already supports it

## Required Operations

Support:

* Add commander
* Update commander name
* Activate/deactivate commander
* Move commander to a different variant
* View current commanders by variant
* Prevent accidental duplicate active commander names for the same variant

## History / Current Event Rules

Codex must inspect the schema and current code, then enforce this policy unless the existing model requires a safer alternative:

* Historical MGE signups/awards should remain stable by using existing snapshot fields where available.
* Updating `MGE_Commanders` should affect future event setup and future commander dropdowns.
* Existing MGE events already created should not silently mutate their published award history.
* If a commander is inactive, it should not appear for new signup/award flows, but existing historical records should still display correctly.
* Deleting commanders should be avoided unless no references exist. Prefer inactive status over physical delete.

## If Delete Is Requested

The command may include “Deactivate” rather than hard delete.

Only add hard delete if:

* No signup/award/event history references the commander.
* The DAL performs a safe reference check.
* The UI labels it clearly as dangerous.

## Tests

Add tests for:

* Admin-only access.
* Listing by variant.
* Add new commander.
* Update name.
* Update active flag.
* Move variant.
* Duplicate prevention.
* Inactive commanders excluded from new event/signup dropdowns.
* Historical snapshots remain unchanged.

---

# Step 4 — Resolve MGE-Related Deferred Items / GitHub Issues

Review:

* `docs/deferred_optimisations.md`
* Open GitHub issues
* Recent closed MGE PRs
* Current `tests/test_mge_*.py`

Known relevant point from deferred docs:

* `tests/test_dl_bot_mge_auto_import.py` is listed among tests affected by local validation/environment blockers.
* If this still affects reliable MGE validation, either fix it or clearly isolate it with an environment capability gate.

Do not resolve unrelated deferred items unless they directly block MGE.

---

# Step 5 — MGE Optimisation / Underlying Issue Review

Look for and fix low-risk issues in:

* Race conditions around signup close/open-mode switch.
* Duplicate reminder/message creation.
* Missing message ID persistence.
* Stale component views after event mode changes.
* Direct SQL in command/view layers.
* Missing transaction boundaries in DAL writes.
* Weak error handling around Discord message edits/deletes.
* Inconsistent UTC handling.
* Embed fields near Discord limits.
* Rules text escaping/formatting issues.
* Permission checks.

Any large architectural refactor should be captured as a new deferred optimisation unless it is directly required for this task.

---

# Step 6 — Validation

Run focused MGE validation:

```powershell
python -m pytest -q (Get-ChildItem tests\test_mge_*.py).FullName
python scripts\validate_architecture_boundaries.py
python scripts\validate_deferred_items.py
python scripts\select_tests.py
python scripts\smoke_imports.py
python scripts\validate_command_registration.py
python -m ruff check mge commands ui tests
python -m black --check mge commands ui tests
git diff --check
```

If full suite is practical:

```powershell
python -m pytest -q tests
```

If any test is gated due to environment constraints, document clearly why and ensure it is not silently skipped without explanation.

---

# Acceptance Criteria

* MGE audit report produced before implementation.
* Admin can refresh/re-publish award reminders after correcting rules.
* Reminder refresh is idempotent and avoids duplicate posts.
* Admin can manage MGE commanders from Discord.
* Commander changes affect future events only unless current-event behaviour is explicitly and safely handled.
* Historical MGE display remains stable.
* Existing open/fixed mode behaviour remains protected.
* No new direct SQL is added to Discord command handlers.
* Tests cover the new reminder and commander workflows.
* MGE-related deferred/GitHub items are resolved or explicitly re-deferred with reason.
