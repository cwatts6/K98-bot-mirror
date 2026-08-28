# Codex Chat Starter - Player Self-Service Command Centre Phase 13 Legacy Redirect Planning

Status: archived starter. Phase 13 was delivered in production PR #486 and smoke tested
successfully by the operator on 2026-06-27.

Phase 12B is complete. Mirror PR #177, SQL PR #20, and production PR #485 delivered the
SQL-backed Discord-user profile preference store. Smoke testing on 2026-06-27 confirmed
`/me preferences` remains private, timezone/location/language dropdowns work, values persist and
reload, the generated main card refreshes, and the private Manage Profile child window is replaced
instead of duplicated after repeated updates.

This starter is retained as the historical initiation prompt for Phase 13. Do not reuse it for
new work; use the Player Self-Service Command Centre v2 Phase 1 starter for the remaining
stats/profile/inventory audit scope.

## Copy/Paste Starter

```text
Codex, start Phase 13 of the Player Self-Service Command Centre: Legacy Redirect Planning.

Phase 12B is complete. Mirror PR #177, SQL PR #20, and production PR #485 delivered the
SQL-backed Discord-user profile preference store. Smoke testing on 2026-06-27 confirmed
`/me preferences` remains private, timezone/location/language dropdowns work, values persist and
reload, the generated main card refreshes, and the private Manage Profile child window is replaced
instead of duplicated after repeated updates.

Phase 13 objective:
Plan the safe rollout for remaining legacy player self-service command paths now that `/me`
dashboard, accounts, reminders, preferences, inventory, and exports have been delivered and smoke
tested.

Start with audit/scope only. Do not redirect, deprecate, or remove commands until I explicitly
approve the rollout after reviewing your classifications and recommendations.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md
- docs/task_packs/archive/Player Self-Service Command Centre - Programme Pack.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 13 Legacy Redirect Planning.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-discord-command-feature
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff if Discord command behavior changes

Audit these legacy paths:
- /register_governor
- /modify_registration
- /my_registrations
- /mygovernorid
- /subscribe
- /modify_subscription
- /unsubscribe
- /calendar_reminder_config
- /inventory_preferences
- /my_stats_export
- /export_inventory

Also review related personal paths that may need preservation rather than redirect:
- /myinventory
- /my_stats
- /mykvkcrystaltech
- /player_profile

Scope:
1. Audit current behavior, owner module, permission model, visibility, command registration, and
   user-facing copy for each legacy path.
2. Review available command usage signals before recommending redirects or removals.
3. Classify each path as preserve, prefer `/me` but keep live, redirect/help candidate,
   no-feedback-window removal candidate, or out of Phase 13.
4. Propose player briefing and operator communication for any redirect/deprecation path.
5. Define a no-feedback monitoring window before final removal.
6. Preserve compatibility unless I explicitly approve a rollout change.
7. Do not redesign export schemas, `/my_stats`, `/myinventory`, public calendar/KVK calendar, or
   unrelated command surfaces.
8. Update docs, canonical command reference, deferred backlog, and tests only for the approved
   audit/design or implementation slice.

Suggested validation for audit-only scope:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py

Acceptance criteria:
- Phase 13 begins with audit/scope.
- Every candidate legacy path has a documented classification and rationale.
- Redirect/removal recommendations are backed by behavior review and available usage evidence.
- No command is removed without explicit operator approval, player communication, and a
  no-feedback monitoring plan.
- Export legacy commands are not redirected or removed without explicit approval.
- Docs, canonical command reference, and deferred backlog are updated to match the approved plan.
```
