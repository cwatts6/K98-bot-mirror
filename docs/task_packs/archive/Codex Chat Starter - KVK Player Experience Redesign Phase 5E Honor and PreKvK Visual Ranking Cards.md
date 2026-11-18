# Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards

Phase 5A, Phase 5B, Phase 5C, and Phase 5D are complete.

- Phase 5A: mirror PR #152 and production PR #461 delivered
  `/kvk rankings type:records` as the KD98 Hall of Fame Top 10 all-time single-KVK records
  foundation.
- Phase 5B: mirror PR #153 and production PR #462 delivered the unified current-ranking browser
  for KVK, Honor, and PreKvK rankings. It was pushed to production and smoke tested successfully.
- Phase 5C: mirror PR #154 and production PR #463 delivered the current KVK Top 10 visual ranking
  card for `/kvk rankings type:kvk`. It was pushed to production, smoke tested successfully, and
  polished through production feedback.
- Phase 5D: mirror PR #155 and production PR #464 delivered the Hall of Fame records Top 10 visual
  cards for `/kvk rankings type:records`. It was pushed to production, smoke tested successfully,
  and polished through production feedback.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5C Top 10 Visual Ranking Cards.md`
- `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5D Hall of Fame Records Visual Cards.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Delivered Phase 5D baseline:

- `/kvk rankings type` choices remain `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Records mode uses the same rankings foundation plus `kvk.dal.kvk_rankings_dal` and
  `HallOfFameRecordsView`.
- Current KVK Top 10 cards and Hall of Fame records Top 10 cards use
  `kvk.rendering.kvk_rankings_card_renderer`.
- Current KVK Top 10 card metrics are Kills, % Kill Target, Deads, DKP, Acclaim, and Tanking
  Score.
- Current KVK rankings default to Kills.
- Hall of Fame records visual cards support all existing records metrics and show Top 10 from the
  metric-specific qualifying records count.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified embed output.
- Top 10, Top 25, and Top 50 are the primary current-ranking controls.
- Top 25 and Top 50 remain compact unified embed/browser output.
- Top 100 remains out of primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.
- Renderer/card send failures must have user-visible embed fallback.
- Remaining known Phase 5 delivery work is captured structurally:
  - Honor and PreKvK Top 10 visual cards in Phase 5E.
  - Registry-aware private My Rank / local-position or export flow in Phase 5F.
  - Full-list/export path if Top 100 remains out of primary controls.
  - Legacy ranking command consolidation/deprecation after usage evidence and rollout approval.

## Copy/Paste Starter

```text
Codex, start Phase 5E of the KVK Player Experience Redesign: Honor and PreKvK Visual Ranking Cards.

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
successfully, and completed follow-up polish. Preserve the Phase 5B unified browser, Phase 5C
current KVK card foundation, and Phase 5D records card foundation unless this new phase explicitly
approves a change.

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
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5D Hall of Fame Records Visual Cards.md
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, and `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Current KVK and Hall of Fame records Top 10 cards use
  `kvk.rendering.kvk_rankings_card_renderer`.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified embed output.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.
- Top 10, Top 25, and Top 50 are the primary current-ranking controls.
- Top 25 and Top 50 remain compact unified embed/browser output.
- Top 100 must remain out of the primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- My Rank/export and legacy-ranking consolidation remain deferred to later Phase 5 delivery.

Phase 5E objective:
Add visual Top 10 ranking-card output for `/kvk rankings type:honor` and
`/kvk rankings type:prekvk` so the full `/kvk rankings` visual surface is complete, without
destabilising the delivered current KVK card, Hall of Fame records card, or unified browser.

Scope:
1. Audit delivered Phase 5C/5D ranking-card primitives and the existing Honor/PreKvK current
   ranking payload/service output.
2. Confirm the first Phase 5E implementation slice before implementation unless the operator
   explicitly approves one-pass delivery. Recommended first slice:
   - Honor Top 10 visual card using the shared current-ranking payload.
   - PreKvK Top 10 visual card using the shared current-ranking payload.
   - Implement both in one PR only if the audit confirms they can share primitives without
     weakening mode-specific wording or fallback behaviour.
3. Preserve Honor's no-admin-override KVK stats channel gate at command entry and browser refresh.
4. Preserve image-based legacy `/prekvk report`.
5. Preserve `/kvk rankings type:prekvk` unified embed output for Top 25 and Top 50.
6. Preserve `/kvk rankings type:honor` unified embed output for Top 25 and Top 50.
7. Preserve current KVK Top 10 cards from Phase 5C.
8. Preserve Hall of Fame records Top 10 cards from Phase 5D.
9. Preserve records Top 10 only.
10. Preserve Top 25 and Top 50 compact current-ranking browser output.
11. Keep Top 100 out of primary player controls.
12. Preserve legacy commands during rollout.
13. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, or renderer
    modules.
14. Preserve embed fallback for card render/send failures.
15. Follow the Phase 5C/5D visual language: clean modern cards, bold readable text, no black text
    boxes, no unnecessary borders, no dense table lines, and no low-value developer-note copy.
16. Keep My Rank/export and legacy-ranking consolidation captured for Phase 5F+ delivery.

Likely touched areas:
- commands/kvk_cmds.py
- kvk/models/kvk_rankings.py
- kvk/services/kvk_rankings_service.py
- kvk/rendering/kvk_rankings_embed.py
- kvk/rendering/kvk_rankings_card_renderer.py or a new mode-specific card renderer
- ui/views/kvk_rankings_views.py
- prekvk/report_service.py only if payload support requires a narrow adapter change
- assets/kvk/cards/
- tests/test_kvk_cmds.py
- tests/test_kvk_rankings_service.py
- tests/test_kvk_rankings_browser_view.py
- tests/test_kvk_rankings_card_renderer.py
- nearest existing Honor ranking tests
- nearest existing PreKvK report/ranking tests
- docs/reference/canonical_command_reference.md if visible behaviour changes
- docs/reference/deferred_optimisations.md if new deferred work is found

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5E implementation plan.
2. Confirm whether Phase 5E should deliver Honor and PreKvK cards together or as two internal
   Phase 5E slices before implementation unless the operator explicitly approves one-pass
   delivery.
3. Validate SQL/cache/source assumptions against C:\K98-bot-SQL-Server where data contracts are
   SQL-backed or ambiguous, especially Honor freshness/source metadata.
4. Implement only the approved Phase 5E slice.
5. Add/update focused tests for Honor card rendering, PreKvK card rendering, fallback behaviour,
   view/command routing, Top 10-only card behaviour, Top 25/50 compact browser preservation,
   Honor channel-gate preservation, legacy command preservation, and legacy `/prekvk report`
   image preservation.
6. Generate local visual samples for Honor and PreKvK cards and inspect desktop/mobile-like
   readability.
7. Run focused tests and standard validators.
8. Run or justify skipping Codex Security before PR handoff.
9. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_card_renderer.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_honor_rankings.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_embed.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_report_views.py
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- Honor Top 10 visual card output is readable, polished, and aligned with the modern KVK ranking
  card language.
- PreKvK Top 10 visual card output is readable, polished, and aligned with the modern KVK ranking
  card language.
- Card wording clearly distinguishes Honor and PreKvK source/context from current KVK and Hall of
  Fame records.
- Renderers consume ranking payloads and do not recalculate source-of-truth ranking semantics.
- Honor no-admin-override KVK stats channel gate remains preserved.
- Legacy `/prekvk report` remains image-based.
- Current KVK Top 10 cards remain stable.
- Hall of Fame records Top 10 cards remain stable.
- Records remain Top 10 only.
- Phase 5B unified current-ranking embed browser remains stable.
- Top 25 and Top 50 remain available through the compact browser for KVK, Honor, and PreKvK.
- Top 100 is not added as a primary player control.
- Legacy ranking commands remain live.
- Commands and views stay thin.
- No SQL is added to command, view, or renderer modules.
- Renderer failures have user-visible fallback.
- Local visual Honor and PreKvK samples are generated and inspected.
- Focused tests and standard validators pass.
- Remaining Phase 5 deferred work is captured structurally.
```
