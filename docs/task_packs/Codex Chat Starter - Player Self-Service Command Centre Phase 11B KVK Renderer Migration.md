# Codex Chat Starter - Player Self-Service Command Centre Phase 11B KVK Renderer Migration

Status: active starter for the next Player Self-Service Command Centre Phase 11 slice.

Phase 11A Shared Visual-Card Renderer Consolidation is delivered in mirror PR #173 and production
PR #481 and smoke tested successfully on 2026-06-26. It extracted `core.visual_text`, migrated
`/me` page cards to the shared glyph-safe text primitives, preserved PreKvK compatibility wrappers,
added focused helper and renderer tests, included the rendered `phase11_me_dashboard_smoke.png`
visual artifact, and kept command, SQL/data, export, preference, and Discord visibility behavior
unchanged.

Phase 11 is not complete yet. Phase 11B must migrate KVK renderers, and Phase 11C must migrate the
Inventory report renderer, unless the operator explicitly re-scopes the phase.

## Copy/Paste Starter

```text
Codex, start Phase 11B of the Player Self-Service Command Centre: KVK Renderer Migration.

Phase 11A is delivered in mirror PR #173 and production PR #481 and smoke tested successfully on
2026-06-26. It extracted `core.visual_text`, migrated `/me` page cards to the shared glyph-safe
text primitives, preserved PreKvK compatibility wrappers, added focused helper and renderer tests,
included `phase11_me_dashboard_smoke.png`, and kept command, SQL/data, export, preference, and
Discord visibility behavior unchanged.

Phase 11B objective:
Migrate the KVK visual-card renderer family to the shared `core.visual_text` primitives without
changing visual output, filenames, dimensions, fallback behavior, Unicode/player-name handling, or
public/private command behavior.

Target renderer family:
- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/rendering/kvk_targets_card_renderer.py`
- `kvk/rendering/kvk_rankings_card_renderer.py`
- `kvk/rendering/kvk_history_renderer.py`

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
- docs/task_packs/Codex Task Pack - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation.md
- docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre Phase 11B KVK Renderer Migration.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit current KVK renderer helper dependencies, especially imports that still flow through
   `prekvk.report_image_renderer` or KVK stats helper functions.
2. Decide which KVK-local helpers should remain local and which should call `core.visual_text`.
3. Migrate KVK stats and targets away from the PreKvK helper path first unless audit shows a safer
   order.
4. Rationalise history and rankings helper imports only where this preserves existing KVK output
   contracts.
5. Preserve existing image dimensions, filenames, attachment names, text content, fallback embeds,
   Unicode/player-name handling, and public/private output behavior.
6. Add focused KVK renderer/helper tests.
7. Render at least one representative local KVK PNG for visual inspection.
8. Keep command registration, SQL/data contracts, export schemas, preferences expansion, and
   legacy redirects/removal out of scope.
9. Update docs and deferred backlog. Keep Phase 11C Inventory migration captured as the remaining
   Phase 11 slice.

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_core_visual_text.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_targets_card_renderer.py tests\test_kvk_stats_card_renderer.py tests\test_kvk_rankings_card_renderer.py tests\test_kvk_history_renderer.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_report_image_renderer.py

Manual smoke after implementation:
- `/kvk stats` visual card path.
- `/kvk targets` visual card path.
- `/kvk rankings` visual card path for at least one Top 10 card mode.
- `/kvk history` visual card path.
- Long/special-character governor name handling on at least one KVK card.
- Safe embed fallback remains unchanged if image rendering or delivery fails.

Acceptance criteria:
- Phase 11B starts with audit/scope unless implementation is explicitly approved.
- KVK renderer duplication and helper ownership are mapped before migration.
- KVK renderers use `core.visual_text` directly for shared text primitives where practical.
- Existing KVK card dimensions, filenames, attachment names, fallback behavior, and visibility are
  preserved.
- No command, SQL, export schema, preference, or legacy redirect behavior changes are included.
- Focused KVK renderer/helper tests and standard validators pass.
- At least one rendered KVK PNG smoke artifact is inspected before handoff.
- Deferred backlog and Player Self-Service docs identify Phase 11C Inventory migration as the
  remaining Phase 11 slice.
- Phase 11 is not marked complete until Inventory report rendering is migrated in Phase 11C or the
  operator explicitly re-scopes the phase.
```
