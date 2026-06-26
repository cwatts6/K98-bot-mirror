# Codex Task Pack - Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation

## 1. Task Header

- Task name: `Player Self-Service Command Centre Phase 11 Shared Visual-Card Renderer Consolidation`
- Date: `2026-06-26`
- Owner/context: Player Self-Service Command Centre programme after Phase 10 Inventory Summary Card was delivered in production PR #480 and smoke tested successfully
- Task type: `renderer refactor | visual card consolidation | player self-service polish | deferred optimisation execution`
- One-pass approved: `no`
- Status: `Phase 11A and Phase 11B delivered; Phase 11C next`

## 2. Required Reading

Before implementation, read:

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
- `docs/task_packs/archive/Codex Task Pack - Player Self-Service Command Centre Phase 10 Inventory Summary Card.md`
- `docs/player_self_service_command_centre_briefing.md`

Conditionally read renderer-specific tests and modules for the renderer family selected in the
implementation slice:

- `player_self_service/page_cards.py`
- `player_self_service/dashboard_card.py`
- `inventory/report_image_renderer.py`
- `prekvk/report_image_renderer.py`
- `kvk/rendering/`
- renderer tests under `tests/test_*renderer*.py`, `tests/test_*card*.py`, and player self-service
  page-card tests

## 3. Objective

Consolidate stable visual-card rendering primitives now that the Player Self-Service Command
Centre has stable generated cards for Dashboard, Accounts, Reminders, Preferences, Inventory, and
Exports.

The goal is not to redesign cards. The goal is to reduce duplicated rendering mechanics while
preserving existing visual output, fallback behavior, filenames, dimensions, and private/public
delivery rules.

## 4. Background

Phase 10 completed the final obvious `/me` page-level visual gap by adding `/me inventory` and the
Inventory summary card. Smoke testing confirmed all cards and commands are working. The final
Phase 10 polish also exposed the main reason this deferred item should now be promoted: multiple
renderers use similar Pillow text-fitting, badges, shadows, wrappers, and output handling, but the
spacing and fit rules are still local to each renderer.

Phase 11A is delivered in mirror PR #173 and production PR #481, and smoke testing was completed
successfully by the operator on 2026-06-26. It extracted `core.visual_text`, moved `/me` page
cards to the shared text primitives, preserved PreKvK compatibility wrappers, added focused helper
tests, included the local `phase11_me_dashboard_smoke.png` visual artifact, and kept command,
SQL/data, export, preference, and Discord visibility behavior unchanged.

The active deferred backlog now keeps Phase 11C visible so the remaining renderer family is not
lost after the first two helper-consolidation slices:

- Phase 11C: Inventory report renderer text primitive migration to `core.visual_text`.

## 5. Scope

### In Scope

- Start with an audit/scope pass before coding.
- Map duplicated renderer primitives across:
  - `/me` page cards
  - `/me dashboard`
  - KVK stats, targets, history, and ranking cards
  - PreKvK report/ranking card rendering
  - Inventory report image rendering
- Identify which primitives are stable enough to share:
  - font loading and glyph-safe fallback selection
  - text width measurement
  - fit-to-width text sizing
  - wrapped text drawing
  - shadowed text drawing
  - status badge/pill drawing where shapes are genuinely reusable
  - PNG export and `BytesIO` wrapping
- Create or extend a shared rendering utility only when it reduces duplication without forcing
  every renderer into the same layout model.
- Migrate one renderer family in the first implementation slice, preferably the `/me` card
  renderer family unless audit shows a safer first target.
- Preserve existing:
  - image dimensions
  - filenames
  - attachment naming
  - visual hierarchy
  - fallback embed behavior
  - text content and status labels
  - Unicode/player-name handling
  - public/private output behavior
- Add focused tests around the migrated renderer family and shared helper behavior.
- Produce at least one local rendered PNG smoke artifact for visual inspection during handoff.
- Update docs and deferred backlog after implementation.

### Phase 11 Slice Plan

Phase 11 should remain slice-based for risk control, but it is not complete until all target
renderer families have moved onto the shared primitive layer where practical:

1. Phase 11A: delivered in mirror PR #173 and production PR #481. Extracted `core.visual_text`
   and migrated `/me` page cards plus PreKvK compatibility wrappers away from the accidental
   `prekvk.report_image_renderer` shared-helper role.
2. Phase 11B: delivered. Migrated KVK stats and targets directly to the shared text primitives,
   kept history and rankings on KVK-local helpers backed by `core.visual_text`, and preserved KVK
   card output contracts.
3. Phase 11C: final renderer slice. Migrate Inventory report rendering text primitives to the
   shared helper while preserving report chart layout, filenames, dimensions, and existing
   report/export behavior.

Inventory is captured in `docs/reference/deferred_optimisations.md` as the remaining Phase 11
follow-up slice so it is not lost after the KVK migration. Do not close Phase 11 as complete until
the inventory renderer family is migrated or an explicit operator decision changes the phase scope.

### Out of Scope

- Redesigning card layouts, palettes, or copy.
- Adding new `/me` commands or changing command registration.
- Changing inventory, stats, KVK, PreKvK, or export data contracts.
- Changing Discord response visibility or public/private delivery rules.
- Rewriting all renderers in one PR.
- Export schema or file-format redesign.
- Broader `/me preferences` expansion.
- Legacy command redirect/removal.
- SQL schema changes.

## 6. Deferred Items Considered For Next Scope

The following Player Self-Service deferred items remain in the programme but should not be folded
into Phase 11:

- Legacy export command redirect/removal for `/my_stats_export` and `/export_inventory`.
- Broader Preferences Hub expansion.
- Legacy account/reminder/inventory preference command redirect or removal.

The export schema and format redesign deferred item should stay outside this programme as a
separate export-output programme unless a later task explicitly narrows one backwards-compatible
file-output improvement.

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Phase 11 must start by mapping renderer ownership and selecting a safe first migration slice. |
| `k98-test-selection` | use | Renderer refactors need focused visual/output tests plus standard validators. |
| `k98-deferred-optimisation-capture` | use | The phase executes one active deferred item and must keep unrelated deferred items out of scope. |
| `k98-pr-review` | use before handoff | Review visual regression risk, helper boundaries, and test coverage. |
| `codex-security:security-diff-scan` | likely skip or run based on final diff | Pure renderer-helper refactors may justify a documented skip; run if file handling, user-controlled paths, permissions, SQL/data access, or Discord interaction behavior changes. |

## 8. Mandatory Workflow

1. Start with audit/scope only unless the operator explicitly approves one-pass implementation.
2. Inventory renderer duplication and existing tests before creating shared helpers.
3. Choose the first renderer family to migrate and document why.
4. Extract only stable primitives; do not introduce a large renderer framework.
5. Migrate one renderer family.
6. Preserve output filenames, dimensions, fallback behavior, and visibility.
7. Add focused helper and renderer regression tests.
8. Render at least one representative local PNG for visual inspection.
9. Update docs and deferred backlog.
10. Run selected validators and tests.

## 9. Likely Files

```text
player_self_service/page_cards.py
player_self_service/dashboard_card.py
core/
kvk/rendering/
prekvk/report_image_renderer.py
inventory/report_image_renderer.py
tests/test_player_self_service_page_cards.py
tests/test_player_self_service_dashboard_card.py
tests/test_kvk_*renderer*.py
tests/test_inventory_report_image_renderer.py
tests/test_prekvk_report_image_renderer.py
docs/player_self_service_command_centre_briefing.md
docs/reference/deferred_optimisations.md
docs/task_packs/Player Self-Service Command Centre - Programme Pack.md
```

## 10. Suggested Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_self_service_page_cards.py tests\test_player_self_service_dashboard_card.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_targets_card_renderer.py tests\test_kvk_stats_card_renderer.py tests\test_kvk_rankings_card_renderer.py tests\test_kvk_history_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_inventory_report_image_renderer.py tests\test_prekvk_report_image_renderer.py
```

Run full `pytest -q tests` if shared helper changes touch more than one renderer family or if
`scripts/select_tests.py` recommends it.

## 11. Manual / Visual Smoke Checklist

- Render at least one `/me dashboard` card.
- Render at least one `/me inventory` partial-data card.
- Render at least one card from the migrated non-`/me` renderer family if Phase 11 migrates one.
- Confirm generated PNG dimensions and filenames are unchanged.
- Confirm long player names and Unicode-like names still fit or degrade safely.
- Confirm badge/status labels still fit.
- Confirm no text overlaps in desktop-sized generated cards.
- Confirm safe embed fallback behavior is unchanged.

## 12. Acceptance Criteria

- [x] Phase 11 starts with audit/scope unless one-pass implementation is explicitly approved.
- [x] Renderer duplication is mapped before shared helpers are introduced.
- [x] Only stable primitives are extracted.
- [x] At most one renderer family is migrated in the first implementation slice unless the
  operator explicitly approves a broader migration.
- [x] Existing card dimensions, filenames, attachment names, and fallback behavior are preserved
  for Phase 11A.
- [x] No command, SQL, export schema, preference, or legacy redirect behavior changes are included.
- [x] Focused renderer/helper tests pass for Phase 11A.
- [x] Standard validators pass for Phase 11A.
- [x] At least one rendered PNG smoke artifact is inspected before handoff.
- [x] Deferred backlog is updated to reflect the completed slice or remaining renderer work.
- [x] Phase 11B migrates KVK renderers to the shared helper while preserving KVK output.
- [ ] Phase 11C migrates Inventory report rendering text primitives to the shared helper while
  preserving inventory output.
- [ ] Inventory renderer migration is completed before Phase 11 is closed, unless the operator
  explicitly re-scopes the phase.

## 13. PR Summary Template

```md
## Summary

- Consolidated stable visual-card renderer primitives.
- Migrated <renderer family> to the shared helper path without changing visual behavior.
- Preserved filenames, dimensions, fallback behavior, and Discord visibility.

## Changes

- <shared helper changes>
- <renderer migration>
- <tests/docs>

## Tests

- <commands run>

## Visual Smoke

- <rendered PNG artifact paths and inspection notes>

## AI Review Gates

- Codex Security: <run or skipped with reason>

## Risk / Rollback

- Roll back by reverting the helper extraction and renderer migration; no command or data contract
  changes are expected in this phase.
```
