# Codex Chat Starter - KVK Player Experience Redesign Phase 5D Hall of Fame Records Visual Cards

Status: Phase 5D is complete. This starter is retained as the Phase 5D execution record.
Use `docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5E Honor and PreKvK Visual Ranking Cards.md`
for the next active sub-phase.

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
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Delivered Phase 5C baseline:

- `/kvk rankings type` choices remain `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, and
  `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Records mode uses the shared rankings foundation plus `kvk.dal.kvk_rankings_dal` and
  `HallOfFameRecordsView`.
- `/kvk rankings type:kvk` Top 10 now renders a visual card for current KVK rankings.
- Current KVK Top 10 card metrics are Kills, % Kill Target, Deads, DKP, Acclaim, and Tanking
  Score.
- Current KVK rankings default to Kills.
- Power remains available for Top 25 and Top 50 compact browser analysis, but is not a Top 10 card
  metric.
- Tanking Score ranks lower scores first and requires positive KillPoints plus positive healed
  troops, matching `/kvk history` semantics.
- Top 25 and Top 50 remain compact unified embed/browser output.
- Top 100 remains out of primary player controls.
- Current KVK card render/send failures fall back to the unified embed output.
- Records remain Top 10 only, single-KVK performances, not lifetime totals.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Legacy `/prekvk report` remains image-based.
- Remaining known Phase 5 delivery work is captured structurally and must not be lost:
  - Honor and PreKvK Top 10 visual cards in Phase 5E.
  - Registry-aware private My Rank / local-position or export flow in Phase 5F.
  - Full-list/export path if Top 100 remains out of primary controls.
  - Legacy ranking command consolidation/deprecation after usage evidence and rollout approval.

## Copy/Paste Starter

```text
Codex, start Phase 5D of the KVK Player Experience Redesign: Hall of Fame Records Visual Cards.

Phase 5A is complete: mirror PR #152 and production PR #461 delivered `/kvk rankings type:records`
as the KD98 Hall of Fame Top 10 all-time single-KVK records foundation.

Phase 5B is complete: mirror PR #153 and production PR #462 delivered the unified current-ranking
browser for `/kvk rankings type:kvk`, `honor`, and `prekvk`, pushed it to production, and smoke
tested it successfully.

Phase 5C is complete: mirror PR #154 and production PR #463 delivered the current KVK Top 10
visual ranking card for `/kvk rankings type:kvk`, pushed it to production, smoke tested it
successfully, and completed follow-up polish. Preserve the Phase 5B unified browser and Phase 5C
current KVK card foundation unless this new phase explicitly approves a change.

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
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5D Hall of Fame Records Visual Cards.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Current-ranking modes use `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.rendering.kvk_rankings_embed`, and `ui.views.kvk_rankings_views.CurrentRankingsBrowserView`.
- Records mode uses the same rankings foundation plus `kvk.dal.kvk_rankings_dal` and
  `HallOfFameRecordsView`.
- Current KVK Top 10 cards use `kvk.rendering.kvk_rankings_card_renderer`.
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

Phase 5D objective:
Add a visual Top 10 Hall of Fame records-card layer for `/kvk rankings type:records` without
destabilising the delivered records foundation or the current-ranking browser.

Scope:
1. Audit the delivered Phase 5C ranking-card primitives and the existing records payload/DAL/service
   output.
2. Confirm the first records-card slice before implementation. Recommended first slice:
   - Hall of Fame records Top 10 visual card for selected records metric.
   - Start with high-confidence records metrics such as Kills, KillPoints, Deads, and DKP before
     sparse historical metrics if the audit finds risk.
3. Preserve records Top 10 only.
4. Preserve repeated-governor appearances where a governor holds multiple single-KVK records.
5. Preserve missing/uncollected historical metric exclusion; never rank missing values as zero.
6. Use existing Hall of Fame ranking payload/service/DAL rows rather than recalculating records in
   the renderer.
7. Preserve embed fallback for records card render/send failures.
8. Preserve current KVK Top 10 cards from Phase 5C.
9. Preserve Top 25 and Top 50 compact current-ranking browser output.
10. Keep Top 100 out of primary player controls.
11. Preserve legacy commands during rollout.
12. Preserve image-based legacy `/prekvk report`.
13. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, or renderer
    modules.
14. Decide whether Honor and PreKvK Top 10 visual cards should be a later Phase 5 visual sub-phase
    or remain deferred.
15. Keep My Rank/export and legacy-ranking consolidation captured for later Phase 5 delivery.

Likely touched areas:
- commands/kvk_cmds.py
- kvk/models/kvk_rankings.py
- kvk/services/kvk_rankings_service.py
- kvk/dal/kvk_rankings_dal.py
- kvk/rendering/kvk_rankings_embed.py
- kvk/rendering/kvk_rankings_card_renderer.py or a new records-card renderer
- ui/views/kvk_rankings_views.py
- assets/kvk/cards/
- tests/test_kvk_cmds.py
- tests/test_kvk_rankings_service.py
- tests/test_kvk_rankings_browser_view.py
- tests/test_kvk_rankings_card_renderer.py
- nearest existing Hall of Fame records tests
- docs/reference/canonical_command_reference.md if visible behaviour changes
- docs/reference/deferred_optimisations.md if new deferred work is found

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5D implementation plan.
2. Confirm the first records-card slice and fallback policy before implementation unless the
   operator explicitly approves one-pass delivery.
3. Validate SQL/historical-record assumptions against C:\K98-bot-SQL-Server where data contracts
   are SQL-backed or ambiguous.
4. Implement only the approved Phase 5D slice.
5. Add/update focused tests for records renderer payload use, fallback behaviour, view/command
   routing, Top 10-only records behaviour, repeated-governor record behaviour, missing historical
   metric exclusion, and legacy command preservation.
6. Generate local visual records-card samples and inspect desktop/mobile-like readability.
7. Run focused tests and standard validators.
8. Run or justify skipping Codex Security before PR handoff.
9. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_browser_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_card_renderer.py
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- Hall of Fame Top 10 visual records card output is readable, polished, and aligned with the
  modern KVK card language.
- Records card wording clearly communicates all-time single-KVK performances, not lifetime totals.
- The renderer consumes ranking payloads and does not recalculate source-of-truth record semantics.
- Records remain Top 10 only.
- Records do not add Top 25, Top 50, or Top 100 controls.
- Repeated-governor record appearances remain allowed.
- Missing/uncollected historical metrics are excluded safely.
- Current KVK Top 10 cards remain stable.
- Phase 5B unified current-ranking embed browser remains stable.
- Top 25 and Top 50 remain available through the compact browser.
- Top 100 is not added as a primary player control.
- Legacy ranking commands remain live.
- Legacy `/prekvk report` remains image-based.
- Commands and views stay thin.
- No SQL is added to command, view, or renderer modules.
- Renderer failures have user-visible fallback.
- Local visual records-card samples are generated and inspected.
- Focused tests and standard validators pass.
- Remaining Phase 5 deferred work is captured structurally.
```
