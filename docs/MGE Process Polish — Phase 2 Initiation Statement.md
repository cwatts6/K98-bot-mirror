# MGE Process Polish — Phase 2 Initiation Statement

## Purpose

Continue the MGE process polish after Phase 1 production promotion and smoke testing.

Phase 1 delivered the operational admin controls:

* `/mge_refresh_award_reminders`
* `/mge_commanders`
* reminder message/channel ID persistence
* focused reminder refresh and commander management tests

Phase 2 should address the MGE architecture debt that was intentionally deferred from Phase 1 because it was broader than the two production-facing admin features.

## Required Reading

Before changing code, review:

* `AGENTS.md`
* `README-DEV.md`
* `docs/K98 Bot — Coding Execution Guidelines.md`
* `docs/K98 Bot — Project Engineering Standards.md`
* `docs/K98 Bot — Testing Standards.md`
* `docs/k98 Bot — Deferred Optimisation Framework.md`
* `docs/deferred_optimisations.md`
* `docs/Codex Task Pack — MGE Process Audit + Polish.md`
* Recent MGE PRs, especially PR #74 and the earlier PRs #71 and #72
* GitHub issues #29 and #32

Also inspect the current MGE modules under:

* `mge/`
* `commands/mge_cmds.py`
* `ui/views/`
* `tests/test_mge_*.py`

## Current Baseline

Phase 1 is production-promoted and smoke-tested. Do not rework the delivered admin behavior unless the Phase 2 audit finds a direct regression or an implementation detail that blocks the service-boundary cleanup.

The important Phase 1 invariants to preserve are:

* award reminder refresh remains idempotent
* commander administration affects future selection flows without mutating historical snapshots
* open/fixed mode cleanup behavior remains protected
* no direct SQL is added to Discord command handlers

## Phase 2 Goals

Address the two MGE deferred optimisation items now marked for this phase:

1. Move `mge/mge_signup_service.py` governor/account lookup away from the legacy registry shape and onto the current registry service boundary, expected to be `registry_service.get_user_accounts()` unless the audit finds a newer preferred API.
2. Extract Discord message fetch/edit/send/delete operations out of `mge/mge_publish_service.py` so the service layer owns publish state decisions and persistence, while Discord IO is handled by an interaction adapter or UI orchestration layer.

Keep the PR focused on these service-boundary improvements. Do not add new MGE product features in this phase.

## Step 1 — Audit Only

Stop after Step 1 with findings before implementing.

The audit should cover:

* current signup account-resolution flow, including self-signup and admin-add paths
* registry APIs available today and which one should become the MGE boundary
* current publish, republish, unpublish, award reminder refresh, award DM, and board refresh flows
* exactly which Discord objects `mge_publish_service.py` currently receives or mutates
* existing architecture-check allowances related to MGE publish behavior
* current regression tests that must remain green
* any migration risk for production events already carrying reminder message metadata

## Implementation Guidance

Prefer small, staged changes that preserve public behavior:

* Keep command/view code responsible for Discord interactions.
* Keep service code responsible for validation, state decisions, and domain outcomes.
* Keep DAL code responsible for SQL and persistence.
* Use fake Discord objects in tests where needed rather than live Discord clients.
* Do not change award allocation, signup semantics, event mode switching, or commander management unless directly required by the boundary cleanup.
* If extracting all Discord IO from `mge_publish_service.py` is too large for one safe PR, split the work and update `docs/deferred_optimisations.md` with a precise remaining item.

## Expected Tests

Add or update focused coverage for:

* MGE signup account lookup through the selected registry service boundary
* self-signup behavior after registry-boundary migration
* admin-add signup behavior after registry-boundary migration
* publish and republish behavior after Discord IO extraction
* reminder refresh behavior after Discord IO extraction
* unpublish, award DM, and board refresh behavior if touched

Run at minimum:

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
```

Run the full suite if practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

## Acceptance Criteria

* Step 1 audit report is produced before implementation.
* MGE signup uses the selected registry service boundary without changing user-visible signup behavior.
* `mge_publish_service.py` no longer owns Discord message IO, or any remaining Discord-aware surface is explicitly documented and re-deferred with a narrow reason.
* Reminder refresh, republish, unpublish, award DM, and board refresh behavior remain protected by focused tests.
* Existing Phase 1 commands remain registered and admin-only.
* No new direct SQL is added to command or view modules.
* `docs/deferred_optimisations.md` is updated to close, narrow, or re-defer the two Phase 2 MGE items.
