# Codex Chat Starter - KVK Player Experience Redesign Phase 5G Rankings Wrap-up Polish

Status: completed execution starter. Phase 5A through Phase 5H are complete; Phase 5H ranking-card
performance optimisation delivered the final Phase 5 slice.

Phase 5A through Phase 5F-2 were complete when this starter was created.
Phase 5G was completed in mirror PR #160 after smoke-test polish confirmed Honor Top 25/50 values,
PreKvK Top 25/50 alignment, near-billion unit preservation, display-width alignment for
wide/special-character governor names, and current KVK Top 10 podium centering.

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
  current KVK, Honor, and PreKvK rankings. It was pushed to production, smoke tested successfully,
  and polished through review/smoke-test feedback.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5F CSV Full-List Export.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Delivered Phase 5F-2 baseline:

- `/kvk rankings type` choices remain `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, `kvk.rendering.kvk_rankings_card_renderer`,
  `kvk.rendering.kvk_rankings_csv`, `kvk.services.kvk_rankings_export_service`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Current KVK, Honor, PreKvK, and Hall of Fame records all have Top 10 visual cards with embed
  fallback.
- Top 25 and Top 50 remain compact unified browser output for current KVK, Honor, and PreKvK.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Private My Rank is available for registered governors in current KVK, Honor, and PreKvK modes.
- Private Full List CSV export is available for current KVK, Honor, and PreKvK modes.
- CSV output uses clean leaderboard-only columns:
  - Honor: `Rank`, `GovernorID`, `GovernorName`, `Honor`, `KVK`.
  - KVK: `Rank`, `GovernorID`, `GovernorName`, `Power`, `Kills`, `PercentKillTarget`, `Deads`,
    `DKP`, `Acclaim`, `TankingScore`, `KillPoints`, `Healed`.
  - PreKvK: `Rank`, `GovernorID`, `GovernorName`, `Power`, `Stage1`, `Stage2`, `Stage3`,
    `Overall`.
- CSV generation is in-memory, formula-leading text is escaped, response errors are private, and
  records export remains out of scope.
- KVK Top 10 metric selection includes Kills, % Kill Target, Deads, DKP, Acclaim, Tanking Score,
  Kill Points, and Healed.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified browser output.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.

Next starter, now completed by Phase 5H:

`docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5H Ranking Card Performance Optimisation.md`

## Copy/Paste Starter

```text
Codex, start Phase 5G of the KVK Player Experience Redesign: rankings wrap-up polish for /kvk rankings.

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
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5F CSV Full-List Export.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, `kvk.rendering.kvk_rankings_card_renderer`,
  `kvk.rendering.kvk_rankings_csv`, `kvk.services.kvk_rankings_export_service`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Current KVK, Honor, PreKvK, and Hall of Fame records all have Top 10 visual cards with embed
  fallback.
- Top 25 and Top 50 remain compact unified browser output for current KVK, Honor, and PreKvK.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Private My Rank is available for registered governors in current KVK, Honor, and PreKvK modes.
- Private Full List CSV export is available for current KVK, Honor, and PreKvK modes.
- CSV columns are clean leaderboard-only columns:
  - Honor: Rank, GovernorID, GovernorName, Honor, KVK.
  - KVK: Rank, GovernorID, GovernorName, Power, Kills, PercentKillTarget, Deads, DKP, Acclaim,
    TankingScore, KillPoints, Healed.
  - PreKvK: Rank, GovernorID, GovernorName, Power, Stage1, Stage2, Stage3, Overall.
- KVK Top 10 metric selection includes Kills, % Kill Target, Deads, DKP, Acclaim, Tanking Score,
  Kill Points, and Healed.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.

Phase 5G objective:
Deliver the remaining rankings wrap-up polish items captured during Phase 5E/5F so Phase 5 can
move toward performance optimisation and closure without leaving known current-ranking UX gaps.

Scope:
1. Start with audit/scope and a proposed Phase 5G implementation plan.
2. Confirm the first implementation slice before coding unless the operator explicitly approves
   one-pass delivery.
3. Fix Honor Top 25 and Top 50 compact browser output so ranking values are displayed.
4. Fix PreKvK Top 25 and Top 50 compact browser output alignment using fixed-width formatting
   where appropriate.
5. Center current KVK Top 10 card podium ranks/names/values to match Records, Honor, and PreKvK.
6. Preserve all delivered Top 10 visual cards and embed fallbacks.
7. Preserve Top 25 and Top 50 compact browser controls.
8. Preserve Top 100 exclusion from primary player controls.
9. Preserve private My Rank and private Full List CSV export.
10. Preserve records Top 10 only; records export/detail output remains out of scope unless
    explicitly approved.
11. Preserve Honor's no-admin-override KVK stats channel gate at command entry, browser refresh,
    My Rank, and export interaction time.
12. Preserve legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`.
13. Preserve image-based legacy `/prekvk report`.
14. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, renderer,
    or export formatting modules.
15. Keep Phase 5H performance optimisation separate. Do not profile/cache/refactor ranking-card
    render performance in this slice unless explicitly approved.
16. Capture any out-of-scope findings structurally.

Likely touched areas:
- kvk/rendering/kvk_rankings_embed.py
- kvk/rendering/kvk_rankings_card_renderer.py
- kvk/services/kvk_rankings_service.py only if supporting values or labels need service-owned
  correction
- ui/views/kvk_rankings_views.py only if browser refresh/control state needs narrow polish
- tests/test_kvk_rankings_service.py
- tests/test_kvk_rankings_browser_view.py
- nearest renderer/card tests selected during audit
- docs/reference/deferred_optimisations.md if Phase 5G items are closed or new deferred work is found

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5G implementation plan.
2. Confirm the implementation slice before coding unless the operator explicitly approves
   one-pass delivery.
3. Implement only the approved Phase 5G slice.
4. Add/update focused tests for Honor Top 25/50 value rendering, PreKvK Top 25/50 alignment,
   KVK podium centering, preservation of Top 10/25/50 controls, Top 100 exclusion, My Rank/export
   preservation, records Top 10-only preservation, Honor gate preservation, and legacy command
   preservation where touched.
5. Generate or inspect visual/card samples for the KVK podium-centering change if the renderer
   change is visual.
6. Run focused tests and standard validators.
7. Run or justify skipping Codex Security. This slice likely touches Discord rendering and
   user-controlled ranking text; if the implementation changes only layout/formatting with no new
   trust boundary, document the skip reason clearly.
8. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- nearest renderer/card tests selected during audit
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- Honor Top 25 and Top 50 compact browser rows display ranking values.
- PreKvK Top 25 and Top 50 compact browser rows are aligned and readable on Discord.
- Current KVK Top 10 card podium ranks/names/values are centered consistently with Records,
  Honor, and PreKvK cards.
- Private My Rank / Find Me remains stable.
- Private Full List CSV export remains stable.
- Current KVK, Honor, PreKvK, and Hall of Fame records Top 10 cards remain stable.
- Top 25 and Top 50 compact browser output remains available.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only.
- Honor no-admin-override KVK stats channel gate remains preserved.
- Legacy ranking commands remain live.
- Legacy `/prekvk report` remains image-based.
- Commands and views stay thin.
- No SQL is added to command, view, renderer, or export formatting modules.
- Focused tests and standard validators pass.
- Codex Security is run or explicitly justified.
- Remaining Phase 5H performance work stays captured structurally.
```
