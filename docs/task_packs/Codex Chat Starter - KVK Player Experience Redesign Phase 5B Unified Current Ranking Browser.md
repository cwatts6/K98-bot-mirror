# Codex Chat Starter - KVK Player Experience Redesign Phase 5B Unified Current Ranking Browser

Status: historical. Phase 5B was delivered in mirror PR #153 and production PR #462, pushed to
production, and smoke tested successfully. Use
`docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5C Top 10 Visual Ranking Cards.md`
for the next active Phase 5 chat.

Phase 5A was completed in mirror PR #152 and production PR #461, pushed to production, and smoke
tested successfully.

Source programme documents:

- `docs/task_packs/KVK Player Experience Redesign - Programme Pack.md`
- `docs/task_packs/Codex Task Pack - KVK Player Experience Redesign Phase 5 Unified Rankings Visual UX Polish.md`
- `docs/reference/canonical_command_reference.md`
- `docs/reference/deferred_optimisations.md`

Delivered Phase 5A baseline:

- `/kvk rankings type:records` is live under the existing `/kvk rankings` command.
- KD98 Hall of Fame records are Top 10 all-time single-KVK performances only.
- Supported records metrics are Kills, KillPoints, Deads, DKP, Healed, Acclaim, Honor, and PreKvK
  where qualifying source values exist.
- Records allow the same governor to appear multiple times.
- Records have a metric selector only; do not add Top 25, Top 50, or Top 100 controls unless a
  later task explicitly approves it.
- Shared rankings foundation files now exist:
  - `kvk/models/kvk_rankings.py`
  - `kvk/services/kvk_rankings_service.py`
  - `kvk/dal/kvk_rankings_dal.py`
  - `kvk/rendering/kvk_rankings_embed.py`
  - `ui/views/kvk_rankings_views.py`
- Current KVK rankings still primarily use `build_KVKrankings_embed.py` and
  `ui/views/stats_views.py::KVKRankingView`.
- Current Honor rankings still primarily use `honor_rankings_view.py::HonorRankingView`.
- Current PreKvK rankings still use `ui/views/prekvk_report_views.py::PreKvkReportView` and
  `prekvk.report_image_renderer`.
- KVK and Honor primary controls use Top 10, Top 25, and Top 50; Top 100 is no longer a primary
  player button.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` paths remain live.

## Copy/Paste Starter

```text
Codex, start Phase 5B of the KVK Player Experience Redesign: Unified Current Ranking Browser.

Phase 5A is complete: mirror PR #152 and production PR #461 were merged, pushed to production, and
smoke tested successfully. Phase 5A delivered `/kvk rankings type:records` as the KD98 Hall of
Fame Top 10 all-time single-KVK records foundation. Preserve that records mode exactly unless this
new phase explicitly approves a change.

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
- docs/task_packs/Codex Chat Starter - KVK Player Experience Redesign Phase 5B Unified Current Ranking Browser.md
- docs/reference/canonical_command_reference.md
- docs/reference/deferred_optimisations.md

Current delivered context:
- `/kvk rankings type` choices are `kvk`, `honor`, `prekvk`, and `records`.
- Records mode uses `kvk.models.kvk_rankings`, `kvk.services.kvk_rankings_service`,
  `kvk.dal.kvk_rankings_dal`, `kvk.rendering.kvk_rankings_embed`, and
  `ui.views.kvk_rankings_views.HallOfFameRecordsView`.
- Records are Top 10 only, single-KVK performances, not lifetime totals.
- Do not add records Top 25/50/100 controls in Phase 5B.
- KVK current rankings still use `build_KVKrankings_embed.py` and
  `ui/views/stats_views.py::KVKRankingView`.
- Honor current rankings still use `honor_rankings_view.py::HonorRankingView`.
- PreKvK current rankings still use `ui/views/prekvk_report_views.py::PreKvkReportView` and the
  existing PreKvK image renderer.
- Legacy `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` commands remain live.
- Players heavily use Top 10, Top 25, and Top 50. Top 100 should remain out of primary player
  controls unless usage evidence proves otherwise.

Phase 5B objective:
Build the unified current-ranking browser foundation for KVK, Honor, and PreKvK rankings so
`/kvk rankings` feels like one coherent player journey. This is not the Top 10 visual-card phase
yet; keep image output optional and prefer a stable unified browser/payload/control foundation.

Scope:
1. Review current KVK, Honor, and PreKvK ranking flows and confirm the safest integration point.
2. Extend or wrap the shared ranking payload/service model so current rankings can use consistent
   mode, metric, limit, freshness, filters, rows, and fallback semantics.
3. Align controls around mode/metric selectors and Top 10, Top 25, Top 50 primary limits.
4. Keep Top 100 out of primary player controls. If deeper access is needed, propose export or
   advanced handling instead of adding a main button.
5. Preserve Hall of Fame records mode and keep records Top 10 only.
6. Preserve legacy commands during rollout.
7. Keep SQL/data access in service/DAL/cache layers. Do not put SQL in command, view, or renderer
   modules.
8. Capture any out-of-scope rankings work as structured deferred optimisations, but do not let
   known Phase 5 ranking-browser debt disappear. Add more Phase 5 sub-phases if needed.

Likely touched areas:
- commands/kvk_cmds.py
- build_KVKrankings_embed.py
- honor_rankings_view.py
- ui/views/stats_views.py
- ui/views/prekvk_report_views.py
- kvk/models/kvk_rankings.py
- kvk/services/kvk_rankings_service.py
- kvk/rendering/kvk_rankings_embed.py
- stats_alerts/honors.py
- prekvk/report_service.py
- prekvk/report_image_renderer.py
- tests/test_kvk_cmds.py
- tests/test_kvkrankingview.py
- tests/test_honor_rankings_view.py
- tests/test_kvk_rankings_service.py
- tests/test_prekvk_report_views.py or the nearest existing PreKvK view/report tests

Mandatory workflow:
1. Start with audit/scope and a proposed Phase 5B implementation plan.
2. Validate SQL/cache source assumptions against C:\K98-bot-SQL-Server where current ranking data
   contracts are SQL-backed or ambiguous.
3. Stop for approval before implementation unless the operator explicitly approves one-pass
   delivery in the new chat.
4. Implement only the approved Phase 5B slice.
5. Add/update focused tests for current-ranking payload shaping, view controls, command routing,
   Top-N behavior, empty/failure states, and legacy command preservation.
6. Run focused tests and standard validators.
7. Run or justify skipping Codex Security before PR handoff.
8. Open a ready-for-review PR against `K98-bot-mirror`.

Suggested validation after implementation:
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_cmds.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvkrankingview.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_honor_rankings_view.py
- .\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_rankings_service.py
- .\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
- .\.venv\Scripts\python.exe scripts\validate_deferred_items.py
- .\.venv\Scripts\python.exe scripts\select_tests.py
- .\.venv\Scripts\python.exe scripts\smoke_imports.py
- .\.venv\Scripts\python.exe scripts\validate_command_registration.py
- .\.venv\Scripts\python.exe -m pre_commit run -a
- .\.venv\Scripts\python.exe -m pytest -q tests

Acceptance criteria:
- `/kvk rankings type:kvk`, `honor`, and `prekvk` feel like one coherent browser.
- Top 10, Top 25, and Top 50 controls are consistent where each mode supports them.
- Top 100 is not a primary player control.
- Records mode still works, remains Top 10 only, and is not regressed.
- Legacy ranking commands remain live.
- Commands and views stay thin.
- No SQL is added to command, view, or renderer modules.
- Fallbacks are user-visible for cache/SQL/rendering failures.
- Focused tests and standard validators pass.
- Deferred optimisations are captured structurally, with any remaining Phase 5 work assigned to
  explicit later sub-phases.
```
