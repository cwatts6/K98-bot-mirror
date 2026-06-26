# Codex Chat Starter - Player Self-Service Command Centre Phase 12 Preferences Hub Expansion

Status: completed starter for Phase 12 Slice 1. Mirror PR #176 was merged and smoke tested
successfully by the operator on 2026-06-26.

Phase 11 Shared Visual-Card Renderer Consolidation is complete. Phase 11A delivered
`core.visual_text` and migrated `/me` page cards plus PreKvK compatibility wrappers. Phase 11B
migrated the KVK renderer family and was smoke tested successfully in production PR #482. Phase
11C migrated Inventory report rendering to the shared text primitive path, production PR #483 was
smoke tested successfully by the operator on 2026-06-26, and special-character rendering was
confirmed correct.

Phase 12 started with audit/scope and delivered the approved Inventory Preferences slice only:
`/me preferences` remains private, shows the generated Inventory Preferences card, preserves the
existing service-backed Inventory report visibility and Inventory VIP flows, and does not expose
unsaved export, stats privacy, reminder, account, timezone, location, or language controls.

The copy/paste starter below is retained as the historical execution prompt that launched the
completed Phase 12 Slice 1. Use the Phase 12B starter for the next preference-profile slice.

## Copy/Paste Starter

```text
Codex, start Phase 12 of the Player Self-Service Command Centre: Preferences Hub Expansion.

Phase 11 is complete. Phase 11A delivered `core.visual_text` and migrated `/me` page cards plus
PreKvK compatibility wrappers. Phase 11B migrated the KVK renderer family and was smoke tested
successfully in production PR #482. Phase 11C migrated `inventory/report_image_renderer.py` to the
shared text primitive path, production PR #483 was smoke tested successfully on 2026-06-26, and
special-character rendering was confirmed correct.

Phase 12 objective:
Expand `/me preferences` from the current first-pass controls into a coherent player preference
hub, but only where each setting has a clear product purpose and safe service-backed persistence.

Start with audit/scope only unless I explicitly approve implementation.

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
- docs/task_packs/Player Self-Service Command Centre - Programme Pack.md
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 12 Preferences Hub Expansion.md
- docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff if security-sensitive surfaces are touched

Scope:
1. Audit current `/me preferences`, `/inventory_preferences`, Inventory visibility, Inventory VIP,
   export option windows, reminder preferences, account/main-account behavior, and local-time or
   timezone signals before changing code.
2. Map which preference-like settings already have safe persistence and which do not.
3. Decide which settings belong in `/me preferences`, which remain in domain-specific centres,
   and which should be deferred.
4. Add only service-backed preference mutations where privacy, restart safety, validation,
   fallback behavior, and legacy compatibility are preserved.
5. Preserve `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me exports`,
   `/my_stats_export`, `/export_inventory`, reminder flows, command registration, export schemas,
   generated file contracts, and public/private response behavior.
6. Do not add placeholder, "coming soon", or unsaved preference controls.
7. Keep commands and views thin; domain persistence remains in services/DAL.
8. Update `/me preferences` card/fallback copy only for settings that are actually delivered.
9. Add focused preference service, view, card, and failure-path tests.
10. Update docs and deferred backlog after implementation.

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_preference_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_page_cards.py

Manual smoke after implementation:
- `/me preferences` remains private and renders the generated card.
- Inventory visibility still saves and refreshes correctly.
- Inventory VIP update handoff still works.
- Any newly added preference persists across a fresh interaction and survives restart expectations.
- Failure states remain private and actionable.
- `/inventory_preferences`, `/myinventory`, `/me inventory`, `/me exports`, `/my_stats_export`,
  and `/export_inventory` remain behavior-compatible.

Acceptance criteria:
- Phase 12 starts with audit/scope unless implementation is explicitly approved.
- Candidate preferences are mapped before new controls are added.
- Every shipped preference has a clear product purpose and service-backed persistence.
- No placeholder or unsaved controls are introduced.
- Existing Inventory visibility, VIP, report, export, reminder, command registration, and
  public/private behavior is preserved.
- Focused tests and standard validators pass.
- Deferred backlog captures useful but unsafe candidate settings.
```
