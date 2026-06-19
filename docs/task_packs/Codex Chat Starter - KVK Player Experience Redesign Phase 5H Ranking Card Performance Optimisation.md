# Codex Chat Starter - KVK Player Experience Redesign Phase 5H Ranking Card Performance Optimisation

Status: next active Phase 5 slice after Phase 5G smoke-test completion.

Phase 5A through Phase 5G are complete.

- Phase 5A: mirror PR #152 and production PR #461 delivered
  `/kvk rankings type:records` as the KD98 Hall of Fame Top 10 all-time single-KVK records
  foundation.
- Phase 5B: mirror PR #153 and production PR #462 delivered the unified current-ranking browser
  for KVK, Honor, and PreKvK rankings.
- Phase 5C: mirror PR #154 and production PR #463 delivered the current KVK Top 10 visual ranking
  card for `/kvk rankings type:kvk`.
- Phase 5D: mirror PR #155 and production PR #464 delivered the Hall of Fame records Top 10 visual
  cards for `/kvk rankings type:records`.
- Phase 5E: mirror PR #156 and production PR #465 delivered Honor and PreKvK Top 10 visual cards
  for `/kvk rankings type:honor` and `/kvk rankings type:prekvk`.
- Phase 5F-1: mirror PR #158 and production PR #466 delivered private My Rank / Find Me for
  current KVK, Honor, and PreKvK rankings.
- Phase 5F-2: mirror PR #159 and production PR #467 delivered private Full List CSV export for
  current KVK, Honor, and PreKvK rankings.
- Phase 5G: mirror PR #160 delivered rankings wrap-up polish: Honor compact values, PreKvK compact
  fixed-width alignment, near-billion value unit preservation, display-width-aware compact rows for
  wide/special governor-name characters, and centered current KVK Top 10 card podium text.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5G Rankings Wrap-up Polish.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Current delivered context:

- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current KVK, Honor, PreKvK, and Hall of Fame records all have Top 10 visual cards with embed
  fallback.
- Top 25 and Top 50 remain compact unified browser output for current KVK, Honor, and PreKvK.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Private My Rank is available for registered governors in current KVK, Honor, and PreKvK modes.
- Private Full List CSV export is available for current KVK, Honor, and PreKvK modes.
- Compact Top 25/50 output has been smoke-polished for Honor values, PreKvK fixed-width alignment,
  near-billion values, and wide/special governor-name characters.
- Current KVK Top 10 podium text is centered consistently with Records, Honor, and PreKvK cards.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.

## Copy/Paste Starter

```text
Codex, start Phase 5H of the KVK Player Experience Redesign: ranking-card performance optimisation for /kvk rankings.

Phase 5A is complete: mirror PR #152 and production PR #461 delivered `/kvk rankings type:records`
as the KD98 Hall of Fame Top 10 all-time single-KVK records foundation.

Phase 5B is complete: mirror PR #153 and production PR #462 delivered the unified current-ranking
browser for `/kvk rankings type:kvk`, `honor`, and `prekvk`, pushed it to production, and smoke
tested it successfully.

Phase 5C is complete: mirror PR #154 and production PR #463 delivered the current KVK Top 10
visual ranking card for `/kvk rankings type:kvk`, pushed it to production, smoke tested it
successfully, and completed follow-up polish.

Phase 5D is complete: mirror PR #155 and production PR #464 delivered the Hall of Fame records
Top 10 visual cards for `/kvk rankings type:records`, pushed them to production, smoke tested them
successfully, and completed follow-up polish.

Phase 5E is complete: mirror PR #156 and production PR #465 delivered Honor and PreKvK Top 10
visual cards for `/kvk rankings type:honor` and `/kvk rankings type:prekvk`, pushed them to
production, smoke tested them successfully, and completed review/smoke-test polish.

Phase 5F-1 is complete: mirror PR #158 and production PR #466 delivered private My Rank / Find Me
for current KVK, Honor, and PreKvK rankings, pushed it to production, and smoke tested it
successfully.

Phase 5F-2 is complete: mirror PR #159 and production PR #467 delivered private Full List CSV
export for current KVK, Honor, and PreKvK rankings, pushed it to production, smoke tested it
successfully, and completed review/smoke-test polish.

Phase 5G is complete: mirror PR #160 delivered the remaining rankings wrap-up polish for current
rankings. Honor Top 25/50 compact rows display values, PreKvK Top 25/50 rows are fixed-width and
display-width aware for wide/special governor-name characters, near-billion values preserve their
unit, and current KVK Top 10 card podium text is centered. Smoke testing confirmed the compact
browser and KVK Top 10 card look good.

Read first:
- AGENTS.md
- README-DEV.md
- docs/reference/README.md
- docs/reference/K98 Bot - Project Engineering Standards.md
- docs/reference/K98 Bot - Coding Execution Guidelines.md
- docs/reference/K98 Bot - Testing Standards.md
- docs/reference/K98 Bot - Skills & Refactor Triggers.md
- docs/reference/K98 Bot - Deferred Optimisation Framework.md
- docs/task_packs/KVK Player Experience Redesign - Programme Pack.md
- docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5G Rankings Wrap-up Polish.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Phase 5H objective:
Profile and optimise ranking-card render/load latency for the delivered current KVK, Honor,
PreKvK, and Hall of Fame Top 10 visual cards. Performance is acceptable after Phase 5G, but any
low-risk improvements that make cards render/load faster without changing player-facing behaviour
should be delivered before Phase 5 closes.

Scope:
1. Start with audit/scope and a proposed Phase 5H implementation plan.
2. Confirm the first implementation slice before coding unless the operator explicitly approves
   one-pass delivery.
3. Measure current ranking-card render timings for representative current KVK, Honor, PreKvK, and
   Hall of Fame payloads.
4. Profile likely hot spots in `kvk.rendering.kvk_rankings_card_renderer`, including background
   loading, overlay generation, font loading/fitting, text measurement, PNG encoding, and
   in-memory file handling.
5. Apply only low-risk optimisations that preserve visual output and embed fallback behaviour.
6. Prefer caching reusable immutable assets or layout primitives where safe.
7. Do not change ranking semantics, service/DAL contracts, command/view controls, SQL/cache
   behaviour, My Rank, CSV export, records Top 10-only behaviour, or compact Top 25/50 output.
8. Preserve Honor's no-admin-override KVK stats channel gate at command entry, browser refresh,
   My Rank, and export interaction time.
9. Preserve legacy `/kvk_rankings`, `/honor_rankings`, and image-based legacy `/prekvk report`.
10. Capture any out-of-scope findings structurally.

Likely touched areas:
- kvk/rendering/kvk_rankings_card_renderer.py
- tests/test_kvk_rankings_card_renderer.py
- nearest performance/renderer tests selected during audit
- docs/reference/deferred_optimisations.md if the Phase 5H performance item is closed or refined

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5H implementation plan.
2. Confirm the implementation slice before coding unless one-pass delivery is explicitly approved.
3. Capture before/after timing evidence for representative ranking-card render paths.
4. Implement only the approved Phase 5H optimisation slice.
5. Add/update focused tests to preserve card rendering, filenames, mode-specific support text,
   records card behaviour, current KVK/Honor/PreKvK card eligibility, and fallback assumptions.
6. Generate or inspect visual samples if any rendering/layout code changes.
7. Run focused tests and standard validators.
8. Run or justify skipping Codex Security. This slice is expected to be renderer-performance only;
   if it does not add data access, command/view interactions, file-system writes, network calls, or
   new trust boundaries, document the skip reason clearly.
9. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_card_renderer.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- Representative ranking-card render timings are measured before and after optimisation.
- Any optimisation preserves visual fidelity for current KVK, Honor, PreKvK, and Hall of Fame
  records Top 10 cards.
- Embed fallback remains stable.
- Top 25 and Top 50 compact browser output remains unchanged.
- Top 100 remains out of primary player controls.
- Private My Rank / Find Me remains stable.
- Private Full List CSV export remains stable.
- Records remain Top 10 only.
- Honor no-admin-override KVK stats channel gate remains preserved.
- Legacy ranking commands remain live.
- Legacy `/prekvk report` remains image-based.
- No SQL is added to command, view, renderer, or export formatting modules.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
- Phase 5H performance deferred item is closed or updated structurally based on the result.
```
