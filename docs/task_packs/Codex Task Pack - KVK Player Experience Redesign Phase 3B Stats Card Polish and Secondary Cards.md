# Codex Task Pack - KVK Player Experience Redesign Phase 3B Stats Card Polish and Secondary Cards

## 1. Task Header

- Task name: `KVK Player Experience Redesign - Phase 3B Stats Card Polish and Secondary Cards`
- Date: `2026-06-04`
- Owner/context: `K98 Bot KVK Player Experience Redesign programme after Phase 3 visual card rollout`
- Task type: `feature / UX polish / generated image renderer / Discord interaction polish`
- One-pass approved: `no`
- Status: `complete - delivered in mirror PR #143 and promoted to production`

### Phase Completion Update

Phase 3B is complete as of 2026-06-05.

Delivered result:

- Main-card compact values use one-decimal formatting.
- KVK mode card backgrounds are selected through shared mode normalization and asset fallback logic.
- Main-card rank displays the existing `KVK_RANK` value from the stats payload.
- More Stats top-right `Overall KVK Rank` is intentionally shown as `TBC` until Phase 3C adds the durable SQL-backed rank source.
- More Stats and History are Pillow-rendered secondary cards attached to `/kvk stats`.
- More Stats includes pass-window kills/deads, Pre-KVK rank/points, Honor rank/points, and DKP progress.
- History includes Autarch, KVK Played, Highest Acclaim, personal bests, and last KVK summary metrics; matchmaking snapshot data is intentionally excluded.
- Dynamic progress scales support high performers, including values around `225%`.
- Secondary-card interaction callbacks defer before rendering.
- `/mykvkstats` remains on the legacy embed path.

Follow-on work has been split into Phase 3C:

`docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3C Overall Rank and Card Polish.md`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Also read:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern mykvkstats Visual Card.md`
- `docs/task_packs/KVK Player Experience Redesign - Phase 1 Audit and Design Report.md` as historical context
- `docs/reference/canonical_command_reference.md` if command output descriptions or command-surface validation are touched

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

```text
C:\K98-bot-SQL-Server
```

## 3. Objective

Polish the delivered Phase 3 `/kvk stats` visual card and extend the same visual language to the attached `More Stats` and `History` views.

This phase should improve readability, mode-specific branding, progress-scale clarity, and secondary-card presentation while preserving the Phase 3 rollout model: `/kvk stats` uses the new visual card and `/mykvkstats` remains on the legacy embed during parallel validation.

## 4. Background

Phase 3 delivered the first modern KVK visual card for `/kvk stats`, including a renderer-independent payload, Pillow renderer, Discord avatar support, three-button view model, embed fallback, and preserved legacy `/mykvkstats` output.

Follow-up user review identified these Phase 3B improvements:

- Compact values should display fewer decimals, for example `124.1M` instead of `124.135M`.
- Card background should change by KVK mode from `dbo.KVK_Details.KVK_NAME`.
- `assets/kvk/cards/Heroic_Anthem_Stats_Card.jpg` has been added locally and should be used for Heroic Anthem mode.
- Rank needs a trophy emoji or suitable trophy visual marker.
- Kills target progress ticks should scale beyond `150%` for high performers, including players around `225%`.
- `More Stats` and `History` should become Pillow-rendered cards rather than remaining plain embed-style detail views.

## 5. Scope

### In Scope

- Keep `/kvk stats` as the new-card path and keep `/mykvkstats` legacy during validation.
- Reduce compact stat formatting on the main card to one decimal place for `M`, `B`, and similar large values where appropriate.
- Add KVK mode background selection using the existing `KVK_NAME`/mode value from the Phase 3 payload or service layer.
- Use `Tides_Stats_Card.png` for `Tides of War`.
- Use `Heroic_Anthem_Stats_Card.jpg` for `Heroic Anthem`.
- Preserve a safe fallback background when KVK mode is missing, unknown, or the mapped asset is unavailable.
- Add a trophy emoji or suitable trophy marker next to the rank label without disrupting the rank layout.
- Make kills target progress bar ticks dynamic for high progress values, including values above `150%` and around `225%`.
- Review and improve the ordering, grouping, labels, and visual hierarchy for `More Stats`.
- Build a Pillow-rendered `More Stats` card if the audit confirms it is PR-sized.
- Review and improve the ordering, grouping, labels, and visual hierarchy for `History`.
- Build a Pillow-rendered `History` card if the audit confirms it is PR-sized.
- Preserve `Main Card`, `More Stats`, and `History` as the three visible view choices.
- Add/update focused tests for formatting, background selection, progress tick scaling, rank marker, and secondary-card rendering.
- Include generated sample images or screenshots for visual review.

### Out of Scope

- No command-surface migration or new top-level command.
- No removal, redirect, or deprecation of `/mykvkstats`.
- No SQL schema, stored procedure, view, function, index, or migration changes unless separately approved.
- No KVK import, recompute, export, Google Sheets, or cache scheduling changes.
- No changes to KVK calculations or target rules beyond display formatting and renderer scale presentation.
- No redesign of `/kvk targets`, `/kvk history`, `/kvk rankings`, `/mykvktargets`, `/mykvkhistory`, or `/kvk_rankings` command outputs outside the buttons attached to `/kvk stats`.
- No website implementation.
- No predictive "on track" modelling.
- No direct SQL in commands, views, or renderers.

## 6. Source Deferred Items

This task is a planned programme sub-phase, not a deferred optimisation batch.

If audit finds out-of-scope debt, capture it in `docs/reference/deferred_optimisations.md` using the required structure:

```md
### Deferred Optimisation
- Area:
- Type: performance | architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies:
```

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to keep the polish and secondary-card work PR-sized and layered correctly. |
| `k98-discord-command-feature` | use | Required because `/kvk stats` output, buttons, Discord attachments, and interaction views are touched. |
| `k98-sql-validation` | use if needed | Required if the task changes or newly depends on SQL-backed KVK mode, camp, history, or secondary metric fields. Background selection must not guess schema details. |
| `k98-test-selection` | use | Required before validation to select focused renderer, service, view, command, and regression tests. |
| `k98-deferred-optimisation-capture` | use if needed | Required if audit finds out-of-scope renderer, payload, view, or service debt. |
| `k98-pr-review` | use | Required before PR handoff. |
| `k98-promotion-check` | use | Required before production promotion or deployment. |
| `codex-security:security-scan` | use | Required before PR handoff because Discord interactions, SQL-backed data, user avatars/names, and generated image/file output are touched. |

## 8. Mandatory Workflow

1. Audit the Phase 3 implementation and current rendered output, then stop for approval.
2. Confirm the Phase 3B implementation split, especially whether `More Stats` and `History` both fit in one PR.
3. Validate KVK mode/background data source and asset availability.
4. Implement approved card polish and secondary-card renderer work.
5. Add or update tests.
6. Generate visual review artifacts.
7. Run focused validation and selected broader validation.
8. Run Codex Security review when preparing PR handoff.

Proceed in one pass only if the operator explicitly approves it.

## 9. Audit Requirements

Review and document:

- current `/kvk stats` Phase 3 posting path
- current `/mykvkstats` legacy path to confirm it remains unchanged
- current KVK stats payload fields for KVK mode, camp, map, KVK number, rank, timestamps, and avatar
- current `KVK_NAME` source and whether it is already present in the payload
- SQL repo object defining `dbo.KVK_Details.KVK_NAME` if the payload source is ambiguous
- current asset path and asset naming under `assets/kvk/cards/`
- current compact number formatter and where one-decimal card formatting belongs
- current progress-bar renderer and tick-label scaling
- current `More Stats` payload data order and empty-state behaviour
- current `History` payload data order and empty-state behaviour
- whether shared rendering primitives should be extracted before adding secondary cards
- existing renderer tests and visual artifact patterns
- fallback behaviour when rendering or attachment upload fails

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | Existing `commands/kvk_cmds.py` only if wiring or fallback needs adjustment. Do not create new commands. |
| Posting/fallback | Existing KVK stats card posting helper. Keep Discord-specific behaviour outside renderer/service code. |
| Views/buttons | Existing `ui/views/kvk_stats_card_views.py`; callbacks should stay thin. |
| Service payload | Existing KVK stats card service/payload module. Keep calculations and data normalization out of the renderer. |
| Renderer | Existing KVK stats card renderer module plus secondary-card renderer functions where appropriate. |
| Assets | `assets/kvk/cards/` with explicit mode-to-background mapping and fallback. |
| Tests | Existing focused KVK stats card tests under `tests/`, extended for Phase 3B behaviours. |
| Docs | Task pack/programme updates only unless command reference text changes. |

## 11. Likely Files

### Review

- `commands/kvk_cmds.py`
- `commands/kvk_stats_card_posting.py`
- `kvk/services/kvk_stats_card_service.py`
- `kvk/rendering/kvk_stats_card_renderer.py`
- `ui/views/kvk_stats_card_views.py`
- `assets/kvk/cards/`
- `tests/test_kvk_stats_card_payload.py`
- `tests/test_kvk_stats_card_renderer.py`
- `tests/test_kvk_stats_card_posting.py`
- `tests/test_kvk_stats_card_views.py`
- `tests/test_kvk_cmds.py`

### Modify

- `kvk/rendering/kvk_stats_card_renderer.py`
- `kvk/services/kvk_stats_card_service.py` if background mode or secondary-card payload data needs normalization
- `ui/views/kvk_stats_card_views.py` if More Stats/History switch from embeds to image cards
- `commands/kvk_stats_card_posting.py` if attachment or fallback handling needs extension
- focused KVK stats card tests

### Create

- No new command files expected.
- Optional secondary renderer module only if it avoids bloating the existing renderer and matches local patterns.
- Optional focused tests for secondary cards if existing test files become crowded.

## 12. Implementation Requirements

### 12.1 Main Card Number Formatting

- Use one decimal place for compact display values on the main visual card, for example `124.1M`, `18.9M`, `1.1M`, and `353.7M`.
- Keep percentages compact and readable, for example `103%` or `84.5%` where target precision matters.
- Do not change underlying calculations or payload numeric values.
- Keep embed/detail formatting unchanged unless explicitly approved.

### 12.2 KVK Mode Background Selection

- Select the card background from KVK mode, sourced from the service payload.
- The SQL-backed source is `dbo.KVK_Details.KVK_NAME`; validate the Python source path against the SQL repo if it is not already clear.
- Use a normalized mapping so small text variations do not break background selection.
- Required mappings:
  - `Tides of War` -> `assets/kvk/cards/Tides_Stats_Card.png`
  - `Heroic Anthem` -> `assets/kvk/cards/Heroic_Anthem_Stats_Card.jpg`
- Unknown or missing KVK mode should fall back to the current Tides card or an explicit default background without failing the command.
- Renderer tests should cover known, unknown, and missing mode values.

### 12.3 Rank Marker

- Add a trophy emoji or suitable trophy marker next to the rank label.
- Main-card `Rank` must display the existing `KVK_RANK` value from the stats payload.
- More Stats `Overall KVK Rank` should display `TBC` until Phase 3C introduces a durable SQL-backed overall KVK rank source.
- Keep rank readable and avoid reintroducing a boxed badge.
- Ensure the marker renders with the configured font fallback or use a safe text/icon fallback if emoji support is unreliable.

### 12.4 Dynamic Kills Target Progress Scale

- Progress ticks should communicate the player's actual scale instead of stopping at a fixed low ceiling.
- Support common high-progress cases such as `175%`, `200%`, `225%`, and above without label overlap.
- Suggested approach:
  - keep base ticks at `0%`, `25%`, `50%`, `75%`, `100%`
  - add higher ticks in sensible increments up to the next ceiling above actual progress
  - use `25%` increments through `150%`
  - use `50%` increments above `150%` if space becomes tight
- Bar fill should show true relative progress within the selected scale, not cap visually at `100%` when the scale extends above `100%`.
- Add tests for below target, just above target, around `150%`, and around `225%`.

### 12.5 More Stats Card

- Convert the `More Stats` view to a Pillow-rendered card if the audit confirms it is PR-sized.
- Preserve current data content unless an ordering change is explicitly part of this task.
- Improve visual hierarchy with grouped sections, for example DKP progress, pass-window kills/deads, Pre-KVK, Honor, and missing-data notes.
- Avoid copying a text-heavy embed directly into an image.
- Use clear empty states when a section has no real values.
- Preserve the `Main Card` and `History` navigation options.

### 12.6 History Card

- Convert the `History` view to a Pillow-rendered card if the audit confirms it is PR-sized.
- Preserve current data content unless an ordering change is explicitly part of this task.
- Improve visual hierarchy with grouped sections, for example historical summary, personal bests, and last KVK summary.
- Exclude matchmaking snapshot data from the History card; it is not historical context for this view.
- Filter falsey/empty values so the card does not present zero-filled placeholders as meaningful history.
- Use clear empty states and keep `Main Card` navigation available.

### 12.7 Fallback And Rollout

- Preserve existing embed fallback if image rendering or upload fails.
- If secondary-card image rendering fails, the button should still return useful information via the existing embed path or a clear failure message.
- Keep logs useful for operators without leaking sensitive data.
- Do not make the rollout dependent on `/mykvkstats`.

### 12.8 Command Surface Governance

- [ ] No new top-level command.
- [ ] No new grouped subcommand.
- [ ] Preserve `/kvk stats` and `/mykvkstats` registration.
- [ ] Preserve decorators, permissions, response visibility, usage tracking, and command-cache behaviour.
- [ ] Run or justify skipping `scripts/validate_command_registration.py` and command inventory tests.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Main card formatter needs one-decimal visual output | fix now | Directly requested card readability improvement. |
| Background selection is hardcoded to Tides | fix now | KVK mode-specific branding is required for non-Tides KVKs. |
| Rank lacks visual affordance | fix now | Small safe polish item. |
| Progress ticks stop too low for high performers | fix now | Directly requested and visible in production validation. |
| More Stats remains embed-style | fix now if PR-sized, otherwise split with approval | User requested a Pillow card, but scope must remain manageable. |
| History remains embed-style | fix now if PR-sized, otherwise split with approval | User requested a Pillow card, but scope must remain manageable. |
| Broader `/kvk history` command redesign | defer | Phase 3B only changes the attached stats-card view. |
| Legacy `/mykvkstats` migration to card | defer | Parallel rollout intentionally keeps legacy output unchanged. |

Add further rows based on actual findings.

## 14. Testing Requirements

Cover or justify:

- one-decimal compact number formatting
- percentage formatting remains compact
- Tides background selection by KVK mode
- Heroic Anthem background selection by KVK mode
- unknown/missing KVK mode fallback
- missing background asset fallback
- trophy/rank marker rendering path
- progress tick scale below target
- progress tick scale around `126%`
- progress tick scale around `225%`
- main renderer produces non-empty PNG bytes
- More Stats card renderer happy path and empty state
- History card renderer happy path and empty state
- secondary-card fallback to useful embed/output on render failure
- `/kvk stats` remains the new-card path
- `/mykvkstats` remains legacy
- command registration unchanged

Suggested focused tests, adapt to actual repo file names:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_renderer.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_payload.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_views.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_posting.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
```

Suggested validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run full tests before promotion if practical:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

Visual validation:

- Generate at least one Tides sample card.
- Generate at least one Heroic Anthem sample card.
- Generate at least one high-progress sample around `225%`.
- Generate `More Stats` and `History` samples if those cards are implemented.
- Inspect at Discord desktop and mobile-like sizes.
- Confirm no text overlap, clipped labels, unreadable colours, or missing glyphs.

## 15. Acceptance Criteria

- [ ] Scope is confirmed before implementation.
- [ ] `/kvk stats` continues to output the new card.
- [ ] `/mykvkstats` remains on the original legacy embed path.
- [ ] Main-card compact stat values use one decimal place.
- [ ] Tides of War mode uses the Tides background.
- [ ] Heroic Anthem mode uses `Heroic_Anthem_Stats_Card.jpg`.
- [ ] Unknown/missing mode falls back safely.
- [ ] Rank includes a trophy emoji or suitable trophy marker.
- [ ] Main-card rank uses `KVK_RANK`.
- [ ] More Stats overall KVK rank is marked `TBC` until Phase 3C data support is available.
- [ ] Kills target progress ticks scale dynamically for high performers, including around `225%`.
- [ ] Bar fill reflects progress within the selected scale.
- [ ] `More Stats` ordering and visual hierarchy are reviewed and improved.
- [ ] `More Stats` is rendered as a Pillow card or explicitly split into a follow-up with approval.
- [ ] `History` ordering and visual hierarchy are reviewed and improved.
- [ ] `History` is rendered as a Pillow card or explicitly split into a follow-up with approval.
- [ ] Existing command registration, permissions, response visibility, and fallback behaviour are preserved.
- [ ] No new SQL or direct SQL in commands/views/renderers is added.
- [ ] Focused tests pass.
- [ ] Visual review artifacts are generated.
- [ ] Codex Security review is run before PR handoff or explicitly justified.
- [ ] Rollback plan is documented.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. Asset Files
6. SQL Changes
7. Command Surface Changes
8. User-Visible Behaviour Changes
9. Renderer / Payload Summary
10. Helpers Reused
11. Refactor Findings
12. Test Plan and Results
13. Visual Review Evidence
14. AI Review Gates
15. Deployment Steps
16. Rollback Plan
17. Deferred Optimisations

For documentation-only changes, state that no runtime code, SQL, helper reuse, or restart behaviour changed.

## 17. PR Summary Template

```md
## Summary

- Polished the `/kvk stats` main visual card with one-decimal stat values, mode-specific backgrounds, trophy rank styling, and dynamic high-progress target ticks.
- Added visual-card treatment for `More Stats` and/or `History` according to the approved Phase 3B scope.
- Preserved the Phase 3 rollout model: `/kvk stats` uses the new card and `/mykvkstats` remains legacy during validation.

## Changes

- Updated KVK stats card formatting and progress-scale rendering.
- Added KVK mode background selection for Tides of War and Heroic Anthem.
- Updated secondary stats/history card rendering or documented the approved split.
- Added focused renderer, payload, view, and fallback tests.

## User-visible behaviour

- `/kvk stats` card values are easier to read.
- The card background now reflects KVK mode where supported.
- High-performing players see progress ticks that scale beyond 150%.
- More Stats and History use the modern visual direction where implemented.

## SQL Changes

- None.

## Tests

- List focused pytest, validators, and any full-suite result here.

## Visual Review

- List generated sample card paths or screenshots and note desktop/mobile readability checks.

## AI Review Gates

- Codex Security: run before PR handoff because this touches Discord interactions, SQL-backed data, user avatars/names, and generated image/file output.

## Deferred Optimisations

- None, or include structured deferred items using the repository framework.

## Risk / Rollback

- Risk: visual renderer changes can introduce layout regressions or asset fallback mistakes.
- Mitigation: focused renderer tests, fallback paths, and generated sample review.
- Rollback: disable the card feature flag or revert `/kvk stats` posting to the Phase 3 card/embed fallback path.
```

## 18. Codex Chat Starter

```text
Codex, start Phase 3B of the KVK Player Experience Redesign: Stats Card Polish and Secondary Cards.

Phase 3 is complete. Keep /kvk stats on the new visual card and keep /mykvkstats on the original legacy embed during parallel validation.

Before implementation, read:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 3 Modern mykvkstats Visual Card.md
- this Phase 3B task pack

Use the K98 repo workflow and required skills. First audit the existing Phase 3 renderer, payload, posting helper, and card views. Confirm whether More Stats and History can both be safely converted to Pillow cards in one PR before implementation.

Main-card polish requirements:
- compact stat values should use one decimal place, e.g. 124.1M and 18.9M
- background selection should use KVK mode from dbo.KVK_Details.KVK_NAME
- Tides of War uses Tides_Stats_Card.png
- Heroic Anthem uses Heroic_Anthem_Stats_Card.jpg
- add a trophy emoji or suitable trophy marker next to Rank
- progress ticks should scale dynamically for high performers, including around 225%

Secondary-card requirements:
- review More Stats and History ordering and visual hierarchy
- build Pillow cards for More Stats and History if PR-sized
- preserve Main Card, More Stats, and History navigation
- preserve fallback output if image rendering or upload fails

Do not change SQL, KVK calculations, KVK import/recompute/export, Google Sheets contracts, command registration, or legacy /mykvkstats rollout behaviour unless separately approved.
```
