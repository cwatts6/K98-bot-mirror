# Codex Chat Starter - KVK Player Experience Redesign Phase 5F My Rank and Export Polish

Phase 5A through Phase 5E are complete.

- Phase 5A: mirror PR #152 and production PR #461 delivered
  `/kvk rankings type:records` as the KD98 Hall of Fame Top 10 all-time single-KVK records
  foundation.
- Phase 5B: mirror PR #153 and production PR #462 delivered the unified current-ranking browser
  for KVK, Honor, and PreKvK rankings.
- Phase 5C: mirror PR #154 and production PR #463 delivered the current KVK Top 10 visual ranking
  card for `/kvk rankings type:kvk`.
- Phase 5D: mirror PR #155 and production PR #464 delivered the Hall of Fame records Top 10
  visual cards for `/kvk rankings type:records`.
- Phase 5E: mirror PR #156 and production PR #465 delivered Honor and PreKvK Top 10 visual cards
  for `/kvk rankings type:honor` and `/kvk rankings type:prekvk`.

All delivered Phase 5A-5E work has been merged to mirror/production, pushed to prod, and smoke
tested successfully. Preserve it unless Phase 5F explicitly approves a change.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

## Copy/Paste Starter

```text
Codex, start Phase 5F of the KVK Player Experience Redesign: My Rank and Export Polish for /kvk rankings.

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
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5F My Rank and Export Polish.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, `kvk.rendering.kvk_rankings_card_renderer`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Current KVK, Honor, PreKvK, and Hall of Fame records all have Top 10 visual cards with embed
  fallback.
- KVK current rankings are shaped from the stats cache with `STATUS = INCLUDED` and
  `Starting Power >= 40M`.
- Honor current rankings use latest imported Honor scan metadata and must preserve the
  no-admin-override KVK stats channel gate.
- PreKvK current rankings wrap `prekvk.report_service` for unified browser output.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.
- Top 10, Top 25, and Top 50 are the primary current-ranking controls.
- Top 100 must remain out of the primary player controls.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.

Phase 5F objective:
Design and implement the approved My Rank / Find Me and export polish slice for `/kvk rankings`
so players outside the public Top 10/25/50 can find their own current position without adding
Top 100 back to the primary player controls.

Scope:
1. Start with audit/scope and a proposed Phase 5F implementation plan.
2. Confirm the first implementation slice before coding unless the operator explicitly approves
   one-pass delivery.
3. Audit registry/account lookup options for a private My Rank / Find Me flow.
4. Audit ranking payload/service support needed to find a registered governor's position in KVK,
   Honor, and PreKvK current rankings.
5. Audit export/full-list needs as the deeper access path replacing primary Top 100.
6. Preserve current KVK, Honor, PreKvK, and Hall of Fame Top 10 visual cards.
7. Preserve Top 25 and Top 50 compact browser output.
8. Preserve records Top 10 only.
9. Preserve Top 100 exclusion from primary player controls.
10. Preserve Honor's no-admin-override KVK stats channel gate at command entry and browser refresh.
11. Preserve legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`.
12. Preserve image-based legacy `/prekvk report`.
13. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, or renderer
    modules.
14. Keep My Rank responses private by default unless explicitly approved otherwise.
15. Capture any out-of-scope findings structurally.

Known out-of-scope follow-up already captured:
- Phase 5G wrap-up polish:
  - Honor Top 25/Top 50 compact output is missing values.
  - PreKvK Top 25/Top 50 compact output needs fixed-width column alignment.
  - Current KVK Top 10 card podium ranks/text should be centered to match Records, Honor, and
    PreKvK.
- Phase 5H performance optimisation:
  - Ranking-card render/load latency should be profiled and optimised before Phase 5 closes.
- Legacy-ranking consolidation/deprecation remains separate and requires usage evidence plus
  rollout approval.

Likely touched areas:
- commands/kvk_cmds.py
- kvk/models/kvk_rankings.py
- kvk/services/kvk_rankings_service.py
- kvk/rendering/kvk_rankings_embed.py
- ui/views/kvk_rankings_views.py
- registry/account lookup services if needed for registered governor resolution
- prekvk/report_service.py only if current payload support needs a narrow adapter
- tests/test_kvk_cmds.py
- tests/test_kvk_rankings_service.py
- tests/test_kvk_rankings_browser_view.py
- nearest registry/account tests
- nearest Honor and PreKvK ranking tests
- docs/reference/canonical_command_reference.md if visible behaviour changes
- docs/reference/deferred_optimisations.md if new deferred work is found

Mandatory workflow:
1. Start with audit/scope and proposed Phase 5F plan.
2. Validate SQL/cache/source assumptions against C:\K98-bot-SQL-Server where data contracts are
   SQL-backed or ambiguous.
3. Implement only the approved Phase 5F slice.
4. Add/update focused tests for registered user, unregistered user, multi-account user, not-ranked
   governor, missing source data, mode/metric switching, export/full-list behavior if added,
   Honor channel-gate preservation, Top 100 exclusion, and legacy command preservation.
5. Run focused tests and standard validators.
6. Run or justify skipping Codex Security before PR handoff.
7. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_honor_rankings_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_embed.py
- nearest registry/account tests selected during audit
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- My Rank / Find Me or export polish is delivered only for the approved Phase 5F slice.
- Players have a clear deeper access path without reintroducing Top 100 as a primary control.
- Responses that reveal a registered user's local rank are private by default.
- KVK, Honor, and PreKvK ranking semantics remain service-owned.
- Honor no-admin-override KVK stats channel gate remains preserved.
- Current KVK, Honor, PreKvK, and Hall of Fame records Top 10 cards remain stable.
- Top 25 and Top 50 compact browser output remains available.
- Records remain Top 10 only.
- Legacy ranking commands remain live.
- Legacy `/prekvk report` remains image-based.
- Commands and views stay thin.
- No SQL is added to command, view, or renderer modules.
- Focused tests and standard validators pass.
- Remaining Phase 5G/5H deferred work stays captured structurally.
```
