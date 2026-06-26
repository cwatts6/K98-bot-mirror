# Codex Chat Starter - Player Self-Service Command Centre Phase 11C Inventory Renderer Migration

Status: completed starter for Phase 11C. Phase 11A, Phase 11B, and Phase 11C are now delivered;
Phase 11 Shared Visual-Card Renderer Consolidation is complete at implementation handoff pending
normal PR/promotion smoke.

Phase 11A is delivered in mirror PR #173 and production PR #481 and smoke tested successfully on
2026-06-26. It extracted `core.visual_text`, migrated `/me` page cards to the shared glyph-safe
text primitives, preserved PreKvK compatibility wrappers, added focused helper and renderer tests,
included `phase11_me_dashboard_smoke.png`, and kept command, SQL/data, export, preference, and
Discord visibility behavior unchanged.

Phase 11B is delivered in production PR #482 and smoke tested successfully by the operator on
2026-06-26. It migrated the KVK renderer family to the shared `core.visual_text` primitive path,
kept KVK history and rankings on KVK-local helpers backed by the shared helper, aligned KVK
fit/width measurement with glyph-safe clustered drawing, included `phase11b_kvk_stats_smoke.png`
and `phase11b_kvk_rankings_smoke.png`, and preserved KVK visual output contracts, filenames,
dimensions, fallback behavior, special-character player-name handling, and public/private command
behavior.

The prior KVK `_text_width` measurement concern was completed in Phase 11B and was not carried
forward into Phase 11C.

Phase 11C migrated `inventory/report_image_renderer.py` font loading, glyph-safe text width,
fit-to-width, wrapping, and drawing paths to `core.visual_text` while preserving Inventory-local
chart, panel, PNG export, filename, report visibility, range-control, export-button, SQL/data,
and public/private command behavior. The local `phase11c_inventory_resources_smoke.png` artifact
was rendered and inspected before handoff.

The copy/paste starter below is retained as the historical execution prompt that launched the
completed Phase 11C slice.

## Copy/Paste Starter

```text
Codex, start Phase 11C of the Player Self-Service Command Centre: Inventory Renderer Migration.

Phase 11A is delivered in mirror PR #173 and production PR #481 and smoke tested successfully on
2026-06-26. It extracted `core.visual_text`, migrated `/me` page cards to the shared glyph-safe
text primitives, preserved PreKvK compatibility wrappers, added focused helper and renderer tests,
included `phase11_me_dashboard_smoke.png`, and kept command, SQL/data, export, preference, and
Discord visibility behavior unchanged.

Phase 11B is delivered in production PR #482 and smoke tested successfully by the operator on
2026-06-26. It migrated the KVK renderer family to the shared `core.visual_text` primitive path,
kept KVK history and rankings on KVK-local helpers backed by the shared helper, aligned KVK
fit/width measurement with glyph-safe clustered drawing, included `phase11b_kvk_stats_smoke.png`
and `phase11b_kvk_rankings_smoke.png`, and preserved KVK visual output contracts, filenames,
dimensions, fallback behavior, special-character player-name handling, and public/private command
behavior.

The prior KVK `_text_width` measurement concern is complete in Phase 11B. Keep Phase 11C focused
on inventory renderer ownership.

Phase 11C objective:
Migrate Inventory report image-renderer text primitives to `core.visual_text` without changing
visual output, filenames, dimensions, report visibility behavior, fallback behavior, export
buttons, generated report contracts, or public/private command behavior.

Target renderer family:
- `inventory/report_image_renderer.py`

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
- docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre Phase 11C Inventory Renderer Migration.md
- docs/player_self_service_command_centre_briefing.md

Use these skills as applicable:
- k98-architecture-scope
- k98-test-selection
- k98-deferred-optimisation-capture
- k98-pr-review before handoff
- codex-security security review or documented skip before PR handoff

Scope:
1. Audit current Inventory report image-renderer helper ownership before changing code.
2. Map local font loading, text width measurement, fit-to-width, wrapping, drawing, panel, chart,
   and PNG output helpers.
3. Decide which Inventory-local helpers should remain local because they are layout/chart specific
   and which should call `core.visual_text`.
4. Prefer adopting `core.visual_text` for font loading, glyph-safe text width, fit-to-width, and
   wrapping where this preserves output contracts.
5. Preserve existing image dimensions, filenames, attachment names, report text content, fallback
   embeds/messages, report visibility behavior, export controls, and generated report contracts.
6. Preserve Unicode/player-name handling and any inventory item/value formatting.
7. Add focused Inventory renderer/helper tests.
8. Render at least one representative local Inventory PNG for visual inspection.
9. Keep KVK renderer changes, command registration, SQL/data contracts, export schemas,
   preferences expansion, and legacy redirects/removal out of scope.
10. Update docs and deferred backlog. Mark Phase 11 complete only after Inventory migration is
    delivered, or keep it open if the operator explicitly re-scopes the phase.

Suggested validation:
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_core_visual_text.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_report_image_renderer.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_report_views.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_report_image_renderer.py

Manual smoke after implementation:
- `/myinventory` visual report path.
- `/me inventory` Open Report handoff into the existing report journey.
- Inventory report visibility behavior for private/public preference.
- Inventory report range controls and export buttons remain unchanged.
- Long/special-character governor name handling if names are rendered on the report.
- Safe embed/message fallback remains unchanged if image rendering or delivery fails.

Acceptance criteria:
- Phase 11C starts with audit/scope unless implementation is explicitly approved.
- Inventory renderer duplication and helper ownership are mapped before migration.
- Inventory report rendering uses `core.visual_text` directly for shared text primitives where
  practical.
- Existing Inventory report dimensions, filenames, attachment names, fallback behavior, report
  visibility, export controls, and generated report contracts are preserved.
- No KVK renderer, command, SQL, export schema, preference, or legacy redirect behavior changes
  are included.
- Focused Inventory renderer/helper tests and standard validators pass.
- At least one rendered Inventory PNG smoke artifact is inspected before handoff.
- Deferred backlog and Player Self-Service docs identify Phase 11C as delivered before Phase 11 is
  marked complete.
```
