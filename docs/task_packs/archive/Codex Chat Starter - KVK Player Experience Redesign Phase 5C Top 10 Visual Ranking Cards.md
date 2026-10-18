# Codex Chat Starter - KVK Player Experience Redesign Phase 5C Top 10 Visual Ranking Cards

Phase 5A, Phase 5B, and Phase 5C are complete.

This starter is now a historical execution record. For the next Phase 5 delivery chat, use:

`docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5D Hall of Fame Records Visual Cards.md`

- Phase 5A: mirror PR #152 and production PR #461 delivered
  `/kvk rankings type:records` as the KD98 Hall of Fame Top 10 all-time single-KVK records
  foundation.
- Phase 5B: mirror PR #153 and production PR #462 delivered the unified current-ranking browser
  for KVK, Honor, and PreKvK rankings. It was pushed to production and smoke tested successfully.
- Phase 5C: mirror PR #154 and production PR #463 delivered the current KVK Top 10 visual ranking
  card. It was pushed to production, smoke tested successfully, and polished through production
  feedback.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Delivered Phase 5B baseline:

- `/kvk rankings type` choices remain `kvk`, `honor`, `prekvk`, and `records`.
- `/kvk rankings type:kvk`, `honor`, and `prekvk` use the shared current-ranking payload/service
  and `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- The unified current browser has mode selector, mode-specific metric selector, and Top 10, Top
  25, and Top 50 controls.
- Top 100 is not a primary player control.
- `/kvk rankings type:prekvk` is a public unified embed browser.
- Legacy `/prekvk report` remains image-based.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` remain live.
- Honor rankings preserve the stricter no-admin-override KVK stats channel gate, including inside
  browser mode switching.
- Records mode remains Top 10 only, single-KVK performances, not lifetime totals.
- Do not add records Top 25/50/100 controls in Phase 5C.
- The unified KVK embed table uses the legacy fixed-width one-line row budget after production
  smoke polish.
- Remaining known Phase 5 debt is captured structurally:
  - Hall of Fame records visual cards.
  - Honor and PreKvK Top 10 visual-card decision.
  - registry-aware private My Rank / local-position or export flow
  - legacy ranking command consolidation/deprecation after usage evidence

## Copy/Paste Starter

```text
Codex, start Phase 5C of the KVK Player Experience Redesign: Top 10 Visual Ranking Cards.

Phase 5A is complete: mirror PR #152 and production PR #461 delivered `/kvk rankings type:records`
as the KD98 Hall of Fame Top 10 all-time single-KVK records foundation.

Phase 5B is complete: mirror PR #153 and production PR #462 delivered the unified current-ranking
browser for `/kvk rankings type:kvk`, `honor`, and `prekvk`, pushed it to production, and smoke
tested it successfully. Preserve the Phase 5B unified browser foundation unless this new phase
explicitly approves a change.

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
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5C Top 10 Visual Ranking Cards.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, and `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Records mode uses the same rankings foundation plus `kvk.dal.kvk_rankings_dal` and
  `HallOfFameRecordsView`.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified embed output.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.
- Top 10, Top 25, and Top 50 are the primary current-ranking controls.
- Top 100 must remain out of the primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.

Phase 5C objective:
Add a visual Top 10 spotlight-card layer for the ranking journey without destabilising the Phase 5B
browser. Start with the safest/highest-value Top 10 card slice, likely current KVK rankings and/or
Hall of Fame records, then preserve embed fallback and keep Top 25/50 as the compact browser.

Scope:
1. Audit existing KVK card renderer primitives and assets from `/kvk stats`, `/kvk targets`, and
   `/kvk history`.
2. Confirm the first visual-card slice before implementation. Recommended first candidates:
   - Top 10 current KVK ranking card for the selected KVK metric.
   - Top 10 Hall of Fame records card for selected records metric.
3. Preserve Phase 5B unified browser controls and data contracts.
4. Use the existing ranking payload/service rows rather than recalculating rankings in the renderer.
5. Keep Top 25 and Top 50 on embed/browser output unless separately approved.
6. Keep Top 100 out of primary player controls.
7. Keep records Top 10 only.
8. Preserve legacy commands during rollout.
9. Preserve image-based legacy `/prekvk report`.
10. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, or renderer
    modules.
11. Add structured deferred optimisations for any out-of-scope card, export, My Rank, or legacy
    consolidation work.

Likely touched areas:
- commands/kvk_cmds.py
- kvk/models/kvk_rankings.py
- kvk/services/kvk_rankings_service.py
- kvk/rendering/kvk_rankings_embed.py
- kvk/rendering/ or assets/kvk/cards for a new ranking-card renderer
- ui/views/kvk_rankings_views.py
- tests/test_kvk_cmds.py
- tests/test_kvk_rankings_service.py
- tests/test_kvk_rankings_browser_view.py
- nearest existing renderer/card tests
- docs/reference/canonical_command_reference.md if visible behaviour changes
- docs/reference/deferred_optimisations.md if new deferred work is found

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5C implementation plan.
2. Confirm the first visual-card slice and fallback policy before implementation unless the
   operator explicitly approves one-pass delivery.
3. Validate any SQL/cache assumptions against C:\K98-bot-SQL-Server where data contracts are
   SQL-backed or ambiguous.
4. Implement only the approved Phase 5C slice.
5. Add/update focused tests for renderer payload use, fallback behaviour, view/command routing,
   Top 10-only card behaviour, and legacy command preservation.
6. Generate local visual card samples and inspect desktop/mobile-like readability.
7. Run focused tests and standard validators.
8. Run or justify skipping Codex Security before PR handoff.
9. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- .\.venv\Scripts\python.exe -m pytest -q <nearest ranking/card renderer tests>
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- Top 10 visual card output is readable, polished, and aligned with the modern KVK card language.
- The renderer consumes ranking payloads and does not recalculate source-of-truth ranking
  semantics.
- The Phase 5B unified embed browser remains stable.
- Top 25 and Top 50 remain available through the compact browser.
- Top 100 is not added as a primary player control.
- Records mode remains Top 10 only and does not imply lifetime totals.
- Legacy ranking commands remain live.
- Legacy `/prekvk report` remains image-based.
- Commands and views stay thin.
- No SQL is added to command, view, or renderer modules.
- Renderer failures have user-visible fallback.
- Local visual samples are generated and inspected.
- Focused tests and standard validators pass.
- Deferred optimisations are captured structurally.
```
